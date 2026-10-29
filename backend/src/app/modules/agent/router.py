from ag_ui.core import RunAgentInput
from ag_ui.encoder import EventEncoder
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.modules.agent.agui import get_agui_agent

# Scaffold endpoint kept until the conversation API replaces it (sprint S2).
router = APIRouter(tags=["Agent (legacy)"])


@router.post("/agent")
async def agent_endpoint(
    input_data: RunAgentInput, request: Request
) -> StreamingResponse:
    # Wired by hand (instead of ag_ui_langgraph.add_langgraph_fastapi_endpoint) so
    # auth and run ownership stay under the application's control.
    encoder = EventEncoder(accept=request.headers.get("accept", ""))

    # Clone per request: LangGraphAgent keeps per-run state on the instance.
    request_agent = get_agui_agent().clone()

    async def event_generator():
        async for event in request_agent.run(input_data):
            yield encoder.encode(event)

    return StreamingResponse(event_generator(), media_type=encoder.get_content_type())
