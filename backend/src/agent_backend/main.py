from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .agui import get_agui_agent
from .config import CORS_ORIGINS

app = FastAPI(title="Agent Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent")
async def agent_endpoint(input_data: RunAgentInput, request: Request) -> StreamingResponse:
    # Wired by hand (instead of ag_ui_langgraph.add_langgraph_fastapi_endpoint) so an
    # auth/authz dependency can be added here later, e.g.:
    #   async def agent_endpoint(input_data: RunAgentInput, request: Request, user=Depends(get_current_user)):
    encoder = EventEncoder(accept=request.headers.get("accept"))

    # Clone per request: LangGraphAgent keeps per-run state on the instance.
    request_agent = get_agui_agent().clone()

    async def event_generator():
        async for event in request_agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
