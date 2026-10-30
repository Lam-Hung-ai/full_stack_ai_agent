"""Users, organizations and logged-in clients for API tests."""

from dataclasses import dataclass
from uuid import UUID

import pytest
from argon2 import PasswordHasher

PASSWORD = "Str0ng!pass"
_hasher = PasswordHasher()


@dataclass(frozen=True)
class TestUser:
    id: UUID
    email: str
    personal_workspace_id: UUID


@pytest.fixture(autouse=True)
def _reset_rate_limit():
    from app.common.dependencies.rate_limit import reset

    reset()


@pytest.fixture
def make_user(db):
    """Insert an active user with a password; the trigger adds the workspace."""

    def make(email: str, *, name: str = "Người dùng", active: bool = True) -> TestUser:
        (user,) = db(
            "INSERT INTO chat_app.users (name, email, is_active) VALUES (%s, %s, %s) "
            "RETURNING id",
            (name, email, active),
        )
        db(
            "INSERT INTO chat_app.user_accounts "
            "(user_id, provider_id, account_id, password_hash) "
            "VALUES (%s, 'credential', %s, %s)",
            (user["id"], str(user["id"]), _hasher.hash(PASSWORD)),
        )
        (workspace,) = db(
            "SELECT id FROM chat_app.workspaces WHERE personal_user_id = %s",
            (user["id"],),
        )
        return TestUser(user["id"], email, workspace["id"])

    return make


@pytest.fixture
def make_organization(db):
    """Create an organization owned by `owner`; return (org id, workspace id)."""

    def make(owner: TestUser, *, name: str = "Công ty") -> tuple[UUID, UUID]:
        (org,) = db(
            "INSERT INTO chat_app.organizations (name, created_by) VALUES (%s, %s) "
            "RETURNING id",
            (name, owner.id),
        )
        (workspace,) = db(
            "SELECT id FROM chat_app.workspaces WHERE organization_id = %s",
            (org["id"],),
        )
        return org["id"], workspace["id"]

    return make


@pytest.fixture
def add_member(db):
    def add(organization_id: UUID, user: TestUser) -> UUID:
        (member,) = db(
            "INSERT INTO chat_app.organization_members (organization_id, user_id) "
            "VALUES (%s, %s) RETURNING id",
            (organization_id, user.id),
        )
        return member["id"]

    return add


@pytest.fixture
def assign_role(db):
    """Give a member one of the roles provisioned with the organization."""

    def assign(organization_id: UUID, member_id: UUID, role_key: str) -> None:
        db(
            "INSERT INTO chat_app.member_role_assignments "
            "(organization_id, member_id, role_id) "
            "SELECT %s, %s, id FROM chat_app.organization_roles "
            "WHERE organization_id = %s AND role_key = %s",
            (organization_id, member_id, organization_id, role_key),
        )

    return assign


@pytest.fixture
def login(client):
    """Log in through the API and return the Authorization header."""

    async def do(user: TestUser) -> dict[str, str]:
        response = await client.post(
            "/api/v1/auth/login", json={"email": user.email, "password": PASSWORD}
        )
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return do
