# Sprint 5: Redis live và connect

| | |
| --- | --- |
| Thời gian | 11/01 – 22/01/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S3 |
| Ước lượng | 7 nc |
| Mốc | M-C: Chat đầy đủ |
| Use case | C03 |
| Câu hỏi phải chốt trước | Q-08: đã chốt (QD-23, một SSE mỗi tab) |

## Mục tiêu

1. Lượt đang chạy có bản live trong Redis: stream event giới hạn kích thước và view (bundle + watermark) (kiến trúc §5, lưu trữ §9).
2. `POST /conversations/{id}/connect` không body, không cursor: snapshot mới nhất rồi theo tiếp lượt đang chạy; không gọi model (API §6).
3. Stop tới đúng process đang chạy lượt qua Redis; lượt không còn process nào sở hữu thì huỷ tại chỗ.
4. Frontend `attach`: mở lại hoặc quay lại chat đang chạy thì thấy phần đang sinh và theo tiếp; chuyển chat thì ngắt stream (QD-23).

## Không làm

- Chạy nhiều process backend trong production (vẫn một process tới khi có load test, S9); S5 chỉ bảo đảm connect/stop không phụ thuộc process nhận request.
- Khôi phục lượt khi process chết (RR-01).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S5-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S4; QD-23 | 0,1 | — | ☑ |
| CH-S5-BE-01 | Live store | `modules/agent/live.py`: Redis Stream `chat:{assistant}:events` (MAXLEN), view tại điểm an toàn (không span mở), khoá sở hữu có heartbeat, kênh dừng; `REDIS_URL` | 1,5 | Test với fakeredis | ☑ |
| CH-S5-BE-02 | Runner ghi live | Mỗi event vào stream; view sau mỗi điểm an toàn; hết lượt rút TTL; lỗi Redis không làm hỏng lượt | 1 | Test | ☑ |
| CH-S5-BE-03 | Connect | Không active: snapshot nhánh hiện hành rồi đóng. Đang chạy: snapshot (nhánh + view) rồi tail sau watermark tới event kết thúc. Chờ người dùng: snapshot rồi đóng. Mất dữ liệu live hoặc tail bị cắt: snapshot đã lưu rồi đóng, không nối thiếu | 1,5 | Test: connect giữa lượt nhận đủ nội dung một lần | ☑ |
| CH-S5-BE-04 | Stop qua Redis | Không có task cục bộ mà còn chủ sở hữu thì phát tín hiệu, chờ trạng thái đổi; không còn chủ thì huỷ tại chỗ | 0,75 | Test hai runner | ☑ |
| CH-S5-FE-01 | Attach | `ChatAgent.attach()`; mở chat có lượt đang chạy thì connect, vẽ tiếp trên dòng đang chạy; mất live thì quay về poll | 1,5 | Chạy thật: đóng tab mở lại thấy tiếp | ☑ |
| CH-S5-DOC-02 | Cập nhật tài liệu | API §6, kiến trúc §5, biến môi trường | 0,25 | — | ☑ TD-011 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Người dùng** gửi câu hỏi dài, tải lại trang giữa chừng.
   - Thấy phần đã sinh ngay, chữ chạy tiếp tới hết, không lặp đoạn đầu.
2. **Người dùng** chuyển sang chat khác rồi quay lại khi lượt còn chạy.
   - Như trên; khi ở chat khác không có stream của chat cũ.
3. **Người dùng** mở chat đang chạy ở tab thứ hai và bấm dừng ở đó.
   - Cả hai tab thấy "Đã dừng".

## Rủi ro riêng

- Dữ liệu live mất (Redis khởi động lại) khi lượt đang chạy: connect trả snapshot đã lưu, frontend poll tới khi lượt lưu xong (RR-02).

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 11/01 – 22/01/2027).

**Đã xong**: 7/7 task.
- Backend: `modules/agent/live.py` (Redis Stream giới hạn độ dài, view ở điểm an toàn kèm watermark và số thứ tự, khoá sở hữu có heartbeat, kênh `chat:stop`); runner ghi mọi event qua `_Channel`, lỗi Redis chỉ làm mất live view; `POST /connect` (`conversations/connect.py`): snapshot nhánh + view rồi tail tới hết lượt, mất live hoặc có khoảng trống thì chỉ gửi snapshot; stop ở process khác đi qua Redis và chờ DB.
- Frontend: `ChatAgent.attach()`; hook tự connect khi chat mở ra có lượt đang chạy (một lần cho mỗi dòng), vẽ tiếp trên dòng đó; rời chat thì ngắt stream (QD-23); poll còn là đường dự phòng.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 84 passed (connect 6: không có lượt chạy, giữa lượt thấy đủ nội dung đúng một lần, sau bước tool bắt đầu từ điểm an toàn, đang chờ người dùng, mất dữ liệu live, stop từ process khác; unit live 1).
- Frontend: `pnpm test` 42 passed; `typecheck`, `eslint` sạch; `pnpm build` thành công.
- Chạy thật với Redis container và model OpenRouter: kịch bản 1–3 đạt (tải lại giữa chừng thấy phần đã sinh rồi chạy tiếp không lặp; chuyển chat trong app rồi quay lại thì connect lại; dừng ở tab thứ hai, cả hai tab thấy "Đã dừng").

**Lỗi**: không.

**Thay đổi**: TD-011; QD-23 (Q-08); RR-14 đã xử lý; cập nhật RR-02, RR-10.

**Dời**: không.
