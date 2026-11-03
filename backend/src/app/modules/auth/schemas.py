from pydantic import BaseModel, EmailStr, Field, field_validator

from app.common.schemas.common import Input, Name, Password
from app.modules.users.schemas import UserResponse
from app.modules.workspaces.schemas import WorkspaceResponse


class EmailInput(Input):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def _normalize(cls, value: object) -> object:
        return value.strip().lower() if isinstance(value, str) else value


class Register(EmailInput):
    name: Name
    password: Password


class Login(EmailInput):
    password: str = Field(min_length=1, max_length=256)
    #: Keep the refresh cookie after the browser closes.
    remember: bool = False


class TokenInput(Input):
    """A single-use token from a letter's link."""

    token: str = Field(min_length=1, max_length=256)


class PasswordReset(TokenInput):
    password: Password


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class SessionResponse(TokenResponse):
    """Everything the frontend needs to open a session, in one round trip."""

    user: UserResponse
    workspaces: list[WorkspaceResponse]
