# Gộp cập nhật reasoning vào 1 `requestAnimationFrame`

Tham khảo từ: deepseek-harness (note `2026-08-03-opt-in-reasoning-chunk-browser-stress`).

## Vấn đề

`useAgentChat` gọi `setMessages` ngay lập tức mỗi khi `onMessagesChanged` bắn — tức là **mỗi event AG-UI = một lần React render**, bất kể trình duyệt có kịp vẽ ra màn hình hay không.

```ts
// src/hooks/use-agent-chat.ts (trước khi sửa)
onMessagesChanged: ({ messages: updated }) => setMessages([...updated]),
```

Trình duyệt chỉ vẽ lại màn hình tối đa ~60 lần/giây (~16.7ms/khung hình). Nếu nhiều event đến dồn dập trong cùng một khung hình, các lần `setState` ở giữa bị khung hình tiếp theo ghi đè trước khi ai kịp nhìn thấy — hoàn toàn lãng phí.

### Ví dụ dữ liệu thật (log đo được, model nemotron, câu hỏi khó)

```
16224ms  onMessagesChanged  reasoning len=7
16224ms  onMessagesChanged  reasoning len=18   ← cùng 1 khung hình với dòng trên
16259ms  onMessagesChanged  reasoning len=20
16259ms  onMessagesChanged  reasoning len=21   ← cùng 1 khung hình với dòng trên
16260ms  onMessagesChanged  reasoning len=23
16261ms  onMessagesChanged  reasoning len=25
```

Với câu hỏi khó nhất test được, một lần chạy sinh ra **3175 event `REASONING_MESSAGE_CONTENT`** — tức 3175 lần gọi `setMessages` riêng lẻ. deepseek-harness stress test tới quy mô 100.000 chunk và xác nhận: gọi `setState` trực tiếp trên từng chunk làm nghẽn main thread (reconciliation + commit + layout cho từng lần, dù phần lớn không bao giờ được vẽ ra).

## Giải pháp

Gom nhiều lần gọi liên tiếp lại, chỉ thực sự `setState` **đúng 1 lần mỗi khung hình trình duyệt**, bằng `requestAnimationFrame`. Dữ liệu không bao giờ mất — luôn giữ bản mới nhất trong `ref`, chỉ số lần *render* bị giảm.

```ts
// src/hooks/use-agent-chat.ts (sau khi sửa)
const pendingMessagesRef = useRef<AGUIMessage[] | null>(null);
const frameRef = useRef<number | null>(null);

const scheduleMessages = useCallback((updated: AGUIMessage[]) => {
  pendingMessagesRef.current = updated;       // luôn cập nhật ngay, không mất data
  if (frameRef.current !== null) return;      // đã có 1 frame đang chờ rồi → không đặt thêm
  frameRef.current = requestAnimationFrame(() => {
    frameRef.current = null;
    if (pendingMessagesRef.current) setMessages(pendingMessagesRef.current);
  });
}, []);

// ...
onMessagesChanged: ({ messages: updated }) => scheduleMessages([...updated]),

// cleanup khi unmount — tránh setState sau khi component đã gỡ
return () => {
  unsubscribe();
  agentRef.current = null;
  if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
};
```

## Ví dụ sau khi xử lý

Với cùng chuỗi event ở trên, hành vi thay đổi như sau:

**Trước (không batch):**
```
16224ms: setMessages(len=7)   → React render #1
16224ms: setMessages(len=18)  → React render #2
16259ms: setMessages(len=20)  → React render #3
16259ms: setMessages(len=21)  → React render #4
16260ms: setMessages(len=23)  → React render #5
16261ms: setMessages(len=25)  → React render #6
→ 6 lần render trong ~37ms, nhưng trình duyệt chỉ vẽ được ~2 khung hình trong khoảng đó
→ 4/6 lần render bị ghi đè trước khi ai nhìn thấy — lãng phí hoàn toàn
```

**Sau (có batch bằng rAF):**
```
16224ms: scheduleMessages(len=7)   → đặt 1 rAF, lưu vào ref
16224ms: scheduleMessages(len=18)  → đã có rAF chờ sẵn, chỉ cập nhật ref = len=18
16259ms: scheduleMessages(len=20)  → ref = len=20
16259ms: scheduleMessages(len=21)  → ref = len=21
16260ms: scheduleMessages(len=23)  → ref = len=23
16261ms: scheduleMessages(len=25)  → ref = len=25
16266ms: [khung hình trình duyệt tới] → setState(len=25) → React render ĐÚNG 1 LẦN với bản mới nhất
→ 1 lần render thay vì 6, hiển thị đúng nội dung mới nhất, không thiếu chữ nào
```

Test thật qua Playwright (câu hỏi toán khó, dùng model nemotron) xác nhận: UI vẫn cập nhật mượt theo thời gian thực (dòng tóm tắt sống vẫn thay đổi liên tục, xem `live-reasoning-summary.md`), build + lint sạch, không có hồi quy nào về mặt hiển thị hay nội dung cuối cùng.

Ở quy mô hiện tại (vài trăm đến ~3000 event/câu hỏi), React 18 tự xử lý ổn ngay cả không có thay đổi này — đây là khoản phòng ngừa trước, giá rẻ (không đổi logic nghiệp vụ, chỉ gộp thời điểm render), chỉ thực sự phát huy giá trị khi dùng model có reasoning cực dài hoặc chạy trên máy yếu.
