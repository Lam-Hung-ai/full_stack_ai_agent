"""System administration of LLM connections, models and assignments (QD-34)."""

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

ADMIN = "/api/v1/admin/llm"
KEY = "sk-or-v1-secret-abcd"


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch):
    from app.config.settings import get_settings

    key = Fernet.generate_key().decode()
    monkeypatch.setattr(get_settings(), "llm_encryption_key", SecretStr(key))
    return key


@pytest.fixture
def superuser(db, make_user, login):
    async def make(email="root@example.com"):
        user = make_user(email)
        db("UPDATE chat_app.users SET is_superuser = true WHERE id = %s", (user.id,))
        return await login(user)

    return make


async def connection(client, headers, **overrides):
    body = {
        "key": "openrouter",
        "name": "OpenRouter",
        "provider": "openrouter",
        "client_params": {"openrouter_api_base": "https://openrouter.ai/api/v1"},
        "api_key": KEY,
        **overrides,
    }
    response = await client.post(f"{ADMIN}/connections", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def model(client, headers, connection_id, key="claude", **overrides):
    body = {
        "key": key,
        "connection_id": connection_id,
        "model": "anthropic/claude-sonnet-4.5",
        "name": key.title(),
        "params": {"temperature": 0.2},
        **overrides,
    }
    response = await client.post(f"{ADMIN}/models", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_only_superusers_reach_the_admin_api(client, make_user, login, superuser):
    member = await login(make_user("an@example.com"))
    for path in ("/providers", "/connections", "/models", "/assignments"):
        response = await client.get(f"{ADMIN}{path}", headers=member)
        assert response.status_code == 403, path
        assert response.json()["error"]["code"] == "superuser_required"
    me = await client.get("/api/v1/users/me", headers=member)
    assert me.json()["is_superuser"] is False

    root = await superuser()
    assert (await client.get("/api/v1/users/me", headers=root)).json()["is_superuser"]
    providers = (await client.get(f"{ADMIN}/providers", headers=root)).json()["data"]
    openrouter = next(p for p in providers if p["provider"] == "openrouter")
    assert openrouter == {
        "provider": "openrouter",
        "package": "langchain_openrouter",
        "installed": True,
    }


async def test_api_key_is_encrypted_and_never_returned(
    client, db, superuser, encryption_key
):
    root = await superuser()
    created = await connection(client, root)

    assert created["has_api_key"] is True
    assert created["api_key_hint"] == "abcd"
    assert KEY not in str(created)
    (row,) = db(
        "SELECT api_key_ciphertext FROM chat_app.llm_connections WHERE id = %s",
        (created["id"],),
    )
    assert KEY not in row["api_key_ciphertext"]
    assert Fernet(encryption_key).decrypt(row["api_key_ciphertext"].encode()) == (
        KEY.encode()
    )
    listed = (await client.get(f"{ADMIN}/connections", headers=root)).text
    assert KEY not in listed

    # Omitted keeps the key, null clears it.
    renamed = await client.patch(
        f"{ADMIN}/connections/{created['id']}", json={"name": "OR"}, headers=root
    )
    assert renamed.json()["has_api_key"] is True
    cleared = await client.patch(
        f"{ADMIN}/connections/{created['id']}", json={"api_key": None}, headers=root
    )
    assert cleared.json()["has_api_key"] is False
    assert cleared.json()["api_key_hint"] is None


async def test_settings_and_providers_are_checked(client, superuser, monkeypatch):
    root = await superuser()
    url = f"{ADMIN}/connections"
    base = {"key": "x", "name": "X", "provider": "openrouter"}

    unknown = await client.post(url, json={**base, "provider": "nope"}, headers=root)
    assert unknown.json()["error"]["code"] == "unknown_provider"
    missing = await client.post(url, json={**base, "provider": "openai"}, headers=root)
    assert missing.status_code == 422
    assert missing.json()["error"]["code"] == "provider_not_installed"
    secret = await client.post(
        url,
        json={**base, "client_params": {"default_headers": {"X-Api-Key": "s"}}},
        headers=root,
    )
    assert secret.json()["error"]["code"] == "secret_in_settings"
    assert secret.json()["error"]["details"]["names"] == ["default_headers.X-Api-Key"]

    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "llm_encryption_key", None)
    no_key = await client.post(url, json={**base, "api_key": "k"}, headers=root)
    assert no_key.status_code == 503
    assert no_key.json()["error"]["code"] == "llm_encryption_unavailable"


async def test_assigned_models_cannot_be_deleted(client, superuser):
    root = await superuser()
    conn = await connection(client, root)
    primary = await model(client, root, conn["id"], key="claude")
    fallback = await model(client, root, conn["id"], key="gpt")

    duplicate = await client.post(
        f"{ADMIN}/models",
        json={"key": "claude", "connection_id": conn["id"], "model": "m", "name": "M"},
        headers=root,
    )
    assert duplicate.status_code == 409
    assigned = await client.put(
        f"{ADMIN}/assignments/chat",
        json={"model_ids": [primary["id"], fallback["id"]]},
        headers=root,
    )
    assert assigned.json()["model_ids"] == [primary["id"], fallback["id"]]
    listed = (await client.get(f"{ADMIN}/assignments", headers=root)).json()["data"]
    assert {a["purpose"]: a["model_ids"] for a in listed} == {
        "chat": [primary["id"], fallback["id"]],
        "title": [],
    }
    unknown = await client.put(
        f"{ADMIN}/assignments/summary", json={"model_ids": []}, headers=root
    )
    assert unknown.status_code == 404

    in_use = await client.delete(f"{ADMIN}/models/{primary['id']}", headers=root)
    assert in_use.status_code == 409
    assert in_use.json()["error"]["code"] == "model_in_use"
    busy = await client.delete(f"{ADMIN}/connections/{conn['id']}", headers=root)
    assert busy.json()["error"]["code"] == "connection_in_use"

    await client.put(f"{ADMIN}/assignments/chat", json={"model_ids": []}, headers=root)
    gone = await client.delete(f"{ADMIN}/models/{primary['id']}", headers=root)
    assert gone.status_code == 204


def test_langchain_still_lists_its_providers():
    # The provider list reads a private LangChain table; fail loudly if it moves.
    from app.modules.llm.service import providers

    assert providers()["openrouter"] == "langchain_openrouter"
