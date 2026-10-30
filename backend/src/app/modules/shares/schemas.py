from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas.common import Input

ShareMode = Literal["public", "organization"]


class ShareResponse(BaseModel):
    """The owner's view of a chat's share."""

    id: UUID
    mode: ShareMode
    url: str
    version: int
    published_at: datetime


class SharedMessage(BaseModel):
    id: UUID
    parent_message_id: UUID | None
    role: str
    status: str
    content: list[dict[str, Any]]
    created_at: datetime
    sibling_ids: list[UUID]


class SharedConversation(BaseModel):
    """A published snapshot: the whole tree as it was, not the live chat."""

    title: str
    mode: ShareMode
    version: int
    published_at: datetime
    #: Leaf of the branch the owner had open; the reader starts there.
    current_message_id: UUID
    messages: list[SharedMessage]
    #: Whether the reader may continue it as a copy of their own.
    can_copy: bool


class CopyRequest(Input):
    #: Same id again (a retry) returns the same copy.
    client_request_id: str = Field(min_length=1, max_length=100)


class CopyResponse(BaseModel):
    conversation_id: UUID
    workspace_id: UUID
