# Rà soát database giai đoạn 1–4 so với tài liệu chat_development

> **Ghi chú sau dọn tài liệu:** đây là snapshot đánh giá trước khi người dùng yêu cầu xóa/rút gọn thiết kế cũ trong chat_development. Các nguồn ở mục 2 phản ánh nội dung đã đọc tại thời điểm review; một số file đã xóa hoặc viết lại. Không dùng các nhận xét về schema/API cũ ở đây làm quyết định hiện hành. Xem [database đã chốt](../chat_development/database-decisions.md).

Ngày: **29/10/2026**, Asia/Ho_Chi_Minh.

Đây là **báo cáo đối chiếu**, không phải quyết định bổ sung chức năng hoặc yêu cầu tạo thêm bảng. Không thay đổi schema đã chốt, code backend hoặc các tài liệu cũ.

## 1. Kết luận

**Bản mới phù hợp hơn với phạm vi sản phẩm hiện tại đã được người dùng chốt; không bao phủ toàn bộ kiến trúc production/doanh nghiệp trong tài liệu cũ.** Không nên kết luận bản mới tốt hơn trên mọi mặt hoặc đã đáp ứng đủ 32 use case.

- Đủ mô hình dữ liệu cho tài khoản/login, personal + organization workspace, RBAC tổ chức, chat riêng tư, cây message, pin/folder, file đơn giản, share snapshot/copy và intentional pause/resume.
- Chưa đủ thiết kế cho durable streaming/reconnect, idempotency gửi chat, title background có bảo vệ xung đột, tìm kiếm nội dung, RAG/nguồn có ACL, memory xuyên chat, external action reconciliation, audit toàn hệ thống và purge/export.
- Một số khoảng trống là **chủ động hoãn hoặc đổi policy**, không phải lỗi phải sửa lại database: không phục hồi worker chết, không bảng run, không team/org unit, không file processing status, không live collaboration, Langfuse thay thống kê usage nội bộ.
- Một số khoảng trống là **hợp đồng backend/API còn cần xác định**, không tự động đòi hỏi bảng mới: mapping ID, chống gửi trùng, multi-tab, background title, định dạng renderer/context từ activity.

## 2. Những nguồn đã đối chiếu

| Nguồn cũ | Phần được dùng |
|---|---|
| `identity-chat-schema.sql` (đã xóa sau review) | Đọc toàn bộ DDL 19 bảng identity/org/chat/branch/share/file/memory/audit |
| `identity-chat-database-design.md` (đã xóa sau review) | Quyết định thiết kế, SQL, access paths, benchmark cũ và phần tự khai còn thiếu |
| [chat-use-cases-and-organization-access.md](../chat_development/chat-use-cases-and-organization-access.md) | Toàn bộ 32 use case C/D/T/O, policy nguồn, approval, share và actor |
| `production-data-storage-design.md` (đã xóa sau review) | Cam kết journal trước SSE, queue/cancel, branch mapping, retention và nghiệm thu |
| [chat-agent-api-contract.md](../chat_development/chat-agent-api-contract.md) | Run/connect/stop, idempotency, If-Match, thread/run/native ID và acceptance |
| `database-schema-review.md` (đã xóa sau review) | Catalogue bảng, boundaries, nhánh/index, source/tool lifecycle |
| `langgraph-oss-agent-platform-design.md` (đã xóa sau review) | Yêu cầu execution tách HTTP, title, recovery, approval và memory |
| [langgraph-native-storage-findings.md](../chat_development/langgraph-native-storage-findings.md) | Checkpoint không giữ token giữa node, số bảng Saver/Store, durability và tăng trưởng |
| [agent-chat-architecture.md](../chat_development/agent-chat-architecture.md) | Mục tiêu gốc và lưu ý đây là bản nền lịch sử |
| Manual wiring, CopilotKit/AG-UI và các ghi chú UI | Quét ràng buộc persistence, ID, restore và source event |

Nguồn mới: [giai đoạn 1](phase-1-decisions.md), [giai đoạn 2](phase-2-decisions.md), [giai đoạn 3](phase-3-decisions.md), [giai đoạn 4](phase-4-decisions.md), các SQL tương ứng và [bằng chứng checkpoint/AG-UI](../experiments/langgraph-action-checkpoints/README.md).

Thứ tự ưu tiên: quyết định người dùng ngày 28–29/10 trong database_decisions thay thế các đề xuất khác policy ngày 23–27/10. Không lấy câu “phải có bảng X” trong tài liệu nghiên cứu làm chỉ thị tự mở rộng schema.

**Giới hạn nguồn cũ:** DDL 19 bảng ghi rõ chưa có execution/stream/tool/source. `chat-schema.sql` được README/native findings nhắc tới không có trong thư mục chat_development hiện tại. Vì vậy đối chiếu phần execution với mô tả thiết kế/cataloque, không khẳng định đã đọc DDL hoặc implementation cũ không có trên disk.

## 3. Bản mới tốt hơn ở đâu

| Nội dung | Bản cũ | Bản mới và đánh giá |
|---|---|---|
| Workspace | Conversation gắn org bắt buộc; chưa có personal workspace riêng trong DDL | Có personal workspace/user và org workspace, đúng yêu cầu mới |
| Đăng nhập | app_user có issuer/subject, chưa có bộ login/session đầy đủ trong DDL cũ | user_accounts nhiều provider + password, refresh token families, verification, invitation; cụ thể hơn cho auth đã chọn |
| Role tổ chức | org_role cố định owner/admin/member trong DDL | Role/permission động, nhiều role/thành viên, không cần đổi schema mỗi tool mới |
| Private by default | Có nguyên tắc owner/admin không tự đọc; grant authority còn là phần backend | Giữ nguyên nguyên tắc, bổ sung helper và kiểm tra SQL; không có admin bypass nhưng vẫn chưa phải RLS hoàn chỉnh |
| Share/copy | Shared result/version có trong DDL; audience grants/dependencies còn ở catalogue, payload JSON; không copy byte mặc định | Snapshot theo row, seal bất biến, file manifest, copy job và file mapping; sát luật toàn cây và object mới đã chốt |
| Sidebar | conversation_view riêng vì giả định live grants/nhiều viewer | Pin/archive/folder trực tiếp vì một owner, người nhận xem snapshot hoặc copy; tránh bảng không còn cần thiết |
| Folder | Tự khai thiếu trong phần 9.7 thiết kế cũ | Folder một cấp, FK scope và index; đã đáp ứng phần này |
| File cơ bản | stored_object + conversation_object, nhiều lifecycle dự kiến | message_files -> stored_files(metadata), một nguồn metadata vật lý, scope guard; đơn giản hơn cho attach/download, không thay file pipeline |
| Transcript | Content blocks JSONB, mapping sang AG-UI cần tích hợp | AG-UI Message[] canonical, attachments và activity hỏi–đáp; SDK validation đã thử trong proof |
| Checkpoint | Từng hướng tới sync theo step, thread theo conversation/branch và nhiều ranh giới chưa thử | Chỉ giữ khi pause, thread theo assistant message, resume process mới và async adapter đã thử; ít ghi hơn trên normal path trong probe, không phải benchmark tổng thể |
| Kiểm chứng | SQL/access paths đã đo, nhưng nhiều integration còn là đề xuất | Có 122 assertions SQL, 27 checks sync và 30 checks async/AG-UI; nhiều bằng chứng về scope đang dùng hơn, chưa thay integration/load/security tests |

Không so số bảng để chấm chất lượng. Bản cũ ít/more bảng ở từng vùng vì chứa team/principal/memory/audit trong khi bản mới thêm auth/workspace/copy và bỏ các vùng chưa dùng.

## 4. Ma trận 32 use case

Nhãn: **Có nền** = schema phù hợp, còn cần backend; **Một phần** = thiếu semantics hoặc subsystem để đạt toàn bộ yêu cầu; **Đổi policy** = khác yêu cầu cũ theo quyết định mới; **Để sau** = ngoài scope đã chốt. Không nhãn nào có nghĩa API/UI production đã triển khai.

| ID | Yêu cầu cũ | Đánh giá với bản mới |
|---|---|---|
| C01 | Chat mới, stream, title tự sinh | **Một phần:** conversation/message có; auto-title và live delivery cần backend, bảo vệ title chưa chốt |
| C02 | Hỏi tiếp đúng nhánh, giữ câu cũ | **Có nền:** parent/current_message, terminal immutable; dựng context server theo parent |
| C03 | Đóng/mở browser giữa câu, thấy prefix rồi nối suffix | **Một phần:** chưa có live projection/tail contract được triển khai; checkpoint khi pause không thay prefix đang sinh |
| C04 | Stop đúng lượt, giữ partial, acknowledge sau cleanup | **Một phần:** status cancelled + partial có; durable cancel intent và chuyển tín hiệu tới worker chưa có contract hoàn chỉnh |
| C05 | Retry mạng không nhân input/run; regenerate là lượt mới | **Một phần:** sibling regenerate có; chưa có request key/hash và dedupe chat được chốt. Unique active chỉ chặn cùng lúc |
| C06 | Edit câu cũ, đổi nhánh, fork có lineage | **Một phần/đổi semantics:** cây edit/regenerate có; không exact native checkpoint fork. Lượt mới dựng context từ lịch sử; copy hiện qua snapshot |
| C07 | Rename thủ công thắng title job | **Một phần:** title ghi được; đã bỏ source/revision nên chưa có chính sách conditional update thay thế |
| C08 | Hai tab khác nhánh, giữ context run, báo busy | **Có nền/một phần:** active unique + parent tường minh; nhánh của tab phải lưu client, chưa có integration test hai tab |
| C09 | Search, pin/archive, đọc từ điện thoại | **Một phần:** pin/archive/folder/history có; search nội dung chưa thiết kế, không có unread/read markers theo quyết định mới |
| D01 | Upload -> xử lý -> ready/failed/retry | **Một phần:** object và liên kết file có; status/job extraction/scanning cố ý chưa có |
| D02 | Hỏi tài liệu nội bộ có citation/version/ACL | **Để sau:** attachments chứa citation được nhưng chưa có RAG/source version/ACL subsystem |
| D03 | Chặn tìm lương ngoài quyền HR | **Để sau:** RBAC tool không thay document/row/field authorization trước model |
| D04 | Chỉ tổng hợp nguồn/dataset được phép | **Để sau:** chưa có source scope và output completeness policy |
| D05 | Thu hồi quyền nguồn ảnh hưởng answer cũ | **Để sau:** chưa có dependency graph hoặc hạn chế derived content theo ACL nguồn |
| D06 | Tạo/tải lại Excel/PDF | **Có nền/một phần:** file output + S3 key có; worker tạo file/copy thật chưa tích hợp, pipeline/provenance nâng cao chưa có |
| D07 | Web search kết hợp nguồn nội bộ, kiểm soát đưa dữ liệu ra ngoài | **Một phần:** quyền tool có; data egress/source policy chưa thiết kế |
| T01 | Tra đơn hàng bằng đúng account/row scope | **Một phần:** có quyền gọi tool; delegated credentials/resource scope chưa có mô hình đã chốt |
| T02 | Tạo ticket có idempotency và receipt | **Để sau:** approval cơ bản có nhưng external operation/receipt/reconcile chưa có contract |
| T03 | Preview và gửi email đúng bản đã duyệt | **Một phần:** pending payload lưu được; ràng buộc request hash/operation/receipt và account gửi chưa được kiểm chứng đầy đủ |
| T04 | Người quản lý khác duyệt/ủy quyền thực thi | **Để sau:** hiện resume do người có quyền chat/owner; không phải approval delegation/quorum workflow |
| T05 | Tool timeout, kết quả unknown, không làm lại | **Để sau:** failed message/checkpoint không thay external-operation ledger/idempotency. Unknown phải là outcome của action |
| T06 | Tool được cấp nhưng OAuth hết hạn/chưa kết nối | **Để sau:** auth login không tự là integration credential binding; MCP cấu hình hệ thống là phạm vi khác |
| T07 | Thu hồi quyền tool lúc chờ | **Có nền và proof:** RBAC hiện tại được recheck trước approve và tool execution; đã thử revoke thực trên bảng role_permissions |
| O01 | Một user nhiều org, đổi workspace không đổi scope cũ | **Có nền:** workspace/owner bất biến, membership kiểm tra theo request; worker context phải lấy scope server |
| O02 | Invitation và team Sales | **Một phần/đổi scope:** invitation/membership có; team/org units chưa có và không phải phạm vi đã chọn |
| O03 | Share cho người/team, chỉ bản/nhánh chọn | **Đổi policy:** public cho personal, link nội bộ cho active cùng org; snapshot toàn cây, không direct-recipient/team grant |
| O04 | Người nhận hỏi tiếp bằng quyền mình | **Có nền/đổi policy:** copy chat và object độc lập; backend vẫn phải remap đủ tree/JSON, không kế thừa runtime/credential |
| O05 | Nhớ sở thích user theo org xuyên chat | **Để sau:** chưa setup native Store/memory policy; checkpoint theo assistant không là memory xuyên conversation |
| O06 | Xem/sửa/xóa memory | **Để sau:** chưa có Store UI/API/provenance/cleanup |
| O07 | Rời org khi có stream/run/approval | **Một phần:** membership helper/revocation share và kiểm tra resume có; live SSE invalidation/cancel worker chưa tích hợp |
| O08 | Xóa chat/account hoặc export toàn lịch sử | **Một phần:** soft-delete và revoke share có; hard purge/export/native/S3 cleanup chưa thiết kế |
| O09 | Audit ai đề xuất/duyệt/gửi và ai đổi quyền | **Một phần:** action metadata có actor/response; không có audit đầy đủ quyền/receipt. Langfuse không tự thay authorization audit |

## 5. Những xung đột cần giải quyết ở API/backend trước khi triển khai

### A. Chống gửi trùng không đồng nghĩa một active message

API cũ yêu cầu cùng request identity + cùng normalized input trả về cùng operation; khác payload cùng key phải conflict. Hiện messages có ID và active unique, còn client_request_id trong copy_jobs chỉ dành copy.

Hai request trùng có thể gặp busy khi chạy đồng thời nhưng request thứ hai tới sau completed vẫn có thể tạo assistant mới nếu backend không dedupe. Chưa có cơ chế đã chốt cho input duplicate sau mất ACK.

Không bắt buộc đưa lại bảng run. Có thể thiết kế quanh stable user/assistant IDs và idempotency binding/hash; phải chốt lifetime, uniqueness/scope và xử lý cùng ID khác payload. Chưa tự thêm cột/index/bảng trong lần review này.

### B. Reload đang sinh khác reload đang chờ

Phase 4 đã chứng minh reload **sau pause** từ content + checkpoint. Yêu cầu C03/API connect cần snapshot prefix + watermark + tail **khi LLM chưa kết thúc node**. Bản mới chỉ ghi content lúc terminal/pause nên PostgreSQL chưa có prefix đó.

Nếu vẫn cần C03, backend phải có shared live buffer/projection (ví dụ Redis) và quy tắc continuity cho reconnect. Nếu giữ cam kết ngày 27/10 rằng Redis mất vẫn cứu toàn bộ response đã gửi, còn cần durable journal/snapshot thích hợp; schema hiện tại không cung cấp cam kết đó. Không gọi thêm LLM để lấy history.

Người dùng đã chốt bỏ qua worker crash. Không biến journal/attempt/recovery cũ thành yêu cầu bắt buộc mới; cần nói rõ contract reconnect nào còn được giữ, RPO nào chấp nhận. Việc bỏ bảng run không tự giải quyết việc execution phải sống độc lập với HTTP.

### C. Tiêu đề và If-Match

API cũ yêu cầu conversation revision/If-Match, user rename thắng title job. Bản mới bỏ revision/source theo yêu cầu; do đó không thể triển khai nguyên contract If-Match số revision hay source=user từ tài liệu cũ.

Manual rename vẫn làm được. Auto-title cần conditional update hoặc lifecycle backend được thiết kế rõ để không overwrite sau rename; không tự đưa lại các cột người dùng đã bỏ. Nếu dùng updated_at làm precondition cần chấp nhận xung đột do các cập nhật conversation khác; chưa có bảo đảm đã kiểm chứng cho giải pháp thay thế.

### D. ID công khai, checkpoint và AG-UI invocation

API cũ đồng nhất threadId với conversation/checkpointer. Bản mới dùng checkpoint thread_id = assistant message ID, còn conversation vẫn là danh tính chat/sidebar. Một assistant pause/resume có thể trải qua nhiều wire runId.

Cần mapping rõ `conversation_id -> assistant_message_id -> action_id/checkpoint` và wire invocation hiện tại. Stop phải nhắm đúng message/lượt, không dừng nhầm lượt sau. Proof đã dùng AG-UI thread_id bằng assistant ID để thử saver; chưa chứng minh drop-in compatibility với frontend/API cũ lấy threadId làm conversation. Không bắt buộc có bảng mapping riêng nếu backend thiết kế được binding ổn định, nhưng không dùng lẫn các ID.

### E. Context, nhánh và tìm kiếm

Parent tree đủ correctness cho nhánh và không copy prefix references mỗi regenerate. Index thời gian `(conversation_id, created_at, id)` không tự biến thành keyset paging trên ancestor path.

Bản cũ có branch_item/ordinal và số đo 100.000 item; bản mới chưa có benchmark tương đương. Không kết luận mới nhanh hơn trên chat rất dài. Bắt đầu bằng truy vấn parent đúng nhánh, đo độ sâu/tải thật trước khi cân nhắc materialized path/branch index. Không tự khôi phục position đã bị bỏ.

Cần integration adapter dựng context của lượt mới từ AG-UI bundle, gồm activity user_interaction đã answered như HumanMessage; phần này đã có proof, chưa nối backend. Search title đơn giản có thể dùng SQL, còn tìm kiếm nội dung/tiếng Việt cần chiến lược và index/engine; không suy từ JSONB rằng đã có search.

## 6. Các thay đổi policy có chủ đích

- Chia sẻ **toàn cây**, không chỉ nhánh đang xem. Nhánh cũ có nội dung nhạy cảm cũng thuộc snapshot theo luật mới; giao diện cần mô tả đúng phạm vi này.
- Link org cho active member cùng tổ chức, không giới hạn người nhận/team như đề xuất cũ.
- Copy là chat và byte file mới, tiếp tục tồn tại sau revoke/xóa source. Đó là tính độc lập đã chốt, khác với policy cũ thu hồi quyền source phải chặn mọi derived copy.
- Chưa có document/row ACL. Nếu sau này bật nguồn Finance/HR riêng, luật share cả org và copy độc lập cần được thảo luận cùng quyền phân phối/derived content; metadata file và citation đơn lẻ không giải quyết điều đó.
- Không unread/read state, không live collaboration, không team, không nhiều agent authoring, không usage table nội bộ. Không coi việc thiếu các bảng tương ứng là defect hiện tại.
- Chỉ intentional pause được persist checkpoint, không cố gắng sync mỗi step để recover worker. Giảm write ở normal path của probe nhưng chủ động bỏ mức bảo đảm recovery cũ.

## 7. Những vùng chỉ cần mở khi bật chức năng tương ứng

| Khi bật | Cần thiết kế thêm điều gì |
|---|---|
| RAG/nguồn doanh nghiệp | Resource/version, upstream ACL, dependency của output/share/artifact, quyền search trước model và revalidation |
| Tool ghi như gửi email/tạo ticket | Operation identity, args binding, account thực thi, idempotency/receipt/unknown-result reconciliation; không mặc định mỗi mục phải là một bảng |
| Approval người khác duyệt | Reviewer scope, quyền xem preview, delegation/execution principal, decision policy; không cho reviewer mượn owner identity |
| Memory xuyên chat | Native Store, namespace user/workspace, policy xem/sửa/xóa, provenance/retention |
| Scan/extract file async | Processing state/job, readiness/error/retry; stored_files.metadata là điểm mở rộng, chưa phải implementation |
| Purge/export và audit | Workflow/retry, reference checks, native/S3 cleanup; bằng chứng quyền và action độc lập transcript khi cần |
| Reconnect chống mất Redis hoặc recovery đa worker | Journal/snapshot, durable claim/cancel, fencing/lease và capacity tests theo cam kết thực tế |

Đây là backlog phụ thuộc feature, không là danh sách yêu cầu phải thêm ngay vào database đã chốt.

## 8. Mức chắc chắn của đánh giá

Đã đọc/đối chiếu SQL và tài liệu; dùng kết quả kiểm chứng đã ghi nhận: 122 SQL checks, 27 sync và 30 async/AG-UI. **Không chạy benchmark mới hoặc kiểm thử end-to-end 32 use case** trong lần review này. Các chứng cứ đó không chứng minh backend auth, S3 copy, real LLM/MCP, Redis reconnect, production load hoặc external exactly-once.

Các ví dụ trong folder cũ vẫn là thiết kế/đề xuất ở nhiều nơi, không phải hệ thống cũ đã triển khai. Bản mới có nhiều ràng buộc/luồng được kiểm chứng hơn cho scope đã chọn, còn bản cũ có phân tích enterprise/operation rộng hơn và benchmark branch paging mà bản mới chưa có.

**Khuyến nghị:** giữ schema giai đoạn 1–4 làm baseline hiện tại. Trước khi viết API, thống nhất hợp đồng chống gửi trùng, live reconnect, title và ID mapping; cập nhật tài liệu triển khai đang xung đột với baseline. Chỉ mở lại schema khi một nhu cầu cụ thể chứng minh cần, không nhập toàn bộ catalogue cũ trở lại.
