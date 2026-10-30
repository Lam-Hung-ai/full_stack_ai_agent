"""Members and invitations (O02, O07; QD-24, QD-25)."""

import asyncio

from tests.support.chat import body, send

ORGS = "/api/v1/organizations"
INVITATIONS = "/api/v1/invitations"
LONG = " ".join(f"từ{i}" for i in range(60))


async def invite(client, organization_id, email, headers):
    return await client.post(
        f"{ORGS}/{organization_id}/invitations", json={"email": email}, headers=headers
    )


async def members_of(client, organization_id, headers):
    response = await client.get(f"{ORGS}/{organization_id}/members", headers=headers)
    return {m["email"]: m for m in response.json()["data"]}


async def roles_of(client, organization_id, headers):
    response = await client.get(f"{ORGS}/{organization_id}/roles", headers=headers)
    return {r["role_key"] or r["name"]: r["id"] for r in response.json()["data"]}


async def test_invitee_without_an_account_registers_and_joins(
    client, make_user, make_organization, login, mailbox
):
    owner = make_user("owner@example.com", name="Chủ")
    organization_id, workspace_id = make_organization(owner, name="Công ty A")
    headers = await login(owner)

    response = await invite(client, organization_id, "B@Example.com", headers)
    assert response.status_code == 201, response.text
    assert response.json()["email"] == "b@example.com"
    (letter,) = mailbox
    assert letter.to == "b@example.com" and "Công ty A" in letter.subject
    token = mailbox.token("invitation")

    preview = await client.post(f"{INVITATIONS}/preview", json={"token": token})
    assert preview.json() == {
        "organization_name": "Công ty A",
        "email": "b@example.com",
        "status": "pending",
        "account_exists": False,
    }
    joined = await client.post(
        f"{INVITATIONS}/register",
        json={"token": token, "name": "Bình", "password": "Str0ng!pass"},
    )
    assert joined.status_code == 201, joined.text
    assert joined.json()["workspace_id"] == str(workspace_id)

    member = (await members_of(client, organization_id, headers))["b@example.com"]
    assert [role["role_key"] for role in member["roles"]] == ["member"]
    again = await client.post(f"{INVITATIONS}/accept", json={"token": token})
    assert again.status_code == 401
    used = await client.post(f"{INVITATIONS}/preview", json={"token": token})
    assert used.json()["status"] == "accepted"


async def test_existing_account_accepts_only_as_the_invited_email(
    client, db, make_user, make_organization, login, mailbox
):
    owner = make_user("owner@example.com")
    invitee = make_user("b@example.com")
    other = make_user("c@example.com")
    organization_id, workspace_id = make_organization(owner)
    await invite(client, organization_id, invitee.email, await login(owner))
    token = mailbox.token("invitation")

    wrong = await client.post(
        f"{INVITATIONS}/accept", json={"token": token}, headers=await login(other)
    )
    assert wrong.status_code == 403
    assert wrong.json()["error"]["code"] == "invitation_email_mismatch"
    accepted = await client.post(
        f"{INVITATIONS}/accept", json={"token": token}, headers=await login(invitee)
    )
    assert accepted.json()["workspace_id"] == str(workspace_id)
    (user,) = db(
        "SELECT email_verified FROM chat_app.users WHERE id = %s", (invitee.id,)
    )
    assert user["email_verified"] is True


async def test_inviting_again_replaces_the_link(
    client, make_user, make_organization, login, mailbox
):
    owner = make_user("owner@example.com")
    organization_id, _ = make_organization(owner)
    headers = await login(owner)
    await invite(client, organization_id, "b@example.com", headers)
    first = mailbox.token("invitation")
    await invite(client, organization_id, "b@example.com", headers)

    old = await client.post(
        f"{INVITATIONS}/register",
        json={"token": first, "name": "B", "password": "Str0ng!pass"},
    )
    assert old.status_code == 410
    assert old.json()["error"]["code"] == "invitation_revoked"
    pending = await client.get(f"{ORGS}/{organization_id}/invitations", headers=headers)
    assert len(pending.json()["data"]) == 1


async def test_cannot_invite_a_current_member_or_without_permission(
    client, make_user, make_organization, add_member, assign_role, login, mailbox
):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, _ = make_organization(owner)
    assign_role(organization_id, add_member(organization_id, member), "member")

    taken = await invite(client, organization_id, member.email, await login(owner))
    assert taken.status_code == 409
    assert taken.json()["error"]["code"] == "already_member"
    refused = await invite(
        client, organization_id, "x@example.com", await login(member)
    )
    assert refused.status_code == 403
    assert mailbox == []


async def test_owner_role_guards(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    admin = make_user("admin@example.com")
    organization_id, _ = make_organization(owner)
    admin_member = add_member(organization_id, admin)
    assign_role(organization_id, admin_member, "admin")
    admin_headers = await login(admin)
    owner_headers = await login(owner)
    roles = await roles_of(client, organization_id, owner_headers)
    owner_member = (await members_of(client, organization_id, owner_headers))[
        owner.email
    ]["id"]

    # An admin cannot make anyone an owner, nor remove the owner.
    promote = await client.patch(
        f"{ORGS}/{organization_id}/members/{admin_member}",
        json={"role_ids": [roles["owner"]]},
        headers=admin_headers,
    )
    assert promote.status_code == 403
    assert promote.json()["error"]["code"] == "owner_required"
    remove = await client.delete(
        f"{ORGS}/{organization_id}/members/{owner_member}", headers=admin_headers
    )
    assert remove.status_code == 403

    # The only owner cannot leave or drop the role.
    leave = await client.post(f"{ORGS}/{organization_id}/leave", headers=owner_headers)
    assert leave.status_code == 409
    assert leave.json()["error"]["code"] == "last_owner"
    demote = await client.patch(
        f"{ORGS}/{organization_id}/members/{owner_member}",
        json={"role_ids": [roles["member"]]},
        headers=owner_headers,
    )
    assert demote.status_code == 409

    # With a second owner, the first may go.
    promote = await client.patch(
        f"{ORGS}/{organization_id}/members/{admin_member}",
        json={"role_ids": [roles["owner"]]},
        headers=owner_headers,
    )
    assert promote.status_code == 200
    assert [r["role_key"] for r in promote.json()["roles"]] == ["owner"]
    leave = await client.post(f"{ORGS}/{organization_id}/leave", headers=owner_headers)
    assert leave.status_code == 204


async def test_removed_member_loses_chats_and_running_turns_stop(
    client, make_user, make_organization, add_member, assign_role, login, scripted_model
):
    model = scripted_model(LONG, word_delay=0.02)
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, workspace_id = make_organization(owner)
    member_id = add_member(organization_id, member)
    assign_role(organization_id, member_id, "member")
    headers = await login(member)
    created = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    conversation_id = created.json()["id"]
    turn = asyncio.create_task(send(client, conversation_id, headers, body("Đếm")))
    for _ in range(500):
        if model.streamed_words >= 3:
            break
        await asyncio.sleep(0.01)

    removed = await client.delete(
        f"{ORGS}/{organization_id}/members/{member_id}", headers=await login(owner)
    )
    assert removed.status_code == 204
    _, events = await turn
    statuses = [e["value"]["status"] for e in events if e["type"] == "CUSTOM"]
    assert statuses[-1] == "cancelled"
    old_chat = await client.get(
        f"/api/v1/conversations/{conversation_id}/messages", headers=headers
    )
    assert old_chat.status_code == 404
    workspaces = (await client.get("/api/v1/workspaces", headers=headers)).json()
    assert str(workspace_id) not in [w["id"] for w in workspaces["data"]]


async def test_rejoining_starts_as_a_plain_member(
    client, make_user, make_organization, add_member, assign_role, login, mailbox
):
    owner = make_user("owner@example.com")
    former = make_user("b@example.com")
    organization_id, _ = make_organization(owner)
    member_id = add_member(organization_id, former)
    assign_role(organization_id, member_id, "admin")
    headers = await login(owner)
    await client.delete(
        f"{ORGS}/{organization_id}/members/{member_id}", headers=headers
    )

    await invite(client, organization_id, former.email, headers)
    await client.post(
        f"{INVITATIONS}/accept",
        json={"token": mailbox.token("invitation")},
        headers=await login(former),
    )
    member = (await members_of(client, organization_id, headers))[former.email]
    assert member["id"] == str(member_id)
    assert [role["role_key"] for role in member["roles"]] == ["member"]
