"""Pausing for the user and resuming from the stored checkpoint (phase 4)."""

import asyncio

import pytest
from langchain_core.messages import AIMessage

from tests.support.chat import body, history, new_conversation, send, stream_turn

ASK_ROOM = AIMessage(
    content="",
    tool_calls=[
        {"name": "ask_user", "args": {"question": "Phòng nào?"}, "id": "call_ask"}
    ],
)
ASK_TIME = AIMessage(
    content="",
    tool_calls=[
        {"name": "ask_user", "args": {"question": "Mấy giờ?"}, "id": "call_time"}
    ],
)
CLOCK_CALL = AIMessage(
    content="", tool_calls=[{"name": "get_current_time", "args": {}, "id": "call_1"}]
)


def resume_url(conversation_id, message_id):
    return f"/api/v1/conversations/{conversation_id}/messages/{message_id}/resume"


async def resume(client, conversation_id, message_id, headers, interrupt_id, payload):
    return await stream_turn(
        client,
        resume_url(conversation_id, message_id),
        headers,
        {
            "resume": [
                {"interruptId": interrupt_id, "status": "resolved", "payload": payload}
            ]
        },
    )


def waiting(assistant):
    return [
        m["content"]
        for m in assistant["content"]
        if m["role"] == "activity" and m["content"]["status"] == "waiting"
    ]


def checkpoints(db, thread_id):
    (row,) = db(
        "SELECT count(*) AS n FROM langgraph_checkpoints.checkpoints "
        "WHERE thread_id = %s",
        (str(thread_id),),
    )
    return row["n"]


@pytest.fixture
def needs_approval(monkeypatch):
    """Make get_current_time ask for approval (TOOLS_REQUIRING_APPROVAL)."""
    from app.config.settings import get_settings
    from app.modules.agent import graph

    monkeypatch.setattr(
        get_settings(), "tools_requiring_approval", ["get_current_time"]
    )
    graph.get_agent.cache_clear()


async def paused_turn(client, user, headers, text="Đặt phòng họp"):
    conversation_id = await new_conversation(client, user, headers)
    status, events = await send(client, conversation_id, headers, body(text))
    assert status == 200
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    return conversation_id, assistant, events


async def test_question_pauses_then_resumes_after_a_restart(
    client, db, make_user, login, scripted_model
):
    model = scripted_model(ASK_ROOM, "Đã đặt phòng A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant, events = await paused_turn(client, user, headers)

    custom = [e["value"]["status"] for e in events if e["type"] == "CUSTOM"]
    assert custom == ["running", "requires_action"]
    assert events[-1]["type"] == "RUN_FINISHED"
    assert events[-1]["outcome"]["type"] == "interrupt"
    assert any(e["type"] == "ACTIVITY_SNAPSHOT" for e in events)
    assert assistant["status"] == "requires_action"
    (question,) = waiting(assistant)
    assert question["kind"] == "user_question"
    assert question["question"] == "Phòng nào?"
    assert checkpoints(db, assistant["id"]) == 1

    # A new process: nothing in memory survives but the database.
    from app.main import app
    from app.modules.agent import graph
    from app.modules.agent.agui import turn_agent
    from app.modules.agent.runner import Runner

    app.state.runner = Runner(agent_factory=turn_agent, max_concurrent=2)
    graph.get_agent.cache_clear()

    status, events = await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        question["interrupt_id"],
        {"answer": " Phòng A "},
    )
    assert status == 200
    custom = [e["value"] for e in events if e["type"] == "CUSTOM"]
    assert custom[-1]["status"] == "completed"
    assert custom[-1]["assistantMessageId"] == assistant["id"]
    # The model got the answer as the result of its ask_user call.
    tool_results = [m for m in model.prompts[-1] if m.type == "tool"]
    assert [m.content for m in tool_results] == ["Phòng A"]

    saved = (await history(client, conversation_id, headers))["data"]
    assert len(saved) == 2
    final = saved[-1]
    assert final["id"] == assistant["id"] and final["status"] == "completed"
    roles = [m["role"] for m in final["content"]]
    assert roles == ["assistant", "activity", "tool", "assistant"]
    answered = final["content"][1]["content"]
    assert answered["status"] == "answered"
    assert answered["response"] == "Phòng A"
    assert answered["actor_id"] == str(user.id)
    assert final["content"][-1]["content"] == "Đã đặt phòng A"
    (row,) = db("SELECT metadata FROM chat_app.messages WHERE id = %s", (final["id"],))
    assert "pending_action" not in row["metadata"]
    assert row["metadata"]["actions"][0]["status"] == "answered"
    # Nothing resumes a finished turn: its checkpoint went with it (RR-16).
    assert checkpoints(db, assistant["id"]) == 0


async def test_an_ordinary_turn_stores_no_checkpoint(
    client, db, make_user, login, scripted_model
):
    scripted_model("Xin chào")
    user = make_user("an@example.com")
    headers = await login(user)
    _, assistant, _ = await paused_turn(client, user, headers, "Chào")
    assert assistant["status"] == "completed"
    assert checkpoints(db, assistant["id"]) == 0


async def test_two_questions_in_one_turn(client, make_user, login, scripted_model):
    model = scripted_model(ASK_ROOM, ASK_TIME, "Phòng A lúc 9 giờ")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant, _ = await paused_turn(client, user, headers)

    (first,) = waiting(assistant)
    await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        first["interrupt_id"],
        {"answer": "Phòng A"},
    )
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    assert assistant["status"] == "requires_action"
    (second,) = waiting(assistant)
    assert second["question"] == "Mấy giờ?"
    assert second["action_id"] != first["action_id"]

    status, _ = await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        second["interrupt_id"],
        {"answer": "9 giờ"},
    )
    assert status == 200
    final = (await history(client, conversation_id, headers))["data"][-1]
    assert final["status"] == "completed"
    answers = [
        m["content"]["response"] for m in final["content"] if m["role"] == "activity"
    ]
    assert answers == ["Phòng A", "9 giờ"]
    assert [m.content for m in model.prompts[-1] if m.type == "tool"] == [
        "Phòng A",
        "9 giờ",
    ]


async def test_answers_are_checked_before_the_claim(
    client, make_user, login, scripted_model
):
    scripted_model(ASK_ROOM, "Xong")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant, _ = await paused_turn(client, user, headers)
    (question,) = waiting(assistant)
    args = (client, conversation_id, assistant["id"], headers)

    status, error = await resume(*args, question["interrupt_id"], {"answer": "  "})
    assert (status, error["error"]["code"]) == (422, "empty_answer")
    status, error = await resume(*args, "not-an-interrupt", {"answer": "A"})
    assert (status, error["error"]["code"]) == (409, "stale_interrupt")
    status, error = await send(
        client, conversation_id, headers, body("Câu khác", assistant["id"])
    )
    assert (status, error["error"]["code"]) == (409, "invalid_parent")
    still = (await history(client, conversation_id, headers))["data"][-1]
    assert still["status"] == "requires_action"

    await resume(*args, question["interrupt_id"], {"answer": "A"})
    status, error = await resume(*args, question["interrupt_id"], {"answer": "B"})
    assert (status, error["error"]["code"]) == (409, "not_waiting")


async def test_concurrent_answers_claim_once(client, make_user, login, scripted_model):
    scripted_model(ASK_ROOM, "Xong")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant, _ = await paused_turn(client, user, headers)
    (question,) = waiting(assistant)
    args = (client, conversation_id, assistant["id"], headers, question["interrupt_id"])

    results = await asyncio.gather(
        resume(*args, {"answer": "A"}), resume(*args, {"answer": "B"})
    )
    assert sorted(status for status, _ in results) == [200, 409]


async def test_tool_approval(client, make_user, login, scripted_model, needs_approval):
    scripted_model(CLOCK_CALL, "Bây giờ là sáng", CLOCK_CALL, "Không xem giờ")
    user = make_user("an@example.com")
    headers = await login(user)

    conversation_id, assistant, _ = await paused_turn(client, user, headers, "Mấy giờ?")
    (approval,) = waiting(assistant)
    assert approval["kind"] == "tool_approval"
    assert approval["tool_name"] == "get_current_time"
    assert not [m for m in assistant["content"] if m["role"] == "tool"]
    await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        approval["interrupt_id"],
        {"approved": True},
    )
    final = (await history(client, conversation_id, headers))["data"][-1]
    (result,) = [m for m in final["content"] if m["role"] == "tool"]
    assert result["content"].startswith("20")  # an ISO timestamp
    assert final["status"] == "completed"

    conversation_id, assistant, _ = await paused_turn(client, user, headers, "Mấy giờ?")
    (approval,) = waiting(assistant)
    await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        approval["interrupt_id"],
        {"approved": False},
    )
    final = (await history(client, conversation_id, headers))["data"][-1]
    (result,) = [m for m in final["content"] if m["role"] == "tool"]
    assert result["content"] == "The user declined to run this tool."
    assert final["status"] == "completed"


async def test_grant_revoked_while_waiting_refuses_the_approval(
    client, db, make_user, make_organization, login, scripted_model, needs_approval
):
    scripted_model(CLOCK_CALL, "Xong")
    owner = make_user("owner@example.com")
    organization_id, workspace_id = make_organization(owner)
    headers = await login(owner)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    conversation_id = created.json()["id"]
    await send(client, conversation_id, headers, body("Mấy giờ?"))
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    (approval,) = waiting(assistant)

    db(
        "DELETE FROM chat_app.role_permissions rp "
        "USING chat_app.organization_roles r, chat_app.permissions p "
        "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
        "AND r.organization_id = %s AND p.resource = 'tool'",
        (organization_id,),
    )
    status, error = await resume(
        client,
        conversation_id,
        assistant["id"],
        headers,
        approval["interrupt_id"],
        {"approved": True},
    )
    assert (status, error["error"]["code"]) == (403, "permission_denied")
    still = (await history(client, conversation_id, headers))["data"][-1]
    assert still["status"] == "requires_action"


async def test_stop_cancels_a_waiting_turn(
    client, db, make_user, login, scripted_model
):
    scripted_model(ASK_ROOM, "Câu mới")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id, assistant, _ = await paused_turn(client, user, headers)

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/messages/{assistant['id']}/stop",
        headers=headers,
    )
    assert response.json() == {"id": assistant["id"], "status": "cancelled"}
    final = (await history(client, conversation_id, headers))["data"][-1]
    activity = next(m for m in final["content"] if m["role"] == "activity")
    assert activity["content"]["status"] == "cancelled"
    (row,) = db("SELECT metadata FROM chat_app.messages WHERE id = %s", (final["id"],))
    assert "pending_action" not in row["metadata"]
    assert checkpoints(db, assistant["id"]) == 0

    # The unanswered ask_user call is left out of the next turn's context.
    status, _ = await send(
        client, conversation_id, headers, body("Thôi, hỏi khác", assistant["id"])
    )
    assert status == 200


async def test_a_failed_pause_write_rolls_the_checkpoint_back(
    client, db, make_user, login, scripted_model, monkeypatch
):
    from app.modules.conversations.repository import MessageRepository

    original = MessageRepository.set_status

    async def failing(self, *, message_id, status, **kwargs):
        if status == "requires_action":
            raise RuntimeError("disk full")
        return await original(self, message_id=message_id, status=status, **kwargs)

    monkeypatch.setattr(MessageRepository, "set_status", failing)
    scripted_model(ASK_ROOM)
    user = make_user("an@example.com")
    headers = await login(user)
    _, assistant, events = await paused_turn(client, user, headers)

    assert events[-1]["code"] == "persist_failed"
    assert assistant["status"] == "running"  # no recovery (RR-01)
    assert checkpoints(db, assistant["id"]) == 0
