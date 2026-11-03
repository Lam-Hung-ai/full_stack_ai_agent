from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas.common import Input, Name


class OrganizationCreate(Input):
    name: Name


class OrganizationUpdate(Input):
    name: Name


class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    workspace_id: UUID
    created_at: datetime
    #: What the current member may do here, as `resource.action` keys; the
    #: UI shows admin screens by them, the API checks again on every call.
    permissions: list[str]
    is_owner: bool
