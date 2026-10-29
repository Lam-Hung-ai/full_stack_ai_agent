from typing import Annotated

from fastapi import APIRouter, Depends

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.workspace import CurrentWorkspace
from app.common.schemas.pagination import PageParams, page_params
from app.database.session import SessionDep
from app.modules.workspaces.schemas import WorkspaceListResponse, WorkspaceResponse
from app.modules.workspaces.service import WorkspaceService

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])


@router.get("", response_model=WorkspaceListResponse)
async def list_workspaces(
    user: CurrentUser,
    session: SessionDep,
    params: Annotated[PageParams, Depends(page_params)],
) -> WorkspaceListResponse:
    return await WorkspaceService(session).list_for_user(user_id=user.id, params=params)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace: CurrentWorkspace, user: CurrentUser, session: SessionDep
) -> WorkspaceResponse:
    return await WorkspaceService(session).get(
        user_id=user.id, workspace_id=workspace.id
    )
