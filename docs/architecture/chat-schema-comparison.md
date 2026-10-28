# Sáu dự án thiết kế bảng cho chat agent thế nào

> Ngày khảo sát: 26/10/2026. Phạm vi: đọc schema thật trong source local, không đọc tài liệu marketing.
> Mục đích: đối chiếu với [`chat-schema.sql`](../chat_development/chat-schema.sql) của mình để biết
> chỗ nào mình làm giống người đã chạy production, chỗ nào mình đang thiếu, và chỗ nào mình **sai**.
> Liên quan: [so sánh chat data flow](./chat-data-flow-comparison.md), [kết quả đo LangGraph](../chat_development/langgraph-native-storage-findings.md).

## 0. Nguồn đã đọc

| Dự án | File | Dạng |
|---|---|---|
| Onyx | [`backend/onyx/db/models.py`](/home/lamhung/code/onyx/backend/onyx/db/models.py:3298) (7 796 dòng) | SQLAlchemy + Alembic (512 migration) |
| TrueForge | [`src/db/postgres/migrations/20260728_000001_session_store.ts`](/home/lamhung/code/trueforge/packages/trueforge/src/db/postgres/migrations/20260728_000001_session_store.ts:1) | Kysely (42 migration) |
| Codex | [`codex-rs/state/*_migrations/`](/home/lamhung/code/codex/codex-rs/state/thread_history_migrations/0001_thread_history.sql:1) | sqlx + SQLite, **6 database riêng** |
| open-webui | [`backend/open_webui/models/chat_messages.py`](/home/lamhung/code/open-webui/backend/open_webui/models/chat_messages.py:1) | SQLAlchemy + Alembic (66 migration) |
| DeepSeek Harness | [`session-query-sqlite/src/schema.ts`](/home/lamhung/code/deepseek-harness/packages/session-query/session-query-sqlite/src/schema.ts:106) | JSONL canonical + SQLite derived |
| OpenHands | — | **Không đọc được** (xem bên dưới) |

**Cảnh báo phạm vi — OpenHands:** checkout local `/home/lamhung/code/OpenHands` là **frontend
React/TS**, không có bảng DB nào. Agent Server ở repo khác (`software-agent-sdk`) không có bản
local. Trùng với ghi nhận ở [openhands-LLD.md](./openhands-LLD.md) dòng 235. **Không kết luận gì
về schema của OpenHands**; so sánh bên dưới chỉ có 5 dự án.

---

## 1. Năm câu trả lời cho "nguồn sự thật nằm ở đâu"

| Dự án | Canonical store | Projection/derived | Transcript có nhánh? |
|---|---|---|---|
| Onyx | Postgres chuẩn hoá | — | **Có** (`parent_message_id`) |
| TrueForge | Postgres, event log + per-turn state | — | **Có** (`ancestor_ids`) |
| Codex | **File JSONL rollout** | SQLite, có watermark byte offset | **Có** (`root_turn_id`) |
| open-webui | Postgres/SQLite chuẩn hoá (vừa migrate từ blob) | — | **Có** (`parent_id`) |
| DeepSeek | **File JSONL** append-only | SQLite FTS5, vứt được | — |
| **Của mình** | Postgres + native LangGraph | Redis live projection | **Không** |

Hai dự án chọn canonical là **file**, không phải database: Codex và DeepSeek. Cả hai đều coi SQL
là read model dựng lại được. Codex đi xa hơn một bước: nó lưu **watermark của projection** ngay
trong SQLite (mục 4.2).

Và điểm đáng chú ý nhất của bảng trên: **4/5 dự án có transcript dạng cây. Mình là dự án duy
nhất không có.**

---

## 2. Onyx — chuẩn hoá quan hệ, message là cây

| Bảng | Vai trò |
|---|---|
| `chat_session` | conversation; title nằm ở cột tên `description` |
| `chat_message` | `parent_message_id` + `latest_child_message_id` |
| `tool_call` | tự tham chiếu `parent_tool_call_id` cho sub-agent |
| `build_session`, `build_message`, `action_approval` | thiết kế agent mới hơn, chạy song song chat cũ |

**Message là cây.** Comment nói rõ message đầu tiên là **root node rỗng** chỉ để cho phép sửa
message đầu. `preferred_response_id` cho phép một user message có nhiều assistant response và
chọn một để đi tiếp.

**Tool call lồng nhau có thứ tự tường minh:** `parent_tool_call_id` (tool gọi tool),
`turn_number` (cùng số = song song), `tab_index` (thứ tự hiển thị trong nhóm song song).

**`tool_id` cố ý KHÔNG phải FK** — *"we want to be able to delete the tool without deleting this
entry"*. Lịch sử phải sống sót qua việc xoá tool definition.

**`action_approval` trùng khớp thiết kế của mình:** `decision IS NULL` = pending, partial index
theo pending, `ondelete="SET NULL"` với comment *"the decided row stays as an audit record"*.
Cái mình thiếu: **`decided_via`** (UI / API / auto-policy).

Chi tiết đáng tin: Onyx dùng `native_enum=False` ở **mọi** enum trong 7 796 dòng. Sau 512
migration họ kết luận enum native của Postgres không đáng — trùng lựa chọn `text` + CHECK của mình.

---

## 3. TrueForge — schema tối ưu theo "nhiệt độ ghi"

Migration có hẳn docstring "write-heat summary". Quy tắc đặt cột viết thành luật:

> Top-level column ONLY if (a) key/query target, (b) hot write target (isolated so nothing else
> churns with it), or (c) big-and-immutable (own TOAST value carried by pointer through row
> rewrites). Everything small/rare/descriptive inlines into a store-owned extensible
> `checkpoint` jsonb. `custom` is always its own column.

`fillfactor` chỉnh theo từng bảng, có lý do ghi kèm:

| Bảng | fillfactor | Lý do trong migration |
|---|---|---|
| `turn_thread` | **70** | *"the ONE deliberately-hot table: rewritten 5–10x while its turn runs"* |
| `session`, `turn` | **85** | *"headroom so the per-turn bump stays HOT (no index churn)"* |
| `session_event`, `thread_context_log` | **100** | *"pure INSERT → zero dead tuples"* |

Không một FK nào; PK composite bắt đầu bằng `tenant_id`. Mọi migration mở đầu bằng
`SET LOCAL lock_timeout = '5s'`, kể cả migration chỉ `CREATE SCHEMA`.

**`event_id` là ULID, cố ý KHÔNG auto-increment** — comment dài nhất trong file, và nó chỉ ra
một lỗi thật trong schema của mình (mục 7.1):

> A database auto-increment id is deliberately not used: it assigns order at **persistence**
> rather than event **creation**, couples the contract to Postgres, and sequence allocation
> across pooled connections, transactions, retries, or larger sequence caches need not
> represent logical event order.

---

## 4. Codex — sáu database, canonical là file rollout

### 4.1. Chia database theo mối quan tâm, không gộp một chỗ

```
codex-rs/state/migrations/                  threads, logs, memories, backfill
codex-rs/state/thread_history_migrations/   thread_turns, thread_items, projection state
codex-rs/state/queue_migrations/            queued_items, queued_thread_revisions
codex-rs/state/memory_migrations/           stage1_outputs, jobs
codex-rs/state/goals_migrations/            thread_goals
codex-rs/state/logs_migrations/             logs
```

Sáu bộ migration độc lập, mỗi bộ một vòng đời/retention riêng. Xoá sạch log không đụng tới
thread history; reset projection không đụng tới queue.

### 4.2. Projection có watermark bền vững — đúng bài toán `connect` của mình

```sql
CREATE TABLE thread_history_projection_state (
    thread_id TEXT PRIMARY KEY,
    next_rollout_byte_offset INTEGER NOT NULL,
    next_rollout_ordinal INTEGER NOT NULL
);
```

`threads.rollout_path` trỏ tới file JSONL canonical. Projection đọc tới đâu thì ghi lại **byte
offset** tới đó. Mất SQLite thì dựng lại từ byte 0; chết giữa chừng thì chạy tiếp từ offset đã lưu.

Đây chính là watermark của contract snapshot+tail, nhưng **được lưu bền vững** thay vì chỉ sống
trong Redis như thiết kế của mình. Xem mục 7.4.

### 4.3. Live tách khỏi durable, dọn bằng trigger

```sql
CREATE TABLE thread_realtime_items ( thread_id, item_id, rollout_ordinal, item_type, item_json, ... );

CREATE INDEX idx_thread_realtime_items_boundary
    ON thread_realtime_items(thread_id, rollout_ordinal)
    WHERE item_type IN ('realtime_session_started', 'realtime_session_closed');

CREATE TRIGGER thread_realtime_items_projection_cleanup
    AFTER DELETE ON thread_history_projection_state
BEGIN
    DELETE FROM thread_realtime_items WHERE thread_id = OLD.thread_id;
END;
```

Item realtime nằm bảng riêng, không trộn vào `thread_items` durable. Xoá projection state thì
trigger dọn luôn realtime — vòng đời buộc vào nhau ở tầng DB. Xác nhận lựa chọn của mình: để
partial text ở Redis, không nhét vào `transcript_item`.

### 4.4. Hai ordinal: tạo và cập nhật

```sql
ALTER TABLE thread_items ADD COLUMN updated_at_ordinal INTEGER NOT NULL DEFAULT 0;
```

`rollout_ordinal` = thứ tự tạo. `updated_at_ordinal` = thứ tự cập nhật gần nhất. Comment giải
thích: *"Incremental replay excludes those items until a newer writer projects an update for them."*

Tức là: một item **được sửa sau** khi client đã đọc qua vị trí tạo của nó thì replay theo ordinal
tạo sẽ bỏ sót. Phải có ordinal thứ hai. Đây là lỗ hổng trong `transcript_item` của mình (mục 7.3).

Index giữ **non-unique** có chủ đích: *"so mixed-version writers can continue to persist history"*
— rolling deploy có writer cũ ghi `DEFAULT 0`.

### 4.5. `jobs` — durable queue tổng quát, tốt hơn `metadata_job` của mình

```sql
CREATE TABLE jobs (
    kind TEXT NOT NULL,
    job_key TEXT NOT NULL,
    status TEXT NOT NULL,
    worker_id TEXT,
    ownership_token TEXT,        -- fencing token
    started_at INTEGER, finished_at INTEGER,
    lease_until INTEGER,
    retry_at INTEGER,
    retry_remaining INTEGER NOT NULL,
    last_error TEXT,
    input_watermark INTEGER,
    last_success_watermark INTEGER,
    PRIMARY KEY (kind, job_key)
);
```

So với `app.metadata_job` của mình:

| | Mình | Codex |
|---|---|---|
| Danh tính | `UNIQUE (conversation_id, kind, input_revision)` → **một row mỗi revision** | `PK (kind, job_key)` → **một row, cập nhật tại chỗ** |
| Fencing | không có | `ownership_token` |
| Giới hạn retry | `attempts` đếm lên, không có trần | `retry_remaining` đếm xuống |
| Biết đã xử lý tới đâu | `input_revision` | `input_watermark` **+** `last_success_watermark` |

Thiết kế của Codex không phình theo thời gian và phân biệt được "input mới nhất" với "lần
thành công gần nhất" — biết chính xác có cần chạy lại hay không.

### 4.6. Revision per-thread duy trì bằng trigger

```sql
CREATE TABLE queued_thread_revisions (
    revision INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL UNIQUE
);
CREATE TRIGGER queued_items_revision_after_insert AFTER INSERT ON queued_items ...
CREATE TRIGGER queued_items_revision_after_update AFTER UPDATE ON queued_items ...
CREATE TRIGGER queued_items_revision_after_delete AFTER DELETE ON queued_items ...
```

Ba trigger giữ một bộ đếm "thread này có gì đổi chưa" để client poll rẻ. Logic nằm ở DB nên
không writer nào quên bump.

### 4.7. Ngân sách là cột, không phải cấu hình

```sql
CREATE TABLE thread_goals (
    thread_id TEXT PRIMARY KEY, goal_id TEXT NOT NULL, objective TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN (
        'active','paused','blocked','usage_limited','budget_limited','complete')),
    token_budget INTEGER, tokens_used INTEGER NOT NULL DEFAULT 0,
    time_used_seconds INTEGER NOT NULL DEFAULT 0, ...
);
```

`usage_limited` và `budget_limited` là **trạng thái hạng nhất**, không phải một loại lỗi. Run của
mình chỉ có `failed` + `error_code` — không phân biệt được "hết quota" với "lỗi thật".

---

## 5. open-webui — bằng chứng sống về việc blob không đủ

### 5.1. Vừa migrate blob → chuẩn hoá

`chat` có cột `chat = Column(JSON)` chứa **toàn bộ** hội thoại. Tháng 2/2026 họ thêm bảng
`chat_message` chuẩn hoá và backfill:
[`8452d01d26d7_add_chat_message_table.py`](/home/lamhung/code/open-webui/backend/open_webui/migrations/versions/8452d01d26d7_add_chat_message_table.py:1),
batch 5 000 row, có savepoint fallback từng dòng khi bulk insert fail.

Một sản phẩm chat đông người dùng bắt đầu bằng blob JSON rồi phải chuẩn hoá, và trả giá bằng
một migration backfill. Đây là lý do tốt để mình **không** nhét transcript vào một cột jsonb.

### 5.2. `chat_message` — ba thứ mình thiếu

```python
class ChatMessage(Base):
    __tablename__ = 'chat_message'
    id, chat_id, user_id, role
    parent_id       = Column(Text, nullable=True)      # cây
    content, output = Column(JSON)
    done            = Column(Boolean, default=True)    # <- probe tin nhắn dở
    status_history  = Column(JSON, nullable=True)      # <- lịch sử tiến trình
    usage           = Column(JSON, nullable=True)      # <- token/timing
    context_summary = Column(Text, nullable=True)      # <- mốc nén context
    error           = Column(JSON, nullable=True)

    __table_args__ = (
        Index('chat_message_chat_parent_idx', 'chat_id', 'parent_id'),
        Index('chat_message_chat_role_done_idx', 'chat_id', 'role', 'done'),  # unfinished-assistant probe
    )
```

Index cuối có comment **"unfinished-assistant probe"** — một index dành riêng để tìm assistant
message chưa hoàn tất. Đúng bài toán "mở lại chat sau khi worker chết" mà mình thiết kế
`status='streaming'` để diễn đạt, nhưng **mình chưa có index để tìm chúng**.

### 5.3. `chat.current_message_id` — con trỏ lá đang xem

Có cây thì phải có con trỏ "đang ở nhánh nào". Onyx giải bằng `latest_child_message_id` trên từng
message; open-webui giải bằng một con trỏ ở cấp chat. Cách thứ hai đơn giản hơn.

### 5.4. Partial index viết tường minh cho cả hai dialect

```python
Index('user_id_timer_at_idx', 'user_id', 'timer_at',
      sqlite_where=text('timer_at IS NOT NULL'),
      postgresql_where=text('timer_at IS NOT NULL')),
# timer_at key column turns the IS NOT NULL into a seek, so this beats the plain user_id indexes
```

---

## 6. DeepSeek Harness — projection thì đừng migrate, hãy dựng lại

Canonical: JSONL append-only, nén Zstandard, có checksum, có torn-tail crash recovery.
Derived: SQLite FTS5 tự bảo vệ mình bằng ba lớp kiểm tra trước khi đụng dữ liệu:

```ts
export const SESSION_QUERY_SQLITE_SCHEMA_VERSION = 8
export const SESSION_QUERY_SQLITE_APPLICATION_ID = 0x44534851   // "DSHQ"
const DERIVED_USER_TABLES = new Set(['search_state', 'persisted_sessions', ...])
```

1. `application_id` khác → *"belongs to another application"*, từ chối.
2. `application_id == 0` mà đã có bảng → *"is not an empty or recognized derived index"*, từ chối.
3. Bảng lạ ngoài danh sách → từ chối.

Chỉ qua cả ba mới `PRAGMA journal_mode` (*"Apply mutating pragmas only after refusing foreign or
canonical files"*). Lệch version thì drop hết dựng lại — **không migration cho derived index**.

`storage-sqlite` đóng dấu version **sau cùng**: *"the stamp asserts the layout is complete, so a
failure above must leave the medium unstamped"*.

Title là policy cắm được, không phải một cột: có tới 4 package `session-title*` riêng.

---

## 7. Đối chiếu với `chat-schema.sql` của mình

### 7.1. MỘT LỖI THẬT: `outbox_event` đọc theo cursor sẽ mất event

Lý luận ULID của TrueForge áp thẳng vào bảng của mình. Dựng Postgres 17 kiểm chứng:

```
A giành id=1, B giành id=2
B commit. A vẫn đang mở.
Relay đọc được: [(2, 'event của B')] -> cursor tiến tới 2
A commit.
Relay đọc tiếp từ cursor=2: []
>>> Event id=1 BỊ BỎ QUA VĨNH VIỄN

Mark-and-sweep (published_at IS NULL) lấy được: [(1, ...), (2, ...)]
```

`nextval()` cấp số lúc **INSERT**, row hiện ra lúc **COMMIT** — hai thứ tự khác nhau.

**Schema không sai, cách đọc mới sai.** Phải ghi thành luật: relay claim theo
`published_at IS NULL`, **tuyệt đối không đọc theo con trỏ `id`**. Cột `id` chỉ để sắp xếp
*trong một lô đã claim*.

> `langgraph-oss-agent-platform-design.md` mục 11 đã lo chiều "publish trùng" nhưng chưa lo
> chiều **mất** event. Cần bổ sung.

### 7.2. Transcript phẳng — 4/5 dự án đều có cây

| Dự án | Cơ chế |
|---|---|
| Onyx | `parent_message_id` + `latest_child_message_id` + root node rỗng |
| TrueForge | `previous_turn_id` + `ancestor_ids text[]` |
| open-webui | `parent_id` + `chat.current_message_id` |
| Codex | `root_turn_id` |
| **Mình** | **không có** |

`UNIQUE (conversation_id, ordinal)` của mình **loại trừ** nhánh. Không làm được "sửa câu hỏi rồi
chạy lại" — tính năng chat rất thông thường. Thêm sau nghĩa là bỏ unique constraint đó: migration
có đau, đúng kiểu backfill mà open-webui vừa phải làm.

Khuyến nghị đổi từ "cần chốt" thành **nên thêm `parent_item_id` nullable ngay bây giờ**. Rẻ lúc
này, đắt về sau, và bốn dự án độc lập đều kết luận là cần.

### 7.3. Thiếu ordinal thứ hai cho item bị sửa sau snapshot

Codex tách `rollout_ordinal` (tạo) khỏi `updated_at_ordinal` (cập nhật). Lý do: item được sửa
**sau** khi client đã đọc qua vị trí tạo của nó thì tail theo ordinal tạo sẽ bỏ sót.

`transcript_item` của mình có `revision` nhưng tail replay lại đi theo `ordinal`. Một message
hoàn tất rồi được sửa (ví dụ tool result tới muộn, hoặc finalize ghi đè partial) sẽ không được
client nhặt lên. Cần `updated_ordinal` hoặc đổi cách tail.

### 7.4. Watermark của projection chỉ sống trong Redis

Codex lưu `next_rollout_byte_offset` bền vững trong SQLite. Của mình, watermark W chỉ có trong
Redis projection. Redis reset → không biết dựng lại projection từ đâu, phải làm lại từ đầu
transcript. Với thread dài thì đắt.

Cân nhắc một bảng `projection_state(conversation_id, last_applied_ordinal, last_applied_revision)`.

### 7.5. Thiếu index tìm message dở dang

open-webui có index riêng `(chat_id, role, done)` với comment "unfinished-assistant probe".
Mình có `status='streaming'` nhưng không có index — recovery controller và cold start phải
seq-scan `transcript_item` để tìm.

Thêm: `CREATE INDEX ... ON app.transcript_item (conversation_id) WHERE status IN ('streaming','interrupted');`

### 7.6. `metadata_job` nên theo mô hình `jobs` của Codex

Hiện tại mình tạo **một row mỗi `input_revision`** → bảng phình theo thời gian. Codex dùng
`PK (kind, job_key)` cập nhật tại chỗ, cộng `ownership_token` (fencing), `retry_remaining`
(trần retry), và cặp `input_watermark` / `last_success_watermark`.

Đặc biệt `ownership_token`: `metadata_job` của mình hiện **không có fencing** — hai title worker
cùng claim một job thì không có gì chặn worker cũ ghi đè kết quả worker mới.

### 7.7. `run` không phân biệt hết quota với lỗi thật

Codex `thread_goals.status` có `usage_limited` và `budget_limited` là trạng thái hạng nhất.
`app.run` của mình chỉ có `failed` + `error_code` — UI không phân biệt được "thử lại sau" với
"hỏng thật", và retry policy cũng không.

### 7.8. Thiếu lặt vặt nhưng đáng thêm

| Thiếu | Nguồn |
|---|---|
| `decided_via` trên `approval` (UI / API / auto-policy) | Onyx `action_approval` |
| `token_count` / `usage` trên `transcript_item` | Onyx, open-webui |
| `step_number` + `parallel_index` trên `tool_invocation` | Onyx `turn_number` + `tab_index` |
| `context_summary` — mốc nén context | open-webui |
| `started_at_ms` / `completed_at_ms` trên transcript item | Codex 0007 |

### 7.9. `run_attempt` tưởng có HOT update nhưng không

Theo luật fillfactor của TrueForge (mục 3): HOT update chỉ xảy ra khi cột được update **không
nằm trong index nào**. `run_attempt` là bảng nóng (heartbeat 5 giây/lần), nhưng mình đặt
`run_attempt_lease_idx ON (lease_expires_at)` — mà `lease_expires_at` được update cùng nhịp
heartbeat. Mỗi nhịp sinh một row version mới cộng index churn.

| Cách | Đánh đổi |
|---|---|
| Bỏ index, recovery controller seq-scan | Bảng chỉ chứa attempt đang sống, có thể chấp nhận |
| Giữ index, thêm `WITH (fillfactor = 70)` | Vẫn churn index, chỉ giảm page split |
| Bỏ `lease_expires_at`, tính hạn bằng `heartbeat_at + interval` | Index theo `heartbeat_at` — vẫn là cột nóng |

Cần đo mới chốt. Điều chắc chắn: schema hiện tại đang nghĩ mình có HOT update mà thực ra không.

### 7.10. Chỗ mình làm đúng, có production xác nhận

| Quyết định của mình | Xác nhận |
|---|---|
| `decision IS NULL` = pending + partial index | Onyx `action_approval` giống hệt |
| Không FK sang bảng hệ thống khác | Onyx cố ý bỏ FK trên `tool_id` cùng lý do |
| Transcript tách khỏi state engine | **cả 5 dự án** |
| Live/partial tách khỏi durable transcript | Codex `thread_realtime_items` bảng riêng |
| Tombstone thay vì xoá ngay | Onyx `chat_session.deleted` |
| `status` text + CHECK thay vì enum native | Onyx `native_enum=False` ở mọi enum |
| Không nhét transcript vào một cột jsonb | open-webui vừa phải backfill thoát khỏi đúng cách đó |

---

## 8. Việc cần làm

| Ưu tiên | Việc | Mục |
|---|---|---|
| **Cao** | Ghi luật: relay claim theo `published_at IS NULL`, cấm đọc cursor `id` | 7.1 |
| **Cao** | Thêm `parent_item_id` — 4/5 dự án đều có cây | 7.2 |
| **Cao** | Thêm `ownership_token` cho `metadata_job` (hiện không có fencing) | 7.6 |
| **Cao** | Quyết định lại index/fillfactor `run_attempt` (heartbeat phá HOT update) | 7.9 |
| Vừa | Ordinal thứ hai cho item sửa sau snapshot | 7.3 |
| Vừa | Index tìm message dở dang | 7.5 |
| Vừa | Trạng thái `usage_limited` / `budget_limited` cho `run` | 7.7 |
| Vừa | `decided_via`, `token_count`, `step_number`/`parallel_index` | 7.8 |
| Thấp | Bảng `projection_state` để watermark sống qua Redis reset | 7.4 |
| Thấp | `lock_timeout` trong migration; version stamp ghi sau cùng | 3, 6 |

Chưa áp dụng vào file schema — đây là kết quả khảo sát để bạn chốt trước.
