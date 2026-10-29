# Giai đoạn 4 — bản chốt: checkpoint LangGraph và chờ người dùng

Ngày chốt: **29/10/2026**, Asia/Ho_Chi_Minh.

Chốt sau khi kiểm chứng graph sync và async/AG-UI trên PostgreSQL tạm. Tài liệu này bổ sung giai đoạn 1–3 và thay thế phần status/thời điểm lưu message liên quan đến pause ở giai đoạn 2. Chưa áp dụng vào database hoặc backend ứng dụng.

## 1. Quyết định chính

- Checkpoint phục vụ **chờ duyệt tool hoặc hỏi người dùng**, không dùng làm nguồn lịch sử hội thoại giữa các lượt chat thường.
- Không tạo bảng `message_pending_actions`, `conversation_runs` hoặc `run_attempts`.
- Thêm `messages.metadata JSONB NOT NULL DEFAULT '{}'` và status `requires_action`.
- Lưu action đang chờ và checkpoint pointer trong metadata của chính message assistant.
- Lưu cả phần nội dung đã sinh khi pause; mở lại trang không cần model sinh lại câu hỏi.
- Chỉ export checkpoint/pending writes xuống PostgreSQL khi có interrupt. Chat hoàn tất bình thường hoặc lỗi trước action không ghi checkpoint bền vững.
- Yêu cầu chờ mặc định không tự hết hạn: `expires_at = null`. Không giữ request/worker ở trạng thái chờ người dùng.
- Câu trả lời bổ sung nằm trong cùng message assistant dưới dạng AG-UI activity có ghi rõ người trả lời; không tạo SQL message user riêng.
- Không thay quyết định chưa tự khôi phục worker chết giữa quá trình đang chạy.

## 2. File SQL và thứ tự áp dụng

`phase-4-schema.sql` chạy **một lần sau** `phase-2-final-schema.sql`. Giai đoạn 3 không có SQL.

```bash
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-part-1-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-2-final-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-4-schema.sql
psql -X -v ON_ERROR_STOP=1 --dbname=agent_chat_scratch -f docs/database_decisions/phase-4-checks.sql
```

Các bước phase 2 vẫn có preflight database thiết kế/scratch, không phải migration backfill production. Phase 4 là thay đổi bổ sung; không tự chuyển metadata/payload cũ, không tự cấp quyền tool hoặc triển khai runtime. Checks tại mốc cũ chạy trước bước schema mới tương ứng, theo README.

## 3. Thay đổi messages

| Cột | Quyết định |
|---|---|
| `status` | `pending`, `running`, **`requires_action`**, `completed`, `failed`, `cancelled` |
| `metadata` | JSONB, NOT NULL, default `{}`, CHECK phải là object |
| `content`, `attachments` | Giữ cấu trúc đã chốt; thêm mốc lưu khi pause |

User message sau commit vẫn luôn completed. Chỉ assistant có thể requires_action. Trạng thái mới chưa terminal; các luật terminal bất biến giai đoạn 2 tiếp tục áp dụng cho content, attachments, metadata và liên kết file.

```text
pending -> running -> requires_action -> running -> completed
               |             |             +----> failed
               |             +------------------> cancelled
               +--------------------------------> failed/cancelled
```

Một message có thể pause/resume nhiều lần. Mỗi lần chờ mới có action_id mới. Một assistant requires_action vẫn chiếm chỗ active: index một assistant active/conversation bao gồm pending/running/requires_action.

Không nhận lượt assistant mới trong cùng conversation khi action chưa được trả lời hoặc hủy. Không tạo/cập nhật/publish snapshot mới lúc chờ. Snapshot đã publish từ trước vẫn xem được; copy job không được completed khi conversation đích còn message requires_action.

Không thêm GIN index metadata khi chưa có truy vấn cụ thể; hiện lookup action qua message/conversation và index đã có.

## 4. metadata của message

Ví dụ minh họa, cấu trúc do backend quản lý:

```json
{
  "pending_action": {
    "action_id": "uuid-action",
    "state": "waiting",
    "graph_version": "graph-v1",
    "expires_at": null,
    "checkpoint": {
      "thread_id": "uuid-assistant-message",
      "checkpoint_ns": "",
      "checkpoint_id": "langgraph-checkpoint-id"
    },
    "interrupts": [
      {
        "interrupt_id": "langgraph-interrupt-id",
        "payload": {
          "kind": "user_question",
          "question": "Bạn muốn xuất CSV hay Excel?",
          "question_message_id": "agui-question-message-id"
        }
      }
    ]
  },
  "actions": []
}
```

- `action_id` định danh yêu cầu ứng dụng; không đồng nhất với interrupt_id, message_id hay checkpoint_id.
- Tool approval dùng payload tool_name/tool_call_id/arguments thay vì câu hỏi. Người dùng chỉ gửi quyết định, không tùy ý đổi tool/arguments đang chờ.
- `state` waiting/resuming mô tả action, không thêm status message khác.
- `actions` giữ các response/decision đã giải quyết cùng actor_id; không phải audit log bất biến độc lập. Không lưu toàn bộ checkpoint hoặc secret vào metadata.
- Backend validate hợp đồng metadata và giá trị response. SQL chỉ kiểm tra object; không chứng minh pointer hợp lệ hoặc yêu cầu đang chờ có payload đầy đủ.
- Client không được tùy ý ghi metadata, chọn checkpoint thread hoặc tự chuyển status.
- Khi hoàn tất/hủy, bỏ pending_action. Nội dung/response đã lưu vẫn được giữ.

## 5. Câu hỏi và câu trả lời trong content

Cột role SQL vẫn chỉ user/assistant. Bundle của message assistant không thêm role user; dùng AG-UI **ActivityMessage** loại ứng dụng `user_interaction` để ghi nhận người dùng trả lời.

```json
[
  {
    "id": "question-id",
    "role": "assistant",
    "content": "Bạn muốn xuất CSV hay Excel?"
  },
  {
    "id": "interaction:action-id",
    "role": "activity",
    "activityType": "user_interaction",
    "content": {
      "action_id": "action-id",
      "kind": "user_question",
      "status": "answered",
      "question_message_id": "question-id",
      "response": "CSV",
      "actor_id": "user-id"
    }
  },
  {
    "id": "continuation-id",
    "role": "assistant",
    "content": "Tôi sẽ xuất kết quả dưới dạng CSV."
  }
]
```

- Khi mới pause, activity có status waiting; khi trả lời cập nhật answered; khi hủy cập nhật cancelled. Đây là status trong contract activity, không phải status SQL message.
- Câu hỏi do LLM sinh được giữ nguyên trong content. Nếu câu hỏi chỉ có trong interrupt payload thì backend phải bổ sung phần hiển thị theo cùng contract; không nối lại text nếu đã có. Thử nghiệm async đã kiểm chứng đường câu hỏi do model mô phỏng sinh.
- Giao diện render response là lời người dùng thông qua actor_id/activity, không trình bày như lời assistant. Cần renderer cho activityType này; chưa có UI được triển khai.
- Khi resume, response được đưa vào context graph như HumanMessage nội bộ. Khi dựng context lượt chat mới từ lịch sử, ánh xạ activity answered/user_question sang HumanMessage đúng thứ tự, đúng một lần; không cộng lại response từ metadata.actions.
- Pending/cancelled activity và widget approval không tự biến thành instruction cho model. Tool-call/result giữ cấu trúc AG-UI đã chốt.
- Merge theo ID ổn định, giữ thứ tự câu hỏi → response → phần trả lời tiếp; không nối lặp nội dung khi nhận snapshot stream hoặc reload.

## 6. Checkpoint lưu ở đâu và khi nào

Tách schema kỹ thuật **`langgraph_checkpoints`**, không trộn vào bảng message:

| Bảng do SDK quản lý | Vai trò |
|---|---|
| `checkpoints` | State/checkpoint boundary và metadata runtime |
| `checkpoint_blobs` | Channel values được serializer tách thành blob |
| `checkpoint_writes` | Pending writes theo task, gồm interrupt/resume và kết quả node đã hoàn thành |
| `checkpoint_migrations` | Phiên bản cấu trúc lưu của SDK |

Không chuyển nguyên hai collection MongoDB của LibreChat thành hai bảng tùy ý. SQL giai đoạn 4 chỉ tạo schema; **saver SDK đã pin tạo/migrate bốn bảng qua setup()**. Không chép DDL thư viện vào application migration để rồi lệch khi nâng package.

Ví dụ bootstrap đồng bộ, `conninfo` do môi trường triển khai cung cấp:

```python
import psycopg
from psycopg.rows import dict_row
from langgraph.checkpoint.postgres import PostgresSaver

with psycopg.connect(
    conninfo,
    autocommit=True,
    row_factory=dict_row,
    prepare_threshold=0,
    options="-csearch_path=langgraph_checkpoints,public",
) as conn:
    PostgresSaver(conn).setup()
```

Đường async dùng AsyncPostgresSaver. Kết nối runtime saver dùng cùng schema/search_path; các truy vấn ứng dụng dùng `chat_app` tường minh. Không expose các bảng checkpoint cho client; checkpoint có thể chứa state nội bộ không được hiển thị.

Quy ước thread_id là ID message assistant, tạo bởi server. Mỗi câu trả lời có phạm vi riêng; regenerate tạo ID mới. `checkpoint_ns` giữ ý nghĩa namespace của root/subgraph, không lấy chuỗi bất kỳ từ client để làm quyền.

### Chỉ lưu khi pause

1. Trong thời gian graph chạy, buffer checkpoint/writes trong RAM của invocation.
2. Chạy graph với durability exit trong phạm vi đã kiểm chứng.
3. Hoàn tất bình thường hoặc lỗi trước khi có action: không export checkpoint xuống PostgreSQL.
4. Có interrupt: export boundary checkpoint, đủ channel versions/values và **tất cả pending writes cần thiết**.
5. Lưu checkpoint/writes và content/attachments/file links/status/metadata đang chờ trong cùng transaction trên cùng database. Chỉ báo trạng thái chờ sau khi commit thành công.

Không chỉ lưu `__interrupt__`: writes của sibling hoàn thành có thể cần để tránh chạy lặp side effect. Interrupt lần hai trong cùng node có thể cập nhật writes trên checkpoint cũ, không nhất thiết tạo checkpoint_id mới.

Tối ưu này được kiểm chứng bằng adapter sync/async riêng, không phải mặc định chỉ cần bật PostgresSaver là có. Không sao chép nguyên saver JavaScript LibreChat vì thứ tự put/put_writes trong runtime Python đã thử khác nhau.

## 7. Resume, hủy và kiểm tra quyền

### Người dùng trả lời/duyệt

- Request mang message/action_id và response; checkpoint pointer lấy từ metadata server.
- Trong transaction ngắn: khóa conversation/message, kiểm tra owner/workspace/membership, requires_action và action_id hiện tại, graph_version tương thích; validate response.
- Với approve tool, kiểm tra quyền tool hiện tại; có approval không thay thế permission. Kiểm tra lại sát lúc thực thi tool theo cơ chế giai đoạn 3.
- Lưu response vào metadata/activity và claim chuyển running nguyên tử. Hai submit đồng thời chỉ một request được claim; request còn lại bị từ chối.
- Nhả transaction trước khi chạy graph; dựng runtime mới, đọc checkpoint đã chọn và dùng Command resume. Không dựng lại execution từ transcript để thay thế checkpoint của action đang chờ.
- Nếu pause lần nữa: lưu action_id mới, vẫn cùng message. Nếu kết thúc: finalize message như giai đoạn 2.

### Từ chối tool và hủy toàn lượt

- Từ chối tool: resume với quyết định từ chối, tool không chạy; agent có thể giải thích/tìm cách khác và completed.
- Hủy action/toàn lượt: message cancelled, giữ nội dung đã sinh, activity cancelled, bỏ pending_action; action cũ không được resume.
- Response sai định dạng hoặc không còn quyền: từ chối trước claim, giữ action đang chờ để tránh làm message kẹt running do input không hợp lệ.

`expires_at = null` nghĩa là không tự hết hạn. Lưu lâu dài vẫn cần giữ graph/runtime tương thích cho action đang chờ; không ép checkpoint cũ chạy bằng graph khác. Migration graph/SDK chưa được xây, graph_version hiện dùng để phát hiện không tương thích.

## 8. Chính sách lưu, share/copy và giới hạn

- Các mốc lưu content: **completed, caught failure, user cancellation và interrupt/pause**. Response của người dùng được lưu ngay trong transaction claim trước resume.
- Không ghi token định kỳ vào PostgreSQL. Không giữ database transaction suốt thời gian chờ LLM/người dùng.
- Source chat vẫn private by default; không có admin bypass đọc checkpoint/chat riêng.
- Chưa có cleanup tự động checkpoint sau completed/cancelled; chốt nguyên tắc không dọn checkpoint khi action còn chờ. Chính sách retention sau kết thúc thiết lập sau.
- Share/copy giữ lịch sử content/activity đã hoàn thành; không copy pending_action, checkpoint pointer, resume token hoặc runtime state. Bản copy bắt đầu không có action sống từ nguồn; snapshot không chứa raw metadata điều khiển của message.
- Node chứa interrupt có thể chạy lại từ đầu khi resume. Side effect trước interrupt phải đặt lại vị trí hoặc có idempotency; checkpoint không khôi phục nguyên Python call stack.
- Worker chết khi đang chạy hoặc sau claim: chưa có recovery/takeover tự động, có thể còn pending/running và mất buffer RAM. Checkpoint bền vững cho intentional pause không đồng nghĩa đã giải quyết crash giữa lượt.
- Helper quyền và trigger không thay thế HTTP auth, runtime DB roles/RLS hoặc kiểm tra backend đầy đủ.

## 9. Kiểm chứng và trạng thái triển khai

Nguồn kiểm chứng trong [thư mục thử nghiệm](../experiments/langgraph-action-checkpoints/README.md):

- [27 kiểm tra sync](../experiments/langgraph-action-checkpoints/results.json): export chỉ khi pause, process mới/restart PostgreSQL, nhiều interrupt cùng node, parallel sibling, rollback checkpoint + dấu chờ.
- [30 kiểm tra async/AG-UI](../experiments/langgraph-action-checkpoints/async-results.json): stream chunk, SDK validation/SSE codec, lưu question/response cùng message, context rebuild, revoke role permission, cancel và submit đồng thời.
- [14 SQL checks giai đoạn 4](phase-4-checks.sql): metadata, trạng thái mới, active uniqueness, terminal immutability, snapshot/copy và không có bảng action/run. Toàn chuỗi schema/checks giai đoạn 1–4 đã qua 122 assertions SQL; SDK setup đã được thử với cả bốn bảng trong schema `langgraph_checkpoints`. Bộ 30 kiểm tra async đã chạy lại sau khi bootstrap thử nghiệm chuyển sang dùng SQL chốt giai đoạn 4.

Môi trường đã thử: PostgreSQL 18.6, Python 3.12, LangGraph 1.2.16, checkpoint 4.3.0, postgres saver 3.2.0, langchain-core 1.6.12, psycopg 3.3.6, AG-UI protocol 1.0.0, ag-ui-langgraph 0.0.47. Các version cụ thể của lần chạy nằm trong báo cáo.

Model streaming được mô phỏng; SDK/graph/PostgreSQL/AG-UI adapter thật. Chưa kiểm chứng provider LLM/MCP bên ngoài, HTTP deployment, subgraph/DeltaChannel/conformance đầy đủ hoặc nâng graph/runtime. Code thử nghiệm chưa được tích hợp vào backend ứng dụng. Chốt mô hình database không có nghĩa tất cả các tích hợp đó đã hoàn thành.
