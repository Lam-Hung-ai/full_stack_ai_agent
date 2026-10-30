from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

from app.common.schemas.common import Input
from app.common.schemas.pagination import Pagination

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
MessageStatus = Literal[
    "pending", "running", "requires_action", "completed", "failed", "cancelled"
]
ACTIVE_STATUSES: frozenset[str] = frozenset({"pending", "running", "requires_action"})


def _uuid_v7(value: UUID) -> UUID:
    # Application IDs are UUIDv7 (ID decisions §2); a v4 from crypto.randomUUID
    # would sort randomly in indexes and is rejected at the boundary.
    if value.version != 7:
        raise ValueError("must be a UUIDv7")
    return value


UUIDv7 = Annotated[UUID, AfterValidator(_uuid_v7)]


class ConversationCreate(Input):
    title: Title | None = None


class ConversationUpdate(Input):
    title: Title


class ActiveAssistant(BaseModel):
    id: UUID
    status: MessageStatus


class ConversationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    current_message_id: UUID | None
    pinned_at: datetime | None
    archived_at: datetime | None
    folder_id: UUID | None
    created_at: datetime
    updated_at: datetime
    active_assistant: ActiveAssistant | None = None


class ConversationListItem(BaseModel):
    id: UUID
    title: str
    pinned_at: datetime | None
    updated_at: datetime


class ConversationListResponse(BaseModel):
    data: list[ConversationListItem]
    pagination: Pagination


class MessageResponse(BaseModel):
    """One SQL row: a user message or a whole assistant turn. `content` is the
    AG-UI Message[] bundle the UI renders; a turn may hold several protocol
    messages (text, tool calls and results, reasoning)."""

    id: UUID
    parent_message_id: UUID | None
    role: Literal["user", "assistant"]
    status: MessageStatus
    content: list[dict[str, Any]]
    created_at: datetime


class HistoryResponse(BaseModel):
    current_message_id: UUID | None
    #: The current branch, root first.
    data: list[MessageResponse]


class ChatMessageInput(Input):
    id: UUIDv7
    text: str = Field(max_length=32_000)
    file_ids: list[UUID] = Field(default_factory=list, max_length=20)


class SendMessage(Input):
    #: Null only for the first turn; otherwise the assistant row being answered.
    parent_message_id: UUID | None
    message: ChatMessageInput
