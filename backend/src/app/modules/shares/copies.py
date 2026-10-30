"""Continue a shared chat as one's own copy (O04; database phase 1 §9, §13).

The copy is a new conversation with new message and file ids and new
objects holding copied bytes; it stays hidden (`can_read_conversation`)
until its job completes. The job is tied to one snapshot version and to the
caller's `client_request_id`, so a retry finishes the same copy. Bytes are
copied server-side in the request under a lease (no worker yet, QD-15,
QD-28); a request that loses the lease cannot record a copy.
"""

from uuid import UUID

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_utils.compat import uuid7

from app.common.dependencies.auth import Principal
from app.common.exceptions.handlers import fail
from app.common.storage.client import ObjectStorage
from app.common.storage.exceptions import ObjectStorageError
from app.modules.authorization.service import AuthorizationService
from app.modules.conversations.repository import (
    ConversationRepository,
    MessageRepository,
)
from app.modules.files.policy import file_key
from app.modules.files.repository import FileRepository
from app.modules.shares.repository import ShareRepository
from app.modules.shares.schemas import CopyRequest, CopyResponse
from app.modules.shares.service import ShareService, remap_bundle
from app.modules.workspaces.repository import WorkspaceRepository
from app.modules.workspaces.service import WorkspaceService

LEASE_SECONDS = 120


class CopyService:
    def __init__(self, session: AsyncSession, storage: ObjectStorage) -> None:
        self._session = session
        self._storage = storage
        self._shares = ShareRepository(session)

    async def copy(
        self, *, user: Principal, token: str, data: CopyRequest
    ) -> CopyResponse:
        share = await ShareService(self._session).readable(user=user, token=token)
        job = await self._shares.job(
            requested_by=user.id, client_request_id=data.client_request_id
        )
        if job is not None and job["snapshot_id"] != share["current_snapshot_id"]:
            # Same request id for another copy (phase 1 §9): refuse, never merge.
            fail(409, "copy_request_conflict")
        if job is None:
            job = await self._prepare(user, share, data.client_request_id)
        if job["status"] != "completed":
            await self._copy_bytes(user, share, job)
        return CopyResponse(
            conversation_id=job["target_conversation_id"],
            workspace_id=job["target_workspace_id"],
        )

    async def _prepare(
        self, user: Principal, share: RowMapping, client_request_id: str
    ) -> RowMapping:
        """One transaction: the empty target, its job, the remapped tree and
        a new object (key reserved, bytes pending) for every file."""
        workspace_id = await self._target_workspace(user, share)
        workspace = await WorkspaceService(self._session).context(
            user_id=user.id, workspace_id=workspace_id
        )
        await AuthorizationService(self._session).require(
            workspace, "conversation", "create"
        )
        snapshot_id = share["current_snapshot_id"]
        conversations = ConversationRepository(self._session)
        target = await conversations.create(
            workspace_id=workspace_id, owner_user_id=user.id, title=share["title"]
        )
        # The job comes before any payload (guard_copy_scope).
        job = await self._shares.add_job(
            requested_by=user.id,
            snapshot_id=snapshot_id,
            target_workspace_id=workspace_id,
            target_conversation_id=target["id"],
            client_request_id=client_request_id,
        )
        files = FileRepository(self._session)
        links = await self._shares.snapshot_file_links(snapshot_id=snapshot_id)
        new_file: dict[str, str] = {}
        for link in links:
            if str(link["id"]) in new_file:
                continue
            target_file = UUID(str(uuid7()))
            await files.add(
                id=target_file,
                bucket=link["bucket"],
                object_key=file_key(workspace_id=workspace_id, file_id=target_file),
                original_name=link["original_name"],
                content_type=link["content_type"],
                visibility="private",
                size_bytes=link["size_bytes"],
                checksum_sha256=link["checksum_sha256"],
                uploaded_by=user.id,
            )
            new_file[str(link["id"])] = str(target_file)
        await self._shares.add_copy_files(
            job_id=job["id"],
            pairs=[(UUID(old), UUID(new)) for old, new in new_file.items()],
        )
        current = await self._copy_tree(
            snapshot_id, share["current_message_id"], target["id"], new_file, links
        )
        await conversations.update(
            conversation_id=target["id"], current_message_id=current
        )
        await self._session.commit()
        return job

    async def _copy_tree(
        self,
        snapshot_id: UUID,
        current_message_id: UUID,
        conversation_id: UUID,
        new_file: dict[str, str],
        links: list[RowMapping],
    ) -> UUID:
        rows = await self._shares.snapshot_messages(snapshot_id=snapshot_id)
        new_id = {row["id"]: UUID(str(uuid7())) for row in rows}
        files_of: dict[UUID, list[UUID]] = {}
        for link in links:
            files_of.setdefault(link["message_id"], []).append(
                UUID(new_file[str(link["id"])])
            )
        messages = MessageRepository(self._session)
        files = FileRepository(self._session)
        for row in rows:
            attached = files_of.get(row["id"], [])
            # Links are refused on terminal rows: stage pending, link, finish.
            await messages.insert(
                message_id=new_id[row["id"]],
                conversation_id=conversation_id,
                parent_message_id=new_id.get(row["parent_message_id"]),
                role=row["role"],
                status="pending" if attached else row["status"],
                content=remap_bundle(row, new_id[row["id"]], new_file),
            )
            if attached:
                await files.link(message_id=new_id[row["id"]], file_ids=attached)
                await messages.set_status(
                    message_id=new_id[row["id"]], status=row["status"]
                )
        return new_id[current_message_id]

    async def _copy_bytes(
        self, user: Principal, share: RowMapping, job: RowMapping
    ) -> None:
        lease = UUID(str(uuid7()))
        if not await self._shares.claim(
            job_id=job["id"], lease_token=lease, seconds=LEASE_SECONDS
        ):
            await self._session.rollback()
            fail(409, "copy_in_progress")
        await self._session.commit()
        pending = await self._shares.pending_copies(job_id=job["id"])
        try:
            for item in pending:
                await self._storage.copy_object(
                    source_bucket=item["source_bucket"],
                    source_key=item["source_key"],
                    destination_bucket=item["target_bucket"],
                    destination_key=item["target_key"],
                )
                if not await self._shares.mark_copied(
                    job_id=job["id"],
                    lease_token=lease,
                    target_file_id=item["target_stored_file_id"],
                ):
                    fail(409, "copy_in_progress")
                await self._session.commit()
        except ObjectStorageError:
            await self._shares.finish(
                job_id=job["id"], lease_token=lease, status="failed", error="storage"
            )
            await self._session.commit()
            fail(503, "storage_unavailable")
        # Finalize under the share's rules as they are now (phase 1 §13).
        if not await self._shares.can_read(user_id=user.id, share_id=share["id"]):
            await self._shares.finish(
                job_id=job["id"], lease_token=lease, status="cancelled"
            )
            await self._session.commit()
            fail(404, "share_not_found")
        if not await self._shares.finish(
            job_id=job["id"], lease_token=lease, status="completed"
        ):
            fail(409, "copy_in_progress")
        await self._session.commit()

    async def _target_workspace(self, user: Principal, share: RowMapping) -> UUID:
        """Public → the reader's personal workspace; organization → that
        organization's workspace (never across the two, phase 1 §7)."""
        workspaces = WorkspaceRepository(self._session)
        if share["mode"] == "public":
            rows, _ = await workspaces.list_for_user(user_id=user.id, limit=1, offset=0)
            personal = [row for row in rows if row["kind"] == "personal"]
            return personal[0]["id"]
        row = await workspaces.accessible_by_organization(
            user_id=user.id, organization_id=share["organization_id"]
        )
        if row is None:
            fail(404, "share_not_found")
        return row["id"]
