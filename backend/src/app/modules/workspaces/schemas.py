from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas.pagination import Pagination

WorkspaceKind = Literal["personal", "organization"]


class WorkspaceResponse(BaseModel):
    id: UUID
    kind: WorkspaceKind
    #: Organization name; null for the personal workspace (the UI labels it).
    name: str | None
    organization_id: UUID | None


class WorkspaceListResponse(BaseModel):
    data: list[WorkspaceResponse]
    pagination: Pagination


@dataclass(frozen=True)
class WorkspaceContext:
    """A workspace the current user may act in, resolved on this request."""

    id: UUID
    kind: WorkspaceKind
    organization_id: UUID | None
    #: Active membership row in the organization; None for the personal workspace.
    member_id: UUID | None
