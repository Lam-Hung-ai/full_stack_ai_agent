from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ag_ui.core import RunAgentInput
from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.common.schemas.pagination import PageParams, Pagination
from app.modules.agent.bundle import AguiMessage
from app.modules.agent.runner import Runner, RunStream, TurnStatus
from app.modules.authorization.service import AuthorizationService
from app.modules.conversations.context import branch_messages
from app.modules.conversations.repository import (
    DEFAULT_TITLE,
    ConversationRepository,
    MessageRepository,
)
from app.modules.conversations.schemas import (
    ActiveAssistant,
    ConversationCreate,
    ConversationListItem,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    HistoryResponse,
    MessageResponse,
    SendMessage,
)
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService

TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})
TITLE_LENGTH = 60

type SessionFactory = Callable[[], AsyncSession]


def _fallback_title(text: str) -> str:
    """First line of the first question; a background title generator that
    never overwrites a user's rename is left for later (use case C07)."""
    line = " ".join(text.split())
    return line if len(line) <= TITLE_LENGTH else line[: TITLE_LENGTH - 1] + "…"


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)

    async def create(
        self, *, user: Principal, workspace: WorkspaceContext, data: ConversationCreate
    ) -> ConversationResponse:
        await AuthorizationService(self._session).require(
            workspace, "conversation", "create"
        )
        row = await self._conversations.create(
            workspace_id=workspace.id, owner_user_id=user.id, title=data.title
        )
        await self._session.commit()
        return ConversationResponse.model_validate(dict(row))

    async def list(
        self, *, user: Principal, workspace: WorkspaceContext, params: PageParams
    ) -> ConversationListResponse:
        rows, total = await self._conversations.list_for_owner(
            workspace_id=workspace.id,
            owner_user_id=user.id,
            limit=params.page_size,
            offset=params.offset,
        )
        return ConversationListResponse(
            data=[ConversationListItem.model_validate(dict(row)) for row in rows],
            pagination=Pagination.of(params, total),
        )

    async def get(
        self, *, user: Principal, conversation_id: UUID
    ) -> ConversationResponse:
        row = await self.require_owned(user=user, conversation_id=conversation_id)
        return await self._response(row)

    async def rename(
        self, *, user: Principal, conversation_id: UUID, data: ConversationUpdate
    ) -> ConversationResponse:
        await self.require_owned(user=user, conversation_id=conversation_id, lock=True)
        row = await self._conversations.update(
            conversation_id=conversation_id, title=data.title
        )
        await self._session.commit()
        return await self._response(row)

    async def delete(self, *, user: Principal, conversation_id: UUID) -> None:
        await self.require_owned(user=user, conversation_id=conversation_id, lock=True)
        # The trigger revokes the source shares; copies stay (decisions §9).
        await self._conversations.soft_delete(conversation_id=conversation_id)
        await self._session.commit()

    async def history(
        self, *, user: Principal, conversation_id: UUID
    ) -> HistoryResponse:
        row = await self.require_owned(user=user, conversation_id=conversation_id)
        leaf = row["current_message_id"]
        path = (
            await self._messages.branch(conversation_id=conversation_id, leaf_id=leaf)
            if leaf
            else []
        )
        return HistoryResponse(
            current_message_id=leaf,
            data=[MessageResponse.model_validate(dict(message)) for message in path],
        )

    async def require_owned(
        self, *, user: Principal, conversation_id: UUID, lock: bool = False
    ) -> RowMapping:
        """Chats are private to their owner (decisions §1), and the owner must
        still belong to the chat's workspace. Anything else looks like 404."""
        row = await self._conversations.get_for_owner(
            conversation_id=conversation_id, owner_user_id=user.id, lock=lock
        )
        if row is None:
            fail(404, "conversation_not_found")
        await WorkspaceService(self._session).context(
            user_id=user.id, workspace_id=row["workspace_id"]
        )
        return row

    async def _response(self, row: RowMapping) -> ConversationResponse:
        active = await self._messages.active_assistant(conversation_id=row["id"])
        return ConversationResponse.model_validate(
            {
                **dict(row),
                "active_assistant": ActiveAssistant.model_validate(dict(active))
                if active
                else None,
            }
        )


@dataclass(frozen=True)
class StartedTurn:
    user_message_id: UUID
    assistant_message_id: UUID
    stream: RunStream


class TurnService:
    """Starts assistant turns and records their outcome."""

    def __init__(
        self, session: AsyncSession, *, runner: Runner, session_factory: SessionFactory
    ) -> None:
        self._session = session
        self._runner = runner
        self._session_factory = session_factory
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)

    async def send(
        self, *, user: Principal, conversation_id: UUID, data: SendMessage
    ) -> StartedTurn:
        conversation = await ConversationService(self._session).require_owned(
            user=user, conversation_id=conversation_id, lock=True
        )
        text = data.message.text.strip()
        if data.message.file_ids:
            fail(400, "file_attachments_unavailable")
        if not text:
            fail(422, "empty_message")
        await self._check_parent(conversation_id, data.parent_message_id)
        if await self._messages.exists(message_id=data.message.id):
            fail(409, "message_id_conflict")
        if await self._messages.active_assistant(conversation_id=conversation_id):
            fail(409, "assistant_active")

        history = (
            await self._messages.branch(
                conversation_id=conversation_id, leaf_id=data.parent_message_id
            )
            if data.parent_message_id
            else []
        )
        user_content: list[AguiMessage] = [
            {"id": str(data.message.id), "role": "user", "content": text}
        ]
        await self._messages.insert(
            message_id=data.message.id,
            conversation_id=conversation_id,
            parent_message_id=data.parent_message_id,
            role="user",
            status="completed",
            content=user_content,
        )
        try:
            assistant = await self._messages.insert(
                conversation_id=conversation_id,
                parent_message_id=data.message.id,
                role="assistant",
                status="pending",
                content=[],
            )
        except IntegrityError:
            # Another request started a turn between the check and the insert;
            # the partial unique index allows one active assistant per chat.
            await self._session.rollback()
            fail(409, "assistant_active")
        updates: dict[str, Any] = {"current_message_id": assistant["id"]}
        if conversation["title"] == DEFAULT_TITLE and data.parent_message_id is None:
            updates["title"] = _fallback_title(text)
        await self._conversations.update(conversation_id=conversation_id, **updates)
        await self._session.commit()

        run_input = RunAgentInput.model_validate(
            {
                "threadId": str(conversation_id),
                "runId": str(uuid7()),
                "state": {},
                "messages": branch_messages(history) + user_content,
                "tools": [],
                "context": [],
                "forwardedProps": {},
            }
        )
        stream = self._runner.start(
            assistant_id=assistant["id"],
            run_input=run_input,
            announce={
                "conversationId": str(conversation_id),
                "userMessageId": str(data.message.id),
                "assistantMessageId": str(assistant["id"]),
            },
            on_running=lambda: self._record(assistant["id"], "running"),
            finalize=lambda status, content: self._record(
                assistant["id"], status, content
            ),
        )
        return StartedTurn(data.message.id, assistant["id"], stream)

    async def _check_parent(
        self, conversation_id: UUID, parent_id: UUID | None
    ) -> None:
        if parent_id is None:
            # A null parent starts the tree; later roots come from edits (S3).
            if await self._messages.has_any(conversation_id=conversation_id):
                fail(409, "parent_required")
            return
        parent = await self._messages.get(
            conversation_id=conversation_id, message_id=parent_id
        )
        if (
            parent is None
            or parent["role"] != "assistant"
            or parent["status"] not in TERMINAL_STATUSES
        ):
            fail(409, "invalid_parent")

    async def _record(
        self,
        assistant_id: UUID,
        status: TurnStatus | str,
        content: list[AguiMessage] | None = None,
    ) -> None:
        """Runs in the turn's task, after the request ended: its own session."""
        async with self._session_factory() as session:
            await MessageRepository(session).set_status(
                message_id=assistant_id, status=status, content=content
            )
            await session.commit()
