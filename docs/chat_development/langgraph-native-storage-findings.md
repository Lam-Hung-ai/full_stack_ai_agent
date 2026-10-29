# LangGraph native storage — ghi nhận thực nghiệm và giới hạn

Cập nhật tài liệu: **29/10/2026**. Giữ các quan sát hữu ích về native Saver, đã bỏ phần DDL/catalogue ứng dụng cũ. **Đây không phải nguồn schema sản phẩm.** Database hiện hành: [bản chốt giai đoạn 1–4](database-decisions.md).

## 1. Bảng native do SDK quản lý

PostgresSaver setup tạo **4 bảng**: checkpoints, checkpoint_blobs, checkpoint_writes, checkpoint_migrations. Chúng nằm trong schema langgraph_checkpoints của database hiện hành, không tạo FK ứng dụng vào internal rows.

Các thí nghiệm cũ đo cả PostgresSaver và PostgresStore nên ghi nhận 6 bảng; hai bảng thêm store/store_migrations thuộc long-term memory. Baseline hiện tại chưa bật Store, không cần tạo hai bảng đó.

Scalar có thể inline trong checkpoint JSON; các channel phức tạp như LangChain message objects đi qua blob serializer. Pending writes giữ task/channel/value và interrupt/resume. Không chỉ copy một JSON checkpoint rồi mặc định resume được mọi trường hợp.

SDK không có tham số schema trong constructor đã kiểm tra; set search_path trên chính connection saver. Setup/migrations theo package pin trong deployment, không chạy mỗi request.

## 2. Checkpoint không phải transcript hoặc token journal

Ghi nhận cũ ngày 26/10/2026, LangGraph 1.2.17/checkpoint 4.3.0/Postgres saver 3.2.0: một node sinh 94 ký tự rồi process chết, checkpoint không có phần text đang sinh của node đó dù durability sync. Sync là boundary giữa bước, không phải persist từng token.

Vì vậy:

- Transcript người dùng xem nằm trong messages của ứng dụng.
- Live partial nằm trong accumulator/Redis, cần snapshot/tail nếu muốn reconnect.
- Checkpoint lưu state để resume intentional pause, không thay history hoặc live prefix.
- Worker chết giữa node có thể mất buffer; chưa xử lý auto-recovery theo quyết định hiện tại.

## 3. Durability và chi phí

Thí nghiệm lịch sử từng đo sync nhiều checkpoint hơn exit, và state messages lặp qua nhiều version làm storage lớn hơn transcript. Đây là số đo trên graph/phiên bản cụ thể, không phải benchmark capacity hoặc hệ số chung cho mọi agent.

Hiện đã chốt **buffer trong RAM khi chạy, durability exit và chỉ export khi interrupt**. Chat thường/lỗi trước action không ghi checkpoint bền vững. Không giữ checkpoint mọi bước chỉ để giống thiết kế cũ.

Pending writes của sibling hoàn thành và resume values vẫn phải được giữ. Hai interrupt trong cùng node có thể cập nhật writes trên cùng checkpoint; ID action ứng dụng không đồng nhất checkpoint_id.

## 4. Proof hiện tại

[Code và báo cáo](../experiments/langgraph-action-checkpoints/README.md) pin LangGraph 1.2.16, checkpoint 4.3.0, postgres saver 3.2.0, psycopg 3.3.6; có 27 checks sync và 30 async/AG-UI trên PostgreSQL thật với model mô phỏng.

Đã thử: chỉ persist khi pause, process mới và PostgreSQL restart, question content/response, SDK validation/SSE codec, parallel sibling, atomic rollback, role permission revoke, cancel và concurrent duplicate answer.

Native state/lifecycle được thử không đồng nghĩa public/native thread mapping đã tích hợp vào app: proof dùng assistant ID làm public thread khi thử saver; bản đích dùng public conversation ID và native assistant ID qua adapter.

## 5. Những điều không suy ra từ kết quả

- Không có bảo đảm async/subgraph/DeltaChannel tổng quát chỉ từ root-graph proof.
- Node có interrupt có thể chạy lại từ đầu; side effect đặt trước interrupt có thể lặp.
- Checkpoint tồn tại không cấp quyền resume hoặc dùng tool; backend phải revalidate.
- Native Store không tự tạo memory policy hoặc source ACL.
- Shared PostgreSQL không tự làm mọi workflow atomic; intentional pause đã thử cùng connection/transaction, còn toàn bộ streaming/provider không nằm trong transaction đó.
- Chưa có cleanup, graph migration, HTTP/Redis/provider end-to-end hoặc multi-pod load test.

Không dùng schema app/run/attempt/outbox/branch từ các thí nghiệm lịch sử. Xem [database đã chốt](database-decisions.md) và [quy ước ID](conversation-message-run-id-decisions.md).
