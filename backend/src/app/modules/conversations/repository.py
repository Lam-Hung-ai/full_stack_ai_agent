from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, func, insert, literal, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import now
from app.database.generated_tables import t_conversations as conversations
from app.database.generated_tables import t_messages as messages
from app.modules.conversations.schemas import ACTIVE_STATUSES

DEFAULT_TITLE = "Cuộc trò chuyện mới"


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, workspace_id: UUID, owner_user_id: UUID, title: str | None
    ) -> RowMapping:
        values: dict[str, Any] = {
            "workspace_id": workspace_id,
            "owner_user_id": owner_user_id,
        }
        if title:
            values["title"] = title
        statement = insert(conversations).values(values).returning(conversations)
        return (await self._session.execute(statement)).mappings().one()

    async def list_for_owner(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        archived: bool,
        folder_id: UUID | None,
        unfiled: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[RowMapping], int]:
        scope = [
            conversations.c.workspace_id == workspace_id,
            conversations.c.owner_user_id == owner_user_id,
            conversations.c.deleted_at.is_(None),
            conversations.c.archived_at.is_not(None)
            if archived
            else conversations.c.archived_at.is_(None),
        ]
        if folder_id is not None:
            scope.append(conversations.c.folder_id == folder_id)
        elif unfiled:
            scope.append(conversations.c.folder_id.is_(None))
        total = (
            await self._session.execute(
                select(func.count()).select_from(conversations).where(*scope)
            )
        ).scalar_one()
        statement = (
            select(
                conversations.c.id,
                conversations.c.title,
                conversations.c.pinned_at,
                conversations.c.archived_at,
                conversations.c.folder_id,
                conversations.c.updated_at,
            )
            .where(*scope)
            # Pinned chats first, then conversations_sidebar_idx order; id
            # breaks ties for a stable page boundary.
            .order_by(
                conversations.c.pinned_at.desc().nulls_last(),
                conversations.c.updated_at.desc(),
                conversations.c.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).mappings().all()
        return list(rows), total

    async def get_for_owner(
        self, *, conversation_id: UUID, owner_user_id: UUID, lock: bool = False
    ) -> RowMapping | None:
        statement = select(conversations).where(
            conversations.c.id == conversation_id,
            conversations.c.owner_user_id == owner_user_id,
            conversations.c.deleted_at.is_(None),
        )
        if lock:
            statement = statement.with_for_update()
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def update(self, *, conversation_id: UUID, **values: Any) -> RowMapping:
        statement = (
            update(conversations)
            .where(conversations.c.id == conversation_id)
            .values(**values)
            .returning(conversations)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def soft_delete(self, *, conversation_id: UUID) -> None:
        await self._session.execute(
            update(conversations)
            .where(conversations.c.id == conversation_id)
            .values(deleted_at=now())
        )


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(
        self, *, conversation_id: UUID, message_id: UUID
    ) -> RowMapping | None:
        statement = select(messages).where(
            messages.c.conversation_id == conversation_id,
            messages.c.id == message_id,
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def exists(self, *, message_id: UUID) -> bool:
        statement = select(messages.c.id).where(messages.c.id == message_id)
        return (await self._session.execute(statement)).first() is not None

    async def has_any(self, *, conversation_id: UUID) -> bool:
        statement = (
            select(messages.c.id)
            .where(messages.c.conversation_id == conversation_id)
            .limit(1)
        )
        return (await self._session.execute(statement)).first() is not None

    async def active_assistant(self, *, conversation_id: UUID) -> RowMapping | None:
        statement = select(messages.c.id, messages.c.status).where(
            messages.c.conversation_id == conversation_id,
            messages.c.role == "assistant",
            messages.c.status.in_(ACTIVE_STATUSES),
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def insert(
        self,
        *,
        message_id: UUID | None = None,
        conversation_id: UUID,
        parent_message_id: UUID | None,
        role: str,
        status: str,
        content: list[dict[str, Any]],
    ) -> RowMapping:
        values: dict[str, Any] = {
            "conversation_id": conversation_id,
            "parent_message_id": parent_message_id,
            "role": role,
            "status": status,
            "content": content,
        }
        if message_id is not None:
            values["id"] = message_id
        statement = insert(messages).values(values).returning(messages)
        return (await self._session.execute(statement)).mappings().one()

    async def set_status(
        self,
        *,
        message_id: UUID,
        status: str,
        content: list[dict[str, Any]] | None = None,
    ) -> None:
        """Only an active message changes: terminal rows are immutable, and a
        turn finishing after a stop already marked it cancelled is a no-op."""
        values: dict[str, Any] = {"status": status}
        if content is not None:
            values["content"] = content
        await self._session.execute(
            update(messages)
            .where(messages.c.id == message_id, messages.c.status.in_(ACTIVE_STATUSES))
            .values(values)
        )

    async def links(self, *, conversation_id: UUID) -> list[tuple[UUID, UUID | None]]:
        """(id, parent) of every message, oldest first (messages_history_idx)."""
        statement = (
            select(messages.c.id, messages.c.parent_message_id)
            .where(messages.c.conversation_id == conversation_id)
            .order_by(messages.c.created_at, messages.c.id)
        )
        rows = (await self._session.execute(statement)).all()
        return [(row.id, row.parent_message_id) for row in rows]

    async def branch(self, *, conversation_id: UUID, leaf_id: UUID) -> list[RowMapping]:
        """The path from `leaf_id` up to the root, returned root first.

        Follows parent links, never creation time: siblings from edits and
        regenerations share a parent and must not leak into the path."""
        path = (
            select(messages, literal(0).label("depth"))
            .where(
                messages.c.conversation_id == conversation_id,
                messages.c.id == leaf_id,
            )
            .cte("path", recursive=True)
        )
        parent = messages.alias("parent")
        path = path.union_all(
            select(parent, (path.c.depth + 1).label("depth")).where(
                parent.c.id == path.c.parent_message_id,
                parent.c.conversation_id == conversation_id,
            )
        )
        statement = select(path).order_by(path.c.depth.desc())
        return list((await self._session.execute(statement)).mappings().all())
