from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.modules.authorization.service import AuthorizationService
from app.modules.organizations.repository import OrganizationRepository
from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService, organization_of


class OrganizationService:
    def __init__(
        self, session: AsyncSession, repository: OrganizationRepository | None = None
    ) -> None:
        self._session = session
        self._organizations = repository or OrganizationRepository(session)
        self._authorization = AuthorizationService(session)

    async def create(
        self, *, user: Principal, data: OrganizationCreate
    ) -> OrganizationResponse:
        organization_id = await self._organizations.create(
            name=data.name, created_by=user.id
        )
        await self._session.commit()
        workspace = await WorkspaceService(self._session).organization_context(
            user_id=user.id, organization_id=organization_id
        )
        return await self.get(workspace)

    async def get(self, workspace: WorkspaceContext) -> OrganizationResponse:
        organization_id = organization_of(workspace)
        row = await self._organizations.get(organization_id=organization_id)
        if row is None:
            fail(404, "organization_not_found")
        return OrganizationResponse.model_validate(
            {
                **row,
                "permissions": sorted(
                    await self._authorization.permissions_of(workspace)
                ),
                "is_owner": await self._authorization.is_owner(workspace),
            }
        )

    async def update(
        self, workspace: WorkspaceContext, data: OrganizationUpdate
    ) -> OrganizationResponse:
        await self._authorization.require(workspace, "organization", "manage")
        await self._organizations.rename(
            organization_id=organization_of(workspace), name=data.name
        )
        await self._session.commit()
        return await self.get(workspace)
