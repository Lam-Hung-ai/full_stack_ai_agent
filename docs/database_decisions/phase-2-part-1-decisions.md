# Giai đoạn 2 — phần 1 đã chốt: conversation, cây message và liên kết file

> **Đã có bản chốt mới:** xem [giai đoạn 2 hoàn tất](phase-2-decisions.md). Tài liệu này giữ làm lịch sử; trạng thái message, pin/folder và cấu trúc file tại đây đã được thay thế bởi bước SQL cuối.

Ngày ghi: **28/10/2026**, Asia/Ho_Chi_Minh.

Đây là phần đã thống nhất trong cuộc thảo luận, được ghi lại theo yêu cầu người dùng trước khi bàn tiếp. Không coi đây là toàn bộ giai đoạn 2. Chưa áp dụng vào database ứng dụng hoặc tích hợp backend.

## 1. Các file và thứ tự áp dụng

- [`phase-1-schema.sql`](phase-1-schema.sql): bản nền lịch sử giai đoạn 1, giữ nguyên.
- [`phase-2-part-1-schema.sql`](phase-2-part-1-schema.sql): thay đổi áp dụng **sau giai đoạn 1**, trong cùng schema `chat_app`.
- [`phase-2-part-1-checks.sql`](phase-2-part-1-checks.sql): kiểm tra cấu trúc mới, fixture rollback.
- Tài liệu này ưu tiên hơn phần conversation/message/file tương ứng trong [quyết định giai đoạn 1](phase-1-decisions.md).

SQL yêu cầu PostgreSQL 18+ như giai đoạn 1. Đây là bước tiến hóa baseline cho database thiết kế/scratch, không phải migration dữ liệu production đã hoàn chỉnh. Script chủ động từ chối khi đã có message, file, snapshot, copy job hoặc conversation đang copy/thất bại: không đoán bucket S3, không âm thầm chuyển transcript cũ thành AG-UI và không sửa snapshot đã seal. Nếu có dữ liệu như vậy cần lập backfill riêng trước. Khi từ chối, transaction rollback, dữ liệu cũ được giữ nguyên.

## 2. Những yêu cầu đã chốt

### Conversation

- Bỏ `title_source`, `revision`, `availability_status`.
- Giai đoạn 1 dùng tên `status` cho trạng thái copy của conversation; giai đoạn 2 cũng bỏ cột này để không giữ lại cùng ý nghĩa dưới tên khác.
- Copy job là nơi duy nhất giữ pending/copying/completed/failed/cancelled. Các helper đọc và share được cập nhật để không lộ destination chưa hoàn tất.
- Không thêm history JSON hoặc mảng ID message vào conversation.

### Message

- SQL role chỉ `user`, `assistant`.
- Bỏ `position`, `revision`, `finish_reason`, `error_code`, `error_message`, `origin`, `completed_at`.
- Không cho xóa message riêng lẻ. SQL chặn DELETE và TRUNCATE trên bảng message; soft-delete toàn conversation vẫn giữ quy tắc giai đoạn 1.
- Sửa câu hỏi hoặc regenerate tạo message sibling/nhánh mới; không reparent message cũ để làm thay đổi lịch sử.
- `content` dùng JSONB theo hướng AG-UI; `attachments` dùng JSONB lấy cảm hứng từ LibreChat.
- Cho phép lưu toàn bộ tool output trùng ở cả `content` và `attachments`, theo yêu cầu tường minh của người dùng.

### Sidebar và nhãn

- `conversation_user_states` không có `last_read_at`, `last_opened_at`.
- Không tạo `conversation_tags`, `conversation_tag_assignments`.
- Giữ phần trạng thái cơ bản `pinned_at`, `archived_at` theo user. FK gắn user với chủ conversation hiện tại; đây không phải access grant.
- Folder/project và cấu trúc thư mục chưa được duyệt rõ, nên không tạo bảng folder hoặc cột folder trong phần SQL này.

### File

- Không có `messages.files` JSONB vật lý.
- File dùng bảng nối riêng theo hướng Open WebUI.
- Metadata object S3 nằm trong `stored_files` theo schema người dùng đưa.
- Giữ lớp `files` có sẵn ở giai đoạn 1 để đại diện quyền sở hữu/phạm vi workspace; metadata vật lý chuyển sang `stored_files`.

## 3. Bảng conversations sau thay đổi

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | UUID | Khóa chính |
| `workspace_id` | UUID | FK workspace |
| `owner_user_id` | UUID | Chủ conversation |
| `title` | TEXT | Tiêu đề |
| `current_message_id` | UUID nullable | Message cuối của đường hội thoại được lưu để mở lại |
| `deleted_at` | TIMESTAMPTZ nullable | Xóa mềm cả conversation |
| `created_at` | TIMESTAMPTZ | Thời điểm tạo |
| `updated_at` | TIMESTAMPTZ | Thời điểm cập nhật |

Giữ FK composite để current message thuộc cùng conversation. Workspace và owner bất biến. Bỏ trạng thái copy khỏi bảng này nhưng không bỏ yêu cầu giấu bản copy dở: `can_read_conversation` kiểm tra copy job đích, chỉ cho đọc khi completed hoặc không phải destination copy.

`title_revision` và `last_message_at` từng được đề xuất nhưng chưa có trong phase 1 và chưa được duyệt, nên chưa tự thêm. Không thể tuyên bố title tự động đã được bảo vệ sau khi bỏ source/revision; cơ chế chống AI ghi đè title user sẽ cần bàn ở phần background task.

## 4. Bảng messages sau thay đổi

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | UUID | ID dòng message của ứng dụng |
| `conversation_id` | UUID | FK conversation |
| `parent_message_id` | UUID nullable | Parent cùng conversation |
| `role` | TEXT | Chỉ user/assistant |
| `content` | JSONB | Danh sách đầy đủ message AG-UI thuộc một message hiển thị |
| `attachments` | JSONB | Mảng nguồn/citation/artifact và tool output bổ sung |
| `created_at` | TIMESTAMPTZ | Thời điểm tạo |
| `updated_at` | TIMESTAMPTZ | Thời điểm cập nhật |

Không thêm `created_by_user_id`, `content_version` hay status message trong phần chốt này: chúng vẫn là đề xuất cần bàn tiếp. Status của file/copy job giai đoạn 1 không bị bỏ theo yêu cầu bỏ status conversation.

### Hai lớp role và ID

Một dòng assistant hiển thị có thể chứa nhiều message protocol: assistant gọi tool, tool trả kết quả, assistant trả lời. Cột role database vẫn là assistant, còn role bên trong JSON giữ đúng AG-UI.

```json
[
  {
    "id": "agui-assistant-1",
    "role": "assistant",
    "toolCalls": [
      {
        "id": "call-1",
        "type": "function",
        "function": {"name": "file_search", "arguments": "{\"query\":\"doanh thu\"}"}
      }
    ]
  },
  {"id": "agui-tool-1", "role": "tool", "toolCallId": "call-1", "content": "Doanh thu tăng 20%."},
  {"id": "agui-assistant-2", "role": "assistant", "content": "Theo tài liệu, doanh thu tăng 20%."}
]
```

User row chứa một message AG-UI user, với content text hoặc multimodal. Assistant row cho phép assistant/tool/reasoning/activity; không lưu system/developer prompt nội bộ vào transcript này. Empty assistant bundle được phép như placeholder; lifecycle/finalize còn chờ bàn phần run/message status. Chỉ lưu reasoning được phép công bố, không mặc định lấy mọi nội dung riêng của runtime.

ID dòng database khác ID các message AG-UI trong bundle. Khi snapshot/copy phải remap đồng bộ ID message nội bộ, tool call/result và tham chiếu file/citation; role và nội dung vẫn giữ ý nghĩa gốc. Không sao chép nguyên ID rồi dùng chúng làm danh tính độc lập của bản copy.

Không lưu log token SSE làm transcript. Streaming writer tích lũy message rồi persist ở boundary theo chính sách sẽ chốt tiếp. Serialization JSON và chuyển qua LangChain là hai việc khác nhau: không dùng round-trip LangChain để ghi đè dữ liệu gốc vì adapter có thể mất metadata hoặc bỏ loại message.

### Validate

CHECK SQL chỉ kiểm tra hình dạng ngoài: mảng, object có ID/role, role hợp lệ, ID không trùng trong bundle. Nó không kiểm chứng đầy đủ mọi kiểu AG-UI, toolCalls, multimodal hoặc chuỗi liên kết tool. Backend phải pin SDK version, validate bằng `ag_ui.core.Message`/Pydantic, kiểm tra liên kết và chuẩn hóa alias như `toolCalls`, `toolCallId`.

Thiết kế không bảo đảm đổi SDK tùy ý vẫn đọc được mọi lịch sử. Chiến lược version payload/migration chưa chốt; cần bàn trước khi nâng protocol.

## 5. Attachments và dữ liệu lặp

Ví dụ attachments tương ứng:

```json
[
  {
    "type": "file_search",
    "toolCallId": "call-1",
    "output": "Doanh thu tăng 20%.",
    "sources": [
      {"citationId": "source-1", "fileId": "uuid-file-resource", "pages": [5], "excerpt": "Doanh thu tăng 20%."}
    ]
  }
]
```

- Có thể lặp toàn bộ tool output ở đây và trong `content`; không có constraint cấm lặp.
- `content` dùng dựng diễn biến/context, `attachments` thuận tiện render artifact/citation.
- Khi gửi lại model chỉ lấy kết quả từ `content` một lần.
- Backend cập nhật hai phần trong cùng transaction khi persist boundary; database không tự so sánh/gộp JSON hoặc tự đồng bộ hai trường.
- Attachments không phải một kiểu message AG-UI chuẩn; đây là contract ứng dụng lấy cảm hứng LibreChat.
- `fileId` trong JSON không cấp quyền truy cập. Mọi file vật lý được dùng làm attachment/citation phải có quan hệ hợp lệ trong bảng nối; kiểm tra completeness đó do backend thực hiện, không dựa vào UUID trong JSON.
- Snapshot chứa cả content và attachments; phần snapshot đã seal không được sửa. Bản copy phải copy cả hai, không chỉ text câu trả lời.

## 6. Cây message khi không có position

- Parent composite FK vẫn bảo đảm cùng conversation và tồn tại.
- Trigger khóa theo conversation rồi kiểm tra đệ quy đường tổ tiên, phát hiện chu trình kể cả khi nhiều dòng cùng insert với FK deferred.
- ID, conversation, parent, role và created_at của message không được sửa. Edit/regenerate tạo dòng mới; nội dung đang sinh vẫn có thể cập nhật, chưa có quy tắc terminal vì lifecycle còn chưa chốt.
- Thứ tự sibling/hiển thị ổn định dùng `(created_at, id)`. Cursor phân trang phải chứa đủ hai giá trị. Đây là thứ tự hiển thị, không chứng minh thứ tự nhân quả hoặc commit của các writer đồng thời.
- Context đi theo parent, không lấy mọi dòng có created_at nhỏ hơn một mốc.
- Không lưu mảng children trong DB. Truy vấn theo parent có index `(conversation_id, parent_message_id)`.
- Service phải dùng cùng lock `pg_advisory_xact_lock(hashtextextended(conversation_id::text, 42))` **trước khi đọc** baseline để snapshot. Trigger chỉ khóa lúc ghi, không biến mọi luồng đọc tùy ý thành snapshot nguyên tử.
- Khi gửi luôn mang parent rõ ràng, không tự suy từ con trỏ global vừa bị một tab khác thay đổi. Chính sách ghi nhớ nhánh nhiều tab và kiểm soát xung đột sẽ được bàn tiếp.

## 7. File: stored_files, files, chat_files

```text
messages -> chat_files -> files -> stored_files -> S3 object
snapshots -> share_snapshot_files -> files -> stored_files
```

### stored_files

Giữ các trường schema người dùng cung cấp: `id`, `bucket`, `object_key`, `original_name`, `content_type`, `visibility`, `size_bytes`, `checksum_sha256`, `uploaded_by`, `created_at`, `deleted_at`.

- UNIQUE `(bucket, object_key)`; prefix public/private khớp visibility; check cơ bản về tên, size, SHA-256 và thời gian.
- Bổ sung FK `uploaded_by -> users.id ON DELETE SET NULL` (index partial giữ nguyên).
- Object identity/metadata vật lý bất biến sau tạo. Checksum nullable có thể được điền lần đầu sau khi kiểm chứng, nhưng giá trị đã có không được thay đổi.
- Validation bucket chỉ là kiểm tra cơ bản theo schema đầu vào; backend còn kiểm tra quy tắc storage vendor và object thật.
- Không lưu presigned URL làm địa chỉ bền vững, không lưu base64 file lớn vào transcript mặc định.

### files — giữ vai trò tài nguyên chat theo workspace

Các trường: `id`, `workspace_id`, `owner_user_id`, `stored_file_id`, `status`, `created_at`, `updated_at`.

Thông tin filename/MIME/size/checksum/storage key chuyển sang `stored_files`, không lưu lặp ở lớp này. `stored_file_id` unique để một object không bị alias sang nhiều workspace một cách vô tình. Upload user không thay thế owner/scope của tài nguyên.

File chat dùng object **private**; public share vẫn kiểm tra link ở backend rồi cấp tải. Không tự đổi object thành public khi share public. Bảng stored_files vẫn hỗ trợ public cho các mục đích ngoài file chat.

### chat_files — đổi tên message_files ở giai đoạn 1

Các trường: `id` (unique), `conversation_id`, `message_id`, `workspace_id`, `file_id`, `kind`, `created_at`. Giữ primary key `(message_id, file_id)`; ID riêng không thay unique chống trùng. `kind` là input/output; giai đoạn này backend quyết định giá trị theo luồng, chưa thêm role constraint cứng cho bảng nối.

- Một file được dùng ở nhiều message, khác với UNIQUE theo chat/file của Open WebUI.
- FK bảo đảm conversation/message/file cùng phạm vi.
- Không lặp danh sách file authoritative trong JSON message. API có thể trả trường files bằng join.
- Object chưa được xóa mềm/xóa metadata khi còn `files` tham chiếu; file resource cũng được snapshot/job bảo vệ bằng FK. Xóa byte S3 ngoài DB vẫn cần cleanup worker tuân thủ retention.

## 8. Tương thích chia sẻ và copy giai đoạn 1

Giữ luật cá nhân public, tổ chức chỉ nội bộ, snapshot toàn cây và copy độc lập.

- Snapshot message bỏ position, chỉ user/assistant, thêm attachments và cùng hình dạng AG-UI bundle.
- Bản copy được giấu dựa vào copy job, không còn trạng thái trên conversation. Tạo destination rỗng và job trong cùng transaction trước khi thêm message/file.
- Copy target đã có message hoặc đã được share không được tái dùng làm destination mới.
- Copy file tạo `stored_files` mới với bucket/key khác, resource `files` mới và link mới. Guard mapping xác minh metadata giống nhau và checksum có giá trị/khớp khi đánh dấu copied.
- SQL không thực hiện COPY object S3 hoặc tính checksum thật; worker chịu trách nhiệm và không chỉ tin giá trị client gửi.
- Khi job completed, helper cho đọc destination. Backend vẫn phải xác minh đủ transcript, remap JSON, đủ attachments và kiểm tra lại quyền/lease khi finalize. CHECK hiện tại chưa chứng minh bản copy có toàn bộ cây giống snapshot.
- Source xóa mềm/thu hồi không xóa bản copy completed. Share tổ chức vẫn yêu cầu membership còn hoạt động, không có admin bypass đọc source.
- Không cho xóa message đồng nghĩa cleanup job thất bại không được tự DELETE một phần transcript. Giai đoạn này giữ destination dở ở trạng thái ẩn qua job; purge có đặc quyền chưa được thiết kế.

## 9. Những phần chưa chốt / chưa ghi SQL

| Phần | Trạng thái |
|---|---|
| Title revision/source thay thế, background title chống ghi đè | Chưa chốt sau yêu cầu bỏ các cột |
| Status message và thời điểm đóng nội dung terminal | Chưa chốt |
| Version cấu trúc content/SDK migration | Chưa chốt |
| Folder/project và thứ bậc | Chưa duyệt rõ, không tạo bảng |
| Trạng thái chọn nhánh giữa tab và xung đột | Có hướng parent tường minh, policy chi tiết còn bàn |
| Run/attempt, queue, lease, cancel, approval | Bàn phần sau |
| Tool execution, usage/model thực tế, agent version | Bàn phần sau |
| Checkpoint LangGraph, Redis retention/replay | Bàn phần sau |
| RLS và DB role runtime | Chưa tích hợp, như giới hạn giai đoạn 1 |

Không có thêm bảng tags hoặc trường người dùng đã yêu cầu bỏ dưới một tên tương đương. Status file và copy job là lifecycle riêng đã có từ giai đoạn 1.

## 10. Kiểm chứng và cách chạy

Trên database scratch **mới**:

```bash
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-part-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-part-1-checks.sql
```

`phase-1-checks.sql` dùng cấu trúc cũ, chạy trước khi áp dụng phase 2 nếu muốn kiểm tra baseline. Sau phase 2 dùng bộ checks tương ứng, không chạy lại checks cũ rồi hiểu lỗi là lỗi migration.

Đã áp dụng phase 1 rồi phase 2 trên PostgreSQL 18.6 trong cluster tạm riêng, chạy 30 kiểm tra thành công: field/role removals, branches/cycle/no-delete, JSON tool output lặp, sidebar ownership, file mapping/scope/immutability, public/internal sharing, snapshot attachments, copy visibility và độc lập với xóa nguồn. Kiểm tra bổ sung preflight từ chối dữ liệu cũ và rollback được thực hiện riêng.

Chưa thử storage S3 thật, HTTP auth, load test, executor, SDK conversion end-to-end hoặc chạy database ứng dụng. SQL chỉ check hình dạng JSON ngoài, không được mô tả là validator toàn bộ AG-UI protocol. Private-by-default vẫn cần backend dùng đúng hàm quyền; đây chưa phải cấu hình RLS chống mọi truy vấn viết sai.

## 11. Nguồn tham khảo

- [Khảo sát LibreChat](../database_research/librechat-full-schema.md): content parts, artifact/citation attachments, file lifecycle.
- [Khảo sát Open WebUI](../database_research/open-webui-official-schema.md): bảng nối chat/file và transcript riêng.
- Chat **Tìm cách lưu lịch sử agent** (`01a17c47-19c2-7691-8408-838451673e0c`): phân biệt files/attachments và metadata citation. Đã đọc nội dung chat trước khi sử dụng.
- Chat **Kiểm tra chuyển AG-UI sang JSON** (`01a18196-8e21-76b0-887b-fa3d09406f94`): JSON round-trip, multimodal và giới hạn adapter LangChain. Đã đọc nội dung chat trước khi sử dụng.
- [AG-UI Message Types](https://docs.ag-ui.com/sdk/python/core/types), [multimodal](https://docs.ag-ui.com/sdk/python/core/multimodal-inputs): contract protocol; pin phiên bản khi tích hợp.
