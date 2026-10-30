from typing import Any
from uuid import UUID

from sqlalchemy import (
    RowMapping,
    Text,
    and_,
    delete,
    func,
    literal,
    select,
    tuple_,
    update,
)
from sqlalchemy.dialects.postgresql import aggregate_order_by, array, array_agg, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_member_role_assignments as assignments
from app.database.generated_tables import t_organization_members as members
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

    async def grant_all_to_owner_roles(self) -> None:
        """Owner roles hold the whole catalog, including permissions added
        after their organization was created (QD-24, RR-15)."""
        await self._session.execute(
            insert(role_permissions)
            .from_select(
                ["role_id", "permission_id"],
                select(roles.c.id, permissions.c.id)
                .select_from(roles)
                .join(permissions, literal(True))
                .where(roles.c.role_key == "owner"),
            )
            .on_conflict_do_nothing()
        )

    async def catalog(self) -> list[RowMapping]:
        statement = select(
            permissions.c.resource, permissions.c.action, permissions.c.description
        ).order_by(permissions.c.resource, permissions.c.action)
        return list((await self._session.execute(statement)).mappings())

    async def member_permissions(self, *, member_id: UUID) -> set[str]:
        """Every `resource.action` the member's active roles grant."""
        statement = (
            self._granted(member_id)
            .with_only_columns(permissions.c.resource, permissions.c.action)
            .distinct()
        )
        rows = await self._session.execute(statement)
        return {f"{resource}.{action}" for resource, action in rows}

    async def member_role_keys(self, *, member_id: UUID) -> set[str]:
        statement = (
            select(roles.c.role_key)
            .join(assignments, assignments.c.role_id == roles.c.id)
            .where(
                assignments.c.member_id == member_id,
                assignments.c.is_active.is_(True),
                roles.c.is_active.is_(True),
                roles.c.role_key.is_not(None),
            )
        )
        return set((await self._session.execute(statement)).scalars())

    async def roles(
        self, *, organization_id: UUID, role_id: UUID | None = None
    ) -> list[RowMapping]:
        """Roles with their permission keys and active member count."""
        granted = (
            select(
                role_permissions.c.role_id,
                array_agg(
                    aggregate_order_by(
                        permissions.c.resource + "." + permissions.c.action,
                        permissions.c.resource,
                        permissions.c.action,
                    )
                ).label("permissions"),
            )
            .join(permissions, permissions.c.id == role_permissions.c.permission_id)
            .group_by(role_permissions.c.role_id)
            .subquery()
        )
        holders = (
            select(assignments.c.role_id, func.count().label("member_count"))
            .join(
                members,
                and_(
                    members.c.id == assignments.c.member_id,
                    members.c.is_active.is_(True),
                ),
            )
            .where(
                assignments.c.organization_id == organization_id,
                assignments.c.is_active.is_(True),
            )
            .group_by(assignments.c.role_id)
            .subquery()
        )
        statement = (
            select(
                roles.c.id,
                roles.c.name,
                roles.c.role_key,
                roles.c.description,
                func.coalesce(granted.c.permissions, array([], type_=Text)).label(
                    "permissions"
                ),
                func.coalesce(holders.c.member_count, 0).label("member_count"),
            )
            .outerjoin(granted, granted.c.role_id == roles.c.id)
            .outerjoin(holders, holders.c.role_id == roles.c.id)
            .where(
                roles.c.organization_id == organization_id,
                roles.c.is_active.is_(True),
            )
            # Built-in roles first, in rank order, then the rest by name.
            .order_by(
                func.array_position(
                    array(["owner", "admin", "member"]), roles.c.role_key
                ).nulls_last(),
                func.lower(roles.c.name),
            )
        )
        if role_id is not None:
            statement = statement.where(roles.c.id == role_id)
        return list((await self._session.execute(statement)).mappings())

    async def name_taken(
        self, *, organization_id: UUID, name: str, except_id: UUID | None = None
    ) -> bool:
        statement = select(roles.c.id).where(
            roles.c.organization_id == organization_id,
            func.lower(roles.c.name) == name.lower(),
        )
        if except_id is not None:
            statement = statement.where(roles.c.id != except_id)
        return (await self._session.execute(statement.limit(1))).first() is not None

    async def create_role(
        self, *, organization_id: UUID, name: str, description: str | None
    ) -> UUID:
        statement = (
            insert(roles)
            .values(organization_id=organization_id, name=name, description=description)
            .returning(roles.c.id)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def update_role(
        self, *, organization_id: UUID, role_id: UUID, values: dict[str, Any]
    ) -> None:
        await self._session.execute(
            update(roles)
            .where(roles.c.organization_id == organization_id, roles.c.id == role_id)
            .values(**values)
        )

    async def set_role_permissions(self, *, role_id: UUID, keys: set[str]) -> None:
        await self._session.execute(
            delete(role_permissions).where(role_permissions.c.role_id == role_id)
        )
        if not keys:
            return
        pairs = [tuple(key.split(".", 1)) for key in keys]
        await self._session.execute(
            insert(role_permissions).from_select(
                ["role_id", "permission_id"],
                select(literal(role_id), permissions.c.id).where(
                    tuple_(permissions.c.resource, permissions.c.action).in_(pairs)
                ),
            )
        )

    async def delete_role(self, *, organization_id: UUID, role_id: UUID) -> None:
        """Assignments go with the role (their FK restricts the delete)."""
        await self._session.execute(
            delete(assignments).where(
                assignments.c.organization_id == organization_id,
                assignments.c.role_id == role_id,
            )
        )
        await self._session.execute(
            delete(roles).where(
                roles.c.organization_id == organization_id, roles.c.id == role_id
            )
        )

    async def member_has(self, *, member_id: UUID, resource: str, action: str) -> bool:
        """Union of grants from the member's active role assignments."""
        statement = (
            self._granted(member_id)
            .where(permissions.c.resource == resource, permissions.c.action == action)
            .limit(1)
        )
        return (await self._session.execute(statement)).first() is not None

    async def member_actions(self, *, member_id: UUID, resource: str) -> set[str]:
        statement = self._granted(member_id).where(permissions.c.resource == resource)
        return set((await self._session.execute(statement)).scalars())

    @staticmethod
    def _granted(member_id: UUID):
        return (
            select(permissions.c.action)
            .distinct()
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
            )
        )
