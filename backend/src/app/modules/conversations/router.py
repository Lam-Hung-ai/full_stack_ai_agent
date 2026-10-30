from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from ag_ui.core import BaseEvent
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.rate_limit import user_rate_limit
from app.common.dependencies.storage import OptionalStorageDep
from app.common.dependencies.workspace import CurrentWorkspace
from app.common.schemas.pagination import PageParams, page_params
from app.database.session import SessionDep, SessionLocal
from app.modules.agent.dependencies import RunnerDep
from app.modules.conversations.connect import ConnectService
from app.modules.conversations.export import content_disposition
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationSearchResponse,
    ConversationUpdate,
    EditMessage,
    HistoryResponse,
    ResumeMessage,
    SendMessage,
    StopResponse,
)
from app.modules.conversations.search import MAX_QUERY, MIN_QUERY
from app.modules.conversations.service import (
    ConversationService,
    StartedTurn,
    TurnService,
)

#: Each export reads every chat of the workspace.
EXPORTS_PER_HOUR = 10

router = APIRouter(tags=["Conversations"])

#: The turn routes stream AG-UI events; errors before the turn starts are JSON.
TURN_RESPONSES: dict[int | str, dict] = {200: {"content": {"text/event-stream": {}}}}


@router.post(
    "/workspaces/{workspace_id}/conversations",
    status_code=status.HTTP_201_CREATED,
    response_model=ConversationResponse,
)
async def create_conversation(
    data: ConversationCreate,
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
) -> ConversationResponse:
    return await ConversationService(session).create(
        user=user, workspace=workspace, data=data
    )


@router.get(
    "/workspaces/{workspace_id}/conversations",
    response_model=ConversationListResponse,
)
async def list_conversations(
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
    params: Annotated[PageParams, Depends(page_params)],
    archived: Annotated[bool, Query(description="Archived chats only")] = False,
    folder_id: Annotated[UUID | None, Query(description="Chats of one folder")] = None,
    unfiled: Annotated[bool, Query(description="Chats outside any folder")] = False,
) -> ConversationListResponse:
    """Pinned chats come first, then the most recently updated."""
    return await ConversationService(session).list(
        user=user,
        workspace=workspace,
        params=params,
        archived=archived,
        folder_id=folder_id,
        unfiled=unfiled,
    )


@router.get(
    "/workspaces/{workspace_id}/conversations/search",
    response_model=ConversationSearchResponse,
)
async def search_conversations(
    workspace: CurrentWorkspace,
    user: CurrentUser,
    session: SessionDep,
    q: Annotated[str, Query(min_length=MIN_QUERY, max_length=MAX_QUERY)],
    params: Annotated[PageParams, Depends(page_params)],
) -> ConversationSearchResponse:
    """Own chats matching `q` by title or message text, ignoring accents and
    case; each with the newest matching message and a snippet."""
    return await ConversationService(session).search(
        user=user, workspace=workspace, query=q, params=params
    )


@router.get(
    "/workspaces/{workspace_id}/export",
    response_class=StreamingResponse,
    responses={200: {"content": {"application/zip": {}}}},
    dependencies=[
        Depends(user_rate_limit("conversation-export", EXPORTS_PER_HOUR, window=3600))
    ],
)
async def export_conversations(
    workspace: CurrentWorkspace, user: CurrentUser, session: SessionDep
) -> StreamingResponse:
    """The caller's own chats of the workspace as a zip (JSON + Markdown)."""
    name, chunks = await ConversationService(session).export(
        user=user, workspace=workspace, session_factory=SessionLocal
    )
    return StreamingResponse(
        chunks,
        media_type="application/zip",
        headers={"Content-Disposition": content_disposition(name)},
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> ConversationResponse:
    return await ConversationService(session).get(
        user=user, conversation_id=conversation_id
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    data: ConversationUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> ConversationResponse:
    return await ConversationService(session).update(
        user=user, conversation_id=conversation_id, data=data
    )


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: UUID, user: CurrentUser, session: SessionDep, runner: RunnerDep
) -> None:
    await TurnService(session, runner=runner, session_factory=SessionLocal).delete(
        user=user, conversation_id=conversation_id
    )


@router.get("/conversations/{conversation_id}/messages", response_model=HistoryResponse)
async def get_history(
    conversation_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    from_message_id: Annotated[
        UUID | None,
        Query(description="Open the branch through this message instead"),
    ] = None,
) -> HistoryResponse:
    return await ConversationService(session).history(
        user=user, conversation_id=conversation_id, from_message_id=from_message_id
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_class=StreamingResponse,
    responses=TURN_RESPONSES,
)
async def send_message(
    conversation_id: UUID,
    data: SendMessage,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
    storage: OptionalStorageDep,
) -> StreamingResponse:
    """Start an assistant turn and stream it as AG-UI events.

    Errors before the turn starts are JSON (401/403/404/409/422). Leaving the
    stream only detaches this subscriber; the turn continues and is saved.
    """
    turn = await TurnService(
        session, runner=runner, session_factory=SessionLocal, storage=storage
    ).send(user=user, conversation_id=conversation_id, data=data)
    return _turn_stream(turn, request)


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/edit",
    response_class=StreamingResponse,
    responses=TURN_RESPONSES,
)
async def edit_message(
    conversation_id: UUID,
    message_id: UUID,
    data: EditMessage,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
    storage: OptionalStorageDep,
) -> StreamingResponse:
    """Answer a new version of a user question; the old branch stays."""
    turn = await TurnService(
        session, runner=runner, session_factory=SessionLocal, storage=storage
    ).edit(user=user, conversation_id=conversation_id, message_id=message_id, data=data)
    return _turn_stream(turn, request)


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/regenerate",
    response_class=StreamingResponse,
    responses=TURN_RESPONSES,
)
async def regenerate_message(
    conversation_id: UUID,
    message_id: UUID,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
    storage: OptionalStorageDep,
) -> StreamingResponse:
    """Answer the same question again beside the given assistant message."""
    turn = await TurnService(
        session, runner=runner, session_factory=SessionLocal, storage=storage
    ).regenerate(user=user, conversation_id=conversation_id, message_id=message_id)
    return _turn_stream(turn, request)


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/resume",
    response_class=StreamingResponse,
    responses=TURN_RESPONSES,
)
async def resume_message(
    conversation_id: UUID,
    message_id: UUID,
    data: ResumeMessage,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
    storage: OptionalStorageDep,
) -> StreamingResponse:
    """Answer what a paused assistant waits on and continue the same turn."""
    # Storage too: the continued turn may create files (D06).
    turn = await TurnService(
        session, runner=runner, session_factory=SessionLocal, storage=storage
    ).resume(
        user=user, conversation_id=conversation_id, message_id=message_id, data=data
    )
    return _turn_stream(turn, request)


@router.post(
    "/conversations/{conversation_id}/messages/{message_id}/stop",
    response_model=StopResponse,
)
async def stop_message(
    conversation_id: UUID,
    message_id: UUID,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
) -> StopResponse:
    """Stop an assistant turn, keeping what it produced so far."""
    return await TurnService(session, runner=runner, session_factory=SessionLocal).stop(
        user=user, conversation_id=conversation_id, message_id=message_id
    )


@router.post(
    "/conversations/{conversation_id}/connect",
    response_class=StreamingResponse,
    responses=TURN_RESPONSES,
)
async def connect(
    conversation_id: UUID,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
) -> StreamingResponse:
    """The latest state of the chat, then the running turn if there is one.
    Read only: no model is called and nothing is started or resumed."""
    events = await ConnectService(session, live=runner.live).open(
        user=user, conversation_id=conversation_id
    )
    return _event_stream(events, request)


def _turn_stream(turn: StartedTurn, request: Request) -> StreamingResponse:
    return _event_stream(turn.stream.subscribe(), request)


def _event_stream(
    source: AsyncIterator[BaseEvent], request: Request
) -> StreamingResponse:
    encoder = EventEncoder(accept=request.headers.get("accept", ""))

    async def events():
        async for event in source:
            yield encoder.encode(event)

    return StreamingResponse(
        events(),
        media_type=encoder.get_content_type(),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
