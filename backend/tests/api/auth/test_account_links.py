"""Email verification and password reset links (S6)."""

AUTH = "/api/v1/auth"
NEW_PASSWORD = "N3w!passw0rd"


async def me(client, headers):
    return await client.get("/api/v1/users/me", headers=headers)


async def test_register_sends_a_verification_link(client, mailbox):
    response = await client.post(
        f"{AUTH}/register",
        json={"email": "lan@example.com", "name": "Lan", "password": "Str0ng!pass"},
    )
    assert response.status_code == 201
    assert response.json()["email_verified"] is False
    token = mailbox.token("email_verify", to="lan@example.com")

    confirmed = await client.post(
        f"{AUTH}/email-verification/confirm", json={"token": token}
    )
    assert confirmed.status_code == 204
    login = await client.post(
        f"{AUTH}/login", json={"email": "lan@example.com", "password": "Str0ng!pass"}
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await me(client, headers)).json()["email_verified"] is True

    reused = await client.post(
        f"{AUTH}/email-verification/confirm", json={"token": token}
    )
    assert reused.status_code == 400
    assert reused.json()["error"]["code"] == "invalid_token"


async def test_requests_answer_the_same_for_unknown_emails(client, make_user, mailbox):
    make_user("an@example.com")
    for path in ("email-verification/request", "password-reset/request"):
        known = await client.post(f"{AUTH}/{path}", json={"email": "an@example.com"})
        unknown = await client.post(
            f"{AUTH}/{path}", json={"email": "nobody@example.com"}
        )
        assert known.status_code == unknown.status_code == 202
        assert known.content == unknown.content
    assert [letter.to for letter in mailbox] == ["an@example.com"] * 2


async def test_a_newer_link_voids_the_older_one(client, make_user, mailbox):
    make_user("an@example.com")
    for _ in range(2):
        await client.post(
            f"{AUTH}/password-reset/request", json={"email": "an@example.com"}
        )
    first, second = (letter.body.split("token=")[1].split()[0] for letter in mailbox)
    old = await client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": first, "password": NEW_PASSWORD},
    )
    assert old.status_code == 400
    new = await client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": second, "password": NEW_PASSWORD},
    )
    assert new.status_code == 204


async def test_password_reset_signs_every_session_out(
    client, make_user, login, mailbox
):
    user = make_user("an@example.com")
    headers = await login(user)
    await client.post(f"{AUTH}/password-reset/request", json={"email": user.email})

    response = await client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": mailbox.token("password_reset"), "password": NEW_PASSWORD},
    )
    assert response.status_code == 204
    assert (await me(client, headers)).status_code == 401
    old = await client.post(
        f"{AUTH}/login", json={"email": user.email, "password": "Str0ng!pass"}
    )
    assert old.status_code == 401
    new = await client.post(
        f"{AUTH}/login", json={"email": user.email, "password": NEW_PASSWORD}
    )
    assert new.status_code == 200


async def test_expired_link_is_refused(client, db, make_user, mailbox):
    make_user("an@example.com")
    await client.post(
        f"{AUTH}/password-reset/request", json={"email": "an@example.com"}
    )
    db(
        "UPDATE chat_app.verifications SET created_at = now() - interval '2 hours', "
        "expires_at = now() - interval '1 hour'"
    )
    response = await client.post(
        f"{AUTH}/password-reset/confirm",
        json={"token": mailbox.token("password_reset"), "password": NEW_PASSWORD},
    )
    assert response.status_code == 400
