"""An organization's admin reaches no member, role or invitation of another
organization, even with its ids (backend AGENTS §11, S6)."""

ORGS = "/api/v1/organizations"


async def test_ids_of_another_organization_are_not_found(
    client, db, make_user, make_organization, add_member, login, mailbox
):
    alice = make_user("alice@example.com")
    bob = make_user("bob@example.com")
    bob_colleague = make_user("colleague@example.com")
    org_a, _ = make_organization(alice, name="A")
    org_b, _ = make_organization(bob, name="B")
    member_b = add_member(org_b, bob_colleague)
    bob_headers = await login(bob)
    role_b = await client.post(
        f"{ORGS}/{org_b}/roles", json={"name": "Riêng B"}, headers=bob_headers
    )
    invitation_b = await client.post(
        f"{ORGS}/{org_b}/invitations",
        json={"email": "new@example.com"},
        headers=bob_headers,
    )
    headers = await login(alice)

    # B's ids under A's path, where Alice holds every permission.
    attempts = (
        (
            "PATCH",
            f"{ORGS}/{org_a}/members/{member_b}",
            {"role_ids": [role_b.json()["id"]]},
        ),
        ("DELETE", f"{ORGS}/{org_a}/members/{member_b}", None),
        ("PATCH", f"{ORGS}/{org_a}/roles/{role_b.json()['id']}", {"name": "Đổi"}),
        ("DELETE", f"{ORGS}/{org_a}/roles/{role_b.json()['id']}", None),
        ("DELETE", f"{ORGS}/{org_a}/invitations/{invitation_b.json()['id']}", None),
    )
    for method, path, payload in attempts:
        response = await client.request(method, path, json=payload, headers=headers)
        assert response.status_code in (404, 422), (path, response.text)

    (row,) = db(
        "SELECT is_active FROM chat_app.organization_members WHERE id = %s", (member_b,)
    )
    assert row["is_active"] is True
    roles_b = await client.get(f"{ORGS}/{org_b}/roles", headers=bob_headers)
    assert "Riêng B" in [r["name"] for r in roles_b.json()["data"]]
    pending = await client.get(f"{ORGS}/{org_b}/invitations", headers=bob_headers)
    assert len(pending.json()["data"]) == 1
    listed = await client.get(f"{ORGS}/{org_a}/members", headers=headers)
    assert [m["email"] for m in listed.json()["data"]] == [alice.email]
