from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.handlers import fail
from app.modules.authorization.catalog import PERMISSIONS, PERSONAL_ALLOWED
from app.modules.authorization.repository import AuthorizationRepository
from app.modules.workspaces.schemas import WorkspaceContext


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

    async def require(
        self, workspace: WorkspaceContext, resource: str, action: str
    ) -> None:
        if not await self.can(workspace, resource, action):
            fail(
                403, "permission_denied", details={"permission": f"{resource}.{action}"}
            )

    async def sync_catalog(self) -> None:
        """Make the permissions table match the code catalog (insert or describe)."""
        await self._authorization.upsert_permissions(PERMISSIONS)
        await self._session.commit()
