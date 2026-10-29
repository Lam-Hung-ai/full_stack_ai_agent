"""A workspace is reachable only by its owner or an active member (QD-10)."""

from uuid import uuid4

WORKSPACES = "/api/v1/workspaces"


async def test_cannot_open_another_users_personal_workspace(client, make_user, login):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    response = await client.get(
        f"{WORKSPACES}/{alice.personal_workspace_id}", headers=await login(bob)
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "workspace_not_found"


async def test_unknown_workspace_looks_the_same_as_a_forbidden_one(
    client, make_user, login
):
    user = make_user("an@example.com")
    response = await client.get(f"{WORKSPACES}/{uuid4()}", headers=await login(user))
    assert response.status_code == 404


async def test_membership_is_checked_on_every_request(
    client, db, make_user, make_organization, add_member, login
):
    owner = make_user("owner@example.com")
    user = make_user("an@example.com")
    org, workspace = make_organization(owner)
    add_member(org, user)
    headers = await login(user)
    assert (
        await client.get(f"{WORKSPACES}/{workspace}", headers=headers)
    ).status_code == 200

    db(
        "UPDATE chat_app.organization_members SET is_active = false, left_at = now() "
        "WHERE organization_id = %s AND user_id = %s",
        (org, user.id),
    )
    # Same access token, membership gone: access ends immediately.
    assert (
        await client.get(f"{WORKSPACES}/{workspace}", headers=headers)
    ).status_code == 404
    listed = await client.get(WORKSPACES, headers=headers)
    assert [w["kind"] for w in listed.json()["data"]] == ["personal"]


async def test_inactive_organization_is_not_reachable(
    client, db, make_user, make_organization, login
):
    owner = make_user("owner@example.com")
    _, workspace = make_organization(owner)
    db("UPDATE chat_app.organizations SET is_active = false")
    response = await client.get(f"{WORKSPACES}/{workspace}", headers=await login(owner))
    assert response.status_code == 404
