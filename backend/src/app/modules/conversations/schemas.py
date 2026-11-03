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
from app.modules.files.policy import MAX_ATTACHMENTS_PER_TURN

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)
]
TurnState = Literal[
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
    status: TurnState


class ConversationResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    title: str
    current_turn_id: UUID | None
    pinned_at: datetime | None
    archived_at: datetime | None
    folder_id: UUID | None
    created_at: datetime
    updated_at: datetime
    active_assistant: ActiveAssistant | None = None


#: Sidebar order after pinned chats: newest activity or newest created.
ConversationSort = Literal["updated", "created"]


class ConversationListItem(BaseModel):
    id: UUID
    title: str
    pinned_at: datetime | None
    archived_at: datetime | None
    folder_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    data: list[ConversationListItem]
    pagination: Pagination


class ConversationSearchItem(BaseModel):
    id: UUID
    title: str
    archived_at: datetime | None
    updated_at: datetime
    #: The newest matching turn (open the chat through it), or null when
    #: only the title matches.
    turn_id: UUID | None
    snippet: str | None


class ConversationSearchResponse(BaseModel):
    data: list[ConversationSearchItem]
    pagination: Pagination


class TurnResponse(BaseModel):
    """One turn: a user question or a whole assistant answer. `content` is the
    AG-UI Message[] bundle the UI renders; an assistant turn may hold several
    protocol messages (text, tool calls and results, reasoning)."""

    id: UUID
    parent_turn_id: UUID | None
    role: Literal["user", "assistant"]
    status: TurnState
    content: list[dict[str, Any]]
    created_at: datetime
    #: Last change; a finished turn no longer changes, so for one it is when
    #: the turn ended.
    updated_at: datetime
    #: How long an assistant turn's runs took, summed: a pause waiting for
    #: the user is not counted. None for questions and older turns.
    work_seconds: float | None = None
    #: Every version at this position (same parent), oldest first, this one
    #: included; more than one means the UI offers a branch switch.
    sibling_ids: list[UUID]


class HistoryResponse(BaseModel):
    #: Leaf of the returned branch.
    current_turn_id: UUID | None
    #: The branch, root first.
    data: list[TurnResponse]


class TurnInput(Input):
    id: UUIDv7
    text: str = Field(max_length=32_000)
    file_ids: list[UUID] = Field(
        default_factory=list, max_length=MAX_ATTACHMENTS_PER_TURN
    )


class SendTurn(Input):
    #: Null only for the first turn; otherwise the assistant row being answered.
    parent_turn_id: UUID | None
    turn: TurnInput


class EditTurn(Input):
    #: The new version, with its full list of files (API §4).
    turn: TurnInput


class ResumeTurn(Input):
    """Answers to every interrupt the assistant waits on (API §5), in the
    SDK's own `ResumeEntry` shape (`interruptId`, `status`, `payload`):
    `{"answer": "..."}` for a question, `{"approved": true}` for a tool."""

    resume: list[ResumeEntry] = Field(min_length=1, max_length=20)


class StopResponse(BaseModel):
    """Acknowledgement (API §7): the status the assistant has now. A turn that
    did not stop within the wait still shows `running`."""

    id: UUID
    status: TurnState
