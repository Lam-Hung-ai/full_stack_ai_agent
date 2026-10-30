from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.schemas.common import Input, Name
from app.common.schemas.pagination import Pagination


class FolderCreate(Input):
    name: Name


class FolderUpdate(Input):
    name: Name


class FolderResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class FolderListResponse(BaseModel):
    data: list[FolderResponse]
    pagination: Pagination
