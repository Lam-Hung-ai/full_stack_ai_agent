# Sprint 8: Share và copy

| | |
| --- | --- |
| Thời gian | 22/02 – 05/03/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S6, S7 |
| Ước lượng | 8 nc |
| Mốc | — |
| Use case | O03, O04 |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Chủ chat chia sẻ snapshot toàn cây: chat cá nhân bằng link public, chat tổ chức bằng link nội bộ; cập nhật bản chia sẻ giữ nguyên link; thu hồi (database giai đoạn 1 §7–8).
2. Người có link xem snapshot đọc-chỉ, chuyển được giữa các phiên bản câu trả lời, mở được tệp.
3. "Hỏi tiếp": copy thành chat riêng của người xem với message, tệp và object mới, chạy bằng quyền của họ (§9).

## Không làm

- Chia sẻ cho người nhận cụ thể, nhóm (O03 phần team): ngoài phạm vi database.
- Worker nền cho copy job (RR-18, xét ở S9).
- Purge snapshot cũ, job dở (database giai đoạn 1 §8.7, §10).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S8-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S7; không có Q chặn | 0,1 | — | ☑ |
| CH-S8-BE-01 | Share và snapshot | Module `shares`: token HMAC, xuất bản (chụp cây, tệp, nhánh đang mở, đóng dấu), xem lại link, thu hồi | 2 | Test API | ☑ QD-28 |
| CH-S8-BE-02 | Xem share | `GET /shares/{token}` có/không đăng nhập theo `can_read_share`; tệp theo `can_read_share_file` | 1 | Test public/tổ chức/thu hồi/xoá | ☑ |
| CH-S8-BE-03 | Copy | Job theo `client_request_id`, cây đổi id, `stored_files` mới, copy byte dưới lease, kiểm lại quyền khi hoàn tất | 2 | Test copy có tệp, gọi lại, chat tiếp | ☑ |
| CH-S8-FE-01 | Hộp thoại chia sẻ | Mục "Chia sẻ" trong menu chat: tạo, sao chép, cập nhật, thu hồi link | 1 | Chạy thật | ☑ |
| CH-S8-FE-02 | Trang xem share | `/s/{token}`: đọc-chỉ, chuyển phiên bản, tệp, "Hỏi tiếp" hoặc đăng nhập | 1,5 | Vitest nhánh + chạy thật | ☑ L-11 |
| CH-S8-DOC-02 | Cập nhật tài liệu | API §2; use case O03, O04 | 0,25 | — | ☑ TD-014 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Chủ chat cá nhân** chia sẻ một chat có ảnh.
   - Nhận link; người chưa đăng nhập mở link thấy câu hỏi, ảnh, câu trả lời và nút "Đăng nhập để hỏi tiếp".
2. **Người khác** đăng nhập từ trang share rồi bấm "Hỏi tiếp".
   - Vào chat mới trong workspace cá nhân của mình, có đủ lịch sử và ảnh (object mới thuộc họ).
3. **Chủ chat** thu hồi link.
   - Link báo không tồn tại; bản sao đã tạo vẫn còn.
4. **Chat tổ chức** được chia sẻ.
   - Người ngoài và người chưa đăng nhập không xem được; thành viên xem được.

## Rủi ro riêng

- Copy trong request với chat nhiều tệp (RR-18).

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 22/02 – 05/03/2027).

**Đã xong**: 7/7 task.
- Backend: module `shares` (token HMAC xem lại được, xuất bản snapshot toàn cây có version và tệp, thu hồi, xem bằng token có/không đăng nhập theo `can_read_share`, tệp theo `can_read_share_file`, copy job theo `client_request_id` với cây đổi id, `stored_files` mới trong workspace đích, copy byte dưới lease và kiểm lại quyền khi hoàn tất); `optional_user`.
- Frontend: mục "Chia sẻ" và hộp thoại (tạo, sao chép, cập nhật, thu hồi link), trang `/s/{token}` đọc-chỉ có chuyển phiên bản, tệp và "Hỏi tiếp"; `ChatMessages` nhận nguồn link tệp và thao tác tuỳ chọn.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 122 passed (mới: share 6 gồm toàn cây và giữ link, thu hồi/xoá chat, link tổ chức chỉ cho thành viên, chat bận, copy có tệp và gọi lại rồi chat tiếp, tệp theo link).
- Frontend: `pnpm test` 59 passed; `typecheck`, `eslint` (code dự án) sạch; `pnpm build` thành công.
- Chạy thật với RustFS: kịch bản 1–3 đạt (người ngoài xem chat có ảnh; Bình đăng nhập rồi "Hỏi tiếp", bản sao ở workspace cá nhân với object mới thuộc Bình; thu hồi thì link 404, bản sao vẫn đọc được). Kịch bản 4 kiểm bằng test API.

**Lỗi**: L-11 (đã sửa).

**Thay đổi**: TD-014; QD-28; RR-18 (mới).

**Dời**: không.
