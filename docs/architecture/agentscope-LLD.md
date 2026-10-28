# Low-Level Design — `agentscope`

> Nguồn: `/home/lamhung/code/agentscope`. Đọc kèm `agentscope-HLD.md`.

## 1. Cấu trúc module (`src/agentscope/`)

```
agent/        Class Agent (base, duy nhất — không có hierarchy ReactAgent/DialogAgent như bản 1.0)
app/          Agent Service (FastAPI): router, message_bus, storage, service (chat/session/...)
asr/          Speech-to-text
classifier/   Phân loại
console/      launch_console — chạy agent qua terminal, KHÔNG persistence
credential/   Quản lý credential
embedding/    Embedding provider
event/        Taxonomy sự kiện thống nhất (streaming)
exception/    Exception riêng
formatter/    Format message theo provider
mcp/          Tích hợp Model Context Protocol
message/      Msg, ContentBlock (Text/Thinking/ToolCall/ToolResult/Data/Hint)
middleware/   Hook pipeline: on_reply, on_reasoning, on_check_permission, on_acting, on_model_call, on_system_prompt, on_compress_context
model/        ChatModelBase + wrapper từng provider (OpenAI/Anthropic/Gemini/DashScope/DeepSeek/...)
permission/   PermissionEngine (gate thực thi tool, HITL confirm)
pipeline/     PipelineProtocol, GoalPipeline, TeamPipeline
rag/          Retrieval-augmented generation
realtime/     Voice/WebRTC transport
skill/        Tích hợp "skill"
sop/          (Standard Operating Procedure — chưa đào sâu)
state/        AgentState (pydantic) — nơi lưu context/summary/permission/tool_context
tool/         Toolkit, ToolBase/FunctionTool, ToolResponse/ToolChunk, tool code sẵn (Bash/Grep/Glob/Read/Write/Edit)
tts/          Text-to-speech
tui/          Giao diện terminal (textual)
types/        Type định nghĩa chung
workspace/    Sandbox thực thi tool (Docker/E2B/Daytona/K8s/Apple Container/Bubblewrap/OpenSandbox)
```

## 2. Class `Agent` (`src/agentscope/agent/_agent.py`, ~3925 dòng)

Thiết kế **1 class duy nhất** (khác bản AgentScope 1.0 từng có hierarchy `ReactAgent`/`DialogAgent`) — hành vi được compose qua tham số:

```python
def __init__(self, name, system_prompt, model: ChatModelBase, toolkit=None,
             middlewares=None, state: AgentState | None = None,
             offloader=None, model_config=None, context_config=None,
             react_config=None, injection_config=None) -> None:
    ...
    self.state = state or AgentState()
    self._engine = PermissionEngine(self.state.permission_context)
    self.toolkit = toolkit or Toolkit()
```

### API công khai (dòng 288-380)
- `reply_stream(inputs) -> AsyncGenerator[AgentEvent | Msg, None]`
- `reply(inputs) -> Msg` (tiêu thụ hết stream, trả message cuối)

`inputs` nhận `Msg | list[Msg] | UserConfirmResultEvent | UserInterruptEvent | ExternalExecutionResultEvent | None`.

### Vòng lặp ReAct nội bộ
`_reasoning` → `_acting` → thực thi tool (`_execute_tool_call`, có batch tuần tự/song song: `_batch_tool_calls`, `_execute_concurrent_tool_calls`) → nén context → kiểm tra permission — tất cả đi qua hệ thống **Middleware** (hook: `on_reply`, `on_reasoning`, `on_check_permission`, `on_acting`, `on_model_call`, `on_system_prompt`, `on_compress_context` — `middleware/_base.py:13 MiddlewareBase`).

## 3. Message schema (`src/agentscope/message/`)

- `_base.py`: `Msg` (role/name/content), content = list block kiểu `ContentBlock` union (`_block.py`): `TextBlock`, `ThinkingBlock`, `ToolCallBlock`, `ToolResultBlock`, `DataBlock` (đa phương thức), `HintBlock`.
- Subtype `UserMsg`/`SystemMsg`/`AssistantMsg` validate loại block được phép theo từng role.

## 4. State / "Memory" (`src/agentscope/state/_state.py`)

```python
class AgentState(BaseModel):
    session_id: ...
    summary: ...          # context đã nén
    context: list[Msg]    # toàn bộ hội thoại chưa nén = short-term memory thực tế
    reply_context: ...    # reply_id/cur_iter/structured_schema/output
    permission_context: ...
    tool_context: ...     # cache file-read, tool group đã kích hoạt
    tasks_context: ...
    middle_context: dict  # state tự do cho middleware
```

**Không có class `Memory` riêng biệt** trong bản này — bộ nhớ hội thoại chính là field `context` của `AgentState`. Long-term/semantic memory là mối quan tâm riêng, xử lý qua middleware pluggable: `middleware/_longterm_memory/` tích hợp **Mem0** (pin v2.x) hoặc **ReMe**.

## 5. Tool-calling (`src/agentscope/tool/`)

`Toolkit`, `ToolBase`/`FunctionTool`, `ToolResponse`, `ToolChunk`, `ToolChoice`; tool coding sẵn (`Bash`, `Grep`, `Glob`, `Read`, `Write`, `Edit`) + tích hợp MCP server và "skill" (`src/agentscope/mcp/`, `src/agentscope/skill/`). Thực thi tool có thể tuần tự hoặc song song, được `PermissionEngine` (`src/agentscope/permission/`) chặn/kiểm soát (xác nhận HITL qua `RequireUserConfirmEvent`/`UserConfirmResultEvent`).

## 6. Pipeline / Điều phối đa agent (`src/agentscope/pipeline/`)

- `PipelineProtocol` (`_base.py:15`)
- `GoalPipeline` (`_goal_pipeline.py:55`) — vòng plan→execute→verify theo 1 mục tiêu.
- `TeamPipeline` (`_team_pipeline.py:110`) — agent leader giao việc cho agent thành viên qua tool `_TeamAssign` (mới từ 2026-09 theo README).

**Không có `MsgHub`/broadcast-fanout** (khái niệm của AgentScope 1.x) trong bản này — điều phối đa agent dựa trên pipeline (sequential/goal/team) cộng tính năng "Agent Team" của Agent Service (leader/worker session, `app/_tool/_agent_invite.py`, `_agent_create.py`).

## 7. Streaming — chi tiết cơ chế

### Tầng model
`ChatModelBase` (`model/_base.py:38-96`): constructor có `stream: bool = True`; `__call__(...) -> ChatResponse | AsyncGenerator[ChatResponse, None]` (dòng 182-188). Mọi wrapper provider (OpenAI `model/_openai_chat/_model.py:205`, Anthropic, Gemini, DashScope, DeepSeek, Moonshot, Volcengine, MiniMax, xAI, Ollama) implement đúng hợp đồng này.

### Tầng agent
`Agent._call_model` (`_agent.py:3274`) gọi model, nhận 1 trong 2 dạng trên; `_convert_chat_response_to_event`/`_convert_tool_chunk_to_event` (`_agent.py:3757`, `3886`) biến chunk stream thành **event đã chuẩn hoá** (`event/_event.py`): `ReplyStartEvent`, `ModelCallStartEvent`/`ModelCallEndEvent`, bộ ba Start/Delta/End cho `TextBlock`/`ThinkingBlock`/`ToolCall`/`ToolResult`/`DataBlock`, cộng `HintBlockEvent`, `RequireUserConfirmEvent`, `RequireExternalExecutionEvent`, `UserConfirmResultEvent`, `UserInterruptEvent`, `ExceedMaxItersEvent`, `ReplyEndEvent`, `CustomEvent`.

### Consumer API
```python
async for event in agent.reply_stream(inputs):
    ...
```
Đây chính xác là cách `console/__init__.py` dùng cho terminal, và cách Agent Service dùng để đẩy ra browser (xem §9). Nghĩa là: **1 web backend nhận chunk stream qua async-generator + event có kiểu rõ ràng, không phải raw text delta** — khác hẳn cách 3 dự án FastAPI+LangGraph tự định nghĩa vocabulary sự kiện riêng.

## 8. Persistence

- **Core library (`agentscope.agent`/`agentscope.state`) không sở hữu persistence nào.** `AgentState` là pydantic `BaseModel` thuần — serializable chuẩn (`model_dump()`/`model_dump_json()`/`model_validate()`), nhưng class `Agent` **không có** `.save()`/`.load_state()`/checkpoint hook riêng. Docstring của `launch_console` (`src/agentscope/console/__init__.py`) ghi rõ: *"A lightweight try-out/debugging entry — no session management, no persistence: the conversation lives in `agent.state` and ends with the process."*
- **Persistence do lớp Agent Service tuỳ chọn cung cấp** (`src/agentscope/app/storage/`): abstract `StorageBase` (`storage/_base.py`, 1447 dòng) với `update_session_state(user_id, agent_id, session_id, state: AgentState)` (dòng 435) và `get_session(...) -> SessionRecord | None` (dòng 489). 2 backend cụ thể: `storage/_sql/_storage.py` (SQLAlchemy 2.0 async + Alembic — Postgres/MySQL/SQLite tuỳ driver) và `storage/_redis_storage.py`. `SessionRecord` (`storage/_model/_session.py:315,448`) có field `state: AgentState = Field(default_factory=AgentState)` — **toàn bộ blob pydantic state được lưu nguyên khối** theo từng session.

### Vòng lặp round-trip (`app/_service/_chat.py`)
```
Mỗi lượt chạy:
  1. Load AgentState từ storage (session_record.state, dòng 1176)
  2. Dựng Agent MỚI HOÀN TOÀN với state=agent_state (dòng 1179-1190)
  3. Chạy lượt chat (reply_stream)
  4. _persist() (dòng 1481-1512, chạy "shielded" dưới distributed lock):
       storage.upsert_message(...) cho từng message trả lời
       storage.update_session_state(..., state=agent.state)  # ghi state đã mutate
```
→ Persistence xảy ra **theo từng lượt hoàn chỉnh**, không phải theo từng token.

## 9. Agent Service — Router & Giao thức

- **`POST /chat/`** (`app/_router/_chat.py`) — **fire-and-forget**: spawn chat run thành background task qua `ChatRunRegistry` (trả 409 nếu session đó đang có lượt chạy), **trả về ngay, không trả event trong response body**.
- **`GET /sessions/{session_id}/stream`** (`app/_router/_session.py:810-975`) — endpoint **SSE** dài hạn (`media_type="text/event-stream"`) mà client thực sự dùng: subscribe kênh theo session trên `MessageBus`, **replay log sự kiện đã lưu của session**, sau đó forward sự kiện live, kèm heartbeat 30s (`:\n\n`) để sống qua idle timeout của reverse proxy.
- **`MessageBus`** (`src/agentscope/app/message_bus/`) — abstraction pub/sub + durable log:
  - `_in_memory_message_bus.py` — 1 process.
  - `_redis_message_bus.py` — Redis Streams, multi-process/multi-node.
  - API (`_base.py:53-910`): `publish`/`subscribe` (live), `log_append`/`log_read`/`log_trim` (log sự kiện replay được theo session), `acquire_lock`/`try_lock` (distributed lock), `registry_*` (KV bền vững nhỏ cho HITL projection/checkpoint cursor), `session_run`/`session_is_running`/`session_publish_cancel` (run-lock/cancel theo session).

### Router tổng
`app/_app.py::create_app(storage, message_bus, workspace_manager, ...)` dựng FastAPI app; `app/_router/__init__.py` mount: `agent_router`, `channel_router`, `chat_router`, `credential_router`, `health_router`, `hub_router`, `knowledge_base_router`, `session_router`, ... README mô tả: multi-tenancy, Agent Team (leader-worker), Channels (Feishu/Discord tuỳ biến), RAG service, MCP/Skill hub, resource sharing, SQL/NoSQL persistence, scheduling (apscheduler).

## 10. Cơ chế Resume khi reload (SO VỚI 3 DỰ ÁN TRƯỚC — ĐÂY LÀ ĐIỂM KHÁC BIỆT LỚN NHẤT)

Core library không cung cấp gì cho việc này (chỉ có `AgentState` làm snapshot serializable). Nhưng **Agent Service cung cấp cơ chế resumable-stream thật sự**, gồm 2 phần phối hợp:

### a) Replay log
Mỗi event được append qua `MessageBus.log_append` vào 1 log có giới hạn theo session (`MessageBusKeys.session_events(session_id)`, giới hạn `SESSION_REPLAY_MAX_LEN = 1000` entry). `GET /sessions/{id}/stream?after=<cursor>`:
1. Replay `log_read(events_key, since=after, ...)` trước.
2. Chuyển sang `subscribe()` live.
3. Khử trùng lặp theo entry id ở điểm nối giữa replay/live (`app/_router/_session.py:865-963`, có test riêng `tests/session_event_stream_test.py::test_event_at_replay_live_seam_is_delivered_once`).

→ **Client reload giữa chừng stream → kết nối lại `/sessions/{id}/stream` (kèm cursor `after` lấy từ API list message) → nhận lại đúng những delta đã bỏ lỡ, rồi tiếp tục live — KHÔNG mất token nào kể cả đang generate dở.**

### b) Checkpoint theo lượt
Sau mỗi lượt hoàn chỉnh, `_persist()` (`app/_service/_chat.py:1481-1512`) ghi bền vững `AgentState` vào SQL/Redis storage và trim log replay tới checkpoint cursor — nên log replay chỉ cần cover "từ snapshot `AgentState` bền vững gần nhất", không phải toàn bộ hội thoại.

### Nếu build trực tiếp trên bare SDK (không dùng `agentscope.app`)
Phải tự xây cơ chế này — nhưng có sẵn đúng nguyên liệu để làm: `agent.reply_stream()` đã cho stream sự kiện có cấu trúc (không phải raw text) để tự append vào log/queue riêng và tự fan-out qua SSE/WebSocket riêng, cộng `AgentState` (pydantic) để tự snapshot vào bất kỳ store nào ở độ chi tiết tự chọn.

## 11. Distributed / Scale

- **Không còn runtime distributed/actor-model nào cho bản thân agent.** Grep `RpcAgent`/`to_dist`/class agent phân tán trên toàn `src/` → **0 kết quả**; `docs/changelog.md` xác nhận việc deprecate khi chuyển 0.x→1.0 ("❌ Deprecate distribution functionality momentarily, a new distribution module is coming soon") và chưa có module thay thế — agent là **object Python in-process thuần tuý**.
- Khả năng chạy đa process/đa node chỉ tồn tại ở **tầng Agent Service**: `MessageBus` (bản Redis) cung cấp distributed lock (`acquire_lock`, dùng cho "run lock" theo session — chỉ 1 worker process được thực thi 1 session tại 1 thời điểm; `SessionStatus.RUNNING` nghĩa là "có 1 worker nào đó trong cluster đang giữ run-lease của session này trên message bus", `app/_service/_session.py`), log sự kiện bền vững cho SSE fan-out xuyên process, và storage SQL/Redis dùng chung cho state session giữa các worker. **Đây là lớp điều phối cho các worker app stateless chạy song song, không phải hệ thống actor/object phân tán.**
- Riêng biệt, có tích hợp **A2A (Agent2Agent) protocol** (`src/agentscope/agent/_a2a_agent.py`, `examples/a2a`) để 1 agent nói chuyện với agent **remote** như 1 peer service — đây là giao thức interop, không phải distributed runtime của chính AgentScope.

### Pattern scale khuyến nghị (suy ra từ code Agent Service)
Chạy N process FastAPI/uvicorn stateless sau load balancer, tất cả dùng chung Redis (message bus) + SQL/Redis (storage), mỗi request/lượt **tạo mới hoàn toàn 1 object `Agent`** từ state đã externalize — scale ngang các worker stateless, **không phải** distributed object/actor graph.

## 12. Trả lời trực tiếp 5 câu hỏi áp dụng cho AgentScope

| Câu hỏi | Trả lời |
|---|---|
| **a. SSE hay WebSocket?** | Agent Service dùng **SSE** (`GET /sessions/{id}/stream`), tách biệt khỏi trigger `POST /chat/` (fire-and-forget). Nếu chỉ dùng core SDK (không `agentscope.app`) thì **không có giao thức nào được áp đặt** — tự quyết định. Riêng voice agent dùng **WebRTC** (`aiortc`), không liên quan tới text chat. |
| **b. Có "LangGraph Platform"-tương đương không?** | **Có — chính là Agent Service** (`agentscope.app`): FastAPI runtime hoàn chỉnh, multi-tenant/multi-session, persistence SQL/Redis, scheduling, channel, RAG, frontend dựng sẵn. Nhưng là **self-hosted mã nguồn mở**, không phải managed SaaS. Class `Agent` thuần vẫn dùng độc lập được (`launch_console`), không phụ thuộc service nào. |
| **c. Reload giữa stream có resume được không?** | **Core SDK: không.** **Agent Service: CÓ — và đây là khác biệt lớn nhất so với 3 dự án trước.** Nhờ replay log (`log_append`/`log_read` theo session, cursor `after`) + checkpoint `AgentState` theo lượt, client reload có thể reconnect `GET /sessions/{id}/stream?after=<cursor>` và **nhận lại đúng phần token đã bỏ lỡ rồi tiếp tục live, không mất gì kể cả đang generate dở** — điều mà cả `ai_agent` (mất hẳn lượt đang chạy) lẫn `fastapi-langgraph-agent-production-ready-template` (mất animation stream, chỉ còn text final) đều không làm được. |
| **d. State lưu ở đâu?** | Core: **pure in-memory Python object graph** (`AgentState` pydantic, serializable nhưng `Agent` không tự save/load). Agent Service: **có store built-in** (SQL async/Alembic hoặc Redis) lưu nguyên khối `AgentState` theo session, đọc/ghi quanh mỗi lượt — đây là nơi duy nhất AgentScope "tự quản lý" persistence thật sự, và nó dùng đúng cơ chế serialization gốc của state (pydantic), không phải 1 schema DB song song tự thiết kế như `ai_agent`. |
| **e. Scale thế nào?** | **Không có distributed/actor runtime riêng cho agent** (tính năng RPC/actor của bản cũ đã bị deprecate, chưa có thay thế). Scale là trách nhiệm của app nhúng SDK — nhưng Agent Service cung cấp đúng bộ công cụ chuẩn để làm điều đó: N worker FastAPI/uvicorn **stateless**, mỗi lượt **tạo `Agent` object mới hoàn toàn** từ `AgentState` nạp lại từ storage dùng chung, điều phối quyền "ai đang xử lý session nào" qua distributed lock trên `MessageBus` (Redis). Đây là scale-out kiểu stateless worker + state externalize hoàn toàn — **đúng mô hình `fastapi-langgraph-agent-production-ready-template` đang làm (Postgres checkpointer dùng chung)**, khác hẳn `ai_agent` (state chủ yếu nằm im trong 1 process, không cần externalize vì checkpointer LangGraph gần như không hoạt động). |
