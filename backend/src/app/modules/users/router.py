from fastapi import APIRouter

from app.common.dependencies.auth import CurrentUser
from app.database.session import SessionDep
from app.modules.users.schemas import UserResponse
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser, session: SessionDep) -> UserResponse:
    return await UserService(session).profile(user_id=user.id)
