from uuid import UUID

from sqlalchemy import RowMapping, delete, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.generated_tables import t_conversation_folders as folders


class FolderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self, *, workspace_id: UUID, owner_user_id: UUID, name: str
    ) -> RowMapping:
        statement = (
            insert(folders)
            .values(workspace_id=workspace_id, owner_user_id=owner_user_id, name=name)
            .returning(folders)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def list_for_owner(
        self, *, workspace_id: UUID, owner_user_id: UUID, limit: int, offset: int
    ) -> tuple[list[RowMapping], int]:
        scope = (
            folders.c.workspace_id == workspace_id,
            folders.c.owner_user_id == owner_user_id,
        )
        total = (
            await self._session.execute(
                select(func.count()).select_from(folders).where(*scope)
            )
        ).scalar_one()
        statement = (
            select(folders)
            .where(*scope)
            .order_by(func.lower(folders.c.name), folders.c.id)
            .limit(limit)
            .offset(offset)
        )
        rows = (await self._session.execute(statement)).mappings().all()
        return list(rows), total

    async def get_for_owner(
        self, *, folder_id: UUID, owner_user_id: UUID
    ) -> RowMapping | None:
        statement = select(folders).where(
            folders.c.id == folder_id, folders.c.owner_user_id == owner_user_id
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def name_taken(
        self,
        *,
        workspace_id: UUID,
        owner_user_id: UUID,
        name: str,
        except_id: UUID | None = None,
    ) -> bool:
        # Same expression as conversation_folders_name_idx.
        statement = select(folders.c.id).where(
            folders.c.workspace_id == workspace_id,
            folders.c.owner_user_id == owner_user_id,
            func.lower(func.btrim(folders.c.name)) == name.strip().lower(),
        )
        if except_id is not None:
            statement = statement.where(folders.c.id != except_id)
        return (await self._session.execute(statement.limit(1))).first() is not None

    async def rename(self, *, folder_id: UUID, name: str) -> RowMapping:
        statement = (
            update(folders)
            .where(folders.c.id == folder_id)
            .values(name=name)
            .returning(folders)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def delete(self, *, folder_id: UUID) -> None:
        # conversations_folder_scope_fk sets the chats' folder_id to null.
        await self._session.execute(delete(folders).where(folders.c.id == folder_id))
