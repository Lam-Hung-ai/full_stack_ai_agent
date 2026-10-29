# Tài liệu phát triển chat

Cập nhật: **29/10/2026**. Backend FastAPI + LangGraph OSS + LangGraphAgent/EventEncoder, frontend AG-UI hiện có. Không dùng CopilotKit runtime/SDK; source CopilotKit chỉ để tham khảo API.

## Quyết định hiện hành

- [Database đã chốt giai đoạn 1–4](database-decisions.md): **điểm vào chính** cho identity/workspace/quyền, conversation/message, file/share/copy và checkpoint. SQL gốc ở [database_decisions](../database_decisions/README.md).
- [Quy ước conversation/message/run ID](conversation-message-run-id-decisions.md): public thread là conversation, native checkpoint thread là assistant message, ID ứng dụng UUIDv7, runId chỉ ở protocol và stop theo assistant message.
- [Kiến trúc chat hiện hành](agent-chat-architecture.md): PostgreSQL/Redis/worker/SSE theo phạm vi đã chốt và giới hạn vận hành.
- [Lưu trữ và scale theo database mới](production-data-storage-design.md): áp dụng nguồn LangChain đã đọc lại cho PostgreSQL/Redis/worker/S3; phân biệt baseline và đề xuất vận hành.
- [API contract đã chốt](chat-agent-api-contract.md): input nghiệp vụ riêng, gửi/edit/regenerate/resume, connect không cursor và stop; tạm bỏ requestId/Idempotency-Key.
- [ChatAgent kế thừa HttpAgent](chat-agent-client-decisions.md): tái sử dụng HTTP/SSE, pipeline events và subscriber của SDK AG-UI.
- [32 use case và quyền tổ chức](chat-use-cases-and-organization-access.md): phân biệt hiện tại, backend cần hoàn thiện và feature để sau; không là catalogue bảng bắt buộc.

Đã xóa DDL/catalogue database cũ và các đoạn mâu thuẫn. Không còn một baseline schema thứ hai trong thư mục này. Các SQL từng giai đoạn trong database_decisions giữ nguyên làm lịch sử và dependency áp dụng; đọc cấu trúc cuối sau toàn chuỗi.

## LangGraph và AG-UI

- [Tham khảo API CopilotKit, dùng LangGraphAgent](copilotkit-agui-integration.md): ranh giới wrapper/worker/gateway, không thêm package CopilotKit.
- [Manual wiring endpoint](ag-ui-manual-wiring.md): snippet endpoint hiện tại và lý do kiểm soát auth/lifecycle bằng route custom.
- [Native storage findings](langgraph-native-storage-findings.md): các quan sát Saver/Store/checkpoint, không phải DDL sản phẩm.
- [Proof checkpoint sync/async](../experiments/langgraph-action-checkpoints/README.md): code tái lập và kết quả kiểm tra với database tạm/model mô phỏng.
- [Khảo sát các dự án](../database_research/README.md): nguồn nghiên cứu, không thay quyết định sản phẩm hiện hành.

## Kinh nghiệm frontend

- [Reasoning có dữ liệu nhưng không hiển thị](reasoning-render-gap-bug.md).
- [Dòng tóm tắt reasoning sống](live-reasoning-summary.md).
- [Gộp cập nhật stream theo requestAnimationFrame](raf-batched-reasoning-updates.md).
- [Hiển thị công thức toán](math-rendering.md).

Các ghi chú UI được giữ nguyên. Database và proof đã kiểm tra không có nghĩa backend auth, Redis reconnect, real LLM/MCP/S3, activity renderer hoặc production load đã được triển khai.
