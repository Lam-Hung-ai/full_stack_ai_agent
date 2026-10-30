from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.common.dependencies.auth import CurrentUser, OptionalUser
from app.common.dependencies.rate_limit import rate_limit
from app.common.dependencies.storage import StorageDep
from app.database.session import SessionDep
from app.modules.files.schemas import DownloadResponse
from app.modules.shares.copies import CopyService
from app.modules.shares.schemas import (
    CopyRequest,
    CopyResponse,
    SharedConversation,
    ShareResponse,
)
from app.modules.shares.service import ShareService

SHARE_RATE_LIMIT = 300

router = APIRouter(tags=["Shares"])
#: Reached with a link token, signed in or not.
links_router = APIRouter(
    prefix="/shares/{token}",
    tags=["Shares"],
    # One request per image of a shared chat: wide. A link token cannot be
    # guessed (QD-28); the limit only brakes scraping.
    dependencies=[Depends(rate_limit("shares", SHARE_RATE_LIMIT))],
)


@router.get("/conversations/{conversation_id}/share", response_model=ShareResponse)
async def get_share(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> ShareResponse:
    """The chat's live share and its link, for its owner."""
    return await ShareService(session).get(user=user, conversation_id=conversation_id)


@router.post("/conversations/{conversation_id}/share", response_model=ShareResponse)
async def publish_share(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> ShareResponse:
    """Publish the chat as it is now (whole tree); the link stays the same."""
    return await ShareService(session).publish(
        user=user, conversation_id=conversation_id
    )


@router.delete(
    "/conversations/{conversation_id}/share", status_code=status.HTTP_204_NO_CONTENT
)
async def revoke_share(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> None:
    """The link stops working for good; sharing again makes a new link."""
    await ShareService(session).revoke(user=user, conversation_id=conversation_id)


@links_router.get("", response_model=SharedConversation)
async def view_share(
    token: str, user: OptionalUser, session: SessionDep
) -> SharedConversation:
    """Public links open for anyone; organization links need an active
    member. Anything else is 404."""
    return await ShareService(session).view(user=user, token=token)


@links_router.get("/files/{file_id}", response_model=DownloadResponse)
async def share_file(
    token: str,
    file_id: UUID,
    user: OptionalUser,
    session: SessionDep,
    storage: StorageDep,
) -> DownloadResponse:
    return await ShareService(session, storage).file_link(
        user=user, token=token, file_id=file_id
    )


@links_router.post(
    "/copy",
    response_model=CopyResponse,
    dependencies=[Depends(rate_limit("share-copy"))],
)
async def copy_share(
    token: str,
    data: CopyRequest,
    user: CurrentUser,
    session: SessionDep,
    storage: StorageDep,
) -> CopyResponse:
    """Continue the shared chat as a private copy of one's own."""
    return await CopyService(session, storage).copy(user=user, token=token, data=data)
