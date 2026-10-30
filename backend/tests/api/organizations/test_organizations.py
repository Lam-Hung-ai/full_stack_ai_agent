"""Creating and managing an organization (S6)."""

ORGS = "/api/v1/organizations"


async def test_creator_becomes_owner_with_a_workspace(client, make_user, login):
    user = make_user("an@example.com")
    headers = await login(user)

    response = await client.post(ORGS, json={"name": " Công ty A "}, headers=headers)
    assert response.status_code == 201, response.text
    organization = response.json()
    assert organization["name"] == "Công ty A"
    assert organization["is_owner"] is True
    assert {"member.manage", "role.manage", "organization.manage"} <= set(
        organization["permissions"]
    )
    workspaces = (await client.get("/api/v1/workspaces", headers=headers)).json()
    assert organization["workspace_id"] in [w["id"] for w in workspaces["data"]]


async def test_only_organization_managers_rename(
    client, make_user, make_organization, add_member, assign_role, login
):
    owner = make_user("owner@example.com")
    member = make_user("member@example.com")
    organization_id, _ = make_organization(owner)
    assign_role(organization_id, add_member(organization_id, member), "member")

    refused = await client.patch(
        f"{ORGS}/{organization_id}",
        json={"name": "Tên mới"},
        headers=await login(member),
    )
    assert refused.status_code == 403
    renamed = await client.patch(
        f"{ORGS}/{organization_id}",
        json={"name": "Tên mới"},
        headers=await login(owner),
    )
    assert renamed.json()["name"] == "Tên mới"


async def test_outsiders_cannot_see_the_organization(
    client, make_user, make_organization, login
):
    owner = make_user("owner@example.com")
    outsider = make_user("out@example.com")
    organization_id, _ = make_organization(owner)
    headers = await login(outsider)

    for method, path in (
        ("GET", f"{ORGS}/{organization_id}"),
        ("GET", f"{ORGS}/{organization_id}/members"),
        ("GET", f"{ORGS}/{organization_id}/roles"),
        ("POST", f"{ORGS}/{organization_id}/leave"),
    ):
        response = await client.request(method, path, headers=headers)
        assert response.status_code == 404, path
        assert response.json()["error"]["code"] == "organization_not_found"
