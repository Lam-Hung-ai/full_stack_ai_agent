"""A new chat is named by the model; a rename by the user wins (C01, C07)."""

from tests.support.chat import body, new_conversation, send


def titles():
    # Imported late: the app's engine is built once the test database exists.
    from app.modules.conversations import titles

    return titles


async def title_of(client, conversation_id, headers):
    response = await client.get(
        f"/api/v1/conversations/{conversation_id}", headers=headers
    )
    return response.json()["title"]


async def test_model_names_a_new_chat(
    client, make_user, login, scripted_model, title_model
):
    scripted_model("Thủ đô là Hà Nội")
    title_model('"Thủ đô Việt Nam."\n')
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    await send(client, conversation_id, headers, body("Thủ đô của Việt Nam là gì?"))
    await titles().drain()
    assert await title_of(client, conversation_id, headers) == "Thủ đô Việt Nam"


async def test_a_rename_before_the_model_answers_wins(
    client, make_user, login, scripted_model, title_model, monkeypatch
):
    scripted_model("Được")
    title_model("Tên do model đặt")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    # The user renames while the title call is still on its way.
    suggest = titles().suggest

    async def slow_suggest(question):
        await client.patch(
            f"/api/v1/conversations/{conversation_id}",
            json={"title": "Tên của tôi"},
            headers=headers,
        )
        return await suggest(question)

    monkeypatch.setattr(titles(), "suggest", slow_suggest)

    await send(client, conversation_id, headers, body("Câu hỏi đầu"))
    await titles().drain()
    assert await title_of(client, conversation_id, headers) == "Tên của tôi"


async def test_a_failed_title_call_keeps_the_first_line(
    client, make_user, login, scripted_model
):
    scripted_model("Được")  # the default title model fails
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    await send(client, conversation_id, headers, body("Câu hỏi đầu\ndòng hai"))
    await titles().drain()
    assert await title_of(client, conversation_id, headers) == "Câu hỏi đầu dòng hai"


def test_titles_are_cleaned_and_clipped(pg):
    clean = titles().clean
    assert clean("\n  **Kế hoạch du lịch**  \nthừa") == "Kế hoạch du lịch"
    assert clean("   ") is None
    assert len(clean("x" * 100) or "") == titles().TITLE_LENGTH
