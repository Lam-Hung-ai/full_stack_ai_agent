# Sprint 4: Pause và resume

| | |
| --- | --- |
| Thời gian | 28/12/2026 – 08/01/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S3 |
| Ước lượng | 8 nc |
| Mốc | M-C: Chat đầy đủ |
| Use case | T03 (phần duyệt cơ bản), T07 |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Agent dừng lại để hỏi người dùng hoặc xin duyệt tool; lượt chuyển `requires_action`, không giữ worker, slot hay connection khi chờ (database giai đoạn 4 §6, §7).
2. Checkpoint chỉ ghi xuống PostgreSQL khi có interrupt, cùng transaction với content, metadata và status của message (adapter đã kiểm chứng ở `docs/experiments/langgraph-action-checkpoints`).
3. Resume bằng `ResumeEntry[]` theo API §5: đối chiếu interrupt đang chờ, kiểm quyền tool trước khi claim, claim nguyên tử, chạy tiếp cùng assistant ID kể cả sau khi process khởi động lại.
4. Activity `user_interaction` trong content ghi câu hỏi/duyệt và câu trả lời có `actor_id`; stop huỷ lượt đang chờ.
5. Frontend hiện câu hỏi và thẻ duyệt tool, gửi trả lời, hiển thị lịch sử trả lời.

## Không làm

- Duyệt bởi người khác chủ chat (T04), binding tài khoản gửi email, receipt/reconcile tool bên ngoài (T02, T05).
- Migration checkpoint khi đổi graph; chỉ kiểm `graph_version` khớp (RR-07).
- Dọn checkpoint sau khi lượt kết thúc (chưa có chính sách retention).
- Reconnect vào lượt đang chạy (S5).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S4-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S3 | 0,1 | — | ☑ |
| CH-S4-BE-01 | Saver chỉ export khi interrupt | `modules/agent/checkpoints.py`: saver RAM theo lượt, nạp checkpoint đã lưu trước khi chạy, export checkpoint + mọi pending writes qua `AsyncPostgresSaver` trên connection của transaction | 1,5 | Test: chat thường 0 dòng checkpoint; pause có checkpoint; rollback cùng message | ☑ |
| CH-S4-BE-02 | Interrupt trong agent | Tool `ask_user` (hỏi người dùng); duyệt tool theo cấu hình trong middleware quyền tool; `graph_version` | 1 | Test với model giả | ☑ |
| CH-S4-BE-03 | Pause | Runner nhận biết interrupt, lưu `requires_action` + `pending_action` + activity `waiting`, phát `RUN_FINISHED` có `outcome: interrupt` sau commit | 1,5 | Test: content, metadata, event | ☑ |
| CH-S4-BE-04 | Resume | `POST …/messages/{assistant_id}/resume` body `{resume: ResumeEntry[]}`; đối chiếu interrupt, validate payload, kiểm quyền tool, claim, chạy tiếp từ checkpoint; mapping public C1/native A1 (RR-06) | 1,5 | Test: trả lời sau khi dựng lại runner; hai lần hỏi; từ chối tool; thu hồi quyền khi chờ; hai request đồng thời | ☑ |
| CH-S4-BE-05 | Stop lượt chờ | Huỷ `requires_action`: activity `cancelled`, bỏ `pending_action`, giữ content | 0,25 | Test | ☑ |
| CH-S4-FE-01 | Hỏi và duyệt trên UI | Renderer activity `user_interaction`; form trả lời; thẻ duyệt tool; `ChatAgent.resume`; khoá ô chat khi đang chờ | 1,75 | Chạy thật bằng trình duyệt | ☑ L-09 |
| CH-S4-DOC-02 | Cập nhật tài liệu | API §5, payload activity, cấu hình duyệt tool | 0,4 | — | ☑ TD-010 |

**Migration**: không (schema giai đoạn 4 đã có `metadata`, `requires_action`; bảng saver tạo bằng `uv run db checkpoints`).

## Kịch bản nghiệm thu

1. **Người dùng** hỏi câu mơ hồ ("Đặt giúp tôi một phòng họp").
   - Agent hỏi lại; ô trả lời hiện dưới câu hỏi; ô chat chính bị khoá.
2. **Người dùng** tải lại trang khi đang chờ, rồi khởi động lại backend.
   - Câu hỏi vẫn hiện; trả lời xong agent chạy tiếp trong cùng câu trả lời.
3. **Người dùng** hỏi giờ khi tool `get_current_time` cần duyệt (cấu hình dev).
   - Thẻ duyệt hiện tên tool và tham số; bấm "Cho phép" thì tool chạy; bấm "Từ chối" thì agent giải thích.
4. **Người dùng** bấm dừng khi agent đang chờ.
   - Lượt chuyển "Đã dừng", hỏi tiếp được.

## Rủi ro riêng

- Node chứa interrupt chạy lại từ đầu khi resume (RR-08): `ask_user` và bước duyệt không có tác dụng phụ trước interrupt; tool chỉ chạy sau khi được duyệt.
- Đổi graph khi còn lượt chờ (RR-07): `graph_version` khác thì từ chối resume, người dùng dừng lượt.

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 28/12/2026 – 08/01/2027).

**Đã xong**: 8/8 task.
- Backend: saver RAM theo lượt chỉ export khi có interrupt (`agent/checkpoints.py`, chuyển từ proof); graph biên dịch không checkpointer, mỗi lượt chạy bản copy với `TurnAgent` (durability `exit`, outcome interrupt); tool `ask_user` và bước duyệt trong middleware quyền tool; runner nhận biết interrupt, finalizer lưu checkpoint + content + `pending_action` + activity `waiting` trong một transaction rồi mới phát event; `POST …/resume` kiểm đủ điều kiện trước khi claim, nạp checkpoint từ DB, chạy tiếp cùng assistant; stop huỷ lượt đang chờ (QD-22).
- Frontend: `ChatAgent.resume`; thẻ câu hỏi (RHF + Zod) và thẻ duyệt tool xen đúng chỗ trong câu trả lời; khoá ô chat, nút sửa/tạo lại khi đang chờ; lượt resume hiển thị tiếp trên chính dòng đang chờ.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 77 passed (pause/resume 9: hỏi rồi trả lời sau khi dựng lại runner, chat thường 0 checkpoint, hai câu hỏi một lượt, kiểm tra trước claim, hai request đồng thời, duyệt và từ chối tool, thu hồi quyền khi chờ, stop lượt chờ, lưu lỗi thì checkpoint rollback; unit interactions 2).
- Frontend: `pnpm test` 41 passed; `typecheck`, `eslint` thư mục đã đổi sạch; `pnpm build` thành công.
- Chạy thật với model OpenRouter qua trình duyệt, `TOOLS_REQUIRING_APPROVAL=["get_current_time"]`: kịch bản 1–4 đạt (agent hỏi lại; tải lại trang và khởi động lại backend rồi trả lời, agent chạy tiếp cùng câu trả lời; cho phép và từ chối tool; dừng khi đang chờ rồi hỏi tiếp).

**Lỗi**: L-09 đã sửa.

**Thay đổi**: TD-010; QD-22; RR-16; RR-06 đã xử lý; cập nhật RR-07, RR-08.

**Dời**: không.
