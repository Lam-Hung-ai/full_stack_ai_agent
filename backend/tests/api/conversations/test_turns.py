"""Sending a message: one turn per request, run apart from HTTP, saved at the end."""

import asyncio
import json
from typing import Any
from uuid import uuid4

from uuid_utils.compat import uuid7


async def new_conversation(client, user, headers):
    response = await client.post(
        f"/api/v1/workspaces/{user.personal_workspace_id}/conversations",
        json={},
        headers=headers,
    )
    return response.json()["id"]


def body(text, parent=None, message_id=None):
    return {
        "parent_message_id": parent,
        "message": {"id": str(message_id or uuid7()), "text": text},
    }


async def send(client, conversation_id, headers, payload) -> tuple[int, Any]:
    """POST and read the whole SSE stream; return (status, events)."""
    events = []
    async with client.stream(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages",
        json=payload,
        headers={**headers, "Accept": "text/event-stream"},
    ) as response:
        if response.status_code != 200:
            await response.aread()
            return response.status_code, response.json()
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                events.append(json.loads(line[5:]))
    return 200, events


async def history(client, conversation_id, headers):
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=headers
    )
    return response.json()


async def test_turn_streams_and_is_saved(client, make_user, login, scripted_model):
    scripted_model("Xin chào bạn")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    message_id = uuid7()

    status, events = await send(
        client, conversation_id, headers, body("  Chào agent  ", message_id=message_id)
    )
    assert status == 200
    types = [event["type"] for event in events]
    assert types[0] == "RUN_STARTED" and types[-1] == "RUN_FINISHED"
    assert events[0]["threadId"] == conversation_id
    custom = [event["value"] for event in events if event["type"] == "CUSTOM"]
    assert [value["status"] for value in custom] == ["running", "completed"]
    assert custom[0]["userMessageId"] == str(message_id)
    text = "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")
    assert text == "Xin chào bạn"

    saved = await history(client, conversation_id, headers)
    user_row, assistant_row = saved["data"]
    assert saved["current_message_id"] == assistant_row["id"]
    assert assistant_row["id"] == custom[0]["assistantMessageId"]
    assert user_row["content"] == [
        {"id": str(message_id), "role": "user", "content": "Chào agent"}
    ]
    assert user_row["status"] == "completed"
    assert assistant_row["status"] == "completed"
    assert assistant_row["parent_message_id"] == str(message_id)
    assert [m["role"] for m in assistant_row["content"]] == ["assistant"]
    assert assistant_row["content"][0]["content"] == "Xin chào bạn"

    conversation = (
        await client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    ).json()
    assert conversation["title"] == "Chào agent"
    assert conversation["active_assistant"] is None


async def test_next_turn_gets_the_branch_as_context(
    client, make_user, login, scripted_model
):
    model = scripted_model("Một", "Hai")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu một"))
    parent = (await history(client, conversation_id, headers))["current_message_id"]

    status, _ = await send(client, conversation_id, headers, body("Câu hai", parent))
    assert status == 200
    last_prompt = [message.content for message in model.prompts[-1]]
    assert last_prompt[-3:] == ["Câu một", "Một", "Câu hai"]
    rows = (await history(client, conversation_id, headers))["data"]
    assert [row["role"] for row in rows] == ["user", "assistant", "user", "assistant"]


async def test_parent_rules(client, db, make_user, login, scripted_model):
    scripted_model("A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu một"))
    rows = (await history(client, conversation_id, headers))["data"]

    status, error = await send(client, conversation_id, headers, body("lạc", None))
    assert (status, error["error"]["code"]) == (409, "parent_required")
    status, error = await send(
        client, conversation_id, headers, body("x", rows[0]["id"])
    )
    assert (status, error["error"]["code"]) == (409, "invalid_parent")
    status, error = await send(
        client, conversation_id, headers, body("x", rows[1]["id"], uuid4())
    )
    assert status == 422  # a UUIDv4 message id
    status, error = await send(
        client, conversation_id, headers, body("x", rows[1]["id"], rows[0]["id"])
    )
    assert (status, error["error"]["code"]) == (409, "message_id_conflict")


async def test_one_active_assistant_per_conversation(
    client, db, make_user, login, scripted_model
):
    scripted_model("A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu một"))
    parent = (await history(client, conversation_id, headers))["current_message_id"]
    # A second turn still running in another tab.
    db(
        "INSERT INTO chat_app.messages "
        "(conversation_id, parent_message_id, role, status) "
        "VALUES (%s, %s, 'assistant', 'running')",
        (conversation_id, parent),
    )
    status, error = await send(
        client, conversation_id, headers, body("Câu hai", parent)
    )
    assert (status, error["error"]["code"]) == (409, "assistant_active")


async def test_failed_turn_keeps_partial_content(
    client, make_user, login, scripted_model
):
    scripted_model("một hai ba bốn năm", fail_after_words=2)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    status, events = await send(client, conversation_id, headers, body("Hỏi"))
    assert status == 200
    assert events[-1]["type"] == "RUN_ERROR"
    assert events[-1]["code"] == "agent_run_failed"
    assert "provider exploded" not in json.dumps(events)
    custom = [event["value"]["status"] for event in events if event["type"] == "CUSTOM"]
    assert custom == ["running", "failed"]

    assistant = (await history(client, conversation_id, headers))["data"][-1]
    assert assistant["status"] == "failed"
    assert assistant["content"][0]["content"] == "một "


async def test_leaving_the_stream_does_not_stop_the_turn(
    client, make_user, login, scripted_model
):
    scripted_model("Câu trả lời khá dài cho bài kiểm tra")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    async with client.stream(
        "POST",
        f"/api/v1/conversations/{conversation_id}/messages",
        json=body("Hỏi"),
        headers=headers,
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                break  # the browser tab closes after the first event

    for _ in range(100):
        rows = (await history(client, conversation_id, headers))["data"]
        if rows and rows[-1]["status"] == "completed":
            break
        await asyncio.sleep(0.05)
    assert rows[-1]["status"] == "completed"
    assert rows[-1]["content"][0]["content"] == "Câu trả lời khá dài cho bài kiểm tra"


async def test_input_validation(client, make_user, login, scripted_model):
    scripted_model("A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    status, error = await send(client, conversation_id, headers, body("   "))
    assert (status, error["error"]["code"]) == (422, "empty_message")
    payload = body("x")
    payload["message"]["file_ids"] = [str(uuid4())]
    status, error = await send(client, conversation_id, headers, payload)
    assert (status, error["error"]["code"]) == (400, "file_attachments_unavailable")


async def test_cannot_send_to_someone_elses_conversation(
    client, make_user, login, scripted_model
):
    scripted_model("A")
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    conversation_id = await new_conversation(client, alice, await login(alice))
    status, error = await send(client, conversation_id, await login(bob), body("x"))
    assert (status, error["error"]["code"]) == (404, "conversation_not_found")
