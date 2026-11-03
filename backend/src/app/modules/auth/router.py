from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.rate_limit import SESSION_RATE_LIMIT, rate_limit
from app.common.email import MailerDep, deliver
from app.common.exceptions.handlers import fail
from app.config.settings import get_settings
from app.database.session import SessionDep
from app.modules.auth import schemas
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

#: Passwords, accounts and mail: tight, against guessing and flooding.
GUARDED = [Depends(rate_limit("auth"))]
#: Every page load refreshes or reads the session: a separate, wider bucket.
SESSION = [Depends(rate_limit("session", SESSION_RATE_LIMIT))]

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
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    dependencies=GUARDED,
)
async def register(
    data: schemas.Register,
    session: SessionDep,
    mailer: MailerDep,
    background: BackgroundTasks,
) -> UserResponse:
    user, letter = await AuthService(session).register(data)
    background.add_task(deliver, mailer, letter)
    return user


@router.post("/login", response_model=schemas.TokenResponse, dependencies=GUARDED)
async def login(
    data: schemas.Login, session: SessionDep, response: Response
) -> schemas.TokenResponse:
    body, raw = await AuthService(session).login(data)
    _set_session_cookies(response, raw, persistent=data.remember)
    return body


@router.post("/refresh", response_model=schemas.TokenResponse, dependencies=SESSION)
async def refresh(
    request: Request, response: Response, session: SessionDep
) -> schemas.TokenResponse:
    _require_trusted_origin(request)
    body, raw = await AuthService(session).refresh(request.cookies.get(REFRESH_COOKIE))
    _set_session_cookies(
        response, raw, persistent=request.cookies.get(REMEMBER_COOKIE) == "1"
    )
    return body


@router.post("/session", response_model=schemas.SessionResponse, dependencies=SESSION)
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


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=SESSION)
async def logout(user: CurrentUser, session: SessionDep, response: Response) -> None:
    await AuthService(session).logout(user_id=user.id, family_id=user.family_id)
    _clear_session_cookies(response)


@router.post(
    "/logout-all", status_code=status.HTTP_204_NO_CONTENT, dependencies=SESSION
)
async def logout_all(
    user: CurrentUser, session: SessionDep, response: Response
) -> None:
    await AuthService(session).logout(
        user_id=user.id, family_id=user.family_id, all_sessions=True
    )
    _clear_session_cookies(response)


@router.post(
    "/email-verification/request",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=GUARDED,
)
async def request_email_verification(
    data: schemas.EmailInput,
    session: SessionDep,
    mailer: MailerDep,
    background: BackgroundTasks,
) -> None:
    """Same answer whether or not the email has an unverified account."""
    letter = await AuthService(session).request_link(
        email=str(data.email), purpose="email_verify"
    )
    if letter:
        background.add_task(deliver, mailer, letter)


@router.post(
    "/email-verification/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=GUARDED,
)
async def confirm_email(data: schemas.TokenInput, session: SessionDep) -> None:
    await AuthService(session).confirm_email(data.token)


@router.post(
    "/password-reset/request",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=GUARDED,
)
async def request_password_reset(
    data: schemas.EmailInput,
    session: SessionDep,
    mailer: MailerDep,
    background: BackgroundTasks,
) -> None:
    """Same answer whether or not the email has an account."""
    letter = await AuthService(session).request_link(
        email=str(data.email), purpose="password_reset"
    )
    if letter:
        background.add_task(deliver, mailer, letter)


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=GUARDED,
)
async def confirm_password_reset(
    data: schemas.PasswordReset, session: SessionDep
) -> None:
    await AuthService(session).reset_password(data)
