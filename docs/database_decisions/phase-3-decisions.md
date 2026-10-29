# Giai đoạn 3 — bản chốt: agent cố định, quyền tool/skill và Langfuse

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

Đã thống nhất hướng thiết kế cho phạm vi hiện tại. **Không thêm bảng, cột hoặc migration SQL trong giai đoạn này.** Chưa triển khai backend, đăng ký permission cụ thể, cấp quyền cho role hay cấu hình Langfuse.

## 1. Phạm vi agent, skill và tool

- Hệ thống hiện có **một agent cố định**, sử dụng các skill.
- Agent, instruction, danh mục skill/tool và cấu hình thực thi được quản lý bằng code/cấu hình triển khai.
- Tool chủ yếu do hệ thống xây dựng; có thể gọi dịch vụ qua MCP hoặc tích hợp trực tiếp bằng LangChain.
- Chưa có nhu cầu cho người dùng tự tạo agent, upload skill hoặc tự cấu hình MCP qua giao diện.
- Không tạo các bảng `agents`, `agent_versions`, `agent_tools`, `agent_skills`, `tools`, `skills` hoặc bảng cấu hình MCP trong phạm vi này.

## 2. Định danh chức năng độc lập với cách thực thi

Mỗi tool/skill có key ổn định trong danh mục hệ thống. Key đại diện chức năng; cách thực thi có thể thay đổi mà không đổi quyền.

Ví dụ minh họa, **chưa phải danh sách chức năng đã chốt**:

| Key | Loại | Permission tương ứng |
|---|---|---|
| `web_search` | Tool | resource = `tool_web_search`, action = `execute` |
| `research` | Skill | resource = `skill_research`, action = `use` |

Thay implementation `web_search` từ MCP sang LangChain không đổi key hay permission. Backend ánh xạ tên tool của provider/MCP về key nội bộ đã đăng ký; không coi tên hoặc yêu cầu do model trả về là quyền thực thi.

## 3. Quyền trong workspace tổ chức

Tận dụng RBAC đã có ở giai đoạn 1:

```text
organization_members
  -> member_role_assignments
  -> organization_roles
  -> role_permissions
  -> permissions
```

- Khi triển khai tool/skill cần kiểm soát quyền, đăng ký permission tương ứng bằng dữ liệu; không cần đổi schema.
- Cấp/thu hồi quyền cho role bằng `role_permissions` trong đúng tổ chức.
- Người dùng có nhiều role thì lấy hợp các permission được cấp từ membership, assignment và role đang hoạt động. Tổ chức và tài khoản cũng phải còn hoạt động.
- **Chưa được cấp quyền thì không được dùng.** Không có quyền dùng mọi tool mặc định chỉ vì là Owner/Admin/Superuser.
- Người quản trị chỉ được cấp quyền trong phạm vi được ủy quyền; giữ nguyên các quy tắc chống nâng quyền giai đoạn 1.
- Có thể cấp grant ban đầu có chủ đích khi triển khai chức năng, rồi cho tổ chức điều chỉnh qua luồng quản trị. Chưa chốt grant cho role nào trong tài liệu này.
- Không bổ sung deny override, quyền theo từng user hoặc mô hình global role trong giai đoạn này.

**Danh sách tool/skill bị giới hạn và ma trận Owner/Admin/Member sẽ thiết lập sau.** Hiện chốt cơ chế mở rộng, không seed permission minh họa hoặc tự cấp quyền.

Quyền thực thi tool không cấp thêm quyền đọc dữ liệu. Một tool được phép chạy vẫn phải kiểm tra quyền đối với conversation, file và workspace mà nó truy cập; giữ luật chat riêng tư ở giai đoạn 1–2.

## 4. Workspace cá nhân

- Dùng allowlist tool/skill do hệ thống quản lý trong cấu hình triển khai.
- Không lấy role của một tổ chức để cấp quyền trong workspace cá nhân hoặc tổ chức khác.
- Tool/skill chưa nằm trong allowlist cá nhân thì chưa được dùng ở workspace đó.
- Chưa cần bảng role toàn hệ thống hoặc bảng gán quyền cá nhân.

Danh sách allowlist có thể điều chỉnh khi triển khai sau; không mặc định cho phép toàn bộ tool hiện tại hoặc tương lai.

## 5. Kiểm tra quyền khi chạy agent

Backend thực hiện cả hai bước:

1. Trước khi gọi model, xác định user/workspace và chỉ đưa các tool/skill được phép vào danh sách khả dụng.
2. Trước mỗi lần thực thi tool/skill, kiểm tra lại quyền tại server. Tool bị gọi gián tiếp qua skill, tool hệ thống hoặc MCP đều áp dụng cùng nguyên tắc.

Cho phép dùng một skill **không tự cấp quyền cho các tool bên trong skill**. Nội dung instruction, skill, lịch sử chat hoặc tool output không được dùng để tự nâng quyền. Khi thiếu quyền tool, backend từ chối thực thi và trả kết quả phù hợp cho agent/giao diện.

Luồng kiểm tra khái quát:

```text
User + workspace hiện tại
  -> tổ chức: kiểm tra membership và RBAC
     cá nhân: kiểm tra allowlist hệ thống
  -> lọc tool/skill cho model
  -> model yêu cầu hành động
  -> kiểm tra lại permission và quyền dữ liệu
  -> thực thi tool/skill
```

Cơ chế này là trách nhiệm backend; bảng permission không tự bảo vệ lời gọi tool. Chưa triển khai endpoint quản trị hoặc middleware kiểm tra quyền trong lần ghi nhận này.

## 6. Token, chi phí và Langfuse

- Dùng **Langfuse** để quan sát lời gọi model, token và chi phí.
- Không tạo `model_usage_records`, bảng token hoặc bảng chi phí riêng trong database ứng dụng ở phạm vi hiện tại.
- Không tạo bảng run/attempt/tool execution chỉ để phục vụ tracing. Quyết định này giữ nguyên hướng giai đoạn 2: một lượt trả lời gắn với message assistant.
- Integration cần ghi nhận đúng usage/model và truyền ngữ cảnh tương quan đến các observation liên quan.

Quy ước tích hợp đã đề xuất và được chấp nhận:

| Thuộc tính Langfuse | Giá trị ứng dụng |
|---|---|
| `userId` | `users.id` |
| `sessionId` | `conversations.id` |
| Metadata `message_id` | ID message assistant của lượt trả lời |
| Metadata `workspace_id` | Workspace hiện tại |
| Metadata `organization_id` | ID tổ chức, nếu có |

Đây là thuộc tính gửi sang Langfuse, **không phải cột mới trên `messages` hoặc `conversations`**. Chưa bắt buộc lưu `trace_id` trong database ứng dụng.

Nguồn chính thức đã đối chiếu trong thảo luận: [token và chi phí](https://langfuse.com/docs/observability/features/token-and-cost-tracking), [user tracking](https://langfuse.com/docs/observability/features/users), [sessions](https://langfuse.com/docs/observability/features/sessions).

Thu tiền, trừ hạn mức, gói dịch vụ và sổ giao dịch chưa thuộc phạm vi đã chốt. Nếu xuất hiện nhu cầu đó, thiết kế dữ liệu nghiệp vụ tương ứng riêng; quyết định dùng Langfuse hiện tại phục vụ quan sát/thống kê.

## 7. Vì sao chưa có SQL giai đoạn 3

Không có thay đổi cấu trúc. Các bảng `permissions`, `role_permissions`, `organization_roles`, `member_role_assignments` và `organization_members` đã đáp ứng cơ chế đã chọn.

Chưa có danh sách key và grant thực tế, nên chưa có dữ liệu seed để ghi SQL. Khi triển khai tool/skill cụ thể, bổ sung permission và grant bằng thao tác dữ liệu hoặc seed có kiểm soát; không tự tạo bảng mới để dự phòng.

Chuỗi SQL hiện hành vẫn kết thúc ở `phase-2-final-schema.sql`. Tài liệu này không thay đổi những quyết định về message, file, share/copy hoặc xử lý worker chết đã chốt ở giai đoạn 2.

## 8. Những việc để sau

- Danh mục tool/skill và permission cụ thể.
- Grant ban đầu theo role, allowlist cá nhân và giao diện quản trị nếu cần.
- Tích hợp Langfuse, MCP/LangChain và thực thi kiểm tra quyền ở backend.
- RAG/knowledge, cấu hình model/provider động, nhiều agent hoặc skill do người dùng tạo nếu sản phẩm phát sinh nhu cầu.

Giai đoạn 3 hoàn tất **quyết định thiết kế cho phạm vi hiện tại**, không đồng nghĩa các tích hợp trên đã được triển khai hoặc kiểm thử.
