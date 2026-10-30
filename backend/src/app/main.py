import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common import redis
from app.common.exceptions.handlers import install_handlers
from app.common.logging import configure_logging
from app.common.request_context import RequestIdMiddleware
from app.config.settings import get_settings
from app.modules.agent.agui import turn_agent
from app.modules.agent.live import LiveStore
from app.modules.agent.runner import Runner
from app.modules.auth.router import router as auth_router
from app.modules.authorization.router import router as authorization_router
from app.modules.conversations.router import router as conversations_router
from app.modules.files.router import router as files_router
from app.modules.folders.router import router as folders_router
from app.modules.members.router import invitations_router
from app.modules.members.router import router as members_router
from app.modules.organizations.router import router as organizations_router
from app.modules.users.router import router as users_router
from app.modules.workspaces.router import router as workspaces_router

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    client = redis.create_redis()
    runner = Runner(
        agent_factory=turn_agent,
        max_concurrent=settings.max_concurrent_turns,
        live=LiveStore(client),
    )
    app.state.runner = runner
    stops = asyncio.create_task(runner.listen_for_stops(), name="turn-stop-listener")
    yield
    # Let running turns finish and save before the process exits.
    await runner.shutdown(timeout=settings.shutdown_grace_seconds)
    stops.cancel()
    with suppress(asyncio.CancelledError):
        await stops
    await client.aclose()


app = FastAPI(title="Agent Backend", version="0.1.0", lifespan=lifespan)

# Order matters: install_handlers adds the unhandled-error middleware, which
# must sit inside CORS so 500 responses still carry CORS headers. The request
# id middleware wraps everything so every response and log line has an id.
install_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)
app.add_middleware(RequestIdMiddleware)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(workspaces_router)
api_router.include_router(conversations_router)
api_router.include_router(folders_router)
api_router.include_router(files_router)
api_router.include_router(organizations_router)
api_router.include_router(members_router)
api_router.include_router(invitations_router)
api_router.include_router(authorization_router)
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
