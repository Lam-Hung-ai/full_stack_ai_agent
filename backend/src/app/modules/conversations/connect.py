"""Connect: the latest state of a conversation, then its running turn (API §6).

Read only: no model, tool or resume. The stream starts with a snapshot of
the branch holding the active assistant (or the saved branch), taken from
PostgreSQL plus, for a running turn, the live view in Redis; then it replays
the turn's events after the view's watermark until the turn ends. When live
data is missing or has a gap, only the saved snapshot is sent: the client
reloads once the turn is saved (architecture §5, RR-02).
"""

from collections.abc import AsyncIterator, Sequence
from typing import Any
from uuid import UUID

from ag_ui.core import (
    BaseEvent,
    CustomEvent,
    EventType,
    MessagesSnapshotEvent,
    RunFinishedEvent,
    RunStartedEvent,
)
from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.modules.agent.live import LiveStore, LiveView
from app.modules.agent.runner import ASSISTANT_EVENT
from app.modules.conversations.repository import MessageRepository
from app.modules.conversations.service import ConversationService

LIVE_STATUSES = frozenset({"pending", "running"})
#: How long the tail waits for an event before checking the turn's owner.
TAIL_BLOCK_MS = 5_000


class ConnectService:
    def __init__(self, session: AsyncSession, *, live: LiveStore | None) -> None:
        self._session = session
        self._live = live
        self._messages = MessageRepository(session)

    async def open(
        self, *, user: Principal, conversation_id: UUID
    ) -> AsyncIterator[BaseEvent]:
        """Authorize and read everything from PostgreSQL now; the returned
        stream then needs Redis only."""
        conversation = await ConversationService(self._session).require_owned(
            user=user, conversation_id=conversation_id
        )
        active = await self._messages.get_active(conversation_id=conversation_id)
        leaf = active["id"] if active else conversation["current_message_id"]
        rows = (
            await self._messages.branch(conversation_id=conversation_id, leaf_id=leaf)
            if leaf
            else []
        )
        # The request's session lives as long as the stream: end the read
        # transaction so its connection goes back to the pool now.
        await self._session.commit()
        view = None
        if active is not None and active["status"] in LIVE_STATUSES:
            view = await self._live_view(active["id"])
        return self._events(conversation_id, rows, active, view)

    async def _live_view(self, assistant_id: UUID) -> LiveView | None:
        if self._live is None:
            return None
        view = await self._live.view(assistant_id)
        if view is None and await self._live.owned(assistant_id):
            view = LiveView([], "0-0", 0)  # waiting for a slot, nothing yet
        if view is None or not await self._live.continues(assistant_id, view):
            return None
        return view

    async def _events(
        self,
        conversation_id: UUID,
        rows: Sequence[RowMapping],
        active: RowMapping | None,
        view: LiveView | None,
    ) -> AsyncIterator[BaseEvent]:
        thread_id, run_id = str(conversation_id), str(uuid7())
        yield RunStartedEvent(thread_id=thread_id, run_id=run_id)
        messages: list[dict[str, Any]] = [m for row in rows for m in row["content"]]
        if active is not None:
            yield CustomEvent(
                name=ASSISTANT_EVENT,
                value={
                    "conversationId": thread_id,
                    "userMessageId": str(active["parent_message_id"]),
                    "assistantMessageId": str(active["id"]),
                    "status": active["status"],
                },
            )
        if view is not None:
            messages += view.bundle
        yield MessagesSnapshotEvent.model_validate(
            {"type": EventType.MESSAGES_SNAPSHOT, "messages": messages}
        )
        if active is not None and view is not None and self._live is not None:
            async for event in self._tail(self._live, active["id"], view):
                if event.type == EventType.RUN_ERROR:
                    yield event
                    return
                if event.type == EventType.RUN_FINISHED:
                    yield event.model_copy(update={"run_id": run_id})
                    return
                yield event
        yield RunFinishedEvent(thread_id=thread_id, run_id=run_id)

    @staticmethod
    async def _tail(
        live: LiveStore, assistant_id: UUID, view: LiveView
    ) -> AsyncIterator[BaseEvent]:
        """Events after the watermark up to the turn's end. Stops early when
        nothing arrives and no process owns the turn any more."""
        after = view.watermark
        while True:
            entries = await live.read(assistant_id, after, block_ms=TAIL_BLOCK_MS)
            if not entries and not await live.owned(assistant_id):
                return
            for entry_id, event in entries:
                after = entry_id
                if event.type == EventType.RUN_STARTED:
                    continue  # this stream has its own run
                yield event
                if event.type in (EventType.RUN_FINISHED, EventType.RUN_ERROR):
                    return
