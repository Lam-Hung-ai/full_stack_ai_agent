# High-Level Design — `trueforge`

> Nguồn: `/home/lamhung/code/trueforge`
> TrueForge là **"agent harness"** mã nguồn mở của TrueFoundry — runtime layer biến 1 LLM thành agent hoạt động được: vòng lặp gọi model, MCP tools, skills, sandbox, approval, quản lý context, session state. Expose qua 3 cách: chat UI dựng sẵn, HTTP API + SDK TypeScript, và UI SDK nhúng được (`@truefoundry/trueforge-ui`). Khác hẳn 4 dự án trước (đều Python) — đây là **monorepo TypeScript/Node.js** (pnpm workspace, Node ≥22.14).

> Lưu ý: tuy do TrueFoundry (công ty MLOps/LLM-gateway thương mại) phát triển, đây là **project độc lập, chạy được riêng** (MIT license), không phải wrapper quanh sản phẩm khác của TrueFoundry — chỉ có 1 lớp tích hợp mỏng tuỳ chọn (`src/truefoundry/`) khi chạy trong nền tảng TrueFoundry.

## 1. Tech stack

| Lớp | Công nghệ |
|---|---|
| Runtime | Node.js ≥22.14, TypeScript, ESM, build bằng `tsup`, dev bằng `tsx` |
| HTTP framework | **Hono** + `@hono/zod-openapi` (route có kiểu + tự sinh OpenAPI) |
| SDK generation | Fern — sinh TS SDK (`packages/trueforge-sdk`) và Python SDK (`python/trueforge_sdk/` — **chỉ là client SDK sinh ra, không phải backend Python**) |
| Frontend | **Vite 6 + React 19** (không phải Next.js), chat UI dựng trên `@assistant-ui/react`, có adapter riêng `packages/assistant-ui-runtime` nối runtime của assistant-ui với giao thức turn/event SSE của TrueForge |
| DB / Query builder | **Kysely** (SQL query builder, không phải ORM đầy đủ) — 2 bộ migration **song song, giống hệt cấu trúc** cho Postgres và SQLite (~45 migration mỗi bộ, có rule trong `AGENTS.md` bắt buộc đồng bộ) |
| Queue / Cache | **Redis** — dùng cho (a) RPC request/reply xuyên-replica (điều phối huỷ turn) và (b) Redis Streams làm backend resumable SSE event-transport ở hosted mode |
| MCP / Sandbox | MCP client native (`core/mcp/RemoteMCP.ts`, header-auth + OAuth), sandbox-as-a-tool qua **Daytona** (`core/sandbox/Sandbox.ts`) + chế độ "local sandbox" cho dev |

## 2. Kiến trúc package (`packages/`)

| Package | Vai trò |
|---|---|
| `trueforge` | Server + CLI chính (`@truefoundry/trueforge`). Route Hono (`src/routes/*Routes.ts`), handler (`src/apis/*.ts`), tầng DB (`src/db/{postgres,sqlite}`), auth, catalog YAML (model/MCP/skill/sandbox), **controller** chạy process riêng (`src/controller-main.ts`) cho lịch chạy định kỳ, đóng gói sẵn frontend build (`npx @truefoundry/trueforge` chạy mọi thứ trong 1 process). |
| `trueforge-core` | Thư viện harness/engine thực sự, **không phụ thuộc Hono/Express** — framework-agnostic. Gồm `core/runtime` (vòng lặp agent: `AgentThread.ts` 1562 dòng, `AgentThreadOrchestrator.ts` 593 dòng), `core/llm` (`VercelAILLM.ts`), `core/mcp`, `core/sandbox`, `agent-session` (domain model session/turn/event + store), `request-reply` (RPC xuyên-replica qua Redis). |
| `trueforge-sdk` | SDK TypeScript do Fern sinh. |
| `assistant-ui-runtime` / `frontend` / `trueforge-ui` | Các package frontend. |
| `python/trueforge_sdk/` | SDK Python do Fern sinh (mirror của `trueforge-sdk`) — **không phải backend**. |
| `charts/trueforge` | Helm chart (Deployment server + HPA + PDB, Deployment controller **1 replica riêng biệt**, subchart Postgres/Redis Bitnami tuỳ chọn). |

## 3. Vòng lặp Agent — tự viết tay, chỉ dùng Vercel AI SDK cho model call thô

`AgentThread`/`AgentThreadOrchestrator` là **state machine tự viết hoàn toàn** (không LangChain.js/LangGraph.js), hỗ trợ cây sub-agent thread chạy đồng thời (`mergeAsyncGenerators`, `MAX_PARALLEL_SUB_AGENTS = 5`), gating tool-approval, tạm dừng khi cần MCP auth, phát ra stream sự kiện nội bộ.

Model call đi qua `VercelAILLM.ts` — wrapper của **`streamText` trong Vercel AI SDK** (`"ai": "^7.0.118"`) — nghĩa là **vòng lặp quanh tool-call là tự viết, nhưng primitive stream LLM thô là của Vercel AI SDK**.

Nguyên tắc thiết kế tường minh (`packages/trueforge-core/src/core/runtime/AGENTS.md`):
```
Durable state MUST follow:
  yield event; // consumer persists and may throw
  mutateMemory(); // runs only after persistence succeeds
```
→ Đây là kỷ luật event-sourcing tự viết tay, **không phải checkpointer của framework nào**.

## 4. Giao thức Chat — Trigger & Stream TÁCH BIỆT (giống pattern Onyx/AgentScope)

| Endpoint | Vai trò |
|---|---|
| `POST /{session_id}/turns` | Tạo + thực thi 1 turn. `stream` mặc định `true` → SSE `TurnStreamingEvent`; `stream: false` → trả JSON ngay với `state.status: "running"`, thực thi tiếp tục nền (fire-and-forget, không gắn với response HTTP này). |
| `GET /{session_id}/turns/{turn_id}/subscribe` | Endpoint SSE **riêng biệt** để theo dõi/resume: *"Pass `after_sequence_number` to resume after a disconnect"*. OpenAPI metadata ghi rõ `'x-fern-streaming': { format: 'sse', resumable: true }` (khác route tạo turn có `resumable: false`). |
| `POST /{session_id}/cancel` | Endpoint huỷ tường minh — tách biệt khỏi disconnect. |

→ Đúng pattern **tách trigger khỏi kênh stream** đã thấy ở `onyx` và `agentscope` (Agent Service).

## 5. Scale

- Redis có 2 vai trò độc lập: (a) buffer SSE resumable (Redis Streams) để **bất kỳ replica nào** cũng phục vụ được request `subscribe`; (b) bus request/reply cho việc **huỷ turn xuyên-replica** (turn thực thi vẫn pin vào đúng 1 process, nhưng lệnh huỷ được forward qua Redis pub/sub tới đúng process sở hữu).
- Helm Service **không có `sessionAffinity`** — load balance round-robin bình thường.
- HPA scale server theo CPU; **controller chạy riêng, cố định 1 replica** (vì lịch chạy định kỳ không được double-fire).
- Graceful shutdown timeout được set cao hơn `GRACEFUL_TIMEOUT_SECONDS` để `ActiveTurnRegistry` kịp drain turn đang chạy trước khi bị SIGKILL lúc rolling deploy/scale-down.

## 6. Tài liệu liên quan

- `trueforge-LLD.md` — chi tiết route, cơ chế resume, schema DB, cross-replica cancel.
- `chat-data-flow-comparison.md` — luồng dữ liệu so sánh toàn bộ các dự án đã khảo sát.
