"""Chat files: presigned upload, verified completion, attachment, download
and what the model receives (S7, AGENTS §17.8)."""

from tests.support.chat import body, history, new_conversation, send

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
NOTE = "Doanh thu quý 3 tăng 12%.".encode()


async def upload(client, storage, headers, workspace_id, name, content_type, data):
    """The browser's three steps; returns the `complete` response."""
    declared = {
        "original_name": name,
        "content_type": content_type,
        "size_bytes": len(data),
    }
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/uploads", json=declared, headers=headers
    )
    assert created.status_code == 201, created.text
    ticket = created.json()
    storage.put(
        ticket["upload"]["url"], data, ticket["upload"]["headers"]["Content-Type"]
    )
    return await client.post(
        f"/api/v1/workspaces/{workspace_id}/uploads/{ticket['file_id']}/complete",
        json=declared,
        headers=headers,
    )


async def test_upload_is_checked_then_recorded_under_the_final_key(
    client, db, make_user, login, storage
):
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id

    response = await upload(
        client, storage, headers, workspace, "ảnh.png", "image/png", PNG
    )
    assert response.status_code == 201, response.text
    file = response.json()
    assert file["kind"] == "image" and file["size_bytes"] == len(PNG)
    assert storage.keys() == {f"private/workspaces/{workspace}/files/{file['id']}"}
    (row,) = db("SELECT * FROM chat_app.stored_files WHERE id = %s", (file["id"],))
    assert row["uploaded_by"] == user.id and row["visibility"] == "private"
    assert len(row["checksum_sha256"]) == 64
    assert "ảnh" not in row["object_key"]


async def test_bad_uploads_are_refused_and_leave_nothing(
    client, db, make_user, login, storage
):
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id

    unsupported = await client.post(
        f"/api/v1/workspaces/{workspace}/uploads",
        json={
            "original_name": "x.exe",
            "content_type": "application/x-msdownload",
            "size_bytes": 10,
        },
        headers=headers,
    )
    assert unsupported.status_code == 415
    too_big = await client.post(
        f"/api/v1/workspaces/{workspace}/uploads",
        json={
            "original_name": "a.png",
            "content_type": "image/png",
            "size_bytes": 11 * 2**20,
        },
        headers=headers,
    )
    assert too_big.status_code == 422
    disguised = await upload(
        client, storage, headers, workspace, "a.png", "image/png", b"MZ" + b"\x00" * 40
    )
    assert disguised.status_code == 415
    assert disguised.json()["error"]["code"] == "file_content_mismatch"

    declared = {
        "original_name": "b.png",
        "content_type": "image/png",
        "size_bytes": len(PNG),
    }
    ticket = (
        await client.post(
            f"/api/v1/workspaces/{workspace}/uploads", json=declared, headers=headers
        )
    ).json()
    missing = await client.post(
        f"/api/v1/workspaces/{workspace}/uploads/{ticket['file_id']}/complete",
        json=declared,
        headers=headers,
    )
    assert missing.status_code == 409
    storage.put(ticket["upload"]["url"], PNG + b"extra", "image/png")
    lied = await client.post(
        f"/api/v1/workspaces/{workspace}/uploads/{ticket['file_id']}/complete",
        json=declared,
        headers=headers,
    )
    assert lied.status_code == 422
    assert storage.keys() == set()
    assert db("SELECT count(*) AS n FROM chat_app.stored_files") == [{"n": 0}]


async def test_question_with_files_reaches_the_model(
    client, db, make_user, login, storage, scripted_model
):
    model = scripted_model("Tôi thấy ảnh và ghi chú")
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    image = (
        await upload(client, storage, headers, workspace, "a.png", "image/png", PNG)
    ).json()
    note = (
        await upload(
            client, storage, headers, workspace, "note.txt", "text/plain", NOTE
        )
    ).json()
    conversation_id = await new_conversation(client, user, headers)

    payload = body("Xem giúp")
    payload["message"]["file_ids"] = [image["id"], note["id"]]
    status, _ = await send(client, conversation_id, headers, payload)
    assert status == 200

    question = (await history(client, conversation_id, headers))["data"][0]
    parts = question["content"][0]["content"]
    assert [part["type"] for part in parts] == ["text", "image", "document"]
    assert parts[1]["id"] == image["id"]
    assert parts[1]["source"]["value"] == f"stored-file:{image['id']}"
    links = db(
        "SELECT stored_file_id FROM chat_app.message_files WHERE message_id = %s",
        (question["id"],),
    )
    assert {str(row["stored_file_id"]) for row in links} == {image["id"], note["id"]}

    prompt = model.prompts[0][-1].content
    blocks = {block["type"]: block for block in prompt if isinstance(block, dict)}
    # The picture's bytes, not the stored placeholder.
    assert blocks["image_url"]["image_url"]["url"].startswith("data:image/png;base64,")
    texts = [block["text"] for block in prompt if block.get("type") == "text"]
    assert any("Doanh thu quý 3" in text for text in texts)


async def test_only_own_files_of_this_workspace_attach(
    client, make_user, make_organization, login, storage, scripted_model
):
    scripted_model("ok")
    owner = make_user("an@example.com")
    other = make_user("binh@example.com")
    _, org_workspace = make_organization(owner)
    headers = await login(owner)
    personal = (
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
    others = (
        await upload(
            client,
            storage,
            await login(other),
            other.personal_workspace_id,
            "b.png",
            "image/png",
            PNG,
        )
    ).json()

    chat = await client.post(
        f"/api/v1/workspaces/{org_workspace}/conversations", json={}, headers=headers
    )
    for file_id in (personal["id"], others["id"]):
        payload = body("Xem")
        payload["message"]["file_ids"] = [file_id]
        status, error = await send(client, chat.json()["id"], headers, payload)
        assert status == 422
        assert error["error"]["code"] == "invalid_file"


async def test_download_needs_the_chat_and_the_link(
    client, make_user, login, storage, scripted_model
):
    scripted_model("ok")
    user = make_user("an@example.com")
    stranger = make_user("binh@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    attached = (
        await upload(client, storage, headers, workspace, "a.png", "image/png", PNG)
    ).json()
    loose = (
        await upload(client, storage, headers, workspace, "b.png", "image/png", PNG)
    ).json()
    conversation_id = await new_conversation(client, user, headers)
    payload = body("Ảnh")
    payload["message"]["file_ids"] = [attached["id"]]
    await send(client, conversation_id, headers, payload)
    url = f"/api/v1/conversations/{conversation_id}/files"

    ok = await client.get(f"{url}/{attached['id']}", headers=headers)
    assert ok.status_code == 200
    assert ok.json()["url"].endswith("?inline")
    unlinked = await client.get(f"{url}/{loose['id']}", headers=headers)
    assert unlinked.status_code == 404
    foreign = await client.get(f"{url}/{attached['id']}", headers=await login(stranger))
    assert foreign.status_code == 404


async def test_regenerating_gives_the_model_the_files_again(
    client, make_user, login, storage, scripted_model
):
    model = scripted_model("Lần một", "Lần hai")
    user = make_user("an@example.com")
    headers = await login(user)
    image = (
        await upload(
            client,
            storage,
            headers,
            user.personal_workspace_id,
            "a.png",
            "image/png",
            PNG,
        )
    ).json()
    conversation_id = await new_conversation(client, user, headers)
    payload = body("Ảnh gì?")
    payload["message"]["file_ids"] = [image["id"]]
    await send(client, conversation_id, headers, payload)
    answer = (await history(client, conversation_id, headers))["data"][-1]["id"]

    status, _ = await send_regenerate(client, conversation_id, answer, headers)
    assert status == 200
    prompt = model.prompts[-1][-1].content
    assert any(block.get("type") == "image_url" for block in prompt)


async def send_regenerate(client, conversation_id, message_id, headers):
    from tests.support.chat import stream_turn

    return await stream_turn(
        client,
        f"/api/v1/conversations/{conversation_id}/messages/{message_id}/regenerate",
        headers,
    )


async def test_an_edited_question_names_its_files_again(
    client, db, make_user, login, storage, scripted_model
):
    scripted_model("Một", "Hai")
    user = make_user("an@example.com")
    headers = await login(user)
    image = (
        await upload(
            client,
            storage,
            headers,
            user.personal_workspace_id,
            "a.png",
            "image/png",
            PNG,
        )
    ).json()
    conversation_id = await new_conversation(client, user, headers)
    payload = body("Ảnh gì?")
    payload["message"]["file_ids"] = [image["id"]]
    await send(client, conversation_id, headers, payload)
    question = (await history(client, conversation_id, headers))["data"][0]["id"]

    from tests.support.chat import stream_turn

    edited = body("Ảnh này màu gì?")
    edited["message"]["file_ids"] = [image["id"]]
    status, _ = await stream_turn(
        client,
        f"/api/v1/conversations/{conversation_id}/messages/{question}/edit",
        headers,
        {"message": edited["message"]},
    )
    assert status == 200
    rows = db(
        "SELECT count(*) AS n FROM chat_app.message_files WHERE stored_file_id = %s",
        (image["id"],),
    )
    # The same upload, linked to both versions of the question.
    assert rows == [{"n": 2}]
