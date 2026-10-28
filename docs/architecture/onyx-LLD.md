# Low-Level Design — `onyx`

> Nguồn: `/home/lamhung/code/onyx`. Đọc kèm `onyx-HLD.md`.

## 1. Chat endpoint chính

```
POST /send-chat-message   (backend/onyx/server/query_and_chat/chat_backend.py:776-949)
```
Trả về `StreamingResponse(stream_generator(), media_type="text/event-stream")` (dòng 949), yield từng dòng NDJSON (`get_json_line(obj.model_dump())`) của 1 kiểu "Packet" dạng discriminated-union (`backend/onyx/server/query_and_chat/streaming_models.py`). Hỗ trợ cả `stream=False` để trả `ChatFullResponse` không-stream 1 lần. Có nhánh riêng cho **multi-model parallel streaming** — chạy song song 2-3 LLM.

Frontend tiêu thụ qua `fetch()` + tự parse stream thủ công (`sendMessage()` tại `web/src/app/app/services/lib.tsx:189-272`, `handleSSEStream`) — **không dùng `EventSource`, không dùng WebSocket**. Không có `websocket`/`WebSocket` nào trong toàn bộ đường đi chat.

## 2. Agent runtime — vòng lặp tự viết tay hoàn toàn, không LangGraph, không checkpointer

| File | Vai trò |
|---|---|
| `backend/onyx/chat/process_message.py` | Orchestrator cấp cao nhất (`build_chat_turn`, `_run_models`, `handle_stream_message_objects`) |
| `backend/onyx/chat/llm_loop.py::run_llm_loop` | Vòng lặp "Turn": dựng/cắt context, chạy tool call, lặp tới khi model ngừng gọi tool |
| `backend/onyx/chat/llm_step.py::run_llm_step` | 1 lần inference LLM đơn ("Step/Cycle"), stream token-by-token phần reasoning/answer/tool-call |
| `backend/onyx/deep_research/dr_loop.py` | Vòng lặp riêng, phức tạp hơn, cho chế độ "Deep Research" nhiều bước |

### Mô hình thực thi (theo `backend/onyx/chat/README.md:170-253`, xác nhận trong code)
- Mỗi model đích chạy trong 1 worker thread riêng (`ThreadPoolExecutor`).
- Mỗi worker ghi tuple `(model_idx, packet)` vào `merged_queue` dùng chung qua `Emitter` (`backend/onyx/chat/emitter.py`).
- Thread chính (`_run_models`, `process_message.py:1141`) drain queue và yield packet ra generator HTTP theo đúng thứ tự tới.
- **Không có `StateGraph`/checkpointer LangGraph nào cả.** State trong lúc chạy 1 turn sống trong `ChatStateContainer` (`backend/onyx/chat/chat_state.py`) — 1 accumulator thread-safe (token câu trả lời, token reasoning, tool call, citation) được đọc ra và ghi vào Postgres khi turn kết thúc.
- `thread_id`/session identity chính là `chat_session_id` thật của app (1 UUID của row chat-session) — **không có bug hardcode/default thread_id như `MemorySaver` trong `ai_agent`**.

## 3. Hành vi khi reload giữa stream — generation KHÔNG gắn với kết nối client

**Không có `await request.is_disconnected()` ở bất kỳ đâu trong backend** (grep toàn repo = 0 hit). Thứ duy nhất dừng được 1 generation đang chạy là **hành động rõ ràng của người dùng**:

```python
# backend/onyx/chat/process_message.py:1045-1048
def check_is_connected() -> bool:
    return not is_stop_requested(
        chat_session_id, cache, stream_id=processing_stream_id
    )
```

`is_stop_requested` (`backend/onyx/chat/stop_signal_checker.py`) chỉ kiểm tra 1 cờ trong cache, được set bởi:

```python
# backend/onyx/server/query_and_chat/chat_backend.py:1376-1399
@router.post("/stop-chat-session/{chat_session_id}")
def stop_chat_session(...):
    ...
    request_stop(chat_session_id, cache, stream_id=target_stream_id)
```

Tức là 1 **nút Stop chuyên biệt**, không phải phát hiện disconnect TCP/browser. Theo `backend/onyx/chat/README.md:214-222`: "Vòng lặp drain trong `_run_models` kiểm tra `check_is_connected()` mỗi 50ms (khi queue timeout)... Khi disconnect, vòng lặp drain lưu state dở dang cho mọi model, yield `OverallStop(stop_reason="user_cancelled")`, rồi return... Các worker đã hoàn thành thành công trước đó sẽ tự hoàn tất (persist câu trả lời) nếu vòng lặp drain thoát trước khi tới path hoàn thành bình thường."

**Hệ quả**: nếu browser chỉ reload/đóng mà không bấm Stop, **generation KHÔNG bị huỷ** — worker thread tiếp tục chạy độc lập hoàn toàn với việc có ai đang đọc `StreamingResponse` generator hay không, và câu trả lời cuối được persist vào Postgres bình thường khi LLM sinh xong. Chỉ khi có yêu cầu Stop rõ ràng mới dẫn tới việc persist sớm/dở dang.

## 4. Cơ chế Resume Stream — thiết kế cấp sản phẩm, xuyên pod

Onyx xây đúng kiểu cơ chế resumable-stream (giống pattern của `agentscope` Agent Service) nhưng **là tính năng chính thức tích hợp sẵn, không phải add-on tuỳ chọn**:

### a) Writer
`StreamBufferWriter` (`backend/onyx/chat/stream_buffer.py:64-196`) — khi run phát ra dòng NDJSON, batch và nén zlib thành các chunk đánh số thứ tự (`chatstream_<session>_<stream_id>:<n>`) vào cache dùng chung (Redis hoặc Postgres-cache backend), cộng 1 key `meta` (`chunk_count`, `done`, `truncated`) có TTL (`CHAT_STREAM_BUFFER_TTL_S` khi đang live, `CHAT_STREAM_BUFFER_DONE_TTL_S` ngắn hơn sau khi hoàn thành). Docstring file ghi rõ (dòng 1-10): **"bất kỳ pod api-server nào cũng có thể replay và tail 1 run đang chạy"**.

### b) "Processing fence"
`backend/onyx/chat/chat_processing_checker.py` — `set_processing_status`/`is_chat_session_processing`/`get_processing_stream_id` lưu, theo từng chat session, việc nó có đang xử lý không và `stream_id` nào đang active (`FENCE_TTL = 30 phút`).

### c) Resume endpoint
```python
# backend/onyx/server/query_and_chat/chat_backend.py:1296-1373
@router.get("/chat-session/{session_id}/resume-stream")
def resume_chat_stream(session_id: UUID, cursor: int = Query(0, ge=0), ...):
    ...
    stream_id = get_processing_stream_id(session_id, cache)
    if stream_id is None or not has_stream_buffer(cache, session_id, stream_id):
        raise OnyxError(OnyxErrorCode.NOT_FOUND, "No resumable stream for this chat session")

    def stream_buffered_run():
        chunk_cursor = cursor
        while True:
            read = read_stream_chunks(cache, session_id, stream_id, chunk_cursor, ...)
            if read is None or read.gap:
                return  # client fallback: fetch lại session đã persist
            if read.blocks:
                yield "".join(read.blocks); chunk_cursor = read.next_cursor; continue
            if read.done:
                return
            ...  # còn lại: poll/heartbeat và tiếp tục tail live
    return StreamingResponse(stream_buffered_run(), media_type="text/event-stream")
```
Đây là **GET reconnect dựa trên cursor**, tách biệt khỏi `POST` ban đầu — đúng pattern của AgentScope, nhưng được nhúng vào sản phẩm chính của Onyx chứ không phải tính năng tuỳ chọn. Nếu chuỗi bị gãy/evicted (`gap=True`), client fallback về việc fetch lại các row `ChatMessage` đã persist — **luôn đầy đủ** vì generation chưa bao giờ bị huỷ bởi việc disconnect (xem mục 3).

### d) Nối với frontend
`GET /get-chat-session/{id}` trả thêm field `current_stream: {stream_id}` (`chat_backend.py:433-467`, `models.py:286`) khi session đang generate dở. Lúc load session, `web/src/hooks/useChatSessionController.ts:264-367` (`resumeInFlightRun`) kiểm tra `chatSession.current_stream`, nếu có thì gọi `resumeStream(sessionId, 0, signal)` (`web/src/app/app/services/lib.tsx`, `GET .../resume-stream?cursor=`), replay packet đã buffer vào message tree theo thời gian thực, rồi khi xong fetch lại `/get-chat-session/{id}` để chốt state cuối (citation, document).

→ **Reload giữa stream VẪN cho người dùng xem tiếp animation token-by-token live**, không chỉ thấy câu trả lời cuối — đây là đảm bảo mạnh hơn hẳn so với cả 4 dự án/framework còn lại.

### e) Trường trạng thái trong DB
Không có cột `status` enum tường minh (vd `streaming`/`completed`) trên `ChatMessage` (`backend/onyx/db/models.py:3401+`) — tín hiệu "đang xử lý" được giữ cố ý ở cache tạm (`chat_processing_checker.py`), không phải ở DB, vì bản chất đây là state xuyên-pod/tạm thời; row DB (`message`, `citations`, `tool_calls`, `error`, ...) mới là nguồn sự thật bền vững khi 1 turn kết thúc hoặc bị dừng.

## 5. State lưu ở đâu — 100% self-managed Postgres ORM, không checkpointer

- Lịch sử hội thoại: model SQLAlchemy `ChatSession` và `ChatMessage` (`backend/onyx/db/models.py:3298-3538`), cấu trúc cây cha/con (`parent_message_id`/`latest_child_message_id`) hỗ trợ edit/branch, persist qua `onyx/chat/save_chat.py`. Đây là **nguồn sự thật duy nhất** dùng để dựng lại lịch sử khi load trang (`GET /get-chat-session/{session_id}`, `session_loading.py`).
- Không có checkpointer LangGraph/LangChain nào cả — state tạm thời trong lượt là `ChatStateContainer` (accumulator thread-safe, không persist giữa chừng trừ qua stream buffer dùng cho UI replay), và state bền vững được ghi thẳng vào Postgres bằng code của app khi turn kết thúc (hoặc khi dừng rõ ràng).

## 6. Scaling — chi tiết

- **API server**: Helm chart (`deployment/helm/charts/onyx/templates/api-deployment.yaml`, `api-service.yaml`, `api-hpa.yaml`) — `Service` kiểu `ClusterIP` thường, **không có `sessionAffinity`/sticky-session nào**; `HorizontalPodAutoscaler` với `minReplicas`/`maxReplicas` (mặc định trong `values.yaml`: `minReplicas: 1, maxReplicas: 100`, target CPU/memory 80%), cộng đường thay thế qua KEDA `ScaledObject`. Tính stateless này **chỉ an toàn vì** state của run đang chạy (stream buffer + processing fence) nằm ở cache dùng chung (Redis/Postgres), không phải bộ nhớ pod — bất kỳ pod nào cũng phục vụ được `resume-stream` cho bất kỳ session nào.
- **Nginx** (`deployment/data/nginx/app.conf.template*.conf`): `upstream api_server { server ...:8080 fail_timeout=0; }` đơn giản — **không có `ip_hash`, không có sticky directive nào** (grep `ip_hash|sticky` = 0 hit ngoài các match `upstream` không liên quan). Xác nhận kiến trúc không cần/không dùng sticky session.
- **Celery worker**: nhiều pool scale độc lập, mỗi pool có Deployment + HPA + KEDA `ScaledObject` riêng (`celery-worker-{primary,light,heavy,docfetching,docprocessing,monitoring,scheduled-tasks,user-file-processing}-{hpa,scaledobject}.yaml`), cộng `celery-beat.yaml` cho lịch. Mặc định `replicaCount: 1` với autoscaling bật theo từng pool (vd worker "light" `minReplicas: 1, maxReplicas: 10`).
- **Postgres**: Helm dùng chart kiểu operator CloudNativePG (`deployment/helm/charts/onyx-cnpg-crds/`, `templates/postgres-cluster.yaml`, `instances: {{ .Values.postgresql.cluster.instances | default 1 }}`) — số instance HA do operator quản lý, cấu hình được (mặc định 1). Triển khai multi-tenant còn shard qua nhiều Postgres instance (`shard_routing.py`/`shard_registry.py`, schema-per-tenant, cache tenant→shard).
- **Redis**: Docker Compose dùng 1 container `redis:7.4-alpine` (dev/mặc định, không HA). Module Terraform AWS (`deployment/terraform/modules/aws/redis/main.tf`) dựng `aws_elasticache_replication_group` với `num_cache_clusters = 1` mặc định (1 node, không auto-failover trừ khi cấu hình thêm — dù cấu trúc module cho phép đổi).
- **Vector/document index (OpenSearch)**: module Terraform AWS (`deployment/terraform/modules/aws/opensearch/main.tf`) hỗ trợ `instance_count` và `zone_awareness_enabled`/`zone_awareness_config` cho cluster multi-AZ HA — cấu hình được, **không giới hạn single-node** như Redis mặc định.

## 7. Trả lời trực tiếp 5 câu hỏi áp dụng cho Onyx

| Câu hỏi | Trả lời |
|---|---|
| **a. SSE hay WebSocket?** | **SSE** — `StreamingResponse` HTTP chunked với packet NDJSON (`media_type="text/event-stream"`) qua `POST /send-chat-message`, tiêu thụ bằng `fetch()` + tự đọc stream thủ công ở frontend (không phải `EventSource` gốc, không phải WebSocket). |
| **b. Có "LangGraph agent server" không?** | **Không — app thuần với vòng lặp agent tự viết tay hoàn toàn** (`run_llm_loop`/`run_llm_step` trong `backend/onyx/chat/`, cộng `dr_loop.py` riêng cho deep research). LangGraph không xuất hiện ở đâu trong codebase; `langchain-core` chỉ xuất hiện ở đúng 1 file để import 1 type duy nhất. |
| **c. Reload giữa stream có xem tiếp được không?** | **Có.** Không có phát hiện disconnect nào cả (generation chỉ dừng khi gọi API Stop rõ ràng), nên backend luôn chạy tiếp và persist đầy đủ câu trả lời bất kể client còn kết nối hay không; cộng thêm 1 buffer replay stream xuyên-pod (dựa trên cache Redis/Postgres, đánh địa chỉ theo cursor) cho phép client reload gọi `GET /chat-session/{id}/resume-stream?cursor=N` để phát lại token đã lỡ rồi tail tiếp phần còn lại của generation đang chạy live — **thiết kế resumable-stream mạnh nhất trong 5 dự án/framework đã khảo sát**. |
| **d. State lưu ở đâu?** | **Tự quản lý hoàn toàn**: lịch sử hội thoại bền vững nằm trong Postgres qua model ORM SQLAlchemy `ChatSession`/`ChatMessage` của chính app (nguồn sự thật để dựng lại khi load trang); **không có checkpointer LangGraph/LangChain nào**. State trong lúc chạy 1 turn là `ChatStateContainer` tạm thời trong process, cộng stream buffer cache (Redis/Postgres) chỉ dùng để UI replay/resume, không phải nguồn sự thật của hệ thống. |
| **e. Scale thế nào?** | **Ngang, stateless hoàn toàn**: pod API server sau load balancer/Service không sticky, tự động scale qua HPA/KEDA (mặc định tới 100 replica) vì mọi điều phối xuyên-request (tín hiệu stop, processing fence, buffer replay stream) nằm ở cache ngoài dùng chung (Redis hoặc Postgres-cache cho bản "lite"), không ở bộ nhớ pod; Celery được chia thành nhiều pool worker tự scale độc lập; Postgres (operator CloudNativePG, có thể shard theo tenant) và OpenSearch (hỗ trợ multi-AZ) có thể HA, còn Redis/ElastiCache mặc định là single-node trừ khi cấu hình lại. |
