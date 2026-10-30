# Use cases chat và quyền tổ chức theo database hiện hành

Cập nhật: **29/10/2026**, Asia/Ho_Chi_Minh.

Nguồn dữ liệu chuẩn: [database đã chốt giai đoạn 1–4](database-decisions.md). Tài liệu này giữ danh mục 32 tình huống sản phẩm, phân biệt phạm vi hiện tại và mở rộng. **Không phải catalogue bảng hoặc chỉ thị đưa lại schema cũ.** Chưa có implementation end-to-end của toàn bộ các tình huống.

## 1. Quy tắc hiện hành

- User có personal workspace và nhiều organization workspace; scope mỗi chat bất biến.
- Một agent cố định, tool/skill theo code và cấu hình; org dùng RBAC, personal dùng allowlist.
- Chat riêng tư mặc định, không admin/superuser bypass.
- Share là snapshot toàn cây. Cá nhân public; tổ chức chỉ active member cùng org có link. Không direct-recipient/team hoặc live collaboration.
- Hỏi tiếp từ share tạo bản copy chat và S3 object mới; copy completed độc lập với việc revoke/xóa source.
- Cây message theo parent, edit/regenerate giữ sibling cũ, không xóa message riêng.
- Một assistant pending/running/requires_action mỗi conversation. User bổ sung câu trả lời vào activity/metadata của cùng assistant khi resume.
- Redis phục vụ live reconnect; PostgreSQL lưu terminal/pause. Không cam kết mọi token sống qua mất Redis hoặc worker crash.
- Chưa có RAG ACL, memory xuyên chat, credential/action receipt/audit nâng cao hoặc team.

## 2. Màn hình và dữ liệu nền

| Vùng UI | Phạm vi hiện tại |
|---|---|
| Chọn workspace | Personal và các tổ chức còn membership hợp lệ |
| Sidebar | Chat owner trong workspace, pin/archive/folder một cấp, phân trang |
| Chat | Nhánh đang chọn, AG-UI content/attachments/files, status thật |
| Hoạt động | Text/tool/progress được phép công bố, không raw checkpoint |
| Chờ người dùng | Activity hỏi/duyệt với action_id, payload server, actor/response, không hết hạn mặc định |
| Shared snapshot | Toàn bộ cây và file của bản đã publish, không live source |
| Quản trị tổ chức | Invitation, membership, role và permission trong phạm vi được giao |

Search nội dung, nguồn/kết nối, memory, feedback và audit UI là feature sau. Không hiện tên checkpoint/Redis/fence cho người dùng thông thường.

## 3. Danh mục 32 tình huống

**Hiện tại** nghĩa là mô hình đã chốt hỗ trợ hoặc có proof; vẫn cần backend/UI. **Backend** là contract triển khai chưa hoàn chỉnh. **Sau** là chưa thuộc scope; không tự thêm bảng. **Policy mới** là thay đổi có chủ đích so với đề xuất ban đầu.

### Hội thoại

| ID | Người dùng muốn | Trạng thái và hành vi |
|---|---|---|
| C01 | Viết một email/bản nháp, chat mới có tên | Hiện tại cho chat/text; title background cần cơ chế không ghi đè user trước khi bật |
| C02 | Hỏi tiếp theo nhánh đang chọn | Hiện tại: context đi theo parent đã authorize, giữ câu cũ |
| C03 | Đóng/mở trang giữa câu trả lời | Backend: worker tách HTTP, Redis snapshot + watermark + tail; không hứa khôi phục prefix khi Redis/worker mất |
| C04 | Stop và giữ phần trả lời dở | Hiện tại cho status/partial; stop theo conversation + assistant messageId, không body. pending/running dừng và cancelled giữ partial; requires_action hủy toàn lượt. ACK không đồng nghĩa đã dừng |
| C05 | Retry mạng không nhân lượt, regenerate tạo phương án mới | Regenerate đã chốt. Hiện không tự retry mutation, lỗi mạng thì đọc trạng thái/connect; chưa bảo đảm dedup mọi submit. Identity/hash để mở rộng sau nếu cần |
| C06 | Edit câu cũ, chọn nhánh khác hoặc copy chat | Hiện tại cho parent/sibling và copy snapshot; không exact native checkpoint fork theo branch |
| C07 | Đổi tên thủ công thắng tên tự sinh | Backend: chưa chốt conditional update thay thế source/revision đã bỏ |
| C08 | Hai tab giữ hai nhánh, không trộn context | Hiện tại có parent tường minh và busy qua active unique; state nhánh per-tab và integration test còn cần |
| C09 | Pin/archive/folder, đọc trên thiết bị khác, tìm chat | Hiện tại cho tổ chức sidebar/history; search nội dung chưa thiết kế, không unread/read markers |

Retry request cũ và regenerate mới là hai thao tác khác nhau. Public threadId (conversation) và SQL messageId theo [quyết định ID](conversation-message-run-id-decisions.md).

### File và dữ liệu

| ID | Người dùng muốn | Trạng thái và hành vi |
|---|---|---|
| D01 | Upload PDF, biết đã xử lý được chưa | Có từ S7: đính kèm (ảnh, PDF, văn bản) qua presigned upload có xác minh, tải lại qua URL ký; model đọc tệp mỗi lượt. Extraction/scan/status/retry pipeline để sau, không có files.status |
| D02 | Hỏi tài liệu nội bộ có citation/version | Sau: attachments có chỗ chứa nguồn render nhưng chưa có source/version/ACL/RAG |
| D03 | Bị chặn đọc lương khi không có quyền HR | Sau: quyền source/row/field trước model; quyền gọi tool không đủ thay ACL |
| D04 | So sánh hai dataset nhưng chỉ được đọc một | Sau: source scopes và completeness; không để model nhìn dữ liệu ngoài quyền |
| D05 | Nguồn đổi/xóa/revoke ảnh hưởng dữ liệu dẫn xuất | Sau: source version/dependencies và policy phân phối; chưa áp lên copy độc lập đã chốt |
| D06 | Tạo Excel/PDF rồi tải lại | Hiện tại có object/link cho file output; worker tạo/copy S3 thực và pipeline nâng cao cần tích hợp |
| D07 | Web search kết hợp tài liệu nội bộ | Quyền tool hiện tại; source ACL và policy đưa dữ liệu nội bộ ra ngoài để sau |

Không dùng UUID trong citation hoặc metadata làm quyền tải file. Chat object luôn private; gateway kiểm tra quyền chat/share trước download. URL có hạn không thay bucket/key bền vững.

### Tool và hành động

| ID | Người dùng muốn | Trạng thái và hành vi |
|---|---|---|
| T01 | Tra đơn hàng bằng đúng account/scope | Quyền tool có nền; delegated account và row/target scopes chưa thiết kế |
| T02 | Tạo ticket có xác nhận, không nhân thao tác | Sau: operation identity/idempotency và receipt/reconcile ngoài approval cơ bản |
| T03 | Gửi email đã preview và duyệt đúng người nhận/file | Pause approval có nền; account gửi, args binding và external outcome cần thiết kế theo feature |
| T04 | Người quản lý khác duyệt hoàn tiền | Sau: reviewer scope/delegation/service principal; hiện không cho mượn owner identity để approve |
| T05 | Tool timeout nhưng có thể đã làm xong | Sau: unknown/reconcile theo external operation; không coi failed message là bằng chứng side effect chưa xảy ra |
| T06 | Tool có quyền nhưng cần kết nối lại OAuth | Sau với delegated integration; login provider không tự là credential binding cho mọi tool |
| T07 | Tool bị thu hồi quyền khi đang chờ | Hiện tại và proof: kiểm tra lại trước approve và sát lúc tool chạy, action không tự cấp quyền |

Tool hệ thống chỉ đọc và MCP search có thể dùng cấu hình triển khai. Nếu bật tool ghi, phải xác định account/target/operation và kiểm chứng side effect; không tự suy checkpoint đã bảo đảm external exactly-once. Approve false có thể tiếp tục giải thích; cancel toàn lượt là thao tác khác.

### Tổ chức, share và lifecycle

| ID | Người dùng muốn | Trạng thái và hành vi |
|---|---|---|
| O01 | Một user ở nhiều org, chuyển workspace | Hiện tại: session toàn hệ thống, request kiểm tra scope; execution cũ không chuyển org |
| O02 | Mời thành viên, nhóm team Sales | Có từ S6: mời bằng email, nhận lời mời (tạo tài khoản nếu chưa có), vai trò và quyền; team/org units chưa có trong scope |
| O03 | Share cho đồng nghiệp/team | Có từ S8: public personal hoặc link nội bộ org, snapshot toàn cây có version, thu hồi; chưa direct-recipient/team |
| O04 | Người nhận hỏi tiếp | Có từ S8: "Hỏi tiếp" copy chat và tệp (object mới) thành chat riêng của người nhận, chạy bằng quyền của họ; không copy runtime/credentials |
| O05 | Nhớ sở thích user xuyên chat trong workspace | Sau: native Store + policy, không dùng checkpoint của một assistant làm memory xuyên chat |
| O06 | Xem/sửa/xóa memory | Sau: chưa có Store API/UI/provenance/cleanup |
| O07 | Rời org khi có stream/approval | Có từ S6: rời hoặc bị xoá thì mất đọc/resume/tool ngay request kế tiếp; lượt đang chạy bị dừng, lượt đang chờ bị huỷ (QD-25) |
| O08 | Xóa chat/account hoặc export history | Soft-delete/revoke source share hiện tại; hard purge/export/native/S3 cleanup để sau |
| O09 | Xem ai duyệt/gửi email hoặc ai đổi quyền | Action metadata có actor/response; audit quyền, external receipts và retention độc lập để sau |

## 4. Quyền theo lớp

Các kiểm tra hiện tại: authenticated user active → workspace/membership active → quyền chat/share/file → permission tool/skill → payload/action hiện tại. Owner/Admin quản trị tổ chức không tự có quyền nội dung.

Nếu sau này bật dữ liệu doanh nghiệp, bổ sung authorize nguồn/document/row/field trước model, kiểm tra account và policy đưa dữ liệu ra ngoài. Quyền đọc nguồn không mặc nhiên là quyền phân phối answer/artifact cho mọi người.

Với policy share toàn org hiện tại, nguồn Finance/HR hạn chế cần thảo luận lại audience/redistribution trước khi bật. Không áp mặc định policy cũ “revoke source thì mọi copy cũng biến mất” vì đã chốt copy completed độc lập.

## 5. Hợp đồng cần hoàn thiện trước triển khai

- Public/native thread mapping, phối hợp stop theo assistant message và background title.
- Redis accumulated prefix + tail, gap/reset, authority writer và reconnect không gọi model.
- Renderer activity user_interaction và context builder lấy user answer đúng một lần.
- API auth cho history/list/start/connect/resume/download/share/copy; không tin client state/tools.
- Quyền thay đổi khi socket đang mở cần đường revalidation, không chỉ check ở lúc connect.

Không tạo thêm bảng chỉ vì tên entity xuất hiện trong các tình huống. [Bản tổng hợp database](database-decisions.md) là nguồn schema; [kiến trúc](agent-chat-architecture.md) và [API](chat-agent-api-contract.md) xác định nơi backend còn phải triển khai.

## 6. Chấm lại sau S0–S9 (30/10/2026)

Chấm theo code trên nhánh `chat`: **Đạt** là chạy được và có test hoặc đã chạy thật; **Một phần** là phần trong phạm vi đã có, phần ghi kèm chưa có; **Sau** là ngoài phạm vi đã chốt.

| ID | Kết quả | Căn cứ / còn thiếu |
|---|---|---|
| C01 | Một phần | Chat chữ, tên mặc định lấy từ câu hỏi đầu (S2). Chưa có model tự đặt tên |
| C02 | Đạt | Context dựng lại theo nhánh đã kiểm quyền (S2) |
| C03 | Đạt | Redis live view + `connect` (S5); process chết giữa lượt thì không khôi phục (RR-01) |
| C04 | Đạt | Stop tại chỗ, qua process khác, lượt mồ côi, lượt đang chờ (S3–S5) |
| C05 | Đạt | Regenerate tạo phiên bản mới (S3); không tự retry mutation (QD-06) |
| C06 | Đạt | Sửa câu hỏi, chuyển nhánh (S3), copy từ share (S8) |
| C07 | Đạt | Tên tự sinh chỉ đặt khi chat còn tên mặc định; đổi tên tay luôn giữ (S2, S3) |
| C08 | Đạt | Nhánh theo tab, parent tường minh, một lượt active mỗi chat (S3) |
| C09 | Một phần | Ghim, lưu trữ, folder (S3). Chưa tìm kiếm nội dung |
| D01 | Một phần | Đính kèm, model đọc, tải lại (S7). Chưa có trạng thái xử lý tệp |
| D02 | Sau | RAG, nguồn có version/ACL |
| D03 | Sau | Quyền theo nguồn/hàng/trường |
| D04 | Sau | Như D03 |
| D05 | Sau | Phụ thuộc nguồn |
| D06 | Một phần | Tải lại tệp trong chat và share (S7, S8). Chưa có tool tạo tệp |
| D07 | Sau | Tool web search, chính sách dữ liệu nội bộ |
| T01 | Một phần | Quyền tool theo vai trò (S3, S6). Chưa có tài khoản/phạm vi uỷ quyền |
| T02 | Sau | Idempotency thao tác ngoài |
| T03 | Một phần | Duyệt tool trước khi chạy (S4). Chưa có tool gửi email |
| T04 | Sau | Người duyệt khác người hỏi |
| T05 | Sau | Đối soát kết quả tool |
| T06 | Sau | OAuth uỷ quyền |
| T07 | Đạt | Kiểm lại quyền trước khi duyệt và sát lúc tool chạy (S4); thu hồi qua màn vai trò (S6) |
| O01 | Đạt | Nhiều workspace, kiểm membership mỗi request (S1, S6) |
| O02 | Đạt | Mời, nhận lời mời, vai trò (S6). Chưa có nhóm |
| O03 | Đạt | Link public/nội bộ, version, thu hồi (S8). Chưa chia sẻ cho người cụ thể |
| O04 | Đạt | "Hỏi tiếp" bằng bản sao riêng (S8) |
| O05 | Sau | Memory |
| O06 | Sau | Memory |
| O07 | Đạt | Rời/bị xoá: mất quyền ngay, dừng lượt đang chạy, huỷ lượt đang chờ, thu hồi share (S6, trigger) |
| O08 | Một phần | Xoá mềm chat, thu hồi share (S3, S8). Chưa xoá tài khoản, export |
| O09 | Sau | Nhật ký thao tác chưa có trong schema |

Tổng: 13 Đạt, 7 Một phần, 12 Sau; không tình huống nào trong phạm vi bị bỏ dở.
