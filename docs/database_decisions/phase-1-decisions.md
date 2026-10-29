# Chốt database giai đoạn 1 — tài khoản, tổ chức, phân quyền và chia sẻ

Ngày chốt: **28/10/2026** (Asia/Ho_Chi_Minh).

Trạng thái: quyết định sản phẩm đã được người dùng đồng ý trong cuộc thảo luận; SQL là bản nền triển khai các quyết định này. Chưa áp dụng vào database của ứng dụng, chưa tích hợp backend và chưa xác nhận sẵn sàng production.

## 1. Phạm vi và các file

- [`phase-1-schema.sql`](phase-1-schema.sql): DDL cho PostgreSQL 18+, gồm 23 bảng trong schema `chat_app`, index, FK, trigger, hàm kiểm tra quyền và seed permission.
- [`phase-1-checks.sql`](phase-1-checks.sql): kiểm tra trên database tạm sau khi áp dụng DDL; dữ liệu kiểm tra được rollback.
- Tài liệu này: quyết định đã chốt, giải thích thiết kế và những trách nhiệm backend phải triển khai.

Phần được chốt là danh tính, không gian cá nhân/tổ chức, RBAC tổ chức, chia sẻ snapshot và sao chép conversation/file. Conversation, message và file trong SQL là nền tối thiểu phục vụ các luồng này. Cấu trúc run, tool, agent version, streaming, checkpoint, billing và RAG sẽ được thảo luận tiếp; không coi bản này là toàn bộ database sản phẩm.

DDL được viết cho database mới, chạy một lần trong transaction; không phải script đồng bộ schema, không chạy lại bằng `IF NOT EXISTS` cho mọi bảng để che khác biệt cấu trúc. Thay đổi tiếp theo cần migration có phiên bản. Không khôi phục hoặc sửa các tài liệu cũ đang bị xóa trong working tree.

## 2. Nguồn và bài học kế thừa

- File người dùng cung cấp: `/home/lamhung/Downloads/user_organizaion.sql`. Giữ hướng `users`, `user_accounts`, refresh token hash, verification, thành viên, role, permission và nhiều role/thành viên.
- [Kiến trúc dự án](../agent-chat-architecture.md): PostgreSQL là nơi lưu dữ liệu bền vững; execution và streaming có vòng đời riêng. Đầu tài liệu ghi rõ một phần nội dung là lịch sử; những file API/kiến trúc mới được dẫn tới hiện không có trong checkout, nên bản này không tự chốt lại contract SSE.
- [LibreChat schema](../database_research/librechat-full-schema.md): tenant isolation, tách phiên và credential, file đi kèm bản chia sẻ, retry/lease và idempotency. Giữ FK thật thay vì sao chép giới hạn MongoDB.
- [Open WebUI schema](../database_research/open-webui-official-schema.md): snapshot chia sẻ tách khỏi conversation gốc, phân biệt quyền quản trị với quyền tài nguyên.
- Đã đối chiếu source share: LibreChat `packages/data-schemas/src/methods/share.ts`; Open WebUI `models/shared_chats.py`, `routers/chats.py`, `utils/access_control/files.py` trong hai checkout cục bộ.

Không sao chép nguyên: LibreChat dùng tham chiếu message và thuật toán giới hạn theo tầng cây, không phải snapshot nội dung bất biến một nhánh; Open WebUI còn có đường `continue` đọc chat live khi có quyền ghi. Dự án mình chốt snapshot bất biến của toàn bộ cây message và copy độc lập để chat tiếp.

## 3. Tài khoản và đăng nhập

1. Một tài khoản toàn hệ thống; cùng user có thể tham gia nhiều tổ chức.
2. `users` chứa hồ sơ; `user_accounts` chứa phương thức đăng nhập. Một user có thể liên kết nhiều provider; không tự liên kết chỉ vì trùng email.
3. Email chính duy nhất không phân biệt hoa thường bằng `citext`, không cho khoảng trắng đầu/cuối. Backend vẫn phải kiểm tra định dạng và quy trình xác minh email.
4. Hỗ trợ credential và provider bên ngoài theo hướng file gốc. Credential lưu password hash, không lưu mật khẩu thô. Một user tối đa một credential account.
5. `provider_id` xác định cấu hình provider/issuer; hai SSO issuer khác nhau không được dùng chung namespace account ID một cách mơ hồ.
6. Access/refresh/ID token của provider lưu ciphertext; refresh token phiên ứng dụng và token verification lưu hash. Đây là hai lớp token khác nhau.
7. Phiên đăng nhập toàn hệ thống; `refresh_tokens` không gắn organization. Chuyển workspace không cần đăng nhập lại; membership và trạng thái tổ chức được kiểm tra ở từng yêu cầu.
8. `family_id`, `consumed_at`, `revoked_at` hỗ trợ rotation/reuse detection. Không coi có các cột này là đã triển khai giao thức rotation.
9. Verification email/reset password có hạn dùng và dùng một lần. `identifier` không FK tới user vì xác minh có thể tồn tại trước tài khoản hoặc trước khi thay email.
10. `is_superuser` dành cho quản trị nền tảng, không cấp quyền mặc định đọc chat/file riêng.

Tinh chỉnh so với file đầu vào: `password` đổi thành `password_hash`; token provider đổi tên `*_ciphertext`; `verifications.value` thành `token_hash`; bỏ `refresh_tokens.organization_id`; bỏ `notification_digest_on` vì chưa có luồng thông báo; avatar dùng `avatar_url`, chưa gắn với kho file chat theo workspace. Những tên này phải được ánh xạ rõ nếu sau này chọn thư viện auth.

## 4. Workspace và tổ chức

- Mỗi user có đúng một workspace cá nhân; mỗi tổ chức có đúng một workspace tổ chức ở giai đoạn 1.
- Trigger tạo workspace khi tạo user/tổ chức; unique chống cấp trùng. Backend không cho xóa workspace riêng lẻ hoặc sửa loại/chủ thể workspace. SQL chặn sửa loại/chủ thể; không tự cung cấp API xóa.
- `workspaces` thuộc đúng một user cá nhân hoặc một organization (CHECK XOR).
- Conversation/file thuộc một workspace, owner là user. SQL chặn liên kết attachment chéo workspace.
- Không chuyển conversation hoặc copy chia sẻ giữa cá nhân và tổ chức, hoặc giữa hai tổ chức.
- Không có `organization_units`, `scope_unit_id`, cây phòng ban hay scope đơn vị.
- Một user có tối đa một membership trong mỗi tổ chức. Trạng thái inactive giữ lại danh tính membership và lịch sử.
- Rời hoặc bị khóa khỏi tổ chức mất truy cập tổ chức, kể cả share đã nhận; không ảnh hưởng không gian cá nhân.
- Dữ liệu vẫn ở workspace tổ chức. Owner/Admin không tự có quyền đọc dữ liệu đó. Giai đoạn 1 không tự chuyển chủ chat cho Admin.

## 5. Role, permission và giới hạn quyền

Giữ RBAC theo file gốc:

```text
organization_members -> member_role_assignments -> organization_roles
                                                    |
                                              role_permissions
                                                    |
                                                permissions
```

- Một thành viên có thể có nhiều role; grant hiệu lực là hợp permission từ assignment và role đang active.
- Assignment có composite FK đảm bảo member và role cùng tổ chức.
- Tự seed `owner`, `admin`, `member` cho tổ chức mới; người tạo là thành viên và được gán owner.
- Seed quyền quản lý organization/member/role và quyền tạo/chia sẻ conversation. Owner/Admin có các quyền này; Member có quyền tạo/chia sẻ chat của mình.
- Không seed quyền `read_all_chats`, không bypass riêng tư cho Owner/Admin/Superuser.
- Quyền tổ chức không thay thế sở hữu chat: `conversation.share` chỉ cho phép chủ chat xuất bản chat của chính mình.
- Backend phải kiểm soát chống nâng quyền: Admin không được tự gán owner, sửa quyền bảo vệ owner hoặc nâng vai trò vượt quyền được ủy quyền. `role.manage` không phải quyền bỏ qua các quy tắc này.
- Luôn giữ ít nhất một membership owner active. SQL dùng advisory lock theo tổ chức và deferred constraint trigger trên membership/role/assignment; chuyển owner thực hiện trong một transaction. Trạng thái active ở đây là membership + assignment + role. Trước khi khóa tài khoản toàn hệ thống của owner cuối cùng, backend phải chuyển owner hoặc xử lý tổ chức theo quy trình quản trị riêng.
- Trigger owner được thiết kế cho transaction `READ COMMITTED`; luồng nhiều tổ chức cần khóa theo thứ tự cố định, xử lý deadlock/retry. Nếu dùng isolation khác phải kiểm chứng lại, không tự suy ra bảo đảm tương đương.

## 6. Lời mời tổ chức

- Gia nhập qua lời mời theo email, có token hash và hạn dùng.
- Người chấp nhận phải đăng nhập, tài khoản active và email đã xác minh khớp lời mời.
- Trong cùng transaction: khóa invitation, kiểm tra pending/chưa hết hạn, tạo hoặc kích hoạt membership, gán role Member, đánh dấu accepted và ghi người nhận.
- Unique cho một lời mời pending mỗi `(organization_id, email)`. Trước khi mời lại cần đánh dấu lời mời cũ expired/revoked; thời gian không tự thay đổi trạng thái dòng.
- Thu hồi hoặc hết hạn invitation không tự xóa membership đã được chấp nhận.

## 7. Riêng tư và chia sẻ

### 7.1. Mặc định riêng tư

Conversation chỉ chủ sở hữu đọc trực tiếp; thành viên cùng workspace không tự có quyền. Người nhận share đọc bản snapshot, không đọc conversation live.

### 7.2. Workspace cá nhân

- Chia sẻ công khai qua link; người ngoài không cần tài khoản để xem và tải file trong snapshot.
- Link là bearer capability: người có link có thể gửi link cho người khác. Không hứa kiểm soát người nhận cụ thể cho public link.
- Token URL phải sinh ngẫu nhiên mật mã đủ mạnh; DB chỉ lưu SHA-256. UUID nội bộ không thay cho bí mật của link. Backend phải xác thực link token trước khi gọi các hàm quyền.
- Muốn chat tiếp phải đăng nhập; bản sao chỉ được tạo trong workspace cá nhân của người sao chép.
- Người có membership tổ chức vẫn có thể xem public link như người ngoài, nhưng không copy chat cá nhân vào workspace tổ chức.

### 7.3. Workspace tổ chức

- Chỉ chia sẻ nội bộ cùng tổ chức; không có public link cho chat tổ chức.
- Mọi thành viên active của cùng tổ chức có link đều xem/tải được. Không chọn danh sách người nhận riêng ở giai đoạn 1.
- Owner/Admin cũng phải có link và membership phù hợp; không có đặc quyền đọc mọi chat gốc.
- Copy để chat tiếp chỉ vào cùng workspace tổ chức; người copy là chủ conversation mới, bản sao mặc định riêng tư.
- Thành viên rời tổ chức mất truy cập. Khi người tạo share rời tổ chức, các share họ tạo bị thu hồi vĩnh viễn; tham gia lại không tự mở lại. Có trigger cho cả inactive và xóa membership.

## 8. Nội dung snapshot

1. Chia sẻ toàn bộ cây message hiện có, gồm mọi nhánh regenerate/sửa câu hỏi; giữ con trỏ message hiện tại để mở đúng nhánh.
2. Snapshot chứa title, nội dung message và file đính kèm tương ứng tại thời điểm xuất bản. Không công bố secret, system prompt nội bộ, credential hay cấu hình vận hành chỉ vì chúng có trong runtime.
3. Phần message/file SQL này là dữ liệu sản phẩm được phép render. Backend phải lọc nội dung trước khi snapshot; không copy thẳng checkpoint/runtime state. Phạm vi toàn bộ cây chỉ bao gồm transcript được phép chia sẻ.
4. Snapshot lưu payload riêng, không trỏ live message làm nguồn nội dung. Sửa hoặc chat tiếp ở conversation gốc không thay snapshot.
5. Snapshot có version. Backend tạo version mới rồi đổi `current_snapshot_id`, giữ link cũ; các bản copy đã tạo không đổi.
6. `sealed_at` đánh dấu bất biến. Các trigger chặn sửa/xóa header và content đã seal, chặn publish snapshot chưa seal.
7. Bản snapshot cũ được giữ để copy job đang chạy bám đúng version. Chưa chốt thời hạn purge; baseline không cho xóa tùy tiện snapshot đã seal. Cần migration/quy trình retention có đặc quyền trước khi chạy production lâu dài.
8. File snapshot tham chiếu một phiên bản blob bất biến, không phải file có thể ghi đè. FK giữ bản ghi, trigger giữ metadata/storage key; storage phải cấm overwrite. FK không thể giữ byte nếu worker/storage xóa ngoài DB.
9. Nếu có file chưa ready, chưa được xuất bản snapshot thiếu file; cần chờ hoàn tất hoặc báo không thể chia sẻ. Message đang stream cần lấy baseline nhất quán/đợi boundary, không dùng suffix Redis thiếu prefix.

Snapshot là một tài liệu xuất bản có chủ đích, không phải store transcript thứ hai cần dual-write mỗi lượt chat.

## 9. Copy để chat tiếp

- Tạo conversation mới, message ID mới, file ID mới và storage key mới. Sao chép byte file thật, không chỉ dùng lại đường dẫn file của người gốc.
- Giữ nội dung, thứ tự, quan hệ cha–con, nhánh đang chọn, tên file và liên kết message–file. Có thể giữ thời điểm gốc ở metadata hiển thị khi bổ sung sau; ID và thời điểm tạo bản sao thuộc đối tượng mới.
- Lịch sử đã copy không biến tất cả message thành lời người nhận; role user/assistant/tool được giữ. Ownership conversation và file thuộc người copy.
- Không copy run đang chạy, lease, checkpoint, sandbox session, tool approval, token hay credential. Run tiếp theo dùng quyền/cấu hình khả dụng của người copy; không hứa tái tạo runtime gốc.
- Copy job cố định một snapshot version, idempotent theo `(requested_by, client_request_id)`. Cùng key nhưng payload khác phải bị backend từ chối; không dùng `ON CONFLICT` để nhận âm thầm.
- Tạo đích ở trạng thái `copying`; chỉ cho đọc/chat như bản hoàn chỉnh khi toàn bộ transcript và file sẵn sàng.
- Copy blob bất đồng bộ có lease/token, retry deadline và mapping file. Worker phải dùng token điều kiện khi ghi để chặn worker mất lease; có cột lease chưa có nghĩa worker đã thực thi fencing.
- Khi hoàn tất, SQL kiểm tra mọi file snapshot có mapping copied và conversation đích ready. Backend còn phải xác nhận byte/checksum, toàn bộ message và quan hệ nhánh/link đúng, rồi finalize trong cùng transaction.
- Thu hồi share hoặc mất membership trong lúc copy: không cho hoàn tất một job chưa completed; worker kiểm tra lại dưới khóa khi finalize. Tác vụ dở phải cleanup có retry. Bản copy completed trước lúc thu hồi vẫn tồn tại độc lập.
- Người copy có thể chia sẻ lại bản sao theo luật workspace tương ứng. Không thể thu hồi những byte đã được tải xuống.

## 10. Xóa, thu hồi và retention

- Xóa conversation gốc ở giai đoạn 1 là soft-delete, thu hồi mọi share của nó. Không phục hồi share khi undelete.
- Thu hồi share chặn xem/tải/copy mới. File tải bằng signed URL có thể còn hoạt động tới khi URL hết hạn; dùng URL ngắn hạn hoặc proxy nếu cần thu hồi ngay.
- Bản copy completed và blob riêng không bị xóa khi xóa chat gốc/thu hồi link.
- Giai đoạn 1 không cung cấp hard-delete tài khoản/tổ chức/chat đang được lịch sử tham chiếu. FK RESTRICT giữ dữ liệu; phải xây quy trình purge trước khi cung cấp tính năng xóa vĩnh viễn.
- Xóa byte ngoài DB phải kiểm tra mọi tham chiếu live/snapshot/job còn cần; không chỉ dựa vào chat gốc.
- Không dùng `ON DELETE CASCADE` như thay thế cho cleanup blob/sandbox/vector bên ngoài database.

## 11. Danh mục 23 bảng

| Module | Bảng |
|---|---|
| Tài khoản và xác thực | `users`, `user_accounts`, `refresh_tokens`, `verifications` |
| Tổ chức và không gian | `organizations`, `workspaces`, `organization_members`, `organization_invitations` |
| RBAC | `permissions`, `organization_roles`, `role_permissions`, `member_role_assignments` |
| Nền hội thoại và file | `conversations`, `messages`, `files`, `message_files` |
| Chia sẻ snapshot | `conversation_shares`, `share_snapshots`, `share_snapshot_messages`, `share_snapshot_files`, `share_snapshot_message_files` |
| Copy độc lập | `conversation_copy_jobs`, `conversation_copy_files` |

## 12. Database bảo vệ gì, backend phải làm gì

| Nội dung | Database | Backend/storage |
|---|---|---|
| Email/provider identity duy nhất | UNIQUE/index | Verify, normalize, liên kết danh tính an toàn |
| Token/password | Cột hash/ciphertext, check cơ bản | Hash/mã hóa, key management, rotation, single-use, hết hạn |
| Workspace | XOR, unique, tự cấp, cấm đổi scope | Không cho xóa workspace riêng lẻ; chọn context theo request |
| Role cùng tổ chức | Composite FK | Authz người gán, chống nâng quyền, owner transfer |
| Chủ chat/file thuộc workspace | Trigger khi tạo | Kiểm tra user active, quyền tính năng và membership tại từng request |
| Chat riêng | Hàm `can_read_conversation` không có admin bypass | Bắt buộc dùng đúng predicate trên mọi endpoint, kể cả tìm kiếm/export |
| Download file | Hàm `can_read_share_file` / `can_read_conversation_file` | Xác thực token/session, không lộ storage key, không dùng URL công khai lâu dài |
| Snapshot bất biến | Seal trigger, FK, tree constraints | Đọc snapshot nhất quán, copy đủ cây/file, lọc runtime secrets |
| Copy đúng scope/file | Trigger, unique request key, file mapping | Copy byte, remap IDs, chống retry trùng, kiểm tra quyền khi finalize |
| Last owner | Lock + deferred trigger | Kiểm soát khóa user toàn hệ thống, isolation/retry |
| Policy | Chốt ranh giới public/internal | Chưa có policy engine tùy biến hoặc bảng cấu hình kế thừa |

**Quan trọng:** bản này chưa bật RLS và không tạo DB role runtime. Các hàm quyền không phải SECURITY DEFINER, không tự xác thực người gọi và không thay thế endpoint authorization. Client không được kết nối trực tiếp tới bảng. Service phải dùng DB role riêng với quyền tối thiểu; quản lý quyền DB/RLS sẽ cần thiết kế và kiểm thử khi tích hợp backend. Không tuyên bố SQL này tự ngăn mọi query do backend viết sai.

`can_read_share` chỉ xác định điều kiện truy cập sau khi service đã giải quyết link token. Việc biết UUID share nội bộ không đủ thay cho bước kiểm tra link. File download phải gắn với đúng share/snapshot hoặc conversation; không cho phép tải chỉ bằng UUID file.

## 13. Luồng transaction bắt buộc

### Xuất bản/cập nhật share

1. Xác thực user và quyền share, khóa conversation và share theo thứ tự nhất quán.
2. Đọc toàn bộ cây + file trong một baseline nhất quán; mọi writer conversation phải tuân theo cùng giao thức khóa hoặc dùng isolation/retry phù hợp.
3. Tạo snapshot mới chưa seal, remap message ID và file links; chỉ dùng file ready.
4. Kiểm tra completeness/sanitization, set current message, seal, đổi con trỏ snapshot của link, commit.
5. Xuất bản link sau commit. Không phát link tới snapshot xây dở.

### Copy

1. Xác thực link + user, khóa share và kiểm tra membership, xác định current snapshot.
2. Trong transaction tạo target copying, job và toàn bộ message tree đã remap; lưu mapping file mới với storage key riêng để retry dùng lại.
3. Worker claim job nguyên tử, copy byte và xác minh checksum; chỉ ghi kết quả với lease token còn hiệu lực.
4. Trước finalize: khóa share/membership/job, kiểm tra lại quyền và scope, kiểm tra transcript/files đầy đủ; đặt target ready + job completed trong một transaction.
5. Job thất bại/thu hồi thì không lộ conversation dở; reconcile/cleanup file pending với deadline. Không dùng một cờ có thể kẹt vô hạn.

## 14. Cách kiểm tra

Yêu cầu PostgreSQL 18+ và extension `citext` có sẵn. `uuidv7()` là hàm có sẵn trong PostgreSQL 18; không giả định PostgreSQL 17 chạy được file này nguyên trạng.

Trên **database thử nghiệm mới** do bạn chủ động tạo:

```bash
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-1-checks.sql
```

Đã thực sự áp dụng DDL và chạy 28 kiểm tra trên PostgreSQL 18.6, cluster tạm độc lập, không kết nối database ứng dụng. Thử nghiệm bổ sung bằng hai phiên đồng thời gỡ hai owner: lần gỡ thứ hai bị từ chối, còn lại một owner active. Cluster tạm được dừng và dọn sau kiểm tra. Checks xác nhận: email unique, tự cấp workspace/role, bảo vệ owner cuối cùng, role/file/current-message không chéo scope, cây không chu trình, snapshot seal, riêng tư, public/internal access, copy idempotency và độc lập với xóa nguồn, thu hồi khi rời tổ chức.

Chưa kiểm thử auth HTTP, copy object storage thật, migration dữ liệu có sẵn, tải đồng thời production, Redis, executor hoặc checkpointer. Kiểm thử SQL không thay thế các kiểm thử tích hợp này.
