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
| 29/10/2026 | S0 | BẮT ĐẦU | — | Bắt đầu Sprint 0 trên nhánh `chat` | CH-S0-DOC-01 |
| 29/10/2026 | S0 | QUYẾT ĐỊNH | QD-17 | psycopg 3 cho cả SQLAlchemy và saver | CH-S0-BE-02 |
| 29/10/2026 | S0 | THAY ĐỔI | TD-006 | PostgreSQL dev bằng compose; chi tiết baseline và công cụ database | CH-S0-DB-01, BE-03 |
| 29/10/2026 | S0 | RỦI RO | RR-12 | Lỗi lint có sẵn trong component vendor | CH-S0-FE-01 |
| 29/10/2026 | S0 | KẾT THÚC | — | Xong 9/9 task; backend 8 test, frontend 14 test xanh | — |
| 29/10/2026 | S0 | PHÁT HÀNH | — | Commit Sprint 0 trên `chat` | `d8a6fc4` |
| 29/10/2026 | S1 | BẮT ĐẦU | — | Bắt đầu Sprint 1 | CH-S1-DOC-01 |
| 29/10/2026 | S1 | THAY ĐỔI | TD-007 | Route auth, users, workspaces; rewrite `/api/v1` qua Next | CH-S1-BE-02, FE-01 |
| 29/10/2026 | S1 | LỖI | L-02, L-03 | Phiên bị thu hồi ngay sau đăng nhập; id trùng giữa hai form | CH-S1-FE-02 |
| 29/10/2026 | S1 | QUYẾT ĐỊNH | QD-18 | Ân hạn 10 giây cho token refresh vừa xoay | CH-S1-BE-02 |
| 29/10/2026 | S1 | SỬA | L-02, L-03 | Bỏ abort signal khi xoay token, xóa thay vì reset query session; `useId` cho form | CH-S1-FE-02 |
| 29/10/2026 | S1 | KẾT THÚC | — | Xong 9/9 task; backend 28 test, frontend 29 test xanh; 5 kịch bản chạy thật đạt | — |
| 29/10/2026 | S1 | PHÁT HÀNH | — | Commit Sprint 1 trên `chat` | `69ea9aa` |
| 29/10/2026 | S2 | BẮT ĐẦU | — | Bắt đầu Sprint 2 | CH-S2-DOC-01 |
| 29/10/2026 | S2 | LỖI | L-04 | Baseline mất danh mục permission | CH-S2-BE-01 |
| 30/10/2026 | S2 | LỖI | L-05, L-06 | SSE bị gom qua proxy Next; reasoning cũ mở bung khi tải lại | CH-S2-FE-02 |
| 30/10/2026 | S2 | SỬA | L-04, L-05, L-06 | Danh mục permission trong code + `iam sync-permissions`; Next tắt compress; reasoning lịch sử đóng sẵn | CH-S2-BE-01, FE-02 |
| 30/10/2026 | S2 | QUYẾT ĐỊNH | QD-19 | Wire API chat: đường dẫn theo workspace, DTO snake_case, event `chat.assistant` | CH-S2-BE-04 |
| 30/10/2026 | S2 | THAY ĐỔI | TD-008 | Route conversation; gỡ `/agent`; tài liệu API cập nhật | CH-S2-BE-02 → BE-05 |
| 30/10/2026 | S2 | RỦI RO | RR-13, RR-14 | Proxy production buffer SSE; mở lại lượt đang chạy chỉ poll | — |
| 30/10/2026 | S2 | KẾT THÚC | — | Xong 9/9 task; backend 47 test, frontend 35 test xanh; 5 kịch bản chạy thật đạt | — |
| 30/10/2026 | S2 | PHÁT HÀNH | — | Commit Sprint 2 trên `chat` | `dc6ad48` |
| 30/10/2026 | S3 | BẮT ĐẦU | — | Bắt đầu Sprint 3 | CH-S3-DOC-01 |
| 30/10/2026 | S3 | LỖI | L-07, L-08 | Lượt chat treo khi dựng agent lỗi; stop làm UI báo mất kết nối | CH-S3-BE-05, BE-03 |
| 30/10/2026 | S3 | SỬA | L-07, L-08 | Dựng agent trong `try`, tập tool là `frozenset`; đóng span đang mở trước `RUN_FINISHED` | CH-S3-BE-03, BE-05 |
| 30/10/2026 | S3 | QUYẾT ĐỊNH | QD-20, QD-21 | Nhánh/stop/folder; registry và kiểm quyền tool | CH-S3-BE-01 → BE-05 |
| 30/10/2026 | S3 | THAY ĐỔI | TD-009 | Route edit/regenerate/stop, folder, bộ lọc sidebar, permission `tool.*`; tài liệu API cập nhật | CH-S3-BE-01 → FE-02, DOC-02 |
| 30/10/2026 | S3 | RỦI RO | RR-15 | Role tổ chức cũ không tự có grant tool mới | CH-S3-BE-05 |
| 30/10/2026 | S3 | KẾT THÚC | — | Xong 9/9 task; backend 66 test, frontend 38 test xanh; 5 kịch bản chạy thật đạt | — |
| 30/10/2026 | S3 | PHÁT HÀNH | — | Commit Sprint 3 trên `chat` | `ef8a519` |
| 30/10/2026 | S4 | BẮT ĐẦU | — | Bắt đầu Sprint 4 | CH-S4-DOC-01 |
| 30/10/2026 | S4 | LỖI | L-09 | SDK chặn lần trả lời sau khi pause | CH-S4-FE-01 |
| 30/10/2026 | S4 | SỬA | L-09 | `ChatAgent` xoá `pendingInterrupts`, chuyển `resume` vào input | CH-S4-FE-01 |
| 30/10/2026 | S4 | QUYẾT ĐỊNH | QD-22 | `ask_user` qua tool, duyệt tool trong middleware, saver RAM theo lượt | CH-S4-BE-01 → BE-04 |
| 30/10/2026 | S4 | THAY ĐỔI | TD-010 | Route resume, event pause, biến `TOOLS_REQUIRING_APPROVAL`; tài liệu API §5 | CH-S4-BE-01 → FE-01, DOC-02 |
| 30/10/2026 | S4 | RỦI RO | RR-16, RR-06 | Checkpoint không được dọn; mapping C1/A1 đã kiểm chứng | CH-S4-BE-04 |
| 30/10/2026 | S4 | KẾT THÚC | — | Xong 8/8 task; backend 77 test, frontend 41 test xanh; 4 kịch bản chạy thật đạt | — |
| 30/10/2026 | S4 | PHÁT HÀNH | — | Commit Sprint 4 trên `chat` | `f3a3008` |
| 30/10/2026 | — | QUYẾT ĐỊNH | QD-23 | Người dùng chốt Q-08: một SSE mỗi tab, quay lại thì connect | — |
| 30/10/2026 | S5 | BẮT ĐẦU | — | Bắt đầu Sprint 5 | CH-S5-DOC-01 |
| 30/10/2026 | S5 | THAY ĐỔI | TD-011 | Route connect, live store Redis, stop qua Redis, `REDIS_URL`; tài liệu API §6, §7 | CH-S5-BE-01 → FE-01, DOC-02 |
| 30/10/2026 | S5 | RỦI RO | RR-14, RR-02, RR-10 | Mở lại thấy phần đang sinh (đã xử lý); cập nhật giảm thiểu | — |
| 30/10/2026 | S5 | KẾT THÚC | — | Xong 7/7 task; backend 84 test, frontend 42 test xanh; 3 kịch bản chạy thật đạt | — |
| 30/10/2026 | S5 | PHÁT HÀNH | — | Commit Sprint 5 trên `chat` | `95dd134` |
| 30/10/2026 | S6 | BẮT ĐẦU | — | Bắt đầu Sprint 6; không có câu hỏi chặn | CH-S6-DOC-01 |
| 30/10/2026 | S6 | QUYẾT ĐỊNH | QD-24, QD-25, QD-26 | Vai trò owner khoá và đủ quyền, chống leo thang; lời mời và rời tổ chức; gửi thư sau commit | CH-S6-BE-01 → BE-06 |
| 30/10/2026 | S6 | THAY ĐỔI | TD-012 | Route tổ chức, thành viên, lời mời, vai trò, xác minh email, đặt lại mật khẩu; `SMTP_*`, `FRONTEND_URL`; tài liệu API §2 | CH-S6-BE-01 → FE-03, DOC-02 |
| 30/10/2026 | S6 | RỦI RO | RR-15 | Vai trò owner nhận quyền mới khi đồng bộ (đã xử lý) | CH-S6-BE-05 |
| 30/10/2026 | S6 | LỖI | L-10 | Trang mời không đổi sau khi đăng xuất | CH-S6-FE-03 |
| 30/10/2026 | S6 | SỬA | L-10 | Tải lại trang sau khi đăng xuất | CH-S6-FE-03 |
| 30/10/2026 | S6 | KẾT THÚC | — | Xong 11/11 task; backend 106 test, frontend 49 test xanh; 5 kịch bản chạy thật đạt | — |
| 30/10/2026 | S6 | PHÁT HÀNH | — | Commit Sprint 6 trên `chat` | `44eeb66` |
| 30/10/2026 | S7 | BẮT ĐẦU | — | Bắt đầu Sprint 7; không có câu hỏi chặn | CH-S7-DOC-01 |
| 30/10/2026 | S7 | QUYẾT ĐỊNH | QD-27 | Tệp chat: presigned upload có xác minh, media part AG-UI trỏ `stored-file:`, byte đọc lại trong lượt | CH-S7-BE-02 → BE-04 |
| 30/10/2026 | S7 | THAY ĐỔI | TD-013 | Route upload/complete/tải tệp, `file_ids`, `STORAGE_*`, RustFS, `uv run storage setup`; tài liệu API §2, §3 | CH-S7-BE-01 → FE-02, DOC-02 |
| 30/10/2026 | S7 | RỦI RO | RR-17 | Tệp không gửi nằm lại storage; đọc lại tệp mỗi lượt | CH-S7-BE-02 |
| 30/10/2026 | S7 | KẾT THÚC | — | Xong 9/9 task; backend 116 test, frontend 57 test xanh; 3 kịch bản chạy thật đạt | — |
| 30/10/2026 | S7 | PHÁT HÀNH | — | Commit Sprint 7 trên `chat` | `94eaae8` |
| 30/10/2026 | S8 | BẮT ĐẦU | — | Bắt đầu Sprint 8; không có câu hỏi chặn | CH-S8-DOC-01 |
| 30/10/2026 | S8 | QUYẾT ĐỊNH | QD-28 | Token share bằng HMAC, snapshot toàn cây có version, copy trong request dưới lease | CH-S8-BE-01 → BE-03 |
| 30/10/2026 | S8 | THAY ĐỔI | TD-014 | Route share, xem share, tệp share, copy; trang `/s/{token}`; tài liệu API §2 | CH-S8-BE-01 → FE-02, DOC-02 |
| 30/10/2026 | S8 | LỖI | L-11 | Trang share giữ kết quả của lúc xem ẩn danh sau khi đăng nhập | CH-S8-FE-02 |
| 30/10/2026 | S8 | SỬA | L-11 | Khoá query gồm người xem | CH-S8-FE-02 |
| 30/10/2026 | S8 | RỦI RO | RR-18 | Copy trong request, job dở không được dọn | CH-S8-BE-03 |
| 30/10/2026 | S8 | KẾT THÚC | — | Xong 7/7 task; backend 122 test, frontend 59 test xanh; 4 kịch bản đạt (3 chạy thật, 1 test API) | — |
| 30/10/2026 | S8 | PHÁT HÀNH | — | Commit Sprint 8 trên `chat` | `c60df17` |
| 30/10/2026 | S9 | BẮT ĐẦU | — | Bắt đầu Sprint 9; không có câu hỏi chặn | CH-S9-DOC-01 |
| 30/10/2026 | S9 | QUYẾT ĐỊNH | QD-29 | Trần hàng đợi lượt, rate limit qua Redis, log lượt, Langfuse tuỳ chọn, dọn checkpoint, model giả cho load test | CH-S9-BE-01 → QA-01 |
| 30/10/2026 | S9 | THAY ĐỔI | TD-015 | 503 `server_busy`, `MAX_QUEUED_TURNS`, `LANGFUSE_*`, `AGENT_FAKE_MODEL`, `uv run loadtest`; `van-hanh.md`; chấm lại use case | CH-S9-BE-01 → DOC-02 |
| 30/10/2026 | S9 | RỦI RO | RR-13, RR-16, RR-10 | SSE qua proxy và dọn checkpoint đã xử lý; runner trong process đủ theo load test | CH-S9-BE-05, BE-06, QA-01 |
| 30/10/2026 | S9 | KẾT THÚC | — | Xong 9/9 task; backend 126 test, frontend 59 test xanh; load test đạt; use case 13 Đạt, 7 Một phần, 12 Sau | — |
| 30/10/2026 | S9 | PHÁT HÀNH | — | Commit Sprint 9 trên `chat` | `aa24411` |
| 30/10/2026 | Sau S9 | BẮT ĐẦU | — | Rà soát lỗi và nợ kỹ thuật toàn bộ S0–S9 (backend chat/agent, tổ chức/tệp/share, frontend) | — |
| 30/10/2026 | Sau S9 | LỖI | L-12 → L-29 | 18 lỗi từ rà soát: upload ghi đè, copy dở hiện ra, connect giữ kết nối DB, stop đè resume, rate limit sau proxy, spam lời mời, mất câu hỏi ở composer, link ảnh hết hạn… Đã sửa, có test | — |
| 30/10/2026 | Sau S9 | QUYẾT ĐỊNH | QD-30 | Cách sửa: bucket rate limit, `storage cleanup` hằng ngày, 20 MB tệp mỗi lượt, toast, sidebar theo trang, lint vendor sửa tại chỗ | — |
| 30/10/2026 | Sau S9 | THAY ĐỔI | TD-016 | Xoá chat dừng lượt; copy dở trả 404; 429/422 mới; `uv run storage cleanup`; `van-hanh.md`, API §2 | — |
| 30/10/2026 | Sau S9 | RỦI RO | RR-05, RR-11, RR-12, RR-17, RR-18 | Bốn mục đã xử lý; RR-18 còn copy trong request và chưa purge dòng | — |
| 30/10/2026 | Sau S9 | KẾT THÚC | — | Backend 135 test, frontend 61 test xanh; lint, typecheck, build sạch; kiểm thử thật composer, stop, huỷ lượt chờ, cleanup | — |
| 30/10/2026 | Sau S9 | PHÁT HÀNH | — | Commit sửa lỗi rà soát trên `chat` | `9151e03` |
