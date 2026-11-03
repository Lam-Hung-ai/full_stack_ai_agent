from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.handlers import fail
from app.modules.users.repository import UserRepository
from app.modules.users.schemas import UserResponse


class UserService:
    def __init__(
        self, session: AsyncSession, repository: UserRepository | None = None
    ) -> None:
        self._users = repository or UserRepository(session)

    async def profile(self, *, user_id: UUID) -> UserResponse:
        row = await self._users.profile(user_id=user_id)
        if row is None:
            fail(404, "user_not_found")
        return UserResponse.model_validate(dict(row))
