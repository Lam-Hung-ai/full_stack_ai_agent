# Sprint 6: Tổ chức và quyền

| | |
| --- | --- |
| Thời gian | 25/01 – 05/02/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S1, S3 |
| Ước lượng | 8 nc |
| Mốc | — |
| Use case | O02, O07, T07 |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Người dùng tạo tổ chức; owner/admin mời thành viên bằng email, người được mời nhận lời mời (có tài khoản thì đăng nhập rồi nhận, chưa có thì tạo tài khoản ngay trên trang mời).
2. Quản lý thành viên: xem danh sách, đổi vai trò, xoá khỏi tổ chức; thành viên tự rời tổ chức. Tổ chức luôn còn ít nhất một owner.
3. Vai trò: tạo, sửa, xoá vai trò; gán quyền quản trị, quyền chat và quyền tool (`tool.<tên>`). Không ai cấp được quyền mình không có.
4. Rời hoặc bị xoá khỏi tổ chức thì mất quyền đọc chat, resume và tool ngay ở request kế tiếp; lượt đang chạy của người đó trong workspace tổ chức bị dừng (O07).
5. Email xác minh và đặt lại mật khẩu qua mailer chung (SMTP; dev dùng Mailpit).
6. Frontend: màn quản trị tổ chức (thành viên, lời mời, vai trò, cài đặt), trang nhận lời mời, quên/đặt lại mật khẩu, xác minh email.

## Không làm

- Nhóm/đơn vị trong tổ chức (O02 phần "team Sales": schema không có `organization_units`).
- Nhật ký thao tác (`activity_logs` chưa có trong schema, ghi đè ở `backend/AGENTS.md`).
- Rate limit qua Redis (S9).
- Skill: registry hiện chỉ có tool; quyền skill khi có skill.

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S6-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S5; không có Q chặn | 0,1 | — | ☑ |
| CH-S6-BE-01 | Mailer | `common/email.py` (SMTP trong threadpool, timeout), gửi sau commit; `SMTP_*`, `FRONTEND_URL`; Mailpit trong `compose.yaml` | 0,5 | Test với mailer giả | ☑ QD-26 |
| CH-S6-BE-02 | Email xác minh, đặt lại mật khẩu | `/auth/email-verification/*`, `/auth/password-reset/*` dùng bảng `verifications`; yêu cầu luôn 202; đặt lại thì thu hồi mọi phiên; đăng ký gửi thư xác minh | 1 | Test API | ☑ |
| CH-S6-BE-03 | Tổ chức | Module `organizations`: tạo, xem (kèm quyền của tôi), đổi tên, rời | 0,75 | Test API | ☑ |
| CH-S6-BE-04 | Thành viên, lời mời | Module `members`: danh sách, đổi vai trò, xoá; lời mời tạo/thu hồi/xem trước/nhận/tạo tài khoản khi nhận | 1,5 | Test API + cô lập giữa tổ chức | ☑ QD-25 |
| CH-S6-BE-05 | Vai trò và quyền | Trong `authorization`: danh mục quyền, CRUD vai trò, owner khoá; `iam sync-permissions` cấp quyền mới cho owner (RR-15) | 1 | Test API | ☑ QD-24, RR-15 |
| CH-S6-BE-06 | Rời tổ chức với chat | Xoá/rời thì khoá vai trò, dừng lượt đang chạy; resume/đọc bị chặn; thu hồi quyền tool khi đang chờ duyệt thì tool bị từ chối (T07) | 0,75 | Test API | ☑ |
| CH-S6-FE-01 | Tài khoản | Quên/đặt lại mật khẩu, xác minh email, gửi lại thư xác minh | 0,75 | Vitest schema + chạy thật | ☑ |
| CH-S6-FE-02 | Quản trị tổ chức | Feature `organizations`: tạo tổ chức, màn thành viên/lời mời/vai trò/cài đặt, ẩn thao tác theo quyền | 1,5 | Vitest + chạy thật | ☑ |
| CH-S6-FE-03 | Nhận lời mời | Trang `/invitations?token=`: nhận khi đã đăng nhập, tạo tài khoản khi chưa có | 0,5 | Chạy thật | ☑ L-10 |
| CH-S6-DOC-02 | Cập nhật tài liệu | API contract, biến môi trường | 0,25 | — | ☑ TD-012 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Owner** tạo tổ chức "Công ty A", mời `b@example.com`.
   - Mailpit có thư mời; B (chưa có tài khoản) mở link, tạo tài khoản, vào được workspace "Công ty A" với vai trò Member.
2. **Owner** tạo vai trò "Nhân viên có tool" có quyền `tool.get_current_time`, gán cho B.
   - B hỏi giờ thì agent dùng được tool; bỏ quyền khỏi vai trò thì lượt sau không còn tool.
3. **Owner** xoá B khi B đang có lượt chạy.
   - Lượt của B dừng; B không còn thấy workspace, mở link chat cũ thì không đọc được.
4. **Người dùng** quên mật khẩu.
   - Nhận thư, đặt mật khẩu mới, phiên cũ bị đăng xuất, đăng nhập bằng mật khẩu mới được.
5. **Owner duy nhất** bấm rời tổ chức.
   - Bị từ chối với thông báo phải chuyển quyền owner trước.

## Rủi ro riêng

- Gửi thư thất bại (SMTP chưa cấu hình): yêu cầu vẫn trả 202, lời mời vẫn tạo; ghi log cảnh báo, có nút gửi lại.
- Leo thang quyền qua màn vai trò. Giảm thiểu: chỉ cấp được quyền mình có; vai trò owner chỉ owner gán; test riêng.

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 25/01 – 05/02/2027).

**Đã xong**: 11/11 task.
- Backend: mailer `common/email.py` (gửi sau commit, lỗi chỉ ghi log); xác minh email và đặt lại mật khẩu trên bảng `verifications`; module `organizations` (tạo, xem kèm quyền của tôi, đổi tên) và `members` (thành viên, đổi vai trò, xoá, rời, lời mời, nhận lời mời, tạo tài khoản từ lời mời); `authorization` thêm danh mục quyền và CRUD vai trò, owner khoá, chống leo thang; `iam sync-permissions` cấp quyền mới cho owner (RR-15). Rời hoặc bị xoá thì tắt vai trò, dừng lượt đang chạy, huỷ lượt đang chờ (O07). Quyền tool thu hồi khi đang chờ duyệt đã có test từ S4 (T07).
- Frontend: feature `organizations` (tạo tổ chức, màn Thành viên / Lời mời / Vai trò / Cài đặt hiện theo quyền, trang nhận lời mời), quên/đặt lại mật khẩu, xác minh email, menu "Gửi thư xác minh"; mục "Quản lý tổ chức", "Tạo tổ chức" trong menu workspace; `ConfirmDialog`, `NameDialog` chuyển sang `components/shared`; hook `useSelectWorkspace` dùng chung.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 106 passed (mới: link tài khoản 5, tổ chức 3, thành viên/lời mời 7, vai trò 6, cô lập giữa tổ chức 1).
- Frontend: `pnpm test` 49 passed; `typecheck`, `eslint` (code dự án) sạch; `pnpm build` thành công.
- Chạy thật với Mailpit và model OpenRouter: kịch bản 1–5 đạt (mời người chưa có tài khoản rồi tạo tài khoản từ thư; vai trò có `tool.get_current_time` thì dùng được tool, bỏ quyền thì không; xoá thành viên khi đang chạy thì lượt `cancelled`, mất workspace, lịch sử 404, lượt đang chờ cũng bị huỷ; đặt lại mật khẩu đăng xuất phiên cũ; owner duy nhất không rời được). Thêm: trang xác minh email với link đúng và sai.

**Lỗi**: L-10 (đã sửa).

**Thay đổi**: TD-012; QD-24, QD-25, QD-26; RR-15 đã xử lý.

**Dời**: không. Quyền skill chờ có skill trong registry.

**Môi trường**: cần `uv run iam sync-permissions` sau khi triển khai (owner nhận quyền mới); cấu hình `SMTP_*`, `FRONTEND_URL`; dev chạy `docker compose up -d mailpit` và đọc thư ở http://localhost:8025.
