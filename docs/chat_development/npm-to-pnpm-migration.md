# Chuyển từ npm sang pnpm: lộ ra 2 phantom dependency

## Vấn đề

Đổi package manager từ npm sang pnpm (`rm -rf node_modules package-lock.json && pnpm install`) làm build/typecheck **vỡ ngay**, dù code không hề thay đổi:

```
src/app/layout.tsx:4:1
Error: Module not found: Can't resolve 'katex/dist/katex.min.css'

src/lib/latex.ts(1,55): error TS2307: Cannot find module 'remend' or its corresponding type declarations.
```

Cả `katex` và `remend` đều được import trực tiếp trong code (`layout.tsx`, `latex.ts`) nhưng **không hề có trong `package.json`** — chúng chỉ là dependency gián tiếp của `@streamdown/math` (`katex`) và `streamdown` (`remend`).

npm cài đặt theo kiểu **flat node_modules**: mọi gói, kể cả dependency gián tiếp, đều được trải phẳng vào một thư mục `node_modules/` duy nhất ở gốc, nên `import "remend"` vẫn resolve được dù chưa khai báo — một "phantom dependency". pnpm thì ngược lại: mỗi gói chỉ thấy đúng những gì **chính nó** khai báo là dependency, nhờ cấu trúc symlink về content-addressable store (`node_modules/.pnpm/...`) — phantom dependency bị chặn đứng ngay từ bước resolve module.

## Giải pháp

Khai báo tường minh mọi package được **import trực tiếp trong code của mình**, dù nó "tình cờ" chạy được qua npm nhờ transitive install — không dựa vào việc một package khác tiện thể kéo nó về:

```diff
  "dependencies": {
    ...
    "input-otp": "^1.5.0",
+   "katex": "^0.16.27",
    ...
    "react-resizable-panels": "^4.14.7",
    "recharts": "^3.8.0",
+   "remend": "^1.4.0",
    ...
  }
```

Version ghim theo đúng range mà gói cha (`@streamdown/math`, `streamdown`) yêu cầu, để tránh lệch version giữa bản `remend`/`katex` mình import trực tiếp và bản mà `streamdown` dùng nội bộ.

## Ví dụ sau khi xử lý

```bash
pnpm install   # thêm katex + remend làm direct dependency
pnpm exec next build    # Compiled successfully, 0 lỗi
pnpm exec tsc --noEmit  # exit 0
```

## Bài học

**pnpm không phải chỉ "nhanh hơn npm" — nó còn là một bài kiểm tra ẩn cho `package.json`.** Nếu code chạy được dưới npm nhưng vỡ ngay khi đổi sang pnpm với cùng code, gần như chắc chắn nguyên nhân là phantom dependency: một package được `import` thẳng trong code nhưng không được khai báo, chỉ "ăn ké" qua một dependency khác. Quy tắc chung: **import gì thì khai báo đúng cái đó trong `package.json`**, bất kể package manager nào — pnpm chỉ là thứ buộc phải tuân theo quy tắc này ngay lập tức thay vì âm thầm hoạt động sai cho đến khi một bản nâng cấp vô tình gỡ bỏ transitive dependency đó.
