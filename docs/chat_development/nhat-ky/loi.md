# Nhật ký lỗi

Ghi mọi lỗi của dự án phát triển chat: phát hiện khi rà soát, khi làm, khi kiểm thử hay sau phát hành. Luật ghi và mức độ xem ở [README](./README.md).

Lỗi ở đây là **hành vi sai** so với quyết định đã chốt (database, ID, API, ChatAgent) hoặc tài liệu tự mâu thuẫn. Chức năng **chưa làm** (route chưa có, scaffold hiện tại chưa theo thiết kế đích) là phạm vi của sprint, không ghi thành lỗi.

## Bảng tổng hợp

| Mã | Mức | Tóm tắt | Phát hiện | Xác minh | Sửa ở | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| L-01 | Thấp | Use case C04 ghi backend chuyển tín hiệu stop theo `messageId + runId`; mục 5 còn "API dedupe" | Rà tài liệu 29/10 | Đã xác minh | TD-001 | Đã sửa |
| L-02 | Cao | Sau đăng nhập bị đẩy về `/login`: `resetQueries` hủy request `/auth/session` đang chạy, proxy vẫn chuyển tới backend nên token đã xoay; request lặp mang cookie cũ bị coi là dùng lại, cả phiên bị thu hồi | Chạy thật S1, 29/10 | Đã xác minh | CH-S1-FE-02, CH-S1-BE-02 | Đã sửa (S1) |
| L-03 | Thấp | Form đăng nhập và đăng ký dùng `id` cố định; Next giữ route trước ở trạng thái ẩn nên trùng `id`, nhãn bị gộp ("Email Email") | Chạy thật S1, 29/10 | Đã xác minh | CH-S1-FE-02 | Đã sửa (S1) |
| L-04 | Cao | Baseline chỉ dump schema nên mất 5 dòng danh mục `permissions` mà SQL giai đoạn 1 seed; tổ chức tạo sau đó không có grant nào, chủ tổ chức không tạo được chat | Rà S2, 29/10 | Đã xác minh | CH-S2-BE-01 | Đã sửa (S2) |
| L-05 | Trung bình | Câu trả lời hiện ra một lần lúc kết thúc thay vì stream: lớp nén gzip của Next gom cả response `text/event-stream` đi qua rewrite | Chạy thật S2, 30/10 | Đã xác minh | CH-S2-FE-02 | Đã sửa (S2) |
| L-06 | Thấp | Tải lại trang thì reasoning của mọi lượt cũ mở bung rồi mới tự đóng | Chạy thật S2, 30/10 | Đã xác minh | CH-S2-FE-02 | Đã sửa (S2) |
| L-07 | Cao | Sau khi thêm registry tool, mọi lượt chat treo: tập tool truyền cho `lru_cache` là `set` (không hash được) nên runner ném lỗi trước khối `try`, stream không bao giờ đóng | Test S3, 30/10 | Đã xác minh | CH-S3-BE-05 | Đã sửa (S3) |
| L-08 | Trung bình | Bấm dừng thì câu trả lời giữ đúng nhưng UI báo "Mất kết nối": runner phát `RUN_FINISHED` khi step/text message còn mở, verifier của `@ag-ui/client` từ chối | Chạy thật S3, 30/10 | Đã xác minh | CH-S3-BE-03 | Đã sửa (S3) |
| L-09 | Cao | Bấm "Cho phép" không có tác dụng và báo "Mất kết nối": `@ag-ui/client` ghi `pendingInterrupts` từ `RUN_FINISHED` có outcome interrupt rồi chặn lần chạy kế tiếp không kèm `resume` khớp id, ném lỗi trước khi gửi request | Chạy thật S4, 30/10 | Đã xác minh | CH-S4-FE-01 | Đã sửa (S4) |
| L-10 | Trung bình | Trang nhận lời mời: bấm "Đăng xuất để đổi tài khoản" thì phiên bị thu hồi nhưng màn vẫn báo đang đăng nhập email cũ: `queryClient.clear()` không làm query đang hiển thị tải lại | Chạy thật S6, 30/10 | Đã xác minh | CH-S6-FE-03 | Đã sửa (S6) |
| L-11 | Trung bình | Trang xem share: đăng nhập xong quay lại vẫn hiện "Đăng nhập để hỏi tiếp" vì kết quả lúc xem ẩn danh (`can_copy=false`) còn trong cache với cùng khoá | Chạy thật S8, 30/10 | Đã xác minh | CH-S8-FE-02 | Đã sửa (S8) |
| L-12 | Cao | Upload: `complete` kiểm byte của object tạm rồi `copy_object` lại từ storage; PUT lần nữa bằng URL ký cũ trong lúc kiểm (hoặc sau khi xong) thì key cuối nhận byte chưa kiểm, vượt cỡ, hoặc ghi đè tệp đã ghi nhận (kể cả tệp trong snapshot) | Rà soát code 30/10 | Đã xác minh (test) | `files/service.py`: ghi chính byte đã kiểm bằng `put_object`, commit dòng `stored_files` trước khi ghi | Đã sửa (sau S9) |
| L-13 | Cao | Bản copy hiện trong sidebar, mở và chat tiếp được trước khi job copy hoàn tất (kể cả job thất bại hoặc bị huỷ vì mất quyền share) | Rà soát code 30/10 | Đã xác minh (test) | `ConversationRepository`: ẩn chat có job copy chưa `completed`, như `can_read_conversation` | Đã sửa (sau S9) |
| L-14 | Cao | Connect giữ một kết nối database (transaction mở) suốt thời gian stream; 15 tab connect là hết pool, mọi request khác và việc lưu lượt chờ timeout | Rà soát code 30/10 | Đã xác minh (test) | `connect.py`: commit sau khi đọc xong PostgreSQL | Đã sửa (sau S9) |
| L-15 | Cao | Stop lượt đang chờ đọc trạng thái không khoá, rồi huỷ "tại chỗ" với mọi trạng thái active: resume chen giữa thì lượt đã resume bị đánh `cancelled` trong khi vẫn chạy, câu trả lời mất, chat mở cho lượt thứ hai | Rà soát code 30/10 | Đã xác minh (test) | `TurnService`: huỷ có điều kiện đúng trạng thái đã đọc, không khớp thì rollback và dừng process đang chạy; `_finalize` bỏ kết quả khi dòng đã bị huỷ | Đã sửa (sau S9) |
| L-16 | Trung bình | Resume dùng lại key Redis của lần chạy đã pause (giữ 120 giây): tab khác connect lúc đó thấy lại câu hỏi đã trả lời và `RUN_FINISHED` interrupt cũ, dừng theo dõi lượt đang chạy | Rà soát code 30/10 | Đã xác minh (test) | `LiveStore.reset` khi bắt đầu lượt resume | Đã sửa (sau S9) |
| L-17 | Thấp | Xoá chat còn lượt đang chạy hoặc đang chờ: không ai dừng được nữa, checkpoint không bị dọn | Rà soát code 30/10 | Đã xác minh (test) | Xoá chat dừng lượt active trước và sau khi xoá | Đã sửa (sau S9) |
| L-18 | Thấp | Stop đúng lúc lượt pause: database `cancelled` nhưng stream vẫn kết thúc bằng outcome interrupt | Rà soát code 30/10 | Đã xác minh (test) | `runner._finish`: trạng thái `cancelled` luôn phát outcome cancelled | Đã sửa (sau S9) |
| L-19 | Trung bình | Rate limit tính theo `request.client`: sau Next/nginx mọi người dùng chung một IP; 30 lần đăng nhập sai khoá `/auth/session` và `/auth/refresh` của mọi người; xem share có ảnh nhanh chạm trần 30/phút | Rà soát code 30/10 | Đã xác minh (test) | Tách bucket `auth` / `session` (300) / `shares` (300) / `share-copy`; IP thật qua `--forwarded-allow-ips` của uvicorn (`van-hanh.md` §3) | Đã sửa (sau S9) |
| L-20 | Trung bình | Gửi lời mời không giới hạn: ai cũng tạo được tổ chức nên dùng được SMTP để spam; tên có xuống dòng làm hỏng tiêu đề thư (lỗi không bắt) | Rà soát code 30/10 | Đã xác minh (test) | Giới hạn 50 thư/giờ mỗi người gửi; `Name` cấm ký tự điều khiển; `deliver` bắt `ValueError` | Đã sửa (sau S9) |
| L-21 | Thấp | `complete` và copy giữ transaction trong lúc gọi storage (AGENTS §19) | Rà soát code 30/10 | Đã xác minh (test) | Commit trước khi gọi storage | Đã sửa (sau S9) |
| L-22 | Cao | Nhấn Enter khi đang có lượt chạy hoặc chờ (chỉ có nút Dừng) vẫn submit: câu hỏi và tệp bị xoá, hoặc bị gửi rồi nhận 409 | Rà soát code 30/10 | Đã xác minh (test) | `ChatComposer` không gửi khi bị khoá, giữ chữ | Đã sửa (sau S9) |
| L-23 | Cao | Gửi thất bại (tạo chat lỗi, 409, mạng) làm mất câu hỏi đã gõ và tệp đã tải | Rà soát code 30/10 | Đã xác minh (test) | Composer chỉ xoá khi server đã nhận câu hỏi (`sendMessage` trả kết quả, `PromptInputProvider`) | Đã sửa (sau S9) |
| L-24 | Trung bình | Bấm ảnh trong chat sau hơn 10 phút mở link ký đã hết hạn | Rà soát code 30/10 | Đã xác minh (test) | Link ảnh làm mới trước khi hết hạn; bấm thì lấy link mới | Đã sửa (sau S9) |
| L-25 | Trung bình | Xoá, lưu trữ, ghim, chuyển folder, xoá folder thất bại mà không báo gì | Rà soát code 30/10 | Đã xác minh (test) | Toast báo lỗi (`Toaster` gắn ở `AppProviders`) | Đã sửa (sau S9) |
| L-26 | Trung bình | Tạo tài khoản từ lời mời xong mà đăng nhập lỗi thì thử lại luôn báo lời mời đã dùng | Rà soát code 30/10 | Đã xác minh (test) | Thử lại chỉ đăng nhập | Đã sửa (sau S9) |
| L-27 | Trung bình | Danh sách chat, thành viên, workspace dừng ở 100 mục, không báo | Rà soát code 30/10 | Đã xác minh (test) | Sidebar tải thêm theo trang ("Xem thêm"); thành viên, workspace tải hết các trang | Đã sửa (sau S9) |
| L-28 | Trung bình | Refresh gặp lỗi mạng hoặc 5xx (lúc deploy) là đăng xuất người dùng | Rà soát code 30/10 | Đã xác minh (test) | Chỉ hết phiên khi refresh bị từ chối (401/403); còn lại báo như mất kết nối | Đã sửa (sau S9) |
| L-29 | Thấp | Mở tệp hoặc sao chép link share lỗi thì không báo, promise bị bỏ lửng | Rà soát code 30/10 | Đã xác minh (test) | Bắt lỗi và hiện thông báo | Đã sửa (sau S9) |

Giá trị cột *Xác minh*:
- **Đã xác minh:** đã đọc code/tài liệu hoặc chạy thử và chắc chắn.
- **Theo code:** suy từ code, chưa chạy thử.
- **Cần chạy thử:** cần tái hiện trên môi trường dev.

## Chi tiết

### L-01: Use case còn stop theo runId
- **Vị trí:** `docs/chat_development/chat-use-cases-and-organization-access.md`, dòng C04, ghi chú sau bảng hội thoại, mục 5.
- **Thực tế:** "backend chuyển tín hiệu theo messageId + runId"; "wire runId"; "API dedupe".
- **Mong đợi:** stop theo conversation + assistant `messageId`, không body, không `runId` ([quyết định ID §7](../conversation-message-run-id-decisions.md#7-stop-theo-assistant)); tạm bỏ dedup ([API §9](../chat-agent-api-contract.md#9-xử-lý-mạng-đơn-giản-trong-phạm-vi-hiện-tại)).
- **Đã sửa:** TD-001 (29/10/2026).
- **Trạng thái:** Đã sửa.

### L-02: Phiên bị thu hồi ngay sau đăng nhập
- **Vị trí:** `frontend/src/features/auth/hooks/use-auth-mutations.ts` (`useLogin`), `use-session.ts`; `backend/src/app/modules/auth/service.py::_rotate`.
- **Tái hiện:** đăng ký hoặc đăng nhập trên trình duyệt.
- **Thực tế:** request `/auth/session` đầu `ERR_ABORTED` nhưng backend đã xoay token; request thứ hai nhận `401 refresh_reuse`, mọi token của họ phiên bị thu hồi.
- **Mong đợi:** vào màn chat.
- **Cách sửa:** không gắn abort signal cho request xoay token; `useLogin` xóa query session thay vì reset; backend cho ân hạn 10 giây với token vừa xoay (QD-18), áp cả trường hợp hai tab cùng tải trang.
- **Test chặn tái phát:** `tests/api/auth/test_auth.py::test_token_presented_again_within_grace_keeps_the_session`.
- **Trạng thái:** Đã sửa (S1).

### L-04: Mất danh mục permission
- **Vị trí:** `db/migrations/20261029093342_chat_baseline.sql` (dump `--schema-only`), so với `docs/database_decisions/phase-1-schema.sql` dòng `INSERT INTO permissions`.
- **Thực tế:** bảng `permissions` rỗng; trigger `provision_organization` cấp quyền cho role từ chính bảng này nên tổ chức mới không có grant.
- **Cách sửa:** danh mục nằm trong code (`modules/authorization/catalog.py`), đồng bộ bằng `uv run iam sync-permissions` sau `dbmate up`; fixture test nạp cùng danh mục. Tổ chức tạo trước khi đồng bộ cần bổ sung grant (đã làm tay trên DB dev).
- **Test chặn tái phát:** `tests/api/conversations/test_conversations.py::test_organization_needs_conversation_create`.
- **Trạng thái:** Đã sửa (S2).

### L-05: SSE bị gom qua proxy Next
- **Vị trí:** `frontend/next.config.ts` (rewrite `/api/v1` sang FastAPI).
- **Đo:** gọi thẳng backend, 257 event về rải trong 0,57–3,15 giây; qua Next, 359 event về cùng lúc ở giây 6,19.
- **Cách sửa:** `compress: false`; nén để reverse proxy production lo, proxy đó cũng không được buffer event stream (RR-13).
- **Trạng thái:** Đã sửa (S2).

### L-07: Lượt chat treo khi lỗi trước khối try
- **Vị trí:** `backend/src/app/modules/conversations/service.py::_launch` (`frozenset & dict.keys()` trả về `set`), `modules/agent/runner.py::_execute`.
- **Thực tế:** `get_agui_agent(tools)` ném `TypeError: unhashable type` khi dựng agent, nằm ngoài `try/finally` nên không lưu trạng thái, không đóng stream; request SSE chờ mãi.
- **Cách sửa:** dùng `frozenset.intersection`; dựng agent bên trong `try` để mọi lỗi đều đi qua `_finish` (lưu `failed`, phát `RUN_ERROR`, đóng stream).
- **Test chặn tái phát:** toàn bộ `tests/api/conversations/test_turns.py` (treo trước khi sửa).
- **Trạng thái:** Đã sửa (S3).

### L-08: Stop làm UI báo mất kết nối
- **Vị trí:** `backend/src/app/modules/agent/runner.py::_finish`.
- **Thực tế:** console `AGUIError: Cannot send 'RUN_FINISHED' while steps are still active: model`; hook coi là lỗi mạng.
- **Cách sửa:** `modules/agent/lifecycle.py` theo dõi span đang mở (step, text, reasoning, tool call) và phát event END cho chúng, trong cùng ra trước, rồi mới phát trạng thái cuối và `RUN_FINISHED` có `outcome: {type: "cancelled"}`.
- **Test chặn tái phát:** `tests/unit/test_lifecycle.py`, `tests/api/conversations/test_stop.py::test_stop_keeps_the_partial_answer`.
- **Trạng thái:** Đã sửa (S3).

### L-09: SDK chặn trả lời sau khi pause
- **Vị trí:** `frontend/src/features/chat/agent/chat-agent.ts::runOperation`.
- **Thực tế:** `AGUIError: Thread has 1 pending interrupt(s) not addressed by resume`; không request nào tới backend. Cũng sẽ chặn câu hỏi mới sau khi dừng lượt đang chờ.
- **Cách sửa:** server là nơi đối chiếu interrupt (API §5), nên `ChatAgent` xoá `pendingInterrupts` trước mỗi thao tác và chuyển `resume` vào input của lượt resume.
- **Test chặn tái phát:** `chat-agent.test.ts` "lets the server decide what a paused turn still waits on".
- **Trạng thái:** Đã sửa (S4).

### L-10: Trang mời không đổi sau khi đăng xuất
- **Vị trí:** `frontend/src/features/organizations/components/invitation-screen.tsx::SignedIn`.
- **Thực tế:** `useLogout` gọi `queryClient.clear()`; query phiên và lời mời đang được component dùng không tự tải lại, nên màn giữ trạng thái đã đăng nhập.
- **Cách sửa:** đăng xuất xong thì tải lại trang, bắt đầu lại ở trạng thái chưa đăng nhập (form tạo tài khoản hoặc nút đăng nhập).
- **Test chặn tái phát:** chạy thật kịch bản 1 của S6 (không có test tự động: hành vi nằm ở tải lại trang).
- **Trạng thái:** Đã sửa (S6).

### L-11: Share hiển thị theo người xem cũ
- **Vị trí:** `frontend/src/features/shares/hooks/use-shared-conversation.ts`.
- **Thực tế:** khoá query `["shares", token]` không chứa người xem; nội dung share (link tổ chức, `can_copy`) lại phụ thuộc người xem.
- **Cách sửa:** khoá gồm id người xem (`shareKey(token, viewerId)`), cả cho link tệp.
- **Test chặn tái phát:** chạy thật kịch bản 2 của S8.
- **Trạng thái:** Đã sửa (S8).

## Mẫu ghi

```markdown
| L-xx | Nghiêm trọng/Cao/Trung bình/Thấp | <tóm tắt> | <ai/khi nào> | Đã xác minh/Theo code/Cần chạy thử | CH-S<n>-<lớp>-<số> | Mở/Đang sửa/Đã sửa (S<n>)/Không sửa (lý do) |
```

```markdown
### L-xx: <tiêu đề>
- **Vị trí:** <file:hàm>
- **Tái hiện:** <các bước>
- **Thực tế:** <…>
- **Mong đợi:** <…, trỏ tới quyết định liên quan>
- **Cách sửa:** <mã task>
- **Test chặn tái phát:** <đường dẫn test>
- **Trạng thái:** <…>
```
