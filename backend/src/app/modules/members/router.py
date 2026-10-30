from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.organization import CurrentOrganization
from app.common.dependencies.rate_limit import rate_limit
from app.common.email import MailerDep, deliver
from app.common.schemas.pagination import PageParams, page_params
from app.database.session import SessionDep
from app.modules.agent.dependencies import RunnerDep
from app.modules.auth.schemas import TokenInput
from app.modules.members.schemas import (
    InvitationCreate,
    InvitationListResponse,
    InvitationPreview,
    InvitationRegister,
    InvitationResponse,
    JoinedOrganization,
    MemberListResponse,
    MemberResponse,
    MemberUpdate,
)
from app.modules.members.service import MemberService

router = APIRouter(prefix="/organizations/{organization_id}", tags=["Members"])
#: Token endpoints: whoever holds an invitation link, signed in or not.
invitations_router = APIRouter(
    prefix="/invitations",
    tags=["Members"],
    dependencies=[Depends(rate_limit("invitations"))],
)


@router.get("/members", response_model=MemberListResponse)
async def list_members(
    organization: CurrentOrganization,
    session: SessionDep,
    params: Annotated[PageParams, Depends(page_params)],
) -> MemberListResponse:
    return await MemberService(session).list(organization, params)


@router.patch("/members/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: UUID,
    data: MemberUpdate,
    organization: CurrentOrganization,
    session: SessionDep,
) -> MemberResponse:
    return await MemberService(session).update_roles(organization, member_id, data)


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: UUID,
    organization: CurrentOrganization,
    session: SessionDep,
    runner: RunnerDep,
) -> None:
    """End the membership; the member's unfinished turns here are stopped."""
    await MemberService(session, runner=runner).remove(organization, member_id)


@router.post("/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_organization(
    organization: CurrentOrganization,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
) -> None:
    await MemberService(session, runner=runner).leave(organization, user)


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    organization: CurrentOrganization, session: SessionDep
) -> InvitationListResponse:
    return await MemberService(session).list_invitations(organization)


@router.post(
    "/invitations",
    status_code=status.HTTP_201_CREATED,
    response_model=InvitationResponse,
)
async def invite(
    data: InvitationCreate,
    organization: CurrentOrganization,
    user: CurrentUser,
    session: SessionDep,
    mailer: MailerDep,
    background: BackgroundTasks,
) -> InvitationResponse:
    """Sending again to the same email replaces the pending link."""
    invitation, letter = await MemberService(session).invite(organization, user, data)
    background.add_task(deliver, mailer, letter)
    return invitation


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    invitation_id: UUID, organization: CurrentOrganization, session: SessionDep
) -> None:
    await MemberService(session).revoke_invitation(organization, invitation_id)


# The token travels in the body, never in a URL that proxies may log.


@invitations_router.post("/preview", response_model=InvitationPreview)
async def preview_invitation(
    data: TokenInput, session: SessionDep
) -> InvitationPreview:
    return await MemberService(session).preview(data.token)


@invitations_router.post("/accept", response_model=JoinedOrganization)
async def accept_invitation(
    data: TokenInput, user: CurrentUser, session: SessionDep
) -> JoinedOrganization:
    return await MemberService(session).accept(user=user, token=data.token)


@invitations_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=JoinedOrganization,
)
async def register_with_invitation(
    data: InvitationRegister, session: SessionDep
) -> JoinedOrganization:
    return await MemberService(session).register(data)
