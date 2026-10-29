# Quyết định ID: conversation, message, AG-UI run và checkpoint

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

Trạng thái: **đã được người dùng đồng ý**. Đây là hợp đồng để điều chỉnh backend/frontend, PostgreSQL metadata và Redis. Chưa triển khai adapter/API ứng dụng hoặc đổi schema trong lần ghi tài liệu này.

Tài liệu này ưu tiên hơn các đoạn đồng nhất conversation/checkpointer thread hoặc run/message trong tài liệu cũ. Database nền giữ các quyết định [giai đoạn 1–4](../database_decisions/README.md); không thêm bảng runs/attempts/mapping chỉ để chứa các ID dưới đây.

## 1. Ba danh tính chính

| Danh tính | Ý nghĩa | Vòng đời |
|---|---|---|
| `conversations.id` | Một cuộc hội thoại, dùng trong sidebar, URL, history, share và quyền truy cập | Giữ nguyên trong suốt chat |
| `messages.id` | Một câu hỏi user hoặc toàn bộ một lượt trả lời assistant | Giữ nguyên khi assistant pause/resume |
| AG-UI `run_id` | Một lần start/resume tạo luồng event có lifecycle riêng | Mới cho mỗi lần thực thi mới; retry cùng request không tạo lại |

Các ID được dùng độc lập, không cố ý gán cùng giá trị. Tài nguyên database dùng UUID như schema đã chốt; trên AG-UI/API biểu diễn thành string. Dùng cùng kiểu UUID không có nghĩa cùng thực thể.

- **`RunAgentInput.thread_id = conversations.id`.**
- **`RunAgentInput.run_id` khác `messages.id`**, kể cả lần chạy đầu tiên.
- Một assistant message có thể tương ứng nhiều run_id vì có nhiều lần pause/resume.
- User message có ID riêng, không đại diện một lần agent execution.

Không thêm một lớp logical run riêng: message assistant chính là danh tính bền vững của lượt trả lời trong sản phẩm hiện tại.

## 2. Ví dụ trọn vòng đời

```text
Conversation C1
├─ User U1
└─ Assistant A1
    ├─ Start  R1 -> đang xử lý
    ├─ Pause    -> hỏi người dùng, A1.requires_action
    ├─ Resume R2 -> xử lý tiếp rồi chờ duyệt tool
    ├─ Resume R3 -> hoàn tất A1
    └─ A1.completed

Regenerate từ U1
└─ Assistant A2
    └─ Start R4 -> A2.completed
```

| Lần thực thi | AG-UI thread_id | AG-UI run_id | SQL assistant message | Native checkpoint thread_id |
|---|---|---|---|---|
| Start đầu | C1 | R1 | A1 | A1 |
| Resume câu hỏi | C1 | R2 | A1 | A1 |
| Resume duyệt tool | C1 | R3 | A1 | A1 |
| Regenerate | C1 | R4 | A2 | A2 |

Pause không tạo conversation/message assistant mới. Regenerate tạo sibling mới cùng parent U1, giữ nguyên A1 và nội dung cũ. Các run R1/R2/R3 không phải ba dòng message.

## 3. AG-UI Message ID bên trong content

`messages.content` là bundle đầy đủ AG-UI Message[] cho một logical UI message đã chốt ở giai đoạn 2. Một dòng A1 có thể chứa nhiều protocol messages:

```text
SQL message A1
├─ AG-UI assistant P1: text + tool call
├─ AG-UI tool      P2: kết quả tool
├─ AG-UI activity  P3: người dùng trả lời câu hỏi
└─ AG-UI assistant P4: phần trả lời tiếp
```

P1/P2/P3/P4 có ID riêng. `TEXT_MESSAGE_START.messageId` dùng ID protocol message tương ứng; không tự đổi mọi messageId thành run_id hoặc A1.

Giữ stable protocol IDs khi snapshot/reconnect/resume để client merge đúng và không nối lặp. Tool call ID cũng là danh tính riêng, nối toolCalls với toolCallId; không dùng run_id thay thế.

Activity user_interaction ghi rõ actor và response; khi dựng model context, response đã answered được ánh xạ thành HumanMessage, không diễn giải thành lời assistant.

## 4. Hai nghĩa thread_id cần ánh xạ rõ

| Trường | Giá trị | Mục đích |
|---|---|---|
| Public AG-UI `thread_id` | Conversation C1 | Frontend mở và theo dõi đúng cuộc hội thoại |
| Native LangGraph saver `configurable.thread_id` | Assistant message A1 | Cách ly checkpoint của lượt trả lời đang pause/resume |
| Native `checkpoint_ns` | Namespace graph, root thường rỗng | Phân biệt graph/subgraph theo contract của runtime |
| Native `checkpoint_id` | ID checkpoint do LangGraph quản lý | Chọn đúng state để tiếp tục |

Backend/adapter phải chuyển public C1 sang native A1 trước khi gọi graph/saver, đồng thời giữ event trả frontend thuộc public thread C1 và run hiện tại. Không lấy latest checkpoint toàn conversation rồi coi đó là state của A1.

Khi start lượt mới, dựng context từ parent path đã authorize. Khi resume action, nạp state từ checkpoint pointer của A1. Việc trùng tên thread_id ở hai API không cho phép truyền nguyên một giá trị qua mọi lớp mà không xét scope.

Client không được tùy ý quyết định namespace/checkpoint pointer. Backend resolve từ message và metadata thuộc conversation đã xác thực. UUID không phải bằng chứng quyền.

## 5. PostgreSQL giữ gì

Không thêm bảng runs. Giữ schema message có metadata ở giai đoạn 4:

```json
{
  "current_run_id": "R2",
  "pending_action": {
    "action_id": "Q1",
    "state": "resuming",
    "graph_version": "graph-v1",
    "expires_at": null,
    "checkpoint": {
      "thread_id": "A1",
      "checkpoint_ns": "",
      "checkpoint_id": "CP1"
    },
    "interrupts": [
      {"interrupt_id": "I1", "payload": {"kind": "user_question"}}
    ],
    "response": "CSV"
  }
}
```

Đây là ví dụ khi R2 đã claim action Q1; không phải JSON đầy đủ của mọi trạng thái.

- `messages.id = A1`: cố định.
- `metadata.current_run_id`: run_id của lần thực thi hiện tại/gần nhất. Chỉ backend cập nhật; thay đổi trong transaction claim/start.
- `pending_action.action_id`: lần chờ cụ thể, khác run_id. Pause tiếp tạo action mới.
- `pending_action.checkpoint.thread_id = A1`: phạm vi state thực thi, không phải public C1.
- Response/decision đã giải quyết lưu theo contract metadata.actions/activity của giai đoạn 4.
- Terminal A1 vẫn bất biến; không đổi current_run_id của A1 sau completed/failed/cancelled. Regenerate tạo A2.

current_run_id không tự là lịch sử đầy đủ mọi invocation. Nếu cần audit toàn bộ hoặc recovery nhiều attempt sau này, phải thiết kế riêng theo nhu cầu; không hứa JSON này thay mọi dạng execution ledger.

## 6. Start, pause, resume và reconnect

### Start

1. Authenticate user/workspace/conversation và kiểm tra parent tường minh.
2. Tạo user U1, placeholder assistant A1 và nhận diện request theo cơ chế idempotency sẽ triển khai.
3. Run R1 độc lập với A1; lưu current_run_id trong transaction start/claim.
4. Public input có threadId C1, runId R1. Adapter bind native checkpoint thread A1.
5. Stream events mang public lifecycle R1; protocol message IDs giữ danh tính riêng.

### Pause

Lưu content/attachments/file links đã có, metadata pending action và checkpoint/writes trong cùng transaction theo giai đoạn 4. Message A1 chuyển requires_action. Kết thúc invocation R1 bằng semantics interrupt của AG-UI đã pin; chưa đánh dấu A1 completed.

### Resume

1. User gửi action_id Q1 và response; backend kiểm tra action hiện tại, quyền và graph_version.
2. Claim nguyên tử message đang requires_action; lưu response, gán current_run_id R2 mới, chuyển running.
3. Runtime mới dùng checkpoint A1/namespace/checkpoint ID đã lưu.
4. Public lifecycle mới có threadId C1, runId R2; nội dung tiếp tục thuộc A1.
5. Không chèn lại user message U1 hoặc tạo assistant mới chỉ vì resume.

### Reconnect/đọc lịch sử

Reconnect là attach/read, không phải start/resume execution. Không tạo run mới, không đổi current_run_id và không gọi LLM/tool. Backend trả snapshot + tail cho conversation/message/lượt đang hoạt động, hoặc bản terminal đã lưu.

Một connect request nếu SDK cần request runId riêng thì đó chỉ là danh tính transport của request attach; không được ghi nó đè current_run_id của execution. Cần phân biệt trong adapter/version được triển khai.

## 7. Retry mạng khác thực thi mới

“run_id mới mỗi lần thực thi” không có nghĩa mỗi HTTP retry đều được tạo run_id mới.

- Retry cùng start request: dùng lại operation identity và payload đã chấp nhận; trả/attach R1 và A1 đã có.
- Retry cùng action response: không claim thêm R3 vì R2 đã claim. Trả kết quả đã nhận hoặc trạng thái đang thực hiện theo API, không chạy lại.
- Resume một pause mới thực sự: run_id mới, action_id phải khớp lần chờ mới.
- Người dùng bấm regenerate: assistant message mới và run_id mới.

Tài liệu này chốt ý nghĩa ID; cơ chế idempotency key/hash/lifetime cụ thể vẫn cần implementation contract. `current_run_id` hoặc unique một active assistant không tự đáp ứng chống submit trùng sau terminal.

## 8. Redis và event routing

Redis tổ chức dữ liệu live theo workspace/conversation/message và mang run_id của invocation. Ví dụ tên key minh họa, không phải Redis schema cuối:

```text
chat:{workspace:C1:A1}:head
chat:{workspace:C1:A1}:snapshot
chat:{workspace:C1:A1}:events
```

Cùng hash tag nếu dùng Redis Cluster và cần thao tác nguyên tử nhiều key. Metadata của snapshot/event envelope xác định conversation_id, assistant_message_id, run_id và cursor/epoch theo contract streaming sẽ thiết kế. Không tạo key mới rồi bỏ prefix cũ mỗi lần resume; snapshot nội dung A1 phải tiếp tục từ phần đã có hoặc hydrate PostgreSQL.

- run_id giúp phân biệt writer/invocation và tín hiệu điều khiển cũ.
- Message A1 giúp gom toàn bộ nội dung của nhiều lần resume.
- Conversation C1 giúp định tuyến về chat đúng trên UI.
- Không dùng run_id làm thứ tự event. Cần watermark/sequence riêng cho snapshot+tail.
- Không loại bỏ mọi event lịch sử R1 chỉ vì current_run_id đã là R2; prefix hợp lệ vẫn cần để dựng content. Chặn writer cũ và replay event hợp lệ là hai việc khác nhau.
- Check current_run_id đơn lẻ không phải cơ chế fencing hoặc bảo đảm exactly-once. Backend/Redis phải có kiểm tra quyền ghi nguyên tử theo contract thực thi.

Redis không là nguồn quyền độc lập. Start/resume/stop/read vẫn kiểm tra scope và quyền authoritative.

## 9. Stop phải nhắm đúng invocation

Thông tin nhận diện stop gồm public conversation và **cả message_id lẫn run_id**. Ví dụ body minh họa:

```json
{
  "messageId": "A1",
  "runId": "R2"
}
```

Backend xác minh A1 thuộc conversation/workspace đã authorize, đang thực thi và current_run_id đúng R2, rồi chuyển tín hiệu stop cho đúng execution. Worker/finalizer phải kiểm tra scope trước ghi kết quả.

Stop R1 đến muộn khi A1 đang chạy R2 không được dừng R2. Stop A1 không được dừng A2 vừa regenerate. Đã terminal thì trả trạng thái phù hợp, không phát sinh execution mới.

Hủy khi requires_action dùng action_id hiện tại để vô hiệu chính lần chờ đó; không coi một HTTP abort/detach là lệnh hủy. Chưa bổ sung durable cancel-intent schema hoặc auto-recovery trong tài liệu này.

## 10. So với cách LibreChat

Mã nguồn LibreChat đã đối chiếu cho thấy:

- Native thread_id là conversationId.
- runId truyền vào SDK agent là responseMessageId, giữ lại khi HITL resume.
- streamId lookup theo conversationId.
- Có job epoch/generation, checkpoint namespace và execution scope để phân biệt các lần thực thi và chống event/job cũ.

Đó là SDK/lifecycle riêng, không đồng nghĩa mọi field tên runId trong source đều có cùng nghĩa hoặc là AG-UI RunAgentInput.run_id.

Dự án mình giữ ý tưởng assistant response ID bền vững, nhưng dùng run_id riêng để biểu diễn invocation trực tiếp. Không copy thêm bảng/job epoch chỉ để giống implementation LibreChat.

## 11. Phạm vi đã kiểm chứng và công việc tích hợp còn lại

[Proof checkpoint/AG-UI](../experiments/langgraph-action-checkpoints/README.md) đã kiểm chứng giữ cùng message qua nhiều resume, run_id mới mỗi invocation và lưu response có actor trong activity. **Proof trước dùng public thread_id = assistant ID** để thử checkpoint; chưa kiểm chứng bản adapter hoàn chỉnh public thread C1 ↔ native checkpoint A1 với frontend/API ứng dụng.

Cần thực hiện khi tích hợp:

- Adapter public/native thread mapping và kiểm thử event lifecycle giữ đúng C1/Rn.
- Binding current_run_id, request dedupe và exact stop, bao gồm request/event đến muộn.
- Redis accumulated snapshot/tail qua nhiều invocation của một A1; reconnect không tạo execution mới.
- Giữ riêng protocol message/tool IDs; renderer và context builder đọc activity đúng actor.
- Share/copy tạo conversation/message IDs mới và remap tham chiếu cần thiết; không copy active run_id, pending action hoặc checkpoint pointer của nguồn.

Chưa sửa SQL, backend, frontend hoặc Redis trong lần ghi nhận này. Không thay policy bỏ qua worker crash hoặc mở rộng thành bảng run/attempt. Những phần cũ dùng native thread theo branch/conversation, runId bằng messageId hoặc chỉ stop theo thread phải đọc lại theo quyết định này.
