from uuid import UUID

from sqlalchemy import RowMapping, Select, and_, func, literal, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_organization_members as members
from app.database.generated_tables import t_organizations as organizations
from app.database.generated_tables import t_workspaces as workspaces


class WorkspaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _accessible(self, user_id: UUID) -> Select:
        """Workspaces the user may enter: their personal one, and each active
        organization where their membership is active. Checked on every request,
        never cached in the login session."""
        return (
            select(
                workspaces.c.id,
                workspaces.c.kind,
                workspaces.c.organization_id,
                organizations.c.name,
                members.c.id.label("member_id"),
            )
            .outerjoin(
                organizations,
                and_(
                    organizations.c.id == workspaces.c.organization_id,
                    organizations.c.is_active.is_(True),
                ),
            )
            .outerjoin(
                members,
                and_(
                    members.c.organization_id == organizations.c.id,
                    members.c.user_id == user_id,
                    members.c.is_active.is_(True),
                ),
            )
            .where(
                or_(
                    workspaces.c.personal_user_id == user_id,
                    members.c.id.is_not(None),
                )
            )
        )

    async def list_for_user(
        self, *, user_id: UUID, limit: int, offset: int
    ) -> tuple[list[RowMapping], int]:
        accessible = self._accessible(user_id).subquery()
        total = (
            await self._session.execute(select(func.count()).select_from(accessible))
        ).scalar_one()
        statement = (
            select(accessible)
            # Personal first, then organizations by name; id keeps the order stable.
            .order_by(
                (accessible.c.kind == literal("personal")).desc(),
                accessible.c.name,
                accessible.c.id,
            )
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).mappings().all()
        return list(rows), total

    async def accessible_by_id(
        self, *, user_id: UUID, workspace_id: UUID
    ) -> RowMapping | None:
        statement = self._accessible(user_id).where(workspaces.c.id == workspace_id)
        return (await self._session.execute(statement)).mappings().one_or_none()
