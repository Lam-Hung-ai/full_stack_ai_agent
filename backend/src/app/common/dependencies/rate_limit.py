"""Per-IP request limit per minute, kept in process memory.

A brake against password guessing, not an exact quota: with several worker
processes each one counts separately. Moves to Redis when the backend runs
more than one process (sprint S9). Each endpoint group has its own bucket.
"""

from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from time import monotonic

from fastapi import Request

from app.common.exceptions.handlers import fail
from app.config.settings import get_settings

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
        key = (name, request.client.host if request.client else "unknown")
        timestamp = monotonic()
        bucket = _buckets.setdefault(key, deque())
        _buckets.move_to_end(key)
        while bucket and bucket[0] < timestamp - WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= (get_settings().auth_rate_limit if limit is None else limit):
            fail(429, "rate_limited")
        bucket.append(timestamp)
        while len(_buckets) > MAX_TRACKED_CLIENTS:
            _buckets.popitem(last=False)

    return dependency
