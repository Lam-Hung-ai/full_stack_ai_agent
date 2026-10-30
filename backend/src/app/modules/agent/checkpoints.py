"""Checkpoints that reach PostgreSQL only when a turn pauses (database phase 4 §6).

A turn runs on a saver of its own that keeps state and write batches in RAM.
A turn that completes or fails leaves nothing behind. A turn that pauses on an
interrupt exports its boundary checkpoint with full channel versions and every
pending write batch (not just `__interrupt__`: finished siblings must not run
again), through `AsyncPostgresSaver` on the connection of the transaction that
also marks the message `requires_action`. Resuming seeds a fresh saver with
that stored checkpoint before the graph starts, so no connection is held while
the model runs.

Adapted from the proof in docs/experiments/langgraph-action-checkpoints, which
pins the same langgraph, checkpoint and postgres saver versions as pyproject.
Contract: root graph, ordinary channels, durability "exit"; no subgraphs.
"""

from collections import defaultdict
from collections.abc import Sequence
from copy import deepcopy
from typing import Any
from uuid import UUID

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    ChannelVersions,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
)
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg import AsyncConnection
from sqlalchemy.ext.asyncio import AsyncSession

INTERRUPT_CHANNEL = "__interrupt__"

type WriteBatch = tuple[list[tuple[str, Any]], str, str]


def thread_config(thread_id: str) -> RunnableConfig:
    return {"configurable": {"thread_id": thread_id, "checkpoint_ns": ""}}


def _key(config: RunnableConfig) -> tuple[str, str, str]:
    configurable = config["configurable"]
    return (
        configurable["thread_id"],
        configurable.get("checkpoint_ns", ""),
        configurable.get("checkpoint_id", ""),
    )


def _parent_of(item: CheckpointTuple) -> RunnableConfig:
    """Where the checkpoint hangs: the previous pause, or the thread root
    ("exit" durability writes no intermediate checkpoints)."""
    configurable = item.config["configurable"]
    return item.parent_config or {
        "configurable": {
            "thread_id": configurable["thread_id"],
            "checkpoint_ns": configurable.get("checkpoint_ns", ""),
        }
    }


class TurnSaver(InMemorySaver):
    """RAM checkpointer of one turn that can export its pause."""

    def __init__(self) -> None:
        super().__init__()
        self._batches: dict[tuple[str, str, str], list[WriteBatch]] = defaultdict(list)

    def seed(self, stored: CheckpointTuple) -> None:
        """Load a stored pause; an interrupt later in the same node may update
        its writes without a new checkpoint, so they are replayed too."""
        InMemorySaver.put(
            self,
            _parent_of(stored),
            stored.checkpoint,
            stored.metadata,
            stored.checkpoint["channel_versions"],
        )
        tasks: dict[str, list[tuple[str, Any]]] = defaultdict(list)
        for task_id, channel, value in stored.pending_writes or []:
            tasks[task_id].append((channel, value))
        for task_id, writes in tasks.items():
            InMemorySaver.put_writes(self, stored.config, writes, task_id)

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> RunnableConfig:
        # On resume, unchanged channels may exist only in the stored pause:
        # keep every materialized version so the RAM copy stands alone.
        return InMemorySaver.put(
            self, config, checkpoint, metadata, checkpoint["channel_versions"]
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        batch = list(writes)
        self._batches[_key(config)].append((deepcopy(batch), task_id, task_path))
        InMemorySaver.put_writes(self, config, batch, task_id, task_path)

    def has_pause(self, thread_id: str) -> bool:
        item = InMemorySaver.get_tuple(self, thread_config(thread_id))
        return item is not None and any(
            channel == INTERRUPT_CHANNEL for _, channel, _ in item.pending_writes or []
        )

    async def export(self, durable: AsyncPostgresSaver, thread_id: str) -> dict:
        """Write the pause through `durable`; the caller owns the transaction.
        Returns the stored pointer (thread_id, checkpoint_ns, checkpoint_id)."""
        item = InMemorySaver.get_tuple(self, thread_config(thread_id))
        if item is None or not self.has_pause(thread_id):
            raise ValueError("Refusing to persist a checkpoint without an interrupt")
        saved = await durable.aput(
            _parent_of(item),
            item.checkpoint,
            item.metadata,
            item.checkpoint["channel_versions"],
        )
        for writes, task_id, task_path in self._batches[_key(saved)]:
            await durable.aput_writes(saved, writes, task_id, task_path)
        return dict(saved["configurable"])


async def durable_saver(session: AsyncSession) -> AsyncPostgresSaver:
    """The SDK saver on the session's own connection and transaction, so a
    checkpoint commits or rolls back together with the message rows."""
    connection = await session.connection()
    # The saver's tables are unqualified; this lasts until the transaction ends.
    await connection.exec_driver_sql(
        "SET LOCAL search_path = langgraph_checkpoints, chat_app, public"
    )
    raw = await connection.get_raw_connection()
    driver = raw.driver_connection
    assert isinstance(driver, AsyncConnection)
    return AsyncPostgresSaver(driver)


async def drop_checkpoints(session: AsyncSession, assistant_id: UUID) -> None:
    """Delete an assistant's checkpoint thread within the session's transaction."""
    saver = await durable_saver(session)
    await saver.adelete_thread(str(assistant_id))
