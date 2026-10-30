"""Searching one's own chats by title or message text (C09, QD-31)."""

from tests.support.chat import body, history, new_conversation, send


def search_url(workspace_id, q):
    return f"/api/v1/workspaces/{workspace_id}/conversations/search?q={q}"


async def chat(client, user, headers, question):
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body(question))
    return conversation_id


async def test_matches_titles_and_text_without_accents(
    client, make_user, login, scripted_model
):
    scripted_model("Mùa thu Hà Nội có hoa sữa.", "Phở bò rất ngon.", "Không liên quan.")
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    autumn = await chat(client, user, headers, "Kể về mùa thu")
    pho = await chat(client, user, headers, "Món gì ở HÀ NỘI ngon?")
    await chat(client, user, headers, "Câu khác")

    response = await client.get(search_url(workspace, "ha noi"), headers=headers)
    assert response.status_code == 200, response.text
    found = {row["id"]: row for row in response.json()["data"]}
    assert set(found) == {autumn, pho}
    # The answer matched: the snippet comes from it, with its message id.
    answer = (await history(client, autumn, headers))["data"][-1]
    assert found[autumn]["message_id"] == answer["id"]
    assert "Hà Nội" in found[autumn]["snippet"]

    by_title = await client.get(search_url(workspace, "kể về"), headers=headers)
    assert [row["id"] for row in by_title.json()["data"]] == [autumn]


async def test_only_own_live_chats_are_found(
    client, db, make_user, login, scripted_model
):
    scripted_model("Bí mật số một", "Bí mật số hai")
    owner = make_user("an@example.com")
    other = make_user("binh@example.com")
    owner_headers = await login(owner)
    other_headers = await login(other)
    deleted = await chat(client, owner, owner_headers, "Bí mật đã xoá")
    await client.delete(f"/api/v1/conversations/{deleted}", headers=owner_headers)
    await chat(client, other, other_headers, "Bí mật của người khác")

    mine = await client.get(
        search_url(owner.personal_workspace_id, "bi mat"), headers=owner_headers
    )
    assert mine.json()["data"] == []
    # Another user's workspace is not reachable at all.
    foreign = await client.get(
        search_url(other.personal_workspace_id, "bi mat"), headers=owner_headers
    )
    assert foreign.status_code in (403, 404)


async def test_query_is_validated_and_wildcards_are_literal(
    client, make_user, login, scripted_model
):
    scripted_model("Đúng 100% rồi")
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    percent = await chat(client, user, headers, "Tỉ lệ")

    short = await client.get(search_url(workspace, "a"), headers=headers)
    assert short.status_code == 422
    spaces = await client.get(search_url(workspace, "%20a%20%20"), headers=headers)
    assert spaces.status_code == 422
    literal = await client.get(search_url(workspace, "0%25"), headers=headers)
    assert [row["id"] for row in literal.json()["data"]] == [percent]
    nothing = await client.get(search_url(workspace, "x%25y"), headers=headers)
    assert nothing.json()["data"] == []


def test_snippet_is_cut_around_the_match(pg):
    from app.modules.conversations.search import snippet

    text = "đầu " * 30 + "Thành phố Hồ Chí Minh" + " cuối" * 30
    cut = snippet(text, "ho chi minh")
    assert cut.startswith("…") and cut.endswith("…")
    assert "Hồ Chí Minh" in cut
    assert snippet("Ngắn gọn", "zz") == "Ngắn gọn"
