# Kiểm chứng: action nằm trong messages.metadata, checkpoint chỉ lưu khi pause

Ngày chạy: **29/10/2026**, Asia/Ho_Chi_Minh.

**Kết quả: khả thi trong phạm vi graph đã kiểm chứng.** Không cần bảng `message_pending_actions`; thông tin chờ nằm trong `messages.metadata`, status là `requires_action`. Checkpoint và pending writes lưu riêng bằng PostgresSaver, chỉ khi có interrupt.

Đã bổ sung **bản async/streaming với AG-UI adapter thật**, model streaming mô phỏng, kiểm tra quyền tool qua RBAC đã có và lưu hỏi–đáp trong cùng message assistant. Xem [phần kiểm chứng async](#bổ-sung-asyncstreaming-và-hỏiđáp-trong-cùng-message) và [báo cáo async](async-results.json).

Đây là thử nghiệm chạy thật LangGraph + PostgreSQL. Model/tool là các node mô phỏng xác định trước, không gọi LLM, MCP hoặc tài khoản bên ngoài. **Mô hình đã được chốt trong [database decisions giai đoạn 4](../../database_decisions/phase-4-decisions.md)**; bootstrap thử nghiệm dùng SQL giai đoạn 4 rồi thêm schema đo kiểm riêng. Chưa sửa backend hoặc database ứng dụng.

## Chạy lại

Cần `uv`, PostgreSQL 18+ (`initdb`, `pg_ctl`, `psql`) trên PATH; chạy bằng user thường có quyền tạo cluster tạm.

Từ thư mục gốc repository:

```bash
uv run --python backend/.venv/bin/python \
  docs/experiments/langgraph-action-checkpoints/prove.py \
  --report docs/experiments/langgraph-action-checkpoints/results.json

# Bản async + AG-UI, thêm 30 kiểm tra độc lập:
uv run --python backend/.venv/bin/python \
  docs/experiments/langgraph-action-checkpoints/prove_async.py \
  --report docs/experiments/langgraph-action-checkpoints/async-results.json
```

Script tự tạo PostgreSQL tạm, chỉ mở Unix socket trong thư mục tạm, không mở TCP. Nó áp dụng schema giai đoạn 1 → phần 1 giai đoạn 2 → bản cuối giai đoạn 2 → patch thử nghiệm, rồi setup checkpointer chính thức. Mỗi lượt start/resume chạy trong **Python subprocess mới**, graph/saver/connection mới. Có một lần restart PostgreSQL giữa pause và resume. Kết thúc sẽ dừng và xóa cluster tạm, kể cả khi một assertion lỗi.

Không đọc `.env`, không dùng database ứng dụng và không sửa dependency/lockfile của backend. `uv` tạo môi trường thử riêng; dependencies pin bằng PEP 723 trong `prove.py`. Không chạy `proof_schema.sql` lên database ứng dụng.

## Các file

| File | Vai trò |
|---|---|
| [prove.py](prove.py) | Graph, mô phỏng luồng message, worker subprocess và 27 kiểm tra |
| [interrupt_saver.py](interrupt_saver.py) | Buffer state trong RAM, export sang PostgresSaver khi pause |
| [proof_schema.sql](proof_schema.sql) | Include SQL giai đoạn 4 đã chốt, thêm instrumentation riêng cho thử nghiệm |
| [results.json](results.json) | Báo cáo phiên bản và kết quả lần chạy thành công gần nhất |
| [prove_async.py](prove_async.py) | Async graph, fake streamed LLM, AG-UI adapter/SSE, RBAC và 30 kiểm tra bổ sung |
| [async_interrupt_saver.py](async_interrupt_saver.py) | Export checkpoint bất đồng bộ qua AsyncPostgresSaver |
| [async-results.json](async-results.json) | Báo cáo async và mẫu content/metadata trước–sau khi trả lời |

## Thay đổi database đã thử

Chỉ mở rộng bảng ứng dụng `messages`:

```sql
metadata jsonb NOT NULL DEFAULT '{}'::jsonb
CHECK (jsonb_typeof(metadata) = 'object')
```

Bổ sung status `requires_action` và mở rộng index một assistant active để bao gồm trạng thái này. Guard snapshot/copy cũng tính nó là trạng thái chưa kết thúc.

Ví dụ metadata đang chờ, ID minh họa:

```json
{
  "pending_action": {
    "action_id": "uuid-action",
    "state": "waiting",
    "graph_version": "checkpoint-proof-v1",
    "created_at": "2026-10-29T00:00:00+00:00",
    "expires_at": null,
    "checkpoint": {
      "thread_id": "uuid-assistant-message",
      "checkpoint_ns": "",
      "checkpoint_id": "checkpoint-id"
    },
    "interrupts": [
      {
        "interrupt_id": "langgraph-interrupt-id",
        "payload": {
          "kind": "tool_approval",
          "tool_call_id": "call-demo",
          "tool_name": "demo_tool",
          "arguments": {"query": "example"}
        }
      }
    ]
  }
}
```

`interrupts` cũng có thể chứa payload câu hỏi. Khi trả lời, lưu response và đánh dấu resuming trong metadata, chuyển message về running. Nếu pause tiếp, thay pending_action bằng action mới. Khi hoàn thành, bỏ pending_action và giữ last_action là quyết định gần nhất. Đây không phải nhật ký audit toàn bộ các lần duyệt.

Các trường điều khiển trên do backend ghi/kiểm tra; không cho client tự chọn checkpoint hoặc tùy ý sửa metadata rồi yêu cầu resume. Demo kiểm tra actor có quyền truy cập conversation, action_id hiện tại, graph_version và thread_id gắn đúng message.

Không có bảng pending action hoặc bảng run/attempt. Các bảng SDK vẫn cần tồn tại trong schema kỹ thuật `checkpoint_probe`: `checkpoints`, `checkpoint_writes`, `checkpoint_blobs`, `checkpoint_migrations`. Bảng `probe_evidence.effects` chỉ đếm hiệu ứng node trong thử nghiệm, không phải bảng nghiệp vụ được đề xuất.

## Cách chỉ lưu khi có action

1. Trong khi chạy, saver giữ state và write batches trong RAM của request.
2. Gọi graph với `durability='exit'`.
3. Nếu graph hoàn thành hoặc lỗi mà không có interrupt: không export checkpoint xuống PostgreSQL.
4. Nếu graph trả interrupt: lấy checkpoint ở boundary, lưu đầy đủ channel values/versions và **tất cả** pending write batches cần thiết, gồm cả dữ liệu sibling hoàn thành.
5. Trong **cùng transaction PostgreSQL**, ghi checkpoint, pending writes, content đã sinh và `messages.status/metadata` đang chờ.
6. Commit thành công mới trả trạng thái chờ cho caller. Nếu transaction lỗi thì cả checkpoint và dấu chờ rollback.

Không cần ghi checkpoint xuống DB từ lúc bắt đầu rồi mới xóa ở cuối. Trong khi chưa pause, process chết thì state RAM mất; đúng giới hạn chưa xử lý worker crash đã chốt.

Khi resume, nhận action_id + response; backend đọc checkpoint pointer từ message, không nhận pointer tùy ý từ client. Claim bằng transaction khóa message/conversation, chuyển trạng thái sang running, rồi nhả transaction trước khi chạy graph. Graph mới đọc state bền vững và nhận `Command(resume={interrupt_id: response})`. Runtime có thể deserialize AIMessage/ToolMessage và dùng lại tool-call ID từ checkpoint.

Checkpoint các lần pause cũ được giữ trong thử nghiệm sau khi hoàn thành để kiểm chứng không có checkpoint terminal mới. Chưa thực hiện cleanup; chính sách dọn sau hoàn tất/hủy cần chốt khi tích hợp. Action đang chờ không có TTL tự hết hạn.

## Các kết quả quan trọng

- **Chat thường:** completed, 0 dòng checkpoint/blob/write cho thread đó.
- **Lỗi trước action:** failed, vẫn giữ nội dung dở, 0 dòng checkpoint/blob/write.
- **Tool approval:** checkpoint + pending writes được lưu; tool chưa chạy trước khi duyệt.
- **Resume:** process mới, PostgreSQL đã restart, tiếp tục cùng message và tool chạy đúng một lần trong kịch bản đã kiểm tra.
- **Từ chối tool:** graph tiếp tục, không chạy tool, message vẫn có thể completed.
- **Hai câu hỏi trong cùng node:** hai action_id khác nhau nhưng có thể dùng **cùng checkpoint_id**; pending writes được cập nhật để giữ câu trả lời đầu tiên. Không được suy rằng mỗi action luôn tạo một checkpoint row mới.
- **Approval rồi hỏi tiếp ở node khác:** tiếp tục cùng message, không chạy lại tool đã xong.
- **Fan-out:** sibling đã hoàn thành trước pause không bị chạy lại sau resume; phải giữ pending writes của sibling, không chỉ `__interrupt__`.
- **Stale/double submit:** action_id cũ hoặc message đã hoàn thành bị từ chối trong kiểm tra tuần tự; chưa load-test submit đồng thời.
- **Lỗi lưu pause:** checkpoint và metadata đang chờ rollback cùng nhau; message còn running vì không triển khai crash/recovery.
- **Không TTL:** action được để expires_at NULL và thử đổi created_at thành năm 2000 rồi resume được. Đây là kiểm tra không có điều kiện hết hạn trong code, không phải chạy thực tế nhiều ngày.
- requires_action giữ chỗ một assistant active và chặn tạo snapshot mới.

## Điểm khác với việc sao chép saver LibreChat

Trong probe Python thực tế, boundary `put` có thể xảy ra **trước** `put_writes(__interrupt__)`. Vì vậy không sao chép nguyên cơ chế neo write của saver JavaScript trong LibreChat.

Ngoài ra, khi interrupt lần hai trong cùng node, runtime có thể chỉ cập nhật writes trên checkpoint cũ mà không gọi put cho checkpoint mới. Adapter thử nghiệm phải nạp anchor vào RAM và giữ resume writes; phiên bản ban đầu chưa xử lý điều này đã bị kiểm tra hai câu hỏi bắt lỗi, bản hiện tại đã qua.

LangGraph **chạy lại node chứa interrupt từ đầu** khi resume; không khôi phục nguyên call stack tại dòng Python. Thử nghiệm đếm được node có hai interrupt vào 3 lần. Các node đã hoàn thành có thể được giữ kết quả bằng checkpoint/pending writes, nhưng side effect đặt trước interrupt trong chính node đó vẫn có thể lặp. Khi tích hợp phải đặt side effect đúng vị trí hoặc dùng idempotency.

## Phiên bản và giới hạn

Các thư viện được pin: LangGraph 1.2.16, langgraph-checkpoint 4.3.0, langgraph-checkpoint-postgres 3.2.0, langchain-core 1.6.12, psycopg 3.3.6. Phiên bản Python/PostgreSQL thực tế nằm trong results.json.

**27 kiểm tra đã qua** với graph sync, root graph, ordinary state channels và durability exit. Adapter là proof of concept, chưa phải checkpointer tổng quát đã qua conformance suite:

- Adapter sync ở trên không bao phủ async; bản async riêng đã được kiểm chứng ở phần dưới. Cả hai chưa bao phủ subgraph, DeltaChannel hoặc mọi kiểu serializer/pending writes.
- Bản sync chưa tích hợp AG-UI stream, HTTP auth, role/tool permission thực, MCP, storage file hoặc LLM thật. Bản async bổ sung AG-UI adapter và truy vấn RBAC thật trên database tạm; không triển khai HTTP auth hoặc provider ngoài.
- Chưa thử nâng graph/SDK giữa lúc chờ; graph_version chỉ được kiểm tra khớp, chưa có runtime migration.
- Chưa có auto-recovery, lease/takeover, retry side effect sau process chết, timeout/expiry tùy chọn hoặc cleanup.
- Action mới nhất lưu trên message; chưa có lịch sử audit đầy đủ và chưa có thử nghiệm nhiều interrupt song song cùng một action.

Kết quả chứng minh được **mô hình messages.status + messages.metadata, không có bảng pending action, và chỉ ghi checkpoint khi pause** cho những luồng đã thử. Đã bổ sung SQL giai đoạn 4; các bản SQL giai đoạn 1–3 giữ làm lịch sử. Muốn đưa vào backend cần hoàn thiện các giới hạn theo phạm vi thực tế.

## Bổ sung async/streaming và hỏi–đáp trong cùng message

**30 kiểm tra bổ sung đã qua.** Bản mới dùng `AsyncPostgresSaver`, các node async, `LangGraphAgent.run()` của `ag-ui-langgraph==0.0.47`, `ag-ui-protocol==1.0.0` và `FakeListChatModel` phát từng chunk. Event đi qua SSE encoder thật, được decode và validate lại bằng SDK; đây là transport trong process, chưa phải HTTP server/client được triển khai.

AG-UI adapter mặc định không tự bảo đảm durability exit cho use case này. Subclass `ExitAgent` bổ sung `durability='exit'` vào stream kwargs; async saver giữ state tạm rồi export ở interrupt. Mỗi start/resume vẫn là process Python mới. Không đưa sync PostgreSQL I/O vào callback async; adapter mới dùng connection và saver async.

### Cách lưu câu hỏi và câu trả lời

- Model sinh câu hỏi; phần text được lưu trong `content` ngay khi pause.
- Một AG-UI **ActivityMessage** loại ứng dụng `user_interaction` tham chiếu ID phần câu hỏi, giữ trạng thái waiting/answered/cancelled.
- Response có `actor_id`, không giả thành lời assistant và không thêm role user vào bundle SQL assistant vốn chỉ cho assistant/tool/reasoning/activity.
- Quyết định/câu trả lời cũng nằm trong `metadata.actions`; pending action hiện tại nằm trong `metadata.pending_action`. Đây là hợp đồng ứng dụng, không phải role mới hoặc cơ chế approval có sẵn của protocol.
- Khi resume, response được đưa vào graph context dưới dạng **HumanMessage** nội bộ. Không gửi ActivityMessage trực tiếp cho model như lời assistant. Việc đưa response vào graph xảy ra một lần tại node đã resume; các lượt sau dùng `context_from_bundle()` trong bản thử nghiệm để dựng lại HumanMessage từ activity theo cùng hợp đồng. Đã kiểm tra thứ tự và không lặp response sau JSON reload; chưa tích hợp vào context-builder của backend ứng dụng.
- Claim trả lời được lưu nguyên tử: đánh dấu activity answered, lưu response/actor trong metadata và chuyển running. Nếu process chết sau đó, dữ liệu trả lời vẫn còn nhưng chưa có auto-recovery.
- Merge content theo ID ổn định và cập nhật activity cũ, giữ thứ tự câu hỏi → câu trả lời người dùng → phần trả lời tiếp theo. Không nối lặp text khi adapter phát lại snapshot.
- Có thể mở lại trang bằng content đã lưu mà không chạy lại graph hoặc hỏi model sinh lại câu hỏi.

Ví dụ bundle cuối, rút gọn từ báo cáo:

```json
[
  {"id":"question-id","role":"assistant","content":"Bạn muốn xuất kết quả dưới dạng nào?"},
  {
    "id":"interaction:action-id",
    "role":"activity",
    "activityType":"user_interaction",
    "content": {
      "action_id":"action-id",
      "kind":"user_question",
      "status":"answered",
      "question_message_id":"question-id",
      "response":"CSV",
      "actor_id":"user-id"
    }
  },
  {"id":"final-id","role":"assistant","content":"Đã nhận thông tin và hoàn thành yêu cầu."}
]
```

Bundle này được TypeAdapter của AG-UI validate và lưu qua CHECK SQL hiện có. Không thêm SQL user message cho response bổ sung; cây conversation không thay đổi vì pause/resume. Giao diện cần renderer cho activityType `user_interaction`; thử nghiệm chỉ có reducer event và dữ liệu reload, chưa tạo UI.

### Những luồng bổ sung đã kiểm tra

- Async chat thường và lỗi giữa các chunk: không có checkpoint bền vững nếu không có action; phần text đã stream được giữ khi lỗi.
- Câu hỏi do model mô phỏng sinh ra và widget chờ được lưu cùng message.
- Trả lời sau restart PostgreSQL/process mới, hai vòng hỏi đáp, không trùng nội dung hoặc chạy lại node model đã xong.
- Dựng context cho lượt chat mới từ bundle đã lưu, khôi phục đúng assistant → human answer → assistant, kể cả sau JSON reload; mỗi câu trả lời bổ sung chỉ xuất hiện một lần.
- Response rỗng bị từ chối trước claim; message vẫn requires_action.
- Duyệt tool chạy một lần, từ chối không chạy tool và graph vẫn kết thúc bình thường.
- Thu hồi permission `tool_demo.execute` trong `role_permissions` khi đang chờ: resume với approve bị từ chối, action còn nguyên; quyền cũng được kiểm tra sát trước khi tool chạy. Fixture dùng role Owner nhưng vẫn đòi grant tường minh, không có bypass.
- Hủy khi đang chờ: message cancelled, giữ content, activity cancelled, xóa pointer pending; action cũ không resume được.
- Message requires_action chặn lượt assistant mới.
- Hai process đồng thời trả lời cùng action: chỉ một process claim/resume thành công.

Quyền truy cập conversation được kiểm tra ở server. Demo nhận actor_id từ harness tin cậy, chưa phải HTTP authentication. Các thao tác thực tế qua MCP/LLM và tác động ngoài database vẫn chưa được kiểm chứng. Chưa có subgraph/DeltaChannel/conformance test, runtime-version migration hoặc auto-recovery. Không sao chép pending_action/checkpoint khi share/copy chat; activity lịch sử answered/cancelled chỉ để hiển thị, không phải quyền thực thi.
