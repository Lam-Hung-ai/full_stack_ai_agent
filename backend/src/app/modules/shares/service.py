"""Share a chat as a sealed snapshot of its whole tree (O03; database phase 1
§7–8, phase 2 §8; QD-28).

A personal chat is shared by public link, an organization chat only with
active members of that organization. Readers get the snapshot, never the
live conversation; publishing again makes a new version behind the same link.
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.common.storage.client import ObjectStorage
from app.common.storage.exceptions import ObjectStorageError
from app.config.security import digest, now
from app.modules.authorization.service import AuthorizationService
from app.modules.conversations.repository import MessageRepository
from app.modules.conversations.service import ConversationService
from app.modules.conversations.tree import MessageTree
from app.modules.files.policy import STORED_FILE_SCHEME
from app.modules.files.repository import FileRepository
from app.modules.files.schemas import DownloadResponse
from app.modules.shares.links import link_token_hash, share_url
from app.modules.shares.repository import ShareRepository
from app.modules.shares.schemas import (
    SharedConversation,
    SharedMessage,
    ShareResponse,
)

SHARE_PERMISSION = ("conversation", "share")


class ShareService:
    def __init__(
        self, session: AsyncSession, storage: ObjectStorage | None = None
    ) -> None:
        self._session = session
        self._storage = storage
        self._shares = ShareRepository(session)

    async def get(self, *, user: Principal, conversation_id: UUID) -> ShareResponse:
        await ConversationService(self._session).require_owned(
            user=user, conversation_id=conversation_id
        )
        share = await self._shares.live_share(
            conversation_id=conversation_id, created_by=user.id
        )
        published = (
            await self._shares.published(share_id=share["id"]) if share else None
        )
        if share is None or published is None:
            fail(404, "share_not_found")
        return _response(share, published["version"], published["sealed_at"])

    async def publish(self, *, user: Principal, conversation_id: UUID) -> ShareResponse:
        """Create the share if needed and publish the chat as it is now."""
        conversation, workspace = await ConversationService(self._session).owned(
            user=user, conversation_id=conversation_id, lock=True
        )
        await AuthorizationService(self._session).require(workspace, *SHARE_PERMISSION)
        tree = await MessageRepository(self._session).tree(
            conversation_id=conversation_id
        )
        if not tree:
            fail(409, "nothing_to_share")
        if any(row["status"] not in TERMINAL for row in tree):
            # The snapshot needs a consistent baseline (phase 1 §8.9).
            fail(409, "conversation_busy")
        share = await self._shares.live_share(
            conversation_id=conversation_id, created_by=user.id
        )
        try:
            if share is None:
                share_id = UUID(str(uuid7()))
                await self._shares.add_share(
                    id=share_id,
                    source_conversation_id=conversation_id,
                    workspace_id=workspace.id,
                    created_by=user.id,
                    mode="public" if workspace.kind == "personal" else "organization",
                    organization_id=workspace.organization_id,
                    link_token_hash=link_token_hash(share_id),
                )
                share = await self._shares.live_share(
                    conversation_id=conversation_id, created_by=user.id
                )
                assert share is not None
            snapshot = await self._shares.add_snapshot(
                share_id=share["id"],
                workspace_id=workspace.id,
                title=conversation["title"],
            )
            current = await self._fill(snapshot["id"], workspace.id, conversation, tree)
            sealed_at = await self._shares.seal(
                snapshot_id=snapshot["id"], current_message_id=current
            )
            await self._shares.publish(share_id=share["id"], snapshot_id=snapshot["id"])
            await self._session.commit()
        except DBAPIError:
            # A turn started between the check and the snapshot triggers.
            await self._session.rollback()
            fail(409, "conversation_busy")
        return _response(share, snapshot["version"], sealed_at)

    async def revoke(self, *, user: Principal, conversation_id: UUID) -> None:
        await ConversationService(self._session).require_owned(
            user=user, conversation_id=conversation_id
        )
        share = await self._shares.live_share(
            conversation_id=conversation_id, created_by=user.id
        )
        if share is None:
            fail(404, "share_not_found")
        await self._shares.revoke(share_id=share["id"])
        await self._session.commit()

    async def view(self, *, user: Principal | None, token: str) -> SharedConversation:
        share = await self.readable(user=user, token=token)
        rows = await self._shares.snapshot_messages(
            snapshot_id=share["current_snapshot_id"]
        )
        tree = MessageTree((row["id"], row["parent_message_id"]) for row in rows)
        return SharedConversation(
            title=share["title"],
            mode=share["mode"],
            version=share["version"],
            published_at=share["sealed_at"],
            current_message_id=share["current_message_id"],
            messages=[
                SharedMessage(
                    id=row["id"],
                    parent_message_id=row["parent_message_id"],
                    role=row["role"],
                    status=row["status"],
                    content=row["content"],
                    created_at=row["original_created_at"],
                    sibling_ids=tree.siblings(row["id"]),
                )
                for row in rows
            ],
            can_copy=user is not None,
        )

    async def file_link(
        self, *, user: Principal | None, token: str, file_id: UUID
    ) -> DownloadResponse:
        share = await self.readable(user=user, token=token)
        if not await self._shares.can_read_file(
            user_id=user.id if user else None, share_id=share["id"], file_id=file_id
        ):
            fail(404, "file_not_found")
        (row,) = await FileRepository(self._session).by_ids([file_id])
        assert self._storage is not None
        try:
            request = self._storage.create_download_request(
                bucket=row["bucket"],
                object_key=row["object_key"],
                filename=row["original_name"],
                inline=row["content_type"].startswith("image/"),
            )
        except ObjectStorageError:
            fail(503, "storage_unavailable")
        return DownloadResponse(url=request.url, expires_at=_expiry(request.expires_in))

    async def readable(self, *, user: Principal | None, token: str) -> RowMapping:
        """The share behind a link, if this reader may read it now; one 404
        for every other case so a link reveals nothing."""
        share = await self._shares.by_token_hash(digest(token))
        if share is None or not await self._shares.can_read(
            user_id=user.id if user else None, share_id=share["id"]
        ):
            fail(404, "share_not_found")
        return share

    async def _fill(
        self,
        snapshot_id: UUID,
        workspace_id: UUID,
        conversation: RowMapping,
        tree: list[RowMapping],
    ) -> UUID:
        """Copy the transcript into the snapshot under new ids; returns the
        snapshot id of the branch the owner had open."""
        new_id = {row["id"]: UUID(str(uuid7())) for row in tree}
        await self._shares.add_messages(
            [
                {
                    "snapshot_id": snapshot_id,
                    "id": new_id[row["id"]],
                    "parent_message_id": new_id.get(row["parent_message_id"]),
                    "role": row["role"],
                    "status": row["status"],
                    "content": remap_bundle(row, new_id[row["id"]], {}),
                    "attachments": row["attachments"],
                    "original_created_at": row["created_at"],
                }
                for row in tree
            ]
        )
        links = await FileRepository(self._session).links_of(
            conversation_id=conversation["id"]
        )
        await self._shares.add_files(
            snapshot_id=snapshot_id,
            workspace_id=workspace_id,
            file_ids=list(dict.fromkeys(link["id"] for link in links)),
        )
        await self._shares.add_message_files(
            snapshot_id=snapshot_id,
            links=[(new_id[link["message_id"]], link["id"]) for link in links],
        )
        current = conversation["current_message_id"] or MessageTree(
            (row["id"], row["parent_message_id"]) for row in tree
        ).latest_leaf(tree[0]["id"])
        return new_id[current]


TERMINAL = frozenset({"completed", "failed", "cancelled"})


def remap_bundle(
    row: RowMapping | dict[str, Any], message_id: UUID, files: dict[str, str]
) -> list[dict[str, Any]]:
    """A row's AG-UI bundle for a new row id: the user message takes the new
    id (as stored questions do) and file parts point at `files` (old → new);
    in an answer, tool results naming a file the agent made point there too."""
    if row["role"] != "user":
        return [_remap_tool_result(message, files) for message in row["content"]]
    (question,) = row["content"]
    content = question.get("content")
    if isinstance(content, list) and files:
        content = [_remap_part(part, files) for part in content]
    return [{**question, "id": str(message_id), "content": content}]


def _remap_tool_result(
    message: dict[str, Any], files: dict[str, str]
) -> dict[str, Any]:
    content = message.get("content")
    if not files or message.get("role") != "tool" or not isinstance(content, str):
        return message
    for old, new in files.items():
        content = content.replace(old, new)
    return {**message, "content": content}


def _remap_part(part: dict[str, Any], files: dict[str, str]) -> dict[str, Any]:
    old = part.get("id")
    if old not in files:
        return part
    source = {**part["source"], "value": f"{STORED_FILE_SCHEME}{files[old]}"}
    return {**part, "id": files[old], "source": source}


def _response(share: RowMapping, version: int, published_at: datetime) -> ShareResponse:
    return ShareResponse(
        id=share["id"],
        mode=share["mode"],
        url=share_url(share["id"]),
        version=version,
        published_at=published_at,
    )


def _expiry(seconds: int) -> datetime:
    return now() + timedelta(seconds=seconds)
