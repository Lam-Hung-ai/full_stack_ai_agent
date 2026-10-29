# agent-backend

FastAPI + LangGraph backend for the chat agent. The agent (`langchain.agents.create_agent`, OpenRouter model through `langchain-openrouter`) is exposed over the [AG-UI protocol](https://docs.ag-ui.com) as Server-Sent Events. Design, decisions and sprint plan: [`docs/chat_development`](../docs/chat_development/README.md). Coding rules: [`AGENTS.md`](AGENTS.md).

## Setup

Requires `uv`, Docker (or a PostgreSQL 18 you can create databases on) and [`dbmate`](https://github.com/amacneil/dbmate). Tests also need `initdb`, `pg_ctl` and `pg_dump` on `PATH`.

```bash
cp .env.example .env            # set OPENROUTER_API_KEY
uv sync
docker compose up -d postgres   # from the repository root; PostgreSQL 18 on 5433

# From the repository root: apply migrations, then let the LangGraph saver
# create its tables in schema langgraph_checkpoints.
dbmate --env-file backend/.env -e DBMATE_DATABASE_URL --no-dump-schema up
uv run --directory backend db checkpoints
```

## Run

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- `GET /health` — liveness.
- `POST /agent` — legacy AG-UI endpoint taking a raw `RunAgentInput`; the conversation API under `/api/v1` replaces it in sprint S2.

`OPENROUTER_REASONING_EFFORT` turns on model reasoning when the model supports it (empty turns it off); it is streamed as `REASONING_*` events.

## Structure

```text
src/app/
├── main.py                 app, middleware, routers
├── config/settings.py      environment (pydantic-settings)
├── database/
│   ├── session.py          async engine (psycopg 3), search_path chat_app
│   └── generated_tables.py generated, never edited
├── common/                 errors, request id, logging
├── modules/agent/          LangGraph graph, AG-UI wrapper, legacy /agent route
└── tools/database.py       `uv run db export | generate | checkpoints`
```

## Database workflow

Migrations are plain SQL in `../db/migrations`, run by dbmate (see AGENTS.md section 29). After a schema change, regenerate both generated files **from a freshly migrated database**:

```bash
uv run db export --clean   # ../db/schema/schema.sql
uv run db generate         # src/app/database/generated_tables.py
```

## Checks

```bash
uv run ruff check src tests
uv run ruff format --check src tests
uv run pyrefly check
uv run pytest
```

Tests start a disposable PostgreSQL cluster and load `db/schema/schema.sql`; `tests/integration/test_migrations.py` replays every migration and fails if that file drifts.
