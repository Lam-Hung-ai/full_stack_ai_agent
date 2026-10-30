from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.common.dependencies.auth import CurrentUser
from app.database.session import SessionDep
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService


async def current_organization(
    organization_id: UUID, user: CurrentUser, session: SessionDep
) -> WorkspaceContext:
    """Resolve `{organization_id}` from the path to the organization's workspace
    context. Active membership is re-checked on every request; 404 otherwise."""
    return await WorkspaceService(session).organization_context(
        user_id=user.id, organization_id=organization_id
    )


CurrentOrganization = Annotated[WorkspaceContext, Depends(current_organization)]
