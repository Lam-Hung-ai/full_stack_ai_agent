import asyncio
from dataclasses import dataclass
from functools import partial
from typing import Any
from uuid import UUID

from ag_ui.core import BaseEvent, ResumeEntry, RunAgentInput
from langgraph.checkpoint.base import CheckpointTuple
from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import DomainError, fail
from app.common.schemas.pagination import PageParams, Pagination
from app.common.storage.client import ObjectStorage
from app.config.security import now
from app.database.session import SessionFactory
from app.modules.agent.bundle import AguiMessage
from app.modules.agent.checkpoints import drop_checkpoints, durable_saver
from app.modules.agent.graph import GRAPH_VERSION
from app.modules.agent.runner import Pause, Runner, RunStream, TurnStatus
from app.modules.agent.tools import TOOL_RESOURCE, TOOLS
from app.modules.authorization.service import AuthorizationService
from app.modules.conversations import interactions
from app.modules.conversations.context import branch_messages
from app.modules.conversations.repository import (
    DEFAULT_TITLE,
    ConversationRepository,
    MessageRepository,
)
from app.modules.conversations.schemas import (
    ACTIVE_STATUSES,
    ActiveAssistant,
    ChatMessageInput,
    ConversationCreate,
    ConversationListItem,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    EditMessage,
    HistoryResponse,
    MessageResponse,
    ResumeMessage,
    SendMessage,
    StopResponse,
)
from app.modules.conversations.tree import MessageTree
from app.modules.files.repository import FileRepository
from app.modules.files.service import FileService, file_part, resolve_files
from app.modules.folders.service import FolderService
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService

TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled"})
TITLE_LENGTH = 60
#: How long a stop request waits for the turn to save its partial answer.
STOP_WAIT_SECONDS = 5.0
#: Suggested wait before retrying a turn refused for lack of room.
RETRY_AFTER_SECONDS = 5


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
        self,
        *,
        user: Principal,
        workspace: WorkspaceContext,
        params: PageParams,
        archived: bool = False,
        folder_id: UUID | None = None,
        unfiled: bool = False,
    ) -> ConversationListResponse:
        rows, total = await self._conversations.list_for_owner(
            workspace_id=workspace.id,
            owner_user_id=user.id,
            archived=archived,
            folder_id=folder_id,
            unfiled=unfiled,
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

    async def update(
        self, *, user: Principal, conversation_id: UUID, data: ConversationUpdate
    ) -> ConversationResponse:
        row = await self.require_owned(
            user=user, conversation_id=conversation_id, lock=True
        )
        fields = data.model_fields_set
        values: dict[str, Any] = {}
        if data.title is not None:
            values["title"] = data.title
        # Pinning again keeps the original time, so the order does not jump.
        if data.pinned is not None and data.pinned != (row["pinned_at"] is not None):
            values["pinned_at"] = now() if data.pinned else None
        if data.archived is not None and data.archived != (
            row["archived_at"] is not None
        ):
            values["archived_at"] = now() if data.archived else None
        if "folder_id" in fields:
            if data.folder_id is not None:
                await FolderService(self._session).require_owned(
                    user=user,
                    folder_id=data.folder_id,
                    workspace_id=row["workspace_id"],
                )
            values["folder_id"] = data.folder_id
        if values:
            row = await self._conversations.update(
                conversation_id=conversation_id, **values
            )
            await self._session.commit()
        return await self._response(row)

    async def delete(self, *, user: Principal, conversation_id: UUID) -> None:
        await self.require_owned(user=user, conversation_id=conversation_id, lock=True)
        # The trigger revokes the source shares; copies stay (decisions §9).
        await self._conversations.soft_delete(conversation_id=conversation_id)
        await self._session.commit()

    async def history(
        self,
        *,
        user: Principal,
        conversation_id: UUID,
        from_message_id: UUID | None = None,
    ) -> HistoryResponse:
        """The saved current branch, or with `from_message_id` the branch
        through that message down its newest children. Reading never moves
        the saved pointer: which branch a tab shows is the client's (API §2)."""
        row = await self.require_owned(user=user, conversation_id=conversation_id)
        tree = MessageTree(await self._messages.links(conversation_id=conversation_id))
        if from_message_id is None:
            leaf = row["current_message_id"]
        elif from_message_id in tree:
            leaf = tree.latest_leaf(from_message_id)
        else:
            fail(404, "message_not_found")
        path = (
            await self._messages.branch(conversation_id=conversation_id, leaf_id=leaf)
            if leaf
            else []
        )
        return HistoryResponse(
            current_message_id=leaf,
            data=[
                MessageResponse.model_validate(
                    {**dict(message), "sibling_ids": tree.siblings(message["id"])}
                )
                for message in path
            ],
        )

    async def require_owned(
        self, *, user: Principal, conversation_id: UUID, lock: bool = False
    ) -> RowMapping:
        row, _ = await self.owned(user=user, conversation_id=conversation_id, lock=lock)
        return row

    async def owned(
        self, *, user: Principal, conversation_id: UUID, lock: bool = False
    ) -> tuple[RowMapping, WorkspaceContext]:
        """Chats are private to their owner (decisions §1), and the owner must
        still belong to the chat's workspace. Anything else looks like 404."""
        row = await self._conversations.get_for_owner(
            conversation_id=conversation_id, owner_user_id=user.id, lock=lock
        )
        if row is None:
            fail(404, "conversation_not_found")
        workspace = await WorkspaceService(self._session).context(
            user_id=user.id, workspace_id=row["workspace_id"]
        )
        return row, workspace

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
    """Starts, resumes and stops assistant turns and records their outcome.

    Sending, editing and regenerating differ only in where the new rows hang
    in the tree (database §6); all three end in `_launch`. Resuming continues
    the same assistant row from its stored checkpoint (database phase 4 §7).
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        runner: Runner,
        session_factory: SessionFactory,
        storage: ObjectStorage | None = None,
    ) -> None:
        self._session = session
        self._runner = runner
        self._session_factory = session_factory
        #: Needed by turns that may carry files (send, edit, regenerate).
        self._storage = storage
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)

    async def send(
        self, *, user: Principal, conversation_id: UUID, data: SendMessage
    ) -> StartedTurn:
        conversation, workspace = await self._open(user, conversation_id)
        text = _question_text(data.message)
        await self._check_parent(conversation_id, data.parent_message_id)
        title = (
            _fallback_title(text or "Tệp đính kèm")
            if conversation["title"] == DEFAULT_TITLE and data.parent_message_id is None
            else None
        )
        return await self._ask(
            user,
            workspace,
            conversation_id,
            parent_id=data.parent_message_id,
            message=data.message,
            text=text,
            title=title,
        )

    async def edit(
        self,
        *,
        user: Principal,
        conversation_id: UUID,
        message_id: UUID,
        data: EditMessage,
    ) -> StartedTurn:
        """A new user message beside the edited one (same parent), then a new
        answer; the old version and everything under it stay (API §4)."""
        _, workspace = await self._open(user, conversation_id)
        text = _question_text(data.message)
        original = await self._target(conversation_id, message_id, "user")
        return await self._ask(
            user,
            workspace,
            conversation_id,
            parent_id=original["parent_message_id"],
            message=data.message,
            text=text,
        )

    async def regenerate(
        self, *, user: Principal, conversation_id: UUID, message_id: UUID
    ) -> StartedTurn:
        """A new answer beside the old one, from the question's branch; the old
        answer's checkpoint is not continued (API §4)."""
        _, workspace = await self._open(user, conversation_id)
        original = await self._target(conversation_id, message_id, "assistant")
        await self._ensure_idle(conversation_id)
        question_id = original["parent_message_id"]
        history = await self._messages.branch(
            conversation_id=conversation_id, leaf_id=question_id
        )
        return await self._launch(
            user,
            workspace,
            conversation_id,
            user_message_id=question_id,
            messages=branch_messages(history),
        )

    async def resume(
        self,
        *,
        user: Principal,
        conversation_id: UUID,
        message_id: UUID,
        data: ResumeMessage,
    ) -> StartedTurn:
        """Answer what the assistant waits on and continue it (API §5). Every
        check happens before the claim, so a refused answer leaves the turn
        waiting; the claim, the answers and the activity commit together."""
        _, workspace = await self._open(user, conversation_id)
        self._ensure_room()
        target = await self._target(conversation_id, message_id, "assistant")
        pending = target["metadata"].get("pending_action")
        if target["status"] != "requires_action" or not pending:
            fail(409, "not_waiting")
        if pending.get("graph_version") != GRAPH_VERSION:
            # RR-07: an older graph's checkpoint is not run on a new graph.
            fail(409, "graph_version_changed")
        values = interactions.validate_answers(pending, data.resume)
        authorization = AuthorizationService(self._session)
        for tool_name in sorted(interactions.approved_tools(pending, values)):
            # An approval never stands in for the grant (use case T07).
            await authorization.require(workspace, TOOL_RESOURCE, tool_name)
        stored = await (await durable_saver(self._session)).aget_tuple(
            {"configurable": pending["checkpoint"]}
        )
        if stored is None:
            fail(409, "checkpoint_missing")
        content = interactions.resolve_activities(
            target["content"],
            pending,
            status="answered",
            values=values,
            actor_id=user.id,
        )
        metadata = interactions.resolved_metadata(
            target["metadata"],
            pending,
            status="answered",
            values=values,
            actor_id=user.id,
        )
        claimed = await self._messages.set_status(
            message_id=message_id,
            status="running",
            content=content,
            metadata=metadata,
            expected=frozenset({"requires_action"}),
        )
        if not claimed:
            fail(409, "not_waiting")
        question_id = target["parent_message_id"]
        history = await self._messages.branch(
            conversation_id=conversation_id, leaf_id=question_id
        )
        tools = await authorization.allowed_actions(workspace, TOOL_RESOURCE)
        await self._session.commit()

        # The graph state replays the context and this turn so far; only what
        # the resumed run adds belongs after the stored content.
        known = {m["id"] for row in history for m in row["content"]}
        known.update(m["id"] for m in content)
        return self._run(
            user,
            workspace,
            conversation_id,
            assistant_id=message_id,
            user_message_id=question_id,
            tools=tools,
            messages=[],
            resume=interactions.resume_entries(values),
            resume_from=stored,
            known_ids=known,
            base_content=content,
            base_metadata=metadata,
        )

    async def stop(
        self, *, user: Principal, conversation_id: UUID, message_id: UUID
    ) -> StopResponse:
        """Stop this assistant only (API §7). A finished one is left as is; one
        waiting for the user is cancelled with its question (phase 4 §7)."""
        await ConversationService(self._session).require_owned(
            user=user, conversation_id=conversation_id
        )
        target = await self._target(conversation_id, message_id, "assistant")
        if target["status"] in ACTIVE_STATUSES:
            where = await self._runner.stop(message_id, timeout=STOP_WAIT_SECONDS)
            if where == "orphan":
                # No process runs it: it waits for the user, or a restart
                # orphaned it (RR-01, RR-10). Cancel it in place.
                await self._cancel_in_place(target)
                await self._session.commit()
            elif where == "remote":
                await self._await_end(conversation_id, message_id)
            target = await self._target(conversation_id, message_id, "assistant")
        return StopResponse(id=message_id, status=target["status"])

    async def stop_departed(self, *, workspace_id: UUID, user_id: UUID) -> None:
        """The user left the workspace's organization (O07): end their
        unfinished turns there. Their requests are refused already; this stops
        model and tool work that nobody may read any more."""
        for target in await self._messages.active_of_owner(
            workspace_id=workspace_id, owner_user_id=user_id
        ):
            where = await self._runner.stop(target["id"], timeout=STOP_WAIT_SECONDS)
            if where == "orphan":
                await self._cancel_in_place(target)
        await self._session.commit()

    def _ensure_room(self) -> None:
        if not self._runner.has_room():
            # Nothing was committed: the client may retry the same request.
            fail(503, "server_busy", headers={"Retry-After": str(RETRY_AFTER_SECONDS)})

    async def _await_end(self, conversation_id: UUID, message_id: UUID) -> None:
        """Watch the row while another process saves the stopped turn."""
        deadline = asyncio.get_running_loop().time() + STOP_WAIT_SECONDS
        while asyncio.get_running_loop().time() < deadline:
            message = await self._target(conversation_id, message_id, "assistant")
            if message["status"] not in ACTIVE_STATUSES:
                return
            await asyncio.sleep(0.1)

    async def _cancel_in_place(self, target: RowMapping) -> None:
        pending = target["metadata"].get("pending_action")
        content = metadata = None
        if pending:
            # The question will never be answered: its checkpoint goes too.
            await drop_checkpoints(self._session, target["id"])
            metadata = interactions.resolved_metadata(
                target["metadata"], pending, status="cancelled"
            )
            if target["status"] == "requires_action":
                content = interactions.resolve_activities(
                    target["content"], pending, status="cancelled"
                )
        await self._messages.set_status(
            message_id=target["id"],
            status="cancelled",
            content=content,
            metadata=metadata,
        )

    async def _open(
        self, user: Principal, conversation_id: UUID
    ) -> tuple[RowMapping, WorkspaceContext]:
        # Locked until commit: turns of one chat start one at a time.
        return await ConversationService(self._session).owned(
            user=user, conversation_id=conversation_id, lock=True
        )

    async def _target(
        self, conversation_id: UUID, message_id: UUID, role: str
    ) -> RowMapping:
        message = await self._messages.get(
            conversation_id=conversation_id, message_id=message_id
        )
        if message is None or message["role"] != role:
            fail(404, "message_not_found")
        return message

    async def _ensure_idle(self, conversation_id: UUID) -> None:
        if await self._messages.active_assistant(conversation_id=conversation_id):
            fail(409, "assistant_active")

    async def _ask(
        self,
        user: Principal,
        workspace: WorkspaceContext,
        conversation_id: UUID,
        *,
        parent_id: UUID | None,
        message: ChatMessageInput,
        text: str,
        title: str | None = None,
    ) -> StartedTurn:
        """Insert the user's question under `parent_id` and answer it."""
        if await self._messages.exists(message_id=message.id):
            fail(409, "message_id_conflict")
        await self._ensure_idle(conversation_id)
        history = (
            await self._messages.branch(
                conversation_id=conversation_id, leaf_id=parent_id
            )
            if parent_id
            else []
        )
        files = (
            await FileService(self._session).attachable(
                user=user, workspace=workspace, ids=message.file_ids
            )
            if message.file_ids
            else []
        )
        question: list[AguiMessage] = [
            {"id": str(message.id), "role": "user", "content": _content(text, files)}
        ]
        # With files the row is staged pending: links are refused on terminal
        # messages, and a deferred trigger insists it is completed by commit.
        await self._messages.insert(
            message_id=message.id,
            conversation_id=conversation_id,
            parent_message_id=parent_id,
            role="user",
            status="pending" if files else "completed",
            content=question,
        )
        if files:
            await FileRepository(self._session).link(
                message_id=message.id, file_ids=[row["id"] for row in files]
            )
            await self._messages.set_status(message_id=message.id, status="completed")
        return await self._launch(
            user,
            workspace,
            conversation_id,
            user_message_id=message.id,
            messages=branch_messages(history) + question,
            title=title,
        )

    async def _launch(
        self,
        user: Principal,
        workspace: WorkspaceContext,
        conversation_id: UUID,
        *,
        user_message_id: UUID,
        messages: list[AguiMessage],
        title: str | None = None,
    ) -> StartedTurn:
        """Insert the pending answer, make it the saved branch, commit, run."""
        self._ensure_room()
        try:
            assistant = await self._messages.insert(
                conversation_id=conversation_id,
                parent_message_id=user_message_id,
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
        if title:
            updates["title"] = title
        await self._conversations.update(conversation_id=conversation_id, **updates)
        tools = await AuthorizationService(self._session).allowed_actions(
            workspace, TOOL_RESOURCE
        )
        await self._session.commit()
        return self._run(
            user,
            workspace,
            conversation_id,
            assistant_id=assistant["id"],
            user_message_id=user_message_id,
            tools=tools,
            messages=messages,
        )

    def _run(
        self,
        user: Principal,
        workspace: WorkspaceContext,
        conversation_id: UUID,
        *,
        assistant_id: UUID,
        user_message_id: UUID,
        tools: frozenset[str],
        messages: list[AguiMessage],
        resume: list[ResumeEntry] | None = None,
        resume_from: CheckpointTuple | None = None,
        known_ids: set[str] | None = None,
        base_content: list[AguiMessage] | None = None,
        base_metadata: dict[str, Any] | None = None,
    ) -> StartedTurn:
        """Hand a committed turn to the runner."""
        run_input = RunAgentInput.model_validate(
            {
                "threadId": str(conversation_id),
                "runId": str(uuid7()),
                "state": {},
                "messages": messages,
                "tools": [],
                "context": [],
                "forwardedProps": {},
                "resume": resume,
            }
        )

        async def finalize(
            status: TurnStatus, bundle: list[AguiMessage], pause: Pause | None
        ) -> list[BaseEvent]:
            return await self._finalize(
                assistant_id,
                status,
                [*(base_content or []), *bundle],
                base_metadata or {},
                pause,
                resumed=resume_from is not None,
            )

        stream = self._runner.start(
            assistant_id=assistant_id,
            run_input=run_input,
            announce={
                "conversationId": str(conversation_id),
                "userMessageId": str(user_message_id),
                "assistantMessageId": str(assistant_id),
            },
            tools=tools.intersection(TOOLS),
            tool_guard=partial(self._tool_allowed, user.id, workspace.id),
            on_running=lambda: self._record(assistant_id, "running"),
            finalize=finalize,
            known_ids=known_ids,
            resume_from=resume_from,
            # A resumed turn continues from its checkpoint, which already holds
            # the files it was given.
            prepare=self._with_files if resume_from is None else None,
            log_fields={"workspace_id": str(workspace.id), "user_id": str(user.id)},
        )
        return StartedTurn(user_message_id, assistant_id, stream)

    async def _with_files(self, run_input: RunAgentInput) -> RunAgentInput:
        """Give the model the bytes of attached files (inside the turn)."""
        messages = [
            message.model_dump(by_alias=True, exclude_none=True)
            for message in run_input.messages
        ]
        if self._storage is None:
            return run_input
        resolved = await resolve_files(
            messages, session_factory=self._session_factory, storage=self._storage
        )
        if resolved is messages:
            return run_input
        return RunAgentInput.model_validate(
            {**run_input.model_dump(by_alias=True), "messages": resolved}
        )

    async def _check_parent(
        self, conversation_id: UUID, parent_id: UUID | None
    ) -> None:
        if parent_id is None:
            # A null parent starts the tree; later roots come from edits.
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

    async def _tool_allowed(
        self, user_id: UUID, workspace_id: UUID, tool_name: str
    ) -> bool:
        """Checked right before each tool call, on fresh data: membership or a
        grant may have been revoked since the turn started."""
        async with self._session_factory() as session:
            try:
                workspace = await WorkspaceService(session).context(
                    user_id=user_id, workspace_id=workspace_id
                )
            except DomainError:
                return False
            return await AuthorizationService(session).can(
                workspace, TOOL_RESOURCE, tool_name
            )

    async def _record(self, assistant_id: UUID, status: str) -> None:
        """Runs in the turn's task, after the request ended: its own session."""
        async with self._session_factory() as session:
            await MessageRepository(session).set_status(
                message_id=assistant_id, status=status
            )
            await session.commit()

    async def _finalize(
        self,
        assistant_id: UUID,
        status: TurnStatus,
        content: list[AguiMessage],
        metadata: dict[str, Any],
        pause: Pause | None,
        *,
        resumed: bool = False,
    ) -> list[BaseEvent]:
        """Save the outcome. A pause stores its checkpoint, the waiting
        activities and `pending_action` in one transaction (phase 4 §6) and
        returns the activities to announce once that has committed. A resumed
        turn drops the checkpoint it came from in that transaction too: once
        it ends or pauses anew, nothing resumes from the old one (RR-16)."""
        metadata = {k: v for k, v in metadata.items() if k != "pending_action"}
        events: list[BaseEvent] = []
        async with self._session_factory() as session:
            if resumed:
                await drop_checkpoints(session, assistant_id)
            if pause is not None:
                saver = await durable_saver(session)
                pending = interactions.new_pending_action(
                    checkpoint=await pause.saver.export(saver, pause.thread_id),
                    interrupts=pause.interrupts,
                    graph_version=GRAPH_VERSION,
                )
                activities = interactions.waiting_activities(pending)
                content = [*content, *activities]
                metadata["pending_action"] = pending
                events = interactions.activity_events(activities)
            await MessageRepository(session).set_status(
                message_id=assistant_id,
                status=status,
                content=content,
                metadata=metadata,
            )
            await session.commit()
        return events


def _question_text(message: ChatMessageInput) -> str:
    """The question's text; it may be empty when files carry the question."""
    text = message.text.strip()
    if not text and not message.file_ids:
        fail(422, "empty_message")
    return text


def _content(text: str, files: list[RowMapping]) -> str | list[dict[str, Any]]:
    """A plain question stays a string; with files, AG-UI content parts."""
    if not files:
        return text
    parts: list[dict[str, Any]] = [{"type": "text", "text": text}] if text else []
    return [*parts, *(file_part(row) for row in files)]
