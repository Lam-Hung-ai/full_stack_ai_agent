"""Turns and titles run on the models assigned in the database (QD-34)."""

import pytest
from cryptography.fernet import Fernet
from pydantic import SecretStr

from tests.api.llm.test_admin import ADMIN, KEY, connection, model
from tests.fixtures.ai import scripted
from tests.support.chat import body, history, new_conversation, send


@pytest.fixture(autouse=True)
def encryption_key(monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(
        get_settings(), "llm_encryption_key", SecretStr(Fernet.generate_key().decode())
    )


@pytest.fixture
def db_models(monkeypatch):
    """Stand-ins for the database models, by model key; records each spec."""
    from app.modules.ai import agents, models

    built: dict[str, object] = {}
    specs = []

    def from_spec(spec, **overrides):
        specs.append((spec, overrides))
        return built[spec.key]

    monkeypatch.setattr(models, "from_spec", from_spec)
    agents.get_agent.cache_clear()
    yield built, specs
    agents.get_agent.cache_clear()


async def setup(client, db, make_user, login, keys=("claude", "gpt")):
    root_user = make_user("root@example.com")
    db("UPDATE chat_app.users SET is_superuser = true WHERE id = %s", (root_user.id,))
    root = await login(root_user)
    conn = await connection(client, root)
    ids = [(await model(client, root, conn["id"], key=key))["id"] for key in keys]
    return root, root_user, ids


async def test_turn_runs_on_the_assigned_models_in_order(
    client, db, make_user, login, scripted_model, db_models
):
    env = scripted_model("Từ biến môi trường")
    built, specs = db_models
    root, user, (claude, gpt) = await setup(client, db, make_user, login)
    built["claude"] = scripted("không tới được", fail_after_words=0)
    built["gpt"] = scripted("Trả lời từ gpt")
    await client.put(
        f"{ADMIN}/assignments/chat", json={"model_ids": [claude, gpt]}, headers=root
    )

    conversation_id = await new_conversation(client, user, root)
    status, events = await send(client, conversation_id, root, body("Chào"))

    assert status == 200
    answer = (await history(client, conversation_id, root))["data"][-1]
    assert answer["content"][-1]["content"] == "Trả lời từ gpt"
    assert not env.prompts
    spec, overrides = specs[0]
    assert (spec.provider, spec.model, spec.api_key) == (
        "openrouter",
        "anthropic/claude-sonnet-4.5",
        KEY,
    )
    assert spec.kwargs == {
        "openrouter_api_base": "https://openrouter.ai/api/v1",
        "temperature": 0.2,
    }
    assert overrides == {"streaming": True}

    # Unassigned, the next turn is back on the environment's model.
    await client.put(f"{ADMIN}/assignments/chat", json={"model_ids": []}, headers=root)
    parent = answer["id"]
    await send(client, conversation_id, root, body("Lại", parent=parent))
    assert env.prompts


async def test_a_new_chat_is_named_by_the_title_model(
    client, db, make_user, login, scripted_model, db_models
):
    from app.modules.conversations import titles

    scripted_model("Trả lời")
    built, specs = db_models
    root, user, (claude,) = await setup(client, db, make_user, login, keys=("claude",))
    built["claude"] = scripted("Đường đến Hà Nội")
    await client.put(
        f"{ADMIN}/assignments/title", json={"model_ids": [claude]}, headers=root
    )

    conversation_id = await new_conversation(client, user, root)
    await send(client, conversation_id, root, body("Đi Hà Nội thế nào?"))
    await titles.drain()

    chat = await client.get(f"/api/v1/conversations/{conversation_id}", headers=root)
    assert chat.json()["title"] == "Đường đến Hà Nội"
    assert specs[0][1] == {"streaming": False, "max_tokens": 40}
