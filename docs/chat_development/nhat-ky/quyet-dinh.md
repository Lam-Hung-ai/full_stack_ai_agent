# Nhật ký quyết định

ADR rút gọn. Mỗi quyết định gồm: bối cảnh, lựa chọn chốt, hệ quả, và nguồn chi tiết.

**Luật**
- Không sửa quyết định cũ. Muốn đổi thì thêm quyết định mới ghi "thay cho QD-xx", rồi đổi trạng thái của quyết định cũ.
- Trạng thái đi theo thứ tự: `Đề xuất` → `Chốt` → (`Thay thế bởi QD-yy`).
- Chỉ người dùng (PO) chuyển một quyết định sang `Chốt`.
- Nội dung chi tiết nằm ở tài liệu thiết kế; ở đây chỉ tóm tắt và trỏ tới, không chép lại.

| Mã | Ngày | Quyết định | Nguồn | Trạng thái |
| --- | --- | --- | --- | --- |
| QD-01 | 29/10/2026 | Database giai đoạn 1–4: 24 bảng `chat_app` + 4 bảng checkpoint SDK trong `langgraph_checkpoints`, cùng một database | [database-decisions.md](../database-decisions.md) | Chốt (29/10/2026) |
| QD-02 | 29/10/2026 | Public `threadId` = `conversations.id`; native checkpoint `thread_id` = assistant message ID; `runId` chỉ thuộc protocol AG-UI; ID ứng dụng là UUIDv7 | [conversation-message-run-id-decisions.md](../conversation-message-run-id-decisions.md) | Chốt (29/10/2026) |
| QD-03 | 29/10/2026 | API `/api/v1/conversations…`: input là DTO nghiệp vụ, output là AG-UI SSE; connect không cursor; stop theo assistant message, không body | [chat-agent-api-contract.md](../chat-agent-api-contract.md) | Chốt (29/10/2026) |
| QD-04 | 29/10/2026 | Frontend `ChatAgent extends HttpAgent`, adapter nhỏ, giữ subscriber hiện tại | [chat-agent-client-decisions.md](../chat-agent-client-decisions.md) | Chốt (29/10/2026) |
| QD-05 | 29/10/2026 | Dùng `ag_ui_langgraph.LangGraphAgent` + `EventEncoder` với route FastAPI viết tay; không dùng CopilotKit Runtime/SDK | [copilotkit-agui-integration.md](../copilotkit-agui-integration.md), [ag-ui-manual-wiring.md](../ag-ui-manual-wiring.md) | Chốt (29/10/2026) |
| QD-06 | 29/10/2026 | Tạm bỏ `requestId`/Idempotency-Key và dedup submit; frontend không tự retry mutation | [chat-agent-api-contract.md §9](../chat-agent-api-contract.md#9-xử-lý-mạng-đơn-giản-trong-phạm-vi-hiện-tại) | Chốt (29/10/2026) |
| QD-07 | 29/10/2026 | Checkpoint buffer trong RAM, chỉ export khi interrupt; PostgreSQL ghi content ở terminal/pause, không ghi từng token; không auto-recovery worker chết | [production-data-storage-design.md §7](../production-data-storage-design.md#7-checkpoint-chờ-lâu-mà-không-chiếm-slot) | Chốt (29/10/2026) |
| QD-08 | 29/10/2026 | Một nhánh `chat` cho mọi sprint; mỗi sprint một commit; hỏi trước khi push; vào `main` qua MR (Q-01) | [ke-hoach-sprint.md §5](../ke-hoach-sprint.md#5-nhánh-và-commit) | Chốt (29/10/2026) |
| QD-09 | 29/10/2026 | Chuyển `backend/src/agent_backend` sang `src/app/` + `modules/` theo `backend/AGENTS.md` ở S0 (Q-02) | `backend/AGENTS.md` §4 | Chốt (29/10/2026) |
| QD-10 | 29/10/2026 | Cô lập dữ liệu chat theo `workspace_id`; quyền tổ chức qua membership. Cập nhật `backend/AGENTS.md` ở S0 (Q-03) | [database-decisions.md §4](../database-decisions.md#4-tài-khoản-workspace-và-quyền) | Chốt (29/10/2026) |
| QD-11 | 29/10/2026 | Một migration baseline dbmate gộp từ cấu trúc cuối của SQL giai đoạn 1–4; chuỗi file cũ giữ làm lịch sử; bảng saver do SDK setup (Q-04) | [database_decisions](../../database_decisions/README.md) | Chốt (29/10/2026) |
| QD-12 | 29/10/2026 | Auth theo mẫu `hr-ai/backend`: access token JWT Bearer ngắn hạn, refresh token cookie HttpOnly `SameSite=Strict` có rotation theo họ phiên và phát hiện dùng lại; không claim tổ chức trong token, workspace lấy từ path hoặc conversation và kiểm membership mỗi request (Q-05) | [ke-hoach-sprint.md §2.1](../ke-hoach-sprint.md#21-auth-s1-s6) | Chốt (29/10/2026) |
| QD-13 | 29/10/2026 | Cài TanStack Query, Zustand, Zod, RHF, Vitest ở S0 và tách `src/features/chat`; Playwright khi có kịch bản e2e đầu tiên (Q-07) | `frontend/AGENTS.md` §3, §6 | Chốt (29/10/2026) |
| QD-15 | 29/10/2026 | Lượt trả lời chạy bằng runner trong process backend: `asyncio` task do app sở hữu, tách khỏi HTTP generator, giới hạn concurrency; interface để thay worker riêng sau. Redis cho stop/connect ở S5 (Q-06) | [ke-hoach-sprint.md §1](../ke-hoach-sprint.md#1-lộ-trình) | Chốt (29/10/2026) |
| QD-16 | 29/10/2026 | Xong mỗi sprint: chỉ kiểm tra phần liên quan, commit trên `chat` không cần hỏi, làm tiếp sprint sau. Quyết định nhỏ không ảnh hưởng kiến trúc chung do agent tự quyết và ghi nhật ký (uỷ quyền). Thay phần "commit" của QD-08; vẫn hỏi trước khi push | [ke-hoach-sprint.md §5](../ke-hoach-sprint.md#5-nhánh-và-commit) | Chốt (29/10/2026) |
| QD-17 | 29/10/2026 | SQLAlchemy async và saver LangGraph cùng dùng psycopg 3 (`postgresql+psycopg://`), không dùng asyncpg, để lúc pause ghi checkpoint và message trên cùng kết nối; công cụ và test cũng dùng psycopg 3 thay psycopg2 của hr-ai (uỷ quyền, S0) | `backend/AGENTS.md` mục 1 | Chốt (29/10/2026, uỷ quyền) |
| QD-18 | 29/10/2026 | Token refresh vừa xoay được trình lại trong 10 giây (`REFRESH_REUSE_GRACE_SECONDS`) mà không tính là dùng lại: cấp token mới cùng họ, không thu hồi. Quá hạn đó mới thu hồi cả họ. Đánh đổi: kẻ lấy được cookie trong 10 giây đó không bị phát hiện (uỷ quyền, S1) | `backend/src/app/modules/auth/service.py` | Chốt (29/10/2026, uỷ quyền) |
| QD-19 | 30/10/2026 | Wire của API chat: (1) tạo/liệt kê conversation ở `/workspaces/{id}/conversations`, các route khác suy workspace từ conversation; (2) field JSON của DTO dùng `snake_case`, event AG-UI giữ `camelCase`; (3) liên kết SQL row qua event `CUSTOM chat.assistant` `{conversationId, userMessageId, assistantMessageId, status}`, phát sau `RUN_STARTED` và trước event kết thúc (trạng thái cuối chỉ phát sau commit); (4) native thread của LangGraph là assistant ID, event gửi client được đổi `threadId` về conversation (uỷ quyền, S2) | [chat-agent-api-contract.md §8](../chat-agent-api-contract.md#8-id-và-stream) | Chốt (30/10/2026, uỷ quyền) |
| QD-14 | 29/10/2026 | File S3 theo mẫu `hr-ai`: adapter `ObjectStorage` (boto3, RustFS), khoá do server dựng, presigned PUT rồi `complete` có xác minh cỡ và chữ ký tệp; chỉ `INSERT` `stored_files` sau khi xác minh vì schema chat cấm đổi key | [ke-hoach-sprint.md §2.2](../ke-hoach-sprint.md#22-file-trên-s3-compatible-storage-s7-s8) | Chốt (29/10/2026) |

## Câu hỏi chờ chốt

| Mã | Ngày | Câu hỏi | Chặn sprint | Đề xuất | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| Q-01 | 29/10/2026 | Nhánh và cách commit khi làm theo sprint: một nhánh chung hay mỗi sprint một nhánh; tự commit cuối sprint hay hỏi trước | S0 | Một nhánh `chat`; mỗi sprint một commit; hỏi trước khi push; vào `main` qua MR | Chốt → QD-08 |
| Q-02 | 29/10/2026 | Cấu trúc backend: chuyển `src/agent_backend` sang `src/app/` + `modules/` theo `backend/AGENTS.md` ngay ở S0, hay giữ và chuyển dần | S0 | Chuyển ở S0, trước khi thêm module nghiệp vụ | Chốt → QD-09 |
| Q-03 | 29/10/2026 | `backend/AGENTS.md` yêu cầu cô lập theo `organization_id`, còn database chat scope theo `workspace_id` (gồm workspace cá nhân). Cập nhật AGENTS.md theo `workspace_id`? | S0 | Cập nhật AGENTS.md: cô lập theo `workspace_id`, quyền tổ chức qua membership | Chốt → QD-10 |
| Q-04 | 29/10/2026 | Áp SQL giai đoạn 1–4 thành migration dbmate thế nào: một baseline gộp hay giữ chuỗi 4 file | S0 | Một baseline gộp từ cấu trúc cuối, chuỗi cũ giữ làm lịch sử | Chốt → QD-11 |
| Q-05 | 29/10/2026 | Auth contract (cookie HttpOnly hay bearer, refresh rotation) cho các route chat | S1 | Bản đầu: cookie HttpOnly + refresh rotation. Khi chốt đổi theo mẫu hr-ai: access Bearer + refresh cookie (TD-004) | Chốt → QD-12 |
| Q-06 | 29/10/2026 | Cơ chế dispatch execution: Celery (theo `backend/AGENTS.md`), task supervisor trong process, hay Redis Streams | S2 | (29/10, bổ sung khi rà kế hoạch) Runner trong process: `asyncio` task do app sở hữu, không do HTTP generator; giới hạn concurrency bằng semaphore; interface để thay sau. Redis cho stop/connect ở S5; xét worker riêng (Celery) ở S9 khi cần nhiều process | Chốt → QD-15 |
| Q-07 | 29/10/2026 | Thời điểm cài thư viện frontend theo `frontend/AGENTS.md` (TanStack Query, Zustand, Zod, RHF, Vitest, Playwright) và chuyển sang `src/features/` | S0 | Cài và dựng khung ở S0, cùng lúc tách `features/chat` | Chốt → QD-13 |
| Q-08 | 29/10/2026 | Chính sách nhiều SSE khi chuyển conversation (đang tạm hoãn trong tài liệu) | S5 | Chốt trước khi làm sidebar/chuyển conversation | Mở |

## Mẫu ghi

```markdown
| QD-xx | dd/mm/yyyy | <quyết định> | <file nguồn> | Đề xuất/Chốt (dd/mm/yyyy)/Thay thế bởi QD-yy |
```

```markdown
### QD-xx: <tiêu đề>
- **Ngày / người chốt:** <…>
- **Sprint / task:** <…>
- **Bối cảnh:** <…>
- **Lựa chọn:** (a) … (b) …
- **Chốt:** <…, vì sao>
- **Hệ quả:** <…>
```
