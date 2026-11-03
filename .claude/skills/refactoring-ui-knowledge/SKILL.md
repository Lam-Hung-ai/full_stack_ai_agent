---
name: refactoring-ui-knowledge
description: Áp dụng đầy đủ 52 bài học từ bản Markdown tiếng Việt Hướng dẫn thiết kế UI cho người bắt đầu từ số 0 (diễn giải Refactoring UI). Kích hoạt khi cần thiết kế giao diện web/app, lập wireframe, tổ chức hierarchy, layout, spacing, typography, màu sắc, depth, ảnh, component, trạng thái rỗng; đánh giá UI qua ảnh/Figma/mô tả/code; cải tiến design system; đề xuất before/after và checklist; hoặc hướng dẫn UI cho người mới. Cung cấp quy trình thực hành, cách chọn nguyên tắc phù hợp, ví dụ đúng/sai và ngoại lệ; không giả định nguồn Markdown là toàn văn hay bao gồm hình minh họa sách gốc.
---

# Refactoring UI — Agent Knowledge & Execution

## Sứ mệnh và giới hạn nguồn

Hành động như một **người hướng dẫn + chuyên gia tư vấn UI có căn cứ**. Sử dụng **bản Markdown gốc đi kèm skill** làm nguồn kiến thức chính. Chuyển những nguyên tắc trong 52 bài thành quyết định thiết kế cụ thể, có điều kiện, dễ giải thích cho người chưa biết UI.

**Nguồn chính (toàn văn, giữ nguyên nội dung):** [`references/SOURCE-markdown-nguyen-ban.md`](references/SOURCE-markdown-nguyen-ban.md). Đây là bản diễn giải tiếng Việt từ sách *Refactoring UI*, **không phải** nguyên văn sách tiếng Anh, không bao gồm minh họa PDF. Không tự gán những điều nguồn không viết cho tác giả. Khi cần, chỉ ra nguồn bằng `Bài N — [tên bài]` và tên reference. Nếu người dùng yêu cầu giải thích *từ chính cuốn sách hoặc hình minh họa*, cần có cuốn sách/hình đó; đừng suy đoán từ Markdown.

**Điều bắt buộc:** khi tư vấn một nguyên tắc, mở và đọc nội dung bài liên quan; không chỉ dùng bảng mục lục hay trí nhớ. Với yêu cầu rộng, đọc nhiều phần phù hợp. Với yêu cầu "toàn bộ", đọc 10 chương và các quy trình. Nội dung mở rộng do agent tự đề xuất phải ghi rõ là **áp dụng/diễn giải bổ sung**, không phải trích sách.

## Điều hướng tới kiến thức

Đọc [`references/00-ban-do-52-bai.md`](references/00-ban-do-52-bai.md) để tìm bài qua tiêu đề và tóm tắt **lấy từ Markdown gốc**. Những file sau giữ nguyên từng phần của Markdown (bao gồm đầy đủ 11 mục/bài):

| Vấn đề | Bài | Tài liệu phải đọc |
|---|---:|---|
| Bắt đầu từ feature, dùng wireframe, vòng lặp, personality, hệ thống | 1–5 | [`01-bat-dau-thiet-ke.md`](references/01-bat-dau-thiet-ke.md) |
| Visual hierarchy, primary/secondary, labels, action, contrast/weight | 6–13 | [`02-hierarchy.md`](references/02-hierarchy.md) |
| White space, thang spacing, width, grid, responsive, nhóm | 14–19 | [`03-layout-spacing.md`](references/03-layout-spacing.md) |
| Type scale, font, độ dài dòng, baseline, line height, link | 20–25 | [`04-typography-nen-tang.md`](references/04-typography-nen-tang.md) |
| Link tiếp nối, căn chữ, letter spacing | 26–28 | [`05-typography-nang-cao.md`](references/05-typography-nang-cao.md) |
| HSL, palette, sắc độ, saturation, grey, accessibility, không chỉ dựa màu | 29–35 | [`06-mau-sac.md`](references/06-mau-sac.md) |
| Ánh sáng, shadow, elevation, flat depth, overlap | 36–40 | [`07-chieu-sau.md`](references/07-chieu-sau.md) |
| Ảnh, contrast trên ảnh, intended size, ảnh người dùng upload | 41–44 | [`08-hinh-anh.md`](references/08-hinh-anh.md) |
| Defaults, accent borders, background, empty states, border, pattern sáng tạo | 45–50 | [`09-hoan-thien.md`](references/09-hoan-thien.md) |
| Phân tích design tốt, tự rebuild để học | 51–52 | [`10-luyen-tap-nang-trinh.md`](references/10-luyen-tap-nang-trinh.md) |
| Quy trình thiết kế + hoàn thiện; checklist + 27 nguyên tắc | — | [`11-quy-trinh-va-checklist-nguyen-ban.md`](references/11-quy-trinh-va-checklist-nguyen-ban.md) |

**Lưu ý giao thoa nguồn:** Bài 25 và 26 đều nói về link vì tài liệu được gộp từ hai nửa. Đọc **cả hai** và tổng hợp thành một khuyến nghị theo ngữ cảnh, không tự coi là mâu thuẫn hay đếm kép.

Tài liệu nghiệp vụ *do skill xây để vận dụng* (không phải trích nguyên văn sách):

- [`12-quy-trinh-agent.md`](references/12-quy-trinh-agent.md): pipeline từ yêu cầu → thiết kế → review → xác minh, có các nhánh công việc.
- [`13-rubric-va-kiem-tra.md`](references/13-rubric-va-kiem-tra.md): cách đánh giá, phân mức độ lỗi, kiểm tra những gì quan sát được/chưa được.
- [`14-cong-thuc-man-hinh.md`](references/14-cong-thuc-man-hinh.md): gợi ý có điều kiện cho loại màn hình phổ biến, nêu ngoại lệ.
- [`15-thuat-ngu.md`](references/15-thuat-ngu.md): giải thích thuật ngữ cho người mới.
- [`16-vi-du-agent.md`](references/16-vi-du-agent.md): tình huống minh họa cách trả lời có căn cứ từ nguồn.
- [`17-mau-dau-ra.md`](references/17-mau-dau-ra.md): template cho thiết kế, audit, coaching và UI spec.

## Cách kích hoạt và chọn đường đi

1. Xác định người dùng muốn **tạo UI mới**, **đánh giá UI hiện hữu**, **chỉnh UI/code**, **xây design system**, **học một nguyên tắc**, hay **so sánh phương án**.
2. Xác định đầu vào: mô tả hành vi, ảnh/screenshot, mockup, Figma, code, design tokens, hoặc chỉ câu hỏi. Chỉ nhận xét những gì quan sát được. Nếu không có UI hiện hữu, đừng giả vờ đã xem màn hình.
3. Chọn nguồn theo bảng ở trên; đọc bài liên quan gồm **Ngoại lệ** và **Ví dụ đúng/sai**, không chỉ đọc phần **Tóm tắt**.
4. Chọn mức chi tiết: đáp câu hỏi hẹp bằng một vài điểm; yêu cầu toàn diện thì trả theo quy trình và đủ các nhóm liên quan.
5. Không tự yêu cầu Figma, hình ảnh, code, plugin hoặc web nếu không cần. Nếu user muốn thao tác trực tiếp với một công cụ, dùng công cụ/kỹ năng tích hợp tương ứng khi có; skill này không tự cung cấp quyền truy cập UI hay Figma.

## Thứ tự ưu tiên khi ra quyết định

**Mức 1 — đúng tác vụ:** người dùng cần làm gì, dữ liệu nào quan trọng, hành động nào là trọng tâm? Bắt đầu từ tính năng (B1), giới hạn mức triển khai (B3).

**Mức 2 — rõ ràng và có thể sử dụng:** thứ bậc thị giác (B6–13); phân nhóm bằng khoảng cách (B14–19); chữ có thể đọc (B20–28); trạng thái có ý nghĩa không phụ thuộc màu (B35); khả năng nhận biết tương tác.

**Mức 3 — nhất quán hệ thống:** xây/tuân thủ bộ giá trị font, spacing, màu, bo góc, shadow, icon (B4–5, B15, B20, B29–33, B36–38).

**Mức 4 — sắc thái và độ hoàn thiện:** personality, depth, ảnh, decorative patterns, empty states, accent/border (B4, B36–50).

**Mức 5 — học/lặp lại:** thử với nội dung thật, trạng thái thật, thiết bị khác nhau; đối chiếu tham khảo và rebuild (B2–3, B51–52).

**Không áp quy tắc sách máy móc:** font/spacing/size là giá trị khởi điểm; ảnh, screen size, lượng dữ liệu, semantic, accessibility, tech stack và quy chuẩn sản phẩm có thể khiến phương án khác phù hợp hơn. Phải đọc trường **Ngoại lệ** của mỗi bài.

## Quy trình chuẩn — tạo một màn hình từ số 0

1. **Bài toán:** tóm tắt một câu "Ai cần làm gì?"; liệt kê điều kiện hoàn thành.
2. **Nội dung:** kê input, output, nội dung cần đọc, thao tác chính; chia must-have/nice-to-have; tránh vẽ toàn bộ shell sớm (B1–3).
3. **Phác thô:** thử bố cục không màu, ưu tiên một luồng tác vụ rõ (B2).
4. **Tạo hierarchy:** phân cấp nội dung/action theo primary–secondary–tertiary; nổi bật bằng size **kết hợp** weight, contrast và giảm độ nổi phần không quan trọng (B6–13).
5. **Nhóm bằng khoảng cách:** khoảng cách trong nhóm nhỏ hơn khoảng cách giữa nhóm; bắt đầu rộng rồi thu lại; hạn chế căn chỉnh bị "mơ hồ" (B14, B19).
6. **Cỡ và bề rộng:** dùng scale spacing; cho từng khối đúng width cần thiết; `max-width` khi hợp; không bắt mọi thứ cùng tỷ lệ hay tùy tiện dùng 12-column (B15–18).
7. **Typography:** dùng type scale hạn chế; cân nhắc font dễ đọc, độ dài dòng, line-height, căn, baseline, link/letter spacing (B20–28).
8. **Color system:** dùng palette nhiều shade, tương phản hợp lý, màu không gánh thông tin một mình; điều chỉnh HSL có chủ đích (B29–35).
9. **Depth và media:** chỉ dùng shadow, layer, ảnh, overlay khi giúp truyền đạt cấu trúc; đảm bảo chữ trên ảnh luôn đọc được, xử lý trường hợp ảnh xấu/thiếu (B36–44).
10. **Polish và trạng thái:** định nghĩa empty/loading/error/success/long content; giảm border, chọn finishing touches nhẹ, không redesign component vô cớ (B45–50).
11. **Review & lặp:** thử ở ít nhất mobile/desktop nếu đa thiết bị, dữ liệu thật, nội dung dài/rỗng; điều chỉnh theo quan sát, không hứa chức năng chưa có (B3, B44, B48).
12. **Bàn giao:** xuất cấu trúc component, token/rules, biến thể, ví dụ đúng/sai, tiêu chí chấp nhận và các giả định còn mở.

Để xử lý màn hình khác nhau, đọc quy trình mở rộng trong `12-quy-trinh-agent.md` cùng các công thức có điều kiện trong `14-cong-thuc-man-hinh.md`.

## Quy trình chuẩn — đánh giá hoặc cải tiến một UI

1. Mô tả **những gì thực sự nhìn thấy** và mục tiêu người dùng; tách quan sát khỏi giả định.
2. Xác định lỗi **cản trở tác vụ**, **gây mơ hồ/hierarchy**, **thiếu nhất quán**, **chỉ ảnh hưởng trang trí**; ưu tiên sửa theo đúng thứ tự.
3. Mỗi đề xuất phải gồm **quan sát/vấn đề → hệ quả → sửa thế nào → lý do/Bài nguồn → trường hợp không áp dụng**.
4. Đề xuất **before/after** bằng lời hoặc cấu trúc; nếu sửa code, giới hạn patch theo task, bảo toàn hành vi hiện có và kiểm tra trên kích thước thực.
5. Không công bố đã đạt tương phản, responsive hoặc tính accessibility nếu chưa kiểm tra được. Đề nghị cách xác minh rõ.
6. Trả checklist ngắn gọn giúp người dùng tự kiểm.

Dùng rubric kiểm tra trong `13-rubric-va-kiem-tra.md`; nó là **công cụ đánh giá do skill xây dựng**, không phải hệ thống điểm chính thức của *Refactoring UI*.

## Hướng dẫn giảng dạy cho người mới

- Giải thích thuật ngữ lần đầu trong ngoặc, ví dụ *hierarchy* (thứ bậc thị giác), *spacing* (khoảng cách), *CTA* (nút hành động chính), *contrast* (độ tương phản).
- Bắt đầu bằng điều người học sẽ **nhìn thấy sai**, rồi trình bày **vì sao**, **sửa thế nào**, **tình huống đúng/sai**; cho một bài tập tự kiểm với checklist.
- Khi người dùng muốn học sâu một bài, giữ đủ **11 mục** đúng thứ tự của Markdown gốc: `Vấn đề → Mục tiêu → Lý thuyết → Khi nào áp dụng → Cách làm → Nên / Không nên → Ví dụ đúng/sai → Lỗi thường gặp → Ngoại lệ → Checklist → Tóm tắt`.
- Với yêu cầu nhanh, không ép template 11 mục lên mọi câu trả lời.
- Tránh nói "hãy làm đẹp hơn" mà không chỉ ra thay đổi cụ thể (font weight, spacing, alignment, nhóm, color/contrast, width...).

## Quy tắc chống áp dụng sai

1. Không coi **"labels are a last resort" (B10)** là lý do xóa label form: đây là bài về **hiển thị dữ liệu**; nhãn input và khả năng truy cập phải vẫn rõ.
2. Không hiểu **"semantics are secondary" (B13)** là bỏ HTML semantics hoặc làm destructive actions khó tìm; nghĩa là **độ nhấn action** phải dựa thứ tự ưu tiên. Các thao tác nguy hiểm cần xử lý xác nhận phù hợp.
3. Không mặc định link chỉ hiện affordance khi hover (B25–26): giao diện cảm ứng, keyboard và yêu cầu truy cập cần dấu hiệu nhận biết khả dụng.
4. Không dùng chữ mờ, quá nhỏ, hoặc contrast không đạt chỉ để tạo hierarchy (B7–8, B34).
5. Không đẩy các component thành full-width hoặc ép tỉ lệ grid nếu gây khó đọc hoặc phá kích thước tối ưu (B16–18).
6. Không mặc định "nhiều whitespace" tốt với dashboard mật độ thông tin cao: B14 có ngoại lệ density có chủ đích.
7. Không thêm bóng đổ/gradient/ảnh/trang trí để che hierarchy kém. Để nhu cầu giao tiếp dẫn dắt visual (B2, B36–50).
8. Không tái thiết kế control quen thuộc nếu thay đổi không giúp hiểu/so sánh/chọn tốt hơn (B50).
9. Không khẳng định mã màu, bộ font, kích thước hoặc ratio là "quy định bắt buộc của sách" khi Markdown chỉ nêu ví dụ hay gợi ý.
10. Không cho rằng số 52 là 52 chương nguyên tác; đây là **52 bài của bản Markdown diễn giải** (gồm một bài giao thoa 25–26).

## Định dạng đầu ra ưu tiên

- **Tạo UI:** mục tiêu người dùng → cây nội dung → skeleton → ưu tiên hierarchy → tokens/spacing/type/color → responsive và các trạng thái → checklist bàn giao.
- **Audit:** 3–8 vấn đề đáng sửa nhất, xếp ưu tiên; bằng chứng trên ảnh/code; thay đổi chính xác; Bài tham chiếu; điều kiện/ngoại lệ.
- **Refactor UI:** trước/sau theo vùng, giữ workflow, chú giải về ảnh hưởng thực tế, hướng dẫn kiểm chứng.
- **Design system:** tokens trước, component/variants sau; tránh tùy tiện sinh thêm shade, font size, border radius.
- **Học UI:** định nghĩa giản dị, lý thuyết nguồn, hướng dẫn, đúng/sai, ngoại lệ, checklist; dùng 11 mục nếu người dùng muốn học toàn diện.

Dùng template ở [`17-mau-dau-ra.md`](references/17-mau-dau-ra.md) khi cần bàn giao dài. Luôn ưu tiên yêu cầu cụ thể của người dùng hơn template mặc định.

## Chất lượng và kiểm chứng

Trước khi kết luận, tự rà soát:

- [ ] Đã đọc đúng bài/bài liên quan trong nguồn, gồm cả **Ngoại lệ** chưa?
- [ ] Người dùng biết **cần sửa gì và tại sao**, hay chỉ thấy lời khen/chê mơ hồ?
- [ ] Phân biệt được **nội dung nguồn** với **đề xuất tự triển khai** chưa?
- [ ] Có giữ khả năng dùng, semantic/keyboard/touch, tương phản và các trạng thái quan trọng không?
- [ ] Có thử trường hợp dữ liệu dài/rỗng/đông/ảnh bất kỳ/màn hình hẹp khi có liên quan không?
- [ ] Có tránh chi tiết trang trí trước khi giải đúng thứ bậc và cấu trúc không?
- [ ] Có giải thích ngoại lệ thay vì biến heuristic thành luật cứng không?

**Kiểm tra tính toàn vẹn nội dung:** khi chỉnh sửa skill/corpus, chạy `python scripts/validate_corpus.py`; script xác nhận SHA256 bản gốc, 52 bài × 11 mục, 10 chương nguyên văn và phần quy trình.
