"""Shared Redis client, created in the app lifespan."""

from redis.asyncio import Redis

from app.config.settings import get_settings


def create_redis() -> Redis:
    """Tests replace this with an in-memory fake."""
    return Redis.from_url(get_settings().redis_url)
