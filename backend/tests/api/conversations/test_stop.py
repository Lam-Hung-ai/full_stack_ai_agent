"""Stopping an assistant keeps what it produced and frees the chat."""

import asyncio

from tests.support.chat import body, history, new_conversation, send


def stop_url(conversation_id, message_id):
    return f"/api/v1/conversations/{conversation_id}/messages/{message_id}/stop"


async def test_stop_keeps_the_partial_answer(client, make_user, login, scripted_model):
    model = scripted_model(
        "một hai ba bốn năm sáu bảy tám chín mười", "Tiếp", word_delay=0.05
    )
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    for _ in range(200):
        if model.streamed_words >= 3:
            break
        await asyncio.sleep(0.01)
    conversation = (
        await client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    ).json()
    assistant_id = conversation["active_assistant"]["id"]

    response = await client.post(
        stop_url(conversation_id, assistant_id), headers=headers
    )
    assert response.status_code == 200
    assert response.json() == {"id": assistant_id, "status": "cancelled"}

    status, events = await turn
    assert status == 200
    custom = [e["value"]["status"] for e in events if e["type"] == "CUSTOM"]
    assert custom[-1] == "cancelled"
    assert events[-1]["type"] == "RUN_FINISHED"
    assert events[-1]["outcome"] == {"type": "cancelled"}
    # Every span the stop cut off is closed before the end (client verifier).
    opened = [e for e in events if e["type"] in ("TEXT_MESSAGE_START", "STEP_STARTED")]
    closed = [e for e in events if e["type"] in ("TEXT_MESSAGE_END", "STEP_FINISHED")]
    assert len(opened) == len(closed)

    saved = (await history(client, conversation_id, headers))["data"][-1]
    assert saved["status"] == "cancelled"
    partial = saved["content"][0]["content"]
    assert partial.startswith("một") and "mười" not in partial

    # The chat takes the next question right away.
    status, _ = await send(client, conversation_id, headers, body("Tiếp", assistant_id))
    assert status == 200


async def test_stop_after_the_end_changes_nothing(
    client, make_user, login, scripted_model
):
    scripted_model("Xong")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Hỏi"))
    question, answer = (await history(client, conversation_id, headers))["data"]

    response = await client.post(
        stop_url(conversation_id, answer["id"]), headers=headers
    )
    assert response.json() == {"id": answer["id"], "status": "completed"}
    response = await client.post(
        stop_url(conversation_id, question["id"]), headers=headers
    )
    assert response.json()["error"]["code"] == "message_not_found"


async def test_stop_frees_a_turn_orphaned_by_a_restart(
    client, db, make_user, login, scripted_model
):
    scripted_model("A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu một"))
    parent = (await history(client, conversation_id, headers))["current_message_id"]
    (question,) = db(
        "INSERT INTO chat_app.messages "
        "(id, conversation_id, parent_message_id, role, status, content) "
        "VALUES (uuidv7(), %s, %s, 'user', 'completed', "
        '\'[{"id": "q", "role": "user", "content": "Câu hai"}]\') '
        "RETURNING id",
        (conversation_id, parent),
    )
    (orphan,) = db(
        "INSERT INTO chat_app.messages "
        "(conversation_id, parent_message_id, role, status) "
        "VALUES (%s, %s, 'assistant', 'running') RETURNING id",
        (conversation_id, question["id"]),
    )

    response = await client.post(
        stop_url(conversation_id, orphan["id"]), headers=headers
    )
    assert response.json() == {"id": str(orphan["id"]), "status": "cancelled"}
    conversation = (
        await client.get(f"/api/v1/conversations/{conversation_id}", headers=headers)
    ).json()
    assert conversation["active_assistant"] is None


async def test_cannot_stop_someone_elses_turn(client, make_user, login, scripted_model):
    scripted_model("A")
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    alice_headers = await login(alice)
    conversation_id = await new_conversation(client, alice, alice_headers)
    await send(client, conversation_id, alice_headers, body("Hỏi"))
    answer = (await history(client, conversation_id, alice_headers))["data"][-1]

    response = await client.post(
        stop_url(conversation_id, answer["id"]), headers=await login(bob)
    )
    assert response.status_code == 404
