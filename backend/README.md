# agent-backend

FastAPI + LangGraph backend. Runs a LangGraph ReAct-style agent (via `langchain.agents.create_agent`) behind an [AG-UI protocol](https://docs.ag-ui.com) endpoint, streamed over SSE, using an OpenRouter-hosted model through [`langchain-openrouter`](https://pypi.org/project/langchain-openrouter/)'s `ChatOpenRouter`.

## Setup

```bash
cp .env.example .env
# edit .env and set OPENROUTER_API_KEY (get one at https://openrouter.ai/keys)
uv sync
```

## Run

```bash
uv run uvicorn agent_backend.main:app --reload --port 8000
```

- `GET /health` — liveness check, no API key needed.
- `POST /agent` — AG-UI endpoint. Body is an AG-UI `RunAgentInput`; response is an AG-UI event stream (`text/event-stream`): `RUN_STARTED`, `TEXT_MESSAGE_*`, `TOOL_CALL_*`, `REASONING_*`, `STATE_SNAPSHOT`, `MESSAGES_SNAPSHOT`, `RUN_FINISHED`/`RUN_ERROR`.

`OPENROUTER_REASONING_EFFORT` (`.env`) turns on model "thinking"/reasoning tokens when the chosen model supports them (set it to an empty string to turn it off). OpenRouter streams this as `delta.reasoning`, which the base `langchain-openai` client doesn't parse — `langchain-openrouter`'s `ChatOpenRouter` does, surfacing it as `REASONING_START/MESSAGE_CONTENT/END` events that the frontend renders in a collapsible "Thought for..." block.

## Structure

- `src/agent_backend/agent_graph.py` — builds the LangGraph agent (model, tools, checkpointer).
- `src/agent_backend/agui.py` — wraps the compiled graph as an `ag_ui_langgraph.LangGraphAgent`.
- `src/agent_backend/main.py` — FastAPI app, CORS, and the `/agent` route.
- `src/agent_backend/config.py` — environment variables (OpenRouter key/model/base URL, CORS origins).

## AG-UI wiring

`/agent` is wired by hand in `main.py` (not via `ag_ui_langgraph.add_langgraph_fastapi_endpoint`), so an auth/authz dependency can be added later, e.g.:

```python
@app.post("/agent")
async def agent_endpoint(
    input_data: RunAgentInput,
    request: Request,
    user: User = Depends(get_current_user),
):
    ...
```

The graph uses `InMemorySaver` as its checkpointer (required for AG-UI's `thread_id`-based runs/interrupts) — swap it for a persistent saver (Postgres/Redis) before deploying, since it currently resets on restart and doesn't work across multiple workers.
