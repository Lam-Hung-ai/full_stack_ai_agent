"""HTTP client bound to the FastAPI app, backed by the disposable database."""

import httpx
import pytest


@pytest.fixture
async def client(pg):
    from app.main import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        yield http
