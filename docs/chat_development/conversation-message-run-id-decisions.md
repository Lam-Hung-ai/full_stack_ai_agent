# Quyết định ID: conversation, message và checkpoint

Cập nhật quyết định: **29/10/2026**, Asia/Ho_Chi_Minh.

Trạng thái: đã chốt hướng thiết kế; chưa triển khai adapter/backend/frontend/Redis. Bản này thay quyết định trước lưu current_run_id và yêu cầu stop theo invocation. Đọc cùng [API](chat-agent-api-contract.md), [ChatAgent](chat-agent-client-decisions.md) và [database](database-decisions.md).

## 1. Hai ID nghiệp vụ chính

| ID | Vai trò | Vòng đời |
|---|---|---|
| conversations.id | Danh tính chat, URL, sidebar, history và quyền | Suốt cuộc hội thoại |
| messages.id | Danh tính user message hoặc toàn bộ một lượt assistant | Assistant giữ nguyên qua pause/resume |

Mỗi conversation chỉ có một assistant pending/running/requires_action tối đa. Các conversation khác nhau được phép thực thi độc lập. Resume claim trạng thái nguyên tử, không cho hai execution của cùng assistant chạy đồng thời.

- Public AG-UI RunAgentInput.thread_id = conversations.id.
- Native LangGraph configurable.thread_id = assistant messages.id.
- Regenerate tạo assistant sibling mới, không dùng lại message terminal.
- Edit tạo user sibling mới và assistant mới, không sửa message terminal.

## 2. UUIDv7 thống nhất

Mọi ID do ứng dụng tự tạo ở frontend và backend dùng UUIDv7: conversation, user/assistant message, các bản ghi database, action và ID protocol do adapter mình chủ động tạo.

Frontend dùng helper UUIDv7 thống nhất, không dùng crypto.randomUUID() vì hàm đó tạo UUIDv4. String trong TypeScript phải được validate phù hợp ở backend; không dùng thời gian trong UUID thay permission hoặc parent topology.

ID do provider/LangGraph tự sinh như tool-call/checkpoint/interrupt giữ theo contract thư viện; không sửa ID làm hỏng tham chiếu.

## 3. runId chỉ thuộc AG-UI

RunAgentInput và lifecycle AG-UI vẫn có runId theo SDK. Adapter sử dụng UUIDv7 khi ứng dụng chủ động tạo ID này. Có thể có ID riêng cho mỗi lần start/resume để đáp ứng lifecycle protocol.

Ứng dụng không quản lý runId như một thực thể nghiệp vụ:

- Không nhận runId trong DTO gửi/edit/regenerate/resume/stop.
- Không lưu messages.metadata.current_run_id.
- Không thêm cột run_id hoặc bảng runs/attempts.
- Không dùng runId làm khóa nghiệp vụ Redis hoặc điều kiện chọn execution cho stop.
- runId có thể xuất hiện trong event protocol, kể cả event được transport buffer, nhưng không là execution ledger trong database.

Backend tạo RunAgentInput nội bộ từ DTO nghiệp vụ và dữ liệu authoritative. HttpAgent có thể tự dựng runId khi gọi pipeline; adapter cần kiểm chứng lifecycle với ID protocol server sử dụng. Không giả bỏ trường HTTP đã tự giải quyết tương thích SDK.

## 4. Ví dụ pause/resume

```text
Conversation C1
├─ User U1
└─ Assistant A1
    ├─ running
    ├─ requires_action -> hỏi người dùng
    ├─ running         -> resume cùng A1
    ├─ requires_action -> chờ duyệt tool
    └─ completed       -> resume và hoàn tất cùng A1

Regenerate từ U1 -> Assistant A2 (sibling A1)
```

Public thread luôn C1, checkpoint thread của A1 luôn A1. runId trong từng lifecycle protocol không thay danh tính A1 và không lưu riêng vào PostgreSQL.

Pending action/interrupt, response/actor và checkpoint pointers vẫn nằm trong metadata/content đã chốt giai đoạn 4. Bỏ current_run_id không bỏ các thông tin phục vụ resume.

## 5. Protocol message IDs trong content

Một SQL assistant A1 chứa bundle AG-UI Message[] gồm nhiều protocol messages như assistant text, tool result và activity user_interaction.

Mỗi protocol message có ID riêng; toolCallId nối lời gọi và kết quả tool. Không đổi tất cả ID thành A1 hoặc runId. Giữ tham chiếu ổn định khi lưu/hydrate/resume và remap khi copy conversation.

Activity trả lời người dùng giữ actor/response; context builder chuyển answered response thành HumanMessage đúng một lần.

## 6. Checkpoint và quyền

Adapter ánh xạ public conversation C1 sang native assistant A1 trước khi gọi saver, nhưng lifecycle AG-UI vẫn mang public C1. Native checkpoint_ns/checkpoint_id do runtime quản lý. Backend tự resolve từ assistant/action đã authorize, không nhận pointer tùy ý từ client.

Start dựng context theo parent path; resume lấy checkpoint của đúng assistant đang requires_action. Không lấy latest checkpoint toàn conversation thay cho pointer A1.

## 7. Stop theo assistant

```http
POST /api/v1/conversations/{conversationId}/messages/{assistantMessageId}/stop
```

Không body. Backend kiểm tra ownership/workspace và message thuộc conversation.

- pending/running: yêu cầu dừng assistant hiện tại, giữ partial content và kết thúc cancelled.
- requires_action: hủy toàn bộ lượt đang chờ, giữ content và vô hiệu pending pointer.
- Terminal: không chạy lại hoặc tác động assistant khác.

Stop nghĩa dừng assistant này kể cả vừa resume. Chấp nhận stop đến muộn có thể dừng lần resume hiện tại của cùng assistant. Regenerate có assistant ID mới nên stop A1 không dừng A2. Không có bảo đảm nhắm invocation cũ/mới.

HTTP abort/detach không phải lệnh stop. Từ chối tool nhưng tiếp tục assistant dùng resume chuẩn AG-UI.

## 8. Redis và lỗi mạng

Scope nghiệp vụ Redis/worker theo workspace/conversation/assistant message. Claim trạng thái bảo đảm một assistant active mỗi conversation; không có bảo đảm exactly-once hoặc recovery tự động chỉ nhờ các ID này.

Không expose cursor trong connect: luôn lấy snapshot mới nhất rồi tail nếu đang chạy. Sequence/watermark nội bộ dùng nối snapshot/tail, không dùng runId làm thứ tự.

Tạm bỏ requestId/Idempotency-Key và cơ chế dedup submit chuyên biệt; frontend không tự retry mutation, lỗi mạng thì đọc trạng thái/connect. Không hứa chống mọi submit trùng.

Phần nhiều SSE/chuyển conversation/hiển thị chéo UI tạm hoãn, chưa chốt chính sách chỉ giữ một stream hoặc quản lý nhiều instance.

## 9. Nguồn nghiên cứu và phạm vi kiểm chứng

Quan sát LibreChat trước đây: responseMessageId ổn định qua resume; native thread dùng conversationId cùng checkpoint namespace/generation scope riêng. Các field tên runId của SDK họ không mặc nhiên là AG-UI runId. Đây là tham khảo, không yêu cầu mình sao chép generation machinery.

[Proof checkpoint/AG-UI](../experiments/langgraph-action-checkpoints/README.md) đã thử pause/resume cùng message, lifecycle AG-UI, response có actor, cancel và concurrent answers. Proof từng dùng public thread_id = assistant ID; chưa kiểm chứng đầy đủ adapter C1 public/A1 native hoặc contract API/ChatAgent hiện tại.

SQL metadata là JSONB nên bỏ current_run_id khỏi contract không đòi xóa cột/bảng. Không sửa SQL, SDK proof hoặc code ứng dụng trong lần cập nhật tài liệu này. Không thêm crash recovery, execution audit hoặc bảng run.
