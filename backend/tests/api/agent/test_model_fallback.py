"""A failing model call moves on to OPENROUTER_FALLBACK_MODELS in order."""

from tests.fixtures.ai import scripted
from tests.support.chat import body, history, new_conversation, send


async def test_turn_answers_with_the_fallback_when_the_model_fails(
    client, make_user, login, scripted_model
):
    fallback = scripted("Trả lời từ model dự phòng")
    scripted_model("không tới được", fail_after_words=0, fallbacks=[fallback])
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    status, events = await send(client, conversation_id, headers, body("Chào"))

    assert status == 200
    assert events[-1]["type"] == "RUN_FINISHED"
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    assert assistant["status"] == "completed"
    assert assistant["content"][-1]["content"] == "Trả lời từ model dự phòng"
    # The fallback runs with the same tools the turn offered.
    assert any("get_current_time" in names for names in fallback.bound_tools)


async def test_turn_fails_when_every_model_fails(
    client, make_user, login, scripted_model
):
    fallback = scripted("không tới được", fail_after_words=0)
    scripted_model("không tới được", fail_after_words=0, fallbacks=[fallback])
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)

    status, events = await send(client, conversation_id, headers, body("Chào"))

    assert status == 200
    assert events[-1]["type"] == "RUN_ERROR"
    assistant = (await history(client, conversation_id, headers))["data"][-1]
    assert assistant["status"] == "failed"
