# Low-Level Design — `trueforge`

> Nguồn: `/home/lamhung/code/trueforge`. Đọc kèm `trueforge-HLD.md`.

## 1. Route Chat/Turn (`packages/trueforge/src/routes/turnRoutes.ts`, mount tại `/api/v1/sessions`)

### `POST /{session_id}/turns` (`createAndExecuteTurnRoute`, dòng 215-287)
Tạo + thực thi 1 turn. Body có `stream` (mặc định **true**):
- `stream: true` → response `text/event-stream` SSE, trả `TurnStreamingEvent`.
- `stream: false` → trả JSON turn ngay với `state.status: "running"`, thực thi tiếp tục **ở background trên server, không gắn với response HTTP này**.

### `GET /{session_id}/turns/{turn_id}/subscribe` (`subscribeTurnRoute`, dòng 289-329)
Endpoint SSE **riêng biệt**, docstring: *"Subscribe to the live SSE stream for a turn... Pass `after_sequence_number` to resume after a disconnect (exclusive — events after this sequence number are replayed)."* Metadata OpenAPI: `'x-fern-streaming': { format: 'sse', resumable: true }` (route tạo turn có `resumable: false`).

### `POST /{session_id}/cancel`
Endpoint huỷ tường minh, tách biệt hoàn toàn khỏi việc disconnect.

→ Đây là **cùng pattern tách trigger/stream** đã thấy ở `onyx` (`POST /send-chat-message` + `GET .../resume-stream?cursor=N`) và lớp Agent Service của `agentscope`.

## 2. Agent Runtime — vòng lặp tự viết, Vercel AI SDK chỉ cho raw model call

`AgentThread`/`AgentThreadOrchestrator` (trong `trueforge-core`) là **state machine tự viết hoàn toàn** — không LangChain/LangGraph. Hỗ trợ cây sub-agent thread chạy đồng thời, gating tool-approval, pause khi cần MCP auth.

Model call đi qua `VercelAILLM.ts:1440` gọi `streamText(...)` của Vercel AI SDK. **Không có checkpointer kiểu LangGraph nào** — "checkpoint" chỉ là tên 1 cột jsonb trong schema tự thiết kế của TrueForge (xem mục 5), là khái niệm **tự quản lý**, không phải framework-managed.

## 3. Hành vi khi reload giữa stream — disconnect KHÔNG huỷ generation, chỉ dừng ghi vào socket chết

Trong `createAndExecuteTurnHandler` (`packages/trueforge/src/apis/turns.ts:861-893`):

```ts
let shouldWriteToSSEStream = true;
return streamSSE(c, async stream => {
  stream.onAbort(() => {
    shouldWriteToSSEStream = false;
    deps.logger.info(
      'Create-turn SSE client disconnected, continuing drain without writing',
      disconnectLogContext,
    );
  });
  await drainTurnEvents({
    ...drainInput,
    onEvent: async (event, sequenceNumber) => {
      if (!stream.closed && !stream.aborted && shouldWriteToSSEStream) {
        try {
          await withTimeout(stream.writeSSE(turnEventSsePayload(event, sequenceNumber)), ...);
        } catch (error) { ... shouldWriteToSSEStream = false; }
      }
    },
  });
  ...
});
```

Hono map disconnect của client thành `stream.onAbort()`, nhưng handler **vẫn tiếp tục drain** (`drainTurnEvents`) — chỉ bật cờ để ngừng cố ghi SSE. Việc thực thi model/tool thật sự (`turn.stream()` từ `AgentThread`) được gắn với 1 `AbortController` theo dõi bởi `ActiveTurnRegistry` (`packages/trueforge/src/runtime/activeTurns.ts`) **chỉ bị abort khi**: có lệnh huỷ tường minh (`cancelIfRunning`) hoặc server shutdown (`shutdownAndWait`) — **không bao giờ** bị huỷ bởi HTTP disconnect.

**Quan trọng (khác `fastapi-langgraph-agent-production-ready-template`)**: mọi event stream trung gian được **persist bền vững ngay khi sinh ra** qua "dual-write trước khi gửi tới bất kỳ client sink nào" trong `drainTurnEvents` (`turns.ts:385-410`, comment: *"Dual-write turn events to the resumable subscription registry, then optionally forward each sequenced event... so subscribers can resume after disconnect."*).

## 4. Cơ chế Resumable Stream — replay-then-tail theo cursor, gần giống nhất với thiết kế của Onyx

`EventSubscriptionRegistry` (`packages/trueforge/src/runtime/event-subscription/index.ts`) là transport resumable: "create-turn writes, subscribe polls." 2 backend theo mode:

### Hosted mode (`STANDALONE=false`)
`RedisEventSubscription` (`redis.ts`) — ghi qua `XADD` với sequence number tăng dần tự đánh làm stream-entry ID (`${seq}-1`), có TTL (`TURN_STREAM_TTL_SECONDS` khi đang chạy, rút ngắn còn `TURN_STREAM_POST_COMPLETION_TTL_SECONDS` sau `turn.done`). Đọc (`subscribeTurnHandler`, `turns.ts:903-982`) dùng `XREAD` với cursor resume tính từ `after_sequence_number + 1`, poll mỗi `SUBSCRIBE_STREAM_POLL_SLEEP_INTERVAL_MS` (1s) khi idle — tức là **buffer replay-then-tail đọc được xuyên-replica**, tương đương về chức năng với thiết kế stream-buffer Redis/Postgres của Onyx. `assertSubscribable()` trả HTTP 412 (`StreamGoneError`) nếu key Redis đã hết hạn hoặc sắp hết hạn.

### Local/standalone mode (`STANDALONE=true`, 1 process)
`InMemoryEventSubscription` trên 1 store in-process dùng chung — chỉ hoạt động được vì chỉ có đúng 1 process.

Cursor resume được resolve ưu tiên header `Last-Event-ID` trước, sau đó mới tới `after_sequence_number` ở body (`resolveAfterSequenceNumber`, `turns.ts:566-582`) — khớp đúng ngữ nghĩa reconnect chuẩn của SSE — SDK TS/Python hoặc `EventSource` polyfill có thể tự reconnect, server replay lại event đã lỡ rồi tiếp tục live, kết thúc stream sạch sẽ khi `turn.done` (`turns.ts:965-967`).

### Tín hiệu thiết kế từ schema
`TurnStatusSchema = z.enum(['running', 'paused', 'done', 'cancelled', 'error'])` (`packages/trueforge-core/src/agent-session/schemas/turn.ts:26`) — `turn.state.status` chính là "fence/freeze target" mà comment migration Postgres mô tả (mọi write có điều kiện đều predicate theo `state->>'status'`) — tức là 1 state machine in-progress/terminal **được thiết kế có chủ đích từ đầu** cho đúng mục đích resume/reconnect này.

## 5. Schema DB — 100% self-managed Postgres/SQLite, không có checkpointer framework

Xác nhận qua `packages/trueforge/src/db/postgres/migrations/20260728_000001_session_store.ts` (mirror y hệt cấu trúc ở migration sqlite), DDL bằng Kysely, comment rất chi tiết về lý do thiết kế:

| Bảng | Vai trò |
|---|---|
| `session` | PK `tenant_id, session_id`, `agent_spec` jsonb, `title`, `last_turn_id` (con trỏ nóng tới tip), `custom` jsonb (caller sở hữu), timestamp |
| `turn` | PK `tenant_id, session_id, turn_id`, `first_turn_id`/`previous_turn_id`/`ancestor_ids` (topology chuỗi turn), `input` jsonb, **`state` jsonb** (status fence, xem mục 4), `checkpoint` jsonb (nhỏ, mở rộng được, store tự sở hữu thông tin tài nguyên theo turn: MCP server, sandbox info), `custom` jsonb |
| `turn_thread` | Toàn bộ state của 1 agent thread tại 1 turn: `checkpoint` jsonb, `agent_info` jsonb (định danh sub-agent), `current_context_usage` jsonb, `context_ids` (bigint[] — con trỏ có thứ tự vào message log) |
| `session_event` | **Log append-only thuần tuý** của event turn đã persist (`event_id` ULID, `event` jsonb) — đây là record bền vững backing `listTurnEvents`/`listSessionEvents` (**khác** với Redis/in-memory stream tạm thời chỉ dùng cho replay SSE *live* — Redis có TTL và chỉ phục vụ resume giữa chừng; bảng `session_event` Postgres/SQLite mới là lịch sử vĩnh viễn) |
| `thread_context_log` | Log nội dung message theo thread, bất biến, append-only, `append_id` bigint identity |
| `thread_capability_state` | Snapshot KV theo turn/thread/key (vd quyết định tool-approval), **key theo từng turn** (không phải "latest-wins" xuyên turn) "để fork/restore từ bất kỳ turn nào cũng thấy đúng map tại thời điểm đó" |

Đây là schema **event-sourced thiết kế riêng** (không phải entity model qua ORM, không phải checkpointer LangGraph). Kysely chỉ dùng như SQL builder có kiểu.

## 6. Scaling — chi tiết

- `docker-compose.yml` comment về service `redis`: *"Shared by all server replicas: carries executor peering (cross-replica turn cancel via request-reply)."* Và về `server`: *"Compose runs one replica but keeps peering on... STANDALONE=false ⇒ Postgres + Redis. A single-process deployment can set STANDALONE=true and drop redis."*
- **Redis có 2 vai trò độc lập**:
  1. Buffer resumable SSE event-stream (Redis Streams, mục 4) — cho phép **bất kỳ replica nào** phục vụ được request `subscribe`, bất kể replica nào đang thực sự chạy turn đó.
  2. Bus request/reply RPC (`packages/trueforge-core/src/request-reply/`) cho việc **huỷ turn xuyên-replica**.
- **Thực thi turn KHÔNG được phân tán** — `ActiveTurnRegistry` (`activeTurns.ts`) là strictly in-memory theo process, process sở hữu turn được ghi lại là `active_executor_id` trên row `turn` (migration `20260918_000001_turn_active_executor_id.ts`). Nếu request huỷ đến 1 replica không sở hữu turn đó, `cancelSessionTurn` (`packages/trueforge-core/src/request-reply/client.ts:160-214`) publish request lên kênh pub/sub Redis của executor sở hữu (`requestChannel(executorId)`), rồi poll key reply theo request bằng `GETDEL` tới khi executor sở hữu trả lời qua `cancelSessionTurnPeerHandler`, hoặc timeout, hoặc heartbeat key của owner biến mất (executor chết ⇒ "đóng băng turn đang chạy").
- **Helm chart** (`charts/trueforge/templates/`): `deployment.yaml` không pin `replicas` khi bật autoscale (`hpa.yaml` scale theo CPU); `service.yaml` là Service `ClusterIP` thường, **không set `sessionAffinity` nào cả** — xác nhận request được load-balance round-robin xuyên replica, không cần sticky session, nhất quán với thiết kế dựa trên Redis (bất kỳ replica nào cũng phục vụ được request đọc/resume; chỉ việc tiếp tục thực thi và huỷ cùng-process mới pin vào executor sở hữu, và việc đó được bridge qua Redis request-reply, không phải qua routing). `values.yaml`: *"The server always runs peered (STANDALONE=false) against Postgres + Redis."* 1 Deployment **controller riêng biệt, chỉ 1 replica** (`controller-deployment.yaml`, cũng là service `controller` trong `docker-compose.yml` chạy `dist/controller-main.js`) chạy vòng lặp dispatch lịch định kỳ — **cố ý không replicate** (dispatch lịch không được double-fire), tách biệt khỏi pool server API/UI scale ngang.
- Graceful shutdown: `stop_grace_period: 35s` trong compose và `terminationGracePeriodSeconds: {{ add .Values.server.gracefulTimeoutSeconds 5 }}` trong Helm đều set cao hơn `GRACEFUL_TIMEOUT_SECONDS` (mặc định 30s) để `ActiveTurnRegistry.shutdownAndWait` kịp drain turn đang chạy trước khi bị SIGKILL lúc rolling deploy/scale-down.

## 7. Trả lời trực tiếp 5 câu hỏi áp dụng cho TrueForge

| Câu hỏi | Trả lời |
|---|---|
| **a. SSE hay WebSocket?** | **SSE** (`text/event-stream`, qua `streamSSE` của Hono). 2 endpoint: `POST /sessions/{id}/turns` (trigger, tuỳ chọn stream) và `GET /sessions/{id}/turns/{turnId}/subscribe` (resubscribe riêng biệt) — tách biệt có chủ đích, cùng pattern với `agentscope` và `onyx`. |
| **b. Có "agent server" framework sẵn không?** | **Không — vòng lặp orchestration tự viết tay hoàn toàn** (`AgentThread`/`AgentThreadOrchestrator` trong `trueforge-core`, hỗ trợ cây sub-agent chạy đồng thời + gating tool-approval); thứ duy nhất dùng sẵn là **`streamText` của Vercel AI SDK**, chỉ đóng vai trò primitive stream model thô — không LangChain.js/LangGraph.js, không checkpointer framework. |
| **c. Reload giữa stream có xem tiếp được không?** | **Có — mạnh nhất trong 5 dự án/framework đã khảo sát** (ngang hoặc hơn Onyx). Disconnect không bao giờ huỷ turn (`stream.onAbort` chỉ dừng ghi vào socket chết, việc thực thi và persist event vẫn tiếp tục); client reload gọi endpoint `subscribe` riêng với `after_sequence_number` (hoặc dựa vào `Last-Event-ID`) để replay mọi event đã lỡ từ Redis Stream (hosted) hoặc in-memory store (local) rồi tiếp tục tail token live tới khi `turn.done`. |
| **d. State lưu ở đâu?** | **Tự quản lý hoàn toàn**: lịch sử bền vững (session, topology chuỗi turn, state theo turn/thread, log event/message append-only) nằm trong schema tự thiết kế qua Kysely, đối xứng giữa Postgres (hosted) và SQLite (local) — không có checkpointer framework nào. 1 Redis Stream có TTL riêng biệt (hoặc in-process store ở local mode) tồn tại thuần tuý làm buffer replay SSE live tạm thời, khác với log `session_event` Postgres/SQLite vĩnh viễn. |
| **e. Scale thế nào?** | **Scale ngang stateless theo thiết kế**: Service của Helm không có session affinity, HPA scale server Deployment theo CPU. Redis đóng 2 vai trò scale độc lập: (1) backing stream SSE resumable đọc được xuyên-replica để bất kỳ replica nào cũng phục vụ được request `subscribe`/reload, và (2) mang RPC request/reply (pub/sub + heartbeat + reply key poll bằng `GETDEL`) để 1 replica không sở hữu turn đang chạy vẫn forward được lệnh huỷ của user tới đúng replica sở hữu (`active_executor_id` trên row turn). Bản thân việc thực thi turn vẫn pin in-memory vào đúng 1 process khởi tạo nó; chỉ đường đọc/resume/huỷ được làm an toàn xuyên-replica qua Redis. 1 Deployment `controller` riêng biệt, cố ý chỉ 1 replica, chạy dispatch lịch tách biệt khỏi pool server scale ngang. |
