"""Memberships, role assignments and invitations (O02, O07; QD-24, QD-25).

Owner/admin manage members inside their organization only. Two guards keep
that from becoming a way up: only an owner gives or takes the owner role or
removes an owner, and nobody hands out a role granting what they lack. The
organization always keeps an active owner (also enforced by a deferred
trigger, checked here first for a clear error).
"""

from datetime import timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import Principal
from app.common.email import Letter
from app.common.exceptions.handlers import fail
from app.common.schemas.pagination import PageParams, Pagination
from app.config.security import digest, new_token, now
from app.config.settings import get_settings
from app.database.session import SessionLocal
from app.modules.agent.runner import Runner
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.authorization.repository import AuthorizationRepository
from app.modules.authorization.service import AuthorizationService
from app.modules.conversations.service import TurnService
from app.modules.members.letters import invitation_letter
from app.modules.members.repository import OWNER_ROLE, MemberRepository
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
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService, organization_of

MEMBER_MANAGE = ("member", "manage")
ROLE_MANAGE = ("role", "manage")
MEMBER_ROLE = "member"


class MemberService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MemberRepository | None = None,
        *,
        runner: Runner | None = None,
    ) -> None:
        self._session = session
        self._members = repository or MemberRepository(session)
        self._authorization = AuthorizationService(session)
        self._runner = runner

    async def list(
        self, workspace: WorkspaceContext, params: PageParams
    ) -> MemberListResponse:
        await self._authorization.require(workspace, *MEMBER_MANAGE)
        rows, total = await self._members.listing(
            organization_id=organization_of(workspace),
            limit=params.page_size,
            offset=params.offset,
        )
        return MemberListResponse(
            data=[MemberResponse.model_validate(dict(row)) for row in rows],
            pagination=Pagination.of(params, total),
        )

    async def update_roles(
        self, workspace: WorkspaceContext, member_id: UUID, data: MemberUpdate
    ) -> MemberResponse:
        await self._authorization.require(workspace, *ROLE_MANAGE)
        org = organization_of(workspace)
        await self._members.lock_organization(organization_id=org)
        await self._require_member(org, member_id)
        wanted = set(data.role_ids)
        found = await self._members.active_roles(organization_id=org, role_ids=wanted)
        if len(found) != len(wanted):
            fail(422, "unknown_role")
        held = await self._members.held_roles(organization_id=org, member_id=member_id)
        changed = {row["id"] for row in held} ^ wanted
        owner_rows = [row for row in [*found, *held] if row["role_key"] == OWNER_ROLE]
        if any(row["id"] in changed for row in owner_rows):
            await self._require_owner(workspace)
            if not any(row["role_key"] == OWNER_ROLE for row in found):
                await self._keep_an_owner(org, leaving=member_id)
        added = wanted - {row["id"] for row in held}
        await self._authorization.check_grants(
            workspace, await self._permissions_of_roles(org, added)
        )
        await self._members.set_roles(
            organization_id=org, member_id=member_id, role_ids=wanted
        )
        await self._session.commit()
        return await self._view(org, member_id)

    async def remove(self, workspace: WorkspaceContext, member_id: UUID) -> None:
        await self._authorization.require(workspace, *MEMBER_MANAGE)
        org = organization_of(workspace)
        await self._members.lock_organization(organization_id=org)
        target = await self._require_member(org, member_id)
        if member_id in await self._members.active_owners(organization_id=org):
            await self._require_owner(workspace)
            await self._keep_an_owner(org, leaving=member_id)
        await self._depart(workspace, org, member_id, target["user_id"])

    async def leave(self, workspace: WorkspaceContext, user: Principal) -> None:
        org = organization_of(workspace)
        await self._members.lock_organization(organization_id=org)
        member = await self._members.by_user(organization_id=org, user_id=user.id)
        if member is None or not member["is_active"]:
            fail(404, "organization_not_found")
        await self._keep_an_owner(org, leaving=member["id"])
        await self._depart(workspace, org, member["id"], user.id)

    # Invitations

    async def list_invitations(
        self, workspace: WorkspaceContext
    ) -> InvitationListResponse:
        await self._authorization.require(workspace, *MEMBER_MANAGE)
        rows = await self._members.pending_invitations(
            organization_id=organization_of(workspace)
        )
        return InvitationListResponse(
            data=[InvitationResponse.model_validate(dict(row)) for row in rows]
        )

    async def invite(
        self, workspace: WorkspaceContext, user: Principal, data: InvitationCreate
    ) -> tuple[InvitationResponse, Letter]:
        """A new link for the email; one still pending is revoked by it."""
        await self._authorization.require(workspace, *MEMBER_MANAGE)
        org = organization_of(workspace)
        email = str(data.email)
        await self._members.lock_organization(organization_id=org)
        if await self._members.has_active_email(organization_id=org, email=email):
            fail(409, "already_member")
        await self._members.expire_pending(organization_id=org)
        await self._members.revoke_pending(organization_id=org, email=email)
        raw = new_token()
        invitation_id = await self._members.add_invitation(
            organization_id=org,
            email=email,
            invited_by=user.id,
            token_hash=digest(raw),
            expires_at=now() + timedelta(days=get_settings().invitation_days),
        )
        await self._session.commit()
        (row,) = await self._members.pending_invitations(
            organization_id=org, invitation_id=invitation_id
        )
        invitation = await self._members.invitation_by_token(token_hash=digest(raw))
        assert invitation is not None
        letter = invitation_letter(
            to=email,
            organization_name=invitation["organization_name"],
            inviter_name=user.name,
            token=raw,
        )
        return InvitationResponse.model_validate(dict(row)), letter

    async def revoke_invitation(
        self, workspace: WorkspaceContext, invitation_id: UUID
    ) -> None:
        await self._authorization.require(workspace, *MEMBER_MANAGE)
        if not await self._members.revoke_pending(
            organization_id=organization_of(workspace), invitation_id=invitation_id
        ):
            fail(404, "invitation_not_found")
        await self._session.commit()

    async def preview(self, token: str) -> InvitationPreview:
        invitation = await self._members.invitation_by_token(token_hash=digest(token))
        if invitation is None or not invitation["organization_active"]:
            fail(404, "invitation_not_found")
        status = invitation["status"]
        if status == "pending" and invitation["expires_at"] <= now():
            status = "expired"
        account = await AuthRepository(self._session).user_by_email(
            email=invitation["email"]
        )
        return InvitationPreview(
            organization_name=invitation["organization_name"],
            email=invitation["email"],
            status=status,
            account_exists=account is not None,
        )

    async def accept(self, *, user: Principal, token: str) -> JoinedOrganization:
        invitation = await self._open_invitation(token)
        # The link was sent to this address: only its account may use it.
        if invitation["email"].lower() != user.email.lower():
            fail(403, "invitation_email_mismatch")
        return await self._join(invitation, user.id)

    async def register(self, data: InvitationRegister) -> JoinedOrganization:
        """Open to anyone holding the link, also when sign-up is closed: the
        invitation is what authorizes the account (QD-25)."""
        invitation = await self._open_invitation(data.token)
        user = await AuthService(self._session).create_account(
            name=data.name,
            email=invitation["email"],
            password=data.password,
            email_verified=True,
        )
        return await self._join(invitation, user["id"])

    async def _open_invitation(self, token: str):
        invitation = await self._members.invitation_by_token(
            token_hash=digest(token), lock=True
        )
        if invitation is None or not invitation["organization_active"]:
            fail(404, "invitation_not_found")
        if invitation["status"] == "pending" and invitation["expires_at"] <= now():
            await self._members.mark_invitation(
                invitation_id=invitation["id"], status="expired"
            )
            await self._session.commit()
            fail(410, "invitation_expired")
        if invitation["status"] != "pending":
            fail(410, f"invitation_{invitation['status']}")
        return invitation

    async def _join(self, invitation, user_id: UUID) -> JoinedOrganization:
        """Create or reactivate the membership as a plain member, verify the
        email (the link reached it) and consume the invitation, atomically."""
        org = invitation["organization_id"]
        await self._members.lock_organization(organization_id=org)
        member = await self._members.by_user(organization_id=org, user_id=user_id)
        if member is None or not member["is_active"]:
            if member is None:
                member_id = await self._members.add(
                    organization_id=org, user_id=user_id
                )
            else:
                member_id = member["id"]
                await self._members.reactivate(organization_id=org, member_id=member_id)
            role_id = await self._members.role_by_key(
                organization_id=org, role_key=MEMBER_ROLE
            )
            await self._members.set_roles(
                organization_id=org, member_id=member_id, role_ids={role_id}
            )
        await AuthRepository(self._session).mark_email_verified(user_id=user_id)
        await self._members.mark_invitation(
            invitation_id=invitation["id"], status="accepted", accepted_by=user_id
        )
        await self._session.commit()
        workspace = await WorkspaceService(self._session).organization_context(
            user_id=user_id, organization_id=org
        )
        return JoinedOrganization(organization_id=org, workspace_id=workspace.id)

    async def _depart(
        self, workspace: WorkspaceContext, org: UUID, member_id: UUID, user_id: UUID
    ) -> None:
        await self._members.deactivate(organization_id=org, member_id=member_id)
        await self._session.commit()
        if self._runner is not None:
            await TurnService(
                self._session, runner=self._runner, session_factory=SessionLocal
            ).stop_departed(workspace_id=workspace.id, user_id=user_id)

    async def _require_member(self, org: UUID, member_id: UUID):
        member = await self._members.get(organization_id=org, member_id=member_id)
        if member is None:
            fail(404, "member_not_found")
        return member

    async def _require_owner(self, workspace: WorkspaceContext) -> None:
        if not await self._authorization.is_owner(workspace):
            fail(403, "owner_required")

    async def _keep_an_owner(self, org: UUID, *, leaving: UUID) -> None:
        if not await self._members.active_owners(organization_id=org) - {leaving}:
            fail(409, "last_owner")

    async def _permissions_of_roles(self, org: UUID, role_ids: set[UUID]) -> set[str]:
        if not role_ids:
            return set()
        rows = await AuthorizationRepository(self._session).roles(organization_id=org)
        return {
            key for row in rows if row["id"] in role_ids for key in row["permissions"]
        }

    async def _view(self, org: UUID, member_id: UUID) -> MemberResponse:
        rows, _ = await self._members.listing(
            organization_id=org, limit=1, offset=0, member_id=member_id
        )
        return MemberResponse.model_validate(dict(rows[0]))
