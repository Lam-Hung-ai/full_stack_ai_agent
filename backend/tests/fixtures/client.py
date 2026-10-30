"""HTTP client bound to the FastAPI app, backed by the disposable database."""

import fakeredis
import httpx
import pytest


@pytest.fixture
def redis_server():
    """An in-memory Redis for one test; every client made from it shares data."""
    return fakeredis.FakeServer()


@pytest.fixture
def make_redis(redis_server):
    def make():
        return fakeredis.FakeAsyncRedis(server=redis_server)

    return make


@pytest.fixture
async def client(pg, make_redis, monkeypatch):
    from app.common import redis
    from app.main import app

    monkeypatch.setattr(redis, "create_redis", make_redis)
    # ASGITransport does not run the lifespan; the runner lives there.
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as http:
            yield http
