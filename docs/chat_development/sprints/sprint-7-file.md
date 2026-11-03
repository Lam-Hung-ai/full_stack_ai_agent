# Sprint 7: File

| | |
| --- | --- |
| Thời gian | 08/02 – 19/02/2027 (dự kiến) |
| Nhánh | `chat` (QD-08, QD-16) |
| Phụ thuộc | S2 |
| Ước lượng | 5 nc |
| Mốc | — |
| Use case | D01 (D06 phần tải lại) |
| Câu hỏi phải chốt trước | Không |

## Mục tiêu

1. Người dùng đính kèm ảnh, PDF, tệp văn bản vào câu hỏi; byte đi thẳng từ trình duyệt lên storage qua presigned PUT, backend xác minh rồi mới ghi `stored_files` (backend AGENTS §17.6, QD-14).
2. Model nhận nội dung tệp mỗi lượt (ảnh, PDF, chữ); câu hỏi chỉ lưu tham chiếu tệp, không lưu byte hay URL ký.
3. Tải lại tệp qua URL ký ngắn hạn sau khi kiểm quyền chat.
4. RustFS chạy được ở dev; một lệnh dựng bucket, CORS, luật dọn object tạm.

## Không làm

- Tool tạo tệp cho agent (D06 phần tạo): chưa có tool nào sinh tệp.
- Trích xuất, quét virus, trạng thái xử lý tệp (D01 phần "đã xử lý được chưa"): schema không có, để sau.
- Copy tệp khi share/copy chat (S8).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S7-DOC-01 | Bắt đầu sprint | Dòng `BẮT ĐẦU`, `PHÁT HÀNH` của S6; không có Q chặn | 0,1 | — | ☑ |
| CH-S7-BE-01 | Storage chung | `common/storage`: adapter boto3 của hr-ai, nhận dạng loại tệp theo byte đầu; `STORAGE_*`; `uv run storage setup`; RustFS trong compose | 1 | Unit test nhận dạng tệp | ☑ |
| CH-S7-BE-02 | Upload | Module `files`: xin URL, `complete` (HEAD, so cỡ, byte đầu, SHA-256, copy sang key cuối, ghi `stored_files`), dọn object tạm | 1 | Test với storage giả | ☑ QD-27 |
| CH-S7-BE-03 | Gắn tệp vào câu hỏi | `file_ids` khi gửi/sửa: kiểm chủ và workspace, ghi user pending → `message_files` → completed; content là media part AG-UI | 0,75 | Test API | ☑ |
| CH-S7-BE-04 | Model đọc tệp | Hook `prepare` của runner: ảnh/PDF thành nguồn data, văn bản thành chữ; cả khi tạo lại câu trả lời | 0,5 | Test: prompt của model chứa ảnh và chữ | ☑ |
| CH-S7-BE-05 | Tải tệp | `GET /conversations/{id}/files/{fileId}`: chủ chat và tệp gắn trong chat; URL ký trong body | 0,25 | Test API | ☑ |
| CH-S7-FE-01 | Đính kèm | Nút đính kèm trong composer, tải lên ngay khi chọn, chip trạng thái/lỗi, không gửi khi đang tải; `lib/storage/upload.ts` | 0,75 | Vitest + chạy thật | ☑ |
| CH-S7-FE-02 | Hiển thị tệp | Ảnh trong câu hỏi qua URL ký, tệp khác là nút mở; sửa câu hỏi giữ tệp | 0,4 | Vitest + chạy thật | ☑ |
| CH-S7-DOC-02 | Cập nhật tài liệu | API §2, §3; biến môi trường | 0,25 | — | ☑ TD-013 |

**Migration**: không.

## Kịch bản nghiệm thu

1. **Người dùng** đính kèm một ảnh và một tệp ghi chú, hỏi về cả hai.
   - Hai tệp tải lên xong (chip hết xoay); câu trả lời nói đúng màu ảnh và nội dung ghi chú.
2. **Người dùng** mở lại chat.
   - Ảnh hiện trong câu hỏi, tệp ghi chú là nút tải về.
3. **Người dùng** chọn một tệp `.exe` đổi tên thành `.png`.
   - Chip báo lỗi nội dung không đúng loại; câu hỏi đã gõ vẫn còn.

## Rủi ro riêng

- Model đang cấu hình không nhận ảnh: lượt có ảnh báo lỗi. Giảm thiểu: chọn model có hỗ trợ ảnh khi bật đính kèm ảnh.
- Tệp tải lên nhưng không gửi còn lại trong storage (RR-17).

## Tổng kết

Kết thúc 30/10/2026 (sớm hơn lịch dự kiến 08/02 – 19/02/2027).

**Đã xong**: 9/9 task.
- Backend: `common/storage` (adapter boto3 của hr-ai, nhận dạng loại tệp theo byte đầu), module `files` (xin URL, `complete` có xác minh rồi mới ghi `stored_files`, tải qua URL ký), `file_ids` khi gửi/sửa câu hỏi với user message staged pending → `message_files` → completed, hook `prepare` của runner đưa byte tệp cho model (cả khi tạo lại câu trả lời), `uv run storage setup`, RustFS trong compose.
- Frontend: đính kèm trong composer (tải lên ngay khi chọn, chip trạng thái và lỗi, khoá gửi khi đang tải), ảnh trong câu hỏi qua URL ký, tệp khác là nút mở, sửa câu hỏi giữ tệp; `lib/storage/upload.ts` lấy từ hr-ai.

**Kiểm tra** (QD-16, phần liên quan):
- Backend: `ruff`, `pyrefly` sạch; `pytest` 116 passed (mới: tệp 7 gồm upload hợp lệ, tệp xấu bị từ chối không để lại gì, câu hỏi có tệp tới model, chỉ gắn tệp của mình trong cùng workspace, quyền tải, tạo lại, sửa câu hỏi; unit nhận dạng tệp 3).
- Frontend: `pnpm test` 57 passed; `typecheck`, `eslint` (code dự án) sạch; `pnpm build` thành công.
- Chạy thật với RustFS: kịch bản 1–3 đạt. Kịch bản 1 chạy với model có hỗ trợ ảnh (`nvidia/nemotron-3.5-super-vl:free`, chạy tạm ở cổng 8001): "Hình ảnh màu đỏ và mã dự án trong ghi chú là KIWI-42". Model trong `.env` hiện tại (`nvidia/nemotron-3.5-lightning:free`) không nhận ảnh nên lượt có ảnh báo lỗi, đúng hành vi.

**Lỗi**: không.

**Thay đổi**: TD-013; QD-27; RR-17 (mới).

**Dời**: tool tạo tệp cho agent (D06 phần tạo) và pipeline xử lý tệp (D01 phần trạng thái) chưa có sprint; ghi ở use case.

**Môi trường**: cấu hình `STORAGE_*`, chạy `uv run storage setup`; model cần hỗ trợ ảnh nếu muốn đính kèm ảnh.
