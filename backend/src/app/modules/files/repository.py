from collections.abc import Collection
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_conversation_copy_files as copy_files
from app.database.generated_tables import t_share_snapshot_files as snapshot_files
from app.database.generated_tables import t_stored_files as stored_files
from app.database.generated_tables import t_turn_files as turn_files
from app.database.generated_tables import t_turns as turns


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
        """The file, if a turn of the conversation is linked to it
        (as `can_read_conversation_file` requires)."""
        statement = (
            select(stored_files)
            .join(turn_files, turn_files.c.stored_file_id == stored_files.c.id)
            .join(turns, turns.c.id == turn_files.c.turn_id)
            .where(
                turns.c.conversation_id == conversation_id,
                stored_files.c.id == file_id,
                stored_files.c.deleted_at.is_(None),
            )
            .limit(1)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def links_of(self, *, conversation_id: UUID) -> list[RowMapping]:
        """(turn_id, file row) of every file attached in the conversation."""
        statement = (
            select(turn_files.c.turn_id, stored_files)
            .join(stored_files, stored_files.c.id == turn_files.c.stored_file_id)
            .join(turns, turns.c.id == turn_files.c.turn_id)
            .where(turns.c.conversation_id == conversation_id)
        )
        return list((await self._session.execute(statement)).mappings())

    async def link(self, *, turn_id: UUID, file_ids: Collection[UUID]) -> None:
        """Attach files to a turn that is not terminal yet (trigger)."""
        if file_ids:
            await self._session.execute(
                insert(turn_files).values(
                    [{"turn_id": turn_id, "stored_file_id": f} for f in file_ids]
                )
            )

    async def unattached(
        self, *, created_before: datetime, limit: int
    ) -> list[RowMapping]:
        """Files nothing refers to: no turn, snapshot or copy (RR-17)."""
        statement = (
            select(stored_files)
            .where(
                stored_files.c.deleted_at.is_(None),
                stored_files.c.created_at < created_before,
                ~exists().where(turn_files.c.stored_file_id == stored_files.c.id),
                ~exists().where(snapshot_files.c.stored_file_id == stored_files.c.id),
                ~exists().where(
                    or_(
                        copy_files.c.source_stored_file_id == stored_files.c.id,
                        copy_files.c.target_stored_file_id == stored_files.c.id,
                    )
                ),
            )
            .order_by(stored_files.c.created_at)
            .limit(limit)
        )
        return list((await self._session.execute(statement)).mappings())

    async def remove(self, *, file_id: UUID) -> None:
        """The trigger refuses while anything still refers to the file."""
        await self._session.execute(
            delete(stored_files).where(stored_files.c.id == file_id)
        )
