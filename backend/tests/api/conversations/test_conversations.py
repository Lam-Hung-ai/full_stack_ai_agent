"""Conversation CRUD and history: private to the owner, scoped to a workspace."""

from uuid import uuid4


def path(workspace_id):
    return f"/api/v1/workspaces/{workspace_id}/conversations"


async def test_create_list_rename_delete(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)
    created = await client.post(
        path(user.personal_workspace_id), json={}, headers=headers
    )
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == "Cuộc trò chuyện mới"
    assert body["active_assistant"] is None
    named = await client.post(
        path(user.personal_workspace_id), json={"title": "Kế hoạch"}, headers=headers
    )

    listed = (
        await client.get(path(user.personal_workspace_id), headers=headers)
    ).json()
    assert [c["title"] for c in listed["data"]] == ["Kế hoạch", "Cuộc trò chuyện mới"]
    assert listed["pagination"]["total_items"] == 2

    conversation = f"/api/v1/conversations/{body['id']}"
    renamed = await client.patch(
        conversation, json={"title": " Báo cáo "}, headers=headers
    )
    assert renamed.json()["title"] == "Báo cáo"

    assert (await client.delete(conversation, headers=headers)).status_code == 204
    assert (await client.get(conversation, headers=headers)).status_code == 404
    listed = (
        await client.get(path(user.personal_workspace_id), headers=headers)
    ).json()
    assert [c["id"] for c in listed["data"]] == [named.json()["id"]]


async def test_empty_history(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)
    created = (
        await client.post(path(user.personal_workspace_id), json={}, headers=headers)
    ).json()
    history = await client.get(
        f"/api/v1/conversations/{created['id']}/messages", headers=headers
    )
    assert history.json() == {"current_message_id": None, "data": []}


async def test_organization_needs_conversation_create(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    user = make_user("an@example.com")
    org, workspace = make_organization(owner)
    member = add_member(org, user)
    headers = await login(user)

    denied = await client.post(path(workspace), json={}, headers=headers)
    assert denied.status_code == 403
    assert denied.json()["error"]["details"] == {"permission": "conversation.create"}

    assign_role(org, member, "member")
    assert (
        await client.post(path(workspace), json={}, headers=headers)
    ).status_code == 201
    owner_headers = await login(owner)
    assert (
        await client.post(path(workspace), json={}, headers=owner_headers)
    ).status_code == 201


async def test_conversations_are_private_to_the_owner(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    colleague = make_user("colleague@example.com")
    org, workspace = make_organization(owner)
    assign_role(org, add_member(org, colleague), "admin")
    created = (
        await client.post(path(workspace), json={}, headers=await login(owner))
    ).json()

    # An organization admin still cannot read someone else's chat.
    headers = await login(colleague)
    conversation = f"/api/v1/conversations/{created['id']}"
    for method, url in [
        ("GET", conversation),
        ("GET", f"{conversation}/messages"),
        ("DELETE", conversation),
    ]:
        response = await client.request(method, url, headers=headers)
        assert response.status_code == 404, (method, url)
    listed = (await client.get(path(workspace), headers=headers)).json()
    assert listed["data"] == []


async def test_access_ends_with_membership(
    client, db, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    user = make_user("an@example.com")
    org, workspace = make_organization(owner)
    assign_role(org, add_member(org, user), "member")
    headers = await login(user)
    created = (await client.post(path(workspace), json={}, headers=headers)).json()
    db(
        "UPDATE chat_app.organization_members SET is_active = false, left_at = now() "
        "WHERE user_id = %s",
        (user.id,),
    )
    response = await client.get(
        f"/api/v1/conversations/{created['id']}", headers=headers
    )
    assert response.status_code == 404


async def test_unknown_conversation(client, make_user, login):
    user = make_user("an@example.com")
    response = await client.get(
        f"/api/v1/conversations/{uuid4()}", headers=await login(user)
    )
    assert response.json()["error"]["code"] == "conversation_not_found"
