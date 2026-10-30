from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.handlers import fail
from app.modules.authorization.catalog import PERMISSIONS, PERSONAL_ALLOWED
from app.modules.authorization.repository import AuthorizationRepository
from app.modules.authorization.schemas import (
    PermissionListResponse,
    PermissionResponse,
    RoleCreate,
    RoleListResponse,
    RoleResponse,
    RoleUpdate,
)
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import organization_of

OWNER_ROLE = "owner"
ROLE_MANAGE = ("role", "manage")


class AuthorizationService:
    def __init__(
        self, session: AsyncSession, repository: AuthorizationRepository | None = None
    ) -> None:
        self._session = session
        self._authorization = repository or AuthorizationRepository(session)

    async def can(
        self, workspace: WorkspaceContext, resource: str, action: str
    ) -> bool:
        if workspace.kind == "personal":
            return (resource, action) in PERSONAL_ALLOWED
        if workspace.member_id is None:
            return False
        return await self._authorization.member_has(
            member_id=workspace.member_id, resource=resource, action=action
        )

    async def allowed_actions(
        self, workspace: WorkspaceContext, resource: str
    ) -> frozenset[str]:
        """Every action of `resource` the workspace context may perform."""
        if workspace.kind == "personal":
            return frozenset(
                action for name, action in PERSONAL_ALLOWED if name == resource
            )
        if workspace.member_id is None:
            return frozenset()
        return frozenset(
            await self._authorization.member_actions(
                member_id=workspace.member_id, resource=resource
            )
        )

    async def require(
        self, workspace: WorkspaceContext, resource: str, action: str
    ) -> None:
        if not await self.can(workspace, resource, action):
            fail(
                403, "permission_denied", details={"permission": f"{resource}.{action}"}
            )

    async def permissions_of(self, workspace: WorkspaceContext) -> set[str]:
        """Every `resource.action` the workspace context may perform."""
        if workspace.kind == "personal":
            return {f"{resource}.{action}" for resource, action in PERSONAL_ALLOWED}
        if workspace.member_id is None:
            return set()
        return await self._authorization.member_permissions(
            member_id=workspace.member_id
        )

    async def is_owner(self, workspace: WorkspaceContext) -> bool:
        if workspace.member_id is None:
            return False
        return OWNER_ROLE in await self._authorization.member_role_keys(
            member_id=workspace.member_id
        )

    async def catalog(self) -> PermissionListResponse:
        rows = await self._authorization.catalog()
        return PermissionListResponse(
            data=[
                PermissionResponse.model_validate(
                    {**row, "key": f"{row['resource']}.{row['action']}"}
                )
                for row in rows
            ]
        )

    async def list_roles(self, workspace: WorkspaceContext) -> RoleListResponse:
        await self.require(workspace, *ROLE_MANAGE)
        rows = await self._authorization.roles(
            organization_id=organization_of(workspace)
        )
        return RoleListResponse(data=[_role(row) for row in rows])

    async def create_role(
        self, workspace: WorkspaceContext, data: RoleCreate
    ) -> RoleResponse:
        await self.require(workspace, *ROLE_MANAGE)
        keys = set(data.permissions)
        await self.check_grants(workspace, keys)
        org = organization_of(workspace)
        await self._ensure_free_name(org, data.name)
        try:
            role_id = await self._authorization.create_role(
                organization_id=org, name=data.name, description=data.description
            )
            await self._authorization.set_role_permissions(role_id=role_id, keys=keys)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            fail(409, "role_name_taken")
        return await self._get_role(org, role_id)

    async def update_role(
        self, workspace: WorkspaceContext, role_id: UUID, data: RoleUpdate
    ) -> RoleResponse:
        await self.require(workspace, *ROLE_MANAGE)
        org = organization_of(workspace)
        role = await self._get_role(org, role_id)
        if role.locked or (role.role_key and "name" in data.model_fields_set):
            fail(409, "role_locked")
        values = data.model_dump(include={"name", "description"}, exclude_unset=True)
        if "name" in values:
            if values["name"] is None:
                fail(422, "invalid_role_name")
            await self._ensure_free_name(org, values["name"], except_id=role_id)
        if data.permissions is not None:
            keys = set(data.permissions)
            # Only what is added must be held: removing a grant escalates nothing.
            await self.check_grants(workspace, keys - set(role.permissions))
        try:
            if values:
                await self._authorization.update_role(
                    organization_id=org, role_id=role_id, values=values
                )
            if data.permissions is not None:
                await self._authorization.set_role_permissions(
                    role_id=role_id, keys=set(data.permissions)
                )
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            fail(409, "role_name_taken")
        return await self._get_role(org, role_id)

    async def delete_role(self, workspace: WorkspaceContext, role_id: UUID) -> None:
        await self.require(workspace, *ROLE_MANAGE)
        org = organization_of(workspace)
        role = await self._get_role(org, role_id)
        if role.role_key:
            fail(409, "role_locked")
        await self._authorization.delete_role(organization_id=org, role_id=role_id)
        await self._session.commit()

    async def sync_catalog(self) -> None:
        """Make the permissions table match the code catalog (insert or
        describe), and give owner roles whatever is new (QD-24)."""
        await self._authorization.upsert_permissions(PERMISSIONS)
        await self._authorization.grant_all_to_owner_roles()
        await self._session.commit()

    async def _get_role(self, organization_id: UUID, role_id: UUID) -> RoleResponse:
        rows = await self._authorization.roles(
            organization_id=organization_id, role_id=role_id
        )
        if not rows:
            fail(404, "role_not_found")
        return _role(rows[0])

    async def check_grants(self, workspace: WorkspaceContext, keys: set[str]) -> None:
        """Known permissions only, and none the actor lacks unless an owner."""
        known = {f"{item.resource}.{item.action}" for item in PERMISSIONS}
        if unknown := keys - known:
            fail(422, "unknown_permission", details={"permissions": sorted(unknown)})
        if await self.is_owner(workspace):
            return
        if missing := keys - await self.permissions_of(workspace):
            fail(403, "permission_escalation", details={"permissions": sorted(missing)})

    async def _ensure_free_name(
        self, organization_id: UUID, name: str, except_id: UUID | None = None
    ) -> None:
        if await self._authorization.name_taken(
            organization_id=organization_id, name=name, except_id=except_id
        ):
            fail(409, "role_name_taken")


def _role(row) -> RoleResponse:
    return RoleResponse.model_validate(
        {
            **row,
            "permissions": list(row["permissions"]),
            "locked": row["role_key"] == OWNER_ROLE,
        }
    )
