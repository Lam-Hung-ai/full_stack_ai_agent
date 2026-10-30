from datetime import datetime
from typing import Annotated, Any, Literal
from uuid import UUID

from ag_ui.core import ResumeEntry
from pydantic import (
    AfterValidator,
    BaseModel,
    Field,
    StringConstraints,
    model_validator,
)

from app.common.schemas.common import Input
from app.common.schemas.pagination import Pagination
from app.modules.files.policy import MAX_FILES_PER_MESSAGE

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
    """Allowlist of what a PATCH may change (API §10); omitted fields stay.
    `folder_id: null` takes the chat out of its folder."""

    title: Title | None = None
    pinned: bool | None = None
    archived: bool | None = None
    folder_id: UUID | None = None

    @model_validator(mode="after")
    def _check_fields(self) -> "ConversationUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field is required")
        for name in ("title", "pinned", "archived"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self


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
    archived_at: datetime | None
    folder_id: UUID | None
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
    #: Every version at this position (same parent), oldest first, this one
    #: included; more than one means the UI offers a branch switch.
    sibling_ids: list[UUID]


class HistoryResponse(BaseModel):
    #: Leaf of the returned branch.
    current_message_id: UUID | None
    #: The branch, root first.
    data: list[MessageResponse]


class ChatMessageInput(Input):
    id: UUIDv7
    text: str = Field(max_length=32_000)
    file_ids: list[UUID] = Field(default_factory=list, max_length=MAX_FILES_PER_MESSAGE)


class SendMessage(Input):
    #: Null only for the first turn; otherwise the assistant row being answered.
    parent_message_id: UUID | None
    message: ChatMessageInput


class EditMessage(Input):
    #: The new version, with its full list of files (API §4).
    message: ChatMessageInput


class ResumeMessage(Input):
    """Answers to every interrupt the assistant waits on (API §5), in the
    SDK's own `ResumeEntry` shape (`interruptId`, `status`, `payload`):
    `{"answer": "..."}` for a question, `{"approved": true}` for a tool."""

    resume: list[ResumeEntry] = Field(min_length=1, max_length=20)


class StopResponse(BaseModel):
    """Acknowledgement (API §7): the status the assistant has now. A turn that
    did not stop within the wait still shows `running`."""

    id: UUID
    status: MessageStatus
