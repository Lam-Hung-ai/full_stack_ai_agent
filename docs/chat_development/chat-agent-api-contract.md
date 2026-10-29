# API chat AG-UI theo database đã chốt

Cập nhật: **29/10/2026**, Asia/Ho_Chi_Minh. Đây là contract để triển khai/refactor, chưa khẳng định các endpoint dưới đây đã tồn tại.

Dùng FastAPI custom, LangGraph OSS, `ag_ui_langgraph.LangGraphAgent`, EventEncoder và frontend AG-UI hiện có. Không dùng CopilotKit runtime/SDK hoặc LangGraph Agent Server. Chỉ tham khảo cách chia run/connect/stop từ CopilotKit.

Nguồn chuẩn: [database](database-decisions.md), [ID](conversation-message-run-id-decisions.md), [kiến trúc](agent-chat-architecture.md). Không tạo bảng run/attempt, không yêu cầu conversation revision/title_source hoặc native thread theo branch.

## 1. Nhóm API

Các path tương đối với API base; không tạo hai implementation submit cùng thực thi một input.

| Method/path | Trách nhiệm |
|---|---|
| GET /info | Agent cố định và capabilities thực sự đã triển khai |
| POST /threads | Tạo conversation trong workspace đã authorize |
| GET /threads | Sidebar theo user/workspace, pin/folder/archive, phân trang |
| GET /threads/{threadId} | Metadata và summary assistant active nếu có |
| PATCH /threads/{threadId} | Rename/pin/archive/folder theo allowlist backend |
| DELETE /threads/{threadId} | Soft-delete theo policy; revoke shares nguồn |
| GET /threads/{threadId}/messages | Lịch sử đúng parent path, cursor theo contract repository |
| POST /agent/{agentId}/run | Start hoặc resume hợp lệ, trả AG-UI SSE |
| POST /agent/{agentId}/connect | Read-only snapshot + tail, trả AG-UI SSE |
| POST /agent/{agentId}/stop/{threadId} | Stop đúng message/invocation, JSON acknowledgement |
| GET /health/live, /health/ready | Trạng thái service |

agentId là registry key cấu hình, không phải tenant hoặc danh tính execution. Upload/share/copy dùng service theo database đã chốt; path chi tiết bổ sung khi triển khai feature, không tự chốt route ở tài liệu này.

## 2. ID trên wire

- threadId = conversations.id, ổn định suốt chat.
- User/assistant SQL message có ID riêng.
- runId riêng từng invocation start/resume; khác assistant message ID kể cả lần đầu.
- Native checkpoint thread_id = assistant message ID; adapter ánh xạ public/native thread.
- Protocol messageId/toolCallId trong content/events giữ riêng.
- metadata.current_run_id giữ invocation hiện tại/gần nhất, không phải bảng run hoặc đầy đủ audit history.

Ví dụ RunAgentInput chuẩn:

```json
{
  "threadId": "conversation-uuid",
  "runId": "invocation-uuid",
  "state": {},
  "messages": [{"id":"user-message-uuid","role":"user","content":"Xin chào"}],
  "tools": [],
  "context": [],
  "forwardedProps": {}
}
```

Parent/target assistant/action binding phải được backend resolve/validate. Tên extension truyền thêm chúng trong request sẽ chốt với adapter; không dựa browser-supplied state để ghi đè canonical history hoặc mở tool.

## 3. Start và retry

POST run trả SSE trong chính response, không yêu cầu browser chuyển sang một endpoint khác sau JSON ACK. Input được auth/authorize, reconcile stable message IDs và commit placeholder trước khi xác nhận đã nhận.

Worker consume LangGraphAgent độc lập HTTP subscriber. API subscribe shared output và encode bằng EventEncoder; không có mapper native graph-to-AG-UI thứ hai.

Retry cùng operation dùng lại identity và payload đã chấp nhận; khác payload cùng identity phải conflict. Duplicate retry không tạo user/assistant/invocation mới. Regenerate là operation mới, tạo sibling assistant mới.

Cơ chế idempotency key/hash/lifetime và binding với runId chưa triển khai; không tuyên bố current_run_id hoặc active unique đã tự giải quyết toàn bộ. Không tự thêm bảng run để triển khai API này.

## 4. Pause/resume

- Graph interrupt: lưu partial content, action metadata và checkpoint/writes cùng transaction; SQL message requires_action.
- Invocation có thể kết thúc bằng AG-UI interrupt outcome nhưng message chưa completed.
- Người dùng trả lời gửi action_id/response qua phần input resume được SDK đã pin hỗ trợ; backend validate action và quyền hiện tại trước claim.
- Claim chuyển running và current_run_id mới nguyên tử; response/activity được lưu trước execution.
- Runtime mới resume checkpoint cùng assistant; không tạo SQL user message riêng cho câu trả lời bổ sung.
- Pause tiếp tạo action_id mới. Không cho retry action cũ thực thi thêm lần nữa.
- Hủy action làm message cancelled, giữ lịch sử và bỏ pending pointer. Duyệt từ chối tool có thể resume để assistant giải thích và completed.

Payload resume chuẩn/extension và action_id binding phải được nối với frontend khi triển khai. Không nhận checkpoint pointer hoặc credential tùy ý từ client.

## 5. Connect/reload

POST connect không gọi LangGraphAgent.run()/LLM/tool. Public threadId vẫn là conversation, backend resolve message/lượt active.

1. Kiểm tra user/workspace/quyền đọc và scope.
2. Đọc history PostgreSQL và live projection Redis theo contract nhất quán.
3. Gửi accumulated snapshot kèm watermark, rồi tail sau watermark.
4. Giữ stable message IDs; không append prefix hai lần hoặc END active message sớm.
5. Gap/epoch đổi thì reset/hydrate phù hợp, không bỏ qua phần thiếu.

Nếu SDK cần runId cho request attach, đó là transport identity, không đổi execution current_run_id. Chỉ một consumer text cho chat đang chọn mỗi tab; detach consumer cũ khi chuyển chat. Không có global user feed hoặc public /realtime/* trong scope.

Redis buffer còn thì hỗ trợ reconnect giữa câu. Không có cam kết cứu mọi token sau mất toàn bộ Redis/worker; PostgreSQL content được lưu ở các mốc terminal/pause. Proof mới kiểm chứng reload sau pause, chưa phải HTTP/Redis reconnect end-to-end.

## 6. Stop

Ví dụ body cho path chứa public conversation threadId:

```json
{"messageId":"assistant-message-uuid","runId":"current-invocation-uuid"}
```

Xác minh ownership/scope, message thuộc conversation và exact current_run_id, rồi gửi tín hiệu đúng worker. Lệnh cũ không được dừng lượt resume/regenerate mới. HTTP abort/detach không tự cancel.

Acknowledgement chỉ nói request stop đã được nhận/chấp nhận hoặc lượt đã terminal; không báo đã dừng chỉ vì đã gửi tín hiệu. Trạng thái message cuối chỉ là completed/failed/cancelled; không thêm SQL cancel_requested/stopping ở tài liệu này. Durable cancel-intent/Redis coordination cần implementation contract riêng.

## 7. Conversation và history DTO

API có thể dùng name cho title, boolean archived/pinned suy từ timestamp, folderId từ folder_id. Không expose ORM/native checkpoint trực tiếp.

- Không bắt If-Match bằng conversation revision đã bị bỏ. Cơ chế precondition cho rename/auto-title chưa chốt thay thế.
- Backend chỉ nhận các trường sửa được; không cho đổi owner/workspace hoặc current_run_id qua PATCH chung.
- Sidebar theo user/workspace, keyset (updated_at,id); pin/folder theo index đã chốt.
- History trả AG-UI shapes sau khi reconcile bundle và branch path. Không coi một SQL assistant row luôn bằng đúng một protocol message.
- Activity user_interaction phải render response là lời user; context builder chuyển answered response thành HumanMessage đúng một lần.
- Archive không xóa chat; folder một cấp và không cấp quyền chat.
- Soft-delete chặn đọc/start mới và revoke shares nguồn. Backend xử lý execution đang sống theo workflow cần tích hợp; chưa có hard purge/export toàn hệ thống.

## 8. Metadata, title và quyền

Title event có thể dùng CUSTOM thread.updated khi stream còn mở; sau đóng stream, đọc lại metadata từ GET thread/list. Không thêm global SSE chỉ vì title. Auto-title phải tránh ghi đè user rename nhưng cơ chế thay source/revision cần thiết kế trước khi bật.

List/history/start/resume/connect/stop/download/share/copy đều kiểm tra scope. Owner/Admin/Superuser không có bypass private chat. Role tool, source/file scope và identity provider được xác định ở server; UUID không thay authorization.

## 9. Nghiệm thu implementation

- Retry input không nhân message/execution; regenerate tạo sibling mới.
- Thread public và native checkpoint mapping đúng; mọi lifecycle event thuộc đúng C1/Rn.
- Connect/replay không gọi agent, snapshot/tail không mất hoặc trùng prefix.
- Detached worker tiếp tục khi subscriber rời; stop nhắm đúng message/run.
- Pending action sống qua reload; response/permission/action_id được revalidate, duplicate submit chỉ một claim.
- Terminal outcome chỉ phát sau commit kết quả; interrupt không hiểu nhầm completed.
- Không đưa raw state/secret vào public stream hoặc metadata có thể bị client sửa.

Chưa triển khai các API mới. DDL và proof không thay HTTP auth, Redis reconnect, real provider hoặc load tests. Các feature RAG/memory/action receipts/audit nâng cao nằm trong [use cases](chat-use-cases-and-organization-access.md), chưa tự có trong schema hiện tại.
