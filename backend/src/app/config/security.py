"""Security primitives: password hashing, opaque tokens, access JWT.

Pattern taken from hr-ai (QD-12) with one change: the access token carries no
organization claim. Login sessions are global (`refresh_tokens` has no
organization column) and the workspace comes from the request path or the
conversation, checked against membership on every request.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from starlette.concurrency import run_in_threadpool

from app.common.exceptions.handlers import fail
from app.config.settings import get_settings

_hasher = PasswordHasher()
#: Verified when the email is unknown so both paths cost the same time.
_DUMMY_HASH = _hasher.hash(secrets.token_urlsafe(32))


def now() -> datetime:
    return datetime.now(UTC)


def new_token() -> str:
    return secrets.token_urlsafe(48)


def digest(token: str) -> str:
    """Tokens are stored as SHA-256 digests; the raw value only reaches the client."""
    return hashlib.sha256(token.encode()).hexdigest()


async def hash_password(password: str) -> str:
    return await run_in_threadpool(_hasher.hash, password)


async def verify_password(encoded: str | None, password: str) -> bool:
    try:
        return await run_in_threadpool(_hasher.verify, encoded or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False


def access_token(user_id: UUID, family_id: UUID) -> str:
    settings = get_settings()
    issued = now()
    return jwt.encode(
        {
            "sub": str(user_id),
            "sid": str(family_id),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
            "iat": issued,
            "exp": issued + timedelta(minutes=settings.access_token_minutes),
            "type": "access",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str) -> tuple[UUID, UUID]:
    """Return `(user_id, family_id)` of a valid access token, or fail with 401."""
    settings = get_settings()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "sid", "iat", "exp", "type"]},
        )
        if claims["type"] != "access":
            raise ValueError("not an access token")
        return UUID(claims["sub"]), UUID(claims["sid"])
    except (jwt.InvalidTokenError, ValueError, TypeError, KeyError):
        fail(401, "invalid_access_token")
