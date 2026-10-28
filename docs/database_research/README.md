# Nghiên cứu database cho hệ thống chat agent

Ngày khảo sát: **27/10/2026**. Sáu repository được khảo sát tại checkout cục bộ, chia agent nghiên cứu song song. Mỗi tài liệu đối chiếu schema/migration với nơi đọc, ghi và xử lý streaming; không chỉ suy luận từ tên bảng.

## Tài liệu từng dự án

| Dự án | Tài liệu | Snapshot commit |
|---|---|---|
| Codex | [codex.md](./codex.md) | `970111f6cb62cc02fe36a82ea7d71b37a2889c97` |
| TrueForge | [trueforge.md](./trueforge.md) | `f5427d9116f1ade2c7ec2dc0172e66894a406204` |
| Onyx | [onyx.md](./onyx.md) | `03d0a7fcde658e6c27ce613b4b3cc7cf3da14b0b` |
| Open WebUI | [open-webui.md](./open-webui.md) | `33c1978d5bad52a31df75ea55143025dfad18d16` |
| LibreChat | [librechat.md](./librechat.md) | `8d3da9bbb220a0a96be9330a2e1cbd385fb786d5` |
| NextChat | [nextchat.md](./nextchat.md) | `1d3dc331512929a4b1d3e82354e72acce33b5c7a` |

Bổ sung cho Open WebUI: [open-webui-official-schema.md](./open-webui-official-schema.md) chép lại **toàn bộ 47 bảng** theo trang docs chính thức (<https://docs.openwebui.com/reference/database-schema/>, tới v0.12.0, community contribution). Dùng nó để có độ phủ bảng; dùng [open-webui.md](./open-webui.md) khi cần bằng chứng từ source.

Bổ sung cho Onyx: [onyx-full-schema.md](./onyx-full-schema.md) liệt kê **toàn bộ 167 bảng** đọc từ `backend/onyx/db/models.py` tại cùng snapshot commit, kèm enum, index/constraint và đối chiếu migration.

Bổ sung cho LibreChat: [librechat-full-schema.md](./librechat-full-schema.md) liệt kê **toàn bộ 53 model Mongoose cộng 9 collection thao tác bằng raw driver** đọc từ `packages/data-schemas/src/schema/` tại cùng snapshot commit, kèm index/partial filter, plugin tenant-isolation và các collection checkpoint LangGraph.

So sánh trực tiếp hai dự án: [openwebui-vs-librechat.md](./openwebui-vs-librechat.md) chấm Open WebUI và LibreChat trên bốn trục — **tính năng, khả năng mở rộng, độ sạch, tổ chức hợp lý** — kèm danh sách ưu/nhược điểm chi tiết của từng bên và phần rút ra cho DDL của dự án mình.

Phạm vi chính là dữ liệu phục vụ hội thoại: ownership, metadata/title, message, turn/run, tool, branch, context/memory, response đang sinh, reload, index và tính nhất quán. Các bảng quản trị, connector, billing và RAG chỉ được đề cập khi liên quan. Đây chưa phải bản DDL chốt cho dự án mình.

Đề xuất tổng hợp cho dự án: [Thiết kế lưu trữ lâu dài cho production](../chat_development/production-data-storage-design.md). Tài liệu chọn Postgres app + native Saver/Store, bổ sung durable stream journal trước SSE và mô hình branch riêng; chưa triển khai hoặc benchmark.

## Đối chiếu nhanh

| Khía cạnh | Codex local/app-server | TrueForge | Onyx chat thường | Open WebUI |
|---|---|---|---|---|
| Kho bền vững chính | Rollout filesystem + nhiều SQLite DB theo trách nhiệm | PostgreSQL hoặc SQLite qua adapter | PostgreSQL | SQLite mặc định hoặc PostgreSQL |
| Hội thoại | Thread metadata | Session | ChatSession | Chat |
| Lịch sử | Turn/item projection từ rollout | Turn + context log + event được chọn lưu | Message tree + tool rows | JSON history và normalized message rows cùng tồn tại |
| Nhánh | Fork thread theo lineage và biên lịch sử | Parent turn + context/capability snapshot | Parent/latest-child/preferred-response | Parent/children/current message, fork sao chép đường tổ tiên |
| Response đang dở | Active-turn snapshot RAM; delta text không được persist từng token | Redis Streams TTL, fallback RAM | Chunk NDJSON nén trong shared cache | Snapshot + delta trong Redis string, fallback RAM |
| Reload khi producer sống | Durable history + active snapshot + notification | Replay từ seq rồi tail | Replay chunk rồi poll tail | SQL history được overlay partial + Socket.IO live |
| Worker/pod chết | Không bảo đảm giữ delta chưa durable | Replay data không tự tiếp tục execution | Cache không tự phục hồi model/writer | Registry không phục hồi asyncio task |
| Memory | Pipeline memory riêng + job ownership | Capability state theo turn; chưa thấy generic cross-chat memory trong session-store đã đọc | User memory + provenance | SQL memory + vector index theo user |

Nguồn và giới hạn của mỗi ô nằm trong tài liệu dự án tương ứng. Các đường Build/Craft của Onyx được phân tích riêng trong [onyx.md](./onyx.md); không gán hành vi của chúng cho chat thường.

### Bổ sung LibreChat và NextChat

| Khía cạnh | LibreChat | NextChat |
|---|---|---|
| Kho bền vững chính | MongoDB/Mongoose cho conversation, message, tool, memory và file metadata | Zustand persisted store: JSON trong IndexedDB trình duyệt, fallback localStorage |
| Transcript | Conversation metadata tách Message documents | Session chứa mảng messages trong store snapshot; không normalized message database |
| Nhánh | `parentMessageId`, fork sao chép lineage và mapping ID | Mảng message; sửa/retry/copy không tương đương message tree đầy đủ |
| Response đang dở | Redis job metadata và chunk log, content cache trong runtime; fallback RAM | `onUpdate` cập nhật message và kích hoạt async persistence ở trình duyệt |
| Reload | Đường agent resumable gửi sync chứa state tích lũy/pending events rồi chuyển live, có xử lý frontier và generation | Hydrate phần text đã lưu; không tự nối stream đang chạy trước reload |
| Nhiều pod | Redis chia sẻ job/chunks và vận chuyển event; phải giữ đúng owner/tenant/generation | Backend proxy không sở hữu lịch sử; nhiều pod không chia sẻ chat state ở các trình duyệt |
| Worker chết | Có các cơ chế lease, checkpoint và recovery theo scope; không cam kết tiếp tục tùy ý từ token cuối | Không có durable worker/run queue được tìm thấy trong đường chat khảo sát |
| Memory | User key/value memory và agent partition tùy chọn; checkpoint là lớp khác | Summary/context trong session, không phải memory store xuyên chat ở backend |
| Sync | Persistence trung tâm và reconnect protocol | Đồng bộ snapshot từ xa; merge ID mới không giải quyết sửa/xóa message cùng ID |

LibreChat là dự án **duy nhất trong sáu dự án có dùng LangGraph** — qua ba tầng: LangGraph → `@librechat/agents` (package riêng của họ) → app ([librechat.md §11](./librechat.md)). Cách họ lưu lịch sử chat được đọc lại chi tiết ở [§12](./librechat.md): rows + cursor pagination, nhưng cursor thiếu tiebreak và `conversation.messages` bị ghi đè O(n) mỗi lần `saveConvo`. LibreChat đáng đọc sâu cho bài toán **snapshot + frontier + live**, identity generation và chống stale writer. Phạm vi resumable cần phân biệt agent route với các endpoint khác; không khẳng định toàn sản phẩm có cùng hành vi. NextChat là ví dụ kiến trúc **lưu ở client**: partial text có thể được lưu local, nhưng điều đó khác với detached execution và resume stream nhiều pod.

## Những kết luận cần sửa so với khảo sát cũ

Đối với bốn repository này, ưu tiên bằng chứng đã dẫn trong bộ tài liệu mới khi đối chiếu [chat-schema-comparison.md](../architecture/chat-schema-comparison.md):

1. TrueForge **hiện có cascade FK** và đã bỏ tenant khỏi khóa của nhiều bảng con; migration khởi tạo không đại diện schema sau cùng.
2. Codex `thread_realtime_items` **không phải kho partial text của chat thường**. `root_turn_id` cũng không đủ chứng minh message tree edit/regenerate.
3. Codex hiện định nghĩa **7 database specs**; không phải mọi SQLite data đều có thể dựng lại từ rollout.
4. Open WebUI thêm `chat_message` nhưng **vẫn dual write JSON history**; không thể kết luận đã bỏ blob.
5. Onyx dùng `native_enum=False` không có nghĩa mọi enum đã được database CHECK bảo vệ.
6. Hai migration response/checkpoint mới của Onyx chưa tìm thấy runtime caller trong phạm vi tìm kiếm đã ghi; không coi là bằng chứng durable recovery đang hoạt động.

## Cơ sở cho bước thiết kế schema của mình

Các điểm dưới là định hướng rút ra từ khảo sát, chưa thay thế tài liệu kiến trúc hay chốt DDL:

- **Database ứng dụng:** quản lý ai sở hữu conversation, title, branch được chọn, mapping native thread/checkpoint, logical run/attempt, transcript/tool/attachment và tác vụ metadata.
- **Native LangGraph:** tiếp tục dùng Saver cho checkpoint/state, Store cho memory xuyên thread. Không tự tạo bản sao các bảng nội bộ của thư viện để thay implementation native.
- **Live stream:** lưu accumulated response/projection cùng event tail có retention và watermark nhất quán. Không nhầm ordinal transcript, cache chunk cursor và stream event seq là cùng một thứ.
- **Thực thi:** durable queue, quyền sở hữu attempt, generation fencing, cancel intent và tool idempotency phải được thiết kế rõ. Shared cache giải quyết subscriber nhiều pod, không tự giải quyết worker crash.
- **Nhánh:** xác định cả lịch sử UI và state/context dùng để thực thi. Parent transcript không đủ nếu native checkpoint vẫn ở nhánh khác.
- **Index:** bắt đầu từ truy vấn owner/sidebar, message parent, history paging, active run, pending job và recovery. Đo contention trước khi thêm partition hoặc sao chép fillfactor từ sản phẩm khác.
- **Generation identity:** tham khảo LibreChat về việc phân biệt conversation lâu dài với generation đang chạy, kiểm tra generation khi attach/stop/publish/finalize và nối snapshot với live. Không dùng riêng conversation ID để nhận diện mọi lần chạy.
- **Local cache và sync:** NextChat cho thấy lưu được partial ở trình duyệt chưa đủ cho reload rồi stream tiếp. Nếu có local cache, nó vẫn cần reconcile với state/cursor của server; snapshot sync không thay durable execution hoặc event protocol.

Các lựa chọn đã thống nhất vẫn giữ nguyên: backend custom, không dùng CopilotKit; `from ag_ui_langgraph import LangGraphAgent` emit AG-UI; SSE run/connect; reload bằng snapshot + watermark + tail. Xem [API contract](../chat_development/chat-agent-api-contract.md) và [thiết kế nền tảng](../chat_development/langgraph-oss-agent-platform-design.md).

## Cách đọc và mức kiểm chứng

Mỗi file có sơ đồ, bảng khóa/index và liên kết source tuyệt đối kèm số dòng. Quan hệ logic được phân biệt với FK; schema tồn tại trong migration được phân biệt với tính năng có runtime caller. Các nhận xét về scale là đánh giá từ code, chưa có benchmark.

Chưa chạy migration hoặc truy cập dữ liệu của các dự án nguồn. Chưa thực hiện EXPLAIN, load test, Redis failure hay kill-worker. Bộ tài liệu này phục vụ chọn mô hình và xác định invariant trước khi viết DDL của hệ thống mình.

Review tiếp theo: [Mô hình bảng và truy vấn production](../chat_development/database-schema-review.md), đối chiếu use cases, ranh giới native LangGraph, catalogue bảng, constraints/indexes và tiêu chí nghiệm thu.
