from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import RowMapping, func, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security import now
from app.database.generated_tables import t_conversation_copy_files as copy_files
from app.database.generated_tables import t_conversation_copy_jobs as copy_jobs
from app.database.generated_tables import t_conversation_shares as shares
from app.database.generated_tables import t_share_snapshot_files as snapshot_files
from app.database.generated_tables import (
    t_share_snapshot_message_files as snapshot_message_files,
)
from app.database.generated_tables import t_share_snapshot_messages as snapshot_messages
from app.database.generated_tables import t_share_snapshots as snapshots
from app.database.generated_tables import t_stored_files as stored_files


class ShareRepository:
    """Shares, their sealed snapshots and copy jobs (database phase 1 §7–9)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Shares

    async def live_share(
        self, *, conversation_id: UUID, created_by: UUID
    ) -> RowMapping | None:
        statement = (
            select(shares)
            .where(
                shares.c.source_conversation_id == conversation_id,
                shares.c.created_by == created_by,
                shares.c.revoked_at.is_(None),
            )
            .order_by(shares.c.created_at.desc())
            .limit(1)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def add_share(self, **values: Any) -> None:
        await self._session.execute(insert(shares).values(**values))

    async def publish(self, *, share_id: UUID, snapshot_id: UUID) -> None:
        await self._session.execute(
            update(shares)
            .where(shares.c.id == share_id)
            .values(current_snapshot_id=snapshot_id)
        )

    async def revoke(self, *, share_id: UUID) -> None:
        await self._session.execute(
            update(shares)
            .where(shares.c.id == share_id, shares.c.revoked_at.is_(None))
            .values(revoked_at=now())
        )

    async def by_token_hash(self, token_hash: str) -> RowMapping | None:
        """A share with its published snapshot, whatever its state; callers
        decide readability with `can_read`."""
        statement = (
            select(
                shares,
                snapshots.c.title,
                snapshots.c.version,
                snapshots.c.sealed_at,
                snapshots.c.current_message_id,
            )
            .join(snapshots, snapshots.c.id == shares.c.current_snapshot_id)
            .where(shares.c.link_token_hash == token_hash)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def published(self, *, share_id: UUID) -> RowMapping | None:
        statement = (
            select(snapshots.c.version, snapshots.c.sealed_at)
            .join(shares, shares.c.current_snapshot_id == snapshots.c.id)
            .where(shares.c.id == share_id)
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def can_read(self, *, user_id: UUID | None, share_id: UUID) -> bool:
        statement = text("SELECT chat_app.can_read_share(:user_id, :share_id)")
        result = await self._session.execute(
            statement, {"user_id": user_id, "share_id": share_id}
        )
        return bool(result.scalar_one())

    async def can_read_file(
        self, *, user_id: UUID | None, share_id: UUID, file_id: UUID
    ) -> bool:
        statement = text(
            "SELECT chat_app.can_read_share_file(:user_id, :share_id, :file_id)"
        )
        result = await self._session.execute(
            statement, {"user_id": user_id, "share_id": share_id, "file_id": file_id}
        )
        return bool(result.scalar_one())

    # Snapshots

    async def add_snapshot(
        self, *, share_id: UUID, workspace_id: UUID, title: str
    ) -> RowMapping:
        version = (
            select(func.coalesce(func.max(snapshots.c.version), 0) + 1)
            .where(snapshots.c.share_id == share_id)
            .scalar_subquery()
        )
        statement = (
            insert(snapshots)
            .values(
                share_id=share_id,
                workspace_id=workspace_id,
                version=version,
                title=title,
            )
            .returning(snapshots.c.id, snapshots.c.version)
        )
        return (await self._session.execute(statement)).mappings().one()

    async def add_messages(self, rows: list[dict[str, Any]]) -> None:
        if rows:
            await self._session.execute(insert(snapshot_messages).values(rows))

    async def add_files(
        self, *, snapshot_id: UUID, workspace_id: UUID, file_ids: list[UUID]
    ) -> None:
        if file_ids:
            await self._session.execute(
                insert(snapshot_files).values(
                    [
                        {
                            "snapshot_id": snapshot_id,
                            "workspace_id": workspace_id,
                            "stored_file_id": file_id,
                        }
                        for file_id in file_ids
                    ]
                )
            )

    async def add_message_files(
        self, *, snapshot_id: UUID, links: list[tuple[UUID, UUID]]
    ) -> None:
        if links:
            await self._session.execute(
                insert(snapshot_message_files).values(
                    [
                        {
                            "snapshot_id": snapshot_id,
                            "message_id": m,
                            "stored_file_id": f,
                        }
                        for m, f in links
                    ]
                )
            )

    async def seal(self, *, snapshot_id: UUID, current_message_id: UUID) -> datetime:
        statement = (
            update(snapshots)
            .where(snapshots.c.id == snapshot_id)
            .values(current_message_id=current_message_id, sealed_at=now())
            .returning(snapshots.c.sealed_at)
        )
        return (await self._session.execute(statement)).scalar_one()

    async def snapshot_messages(self, *, snapshot_id: UUID) -> list[RowMapping]:
        statement = (
            select(snapshot_messages)
            .where(snapshot_messages.c.snapshot_id == snapshot_id)
            .order_by(snapshot_messages.c.original_created_at, snapshot_messages.c.id)
        )
        return list((await self._session.execute(statement)).mappings())

    async def snapshot_file_links(self, *, snapshot_id: UUID) -> list[RowMapping]:
        """(message_id, file row) of every file in the snapshot."""
        statement = (
            select(snapshot_message_files.c.message_id, stored_files)
            .join(
                stored_files,
                stored_files.c.id == snapshot_message_files.c.stored_file_id,
            )
            .where(snapshot_message_files.c.snapshot_id == snapshot_id)
        )
        return list((await self._session.execute(statement)).mappings())

    # Copy jobs

    async def job(
        self, *, requested_by: UUID, client_request_id: str
    ) -> RowMapping | None:
        statement = select(copy_jobs).where(
            copy_jobs.c.requested_by == requested_by,
            copy_jobs.c.client_request_id == client_request_id,
        )
        return (await self._session.execute(statement)).mappings().one_or_none()

    async def add_job(self, **values: Any) -> RowMapping:
        statement = insert(copy_jobs).values(**values).returning(copy_jobs)
        return (await self._session.execute(statement)).mappings().one()

    async def add_copy_files(
        self, *, job_id: UUID, pairs: list[tuple[UUID, UUID]]
    ) -> None:
        if pairs:
            await self._session.execute(
                insert(copy_files).values(
                    [
                        {
                            "job_id": job_id,
                            "source_stored_file_id": source,
                            "target_stored_file_id": target,
                        }
                        for source, target in pairs
                    ]
                )
            )

    async def claim(self, *, job_id: UUID, lease_token: UUID, seconds: int) -> bool:
        """Take the job unless another request holds a live lease on it."""
        statement = (
            update(copy_jobs)
            .where(
                copy_jobs.c.id == job_id,
                copy_jobs.c.status.in_(("pending", "copying", "failed")),
                (copy_jobs.c.lease_expires_at.is_(None))
                | (copy_jobs.c.lease_expires_at < now()),
            )
            .values(
                status="copying",
                lease_token=lease_token,
                lease_expires_at=func.now()
                + text(f"interval '{int(seconds)} seconds'"),
                attempts=copy_jobs.c.attempts + 1,
            )
            .returning(copy_jobs.c.id)
        )
        return (await self._session.execute(statement)).first() is not None

    async def pending_copies(self, *, job_id: UUID) -> list[RowMapping]:
        source = stored_files.alias("source")
        target = stored_files.alias("target")
        statement = (
            select(
                copy_files.c.source_stored_file_id,
                copy_files.c.target_stored_file_id,
                source.c.bucket.label("source_bucket"),
                source.c.object_key.label("source_key"),
                target.c.bucket.label("target_bucket"),
                target.c.object_key.label("target_key"),
            )
            .join(source, source.c.id == copy_files.c.source_stored_file_id)
            .join(target, target.c.id == copy_files.c.target_stored_file_id)
            .where(copy_files.c.job_id == job_id, copy_files.c.status != "copied")
        )
        return list((await self._session.execute(statement)).mappings())

    async def mark_copied(
        self, *, job_id: UUID, lease_token: UUID, target_file_id: UUID
    ) -> bool:
        """Only while this request still holds the lease (fencing)."""
        held = (
            select(copy_jobs.c.id)
            .where(copy_jobs.c.id == job_id, copy_jobs.c.lease_token == lease_token)
            .exists()
        )
        statement = (
            update(copy_files)
            .where(
                copy_files.c.job_id == job_id,
                copy_files.c.target_stored_file_id == target_file_id,
                held,
            )
            .values(status="copied")
            .returning(copy_files.c.job_id)
        )
        return (await self._session.execute(statement)).first() is not None

    async def finish(
        self,
        *,
        job_id: UUID,
        lease_token: UUID,
        status: str,
        error: str | None = None,
    ) -> bool:
        statement = (
            update(copy_jobs)
            .where(copy_jobs.c.id == job_id, copy_jobs.c.lease_token == lease_token)
            .values(
                status=status,
                completed_at=now() if status == "completed" else None,
                lease_token=None,
                lease_expires_at=None,
                last_error=error,
            )
            .returning(copy_jobs.c.id)
        )
        return (await self._session.execute(statement)).first() is not None
