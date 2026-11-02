# Sprint 11: Đổi tên message thành turn

| | |
| --- | --- |
| Thời gian | 05/04 – 07/04/2027 (dự kiến) |
| Nhánh | `chat` (QD-08) |
| Phụ thuộc | S10 (và đợt tái tổ chức `ai`, TD-019) |
| Ước lượng | 2,5 nc |
| Mốc | — |
| Use case | Không (đổi tên, hành vi giữ nguyên) |
| Câu hỏi phải chốt trước | Q-13, đã chốt (QD-33) |

## Mục tiêu

1. Một dòng của bảng hội thoại gọi là **turn**: một câu hỏi của người dùng là một turn, một câu trả lời của AI (gọi tool, suy luận, trả lời) là một turn. Ví dụ: turn 1 người dùng hỏi đường đến Hà Nội; turn 2 AI gọi tool, suy luận, trả lời; turn 3 người dùng cảm ơn.
2. Tên thống nhất từ database, code backend, API, frontend đến tài liệu. Chữ "message" chỉ còn dùng cho message AG-UI bên trong `content` của một turn.
3. Hành vi, dữ liệu và id giữ nguyên: đổi tên tại chỗ, không chép dữ liệu, mọi test hiện có vẫn xanh.

## Mapping

| Hiện tại | Sau S11 |
| --- | --- |
| Bảng `messages`, `message_files` | `turns`, `turn_files` |
| Bảng `share_snapshot_messages`, `share_snapshot_message_files` | `share_snapshot_turns`, `share_snapshot_turn_files` |
| Cột `parent_message_id`, `current_message_id`, `message_id` | `parent_turn_id`, `current_turn_id`, `turn_id` |
| Hàm `check_message_tree`, `check_user_message_final`, `forbid_message_delete`, `guard_message_file`, `guard_message_lifecycle`, `lock_message_tree`, `message_text` | `check_turn_tree`, `check_user_turn_final`, `forbid_turn_delete`, `guard_turn_file`, `guard_turn_lifecycle`, `lock_turn_tree`, `turn_text` |
| Index, constraint `messages_*`, `message_files_*`, `share_snapshot_messages_*` | `turns_*`, `turn_files_*`, `share_snapshot_turns_*` |
| Route `/conversations/{id}/messages`, `…/messages/{message_id}/edit\|regenerate\|resume\|stop` | `/conversations/{id}/turns`, `…/turns/{turn_id}/edit\|regenerate\|resume\|stop` |
| Query `?from_message_id=` | `?from_turn_id=` |
| Body gửi/sửa `{parent_message_id, message: {id, text, file_ids}}` | `{parent_turn_id, turn: {id, text, file_ids}}` |
| Trường `parent_message_id`, `current_message_id`; tìm kiếm `message_id`; share `messages`, `current_message_id` | `parent_turn_id`, `current_turn_id`; `turn_id`; `turns`, `current_turn_id` |
| Mã lỗi `message_not_found`, `message_id_conflict`, `empty_message` | `turn_not_found`, `turn_id_conflict`, `empty_turn` |
| Event `CUSTOM chat.assistant` `{userMessageId, assistantMessageId}` | `CUSTOM chat.turn` `{userTurnId, assistantTurnId}` |
| Export JSON `messages` | `turns` |
| `MessageRepository`, `SharedMessage`, `ChatMessageInput` | `TurnRepository`, `SharedTurn`, `TurnInput` |
| Frontend `/c/{id}?m=` | `/c/{id}?t=` |

**Giữ nguyên**: message AG-UI trong `content` (id, `toolCallId`, `MessagesSnapshot`…), role `user`/`assistant`, `branch_messages` (trả message AG-UI), checkpoint (`thread_id` vẫn là id của turn assistant), khoá Redis, `pending_action` (`question_message_id` là id message AG-UI).

## Không làm

- Bảng LLM model và màn quản trị (QD-34): sprint riêng, chưa lập.
- Giữ route cũ song song: chỉ frontend của dự án gọi API, backend và frontend triển khai cùng lúc.
- Sửa tài liệu thiết kế database giai đoạn 1–4 (lịch sử); chỉ thêm ghi chú trỏ sang QD-33.

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S11-DOC-01 | Bắt đầu sprint | Ghi dòng `BẮT ĐẦU` ở dòng thời gian; rà rủi ro | 0,1 | Dòng thời gian có dòng bắt đầu | ☑ |
| CH-S11-DB-01 | Migration đổi tên | `ALTER TABLE … RENAME`, `RENAME COLUMN`, `RENAME CONSTRAINT`, `ALTER INDEX … RENAME`, `ALTER FUNCTION … RENAME`; viết lại thân mọi hàm nhắc tới bảng/cột cũ (`CREATE OR REPLACE`), gồm `valid_agui_bundle`, các guard của share/copy/file và `turn_text` (index tìm kiếm dựng lại); `migrate:down` đổi ngược. Regenerate `schema.sql`, `generated_tables.py` | 0,6 | `dbmate up`/`down`/`up` sạch trên database dùng một lần; test phát lại migration khớp `schema.sql`; dữ liệu dev còn nguyên sau `up` | ☑ |
| CH-S11-BE-01 | Backend conversations | `TurnRepository`, `tree.py`, `context.py`, `service.py`, `connect.py`, `interactions.py`, `export.py`, `titles.py`, `router.py`, `schemas.py` theo mapping; mã lỗi mới; event `chat.turn` | 0,6 | Test conversations, pause/resume, connect, search, export xanh với tên mới | ☑ |
| CH-S11-BE-02 | Backend files, shares, ai, tools | `files` (link, `generated.py`), `shares` (snapshot, copy, remap), `ai/runtime/runner.py` (`ASSISTANT_EVENT`), `tools/loadtest.py` | 0,3 | Test files, generated files, shares, copy, roles xanh; `uv run loadtest` chạy | ☑ |
| CH-S11-FE-01 | Frontend | Regenerate kiểu OpenAPI; `ChatAgent` (đường dẫn, body), `conversations-api`, `use-conversation-chat`, `use-conversations`, `conversation-screen`, `chat-messages`, `branch-switcher`, `conversation-search`, trang `/c/{id}?t=`, `shares` (`shared-chat-screen`, `branch`); không đổi `components/ai-elements` | 0,5 | Vitest, `typecheck`, `eslint`, `build` xanh | ☑ |
| CH-S11-QA-01 | Kịch bản nghiệm thu | Chạy thật kịch bản 1–4 | 0,2 | Đạt | ☑ |
| CH-S11-DOC-02 | Cập nhật tài liệu | API contract (§2–§7), quyết định ID (thêm bảng từ ngữ turn / bundle / message AG-UI), client decisions, `van-hanh.md`; ghi chú QD-33 ở `database_decisions/README.md` | 0,2 | — | ☑ |

**Migration**: một file đổi tên (CH-S11-DB-01).

## Kịch bản nghiệm thu

1. **Người dùng** mở chat cũ tạo trước S11.
   - Lịch sử, nhánh, tệp đính kèm hiển thị như trước.
2. **Người dùng** gửi câu hỏi, sửa câu hỏi, chạy lại câu trả lời, dừng giữa chừng.
   - Network gọi `/turns…`; event `chat.turn` mang `userTurnId`, `assistantTurnId`; cây nhánh đúng.
3. **Người dùng** trả lời câu hỏi của AI (pause) trên một lượt đang chờ tạo trước S11.
   - Lượt resume được (checkpoint giữ `thread_id` cũ).
4. **Người dùng** tìm kiếm, mở kết quả `?t=`, chia sẻ chat, "Hỏi tiếp" trên bản copy, export zip.
   - Đều chạy; JSON export có `turns`.

## Rủi ro riêng

- Thân hàm PL/pgSQL lưu dạng chữ: đổi tên bảng mà sót một hàm thì lỗi chỉ lộ khi trigger chạy. Giảm thiểu: `grep` mọi tên cũ trong `schema.sql` sau `up` phải về 0 (trừ tên giữ nguyên có chủ đích); chạy toàn bộ test có trigger.
- Lẫn "message" của SQL và của AG-UI khi đổi tên trong code. Giảm thiểu: đổi theo mapping, không thay chữ hàng loạt; review diff theo từng file.
- Frontend cũ gọi route cũ sau khi backend lên bản mới. Giảm thiểu: triển khai backend và frontend cùng lúc; ghi trong `van-hanh.md`.
- Lượt đang chạy trong lúc migrate. Giảm thiểu: migrate khi không có lượt `running` (như mọi migration đổi trigger).

## Tổng kết

Kết thúc 02/11/2026 (sớm hơn lịch dự kiến 05/04 – 07/04/2027).

**Đã xong**: 7/7 task.
- Migration `20261102100000_rename_messages_to_turns.sql` đổi tên tại chỗ 4 bảng, 6 cột, constraint (kể cả NOT NULL tự đặt tên của PG18) và index bằng khối `DO`, 7 hàm, trigger `user_turn_final`, viết lại thân 16 hàm; `down` khôi phục đúng thân hàm cũ.
- Backend, API, frontend và tài liệu theo mapping. Thêm tên tránh trùng nghĩa: `MAX_ATTACHMENTS_PER_TURN` (tệp đính kèm của câu hỏi, khác `MAX_FILES_PER_TURN` của tệp agent tạo), `TurnState` (trạng thái của turn, khác `TurnStatus` kết quả lượt chạy của runner).
- Kèm theo: `TurnContext` đánh dấu hai trường hàm là `SkipJsonSchema` vì adapter AG-UI không sinh được JSON schema của context và mỗi lượt ghi cảnh báo `get_schema_keys` rồi dùng khoá mặc định (lộ ra từ TD-019).

**Kiểm tra** (QD-16, phần liên quan):
- Migration: up/down/up trên database dùng một lần; `pg_dump` sau `down` trùng hệt bản trước migration (chỉ khác token `\restrict`); `schema.sql` không còn chữ "message"; test phát lại migration khớp.
- Backend: `ruff`, `pyrefly` sạch; `pytest` 154 passed.
- Frontend: `pnpm test` 68 passed; `typecheck`, `eslint` sạch; `pnpm build` thành công.
- Database dev: migrate tại chỗ, 751 turn, 12 liên kết tệp, 132 chat còn nguyên.
- Kịch bản 1–4 chạy thật với model OpenRouter: chat cũ mở được; gửi, sửa, chạy lại, dừng qua `/turns…` với event `chat.turn`; `turn_not_found`; tìm kiếm trả `turn_id`, `?t=` mở đúng nhánh; share có `turns`, "Hỏi tiếp" tạo bản copy; export có `turns`. Giao diện gọi `POST /turns`, `GET /turns?from_turn_id=`, không lỗi console. Kịch bản 3 (resume lượt chờ tạo trước S11) không có dữ liệu thật để chạy; phần resume sau khởi động lại do test `test_question_pauses_then_resumes_after_a_restart` bao.

**Lỗi**: không.

**Thay đổi**: TD-021.

**Dời**: không.
