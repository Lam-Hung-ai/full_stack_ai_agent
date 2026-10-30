from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping, and_, func, insert, select, text, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import now
from app.database.generated_tables import t_member_role_assignments as assignments
from app.database.generated_tables import t_organization_invitations as invitations
from app.database.generated_tables import t_organization_members as members
from app.database.generated_tables import t_organization_roles as roles
from app.database.generated_tables import t_organizations as organizations
from app.database.generated_tables import t_users as users

OWNER_ROLE = "owner"


class MemberRepository:
    """Memberships, their role assignments and invitations of one organization."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_organization(self, *, organization_id: UUID) -> None:
        """The lock every membership/role write takes by trigger: holding it
        first makes a check-then-write (last owner, pending invite) atomic."""
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(hashtextextended(:org, 0))"),
            {"org": str(organization_id)},
        )

    async def listing(
        self,
        *,
        organization_id: UUID,
        limit: int,
        offset: int,
        member_id: UUID | None = None,
    ) -> tuple[list[RowMapping], int]:
        """Active members with their active roles; `member_id` picks one."""
        held = (
            select(
                assignments.c.member_id,
                func.json_agg(
                    func.json_build_object(
                        "id",
                        roles.c.id,
                        "name",
                        roles.c.name,
                        "role_key",
                        roles.c.role_key,
                    )
                ).label("roles"),
            )
            .join(
                roles,
                and_(roles.c.id == assignments.c.role_id, roles.c.is_active.is_(True)),
            )
            .where(
                assignments.c.organization_id == organization_id,
                assignments.c.is_active.is_(True),
            )
            .group_by(assignments.c.member_id)
            .subquery()
        )
        where = [
            members.c.organization_id == organization_id,
            members.c.is_active.is_(True),
        ]
        if member_id is not None:
            where.append(members.c.id == member_id)
        total = (
            await self._session.execute(select(func.count()).where(*where))
        ).scalar_one()
        statement = (
            select(
                members.c.id,
                members.c.user_id,
                users.c.name,
                users.c.email,
                members.c.joined_at,
                func.coalesce(held.c.roles, text("'[]'::json")).label("roles"),
            )
            .join(users, users.c.id == members.c.user_id)
            .outerjoin(held, held.c.member_id == members.c.id)
            .where(*where)
            .order_by(func.lower(users.c.name), members.c.id)
            .limit(limit)
            .offset(offset)
        )
        return list((await self._session.execute(statement)).mappings()), total

    async def get(self, *, organization_id: UUID, member_id: UUID) -> RowMapping | None:
        """An active membership of the organization."""
        statement = select(members).where(
            members.c.organization_id == organization_id,
            members.c.id == member_id,
            members.c.is_active.is_(True),
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def by_user(
        self, *, organization_id: UUID, user_id: UUID
    ) -> RowMapping | None:
        """The user's membership row, active or not (one per user and org)."""
        statement = select(members).where(
            members.c.organization_id == organization_id,
            members.c.user_id == user_id,
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def has_active_email(self, *, organization_id: UUID, email: str) -> bool:
        statement = (
            select(members.c.id)
            .join(users, users.c.id == members.c.user_id)
            .where(
                members.c.organization_id == organization_id,
                members.c.is_active.is_(True),
                users.c.email == email,
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).first() is not None

    async def add(self, *, organization_id: UUID, user_id: UUID) -> UUID:
        statement = (
            insert(members)
            .values(organization_id=organization_id, user_id=user_id)
            .returning(members.c.id)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def reactivate(self, *, organization_id: UUID, member_id: UUID) -> None:
        await self._session.execute(
            update(members)
            .where(
                members.c.organization_id == organization_id, members.c.id == member_id
            )
            .values(is_active=True, left_at=None, joined_at=now())
        )

    async def deactivate(self, *, organization_id: UUID, member_id: UUID) -> None:
        """End a membership and its roles: rejoining starts as a plain member."""
        await self._session.execute(
            update(assignments)
            .where(
                assignments.c.organization_id == organization_id,
                assignments.c.member_id == member_id,
                assignments.c.is_active.is_(True),
            )
            .values(is_active=False)
        )
        await self._session.execute(
            update(members)
            .where(
                members.c.organization_id == organization_id, members.c.id == member_id
            )
            .values(is_active=False, left_at=now())
        )

    async def active_owners(self, *, organization_id: UUID) -> set[UUID]:
        statement = (
            select(members.c.id)
            .join(
                assignments,
                and_(
                    assignments.c.member_id == members.c.id,
                    assignments.c.is_active.is_(True),
                ),
            )
            .join(
                roles,
                and_(roles.c.id == assignments.c.role_id, roles.c.is_active.is_(True)),
            )
            .where(
                members.c.organization_id == organization_id,
                members.c.is_active.is_(True),
                roles.c.role_key == OWNER_ROLE,
            )
        )
        return set((await self._session.execute(statement)).scalars())

    async def active_roles(
        self, *, organization_id: UUID, role_ids: set[UUID]
    ) -> list[RowMapping]:
        statement = select(roles.c.id, roles.c.role_key).where(
            roles.c.organization_id == organization_id,
            roles.c.is_active.is_(True),
            roles.c.id.in_(role_ids),
        )
        return list((await self._session.execute(statement)).mappings())

    async def held_roles(
        self, *, organization_id: UUID, member_id: UUID
    ) -> list[RowMapping]:
        statement = (
            select(roles.c.id, roles.c.role_key)
            .join(assignments, assignments.c.role_id == roles.c.id)
            .where(
                assignments.c.organization_id == organization_id,
                assignments.c.member_id == member_id,
                assignments.c.is_active.is_(True),
                roles.c.is_active.is_(True),
            )
        )
        return list((await self._session.execute(statement)).mappings())

    async def role_by_key(self, *, organization_id: UUID, role_key: str) -> UUID:
        statement = select(roles.c.id).where(
            roles.c.organization_id == organization_id, roles.c.role_key == role_key
        )
        return (await self._session.execute(statement)).scalar_one()

    async def set_roles(
        self, *, organization_id: UUID, member_id: UUID, role_ids: set[UUID]
    ) -> None:
        """Exactly these roles active; assignment rows are reused, not deleted."""
        await self._session.execute(
            update(assignments)
            .where(
                assignments.c.organization_id == organization_id,
                assignments.c.member_id == member_id,
                assignments.c.role_id.not_in(role_ids),
                assignments.c.is_active.is_(True),
            )
            .values(is_active=False)
        )
        if not role_ids:
            return
        statement = upsert(assignments).values(
            [
                {
                    "organization_id": organization_id,
                    "member_id": member_id,
                    "role_id": r,
                }
                for r in role_ids
            ]
        )
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[
                    assignments.c.organization_id,
                    assignments.c.member_id,
                    assignments.c.role_id,
                ],
                set_={"is_active": True},
                where=assignments.c.is_active.is_(False),
            )
        )

    # Invitations

    async def expire_pending(self, *, organization_id: UUID) -> None:
        """Pending rows past their expiry become expired (schema comment: do
        it before reinviting, the pending index allows one per email)."""
        await self._session.execute(
            update(invitations)
            .where(
                invitations.c.organization_id == organization_id,
                invitations.c.status == "pending",
                invitations.c.expires_at <= now(),
            )
            .values(status="expired")
        )

    async def revoke_pending(
        self,
        *,
        organization_id: UUID,
        email: str | None = None,
        invitation_id: UUID | None = None,
    ) -> bool:
        statement = update(invitations).where(
            invitations.c.organization_id == organization_id,
            invitations.c.status == "pending",
        )
        if email is not None:
            statement = statement.where(invitations.c.email == email)
        if invitation_id is not None:
            statement = statement.where(invitations.c.id == invitation_id)
        result = await self._session.execute(
            statement.values(status="revoked").returning(invitations.c.id)
        )
        return result.first() is not None

    async def add_invitation(
        self,
        *,
        organization_id: UUID,
        email: str,
        invited_by: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> UUID:
        statement = (
            insert(invitations)
            .values(
                organization_id=organization_id,
                email=email,
                invited_by=invited_by,
                token_hash=token_hash,
                expires_at=expires_at,
            )
            .returning(invitations.c.id)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def pending_invitations(
        self, *, organization_id: UUID, invitation_id: UUID | None = None
    ) -> list[RowMapping]:
        statement = (
            select(
                invitations.c.id,
                invitations.c.email,
                invitations.c.status,
                invitations.c.expires_at,
                invitations.c.created_at,
                users.c.name.label("invited_by_name"),
            )
            .join(users, users.c.id == invitations.c.invited_by)
            .where(
                invitations.c.organization_id == organization_id,
                invitations.c.status == "pending",
                invitations.c.expires_at > now(),
            )
            .order_by(invitations.c.created_at.desc())
        )
        if invitation_id is not None:
            statement = statement.where(invitations.c.id == invitation_id)
        return list((await self._session.execute(statement)).mappings())

    async def invitation_by_token(
        self, *, token_hash: str, lock: bool = False
    ) -> RowMapping | None:
        statement = (
            select(
                invitations,
                organizations.c.name.label("organization_name"),
                organizations.c.is_active.label("organization_active"),
            )
            .join(organizations, organizations.c.id == invitations.c.organization_id)
            .where(invitations.c.token_hash == token_hash)
        )
        if lock:
            statement = statement.with_for_update(of=invitations)
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def mark_invitation(
        self, *, invitation_id: UUID, status: str, accepted_by: UUID | None = None
    ) -> None:
        await self._session.execute(
            update(invitations)
            .where(invitations.c.id == invitation_id)
            .values(
                status=status,
                accepted_by=accepted_by,
                accepted_at=now() if accepted_by else None,
            )
        )
