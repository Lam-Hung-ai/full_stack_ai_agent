"""Files the agent writes for the user (use case D06, QD-31).

The `create_file` tool hands over a name, a format and either text or rows.
This module renders the bytes, stores them under the workspace's key and
attaches the file to the assistant message of the running turn, so it is
downloaded, shared and copied like an uploaded file. Spreadsheet cells are
written as data, never as formulas (CSV/formula injection).
"""

import csv
import hashlib
import io
import logging
import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from sqlalchemy import func, select
from uuid_utils.compat import uuid7

from app.common.storage.client import ObjectStorage
from app.common.storage.exceptions import ObjectStorageError
from app.config.settings import get_settings
from app.database.generated_tables import t_message_files as message_files
from app.database.session import SessionFactory
from app.modules.files.policy import file_key
from app.modules.files.repository import FileRepository

logger = logging.getLogger(__name__)

type GeneratedFormat = Literal["csv", "md", "txt", "xlsx"]

XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@dataclass(frozen=True)
class OutputType:
    mime: str
    extension: str


OUTPUT_TYPES: dict[str, OutputType] = {
    "csv": OutputType("text/csv", ".csv"),
    "md": OutputType("text/markdown", ".md"),
    "txt": OutputType("text/plain", ".txt"),
    "xlsx": OutputType(XLSX_MIME, ".xlsx"),
}

MAX_GENERATED_BYTES = 5 * 1024 * 1024
#: Files one turn may create; a model in a loop stops here.
MAX_FILES_PER_TURN = 5
MAX_ROWS = 10_000
MAX_COLUMNS = 100
MAX_NAME = 120
#: A cell starting with one of these is read as a formula by spreadsheets.
FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


class GeneratedFileError(ValueError):
    """The request cannot become a file; the message is shown to the model."""


@dataclass(frozen=True)
class GeneratedFile:
    id: UUID
    name: str
    content_type: str
    size_bytes: int

    def as_result(self) -> dict[str, Any]:
        """What the tool returns; the client renders a file card from it."""
        return {
            "file_id": str(self.id),
            "name": self.name,
            "content_type": self.content_type,
            "size_bytes": self.size_bytes,
        }


def file_name(name: str, output: OutputType) -> str:
    """A readable file name with the format's extension: models like
    `bang_chi_phi`, people read "bang chi phi" better."""
    stem = re.sub(r"[\x00-\x1f/\\:*?\"<>|_]+", " ", name).strip(" .")
    if stem.lower().endswith(output.extension):
        stem = stem[: -len(output.extension)].strip(" .")
    stem = " ".join(stem.split())[: MAX_NAME - len(output.extension)] or "tep"
    return stem + output.extension


def _as_text(value: Any) -> str:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return str(value)  # a negative number is data, not a formula
    text = "" if value is None else str(value)
    return "'" + text if text.startswith(FORMULA_START) else text


def _check_rows(rows: Sequence[Sequence[Any]] | None) -> Sequence[Sequence[Any]]:
    if not rows:
        raise GeneratedFileError("rows is required for csv and xlsx")
    if len(rows) > MAX_ROWS or any(len(row) > MAX_COLUMNS for row in rows):
        raise GeneratedFileError(
            f"at most {MAX_ROWS} rows of {MAX_COLUMNS} columns are allowed"
        )
    return rows


def _csv(rows: Sequence[Sequence[Any]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    for row in rows:
        writer.writerow([_as_text(value) for value in row])
    # A BOM lets spreadsheet apps read Vietnamese text as UTF-8.
    return ("﻿" + buffer.getvalue()).encode()


def _xlsx(rows: Sequence[Sequence[Any]]) -> bytes:
    from openpyxl import Workbook
    from openpyxl.cell.cell import Cell

    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row, start=1):
            cell = sheet.cell(row=r, column=c)
            assert isinstance(cell, Cell)  # a new sheet has no merged cells
            if isinstance(value, bool) or not isinstance(value, int | float):
                cell.value = "" if value is None else str(value)
                cell.data_type = "s"  # text even when it starts with "="
            else:
                cell.value = value
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def render(
    fmt: str, content: str | None, rows: Sequence[Sequence[Any]] | None
) -> bytes:
    if fmt == "csv":
        data = _csv(_check_rows(rows))
    elif fmt == "xlsx":
        data = _xlsx(_check_rows(rows))
    elif fmt in ("md", "txt"):
        if not content:
            raise GeneratedFileError("content is required for md and txt")
        data = content.encode()
    else:
        raise GeneratedFileError(f"unsupported format {fmt!r}")
    if len(data) > MAX_GENERATED_BYTES:
        raise GeneratedFileError(f"the file exceeds {MAX_GENERATED_BYTES} bytes")
    return data


async def save_generated(
    *,
    session_factory: SessionFactory,
    storage: ObjectStorage,
    owner_id: UUID,
    workspace_id: UUID,
    assistant_id: UUID,
    name: str,
    fmt: str,
    content: str | None,
    rows: Sequence[Sequence[Any]] | None,
) -> GeneratedFile:
    """Render, store and attach one file to the running assistant. Bytes go
    first: a row without its object would break the chat, an object without
    a row only costs storage until it is removed."""
    output = OUTPUT_TYPES.get(fmt)
    if output is None:
        raise GeneratedFileError(f"unsupported format {fmt!r}")
    async with session_factory() as session:
        made = (
            await session.execute(
                select(func.count())
                .select_from(message_files)
                .where(message_files.c.message_id == assistant_id)
            )
        ).scalar_one()
    if made >= MAX_FILES_PER_TURN:
        raise GeneratedFileError(f"at most {MAX_FILES_PER_TURN} files per answer")
    data = render(fmt, content, rows)
    file_id = UUID(str(uuid7()))
    bucket = get_settings().storage_bucket
    key = file_key(workspace_id=workspace_id, file_id=file_id)
    await storage.put_object(
        bucket=bucket, object_key=key, content_type=output.mime, body=data
    )
    try:
        async with session_factory() as session:
            files = FileRepository(session)
            await files.add(
                id=file_id,
                bucket=bucket,
                object_key=key,
                original_name=file_name(name, output),
                content_type=output.mime,
                visibility="private",
                size_bytes=len(data),
                checksum_sha256=hashlib.sha256(data).hexdigest(),
                uploaded_by=owner_id,
            )
            await files.link(message_id=assistant_id, file_ids=[file_id])
            await session.commit()
    except Exception:
        try:
            await storage.delete_object(bucket=bucket, object_key=key)
        except ObjectStorageError:
            logger.warning("Could not delete object %s", key)
        raise
    return GeneratedFile(file_id, file_name(name, output), output.mime, len(data))
