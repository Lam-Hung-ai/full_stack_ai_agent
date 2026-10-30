"""Which files a chat accepts and how the model sees each (QD-27)."""

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from app.common.storage.file_types import (
    CSV,
    GIF,
    JPEG,
    JSON,
    MARKDOWN,
    PDF,
    PLAIN_TEXT,
    PNG,
    WEBP,
    FileType,
)

MAX_FILE_BYTES = 10 * 1024 * 1024
#: Files on one question.
MAX_FILES_PER_MESSAGE = 10
#: Characters of a text file given to the model; the rest is cut.
MAX_TEXT_CHARS = 200_000

#: image: the model sees the picture; document: the provider reads the PDF;
#: text: the model reads the file's text inline.
type FileKind = Literal["image", "document", "text"]


@dataclass(frozen=True)
class ChatFileType:
    type: FileType
    kind: FileKind


CHAT_FILE_TYPES: dict[str, ChatFileType] = {
    item.type.mime: item
    for item in (
        ChatFileType(PNG, "image"),
        ChatFileType(JPEG, "image"),
        ChatFileType(GIF, "image"),
        ChatFileType(WEBP, "image"),
        ChatFileType(PDF, "document"),
        ChatFileType(PLAIN_TEXT, "text"),
        ChatFileType(MARKDOWN, "text"),
        ChatFileType(CSV, "text"),
        ChatFileType(JSON, "text"),
    )
}

#: Scheme of the placeholder source a stored message keeps for a file: the
#: bytes are fetched again for each turn, presigned URLs are never stored.
STORED_FILE_SCHEME = "stored-file:"


def upload_key(*, workspace_id: UUID, user_id: UUID, file_id: UUID) -> str:
    """Where the browser puts the bytes before `complete` checks them."""
    return f"private/temp/uploads/workspaces/{workspace_id}/users/{user_id}/{file_id}"


def file_key(*, workspace_id: UUID, file_id: UUID) -> str:
    """Final key: the workspace in the key scopes a file not yet attached."""
    return f"private/workspaces/{workspace_id}/files/{file_id}"
