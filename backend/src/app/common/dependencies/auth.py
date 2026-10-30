from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.common.exceptions.handlers import fail
from app.config.security import decode_token
from app.database.session import SessionDep
from app.modules.auth.repository import AuthRepository

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """The authenticated user of a request. Carries no workspace: that is
    resolved per request by the workspace dependency or from the resource."""

    id: UUID
    family_id: UUID
    name: str
    email: str
    is_superuser: bool


async def current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if credentials is None:
        fail(401, "authentication_required")
    user_id, family_id = decode_token(credentials.credentials)
    repository = AuthRepository(session)
    user = await repository.user_by_id(user_id=user_id)
    # Logging out revokes the family, so every access token of that session
    # stops working at once instead of living until it expires.
    if (
        user is None
        or not user["is_active"]
        or not await repository.session_is_alive(user_id=user_id, family_id=family_id)
    ):
        fail(401, "session_revoked")
    return Principal(
        id=user["id"],
        family_id=family_id,
        name=user["name"],
        email=user["email"],
        is_superuser=user["is_superuser"],
    )


CurrentUser = Annotated[Principal, Depends(current_user)]


async def optional_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal | None:
    """The user when a token is sent, None for an anonymous visitor (public
    share links). A token that is sent must still be valid."""
    if credentials is None:
        return None
    return await current_user(session, credentials)


OptionalUser = Annotated[Principal | None, Depends(optional_user)]
