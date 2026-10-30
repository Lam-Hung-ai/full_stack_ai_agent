from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_member_role_assignments as assignments
from app.database.generated_tables import t_organization_roles as roles
from app.database.generated_tables import t_permissions as permissions
from app.database.generated_tables import t_role_permissions as role_permissions
from app.modules.authorization.catalog import Permission


class AuthorizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_permissions(self, catalog: tuple[Permission, ...]) -> None:
        statement = insert(permissions).values([item._asdict() for item in catalog])
        await self._session.execute(
            statement.on_conflict_do_update(
                index_elements=[permissions.c.resource, permissions.c.action],
                set_={"description": statement.excluded.description},
            )
        )

    async def member_has(self, *, member_id: UUID, resource: str, action: str) -> bool:
        """Union of grants from the member's active role assignments."""
        statement = (
            select(permissions.c.id)
            .select_from(assignments)
            .join(
                roles,
                and_(roles.c.id == assignments.c.role_id, roles.c.is_active.is_(True)),
            )
            .join(role_permissions, role_permissions.c.role_id == roles.c.id)
            .join(permissions, permissions.c.id == role_permissions.c.permission_id)
            .where(
                assignments.c.member_id == member_id,
                assignments.c.is_active.is_(True),
                permissions.c.resource == resource,
                permissions.c.action == action,
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).first() is not None
