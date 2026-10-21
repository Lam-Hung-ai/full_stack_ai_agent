# agent_project

- `backend/` — FastAPI + LangGraph agent, served over the [AG-UI protocol](https://docs.ag-ui.com) (SSE, `/agent`). Uses OpenRouter (OpenAI-compatible) as the model provider.
- `frontend/` — Next.js app with shadcn/ui (all components installed) and AI Elements (all patterns installed) for the chat UI, driven by `@ag-ui/client`.

## Quick start

Terminal 1 — backend:

```bash
cd backend
cp .env.example .env   # set OPENROUTER_API_KEY
uv sync
uv run uvicorn agent_backend.main:app --reload --port 8000
```

Terminal 2 — frontend:

```bash
cd frontend
cp .env.example .env.local
pnpm install
pnpm dev
```

Open http://localhost:3000.

See `backend/README.md` and `frontend/README.md` for details.

See `docs/chat_development/` for notes on non-obvious decisions and bugs found during development (AG-UI manual wiring, the reasoning render-gap bug, math rendering).
