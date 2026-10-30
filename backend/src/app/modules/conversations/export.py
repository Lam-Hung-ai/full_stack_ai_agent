"""Export one's own chats of a workspace as a zip (use case O08, QD-31).

Each chat becomes a folder with `conversation.json` (the whole tree: every
message, its AG-UI bundle, status and attached files) and `conversation.md`
(the saved branch as plain text). Attached files are listed by name, type
and size; their bytes are not included. The zip is streamed one chat at a
time, each read in a short transaction of its own.
"""

import io
import json
import re
import unicodedata
import zipfile
from collections.abc import AsyncIterator, Iterator
from datetime import datetime
from typing import Any
from urllib.parse import quote
from uuid import UUID

from sqlalchemy import RowMapping

from app.database.session import SessionFactory
from app.modules.conversations.repository import MessageRepository
from app.modules.files.repository import FileRepository

ROLE_HEADINGS = {"user": "Bạn", "assistant": "Agent"}


class _Chunks(io.RawIOBase):
    """An unseekable stream collecting what the zip writer produces."""

    def __init__(self) -> None:
        self._parts: list[bytes] = []

    def writable(self) -> bool:
        return True

    def write(self, data: Any) -> int:
        self._parts.append(bytes(data))
        return len(data)

    def drain(self) -> bytes:
        data, self._parts = b"".join(self._parts), []
        return data


def archive_name(workspace_label: str, at: datetime) -> str:
    """E.g. "Chat Cá nhân 30-10-2026.zip": whose chats and from when."""
    return f"{_clean(f'Chat {workspace_label} {at:%d-%m-%Y}') or 'Chat'}.zip"


def content_disposition(name: str) -> str:
    """Attachment header with the UTF-8 name and a plain-ASCII fallback."""
    plain = unicodedata.normalize("NFKD", name.replace("đ", "d").replace("Đ", "D"))
    ascii_name = plain.encode("ascii", "ignore").decode().replace('"', "") or "chat.zip"
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"


async def export_zip(
    *,
    session_factory: SessionFactory,
    conversations: list[RowMapping],
    manifest: dict[str, Any],
) -> AsyncIterator[bytes]:
    """The zip of `conversations`, a chunk per chat."""
    sink = _Chunks()
    with zipfile.ZipFile(sink, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "manifest.json",
            _json({**manifest, "conversations": len(conversations)}),
        )
        for conversation, folder in zip(
            conversations, _folders(conversations), strict=True
        ):
            async with session_factory() as session:
                rows = await MessageRepository(session).tree(
                    conversation_id=conversation["id"]
                )
                links = await FileRepository(session).links_of(
                    conversation_id=conversation["id"]
                )
            files = _files_by_message(links)
            archive.writestr(
                f"{folder}/conversation.json",
                _json(_document(conversation, rows, files)),
            )
            archive.writestr(
                f"{folder}/conversation.md", _markdown(conversation, rows, files)
            )
            yield sink.drain()
    yield sink.drain()


def _clean(text: str, limit: int = 80) -> str:
    """Readable as a file or folder name on every system: no separators or
    reserved characters, single spaces, no trailing dot."""
    text = re.sub(r'[\x00-\x1f/\\:*?"<>|]+', " ", text)
    return " ".join(text.split())[:limit].strip(" .")


def _folders(conversations: list[RowMapping]) -> list[str]:
    """ "2026-10-30 Kế hoạch du lịch" per chat; same names get " (2)", " (3)"."""
    seen: dict[str, int] = {}
    names: list[str] = []
    for conversation in conversations:
        title = _clean(conversation["title"]) or "Chat"
        base = f"{conversation['created_at']:%Y-%m-%d} {title}"
        seen[base] = seen.get(base, 0) + 1
        names.append(base if seen[base] == 1 else f"{base} ({seen[base]})")
    return names


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def _files_by_message(links: list[RowMapping]) -> dict[UUID, list[dict[str, Any]]]:
    files: dict[UUID, list[dict[str, Any]]] = {}
    for link in links:
        files.setdefault(link["message_id"], []).append(
            {
                "id": str(link["id"]),
                "name": link["original_name"],
                "content_type": link["content_type"],
                "size_bytes": link["size_bytes"],
            }
        )
    return files


def _document(
    conversation: RowMapping,
    rows: list[RowMapping],
    files: dict[UUID, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "id": conversation["id"],
        "title": conversation["title"],
        "created_at": conversation["created_at"],
        "updated_at": conversation["updated_at"],
        "archived_at": conversation["archived_at"],
        "current_message_id": conversation["current_message_id"],
        "messages": [
            {
                "id": row["id"],
                "parent_message_id": row["parent_message_id"],
                "role": row["role"],
                "status": row["status"],
                "created_at": row["created_at"],
                "content": row["content"],
                "files": files.get(row["id"], []),
            }
            for row in rows
        ],
    }


def _branch(rows: list[RowMapping], leaf: UUID | None) -> list[RowMapping]:
    by_id = {row["id"]: row for row in rows}
    path: list[RowMapping] = []
    while leaf is not None and leaf in by_id:
        path.append(by_id[leaf])
        leaf = by_id[leaf]["parent_message_id"]
    return path[::-1]


def _texts(row: RowMapping) -> Iterator[str]:
    """What a row says: question text, or the answer's assistant text."""
    for message in row["content"]:
        content = message.get("content")
        if message.get("role") not in ("user", "assistant"):
            continue
        if isinstance(content, str) and content.strip():
            yield content
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    yield str(part.get("text", ""))


def _markdown(
    conversation: RowMapping,
    rows: list[RowMapping],
    files: dict[UUID, list[dict[str, Any]]],
) -> str:
    lines = [f"# {conversation['title']}", ""]
    for row in _branch(rows, conversation["current_message_id"]):
        lines += [f"## {ROLE_HEADINGS.get(row['role'], row['role'])}", ""]
        lines += [text.strip() for text in _texts(row)]
        if row["status"] in ("failed", "cancelled"):
            lines.append(f"_({row['status']})_")
        lines += [
            f"- Tệp: {file['name']} ({file['content_type']}, {file['size_bytes']} B)"
            for file in files.get(row["id"], [])
        ]
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
