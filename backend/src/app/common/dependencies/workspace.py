from typing import Annotated
from uuid import UUID

from fastapi import Depends

from app.common.dependencies.auth import CurrentUser
from app.database.session import SessionDep
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService


async def current_workspace(
    workspace_id: UUID, user: CurrentUser, session: SessionDep
) -> WorkspaceContext:
    """Resolve `{workspace_id}` from the path for the current user (QD-10).

    Membership is re-checked on every request; a removed member loses access
    immediately even with a valid access token.
    """
    return await WorkspaceService(session).context(
        user_id=user.id, workspace_id=workspace_id
    )


CurrentWorkspace = Annotated[WorkspaceContext, Depends(current_workspace)]
