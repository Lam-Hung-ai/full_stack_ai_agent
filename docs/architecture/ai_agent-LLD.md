# Low-Level Design — `ai_agent`

> Nguồn: `/home/lamhung/code/ai_agent`. Đọc kèm `ai_agent-HLD.md` để có bối cảnh tổng thể.

## 1. Nguyên tắc kiến trúc backend (bắt buộc / "hard boundaries")

Tầng hoá nghiêm ngặt, enforce theo convention (và theo `.claude/rules/*`, `CLAUDE.md`):

```
api/routes/v1/*  →  services/*  →  repositories/*  →  db/models/*
```

- **Route không bao giờ gọi trực tiếp repository hoặc raw SQL.**
- **Repository chỉ `db.flush()` + `db.refresh()`, KHÔNG BAO GIỜ `commit()`.** Việc commit/rollback được quản lý tập trung ở `get_db_session` (`app/db/session.py`, hàm `_managed_session`) bao quanh toàn bộ request.
- Route handler cố tình khai báo kiểu trả về `-> Any` để tránh Pydantic validate 2 lần (FastAPI `response_model` làm việc đó 1 lần).
- Luôn dùng `datetime.now(UTC)`, không dùng `.utcnow()` (deprecated/naive).
- So sánh secret/API-key luôn dùng `secrets.compare_digest()`.
- Schema Pydantic theo convention tách riêng theo entity: `*Create` / `*Update` / `*Read` / `*List`; `*Read` dùng `ConfigDict(from_attributes=True)`.

## 2. Cấu trúc thư mục backend (`backend/app/`)

| Thư mục/File | Vai trò |
|---|---|
| `main.py` | `create_app()` factory + `lifespan()` (khởi động Redis, warm embedding service + reranker, kết nối Qdrant, start Telegram/Slack bot polling). Middleware: `RequestIDMiddleware`, CORS, Sentry (tuỳ chọn), Prometheus instrumentator (bearer-token-gated `/metrics`), `SessionMiddleware`, SQLAdmin (chỉ dev/staging/local). |
| `admin.py` | Cấu hình SQLAdmin, chỉ mount khi `ENVIRONMENT ∈ {development, local, staging}`. |
| `api/router.py`, `api/routes/v1/__init__.py` | Gộp ~25 router con, mount dưới `settings.API_V1_STR = "/api/v1"`. |
| `api/deps.py` | Catalog lớn `Annotated[..., Depends(...)]`: `DBSession`, `Redis`, mọi `*Svc` (UserSvc, ConversationSvc, WebhookSvc, RAGDocumentSvc, KnowledgeBaseSvc, BillingSvc, OrganizationSvc, MemberSvc, InvitationSvc, AdminSvc...), auth deps (`CurrentUser`, `CurrentAdmin`, `CurrentSuperuser`, `CurrentAppAdmin`, `CurrentUserWS`), org-scoping deps (`ActiveOrg` qua header `X-Organization-Id`, `RequireOwner`/`RequireAdminPlus`/`RequireMemberPlus`), `ValidAPIKey` (so sánh constant-time). |
| `core/config.py` | `Settings(BaseSettings)`, env-driven; computed fields (`DATABASE_URL`, `DATABASE_URL_SYNC`, `REDIS_URL`), nested `RAGSettings`; validator từ chối default secret và `CORS_ORIGINS=["*"]` khi `ENVIRONMENT=production`. |
| `core/security.py` | Tạo/verify JWT cho 4 loại token (access, refresh, password_reset, magic_link — mỗi loại có claim `type`; reset/magic-link token tự vô hiệu hoá sau khi dùng nhờ bind vào digest mật khẩu/epoch). Hash bcrypt trực tiếp. |
| `core/exceptions.py`, `exception_handlers.py` | Domain exception (`NotFoundError`, `AlreadyExistsError`, `AuthenticationError`, `AuthorizationError`, `ValidationError`) map tập trung sang HTTP response. |
| `core/middleware.py`, `core/audit.py`, `core/cache.py`, `core/channel_crypto.py`, `core/oauth.py`, `core/sanitize.py` | Middleware, audit log, cache helper, mã hoá Fernet cho bot token, OAuth helper, sanitize input. |
| `db/base.py` | `Base(DeclarativeBase)` + `MetaData` naming convention + `TimestampMixin` (created_at/updated_at). |
| `db/session.py` | Async engine/sessionmaker. `get_db_session` (FastAPI DI, auto commit/rollback), `get_db_context` (manual `async with`, dùng trong WS code), `get_worker_db_context` (NullPool engine riêng cho mỗi Celery task). |
| `db/models/` | 27 model class / 20 file (chi tiết §4). |
| `agents/` | `langgraph_assistant.py` (graph định nghĩa, xem §3), `prompts.py`, `tools/` (`chart_tool.py`, `code_execution.py`, `fetch_url.py`, `rag_tool.py`, `web_search.py`), `utils.py`. |
| `services/rag/` | `config.py`, `documents.py` (DocumentProcessor), `embeddings.py` (EmbeddingService), `ingestion.py` (IngestionService), `retrieval.py` (RetrievalService), `reranker.py`, `vectorstore.py` (`BaseVectorStore`/`QdrantVectorStore`), `image_describer.py`, `connectors/` (google_drive.py, s3.py + `CONNECTOR_REGISTRY`), `sources/`. |
| `services/` (~40 file) | `agent.py`, `agent_session.py`, `agent_invocation.py` (xem §3), `billing/` (Stripe facade: checkout, credits, subscription, webhook handler theo event type), `channels/` (Slack/Telegram adapter + `router.py` + `chart_render.py`), `email/` (provider: resend/smtp/log), `rate_limit/` (rules/service/storage), + 1 service/entity theo pattern Service+Repository. |
| `worker/celery_app.py` | Celery app, `beat_schedule` 6 mục: RAG sync check (60s), trial reminder (hàng ngày 9h), low-credit alert (4h), usage-event cleanup (hàng tuần), anomaly detection (15 phút), usage matview refresh (5 phút). |
| `worker/background/`, `worker/tasks/` | Fallback `BackgroundTasks` cho gửi tin kênh chat; task rag/email/cleanup/anomaly. |
| `commands/` | CLI Click tự động discover: `rag.py`, `seed.py`, `create_app_admin.py`, `sync_stripe_plans.py`, `channel.py`, `cleanup.py`, `example.py`. |
| `alembic/versions/` | 27 migration (users → org tables → audit log → core tables → org_id backfill conversations/RAG → knowledge_bases → billing (plans/prices/subscriptions/stripe_events/credits/usage matview) → onboarding → slash commands → sync-source org scope → demo conversations → webhooks → message thinking → magic-link epoch). |
| `tests/` | pytest: API routes, services, repositories, RBAC/teams, tenant isolation, SSRF, migrations, agent/tools, Stripe seats... |

## 3. Thiết kế LangGraph Agent (`app/agents/langgraph_assistant.py`)

### State & Context
```python
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: RemainingSteps

class AgentContext(TypedDict, total=False):
    user_id: str
    user_name: str
    kb_collection_names: list[str]
    metadata: dict
```
`AgentContext` được truyền qua `config["configurable"]`, **không** nằm trong graph state.

### Tools (`ALL_TOOLS`)
`current_datetime`, `web_search_tool`, `fetch_url_tool`, `search_documents` (RAG), `create_chart_tool`.

### Graph
- 2 node: `"agent"` (`_agent_node` — gọi `ChatOpenAI.ainvoke` với `SystemMessage` + history, có guard giới hạn step qua `remaining_steps`) và `"tools"` (`ToolNode(ALL_TOOLS)`).
- Edge: `START → agent`; conditional `agent → {tools | END}` qua `_should_continue` (kiểm tra `last_message.tool_calls`); `tools → agent` (loop lại).
- Compile: `workflow.compile(checkpointer=self._checkpointer)` với `self._checkpointer = MemorySaver()` — **chỉ lưu trong bộ nhớ process, không bền vững qua restart**. Tính bền vững thực tế đến từ bảng Postgres `Conversation`/`Message` (được replay lại thành LangChain message history mỗi lượt).
- Model: `ChatOpenAI` (tên model từ setting `AI_MODEL`, mặc định `"gpt-5.5"`), hỗ trợ extended-thinking qua OpenAI Responses API (`reasoning={"effort":..., "summary":"auto"}`, `use_responses_api=True`).

### Streaming
`LangGraphAssistant.stream()` gọi `graph.astream(..., stream_mode=["messages","updates"])`:
- `"messages"` — token chunk thô.
- `"updates"` — state diff theo node, là **nguồn sự thật** cho tool-call args/result đầy đủ (vì token chunk chỉ có JSON từng phần).

### 2 điểm gọi agent
1. `agent_invocation.py::AgentInvocationService` — non-streaming (`graph.ainvoke`), dùng cho Slack/Telegram adapter.
2. `agent_session.py::AgentSession` — path WebSocket thời gian thực, consume `assistant.stream()`, forward sự kiện hạt mịn tới browser: `text_delta`, `thinking_delta`, `tool_call`, `tool_result`, `model_request_start`, `final_result`, `message_saved`, `complete`, `error`. Có cả `tool_approval_required`/`ask_user` (HITL) mà frontend hỗ trợ nhưng agent hiện tại **không emit** (khả năng là tàn dư từ biến thể PydanticAI).

### RAG scoping theo tenant
`app.agents.tools.rag_tool._active_kb_collections` là `ContextVar` set theo từng turn từ danh sách collection đã được server resolve + kiểm tra quyền — **không tin** client gửi lên, nhờ vậy tool `search_documents` chỉ search đúng collection được phép.

## 4. Database — Model & Migration

### Danh sách model (`db/models/`, 27 class / 20 file)
- `User` (+ `UserRole`: admin/user)
- `Organization` / `OrganizationMember` / `Invitation` (+ `OrgRole`: owner/admin/member/viewer)
- `Conversation` / `Message` / `ToolCall`
- `ChatFile`
- `ConversationShare`
- `KnowledgeBase` (+ `KBScope`: personal/org/app)
- `RAGDocument`, `SyncSource`, `SyncLog`
- `MessageRating`
- `Webhook` / `WebhookDelivery`
- `ChannelBot` / `ChannelIdentity` / `ChannelSession`
- `Session` (login session)
- `Plan` / `Price`, `Subscription`, `CreditTransaction` / `UsageEvent`, `StripeEvent`
- `AppAdminAuditLog`
- `UserSlashCommand`

### Migration (27 bản, theo thứ tự thời gian)
`users` → `org tables` → `audit log` → `core tables` → `org_id backfill (conversations/RAG)` → `knowledge_bases` → `billing (plans/prices/subscriptions/stripe_events/credits/usage matview)` → `onboarding` → `slash commands` → `sync-source org scope` → `demo conversations` → `webhooks` → `message thinking` → `magic-link epoch`.

## 5. Auth & RBAC

- JWT HS256: access token (30 phút mặc định), refresh token (7 ngày mặc định).
- Login `Session` lưu DB, có thể revoke qua `/sessions`.
- Google OAuth2 (code flow, `api/routes/v1/oauth.py`), magic-link email sign-in, password reset — reset/magic-link token là JWT dùng 1 lần, tự vô hiệu hoá.
- API key tĩnh (header) cho service-to-service.
- WebSocket auth riêng (`get_current_user_ws` trong `api/deps.py`): đọc token từ `Sec-WebSocket-Protocol: access_token.<jwt>` (không dùng query string để tránh lộ qua log/Referer), có cookie fallback.
- RBAC 2 trục: `UserRole` toàn cục (admin/user) + `OrgRole` theo tổ chức (owner/admin/member/viewer), resolve qua header `X-Organization-Id`.

## 6. Danh sách API endpoint chính (`/api/v1`)

| Nhóm | Endpoint tiêu biểu |
|---|---|
| Auth | `login`, `register`, `refresh`, `logout`, `me`, password-reset request/confirm, magic-link request/verify |
| OAuth | `oauth/google/{login,callback}` |
| Users | `users/*`, `/me`, avatar, admin CRUD |
| Sessions | `sessions` (list/revoke/revoke-all) |
| Conversations | CRUD, messages, export, sharing, tool-stats, kb-settings |
| Demos | `demos/*` (public) |
| Webhooks | CRUD, test, regenerate-secret, deliveries |
| Agent | `GET /agent/models`, `WS /ws/agent` (chat socket) |
| RAG | `rag/*` (collections, search, documents, sync sources/connectors), `GET /rag/status/stream` (SSE) |
| Files | `files/upload`, `files/{id}` |
| Admin | `admin/conversations`, `admin/users`, `admin/ratings` (+summary/export), `admin/stats`, `admin/stripe-events` |
| Channels | `channels/bots/*` (Slack/Telegram CRUD, activate/deactivate, webhook register), `telegram/{bot_id}/webhook`, `slack/{bot_id}/events` |
| Organizations | `orgs/*`, `orgs/{id}/members`, invitations |
| Knowledge base | `kb/*` (knowledge bases, documents, sync-sources, connectors, sync logs) |
| Billing | `billing/*` (plans, checkout, portal, subscription, storage, invoices, credits + usage + usage/timeline, Stripe webhook) |
| Khác | `contact`, `me/slash-commands/*`, `org/integrations/*` |

## 7. Kiến trúc Frontend (`frontend/src/`)

### Routing
`app/` (Next.js 15 App Router) → `[locale]/` (next-intl) tách thành route public (home, about, pricing, blog, changelog, community, legal, security, contact) và route group `(dashboard)` (chat, dashboard, admin/*, billing/*, kb/*, orgs/*, profile, settings/*, onboarding). Auth pages `(auth)/` (login, register, forgot/reset password) + `auth/callback`, `auth/magic-link` độc lập.

### BFF layer (`app/api/*`)
Hàng loạt Next.js Route Handler map 1:1 với backend endpoint (auth, admin, billing, conversations, files, kb, me/slash-commands, orgs, sessions, users, v1/rag, v1/agent/models). Dùng `src/lib/server-api.ts::backendFetch` để forward cookie HTTP-only tới FastAPI backend — backend origin/URL **không bao giờ** lộ ra client JS. Ví dụ: `app/api/auth/login/route.ts` gọi backend (OAuth2 form-encoded), lấy `/auth/me`, set cookie HTTP-only qua `setAuthCookies` (`src/lib/auth-cookies.ts`), đồng thời trả `access_token` trong JSON body để dùng in-memory.

### Ngoại lệ: WebSocket chat
`src/hooks/use-websocket.ts` + `use-chat.ts` kết nối **trực tiếp từ browser** tới backend (`NEXT_PUBLIC_WS_URL`), xác thực qua subprotocol `Sec-WebSocket-Protocol: access_token.<jwt>,chat` (access token chỉ giữ trong Zustand `auth-store`, không ở cookie đọc được).

`use-websocket.ts`: reconnect có backoff, phân biệt "chủ động đóng" vs "rớt kết nối", `NO_RETRY_CLOSE_CODES` (1000/1001/1005/1008/4001/4401/4403) tránh retry storm, xử lý React StrictMode double-mount bằng so khớp "socket signature".

`use-chat.ts`: dựng payload gửi đi (`message`, `conversation_id`, tuỳ chọn `model`/`temperature`/`thinking_effort`/`active_knowledge_base_ids`/`file_ids`), xử lý toàn bộ vocabulary sự kiện inbound, queue tin nhắn gõ khi đang bận/offline và drain khi socket rảnh lại.

### State management
Zustand store (`src/stores/`): `auth-store`, `chat-store` (timeline message dạng parts: text/thinking/tool-call, hỗ trợ append delta), `conversation-store`, `chat-sidebar-store`, `kb-selection-store`, `org-store`, `sidebar-store`, `theme-store`, `sources-panel-store`, `file-preview-store`.

TanStack React Query layer trên server-state (list, CRUD) qua hook trong `src/hooks/` gọi `src/lib/api-client.ts::apiClient` — luôn gọi same-origin `/api/*`, tự retry 1 lần khi 401 qua `/api/auth/refresh` (de-duplicated).

### Components tiêu biểu
`src/components/chat/*` (message list/item, markdown renderer, tool-call card + `tool-results/` theo từng tool, chart/map renderer, file preview, slash-command palette, share dialog, HITL dialog), `admin/*`, `billing/*`, `kb/*`, `teams/*`, `onboarding/*`, `marketing/*`, `ui/*` (Radix), `dashboard/*` (recharts).

## 8. Deployment chi tiết

- `make dev` (idempotent): build backend image, `docker-compose.dev.yml` up, poll Postgres, chạy Alembic migration tự động. `make bootstrap` = `make dev` + `make seed`. `make stage` dùng `docker-compose.yml` (prod-like, không bind mount). `make prod` dùng `docker-compose.prod.yml` + `backend/.env` thật.
- Backend `Dockerfile`: multi-stage, `uv sync --frozen`, cài thêm Node.js 20 + `@llamaindex/liteparse` CLI (OCR PDF) vào runtime image, chạy non-root `appuser`, healthcheck `/api/v1/health`, entrypoint `python -m cli.commands server run`.
- `.gitlab-ci.yml`: **lint** (ruff check/format, `ty check`, job riêng) → **test** (pytest + Postgres/Valkey service, coverage cobertura) → **security** (`pip-audit`, allow_failure) → **build** (docker build backend trên default branch; job push registry đang comment sẵn cho sau).
- Secret: `backend/.env` dùng chung dev/prod (gitignored), tham chiếu đầy đủ ở `ENV_VARS.md`. Frontend secret riêng (`frontend/.env.local`); `NEXT_PUBLIC_*` được bake lúc **build** image (không phải runtime) — đặc biệt `NEXT_PUBLIC_WS_URL`, `COOKIE_SECURE`.
- `MANUAL_STEPS.md`: checklist provisioning thủ công 1 lần (OpenAI key, Google OAuth client, Qdrant, Stripe products/webhook, Resend domain, Sentry, LangSmith) + smoke-test sau deploy.

## 9. File tham chiếu nhanh

| Mục đích | File |
|---|---|
| App factory + lifespan | `backend/app/main.py` |
| Router tổng | `backend/app/api/router.py`, `backend/app/api/routes/v1/__init__.py` |
| DI/auth/org-scoping | `backend/app/api/deps.py` |
| LangGraph graph | `backend/app/agents/langgraph_assistant.py` |
| WS orchestration | `backend/app/services/agent_session.py` |
| Non-streaming invoke | `backend/app/services/agent_invocation.py` |
| Settings | `backend/app/core/config.py` |
| JWT scheme | `backend/app/core/security.py` |
| ORM base/session | `backend/app/db/base.py`, `backend/app/db/session.py` |
| Celery app + schedule | `backend/app/worker/celery_app.py` |
| Migrations | `backend/alembic/versions/` |
| Compose/Nginx/CI | `docker-compose*.yml`, `nginx/nginx.conf`, `.gitlab-ci.yml`, `Makefile` |
| i18n routing | `frontend/src/middleware.ts` |
| BFF proxy | `frontend/src/lib/api-client.ts`, `server-api.ts`, `auth-cookies.ts` |
| WS transport + protocol | `frontend/src/hooks/use-websocket.ts`, `use-chat.ts` |
| Client state | `frontend/src/stores/*.ts` |
| Tài liệu gốc dự án | `docs/architecture.md`, `docs/patterns.md`, `docs/permissions.md`, `docs/file-processing.md` (trong repo `ai_agent`) |

## 10. Ghi chú thiết kế đáng chú ý khác

- RAG là tài nguyên **chia sẻ theo tổ chức**, không phải per-user; chỉ admin được quản lý ingestion/sync. 3 chế độ sync: `full`, `new_only`, `update_only`. Pattern connector pluggable (`BaseSyncConnector`, `CONNECTOR_REGISTRY`) cho Google Drive/S3 — là điểm mở rộng chính thức (`docs/howto/add-sync-connector.md`, `docs/howto/add-rag-source.md`).
- `docs/howto/*.md` trong repo là hướng dẫn mở rộng chuẩn: add-api-endpoint, add-agent-tool, customize-agent-prompt, add-background-task, add-rag-source, add-sync-connector, configure-sync-sources, use-ratings.
- Pre-commit hook chạy ruff (format+check); checklist PR yêu cầu `ruff`/`ty`/`tsc --noEmit`/pytest xanh, kèm Alembic migration commit khi đổi schema.
