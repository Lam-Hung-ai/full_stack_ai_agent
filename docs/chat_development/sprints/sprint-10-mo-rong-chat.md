# Sprint 10: Mở rộng chat

| | |
| --- | --- |
| Thời gian | 22/03 – 02/04/2027 (dự kiến) |
| Nhánh | `chat` (QD-08) |
| Phụ thuộc | S2, S3 (conversation, sidebar), S7 (file), S8 (share, copy) |
| Ước lượng | 11 nc |
| Mốc | — |
| Use case | C01, C09, D06, O08 (phần export) |
| Câu hỏi phải chốt trước | Q-09 → Q-12, đã chốt (QD-31) |

## Mục tiêu

1. Chat mới có tên do model đặt theo câu hỏi đầu. Tên đổi tay luôn được giữ (C07).
2. Tìm chat của mình trong workspace theo tên hoặc nội dung, không phân biệt dấu (C09).
3. Agent tạo được tệp CSV, Markdown, TXT, XLSX. Tệp gắn vào câu trả lời, tải về được, và đi theo share và bản copy (D06).
4. Người dùng export được các chat của mình trong workspace thành một tệp zip (JSON + Markdown) (O08).

## Không làm

- **T03, tool gửi email:** dời sang sau. Cần tài khoản uỷ quyền (T06) và chính sách người nhận (QD-31).
- **O08, xoá tài khoản và purge:** dời sang sau. Cần chính sách retention; trigger hiện cấm xoá message.
- **D01, trạng thái xử lý tệp** (trích nội dung, quét virus, thử lại): cần worker nền. Ở lại mức Một phần.
- **T01, tài khoản và phạm vi uỷ quyền:** phụ thuộc OAuth (T06, Sau).
- **PDF:** không có trong tool tạo tệp. Export không kèm byte của tệp đính kèm, chỉ có tên, loại và cỡ (QD-31).

## Task

| Mã | Việc | Chi tiết | Nc | Nghiệm thu | Trạng thái |
| --- | --- | --- | --- | --- | --- |
| CH-S10-DOC-01 | Bắt đầu sprint | Ghi dòng `BẮT ĐẦU` ở dòng thời gian; rà rủi ro | 0,1 | Dòng thời gian có dòng bắt đầu | ☐ |
| CH-S10-BE-01 | Tên chat do model đặt | Khi gửi câu hỏi đầu, chạy song song một lời gọi model ngắn, tắt reasoning. Tên tối đa 60 ký tự. Cập nhật có điều kiện `title = <tên fallback>` nên tên đã đổi tay không bị ghi đè (C07). Lỗi model thì giữ tên fallback; model giả dùng được cho test và load test | 1,5 | Test: tên mới được đặt; đổi tay trước khi model trả thì tên tay được giữ; model lỗi thì giữ fallback | ☐ |
| CH-S10-DB-01 | Index tìm kiếm | Migration: `pg_trgm`, `unaccent`; hàm immutable lấy chữ của câu hỏi và câu trả lời từ `messages.content`, bỏ dấu; GIN trigram index trên hàm đó và trên `conversations.title` | 1 | `dbmate up`/`down`/`up` sạch; `EXPLAIN` dùng index | ☐ |
| CH-S10-BE-02 | API tìm kiếm | `GET /workspaces/{id}/conversations/search?q=` chỉ trên chat của mình, đã lọc xoá mềm và bản copy chưa xong. Trả chat khớp kèm đoạn trích quanh chỗ khớp và id message để mở đúng nhánh; phân trang; `q` từ 2 tới 200 ký tự | 1 | Test: khớp tên, khớp nội dung có/không dấu; không thấy chat người khác, chat đã xoá, bản copy dở | ☐ |
| CH-S10-FE-01 | Ô tìm kiếm ở sidebar | Ô tìm có debounce; kết quả có đoạn trích; bấm vào mở chat ở nhánh chứa message khớp (`?from_message_id=`) | 1 | Vitest cho hook và bộ dựng đoạn trích; chạy thật | ☐ |
| CH-S10-BE-03 | Tool tạo tệp | Tool `create_file(name, format, content)` cho CSV, MD, TXT, XLSX (`openpyxl`; bảng truyền dạng hàng). Ghi object vào key của workspace, ghi `stored_files` (`uploaded_by` là chủ chat) và gắn vào assistant đang chạy. Kết quả tool trả id, tên, loại, cỡ. Giới hạn cỡ và số tệp mỗi lượt; quyền tool `create_file` theo vai trò (S3, S6) | 2 | Test: tạo từng định dạng, tải về đúng byte; vượt giới hạn bị từ chối; không có quyền thì model không thấy tool | ☐ |
| CH-S10-BE-04 | Tệp của assistant trong share và copy | Snapshot giữ link tệp của assistant; copy đổi id tệp trong kết quả tool (hiện `remap_bundle` chỉ đổi phần của câu hỏi) | 0,5 | Test: share và copy chat có tệp do tool tạo; mở được tệp ở bản copy | ☐ |
| CH-S10-FE-02 | Hiện tệp do agent tạo | Thẻ tệp trong câu trả lời, dựng từ kết quả tool, tải qua link ký (dùng lại `MessageFiles`). Hiện cả trong trang xem share | 1 | Vitest; chạy thật: hỏi tạo bảng XLSX rồi tải về mở được | ☐ |
| CH-S10-BE-05 | Export chat | `GET /workspaces/{id}/export` stream tệp zip các chat của mình trong workspace: mỗi chat một JSON (cả cây message) và một Markdown (nhánh đã lưu). Tệp đính kèm chỉ có tên, loại, cỡ. Có rate limit; không giữ transaction trong lúc stream | 1,5 | Test: zip đúng cấu trúc, chỉ chứa chat của người gọi, không có chat đã xoá hoặc bản copy dở | ☐ |
| CH-S10-FE-03 | Nút export | Mục "Export chat" ở menu workspace, tải tệp zip | 0,3 | Chạy thật | ☐ |
| CH-S10-QA-01 | Kịch bản nghiệm thu | Chạy thật kịch bản 1–4 | 0,5 | Đạt | ☐ |
| CH-S10-DOC-02 | Cập nhật tài liệu | API §2 (search, export, tool tạo tệp), use case §6 (C01, C09, D06, O08), `van-hanh.md` (dependency `openpyxl`) | 0,5 | — | ☐ |

**Migration**: một file cho tìm kiếm (CH-S10-DB-01).

## Kịch bản nghiệm thu

1. **Người dùng** gửi câu hỏi đầu trong chat mới.
   - Sidebar đổi sang tên do model đặt sau khi lượt trả lời xong.
   - Đổi tên tay ngay khi gửi thì tên tay được giữ.
2. **Người dùng** gõ "ha noi" vào ô tìm kiếm.
   - Thấy các chat có "Hà Nội" trong tên hoặc nội dung, kèm đoạn trích.
   - Bấm vào thì mở đúng nhánh chứa đoạn khớp.
   - Không thấy chat của người khác.
3. **Người dùng** hỏi "Lập bảng chi phí tháng này dạng Excel".
   - Câu trả lời có thẻ tệp `.xlsx`, tải về mở được.
   - Chia sẻ chat thì người xem tải được tệp; "Hỏi tiếp" trên bản copy vẫn mở được tệp.
4. **Người dùng** chọn "Export chat".
   - Nhận tệp zip có JSON và Markdown của các chat của mình trong workspace, không có chat đã xoá.

## Rủi ro riêng

- Gọi model đặt tên làm tăng chi phí mỗi chat mới. Giảm thiểu: chỉ gọi ở câu hỏi đầu, prompt ngắn, tắt reasoning; ghi token vào log lượt.
- Index trigram trên nội dung làm ghi message chậm hơn và tốn dung lượng. Giảm thiểu: chỉ index phần chữ của câu hỏi và câu trả lời; đo lại bằng `uv run loadtest`.
- Model tạo tệp lớn hoặc chèn công thức độc hại vào XLSX/CSV (formula injection). Giảm thiểu: giới hạn cỡ; ô bắt đầu bằng `=`, `+`, `-`, `@` được ghi thành chữ.
- Export chat dài làm request lâu. Giảm thiểu: stream zip từng chat, đọc theo lô.

## Tổng kết

Điền ngày cuối sprint.

**Đã xong**: <x/y task>.

**Kiểm tra**: <lệnh đã chạy và kết quả>.

**Thay đổi**: <TD-xxx>.

**Dời**: <task và sprint nhận, hoặc "không">.
