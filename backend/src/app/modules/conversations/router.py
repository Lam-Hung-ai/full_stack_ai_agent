from typing import Annotated
from uuid import UUID

from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import StreamingResponse

from app.common.dependencies.auth import CurrentUser
from app.common.dependencies.workspace import CurrentWorkspace
from app.common.schemas.pagination import PageParams, page_params
from app.database.session import SessionDep, SessionLocal
from app.modules.agent.dependencies import RunnerDep
from app.modules.conversations.schemas import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    HistoryResponse,
    SendMessage,
)
from app.modules.conversations.service import ConversationService, TurnService

router = APIRouter(tags=["Conversations"])


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
) -> ConversationListResponse:
    return await ConversationService(session).list(
        user=user, workspace=workspace, params=params
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
    return await ConversationService(session).rename(
        user=user, conversation_id=conversation_id, data=data
    )


@router.delete(
    "/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_conversation(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> None:
    await ConversationService(session).delete(
        user=user, conversation_id=conversation_id
    )


@router.get("/conversations/{conversation_id}/messages", response_model=HistoryResponse)
async def get_history(
    conversation_id: UUID, user: CurrentUser, session: SessionDep
) -> HistoryResponse:
    return await ConversationService(session).history(
        user=user, conversation_id=conversation_id
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def send_message(
    conversation_id: UUID,
    data: SendMessage,
    request: Request,
    user: CurrentUser,
    session: SessionDep,
    runner: RunnerDep,
) -> StreamingResponse:
    """Start an assistant turn and stream it as AG-UI events.

    Errors before the turn starts are JSON (401/403/404/409/422). Leaving the
    stream only detaches this subscriber; the turn continues and is saved.
    """
    turn = await TurnService(session, runner=runner, session_factory=SessionLocal).send(
        user=user, conversation_id=conversation_id, data=data
    )
    encoder = EventEncoder(accept=request.headers.get("accept", ""))

    async def events():
        async for event in turn.stream.subscribe():
            yield encoder.encode(event)

    return StreamingResponse(
        events(),
        media_type=encoder.get_content_type(),
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
