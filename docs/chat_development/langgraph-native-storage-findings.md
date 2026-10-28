# LangGraph sinh ra dữ liệu gì — đo thật trên Postgres và Redis

> Ngày đo: 26/10/2026. Phiên bản pin khi đo: `langgraph 1.2.17`, `langgraph-checkpoint 4.3.0`,
> `langgraph-checkpoint-postgres 3.2.0`, `langgraph-checkpoint-redis 0.5.2`, `psycopg 3.3.6`,
> PostgreSQL 17-alpine, Redis 8-alpine.
> Mục đích: trước khi thiết kế bảng cho chat, phải biết **LangGraph đã tự lưu gì** để không
> làm trùng, và quan trọng hơn là biết **nó KHÔNG lưu gì** để biết bảng nào mình bắt buộc phải có.
> Kết quả thiết kế: [`chat-schema.sql`](./chat-schema.sql).

## 0. Cách tái lập

Graph dùng để đo mô phỏng đúng hình dạng chat thật: `llm → approval (interrupt) → tool`,
state có channel `messages` (reducer `add_messages`) và một channel scalar `scratch`.

```bash
docker run -d --name lg-pg-lab    -e POSTGRES_PASSWORD=lab -e POSTGRES_USER=lab \
                                  -e POSTGRES_DB=lglab -p 55432:5432 postgres:17-alpine
docker run -d --name lg-redis-lab -p 56379:6379 redis:8-alpine
```

Script trong scratchpad của phiên làm việc: `run_pg.py`, `run_redis.py`, `crash_test.py`, `growth.py`.
Dọn dẹp: `docker rm -f lg-pg-lab lg-redis-lab`.

## 1. Postgres: `setup()` tạo đúng 6 bảng

`PostgresSaver.setup()` + `PostgresStore.setup()` tạo:

| Bảng | Khoá chính | Nội dung thật |
|---|---|---|
| `checkpoints` | `(thread_id, checkpoint_ns, checkpoint_id)` | `checkpoint` jsonb + `metadata` jsonb, `parent_checkpoint_id` |
| `checkpoint_blobs` | `(thread_id, checkpoint_ns, channel, version)` | giá trị channel lớn, `blob` bytea msgpack |
| `checkpoint_writes` | `(thread_id, checkpoint_ns, checkpoint_id, task_id, idx)` | pending writes theo task, có cột `task_path` |
| `checkpoint_migrations` | `(v)` | version schema — khi đo là `9` |
| `store` | `(prefix, key)` | long-term memory, có `expires_at` + `ttl_minutes` |
| `store_migrations` | `(v)` | version schema — khi đo là `3` |

**Tài liệu chính thức mô tả sai so với thực tế.** Trang checkpointers đưa "recommended schema"
gồm hai bảng `checkpoints` và `writes`; đó là gợi ý cho người **tự viết** checkpointer, không
phải schema `PostgresSaver` tạo ra. Thực tế có 6 bảng, tên bảng writes là `checkpoint_writes`,
và có thêm `checkpoint_blobs` mà tài liệu không hề nhắc tới. Không thiết kế dựa trên trang docs đó.

Index native tạo sẵn chỉ gồm PK và một index `thread_id` cho mỗi bảng checkpoint; `store` có thêm
`store_prefix_idx (prefix text_pattern_ops)` và `idx_store_expires_at` partial theo `expires_at IS NOT NULL`.

### 1.1. `checkpoints.checkpoint` chứa gì

Giá trị scalar nằm **inline**, giá trị channel phức tạp bị đẩy ra `checkpoint_blobs`:

```json
{
  "v": 4,
  "id": "1f1d11bd-c0d9-67c3-8002-11d91ce2bbfa",
  "ts": "2026-10-26T09:01:41.139646+00:00",
  "channel_values": { "scratch": "approved=yes", "branch:to:tool": null },
  "channel_versions": { "messages": "00000000000000000000000000000003.0.7367659644054111", ... },
  "versions_seen": { "llm": {...}, "approval": {...}, "__interrupt__": {...} },
  "updated_channels": ["branch:to:tool", "scratch"]
}
```

`messages` **không** có trong `channel_values` — nó ở `checkpoint_blobs` dưới dạng msgpack của
LangChain message objects. `metadata` jsonb chứa `step`, `source` (`input`/`loop`/`update`) và `writes`.

### 1.2. `checkpoint_writes` lộ ra cơ chế interrupt

Một lượt có interrupt sinh ra các row với `idx` âm — đây là `WRITES_IDX_MAP`:

| channel | idx | ý nghĩa |
|---|---|---|
| `__interrupt__` | `-3` | payload `Interrupt(value=..., id='f973484572e07ef085caa9b578c1d62c')` |
| `__resume__` | `-4` | giá trị người dùng gửi qua `Command(resume=...)` |
| channel thường | `0,1,2...` | output của node theo thứ tự |

`Interrupt.id` là hex 32 ký tự ổn định → dùng trực tiếp làm `app.approval.interrupt_id`.
`task_path` có dạng `~__pregel_pull, approval` — cho biết node nào tạo write.

### 1.3. Store lưu namespace dạng chuỗi nối dấu chấm

`store.put(("tenant-1", "user-1", "memories"), "fact-1", {...})` ghi ra row:

```
prefix      | tenant-1.user-1.memories
key         | fact-1
value       | {"text": "User thich tieng Viet"}
expires_at  | (null)
ttl_minutes | (null)
```

Namespace là tuple nối bằng `.` và đánh index `text_pattern_ops` để prefix-match. Hệ quả:
**tenant/user id không được chứa dấu chấm**, nếu không namespace sẽ nhập nhằng. TTL chỉ có khi
truyền `ttl=TTLConfig(...)`; mặc định `NULL` = không hết hạn.

## 2. Redis: khác bản chất, không chỉ khác địa chỉ lưu

`RedisSaver.setup()` + `RedisStore.setup()` tạo 3 **RediSearch index** (`checkpoint`,
`checkpoint_write`, `store`) và lưu dữ liệu bằng **ReJSON**. Tức là nó cần Redis có module
`search` + `ReJSON` — Redis 8 có sẵn, Redis thuần cũ thì không chạy được.

Key sinh ra:

```
checkpoint:<thread>:<ns>:<checkpoint_id>              ReJSON-RL
checkpoint_latest:<thread>:<ns>                       string (con trỏ tới checkpoint_id mới nhất)
checkpoint_write:<thread>:<ns>:<cp_id>:<task_id>:<idx>  ReJSON-RL
write_keys_zset:<thread>:<ns>:<cp_id>                 zset
store:<ULID>                                          ReJSON-RL
```

`checkpoint_ns` rỗng được mã hoá thành literal `__empty__`.

**Ba khác biệt đáng kể so với bản Postgres:**

1. **Không có tầng blob.** Redis nhét trọn `channel_values` (kể cả toàn bộ `messages` ở dạng
   LangChain serialized JSON) vào trong mỗi checkpoint key. Đo được trên cùng một hội thoại
   3 message: 1 976 → 2 560 → 3 448 → 4 336 → 4 896 bytes qua 5 checkpoint. Mỗi checkpoint là
   một bản sao đầy đủ, nằm trong RAM.
2. **Không có TTL mặc định.** `TTL` của mọi key đo được là `-1`. Phải truyền `ttl=` vào
   `RedisSaver(...)`/`RedisStore(...)`, nếu không Redis phình vô hạn.
3. **Store nằm ngoài Postgres.** Memory và checkpoint không còn cùng một transaction boundary
   với dữ liệu ứng dụng.

Kết luận cho dự án: **giữ native persistence ở Postgres**. Redis trong kiến trúc này đóng vai
live projection + replay stream (dữ liệu của mình, schema của mình), không phải nơi chứa
checkpoint. Dùng RedisSaver sẽ đưa toàn bộ graph state vào RAM và thêm phụ thuộc RediSearch mà
không đổi lại được gì cho yêu cầu snapshot+tail.

## 3. Bốn phát hiện thay đổi thiết kế

### 3.1. Checkpoint chứa **0 ký tự** của response đang sinh dở

Đây là phép đo quan trọng nhất. Node `slow_llm` sinh text dần trong RAM rồi `os._exit(1)` giữa chừng:

```
   streaming... 94 chars
   >>> CRASH (os._exit) giua luc dang sinh
```

Postgres sau crash, với `durability="sync"`:

```
 step |  src  |           cv
------+-------+-------------------------
 -1   | input | {}
 0    | loop  | {"branch:to:llm": null}
```

`checkpoint_writes` chỉ có message của **user**. 94 ký tự assistant đã sinh: không còn gì.

Lý do: checkpoint ghi ở ranh giới super-step, mà một node đang stream vẫn **chưa kết thúc
super-step của nó**. `durability="sync"` không cứu được — "sync" nghĩa là ghi trước khi sang
bước kế tiếp, không phải ghi liên tục trong bước.

Hệ quả trực tiếp cho kiến trúc đã chốt:

- Khẳng định "native checkpoint không mặc nhiên chứa token đang sinh dở" trong
  [copilotkit-agui-integration.md](./copilotkit-agui-integration.md) mục 6 là **đúng, đã kiểm chứng**.
- Redis live projection không phải tối ưu hoá, nó là **thành phần bắt buộc** của contract snapshot+tail.
- Mất Redis = mất phần đang dở, thật sự, không có đường cứu từ Postgres. Phát biểu "RPO của
  partial response khác RPO của final transcript" trong thiết kế nền tảng mục 3.2 được xác nhận.
- Worker chết giữa lúc sinh → resume sẽ **chạy lại cả node** từ đầu, sinh text mới. Đúng như
  mục 13.2 yêu cầu: phải phát `message.replaced` với fence mới, không nối vào prefix cũ.

### 3.2. `durability` thay đổi số checkpoint rất mạnh

Cùng một graph, cùng một lượt:

| `durability` | số checkpoint ghi được |
|---|---|
| `"sync"` | 5 |
| `"exit"` | 1 |

`"exit"` chỉ ghi khi execution thoát (xong, lỗi, hoặc dừng ở interrupt). Với graph có tool và
approval thì mất gần hết khả năng recovery giữa chừng. Xác nhận lựa chọn `sync` cho MVP ở mục 5.2.

Tham số truyền **lúc gọi**, không phải lúc compile: `graph.stream(input, config, durability="sync")`.
Đây là điểm mục 5.2 đánh dấu "chưa kiểm chứng, không giả định `.run(input, durability=...)` tồn tại"
— nay đã rõ: nó là kwarg của `stream`/`invoke`, nên muốn dùng qua `LangGraphAgent.run()` thì phải
xác minh wrapper có đường truyền xuống hay không. **Phần này vẫn chưa test** (xem mục 5).

### 3.3. Checkpoint phình phi tuyến, ~18x so với transcript thô

20 lượt, mỗi reply ~270 ký tự, cùng một thread, `durability="sync"`:

| lượt | #cp | cp_bytes | #blob | blob_bytes | #write | write_bytes | **tổng** |
|---|---|---|---|---|---|---|---|
| 1 | 3 | 1 753 | 3 | 900 | 3 | 334 | **2 987** |
| 5 | 15 | 10 461 | 15 | 8 205 | 15 | 1 670 | **20 336** |
| 10 | 30 | 21 298 | 30 | 18 764 | 30 | 3 341 | **43 403** |
| 20 | 60 | 43 008 | 60 | 53 703 | 60 | 6 691 | **103 402** |

Transcript thô chỉ khoảng 5.6 KB. Checkpoint tốn 103 KB — **18 lần**. Và `blob_bytes` tăng
*phi tuyến* (gấp 60 lần khi số lượt gấp 20): mỗi version của channel `messages` lưu lại **toàn bộ**
danh sách message, nên chi phí là O(n²) theo số lượt.

Đây là bằng chứng định lượng cho hai quyết định đã có trong thiết kế:

- `app.transcript_item` là **bắt buộc**, không phải tối ưu hoá. Không bao giờ phân trang history
  bằng cách đọc checkpoint.
- Phải có retention/prune cho checkpoint. `DeltaChannel` (`langgraph>=1.2`, beta) là hướng giảm
  O(n²) này, đáng đánh giá nhưng chưa test ở đây.

### 3.4. Native saver không nhận tham số `schema`

```python
PostgresSaver.__init__(self, conn, pipe=None, serde=None)   # không có schema
```

Không có chữ `schema` nào trong `langgraph/checkpoint/postgres/base.py`. Bảng rơi vào
`search_path`, mặc định là `public`. Mục 4 của thiết kế nền tảng đặt vấn đề "không giả định
native package tự hỗ trợ một tên schema tuỳ ý" — xác nhận: **không hỗ trợ**.

Cách làm được, đã test:

```python
conn = psycopg.connect(DSN, autocommit=True, options="-c search_path=lg")
PostgresSaver(conn).setup()
# -> checkpoints, checkpoint_blobs, checkpoint_writes, checkpoint_migrations trong schema "lg"
```

Vậy ranh giới `app` / `lg` trong cùng một cluster là khả thi, nhưng phải set `search_path` trên
**chính connection** của saver, và nhớ rằng connection đó cũng là connection giữ advisory lock.

## 4. Phân chia trách nhiệm: cái gì nằm ở đâu

| Dữ liệu | Ai lưu | Mình có cần bảng riêng không? |
|---|---|---|
| Graph state để tiếp tục chạy | `checkpoints` + `checkpoint_blobs` | Không — chỉ giữ `checkpoint_id` dạng text |
| Pending writes, interrupt payload | `checkpoint_writes` | Không — nhưng `approval` cần ánh xạ `interrupt_id` |
| Memory xuyên hội thoại | `store` | Không — chỉ đặt policy namespace |
| Transcript người dùng thấy | **không ai** | **Có** — `transcript_item` |
| Ownership, quyền, title | **không ai** | **Có** — `conversation` |
| Hàng đợi run, trạng thái, idempotency | **không ai** | **Có** — `run`, `run_attempt` |
| Quyết định approval của người dùng | **không ai** | **Có** — `approval` |
| Chống lặp side effect của tool | **không ai** | **Có** — `tool_invocation` |
| Title/memory job | **không ai** | **Có** — `metadata_job` |
| Publish sau commit | **không ai** | **Có** — `outbox_event` |
| Text đang sinh dở | **không ai** (Redis projection của mình) | Tuỳ chọn — `run_event_journal` nếu cần RPO |

LangGraph lo "graph chạy tiếp thế nào". Toàn bộ phần "sản phẩm chat" phải tự lưu.

## 5. Schema đã thiết kế

Chi tiết trong [`chat-schema.sql`](./chat-schema.sql) — 9 bảng trong schema `app`, cộng một
bảng thứ 10 để comment sẵn (`run_event_journal`) chỉ bật khi RPO partial bắt buộc.

DDL đã **chạy sạch trên PostgreSQL 17** và các invariant sau đã được kiểm chứng bằng SQL thật:

| Invariant | Cơ chế | Kết quả test |
|---|---|---|
| Một conversation chỉ một run chưa terminal | partial unique `run_one_open_per_conversation` | Insert thứ hai bị chặn ✅ |
| Retry cùng idempotency key không nhân run | unique `(conversation_id, created_by, idempotency_key)` | Bị chặn ✅ |
| Terminal phải có `finished_at` | check `run_terminal_finished_chk` | Bị chặn ✅ |
| Run đóng rồi thì nhận lượt mới | partial index chỉ tính status chưa terminal | Nhận được ✅ |
| Hai worker không claim trùng job | `FOR UPDATE SKIP LOCKED` | Worker 2 nhận `None` ✅ |
| Worker B không ghi đè khi A còn sống | `pg_try_advisory_lock(lock_key)` | B bị từ chối ✅ |
| A chết thì B vào được | advisory lock session-scope tự nhả khi connection đóng | B acquire được ✅ |

Điểm cuối là xác nhận cho lập luận mục 8.1 của thiết kế nền tảng: lease TTL đơn thuần không
chặn được worker cũ, nhưng advisory lock gắn với connection thì chặn được, **và tự nhả đúng lúc
process chết** — vốn là tình huống cần recovery.

## 6. Chưa kiểm chứng

Để không nhầm phạm vi, những thứ sau **chưa** được test trong lần đo này:

- `LangGraphAgent.run()` có truyền được `durability` xuống graph hay không. Đây là rủi ro
  integration lớn nhất còn lại: toàn bộ mục 3.2 ở trên nói về `graph.stream(...)` trực tiếp,
  trong khi kiến trúc đã chốt là worker chạy qua wrapper.
- Reducer phía AG-UI client có nuốt đúng snapshot `MESSAGES_SNAPSHOT` vs `START + CONTENT` lớn hay không.
- `DeltaChannel` giảm được bao nhiêu phần tăng trưởng O(n²) ở mục 3.3.
- Hành vi dưới PgBouncer (advisory lock session-scope **không** đi qua transaction pooling).
- `AsyncPostgresSaver`: lần đo này dùng bản sync. Schema giống nhau, nhưng ownership connection
  theo attempt cần test lại trên bản async.
- Postgres failover/partition với advisory lock.

## 7. Liên quan

- [API contract](./chat-agent-api-contract.md) — run/connect/stop và wire DTO.
- [Thiết kế nền tảng](./langgraph-oss-agent-platform-design.md) — mục 5 (native persistence),
  mục 6 (mô hình dữ liệu), mục 8 (ownership), mục 10 (snapshot+tail).
- [Tích hợp AG-UI](./copilotkit-agui-integration.md) — ranh giới wrapper và EventEncoder.
