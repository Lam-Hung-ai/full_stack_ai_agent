from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, StringConstraints

from app.common.schemas.common import Input
from app.modules.files.policy import MAX_FILE_BYTES, FileKind

FileName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)
]


class UploadCreate(Input):
    """What the browser is about to upload; `complete` checks it for real."""

    original_name: FileName
    content_type: str = Field(min_length=1, max_length=255)
    size_bytes: int = Field(ge=1, le=MAX_FILE_BYTES)


class PresignedUpload(BaseModel):
    url: str
    method: str
    #: Send exactly these headers: they are part of the signature.
    headers: dict[str, str]
    expires_at: datetime


class UploadResponse(BaseModel):
    file_id: UUID
    upload: PresignedUpload


class FileResponse(BaseModel):
    id: UUID
    original_name: str
    content_type: str
    size_bytes: int
    kind: FileKind


class DownloadResponse(BaseModel):
    """A short-lived link; returned in the body, never as a redirect."""

    url: str
    expires_at: datetime
