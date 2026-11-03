from uuid import UUID

from sqlalchemy import RowMapping, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_organizations as organizations
from app.database.generated_tables import t_workspaces as workspaces


class OrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, name: str, created_by: UUID) -> UUID:
        """The insert trigger provisions the workspace, the creator's
        membership and the owner, admin and member roles."""
        statement = (
            insert(organizations)
            .values(name=name, created_by=created_by)
            .returning(organizations.c.id)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def get(self, *, organization_id: UUID) -> RowMapping | None:
        statement = (
            select(
                organizations.c.id,
                organizations.c.name,
                organizations.c.created_at,
                workspaces.c.id.label("workspace_id"),
            )
            .join(workspaces, workspaces.c.organization_id == organizations.c.id)
            .where(
                organizations.c.id == organization_id,
                organizations.c.is_active.is_(True),
            )
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def rename(self, *, organization_id: UUID, name: str) -> None:
        await self._session.execute(
            update(organizations)
            .where(organizations.c.id == organization_id)
            .values(name=name)
        )
