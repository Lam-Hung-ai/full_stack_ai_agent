# Hành trình xử lý hiển thị công thức toán học

## Vấn đề 1 — `$$...$$` đẹp, `$...$` không render

Model trả lời có cả math inline (`$x^2$`) và math block (`$$...$$`). Chỉ `$$...$$` render đúng bằng KaTeX; `$...$` hiện ra y nguyên dạng text thô (`$x^2$`).

**Nguyên nhân:** `remark-math` (thư viện gốc) mặc định `singleDollarTextMath: true`, nhưng `@streamdown/math` — gói bọc KaTeX cho Streamdown — export sẵn một plugin `math` với option này bị tắt (`false`). Dùng thẳng export mặc định đó là tắt luôn nhận diện `$...$`.

**Giải pháp:** tự tạo plugin bằng `createMathPlugin` với option đúng, thay vì dùng export mặc định:

```ts
// frontend/src/lib/math-plugin.ts
import { createMathPlugin } from "@streamdown/math";
export const mathPlugin = createMathPlugin({ singleDollarTextMath: true });
```

## Vấn đề 2 — `\(...\)` / `\[...\]` không bao giờ render

Model đôi khi viết công thức theo kiểu LaTeX gốc: `\(x^2\)`, `\[\int...\]` thay vì `$x^2$`/`$$...$$`. Các đoạn này hiện ra với dấu ngoặc trần, không có backslash — vì cơ chế escape của Markdown **nuốt mất** dấu `\` đứng trước `(`/`[`, để lại ngoặc trơ không ai parse.

`remark-math` chỉ parse delimiter `$`/`$$`, không biết gì về `\(...\)`/`\[...\]`.

**Giải pháp ban đầu:** viết hàm `normalizeLatexDelimiters()` quét regex, gọi thủ công tại từng nơi render (`page.tsx`) trước khi đưa text vào `MessageResponse`/`ReasoningContent`.

**Giải pháp sau khi refactor:** chuyển thành một `remend` handler, đăng ký qua prop `remend={{ handlers: [...] }}` ngay tại `MessageResponse`/`ReasoningContent` — không cần gọi tay ở `page.tsx` nữa, mọi nơi dùng Streamdown đều tự động được xử lý, và chạy chung một lượt với các phép "hoàn thiện markdown chưa đầy đủ" khác mà `remend` đã làm (đóng `**...**`, `` ` ``, `$$...` còn thiếu dấu đóng khi đang stream dở).

```ts
// frontend/src/lib/latex.ts
import { isWithinCodeBlock, type RemendHandler } from "remend";

export const latexDelimiterHandler: RemendHandler = {
  name: "latex-delimiters",
  priority: 10, // chạy trước các handler mặc định của remend (default 100)
  handle(text) {
    const rewrite = (input: string, pattern: RegExp, format: (expr: string) => string) =>
      input.replace(pattern, (match, expr, offset: number) =>
        isWithinCodeBlock(input, offset) ? match : format(expr),
      );
    let result = text;
    result = rewrite(result, /\\\[([\s\S]*?)\\\]/g, (expr) => `$$${expr}$$`);
    result = rewrite(result, /\\\(([\s\S]*?)\\\)/g, (expr) => `$${expr}$`);
    return result;
  },
};
```

Dùng `isWithinCodeBlock` (có sẵn trong `remend`) để **không** viết đè những đoạn `\(...\)` xuất hiện bên trong code block mẫu (ví dụ model đang giải thích cú pháp LaTeX bằng ví dụ code) — nếu không, ví dụ code sẽ bị biến thành công thức render thay vì giữ nguyên dạng text.

## So sánh với deepseek-harness

Đọc source của `deepseek-harness` (dự án tham chiếu riêng, không phải thư viện public) cho thấy họ giải quyết vấn đề 2 ở tầng sâu hơn hẳn: viết hẳn một micromark extension (`mathCompatibility.ts`) để `\(...\)`/`\[...\]` trở thành delimiter **hạng nhất** trong grammar, ngang hàng với `$`/`$$` — không cần quét regex sau khi parse.

Về mặt chức năng, cách tiếp cận regex + `remend` handler ở đây cho ra kết quả tương đương cho use case hiện tại (không cần parse incremental ở quy mô cực lớn như họ), đổi lại đơn giản hơn nhiều để viết và bảo trì.

## Vấn đề 3 — mơ hồ giữa tiền tệ và toán học (chưa giải quyết)

Bật `singleDollarTextMath: true` có đánh đổi: văn xuôi thông thường như `"giá $100 và doanh thu là $500"` bị đọc nhầm thành **một** inline-math span (`100 và doanh thu là 500` bị gộp lại giữa hai dấu `$`), hiển thị ra chữ bị dính nhau kiểu in nghiêng toán học.

Đã xác nhận: đây **không phải lỗi riêng** của cách làm ở đây — `deepseek-harness`, dự án tham chiếu với renderer markdown tự viết tay rất kỹ, cũng mắc đúng lỗi này trên web client chính thức của họ (xác nhận qua ảnh chụp màn hình thực tế). Đây là giới hạn cố hữu của quy ước "một dấu `$` là inline math" khi áp dụng lên văn bản tự nhiên có nhắc tới tiền tệ — không có cách nào phân biệt thuần túy bằng cú pháp.

Hai hướng từng cân nhắc:
1. Bật `singleDollarTextMath: true` + thêm chỉ dẫn trong system prompt bảo model escape tiền tệ thành `\$`.
2. Tắt hẳn `singleDollarTextMath`, chấp nhận inline math dạng `$...$` không bao giờ render (chỉ `$$...$$` render).

**Quyết định hiện tại:** không chọn cả hai — xem mục "Kết luận" bên dưới. Đây vẫn là một đánh đổi đã biết, chưa có giải pháp triệt để, không phải điểm cần "sửa cho xong" ngay.

## Kết luận: không cần system prompt nhắc về toán

Yêu cầu rõ ràng được đặt ra: UI/renderer phải tự xử lý đúng bất kể model chọn định dạng gì, **không** dựa vào một đoạn system prompt dạy model cách viết công thức.

Đã gỡ bỏ hoàn toàn phần hướng dẫn định dạng toán khỏi `SYSTEM_PROMPT` (`backend/src/agent_backend/agent_graph.py`), chỉ giữ lại mô tả vai trò chung chung, rồi test trực tiếp qua Playwright với 2 câu hỏi:

1. Giải phương trình bậc hai — model tự chọn trộn lẫn code-span (``` `ax^2+bx+c=0` ```) và `$$...$$` thật cho công thức nghiệm chính → cả hai dạng hiển thị đúng ý đồ (code-span hiện dạng code, `$$...$$` render KaTeX đẹp).
2. Bài toán max/min phức tạp (`P = x³+y³-3xy` với ràng buộc `x²+y²+xy=3`), yêu cầu "trình bày lời giải chi tiết bằng LaTeX" — model tự dùng `\(...\)`, `\[...\]`, và `\boxed{...}` ở kết luận cuối. Toàn bộ phần dẫn giải dài (phân số lồng nhau, căn bậc hai, chỉ số dưới, giá trị gần đúng) render đúng. Một đoạn `\boxed{...}` ban đầu trông như lỗi ("[ \boxed{ \begin{aligned}...") hoá ra chỉ là trạng thái **đang stream dở** (nút Submit vẫn hiện icon dừng) — sau khi stream xong, `remend` tự hoàn thiện phần markdown còn thiếu và đoạn này render đúng thành KaTeX.

**Kết quả:** `singleDollarTextMath: true` + `latexDelimiterHandler` đủ để render đúng mọi kiểu delimiter mà model tự nhiên chọn, không cần ràng buộc model qua system prompt. Đánh đổi duy nhất còn lại là mơ hồ tiền tệ ở Vấn đề 3, vốn là giới hạn chung của cả ngành (không riêng dự án này), và không được "vá" bằng cách thêm lại hướng dẫn system prompt — theo đúng yêu cầu đã đặt ra.
