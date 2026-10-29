from fastapi import APIRouter, Depends, Request, Response, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.rate_limit import rate_limit
from app.common.exceptions.handlers import fail
from app.config.settings import get_settings
from app.database.session import SessionDep
from app.modules.auth import schemas
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(rate_limit("auth"))],
)

REFRESH_COOKIE = "refresh_token"
REMEMBER_COOKIE = "remember_login"
COOKIE_PATH = "/api/v1/auth"


def _set_session_cookies(response: Response, raw: str, *, persistent: bool) -> None:
    settings = get_settings()
    # A session cookie unless the user asked to be remembered.
    max_age = settings.refresh_token_days * 86400 if persistent else None
    for name, value in ((REFRESH_COOKIE, raw), (REMEMBER_COOKIE, str(int(persistent)))):
        response.set_cookie(
            name,
            value,
            max_age=max_age,
            path=COOKIE_PATH,
            secure=settings.cookie_secure,
            httponly=True,
            samesite="strict",
        )
    response.headers["Cache-Control"] = "no-store"


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(REFRESH_COOKIE, path=COOKIE_PATH)
    response.delete_cookie(REMEMBER_COOKIE, path=COOKIE_PATH)


def _require_trusted_origin(request: Request) -> None:
    """Endpoints authenticated by the refresh cookie must refuse foreign pages:
    the browser attaches the cookie whoever initiates the request."""
    origin = request.headers.get("origin")
    if (origin and origin not in get_settings().allowed_origins) or request.headers.get(
        "sec-fetch-site"
    ) == "cross-site":
        fail(403, "untrusted_origin")


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def register(data: schemas.Register, session: SessionDep) -> UserResponse:
    return await AuthService(session).register(data)


@router.post("/login", response_model=schemas.TokenResponse)
async def login(
    data: schemas.Login, session: SessionDep, response: Response
) -> schemas.TokenResponse:
    body, raw = await AuthService(session).login(data)
    _set_session_cookies(response, raw, persistent=data.remember)
    return body


@router.post("/refresh", response_model=schemas.TokenResponse)
async def refresh(
    request: Request, response: Response, session: SessionDep
) -> schemas.TokenResponse:
    _require_trusted_origin(request)
    body, raw = await AuthService(session).refresh(request.cookies.get(REFRESH_COOKIE))
    _set_session_cookies(
        response, raw, persistent=request.cookies.get(REMEMBER_COOKIE) == "1"
    )
    return body


@router.post("/session", response_model=schemas.SessionResponse)
async def start_session(
    request: Request, response: Response, session: SessionDep
) -> schemas.SessionResponse:
    """Refresh + profile + workspaces in one round trip, used on page load."""
    _require_trusted_origin(request)
    body, raw = await AuthService(session).session(request.cookies.get(REFRESH_COOKIE))
    _set_session_cookies(
        response, raw, persistent=request.cookies.get(REMEMBER_COOKIE) == "1"
    )
    return body


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(user: CurrentUser, session: SessionDep, response: Response) -> None:
    await AuthService(session).logout(user_id=user.id, family_id=user.family_id)
    _clear_session_cookies(response)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    user: CurrentUser, session: SessionDep, response: Response
) -> None:
    await AuthService(session).logout(
        user_id=user.id, family_id=user.family_id, all_sessions=True
    )
    _clear_session_cookies(response)
