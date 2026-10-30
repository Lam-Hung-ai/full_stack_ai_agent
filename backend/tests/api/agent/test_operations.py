"""Operations (S9): turn logs, backpressure, shared rate limits, tracing."""

import logging

from tests.support.chat import body, history, new_conversation, send


async def test_each_turn_logs_one_line_without_content(
    client, make_user, login, scripted_model, caplog
):
    scripted_model("Câu trả lời bí mật")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    with caplog.at_level(logging.INFO, logger="app.modules.agent.runner"):
        await send(client, conversation_id, headers, body("Câu hỏi riêng tư"))
    (record,) = [r for r in caplog.records if r.getMessage() == "Assistant turn ended"]
    fields = record.fields
    assert fields["status"] == "completed"
    assert fields["conversation_id"] == conversation_id
    assert fields["user_id"] == str(user.id)
    assert fields["duration_ms"] >= 0
    line = repr(record.__dict__)
    assert "riêng tư" not in line and "bí mật" not in line


async def test_a_full_runner_refuses_new_turns_with_retry_after(
    client, make_user, login, scripted_model
):
    from app.main import app

    scripted_model("ok")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    runner = app.state.runner
    capacity = runner._capacity
    runner._capacity = 0
    try:
        status, error = await send(client, conversation_id, headers, body("Câu hỏi"))
    finally:
        runner._capacity = capacity
    assert (status, error["error"]["code"]) == (503, "server_busy")
    # Nothing was saved: the same question can be sent again.
    assert (await history(client, conversation_id, headers))["data"] == []
    status, _ = await send(client, conversation_id, headers, body("Câu hỏi"))
    assert status == 200


async def test_rate_limit_counts_in_redis(client, make_redis, monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "auth_rate_limit", 2)
    codes = []
    for _ in range(3):
        response = await client.post(
            "/api/v1/auth/login", json={"email": "x@example.com", "password": "x"}
        )
        codes.append(response.status_code)
    assert codes == [401, 401, 429]
    assert response.headers["retry-after"] == "60"
    keys = [key async for key in make_redis().scan_iter("ratelimit:auth:*")]
    assert len(keys) == 1


def test_tracing_is_off_without_keys_and_on_with_them(monkeypatch):
    from app.config.settings import get_settings
    from app.modules.agent import tracing

    tracing._client.cache_clear()
    assert tracing.tracing_config({"conversation_id": "c"}) is None

    monkeypatch.setattr(get_settings(), "langfuse_public_key", "pk-lf-test")
    monkeypatch.setattr(get_settings(), "langfuse_secret_key", _secret("sk-lf-test"))
    monkeypatch.setattr(get_settings(), "langfuse_host", "http://127.0.0.1:9")
    tracing._client.cache_clear()
    try:
        config = tracing.tracing_config(
            {"conversation_id": "c1", "user_id": "u1", "assistant_id": "a1"}
        )
        assert config is not None
        assert config["metadata"]["langfuse_session_id"] == "c1"
        assert config["metadata"]["langfuse_user_id"] == "u1"
        callbacks = config["callbacks"]
        assert isinstance(callbacks, list)
        assert type(callbacks[0]).__name__ == "LangchainCallbackHandler"
    finally:
        tracing.flush_traces()
        tracing._client.cache_clear()


def _secret(value):
    from pydantic import SecretStr

    return SecretStr(value)


async def test_user_rate_limit_counts_per_user_not_per_ip():
    """Invitation letters are bounded per sender, whatever the IP."""
    from types import SimpleNamespace
    from uuid import uuid4

    import pytest
    from starlette.requests import Request

    from app.common.dependencies import rate_limit
    from app.common.dependencies.auth import Principal
    from app.common.exceptions.handlers import DomainError

    rate_limit.reset()
    limit = rate_limit.user_rate_limit("letters", 2, window=3600)

    def principal():
        return Principal(uuid4(), uuid4(), "An", "an@example.com", False)

    def request(ip):
        app = SimpleNamespace(state=SimpleNamespace())
        return Request({"type": "http", "client": (ip, 1), "app": app, "headers": []})

    sender, other = principal(), principal()
    await limit(request("10.0.0.1"), sender)
    await limit(request("10.0.0.2"), sender)
    with pytest.raises(DomainError) as refused:
        await limit(request("10.0.0.3"), sender)
    assert refused.value.headers == {"Retry-After": "3600"}
    await limit(request("10.0.0.3"), other)
