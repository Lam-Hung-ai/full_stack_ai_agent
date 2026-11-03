from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.exceptions.handlers import fail
from app.common.schemas.pagination import PageParams, Pagination
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.schemas import (
    WorkspaceContext,
    WorkspaceListResponse,
    WorkspaceResponse,
)


class WorkspaceService:
    def __init__(
        self, session: AsyncSession, repository: WorkspaceRepository | None = None
    ) -> None:
        self._workspaces = repository or WorkspaceRepository(session)

    async def list_for_user(
        self, *, user_id: UUID, params: PageParams
    ) -> WorkspaceListResponse:
        rows, total = await self._workspaces.list_for_user(
            user_id=user_id, limit=params.page_size, offset=params.offset
        )
        return WorkspaceListResponse(
            data=[WorkspaceResponse.model_validate(dict(row)) for row in rows],
            pagination=Pagination.of(params, total),
        )

    async def get(self, *, user_id: UUID, workspace_id: UUID) -> WorkspaceResponse:
        row = await self._require(user_id=user_id, workspace_id=workspace_id)
        return WorkspaceResponse.model_validate(dict(row))

    async def context(self, *, user_id: UUID, workspace_id: UUID) -> WorkspaceContext:
        row = await self._require(user_id=user_id, workspace_id=workspace_id)
        return _context(row)

    async def organization_context(
        self, *, user_id: UUID, organization_id: UUID
    ) -> WorkspaceContext:
        """The workspace of an organization the user is an active member of."""
        row = await self._workspaces.accessible_by_organization(
            user_id=user_id, organization_id=organization_id
        )
        if row is None:
            fail(404, "organization_not_found")
        return _context(row)

    async def _require(self, *, user_id: UUID, workspace_id: UUID):
        row = await self._workspaces.accessible_by_id(
            user_id=user_id, workspace_id=workspace_id
        )
        # 404 rather than 403: a non-member cannot tell whether it exists.
        if row is None:
            fail(404, "workspace_not_found")
        return row


def _context(row) -> WorkspaceContext:
    return WorkspaceContext(
        id=row["id"],
        kind=row["kind"],
        organization_id=row["organization_id"],
        member_id=row["member_id"],
    )


def organization_of(workspace: WorkspaceContext) -> UUID:
    """The organization of an organization workspace; 404 for a personal one."""
    if workspace.organization_id is None:
        fail(404, "organization_not_found")
    return workspace.organization_id
