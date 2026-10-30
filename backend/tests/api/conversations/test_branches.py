"""Edit and regenerate add siblings; history walks and switches branches."""

from uuid_utils.compat import uuid7

from tests.support.chat import body, history, new_conversation, send, stream_turn


async def edit(client, conversation_id, message_id, headers, text):
    return await stream_turn(
        client,
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/edit",
        headers,
        {"message": {"id": str(uuid7()), "text": text}},
    )


async def regenerate(client, conversation_id, message_id, headers):
    return await stream_turn(
        client,
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate",
        headers,
    )


async def test_edit_creates_a_sibling_and_keeps_the_old_branch(
    client, make_user, login, scripted_model
):
    model = scripted_model("Một", "Hai", "Một mới")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu một"))
    first = (await history(client, conversation_id, headers))["data"]
    await send(client, conversation_id, headers, body("Câu hai", first[1]["id"]))
    old_leaf = (await history(client, conversation_id, headers))["current_message_id"]

    status, events = await edit(
        client, conversation_id, first[0]["id"], headers, "Câu một đã sửa"
    )
    assert status == 200
    assert events[-1]["type"] == "RUN_FINISHED"
    # The edited question is answered without the old branch as context.
    assert [m.content for m in model.prompts[-1]][-1:] == ["Câu một đã sửa"]
    assert "Câu hai" not in [m.content for m in model.prompts[-1]]

    saved = await history(client, conversation_id, headers)
    new_question, new_answer = saved["data"]
    assert new_question["parent_message_id"] is None
    assert new_question["sibling_ids"] == [first[0]["id"], new_question["id"]]
    assert new_answer["content"][0]["content"] == "Một mới"
    assert new_answer["sibling_ids"] == [new_answer["id"]]

    # Opening the old version comes back down to where it last continued.
    old = await history(client, conversation_id, headers, first[0]["id"])
    assert old["current_message_id"] == old_leaf
    assert [row["role"] for row in old["data"]] == ["user", "assistant"] * 2
    assert old["data"][0]["sibling_ids"] == new_question["sibling_ids"]


async def test_regenerate_answers_the_same_question_again(
    client, make_user, login, scripted_model
):
    model = scripted_model("Lần một", "Lần hai")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu hỏi"))
    question, answer = (await history(client, conversation_id, headers))["data"]

    status, events = await regenerate(client, conversation_id, answer["id"], headers)
    assert status == 200
    custom = [e["value"] for e in events if e["type"] == "CUSTOM"]
    assert custom[0]["userMessageId"] == question["id"]
    assert [m.content for m in model.prompts[-1]][-1:] == ["Câu hỏi"]
    assert "Lần một" not in [m.content for m in model.prompts[-1]]

    saved = await history(client, conversation_id, headers)
    assert saved["data"][0]["id"] == question["id"]
    second = saved["data"][1]
    assert second["sibling_ids"] == [answer["id"], second["id"]]
    assert second["content"][0]["content"] == "Lần hai"


async def test_asking_on_an_older_branch_continues_that_branch(
    client, make_user, login, scripted_model
):
    model = scripted_model("Lần một", "Lần hai", "Tiếp lần một")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu hỏi"))
    _, answer = (await history(client, conversation_id, headers))["data"]
    await regenerate(client, conversation_id, answer["id"], headers)

    # The tab still shows the first answer and asks from there.
    status, _ = await send(
        client, conversation_id, headers, body("Hỏi tiếp", answer["id"])
    )
    assert status == 200
    assert [m.content for m in model.prompts[-1]][-3:] == [
        "Câu hỏi",
        "Lần một",
        "Hỏi tiếp",
    ]
    saved = await history(client, conversation_id, headers)
    assert saved["data"][1]["id"] == answer["id"]
    assert len(saved["data"]) == 4


async def test_edit_and_regenerate_targets(client, make_user, login, scripted_model):
    scripted_model("A")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu hỏi"))
    question, answer = (await history(client, conversation_id, headers))["data"]

    status, error = await edit(client, conversation_id, answer["id"], headers, "x")
    assert (status, error["error"]["code"]) == (404, "message_not_found")
    status, error = await regenerate(client, conversation_id, question["id"], headers)
    assert (status, error["error"]["code"]) == (404, "message_not_found")
    status, error = await edit(client, conversation_id, question["id"], headers, "  ")
    assert (status, error["error"]["code"]) == (422, "empty_message")
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        params={"from_message_id": str(uuid7())},
        headers=headers,
    )
    assert response.json()["error"]["code"] == "message_not_found"


async def test_cannot_branch_someone_elses_conversation(
    client, make_user, login, scripted_model
):
    scripted_model("A")
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    alice_headers = await login(alice)
    conversation_id = await new_conversation(client, alice, alice_headers)
    await send(client, conversation_id, alice_headers, body("Câu hỏi"))
    question, answer = (await history(client, conversation_id, alice_headers))["data"]

    bob_headers = await login(bob)
    status, error = await regenerate(client, conversation_id, answer["id"], bob_headers)
    assert (status, error["error"]["code"]) == (404, "conversation_not_found")
    status, error = await edit(
        client, conversation_id, question["id"], bob_headers, "x"
    )
    assert (status, error["error"]["code"]) == (404, "conversation_not_found")
