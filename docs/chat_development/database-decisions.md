# Database đã chốt — giai đoạn 1–4

Ngày cập nhật: **29/10/2026**, Asia/Ho_Chi_Minh.

Đây là bản tổng hợp database hiện hành cho tài liệu phát triển chat. Nguồn quyết định chi tiết và SQL nằm trong [database_decisions](../database_decisions/README.md). Không dùng DDL/catalogue cũ trong chat_development để tạo migration.

Trạng thái: thiết kế đã chốt, SQL và các proof đã được kiểm chứng trên database tạm; **chưa áp dụng database hoặc tích hợp backend ứng dụng**. Quy ước ID bổ sung ở [conversation-message-run-id-decisions.md](conversation-message-run-id-decisions.md).

## 1. Phạm vi sản phẩm

- Một agent cố định với skill/tool do hệ thống quản lý bằng code/cấu hình.
- User có không gian cá nhân và có thể tham gia nhiều tổ chức; chuyển workspace không đăng nhập lại.
- Chat riêng tư mặc định; Owner/Admin/Superuser không tự có quyền đọc chat riêng.
- Hội thoại dạng cây, hai role SQL user/assistant, nội dung theo AG-UI, pin/archive/folder một cấp.
- File trên S3-compatible storage; share snapshot và copy độc lập để chat tiếp.
- Quyền tool/skill động qua RBAC; Langfuse theo dõi token/chi phí.
- Checkpoint bền vững phục vụ chờ duyệt tool/hỏi người dùng; không tự khôi phục worker chết giữa lượt.

## 2. Phân chia PostgreSQL, Redis và object storage

| Dữ liệu | Nơi lưu và trách nhiệm |
|---|---|
| Identity, workspace, quyền, chat/history/file metadata, share/copy | PostgreSQL schema `chat_app` |
| State để resume một intentional interrupt | PostgreSQL schema `langgraph_checkpoints`, bảng SDK quản lý |
| Text/tool events đang sinh, accumulated snapshot, event tail, tín hiệu điều khiển | Redis; backend cần triển khai contract atomic view/watermark/tail |
| Byte file | Object storage, không nằm trong JSONB message |
| Token/chi phí/tracing | Langfuse theo mapping user/conversation/workspace/message |

PostgreSQL không ghi từng token. Content được ghi khi hoàn tất, bắt được lỗi, người dùng dừng hoặc graph pause. Response của người dùng được lưu trong transaction claim trước resume.

Redis giúp reconnect khi executor và dữ liệu live còn hoạt động. Không có cam kết journal PostgreSQL trước mọi token hoặc rebuild toàn bộ prefix sau mất Redis. Checkpoint không thay live buffer. Disconnect chỉ detach subscriber; execution cần backend tách khỏi vòng đời HTTP.

## 3. Danh mục bảng cuối

**24 bảng ứng dụng**, cộng **4 bảng checkpoint kỹ thuật** khi chạy setup SDK:

| Nhóm | Bảng |
|---|---|
| Tài khoản/phiên | `users`, `user_accounts`, `refresh_tokens`, `verifications` |
| Tổ chức/workspace | `organizations`, `workspaces`, `organization_members`, `organization_invitations` |
| RBAC | `permissions`, `organization_roles`, `role_permissions`, `member_role_assignments` |
| Hội thoại | `conversations`, `messages`, `conversation_folders` |
| File | `stored_files`, `message_files` |
| Share | `conversation_shares`, `share_snapshots`, `share_snapshot_messages`, `share_snapshot_files`, `share_snapshot_message_files` |
| Copy | `conversation_copy_jobs`, `conversation_copy_files` |
| Native checkpoint | `checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations` trong `langgraph_checkpoints` |

Không có bảng `organization_units`, `conversation_user_states`, `files` trung gian, `chat_files`, tags, branches/branch_items, runs/attempts, pending_actions, usage hoặc agent authoring. Không tạo native Store/memory tables trong scope hiện tại.

## 4. Tài khoản, workspace và quyền

- User toàn hệ thống; user_accounts hỗ trợ password hash và nhiều provider. Provider identity được scope theo cấu hình issuer/provider, không tự liên kết chỉ vì cùng email.
- Email chính dùng citext unique; token phiên/verification lưu hash, token provider lưu ciphertext theo schema.
- Refresh token có family/consumed/revoked để backend triển khai rotation/reuse detection. Membership được kiểm tra mỗi request, không gắn cố định vào phiên login.
- Một personal workspace cho mỗi user, một organization workspace cho mỗi tổ chức, được provision bằng trigger.
- Role tổ chức động; một thành viên có nhiều role, quyền là hợp grant từ membership/assignment/role đang hoạt động. Giữ ít nhất một active owner.
- Invitation dùng token hash, email xác minh khớp, accept transactionally.
- Quyền tool/skill dùng permission resource/action theo key ổn định trong registry code; tổ chức chưa grant thì không được dùng. Cá nhân dùng allowlist hệ thống.
- Backend lọc tool trước khi gửi model và kiểm tra lại trước thực thi; skill không cấp thêm quyền tool bên trong.
- Chưa có RLS/runtime DB roles hoàn chỉnh. FK/helper hỗ trợ toàn vẹn và kiểm tra quyền, không tự xác thực HTTP hoặc bảo vệ mọi truy vấn backend viết sai.

Chi tiết: [giai đoạn 1](../database_decisions/phase-1-decisions.md), [giai đoạn 3](../database_decisions/phase-3-decisions.md).

## 5. conversations

| Cột | Ý nghĩa |
|---|---|
| `id`, `workspace_id`, `owner_user_id` | Danh tính, scope và owner duy nhất |
| `title` | Tiêu đề |
| `current_message_id` | Nhánh được lưu để mở lại, phải thuộc cùng conversation |
| `pinned_at`, `archived_at` | NULL nghĩa là chưa ghim/chưa archive |
| `folder_id` | NULL nghĩa là ngoài folder |
| `deleted_at`, `created_at`, `updated_at` | Xóa mềm và thời gian |

Không có title_source/revision/availability_status hoặc conversation status. Availability của bản copy chưa xong suy từ copy job.

Folder chỉ một cấp: `conversation_folders(id, workspace_id, owner_user_id, name, created_at, updated_at)`. Không parent_id. Folder và chat phải cùng owner/workspace; không trùng tên sau chuẩn hóa theo index; xóa folder chỉ đặt folder_id NULL. Pin và folder cùng tồn tại.

Có index sidebar, partial index pin/folder và FK access paths. Per-tab branch selection ở client; gửi message phải mang parent tường minh, không tự dùng con trỏ global vừa bị tab khác đổi.

## 6. messages và AG-UI

Các cột: `id`, `conversation_id`, `parent_message_id`, `role`, `content`, `attachments`, `status`, `metadata`, `created_at`, `updated_at`.

- Role SQL chỉ user/assistant. Không position/revision/finish_reason/error_code/error_message/origin/completed_at.
- Parent cùng conversation, không chu trình, không sửa topology của message cũ.
- Không xóa message riêng. Edit/regenerate tạo sibling, giữ bản cũ.
- Content là **AG-UI Message[] đầy đủ cho một logical UI message**, không phải raw SSE event log. Assistant bundle có thể gồm assistant/tool/reasoning/activity; không đưa system/developer prompt nội bộ vào public transcript.
- Attachments là contract ứng dụng cho citation/artifact/tool output, cho phép lặp toàn bộ output đã có trong content. Backend ghi đồng thời; context chỉ lấy tool output một lần.
- Metadata là JSON object do backend quản lý: current_run_id, pending_action/checkpoint pointer và response/decision theo giai đoạn 4. Metadata không tự cấp quyền.
- SQL chỉ kiểm tra hình dạng ngoài; backend validate đầy đủ bằng SDK AG-UI đã pin và kiểm tra tool/file references.
- Sibling hiển thị theo `(created_at,id)`, context đi theo parent. Chưa có bảo đảm hiệu năng phân trang ancestor path rất dài; không dùng sort thời gian để thay đường nhánh.

### Vòng đời

```text
pending -> running -> requires_action -> running -> completed
    |          |             |              +---> failed
    |          |             +------------------> cancelled
    +----------+--------------------------------> failed/cancelled
```

Chỉ assistant có thể requires_action. Một assistant pending/running/requires_action tối đa mỗi conversation. Terminal completed/failed/cancelled bất biến, gồm content/attachments/metadata/file links.

User message có thể stage pending trong transaction tạo và gắn file nhưng **phải completed trước commit**. Deferred trigger bảo vệ quy tắc này; client không thấy user pending đã commit.

Lỗi/dừng sau nửa câu vẫn giữ phần đã sinh. Worker chết đột ngột thì có thể mất buffer và kẹt trạng thái; chưa có auto-recovery.

## 7. Quy ước ID

| Trường | Mapping |
|---|---|
| Public AG-UI thread_id | conversations.id |
| SQL assistant message ID | Giữ nguyên qua mọi pause/resume của lượt trả lời |
| AG-UI run_id | ID riêng mỗi start/resume mới; khác message ID kể cả lần đầu |
| Native checkpoint thread_id | SQL assistant message ID |
| AG-UI protocol message/tool IDs trong content | Giữ riêng, stable khi replay/merge |

`messages.metadata.current_run_id` giữ invocation hiện tại/gần nhất. Redis scope theo workspace/conversation/message và kèm run_id. Stop nhận messageId + runId, không dừng nhầm invocation mới. Retry cùng request không phải execution mới.

Adapter phải ánh xạ public conversation thread sang native assistant thread. Proof trước chưa tích hợp mapping này với frontend/API ứng dụng. Không thêm bảng run chỉ để có mapping ID. Chi tiết: [quyết định ID](conversation-message-run-id-decisions.md).

## 8. File

```text
messages -> message_files -> stored_files -> S3 object
```

- message_files chỉ có message_id và stored_file_id, PK composite, index tra ngược object.
- stored_files giữ bucket/key, tên gốc, MIME, visibility, size, checksum, uploaded_by, metadata object, created_at/deleted_at.
- Không có file status hoặc lớp resource files trung gian. Extraction/preview/RAG processing chưa được triển khai; metadata chỉ là điểm mở rộng.
- Object identity bất biến, không overwrite key; một checksum đã xác minh không thay đổi. SQL không kiểm chứng byte S3 thật.
- Chat chỉ gắn private object chưa xóa, không alias object giữa owner/workspace. uploaded_by là guard nguồn upload, không phải ACL tải file; backend còn kiểm tra upload scope trước association.
- Chỉ cấp tải khi có quyền chat/share. Public share không đổi S3 object thành public; cấp truy cập qua gateway/URL ngắn hạn có kiểm tra link.
- Không xóa metadata/object đang được message/snapshot/copy tham chiếu. Chưa có cleanup/purge worker.

## 9. Share và copy

- Personal workspace: public link, người ngoài được xem snapshot, đọc/tải file.
- Organization workspace: chỉ active member cùng tổ chức có link, không public hoặc cross-org.
- Không share/copy giữa personal và organization theo luồng đã chốt.
- Snapshot **toàn cây message**, gồm các nhánh cũ, content/attachments/file manifest và current branch; không tự cập nhật theo chat live.
- Cập nhật share tạo version snapshot mới, seal bất biến rồi publish; link giữ nguyên.
- Không tạo/cập nhật snapshot khi conversation còn assistant active. Snapshot cũ vẫn đọc được trong khi source chạy lượt mới.
- Người muốn chat tiếp tạo copy: conversation/message/file metadata và **byte object S3 mới**, owner mới, không copy credential/runtime/checkpoint/action sống.
- Copy chưa complete bị ẩn; backend remap đầy đủ IDs/content/file refs và kiểm tra đủ cây, SQL không tự thực hiện S3 COPY hay chứng minh mọi mapping JSON.
- Source soft-delete/revoke không xóa copy completed. Creator rời org thì share của họ bị revoke, không tự sống lại khi rejoin.
- Chưa có share theo direct recipient/team hoặc source-document ACL; khi bật nguồn hạn chế phải bàn quyền phân phối derived content.

## 10. Chờ người dùng và checkpoint

- Không bảng pending_actions. Pending action lưu trên metadata của assistant; mặc định expires_at NULL, không tự hết hạn.
- Chỉ khi interrupt mới export checkpoint cùng toàn bộ pending writes cần thiết. Ordinary chat hoàn tất không giữ checkpoint chỉ để dựng history.
- Checkpoint, message content và dấu chờ commit cùng transaction. Graph/node chạy ngoài transaction database dài.
- Hỏi người dùng: câu hỏi ở content; ActivityMessage loại user_interaction lưu response/actor, không thêm SQL user message. Context builder ánh xạ answered activity thành HumanMessage đúng một lần.
- Duyệt/từ chối tool và hủy toàn lượt khác nhau; từ chối có thể resume giải thích rồi completed, hủy thì cancelled và bỏ pending pointer.
- Claim action nguyên tử, recheck quyền hiện tại, graph_version và action_id; không tin checkpoint pointer do browser chọn.
- Node chứa interrupt có thể chạy lại từ đầu; side effect trước interrupt phải được bố trí/idempotent phù hợp.
- Bốn bảng saver do SDK đã pin setup/migrate trong schema riêng; không copy DDL thư viện bằng tay hoặc tạo FK vào internal rows.
- Giữ checkpoint cho action đang chờ. Cleanup sau kết thúc và migration graph/version chưa thiết kế.

Chi tiết và bootstrap SDK: [giai đoạn 4](../database_decisions/phase-4-decisions.md).

## 11. SQL và kiểm chứng

Áp dụng một lần vào PostgreSQL 18+ scratch mới:

1. [phase-1-schema.sql](../database_decisions/phase-1-schema.sql)
2. [phase-2-part-1-schema.sql](../database_decisions/phase-2-part-1-schema.sql)
3. [phase-2-final-schema.sql](../database_decisions/phase-2-final-schema.sql)
4. [phase-4-schema.sql](../database_decisions/phase-4-schema.sql)
5. Setup native saver theo hướng dẫn giai đoạn 4 để tạo bốn bảng kỹ thuật.

Phase 3 không có SQL. Các bước phase 2 từ chối dữ liệu cũ cần backfill; đây không phải migration production đã hoàn chỉnh. Script bước trước giữ nguyên làm lịch sử và dependency; cấu trúc cuối phải đọc sau toàn chuỗi.

Đã có 122 SQL assertions theo từng mốc, 27 checks sync và 30 checks async/AG-UI trong [proof](../experiments/langgraph-action-checkpoints/README.md). Không coi đó là đã chạy provider LLM/MCP/S3 thật, HTTP end-to-end, Redis reconnect, benchmark tải hoặc kiểm toán bảo mật.

## 12. Những phần chưa chốt implementation hoặc ngoài phạm vi

- Idempotency submit/hash/lifetime, exact stop coordination và Redis snapshot/tail/watermark.
- Title background chống ghi đè user sau khi bỏ source/revision; không tự đưa cột cũ trở lại.
- Tìm kiếm nội dung, performance nhánh rất dài, RLS/runtime roles và kiểm thử auth.
- RAG/source ACL/dependencies, native Store/memory, integration credential bindings và external operation receipts.
- Approval người khác duyệt, audit toàn hệ thống, file processing, export/purge, cleanup checkpoint, recovery worker.

Những mục này không phải danh sách bảng phải thêm ngay. Chỉ mở lại schema khi feature được chọn và có nhu cầu dữ liệu cụ thể. Catalogue chức năng hiện tại/để sau ở [use cases](chat-use-cases-and-organization-access.md).
