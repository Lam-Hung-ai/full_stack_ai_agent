`# Giai đoạn 2 — bản chốt: hội thoại, message, pin/folder và file

> **Bổ sung mới:** [giai đoạn 4](phase-4-decisions.md) mở rộng status `requires_action`, `messages.metadata` và mốc lưu khi pause. Bản giai đoạn 2 giữ làm lịch sử cho cấu trúc hội thoại/file.

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

**Hoàn thành thiết kế database giai đoạn 2 trong phạm vi đã thống nhất.** Đây là tài liệu thiết kế và SQL đã kiểm tra trên PostgreSQL tạm; chưa áp dụng vào database ứng dụng, chưa triển khai backend/LLM/S3.

Tài liệu này thay thế các quyết định conversation/message/sidebar/file tương ứng trong giai đoạn 1 và giai đoạn 2 phần 1. Các bản cũ giữ nguyên làm lịch sử, không phải lựa chọn cấu trúc song song.

## 1. File và thứ tự áp dụng

| File | Vai trò |
|---|---|
| `phase-1-schema.sql` | Baseline danh tính, tổ chức, quyền, share/copy |
| `phase-2-part-1-schema.sql` | Bước chuyển đầu: cây message, AG-UI và tách object S3 |
| `phase-2-final-schema.sql` | Bước chuyển cuối: status, folder/pin và file rút gọn |
| `phase-2-final-checks.sql` | Kiểm tra cấu trúc cuối, fixture rollback |

Áp dụng **một lần**, theo đúng thứ tự, trên database scratch mới PostgreSQL 18+:

```bash
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-part-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-final-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-final-checks.sql
```

Đây là chuỗi tiến hóa baseline thiết kế, **không phải backfill production**. Bước cuối chủ động từ chối nếu đã có message, file/object, share, snapshot hoặc copy job. Nó không tự đoán bucket, chuyển JSON cũ hay đổi danh tính file đã chia sẻ. Khi từ chối, transaction rollback. Có thể giữ identity, conversation rỗng và chuyển pin/archive từ bảng trạng thái cũ trước khi bỏ bảng đó.

Checks giai đoạn cũ chỉ chạy ở đúng thời điểm của chúng: phase-1-checks trước phase-2-part-1; phase-2-part-1-checks trước phase-2-final. Sau bước cuối dùng phase-2-final-checks.

## 2. Các bảng cuối cùng trong phạm vi giai đoạn 2

| Bảng | Trách nhiệm |
|---|---|
| `conversations` | Conversation, owner/workspace, tiêu đề, con trỏ nhánh, pin/archive/folder |
| `messages` | Cây message, AG-UI content, attachments và status |
| `conversation_folders` | Folder riêng theo user/workspace, một cấp |
| `stored_files` | Metadata object S3 và JSON metadata mở rộng |
| `message_files` | Liên kết message với object file |

Các bảng share/copy có từ giai đoạn 1 tiếp tục tồn tại, được cập nhật FK và helper để dùng trực tiếp `stored_files`: `conversation_shares`, `share_snapshots`, `share_snapshot_messages`, `share_snapshot_files`, `share_snapshot_message_files`, `conversation_copy_jobs`, `conversation_copy_files`.

**Không còn** `conversation_user_states`, `files`, `chat_files`. Không tạo tags, bảng run/attempt/tool execution hoặc folder con.

## 3. conversations

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | UUID | Khóa chính |
| `workspace_id` | UUID | Workspace chứa chat |
| `owner_user_id` | UUID | Chủ sở hữu duy nhất |
| `title` | TEXT | Tiêu đề |
| `current_message_id` | UUID nullable | Message cuối của nhánh được lưu để mở lại |
| `pinned_at` | TIMESTAMPTZ nullable | NULL = chưa ghim |
| `archived_at` | TIMESTAMPTZ nullable | NULL = chưa lưu trữ |
| `folder_id` | UUID nullable | NULL = ngoài folder |
| `deleted_at` | TIMESTAMPTZ nullable | Xóa mềm cả conversation |
| `created_at`, `updated_at` | TIMESTAMPTZ | Thời điểm tạo/cập nhật |

Bỏ `title_source`, `revision`, `availability_status` và trạng thái copy cũ `status`. Không đưa chúng trở lại dưới tên khác. Copy chưa hoàn tất bị ẩn qua `conversation_copy_jobs`, không cần status conversation.

Một conversation chỉ có một owner; người được share xem snapshot, muốn chat tiếp sẽ tạo bản copy riêng. Vì vậy pin/archive/folder đặt trực tiếp trên conversation, không cần bảng trạng thái theo từng user. Pin và folder có thể cùng tồn tại; snapshot không mang trạng thái sidebar, bản copy mới để ba trường này NULL.

Index cho hai truy vấn chính:

```sql
CREATE INDEX idx_conversations_pinned
ON conversations(workspace_id, owner_user_id, pinned_at DESC, id DESC)
WHERE pinned_at IS NOT NULL AND deleted_at IS NULL AND archived_at IS NULL;

CREATE INDEX idx_conversations_folder
ON conversations(workspace_id, owner_user_id, folder_id, updated_at DESC, id DESC)
WHERE folder_id IS NOT NULL AND deleted_at IS NULL AND archived_at IS NULL;
```

Không mặc định quét toàn bảng: truy vấn phải lọc workspace/owner và khớp điều kiện partial index. PostgreSQL vẫn có thể chọn quét bảng nhỏ nếu rẻ hơn. Danh sách trả các trường cần hiển thị, phân trang, không kéo toàn bộ transcript.

## 4. conversation_folders

Các cột: `id`, `workspace_id`, `owner_user_id`, `name`, `created_at`, `updated_at`.

- **Một cấp, không có `parent_id`.**
- Folder riêng theo user/workspace, kể cả trong tổ chức. Owner/admin không được đọc chat nhờ folder.
- Một conversation thuộc tối đa một folder; composite FK bảo đảm cùng workspace và owner.
- Tên không rỗng; unique theo `(workspace_id, owner_user_id, lower(btrim(name)))`: không trùng tên sau khi bỏ khoảng trắng đầu/cuối và không phân biệt hoa/thường theo phép lower của database.
- Folder không đổi owner/workspace sau tạo; tên được sửa.
- Xóa folder đặt `folder_id` về NULL, giữ nguyên conversation và pin/archive.
- Không gắn instruction, knowledge hay file dùng chung vào folder trong giai đoạn này.

## 5. messages và cây hội thoại

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | UUID | ID message ứng dụng |
| `conversation_id` | UUID | Conversation |
| `parent_message_id` | UUID nullable | Parent trong cùng conversation |
| `role` | TEXT | Chỉ `user`, `assistant` |
| `content` | JSONB | Danh sách đầy đủ AG-UI Message của một message hiển thị |
| `attachments` | JSONB | Mảng citation/artifact/tool output bổ sung |
| `status` | TEXT | Vòng đời message |
| `created_at`, `updated_at` | TIMESTAMPTZ | Thời điểm tạo/cập nhật |

Không có `position`, `revision`, `finish_reason`, `error_code`, `error_message`, `origin`, `completed_at` hoặc danh sách file authoritative trong JSON message.

Parent composite FK và trigger đệ quy chặn parent khác conversation và chu trình. ID, role, parent, conversation và thời điểm tạo bất biến. Không xóa message riêng; xóa mềm conversation giữ lịch sử. Sửa câu hỏi/regenerate tạo sibling mới, không sửa lịch sử cũ. Sibling hiển thị theo `(created_at, id)`; context đi theo parent, không lấy tất cả dòng trước một timestamp.

Khi gửi phải chỉ rõ parent/nhánh; không suy parent từ con trỏ global vừa bị tab khác đổi. `current_message_id` chỉ là nhánh được lưu gần nhất, không cấp quyền cho request. Chưa bổ sung bảng ghi nhớ nhánh riêng từng tab.

### Content và attachments

Một dòng assistant có thể chứa chuỗi AG-UI assistant gọi tool → tool result → assistant trả lời. Role SQL vẫn là assistant; role bên trong bundle có thể assistant/tool/reasoning/activity. User bundle chứa đúng một AG-UI user message. Không lưu system/developer prompt nội bộ vào transcript; chỉ lưu reasoning được phép công bố.

```json
[
  {"id":"agui-a1","role":"assistant","toolCalls":[{"id":"call-1","type":"function","function":{"name":"search","arguments":"{}"}}]},
  {"id":"agui-t1","role":"tool","toolCallId":"call-1","content":"Tool output"},
  {"id":"agui-a2","role":"assistant","content":"Answer"}
]
```

Cho phép lưu toàn bộ tool output lặp ở `content` và `attachments`. Backend ghi đồng thời khi finalize; database không tự đồng bộ hai JSON. Context gửi model chỉ lấy kết quả từ content một lần.

CHECK SQL chỉ validate hình dạng ngoài/role/ID trong bundle. Backend cần pin SDK, validate đầy đủ AG-UI, alias `toolCalls`/`toolCallId`, chuỗi gọi tool và tham chiếu ID. Không lấy dữ liệu đã round-trip qua adapter LangChain để ghi đè bản AG-UI gốc nếu adapter làm mất thông tin. Không lưu raw token SSE thành transcript. Chiến lược nâng phiên bản protocol sẽ cần thiết kế khi nâng SDK, chưa có cột version mới được duyệt.

## 6. Status và thời điểm lưu

| Status | Ý nghĩa |
|---|---|
| `pending` | Assistant đang chờ xử lý |
| `running` | Agent đang xử lý, bao gồm chờ LLM/gọi tool/sinh nội dung |
| `completed` | Hoàn thành và lưu thành công |
| `failed` | Bắt được lỗi, lưu phần đã sinh nếu có |
| `cancelled` | Dừng theo yêu cầu, lưu phần đã sinh nếu có |

```text
pending -> running -> completed
   |          +----> failed
   |          +----> cancelled
   +---------------> failed
   +---------------> cancelled
```

- User message sau commit luôn `completed`.
- Assistant rỗng được tạo `pending`, sau đó chuyển `running`.
- **Nội dung PostgreSQL chỉ ghi khi hoàn tất, lỗi bắt được hoặc dừng.** Không yêu cầu lưu text theo token/định kỳ; thay đổi status đầu lượt vẫn được ghi riêng.
- Finalize ghi content, attachments, liên kết file và terminal status trong một transaction. Đính kèm file trước rồi mới đổi status terminal.
- Lỗi/dừng sau nửa câu trả lời vẫn giữ phần đã có; chưa sinh nội dung thì có thể `content = []`. Không cần status partial.
- Terminal message được khóa cập nhật; content, attachments, status, topology và liên kết file không thay đổi nữa. Retry do người dùng bấm tạo message mới.
- Tối đa **một assistant pending/running mỗi conversation**, được partial UNIQUE index bảo vệ cả ghi đồng thời. Conversation khác vẫn chạy song song.
- Không có bảng `conversation_runs`, `run_attempts`, `tool_executions` trong phạm vi hiện tại.

### Ghi user message kèm file một cách nguyên tử

Để cùng áp dụng quy tắc không sửa liên kết file sau terminal, SQL dùng **pending tạm thời trong transaction tạo user message**, rồi chuyển completed trước commit. Đây không phải trạng thái user nhìn thấy. Constraint trigger deferred từ chối nếu user vẫn pending khi commit.

```sql
BEGIN;
-- Service kiểm tra quyền, khóa conversation trước khi đọc/ghi.
SELECT pg_advisory_xact_lock(hashtextextended(:conversation_id::text, 42));
-- INSERT user với default pending, lấy id.
-- INSERT message_files cho những file đã upload thành công.
-- UPDATE user SET status = 'completed'.
-- Nếu cần, INSERT assistant default pending và cập nhật current_message_id.
COMMIT;
```

Không chuyển toàn bộ deferred constraints sang IMMEDIATE giữa bước insert user và finalize; nếu cần đổi chế độ thì đổi sau khi user completed. Import/copy message có file cũng stage pending, gắn file, finalize terminal trong một transaction. Message không có file có thể insert trực tiếp terminal khi import.

### Giới hạn đã chấp nhận

Worker chạy LLM bọc xử lý lỗi và lưu partial output khi bắt được lỗi; tín hiệu dừng có handler lưu tương tự. **Worker chết đột ngột thì bỏ qua ở giai đoạn này**: nội dung trong bộ nhớ có thể mất và message có thể còn pending/running. Không tạo recovery worker, heartbeat, lease LLM hay Redis recovery để giải quyết trường hợp đó. Vì quy tắc một active message, chat bị kẹt như vậy sẽ không nhận lượt mới cho đến khi được xử lý thủ công; đã chủ động chấp nhận chưa xây cơ chế tự xử lý.

Giai đoạn này không thiết kế thêm bảng queue/checkpoint/approval/usage hay cấu hình agent. Copy file vẫn có job riêng từ phase 1 vì đó là workflow S3, không phải lượt chạy LLM.

## 7. File rút gọn

```text
messages --< message_files >-- stored_files --> S3 object
                                  |
                                  +-- metadata JSONB
```

### stored_files

Giữ schema người dùng cung cấp và thêm metadata:

| Cột | Kiểu |
|---|---|
| `id` | UUID |
| `bucket`, `object_key` | TEXT |
| `original_name`, `content_type` | TEXT |
| `visibility` | TEXT: public/private |
| `size_bytes` | BIGINT |
| `checksum_sha256` | TEXT nullable |
| `uploaded_by` | UUID nullable, FK users |
| `metadata` | JSONB NOT NULL DEFAULT `{}` |
| `created_at`, `deleted_at` | TIMESTAMPTZ, deleted_at nullable |

Giữ các check về bucket/key, SHA-256, MIME, tên file, size, thời điểm xóa và prefix public/private. UNIQUE `(bucket, object_key)`. SQL không xác minh object S3 thật; backend xác minh upload thành công, byte/checksum và không ghi đè key cũ.

Object identity (bucket/key/tên/MIME/size/visibility) bất biến. Checksum NULL có thể điền lần đầu, giá trị đã xác minh không đổi. Không xóa mềm/xóa metadata khi còn message/snapshot/copy tham chiếu; xóa byte trên S3 cũng phải tuân thủ retention. Không lưu presigned URL lâu dài hoặc secret trong metadata.

`metadata` phải là object, có thể cập nhật khi bổ sung xử lý; không cấp quyền và không lặp các cột vật lý. Chưa tạo GIN index khi chưa có truy vấn cụ thể. Ví dụ mở rộng, **không bắt buộc phải có ngay**:

```json
{
  "image": {"width": 1920, "height": 1080},
  "extraction": {"page_count": 24, "language": "vi"},
  "rag": {"parser": "docling"}
}
```

Vector embedding và corpus chunk không nhét vào metadata. Khi làm RAG, thông tin phụ thuộc workspace/agent/index hoặc cần retry/query riêng có thể cần bảng riêng; cột metadata hiện tại không thay thế thiết kế RAG tương lai. Không tự thêm status xử lý file hay cấu trúc preview lúc này.

### message_files

Chỉ hai cột:

| Cột | Quan hệ |
|---|---|
| `message_id` | FK messages |
| `stored_file_id` | FK stored_files |

PK `(message_id, stored_file_id)`; index ngược `stored_file_id`. Một message có nhiều file, một file có thể dùng lại trong các message cùng owner/workspace. Conversation/workspace/owner suy qua message; không lặp lại ba cột này. Không còn `kind`, `status` hoặc ID của lớp files trung gian.

Trigger bảo vệ liên kết của message terminal, chỉ chấp nhận private object chưa xóa và không cho alias object sang owner/workspace khác. Scope hiện có được kiểm tra qua message, snapshot và reservation copy. Để bổ sung guard khi chưa có liên kết nào, object chat được ghi `uploaded_by` là chủ conversation; file agent tạo/copy được quy cho người yêu cầu. Trường uploaded_by vẫn nullable cho object ngoài chat và nghiệp vụ chung; NULL không đủ để gắn mới vào chat qua guard này.

`uploaded_by` là thông tin nguồn upload, **không phải quyền tải file**. Backend phải xác thực upload token/quyền workspace trước khi gắn file; database không biết người dùng HTTP hiện tại. File chưa gửi chưa có scope workspace bền vững trong bảng quan hệ này; luồng upload phải quản lý quyền phiên upload, và dọn object không được sử dụng theo chính sách sau này.

Để tải file: kiểm tra quyền owner trên conversation hoặc quyền link snapshot rồi mới đọc/cấp URL ngắn hạn. `fileId` trong AG-UI/attachments dùng `stored_files.id`, không tự cấp quyền; backend xác minh mọi tham chiếu file vật lý đều có liên kết tương ứng. API có thể trả `message.files` bằng join, không lưu lặp mảng authoritative trong messages.

## 8. Share snapshot và copy sau thay đổi file

Giữ các luật giai đoạn 1: cá nhân public, tổ chức chỉ nội bộ cùng tổ chức, snapshot toàn bộ cây, copy thành chat riêng và object vật lý mới; không chuyển cá nhân ↔ tổ chức.

- Chỉ tạo/cập nhật/publish snapshot khi không có message pending/running trong source conversation.
- Snapshot đã publish từ trước vẫn đọc được khi source chạy một lượt mới; thu hồi/expiry maintenance vẫn được phép trong lúc chạy.
- Backend khóa cùng conversation trước khi đọc tree, dựng payload, seal và publish trong một transaction.
- Snapshot giữ role, status terminal, content, attachments, nhánh hiện tại và file ở thời điểm chụp. SQL không tự thực hiện sao chép toàn bộ tree; backend đảm bảo đủ mọi nhánh và ID mapping.
- `share_snapshot_files.stored_file_id` trỏ thẳng stored_files; `share_snapshot_message_files` cũng đổi tên cột tương ứng.
- `share_snapshot_files.metadata` giữ **bản chụp subset metadata được phép chia sẻ**, do backend allowlist; không trả raw metadata có tham chiếu sandbox/provider/đường dẫn nội bộ. Sau seal bất biến, không lấy metadata live để thay thế.
- Copy mapping dùng `source_stored_file_id`, `target_stored_file_id`. Đích có UUID, bucket/key mới và checksum khớp; SQL không thực hiện S3 COPY hoặc kiểm chứng byte từ xa.
- Metadata đích lấy phần phù hợp từ snapshot; không sao chép sandbox session, provider handles, vector namespace hoặc runtime credentials của nguồn.
- Worker remap cả ID message, AG-UI bundle/tool calls và tham chiếu stored file trong content/attachments. Không copy live runtime.
- Copy job chỉ complete khi mọi file snapshot có mapping copied và file đích đã gắn message thuộc conversation đích, không còn message pending/running. Việc chứng minh **toàn bộ** cây message và mapping giống snapshot vẫn thuộc backend.
- Source xóa mềm/thu hồi share không ảnh hưởng bản copy đã hoàn thành. Job dở còn ẩn; cleanup/purge có đặc quyền chưa thiết kế vì không cho xóa message riêng.

## 9. Khóa, quyền và trách nhiệm tích hợp

- Writer service dùng READ COMMITTED, khóa conversation **trước** đọc/ghi:
  `pg_advisory_xact_lock(hashtextextended(conversation_id::text, 42))`.
- Trigger hỗ trợ bảo vệ dữ liệu nhưng không thay việc khóa trước khi đọc baseline. File writers khóa object để chống hai workspace cùng gắn một object đồng thời. Khi nhiều object, service lấy khóa theo thứ tự UUID ổn định để giảm deadlock; vẫn retry transaction khi database báo deadlock/serialization conflict.
- Trước khi gửi LLM, kiểm tra quyền, message parent và tạo placeholder assistant trong transaction ngắn; không giữ transaction database suốt thời gian chờ LLM.
- Runtime chỉ dùng kết nối backend được kiểm soát. Chưa cấu hình RLS/runtime DB roles; helper quyền không tự bảo vệ truy vấn viết sai hoặc DB owner tắt trigger.
- Owner/admin tổ chức và superuser không có quyền mặc định đọc chat riêng.
- Background title chống ghi đè tên user và chiến lược nâng SDK chưa thiết kế, không hứa đã giải quyết sau khi bỏ source/revision.

## 10. Kiểm chứng

Đã kiểm tra trên **PostgreSQL 18.6** ở cluster tạm riêng:

- Áp dụng toàn chuỗi schema và checks lịch sử theo đúng thứ tự: **108 assertions thành công**, trong đó **50 checks cho bản cuối**.
- Ba kiểm tra hai session đồng thời: chặn assistant active thứ hai; snapshot chờ writer rồi từ chối source đang chạy; cùng object không bị gắn đồng thời sang workspace khác.
- Preflight từ chối dữ liệu message cũ, rollback và giữ nguyên message/schema trước bước cuối.
- Phủ các thay đổi status, partial text, terminal immutability, cây message, folder/pin, metadata, scope file, share public/nội bộ và copy độc lập.

Chưa kiểm tra LLM thật, S3 thật, AG-UI SDK end-to-end, tải lớn hoặc backend ứng dụng. Không có migration production/backfill tự động. Các giới hạn này không được diễn giải thành tính năng đã hoàn thành.

## 11. Cơ sở kế thừa hai dự án

Đã đọc mã nguồn local trong `/home/lamhung/code/LibreChat` và `/home/lamhung/code/open-webui`:

- Open WebUI: pin/folder trực tiếp trên chat; bảng file riêng, chat_file và JSON file trong message. `file.meta` chứa mô tả, hash byte upload, collection_name; `file.data` có text trích xuất, status và error. Thiết kế mình chỉ dùng quan hệ message_files làm nguồn liên kết authoritative.
- LibreChat: content/attachments phong phú; file lưu storage/image/text/embedding/sandbox/artifact provenance. **Có status pending/ready/failed cho deferred preview**; không suy rằng LibreChat không theo dõi trạng thái file. Dự án mình chủ động bỏ file status theo phạm vi đã chọn.
- Dùng metadata mở rộng khi cần, không sao chép toàn bộ cấu trúc runtime/RAG của hai dự án vào baseline hiện tại.

Các nguồn đã khảo sát: [LibreChat](../database_research/librechat-full-schema.md), [Open WebUI](../database_research/open-webui-official-schema.md), [đối chiếu](../database_research/openwebui-vs-librechat.md). Nội dung hai chat tham khảo về AG-UI và lịch sử agent đã được đọc ở phần thảo luận trước, xem nguồn trong [bản phần 1](phase-2-part-1-decisions.md).
