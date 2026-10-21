# Dòng tóm tắt sống cho reasoning khi thu gọn

Tham khảo từ: deepseek-harness (`ReasoningRow.tsx`, note `2026-08-02-web-thinking-tail-scroll`).

> Ghi chú: `ReasoningContent` tự áp dụng chuyển đổi delimiter LaTeX qua `remend` handler (xem [`math-rendering.md`](./math-rendering.md)), nên ở đây chỉ truyền thẳng `reasoning`, không cần gọi hàm chuẩn hoá thủ công nào.

## Vấn đề

`ReasoningTrigger` (AI Elements) chỉ hiện một nhãn **tĩnh** trong lúc đang stream, không quan tâm nội dung thật đang chảy về:

```tsx
// src/components/ai-elements/reasoning.tsx (mặc định của thư viện)
const defaultGetThinkingMessage = (isStreaming: boolean, duration?: number) => {
  if (isStreaming || duration === 0) {
    return <Shimmer duration={1}>Thinking...</Shimmer>; // luôn chỉ ra đúng chữ này
  }
  ...
};
```

Hệ quả: nếu người dùng không bấm mở panel reasoning ra, họ **không có cách nào phân biệt** "model đang suy nghĩ nhanh" với "model bị treo/mạng rớt" — cả hai trường hợp đều hiện y hệt nhau: chữ "Thinking..." nhấp nháy.

### Ví dụ dữ liệu thật (đo được khi test câu hỏi "41×53, think step by step")

| Thời điểm | `reasoning` text (tích lũy tới lúc đó) | UI hiện (trước khi sửa) |
|---|---|---|
| t=0ms | `""` | `Thinking...` |
| t=300ms | `"The user asks a simple arithmetic\nquestion. Let me compute: 41 × 53 = 41 × 50 + 41 × 3 = 2050 + 123"` | `Thinking...` |
| t=600ms | `"...= 2050 + 123 = 2173.\n\nI could use the tool but it's not needed."` | `Thinking...` |
| t=5000ms (model bị treo, không có delta mới) | giống hệt t=600ms | `Thinking...` (y hệt, không phân biệt được) |

## Giải pháp

Khi đang streaming, thay nhãn tĩnh bằng **dòng cuối cùng không rỗng** của reasoning text. Khi đã xong, quay lại nhãn tĩnh "Thought for a few seconds" như cũ.

```ts
// src/app/page.tsx
function latestLine(text: string): string {
  const visible = text.trimEnd();
  const newline = visible.lastIndexOf("\n");
  return newline === -1 ? visible : visible.slice(newline + 1);
}

function ReasoningSummary({ reasoning, isStreaming }: { reasoning: string; isStreaming: boolean }) {
  const { isOpen } = useReasoning();

  return (
    <>
      <BrainIcon className="size-4 shrink-0" />
      {isStreaming ? (
        <span className="min-w-0 flex-1 truncate text-left">{latestLine(reasoning)}</span>
      ) : (
        <span>Thought for a few seconds</span>
      )}
      <ChevronDownIcon
        className={cn("size-4 shrink-0 transition-transform", isOpen ? "rotate-180" : "rotate-0")}
      />
    </>
  );
}
```

Gắn vào `ReasoningTrigger` bằng cách truyền `children` tùy chỉnh (ghi đè nhãn mặc định của thư viện):

```tsx
<Reasoning isStreaming={isReasoningStreaming}>
  <ReasoningTrigger>
    <ReasoningSummary isStreaming={isReasoningStreaming} reasoning={reasoning} />
  </ReasoningTrigger>
  <ReasoningContent>{reasoning}</ReasoningContent>
</Reasoning>
```

Dùng CSS `truncate` (ellipsis khi tràn dòng) thay vì cơ chế scroll ngang bằng tay (`scrollLeft` + rAF) mà deepseek-harness làm — họ cần điều đó vì muốn chữ "trôi" theo đúng cuối dòng khi dòng quá dài; với scaffold này, `truncate` đã đủ giải quyết vấn đề cốt lõi (biết model còn sống hay không) mà không cần thêm logic JS.

Lưu ý quan trọng (lấy từ note gốc của deepseek-harness): **không** dùng animation chạy chữ giả lập (CSS marquee độc lập với dữ liệu thật) — nó sẽ tiếp tục chạy ngay cả khi model bị treo, khiến model chậm trông như đang chạy nhanh. Dòng tóm tắt phải phản ánh đúng nhịp dữ liệu thật đến, đứng yên khi không có delta mới.

## Ví dụ sau khi xử lý

Test thật qua Playwright với câu hỏi "Cho hai số thực x, y thỏa mãn x²+y²+xy=3...":

**Lúc đang stream (3 giây sau khi gửi), accessibility tree của nút trigger:**
```
button "s^2 = ( (r - 1)^2 ) /4 = (r^2 -2r +1)/4 = (7 -2r +1)/4 =" [expanded]
```
→ Chính là dòng cuối cùng model vừa gõ xong, cập nhật liên tục theo từng delta mới.

**Sau khi hoàn tất:**
```
button "Thought for a few seconds"
```
→ Quay lại nhãn tĩnh như hành vi gốc, không đổi gì ở trạng thái settled.

Kết quả cuối (max P = (8+7√7)/2, min P = (8-7√7)/2) không đổi — thay đổi này thuần túy là presentation, không chạm vào logic tính toán/stream dữ liệu.
