# Low-Level Design — `fastapi-langgraph-agent-production-ready-template`

> Nguồn: `/home/lamhung/code/fastapi-langgraph-agent-production-ready-template`. Đọc kèm file HLD cùng tên.

## 1. Cấu trúc thư mục (`app/`)

```
app/
  main.py                      FastAPI app factory + lifespan + root/health endpoints
  api/v1/api.py                Router tổng (mount auth + chatbot dưới /api/v1)
  api/v1/auth.py               Register/login/session CRUD, get_current_user/get_current_session deps
  api/v1/chatbot.py             /chat, /chat/stream, /messages GET+DELETE
  core/config.py                Settings (TỰ VIẾT TAY bằng os.getenv — KHÔNG phải pydantic-settings
                                 dù AGENTS.md/README nói vậy — xem §8 phần "khác biệt doc vs code")
  core/langgraph/graph.py       LangGraphAgent: build graph, checkpointer, node chat/tool_call, streaming
  core/langgraph/tools/         ask_human.py (HITL qua interrupt), duckduckgo_search.py
  core/prompts/                 system.md, session_title.md, memory_capture.md + loader (cache lúc import)
  core/cache.py                  InMemoryCacheService / ValkeyCacheService + cache_key()
  core/limiter.py                 slowapi Limiter, backend Valkey nếu có cấu hình
  core/logging.py                 structlog setup (JSONL file handler + console/JSON renderer), bind/clear/get context
  core/metrics.py                 Prometheus Counter/Histogram/Gauge + setup_metrics()
  core/middleware.py               MetricsMiddleware, LoggingContextMiddleware, ProfilingMiddleware
  core/observability.py            Khởi tạo Langfuse + CallbackHandler singleton
  models/{base,user,session,thread}.py   Bảng SQLModel
  schemas/{auth,chat,base,graph}.py       Pydantic request/response + GraphState
  services/llm/{registry,service}.py      LLMRegistry (danh sách model), LLMService (retry/fallback/structured output)
  services/memory.py              mem0 AsyncMemory + cache wrapper
  services/database.py            CRUD SQLModel đồng bộ (User/Session), pool kết nối, health_check
  services/session_naming.py      Claim nguyên tử qua Postgres để tự đặt tên session nền
  utils/{auth,graph,sanitization,tasks}.py   JWT helper, chuẩn bị/trim message (tiktoken), sanitize input, tracker background task
alembic/                        env.py (load settings, loại trừ bảng do bên ngoài quản lý), versions/ (1 migration)
evals/                           main.py (CLI), evaluator.py (fetch Langfuse + judge OpenAI + push score), schemas.py, helpers.py, metrics/ (5 prompt judge .md)
grafana/dashboards/              dashboards.yml (provisioning) + json/llm_latency.json (CHỈ 1 dashboard tồn tại thật)
prometheus/prometheus.yml        Cấu hình scrape: fastapi (app:8000/metrics), cadvisor
scripts/                         docker-entrypoint.sh, build-docker.sh, set_env.sh
```

## 2. Luồng request chi tiết (chat)

```
POST /api/v1/chatbot/chat (app/api/v1/chatbot.py:35)
  → get_current_session (app/api/v1/auth.py:105 — verify JWT + lookup DB session + bind context log)
  → maybe_name_session() (fire-and-forget nếu session chưa được đặt tên)
  → agent.get_response() (app/core/langgraph/graph.py:268)
      → asyncio.gather(graph.aget_state(), memory_service.search())
      → graph.ainvoke(..., thread_id=session_id) — checkpoint qua Postgres
          → node "chat": llm_service.call() (retry+fallback)
          → nếu AIMessage có tool_calls → node "tool_call" (asyncio.gather chạy song song) → quay lại "chat"
          → END
      → background task: memory_service.add()
  → serialize ChatResponse
```

Thứ tự middleware bao quanh mỗi request: `LoggingContextMiddleware` (bind session/user vào context structlog) → `MetricsMiddleware` (counter/histogram Prometheus tự viết) → `ProfilingMiddleware` (chỉ chạy khi DEBUG, dùng pyinstrument) → `CorrelationIdMiddleware` (set `X-Request-ID`, đăng ký sau cùng trong `main.py` nên theo thứ tự reverse-registration của Starlette thì nó bao ngoài cùng) → `PrometheusMiddleware` (từ `starlette_prometheus`, cài qua `setup_metrics`) → CORS.

## 3. Thiết kế LangGraph (`app/core/langgraph/graph.py`)

### State schema (`app/schemas/graph.py`)
```python
class GraphState(BaseModel):
    messages: Annotated[list, add_messages]
    long_term_memory: str
```

### Topology
2 node, dùng **`Command(update=..., goto=...)`** (command-routing style của LangGraph, không phải conditional edge truyền thống):

- **`chat`** — entry point VÀ finish point, đích đến `("tool_call", END)`.
- **`tool_call`** — đích đến `("chat",)`, có `RetryPolicy(max_attempts=3)`.

### Node `_chat` (graph.py:130)
- Load system prompt qua `load_system_prompt(username, long_term_memory=state.long_term_memory)`.
- Trim/chuẩn bị message (trim dựa trên `tiktoken`, trong `app/utils/graph.py`).
- Gọi `llm_service.call()`, đo thời gian bằng metric `llm_inference_duration_seconds`.
- Chuẩn hoá content block có cấu trúc (`process_llm_response`).
- Route sang `tool_call` nếu `AIMessage.tool_calls` tồn tại, ngược lại `END`.

### Node `_tool_call` (graph.py:187)
Thực thi toàn bộ tool call **đồng thời** bằng `asyncio.gather` khi có >1 tool call, bọc kết quả thành `ToolMessage`, route về lại `chat`.

### Tools
- `duckduckgo_search_tool` (`DuckDuckGoSearchResults`, `num_results=10`).
- `ask_human` — một `@tool` gọi `langgraph.types.interrupt(question)` — human-in-the-loop pause/resume **thật sự**.

### Checkpointer
`AsyncPostgresSaver(connection_pool)` trên `psycopg_pool.AsyncConnectionPool` (dựng từ setting `POSTGRES_*`, `autocommit=True`, `row_factory=dict_row`, `prepare_threshold=None`). Gọi `checkpointer.setup()` 1 lần; graph compile với `checkpointer=checkpointer`. Đây là **persistence duy nhất** cho conversation state — comment code nói rõ: tạo pool thất bại thì phải raise, không được âm thầm chạy mà thiếu checkpointer (graph.py:124-127).

Bảng checkpoint: `checkpoints`, `checkpoint_blobs`, `checkpoint_writes` (`settings.CHECKPOINT_TABLES`, config.py:194) — xoá qua pipelined multi-table `DELETE ... WHERE thread_id = %s` khi gọi `DELETE /messages` (`clear_chat_history`, graph.py:437).

### Interrupt / Resume
```
graph.aget_state(config)
  → nếu state.next khác rỗng (graph đang pause giữa chừng do interrupt)
    → lần gọi tiếp theo: graph.ainvoke(Command(resume=messages[-1].content), config)
      thay vì gọi với messages input mới
  → bắt riêng exception GraphInterrupt
```

### Streaming
`get_stream_response` dùng `graph.astream(graph_input, config, stream_mode="messages")`, lọc còn `AIMessage/AIMessageChunk`, trích text qua `extract_text_content` (xử lý được cả format content-block kiểu GPT-5 Responses API với block `reasoning`/`text`), yield từng đoạn text; expose ở router chatbot dưới dạng SSE (`data: {...}\n\n`).

### Pre-warming
`app/main.py` lifespan gọi `agent.create_graph()` và `memory_service.initialize()` lúc startup để tránh cold-start ở request đầu tiên (pool kết nối + kiểm tra schema pgvector).

### Mở rộng multi-agent (chỉ ghi trong README, CHƯA implement)
Compile sub-graph không có checkpointer riêng (kế thừa checkpointer của parent), thêm làm node, dùng `Command(goto="research_agent")` từ node `chat` đóng vai supervisor.

## 4. LLM Service (`app/services/llm/registry.py`, `service.py`)

- `LLMRegistry.LLM_CONFIGS` — danh sách có thứ tự (index 0 = model mặc định + đầu chuỗi fallback), mỗi entry dựng qua `init_chat_model` của LangChain (nên chuỗi `provider:model` cho phép thêm provider bất kỳ); entry dạng OpenAI tự động được tiêm `api_key`.
- `LLMService.call()`: bọc `_call_with_fallback` trong `asyncio.wait_for(timeout=settings.LLM_TOTAL_TIMEOUT)` (mặc định 60s). `_invoke_with_retry` dùng `@retry` của tenacity (`stop_after_attempt(MAX_LLM_CALL_RETRIES=3)`, `wait_exponential(min=2,max=10)`, chỉ retry khi gặp `RateLimitError/APITimeoutError/APIError` của OpenAI). Khi hết retry, `_switch_to_next_model` xoay vòng tròn qua `LLMRegistry.LLMS`, bind lại tool để model mặc định của agent giữ nguyên tool khi đổi model.
- 2 đường gọi: **"default"** (mutate `self._llm`, dùng cho vòng lặp agent chính) vs **"one-off"** (override model_name/response_format/kwargs — dựng Runnable cục bộ mới, dùng ví dụ cho sinh tiêu đề session, không đụng tới state dùng chung). Hỗ trợ `response_format: Type[BaseModel]` → chain `.with_structured_output()`.

## 5. Database Schema (SQLModel, `app/models/`)

| Bảng | Cột chính | Ghi chú |
|---|---|---|
| `User` | `id PK`, `email unique+index`, `hashed_password`, `username` (tuỳ chọn), `created_at` | có method bcrypt verify/hash (static/instance) |
| `Session` | `id PK (UUID str)`, `user_id FK→user.id`, `name` (mặc định ""), `username` (copy denormalize từ User lúc tạo, tránh join mỗi request chat), `created_at` | quan hệ tới `User` |
| `Thread` | `id PK`, `created_at` | docs mô tả là "mirror LangGraph checkpoint thread" nhưng **không có code service nào dùng nó** (không CRUD trong `app/services`) — khả năng là vestigial/chuẩn bị cho tương lai |

Bảng do hệ thống ngoài quản lý, **loại trừ khỏi Alembic** (qua `include_object` trong `alembic/env.py:37-51`): `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`, `checkpoints` (LangGraph), `longterm_memory`, `mem0migrations` (mem0/pgvector).

1 migration duy nhất: `alembic/versions/b25d38b0cd7c_initial_schema.py` — tạo `user`, `session`, `thread` đúng như model trên.

## 6. Auth

2 scope JWT dùng chung cơ chế claim `sub` (`app/utils/auth.py`):
- **User token** (`sub=user.id`) — chỉ dùng để tạo/liệt kê session.
- **Session token** (`sub=session_id`) — bắt buộc cho mọi endpoint chat.

Cả hai: HS256, có claim `jti` (uniqueness), `JWT_ACCESS_TOKEN_EXPIRE_DAYS` (mặc định 30). `get_current_user`/`get_current_session` (`app/api/v1/auth.py:54,105`) là FastAPI dependency dùng `HTTPBearer`, decode qua `verify_token`, lookup lại user/session trong Postgres (nên xoá record sẽ vô hiệu hoá JWT dù chưa hết hạn), bind `user_id` vào context structlog.

`Settings.validate_jwt_secret_key()` (config.py:272) chặn cứng khởi động app (ngoài môi trường TEST) nếu `JWT_SECRET_KEY` < 32 ký tự hoặc trùng danh sách placeholder đã biết.

## 7. API Endpoints

| Method/Path | Rate limit | Mô tả |
|---|---|---|
| `POST /api/v1/auth/register` | 10/giờ | bcrypt-hash password, trả `UserResponse{id,email,username,token}` |
| `POST /api/v1/auth/login` | 20/phút | OAuth2 password-grant form, trả `TokenResponse` |
| `POST /api/v1/auth/session` | — | cần user token, tạo `Session` (copy `username`), trả `SessionResponse{session_id,name,token}` |
| `PATCH /api/v1/auth/session/{id}/name` | — | đổi tên session |
| `DELETE /api/v1/auth/session/{id}` | — | xoá session |
| `GET /api/v1/auth/sessions` | — | liệt kê session |
| `POST /api/v1/chatbot/chat` | 30/phút | chat đồng bộ |
| `POST /api/v1/chatbot/chat/stream` | 20/phút | chat streaming (SSE) |
| `GET /api/v1/chatbot/messages` | 50/phút | lấy lịch sử tin nhắn |
| `DELETE /api/v1/chatbot/messages` | 50/phút | xoá lịch sử (và checkpoint) |
| `GET /health` | — | check DB, trả 503 nếu unhealthy (top-level) |
| `GET /api/v1/health` | — | health check đơn giản hơn, cấp router |
| `GET /metrics` | — | Prometheus exposition |
| `GET /` | — | thông tin root |

## 8. Config / Logging

### Config (`app/core/config.py`)
**Tự viết tay** (không dùng `pydantic-settings` dù AGENTS.md/README nói vậy — đây là 1 điểm lệch doc/code đáng chú ý) — đọc env var qua `os.getenv` với ép kiểu thủ công, hỗ trợ resolve file cascading `.env.{environment}[.local]` (`load_env_file()`), bảng override theo môi trường trong `apply_environment_settings()` (DEBUG/LOG_LEVEL/LOG_FORMAT/RATE_LIMIT_DEFAULT khác nhau giữa development/staging/production/test, chỉ áp dụng nếu biến env chưa được set tường minh).

### Logging (`app/core/logging.py`)
structlog, cấu hình 1 lần lúc import qua `setup_logging()`. Output kép: `JsonlFileHandler` ghi file JSONL theo ngày vào `LOG_DIR` (`logs/{env}-{date}.jsonl`) **và** `StreamHandler` console; renderer chọn theo `LOG_FORMAT` (console = `ConsoleRenderer`, khác thì `JSONRenderer`). `ContextVar`-based `bind_context`/`clear_context`/`get_context` tiêm `request_id`/`session_id`/`user_id` vào mọi dòng log; `LoggingContextMiddleware` clear context mỗi request và decode JWT 1 cách "defensive" (bỏ qua `JWTError`) chỉ để bind `session_id` sớm cho log, trước cả khi dependency auth đầy đủ chạy.

## 9. Observability chi tiết

### Langfuse (`app/core/observability.py`)
Khởi tạo 1 lần lúc import (`langfuse_init()` tại `main.py:38`) với `auth_check()` chỉ log, không fail app. 1 instance `CallbackHandler` duy nhất (`langfuse_callback_handler`) truyền vào `callbacks` của mọi lần gọi `ainvoke`/`astream` của graph, có điều kiện `settings.LANGFUSE_TRACING_ENABLED`. Bắt input/output, token/cost, latency, model/params từng lần gọi.

### Prometheus metrics (`app/core/metrics.py`)

| Metric | Loại | Trạng thái dùng |
|---|---|---|
| `http_requests_total{method,endpoint,status}` | Counter | đang dùng |
| `http_request_duration_seconds{method,endpoint}` | Histogram | đang dùng |
| `db_connections` | Gauge | **định nghĩa nhưng không thấy code `.set()`** — có vẻ chưa dùng/aspirational |
| `orders_processed_total` | Counter | **vestigial** — không được tham chiếu ở đâu khác trong `app/`, khả năng sót lại từ template gốc khác (vd demo đặt hàng) |
| `llm_inference_duration_seconds{model}` | Histogram (bucket 0.1–5.0s) | dùng trong node `_chat` |
| `llm_stream_duration_seconds{model}` | Histogram (bucket 0.1–10.0s) | dùng trong endpoint stream của `chatbot.py` |
| `session_names_generated_total{status}` | Counter | dùng trong `session_naming.py` |

Hai middleware metric chồng nhau: `MetricsMiddleware` tự viết + `starlette_prometheus.PrometheusMiddleware` (cài qua `setup_metrics`), expose ở `GET /metrics` qua `starlette_prometheus.metrics`.

### Grafana
**Chỉ 1 dashboard thực sự tồn tại**: `grafana/dashboards/json/llm_latency.json` ("LLM Inference Latency", 4 panel: p95 chat duration, p95 stream duration, average chat duration, request-count rate — dựa trên `llm_inference_duration_seconds*`/`llm_stream_duration_seconds*`). `docs/docker.md` claim thêm các dashboard ("API performance", "Rate limiting statistics", "Database connection pool health", "System resource usage") **không tồn tại dưới dạng file** — khoảng cách doc vs thực tế cần lưu ý. Dashboard auto-provision qua `grafana/dashboards/dashboards.yml` (file provider, path `/etc/grafana/provisioning/dashboards/json`).

### cAdvisor
Prometheus scrape job `cadvisor` → `cadvisor:8080` lấy metric container-level CPU/mem/disk/net; **chưa có dashboard Grafana riêng** cho cAdvisor (cần import dashboard cAdvisor generic của Grafana nếu muốn).

### Profiling (`ProfilingMiddleware`, `app/core/middleware.py:136`)
Chỉ chạy khi DEBUG, dùng `pyinstrument` + `tracemalloc` + `time.process_time()` cùng lúc; request vượt `PROFILING_THRESHOLD_SECONDS` sẽ ghi báo cáo JSON (`{request_id}.json`) vào `PROFILING_DIR` gồm wall/cpu/io-wait time, memory peak, top 20 memory allocator, full call tree.

## 10. Evaluation Harness (`evals/`)

Harness tự viết, **không** dùng LangSmith/promptfoo/deepeval/ragas — hệ thống LLM-judge build trực tiếp trên trace Langfuse:

- `evals/evaluator.py::Evaluator`:
  - `__fetch_traces()` — kéo trace Langfuse 24h gần nhất qua `langfuse.api.trace.list(...)`, lọc còn trace chưa có score.
  - Với mỗi trace × mỗi metric: trích input/output message string (`evals/helpers.py: get_input_output`/`format_messages` — xử lý riêng message dạng tool-call), gọi `_call_openai()` dùng `openai.AsyncOpenAI.beta.chat.completions.parse(model=EVALUATION_LLM, response_format=ScoreSchema)` (structured output, 3 lần retry, sleep 10s) để nhận `ScoreSchema{score: float 0-1, reasoning: str}`.
  - Score thành công được push ngược vào Langfuse qua `langfuse.create_score(trace_id, name=metric, data_type="NUMERIC", value, comment=reasoning)`.
  - `EVALUATION_SLEEP_TIME` cố định (mặc định 10s) giữa các trace (tránh rate-limit đơn giản).
  - Tổng hợp thành report dict, ghi JSON vào `evals/reports/evaluation_report_{timestamp}.json` (`evals/helpers.py: generate_report`).
- **Metric là file markdown system prompt**, tự động discover từ `evals/metrics/prompts/*.md` (`evals/metrics/__init__.py` chỉ glob file `.md`, dùng tên file (bỏ đuôi) làm tên metric) — 5 metric có sẵn: `helpfulness.md`, `conciseness.md`, `hallucination.md`, `relevancy.md`, `toxicity.md`. **Thêm metric mới = thêm 1 file markdown, không cần sửa code.**
- `evals/schemas.py`: `ScoreSchema(score: float, reasoning: str)`.
- `evals/main.py`: CLI argparse với `--interactive` (prompt màu bằng `colorama`), `--quick` (dùng toàn bộ default), `--no-report`; expose qua Make target `make eval` / `make eval-quick` / `make eval-no-report`. **Không được wire vào CI** — đây là ops tool thủ công/định kỳ, không phải cổng chặn test.
- Model judge cấu hình riêng (`EVALUATION_LLM` mặc định `gpt-5`, `EVALUATION_BASE_URL`, `EVALUATION_API_KEY` mặc định lấy `OPENAI_API_KEY`) để việc chấm điểm có thể dùng model khác/rẻ hơn agent chính.

## 11. Deployment / Infra chi tiết

- **Dockerfile**: 1 stage `python:3.13.2-slim`, cài `build-essential`/`libpq-dev`, `uv sync --frozen` chạy 2 lần (layer deps-only cache riêng, sau đó full project) để tận dụng Docker layer cache, tạo non-root user `appuser`, `ENTRYPOINT scripts/docker-entrypoint.sh` (validate `JWT_SECRET_KEY`/`OPENAI_API_KEY` tồn tại, load `.env.${APP_ENV}` tôn trọng biến env đã set sẵn) rồi `exec uvicorn app.main:app`.
- **Makefile**: mọi target đều nhận `ENV=development|staging|production|test`, bọc `uv run`, Alembic, Docker Compose, eval CLI, ruff/pyright, pre-commit. `scripts/set_env.sh` là bộ load env cho chạy bare-metal (không Docker), có validate JWT secret trùng logic với Python config (duplicate logic).
- **CI** (`.github/workflows/ci.yaml`): 1 job `checks` (PR + push `master`) — `uv sync --all-extras --all-groups` → `ruff check` → `ruff format --check` → `pyright`. **Không chạy test** dù `pytest`/`httpx` có khai báo ở dependency group `test` — thực tế không tồn tại thư mục `tests/` nào trong repo.
- **Deploy** (`.github/workflows/deploy.yaml`): build image production (`make docker-build ENV=production`) rồi push Docker Hub khi push `master` (điều kiện secret `DOCKER_USERNAME` tồn tại).
- **Env var đáng chú ý**: `JWT_SECRET_KEY` (validate ≥32 ký tự, từ chối placeholder — cả Python `config.py` lẫn bash `set_env.sh` đều validate, bị duplicate logic), `OPENAI_API_KEY`, `DEFAULT_LLM_MODEL`, `LANGFUSE_*` (bật/tắt tracing), `POSTGRES_*` (host khác nhau giữa container `db` và bare-metal `localhost` — gotcha đã ghi trong docs), `VALKEY_HOST` (chỉ cần tồn tại là bật cache/rate-limit phân tán thay vì fallback in-memory), `RATE_LIMIT_*` theo endpoint, `PROFILING_*` (chỉ chạy khi DEBUG), `SESSION_NAMING_ENABLED`.

## 12. Quy ước / Nguyên tắc thiết kế đáng chú ý

Từ AGENTS.md ("10 Commandments", dòng 181-194) + code:
- Rate limiting trên mọi route; Langfuse tracing trên mọi thao tác LLM; tenacity cho mọi retry.
- structlog: tên event dạng `lowercase_with_underscores`, không f-string (chỉ dùng kwargs); dùng `logger.exception()` thay vì `.error()` trong khối `except`.
- rich cho console output; chỉ cache response thành công, không cache lỗi.
- Import luôn ở đầu file; toàn bộ thao tác DB phải async (dù `DatabaseService` thực chất là sync/SQLModel `Session`-based bọc trong `async def` — **vi phạm một phần** nguyên tắc này, đáng lưu ý).
- Full type hint + Pydantic model khắp nơi; `make typecheck` (pyright standard mode) phải pass.
- Pattern RORO (Receive an Object, Return an Object), phong cách functional/declarative, tránh class trừ service/agent, early-return guard clause, happy path để cuối.

### Bảo mật
bcrypt hash password, JWT có `jti` để đảm bảo uniqueness, sanitize input qua `app/utils/sanitization.py` (HTML-escape, strip null-byte, validate email/password-strength bằng regex) áp dụng ở biên router auth, pre-commit hook `detect-secrets` với `.secrets.baseline`, CORS giới hạn qua `ALLOWED_ORIGINS`, hướng dẫn rõ ràng "rotate toàn bộ secret trước khi lên prod" và "đặt `DEBUG=false`".

### Fail-loud thay vì fail-silent cho hạ tầng quan trọng
Tạo pool cho checkpointer thất bại → raise (lựa chọn kiến trúc tường minh trong comment code); validate JWT secret raise `RuntimeError` ngay lúc dựng `Settings` (ngoài môi trường test).

### Concurrency-first cho hiệu năng
`asyncio.gather` cho (kiểm tra state + tìm memory) và cho tool call song song; pattern claim nguyên tử qua Postgres `UPDATE ... WHERE name=''` để dedupe việc sinh tiêu đề session giữa các worker đồng thời mà không cần distributed lock; background task `asyncio.create_task` (theo dõi trong 1 `set` cấp module để tránh bị GC khi đang chạy dở — `app/utils/tasks.py`) cho ghi memory và lưu tiêu đề session, giúp luồng response chính không phải chờ.

### LLM provider-agnostic
Toàn bộ dựng qua `init_chat_model` của LangChain, nên đổi provider chỉ là đổi 1 entry trong registry (`"name": ..., "model": "anthropic:claude-opus-4-6", "kwargs": {...}}`) không cần sửa code graph — nhưng retry theo loại exception hiện chỉ đặc thù cho OpenAI trừ khi mở rộng thêm (giới hạn đã ghi trong `docs/llm-service.md`).

## 13. Khác biệt đáng chú ý giữa tài liệu và code thực tế

| Tài liệu nói | Code thực tế | Ghi chú |
|---|---|---|
| AGENTS.md/README: config dùng "Pydantic Settings" | `app/core/config.py` là class tự viết đọc `os.getenv` trực tiếp | cần sửa doc hoặc sửa code |
| `docs/docker.md`: liệt kê 4 dashboard Grafana | chỉ có 1 file JSON dashboard (`llm_latency.json`) | 3 dashboard còn lại chưa tồn tại |
| Metric `orders_processed_total`, `db_connections` định nghĩa trong `metrics.py` | không có code nào gọi/dùng | khả năng sót lại từ template gốc khác (gợi ý: `POSTGRES_DB` default là `food_order_db` trong `config.py:189` và `docs/configuration.md`) |
| `Thread` model tồn tại và được migrate, docs mô tả "mirror LangGraph checkpoint thread" | không có service code nào CRUD bảng `Thread`; LangGraph tự quản lý bảng `checkpoints` riêng | có thể xoá hoặc hoàn thiện tuỳ ý định tương lai |
| CI/deploy workflow trigger trên branch `master` | `git status` cho thấy branch hiện tại/chính là `main` | khả năng lệch tên branch, nên kiểm tra lại workflow trigger |
| `pyproject.toml` có dependency group `test` (pytest, httpx) | không có thư mục `tests/` nào trong repo | eval dựa trên LLM-judge thay cho unit/integration test truyền thống |

## 14. File tham chiếu nhanh

| Mục đích | File |
|---|---|
| App factory + lifespan | `app/main.py` |
| Router tổng | `app/api/v1/api.py` |
| Auth | `app/api/v1/auth.py`, `app/utils/auth.py` |
| Chat endpoint | `app/api/v1/chatbot.py` |
| LangGraph graph | `app/core/langgraph/graph.py` |
| Tools | `app/core/langgraph/tools/` |
| Settings | `app/core/config.py` |
| Logging | `app/core/logging.py` |
| Metrics | `app/core/metrics.py` |
| Observability (Langfuse) | `app/core/observability.py` |
| DB models | `app/models/{base,user,session,thread}.py` |
| LLM service | `app/services/llm/{registry,service}.py` |
| Memory service | `app/services/memory.py` |
| Migration | `alembic/versions/b25d38b0cd7c_initial_schema.py`, `alembic/env.py` |
| Eval harness | `evals/evaluator.py`, `evals/main.py`, `evals/metrics/prompts/*.md` |
| Compose/Docker/CI | `docker-compose.yml`, `Dockerfile`, `.github/workflows/{ci,deploy}.yaml`, `Makefile` |
| Grafana/Prometheus | `grafana/dashboards/json/llm_latency.json`, `prometheus/prometheus.yml` |
