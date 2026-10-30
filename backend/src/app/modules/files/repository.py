from collections.abc import Collection
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_message_files as message_files
from app.database.generated_tables import t_messages as messages
from app.database.generated_tables import t_stored_files as stored_files


class FileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, **values: Any) -> RowMapping:
        statement = insert(stored_files).values(**values).returning(stored_files)
        return (await self._session.execute(statement)).mappings().one()

    async def by_ids(self, ids: Collection[UUID]) -> list[RowMapping]:
        """Live private files among `ids`; callers check whose they are."""
        statement = select(stored_files).where(
            stored_files.c.id.in_(ids),
            stored_files.c.deleted_at.is_(None),
            stored_files.c.visibility == "private",
        )
        return list((await self._session.execute(statement)).mappings())

    async def in_conversation(
        self, *, conversation_id: UUID, file_id: UUID
    ) -> RowMapping | None:
        """The file, if a message of the conversation is linked to it
        (as `can_read_conversation_file` requires)."""
        statement = (
            select(stored_files)
            .join(message_files, message_files.c.stored_file_id == stored_files.c.id)
            .join(messages, messages.c.id == message_files.c.message_id)
            .where(
                messages.c.conversation_id == conversation_id,
                stored_files.c.id == file_id,
                stored_files.c.deleted_at.is_(None),
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def link(self, *, message_id: UUID, file_ids: Collection[UUID]) -> None:
        """Attach files to a message that is not terminal yet (trigger)."""
        if file_ids:
            await self._session.execute(
                insert(message_files).values(
                    [{"message_id": message_id, "stored_file_id": f} for f in file_ids]
                )
            )
