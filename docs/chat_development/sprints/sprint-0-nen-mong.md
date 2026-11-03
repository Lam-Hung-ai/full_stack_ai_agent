# Sprint 0: Nền móng

| | |
| --- | --- |
| Thời gian | 02/11 – 13/11/2026 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | Không |
| Ước lượng | 6 nc |
| Mốc | M-A: Nền móng |
| Use case | — |
| Câu hỏi phải chốt trước | Q-01, Q-02, Q-03, Q-04, Q-07: đã chốt (QD-08 → QD-13) |

## Mục tiêu

1. Backend theo cấu trúc `src/app/` của `backend/AGENTS.md` (QD-09): settings, DB session, error format, request id, logging.
2. Database chat chạy được bằng dbmate từ một migration baseline (QD-11); `schema.sql` và `generated_tables.py` sinh lại được; test chứng minh không drift.
3. Pytest chạy với PostgreSQL tạm.
4. Frontend có thư viện theo `frontend/AGENTS.md` (QD-13), API client chung, chat tách vào `features/chat`, Vitest chạy được.
5. `POST /agent` cũ vẫn chạy để UI hiện tại dùng tiếp tới S2.

## Không làm

- Chưa có auth, route `/api/v1/conversations` (S1, S2).
- Chưa dùng saver PostgreSQL trong graph (S4); S0 chỉ có lệnh setup bảng saver.
- Chưa sinh client OpenAPI frontend: chưa có route `/api/v1` nào cần (S1).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S0-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, rà rủi ro | 0,1 | Dòng thời gian có dòng bắt đầu | ☑ |
| CH-S0-BE-01 | Chuyển cấu trúc backend | `src/agent_backend` → `src/app/` (`main.py`, `config/`, `database/`, `common/`, `modules/agent/`, `tools/`); Python 3.13; pin SDK AG-UI/LangGraph | 1 | `uv run uvicorn app.main:app` chạy; `POST /agent` stream như cũ | ☑ |
| CH-S0-BE-02 | Hạ tầng dùng chung | `config/settings.py` (pydantic-settings), `database/session.py` (psycopg 3 async, `search_path=chat_app,public`), `common/exceptions/handlers.py` (lỗi `{error:{code,message,details,request_id}}`), `common/request_context.py` (request id), `common/logging.py` | 1 | Test API: 404 và lỗi validation đúng format, có `request_id`, header `X-Request-Id` | ☑ |
| CH-S0-DB-01 | Migration baseline | `db/migrations/<ts>_chat_baseline.sql` từ cấu trúc cuối SQL giai đoạn 1–4 (schema `chat_app`, `langgraph_checkpoints`) | 1 | `dbmate up`/`rollback`/`up` sạch trên DB tạm | ☑ |
| CH-S0-BE-03 | Công cụ database | `uv run db export --clean`, `uv run db generate` (port từ hr-ai), `uv run db checkpoints` (setup 4 bảng saver bằng SDK) | 0,75 | `db/schema/schema.sql`, `generated_tables.py` sinh được; lệnh checkpoints tạo đủ 4 bảng | ☑ |
| CH-S0-QA-01 | Khung test backend | `tests/support/postgres.py` (cluster tạm), `tests/fixtures/database.py`, `tests/integration/test_migrations.py`, `tests/api/test_health.py` | 0,75 | Pytest xanh | ☑ |
| CH-S0-FE-01 | Thư viện và hạ tầng frontend | Cài TanStack Query, Zustand, Zod, RHF, Vitest, Testing Library; script `typecheck`, `test`; `app/providers.tsx`; `config/env.ts`; `lib/api/client.ts`, `api-error.ts` | 0,75 | `pnpm typecheck`, `pnpm test`, `pnpm lint` xanh | ☑ |
| CH-S0-FE-02 | Tách `features/chat` | Chuyển `use-agent-chat`, `agui-messages`, `reasoning-summary` và màn chat vào `features/chat`; `page.tsx` chỉ compose | 0,5 | UI chat như cũ; test Vitest cho `buildTurns`, `latestLine` | ☑ |
| CH-S0-DOC-02 | Cập nhật tài liệu | `backend/AGENTS.md` theo QD-10 (cô lập `workspace_id`), README backend/frontend | 0,15 | — | ☑ |

**Migration**: `…_chat_baseline.sql`.

## Kịch bản nghiệm thu

1. **Dev** tạo database trống, chạy `dbmate up`, `uv run db checkpoints`, rồi `uv run db export --clean`, `uv run db generate`.
   - Không có diff với file đã commit.
2. **Dev** chạy backend và frontend, hỏi một câu ở UI.
   - Câu trả lời stream như trước S0, có reasoning và tool.
3. **Dev** gọi `GET /api/v1/khong-ton-tai`.
   - 404, body `{"error": {"code": "not_found", ...,"request_id": ...}}`.

## Rủi ro riêng

- Đổi driver sang psycopg 3 có thể khác hành vi asyncpg. Giảm thiểu: S0 chỉ dùng session ở test và tool; S1 mới có truy vấn nghiệp vụ.

## Tổng kết

Kết thúc 29/10/2026 (sớm hơn lịch dự kiến 02/11 – 13/11).

**Đã xong**: 9/9 task.
- Backend chuyển sang `src/app/` (`config`, `database`, `common`, `modules/agent`, `tools`), Python 3.13; pin chính xác AG-UI, LangGraph, `langchain-core`, psycopg 3 (QD-17).
- Lỗi theo `{"error": {code, message, details, request_id}}`; middleware request id nhận `X-Request-Id` an toàn hoặc sinh mới; log JSON có `request_id`.
- Migration `20261029093342_chat_baseline.sql`: dump cấu trúc cuối của SQL giai đoạn 1 → 4 (24 bảng `chat_app`, schema `langgraph_checkpoints` rỗng). `dbmate up`, `rollback`, `up` sạch.
- `uv run db export --clean | generate | checkpoints`; `schema.sql` và `generated_tables.py` sinh từ database vừa migrate.
- `compose.yaml` chạy PostgreSQL 18 dev ở cổng 5433 (TD-006).
- Frontend: TanStack Query, Zustand, Zod, RHF, Vitest, Testing Library; `app/providers.tsx`, `config/env.ts`, `lib/api` (`apiClient`, `ApiError`); chat chuyển vào `features/chat`, `page.tsx` chỉ compose.
- `backend/AGENTS.md` có mục "Ghi đè cho dự án chat" (QD-10, QD-15, QD-17).

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff check`, `ruff format --check`, `pyrefly check` sạch; `pytest` 8 passed (test migration so `schema.sql` và kiểm 4 bảng saver; test lỗi, request id).
- Frontend: `pnpm typecheck` sạch; `pnpm test` 14 passed; `pnpm build` thành công. `pnpm lint` sạch với file đã đổi; 13 lỗi có sẵn trong component vendor ghi ở RR-12.
- Chạy thật: `GET /health`; `POST /agent` qua proxy Next stream đủ `REASONING_*`, `TEXT_MESSAGE_*`, `RUN_FINISHED`.

**Thay đổi**: TD-006; QD-17; RR-12 mới; RR-04 đã xử lý.

**Dời**: không.
