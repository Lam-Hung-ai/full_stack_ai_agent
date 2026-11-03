"""Workspaces a user may enter: personal plus active organization memberships."""

WORKSPACES = "/api/v1/workspaces"


async def test_lists_personal_then_organizations(
    client, make_user, make_organization, add_member, login
):
    owner = make_user("owner@example.com")
    user = make_user("an@example.com")
    org_b, workspace_b = make_organization(owner, name="Beta")
    org_a, workspace_a = make_organization(owner, name="Alpha")
    add_member(org_a, user)
    add_member(org_b, user)

    response = await client.get(WORKSPACES, headers=await login(user))
    assert response.status_code == 200
    body = response.json()
    assert [(w["kind"], w["name"]) for w in body["data"]] == [
        ("personal", None),
        ("organization", "Alpha"),
        ("organization", "Beta"),
    ]
    assert body["pagination"]["total_items"] == 3
    assert body["data"][0]["id"] == str(user.personal_workspace_id)


async def test_pagination(client, make_user, make_organization, add_member, login):
    owner = make_user("owner@example.com")
    user = make_user("an@example.com")
    for name in ("A", "B"):
        org, _ = make_organization(owner, name=name)
        add_member(org, user)
    response = await client.get(
        WORKSPACES, params={"page": 2, "page_size": 2}, headers=await login(user)
    )
    body = response.json()
    assert [w["name"] for w in body["data"]] == ["B"]
    assert body["pagination"] == {
        "page": 2,
        "page_size": 2,
        "total_items": 3,
        "total_pages": 2,
        "has_next_page": False,
        "has_previous_page": True,
    }


async def test_get_workspace(client, make_user, login):
    user = make_user("an@example.com")
    response = await client.get(
        f"{WORKSPACES}/{user.personal_workspace_id}", headers=await login(user)
    )
    assert response.status_code == 200
    assert response.json()["kind"] == "personal"
