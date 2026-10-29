"""Error contract and request id (backend/AGENTS.md section 16)."""

from fastapi import APIRouter

from app.common.exceptions.handlers import fail


async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_unknown_route_uses_error_format(client):
    response = await client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["request_id"] == response.headers["x-request-id"]


async def test_request_id_is_echoed_when_safe(client):
    response = await client.get("/health", headers={"X-Request-Id": "trace-1"})
    assert response.headers["x-request-id"] == "trace-1"


async def test_unsafe_request_id_is_replaced(client):
    response = await client.get("/health", headers={"X-Request-Id": "bad id\nforged"})
    assert response.headers["x-request-id"] != "bad id\nforged"
    assert len(response.headers["x-request-id"]) == 32


async def test_validation_error_lists_locations_only(client):
    response = await client.post("/agent", json={"threadId": 1})
    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert all(set(item) == {"location", "type"} for item in error["details"])


async def test_domain_and_unhandled_errors(client):
    from app.main import app

    router = APIRouter()

    @router.get("/__test/domain")
    async def domain():
        fail(409, "demo_conflict", "Xung đột", {"version": 2})

    @router.get("/__test/crash")
    async def crash():
        raise RuntimeError("secret internals")

    app.include_router(router)
    try:
        conflict = await client.get("/__test/domain")
        assert conflict.status_code == 409
        assert conflict.json()["error"] == {
            "code": "demo_conflict",
            "message": "Xung đột",
            "details": {"version": 2},
            "request_id": conflict.headers["x-request-id"],
        }

        crashed = await client.get("/__test/crash")
        assert crashed.status_code == 500
        assert crashed.json()["error"]["code"] == "internal_error"
        assert "secret" not in crashed.text
    finally:
        app.router.routes[:] = [
            route
            for route in app.router.routes
            if not getattr(route, "path", "").startswith("/__test")
        ]
