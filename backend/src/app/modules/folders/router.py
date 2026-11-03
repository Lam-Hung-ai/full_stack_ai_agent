from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.workspace import CurrentWorkspace
from app.common.schemas.pagination import PageParams, page_params
from app.database.session import SessionDep
from app.modules.folders.schemas import (
    FolderCreate,
    FolderListResponse,
    FolderResponse,
    FolderUpdate,
)
from app.modules.folders.service import FolderService

router = APIRouter(tags=["Folders"])


@router.post(
    "/workspaces/{workspace_id}/folders",
    status_code=status.HTTP_201_CREATED,
    response_model=FolderResponse,
)
async def create_folder(
    data: FolderCreate,
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
) -> FolderResponse:
    return await FolderService(session).create(
        user=user, workspace=workspace, data=data
    )


@router.get("/workspaces/{workspace_id}/folders", response_model=FolderListResponse)
async def list_folders(
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
    params: Annotated[PageParams, Depends(page_params)],
) -> FolderListResponse:
    return await FolderService(session).list(
        user=user, workspace=workspace, params=params
    )


@router.patch("/folders/{folder_id}", response_model=FolderResponse)
async def rename_folder(
    folder_id: UUID, data: FolderUpdate, user: CurrentUser, session: SessionDep
) -> FolderResponse:
    return await FolderService(session).rename(
        user=user, folder_id=folder_id, data=data
    )


@router.delete("/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID, user: CurrentUser, session: SessionDep
) -> None:
    await FolderService(session).delete(user=user, folder_id=folder_id)
