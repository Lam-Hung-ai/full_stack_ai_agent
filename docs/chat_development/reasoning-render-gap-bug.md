# Bug: reasoning có dữ liệu nhưng UI không hiển thị gì

## Vấn đề

Sau khi bật `OPENROUTER_REASONING_EFFORT`, reasoning/thinking của model đáng lẽ phải hiện dần trong lúc model đang suy nghĩ (trước khi có câu trả lời cuối). Thực tế: panel reasoning **không hiện gì cả** trong suốt thời gian model suy nghĩ — chỉ bất ngờ xuất hiện đầy đủ sau khi cả câu trả lời đã xong.

Chẩn đoán sai đầu tiên: kết luận "chắc do model suy nghĩ quá nhanh, mắt không kịp thấy" — kết luận này **sai**, và chỉ bị bác bỏ khi người dùng yêu cầu kiểm tra trực tiếp ở tầng network:

> "khoan tập trung vào tại sao nó không streaming reasoning đi rồi xem bằng Fetch/XHR trình duyệt EventStream vẫn thấy reasoning"

Mở tab Network → EventStream của request `/agent`, thấy rõ các event `REASONING_MESSAGE_CONTENT` bắn về **liên tục, đúng nhịp**, hàng nghìn event cho một câu hỏi dài (xem thêm [`raf-batched-reasoning-updates.md`](./raf-batched-reasoning-updates.md)). Vậy dữ liệu luôn tới đúng — vấn đề nằm ở tầng render của React, không phải ở backend/stream.

## Nguyên nhân thật

Trong AG-UI, thứ tự event cho một lượt có reasoning là:

```
RUN_STARTED
REASONING_START
REASONING_MESSAGE_START
REASONING_MESSAGE_CONTENT  (lặp lại nhiều lần)
REASONING_MESSAGE_END
REASONING_END
TEXT_MESSAGE_START   ← message "assistant" CHỈ được tạo ra từ đây
TEXT_MESSAGE_CONTENT
TEXT_MESSAGE_END
RUN_FINISHED
```

`@ag-ui/client` tạo ra một message `role: "reasoning"` riêng khi reasoning bắt đầu — nhưng message `role: "assistant"` chỉ tồn tại sau `TEXT_MESSAGE_START`, tức là **sau khi reasoning đã kết thúc**.

`buildTurns()` ở `page.tsx` ghép reasoning vào message assistant đi theo sau nó:

```ts
function buildTurns(messages: AGUIMessage[]): Turn[] {
  const turns: Turn[] = [];
  let pendingReasoning: string | undefined;
  for (const message of messages) {
    if (message.role === "reasoning") {
      pendingReasoning = message.content;
      continue; // chỉ giữ tạm trong biến local, KHÔNG push vào turns
    }
    if (message.role === "user" || message.role === "assistant") {
      turns.push({ message, reasoning: message.role === "assistant" ? pendingReasoning : undefined });
      pendingReasoning = undefined;
    }
  }
  return turns; // bản gốc dừng ở đây
}
```

Trong suốt giai đoạn reasoning, `pendingReasoning` được cập nhật liên tục nhưng **không có message assistant nào tồn tại để gắn nó vào** → vòng lặp kết thúc mà không `push` gì cả → `turns` không có phần tử nào chứa reasoning → JSX không render gì → UI trông như "không nhận được dữ liệu", dù dữ liệu luôn ở đó.

## Giải pháp

Thêm một turn giả (placeholder) ngay sau vòng lặp, nếu vẫn còn `pendingReasoning` chưa được gắn vào đâu — tức là reasoning đang chảy nhưng assistant message thật chưa xuất hiện:

```ts
// src/app/page.tsx
if (pendingReasoning !== undefined) {
  turns.push({
    message: { id: "__pending-reasoning__", role: "assistant", content: "" },
    reasoning: pendingReasoning,
  });
}
return turns;
```

Khi `TEXT_MESSAGE_START` thật sự bắn, message assistant thật xuất hiện trong `messages`, turn giả này tự nhiên bị thay thế ở lần render tiếp theo (reasoning được gắn đúng vào message thật).

## Bài học

Khi dữ liệu stream "biến mất" giữa backend và UI, **luôn xác minh ở tầng network trước khi nghi ngờ model hoặc kết luận "do quá nhanh"**. Nếu network tab cho thấy dữ liệu tới đúng nhịp, bug chắc chắn nằm ở logic render — cụ thể ở đây là một giả định ngầm sai: "cứ có `pendingReasoning` thì sẽ sớm có message để gắn vào", trong khi thứ tự event thực tế của protocol lại đặt `TEXT_MESSAGE_START` sau toàn bộ reasoning, không phải trước hay xen kẽ.
