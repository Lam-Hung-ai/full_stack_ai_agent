# Sprint 9: Vận hành và hoàn thiện

| | |
| --- | --- |
| Thời gian | 08/03 – 19/03/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S4, S5, S8 |
| Ước lượng | 6 nc |
| Mốc | M-E: Hoàn thiện |
| Use case | Rà toàn bộ |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Mỗi lượt ghi một dòng log JSON có ngữ cảnh (assistant, conversation, workspace, user, trạng thái, thời lượng, token theo model); không ghi nội dung chat.
2. Langfuse nhận trace và token/chi phí của từng lượt khi được cấu hình; không cấu hình thì không đổi gì.
3. Backpressure: hàng đợi lượt có trần; vượt trần trả 503 `server_busy` kèm `Retry-After` thay vì treo.
4. Rate limit dùng Redis khi chạy nhiều process (thay bộ đếm trong bộ nhớ).
5. Dọn checkpoint của lượt đã pause khi lượt kết thúc (RR-16).
6. Stream không bị proxy gom (RR-13): header cho SSE, cấu hình proxy mẫu.
7. Load test có kịch bản lặp lại được, với model giả để đo API, stream, runner, PostgreSQL, Redis mà không tốn tiền model.
8. Rà soát toàn bộ, chấm lại use case, cập nhật tài liệu.

## Không làm

- Worker nền riêng cho lượt chat và copy job (RR-10, RR-18): load test cho thấy runner trong process đủ cho ngưỡng đo; xét lại khi có số liệu production.
- Dọn tệp không gắn (RR-17), purge snapshot/job dở: cần chính sách retention (database giai đoạn 1 §10).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S9-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S8 | 0,1 | — | ☑ |
| CH-S9-BE-01 | Log lượt | Log JSON nhận trường ngữ cảnh; runner ghi một dòng khi lượt kết thúc, gồm token từ `RUN_FINISHED.usage` | 0,5 | Test | ☑ |
| CH-S9-BE-02 | Langfuse | Callback LangChain khi có `LANGFUSE_*`; trace gắn assistant/conversation/user | 0,75 | Test bật/tắt | ☑ |
| CH-S9-BE-03 | Backpressure | `MAX_QUEUED_TURNS`; 503 `server_busy` + `Retry-After` | 0,5 | Test | ☑ |
| CH-S9-BE-04 | Rate limit qua Redis | Cửa sổ cố định theo IP, dùng chung giữa process | 0,5 | Test với fakeredis | ☑ |
| CH-S9-BE-05 | Dọn checkpoint | Lượt đã pause kết thúc (trả lời xong, dừng, huỷ) thì xoá thread checkpoint trong cùng transaction | 0,5 | Test | ☑ RR-16 |
| CH-S9-BE-06 | SSE qua proxy | `X-Accel-Buffering: no`, `Cache-Control: no-cache`; mẫu nginx | 0,25 | Test header | ☑ RR-13 |
| CH-S9-QA-01 | Load test | `uv run loadtest`: N người dùng đồng thời gửi, stream, connect; model giả qua `AGENT_FAKE_MODEL` | 1,5 | Báo cáo số liệu | ☑ |
| CH-S9-DOC-02 | Rà soát, chấm lại use case | Use case, rủi ro, tài liệu vận hành | 1 | — | ☑ TD-015 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Vận hành** xem log của một lượt.
   - Một dòng JSON có `assistant_id`, `status`, `duration_ms`, token; không có nội dung câu hỏi.
2. **Nhiều người dùng** gửi cùng lúc vượt sức chứa.
   - Lượt vượt trần nhận 503 có `Retry-After`; lượt đã nhận vẫn chạy hết.
3. **Load test** chạy theo ngưỡng thống nhất.
   - Có số liệu độ trễ (p50/p95) cho gửi tới token đầu, connect, và lỗi bằng 0 dưới trần.

## Rủi ro riêng

- Số liệu load test với model giả không phản ánh độ trễ nhà cung cấp; dùng để đo phần của hệ thống.

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 08/03 – 19/03/2027).

**Đã xong**: 9/9 task.
- Backend: log JSON nhận trường ngữ cảnh, mỗi lượt một dòng kèm token; Langfuse qua callback khi có khoá; trần hàng đợi lượt với 503 `server_busy` + `Retry-After`; rate limit qua Redis có dự phòng bộ nhớ; xoá checkpoint khi lượt đã pause kết thúc; model giả và `uv run loadtest`.
- Frontend: thông báo cho `server_busy` và lỗi tệp.
- Tài liệu: `van-hanh.md` (dịch vụ, lệnh triển khai, nginx cho SSE, sức chứa, log/trace, load test); chấm lại 32 use case (§6: 13 Đạt, 7 Một phần, 12 Sau).

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 126 passed (mới: log lượt, backpressure, rate limit qua Redis, Langfuse bật/tắt; checkpoint bị xoá sau khi trả lời và sau khi dừng).
- Frontend: `pnpm test` 59 passed; `typecheck`, `eslint` (code dự án) sạch; `pnpm build` thành công.
- Load test (một process, 10 slot, model giả): 10 người × 5 lượt 50/50, token đầu p95 328 ms; 30 người × 3 lượt 90/90 không lỗi; 60 người × 1 lượt: 33 lượt chạy hết, 27 lượt nhận 503 `server_busy` ngay (`van-hanh.md` §6). Kịch bản 1–3 đạt.

**Lỗi**: không.

**Thay đổi**: TD-015; QD-29; RR-13, RR-16 đã xử lý; cập nhật RR-10.

**Dời**: worker nền cho lượt và copy (RR-10, RR-18), dọn tệp không gắn và purge (RR-17, database giai đoạn 1 §10): chưa có sprint, cần chính sách retention và số liệu production.

**Môi trường**: load test đã tạo các tài khoản `load-*@example.com` trong database dev.
