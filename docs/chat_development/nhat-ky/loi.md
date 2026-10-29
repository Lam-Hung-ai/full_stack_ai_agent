# Nhật ký lỗi

Ghi mọi lỗi của dự án phát triển chat: phát hiện khi rà soát, khi làm, khi kiểm thử hay sau phát hành. Luật ghi và mức độ xem ở [README](./README.md).

Lỗi ở đây là **hành vi sai** so với quyết định đã chốt (database, ID, API, ChatAgent) hoặc tài liệu tự mâu thuẫn. Chức năng **chưa làm** (route chưa có, scaffold hiện tại chưa theo thiết kế đích) là phạm vi của sprint, không ghi thành lỗi.

## Bảng tổng hợp

| Mã | Mức | Tóm tắt | Phát hiện | Xác minh | Sửa ở | Trạng thái |
| --- | --- | --- | --- | --- | --- | --- |
| L-01 | Thấp | Use case C04 ghi backend chuyển tín hiệu stop theo `messageId + runId`; mục 5 còn "API dedupe" | Rà tài liệu 29/10 | Đã xác minh | TD-001 | Đã sửa |

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
