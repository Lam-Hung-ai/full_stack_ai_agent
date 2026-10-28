# Open WebUI vs LibreChat — so sánh database

Ngày ghi: 2026-10-27.

Tài liệu này so sánh hai database trên bốn trục: **tính năng**, **khả năng mở rộng**, **độ sạch (clean)** và **tổ chức hợp lý**. Nguồn là bốn tài liệu khảo sát đã có trong thư mục này, không khảo sát lại từ đầu:

| Dự án | Bản liệt kê schema | Bản đọc source |
|---|---|---|
| Open WebUI | [open-webui-official-schema.md](./open-webui-official-schema.md) — 47 bảng theo docs chính thức (tới v0.12.0) | [open-webui.md](./open-webui.md) — commit `33c1978d5bad52a31df75ea55143025dfad18d16` |
| LibreChat | [librechat-full-schema.md](./librechat-full-schema.md) — 53 model + 9 collection raw driver | [librechat.md](./librechat.md) — commit `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5`, `v0.8.9-rc1` |

**Lưu ý về tính đối xứng của nguồn.** Tài liệu Open WebUI phủ bảng dựa trên trang docs **community contribution** mà chính trang đó khai là không được team hỗ trợ; tài liệu LibreChat dựng **từ source**. Vì vậy các nhận định về "cột này không ai ghi" ở Open WebUI là lời của trang docs, còn ở LibreChat là kết quả grep source. Chỗ nào Open WebUI được kiểm chứng bằng source thì đã dẫn [open-webui.md](./open-webui.md).

---

## 1. Cách chấm

Bốn trục được định nghĩa trước khi đọc, để tránh chấm theo ấn tượng:

| Trục | Định nghĩa dùng trong tài liệu này |
|---|---|
| **Tính năng** | Số miền nghiệp vụ mà schema thực sự mô hình hóa, và độ sâu của từng miền |
| **Khả năng mở rộng** | Tách làm hai: **(a) mở rộng tải** — multi-tenant, nhiều pod, đồng thời; **(b) mở rộng schema** — thêm/đổi cấu trúc mà không vỡ |
| **Database clean** | Bốn chỉ số: toàn vẹn tham chiếu, số invariant do chính database giữ, nguyên tắc một-sự-thật-một-chỗ, lượng cột/bảng chết |
| **Tổ chức hợp lý** | Nhất quán đặt tên và kiểu, nhóm theo miền, mẫu thiết kế có lặp lại, có god table hay không, schema có tự giải thích không |

Các con số đếm được dùng làm bằng chứng:

| Chỉ số | Open WebUI | LibreChat |
|---|---|---|
| Đơn vị lưu trữ | 47 bảng | 53 model Mongoose + 9 collection raw driver |
| Lần nhắc `UNIQUE` trong tài liệu schema | 25 | 79 |
| Partial index | 2 | 33 |
| TTL index | 0 | 40 |
| Dòng khai `FOREIGN KEY` | 20 (trên 47 bảng) | **0** |
| Cột `user_id` có FK tới `user.id` | **3 / ~40** | không áp dụng |
| Cột được đánh dấu "không code path nào ghi" | 4 mục (≈9 cột) | — (tài liệu LC không dùng cách đánh dấu này) |

---

## 2. Hai kiến trúc

| Khía cạnh | Open WebUI | LibreChat |
|---|---|---|
| Engine | SQLite mặc định (`data/webui.db`), PostgreSQL tùy chọn | MongoDB (`MONGO_URI`), Amazon DocumentDB là target hạng hai |
| ORM/ODM | SQLAlchemy, async session runtime + sync engine cho startup | Mongoose, schema khai bằng TypeScript |
| Migration | **Alembic**, cây tuần tự, cộng bảng `migrate_history` | **Không có cây migration.** Schema là nguồn sự thật; index build lúc `createModels()`; thư mục `migrations/` chỉ vài tác vụ one-shot gọi tay |
| Timestamp | Epoch `BigInteger` — **trộn đơn vị**: giây ở nhóm chat, nanosecond ở `channel`/`message`/`app` | `Date` qua `{ timestamps: true }`; vài schema cố ý bỏ (`auditLog` không có `updatedAt`) |
| Khóa ngoại | Có, nhưng thưa | **Không có bất kỳ FK cấp database nào.** `ref:` chỉ là metadata cho `populate()` |
| Multi-tenant | **Không có khái niệm** | `tenantId: String` + Mongoose plugin tiêm filter, 43/53 model |
| Store ngoài SQL | Redis (response cache), vector DB cho memory | MeiliSearch (mirror tìm kiếm), RAG API + vector DB, Redis |
| Mã hóa at rest | SQLCipher **đã gỡ ở v0.9.0**; khuyến nghị dùng filesystem mã hóa hoặc PostgreSQL | Mã hóa ở tầng ứng dụng cho một số field; `action.metadata.api_key` là String thường |

---

## 3. Open WebUI — ưu điểm

### 3.1. Có migration thật, có đường tiến hóa

Alembic với revision ID truy được. Những thay đổi lớn đều để lại dấu vết kiểm tra được:

- `b10670c03dd5` (v0.6.41): tách bảng `api_key`, copy mọi key rồi **drop cột `user.api_key`**; thay cột text `oauth_sub` bằng JSON `oauth` để một tài khoản giữ subject của nhiều IdP.
- `3ff2c63645b8` (v0.10.0): chuyển `config` từ **một dòng blob JSON** sang **per-key** (`key` PK dot-notation, `value` JSON), giữ bảng cũ dưới tên `config_old` để đảo ngược được.
- `8452d01d26d7`: tạo `chat_message` và backfill từ history JSON, **batch 5.000 message, dùng savepoint**, lỗi batch thì thử từng dòng để cô lập dòng hỏng.
- `f0bd01a18a3d`: thêm partial unique index `uq_user_email_lower` trên `lower(email)`; nâng cấp gặp hai tài khoản chỉ khác hoa thường thì **dừng lại và nêu tên chúng** thay vì tự chọn.
- `6d09d1bf1f23`: viết lại các dòng `oauth` bị ghi sai kiểu (text thay vì object) lúc startup, không đụng dòng khác.

Đây là thứ LibreChat không có, và là lợi thế dài hạn lớn nhất của Open WebUI.

### 3.2. Mẫu versioning tài nguyên lặp lại nhất quán 5 lần

`model`, `tool`, `function`, `prompt`, `skill` đều theo **đúng một mẫu**: bảng "live" có cột `version_id`, cộng bảng `*_history` với `(id, <resource>_id, parent_id, snapshot JSON, user_id, commit_message, created_at)`.

Và mẫu này được áp dụng **có suy nghĩ**, không máy móc: snapshot chỉ giữ nội dung, còn **cờ ẩn, công tắc bật/tắt, valves và access grant ở lại dòng live** — vì rollback nội dung không nên rollback trạng thái vận hành. Migration tạo các bảng này (`e7b9d4a023bc`, `f8c0e5b134cd`, `d6a8c3f912ab`) đều seed một version khởi đầu cho mọi dòng hiện có.

So sánh: LibreChat nhúng `agent.versions: [Mixed]` ngay trong document agent, không biên, rủi ro trần 16 MB.

### 3.3. Tách access control ra bảng riêng, có UNIQUE đầy đủ

`access_grant` thay cột JSON `access_control` từng nhúng trong từng bảng resource. UNIQUE `(resource_type, resource_id, principal_type, principal_id, permission)` + index theo cả hai chiều `(resource_type, resource_id)` và `(principal_type, principal_id)`.

Thiết kế principal có ba giá trị với ngữ nghĩa phân biệt rõ:

- `user` + `principal_id = '*'` = **mọi user đã đăng nhập**, không tới được khách.
- `anyone` (v0.11.0) = không cần đăng nhập, **chỉ tồn tại ở đúng tổ hợp** `anyone`/`*`/`read` và **chỉ cho `resource_type = 'shared_chat'`**; mọi resource khác strip nó đi.
- Grant cấp group **kế thừa xuống subgroup**; xóa group xóa luôn grant của nó.

### 3.4. Vài bảng nối được thiết kế có lý lẽ viết ra

`chat_file` có ba lý do được ghi thẳng trong docs: (1) hiệu năng — trước đó file nhúng trong object message nên phải duyệt từng message; (2) nhất quán — single source of truth khi chạy nhiều node; (3) chống trùng — UNIQUE ở mức database đáng tin hơn kiểm tra ở tầng ứng dụng. `channel_file` đi xa hơn: **cả ba FK đều cascade**, kể cả `message_id`, nên xóa message cũng tháo liên kết file.

### 3.5. Index theo truy vấn thật, không phải theo cột

Từ [open-webui.md](./open-webui.md) §3:

| Access pattern | Index |
|---|---|
| Sidebar theo owner + trạng thái | `(user_id, pinned)`, `(user_id, archived)` |
| Tìm con của một message | `(chat_id, parent_id)` |
| Tìm assistant chưa sinh xong | `(chat_id, role, done)` |
| Usage theo model/user và thời gian | `(model_id, created_at)`, `(user_id, created_at)` |
| Timer đang chờ | **Partial index** `(user_id, timer_at)` với `timer_at IS NOT NULL`, khai cho cả SQLite và PostgreSQL |
| File đang xử lý trong một knowledge base | **Partial index** `file_pending_knowledge_idx` phủ `data.status ∈ {pending, processing}` |

Index `(user_id, group_id)` trên `group_member` có ghi chú đáng chú ý: unique constraint dẫn đầu bằng `group_id` **không trả lời được** câu "user này thuộc group nào", và thiếu index này thì **mọi** kiểm tra permission phải quét toàn bảng membership — chi phí theo tổng membership của cả instance chứ không theo riêng user đó.

### 3.6. Ghi history có tuần tự hóa tường minh

`_chat_transaction`: SQLite dùng `BEGIN IMMEDIATE`, PostgreSQL đọc Chat với `FOR UPDATE`, rồi cập nhật trong cùng transaction. Điều này **tránh mất cập nhật** khi nhiều writer sửa cùng một chat — một vấn đề thật mà nhiều dự án bỏ qua. (Đánh đổi xem §4.5.)

### 3.7. Đặt tên và hình dạng bảng rất dễ đoán

snake_case, bảng số ít, bộ cột lặp đều `id` / `user_id` / `created_at` / `updated_at` / `data` / `meta`. Đọc tên bảng là đoán được gần đúng cấu trúc. Nhóm theo miền sạch: auth → chat → channel → calendar/automation → file/knowledge → workspace → system.

### 3.8. Mã hóa field nhạy cảm ở nơi cần

`oauth_session.token` chứa token set của provider, **mã hóa at rest bằng Fernet** trước khi ghi; key từ `OAUTH_SESSION_TOKEN_ENCRYPTION_KEY`, fallback `WEBUI_SECRET_KEY`, tự hash SHA-256 + base64 nếu key chưa đủ 44 ký tự. `app.api_key` và credential kết nối trong `app.data` cũng mã hóa.

---

## 4. Open WebUI — nhược điểm

### 4.1. Không có khái niệm tổ chức / tenant

Chỉ có `user` và `group` (có `parent_group_id` để lồng nhau). Không có bảng organization, không có cột tenant, không có cơ chế cô lập. Toàn bộ instance là một không gian dữ liệu.

Với bài toán của dự án mình — database tích hợp người dùng **và tổ chức** — Open WebUI **không cung cấp bằng chứng gì cả**. Đây là nhược điểm quyết định, không phải nhược điểm nhỏ.

### 4.2. Dual write toàn bộ blob history

Đây là khiếm khuyết nặng nhất của schema này.

Migration `8452d01d26d7` thêm `chat_message` để chuẩn hóa transcript, nhưng **blob `chat.chat` không bị bỏ**. Writer vẫn ghi cả hai. Reader `get_messages_map_by_chat_id` ưu tiên bảng message, không có row thì đọc history JSON rồi backfill, thiếu parent thì ghép phần thiếu từ JSON rồi backfill.

Kết luận chính xác là **"chuẩn hóa thêm một lớp truy vấn và duy trì tương thích"**, không phải "đã bỏ blob". Hệ quả:

- Mỗi lần cập nhật transcript ghi lại một blob JSON có kích thước theo độ dài hội thoại → khuếch đại ghi `O(n)`.
- Blob và row có thể lệch nhau; reader phải có logic self-heal, tức là code đã thừa nhận khả năng lệch.
- **Chat search đọc tập store khác nhau tùy backend**: trên PostgreSQL match `chat_message.content` *cùng với* `history.messages` và mảng `messages` cũ trong blob; trên SQLite chỉ match hai vị trí JSON. Nghĩa là **cùng một truy vấn cho kết quả khác nhau trên hai backend được hỗ trợ**.

### 4.3. Toàn vẹn tham chiếu rất mỏng

20 dòng khai `FOREIGN KEY` trên 47 bảng. Trong khoảng 40 cột `user_id`, **chỉ 3 cột có FK tới `user.id`**: `api_key.user_id`, `group_member.user_id`, `oauth_session.user_id`.

Không có FK: `chat.user_id`, `chat_message.user_id`, `shared_chat.user_id`, `feedback.user_id`, `memory.user_id`, `knowledge.user_id`, `calendar.user_id`, `calendar_event.user_id`, `note.user_id`, `file.user_id`, `channel.user_id`, `message.user_id`, `app.user_id`, `automation.user_id`, và mọi `*_history.user_id`.

Hệ quả cụ thể, chính docs ghi lại: **xóa tài khoản user để lại dòng `channel_member` của họ**. Danh sách thành viên, bộ đếm, và truy vấn tìm DM đều phải tự bỏ qua dòng có `user_id` không còn khớp tài khoản nào — tức dọn dẹp bằng filter ở mọi đường đọc thay vì bằng một ràng buộc.

Nặng hơn: **cây message không thể có FK**. PK của `chat_message` là chuỗi ghép `chat_id-message_id`, còn `parent_id` giữ ID message theo history — hai không gian khóa khác nhau, nên `parent_id` không trỏ được tới `chat_message.id`. `chat.current_message_id` cũng chỉ là con trỏ logic. Cấu trúc cốt lõi nhất của sản phẩm không được database bảo vệ.

`automation.folder_id` còn là một trường hợp riêng: **cố ý không phải FK** — xóa folder thì xóa giá trị cột trên các automation của chủ đó, và một lần chạy mà folder biến mất giữa chừng sẽ đặt chat ra ngoài mọi folder.

### 4.4. Cột chết và bảng legacy không bao giờ dọn

Chính trang docs đánh dấu **"có trong schema nhưng không code path nào ghi"** ở 4 mục:

| Vị trí | Cột |
|---|---|
| `api_key` | `data`, `expires_at`, `last_used_at` — tra cứu key chỉ join trên `key`, **không xét `expires_at`** |
| `channel` | `archived_at`, `archived_by`, `deleted_at`, `deleted_by`, `updated_by` (5 cột) |
| `user` | `presence_state` — vẫn được trả về trong danh sách thành viên channel và payload socket |
| `channel_member` | `is_channel_pinned` (có setter `Channels.pin_channel` nhưng **không ai gọi**) |

Trường hợp `channel` đặc biệt mỉa mai: truy vấn liệt kê **chỉ trả dòng có cả `archived_at` và `deleted_at` null**, tức schema được định hình cho soft delete, nhưng xóa channel là xóa hẳn dòng — nên filter `deleted_at` không bao giờ loại trừ được gì.

Và một cột chết gây **lỗi logic thật**: `channel_member.role` không nơi nào ghi `'manager'` (membership user để null, membership app ghi `'member'`), nên phép kiểm tra "có phải manager không" **không bao giờ khớp**. Các hành động chỉ-manager — xem và tạo channel webhook — rơi xuống hai nhánh còn lại: owner của channel, hoặc admin instance.

Bảng và cột legacy không bao giờ drop: `document` (migrate sang `knowledge` ở `6a39f3d8e55c`, **không migration nào drop bảng**), `chatidtag` (migrate sang `chat.meta.tags` ở `1af9b942657b`, **để nguyên các dòng**), `config_old` (đổi tên, không drop), cột `chat.old_chat` (backup blob JSON gốc dạng text, lưới an toàn của migration, không thuộc model và không đọc lúc runtime).

### 4.5. Khóa ghi thô

`_chat_transaction` tuần tự hóa đúng, nhưng phạm vi là **cả dòng chat**. Chat có nhiều thao tác sẽ tranh cùng một row lock; trên SQLite phạm vi khóa ghi còn rộng hơn PostgreSQL. `edit_message_output` cũng giữ khóa khi sửa tool state.

Không có bất kỳ cơ chế đồng thời mịn hơn: không lease, không fencing token, không partial unique làm hạn mức, không bộ cấp số thứ tự. So với LibreChat đây là khoảng cách lớn.

### 4.6. Thực thi nằm trong RAM của pod

Từ [open-webui.md](./open-webui.md) §6.3:

- Thực thi là `asyncio.create_task` trong RAM của pod sở hữu. Task registry và heartbeat **không biến nó thành durable queue**.
- Stop gửi Redis pub/sub; pub/sub **không phải durable cancel intent có ACK**.
- Pod chết thì coroutine mất; không có bằng chứng về tự dựng lại từ checkpoint.
- Redis mất hoặc hết TTL có thể mất partial chưa finalize; SQL không được cập nhật mọi token.
- Response TTL mặc định 3.600 giây **nhưng** lookup còn phụ thuộc task đang active trong registry — nên TTL không phải lời hứa xem lại được partial trong đủ một giờ.

Đây là giới hạn kiến trúc, không phải giới hạn schema, nhưng nó quyết định schema được dùng như thế nào.

### 4.7. `data` và `meta` JSON ở gần như mọi bảng

`group`, `chat`, `chat_message`, `channel`, `channel_member`, `message`, `calendar`, `calendar_event`, `automation`, `file`, `knowledge`, `model`, `tool`, `function`, `prompt`, `skill`, `note`, `memory`, `tag`, `feedback`, `app` — tất cả đều có `data` và/hoặc `meta` JSON.

Hệ quả: schema nói rất ít về dữ liệu thật. Những thứ quan trọng nằm trong JSON không được ràng buộc: `group.data.config.default_models`, `automation.data.rrule` (**điều khiển scheduler**), `chat.meta.tags`, `file.meta.data.knowledge_id`, `app.data` (URL, manifest, scope, credential). Muốn biết hình dạng phải đọc code.

Thêm một điểm kỹ thuật: các JSON này là SQLAlchemy `JSON`, **không được mô tả là PostgreSQL `JSONB`**; còn helper `JSONField` ở tầng database lại là TEXT có codec — một kiểu khác hẳn.

### 4.8. Những điểm không nhất quán khác

- **Đơn vị timestamp trộn** trong cùng một database: `chat.created_at` epoch giây, `channel.created_at`/`message.created_at`/`app.created_at` nanosecond, `chat.timer_at` nanosecond.
- **`user.email` khai `unique=True` trong SQLAlchemy nhưng không có UNIQUE trong database** — schema chỉ dựng từ migration, và không migration nào tạo constraint đó; partial index `uq_user_email_lower` là **toàn bộ** sự cưỡng chế.
- **Model SQLAlchemy lệch database ở ít nhất hai chỗ**: `channel_member.joined_at` là NOT NULL trong database nhưng model bỏ cờ; `message_reaction.user_id`/`message_id`/`name` NOT NULL trong database nhưng model không khai. Ràng buộc database mới là cái có hiệu lực — tức đọc model sẽ hiểu sai.
- **`folder.items` JSON song song với `chat.folder_id`** — hai cách biểu diễn cùng một quan hệ.
- **`feedback.snapshot`** lưu snapshot chat liên quan → nhân bản nội dung.
- Migration `b8f2c6d91a04` tạo partial index chỉ có tác dụng trên PostgreSQL; **trên SQLite không có tác dụng**, và nếu PostgreSQL không tạo được thì migration **ghi warning rồi vẫn đánh dấu đã áp dụng**, startup tiếp tục mà không có index.

---

## 5. LibreChat — ưu điểm

### 5.1. Multi-tenancy có thật, fail-closed, có di sản được ghi lại

`tenantId: String` + plugin Mongoose tiêm filter cho **12 phép đọc/ghi** (`find`, `findOne`, `distinct`, `findOneAndUpdate`, `findOneAndDelete`, `findOneAndReplace`, `updateOne`, `updateMany`, `deleteOne`, `deleteMany`, `countDocuments`, `replaceOne`), cộng `aggregate` (unshift `$match` vào đầu pipeline) và `save`.

| Trạng thái context | Hành vi |
|---|---|
| Có `tenantId` | Tiêm vào mọi query filter |
| `tenantId === '__SYSTEM__'` | Bỏ qua — thao tác cross-tenant **tường minh** |
| Không có + `TENANT_ISOLATION_STRICT=true` | **Throw** (fail-closed) |
| Không có + strict tắt | Cho qua (chế độ chuyển tiếp) |

`updateGuard` chặn update tự sửa `tenantId`; update rỗng sau khi lọc bị ép `{ _id: { $in: [] } }` và tắt `upsert` thay vì chạy không điều kiện.

**43/53 model áp plugin; 7 model cố ý không áp, mỗi cái có lý do đọc được từ code.** Hai trong số đó (`AuditLog`, `SystemGrant`) có **validator cấm `tenantId: null`** kèm comment giải thích: `{ tenantId: { $exists: false } }` khớp field vắng mặt chứ không khớp `null`, nên một document lưu `null` sẽ biến mất khỏi **cả** truy vấn platform-level **lẫn** tenant-scoped.

Và họ ghi lại cái giá của việc bật tenancy muộn: [`migrations/tenantIndexes.ts`](/home/lamhung/code/LibreChat/packages/data-schemas/src/migrations/tenantIndexes.ts) liệt kê **13 collection có index unique cũ phải drop** trước khi multi-tenancy chạy được. Index không-unique mở rộng thêm `tenantId` thì **không** cần drop — comment nói rõ chúng vô hại, chỉ làm plan kém tối ưu hơn một chút.

### 5.2. Partial unique index làm lock và hạn mức — dùng nhất quán ≥5 chỗ

Đây là mẫu thiết kế mạnh nhất của LibreChat.

| Vị trí | Partial filter | Bất biến được thực thi |
|---|---|---|
| `schedule.slot` | `{deleting: false, slot: {$exists: true}}` | Hạn mức số schedule mỗi user |
| `scheduleRun.capacitySlot` | `{status: 'started', capacitySlot: {$exists: true}}` | **fireConcurrency TOÀN CỤC** |
| `scheduleRun {scheduleId}` | `status: 'started'` | Tối đa một run đang chạy mỗi schedule |
| `codeEnvironment.ownerSlot` | `ownerSlot: {$type: 'number'}` | Hạn mức sandbox mỗi chủ sở hữu |
| `agentQueuedTurn` × 3 | `status: 'claimed'` / `activeSlot` / `admissionSlot: true` | Một lượt claimed mỗi lane, giới hạn lượt hoạt động, một admission mỗi lane |

Lý lẽ giống nhau ở mọi chỗ và được viết ra: **thay "đọc rồi so sánh" (racy) bằng một va chạm duplicate-key nguyên tử**. Hai lần create đồng thời giành cùng slot thì va chạm trên index, một bên retry slot trống kế tiếp.

`agentqueuedturns` có **sáu unique index, mỗi cái thực thi một bất biến khác nhau** — từ idempotency của create `{tenantId, user, conversationId, clientRequestId}` tới hàng rào xuyên phiên bản `admissionStartedAt` (được **cả worker cũ và mới ghi**, sống sót qua trạng thái cách ly `dead/ADMISSION_INDETERMINATE`, nên nó được chọn làm hàng rào chứ không phải `status`).

### 5.3. Trạng thái "không biết được" là trạng thái hạng nhất

- `actorDetachedAction.status` có `launch_indeterminate` — thừa nhận tường minh rằng **"đã gọi hay chưa" có thể không biết được**, kèm `idempotencyKey` cố định 64 ký tự và `recoveryAfter` để đi tiếp.
- `agentEventActorReconciliations.status` có `commit_indeterminate` trong 7 trạng thái từ `invocation_pending` → `settled`.
- `agentQueuedTurn` có hàng rào riêng cho `dead/ADMISSION_INDETERMINATE` của worker cũ.

Rất ít schema mô hình hóa điều này. Open WebUI không có gì tương đương.

### 5.4. Lease riêng cho từng pha vòng đời

`codeenvironments` có **ba bộ** `*LeaseId` + `*LeaseExpiresAt` + `*ReconcileAfter` riêng cho registration, revocation và deletion. Lý do ghi trong source: ba pha **có thể chồng lấn**, và một pha cướp lease của pha khác sẽ mất tính đúng đắn.

Mẫu này lặp lại ở `agenttriggerdeliveries` (trục thường + trục `capability_*` với bộ lease riêng), `schedule` (`leaseUntil`/`leaseBy`/`claimToken`), `skillsyncstatuses` (`lockOwner`/`lockExpiresAt`), `skilldeletions` (`claimOwner`/`claimExpiresAt`).

Đáng chú ý: **mọi lock đều nhúng vào chính document của tài nguyên**, trừ `resourcelocks` là lock phân tán tổng quát duy nhất (unique trên `key` để giành, TTL để tự nhả khi process chết).

### 5.5. Generation fencing nhiều chiều

`toolapprovalgrants` có **năm trục độc lập** làm phê duyệt mất hiệu lực: `generation`, `approvedAgentGeneration`, `approvedToolGeneration`, `approvedRevocation`, `oauthEpoch`.

`schedule` tách rõ hai thứ dễ gộp nhầm: `claimToken` xoay **mỗi lần claim và mỗi lần chủ sửa**, còn `configRevision` **chỉ tăng khi chủ sửa**. Run bắt `configRevision` lúc claim nên bookkeeping cuối không hành động trên config nó chưa từng chạy dưới.

`conversation.agentEventActorEpoch` **tăng bởi mọi sự kiện đường legacy**, để một fork đang chuẩn bị không commit vượt qua một lần vô hiệu hóa mà riêng các head field không thể hiện được.

### 5.6. Audit log append-only có bằng chứng chống sửa

Collection duy nhất trong cả hai dự án được thiết kế như vậy.

- Mọi field `immutable`. **Không có `updatedAt`** — comment nói thẳng: một timestamp thay đổi được sẽ hàm ý rằng sửa đổi là hợp lệ.
- `createdAt` **do writer đặt tường minh**, không phải `timestamps`, để nó nằm trong phạm vi hash.
- Chuỗi hash `prevHash` → `hash`, `GENESIS_HASH` = 64 số `0`.
- Unique `{chainKey, seq}` vừa là **khóa phân trang keyset** vừa là **lớp chống phân nhánh chuỗi**: append đồng thời đua nhau giành `seq`, một bên thắng, bên thua retry.
- **Bảy hook bịt mọi lối thoát**, gồm cả biến thể `{document: true, query: false}` (vì Mongoose mặc định đăng ký `deleteOne`/`updateOne` là query middleware, để hở `Document.prototype.*`), và chặn `bulkWrite` + `insertMany` vì chúng đi thẳng raw driver.
- `metadata` có comment: **không bao giờ lưu prompt thô, secret, hay output tool đầy đủ**.
- Tự thú giới hạn: purge lưu trữ có đặc quyền dùng `Model.collection` và **không bị các hook này chạm tới**; tamper-evidence vượt ngoài guard tầng ứng dụng chỉ đến từ chuỗi hash.

### 5.7. Index được thiết kế theo truy vấn, kèm lý do viết ra

Ba comment trong source là bài học thiết kế index đúng nghĩa:

> **Facet `endpoint`:** thiếu `endpoint` trong khóa thì MongoDB phải fetch **mọi** document theo thứ tự danh sách của user chỉ để loại bỏ — một filter khớp ít dòng lại đọc cả danh sách. Có nó thì scan nằm trong index. Facet khoảng-ngày **không cần index riêng**: chúng chỉ là biên trên khóa sort mà các index khác đã dẫn đầu.

> **Vì sao cần `{user, updatedAt↓, _id↓}` riêng:** index compound chỉ cung cấp thứ tự sort khi các khóa đứng trước bị ghim bằng **equality**, mà hai index `updatedAt` kia ghim `chatProjectId` và `pinned`.

> **`tenantId` cố ý không nằm ở giữa** trong `{conversationId, user, createdAt, _id}`: deployment không bật tenant không phát predicate `tenantId` nào, và một lỗ hổng trong prefix sẽ đẩy sort về in-memory cho họ.

Điểm thứ ba đáng học riêng: đây là trường hợp mẫu multi-tenant-bằng-cột **va chạm với thực tế có cả deployment chưa bật tenancy**, và họ chọn ưu tiên nhóm sau cho đường đọc nóng nhất.

Thêm: `{createdAt↓, _id}` + `{createdAt↑, _id}` trên `agents` với comment *"chiều cũ nhất đảo ngược toàn bộ key pattern"* — một index phục vụ hai chiều sort nhờ MongoDB đọc index ngược được, miễn là **đảo toàn bộ** chứ không đảo một phần.

### 5.8. Hai index cùng khóa, khác partial filter

`files` có `project_file_picker` (partial `embedded: true`) và `project_file_picker_search_destination` (partial `metadata.searchDestination: true`) — **cùng hình dạng truy vấn, hai tập con rời nhau, hai index hẹp thay vì một index rộng**.

Index `committed_cleanup_candidates` trên `skilluploadintents` có lý do rõ: nhánh dọn `committed` **không được phép quét các upload đang sống khỏe mạnh chỉ để giữ thứ tự**.

### 5.9. TTL thuần thay partial index — vì lý do tương thích cụ thể

`scheduleRun.settledAt` chỉ được ghi bởi **các lần ghi terminal**, nên TTL trên nó tự động bỏ qua dòng sống, **không cần `partialFilterExpression`**.

Lý do kỹ thuật được ghi lại: predicate `$in` trong `partialFilterExpression` **Amazon DocumentDB 5.0 không build được**, và điều đó sẽ khiến `initializeScheduleEngine` từ chối khởi động. Thêm lý do nghiệp vụ: một cửa sổ phê duyệt dài hơn retention sẽ khiến Mongo hết hạn một run `requires_action` **còn sống**.

Đây là mẫu đáng mượn nguyên vẹn: **dùng sự vắng mặt của trường TTL làm điều kiện lọc, thay vì partial index.**

### 5.10. Tách tool result và transcript subagent khỏi message

- `toolcalls` giữ kết quả tool **tách khỏi message** nhưng vẫn neo vào vị trí trong đó bằng `blockIndex`/`partIndex` trong mảng `content`.
- `subagentcontents` là **commit hai pha trên một collection**: ghi các mảnh `fragment ≥ 0`, rồi publish bản ghi `fragment = -1` làm điểm nhìn thấy. Partial index `subagent_content_sequence` **chỉ index bản ghi commit**.
- `subagentTranscript.messagesJson` và `subagentActivityProjection.activityJson` lưu JSON **dưới dạng chuỗi**, không phải document lồng — tránh giới hạn độ sâu và giữ payload mờ đục với Mongoose.

### 5.11. Khóa tất định trong `_id`

`code_environment_tombstones` (`_id` = SHA-256 của `(environmentId, tenantId)`, hash còn che `environmentId` thật), `mcp_authorization_fence_retries` (`_id` = JSON tuple), `agentTriggerUserPurge` (`_id` = **ObjectId của User**), cộng `subagentContent`, `agentQueuedTurnSequence`, `agentTriggerLaneSequence` đều `_id: String` do ứng dụng cấp.

Lợi ích: **upsert idempotent miễn phí, không cần unique index phụ**.

### 5.12. Snapshot bất biến thay vì tra ACL sống

`sharedLink.fileSnapshots` chép **metadata file, cố ý không chép byte**: route file theo share stream/preview được file mà **không hỏi ACL file sống của chủ sở hữu**. Đây là lời giải cho "link chia sẻ phải tiếp tục hoạt động sau khi quyền của chủ thay đổi" mà không nhân bản dữ liệu.

### 5.13. `select: false` dùng như biện pháp hiệu năng, không chỉ bảo mật

`user.pinnedOrder` có comment nói rõ: **mọi request xác thực đều load user document**, để field này selected sẽ kéo hàng trăm KB trên những đường không bao giờ đọc nó.

Nhiều field `select: false` khác cũng theo logic này: toàn bộ khối event-actor của `conversation`, `conversation.initial_agent_id`, các field `backgroundToolResult*` của delivery.

### 5.14. Schema tự giải thích

Đây là điểm mạnh nhất về chất lượng kỹ thuật, và là thứ cả bốn dự án còn lại trong bộ khảo sát đều không có. Vài comment đáng chép thẳng vào chuẩn thiết kế:

- **"Một deadline, không bao giờ là một cờ"** (`file.deletionRetryAt`): để bản ghi bị tái dùng cho nội dung khác **bị trì hoãn chứ không bị mắc kẹt**.
- **`clientRequestId` cố ý KHÔNG lọc theo `deleting`**: một key phải giữ nguyên trong lúc dòng của nó đang bị xóa, nếu không một retry đến giữa chừng sẽ tạo **bản sao sống lâu hơn cả bản gốc**.
- **`countedFor` + `countersAsOf` là hai lớp khác nhau**: `countedFor` (mảng Date có `$slice`) làm việc đếm idempotent *theo từng lần xảy ra*; `countersAsOf` làm nó *có thứ tự*, để một lần xảy ra cũ settle muộn không dựng lại streak mà một lần mới hơn đã xóa.
- **Bug `isStructuredCadence` được ghi lại tại chỗ**: `cadence` là nested path chứ không phải subdocument, nên validator nhận `this` là **document**; đọc `this.frequency` ở đó luôn `undefined`, khiến mọi cadence trông như structured và **mọi lần ghi cron đều bị từ chối**.
- **`skillsyncstatuses` dùng `validate` kiểm `typeof === 'string'` thay vì `required: true`** vì skill mirror từ gốc repository có path rỗng, mà `required` từ chối chuỗi rỗng — bẫy Mongoose kinh điển, ghi ngay tại chỗ.
- **`allowedTools` để `default: undefined` chứ không `[]`**, để phân biệt "tác giả không khai" với "tác giả khai rõ là không có".
- **`alwaysApplySkills` lưu lúc chạy chứ không dựng lại lúc render**, vì `Skill.alwaysApply` có thể đổi — admin tắt cờ sau này thì lịch sử vẫn phải hiển thị đúng cái đã chạy.

### 5.15. Rotation chống đói, dùng nhất quán

`skillDeletion.lastAttemptAt`, `skillUploadIntent.lastCleanupAttemptAt`, `schedule.eraseAttemptedAt`, `scheduleRun.reconciledAt`, `browser_setup_sessions.reconciledAt` — cùng một mẫu: sắp theo "lần thử gần nhất" để **một dòng không drain được không chặn cả hàng đợi**.

---

## 6. LibreChat — nhược điểm

### 6.1. Không có migration framework

Nhược điểm nặng nhất, và nó kéo theo một chuỗi hệ quả:

- **Schema là nguồn sự thật**; index chỉ được build lúc `createModels()` chạy → **thay đổi index chỉ xảy ra khi process khởi động lại**.
- **Build index nền thất bại im lặng nếu không có listener.** [`models/index.ts:166-181`](/home/lamhung/code/LibreChat/packages/data-schemas/src/models/index.ts) gắn listener `'index'` cho mọi model **chính vì lý do này**.
- **Trên DocumentDB <5.0, `partialFilterExpression` bị từ chối → unique constraint không được thực thi mà log không ghi gì.** Nghĩa là trên target đó, **toàn bộ nhóm "partial unique làm lock" ở §5.2 trở thành vô hiệu** — hạn mức không có, lock không có, và không ai biết.
- Thư mục `migrations/` chỉ chứa vài tác vụ one-shot gọi tay: `tenantIndexes.ts`, `mcpServerNames.ts` (có error type riêng `MCPServerNameMigrationError`), `promptGroupIndexes.ts`. Không có thứ tự, không có bảng version, không có rollback.
- Không có đường đổi tên field, đổi kiểu, hay tách bảng. Mọi thứ phải tương thích ngược vô hạn.

### 6.2. Không có bất kỳ khóa ngoại nào

`ref: 'User'` chỉ là metadata cho `populate()`. Không cascade, không ràng buộc tham chiếu.

Hệ quả trực tiếp: **ba collection tồn tại chính là để làm việc mà FK sẽ làm giúp** — `skilldeletions`, `skilluploadintents`, `code_environment_tombstones`. Cộng `agenttriggeruserpurges` làm hàng rào khi xóa tài khoản.

Nói cách khác, một phần đáng kể độ phức tạp ở §5 **là chi phí của việc không có FK**, không phải năng lực tăng thêm. `skilldeletions` là **nhật ký công việc dọn dẹp có retry**, với claim lease và rotation — tất cả để thay thế một dòng `ON DELETE CASCADE`.

### 6.3. `conversations.messages` ghi lại toàn bộ mỗi `saveConvo`

```ts
// methods/conversation.ts — saveConvo, khi appendMessageIds == null
update.messages = await getMessages({ conversationId, user: userId }, '_id');
```

Truy vấn lại **mọi `_id`** rồi ghi đè cả mảng: `O(n)` đọc + `O(n)` ghi. Hội thoại 10.000 message thì một lần đổi title đọc 10.000 ID và ghi lại mảng 10.000 phần tử.

Có đường tăng dần (`$addToSet` trong `appendConvoMessageReference`) nhưng **không phải mặc định**. Đường đọc trong production code tìm được **đúng một chỗ**, làm fallback khi `messageIds` rỗng.

Đây là biến thể của chính khiếm khuyết mà Open WebUI mắc ở §4.2 — mảng ID thay vì nội dung, nhưng khuếch đại ghi vẫn `O(n)`.

### 6.4. `users.refreshToken` — di sản chưa gỡ, chứa token thô

`userSchema` có mảng nhúng `refreshToken: [{refreshToken: String}]` (**token thô**), song song collection `sessions` lưu `refreshTokenHash` với unique `{user, refreshTokenHash}` và TTL trên `expiration`.

Đường đăng xuất dùng `findSession`, tức collection `sessions`. Grep `$push`/`$pull` trên `refreshToken` trong toàn bộ `api/` và `packages/` ra **đúng một kết quả, nằm trong file test**.

Mảng trên user document do đó là di sản chưa gỡ: **không TTL, không hash**, và nếu dữ liệu cũ còn sót thì đó là refresh token thô nằm trong document được load trên **mọi request xác thực**.

### 6.5. Invariant chỉ Mongoose thực thi — raw driver bỏ qua hết

| Invariant | Thực thi bởi | Bị bỏ qua khi |
|---|---|---|
| `promptGroup.productionId` required khi `source === 'native'` | `required` dạng hàm | `bulkWrite`, raw driver |
| `promptGroup.source*` required khi `source === 'langfuse'` | như trên | như trên |
| `systemGrant.principalId` chuẩn hóa String→ObjectId | **Chỉ hàm `grantCapability`** — không có hook cấp schema | `Model.create()` hay `save()` trực tiếp → lưu sai kiểu, **dòng đó không bao giờ khớp truy vấn** |
| `preset.defaultPreset` một mặc định mỗi user | **Không có gì** — hoàn toàn ở tầng ứng dụng | mọi lúc |
| Search token `nameTokens`/`emailTokens` | Plugin `applySearchTokens` | **`bulkWrite`** — quên gọi `withSearchTokens` thì user biến mất khỏi tìm kiếm **mà không lỗi gì** |
| `auditLog` append-only | 7 hook Mongoose | purge lưu trữ dùng `Model.collection` |

Số lượng comment cảnh báo về `bulkWrite`/`insertMany`/raw driver trong source cho thấy đây là vấn đề **có thật mà họ đã gặp nhiều lần**.

### 6.6. `conversations` là god document

493 dòng, schema lớn nhất hệ, chứa **bốn mối quan tâm không liên quan**:

1. Định danh và nội dung hội thoại (`conversationId`, `title`, `user`, `messages`, `tags`).
2. Toàn bộ khối `conversationPreset` — **~55 tham số model** spread từ `defaults.ts`, dùng chung với collection `presets`.
3. Máy móc thread con (`subagentThread`, `subagentThreadLease`).
4. Máy móc event-actor — **chiếm quá nửa schema**, toàn bộ `select: false`: `agentEventBinding`, `agentEventActor` (với `checkpoint`, `contextFingerprint`, `skillManifest`, `summary`, `contextMeta`, `compactionSemanticIndex`…), `agentEventActorCleanup`, `agentEventActorReconciliations`, `agentEventActorEpoch`, `agentEventActorLegacyTurn`, `agentEventActorSuspension`.

22 index trên một collection. Bất kỳ thay đổi nào ở một trong bốn nhóm đều chạm vào cùng một document.

### 6.7. Lịch sử một lượt chat nằm rải ở năm nơi

`messages` (message thường) · `toolcalls` (kết quả tool, neo bằng `blockIndex`/`partIndex`) · `subagentcontents` (transcript subagent, commit hai pha, `messagesJson` dạng chuỗi) · Redis chunks (phần đang sinh) · MeiliSearch (projection tìm kiếm).

Dựng lại một lượt đầy đủ cần ít nhất `messages` + `toolcalls`. Tách là đúng về nguyên tắc (xem §5.10), nhưng **không có transaction** giữa các collection, và MongoDB ở đây không dùng multi-document transaction trong các đường đã đọc.

### 6.8. Cursor phân trang lịch sử thiếu tiebreak

```ts
// methods/message.ts — getMessagesByCursor
queryFilter[sortField] = sortOrder === 1 ? { $gt: cursor } : { $lt: cursor };
```

Cursor **một trường duy nhất, không có `_id`**. Index đọc lịch sử là `{conversationId, user, createdAt, _id}` — **có** `_id` mà query không dùng. Hai message cùng `createdAt` ở biên trang bị **bỏ sót hoặc lặp**.

Nặng hơn: `sortField` còn nhận `'endpoint'`, một trường **không duy nhất và không đơn điệu**. Chi tiết ở [librechat.md §12.2](./librechat.md).

### 6.9. Document không có biên

| Vị trí | Rủi ro |
|---|---|
| `agent.versions: [Mixed]` | Lịch sử phiên bản **nhúng ngay trong document agent**. Giữ được atomic đọc/ghi nhưng document lớn dần không có chặn trên |
| `group.memberIds: [String]` | Tư cách thành viên **nằm trên group**, không có collection membership riêng → số thành viên bị chặn bởi **trần 16 MB mỗi document** |
| `conversations.messages: [ObjectId]` | Mảng tham chiếu, cộng thêm vấn đề `O(n)` ở §6.3 |

Tài liệu nguồn ghi rõ là **chưa kiểm chứng được nếu không có dữ liệu thật**.

### 6.10. `files.expiresAt` và `files.expiredAt`

Hai field cùng tồn tại trên một collection, tên gần như giống hệt, nghĩa **hoàn toàn khác nhau**:

- `expiresAt` — `expires: 3600`, **TTL 1 giờ do MongoDB quản**, cho upload dở.
- `expiredAt` — hạn lưu trữ, **do code quét sau khi xóa storage thành công**; index `{expiredAt}` **không phải TTL**, chỉ để sweep quét.

Tài liệu nguồn gọi đây là "chỗ dễ đọc nhầm nhất trong toàn bộ schema LibreChat".

### 6.11. Không nhất quán kiểu và đặt tên

| Vị trí | Vấn đề |
|---|---|
| `pluginauths.userId` | **String**, trong khi hầu hết nơi khác là ObjectId → join phải ép kiểu |
| `conversations.user`, `messages.user` | **String**, không phải ObjectId |
| `tokens.userId` | `ref: 'user'` — **viết thường**, trong khi nơi khác là `'User'` |
| `memoryentries.updated_at` | **snake_case** giữa một schema camelCase, và tự quản (schema không bật `timestamps`) |
| `agents.id` vs `_id` | Định danh nghiệp vụ tách khỏi `_id`, lặp lại ở `agents`, `schedules`, `assistants`, `actions` |
| `passkey.credentialId` | Unique **toàn cục, không ghép `tenantId`** — ngoại lệ duy nhất trong hệ (hợp lý về WebAuthn nhưng vẫn là ngoại lệ) |

### 6.12. Trùng lặp và xác chết trong schema

- **`conversations.agent_id` khai hai lần**: một lần qua spread `conversationPreset`, một lần tường minh. Cùng kiểu nên không đổi hành vi, nhưng là trùng lặp thật.
- **`presets.title` mang `meiliIndex: true` nhưng `presets` không gắn plugin Meili** — chỉ `conversations` và `messages` gọi `schema.plugin(mongoMeili, ...)`. Cờ này vô hiệu.
- **`categoriesSchema` export từ `schema/index.ts` nhưng không model nào dùng** — khai hai unique index không bao giờ được build. Vai trò đã bị `AgentCategory` thay thế.
- **`conversationPreset.resendImages`** đánh dấu deprecated nhưng vẫn spread vào cả hai collection.
- **`systemGrant.expiresAt`** có comment: *"dành cho TTL tương lai — chưa được thực thi"*.
- **`messages.attachments`** có một khối khai báo chi tiết **bị comment out** ngay bên dưới.
- **`messages.conversationSignature`, `clientId`, `invocationId`** — di sản Bing.
- **`projects`** là collection legacy, chỉ còn `ensureRequiredCollectionsExist` tạo và một migration đọc.

### 6.13. Thiếu unique ở những chỗ đáng có

| Vị trí | Hiện trạng |
|---|---|
| `aclentries` | **Không có unique nào.** Một principal có nhiều entry cho cùng resource; quyền hiệu lực là **hợp của `permBits`** |
| `memoryentries` | `{userId, agentId, key}` **không unique** → trùng được database cho phép, dedupe ở tầng ứng dụng |
| `keys` | `{userId, name, tenantId}` không unique, kèm comment tự thú: *"database cũ có thể đang giữ dòng trùng cho một user và một tên key"* |
| `pluginauths` | `{userId, pluginKey, authField, tenantId}` không unique |
| `assistants` | **Không có unique nào trên `assistant_id`** |
| `banners` | **Không có index nào ngoài `tenantId` inline** — kể cả trên `bannerId` |
| `balances.reservations` | Có `expiresAt` **nhưng không có TTL index** — request chết không tự nhả credit |
| `transactions` | **Không có index compound nào**; `messageId` là String không index → truy ngược từ message về chi phí phải quét |

### 6.14. Vài field nhạy cảm không được bảo vệ ở schema

`action.metadata.api_key` và `action.metadata.oauth_client_secret` là **String thường, không `select: false`**. Mã hóa (nếu có) xảy ra ở tầng ứng dụng, không ở schema. So sánh: `skillsynccredentials.encryptedToken`/`tokenHash` đều `select: false`, và `user.password`/`totpSecret`/`backupCodes` cũng vậy — tức mẫu đúng có tồn tại, chỉ là không áp đều.

---

## 7. So sánh theo bốn trục

### 7.1. Tính năng

Hai dự án phủ hai nửa khác nhau, gần như không tranh chấp.

**Chỉ Open WebUI có:**

| Miền | Bảng |
|---|---|
| Chat kiểu Slack | `channel`, `channel_member`, `channel_file`, `channel_webhook`, `message`, `message_reaction` |
| Lịch | `calendar`, `calendar_event` (RRULE), `calendar_event_attendee` |
| Automation | `automation`, `automation_run` |
| App marketplace | `app` (credential mã hóa, uninstall giữ `slug`) |
| Note | `note`, `pinned_note` |
| RAG trong DB | `knowledge`, `knowledge_directory`, `knowledge_file` |
| Khác | `memory`, `feedback` (bảng riêng), `folder`, `tag` |

**Chỉ LibreChat có:**

| Miền | Collection |
|---|---|
| Multi-tenant | `tenantId` toàn hệ + plugin |
| Audit | `auditlogs` (chuỗi hash append-only) |
| Billing | `balances`, `transactions` |
| Hàng đợi bền vững | `agenttriggerdeliveries` (10 trạng thái, 19 index), `agentqueuedturns` (6 unique index), hai bộ cấp số thứ tự |
| Lập lịch | `schedules`, `scheduleruns` |
| LangGraph | `agent_checkpoints`, `agent_checkpoint_writes`, `agent_checkpoint_stores`, `agent_checkpoint_deletions` |
| Sandbox code | `codeenvironments` (ba pha vòng đời), `code_environment_tombstones` |
| MCP | `mcpservers`, `mcp_authorization_fence_retries` |
| Skill | `skills`, `skillfiles`, `skilldeletions`, `skilluploadintents`, `skillsynccredentials`, `skillsyncstatuses` |
| ACL chi tiết | `accessroles` (`permBits` bitmask), `aclentries`, `systemgrants`, `configs` |
| Auth nâng cao | `passkeys`, `refreshtokenbridges`, `openidrefreshflights`, `agentapikeys` |
| Subagent | `subagentcontents`, cộng 5 khối trên `messages` |

**Hai điểm phân thắng bại rõ:**

- **Versioning tài nguyên: Open WebUI thắng.** Mẫu `*_history` + `version_id` lặp 5 lần, có suy nghĩ về cái gì nên/không nên rollback. LibreChat nhúng `agent.versions: [Mixed]` không biên.
- **Tách tool result khỏi message: LibreChat thắng.** `toolcalls` + `subagentcontents` vs `chat_message.output` JSON.

**Khác biệt kiến trúc, không phải thiếu tính năng:** Open WebUI để RAG/knowledge trong database; LibreChat đẩy ra RAG API + vector DB ngoài, và tìm kiếm ra MeiliSearch.

> **Kết:** hòa, nhưng khác trục. Open WebUI rộng về **sản phẩm workspace**; LibreChat sâu về **vận hành agent**.

### 7.2. Khả năng mở rộng

Phải tách hai nghĩa, vì mỗi bên thắng một nghĩa, và cả hai chênh lệch đều lớn.

#### (a) Mở rộng tải — **LibreChat thắng đậm**

| Tiêu chí | Open WebUI | LibreChat |
|---|---|---|
| Multi-tenant | **Không có** | `tenantId` + plugin + fail-closed + 43/53 model |
| Khóa đồng thời | Một row lock thô cho cả chat (`BEGIN IMMEDIATE` / `FOR UPDATE`) | Partial unique làm lock ≥5 chỗ; lease riêng từng pha; bộ cấp số theo lane |
| Nhiều pod | Thực thi `asyncio.Task` trong RAM pod sở hữu; **pod chết thì coroutine mất** | `openidrefreshflights`, `resourcelocks`, lane sequence, `claimToken`/`leaseUntil` — tranh chấp giải trong DB |
| Idempotency | Không thấy trong schema | `clientRequestId`, `idempotencyKey` 64 ký tự, khóa tất định trong `_id`, `deliveryKey` unique |
| Trạng thái không xác định | Không mô hình hóa | `launch_indeterminate`, `commit_indeterminate`, `ADMISSION_INDETERMINATE` |
| Cancel | Redis pub/sub, **không có ACK** | `abortRequestedAt`/`abortSource`/`abortPersistedAt`, `controlReceipts[]` |
| Số invariant DB giữ | 25 UNIQUE, 2 partial, 0 TTL | 79 unique, 33 partial, 40 TTL |

Một cảnh báo quan trọng: **trên DocumentDB <5.0, phần lớn lợi thế này biến mất im lặng** (§6.1).

#### (b) Mở rộng schema — **Open WebUI thắng đậm**

| Tiêu chí | Open WebUI | LibreChat |
|---|---|---|
| Framework | Alembic, cây tuần tự, có `migrate_history` | **Không có** |
| Thay đổi index | Qua migration, có thứ tự | Chỉ khi **process khởi động lại** |
| Thất bại khi build index | Migration dừng và báo (trừ trường hợp `b8f2c6d91a04`) | **Im lặng nếu thiếu listener** |
| Đổi tên / đổi kiểu field | Có đường đi | Không có |
| Rollback | Có downgrade (một số bị chặn có chủ ý, ví dụ `c92da83b017f`) | Không |
| Backfill dữ liệu | Có mẫu chuẩn (batch + savepoint + cô lập dòng hỏng) | Script one-shot gọi tay |

### 7.3. Database clean

| Chỉ số | Open WebUI | LibreChat |
|---|---|---|
| **Toàn vẹn tham chiếu** | Có FK + CASCADE nhưng **rất thưa**: 3/40 cột owner, và cây message **không thể** có FK | **Không có FK nào.** Ba collection tồn tại chỉ để thay cascade |
| **Invariant do DB giữ** | Ít: 25 UNIQUE, 2 partial, 0 TTL | Nhiều: 79 unique, 33 partial, 40 TTL — **nhưng vô hiệu trên DocumentDB <5.0** |
| **Một sự thật một chỗ** | Vi phạm nặng: `chat.chat` blob ↔ `chat_message` rows, dual write mọi lần | Vi phạm nặng: `conversations.messages` ghi đè `O(n)`; cộng denormalize `conversationCount`, `lastConversationAt`, `mcpServerNames`, `authorName` không có trigger giữ đúng |
| **Xác chết** | **Nhiều, có đánh dấu**: ≈9 cột không ai ghi, 3 bảng legacy + 1 cột backup không bao giờ drop, 1 cột chết gây lỗi logic (`role = manager`) | Ít hơn về số lượng nhưng **nguy hiểm hơn**: `users.refreshToken` chứa token thô; cộng `categoriesSchema` không model, `presets.title` meiliIndex vô hiệu, `agent_id` khai hai lần |
| **Nhất quán kiểu** | Trộn đơn vị timestamp (giây / nanosecond); model SQLAlchemy lệch database ở ≥2 chỗ | String vs ObjectId lẫn lộn; snake_case lọt vào camelCase; `expiresAt` vs `expiredAt` |
| **Tự ghi lại cái bẫy** | **Không** | **Có, ngay tại chỗ** |

**Nhận định.** Cả hai đều không sạch, nhưng **loại bẩn khác nhau** và đây là điểm phân biệt quan trọng nhất:

- Bẩn của Open WebUI phần lớn **trơ** — cột chết, bảng legacy, blob trùng. Xấu, tốn ghi, gây hiểu nhầm, nhưng hiếm khi sinh dữ liệu sai. Ngoại lệ: `role = manager` và chat search khác nhau giữa hai backend.
- Bẩn của LibreChat **chịu lực** — không FK, invariant chỉ Mongoose giữ, mảng ghi `O(n)`, document không biên. Nó **có thể** sinh dữ liệu sai, và một số đường (`bulkWrite`) sai **mà không báo lỗi**.

Bù lại, LibreChat **ghi lại từng cái bẫy ngay tại chỗ**, còn Open WebUI thì trang docs tự mâu thuẫn (nói loại `migrate_history` khỏi danh sách nhưng vẫn liệt kê nó ở dòng 25).

> **Kết:** LibreChat sạch hơn, sít sao — ít rác hơn và nhiều invariant hơn. Open WebUI an toàn hơn về toàn vẹn tham chiếu **trên lý thuyết**, nhưng FK quá thưa để tạo khác biệt thật.

### 7.4. Tổ chức hợp lý

| Khía cạnh | Open WebUI | LibreChat |
|---|---|---|
| Đặt tên | snake_case, bảng số ít, bộ cột lặp đều → **rất dễ đoán** | camelCase, collection số nhiều, nhưng có ngoại lệ lọt lưới |
| Nhóm theo miền | Sạch và đều: auth → chat → channel → calendar → file/knowledge → workspace → system | Sạch ở nhóm vận hành; **rối ở nhóm chat** |
| Mẫu lặp lại | `*_history` + `version_id` × 5 — **điểm tổ chức mạnh nhất của họ** | Partial-unique-làm-lock × 5+; lease theo pha × 4; khóa tất định trong `_id` × 6; rotation chống đói × 5 |
| God table | Không có | **`conversations` 493 dòng, 4 mối quan tâm, 22 index** |
| Một lượt chat nằm ở đâu | 2 chỗ (blob + row), cùng một bảng | **5 chỗ**, không có transaction giữa chúng |
| Mô hình quyền | `access_grant` đa hình `(resource_type, resource_id)` text, **UNIQUE đầy đủ**, nhưng chỉ `read`/`write` | `accessroles` + `aclentries` với `permBits` bitmask, `inheritedFrom`, `expiredAt`, principal `PUBLIC` — **giàu hơn hẳn**, nhưng `principalId: Mixed` và **không unique** |
| Tách concern | Tốt: `access_grant`, `chat_file`, `shared_chat`, `pinned_note` (ghim theo user thay vì cột trên note) | Tốt: `toolcalls`, `subagentcontents`, `accessroles`/`aclentries`, `sharedLink.fileSnapshots` |
| Schema tự giải thích | **Không**; docs là community contribution, tự mâu thuẫn | **Có** — comment là tài liệu thiết kế đúng nghĩa |

Một điểm tổ chức của Open WebUI đáng nêu riêng: **`pinned_note` thay cột `note.is_pinned`**. Migration `4de81c2a3af1` xóa cột legacy, backfill pin về chủ sở hữu, và API vẫn phơi `is_pinned` dưới dạng join theo request của user đang gọi. Ghim là **riêng tư**, không ảnh hưởng user khác có quyền với cùng note, và bật/tắt ghim **không** làm đổi `note.updated_at`. Đây là ví dụ mẫu về tách một thuộc tính per-user ra khỏi bảng tài nguyên dùng chung.

---

## 8. Tổng kết

| Trục | Thắng | Mức chênh |
|---|---|---|
| Tính năng | Hòa, khác trục | OWUI rộng (workspace), LC sâu (vận hành agent) |
| Mở rộng tải | **LibreChat** | **Lớn** — OWUI không có tenant, thực thi trong RAM |
| Mở rộng schema | **Open WebUI** | **Lớn** — LC không có migration |
| Database clean | **LibreChat** | Sít sao |
| Tổ chức hợp lý | **LibreChat** | Vừa — nhờ comment-là-tài-liệu; trừ điểm vì god document |

**Một câu:** Open WebUI là schema của một **sản phẩm** — dễ đọc, dễ tiến hóa, nhưng chưa từng phải đúng dưới tải nhiều tenant nhiều pod. LibreChat là schema của một **hệ vận hành** — giải đúng những bài toán khó nhất (đồng thời, idempotency, fencing, hàng đợi bền vững) nhưng trả giá bằng việc vứt bỏ toàn bộ toàn vẹn tham chiếu và không có đường nâng cấp schema.

Không bên nào là hình mẫu để sao chép nguyên.

---

## 9. Áp dụng cho dự án

Đối chiếu với [identity-chat-database-design.md](../chat_development/identity-chat-database-design.md) và [identity-chat-schema.sql](../chat_development/identity-chat-schema.sql).

### 9.1. Ba lựa chọn đã chốt được xác nhận thêm

1. **PostgreSQL + composite FK `(org_id, id)`.** Lấy được nhóm invariant của LibreChat **mà không mất FK**. Cả hai dự án đều **không** có được đồng thời hai thứ đó: Open WebUI có FK nhưng thưa và không có tenant; LibreChat có tenant và nhiều invariant nhưng không có FK nào.
2. **Không dual-write transcript.** Cả hai đều vi phạm, mỗi bên một kiểu (`chat.chat` blob vs `conversations.messages` array), và cả hai đều trả giá khuếch đại ghi `O(n)`.
3. **`principal` registry thay `(resource_type, resource_id)` text.** Vá đồng thời lỗ của `access_grant` (đa hình không FK) và lỗ của `aclentries` (`principalId: Mixed`, không unique).

### 9.2. Nên mượn thêm — chưa có trong thiết kế hiện tại

| Mượn từ | Nội dung |
|---|---|
| LibreChat | **Comment là tài liệu thiết kế, viết thẳng vào DDL.** Mỗi index và mỗi constraint không hiển nhiên đều nêu lý do và cái bẫy nó tránh |
| LibreChat | **"Một deadline, không bao giờ là một cờ"** cho mọi cột điều khiển retry/cleanup |
| LibreChat | **Dùng sự vắng mặt của cột làm điều kiện lọc** thay vì partial index, khi cột đó chỉ được ghi ở đường terminal |
| LibreChat | **Trạng thái "không biết được" là hạng nhất** nếu có đường gọi ngoài không idempotent |
| Open WebUI | **Mẫu `*_history` + `version_id` thống nhất**, nếu sau này có agent/prompt versioning. Kèm nguyên tắc: snapshot giữ nội dung, cờ vận hành ở lại dòng live |
| Open WebUI | **Tách thuộc tính per-user ra bảng riêng** (mẫu `pinned_note`) thay vì thêm cột vào bảng tài nguyên dùng chung |
| Open WebUI | **Mẫu backfill**: batch có kích thước, savepoint, lỗi batch thì thử từng dòng để cô lập |

### 9.3. Không được sao chép

| Tránh | Vì |
|---|---|
| Dual write blob history (`chat.chat`) | Khuếch đại ghi `O(n)`, hai nguồn lệch nhau, reader phải self-heal |
| Mảng ID song song (`conversations.messages`) | Cùng vấn đề, chỉ đổi dạng |
| PK ghép chuỗi (`chat_id-message_id`) | Giết khả năng dùng FK cho cây message |
| Cột `data`/`meta` JSON mặc định ở mọi bảng | Schema mất khả năng nói về dữ liệu |
| Cột chết để lại trong schema | Open WebUI có ≈9 cột và một trong số đó gây lỗi logic thật |
| Trộn đơn vị timestamp | Chọn một, ghi vào chuẩn |
| Lịch sử phiên bản nhúng trong document/dòng | `agent.versions` không biên |
| Invariant chỉ tầng ứng dụng giữ | Mọi đường ghi bỏ qua ORM sẽ bỏ qua nó |

### 9.4. Một rủi ro cần cân nhắc lại

Nguyên tắc đã chốt *"xóa thread bằng native saver API, không tự ghi vào bảng native"* bị LibreChat mâu thuẫn trong thực tế: họ phải **tiêm `lc_owner` vào document do thư viện quản lý**, thêm hai khóa config `__librechat_checkpoint_owner` / `__librechat_legacy_checkpoint_id`, và thao tác `WRITES_IDX_MAP` trực tiếp — vì `@langchain/langgraph-checkpoint-mongodb` **không hỗ trợ xóa theo chủ sở hữu**.

Xem [librechat.md §11](./librechat.md) và [langgraph-native-storage-findings.md](../chat_development/langgraph-native-storage-findings.md) §6.

---

## 10. Giới hạn của tài liệu này

- **Nguồn không đối xứng.** Phần Open WebUI dựa chủ yếu vào trang docs community contribution (tới v0.12.0); phần LibreChat dựng từ source tại commit cụ thể. Nhận định "cột này không ai ghi" ở hai bên không cùng độ tin cậy.
- **Chưa chạy migration, chưa kết nối database thật, chưa `getIndexes()`.** Mọi index đều là **khai báo**, không phải index đang tồn tại.
- **Chưa benchmark, chưa EXPLAIN, chưa load test, chưa kill-pod.** Mọi nhận định về scale là đánh giá từ code và từ cơ chế khóa.
- **Chưa kiểm chứng hành vi DocumentDB thật.** Mục "unique constraint không được thực thi trên DocumentDB <5.0" là điều **code LibreChat tự nói**, không phải kết quả thử nghiệm.
- **Chưa đối chiếu mọi field với đường đọc/ghi runtime** ở phía LibreChat — [librechat-full-schema.md](./librechat-full-schema.md) là bản liệt kê schema; một field có mặt không có nghĩa là có code ghi vào nó.
- **Không so sánh hiệu năng**, chỉ so sánh thiết kế.
- Hai dự án **không cùng mục tiêu sản phẩm**, nên trục "tính năng" không nên đọc như bảng điểm.
