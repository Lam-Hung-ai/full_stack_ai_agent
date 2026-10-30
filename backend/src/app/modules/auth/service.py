"""Login sessions: rotating refresh tokens grouped by family (QD-12).

A family is one login. Each refresh consumes the presented token and issues
the next one in the same family. Presenting an already consumed token means
it was copied, so the whole family is revoked, except within a short grace
period after the rotation (QD-18): concurrent page loads and lost responses
present the same token twice without any theft.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.email import Letter
from app.common.exceptions.handlers import fail
from app.common.schemas.pagination import MAX_PAGE_SIZE, PageParams
from app.config.security import (
    access_token,
    digest,
    hash_password,
    new_token,
    now,
    verify_password,
)
from app.config.settings import get_settings
from app.modules.auth.letters import Purpose, account_letter
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import (
    Login,
    PasswordReset,
    Register,
    SessionResponse,
    TokenResponse,
)
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService
from app.modules.workspaces.service import WorkspaceService

#: The raw refresh token travels next to the response body, only to be set as
#: an HttpOnly cookie by the router; it never appears in a JSON body.
type IssuedTokens = tuple[TokenResponse, str]


class AuthService:
    def __init__(
        self, session: AsyncSession, repository: AuthRepository | None = None
    ) -> None:
        self._session = session
        self._auth = repository or AuthRepository(session)

    async def register(self, data: Register) -> tuple[UserResponse, Letter]:
        """New account and the letter that verifies its email."""
        if not get_settings().registration_enabled:
            fail(403, "registration_disabled")
        user = await self.create_account(
            name=data.name, email=str(data.email), password=data.password
        )
        letter = await self._verification_letter(user, "email_verify")
        await self._session.commit()
        return UserResponse.model_validate(dict(user)), letter

    async def create_account(
        self, *, name: str, email: str, password: str, email_verified: bool = False
    ):
        """Uncommitted; the insert trigger provisions the personal workspace."""
        if await self._auth.user_by_email(email=email):
            fail(409, "email_exists")
        user = await self._auth.create_user(
            name=name, email=email, email_verified=email_verified
        )
        await self._auth.add_password(
            user_id=user["id"], password_hash=await hash_password(password)
        )
        return user

    async def request_link(self, *, email: str, purpose: Purpose) -> Letter | None:
        """A verification or reset link, if the account can use one. The
        caller answers the same either way, so no answer reveals an account."""
        user = await self._auth.user_by_email(email=email, lock=True)
        if (
            user is None
            or not user["is_active"]
            or (purpose == "email_verify" and user["email_verified"])
            or (
                purpose == "password_reset"
                and await self._auth.password_hash(user_id=user["id"]) is None
            )
        ):
            return None
        letter = await self._verification_letter(user, purpose)
        await self._session.commit()
        return letter

    async def confirm_email(self, raw: str) -> None:
        user = await self._consume(raw, "email_verify")
        await self._auth.mark_email_verified(user_id=user["id"])
        await self._session.commit()

    async def reset_password(self, data: PasswordReset) -> None:
        """New password; every session of the account is signed out."""
        user = await self._consume(data.token, "password_reset")
        if not await self._auth.set_password(
            user_id=user["id"], password_hash=await hash_password(data.password)
        ):
            fail(400, "invalid_token")
        await self._auth.revoke(user_id=user["id"])
        # The link reached the mailbox, which is what verifying proves.
        await self._auth.mark_email_verified(user_id=user["id"])
        await self._session.commit()

    async def _verification_letter(self, user, purpose: Purpose) -> Letter:
        settings = get_settings()
        lifetime = (
            timedelta(hours=settings.email_verification_hours)
            if purpose == "email_verify"
            else timedelta(minutes=settings.password_reset_minutes)
        )
        raw = new_token()
        await self._auth.replace_verification(
            identifier=user["email"],
            purpose=purpose,
            token_hash=digest(raw),
            expires_at=now() + lifetime,
        )
        return account_letter(
            to=user["email"], name=user["name"], purpose=purpose, token=raw
        )

    async def _consume(self, raw: str, purpose: Purpose):
        """Mark a link used; one invalid answer for every cause."""
        row = await self._auth.verification_for_update(
            token_hash=digest(raw), purpose=purpose
        )
        if row is None or row["consumed_at"] is not None or row["expires_at"] <= now():
            fail(400, "invalid_token")
        user = await self._auth.user_by_email(email=row["identifier"], lock=True)
        if user is None or not user["is_active"]:
            fail(400, "invalid_token")
        await self._auth.consume_verification(verification_id=row["id"])
        return user

    async def login(self, data: Login) -> IssuedTokens:
        user = await self._auth.user_by_email(email=str(data.email), lock=True)
        encoded = await self._auth.password_hash(user_id=user["id"]) if user else None
        valid = await verify_password(encoded, data.password)
        if user is None or not user["is_active"] or not valid:
            # One answer for every cause so the response never reveals which
            # emails have accounts.
            fail(401, "invalid_credentials")
        issued = await self._issue(user["id"])
        await self._session.commit()
        return issued

    async def refresh(self, raw: str | None) -> IssuedTokens:
        user_id, family_id, expires_at = await self._rotate(raw)
        issued = await self._issue(user_id, family_id=family_id, expires_at=expires_at)
        await self._session.commit()
        return issued

    async def session(self, raw: str | None) -> tuple[SessionResponse, str]:
        user_id, family_id, expires_at = await self._rotate(raw)
        token, refresh = await self._issue(
            user_id, family_id=family_id, expires_at=expires_at
        )
        user = await UserService(self._session).profile(user_id=user_id)
        workspaces = await WorkspaceService(self._session).list_for_user(
            user_id=user_id, params=PageParams(page=1, page_size=MAX_PAGE_SIZE)
        )
        await self._session.commit()
        body = SessionResponse(
            **token.model_dump(), user=user, workspaces=workspaces.data
        )
        return body, refresh

    async def logout(
        self, *, user_id: UUID, family_id: UUID, all_sessions: bool = False
    ) -> None:
        await self._auth.revoke(
            user_id=user_id, family_id=None if all_sessions else family_id
        )
        await self._session.commit()

    async def _issue(
        self,
        user_id: UUID,
        *,
        family_id: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> IssuedTokens:
        """New refresh token; a rotation keeps the family and its absolute expiry."""
        settings = get_settings()
        raw = new_token()
        family_id = family_id or uuid4()
        await self._auth.add_refresh_token(
            user_id=user_id,
            family_id=family_id,
            token_hash=digest(raw),
            expires_at=expires_at
            or now() + timedelta(days=settings.refresh_token_days),
        )
        body = TokenResponse(
            access_token=access_token(user_id, family_id),
            expires_in=settings.access_token_minutes * 60,
        )
        return body, raw

    async def _rotate(self, raw: str | None) -> tuple[UUID, UUID, datetime]:
        """Consume a refresh token; uncommitted so the caller issues the next one
        in the same transaction."""
        if not raw:
            fail(401, "invalid_refresh_token")
        token = await self._auth.refresh_token_for_update(token_hash=digest(raw))
        if token is None or token["revoked_at"] is not None:
            fail(401, "invalid_refresh_token")
        grace = timedelta(seconds=get_settings().refresh_reuse_grace_seconds)
        if token["consumed_at"] is not None and token["consumed_at"] + grace < now():
            await self._auth.revoke(
                user_id=token["user_id"], family_id=token["family_id"]
            )
            await self._session.commit()
            fail(401, "refresh_reuse")
        user = await self._auth.user_by_id(user_id=token["user_id"])
        if token["expires_at"] <= now() or user is None or not user["is_active"]:
            fail(401, "invalid_refresh_token")
        if token["consumed_at"] is None:
            await self._auth.consume_refresh_token(token_id=token["id"])
        return token["user_id"], token["family_id"], token["expires_at"]
