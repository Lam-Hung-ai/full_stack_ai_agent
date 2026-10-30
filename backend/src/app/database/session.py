from collections.abc import AsyncIterator, Callable
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings

#: Application tables live in `chat_app`. Trigger and helper functions in the
#: baseline reference them unqualified, so every connection needs this path.
SEARCH_PATH = "chat_app,public"

engine = create_async_engine(
    get_settings().database_url.get_secret_value(),
    pool_pre_ping=True,
    hide_parameters=True,
    pool_size=get_settings().db_pool_size,
    max_overflow=get_settings().db_max_overflow,
    pool_timeout=get_settings().db_pool_timeout,
    connect_args={"options": f"-csearch_path={SEARCH_PATH}"},
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

#: Opens a session of its own, for work outliving the request (a turn's task).
type SessionFactory = Callable[[], AsyncSession]


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide one session per request; services commit their own writes."""
    async with SessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
