# Kiến trúc chat theo database đã chốt

Cập nhật: **29/10/2026**, Asia/Ho_Chi_Minh. Tài liệu đích để chỉnh backend, chưa mô tả một hệ thống đã triển khai đầy đủ.

Nguồn chuẩn: [database giai đoạn 1–4](database-decisions.md), [quy ước ID](conversation-message-run-id-decisions.md), [API](chat-agent-api-contract.md). Các sơ đồ cũ về run/attempt/journal bắt buộc, native thread theo branch và global user feed đã được thay bằng phạm vi dưới đây.

Chi tiết áp dụng nguồn web để mở rộng storage, pool và execution: [thiết kế lưu trữ và scale](production-data-storage-design.md). Các đề xuất vận hành trong đó chưa là thay đổi schema đã duyệt.

## 1. Component

| Component | Trách nhiệm |
|---|---|
| Frontend AG-UI hiện có | Sidebar/history, nhánh per-tab, messages, activity hỏi–đáp, attach/detach/stop |
| FastAPI custom | Auth/authorization, lifecycle conversation/message, start/resume/connect/stop |
| Execution worker/task | Sở hữu coroutine agent, không phụ thuộc HTTP subscriber |
| LangGraphAgent | Một nguồn chuyển native graph events sang AG-UI; không dùng CopilotKit runtime |
| EventEncoder | Encode BaseEvent thành SSE, không tự tạo graph semantics |
| PostgreSQL chat_app | Dữ liệu nghiệp vụ và lịch sử bền vững theo database đã chốt |
| PostgreSQL langgraph_checkpoints | Checkpoint/writes do SDK quản lý, chỉ export khi pause |
| Redis | Shared accumulated view, event tail, tín hiệu và điều phối live theo contract backend |
| Object storage | Byte file private, gateway kiểm tra quyền trước tải |
| Langfuse | Tracing/token/chi phí |

Không có bảng run/attempt hoặc native Store trong baseline hiện tại. Có thể tách API/worker/gateway theo tải; số pod, queue implementation, ownership/fencing và connection budget chưa được benchmark hoặc chốt chi tiết.

## 2. ID và vòng đời

```text
Conversation C1 = public AG-UI threadId
  User U1
  Assistant A1 = logical response + native checkpoint thread
    Start R1 -> pause -> Resume R2 -> pause -> Resume R3 -> terminal
```

AG-UI runId chỉ phục vụ adapter/protocol; không lưu metadata.current_run_id hoặc dùng làm khóa nghiệp vụ. Regenerate tạo A2. Không dùng runId làm message ID hoặc cursor event. Adapter phải giữ public C1 trong lifecycle events nhưng bind saver theo A1.

## 3. Nhận câu hỏi và sinh câu trả lời

1. Xác thực user/workspace, kiểm tra parent và quyền; không tin tenant/tool/context từ browser.
2. Lưu user và placeholder assistant, tuân transaction gắn file và user completed trước commit.
3. Claim trạng thái assistant nguyên tử; chỉ một assistant pending/running/requires_action trong conversation.
4. Dựng context từ parent path đã lưu, quyền/skill/tool hiện tại; runtime mới cho invocation.
5. Worker consume LangGraphAgent.run(); HTTP chỉ subscribe output. Không consume thêm native graph stream song song để tự tạo một bộ events khác.
6. Tích lũy text/tools/public state trong Redis; publish bằng EventEncoder ở gateway.
7. Hoàn tất/lỗi bắt được/stop: transaction ghi content/attachments/file links/status cuối trước khi thông báo kết quả durable.

Không update JSONB mỗi token. Hiện tạm bỏ requestId/Idempotency-Key, không tự retry mutation; đọc trạng thái và connect khi lỗi mạng theo [API contract](chat-agent-api-contract.md). Claim/writer ownership vẫn cần backend hiện thực; unique một active assistant không tự chống request trùng sau terminal.

## 4. Pause/resume

Interrupt -> lưu checkpoint/writes + content + requires_action + metadata trong cùng transaction -> nhả invocation. Redis không phải bản duy nhất của pending action.

Người dùng trả lời/duyệt -> kiểm tra action_id/quyền/graph_version -> claim chuyển running, lưu response -> dựng graph mới -> resume native checkpoint của cùng assistant.

Activity user_interaction giữ tác giả/response để render và rebuild context như HumanMessage. Từ chối tool không mặc nhiên hủy cả lượt. Hủy action thì cancelled, giữ partial và vô hiệu pending pointer.

## 5. Reconnect và nhiều tab

- Connect chỉ đọc, không enqueue/start/resume agent.
- Redis view + watermark + tail cần được đọc/apply nhất quán, giữ protocol message IDs, không kết thúc message chỉ vì vừa gửi prefix.
- Cursor gap/Redis reset phải có reset/hydrate policy; không âm thầm nối suffix vào prefix thiếu.
- History PostgreSQL giữ các mốc terminal/pause. Không giả định checkpoint giữ text node đang sinh.
- Nếu mất toàn bộ Redis trước mốc lưu, partial có thể mất; không có journal SQL bảo đảm mọi token đã gửi.
- Tab tự giữ nhánh đang xem; request gửi parent tường minh, không đổi context của invocation đã bắt đầu.
- Chuyển workspace không thay scope của message/execution cũ. Quyền đọc/stream phải được kiểm tra theo scope server.

Shared Redis làm nền cho reconnect qua pod khác; chưa có implementation/test multi-pod end-to-end. Không suy ra detached execution hoặc snapshot+tail chỉ vì đã dùng LangGraphAgent.

## 6. Stop, lỗi và giới hạn

Stop nhắm conversation + assistant messageId, không body/runId; dừng lượt assistant hiện tại kể cả vừa resume. Chấp nhận lệnh muộn có thể dừng lần resume mới của cùng assistant. Detach/browser abort không phải stop.

Worker xử lý lỗi/dừng có handler ghi partial. Worker chết bất ngờ, hoặc chết sau claim trước finalize, chưa có auto-recovery; có thể còn message pending/running. Không thêm attempt/recovery/journal như chức năng mặc định.

Graph version đang chờ cần tương thích để resume; chưa có migration runtime. Checkpoint không cấp quyền, không chống external side effect lặp một cách tổng quát.

## 7. Tác vụ nền và metadata

Title có fallback; tên user không được tác vụ background ghi đè. Cơ chế conditional update thay source/revision chưa được chốt, không đưa cột đã bỏ trở lại bằng sơ đồ này.

Token/chi phí gửi Langfuse với user/session/workspace/message mapping. Tool/skill registry ở code; org dùng RBAC, cá nhân dùng allowlist. RAG/memory/credential riêng/receipt/audit/purge là feature sau, không phải dependency bắt buộc để chạy chat hiện tại.

## 8. Kiểm chứng còn cần khi tích hợp

Proof đã thử sync, async/AG-UI, pause/resume process mới, SDK validation, RBAC revoke và duplicate answer. Chưa có public/native thread mapping với frontend, Redis connect dưới tải, HTTP auth/stop, provider LLM/MCP/S3 thực hoặc load test.

Chi tiết bằng chứng: [checkpoint experiments](../experiments/langgraph-action-checkpoints/README.md). Các giới hạn nằm trong [bản database đã chốt](database-decisions.md); tài liệu này không bổ sung schema mới.
