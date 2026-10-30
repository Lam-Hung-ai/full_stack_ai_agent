"""Chat files: presigned upload, verified completion, attachment and download
(AGENTS §17.6, database phase 2 §7, QD-27).

A file is recorded in `stored_files` only once `complete` has checked the
bytes, under its final key. Until a message links it, the workspace in that
key and `uploaded_by` say who may attach it; once linked, the database keeps
it within that owner and workspace.
"""

import base64
import hashlib
import logging
from collections.abc import Sequence
from datetime import timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.common.storage.client import ObjectStorage
from app.common.storage.exceptions import ObjectNotFoundError, ObjectStorageError
from app.common.storage.file_types import SNIFF_BYTES, extension_of
from app.config.security import now
from app.config.settings import get_settings
from app.database.session import SessionFactory
from app.modules.authorization.service import AuthorizationService
from app.modules.files.policy import (
    CHAT_FILE_TYPES,
    MAX_FILE_BYTES,
    MAX_FILES_PER_MESSAGE,
    MAX_TEXT_CHARS,
    MAX_TURN_FILE_BYTES,
    STORED_FILE_SCHEME,
    ChatFileType,
    file_key,
    upload_key,
)
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import (
    DownloadResponse,
    FileResponse,
    PresignedUpload,
    UploadCreate,
    UploadResponse,
)
from app.modules.workspaces.schemas import WorkspaceContext

logger = logging.getLogger(__name__)

#: Attaching a file is part of chatting in the workspace.
UPLOAD_PERMISSION = ("conversation", "create")


class FileService:
    def __init__(
        self,
        session: AsyncSession,
        storage: ObjectStorage | None = None,
        repository: FileRepository | None = None,
    ) -> None:
        self._session = session
        self._storage_adapter = storage
        self._files = repository or FileRepository(session)

    @property
    def _storage(self) -> ObjectStorage:
        """Only uploads and downloads touch storage; attaching does not."""
        if self._storage_adapter is None:
            raise RuntimeError("FileService needs object storage for this call")
        return self._storage_adapter

    async def create_upload(
        self, *, user: Principal, workspace: WorkspaceContext, data: UploadCreate
    ) -> UploadResponse:
        await AuthorizationService(self._session).require(workspace, *UPLOAD_PERMISSION)
        chat_type = _accepted(data)
        file_id = UUID(str(uuid7()))
        try:
            request = self._storage.create_upload_request(
                bucket=get_settings().storage_bucket,
                object_key=upload_key(
                    workspace_id=workspace.id, user_id=user.id, file_id=file_id
                ),
                content_type=chat_type.type.mime,
            )
        except ObjectStorageError:
            fail(503, "storage_unavailable")
        return UploadResponse(
            file_id=file_id,
            upload=PresignedUpload(
                url=request.url,
                method=request.method,
                headers=request.headers,
                expires_at=now() + timedelta(seconds=request.expires_in),
            ),
        )

    async def complete(
        self,
        *,
        user: Principal,
        workspace: WorkspaceContext,
        file_id: UUID,
        data: UploadCreate,
    ) -> FileResponse:
        """Check the uploaded bytes against what was declared, record the file
        and write those same bytes to the final key. The row is committed
        before the write, so a second `complete` can never overwrite a recorded
        object; the temporary object goes either way."""
        await AuthorizationService(self._session).require(workspace, *UPLOAD_PERMISSION)
        chat_type = _accepted(data)
        # No transaction stays open across storage calls (AGENTS §19).
        await self._session.commit()
        bucket = get_settings().storage_bucket
        temporary = upload_key(
            workspace_id=workspace.id, user_id=user.id, file_id=file_id
        )
        final = file_key(workspace_id=workspace.id, file_id=file_id)
        try:
            try:
                # The browser may PUT again while this reads: only the bytes
                # checked here are stored, never the temporary object itself.
                content = await self._verified_bytes(bucket, temporary, data, chat_type)
            except ObjectStorageError:
                fail(503, "storage_unavailable")
            try:
                row = await self._files.add(
                    id=file_id,
                    bucket=bucket,
                    object_key=final,
                    original_name=data.original_name,
                    content_type=chat_type.type.mime,
                    visibility="private",
                    size_bytes=len(content),
                    checksum_sha256=hashlib.sha256(content).hexdigest(),
                    uploaded_by=user.id,
                )
                await self._session.commit()
            except IntegrityError:
                # Completed already: that row owns the final object, keep it.
                await self._session.rollback()
                fail(409, "upload_completed")
            try:
                await self._storage.put_object(
                    bucket=bucket,
                    object_key=final,
                    content_type=chat_type.type.mime,
                    body=content,
                )
            except ObjectStorageError:
                await self._files.remove(file_id=file_id)
                await self._session.commit()
                fail(503, "storage_unavailable")
        finally:
            await self._discard(bucket, temporary)
        return file_response(row)

    async def attachable(
        self, *, user: Principal, workspace: WorkspaceContext, ids: Sequence[UUID]
    ) -> list[RowMapping]:
        """The files of a question, in the order given: each must be the
        user's own upload in this workspace."""
        unique = list(dict.fromkeys(ids))
        if len(unique) > MAX_FILES_PER_MESSAGE:
            fail(422, "too_many_files", details={"max": MAX_FILES_PER_MESSAGE})
        rows = {row["id"]: row for row in await self._files.by_ids(unique)}
        for file_id in unique:
            row = rows.get(file_id)
            if (
                row is None
                or row["uploaded_by"] != user.id
                or row["object_key"]
                != file_key(workspace_id=workspace.id, file_id=file_id)
            ):
                fail(422, "invalid_file", details={"file_id": str(file_id)})
        return [rows[file_id] for file_id in unique]

    async def download(
        self, *, conversation_id: UUID, file_id: UUID
    ) -> DownloadResponse:
        """For a conversation the caller has been checked to own."""
        row = await self._files.in_conversation(
            conversation_id=conversation_id, file_id=file_id
        )
        if row is None:
            fail(404, "file_not_found")
        chat_type = CHAT_FILE_TYPES.get(row["content_type"])
        try:
            request = self._storage.create_download_request(
                bucket=row["bucket"],
                object_key=row["object_key"],
                filename=row["original_name"],
                # Pictures show in the chat; anything else downloads.
                inline=chat_type is not None and chat_type.kind == "image",
            )
        except ObjectStorageError:
            fail(503, "storage_unavailable")
        return DownloadResponse(
            url=request.url, expires_at=now() + timedelta(seconds=request.expires_in)
        )

    async def _verified_bytes(
        self, bucket: str, key: str, data: UploadCreate, chat_type: ChatFileType
    ) -> bytes:
        try:
            head = await self._storage.head_object(bucket=bucket, object_key=key)
        except ObjectNotFoundError:
            fail(409, "upload_missing")
        if head.size_bytes != data.size_bytes or head.size_bytes > MAX_FILE_BYTES:
            fail(422, "upload_size_mismatch")
        content = await self._storage.read_object(
            bucket=bucket, object_key=key, max_bytes=MAX_FILE_BYTES
        )
        if not chat_type.type.fits(content[:SNIFF_BYTES]):
            fail(415, "file_content_mismatch")
        return content

    async def _discard(self, bucket: str, key: str) -> None:
        try:
            await self._storage.delete_object(bucket=bucket, object_key=key)
        except ObjectStorageError:
            # Storage lifecycle on private/temp/ removes what is left (RR-17).
            logger.warning("Could not delete object %s", key)


def _accepted(data: UploadCreate) -> ChatFileType:
    """A supported type whose extension matches; the bytes are checked later."""
    chat_type = CHAT_FILE_TYPES.get(data.content_type.split(";")[0].strip().lower())
    if chat_type is None or extension_of(data.original_name) not in (
        chat_type.type.extensions
    ):
        fail(415, "unsupported_file_type")
    return chat_type


def file_response(row: RowMapping) -> FileResponse:
    return FileResponse(
        id=row["id"],
        original_name=row["original_name"],
        content_type=row["content_type"],
        size_bytes=row["size_bytes"],
        kind=CHAT_FILE_TYPES[row["content_type"]].kind,
    )


def file_part(row: RowMapping) -> dict[str, Any]:
    """How a question stores an attached file: an AG-UI media part whose
    source names the file, never its bytes or a presigned URL."""
    kind = CHAT_FILE_TYPES[row["content_type"]].kind
    return {
        "type": "image" if kind == "image" else "document",
        "id": str(row["id"]),
        "source": {
            "type": "url",
            "value": f"{STORED_FILE_SCHEME}{row['id']}",
            "mimeType": row["content_type"],
        },
        "metadata": {"filename": row["original_name"], "sizeBytes": row["size_bytes"]},
    }


async def resolve_files(
    messages: list[dict[str, Any]],
    *,
    session_factory: SessionFactory,
    storage: ObjectStorage,
) -> list[dict[str, Any]]:
    """Model input for a turn: each stored file part becomes what the model
    can read (picture or PDF inline, text files as text). Runs inside the
    turn, after the request's transaction has committed."""
    # Newest question first, so the budget keeps the files asked about now.
    ids = list(
        dict.fromkeys(
            UUID(part["id"])
            for message in reversed(messages)
            if message.get("role") == "user"
            and isinstance(message.get("content"), list)
            for part in message["content"]
            if _stored(part)
        )
    )
    if not ids:
        return messages
    async with session_factory() as session:
        rows = {row["id"]: row for row in await FileRepository(session).by_ids(ids)}
    resolved: dict[str, dict[str, Any]] = {}
    budget = MAX_TURN_FILE_BYTES
    for file_id in ids:
        row = rows.get(file_id)
        if row is None:
            resolved[str(file_id)] = _gone()
        elif row["size_bytes"] > budget:
            resolved[str(file_id)] = _not_sent(row["original_name"])
        else:
            budget -= row["size_bytes"]
            resolved[str(file_id)] = await _model_part(row, storage)
    return [
        {
            **message,
            "content": [
                resolved[part["id"]] if _stored(part) else part
                for part in message["content"]
            ],
        }
        if message.get("role") == "user" and isinstance(message.get("content"), list)
        else message
        for message in messages
    ]


def _stored(part: Any) -> bool:
    source = part.get("source") if isinstance(part, dict) else None
    return (
        isinstance(source, dict)
        and str(source.get("value", "")).startswith(STORED_FILE_SCHEME)
        and bool(part.get("id"))
    )


async def _model_part(row: RowMapping, storage: ObjectStorage) -> dict[str, Any]:
    content = await storage.read_object(
        bucket=row["bucket"], object_key=row["object_key"], max_bytes=MAX_FILE_BYTES
    )
    name = row["original_name"]
    kind = CHAT_FILE_TYPES[row["content_type"]].kind
    if kind == "text":
        text = content.decode("utf-8", errors="replace")[:MAX_TEXT_CHARS]
        return {"type": "text", "text": f"Tệp đính kèm {name}:\n\n{text}"}
    return {
        "type": kind,
        "source": {
            "type": "data",
            "value": base64.b64encode(content).decode("ascii"),
            "mimeType": row["content_type"],
        },
        "metadata": {"filename": name},
    }


def _gone() -> dict[str, Any]:
    return {"type": "text", "text": "[Tệp đính kèm không còn]"}


def _not_sent(name: str) -> dict[str, Any]:
    return {
        "type": "text",
        "text": f"[Tệp đính kèm {name} không gửi lại: vượt dung lượng tệp mỗi lượt]",
    }
