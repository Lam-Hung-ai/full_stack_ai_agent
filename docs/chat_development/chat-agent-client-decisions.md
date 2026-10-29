# Quyết định frontend ChatAgent và input API riêng

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

Trạng thái: đã đồng ý về hướng thiết kế, chưa triển khai code. Đọc cùng [API contract](chat-agent-api-contract.md), [database](database-decisions.md) và [ID](conversation-message-run-id-decisions.md).

## 1. Hướng đã chọn

Input HTTP do ứng dụng thiết kế theo nghiệp vụ conversation/message/file. Response chạy agent tiếp tục dùng AG-UI events/SSE. Backend chuyển DTO đã kiểm tra thành RunAgentInput nội bộ để gọi LangGraphAgent.

Không ép frontend gửi toàn bộ history/state/tools/context chỉ để khớp input tổng quát của AG-UI. Resume vẫn dùng ResumeEntry chuẩn của SDK.

## 2. Kế thừa HttpAgent

```text
AbstractAgent
  └─ HttpAgent
       └─ ChatAgent
```

| Lớp | Trách nhiệm được tái sử dụng |
|---|---|
| AbstractAgent | Pipeline events, cập nhật messages/state, subscriber |
| HttpAgent | Gửi HTTP, đọc SSE thành events, abort request |
| ChatAgent | Chuyển DTO nghiệp vụ sang request tương ứng và triển khai connect |

Kế thừa trực tiếp AbstractAgent làm phải viết thêm HTTP/SSE vốn đã có ở HttpAgent; không cần trong phạm vi hiện tại.

Theo SDK local đã kiểm tra, runAgent() nhận runId/tools/context/forwardedProps/resume; threadId/messages/state được dựng từ instance. HttpAgent.requestInit(input) là điểm override để gửi body riêng. AbstractAgent có connectAgent(), nhưng protected connect() mặc định chưa triển khai; HttpAgent hiện chưa thêm transport connect.

Các chi tiết này cần đối chiếu lại khi nâng phiên bản SDK, không phải cam kết API mọi phiên bản.

## 3. ChatAgent là adapter nhỏ

ChatAgent chỉ xử lý transport của gửi/sửa/regenerate/resume và connect. Tái sử dụng HTTP/SSE của SDK ở nơi phù hợp, đưa events qua pipeline để SDK cập nhật state rồi gọi subscribers.

Stop phía server là REST command; không đồng nhất với HttpAgent.abortRun(). Nếu có convenience method stop(), nó chỉ gọi API ứng dụng, không tạo execution mới.

Không đưa vào ChatAgent:

- CRUD conversation, folder, upload/download, share/copy hoặc RBAC.
- Một messages store riêng song song với SDK.
- Bộ reducer text/tool/activity tự viết lại.
- Cơ chế gọi subscriber bằng tay.
- Cơ chế requestId/Idempotency-Key hoặc auto-retry mutation trong giai đoạn hiện tại.

Các method send/edit/regenerate/resume có thể là convenience methods, không cần thêm nhiều tầng class/service/command framework chỉ để bọc từng endpoint.

## 4. Luồng dữ liệu

```text
useAgentChat / thao tác UI
    -> ChatAgent: input nghiệp vụ
    -> REST endpoint tương ứng
    -> AG-UI SSE
    -> pipeline kế thừa từ SDK
    -> agent.messages / agent.state
    -> subscriber
    -> React UI
```

runAgent() vẫn có thể dựng RunAgentInput bên trong SDK. Adapter chuyển input cùng ngữ cảnh thao tác sang DTO public trước khi gửi; điều này không buộc HTTP body giống RunAgentInput.

Ngữ cảnh thao tác phải được bind rõ cho invocation, không dùng một biến request chung có thể bị ghi đè giữa các lời gọi. Instance có conversationId trong cấu hình. Chính sách số kết nối SSE, detach và chuyển instance khi chuyển conversation tạm hoãn, chưa chốt trong giai đoạn này.

## 5. Subscriber và UI

Giữ cách sử dụng subscriber hiện tại như onMessagesChanged, onTextMessageStartEvent và onRunErrorEvent. Đổi lớp HttpAgent sang ChatAgent không yêu cầu thay bộ component render chỉ vì transport thay đổi.

UI vẫn cần phần chức năng chưa có: render activity hỏi người dùng/duyệt tool, hiển thị pending/running/requires_action/terminal và liên kết protocol messages với SQL assistant row. Không tự suy completed từ stream đóng.

Tên event/metadata liên kết nghiệp vụ sẽ chốt khi tích hợp. Chưa yêu cầu custom event chat.execution ở mọi thay đổi.

## 6. Connect, detach và stop

- Connect gọi endpoint theo conversation, không body/cursor, lấy snapshot mới nhất rồi theo dõi stream nếu đang chạy.
- Snapshot hydrate/thay projection tương ứng, không append lặp prefix.
- Connect không chạy LLM/tool, không tạo hoặc đổi runId execution.
- Detach/abort ngắt transport phía client. Worker có vòng đời độc lập stream.
- Stop gửi lệnh server theo assistant message, không body/runId; nếu requires_action thì hủy toàn bộ lượt đang chờ.
- Không tự retry mutation khi lỗi mạng; đọc trạng thái rồi connect. Không hứa chống mọi duplicate submit.

## 7. Input cấu hình instance

Các interface dưới đây là contract thiết kế, chưa phải class đã triển khai.

```ts
import type { Message, ResumeEntry } from "@ag-ui/core";

interface ChatAgentConfig {
  apiBaseUrl: string;
  conversationId: string;
  headers?: Record<string, string>;
  initialMessages?: Message[];
}
```

| Trường | Bắt buộc | Ý nghĩa |
|---|---|---|
| apiBaseUrl | Có | Base API, ví dụ /api/v1; adapter tự dựng URL từng thao tác |
| conversationId | Có | UUIDv7 conversation đã tạo; bind một instance với một conversation; cũng là AG-UI threadId |
| headers | Không | Headers bổ sung nếu cần; auth theo cơ chế chung của ứng dụng |
| initialMessages | Không | Protocol messages của nhánh đã tải để hydrate SDK, không phải raw SQL rows |

Không nhận workspaceId để ghi đè conversation scope; server tra workspace từ conversation. Tạo conversation nằm ở REST service trước khi khởi tạo ChatAgent. Không cấu hình tools/context/state/checkpoint từ UI như nguồn quyền hoặc lịch sử authoritative.

Nếu dùng cookie cross-origin, credentials và proxy auth phải được cấu hình ở transport theo auth contract; headers không tự giải quyết cookie forwarding. Chưa chốt thêm cơ chế auth trong tài liệu này.

## 8. Input thao tác chạy

```ts
interface ChatMessageInput {
  id: string;
  text: string;
  fileIds: string[];
}

interface SendMessageInput {
  parentMessageId: string | null;
  message: ChatMessageInput;
}

interface EditMessageInput {
  userMessageId: string;
  message: ChatMessageInput;
}

interface RegenerateInput {
  assistantMessageId: string;
}

interface ResumeInput {
  assistantMessageId: string;
  resume: ResumeEntry[];
}

interface StopInput {
  assistantMessageId: string;
}
```

Tất cả ID do ứng dụng tự tạo ở cả frontend/backend dùng UUIDv7; ID provider/checkpointer giữ theo thư viện. Kiểu TypeScript string không thay runtime validation.

| Trường | Quy tắc |
|---|---|
| message.id | UUIDv7 user message mới do client tạo, dùng optimistic UI; edit cũng phải tạo ID mới |
| message.text | Nội dung câu hỏi mới/đã sửa; không mang toàn bộ conversation history |
| message.fileIds | Danh sách stored_files.id đầy đủ cho message mới, không có file thì [] |
| parentMessageId | null khi gửi đầu; còn lại là message cha tường minh thuộc nhánh đã authorize |
| userMessageId | User message cũ cần tạo phiên bản sửa; backend lấy parent của nó, không sửa trực tiếp |
| assistantMessageId | SQL assistant row đích; không phải ID của từng protocol message bên trong bundle |
| resume | Các ResumeEntry chuẩn AG-UI trả lời đúng interrupts hiện tại; giữ nguyên cấu trúc SDK |

Không chèn requestId/Idempotency-Key vào các input. Backend tạo assistant ID; runId chỉ phục vụ SDK/protocol, không lưu messages.metadata.current_run_id hoặc dùng làm khóa nghiệp vụ. Một câu hỏi không có text nhưng có file có được phép hay không thuộc validation UX cần chốt khi triển khai; ít nhất không chấp nhận đồng thời text rỗng và fileIds rỗng.

Edit không có parentMessageId: parent phải lấy từ userMessageId cũ. Regenerate không có text/fileIds vì nó dùng lại context parent đã lưu. Resume không có user message ID mới vì tiếp tục cùng SQL assistant.

## 9. Method public và mapping HTTP

```ts
// Chữ ký thiết kế của ChatAgent, không phải implementation.
// Các method streaming trả Promise theo kết quả pipeline SDK.
sendMessage(input: SendMessageInput): Promise<RunAgentResult>;
editMessage(input: EditMessageInput): Promise<RunAgentResult>;
regenerate(input: RegenerateInput): Promise<RunAgentResult>;
resume(input: ResumeInput): Promise<RunAgentResult>;
attach(): Promise<RunAgentResult>;
stop(input: StopInput): Promise<StopAcknowledgement>;
```

RunAgentResult tái sử dụng từ @ag-ui/client. StopAcknowledgement là DTO JSON REST riêng; cấu trúc response chi tiết theo API implementation, không phải bằng chứng worker đã terminal. Các convenience method này thuộc cùng một adapter, không yêu cầu thêm lớp command framework.

| Method | URL sau /conversations/{conversationId} | HTTP body |
|---|---|---|
| sendMessage | /messages | { parentMessageId, message } |
| editMessage | /messages/{userMessageId}/edit | { message } |
| regenerate | /messages/{assistantMessageId}/regenerate | {} |
| resume | /messages/{assistantMessageId}/resume | { resume } |
| attach | /connect | Không body |
| stop | /messages/{assistantMessageId}/stop | Không body |

conversationId lấy từ config, không lặp lại trong mỗi input/body. userMessageId/assistantMessageId của thao tác đích dùng dựng URL, không tự chèn thêm vào body. attach không nhận cursor, messageId hoặc runId; server resolve assistant active và snapshot mới nhất.

StopInput áp dụng cả pending/running và requires_action: dừng/hủy toàn bộ assistant đích. Không nhận runId hoặc interrupt ID để phân biệt các lần resume. Chấp nhận stop đến muộn có thể dừng lần resume mới của cùng assistant; không tác động assistant khác của regenerate.

Ví dụ sử dụng ở UI:

```ts
const agent = new ChatAgent({
  apiBaseUrl: "/api/v1",
  conversationId,
  initialMessages: historyMessages,
});

agent.subscribe({
  onMessagesChanged: ({ messages }) => setMessages([...messages]),
});

await agent.sendMessage({
  parentMessageId: selectedParentMessageId,
  message: {
    id: uuidv7(),
    text: "Phân tích tài liệu này",
    fileIds: uploadedFileIds,
  },
});

// Khi nối lại stream: không gọi sendMessage lần nữa.
await agent.attach();

// Khi UI trả lời interrupt: resumeEntries đúng kiểu SDK.
await agent.resume({ assistantMessageId, resume: resumeEntries });
```

Ví dụ là minh họa contract, chưa phải code copy vào ứng dụng và chạy ngay. uuidv7() là helper UUIDv7 thống nhất của ứng dụng, không phải crypto.randomUUID() (UUIDv4). Cần import helper này, RunAgentResult/ChatAgent implementation và quản lý subscription theo vòng đời React khi triển khai.

## 10. Mapping nội bộ với SDK

Các method nghiệp vụ không thay đổi chữ ký runAgent() kế thừa thành một kiểu không tương thích. Chúng chuẩn bị ngữ cảnh thao tác, gọi pipeline SDK và để requestInit() xuất DTO tương ứng. resume phải truyền entries vào cả lifecycle SDK khi cần validate pendingInterrupts và body HTTP; chỉ giấu entries trong biến riêng là chưa đủ.

runAgent() mặc định có thể sinh runId phía client; contract public hiện để server cấp execution runId. Adapter phải xử lý đồng bộ lifecycle với RUN_STARTED của server; không đưa ID này vào metadata database hoặc bắt UI quản lý nó như định danh nghiệp vụ. Đây là điểm cần kiểm chứng khi viết adapter, chưa tuyên bố override requestInit đã giải quyết.

Context thao tác là cục bộ theo lời gọi, không là field mutable dùng chung bị đổi khi request trước còn chạy. Không tự retry request. Không truyền lịch sử/activity từ client thành quyền gọi tool. Server dựng context từ database/checkpoint đã authorize.

## 11. Phạm vi ghi nhận

Chưa viết ChatAgent hoặc đổi hook/proxy. Khi triển khai cần kiểm tra requestInit mapping, SDK lifecycle khi server cấp runId, SSE decoder reuse, connect pipeline, snapshot replacement, auth/status propagation và nhiều pause/resume. Không giả override requestInit đơn lẻ đã giải quyết toàn bộ các phần này.

## 12. History và phần SSE tạm hoãn

History DTO giữ SQL messageId/parentMessageId/role/status, bundle AG-UI content, files và dữ liệu nhánh. Chuyển bundle thành protocol messages để SDK render nhưng giữ mapping về SQL assistant ID cho thao tác UI. initialMessages không thay DTO cây message của ứng dụng.

Phần nhiều SSE khi chuyển conversation, unsubscribe/detach, callback đến muộn và hiển thị chéo A/B tạm hoãn. Chưa chốt chỉ giữ một SSE hoặc cách quản lý nhiều instance. Việc pause phần thảo luận này không thay endpoint connect/stop đã chốt.
