"""Per-IP request limit per minute, shared by every process through Redis.

A brake against password guessing, not an exact quota: a fixed one-minute
window per IP and endpoint group (S9). When Redis cannot answer, each
process falls back to counting in its own memory rather than letting every
request through or refusing them all.
"""

import logging
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from time import monotonic, time

from fastapi import Request

from app.common.exceptions.handlers import DomainError, fail
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60
MAX_TRACKED_CLIENTS = 10_000

_buckets: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()


def reset() -> None:
    """Clear every counter; tests only."""
    _buckets.clear()


def rate_limit(
    name: str, limit: int | None = None
) -> Callable[[Request], Awaitable[None]]:
    """`limit=None` reads AUTH_RATE_LIMIT at call time so tests can change it."""

    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        allowed = get_settings().auth_rate_limit if limit is None else limit
        redis = getattr(request.app.state, "redis", None)
        if redis is not None:
            try:
                window = int(time() // WINDOW_SECONDS)
                key = f"ratelimit:{name}:{client}:{window}"
                async with redis.pipeline(transaction=True) as pipe:
                    pipe.incr(key)
                    pipe.expire(key, WINDOW_SECONDS)
                    count, _ = await pipe.execute()
                if count > allowed:
                    fail(
                        429,
                        "rate_limited",
                        headers={"Retry-After": str(WINDOW_SECONDS)},
                    )
                return
            except DomainError:
                raise
            except Exception:
                logger.warning("Rate limit falls back to memory: Redis unavailable")
        key = (name, client)
        timestamp = monotonic()
        bucket = _buckets.setdefault(key, deque())
        _buckets.move_to_end(key)
        while bucket and bucket[0] < timestamp - WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= allowed:
            fail(429, "rate_limited", headers={"Retry-After": str(WINDOW_SECONDS)})
        bucket.append(timestamp)
        while len(_buckets) > MAX_TRACKED_CLIENTS:
            _buckets.popitem(last=False)

    return dependency
