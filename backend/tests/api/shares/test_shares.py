"""Share snapshots and copies (O03, O04; database phase 1 §7–9, QD-28)."""

import asyncio

from tests.api.files.test_files import PNG, upload
from tests.support.chat import body, history, new_conversation, send, stream_turn


async def chat_with_branches(client, user, headers):
    """A chat with a regenerated answer: two versions under one question."""
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu hỏi"))
    answer = (await history(client, conversation_id, headers))["data"][-1]["id"]
    await stream_turn(
        client,
        f"/api/v1/conversations/{conversation_id}/messages/{answer}/regenerate",
        headers,
    )
    return conversation_id


async def share(client, conversation_id, headers):
    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/share", headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


def token_of(url):
    return url.rsplit("/", 1)[1]


async def test_public_share_shows_the_whole_tree_to_anyone(
    client, make_user, login, scripted_model
):
    scripted_model("Trả lời một", "Trả lời hai")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await chat_with_branches(client, user, headers)

    shared = await share(client, conversation_id, headers)
    assert shared["mode"] == "public" and shared["version"] == 1
    view = await client.get(f"/api/v1/shares/{token_of(shared['url'])}")
    assert view.status_code == 200
    data = view.json()
    assert data["can_copy"] is False
    answers = [m for m in data["messages"] if m["role"] == "assistant"]
    assert len(answers) == 2
    assert len(answers[0]["sibling_ids"]) == 2
    assert data["current_message_id"] == answers[1]["id"]

    # The link is the same when asked again, and after a new version.
    again = (
        await client.get(
            f"/api/v1/conversations/{conversation_id}/share", headers=headers
        )
    ).json()
    assert again["url"] == shared["url"]
    republished = await share(client, conversation_id, headers)
    assert republished["url"] == shared["url"] and republished["version"] == 2


async def test_revoked_or_deleted_share_is_gone(
    client, make_user, login, scripted_model
):
    scripted_model("Một", "Hai")
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    await send(client, conversation_id, headers, body("Câu hỏi"))
    token = token_of((await share(client, conversation_id, headers))["url"])

    revoked = await client.delete(
        f"/api/v1/conversations/{conversation_id}/share", headers=headers
    )
    assert revoked.status_code == 204
    assert (await client.get(f"/api/v1/shares/{token}")).status_code == 404

    token = token_of((await share(client, conversation_id, headers))["url"])
    await client.delete(f"/api/v1/conversations/{conversation_id}", headers=headers)
    assert (await client.get(f"/api/v1/shares/{token}")).status_code == 404


async def test_organization_share_needs_an_active_member(
    client, make_user, make_organization, add_member, assign_role, login, scripted_model
):
    scripted_model("Nội bộ")
    owner = make_user("owner@example.com")
    colleague = make_user("colleague@example.com")
    outsider = make_user("out@example.com")
    organization_id, workspace_id = make_organization(owner)
    assign_role(organization_id, add_member(organization_id, colleague), "member")
    headers = await login(owner)
    chat = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    conversation_id = chat.json()["id"]
    await send(client, conversation_id, headers, body("Kế hoạch quý"))
    shared = await share(client, conversation_id, headers)
    assert shared["mode"] == "organization"
    url = f"/api/v1/shares/{token_of(shared['url'])}"

    assert (await client.get(url)).status_code == 404
    assert (await client.get(url, headers=await login(outsider))).status_code == 404
    member_view = await client.get(url, headers=await login(colleague))
    assert member_view.status_code == 200
    assert member_view.json()["can_copy"] is True


async def test_busy_chat_cannot_be_shared(client, make_user, login, scripted_model):
    model = scripted_model(" ".join(f"từ{i}" for i in range(40)), word_delay=0.02)
    user = make_user("an@example.com")
    headers = await login(user)
    conversation_id = await new_conversation(client, user, headers)
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    for _ in range(500):
        if model.streamed_words >= 3:
            break
        await asyncio.sleep(0.01)

    response = await client.post(
        f"/api/v1/conversations/{conversation_id}/share", headers=headers
    )
    await turn
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conversation_busy"


async def test_copy_continues_as_a_private_chat_with_new_files(
    client, db, make_user, login, storage, scripted_model
):
    scripted_model("Ảnh đỏ", "Tiếp tục")
    owner = make_user("an@example.com")
    reader = make_user("binh@example.com")
    headers = await login(owner)
    image = (
        await upload(
            client,
            storage,
            headers,
            owner.personal_workspace_id,
            "a.png",
            "image/png",
            PNG,
        )
    ).json()
    conversation_id = await new_conversation(client, owner, headers)
    payload = body("Ảnh gì?")
    payload["message"]["file_ids"] = [image["id"]]
    await send(client, conversation_id, headers, payload)
    token = token_of((await share(client, conversation_id, headers))["url"])
    reader_headers = await login(reader)

    anonymous = await client.post(
        f"/api/v1/shares/{token}/copy", json={"client_request_id": "r1"}
    )
    assert anonymous.status_code == 401
    copied = await client.post(
        f"/api/v1/shares/{token}/copy",
        json={"client_request_id": "r1"},
        headers=reader_headers,
    )
    assert copied.status_code == 200, copied.text
    target = copied.json()
    assert target["workspace_id"] == str(reader.personal_workspace_id)
    retry = await client.post(
        f"/api/v1/shares/{token}/copy",
        json={"client_request_id": "r1"},
        headers=reader_headers,
    )
    assert retry.json() == target

    rows = (await history(client, target["conversation_id"], reader_headers))["data"]
    question = rows[0]["content"][0]["content"]
    new_file = next(part for part in question if part.get("type") == "image")
    assert new_file["id"] != image["id"]
    (stored,) = db(
        "SELECT * FROM chat_app.stored_files WHERE id = %s", (new_file["id"],)
    )
    assert stored["uploaded_by"] == reader.id
    assert stored["object_key"].startswith(
        f"private/workspaces/{reader.personal_workspace_id}/"
    )
    assert stored["object_key"] in storage.keys()
    link = await client.get(
        f"/api/v1/conversations/{target['conversation_id']}/files/{new_file['id']}",
        headers=reader_headers,
    )
    assert link.status_code == 200

    # The copy is the reader's own: it continues, the source is untouched.
    status, _ = await send(
        client,
        target["conversation_id"],
        reader_headers,
        body("Thêm?", parent=rows[-1]["id"]),
    )
    assert status == 200
    assert len((await history(client, conversation_id, headers))["data"]) == 2


async def test_shared_files_follow_the_link(
    client, make_user, login, storage, scripted_model
):
    scripted_model("ok")
    owner = make_user("an@example.com")
    headers = await login(owner)
    image = (
        await upload(
            client,
            storage,
            headers,
            owner.personal_workspace_id,
            "a.png",
            "image/png",
            PNG,
        )
    ).json()
    loose = (
        await upload(
            client,
            storage,
            headers,
            owner.personal_workspace_id,
            "b.png",
            "image/png",
            PNG,
        )
    ).json()
    conversation_id = await new_conversation(client, owner, headers)
    payload = body("Ảnh")
    payload["message"]["file_ids"] = [image["id"]]
    await send(client, conversation_id, headers, payload)
    token = token_of((await share(client, conversation_id, headers))["url"])

    ok = await client.get(f"/api/v1/shares/{token}/files/{image['id']}")
    assert ok.status_code == 200
    other = await client.get(f"/api/v1/shares/{token}/files/{loose['id']}")
    assert other.status_code == 404
