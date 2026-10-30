# Vận hành chat

Tài liệu cho người triển khai và vận hành (S9). Biến môi trường đầy đủ ở `backend/.env.example`.

## 1. Dịch vụ cần có

| Dịch vụ | Dùng cho | Dev |
| --- | --- | --- |
| PostgreSQL 18 | Dữ liệu chat, checkpoint khi pause | `compose.yaml` (`postgres`) |
| Redis | Live view lượt đang chạy, stop qua process, rate limit | `compose.yaml` (`redis`) |
| S3-compatible | Tệp đính kèm | `compose.yaml` (`rustfs`) |
| SMTP | Lời mời, xác minh email, đặt lại mật khẩu | `compose.yaml` (`mailpit`, đọc ở :8025) |
| Langfuse (tuỳ chọn) | Trace, token, chi phí từng lượt | Đặt `LANGFUSE_*` |

## 2. Mỗi lần triển khai

```bash
cd backend
uv run db up                 # migration (dbmate)
uv run db checkpoints        # bảng của saver LangGraph
uv run iam sync-permissions  # danh mục quyền; owner nhận quyền mới (QD-24)
uv run storage setup         # bucket, CORS, hết hạn object tạm (lần đầu mỗi bucket)
```

Chạy hằng ngày (cron hoặc job lịch của nền tảng), mỗi lúc chỉ một bản:

```bash
cd backend && uv run storage cleanup
```

Lệnh xoá tệp đã tải lên nhưng không gắn vào câu hỏi nào sau 1 ngày (dòng `stored_files` trước, object sau), chuyển job copy bỏ dở quá 1 ngày sang `cancelled` và xoá byte của mọi bản copy đã huỷ; dòng của bản copy giữ lại vì message không bao giờ bị xoá (QD-30, RR-17, RR-18).

Từ S10:
- Migration tìm kiếm tạo extension `pg_trgm` và `unaccent` (gói contrib của PostgreSQL): user chạy `dbmate` phải có quyền `CREATE EXTENSION`, hoặc DBA tạo trước.
- `uv sync` cài thêm `openpyxl` (tool tạo XLSX).
- Sau `iam sync-permissions`, vai trò owner có quyền `tool.create_file`; vai trò khác gán ở màn Vai trò.

## 3. Proxy trước backend (RR-13)

Stream SSE phải đi qua không bị gom. Backend đã gửi `Cache-Control: no-cache` và `X-Accel-Buffering: no`; proxy vẫn cần tắt buffer và nén cho đường dẫn API, và đặt timeout đọc dài hơn một lượt:

```nginx
location /api/v1/ {
    proxy_pass http://backend:8000;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_cache off;
    gzip off;
    proxy_read_timeout 3600s;
    proxy_set_header Connection "";
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Frontend Next đã tắt nén (L-05).

Rate limit đếm theo IP client mà uvicorn đưa vào `request.client`. Sau proxy, chạy uvicorn với địa chỉ của proxy (nginx, hoặc server Next khi rewrite `/api/v1`) để nó lấy IP thật từ `X-Forwarded-For`; không đặt `*` vì client sẽ tự khai IP:

```bash
uv run uvicorn app.main:app --proxy-headers --forwarded-allow-ips=10.0.0.5
```

## 4. Sức chứa và backpressure

- Mỗi process chạy tối đa `MAX_CONCURRENT_TURNS` lượt cùng lúc; tối đa `MAX_QUEUED_TURNS` lượt chờ slot. Quá đó, gửi/sửa/tạo lại/trả lời nhận 503 `server_busy` kèm `Retry-After: 5`, không ghi gì vào database (QD-29).
- Rate limit đếm chung qua Redis (Redis lỗi thì mỗi process tự đếm trong bộ nhớ), cửa sổ cố định (QD-30):
  - `auth`: đăng ký, đăng nhập, xác minh email, đặt lại mật khẩu, nhận lời mời; `AUTH_RATE_LIMIT`/phút mỗi IP.
  - `session`: refresh, session, đăng xuất; 300/phút mỗi IP.
  - `shares`: xem share và tệp của share; 300/phút mỗi IP. Copy share dùng bucket `share-copy` theo `AUTH_RATE_LIMIT`.
  - Gửi lời mời: 50 thư/giờ mỗi người gửi, bất kể IP.
- Mỗi lượt gửi cho model tối đa 20 MB tệp đính kèm, ưu tiên câu hỏi mới nhất; tệp cũ hơn chỉ được nêu tên.

- Mỗi chat mới gọi model thêm một lần để đặt tên (tắt reasoning, tối đa 40 token); log `Conversation title suggested` ghi số token.

## 5. Log và trace

- `LOG_FORMAT=json`: mỗi dòng một JSON có `request_id`. Mỗi lượt có một dòng `Assistant turn ended` với `assistant_id`, `conversation_id`, `workspace_id`, `user_id`, `status`, `resumed`, `duration_ms`, `input_tokens`, `output_tokens`, `models`. Không ghi nội dung chat.
- Langfuse: đặt `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`. Session là conversation, user là người hỏi. Trace chứa prompt và câu trả lời: chỉ dùng instance được phép giữ nội dung chat.

## 6. Load test

Chạy backend với model giả rồi chạy công cụ:

```bash
AGENT_FAKE_MODEL=true REGISTRATION_ENABLED=true AUTH_RATE_LIMIT=100000 \
  uv run uvicorn app.main:app --port 8002
uv run loadtest --base-url http://localhost:8002 --users 30 --turns 3
```

Kết quả 30/10/2026, một process, `MAX_CONCURRENT_TURNS=10`, `MAX_QUEUED_TURNS=20`, model giả 60 từ × 20 ms (~1,2 s mỗi câu trả lời), PostgreSQL và Redis local:

| Kịch bản | Lượt xong | Token đầu p50 / p95 | Cả lượt p50 / p95 | Connect p95 | History p95 | Lỗi |
| --- | --- | --- | --- | --- | --- | --- |
| 10 người × 5 lượt (vừa đủ slot) | 50/50, 5,6 lượt/s | 205 / 328 ms | 1 551 / 1 761 ms | 29 ms | 23 ms | 0 |
| 30 người × 3 lượt (đủ slot + hàng đợi) | 90/90, 5,2 lượt/s | 2 985 / 3 673 ms | 4 418 / 5 121 ms | 41 ms | 38 ms | 0 |
| 60 người × 1 lượt (vượt trần 30) | 33/60 | 2 409 / 4 718 ms | 3 871 / 5 954 ms | 300 ms | 84 ms | 27 × 503 `server_busy` |

Đọc số liệu:
- Phần của hệ thống trước token đầu khoảng 200–330 ms khi còn slot; khi xếp hàng, token đầu gồm cả thời gian chờ slot.
- Thông lượng bị chặn bởi số slot × độ dài câu trả lời, đúng thiết kế; tăng `MAX_CONCURRENT_TURNS` hoặc số process (Redis đã cho connect/stop qua process, S5) để tăng.
- Vượt trần thì lượt thừa bị từ chối ngay, lượt đã nhận vẫn chạy hết.

Load test tạo tài khoản `load-<run>-<n>@example.com` trong database đang trỏ tới; chạy trên database thử.

Đo lại 30/10/2026 sau S10 (index tìm kiếm trên `messages`, đặt tên chat mới), 10 người × 5 lượt: 50/50, token đầu p50 247–264 / p95 370–399 ms qua hai lần đo (lần đầu khi còn nguội p95 879 ms), cả lượt p95 ~1,7 s, không lỗi. So với S9 chậm thêm khoảng 50 ms ở token đầu.

## 7. Còn theo dõi

- RR-01, RR-10: process chết giữa lượt thì lượt đó không khôi phục; worker riêng chưa cần theo số liệu trên.
- RR-17: đã có `storage cleanup` (QD-30); mỗi lượt vẫn đọc lại tệp (tối đa 20 MB).
- RR-18: copy chạy trong request; dòng của bản copy huỷ chưa purge.
