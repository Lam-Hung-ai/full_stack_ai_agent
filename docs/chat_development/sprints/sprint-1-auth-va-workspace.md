# Sprint 1: Auth và workspace

| | |
| --- | --- |
| Thời gian | 16/11 – 27/11/2026 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S0 |
| Ước lượng | 7 nc |
| Mốc | — |
| Use case | O01 |
| Câu hỏi phải chốt trước | Q-05: đã chốt (QD-12) |

## Mục tiêu

1. Đăng ký, đăng nhập, xoay refresh token theo họ phiên có phát hiện dùng lại, đăng xuất một phiên hoặc mọi phiên (QD-12, mẫu hr-ai).
2. `GET /users/me`, danh sách workspace; dependency user và workspace kiểm membership ở mỗi request (QD-10).
3. Frontend có đăng nhập, đăng ký, token trong bộ nhớ, tự refresh khi 401, ô chọn workspace, đăng xuất.

## Không làm

- Email xác minh, đặt lại mật khẩu, lời mời tổ chức (S6).
- Tạo tổ chức qua API (S6); test và dev tạo bằng SQL.
- Route conversation dùng workspace (S2).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S1-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S0 | 0,1 | — | ☑ |
| CH-S1-BE-01 | Security primitives | `config/security.py`: argon2 trong threadpool, băm token SHA-256, JWT HS256 không claim tổ chức; settings JWT, cookie, rate limit | 0,5 | Test token sai trả `invalid_access_token` | ☑ |
| CH-S1-BE-02 | Module `auth` | `register`, `login`, `refresh`, `session`, `logout`, `logout-all`; cookie HttpOnly `SameSite=Strict` `path=/api/v1/auth`; kiểm origin khi đọc cookie; rotation theo `family_id` với `consumed_at`; rate limit trong bộ nhớ | 2 | `tests/api/auth/test_auth.py` | ☑ |
| CH-S1-BE-03 | `users`, `workspaces`, dependency | `GET /users/me`; `GET /workspaces` (phân trang chung), `GET /workspaces/{id}`; `common/dependencies/auth.py` (`CurrentUser`), `workspace.py` (`CurrentWorkspace`) | 1 | `tests/api/workspaces`, `tests/security/test_workspace_isolation.py` | ☑ |
| CH-S1-BE-04 | Xuất OpenAPI | `uv run openapi` cho codegen frontend | 0,15 | — | ☑ |
| CH-S1-FE-01 | Phiên và API client | `lib/auth/session.ts` (token trong bộ nhớ), `lib/api/client.ts` gắn Bearer, refresh một lần dùng chung khi 401, báo hết phiên; rewrite `/api/v1` sang backend; `pnpm generate:api` | 1 | Test client: một lần refresh cho nhiều 401 | ☑ |
| CH-S1-FE-02 | Feature `auth` | Trang đăng nhập, đăng ký (RHF + Zod), `AuthGate`, `UserMenu`, `safeNext` chống open redirect | 1,25 | Chạy thật trên trình duyệt | ☑ |
| CH-S1-FE-03 | Feature `workspaces` | `useWorkspaces`, `useCurrentWorkspace`, `WorkspaceSwitcher`; store Zustand chỉ giữ id đã chọn | 0,75 | Test `pickWorkspace`; chuyển workspace trên trình duyệt | ☑ |
| CH-S1-DOC-02 | Cập nhật tài liệu | API contract §2 ghi các route auth/workspace đã có | 0,1 | — | ☑ |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Khách** mở `/`.
   - Bị chuyển tới `/login?next=%2F`.
2. **Khách** đăng ký ở `/register`.
   - Vào thẳng màn chat, header có "Cá nhân" và tên người dùng.
3. **Người dùng** tải lại trang.
   - Vẫn đăng nhập (phiên mở lại từ cookie refresh).
4. **Người dùng** là thành viên một tổ chức, chọn tổ chức ở ô workspace, tải lại trang.
   - Workspace tổ chức vẫn được chọn.
5. **Người dùng** đăng xuất.
   - Về `/login`; mở `/` lại bị chuyển về đăng nhập.

## Rủi ro riêng

- Hai tab cùng tải trang gửi cùng một cookie refresh. Giảm thiểu: ân hạn 10 giây (QD-18).

## Tổng kết

Kết thúc 29/10/2026 (sớm hơn lịch dự kiến 16/11 – 27/11).

**Đã xong**: 9/9 task.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 28 passed (auth 13, workspace 3, cô lập workspace 4, cùng các test S0).
- Frontend: `pnpm test` 29 passed; `pnpm typecheck` sạch; `eslint` sạch với thư mục đã đổi; `pnpm build` thành công.
- Chạy thật bằng Playwright: đủ 5 kịch bản nghiệm thu.

**Lỗi phát hiện khi chạy thật**: L-02 (request session bị hủy làm mất cookie đã xoay, rồi request lặp bị coi là dùng lại token, cả phiên bị thu hồi) đã sửa; L-03 (id trùng giữa hai form khi Next giữ route ẩn) đã sửa.

**Thay đổi**: TD-007; QD-18.

**Dời**: không.
