# Nhật ký phát triển (kinh nghiệm & quyết định kỹ thuật)

Tập hợp các ghi chú về những vấn đề thực tế gặp phải, cách chẩn đoán và giải pháp trong quá trình xây dựng `agent_project` (backend FastAPI + LangGraph, frontend Next.js + AI Elements, giao tiếp qua AG-UI protocol). Mục đích: để lần sau gặp vấn đề tương tự (hoặc đọc lại code) thì hiểu được **tại sao** code trông như vậy, không chỉ **cái gì**.

- [`ag-ui-manual-wiring.md`](./ag-ui-manual-wiring.md) — vì sao `/agent` được nối tay thay vì dùng `add_langgraph_fastapi_endpoint`.
- [`reasoning-render-gap-bug.md`](./reasoning-render-gap-bug.md) — bug reasoning "có dữ liệu nhưng không hiển thị", cách tìm ra nguyên nhân thật (qua Network tab) thay vì đoán mò.
- [`live-reasoning-summary.md`](./live-reasoning-summary.md) — dòng tóm tắt sống thay cho nhãn "Thinking..." tĩnh, để phân biệt model đang chạy hay bị treo.
- [`raf-batched-reasoning-updates.md`](./raf-batched-reasoning-updates.md) — gộp nhiều lần `setState` liên tiếp vào 1 `requestAnimationFrame` khi reasoning stream quá nhanh.
- [`math-rendering.md`](./math-rendering.md) — hành trình xử lý hiển thị công thức toán (singleDollarTextMath, delimiter `\(...\)`/`\[...\]`, so sánh với deepseek-harness, và kết luận không cần system prompt nhắc về toán).
- [`npm-to-pnpm-migration.md`](./npm-to-pnpm-migration.md) — chuyển sang pnpm lộ ra 2 phantom dependency (`katex`, `remend`) mà npm's flat node_modules từng che giấu.

Hai ghi chú `live-reasoning-summary.md` và `raf-batched-reasoning-updates.md` ban đầu nằm ở `frontend/docs/notes/` — gộp về đây để toàn bộ "kinh nghiệm phát triển" nằm một chỗ, tách khỏi code của từng app.
