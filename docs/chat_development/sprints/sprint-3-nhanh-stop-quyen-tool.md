# Sprint 3: Nhánh, stop và quyền tool

| | |
| --- | --- |
| Thời gian | 14/12 – 25/12/2026 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S2 |
| Ước lượng | 8 nc |
| Mốc | M-C: Chat đầy đủ |
| Use case | C04, C05, C06, C08, C09 |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Edit câu hỏi và regenerate câu trả lời tạo nhánh mới, giữ nhánh cũ (database §6, API §4).
2. Lịch sử trả dữ liệu nhánh; UI chuyển nhánh per-tab, câu hỏi tiếp theo đi theo nhánh đang xem.
3. Stop theo assistant message, không body (API §7): dừng lượt đang chạy và giữ partial; gỡ được lượt kẹt do process chết.
4. Pin, archive, folder một cấp cho sidebar.
5. Registry tool trong code; lọc tool theo quyền trước khi gửi model, kiểm lại ngay trước khi tool chạy (database §4, use case T07).

## Không làm

- Hủy lượt `requires_action` (S4, cùng pause/resume).
- Stop xuyên process (S5, tín hiệu qua Redis).
- Màn quản trị gán quyền tool (S6); S3 chỉ có registry, danh mục permission và kiểm quyền.

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S3-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S2 | 0,1 | — | ☑ |
| CH-S3-BE-01 | Edit, regenerate | `POST …/messages/{user_id}/edit`, `POST …/messages/{assistant_id}/regenerate`; dùng chung đường khởi động lượt với gửi | 1,5 | Test: nhánh cũ còn, ngữ cảnh đúng nhánh | ☑ |
| CH-S3-BE-02 | Dữ liệu nhánh | History trả `sibling_ids` từng dòng; `GET …/messages?from_message_id=` mở nhánh qua một message, đi xuống con mới nhất | 1 | Test chuyển nhánh | ☑ |
| CH-S3-BE-03 | Stop | `POST …/messages/{assistant_id}/stop`; runner hủy task, lưu `cancelled` kèm partial; lượt kẹt không có task thì chuyển thẳng `cancelled` | 1 | Test: partial giữ lại, stop lượt đã xong không đổi gì | ☑ L-08 |
| CH-S3-BE-04 | Pin, archive, folder | PATCH `pinned`/`archived`/`folder_id`; CRUD folder; sidebar lọc archive/folder, ghim lên đầu | 1 | Test API | ☑ |
| CH-S3-BE-05 | Registry tool và quyền | `modules/agent/tools.py`; permission `tool.<key>` trong danh mục; personal dùng allowlist; agent theo tập tool được phép; kiểm lại trước khi tool chạy | 1,25 | Test: thành viên không được grant thì model không thấy tool; thu hồi quyền giữa lượt thì tool từ chối | ☑ L-07 |
| CH-S3-FE-01 | Nhánh, edit, regenerate, stop | `ChatAgent.editMessage/regenerate/stop`; nút sửa, tạo lại, chuyển nhánh, dừng; nhãn trạng thái failed/cancelled | 1,5 | Chạy thật bằng trình duyệt | ☑ |
| CH-S3-FE-02 | Sidebar | Ghim, đổi tên, lưu trữ, xoá, folder | 0,75 | Chạy thật | ☑ |
| CH-S3-DOC-02 | Cập nhật tài liệu | API contract (history, stop response, PATCH) | 0,15 | — | ☑ TD-009 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Người dùng** sửa câu hỏi đầu tiên.
   - Có câu trả lời mới; nút "1/2" chuyển qua lại hai phiên bản, nhánh cũ còn nguyên.
2. **Người dùng** bấm tạo lại câu trả lời.
   - Có phiên bản thứ hai cho cùng câu hỏi.
3. **Người dùng** đang xem nhánh cũ, hỏi tiếp.
   - Câu hỏi nối vào nhánh đang xem.
4. **Người dùng** bấm dừng khi agent đang trả lời.
   - Phần đã sinh còn lại, nhãn "Đã dừng"; hỏi tiếp được ngay.
5. **Người dùng** ghim, chuyển vào folder, lưu trữ một chat.
   - Sidebar phản ánh đúng.

## Rủi ro riêng

- Hủy task giữa lúc tool đang chạy: tool đã có tác dụng phụ thì không hoàn tác được (RR-08). Giảm thiểu: tool hiện chỉ đọc.

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 14/12 – 25/12).

**Đã xong**: 9/9 task.
- Backend: edit/regenerate/send dùng chung `TurnService._launch`; history có `sibling_ids` và `?from_message_id=` (`conversations/tree.py`); stop qua `Runner.stop` (huỷ task, chờ lưu `cancelled`), lượt mồ côi chuyển thẳng `cancelled`; đóng span đang mở khi lượt bị cắt (`agent/lifecycle.py`); module `folders`, PATCH pin/archive/folder, sidebar lọc và ghim lên đầu; registry tool `agent/tools.py`, permission `tool.get_current_time`, agent theo tập tool được phép, middleware kiểm lại quyền trước mỗi lần tool chạy (QD-20, QD-21).
- Frontend: hook vẽ theo từng dòng SQL với lượt đang stream đè lên nhánh đang xem; nút sửa câu hỏi (RHF + Zod), tạo lại, chuyển phiên bản "‹ n/m ›", dừng, nhãn "Đã dừng"/lỗi; sidebar có folder, ghim, đổi tên, chuyển folder, lưu trữ, xoá.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 66 passed (nhánh 5, stop 4, folder 4, quyền tool 3, unit cây 1, danh mục tool 1, lifecycle 1, cùng các test cũ).
- Frontend: `pnpm test` 38 passed; `typecheck`, `eslint` thư mục đã đổi sạch; `pnpm build` thành công.
- Chạy thật với model OpenRouter qua trình duyệt: kịch bản 1–5 đạt (sửa câu hỏi có "2/2" và nhánh cũ còn nguyên; tạo lại; hỏi tiếp trên nhánh cũ; dừng giữ phần đã sinh, câu sau dùng nó làm ngữ cảnh; ghim, folder, lưu trữ, bỏ lưu trữ).

**Lỗi**: L-07, L-08 đã sửa.

**Thay đổi**: TD-009; QD-20, QD-21; RR-15; cập nhật RR-01, RR-10.

**Dời**: không. Ghi chú: stop là hàm REST của `features/chat/api` thay vì `ChatAgent.stop` như ghi ở CH-S3-FE-01 (TD-009).
