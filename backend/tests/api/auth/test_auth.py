"""Login sessions: login, refresh rotation, reuse detection, logout (QD-12)."""

from app.config.security import digest

AUTH = "/api/v1/auth"


async def test_register_creates_user_with_personal_workspace(client, db):
    response = await client.post(
        f"{AUTH}/register",
        json={"email": " Lan@Example.com ", "name": "Lan", "password": "Str0ng!pass"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["email"] == "lan@example.com"
    assert "password" not in response.text
    rows = db(
        "SELECT kind FROM chat_app.workspaces WHERE personal_user_id = %s",
        (body["id"],),
    )
    assert rows == [{"kind": "personal"}]


async def test_register_rejects_duplicates_and_weak_passwords(client, make_user):
    make_user("taken@example.com")
    duplicate = await client.post(
        f"{AUTH}/register",
        json={"email": "taken@example.com", "name": "X", "password": "Str0ng!pass"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_exists"

    weak = await client.post(
        f"{AUTH}/register",
        json={"email": "new@example.com", "name": "X", "password": "password"},
    )
    assert weak.status_code == 422


async def test_register_can_be_disabled(client, monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "registration_enabled", False)
    response = await client.post(
        f"{AUTH}/register",
        json={"email": "a@example.com", "name": "A", "password": "Str0ng!pass"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "registration_disabled"


async def test_login_sets_http_only_refresh_cookie(client, make_user):
    make_user("an@example.com")
    response = await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer" and body["expires_in"] == 900
    cookie = response.headers.get_list("set-cookie")[0]
    assert cookie.startswith("refresh_token=")
    assert "HttpOnly" in cookie and "SameSite=strict" in cookie
    assert "Path=/api/v1/auth" in cookie
    assert "refresh_token" not in body


async def test_login_gives_one_answer_for_every_failure(client, make_user):
    make_user("an@example.com")
    make_user("off@example.com", active=False)
    attempts = [
        {"email": "an@example.com", "password": "Wrong!pass1"},
        {"email": "nobody@example.com", "password": "Str0ng!pass"},
        {"email": "off@example.com", "password": "Str0ng!pass"},
    ]
    for attempt in attempts:
        response = await client.post(f"{AUTH}/login", json=attempt)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "invalid_credentials"


async def test_refresh_rotates_within_the_family(client, db, make_user):
    make_user("an@example.com")
    await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    first = client.cookies["refresh_token"]

    response = await client.post(f"{AUTH}/refresh")
    assert response.status_code == 200
    second = client.cookies["refresh_token"]
    assert second != first

    rows = db(
        "SELECT token_hash, family_id, consumed_at IS NOT NULL AS consumed "
        "FROM chat_app.refresh_tokens ORDER BY created_at"
    )
    assert [row["token_hash"] for row in rows] == [digest(first), digest(second)]
    assert rows[0]["family_id"] == rows[1]["family_id"]
    assert [row["consumed"] for row in rows] == [True, False]


async def test_reused_refresh_token_revokes_the_session(client, make_user, monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "refresh_reuse_grace_seconds", 0)
    make_user("an@example.com")
    login = await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    stolen = client.cookies["refresh_token"]
    await client.post(f"{AUTH}/refresh")

    client.cookies.clear()
    client.cookies.set("refresh_token", stolen)
    reuse = await client.post(f"{AUTH}/refresh")
    assert reuse.status_code == 401
    assert reuse.json()["error"]["code"] == "refresh_reuse"

    # Every token of the family is dead, including access tokens.
    me = await client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 401
    assert me.json()["error"]["code"] == "session_revoked"


async def test_token_presented_again_within_grace_keeps_the_session(
    client, db, make_user
):
    """Two tabs loading at once present the same cookie (QD-18)."""
    make_user("an@example.com")
    await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    shared = client.cookies["refresh_token"]
    first = await client.post(f"{AUTH}/session")
    client.cookies.clear()
    client.cookies.set("refresh_token", shared)
    second = await client.post(f"{AUTH}/session")
    assert first.status_code == second.status_code == 200
    assert db(
        "SELECT count(*) AS n FROM chat_app.refresh_tokens WHERE revoked_at IS NOT NULL"
    ) == [{"n": 0}]


async def test_refresh_requires_a_cookie_and_a_trusted_origin(client, make_user):
    missing = await client.post(f"{AUTH}/refresh")
    assert missing.json()["error"]["code"] == "invalid_refresh_token"

    make_user("an@example.com")
    await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    foreign = await client.post(
        f"{AUTH}/refresh", headers={"Origin": "https://evil.example"}
    )
    assert foreign.status_code == 403
    assert foreign.json()["error"]["code"] == "untrusted_origin"


async def test_session_returns_user_and_workspaces(client, make_user):
    user = make_user("an@example.com", name="An")
    await client.post(
        f"{AUTH}/login", json={"email": "an@example.com", "password": "Str0ng!pass"}
    )
    response = await client.post(f"{AUTH}/session")
    assert response.status_code == 200
    body = response.json()
    assert body["user"]["name"] == "An"
    assert body["workspaces"] == [
        {
            "id": str(user.personal_workspace_id),
            "kind": "personal",
            "name": None,
            "organization_id": None,
        }
    ]
    me = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {body['access_token']}"}
    )
    assert me.status_code == 200


async def test_logout_ends_only_the_current_session(client, make_user, login):
    user = make_user("an@example.com")
    phone = await login(user)
    laptop = await login(user)

    response = await client.post(f"{AUTH}/logout", headers=laptop)
    assert response.status_code == 204
    assert (await client.get("/api/v1/users/me", headers=laptop)).status_code == 401
    assert (await client.get("/api/v1/users/me", headers=phone)).status_code == 200

    await client.post(f"{AUTH}/logout-all", headers=phone)
    assert (await client.get("/api/v1/users/me", headers=phone)).status_code == 401


async def test_protected_routes_require_a_valid_token(client):
    missing = await client.get("/api/v1/users/me")
    assert missing.status_code == 401
    assert missing.json()["error"]["code"] == "authentication_required"

    forged = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert forged.json()["error"]["code"] == "invalid_access_token"


async def test_auth_is_rate_limited(client, monkeypatch):
    from app.config.settings import get_settings

    monkeypatch.setattr(get_settings(), "auth_rate_limit", 2)
    payload = {"email": "x@example.com", "password": "Wrong!pass1"}
    codes = [
        (await client.post(f"{AUTH}/login", json=payload)).status_code for _ in range(3)
    ]
    assert codes == [401, 401, 429]
