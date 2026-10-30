# API chat đã chốt

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

Trạng thái: quyết định thiết kế để triển khai/refactor; chưa triển khai các route dưới đây. Thay thế contract cũ theo `/threads` và `/agent/{agentId}/run|connect|stop`.

Nguồn liên quan: [database](database-decisions.md), [ID](conversation-message-run-id-decisions.md), [ChatAgent](chat-agent-client-decisions.md), [kiến trúc](agent-chat-architecture.md).

## 1. Nguyên tắc

- Input HTTP là DTO nghiệp vụ riêng; response streaming dùng AG-UI events/SSE.
- Backend tự dựng RunAgentInput từ request đã kiểm tra và history đúng nhánh. Không yêu cầu browser gửi toàn bộ history/state/tools/context.
- Một agent cố định; chưa cần agentId trên URL hoặc endpoint discovery `/info`.
- Base API là `/api/v1`. Tên tài nguyên HTTP là conversations; public AG-UI threadId vẫn bằng conversations.id.
- Resume tái sử dụng cấu trúc ResumeEntry của AG-UI, không tự tạo envelope answer/approval khác.
- Không thêm bảng run, request hoặc pending_actions để phục vụ các endpoint này.

## 2. Danh sách endpoint

Các path dưới đây tương đối với `/api/v1`.

| Method/path | Chức năng | Response |
|---|---|---|
| POST /workspaces/{workspaceId}/conversations | Tạo chat trong workspace | JSON |
| GET /workspaces/{workspaceId}/conversations | Sidebar theo workspace, lọc pin/folder/archive và phân trang | JSON |
| GET /conversations/{id} | Metadata, con trỏ nhánh đã lưu và assistant active nếu có | JSON |
| PATCH /conversations/{id} | Rename, pin, archive, chuyển folder theo allowlist | JSON |
| DELETE /conversations/{id} | Dừng assistant đang chạy hoặc chờ (như stop), rồi xóa mềm và revoke share nguồn (TD-016) | JSON hoặc empty theo convention chung |
| GET /conversations/{id}/messages | History theo nhánh và dữ liệu chuyển nhánh | JSON |
| POST /conversations/{id}/messages | Gửi câu hỏi mới, chạy assistant | AG-UI SSE |
| POST /conversations/{id}/messages/{userMessageId}/edit | Tạo nhánh từ câu hỏi đã sửa | AG-UI SSE |
| POST /conversations/{id}/messages/{assistantMessageId}/regenerate | Tạo câu trả lời khác | AG-UI SSE |
| POST /conversations/{id}/messages/{assistantMessageId}/resume | Tiếp tục assistant đang chờ | AG-UI SSE |
| POST /conversations/{id}/connect | Hydrate mới nhất, rồi theo dõi execution đang chạy | AG-UI SSE |
| POST /conversations/{id}/messages/{assistantMessageId}/stop | Dừng execution hoặc hủy lượt đang chờ | JSON acknowledgement |

Tạo và liệt kê lấy workspace từ path (QD-10, QD-12); các route còn lại suy workspace từ conversation và kiểm membership. Field JSON của DTO dùng `snake_case` như mọi REST API của backend; event AG-UI giữ `camelCase` của protocol (QD-19). GET metadata và history tách riêng vì history có thể dài. Con trỏ nhánh đã lưu không thay parent tường minh trong request gửi; lựa chọn nhánh per-tab vẫn ở client.

Folder, upload/download, share/copy, auth/workspace/RBAC dùng REST API riêng theo database đã chốt. Đã có từ S1 (TD-007): `/auth/{register,login,refresh,session,logout,logout-all}`, `GET /users/me`, `GET /workspaces`, `GET /workspaces/{id}`. Từ S3 (TD-009): `GET/POST /workspaces/{id}/folders`, `PATCH/DELETE /folders/{id}`; xoá folder chuyển chat trong đó về danh sách chung. Payload theo OpenAPI của backend.

Từ S6 (TD-012, QD-24 → QD-26):

| Method/path | Chức năng | Quyền |
|---|---|---|
| POST /auth/email-verification/request, /auth/password-reset/request | Gửi link xác minh email / đặt lại mật khẩu; luôn 202, cùng nội dung | Công khai, rate limit |
| POST /auth/email-verification/confirm, /auth/password-reset/confirm | Dùng link (`token`; đặt lại kèm `password`); đặt lại thu hồi mọi phiên | Công khai |
| POST /organizations | Tạo tổ chức; người tạo là owner | Đăng nhập |
| GET /organizations/{id} | Tên, workspace, `permissions` và `is_owner` của người gọi | Thành viên |
| PATCH /organizations/{id} | Đổi tên | `organization.manage` |
| POST /organizations/{id}/leave | Rời tổ chức; owner cuối cùng bị từ chối (`last_owner`) | Thành viên |
| GET /organizations/{id}/members | Thành viên đang hoạt động và vai trò | `member.manage` |
| PATCH /organizations/{id}/members/{memberId} | Đặt lại toàn bộ vai trò (`role_ids`) | `role.manage`; vai trò owner chỉ owner |
| DELETE /organizations/{id}/members/{memberId} | Xoá khỏi tổ chức, dừng lượt đang chạy của họ trong workspace | `member.manage`; xoá owner chỉ owner |
| GET/POST /organizations/{id}/invitations, DELETE …/{invitationId} | Lời mời đang chờ, mời (gửi thư; mời lại thay link), thu hồi | `member.manage` |
| POST /invitations/preview | Tổ chức, email, trạng thái, `account_exists` của một link | Người có link |
| POST /invitations/accept | Nhận lời mời bằng tài khoản đúng email | Đăng nhập |
| POST /invitations/register | Tạo tài khoản cho email được mời rồi tham gia | Người có link |
| GET /permissions | Danh mục quyền (`resource.action`) | Đăng nhập |
| GET/POST /organizations/{id}/roles, PATCH/DELETE …/{roleId} | Vai trò kèm quyền; owner khoá; vai trò có sẵn không đổi tên/xoá; không cấp quyền mình không có (`permission_escalation`) | `role.manage` |

Người ngoài tổ chức nhận 404 `organization_not_found` ở mọi route `/organizations/{id}`. Token của link luôn nằm trong body, không trong URL API.

Từ S7 (TD-013, QD-27): tệp đính kèm.

| Method/path | Chức năng | Quyền |
|---|---|---|
| POST /workspaces/{id}/uploads | Khai `original_name`, `content_type`, `size_bytes`; nhận `file_id` và presigned PUT (`url`, `method`, `headers` phải gửi đúng, `expires_at`). Chưa ghi gì vào database | `conversation.create` trong workspace |
| POST /workspaces/{id}/uploads/{fileId}/complete | Gửi lại đúng ba trường đã khai; backend HEAD, so cỡ, soi byte đầu, tính SHA-256, chuyển sang key cuối rồi ghi `stored_files`; key cuối nhận đúng byte đã kiểm. Lỗi: 409 `upload_missing`, 409 `upload_completed` (đã xong; object không đổi), 422 `upload_size_mismatch`, 415 `file_content_mismatch` / `unsupported_file_type` | Như trên |
| GET /conversations/{id}/files/{fileId} | URL ký ngắn hạn trong body (`url`, `expires_at`); ảnh mở inline, tệp khác tải về | Chủ chat, tệp phải gắn vào một message của chat |

Gửi câu hỏi (§3) và sửa câu hỏi (§4) nhận `file_ids`: tối đa 10 tệp, mỗi tệp là upload của chính người gửi trong cùng workspace (sai thì 422 `invalid_file`); câu hỏi có tệp được phép không có chữ. Loại được nhận: PNG, JPEG, GIF, WebP, PDF, văn bản (txt, md, csv, json), tối đa 10 MB.

Từ S8 (TD-014, QD-28): chia sẻ và copy.

| Method/path | Chức năng | Quyền |
|---|---|---|
| GET /conversations/{id}/share | Share đang hiệu lực của chat: `url`, `mode`, `version`, `published_at`; 404 nếu chưa có | Chủ chat |
| POST /conversations/{id}/share | Chụp toàn cây (mọi nhánh, tệp, nhánh đang mở) thành snapshot mới, đóng dấu rồi xuất bản; link giữ nguyên. 409 `conversation_busy` khi còn lượt chưa xong | Chủ chat, `conversation.share` |
| DELETE /conversations/{id}/share | Thu hồi vĩnh viễn; chia sẻ lại là link mới | Chủ chat |
| GET /shares/{token} | Snapshot: `title`, `mode`, `version`, `messages` (cả cây, kèm `sibling_ids`), `current_message_id`, `can_copy` | Public: ai cũng xem; tổ chức: thành viên đang hoạt động. Còn lại 404 |
| GET /shares/{token}/files/{fileId} | URL ký của tệp trong snapshot | Như trên |
| POST /shares/{token}/copy | `client_request_id`; tạo chat riêng của người gọi (public → workspace cá nhân, tổ chức → workspace tổ chức đó) với message, tệp và object mới; gọi lại cùng id trả cùng bản sao. Bản sao chưa hoàn tất (đang copy, lỗi, bị huỷ) không hiện và trả 404 cho mọi route conversation (TD-016) | Đăng nhập, đọc được share, `conversation.create` ở workspace đích |

Từ S10 (TD-018, QD-31, QD-32): tìm kiếm, export, tệp do agent tạo.

| Method/path | Chức năng | Quyền |
|---|---|---|
| GET /workspaces/{id}/conversations/search?q=&page=&page_size= | Chat của mình trong workspace khớp `q` (2–200 ký tự) theo tên hoặc chữ của câu hỏi, câu trả lời, không phân biệt hoa thường và dấu. Mỗi dòng: `id`, `title`, `archived_at`, `updated_at`, `message_id` (message khớp mới nhất, null khi chỉ khớp tên), `snippet`; mới nhất trước. Bỏ chat đã xoá và bản copy chưa xong. `q` ngắn hơn 2 ký tự sau khi gộp khoảng trắng: 422 `query_too_short` | Thành viên workspace; chỉ chat của chính mình |
| GET /workspaces/{id}/export | Tệp zip (`application/zip`, tên kiểu "Chat Cá nhân 30-10-2026.zip"): `manifest.json` và mỗi chat một thư mục "yyyy-mm-dd Tên chat" có `conversation.json` (cả cây) và `conversation.md` (nhánh đã lưu). Tệp đính kèm chỉ có tên, loại, cỡ. 10 lần/giờ mỗi người (429) | Thành viên workspace; chỉ chat của chính mình |

Mở chat ở nhánh của một kết quả tìm kiếm: frontend dùng `/c/{id}?m={message_id}`, history gọi `?from_message_id=`.

Tool `create_file` (quyền `tool.create_file`): agent tạo tệp CSV, MD, TXT, XLSX gắn vào assistant đang chạy. Kết quả tool là JSON `{file_id, name, content_type, size_bytes}`; tệp tải qua `GET /conversations/{id}/files/{fileId}` như tệp đính kèm, đi theo share và copy (id trong kết quả tool được đổi ở bản copy). Tối đa 5 tệp mỗi câu trả lời, 5 MB mỗi tệp; ô bảng tính luôn là dữ liệu, không là công thức.

Sidebar (`GET /workspaces/{id}/conversations`) nhận `archived=true` (chỉ chat đã lưu trữ), `folder_id` (chat của một folder) hoặc `unfiled=true` (chat ngoài folder); mặc định là mọi chat chưa lưu trữ. Chat ghim lên đầu, rồi theo `updated_at` giảm dần. `PATCH /conversations/{id}` nhận `title`, `pinned`, `archived`, `folder_id` (null là bỏ khỏi folder); field bỏ trống giữ nguyên, field khác bị từ chối. Các nhóm còn lại chốt khi tới sprint tương ứng. Health endpoints thuộc vận hành service, không phải API agent discovery.

## 3. Gửi câu hỏi mới

Kiểu input frontend, cấu hình instance và mapping từng method được định nghĩa tại [ChatAgent input](chat-agent-client-decisions.md#7-input-cấu-hình-instance).

```http
POST /api/v1/conversations/{id}/messages
```

```json
{
  "parent_message_id": "previous-assistant-id",
  "message": {
    "id": "new-user-message-id",
    "text": "Phân tích tài liệu này",
    "file_ids": ["stored-file-id"]
  }
}
```

- Lượt đầu có parentMessageId null; các lượt sau chỉ rõ parent đã authorize.
- Client tạo UUIDv7 user message để hiển thị optimistic. Server tạo UUIDv7 assistant message. runId chỉ phục vụ adapter/protocol AG-UI, không là input nghiệp vụ hoặc trường metadata database.
- fileIds là file đã upload. Backend kiểm tra ownership/workspace và liên kết qua message_files; không nhận bucket/object_key do browser tùy ý chỉ định.
- (S7, QD-27) Câu hỏi có tệp lưu `content` là mảng content part của AG-UI 1.0: phần chữ `{"type":"text"}` rồi mỗi tệp một part `image` hoặc `document` có `id` = `stored_files.id`, `source` `{"type":"url","value":"stored-file:<id>","mimeType":…}` và `metadata` `{filename, sizeBytes}`. Không lưu byte hay URL ký. Mỗi lượt backend đọc lại tệp từ storage: ảnh và PDF thành nguồn `data` (base64), tệp văn bản thành phần chữ.
- Input text/fileIds là DTO gửi hiện tại; backend dựng canonical AG-UI content. Không thay cấu trúc JSONB content/attachments đã chốt.
- Không append mù danh sách messages từ browser hoặc dùng browser tools để quyết định quyền tool.

## 4. Sửa câu hỏi và regenerate

```http
POST /api/v1/conversations/{id}/messages/{userMessageId}/edit
POST /api/v1/conversations/{id}/messages/{assistantMessageId}/regenerate
```

Edit chỉ nhận đích là user message và body cùng hình dạng message ở mục 3, chứa ID mới, text mới và danh sách fileIds đầy đủ của phiên bản mới. Mảng fileIds rỗng nghĩa không đính kèm file.

```json
{ "message": { "id": "new-user-message-id", "text": "Câu hỏi đã sửa", "file_ids": [] } }
```

Backend tạo user message mới cùng parent với câu hỏi cũ, rồi assistant mới. Không sửa message terminal, không xóa nhánh cũ.

Regenerate chỉ nhận đích là assistant message, body rỗng. Backend tạo assistant mới cùng parent với assistant cũ; dựng context từ parent path, không tiếp tục checkpoint của câu trả lời cũ.

Cả hai trả AG-UI SSE như mục 3; event `chat.assistant` mang `userMessageId` là câu hỏi mới (edit) hoặc câu hỏi đang được trả lời lại (regenerate). Đích sai vai trò hoặc không thuộc conversation trả 404 `message_not_found`; đang có assistant active trả 409 `assistant_active`. Lượt mới thành nhánh đã lưu của conversation (QD-20).

## 5. Resume

```http
POST /api/v1/conversations/{id}/messages/{assistantMessageId}/resume
```

Body có trường `resume: ResumeEntry[]`, dùng đúng kiểu/validation của phiên bản SDK AG-UI được pin. Không định nghĩa thêm response.type answer/approval của ứng dụng.

- requires_action là trạng thái message trong PostgreSQL; resume là input tiếp tục execution. Hai khái niệm không thay nhau.
- Backend đối chiếu interruptId với interrupts đang chờ của assistant/action hiện tại, kiểm tra quyền và graph compatibility trước claim.
- action_id có thể giữ nội bộ trong metadata; backend resolve checkpoint pointer, không nhận pointer/namespace từ client.
- Claim requires_action -> running nguyên tử, ghi response/activity; cùng assistant message ID.
- Không tạo SQL user message mới chỉ vì người dùng trả lời câu hỏi bổ sung. Lưu activity có actor/response; context builder ánh xạ câu trả lời thành HumanMessage đúng một lần.
- Từ chối tool có thể resume để assistant giải thích. Hủy toàn bộ lượt chờ dùng stop.

Tên field chi tiết bên trong ResumeEntry theo SDK đã pin; không sao chép schema tự chế để tránh lệch protocol.

Từ S4 (QD-22):

```json
{ "resume": [ { "interruptId": "<interrupt_id>", "status": "resolved", "payload": { "answer": "CSV" } } ] }
```

- Payload theo loại interrupt: câu hỏi `{ "answer": "<text>" }`, duyệt tool `{ "approved": true | false }`. Phải trả lời đủ mọi interrupt của lượt chờ (`resume_incomplete`), id lạ hoặc cũ trả 409 `stale_interrupt`; `status` khác `resolved` trả 422 (hủy cả lượt dùng stop).
- Thứ tự kiểm tra trước claim: chủ conversation, `requires_action` (`not_waiting`), `graph_version` (`graph_version_changed`), câu trả lời, quyền của tool được duyệt (403 `permission_denied`), checkpoint còn trong DB (`checkpoint_missing`). Lỗi ở bước nào thì lượt vẫn chờ.
- Claim chuyển `requires_action → running` cùng transaction với câu trả lời trong activity và `metadata.actions`; hai request đồng thời chỉ một request được claim.
- Response là AG-UI SSE của cùng assistant ID; `chat.assistant.userMessageId` là câu hỏi gốc.

Lượt dừng để chờ phát `ACTIVITY_SNAPSHOT` loại `user_interaction` (một activity cho mỗi interrupt, id `interaction:<action_id>:<n>`), `chat.assistant` với `requires_action`, rồi `RUN_FINISHED` có `outcome.type = "interrupt"`, tất cả sau khi checkpoint, content và metadata đã commit. Content activity: `{action_id, interrupt_id, kind, status, question? | tool_name, tool_call_id, arguments}`; sau khi trả lời thêm `response`, `actor_id`; `status` là `waiting`/`answered`/`cancelled`.

## 6. Connect không có cursor

```http
POST /api/v1/conversations/{id}/connect
```

Không body, không cursor. Server kiểm tra quyền. Có assistant active thì hydrate nhánh chứa assistant đó; pending/running thì stream tiếp, requires_action thì trả thông tin chờ và đóng stream. Không có assistant active thì hydrate nhánh hiện hành đã lưu rồi đóng stream. Người dùng muốn xem nhánh cũ sử dụng API history; connect không nhận thêm input chọn nhánh.

| Trạng thái assistant | Hành vi |
|---|---|
| pending/running | Snapshot mới nhất rồi stream tiếp |
| requires_action | Snapshot, thông tin interrupt đang chờ, đóng stream |
| completed/failed/cancelled hoặc không có execution active | Snapshot đã lưu rồi đóng stream |

Connect chỉ đọc/attach: không gọi agent/LLM/tool, không tạo execution mới, không tự resume interrupt.

Snapshot thay thế projection tương ứng trên UI; không append prefix lần nữa. Backend vẫn dùng sequence/watermark nội bộ khi nối snapshot với Redis tail để không mất/lặp event, nhưng không đưa cursor vào input public.

Mất Redis/worker có thể mất phần chưa lưu; PostgreSQL lưu ở terminal/pause theo giới hạn đã chốt. Không hứa reconnect cứu mọi token.

Từ S5 (TD-011): stream của connect là `RUN_STARTED` (run riêng của connect), `CUSTOM chat.assistant` nếu có assistant active, `MESSAGES_SNAPSHOT` (nhánh đã lưu + view live), rồi với lượt đang chạy là các event sau watermark tới `RUN_FINISHED`/`RUN_ERROR` của lượt. View chỉ được ghi ở điểm không còn step/message/tool call nào mở, nên phần đuôi không có END thiếu START. Không có dữ liệu live, hoặc stream đã bị cắt mất event sau watermark (phát hiện bằng số thứ tự event), thì chỉ gửi snapshot đã lưu rồi đóng; client poll history tới khi lượt lưu xong. Một SSE mỗi tab (QD-23): rời conversation là ngắt stream, quay lại thì connect.

## 7. Stop và hủy lượt chờ

Không body. Conversation ID và assistant message ID trên URL xác định lượt cần dừng.

Backend kiểm tra quyền, message thuộc conversation và trạng thái hiện tại. pending/running thì gửi tín hiệu dừng lượt đó; requires_action thì hủy toàn bộ lượt, chuyển cancelled, giữ content và vô hiệu pending pointer. Đã terminal thì không chạy lại hay tác động lượt khác. Không có endpoint cancel-action riêng.

Từ S5, process nhận stop mà không chạy lượt đó thì phát tín hiệu qua Redis tới process đang giữ khoá sở hữu của lượt và chờ trạng thái đổi; không còn process nào sở hữu thì huỷ tại chỗ.

Stop mang nghĩa dừng assistant này, kể cả nó vừa resume. Chấp nhận lệnh đến muộn có thể dừng lần resume mới của cùng assistant; không bảo đảm phân biệt invocation cũ/mới. Regenerate có assistant ID khác nên stop message cũ không tác động message mới.

Acknowledgement xác nhận đã nhận/chấp nhận yêu cầu hoặc message đã terminal, không khẳng định worker đã dừng chỉ vì đã phát tín hiệu.

Từ S3 (QD-20), response là `{ "id": "<assistant id>", "status": "<trạng thái hiện tại>" }`. Backend chờ tối đa 5 giây để lượt lưu `cancelled` kèm partial; quá hạn thì `status` vẫn là `running`. Assistant active mà không có lượt nào chạy trong process (process đã khởi động lại) được chuyển thẳng `cancelled`. Stream của lượt bị dừng đóng các span đang mở, phát `chat.assistant` với `cancelled` rồi `RUN_FINISHED` có `outcome: {"type": "cancelled"}`.

Ngắt HTTP/detach chỉ rời stream, không tự stop. Từ chối một tool rồi tiếp tục assistant dùng resume, khác hủy toàn bộ lượt.

## 8. ID và stream

- conversationId = public AG-UI threadId.
- SQL user/assistant message IDs độc lập.
- Một assistant giữ nguyên ID qua nhiều pause/resume. runId chỉ nằm ở RunAgentInput/lifecycle AG-UI theo yêu cầu SDK; không dùng làm khóa nghiệp vụ, input stop, trường metadata hoặc khóa Redis ứng dụng.
- Mọi ID do ứng dụng tự tạo ở frontend/backend dùng UUIDv7. ID do LangGraph/provider sinh (checkpoint/tool-call) giữ theo thư viện, không ép đổi tham chiếu.
- Native LangGraph configurable.thread_id = assistant message ID. Adapter ánh xạ public/native thread, lifecycle events vẫn mang conversationId/runId public.
- Protocol messageId/toolCallId riêng, ổn định khi hydrate/resume; một SQL assistant row có thể chứa nhiều protocol messages.

Liên kết SQL message và trạng thái nghiệp vụ đi trong một event `CUSTOM` tên `chat.assistant`, value `{conversationId, userMessageId, assistantMessageId, status}` (QD-19): phát ngay sau `RUN_STARTED` với `status: "running"`, và trước event kết thúc với trạng thái cuối (`completed`/`failed`/`cancelled`, sau này `requires_action`). Event cuối chỉ phát sau khi đã commit dữ liệu. Ngoài event này, ưu tiên lifecycle/messages/activity chuẩn của AG-UI. RUN_FINISHED hoặc stream đóng không tự có nghĩa SQL assistant completed: interrupt có thể là requires_action.

## 9. Xử lý mạng đơn giản trong phạm vi hiện tại

- Tạm bỏ Idempotency-Key, requestId/clientRequestId và cơ chế dedup submit chuyên biệt khỏi API.
- Frontend khóa thao tác khi submit/đang chờ response, không tự retry gửi/sửa/regenerate/resume.
- Khi lỗi mạng: đọc lại trạng thái conversation; connect để lấy nội dung mới nhất nếu thao tác đã được tiếp nhận. Nếu chưa xác định được kết quả, UI thể hiện chưa xác định thay vì tự gửi lại.
- PostgreSQL giữ một assistant pending/running/requires_action tối đa mỗi conversation; claim resume kiểm tra trạng thái/interrupt nguyên tử.
- Đây không phải bảo đảm chống mọi request trùng, đặc biệt request đến lại sau terminal. Chấp nhận giới hạn này hiện tại, không thêm bảng để giải quyết.

Quyết định này thay yêu cầu cũ về retry luôn attach đúng operation. Assistant message là danh tính bền vững của lượt; runId chỉ ở lớp protocol. Connect không tạo execution mới.

## 10. Quyền, lỗi và điều kiện thực thi

List/create có workspace scope. Mọi read/edit/start/resume/connect/stop/file/share/copy đều kiểm tra quyền authoritative. Owner/Admin/Superuser không tự đọc chat riêng.

Không nhận owner/workspace/checkpoint qua PATCH chung. Auto-title phải tránh ghi đè tên user; cơ chế cụ thể vẫn cần thiết kế trước khi bật.

Lỗi trước stream trả HTTP status phù hợp (401/403/404/409/validation); proxy giữ đúng status. Lỗi sau khi execution bắt đầu được bắt, lưu partial content và failed rồi phát outcome tương ứng. Stop giữ partial và cancelled. Terminal/pause outcome công bố sau commit dữ liệu liên quan.

Worker tiêu thụ LangGraphAgent độc lập subscriber, tích lũy Redis và lưu PostgreSQL ở các mốc đã chốt. Không giữ transaction trong khi chờ model. Bỏ qua recovery khi worker chết đột ngột theo phạm vi hiện tại.

## 11. Chưa triển khai

Chưa thay backend/frontend/SQL. Các việc còn lại gồm DTO/OpenAPI chi tiết, history pagination/branch selection, metadata liên kết SQL message, adapter public/native thread, Redis snapshot/tail và HTTP integration tests. Không tuyên bố proof checkpoint hiện có đã kiểm chứng toàn bộ API này.

## 12. History và chuyển conversation trên UI

GET messages phải giữ được SQL messageId, parentMessageId, role, status, bundle AG-UI content, file liên quan và thông tin các nhánh khác để chuyển nhánh. Một SQL assistant có thể chứa nhiều protocol messages; DTO không được flatten rồi làm mất liên kết SQL assistant ID cần cho edit/regenerate/resume/stop. Không thêm bảng branch.

Từ S3 (QD-20): mỗi dòng có `sibling_ids` (các phiên bản cùng parent, cũ trước, gồm cả chính nó). Không tham số thì trả nhánh theo con trỏ đã lưu; `?from_message_id=` trả nhánh đi qua message đó rồi xuống con mới nhất ở mỗi tầng. `current_message_id` là lá của nhánh trả về và là parent cho câu hỏi tiếp theo trên tab đó. Đọc không đổi con trỏ đã lưu. Phân trang history chưa làm.

Việc có giữ nhiều SSE khi chuyển conversation, detach/subscription, callback đến muộn và cách tránh hiển thị chéo chat **tạm hoãn thảo luận**, chưa chốt chính sách frontend trong giai đoạn này. Không coi đề xuất chỉ giữ một SSE là quyết định đã duyệt.
