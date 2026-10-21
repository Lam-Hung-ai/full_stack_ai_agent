This is the [Next.js](https://nextjs.org) frontend, bootstrapped with `create-next-app` and using [shadcn/ui](https://ui.shadcn.com) + [AI Elements](https://ui.shadcn.com/docs/ai-elements) for the chat UI.

## Setup

```bash
cp .env.example .env.local
# edit .env.local if the backend isn't on http://localhost:8000
pnpm install
```

## Run

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000). The chat page (`src/app/page.tsx`) talks to the backend over the [AG-UI protocol](https://docs.ag-ui.com):

- `src/hooks/use-agent-chat.ts` — wraps `@ag-ui/client`'s `HttpAgent`, subscribes to its message/event stream, and exposes `messages` + `sendMessage`.
- `src/app/api/agent/route.ts` — proxies the AG-UI SSE request/response to the FastAPI backend's `/agent` (see `../backend`), so the browser only ever talks to this origin.

## UI components

- `src/components/ui/*` — every shadcn/ui base component (`pnpm dlx shadcn@latest add --all`).
- `src/components/ai-elements/*` — all AI Elements patterns (conversation, message, prompt-input, reasoning, tool, sources, etc.), installed from the AI SDK registry (`pnpm dlx shadcn@latest add https://registry.ai-sdk.dev/all.json`).
- `Tool`/`ToolHeader`/`ToolContent`/`ToolInput`/`ToolOutput` render AG-UI tool calls — `page.tsx` maps an AG-UI `ToolCall` (plus its matching `tool` result message, by `toolCallId`) into the shape these expect.
- `Reasoning`/`ReasoningTrigger`/`ReasoningContent` render the model's reasoning/thinking — `page.tsx` pairs an AG-UI `reasoning`-role message with the assistant message that follows it (no shared id between them).

To add more shadcn components later: `pnpm dlx shadcn@latest add <name>`.

## Math rendering

`MessageResponse` and `ReasoningContent` render Markdown through Streamdown with:

- `src/lib/math-plugin.ts` — `@streamdown/math`'s KaTeX plugin, created with `singleDollarTextMath: true` (the package's own default export leaves this off, so single-`$` inline math like `$x^2$` would never be recognized — only `$$...$$`). `katex/dist/katex.min.css` is imported globally in `layout.tsx`.
- `src/lib/latex.ts` — `latexDelimiterHandler`, a `remend` handler (passed via `remend={{ handlers: [...] }}`) that rewrites `\(...\)` / `\[...\]` to `$...$` / `$$...$$` before KaTeX sees them, since models inconsistently emit the backslash form and `remark-math` only ever parses `$`. Registered as a `remend` handler rather than called manually before rendering, so it runs in the same pass as `remend`'s own incomplete-markdown completions and every Streamdown call site gets it automatically.

The backend's `SYSTEM_PROMPT` has no math-formatting guidance at all — tested live with no system-prompt hint and the model still freely mixed `$...$`, `$$...$$`, `\(...\)`/`\[...\]`, and code-spans, all of which rendered correctly via the two files above.

Trade-off: `singleDollarTextMath: true` makes ordinary prose like `$100 và $500` (two currency mentions) get misread as one inline-math span — the same ambiguity DeepSeek's own web client has. This is an accepted, currently unresolved limitation of the single-`$` convention, not something either file fixes.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com/docs)
- [AI Elements](https://ui.shadcn.com/docs/ai-elements)
