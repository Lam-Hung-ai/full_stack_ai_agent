from uuid import UUID

from sqlalchemy import RowMapping
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.common.schemas.pagination import PageParams, Pagination
from app.modules.folders.repository import FolderRepository
from app.modules.folders.schemas import (
    FolderCreate,
    FolderListResponse,
    FolderResponse,
    FolderUpdate,
)
from app.modules.workspaces.schemas import WorkspaceContext
from app.modules.workspaces.service import WorkspaceService


class FolderService:
    """Flat, personal folders inside one workspace (no nesting, no sharing).
    Like chats they belong to their owner; no permission beyond membership."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._folders = FolderRepository(session)

    async def create(
        self, *, user: Principal, workspace: WorkspaceContext, data: FolderCreate
    ) -> FolderResponse:
        await self._ensure_free_name(workspace.id, user.id, data.name)
        try:
            row = await self._folders.create(
                workspace_id=workspace.id, owner_user_id=user.id, name=data.name
            )
            await self._session.commit()
        except IntegrityError:
            # A concurrent create took the name after the check.
            await self._session.rollback()
            fail(409, "folder_name_taken")
        return FolderResponse.model_validate(dict(row))

    async def list(
        self, *, user: Principal, workspace: WorkspaceContext, params: PageParams
    ) -> FolderListResponse:
        rows, total = await self._folders.list_for_owner(
            workspace_id=workspace.id,
            owner_user_id=user.id,
            limit=params.page_size,
            offset=params.offset,
        )
        return FolderListResponse(
            data=[FolderResponse.model_validate(dict(row)) for row in rows],
            pagination=Pagination.of(params, total),
        )

    async def rename(
        self, *, user: Principal, folder_id: UUID, data: FolderUpdate
    ) -> FolderResponse:
        folder = await self.require_owned(user=user, folder_id=folder_id)
        await self._ensure_free_name(
            folder["workspace_id"], user.id, data.name, except_id=folder_id
        )
        try:
            row = await self._folders.rename(folder_id=folder_id, name=data.name)
            await self._session.commit()
        except IntegrityError:
            await self._session.rollback()
            fail(409, "folder_name_taken")
        return FolderResponse.model_validate(dict(row))

    async def delete(self, *, user: Principal, folder_id: UUID) -> None:
        """Chats inside move back to the main list; none is deleted."""
        await self.require_owned(user=user, folder_id=folder_id)
        await self._folders.delete(folder_id=folder_id)
        await self._session.commit()

    async def require_owned(
        self, *, user: Principal, folder_id: UUID, workspace_id: UUID | None = None
    ) -> RowMapping:
        """The caller's folder, in `workspace_id` when given, while the caller
        still belongs to its workspace; anything else is 404."""
        row = await self._folders.get_for_owner(
            folder_id=folder_id, owner_user_id=user.id
        )
        if row is None or (
            workspace_id is not None and row["workspace_id"] != workspace_id
        ):
            fail(404, "folder_not_found")
        await WorkspaceService(self._session).context(
            user_id=user.id, workspace_id=row["workspace_id"]
        )
        return row

    async def _ensure_free_name(
        self,
        workspace_id: UUID,
        user_id: UUID,
        name: str,
        except_id: UUID | None = None,
    ) -> None:
        if await self._folders.name_taken(
            workspace_id=workspace_id,
            owner_user_id=user_id,
            name=name,
            except_id=except_id,
        ):
            fail(409, "folder_name_taken")
