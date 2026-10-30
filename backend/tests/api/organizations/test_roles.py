"""Roles and permission grants (QD-24, RR-15, T07)."""

from langchain_core.messages import AIMessage

from tests.support.chat import body, send

ORGS = "/api/v1/organizations"
CLOCK = "tool.get_current_time"
CLOCK_CALL = AIMessage(
    content="", tool_calls=[{"name": "get_current_time", "args": {}, "id": "call_1"}]
)


async def roles_of(client, organization_id, headers):
    response = await client.get(f"{ORGS}/{organization_id}/roles", headers=headers)
    assert response.status_code == 200, response.text
    return {r["role_key"] or r["name"]: r for r in response.json()["data"]}


async def test_catalog_and_built_in_roles(client, make_user, make_organization, login):
    owner = make_user("owner@example.com")
    organization_id, _ = make_organization(owner)
    headers = await login(owner)

    catalog = (await client.get("/api/v1/permissions", headers=headers)).json()
    assert CLOCK in [item["key"] for item in catalog["data"]]
    roles = await roles_of(client, organization_id, headers)
    assert list(roles) == ["owner", "admin", "member"]
    assert roles["owner"]["locked"] is True
    assert roles["owner"]["member_count"] == 1
    assert CLOCK not in roles["member"]["permissions"]


async def test_built_in_roles_keep_their_shape(
    client, make_user, make_organization, login
):
    owner = make_user("owner@example.com")
    organization_id, _ = make_organization(owner)
    headers = await login(owner)
    roles = await roles_of(client, organization_id, headers)
    url = f"{ORGS}/{organization_id}/roles"

    for role, change in (
        ("owner", {"permissions": []}),
        ("admin", {"name": "Quản trị"}),
    ):
        response = await client.patch(
            f"{url}/{roles[role]['id']}", json=change, headers=headers
        )
        assert response.status_code == 409, role
        assert response.json()["error"]["code"] == "role_locked"
    deleted = await client.delete(f"{url}/{roles['member']['id']}", headers=headers)
    assert deleted.status_code == 409
    granted = await client.patch(
        f"{url}/{roles['member']['id']}",
        json={"permissions": ["conversation.create", CLOCK]},
        headers=headers,
    )
    assert granted.json()["permissions"] == ["conversation.create", CLOCK]
    unknown = await client.post(
        url, json={"name": "X", "permissions": ["tool.rm_rf"]}, headers=headers
    )
    assert unknown.status_code == 422


async def test_custom_role_grants_a_tool_until_taken_back(
    client, make_user, make_organization, add_member, assign_role, login, scripted_model
):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, workspace_id = make_organization(owner)
    member_id = add_member(organization_id, member)
    assign_role(organization_id, member_id, "member")
    owner_headers = await login(owner)
    roles = await roles_of(client, organization_id, owner_headers)

    created = await client.post(
        f"{ORGS}/{organization_id}/roles",
        json={
            "name": "Nhân viên có tool",
            "permissions": ["conversation.create", CLOCK],
        },
        headers=owner_headers,
    )
    assert created.status_code == 201, created.text
    role_id = created.json()["id"]
    assigned = await client.patch(
        f"{ORGS}/{organization_id}/members/{member_id}",
        json={"role_ids": [roles["member"]["id"], role_id]},
        headers=owner_headers,
    )
    assert assigned.status_code == 200

    model = scripted_model(CLOCK_CALL, "Bây giờ là sáng", "Không xem được")
    headers = await login(member)
    chat = await client.post(
        f"/api/v1/workspaces/{workspace_id}/conversations", json={}, headers=headers
    )
    conversation_id = chat.json()["id"]
    _, events = await send(client, conversation_id, headers, body("Mấy giờ?"))
    assert any("get_current_time" in names for names in model.bound_tools)

    await client.patch(
        f"{ORGS}/{organization_id}/roles/{role_id}",
        json={"permissions": ["conversation.create"]},
        headers=owner_headers,
    )
    model.bound_tools.clear()
    parent = next(
        e["value"]["assistantMessageId"] for e in events if e["type"] == "CUSTOM"
    )
    await send(client, conversation_id, headers, body("Còn giờ?", parent=parent))
    assert model.bound_tools
    assert all("get_current_time" not in names for names in model.bound_tools)


async def test_nobody_grants_what_they_lack(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    admin = make_user("admin@example.com")
    organization_id, _ = make_organization(owner)
    admin_member = add_member(organization_id, admin)
    assign_role(organization_id, admin_member, "admin")
    owner_headers = await login(owner)
    roles = await roles_of(client, organization_id, owner_headers)
    without_clock = [p for p in roles["admin"]["permissions"] if p != CLOCK]
    await client.patch(
        f"{ORGS}/{organization_id}/roles/{roles['admin']['id']}",
        json={"permissions": without_clock},
        headers=owner_headers,
    )
    admin_headers = await login(admin)

    created = await client.post(
        f"{ORGS}/{organization_id}/roles",
        json={"name": "Có tool", "permissions": [CLOCK]},
        headers=admin_headers,
    )
    assert created.status_code == 403
    assert created.json()["error"]["code"] == "permission_escalation"
    raised = await client.patch(
        f"{ORGS}/{organization_id}/roles/{roles['admin']['id']}",
        json={"permissions": [*without_clock, CLOCK]},
        headers=admin_headers,
    )
    assert raised.status_code == 403
    # What the admin holds can be handed on.
    allowed = await client.post(
        f"{ORGS}/{organization_id}/roles",
        json={"name": "Chat", "permissions": ["conversation.create"]},
        headers=admin_headers,
    )
    assert allowed.status_code == 201


async def test_deleting_a_role_drops_its_assignments(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, _ = make_organization(owner)
    member_id = add_member(organization_id, member)
    headers = await login(owner)
    role = await client.post(
        f"{ORGS}/{organization_id}/roles", json={"name": "Tạm"}, headers=headers
    )
    role_id = role.json()["id"]
    await client.patch(
        f"{ORGS}/{organization_id}/members/{member_id}",
        json={"role_ids": [role_id]},
        headers=headers,
    )
    duplicate = await client.post(
        f"{ORGS}/{organization_id}/roles", json={"name": "tạm"}, headers=headers
    )
    assert duplicate.status_code == 409

    deleted = await client.delete(
        f"{ORGS}/{organization_id}/roles/{role_id}", headers=headers
    )
    assert deleted.status_code == 204
    members = await client.get(f"{ORGS}/{organization_id}/members", headers=headers)
    by_email = {m["email"]: m for m in members.json()["data"]}
    assert by_email[member.email]["roles"] == []


async def test_sync_gives_owner_roles_new_permissions(db, make_user, make_organization):
    from app.database.session import SessionLocal
    from app.modules.authorization.service import AuthorizationService

    owner = make_user("owner@example.com")
    organization_id, _ = make_organization(owner)
    # As if the tool permission arrived after the organization was created.
    db(
        "DELETE FROM chat_app.role_permissions rp "
        "USING chat_app.organization_roles r, chat_app.permissions p "
        "WHERE rp.role_id = r.id AND rp.permission_id = p.id "
        "AND r.organization_id = %s AND p.resource = 'tool'",
        (organization_id,),
    )
    async with SessionLocal() as session:
        await AuthorizationService(session).sync_catalog()

    rows = db(
        "SELECT r.role_key FROM chat_app.role_permissions rp "
        "JOIN chat_app.organization_roles r ON r.id = rp.role_id "
        "JOIN chat_app.permissions p ON p.id = rp.permission_id "
        "WHERE r.organization_id = %s AND p.resource = 'tool'",
        (organization_id,),
    )
    from app.modules.agent.tools import TOOLS

    # Every tool permission, to the owner role only.
    assert [row["role_key"] for row in rows] == ["owner"] * len(TOOLS)
