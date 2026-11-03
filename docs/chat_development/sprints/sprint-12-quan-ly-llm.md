# Sprint 12: Quản lý LLM model

| | |
| --- | --- |
| Thời gian | 08/04 – 16/04/2027 (dự kiến) |
| Nhánh | `chat` (QD-08) |
| Phụ thuộc | S11 |
| Ước lượng | 5 nc |
| Mốc | — |
| Use case | Không (vận hành, quản trị hệ thống) |
| Câu hỏi phải chốt trước | Q-14, đã chốt (QD-34) |

## Mục tiêu

1. Model của agent cấu hình trong database thay vì biến môi trường: kết nối (provider của `init_chat_model`, tham số client, API key), model (tên phía provider, tham số) và gán model theo mục đích có thứ tự (chính rồi dự phòng).
2. API key lưu mã hoá (Fernet, khoá `LLM_ENCRYPTION_KEY`), không bao giờ trả về client; chỉ hiện 4 ký tự cuối.
3. Superuser quản lý ở trang riêng `/admin/llm`: kết nối, model, gán model, thử gọi model.
4. Đổi cấu hình có hiệu lực từ lượt tiếp theo ở mọi process, không cần khởi động lại.

## Không làm

- Người dùng chọn model theo từng chat (QD-34).
- Cấu hình model theo tổ chức hoặc workspace (QD-34: toàn hệ thống).
- Xoay khoá mã hoá tự động (ghi trong `van-hanh.md` cách làm tay).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S12-DOC-01 | Bắt đầu sprint | Ghi dòng `BẮT ĐẦU` ở dòng thời gian; rà rủi ro | 0,1 | Dòng thời gian có dòng bắt đầu | ☑ |
| CH-S12-DB-01 | Bảng LLM | Migration: `llm_connections` (key, tên, provider, `client_params`, `api_key_ciphertext`, `api_key_hint`, `is_active`), `llm_models` (key, `connection_id`, model, tên, `params`, `is_active`), `llm_model_assignments` (purpose, position, `model_id`); CHECK, FK `RESTRICT`, `touch_updated_at` | 0,5 | `dbmate up`/`down`/`up` sạch; test phát lại migration khớp `schema.sql` | ☑ |
| CH-S12-BE-01 | Module `llm` (quản trị) | Router `/api/v1/admin/llm/…` chỉ cho superuser: provider hỗ trợ, CRUD kết nối và model, đặt danh sách model của một mục đích, thử gọi model. Mã hoá key bằng `cryptography` (Fernet); kiểm tra provider có trong `init_chat_model` và đã cài package; tham số không được chứa khoá bí mật | 1,5 | Test: không phải superuser bị 403; key không xuất hiện trong response và được mã hoá trong DB; provider lạ bị 422; xoá model đang được gán bị 409 | ☑ |
| CH-S12-BE-02 | Agent dùng cấu hình DB | `ai/models` dựng chuỗi model của mục đích `chat` và `title` từ DB bằng `init_chat_model`; chưa gán thì dùng biến môi trường như trước. Graph cache theo cả cấu hình model; vân tay cấu hình đọc mỗi lượt nên đổi có hiệu lực ngay. `GET /users/me` thêm `is_superuser` | 1 | Test: lượt dùng model và key từ DB (fallback theo thứ tự); đổi gán thì lượt sau dùng model mới; không có gán thì dùng env | ☑ |
| CH-S12-FE-01 | Trang `/admin/llm` | Feature `admin`: ba tab Kết nối, Model, Gán model; form tạo/sửa (RHF + Zod), key chỉ nhập, không hiện lại; nút thử model; mục "Quản trị LLM" trong menu người dùng khi là superuser | 1,4 | Vitest cho schema form và tiện ích; `typecheck`, `eslint`, `build` xanh | ☑ |
| CH-S12-QA-01 | Kịch bản nghiệm thu | Chạy thật kịch bản 1–3 | 0,3 | Đạt | ☑ |
| CH-S12-DOC-02 | Cập nhật tài liệu | API contract §2, `van-hanh.md` (`LLM_ENCRYPTION_KEY`, cách đổi khoá), `.env.example` | 0,2 | — | ☑ |

**Migration**: một file tạo ba bảng (CH-S12-DB-01).

## Kịch bản nghiệm thu

1. **Superuser** mở `/admin/llm`, tạo kết nối OpenRouter với key, tạo hai model, gán cho `chat` theo thứ tự, bấm thử model.
   - Key chỉ hiện `…abcd`; thử model trả lời được.
2. **Người dùng** gửi câu hỏi.
   - Lượt chạy bằng model chính trong DB; tắt model chính (hoặc key sai) thì lượt dùng model dự phòng.
3. **Người dùng thường** mở `/admin/llm` hoặc gọi API quản trị.
   - Trang báo không có quyền; API trả 403.

## Rủi ro riêng

- Mất `LLM_ENCRYPTION_KEY` thì không giải mã được key đã lưu. Giảm thiểu: báo lỗi rõ khi khoá thiếu hoặc sai; `van-hanh.md` ghi cách nhập lại key.
- Tham số do superuser nhập (base URL…) có thể trỏ tới địa chỉ nội bộ. Giảm thiểu: chỉ superuser; không cho tham số chứa key bí mật; ghi log mỗi thay đổi.
- Đọc cấu hình mỗi lượt làm chậm lượt. Giảm thiểu: một truy vấn vân tay nhỏ; graph và model cache theo vân tay.

## Tổng kết

Kết thúc 02/11/2026 (sớm hơn lịch dự kiến 08/04 – 16/04/2027).

**Đã xong**: 7/7 task.
- Backend: ba bảng LLM; module `llm` (`catalog`, `crypto`, quản trị); agent và tên chat dùng chuỗi model trong database, chưa gán thì dùng biến môi trường; `ModelFallbackMiddleware` cho model dự phòng; dependency `SuperUser`; `/users/me` có `is_superuser`.
- Frontend: feature `admin` (tab Gán model, Model, Kết nối; form RHF + Zod; key chỉ nhập, hiện `…abcd`; nút thử model; sắp thứ tự model chính và dự phòng), trang `/admin/llm`, mục menu cho superuser.

**Kiểm tra** (QD-16, phần liên quan):
- Migration up/down/up trên database dùng một lần; test phát lại migration khớp `schema.sql`.
- Backend: `ruff`, `pyrefly` sạch; `pytest` 161 passed (mới: quản trị LLM 5, chạy theo cấu hình DB 2).
- Frontend: `pnpm test` 74 passed (mới 6); `typecheck`, `eslint` sạch; `pnpm build` thành công.
- Kịch bản 1–3 chạy thật với OpenRouter: người dùng thường nhận 403; kết nối chỉ giữ 4 ký tự cuối của key; thử model trả "OK", model sai tên báo lỗi của provider; lượt chạy bằng model trong DB; model chính hỏng thì model dự phòng trả lời; model đang gán không xoá được; giao diện gán model rồi lưu ghi đúng vào DB. Sau QA đã bỏ gán để dev quay về biến môi trường; tài khoản `demo@example.com` được bật superuser để chạy kịch bản.

**Lỗi**: không.

**Thay đổi**: TD-022; QD-35.

**Dời**: không.
