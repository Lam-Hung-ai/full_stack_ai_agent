"""Request limits per client IP (or per user), shared by every process
through Redis.

A brake against password guessing and mail flooding, not an exact quota: a
fixed window per client and endpoint group (S9). The client IP is
`request.client`, which uvicorn takes from `X-Forwarded-For` only for proxies
listed in `--forwarded-allow-ips` (van-hanh.md §3). When Redis cannot answer,
each process falls back to counting in its own memory rather than letting
every request through or refusing them all.
"""

import logging
from collections import OrderedDict, deque
from collections.abc import Awaitable, Callable
from time import monotonic, time

from fastapi import Request

from app.common.dependencies.auth import CurrentUser
from app.common.exceptions.handlers import DomainError, fail
from app.config.settings import get_settings

logger = logging.getLogger(__name__)

WINDOW_SECONDS = 60
#: Session reads and refreshes per IP and minute; several tabs and users
#: behind one NAT share it.
SESSION_RATE_LIMIT = 300
MAX_TRACKED_CLIENTS = 10_000

_buckets: OrderedDict[tuple[str, str], deque[float]] = OrderedDict()


def reset() -> None:
    """Clear every counter; tests only."""
    _buckets.clear()


def rate_limit(
    name: str, limit: int | None = None, *, window: int = WINDOW_SECONDS
) -> Callable[[Request], Awaitable[None]]:
    """Per client IP. `limit=None` reads AUTH_RATE_LIMIT at call time so tests
    can change it."""

    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        await _hit(request, name, client, limit, window)

    return dependency


def user_rate_limit(
    name: str, limit: int, *, window: int
) -> Callable[[Request, CurrentUser], Awaitable[None]]:
    """Per signed-in user, wherever the requests come from."""

    async def dependency(request: Request, user: CurrentUser) -> None:
        await _hit(request, name, f"user:{user.id}", limit, window)

    return dependency


async def _hit(
    request: Request, name: str, client: str, limit: int | None, window: int
) -> None:
    allowed = get_settings().auth_rate_limit if limit is None else limit
    retry = {"Retry-After": str(window)}
    redis = getattr(request.app.state, "redis", None)
    if redis is not None:
        try:
            key = f"ratelimit:{name}:{client}:{int(time() // window)}"
            async with redis.pipeline(transaction=True) as pipe:
                pipe.incr(key)
                pipe.expire(key, window)
                count, _ = await pipe.execute()
            if count > allowed:
                fail(429, "rate_limited", headers=retry)
            return
        except DomainError:
            raise
        except Exception:
            logger.warning("Rate limit falls back to memory: Redis unavailable")
    key = (name, client)
    timestamp = monotonic()
    bucket = _buckets.setdefault(key, deque())
    _buckets.move_to_end(key)
    while bucket and bucket[0] < timestamp - window:
        bucket.popleft()
    if len(bucket) >= allowed:
        fail(429, "rate_limited", headers=retry)
    bucket.append(timestamp)
    while len(_buckets) > MAX_TRACKED_CLIENTS:
        _buckets.popitem(last=False)
