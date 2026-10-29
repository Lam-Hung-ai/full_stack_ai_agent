# Các quyết định database đã chốt

Đây là tài liệu và SQL thiết kế, chưa áp dụng vào database ứng dụng.

[Báo cáo đối chiếu với yêu cầu và database cũ trong chat_development](review-vs-chat-development.md) — đánh giá 32 use case, phần đáp ứng và những khác biệt phạm vi; không thay đổi quyết định/schema.

| Mốc | Quyết định | SQL | Kiểm tra |
|---|---|---|---|
| Giai đoạn 1 | [Danh tính, tổ chức, quyền và share/copy](phase-1-decisions.md) | [Baseline](phase-1-schema.sql) | [Checks baseline](phase-1-checks.sql) |
| Giai đoạn 2 — phần 1 (lịch sử) | [Conversation, cây message, AG-UI và tách S3](phase-2-part-1-decisions.md) | [Bước chuyển đầu](phase-2-part-1-schema.sql) | [Checks tại mốc phần 1](phase-2-part-1-checks.sql) |
| Giai đoạn 2 — hoàn tất | [Hội thoại, message, folder và file](phase-2-decisions.md) | [Bước chuyển cuối giai đoạn 2](phase-2-final-schema.sql) | [Checks giai đoạn 2](phase-2-final-checks.sql) |
| Giai đoạn 3 — hoàn tất thiết kế | [Agent cố định, quyền tool/skill và Langfuse](phase-3-decisions.md) | Không đổi schema, chưa có seed quyền cụ thể | Chưa triển khai backend/integration |
| **Giai đoạn 4 — hoàn tất thiết kế** | **[Checkpoint và chờ người dùng](phase-4-decisions.md)** | **[Bổ sung message metadata/pause](phase-4-schema.sql)** | **[Checks giai đoạn 4](phase-4-checks.sql)** |

Quyết định mới thay thế phần tương ứng ở mốc trước. Các script cũ giữ nguyên làm lịch sử và là các bước trong chuỗi áp dụng.

## Thứ tự áp dụng

Database scratch mới, PostgreSQL 18+:

1. `phase-1-schema.sql`
2. `phase-2-part-1-schema.sql`
3. `phase-2-final-schema.sql`
4. `phase-4-schema.sql`
5. `phase-4-checks.sql`

Chi tiết hội thoại/file trong [giai đoạn 2](phase-2-decisions.md); status/metadata pause và bootstrap saver SDK trong [giai đoạn 4](phase-4-decisions.md). SQL giai đoạn 4 tạo schema `langgraph_checkpoints`; bốn bảng checkpoint kỹ thuật được SDK đã pin tạo/migrate bằng `setup()`.

Nếu kiểm tra cả mốc lịch sử: chạy `phase-1-checks.sql` ngay sau bước 1, `phase-2-part-1-checks.sql` ngay sau bước 2, `phase-2-final-checks.sql` ngay sau bước 3. Checks dùng cấu trúc của đúng mốc tương ứng. Toàn chuỗi đã qua **122 assertions SQL** trên PostgreSQL 18.6, gồm 14 checks giai đoạn 4. Đã kiểm tra SDK setup bốn bảng trong schema riêng và chạy lại **30 kiểm tra async/AG-UI** với SQL đã chốt.

## Phạm vi và giới hạn

Giai đoạn 2 hoàn tất thiết kế hội thoại cơ bản: cây message/AG-UI, status và lưu partial lúc kết thúc, terminal immutability, một assistant active mỗi conversation, pin/archive/folder một cấp, `message_files -> stored_files(metadata)`, cập nhật tương thích share/copy.

Giai đoạn 3 chốt một agent cố định, tool/skill quản lý bằng code/cấu hình, quyền tổ chức dùng RBAC hiện có và cá nhân dùng allowlist. Danh mục quyền/grant cụ thể thiết lập sau; Langfuse theo dõi token/chi phí, chưa thêm bảng usage. Không có SQL mới trong giai đoạn 3.

Giai đoạn 4 chốt lưu action trong `messages.metadata`, status `requires_action`, content hỏi–đáp trong cùng message và checkpoint bền vững chỉ khi interrupt; không có bảng pending action hoặc run. Yêu cầu chờ không tự hết hạn. SDK quản lý các bảng checkpoint kỹ thuật riêng.

Phase 2 có preflight từ chối dữ liệu cũ cần backfill; không dùng như migration production. Chưa triển khai backend, S3/LLM integration hoặc RLS. Worker LLM chết đột ngột chưa xử lý theo quyết định đã chốt. RAG, cấu hình agent động, cleanup checkpoint và khôi phục runtime thuộc thiết kế sau.
