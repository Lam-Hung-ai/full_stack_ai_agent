"""Exporting one's own chats of a workspace as a zip (O08, QD-31)."""

import io
import json
import zipfile

from tests.api.files.test_files import PNG, upload
from tests.support.chat import body, history, new_conversation, send


async def export(client, workspace_id, headers):
    return await client.get(
        f"/api/v1/workspaces/{workspace_id}/export", headers=headers
    )


async def test_zip_holds_each_own_chat_as_json_and_markdown(
    client, make_user, login, storage, scripted_model
):
    scripted_model("Hà Nội là thủ đô.", "Ảnh màu đỏ.", "Không thấy đâu")
    user = make_user("an@example.com")
    other = make_user("binh@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    first = await new_conversation(client, user, headers)
    await send(client, first, headers, body("Thủ đô Việt Nam?"))
    image = (
        await upload(client, storage, headers, workspace, "a.png", "image/png", PNG)
    ).json()
    second = await new_conversation(client, user, headers)
    payload = body("Ảnh gì?")
    payload["message"]["file_ids"] = [image["id"]]
    await send(client, second, headers, payload)
    deleted = await new_conversation(client, user, headers)
    await client.delete(f"/api/v1/conversations/{deleted}", headers=headers)
    other_headers = await login(other)
    await send(
        client,
        await new_conversation(client, other, other_headers),
        other_headers,
        body("Của người khác"),
    )

    response = await export(client, workspace, headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    disposition = response.headers["content-disposition"]
    # "Chat Cá nhân dd-mm-yyyy.zip", with an accent-free fallback.
    assert disposition.startswith('attachment; filename="Chat Ca nhan ')
    assert "filename*=UTF-8''Chat%20C%C3%A1%20nh%C3%A2n%20" in disposition
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    names = archive.namelist()
    manifest = json.loads(archive.read("manifest.json"))
    assert manifest["conversations"] == 2
    folders = sorted({name.split("/")[0] for name in names if "/" in name})
    assert len(folders) == 2
    documents = [json.loads(archive.read(f"{f}/conversation.json")) for f in folders]
    assert {d["id"] for d in documents} == {first, second}

    capital = next(d for d in documents if d["id"] == first)
    saved = (await history(client, first, headers))["data"]
    assert [m["id"] for m in capital["messages"]] == [row["id"] for row in saved]
    markdown = archive.read(f"{folders[documents.index(capital)]}/conversation.md")
    text = markdown.decode()
    assert "## Bạn\n\nThủ đô Việt Nam?" in text
    assert "## Agent\n\nHà Nội là thủ đô." in text

    with_file = next(d for d in documents if d["id"] == second)
    question = with_file["messages"][0]
    assert question["files"] == [
        {
            "id": image["id"],
            "name": "a.png",
            "content_type": "image/png",
            "size_bytes": len(PNG),
        }
    ]
    # Names only: no file bytes travel in the export.
    assert not any(name.endswith(".png") for name in names)


async def test_export_needs_the_workspace(client, make_user, login):
    user = make_user("an@example.com")
    other = make_user("binh@example.com")
    headers = await login(user)
    refused = await export(client, other.personal_workspace_id, headers)
    assert refused.status_code in (403, 404)
    empty = await export(client, user.personal_workspace_id, headers)
    archive = zipfile.ZipFile(io.BytesIO(empty.content))
    assert archive.namelist() == ["manifest.json"]


async def test_folder_names_are_readable_and_unique(
    client, make_user, login, scripted_model
):
    scripted_model("Một", "Hai")
    user = make_user("an@example.com")
    headers = await login(user)
    for _ in range(2):
        conversation_id = await new_conversation(client, user, headers)
        await send(client, conversation_id, headers, body("Kế hoạch: tuần/tháng?"))

    response = await export(client, user.personal_workspace_id, headers)
    archive = zipfile.ZipFile(io.BytesIO(response.content))
    folders = sorted({n.split("/")[0] for n in archive.namelist() if "/" in n})
    day = folders[0][:10]
    assert folders == [f"{day} Kế hoạch tuần tháng", f"{day} Kế hoạch tuần tháng (2)"]
