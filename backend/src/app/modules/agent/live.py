"""Live state of running turns in Redis (architecture §5, storage design §9).

Per assistant row, under one hash tag so a Redis Cluster keeps them together:

- `events`: a Redis Stream of every AG-UI event of the turn, capped in length.
- `view`: the bundle so far and the stream id it covers (the watermark). It is
  written only at safe points, when no step, message or tool call is open, so
  a reader can send the bundle as a snapshot and then the events after the
  watermark without a client seeing an END whose START it never got.
- `owner`: which process runs the turn, kept alive by a heartbeat. No owner
  while the database says running means the turn was orphaned.

Stop requests go to every process on one pub/sub channel; the process that
owns the task cancels it. Redis holds no history: PostgreSQL has the result
once the turn ends, after which these keys expire shortly.
"""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ag_ui.core import BaseEvent, Event
from pydantic import TypeAdapter
from redis.asyncio import Redis

from app.modules.agent.bundle import AguiMessage

logger = logging.getLogger(__name__)

STOP_CHANNEL = "chat:stop"
_EVENT = TypeAdapter(Event)


@dataclass(frozen=True)
class LiveView:
    bundle: list[AguiMessage]
    #: Stream id of the last event the bundle includes; "0-0" before any.
    watermark: str
    #: How many events of the turn the bundle includes.
    seq: int


@dataclass(frozen=True)
class LiveSettings:
    max_events: int = 20_000
    #: How long keys of a running turn live without a new write.
    running_ttl: int = 3_600
    #: How long they stay once the result is in PostgreSQL.
    ended_ttl: int = 120
    owner_ttl: int = 30


def _key(assistant_id: UUID | str, part: str) -> str:
    return f"chat:{{{assistant_id}}}:{part}"


def _text(value: Any) -> str:
    return value.decode() if isinstance(value, bytes) else str(value)


def _field(fields: dict[Any, Any], name: str) -> str:
    """A stream entry field, whether the client decodes responses or not."""
    return _text(fields.get(name, fields.get(name.encode())))


def encode_event(event: BaseEvent) -> str:
    return event.model_dump_json(by_alias=True, exclude_none=True)


def decode_event(data: str) -> BaseEvent:
    return _EVENT.validate_json(data)


class LiveStore:
    def __init__(self, redis: Redis, settings: LiveSettings | None = None) -> None:
        self.redis = redis
        self.settings = settings or LiveSettings()

    async def append(self, assistant_id: UUID, seq: int, event: BaseEvent) -> str:
        """Add the turn's `seq`-th event (1-based); returns its stream id."""
        key = _key(assistant_id, "events")
        async with self.redis.pipeline(transaction=False) as pipe:
            pipe.xadd(
                key,
                {"e": encode_event(event), "n": seq},
                maxlen=self.settings.max_events,
                approximate=True,
            )
            pipe.expire(key, self.settings.running_ttl)
            entry_id, _ = await pipe.execute()
        return _text(entry_id)

    async def save_view(self, assistant_id: UUID, view: LiveView) -> None:
        key = _key(assistant_id, "view")
        async with self.redis.pipeline(transaction=False) as pipe:
            pipe.hset(
                key,
                mapping={
                    "bundle": json.dumps(view.bundle),
                    "watermark": view.watermark,
                    "seq": view.seq,
                },
            )
            pipe.expire(key, self.settings.running_ttl)
            await pipe.execute()

    async def view(self, assistant_id: UUID) -> LiveView | None:
        """The latest safe-point view, or one at the very start when the turn
        has events but no safe point yet. None when nothing is live."""
        data = await self.redis.hgetall(_key(assistant_id, "view"))
        if data:
            fields = {_text(k): _text(v) for k, v in data.items()}
            return LiveView(
                json.loads(fields["bundle"]), fields["watermark"], int(fields["seq"])
            )
        if await self.redis.exists(_key(assistant_id, "events")):
            return LiveView([], "0-0", 0)
        return None

    async def continues(self, assistant_id: UUID, view: LiveView) -> bool:
        """Whether every event after the view is still in the stream. Trimming
        may have dropped some; replaying the rest would then leave a gap
        (architecture §5: never join a suffix to a prefix missing a part)."""
        first: Any = await self.redis.xrange(_key(assistant_id, "events"), count=1)
        if not first:
            # Nothing published yet (waiting for a slot), or expired.
            return view.seq == 0
        return int(_field(first[0][1], "n")) <= view.seq + 1

    async def read(
        self, assistant_id: UUID, after: str, *, block_ms: int
    ) -> list[tuple[str, BaseEvent]]:
        response: Any = await self.redis.xread(
            {_key(assistant_id, "events"): after}, block=block_ms, count=500
        )
        return [
            (_text(entry_id), decode_event(_field(fields, "e")))
            for _, entries in response or []
            for entry_id, fields in entries
        ]

    async def reset(self, assistant_id: UUID) -> None:
        """Forget an earlier run of this assistant (a pause before a resume):
        its ending must not be replayed as the new run's."""
        await self.redis.delete(
            _key(assistant_id, "events"), _key(assistant_id, "view")
        )

    async def end(self, assistant_id: UUID) -> None:
        async with self.redis.pipeline(transaction=False) as pipe:
            for part in ("events", "view"):
                pipe.expire(_key(assistant_id, part), self.settings.ended_ttl)
            pipe.delete(_key(assistant_id, "owner"))
            await pipe.execute()

    async def claim(self, assistant_id: UUID, process_id: str) -> None:
        await self.redis.set(
            _key(assistant_id, "owner"), process_id, ex=self.settings.owner_ttl
        )

    async def owned(self, assistant_id: UUID) -> bool:
        return bool(await self.redis.exists(_key(assistant_id, "owner")))

    async def request_stop(self, assistant_id: UUID) -> None:
        await self.redis.publish(STOP_CHANNEL, str(assistant_id))

    async def stop_requests(self) -> AsyncIterator[UUID]:
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(STOP_CHANNEL)
            async for message in pubsub.listen():
                if message.get("type") != "message":
                    continue
                try:
                    yield UUID(_text(message["data"]))
                except ValueError:
                    logger.warning("Ignoring malformed stop request %r", message)
