import asyncio
from collections.abc import AsyncIterator

from ag_ui.core import BaseEvent


class RunStream:
    """Ordered events of one turn, readable by any number of subscribers."""

    def __init__(self) -> None:
        self._events: list[BaseEvent] = []
        self._closed = False
        self._changed = asyncio.Condition()

    async def publish(self, event: BaseEvent) -> None:
        async with self._changed:
            self._events.append(event)
            self._changed.notify_all()

    async def close(self) -> None:
        async with self._changed:
            self._closed = True
            self._changed.notify_all()

    async def subscribe(self) -> AsyncIterator[BaseEvent]:
        position = 0
        while True:
            async with self._changed:
                await self._changed.wait_for(
                    lambda: position < len(self._events) or self._closed
                )
                batch = self._events[position:]
                position = len(self._events)
                closed = self._closed
            for event in batch:
                yield event
            if closed and position == len(self._events):
                return
