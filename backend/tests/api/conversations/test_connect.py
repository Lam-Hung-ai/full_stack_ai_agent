"""Connect: snapshot, then the running turn from Redis (API §6, S5)."""

import asyncio
import json

from langchain_core.messages import AIMessage

from tests.support.chat import body, history, new_conversation, send, stream_turn

LONG = " ".join(f"từ{i}" for i in range(40))
CLOCK_CALL = AIMessage(
    content="", tool_calls=[{"name": "get_current_time", "args": {}, "id": "call_1"}]
)
ASK = AIMessage(
    content="",
    tool_calls=[{"name": "ask_user", "args": {"question": "Phòng?"}, "id": "c_ask"}],
)


async def connect(client, conversation_id, headers):
    return await stream_turn(
        client, f"/api/v1/conversations/{conversation_id}/connect", headers
    )


def snapshot_of(events):
    return next(e["messages"] for e in events if e["type"] == "MESSAGES_SNAPSHOT")


def text_seen(events):
    """What a client shows for the answer: snapshot text, then live deltas."""
    snapshot = "".join(
        m.get("content") or "" for m in snapshot_of(events) if m["role"] == "assistant"
    )
    deltas = "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")
    return snapshot + deltas


async def wait_for(predicate, timeout=5.0):
    for _ in range(int(timeout / 0.01)):
        if predicate():
            return
        await asyncio.sleep(0.01)
    raise AssertionError("condition not met")


async def test_connect_without_a_running_turn_sends_the_saved_branch(
    client, make_user, login, scripted_model
):
    scripted_model("Xin chào")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Chào"))

    status, events = await connect(client, conversation_id, headers)
    assert status == 200
    assert [e["type"] for e in events] == [
        "RUN_STARTED",
        "MESSAGES_SNAPSHOT",
        "RUN_FINISHED",
    ]
    assert events[0]["threadId"] == conversation_id
    assert [m["role"] for m in snapshot_of(events)] == ["user", "assistant"]


async def test_connect_mid_turn_shows_everything_once(
    client, make_user, login, scripted_model
):
    model = scripted_model(LONG, word_delay=0.01)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    await wait_for(lambda: model.streamed_words >= 10)

    status, events = await connect(client, conversation_id, headers)
    await turn
    assert status == 200
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
    assert [e["type"] for e in events].count("RUN_STARTED") == 1
    custom = [e["value"]["status"] for e in events if e["type"] == "CUSTOM"]
    assert custom[0] == "running" and custom[-1] == "completed"
    assert text_seen(events) == LONG


async def test_connect_after_a_tool_step_starts_from_the_safe_point(
    client, make_user, login, scripted_model
):
    model = scripted_model(CLOCK_CALL, LONG, word_delay=0.01)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Giờ?")))
    await wait_for(lambda: model.streamed_words >= 10)

    _, events = await connect(client, conversation_id, headers)
    await turn
    snapshot = snapshot_of(events)
    # The finished tool step comes in the snapshot, not again in the tail.
    assert [m["role"] for m in snapshot].count("tool") == 1
    assert not [e for e in events if e["type"] == "TOOL_CALL_RESULT"]
    assert text_seen(events) == LONG


async def test_connect_while_waiting_for_the_user(
    client, make_user, login, scripted_model
):
    scripted_model(ASK)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Đặt phòng"))

    _, events = await connect(client, conversation_id, headers)
    assert [e["type"] for e in events][-1] == "RUN_FINISHED"
    custom = [e["value"]["status"] for e in events if e["type"] == "CUSTOM"]
    assert custom == ["requires_action"]
    activity = next(m for m in snapshot_of(events) if m["role"] == "activity")
    assert activity["content"]["question"] == "Phòng?"


async def test_lost_live_data_sends_only_the_saved_snapshot(
    client, make_user, make_redis, login, scripted_model
):
    model = scripted_model(LONG, word_delay=0.01)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    await wait_for(lambda: model.streamed_words >= 10)
    await make_redis().flushall()  # Redis restarted mid-turn
    await wait_for(lambda: model.streamed_words >= 15)

    _, events = await connect(client, conversation_id, headers)
    await turn
    assert [e["type"] for e in events] == [
        "RUN_STARTED",
        "CUSTOM",
        "MESSAGES_SNAPSHOT",
        "RUN_FINISHED",
    ]
    assert "TEXT_MESSAGE_CONTENT" not in json.dumps(events)


async def test_stop_reaches_the_process_running_the_turn(
    client, make_user, make_redis, login, scripted_model
):
    from app.main import app
    from app.modules.agent.agui import turn_agent
    from app.modules.agent.live import LiveStore
    from app.modules.agent.runner import Runner

    model = scripted_model(LONG, word_delay=0.02)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    await wait_for(lambda: model.streamed_words >= 5)
    assistant_id = (await history(client, conversation_id, headers))["data"][-1]["id"]

    # The stop request lands on another process, which has no such task.
    owner = app.state.runner
    app.state.runner = Runner(
        agent_factory=turn_agent, max_concurrent=1, live=LiveStore(make_redis())
    )
    try:
        response = await client.post(
            f"/api/v1/conversations/{conversation_id}/messages/{assistant_id}/stop",
            headers=headers,
        )
    finally:
        app.state.runner = owner
    assert response.json() == {"id": assistant_id, "status": "cancelled"}
    status, events = await turn
    assert [e["value"]["status"] for e in events if e["type"] == "CUSTOM"][-1] == (
        "cancelled"
    )
