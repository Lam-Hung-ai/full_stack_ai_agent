from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import now
from app.database.generated_tables import t_refresh_tokens as tokens
from app.database.generated_tables import t_user_accounts as accounts
from app.database.generated_tables import t_users as users

CREDENTIAL_PROVIDER = "credential"


class AuthRepository:
    """Users' credentials and login sessions; auth owns both tables."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def user_by_email(
        self, *, email: str, lock: bool = False
    ) -> RowMapping | None:
        statement = select(users).where(users.c.email == email)
        if lock:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def user_by_id(
        self, *, user_id: UUID, lock: bool = False
    ) -> RowMapping | None:
        statement = select(users).where(users.c.id == user_id)
        if lock:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def create_user(self, *, name: str, email: str) -> RowMapping:
        statement = insert(users).values(name=name, email=email).returning(users)
        return (await self._session.execute(statement)).mappings().one()

    async def password_hash(self, *, user_id: UUID) -> str | None:
        statement = select(accounts.c.password_hash).where(
            accounts.c.user_id == user_id,
            accounts.c.provider_id == CREDENTIAL_PROVIDER,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def add_password(self, *, user_id: UUID, password_hash: str) -> None:
        await self._session.execute(
            insert(accounts).values(
                user_id=user_id,
                provider_id=CREDENTIAL_PROVIDER,
                account_id=str(user_id),
                password_hash=password_hash,
            )
        )

    async def add_refresh_token(
        self,
        *,
        user_id: UUID,
        family_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        await self._session.execute(
            insert(tokens).values(
                user_id=user_id,
                family_id=family_id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )

    async def refresh_token_for_update(self, *, token_hash: str) -> RowMapping | None:
        statement = (
            select(tokens).where(tokens.c.token_hash == token_hash).with_for_update()
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def consume_refresh_token(self, *, token_id: UUID) -> None:
        await self._session.execute(
            update(tokens).where(tokens.c.id == token_id).values(consumed_at=now())
        )

    async def revoke(self, *, user_id: UUID, family_id: UUID | None = None) -> None:
        """Revoke one session (family) or, without `family_id`, every session."""
        statement = update(tokens).where(
            tokens.c.user_id == user_id, tokens.c.revoked_at.is_(None)
        )
        if family_id is not None:
            statement = statement.where(tokens.c.family_id == family_id)
        await self._session.execute(statement.values(revoked_at=now()))

    async def session_is_alive(self, *, user_id: UUID, family_id: UUID) -> bool:
        """A session lives while its current (unconsumed) token is valid."""
        statement = (
            select(tokens.c.id)
            .where(
                tokens.c.user_id == user_id,
                tokens.c.family_id == family_id,
                tokens.c.consumed_at.is_(None),
                tokens.c.revoked_at.is_(None),
                tokens.c.expires_at > now(),
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).first() is not None
