"""Folders, pins and the archive: how a user files their own chats."""

from uuid import uuid4


def conversations(workspace_id):
    return f"/api/v1/workspaces/{workspace_id}/conversations"


def folders(workspace_id):
    return f"/api/v1/workspaces/{workspace_id}/folders"


async def create_chat(client, workspace_id, headers, title):
    response = await client.post(
        conversations(workspace_id), json={"title": title}, headers=headers
    )
    return response.json()["id"]


async def titles(client, workspace_id, headers, **params):
    response = await client.get(
        conversations(workspace_id), params=params, headers=headers
    )
    return [item["title"] for item in response.json()["data"]]


async def test_folder_crud_and_unique_names(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id

    created = await client.post(
        folders(workspace), json={"name": "Dự án"}, headers=headers
    )
    assert created.status_code == 201
    folder = created.json()
    duplicate = await client.post(
        folders(workspace), json={"name": " dự ÁN "}, headers=headers
    )
    assert (duplicate.status_code, duplicate.json()["error"]["code"]) == (
        409,
        "folder_name_taken",
    )
    await client.post(folders(workspace), json={"name": "Báo cáo"}, headers=headers)
    listed = (await client.get(folders(workspace), headers=headers)).json()
    assert [item["name"] for item in listed["data"]] == ["Báo cáo", "Dự án"]

    renamed = await client.patch(
        f"/api/v1/folders/{folder['id']}", json={"name": "Dự án 2026"}, headers=headers
    )
    assert renamed.json()["name"] == "Dự án 2026"
    clash = await client.patch(
        f"/api/v1/folders/{folder['id']}", json={"name": "báo cáo"}, headers=headers
    )
    assert clash.status_code == 409
    deleted = await client.delete(f"/api/v1/folders/{folder['id']}", headers=headers)
    assert deleted.status_code == 204
    listed = (await client.get(folders(workspace), headers=headers)).json()
    assert [item["name"] for item in listed["data"]] == ["Báo cáo"]


async def test_pin_archive_and_file_chats(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)
    workspace = user.personal_workspace_id
    folder = (
        await client.post(folders(workspace), json={"name": "Dự án"}, headers=headers)
    ).json()
    first = await create_chat(client, workspace, headers, "Một")
    second = await create_chat(client, workspace, headers, "Hai")
    third = await create_chat(client, workspace, headers, "Ba")

    pinned = await client.patch(
        f"/api/v1/conversations/{first}", json={"pinned": True}, headers=headers
    )
    assert pinned.json()["pinned_at"] is not None
    assert await titles(client, workspace, headers) == ["Một", "Ba", "Hai"]

    filed = await client.patch(
        f"/api/v1/conversations/{second}",
        json={"folder_id": folder["id"]},
        headers=headers,
    )
    assert filed.json()["folder_id"] == folder["id"]
    assert await titles(client, workspace, headers, folder_id=folder["id"]) == ["Hai"]
    assert await titles(client, workspace, headers, unfiled=True) == ["Một", "Ba"]

    await client.patch(
        f"/api/v1/conversations/{third}", json={"archived": True}, headers=headers
    )
    assert await titles(client, workspace, headers) == ["Một", "Hai"]
    assert await titles(client, workspace, headers, archived=True) == ["Ba"]
    await client.patch(
        f"/api/v1/conversations/{third}", json={"archived": False}, headers=headers
    )
    assert "Ba" in await titles(client, workspace, headers)

    # Deleting the folder moves its chats back to the main list.
    await client.delete(f"/api/v1/folders/{folder['id']}", headers=headers)
    chat = (await client.get(f"/api/v1/conversations/{second}", headers=headers)).json()
    assert chat["folder_id"] is None
    unfiled = await client.patch(
        f"/api/v1/conversations/{first}", json={"folder_id": None}, headers=headers
    )
    assert unfiled.status_code == 200


async def test_patch_allowlist(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)
    chat = await create_chat(client, user.personal_workspace_id, headers, "Một")
    url = f"/api/v1/conversations/{chat}"

    for payload in (
        {},
        {"title": None},
        {"pinned": None},
        {"owner_user_id": str(uuid4())},
    ):
        response = await client.patch(url, json=payload, headers=headers)
        assert response.status_code == 422, payload
    missing = await client.patch(url, json={"folder_id": str(uuid4())}, headers=headers)
    assert missing.json()["error"]["code"] == "folder_not_found"


async def test_folders_are_private_and_workspace_scoped(
    client, make_user, make_organization, login
):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    alice_headers = await login(alice)
    bob_headers = await login(bob)
    folder = (
        await client.post(
            folders(alice.personal_workspace_id),
            json={"name": "Riêng"},
            headers=alice_headers,
        )
    ).json()

    url = f"/api/v1/folders/{folder['id']}"
    assert (
        await client.patch(url, json={"name": "x"}, headers=bob_headers)
    ).status_code == 404
    assert (await client.delete(url, headers=bob_headers)).status_code == 404
    bob_chat = await create_chat(client, bob.personal_workspace_id, bob_headers, "Bob")
    response = await client.patch(
        f"/api/v1/conversations/{bob_chat}",
        json={"folder_id": folder["id"]},
        headers=bob_headers,
    )
    assert response.json()["error"]["code"] == "folder_not_found"

    # Alice's own folder cannot hold a chat of another of her workspaces.
    _, org_workspace = make_organization(alice)
    org_chat = await create_chat(client, org_workspace, alice_headers, "Công ty")
    response = await client.patch(
        f"/api/v1/conversations/{org_chat}",
        json={"folder_id": folder["id"]},
        headers=alice_headers,
    )
    assert response.json()["error"]["code"] == "folder_not_found"
