"""Remove files nothing refers to (RR-17).

A file is recorded at `complete`, before the question that uses it is sent;
one never sent stays under its final key. Once old enough, its row goes
first and then its object: a row without bytes would break a chat, bytes
without a row only cost storage.
"""

import logging
from datetime import timedelta

from sqlalchemy.exc import DBAPIError

from app.common.storage.client import ObjectStorage
from app.common.storage.exceptions import ObjectStorageError
from app.config.security import now
from app.database.session import SessionFactory
from app.modules.files.repository import FileRepository

logger = logging.getLogger(__name__)

BATCH = 100


async def purge_unattached(
    *, session_factory: SessionFactory, storage: ObjectStorage, older_than: timedelta
) -> int:
    """Delete files never attached within `older_than`; returns how many."""
    removed = 0
    cutoff = now() - older_than
    skipped: set[object] = set()
    while True:
        async with session_factory() as session:
            rows = [
                row
                for row in await FileRepository(session).unattached(
                    created_before=cutoff, limit=BATCH + len(skipped)
                )
                if row["id"] not in skipped
            ]
        if not rows:
            return removed
        for row in rows:
            async with session_factory() as session:
                try:
                    await FileRepository(session).remove(file_id=row["id"])
                    await session.commit()
                except DBAPIError:
                    # Attached meanwhile: the trigger keeps it.
                    await session.rollback()
                    skipped.add(row["id"])
                    continue
            try:
                await storage.delete_object(
                    bucket=row["bucket"], object_key=row["object_key"]
                )
            except ObjectStorageError:
                logger.warning("Could not delete object %s", row["object_key"])
            removed += 1
