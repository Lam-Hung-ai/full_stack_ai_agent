from uuid import UUID

from fastapi import APIRouter, status

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.storage import StorageDep
from app.common.dependencies.workspace import CurrentWorkspace
from app.database.session import SessionDep
from app.modules.conversations.service import ConversationService
from app.modules.files.schemas import (
    DownloadResponse,
    FileResponse,
    UploadCreate,
    UploadResponse,
)
from app.modules.files.service import FileService

router = APIRouter(tags=["Files"])


@router.post(
    "/workspaces/{workspace_id}/uploads",
    status_code=status.HTTP_201_CREATED,
    response_model=UploadResponse,
)
async def create_upload(
    data: UploadCreate,
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> UploadResponse:
    """A file id and a presigned PUT; nothing is recorded until `complete`."""
    return await FileService(session, storage).create_upload(
        user=user, workspace=workspace, data=data
    )


@router.post(
    "/workspaces/{workspace_id}/uploads/{file_id}/complete",
    status_code=status.HTTP_201_CREATED,
    response_model=FileResponse,
)
async def complete_upload(
    file_id: UUID,
    data: UploadCreate,
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> FileResponse:
    """Check the uploaded bytes (size, type) and record the file; its id can
    then go in a question's `file_ids`."""
    return await FileService(session, storage).complete(
        user=user, workspace=workspace, file_id=file_id, data=data
    )


@router.get(
    "/conversations/{conversation_id}/files/{file_id}",
    response_model=DownloadResponse,
)
async def download_file(
    conversation_id: UUID,
    file_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> DownloadResponse:
    """A short-lived link to a file attached in a chat the user owns."""
    await ConversationService(session).require_owned(
        user=user, conversation_id=conversation_id
    )
    return await FileService(session, storage).download(
        conversation_id=conversation_id, file_id=file_id
    )
