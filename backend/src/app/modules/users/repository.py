from uuid import UUID

from sqlalchemy import RowMapping, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_users as users


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def profile(self, *, user_id: UUID) -> RowMapping | None:
        statement = select(
            users.c.id,
            users.c.name,
            users.c.email,
            users.c.email_verified,
            users.c.avatar_url,
            users.c.created_at,
        ).where(users.c.id == user_id)
        return (await self._session.execute(statement)).mappings().one_or_none()
