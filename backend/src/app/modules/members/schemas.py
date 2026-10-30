from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas.common import Input, Name, Password
from app.common.schemas.pagination import Pagination
from app.modules.auth.schemas import EmailInput, TokenInput

InvitationStatus = Literal["pending", "accepted", "revoked", "expired"]


class MemberRole(BaseModel):
    id: UUID
    name: str
    role_key: str | None


class MemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    email: str
    joined_at: datetime
    roles: list[MemberRole]


class MemberListResponse(BaseModel):
    data: list[MemberResponse]
    pagination: Pagination


class MemberUpdate(Input):
    """The member's roles after the change, all of them."""

    role_ids: list[UUID] = Field(min_length=1, max_length=50)


class InvitationCreate(EmailInput):
    """Invitees join with the member role; roles change after they join."""


class InvitationResponse(BaseModel):
    id: UUID
    email: str
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime
    invited_by_name: str


class InvitationListResponse(BaseModel):
    data: list[InvitationResponse]


class InvitationPreview(BaseModel):
    """What the invitation page shows before the invitee acts."""

    organization_name: str
    email: str
    status: InvitationStatus
    #: Whether to offer signing in (an account exists) or creating one.
    account_exists: bool


class InvitationRegister(TokenInput):
    """Create the invited email's account and join in one step."""

    name: Name
    password: Password


class JoinedOrganization(BaseModel):
    organization_id: UUID
    workspace_id: UUID
