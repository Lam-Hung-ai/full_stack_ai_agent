# Hiển thị phần làm việc của agent (suy nghĩ, công cụ, hỏi lại)

Tài liệu cho đồng nghiệp và AI coding khi **thêm công cụ cho agent** hoặc **sửa cách hiển thị phần làm việc** dưới mỗi câu trả lời. Đọc hết mục 1–4 trước khi code; mục 8 là checklist thêm công cụ.

Trạng thái: áp dụng từ 03/11/2026 (commit `2946560` → `36557ba` trên nhánh `chat`). Thay cho cách hiển thị cũ trong [Dòng tóm tắt reasoning sống](live-reasoning-summary.md) (nhãn "Thought for…" theo từng lượt model, đã bỏ).

---

## 1. Người dùng thấy gì

Một câu trả lời (một assistant turn) được vẽ thành ba loại khối, theo đúng thứ tự xảy ra:

```
[câu hỏi của bạn]                                   14:05 ↻ ✎ ⧉   ← footer câu hỏi (hiện khi rê chuột)

☰ Đã làm việc trong 6 giây · xem giờ, tạo 1 tệp ›    ← KHỐI LÀM VIỆC (gập khi xong)
┊ 🧠 Đã suy nghĩ ›                                    ← bước suy nghĩ
┊ 🕐 Xem giờ hiện tại · 09:48 3/11/2026 ›             ← bước công cụ + kết quả bằng chữ
┊ 🧠 Đã suy nghĩ ›
┊ 📄 Tạo tệp ghi-gio · ghi-gio.txt · 32 B ›
[thẻ tệp ghi-gio.txt · TXT · 32 B]                   ← tệp công cụ tạo, luôn hiện

? Agent hỏi: Phòng nào?  [ô trả lời]                  ← THẺ HỎI ĐÁP (nếu agent hỏi lại)

☰ Đã làm việc · xem giờ ›                             ← khối làm việc sau khi bạn trả lời

Đã tạo tệp ghi-gio.txt chứa giờ hiện tại.            ← CÂU TRẢ LỜI (chỉ chữ sau bước cuối)
⧉ ↻ ‹1/2› Vừa xong                                    ← footer câu trả lời
```

Kiểu hiển thị theo Kimi (chuỗi bước trên một đường kẻ đứt), dựng bằng component shadcn **Trace** (`frontend/src/components/ui/trace.tsx`). Các nguyên tắc UX đến từ đợt review theo *The Design of Everyday Things* (Norman):

| Nguyên tắc | Áp dụng |
|---|---|
| Phản hồi phải nhanh, có thông tin, có ưu tiên (Ch1) | Đồng hồ + tên bước hiện tại khi đang chạy; kết quả công cụ bằng chữ; bước đã xong gập lại |
| Tự động hoá hỏng thường không báo trước (Ch5, ví dụ chữ "dr" của tàu Royal Majesty) | Bước lỗi hiện ngay trên tiêu đề (icon đỏ, "· 1 bước lỗi"), khối tự mở |
| Cho thấy trạng thái hệ thống chính xác (Ch5) | Tiêu đề nói kết cục (xong / dừng / lỗi); thời lượng không tính lúc chờ người dùng |
| Cảm giác kiểm soát (Ch2) | Khối không tự gập khi câu trả lời đang viết; lựa chọn mở/gập của người dùng luôn thắng |

---

## 2. Luồng dữ liệu từ đầu tới cuối

```
LangGraph agent (create_agent)                         backend/src/app/modules/ai/agents/chat.py
  ├─ model stream: reasoning, text, tool_calls
  ├─ ToolPermissionMiddleware → tool chạy → ToolMessage  ai/tools/permissions.py, ai/tools/*.py
  └─ ask_user / tool cần duyệt → interrupt()
        │
        ▼  LangGraphAgent dùng như bộ chuyển LangGraph → AG-UI   ai/runtime/agui.py
AG-UI events (stream SSE) + MESSAGES_SNAPSHOT
        │
        ├─► client đang xem (live)                       frontend/.../hooks/use-conversation-chat.ts
        │
        ▼  BundleBuilder: thứ tự theo stream, nội dung theo snapshot   ai/runtime/bundle.py
turns.content (AG-UI Message[] của cả lượt) + status + metadata.work_seconds
        │                                                 conversations/service.py::_finalize
        ▼  GET /conversations/{id}/turns → TurnResponse (content, created_at, updated_at, work_seconds)
RowView (frontend)                                        features/chat/utils/history.ts::toRowView
        │
        ▼  answerBlocks(row.content)                      features/chat/utils/answer-blocks.ts
[work | activity | text] blocks
        │
        ▼                                                  features/chat/components/chat-messages.tsx::AnswerRow
WorkSteps (Trace) · InteractionCard · MessageResponse
```

### 2.1. Một turn chứa gì (`turns.content`)

Một assistant turn là **một dòng SQL** chứa mảng AG-UI `Message[]` của cả lượt (xem [quy ước ID](conversation-message-run-id-decisions.md)). Các role có thể gặp:

| Role | Trường dùng để hiển thị | Ý nghĩa |
|---|---|---|
| `reasoning` | `content` | Suy nghĩ của model. Đứng **trước** assistant message mà nó thuộc về (không có id chung). |
| `assistant` | `content`, `toolCalls[]` | Chữ model viết và/hoặc các lời gọi công cụ (`function.name`, `function.arguments` là chuỗi JSON). |
| `tool` | `toolCallId`, `content`, `error?` | Kết quả một lời gọi công cụ. `error` có giá trị nghĩa là lỗi (xem 3.2). |
| `activity` | `content` (kind, status, interrupt_id, …) | Thẻ hỏi đáp: `user_question` (ask_user) hoặc `tool_approval`. `status`: `waiting`/`answered`/`cancelled`. |

Trạng thái của turn (`status`): `pending`, `running`, `requires_action` (đang chờ người dùng trả lời), `completed`, `failed`, `cancelled`. Ba trạng thái cuối là terminal, không đổi nữa.

### 2.2. Live và đã lưu

- **Live** (tab đang gửi câu hỏi): `RowView.live = true`, content lấy từ AG-UI events đang chảy về. Chưa có `createdAt`, `updatedAt`, `workSeconds`.
- **Đã lưu**: sau khi lượt kết thúc, client tải lại nhánh từ API và thay dòng live bằng dòng đã lưu. Lúc đó mới có thời lượng thật và cờ `error` chắc chắn (xem 3.2).

---

## 3. Backend: điều công cụ PHẢI làm để hiển thị đúng

### 3.1. Đăng ký công cụ

- Viết công cụ trong module riêng ở `backend/src/app/modules/ai/tools/`, liệt kê trong `TOOLS` (`tools/__init__.py`), thêm quyền `tool.<tên>` trong `authorization/catalog.py`.
- `ask_user` nằm trong `INTERACTION_TOOLS`, không qua quyền; frontend **không** vẽ nó thành bước công cụ mà thành thẻ hỏi đáp.
- Mỗi lời gọi đi qua `ToolPermissionMiddleware` (`tools/permissions.py`): bị từ chối → `ToolMessage(status="error", content=DENIED)`; cần duyệt → `interrupt()` → thẻ `tool_approval`.

### 3.2. Báo lỗi: BẮT BUỘC dùng `status="error"`

Đây là quy tắc quan trọng nhất. Chuỗi chuyển đổi:

```
ToolMessage(status="error")  ──ag-ui-langgraph──►  AG-UI tool message { error: "error", content: "<thông báo>" }
ToolMessage("Could not …")   ──ag-ui-langgraph──►  { content: "Could not …" }   ← KHÔNG có error → UI coi là thành công
```

`ag-ui-langgraph` (`utils.py`, đoạn chuyển `ToolMessage`) chỉ đặt `error` khi `status == "error"`, và chỉ đặt được chữ cố định `"error"` (nội dung lỗi thật nằm ở `content`). Vì vậy:

- **Đúng:** khi công cụ hỏng, trả về `ToolMessage(content=<thông báo cho model>, tool_call_id=runtime.tool_call_id, name=<tên tool>, status="error")`. Mẫu: hàm `_failed` trong `tools/files.py`.
- **Sai:** `return "Could not create the file: …"` (chuỗi thường). Model vẫn đọc được, nhưng giao diện hiện bước đó như thành công và cờ đỏ không bao giờ bật. Đây là lỗi thật đã gặp với `create_file` (sửa ở commit `9858a44`).
- Ném exception chưa bắt sẽ làm hỏng cả lượt (`status = failed`), không phải chỉ một bước. Bắt lỗi trong công cụ và trả `status="error"`.
- Thông báo lỗi (`content`) viết cho model đọc, nhưng cũng hiện cho người dùng ("Lỗi: <content>"), nên viết ngắn, không lộ chi tiết nội bộ (đường dẫn, stack trace, khoá).

Cờ `error` chắc chắn có trong **bản đã lưu** (BundleBuilder lấy tool message từ snapshot, nơi có `error`). Event `TOOL_CALL_RESULT` của AG-UI không có trường `error`, nên trong lúc stream, bước lỗi có thể chỉ bật đỏ khi lượt lưu xong.

### 3.3. Kết quả thành công: dạng nào để hiển thị đẹp

- **Chuỗi ngắn một dòng (≤ 80 ký tự)**: hiện nguyên văn trên dòng bước (`toolResultText`). Ví dụ `"Hà Nội"`.
- **Thời điểm ISO** của `get_current_time`: được định dạng lại (`09:48 3/11/2026`).
- **Tệp tạo ra**: trả JSON `{"file_id", "name", "content_type", "size_bytes"}` (xem `GeneratedFile.as_result()` trong `files/generated.py`). Frontend nhận ra qua `madeFile()` (chỉ với `create_file`) để vẽ thẻ tệp và dòng "tên · dung lượng".
- **Kết quả dài / JSON khác**: dòng bước không hiện kết quả; người dùng mở "Chi tiết kỹ thuật" để xem. Nếu công cụ mới cần một dòng tóm tắt riêng, thêm nhánh trong `toolResultText` (mục 4.4).

### 3.4. Thời lượng làm việc (`work_seconds`)

- Cuối **mỗi lần chạy** (lần đầu, và mỗi lần chạy tiếp sau khi người dùng trả lời thẻ hỏi đáp), `_finalize` cộng `now() - updated_at` vào `metadata.work_seconds` (`conversations/service.py`, `TurnRepository.running_seconds`). Không có gì ghi vào turn trong lúc nó chạy, nên khoảng này chính là thời gian lần chạy đó (tính từ lúc chuyển `running`, không gồm lúc chờ slot).
- API trả `TurnResponse.work_seconds` (None với câu hỏi và các turn cũ trước thay đổi này).
- **Đừng ghi vào dòng turn trong lúc nó đang chạy** (ví dụ cập nhật `metadata`, `attachments`): việc đó làm sai `work_seconds`. Nếu buộc phải ghi, cần đổi cách tính.

### 3.5. Prompt

`ai/prompts/chat.md` có hai quy tắc liên quan:

1. Dùng ngôn ngữ của tin nhắn mới nhất cho mọi thứ người dùng thấy: câu trả lời, phần suy nghĩ, lời viết giữa các lần gọi công cụ.
2. Báo kết quả công cụ trung thực; không nói một việc đã xong (tạo tệp, lấy dữ liệu) nếu kết quả công cụ không xác nhận.

Model hiện gán (`nvidia/nemotron-3.5-lightning:free`) theo quy tắc 1 cho câu trả lời nhưng vẫn **suy nghĩ bằng tiếng Anh**; đây là giới hạn của model.

---

## 4. Frontend: từ `content` tới màn hình

### 4.1. Tách khối: `answerBlocks()` — `features/chat/utils/answer-blocks.ts`

1. `buildItems()` (`agui-messages.ts`) ghép mỗi `reasoning` với assistant message ngay sau nó. Khi reasoning đang stream mà assistant message chưa có, nó tạo turn giữ chỗ id `PENDING_REASONING_ID` để suy nghĩ hiện ngay.
2. Mỗi assistant message sinh ra theo thứ tự: bước `thinking` (nếu có reasoning) → `text` (nếu có chữ) → các bước `tool` (bỏ `ask_user`), mỗi bước kèm `result` tìm theo `toolCallId`.
3. **Chỉ chữ đứng sau bước suy nghĩ/công cụ cuối cùng là câu trả lời** (khối `text`). Chữ viết xen giữa các bước ("Để mình xem giờ…") thành bước `note` trong khối làm việc.
4. Các bước liền nhau gom thành một khối `work`; thẻ hỏi đáp (`activity`) tách khối làm việc thành hai phần (trước và sau khi hỏi).

`answerCopyText(blocks)`: nút Sao chép chỉ lấy các khối `text` (không gồm suy nghĩ, ghi chú, công cụ).

### 4.2. Tiêu đề khối: `workSummary()` — cùng file

| Tình huống | Tiêu đề |
|---|---|
| Đang chạy (khối cuối của dòng live) | `Đang làm việc…` rồi `Đang làm việc… 12 giây` (đồng hồ từ `useElapsedSeconds`) |
| Lượt `completed`, khối đầu tiên | `Đã làm việc trong 6 giây` (từ `work_seconds`, turn cũ dùng `updated_at − created_at`) |
| Lượt `cancelled`, khối cuối | `Đã dừng sau 3 giây` |
| Lượt `failed`, khối cuối | `Gặp lỗi sau …` |
| Các trường hợp khác (khối giữa, đang chờ người dùng) | `Đã làm việc` |

Sau tiêu đề là phần mô tả: khi đang chạy là bước hiện tại (`đang suy nghĩ`, `đang chạy Tạo tệp …`); khi xong là việc đã làm (`workDone()`, ví dụ `xem giờ, tạo 1 tệp`); nếu có lỗi thêm `· N bước lỗi` màu đỏ; icon giữ nguyên `ListChecksIcon` (chữ đỏ đã đủ báo lỗi, không dùng icon cảnh báo).

`workDone()` (`utils/tool-steps.ts`) chỉ đếm **lần thành công** (`tạo 2 tệp`); công cụ chỉ có lần hỏng thì ghi `thử …` (`thử tạo tệp`); không có công cụ nào thì `suy nghĩ`.

### 4.3. Mở / gập — `components/work-steps.tsx`

| Thành phần | Mặc định | Ghi chú |
|---|---|---|
| Khối làm việc | Mở khi cả dòng đang stream (`keepOpen = isStreaming`); gập khi lượt xong | Giữ mở nếu có bước lỗi, hoặc là khối cuối của lượt bị dừng/lỗi. Người dùng bấm thì lựa chọn đó thắng (`choice ?? …`). |
| Bước suy nghĩ | Mở khi đang chạy, tự gập khi xong | `ThinkingStep`, cùng cơ chế `choice ?? active`. |
| Bước công cụ | Gập | Mở ra là "Chi tiết kỹ thuật": Đầu vào (JSON args) và Kết quả/Lỗi (raw). |
| Thẻ tệp | Luôn hiện dưới khối | Lấy từ các bước `create_file` thành công (`madeFile`). |

Trạng thái một bước công cụ (`toolStatus`): có `result` → `done` hoặc `error`; chưa có kết quả → `running` (đang chạy) / `pending` (lượt `requires_action`, hiện "Chờ duyệt") / `error` (lượt `failed`) / `stopped` (lượt `cancelled`, "Đã dừng").

### 4.4. Nhãn và kết quả của từng công cụ

Hai chỗ cần sửa khi thêm công cụ:

- **`TOOLS` trong `components/work-steps.tsx`**: icon lucide và nhãn tiếng Việt, có thể dùng tham số. Không khai báo thì hiện tên kỹ thuật (`search_web`) với icon cờ lê.

  ```ts
  create_file: {
    icon: FilePlusIcon,
    label: (args) => (typeof args.name === "string" ? `Tạo tệp ${args.name}` : "Tạo tệp"),
  },
  ```

- **`utils/tool-steps.ts`**:
  - `workDone()`: cụm từ ngắn cho tiêu đề (`xem giờ`, `tạo N tệp`). Không thêm thì dùng tên công cụ (`search_web ×2`).
  - `toolResultText()`: dòng kết quả bằng chữ. Không thêm thì chỉ chuỗi ngắn một dòng mới hiện.
  - `toolErrorText()`: đổi cờ `"error"` cố định thành nội dung lỗi thật. Không cần sửa.

### 4.5. Kiểu chữ và bố cục

- Khối làm việc dùng **Inter** (giao diện), chữ suy nghĩ/ghi chú 13px màu nhạt (`NOTE_CLASS`). Câu trả lời dùng **Source Serif 4**; code dùng **JetBrains Mono**. Quy tắc: chữ AI nói để đọc thì serif, nút/nhãn thì sans.
- Đường kẻ dọc đứt (`border-dashed`) như Kimi; các khối của một câu trả lời cách nhau 12px, giữa các lượt 32px.
- Trên dòng bước, **tiêu đề giữ chỗ trước** (`TITLE_FIRST`: tối đa 70%, không co), phần mô tả cắt bớt trước. Nhờ vậy màn hình điện thoại 390px vẫn đọc được "Đã làm việc trong 2 giây · thử tạo…".
- Giao diện tối: theo hệ thống mặc định (`next-themes`, menu "Giao diện" trong menu tài khoản). Mọi màu đi qua token (`text-muted-foreground`, `text-destructive`…), không viết màu cứng.

### 4.6. Trình đọc màn hình

Mỗi khối có một vùng `aria-live="polite"` ẩn, đọc lên khi trạng thái đổi: "Agent đang làm việc" → "Đã làm việc trong 6 giây, xem giờ, tạo 1 tệp" (thêm ", 1 bước lỗi" khi có lỗi). Đồng hồ đếm từng giây **không** nằm trong vùng này để tránh đọc liên tục.

---

## 5. Bảng trạng thái đầy đủ

| Tình huống | Tiêu đề khối | Khối | Bước liên quan | Footer câu trả lời |
|---|---|---|---|---|
| Đang chờ bước đầu | `Đang làm việc… N giây` (dòng `WorkingLine`) | — | — | — |
| Đang suy nghĩ | `Đang làm việc… N giây · đang suy nghĩ` | Mở | Suy nghĩ mở, chữ chạy | — |
| Đang chạy công cụ | `… · đang chạy <nhãn>` | Mở | `· Đang chạy…` | — |
| Đang viết câu trả lời | `Đã làm việc · <việc đã làm>` | Mở | Bước xong gập | — |
| Xong | `Đã làm việc trong N giây · <việc>` | Gập | — | Sao chép, Tạo lại, phiên bản, giờ |
| Xong nhưng có công cụ lỗi | `… · 1 bước lỗi` (chữ đỏ, icon bình thường) | Mở | Dòng đỏ `· Lỗi: <nội dung>` | như trên |
| Đang chờ người dùng (`requires_action`) | `Đã làm việc` | Gập | Công cụ cần duyệt: `· Chờ duyệt` | — (thẻ hỏi đáp có ô trả lời) |
| Bị dừng | `Đã dừng sau N giây` | Mở | Công cụ dở: `· Đã dừng` | `· Đã dừng` |
| Lỗi cả lượt | `Gặp lỗi sau N giây` | Mở | Công cụ dở: `· Lỗi` | `Câu trả lời chưa hoàn tất do lỗi` |

---

## 6. Bản đồ file

| Phần | File |
|---|---|
| Đăng ký công cụ, quyền | `backend/src/app/modules/ai/tools/__init__.py`, `tools/permissions.py`, `authorization/catalog.py` |
| Công cụ mẫu (lỗi đúng chuẩn) | `backend/src/app/modules/ai/tools/files.py` (`_failed`), `tools/clock.py` |
| Hỏi lại người dùng | `backend/src/app/modules/ai/tools/interaction.py`, `conversations/interactions.py` |
| Chuyển LangGraph → AG-UI, lưu bundle | `backend/src/app/modules/ai/runtime/agui.py`, `runtime/bundle.py`, `runtime/runner.py` |
| Lưu kết quả, `work_seconds` | `backend/src/app/modules/conversations/service.py` (`_finalize`), `repository.py` (`running_seconds`), `schemas.py` (`TurnResponse`) |
| Prompt | `backend/src/app/modules/ai/prompts/chat.md` |
| Tách khối, tiêu đề | `frontend/src/features/chat/utils/answer-blocks.ts` |
| Tóm tắt công cụ, lỗi | `frontend/src/features/chat/utils/tool-steps.ts`, `utils/files.ts` (`madeFile`) |
| Ghép reasoning | `frontend/src/features/chat/utils/agui-messages.ts` |
| Thời lượng | `frontend/src/features/chat/utils/turn-time.ts`, `src/hooks/use-elapsed-seconds.ts` |
| Vẽ khối làm việc | `frontend/src/features/chat/components/work-steps.tsx` |
| Ghép vào câu trả lời, footer | `frontend/src/features/chat/components/chat-messages.tsx` (`AnswerRow`) |
| Thẻ hỏi đáp | `frontend/src/features/chat/components/interaction-card.tsx`, `utils/interactions.ts` |
| Primitive Trace (shadcn) | `frontend/src/components/ui/trace.tsx` (không sửa; truyền `className`) |
| Giao diện tối | `frontend/src/components/layout/theme-provider.tsx`, `theme-menu.tsx`, `src/app/providers.tsx` |

---

## 7. Kiểm thử

**Unit test (Vitest, chạy `pnpm test`)**

- `utils/answer-blocks.test.ts`: tách khối, ghi chú giữa bước, thẻ hỏi đáp tách khối, `workSummary` theo từng kết cục.
- `utils/tool-steps.test.ts`: `workDone` (đếm, "thử …"), `toolResultText` (giờ, tệp, chuỗi ngắn, lỗi, cờ `"error"` cố định).
- `utils/turn-time.test.ts`: `formatDuration` (giây/phút/giờ), `turnTime`.

**Backend (pytest)**

- `tests/api/files/test_generated_files.py::test_bad_requests_are_refused_to_the_model`: lần hỏng có `error: "error"` trong bản lưu, lần thành công thì không.
- `tests/api/conversations/test_pause_resume.py::test_waiting_for_the_user_is_not_work`: chờ 1.5 giây giữa lúc dừng và chạy tiếp không bị tính vào `work_seconds`.
- `tests/api/conversations/test_turns.py`: `work_seconds` có ở assistant turn, None ở câu hỏi.

**Thử tay bằng lượt chat thật**

| Kịch bản | Câu hỏi gợi ý | Kỳ vọng |
|---|---|---|
| Bình thường | "Xem giờ hiện tại bằng công cụ, rồi tạo tệp txt tên "ghi-gio" chứa giờ đó." | Đồng hồ chạy, tên bước đổi, gập khi xong: "Đã làm việc trong N giây · xem giờ, tạo 1 tệp" |
| Công cụ lỗi thật | "Gọi công cụ tạo tệp định dạng xlsx tên "thu-loi" và KHÔNG truyền rows lẫn content." | "· thử tạo tệp · 1 bước lỗi", dòng đỏ "Lỗi: Could not create the file: rows is required…" |
| Bị dừng | Câu hỏi dài, bấm Dừng sau bước công cụ | "Đã dừng sau N giây", khối mở |
| Hỏi lại | Câu mơ hồ khiến agent dùng `ask_user` | Khối trước thẻ, thẻ hỏi đáp, khối sau khi trả lời |
| Điện thoại / tối | Cửa sổ 390px, menu Giao diện → Tối | Không tràn ngang; tiêu đề không bị cắt mất; màu đúng token |

Giả lập lỗi mà không cần model: chặn `GET /api/v1/conversations/<id>/turns` bằng Playwright `page.route`, đặt `error` vào một tool message rồi trả lại (chỉ trong trình duyệt thử).

---

## 8. Checklist thêm một công cụ mới

**Backend**

- [ ] Module trong `ai/tools/`, khai báo trong `TOOLS`, quyền `tool.<tên>` trong `authorization/catalog.py`.
- [ ] Docstring nói rõ khi nào dùng và tham số (model đọc docstring).
- [ ] Mọi đường hỏng trả `ToolMessage(..., status="error")` với thông báo ngắn, an toàn để người dùng đọc. Không trả chuỗi thường khi lỗi; không để exception thoát ra.
- [ ] Kết quả thành công: chuỗi ngắn một dòng nếu có thể; nếu là dữ liệu có cấu trúc, trả JSON ổn định để frontend tóm tắt.
- [ ] Có tác dụng phụ (tạo, gửi, xoá)? Cân nhắc đưa vào `tools_requiring_approval` (thẻ duyệt). Nhớ: `interrupt()` khiến node chạy lại từ đầu, nên mọi tác dụng phụ phải nằm **sau** chỗ hỏi.
- [ ] Giới hạn số lần (như `MAX_FILES_PER_TURN`) phải chịu được **lời gọi song song** (xem mục 9).
- [ ] Test: lần thành công, lần hỏng có `error` trong bản lưu (`history(...)`, tìm tool message theo `toolCallId`).

**Frontend**

- [ ] Thêm `TOOLS[<tên>]` trong `work-steps.tsx`: icon lucide và nhãn tiếng Việt (động từ + đối tượng, dùng tham số nếu giúp phân biệt).
- [ ] Thêm cụm từ trong `workDone()` (đếm theo lần thành công).
- [ ] Nếu kết quả không phải chuỗi ngắn: thêm nhánh trong `toolResultText()`.
- [ ] Nếu công cụ tạo ra thứ người dùng tải về: cân nhắc cho nó hiện ngoài khối như thẻ tệp (xem `files` trong `WorkSteps`).
- [ ] Test trong `tool-steps.test.ts`; chạy `pnpm lint`, `pnpm typecheck`, `pnpm test`.
- [ ] Chạy thử một lượt thật, cả trường hợp lỗi; xem ở điện thoại và giao diện tối.

**Không làm**

- Không vẽ công cụ riêng bằng component khác (Tool, Chain of Thought của ai-elements): chúng gắn nhãn tiếng Anh và không theo Trace.
- Không sửa `components/ui/trace.tsx` hay component ai-elements; truyền `className` từ ngoài.
- Không hiện JSON thô trên dòng bước; JSON chỉ nằm trong "Chi tiết kỹ thuật".
- Không dùng màu cứng (`text-red-600`); dùng token (`text-destructive`).

---

## 9. Giới hạn và việc còn mở

| Vấn đề | Tình trạng |
|---|---|
| Phần suy nghĩ vẫn tiếng Anh | Giới hạn của model đang gán; prompt đã yêu cầu. Muốn khác phải đổi model. |
| Cờ lỗi lúc đang stream | `TOOL_CALL_RESULT` không mang `error`; cờ đỏ chắc chắn có sau khi lượt lưu xong. |
| Giới hạn 5 tệp mỗi lượt bị vượt khi model gọi song song | Lỗi backend chưa sửa: các lời gọi đồng thời cùng đếm thấy chưa đủ 5 (`files/generated.py`). Cần khoá hoặc đếm nguyên tử. |
| Turn cũ chưa có `work_seconds` | Hiện thời lượng `updated_at − created_at` (tính cả lúc chờ nếu có hỏi lại). |
| Trang chia sẻ công khai | Bản chụp không lưu `updated_at`/`work_seconds`, nên tiêu đề chỉ ghi "Đã làm việc". |
| Kết quả tìm kiếm (danh sách nguồn kiểu Kimi) | Chưa có công cụ tìm web. Khi thêm, hiện danh sách nguồn trong bước tìm kiếm (có thể dùng `Sources` của ai-elements bên trong `TraceCollapsibleContent`). |
| Kiểm chứng với người dùng thật | Chưa làm. Gợi ý: 3–5 người, ba lượt (bình thường, công cụ lỗi, bị dừng), hỏi "agent đã làm gì, có đáng tin không, đã xong chưa". |
