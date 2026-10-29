"""Async sibling of the sync proof. Ordinary root graphs, durability='exit' only."""
from collections import defaultdict
from copy import deepcopy

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


class AsyncInterruptOnlySaver(InMemorySaver):
    def __init__(self, durable: AsyncPostgresSaver):
        super().__init__(serde=durable.serde)
        self.durable = durable
        self.batches = defaultdict(list)

    @staticmethod
    def key(config):
        c = config['configurable']
        return c['thread_id'], c.get('checkpoint_ns', ''), c.get('checkpoint_id', '')

    async def aget_tuple(self, config):
        cached = InMemorySaver.get_tuple(self, config)
        if cached is not None:
            return cached
        stored = await self.durable.aget_tuple(config)
        if stored is None:
            return None
        parent = stored.parent_config or {'configurable': {
            'thread_id': stored.config['configurable']['thread_id'],
            'checkpoint_ns': stored.config['configurable'].get('checkpoint_ns', ''),
        }}
        InMemorySaver.put(self, parent, stored.checkpoint, stored.metadata,
                          stored.checkpoint['channel_versions'])
        tasks = defaultdict(list)
        for task_id, channel, value in stored.pending_writes or []:
            tasks[task_id].append((channel, value))
        for task_id, writes in tasks.items():
            InMemorySaver.put_writes(self, stored.config, writes, task_id)
        return InMemorySaver.get_tuple(self, config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        return InMemorySaver.put(self, config, checkpoint, metadata,
                                 checkpoint['channel_versions'])

    async def aput_writes(self, config, writes, task_id, task_path=''):
        writes = list(writes)
        self.batches[self.key(config)].append((deepcopy(writes), task_id, task_path))
        InMemorySaver.put_writes(self, config, writes, task_id, task_path)

    async def apersist_pause(self, config):
        item = InMemorySaver.get_tuple(self, config)
        if item is None or not any(c == '__interrupt__' for _, c, _ in item.pending_writes or []):
            raise ValueError('Cannot persist without a pending interrupt')
        parent = item.parent_config or {'configurable': {
            'thread_id': item.config['configurable']['thread_id'],
            'checkpoint_ns': item.config['configurable'].get('checkpoint_ns', ''),
        }}
        saved = await self.durable.aput(parent, item.checkpoint, item.metadata,
                                       item.checkpoint['channel_versions'])
        for writes, task_id, task_path in self.batches[self.key(saved)]:
            await self.durable.aput_writes(saved, writes, task_id, task_path)
        return saved
