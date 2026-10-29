"""Synchronous, ordinary-channel proof; not a general replacement for PostgresSaver.

Graph writes go to request-local InMemorySaver. Only an actual paused invocation
is exported by persist_pause(), in the SAME PostgreSQL transaction as the message
status/payload. Full channel versions and ALL write batches are preserved, not
just __interrupt__. A new process falls back to PostgreSQL when reading state.

Tested contract: langgraph 1.2.16, checkpoint 4.3.0, postgres saver 3.2.0,
ordinary state channels, root graphs, durability='exit'. No delta channels,
async API, subgraphs, crash takeover, graph migration or general time travel.
"""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver


class InterruptOnlySaver(InMemorySaver):
    def __init__(self, durable: PostgresSaver):
        super().__init__(serde=durable.serde)
        self.durable = durable
        self.batches: dict[tuple[str, str, str], list[tuple[list, str, str]]] = defaultdict(list)

    @staticmethod
    def key(config: dict) -> tuple[str, str, str]:
        c = config['configurable']
        return c['thread_id'], c.get('checkpoint_ns', ''), c.get('checkpoint_id', '')

    def get_tuple(self, config):
        # No graph object or in-memory saver is reused across HTTP-like workers.
        cached = super().get_tuple(config)
        if cached is not None:
            return cached
        stored = self.durable.get_tuple(config)
        if stored is None:
            return None
        # An interrupt later in THE SAME node can update pending writes without
        # creating another checkpoint. Seed the RAM anchor before applying them.
        parent = stored.parent_config or {'configurable': {
            'thread_id': stored.config['configurable']['thread_id'],
            'checkpoint_ns': stored.config['configurable'].get('checkpoint_ns', ''),
        }}
        super().put(parent, stored.checkpoint, stored.metadata,
                    stored.checkpoint['channel_versions'])
        tasks = defaultdict(list)
        for task_id, channel, value in stored.pending_writes or []:
            tasks[task_id].append((channel, value))
        for task_id, writes in tasks.items():
            super().put_writes(stored.config, writes, task_id)
        return super().get_tuple(config)

    def put(self, config, checkpoint, metadata, new_versions):
        # On resume, unchanged channels may exist only in PostgreSQL. Buffer all
        # materialized versions so the RAM checkpoint can be read independently.
        return super().put(config, checkpoint, metadata, checkpoint['channel_versions'])

    def put_writes(self, config, writes, task_id, task_path=''):
        writes = list(writes)
        self.batches[self.key(config)].append((deepcopy(writes), task_id, task_path))
        return super().put_writes(config, writes, task_id, task_path)

    def persist_pause(self, config: dict) -> dict[str, Any]:
        """Call only AFTER invoke returns interrupts; caller owns DB transaction."""
        item = super().get_tuple(config)
        if item is None or not any(channel == '__interrupt__' for _, channel, _ in item.pending_writes or []):
            raise ValueError('Refusing to persist a checkpoint without a pending interrupt')
        # exit produces a boundary checkpoint: parent is previous persisted pause
        # or None. This proof does not support arbitrary missing ancestor chains.
        parent = item.parent_config or {'configurable': {
            'thread_id': item.config['configurable']['thread_id'],
            'checkpoint_ns': item.config['configurable'].get('checkpoint_ns', ''),
        }}
        saved = self.durable.put(parent, item.checkpoint, item.metadata,
                                 item.checkpoint['channel_versions'])
        for writes, task_id, task_path in self.batches[self.key(saved)]:
            self.durable.put_writes(saved, writes, task_id, task_path)
        return saved
