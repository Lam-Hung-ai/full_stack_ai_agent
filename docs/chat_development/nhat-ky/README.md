# Nhật ký dự án phát triển chat

Nhật ký **dùng chung cho mọi sprint** của dự án phát triển chat ([kế hoạch](../ke-hoach-sprint.md)).

- File này giữ **dòng thời gian**: mỗi sự kiện của dự án ghi một dòng, trỏ tới chi tiết.
- Chi tiết nằm ở các file chuyên đề dưới đây.

| File | Ghi gì | Mã | Ai ghi |
| --- | --- | --- | --- |
| [thay-doi.md](./thay-doi.md) | Thay đổi phạm vi, thiết kế, API, schema, ID/event contract, lịch | `TD-xxx` | Người làm task gây ra thay đổi |
| [loi.md](./loi.md) | Lỗi: phát hiện khi rà soát, khi làm, khi kiểm thử, sau phát hành | `L-xx` | Người phát hiện |
| [quyet-dinh.md](./quyet-dinh.md) | Quyết định kiến trúc và sản phẩm (ADR rút gọn), câu hỏi chờ chốt | `QD-xx`, `Q-xx` | Người đề xuất; trạng thái "Chốt" chỉ khi người dùng (PO) đồng ý |
| [rui-ro.md](./rui-ro.md) | Rủi ro, nợ kỹ thuật đang theo dõi | `RR-xx` | Bất kỳ ai |

**Quan hệ với tài liệu thiết kế**
- Quyết định chi tiết vẫn nằm ở tài liệu thiết kế (`database-decisions.md`, `chat-agent-api-contract.md`, `conversation-message-run-id-decisions.md`…). Nhật ký chỉ ghi mã, tóm tắt và trỏ tới đó, không chép lại nội dung.
- Mã use case `C0x`, `D0x`, `T0x`, `O0x` ở [chat-use-cases-and-organization-access.md](../chat-use-cases-and-organization-access.md) là mã **của tài liệu use case**. Nhật ký trỏ tới chúng, không đánh số lại.

## Luật ghi

1. **Ghi khi phát sinh**, không dồn tới cuối sprint. Một dòng ở dòng thời gian, chi tiết ở file chuyên đề.
2. **Mỗi mục có**: ngày (dd/mm/yyyy), sprint, mã task (`CH-S<n>-<lớp>-<số>`), và commit hoặc MR nếu có.
3. **Chỉ thêm, không sửa lịch sử.**
   - Được cập nhật cột *Trạng thái* của lỗi, rủi ro và quyết định.
   - Nội dung đã ghi sai thì thêm mục mới, ghi "thay cho …".
4. **Mã tăng dần**, không dùng lại mã đã xoá: `TD-001`, `L-01`, `QD-01`, `Q-01`, `RR-01`.
5. **Liên kết hai chiều.** Task trong file sprint ghi mã nhật ký; mục nhật ký ghi mã task.
6. **Thay đổi làm lệch tài liệu thiết kế** trong `docs/chat_development/` hoặc `docs/database_decisions/` thì sửa luôn file đó trong cùng thay đổi và ghi `TD` kèm tên file đã sửa.
7. **Không ghi** mật khẩu, token, API key, nội dung chat thật của người dùng hay dữ liệu cá nhân. Cần ví dụ thì dùng dữ liệu demo.
8. **Câu hỏi `Q-xx` chặn sprint** phải được chốt trước ngày đầu sprint đó. Chưa chốt thì ghi `THAY ĐỔI` (dời task) ở dòng thời gian.

## Mức độ dùng chung

| Mức | Lỗi | Rủi ro |
| --- | --- | --- |
| **Nghiêm trọng** | Lộ chat riêng hoặc file cho người không có quyền, lẫn dữ liệu giữa workspace; chạy tool không có quyền; mất dữ liệu đã commit | Có thể chặn phát hành |
| **Cao** | Hai execution cùng chạy một assistant; mất partial đáng lẽ đã lưu ở terminal/pause; trạng thái message sai làm kẹt conversation; resume nhầm checkpoint | Có thể trễ sprint |
| **Trung bình** | Reconnect thiếu hoặc lặp nội dung; UI báo sai trạng thái (pending/running/requires_action/terminal); hiển thị chéo conversation | Cần theo dõi |
| **Thấp** | Hiển thị, chữ, tài liệu, bất nhất tên | Ghi nhận |

## Dòng thời gian

Định dạng: `dd/mm/yyyy | Sprint | Loại | Mã | Tóm tắt | Mã task / MR`.

Loại: `BẮT ĐẦU`, `KẾT THÚC`, `LỖI`, `SỬA`, `THAY ĐỔI`, `QUYẾT ĐỊNH`, `CÂU HỎI`, `RỦI RO`, `PHÁT HÀNH`.

| Ngày | Sprint | Loại | Mã | Tóm tắt | Task / MR |
| --- | --- | --- | --- | --- | --- |
| 29/10/2026 | — | QUYẾT ĐỊNH | QD-01 → QD-07 | Ghi nhận các quyết định đã chốt trong tài liệu thiết kế (database 1–4, ID, API, ChatAgent, không CopilotKit, bỏ dedup, checkpoint chỉ khi pause) | — |
| 29/10/2026 | — | LỖI | L-01 | Use case C04 ghi stop theo `messageId + runId`, trái quyết định ID | — |
| 29/10/2026 | — | SỬA | L-01, TD-001 | Bỏ `runId`/dedupe khỏi tài liệu use case | — |
| 29/10/2026 | — | THAY ĐỔI | TD-002 | Tạo `nhat-ky/`, `ke-hoach-sprint.md`, `sprints/` (mẫu) | — |
| 29/10/2026 | — | CÂU HỎI | Q-01 → Q-08 | Câu hỏi cần chốt trước khi bắt đầu code theo sprint | — |
| 29/10/2026 | — | RỦI RO | RR-01 → RR-09 | Rủi ro và giới hạn đã biết từ tài liệu thiết kế, cùng độ lệch AGENTS.md với code hiện tại | — |
| 29/10/2026 | — | QUYẾT ĐỊNH | QD-08 → QD-13, TD-004 | Người dùng đồng ý đề xuất Q-01, Q-02, Q-03, Q-04, Q-05, Q-07; auth theo mẫu hr-ai | — |
| 29/10/2026 | — | THAY ĐỔI | TD-003 | Rà phân bổ sprint: thêm S6 tổ chức và quyền, S2 thành lát dọc, quyền tool vào S3, vận hành vào S9; lịch dự kiến 02/11/2026 – 19/03/2027 | — |
| 29/10/2026 | — | CÂU HỎI | Q-06 | Đề xuất runner trong process cho S2, chờ người dùng chốt | — |
| 29/10/2026 | — | RỦI RO | RR-10, RR-11 | Runner trong process; access token hết hạn với stream | — |
| 29/10/2026 | — | QUYẾT ĐỊNH | QD-14, TD-005 | File S3 theo mẫu storage của hr-ai | — |
| 29/10/2026 | — | QUYẾT ĐỊNH | QD-15, QD-16 | Người dùng chốt runner trong process (Q-06); uỷ quyền quyết định nhỏ, tự commit mỗi sprint, chỉ test phần liên quan | — |
