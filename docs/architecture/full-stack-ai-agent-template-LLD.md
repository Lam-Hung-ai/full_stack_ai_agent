# Low-Level Design — `full-stack-ai-agent-template`

> Nguồn: `/home/lamhung/code/full-stack-ai-agent-template`. Đọc kèm `full-stack-ai-agent-template-HLD.md`.

## 1. Cấu trúc repo mức top-level

```
full-stack-ai-agent-template/
├── fastapi_gen/                 # generator engine (Python package thực thi)
│   ├── cli.py                   # entry point Click, preflight check, 9 preset
│   ├── config.py                # ProjectConfig (Pydantic v2) — nguồn sự thật validate
│   ├── generator.py             # render Cookiecutter + write_manifest()
│   ├── prompts.py                # Questionary wizard tương tác
│   └── upgrade/                  # runner.py — 3-way git merge khi `upgrade`
├── template/
│   ├── cookiecutter.json         # ~209 key cấu hình
│   ├── VARIABLES.md               # tài liệu đầy đủ từng biến
│   ├── hooks/post_gen_project.py  # dọn file theo flag tắt + chạy ruff format
│   └── {{cookiecutter.project_slug}}/   # SKELETON của project sẽ được sinh ra
├── tests/                        # 28 file test, ~10,440 dòng (unit + generate thật)
├── scripts/
│   ├── check_rename_coverage.py  # đảm bảo rename trong template có entry UPGRADES.yaml
│   ├── record_renames.py
│   └── lint_template.py
├── docs/                          # mkdocs site (tài liệu MINH HOẠ, có thể lệch code thật)
├── .github/workflows/             # ci.yml, docs.yml, release.yml, rename-guard.yml, add-to-project.yml
├── UPGRADES.yaml                  # metadata renames/variable_renames/removed/breaking/manual_steps theo version
├── mkdocs.yml
└── pyproject.toml                 # package `fastapi-fullstack`, build=hatchling
```

## 2. Generator internals

| File | Vai trò |
|---|---|
| `fastapi_gen/cli.py` | `main()` — entry Click. `_preflight_check()` (dòng ~39–232): validate ràng buộc chéo giữa flag TRƯỚC Pydantic (vd `--billing` cần `--teams`, `--credits` cần `--billing`, RAG+pgvector cần `database=postgresql`, `--marketing-site`/`--oauth-google` cần `--frontend nextjs`, task queue cần `--redis`). 9 preset `ProjectConfig` dựng sẵn (dòng 853–1112): `production`, `ai-agent`, `production-saas`, `b2b-multi-tenant`, `internal-tool`, `embedded-chatbot`, `blog-saas`, `consumer-app`, `dev-playground`. Có cả subcommand `upgrade` / `upgrade finalize` / `upgrade recover`. |
| `fastapi_gen/config.py` | `ProjectConfig(BaseModel)` — validator Pydantic cho toàn bộ option. |
| `fastapi_gen/prompts.py` | Wizard tương tác bằng Questionary khi không truyền đủ flag CLI. |
| `fastapi_gen/generator.py` | Gọi Cookiecutter render template; `write_manifest()` (dòng ~101) ghi `.fastapi-fullstack.json` vào project output (phiên bản template + toàn bộ option đã chọn) để phục vụ `upgrade` sau này. |
| `fastapi_gen/upgrade/runner.py` | Đọc `.fastapi-fullstack.json` của project cũ + `UPGRADES.yaml`, thực hiện 3-way git merge (tạo branch `template-upgrade/vX`) để kéo thay đổi template mới vào project đã tuỳ biến thủ công. |
| `template/hooks/post_gen_project.py` | Chạy NGAY SAU khi Cookiecutter render xong: xoá các file ứng với flag bị tắt (vd xoá `agents/langgraph_assistant.py` nếu `use_langgraph=false`), rồi chạy Ruff format lên toàn bộ project vừa sinh. |

## 3. Cây thư mục `template/{{cookiecutter.project_slug}}/`

```
{{cookiecutter.project_slug}}/
├── AGENTS.md, CLAUDE.md, CONTRIBUTING.md, SECURITY.md, MANUAL_STEPS.md, ENV_VARS.md
├── .claude/                      # commands/, rules/, skills/, settings.json — toolkit Claude Code,
│                                  #   cũng feature-gated theo cùng cookiecutter flag
├── docker-compose.{dev,yml,prod,frontend}.yml
├── nginx/nginx.conf, nginx/ssl/
├── kubernetes/{namespace,configmap,secret,deployment,service,ingress,kustomization}.yaml
├── Makefile                      # make dev/stage/prod/bootstrap/seed/upgrade/...
├── emails/ (compiled/)           # email template giao dịch
├── docs/                         # docs RIÊNG của project sinh ra (architecture, commands,
│                                  #   configuration, deploy, file-processing, howto/, patterns,
│                                  #   permissions, testing, adding_features) — SÁT với code thật
│                                  #   hơn docs/ cấp root vì được template hoá cùng code
├── backend/
│   ├── alembic.ini, alembic/versions/   # 28 migration (users → orgs → billing → RAG → mcp/magic-link)
│   ├── cli/                      # CLI `uv run <slug> ...` kiểu Django cho project sinh ra
│   ├── scripts/, tests/api/
│   └── app/
│       ├── main.py                # create_app() + lifespan (DI redis/embedding/vector-store/channel)
│       ├── admin.py                # SQLAdmin
│       ├── api/
│       │   ├── router.py, deps.py, exception_handlers.py
│       │   └── routes/v1/          # ~30 module: auth, users, agent(WS), conversations, rag, billing,
│       │                           #   organizations, channels(telegram/slack webhook), admin_*, mcp,
│       │                           #   memory, slash commands, webhooks, oauth, sessions, files,
│       │                           #   invitations, projects, marketing, contact, public_demos
│       ├── core/                   # config.py, security.py, exceptions.py, middleware.py,
│       │                           #   logfire_setup.py, logging.py, oauth.py, crypto.py,
│       │                           #   channel_crypto.py, cache.py, sanitize.py, audit.py
│       ├── db/
│       │   ├── models/             # 25 model (xem §5)
│       │   └── base.py, session.py, memory_pool.py, todo_pool.py, migration_filters.py
│       ├── schemas/                 # Pydantic request/response
│       ├── repositories/            # data-access, 1 repo/model
│       ├── services/                # agent.py, agent_session.py (2951 dòng, rẽ nhánh 5 framework —
│       │                           #   xem §4), agent_invocation.py, conversation.py, billing/(handlers/),
│       │                           #   rag_*, channels/, email/(providers/), rate_limit/, usage.py,
│       │                           #   research.py, webhook.py, mcp_connection.py, sync_source.py
│       ├── agents/                  # assistant.py (Pydantic AI), langchain_assistant.py,
│       │                           #   langgraph_assistant.py, deepagents_assistant.py,
│       │                           #   pydantic_deep_assistant.py, mcp.py/mcp_oauth.py, memory.py,
│       │                           #   prompts.py, utils.py, openai_compatible.py,
│       │                           #   tools/ (ask_user, chart, code_execution, fetch_url, rag_tool,
│       │                           #   research, web_search)
│       └── worker/                  # celery_app.py, taskiq_app.py, arq_app.py, prefect_app.py,
│                                   #   background/{channel,rag}.py, tasks/{email,rag,cleanup,anomaly}.py,
│                                   #   schedules.py
└── frontend/
    ├── next.config.ts, vercel.json, playwright.config.ts, vitest.config.ts
    ├── content/ (MDX blog), demo-export/, public/, messages/ (i18n)
    └── src/
        ├── app/
        │   ├── api/                 # proxy backend: admin, auth, billing, contact, conversations,
        │   │                       #   files, health, invitations, kb, me, orgs, sessions, users, v1
        │   └── [locale]/             # (auth), (dashboard), about, blog, changelog, community,
        │                           #   contact, demo, help, legal, onboarding, pricing, security,
        │                           #   auth/magic-link, shared
        ├── components/              # chat/(+tool-results/), marketing/, legal/, auth/, kb/,
        │                           #   settings/, dashboard/, admin/, billing/, onboarding/, teams/,
        │                           #   rag/, seo/, theme/, states/, icons/, ui/
        ├── hooks/                    # use-chat, use-websocket, use-auth, use-billing,
        │                           #   use-conversations, use-conversation-replay, use-knowledge-bases,
        │                           #   use-mcp-connections, use-memory, use-organizations, use-projects,
        │                           #   use-slash-commands, use-step-replay, ...
        ├── lib/                      # api-client.ts, server-api.ts, rag-api.ts, mcp-*, memory-api.ts,
        │                           #   chat-sources.ts, research-from-tools.ts, query-keys.ts,
        │                           #   auth-cookies.ts
        └── stores/, types/
```

## 4. Thiết kế LangGraph Agent trong template

File: `template/{{cookiecutter.project_slug}}/backend/app/agents/langgraph_assistant.py` (chỉ tồn tại khi `use_langgraph=true`; ngược lại là stub).

- **State**: `AgentState(TypedDict)` = `{messages: Annotated[list[AnyMessage], add_messages], remaining_steps: RemainingSteps}`. `AgentContext(TypedDict, total=False)` mang `user_id`, `user_name`, tuỳ chọn `kb_collection_names` (khi bật teams+RAG), `metadata` — truyền qua `config["configurable"]`.
- **Node**: `agent` (`_agent_node` — gọi chat model đã bind tool, guard trả message "reached step limit" khi `remaining_steps <= 2`) và `tools` (`ToolNode(ALL_TOOLS)`). Conditional edge `_should_continue` → `tools` nếu AIMessage cuối có `tool_calls`, ngược lại → `__end__`.
- **Tools** (thêm có điều kiện vào `ALL_TOOLS`): `current_datetime`, `web_search_tool` (Tavily, nếu `enable_web_search`), `fetch_url_tool` (nếu `web_fetch_tool`), `search_documents` (RAG, nếu `enable_rag`), `create_chart_tool` (nếu `enable_charts`).
- **Chọn model**: rẽ nhánh theo `use_openai`/`use_anthropic`/`use_google`/`use_all_providers`. Hỗ trợ "thinking"/extended-reasoning:
  - Anthropic: `thinking={"type":"enabled","budget_tokens":N}` (low/medium/high → 1024/4096/16384 token, ép `temperature=1.0`).
  - OpenAI: Responses API `reasoning={"effort":..., "summary":"auto"}`.
  - Gemini 2.5+: thinking bật mặc định.
- **Checkpointer**: `MemorySaver()` (in-process, **không bền vững**), key theo `thread_id` trong `config["configurable"]`.
- **Streaming**: `graph.astream(..., stream_mode=["messages","updates"])` — `"messages"` cho token-level `AIMessageChunk` (text + reasoning delta, tích luỹ `usage_metadata` qua `add_usage`); `"updates"` cho state diff theo node — nguồn sự thật cho tool-call name+args đầy đủ và `ToolMessage` result.
- **Tích hợp WebSocket**: route `app/api/routes/v1/agent.py` chỉ làm lifecycle (`/ws/agent`, auth JWT/API key, vòng accept/dispatch/disconnect). Toàn bộ orchestration theo lượt nằm ở `app/services/agent_session.py` — **1 file duy nhất ~2951 dòng** rẽ nhánh Jinja `{%- elif cookiecutter.use_langgraph %}` cho cả 5 AI framework (Pydantic AI/LangChain/LangGraph/DeepAgents/PydanticDeep); nhánh LangGraph nằm ở dòng 1346–1829. Sự kiện WS LangGraph emit: `model_request_start`, `user_prompt`, `text_delta`, `thinking_delta`, `tool_call`, `tool_result`, `final_result`, `message_saved`, `complete`/`error`, `conversation_created`. Hỗ trợ: persist turn (`persist_user_turn`/`persist_assistant_turn` nếu `use_database`), huỷ giữa chừng (frame `stop` → `asyncio.Task.cancel()`), ghi nhận token usage/credit nếu bật billing+teams+credits (`UsageService`).

> **Lưu ý**: `docs/ai-agent.md` và `docs/architecture.md` ở root repo mô tả phiên bản đơn giản hoá (dùng `MessagesState` chung, vòng WS đơn giản) — **không khớp** code thật ở trên. Luôn lấy code Jinja làm ground truth.

## 5. Database models & migrations trong template

ORM: SQLAlchemy 2.0 async (mặc định) hoặc SQLModel (`orm_type`), luôn PostgreSQL khi `use_database=true`.

25 model file trong `backend/app/db/models/`: `user`, `organization`, `conversation` (gồm cả `Message`, `ToolCall` cùng file), `conversation_share`, `knowledge_base`, `rag_document`, `sync_source`, `sync_log`, `plan`, `subscription`, `credit_transaction`, `stripe_event`, `webhook`, `mcp_connection`, `channel_bot`, `channel_identity`, `channel_session`, `message_rating`, `session`, `audit_log`, `item` (ví dụ CRUD), `project` (PydanticDeep), `chat_file`, `user_slash_command`.

Model được điều kiện hoá nặng bằng Jinja (vd `Conversation.organization_id` chỉ tồn tại nếu `enable_teams`; cột JSONB `active_knowledge_base_ids` chỉ khi `enable_teams and enable_rag`; cột `external_user_id` chỉ cho delegated-auth). `Message.thinking: Text|None` lưu reasoning — path Pydantic AI điền được, nhưng path LangGraph **chưa persist thinking** (TODO tại `agent_session.py:1413-1417`). `ToolCall` lưu status/args/result/duration mỗi lần gọi tool.

28 Alembic migration (`backend/alembic/versions/`), theo thứ tự: `0000_create_users` → `0001-0003` orgs/admin-flag → `0004(_5)` core tables/audit log → `0005-0009` org_id backfill + knowledge bases → `0010-0015` billing (seats, plans/prices, subscriptions, stripe events, credits/usage, materialized view `mv_usage_daily`) → `0016-0020` onboarding/slash-commands/external-id → `0021` items (ví dụ CRUD) → `0022-0027` sync-source org scope, demo flag, webhooks, mcp connections, message thinking, magic-link epoch. `UPGRADES.yaml` ghi nhận 1 bug đã fix ở v0.2.21: project không bật `--mcp-client` bị gãy migration sau `0025` (thiếu `0026_create_mcp_connections`).

## 6. Frontend trong template

Next.js 15 App Router (`frontend/src/app/`), route i18n dưới `[locale]/` (route group `(auth)`, `(dashboard)`) cộng route marketing (about, blog, changelog, community, contact, demo, help, legal, onboarding, pricing, security, shared) và flow riêng `auth/magic-link`. Cây `app/api/` song song là Next.js Route Handler proxy sang FastAPI backend (admin, auth, billing, contact, conversations, files, health, invitations, kb, me, orgs, sessions, users, v1) — xử lý session qua cookie HTTP-only ở phía server.

Chat UI (`components/chat/`): `chat-container.tsx`, `chat-input.tsx`, `message-list.tsx`/`message-item.tsx`, `conversation-sidebar.tsx`, `tool-call-card.tsx` + `tool-results/` (1 renderer/tool: ask-user, datetime, fetch-url, generic, memory, rag, run-python, skills, web-search), `research-panel.tsx`/`research-replay-block.tsx`, `subagent-feed.tsx`/`subagent-panel.tsx`, `chart-message.tsx`, `sources-panel.tsx`, `slash-command-palette.tsx`, `share-dialog.tsx`, `rating-buttons.tsx`, `tool-approval-dialog.tsx`.

Streaming client:
- `hooks/use-websocket.ts` — generic reconnecting-WebSocket hook (interval cố định, max attempt, `NO_RETRY_CLOSE_CODES` cho mã 1000/1001/1005/1008/4001/4401/4403, an toàn với StrictMode nhờ so khớp "socket signature").
- `hooks/use-chat.ts` — state machine chat dựa trên hook trên (tích luỹ message từ `text_delta`/`thinking_delta`/`tool_call`/`tool_result`, khớp đúng vocabulary sự kiện backend).
- Hook liên quan khác: `use-conversation-replay.ts`, `use-step-replay.ts` (replay hội thoại demo/shared), `use-knowledge-bases.ts`, `use-mcp-connections.ts`, `use-memory.ts`, `use-slash-commands.ts`.
- Lớp API/data trong `lib/`: `api-client.ts`, `server-api.ts`, `rag-api.ts`, `mcp-connections-api.ts`, `memory-api.ts`, `slash-commands-api.ts`, `query-keys.ts` (TanStack Query key factory), `chat-sources.ts`, `research-from-tools.ts` (suy ra state research-panel từ raw tool-call stream), `conversation-to-chat.ts`.

State: Zustand store (`stores/`) + TanStack Query cho server state. Stack xác nhận tại `docs/frontend.md:1-16`: Next.js 15, React 19, TypeScript 5, Tailwind 4, Zustand 5, TanStack Query 5, Bun.

## 7. CI/CD chi tiết của generator

`.github/workflows/ci.yml` — pipeline: `lint` (ruff check+format) → `type-check` → `test` (pytest) → `security` → **~24 job `generate-*`** chạy generator thật với tổ hợp option và validate output:

`generate-minimal`, `generate-postgresql`, `generate-pg-billing`, `generate-pg-billing-credits`, `generate-pg-langchain`, `generate-pg-langgraph`, `generate-pg-deep-research`, `generate-pg-taskiq`, `generate-pg-deepagents`, `generate-pg-pydantic-deep`, `generate-pg-agent-tools`, `generate-pg-channels`, `generate-pg-rag-pgvector`, `generate-pg-rag-connectors`, `generate-pg-email-oauth`, `generate-pg-delegated-auth-jwks`, `generate-pg-delegated-auth-shared-secret`, `generate-pg-rate-limiting`, `generate-pg-rag-reranker`, `generate-pg-mcp-client`, `generate-pg-memory`, `generate-pg-monitoring`, `generate-pg-usage-chain`, `generate-marketing`, `generate-frontend`, `generate-frontend-billing`.

Đây là bộ test hồi quy thật sự của generator — không chỉ unit test logic config mà render project thật vào `tmp_path` rồi lint/type-check/build (khớp với `tests/test_template_integration.py`, `tests/test_rag_integration.py`, `tests/test_generator.py`).

Workflow khác:
- `docs.yml` — `mkdocs gh-deploy --force --no-history` khi push `main`.
- `release.yml` — khi GitHub release published: `uv build` + publish PyPI.
- `rename-guard.yml` — chặn PR rename/move file trong `template/` thiếu entry `UPGRADES.yaml` (qua `scripts/check_rename_coverage.py`).
- `add-to-project.yml` — ops, add issue/PR vào project board.

`UPGRADES.yaml` là metadata cấu trúc (mỗi version: `renames`, `variable_renames`, `removed`, `breaking`, `manual_steps`) được `fastapi-fullstack upgrade` tiêu thụ để merge 3-way vào branch `template-upgrade/vX`.

## 8. Cấu trúc `docs/` (2 cây tài liệu riêng biệt — dễ nhầm lẫn)

1. **`docs/` ở root repo** (nguồn mkdocs, nav tại `mkdocs.yml:141-160`): `index.md`, `installation.md`, `gallery.md`, `getting-help.md`, `concepts/index.md`, `architecture.md`, `ai-agent.md`, `rag.md`, `frontend.md`, `guides/{index,quick-start,configuration,version-upgrade}.md`, `deployment.md`, `observability.md`, `development.md`, `CHANGELOG.md`. → Tài liệu mang tính **khái niệm/marketing**, có code sample **đơn giản hoá, có thể lệch** code Jinja thật (đã xác nhận với LangGraph ở §4).
2. **`template/{{cookiecutter.project_slug}}/docs/`** (`adding_features`, `architecture`, `commands`, `configuration`, `deploy`, `file-processing`, `patterns`, `permissions`, `testing`, `howto/`) — đây là docs **ship kèm mỗi project sinh ra** (nên cũng có trong `ai_agent/docs/` nếu chưa bị xoá), **sát với code thật hơn** vì được template hoá cùng lúc với code.

## 9. Quy ước từ CLAUDE.md / AGENTS.md / CONTRIBUTING.md

- Yêu cầu DCO: mọi commit phải `git commit -s`.
- Vòng lặp dev chuẩn: `uv sync` → `uv run pytest` / `uv run ruff check . --fix` / `uv run ruff format .` / `uv run ty check` (type checker là `ty`, không phải mypy).
- Pattern Repository+Service là quy tắc kiến trúc bắt buộc cho backend sinh ra: "route không được gọi DB trực tiếp".
- Thêm 1 CLI option mới cần checklist 6 bước (`AGENTS.md:69-75`): `config.py` → `prompts.py` → `cookiecutter.json` → Jinja conditional → `post_gen_project.py` cleanup → `VARIABLES.md`.
- Thêm vector store / sync connector mới cũng có checklist từng bước (`AGENTS.md:77-89`).
- Project sinh ra tự mang theo bộ `.claude/` (skills, commands, rules) cũng được feature-gate theo cùng flag cookiecutter — `ai_agent/.claude/` phản ánh đúng các option đã chọn lúc sinh.
- Ruff config loại trừ `template/` khỏi lint/`ty` (vì đó là file Jinja, không phải Python hợp lệ); test loại trừ thư mục `ai_agent_test/` tương tự — tên này gợi ý mạnh rằng chính repo đã tự generate/validate 1 project tên `ai_agent_test` làm bằng chứng cho quan hệ sinh ra `ai_agent`.

## 10. File tham chiếu nhanh

| Mục đích | File |
|---|---|
| Biến cookiecutter | `template/cookiecutter.json`, `template/VARIABLES.md` |
| Lõi generator | `fastapi_gen/{cli.py,config.py,generator.py,prompts.py}` |
| Upgrade tooling | `fastapi_gen/upgrade/`, `UPGRADES.yaml` |
| App factory (template) | `template/{{cookiecutter.project_slug}}/backend/app/main.py` |
| LangGraph agent (template) | `template/{{cookiecutter.project_slug}}/backend/app/agents/langgraph_assistant.py` |
| WS route + session orchestrator | `template/{{cookiecutter.project_slug}}/backend/app/api/routes/v1/agent.py`, `.../backend/app/services/agent_session.py` |
| DB models (template) | `template/{{cookiecutter.project_slug}}/backend/app/db/models/` |
| Migrations (template) | `template/{{cookiecutter.project_slug}}/backend/alembic/versions/` |
| Frontend chat hooks (template) | `template/{{cookiecutter.project_slug}}/frontend/src/hooks/use-websocket.ts`, `use-chat.ts` |
| CI matrix | `.github/workflows/ci.yml` |
