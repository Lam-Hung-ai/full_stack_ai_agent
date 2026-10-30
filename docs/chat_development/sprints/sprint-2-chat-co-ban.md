# Sprint 2: Chat cơ bản end-to-end

| | |
| --- | --- |
| Thời gian | 30/11 – 11/12/2026 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S1 |
| Ước lượng | 9 nc |
| Mốc | M-B: Chat thật |
| Use case | C01, C02, C09 (một phần) |
| Câu hỏi phải chốt trước | Q-06: đã chốt (QD-15) |

## Mục tiêu

1. Conversation thuộc workspace: tạo, liệt kê, mở, đổi tên, xoá mềm; chỉ chủ sở hữu đọc được (database §4, §5).
2. Gửi câu hỏi qua `POST /conversations/{id}/messages`: lưu user + assistant trong một transaction, runner chạy tách khỏi HTTP (QD-15), lưu bundle AG-UI ở terminal, giữ partial khi lỗi.
3. Lịch sử nhánh hiện hành qua `GET /conversations/{id}/messages`, giữ SQL message ID.
4. Frontend `ChatAgent extends HttpAgent` (QD-04), UUIDv7, sidebar, mở lại chat cũ; gỡ `POST /agent` và proxy cũ.

## Không làm

- Edit, regenerate, chuyển nhánh, stop, pin/archive/folder, registry quyền tool (S3).
- Pause/resume, checkpoint PostgreSQL (S4). S2 vẫn dùng saver trong RAM, xoá thread khi lượt kết thúc.
- Reconnect khi đóng tab (S5): lượt vẫn chạy và lưu, nhưng mở lại chỉ thấy kết quả khi đã lưu.
- File đính kèm (S7): `file_ids` phải rỗng.

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S2-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S1 | 0,1 | — | ☑ |
| CH-S2-BE-01 | Danh mục permission (L-04) | `modules/authorization/catalog.py`, lệnh `uv run iam sync-permissions`, `AuthorizationService.member_has` | 0,5 | Test: tổ chức tạo sau khi đồng bộ có role với quyền; thành viên không có quyền thì không tạo được chat | ☑ |
| CH-S2-BE-02 | Module `conversations` | CRUD, sidebar phân trang, lịch sử nhánh hiện hành bằng CTE đệ quy | 1,5 | `tests/api/conversations/test_conversations.py`, cô lập chủ sở hữu | ☑ |
| CH-S2-BE-03 | Runner | `modules/agent/runner.py`: task do app sở hữu, semaphore, buffer event, subscriber, giữ `RUN_FINISHED` tới khi lưu xong; lifespan dừng sạch | 2 | Test: client ngắt giữa chừng mà lượt vẫn lưu completed | ☑ |
| CH-S2-BE-04 | Gửi câu hỏi | Validate parent/UUIDv7, title fallback, một assistant active (409), dựng `RunAgentInput` từ nhánh, native thread = assistant ID, event `CUSTOM chat.assistant` | 1,5 | Test với model giả: stream, lưu bundle, lỗi giữ partial `failed` | ☑ |
| CH-S2-FE-01 | `ChatAgent` | Kế thừa `HttpAgent`; fetch có auth/refresh; thao tác qua `forwardedProps`; map protocol ↔ SQL ID | 1,25 | Test Vitest với SSE giả | ☑ |
| CH-S2-FE-02 | Màn chat theo conversation | Route `/` (chat mới) và `/c/[id]`; sidebar theo workspace; tải lịch sử; gửi | 1,5 | Chạy thật bằng trình duyệt | ☑ |
| CH-S2-BE-05 | Gỡ scaffold | Bỏ `POST /agent`, `frontend/src/app/api/agent` | 0,15 | — | ☑ |
| CH-S2-DOC-02 | Cập nhật tài liệu | API contract (đường dẫn, tên field, event liên kết) | 0,25 | — | ☑ |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Người dùng** ở workspace cá nhân bấm "Chat mới", hỏi một câu.
   - Câu trả lời stream; sidebar có chat mới với tiêu đề lấy từ câu hỏi.
2. **Người dùng** hỏi tiếp câu thứ hai trong cùng chat.
   - Model nhận ngữ cảnh câu trước.
3. **Người dùng** tải lại trang `/c/{id}`.
   - Thấy đủ hai lượt, kể cả reasoning và tool.
4. **Người dùng** gửi câu hỏi rồi đóng tab ngay, mở lại sau vài giây.
   - Câu trả lời đã được lưu completed.
5. **Người dùng khác** mở `/c/{id}` của người đầu.
   - 404.

## Rủi ro riêng

- Proxy rewrite của Next có thể gom SSE. Giảm thiểu: kiểm tra thật; nếu gom thì gọi backend trực tiếp hoặc dùng route handler stream.

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 30/11 – 11/12).

**Đã xong**: 9/9 task.
- Backend: module `authorization` (danh mục trong code, `iam sync-permissions`), `conversations` (CRUD, sidebar, lịch sử nhánh bằng CTE đệ quy, gửi câu hỏi), runner trong process (`modules/agent/runner.py`) với buffer event, semaphore, lưu trước khi phát event kết thúc, lifespan dừng sạch. Native thread = assistant ID, `threadId` gửi client = conversation. Bundle ghép thứ tự stream với snapshot.
- Frontend: `ChatAgent extends HttpAgent` (DTO riêng qua `forwardedProps`, fetch có auth/refresh), `useConversationChat`, route `/` và `/c/[id]`, sidebar theo workspace, UUIDv7. Gỡ `/agent` và proxy cũ.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 47 passed (conversation 6, lượt chat 8, unit bundle 3 và context 2, cùng các test S0–S1).
- Frontend: `pnpm test` 35 passed (thêm `ChatAgent` 3, lịch sử 3); `typecheck`, `eslint` thư mục đã đổi sạch; `pnpm build` thành công.
- Chạy thật với model OpenRouter qua trình duyệt: kịch bản 1–4 đạt (tool, ngữ cảnh lượt trước, tải lại, rời trang giữa chừng rồi quay lại); kịch bản 5 phủ bằng test API.
- Đo stream: gọi thẳng backend, event về rải 0,57–3,15 giây; qua Next sau khi sửa L-05, rải 0,6–3,12 giây.

**Lỗi**: L-04, L-05, L-06 đã sửa.

**Thay đổi**: TD-008; QD-19; RR-13, RR-14.

**Dời**: không.
