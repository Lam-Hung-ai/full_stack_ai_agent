# Nhật ký lỗi

Ghi mọi lỗi của dự án phát triển chat: phát hiện khi rà soát, khi làm, khi kiểm thử hay sau phát hành. Luật ghi và mức độ xem ở [README](./README.md).

Lỗi ở đây là **hành vi sai** so với quyết định đã chốt (database, ID, API, ChatAgent) hoặc tài liệu tự mâu thuẫn. Chức năng **chưa làm** (route chưa có, scaffold hiện tại chưa theo thiết kế đích) là phạm vi của sprint, không ghi thành lỗi.

## Bảng tổng hợp

| Mã | Mức | Tóm tắt | Phát hiện | Xác minh | Sửa ở | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| L-01 | Thấp | Use case C04 ghi backend chuyển tín hiệu stop theo `messageId + runId`; mục 5 còn "API dedupe" | Rà tài liệu 29/10 | Đã xác minh | TD-001 | Đã sửa |
| L-02 | Cao | Sau đăng nhập bị đẩy về `/login`: `resetQueries` hủy request `/auth/session` đang chạy, proxy vẫn chuyển tới backend nên token đã xoay; request lặp mang cookie cũ bị coi là dùng lại, cả phiên bị thu hồi | Chạy thật S1, 29/10 | Đã xác minh | CH-S1-FE-02, CH-S1-BE-02 | Đã sửa (S1) |
| L-03 | Thấp | Form đăng nhập và đăng ký dùng `id` cố định; Next giữ route trước ở trạng thái ẩn nên trùng `id`, nhãn bị gộp ("Email Email") | Chạy thật S1, 29/10 | Đã xác minh | CH-S1-FE-02 | Đã sửa (S1) |
| L-04 | Cao | Baseline chỉ dump schema nên mất 5 dòng danh mục `permissions` mà SQL giai đoạn 1 seed; tổ chức tạo sau đó không có grant nào, chủ tổ chức không tạo được chat | Rà S2, 29/10 | Đã xác minh | CH-S2-BE-01 | Đã sửa (S2) |
| L-05 | Trung bình | Câu trả lời hiện ra một lần lúc kết thúc thay vì stream: lớp nén gzip của Next gom cả response `text/event-stream` đi qua rewrite | Chạy thật S2, 30/10 | Đã xác minh | CH-S2-FE-02 | Đã sửa (S2) |
| L-06 | Thấp | Tải lại trang thì reasoning của mọi lượt cũ mở bung rồi mới tự đóng | Chạy thật S2, 30/10 | Đã xác minh | CH-S2-FE-02 | Đã sửa (S2) |

Giá trị cột *Xác minh*:
- **Đã xác minh:** đã đọc code/tài liệu hoặc chạy thử và chắc chắn.
- **Theo code:** suy từ code, chưa chạy thử.
- **Cần chạy thử:** cần tái hiện trên môi trường dev.

## Chi tiết

### L-01: Use case còn stop theo runId
- **Vị trí:** `docs/chat_development/chat-use-cases-and-organization-access.md`, dòng C04, ghi chú sau bảng hội thoại, mục 5.
- **Thực tế:** "backend chuyển tín hiệu theo messageId + runId"; "wire runId"; "API dedupe".
- **Mong đợi:** stop theo conversation + assistant `messageId`, không body, không `runId` ([quyết định ID §7](../conversation-message-run-id-decisions.md#7-stop-theo-assistant)); tạm bỏ dedup ([API §9](../chat-agent-api-contract.md#9-xử-lý-mạng-đơn-giản-trong-phạm-vi-hiện-tại)).
- **Đã sửa:** TD-001 (29/10/2026).
- **Trạng thái:** Đã sửa.

### L-02: Phiên bị thu hồi ngay sau đăng nhập
- **Vị trí:** `frontend/src/features/auth/hooks/use-auth-mutations.ts` (`useLogin`), `use-session.ts`; `backend/src/app/modules/auth/service.py::_rotate`.
- **Tái hiện:** đăng ký hoặc đăng nhập trên trình duyệt.
- **Thực tế:** request `/auth/session` đầu `ERR_ABORTED` nhưng backend đã xoay token; request thứ hai nhận `401 refresh_reuse`, mọi token của họ phiên bị thu hồi.
- **Mong đợi:** vào màn chat.
- **Cách sửa:** không gắn abort signal cho request xoay token; `useLogin` xóa query session thay vì reset; backend cho ân hạn 10 giây với token vừa xoay (QD-18), áp cả trường hợp hai tab cùng tải trang.
- **Test chặn tái phát:** `tests/api/auth/test_auth.py::test_token_presented_again_within_grace_keeps_the_session`.
- **Trạng thái:** Đã sửa (S1).

### L-04: Mất danh mục permission
- **Vị trí:** `db/migrations/20261029093342_chat_baseline.sql` (dump `--schema-only`), so với `docs/database_decisions/phase-1-schema.sql` dòng `INSERT INTO permissions`.
- **Thực tế:** bảng `permissions` rỗng; trigger `provision_organization` cấp quyền cho role từ chính bảng này nên tổ chức mới không có grant.
- **Cách sửa:** danh mục nằm trong code (`modules/authorization/catalog.py`), đồng bộ bằng `uv run iam sync-permissions` sau `dbmate up`; fixture test nạp cùng danh mục. Tổ chức tạo trước khi đồng bộ cần bổ sung grant (đã làm tay trên DB dev).
- **Test chặn tái phát:** `tests/api/conversations/test_conversations.py::test_organization_needs_conversation_create`.
- **Trạng thái:** Đã sửa (S2).

### L-05: SSE bị gom qua proxy Next
- **Vị trí:** `frontend/next.config.ts` (rewrite `/api/v1` sang FastAPI).
- **Đo:** gọi thẳng backend, 257 event về rải trong 0,57–3,15 giây; qua Next, 359 event về cùng lúc ở giây 6,19.
- **Cách sửa:** `compress: false`; nén để reverse proxy production lo, proxy đó cũng không được buffer event stream (RR-13).
- **Trạng thái:** Đã sửa (S2).

## Mẫu ghi

```markdown
| L-xx | Nghiêm trọng/Cao/Trung bình/Thấp | <tóm tắt> | <ai/khi nào> | Đã xác minh/Theo code/Cần chạy thử | CH-S<n>-<lớp>-<số> | Mở/Đang sửa/Đã sửa (S<n>)/Không sửa (lý do) |
```

```markdown
### L-xx: <tiêu đề>
- **Vị trí:** <file:hàm>
- **Tái hiện:** <các bước>
- **Thực tế:** <…>
- **Mong đợi:** <…, trỏ tới quyết định liên quan>
- **Cách sửa:** <mã task>
- **Test chặn tái phát:** <đường dẫn test>
- **Trạng thái:** <…>
```
