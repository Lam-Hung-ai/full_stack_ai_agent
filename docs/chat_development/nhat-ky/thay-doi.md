# Nhật ký thay đổi

Ghi mọi thay đổi so với kế hoạch và thiết kế đã viết (tài liệu trong `docs/chat_development/`, `docs/database_decisions/`, `sprints/`), gồm:
- Đổi API route, DTO, event AG-UI hoặc metadata liên kết SQL message.
- Đổi schema, trigger, index; đổi quy ước ID.
- Dời task, cắt phạm vi, đổi lịch sprint.
- Thay đổi chung ảnh hưởng nhiều sprint, ví dụ đổi quy ước, đổi nhánh, nâng phiên bản SDK (AG-UI, LangGraph).

## Phân loại

| Nhóm | Ví dụ |
| --- | --- |
| `API` | Thêm trường vào DTO history; đổi response của stop |
| `Event` | Chốt vị trí wire của SQL assistant ID trong stream AG-UI |
| `Schema` | Thêm index cho `messages`; đổi CHECK của `status` |
| `ID` | Đổi cách sinh `runId` phía server |
| `Quyền` | Thêm permission tool/skill mới vào registry |
| `SDK` | Nâng `@ag-ui/client`, `ag-ui-langgraph`, `langgraph` |
| `Phạm vi` | Dời CH-S3-BE-02 sang S4 |
| `Lịch` | Dời S2 một tuần |
| `Tài liệu` | Sửa tài liệu thiết kế cho khớp quyết định |
| `Chung` | Đổi quy ước mã task; đổi nhánh |

## Bảng

| Mã | Ngày | Sprint | Nhóm | Thay đổi | Lý do | Ảnh hưởng | File thiết kế đã sửa | Task / MR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TD-001 | 29/10/2026 | — | Tài liệu | Use case C04: stop theo conversation + assistant `messageId`, không body, bỏ `runId`. Dòng ghi chú sau bảng hội thoại bỏ "wire runId". Mục 5 bỏ "API dedupe", đổi "exact stop" thành "phối hợp stop theo assistant message" | Tài liệu use case cũ, lệch [quyết định ID](../conversation-message-run-id-decisions.md) và [API](../chat-agent-api-contract.md) (L-01) | Không | `chat-use-cases-and-organization-access.md` | — |
| TD-002 | 29/10/2026 | — | Chung | Tạo `nhat-ky/` (5 file), `ke-hoach-sprint.md` và `sprints/_mau-sprint.md` theo mẫu `hr-ai/docs/audit_log` | Người dùng yêu cầu thiết lập nhật ký để chuẩn bị code theo sprint | Mọi sprint | `README.md` | — |
| TD-003 | 29/10/2026 | — | Phạm vi | Rà lại lộ trình: S0 → S8 thành S0 → S9. Thêm S6 tổ chức và quyền (gồm email xác minh, đặt lại mật khẩu); S2 thành lát dọc gửi câu hỏi end-to-end; edit/regenerate/stop/pin/archive/folder và registry quyền tool vào S3; file thành S7, share/copy thành S8; Langfuse, log, backpressure, load test vào S9. Xếp lịch dự kiến 02/11/2026 – 19/03/2027, ≈ 73 nc | Người dùng yêu cầu rà phân bổ; bản đầu thiếu quản trị tổ chức và quyền tool, S2 không nghiệm thu end-to-end được, S3 quá tải (chi tiết ở [ke-hoach-sprint.md §8](../ke-hoach-sprint.md#8-kết-quả-rà-soát-phân-bổ-29102026)) | Mọi sprint | `ke-hoach-sprint.md` | — |
| TD-004 | 29/10/2026 | — | Chung | Chốt Q-01, Q-02, Q-03, Q-04, Q-05, Q-07 thành QD-08 → QD-13. Q-05 đổi từ "cookie HttpOnly + refresh rotation" sang mẫu hr-ai: access Bearer + refresh cookie, bỏ claim tổ chức | Người dùng đồng ý các đề xuất; khi đối chiếu hr-ai, `refresh_tokens` của schema chat không gắn tổ chức nên không mang `org` trong token như hr-ai | S0, S1 | `nhat-ky/quyet-dinh.md`, `ke-hoach-sprint.md` §2 | — |
| TD-005 | 29/10/2026 | — | Phạm vi | S7 dùng storage của hr-ai (`common/storage/`, `lib/storage/upload.ts`) thay vì viết mới; ước lượng 6 → 5 nc; key chat luôn private theo workspace, chỉ ghi `stored_files` sau khi xác minh (QD-14) | Người dùng: "phần file s3 thì cũng có thể tham khảo backend của hr-ai" | S7, S8 (`copy_object`) | `ke-hoach-sprint.md` §1, §2.2 | — |
| TD-006 | 29/10/2026 | S0 | Chung | (1) PostgreSQL dev chạy bằng `compose.yaml` (postgres:18.0, cổng 5433) vì PostgreSQL hệ thống không cho tạo database. (2) Baseline là bản dump cấu trúc cuối, có `SET LOCAL check_function_bodies = false` vì pg_dump đặt hàm SQL trước bảng; `apply_schema` của test làm tương tự. (3) `uv run db export` loại bảng saver và `schema_migrations`; `generate` chỉ đọc schema `chat_app`. (4) Frontend cho phép build script `esbuild` (Vitest); `frontend/.env.example` trước bị `.gitignore` bỏ qua, nay được commit. (5) `CORS_ORIGINS` đổi thành `ALLOWED_ORIGINS` (danh sách JSON) theo settings mới | Chi tiết triển khai S0 | Dev phải chạy `docker compose up -d postgres`, `dbmate up`, `uv run db checkpoints`; `.env` cũ phải đổi biến CORS | `backend/README.md`, `backend/AGENTS.md` mục 1 | CH-S0-BE-01, BE-03, DB-01, FE-01 |
| TD-007 | 29/10/2026 | S1 | API | Thêm route `/api/v1/auth/{register,login,refresh,session,logout,logout-all}`, `GET /api/v1/users/me`, `GET /api/v1/workspaces`, `GET /api/v1/workspaces/{id}`. Access token chỉ có `sub`, `sid`; workspace lấy từ path. Frontend gọi `/api/v1` cùng origin qua rewrite của Next (`BACKEND_URL`). Lựa chọn workspace lưu id trong localStorage (Zustand persist) | Thực hiện QD-12, QD-10 | S2 dùng `CurrentWorkspace`, `apiClient` và rewrite cho các route conversation | `chat-agent-api-contract.md` §2 | CH-S1-BE-02, BE-03, FE-01 |


## Mẫu ghi

```markdown
| TD-xxx | dd/mm/yyyy | S<n> | <Nhóm> | <đổi gì, từ → thành> | <vì sao> | <sprint/task/người dùng nào bị ảnh hưởng> | <file> | CH-S<n>-<lớp>-<số> / !MR |
```

Thay đổi lớn (đổi kiến trúc, đổi luật cốt lõi) thì ghi thêm `QD` ở [quyet-dinh.md](./quyet-dinh.md) và trỏ hai chiều.
