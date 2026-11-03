# Quy trình thực hành 1 — Thiết kế một màn hình UI từ đầu

Phần này gom các nguyên tắc trong 25 bài thành một quy trình đơn giản cho người mới.

## Bước 1 — Viết nhiệm vụ người dùng
Ví dụ: “Người dùng cần tạo một hóa đơn mới.”

Đừng bắt đầu bằng sidebar, màu sắc hay logo.

## Bước 2 — Liệt kê nội dung tối thiểu
- Khách hàng
- Danh sách sản phẩm/dịch vụ
- Số lượng/đơn giá
- Tổng tiền
- Hạn thanh toán
- Nút tạo hóa đơn

## Bước 3 — Phác grayscale
Chỉ dùng khối, text giả lập và 2-3 mức xám. Chưa chọn màu thương hiệu, shadow hay icon chi tiết.

## Bước 4 — Xếp hierarchy
- Primary: tổng tiền + nút tạo hóa đơn
- Secondary: khách hàng, danh sách item
- Tertiary: ghi chú, metadata

## Bước 5 — Nhóm bằng spacing
Các field liên quan đứng gần nhau. Khoảng giữa các nhóm lớn hơn khoảng trong nhóm.

## Bước 6 — Áp hệ thống
Ví dụ:

```text
Spacing: 4, 8, 12, 16, 24, 32, 48, 64...
Type:    12, 14, 16, 18, 20, 24, 30, 36, 48...
Radius:  4, 8, 12 (ví dụ dự án tự chọn)
```

> Hai scale spacing/type đầu tiên bám theo ví dụ trong phần PDF đã đọc; scale radius ở đây chỉ là ví dụ minh họa cách giới hạn lựa chọn, không phải con số được PDF quy định trong nửa đầu.

## Bước 7 — Kiểm tra width
Form có cần full-width không? Nếu không, đặt max-width. Paragraph có quá dài không? Nếu có, giới hạn line length.

## Bước 8 — Kiểm tra typography
- Text size có nằm trong scale không?
- Font có dễ đọc ở size nhỏ không?
- Text khác size trên một hàng có nên căn baseline không?
- Line-height có hợp với font size và line length không?

## Bước 9 — Áp personality
Sau khi cấu trúc ổn, mới thêm font, màu, radius và tone phù hợp với tính cách sản phẩm.

## Bước 10 — Giảm nhiễu
Nếu UI vẫn bận, đừng thêm hiệu ứng. Hãy thử:
- làm text phụ nhẹ hơn,
- giảm background/border thừa,
- giảm emphasis của action phụ,
- bỏ label không cần thiết,
- tăng whitespace.

---

# Quy trình thực hành 2 — Hoàn thiện một màn hình sau khi layout cơ bản đã ổn

Phần này gom nửa sau của sách thành một quy trình đơn giản để bạn dùng trên một màn hình thật.

## Bước 1 - Kiểm tra typography cuối cùng
- Link có nổi đúng mức không?
- Paragraph dài đã căn trái chưa?
- Number column đã căn phải chưa?
- Heading/ALL CAPS có cần chỉnh letter-spacing không?

## Bước 2 - Chuẩn hóa palette
Tạo hoặc rà soát:

```text
Greys:      khoảng 8-10 shade nếu sản phẩm cần đủ dải
Primary:    1-2 color family, mỗi family khoảng 5-10 shade
Accents:    semantic/feature colors theo nhu cầu thật
```

Không thêm shade ngoài hệ thống chỉ vì một màn hình “thiếu đúng một màu”.

## Bước 3 - Kiểm tra accessibility của màu
- Contrast text/background có đạt ngưỡng được sách nêu không?
- Nếu nền màu phải tối quá mới đọc được white text, thử flip contrast.
- Màu có đang là tín hiệu duy nhất không?

## Bước 4 - Xác định depth
Hỏi từng component:
- Nằm cùng mặt phẳng?
- Raised nhẹ?
- Dropdown/popover?
- Modal?
- Inset?

Sau đó chọn color/shadow/elevation tương ứng thay vì thêm effect ngẫu nhiên.

## Bước 5 - Kiểm tra ảnh
- Ảnh có đủ chất lượng không?
- Text trên ảnh có contrast ổn định không?
- Screenshot/icon có đang bị scale ngoài intended size không?
- User-uploaded images có container/crop ổn định không?

## Bước 6 - Làm empty state
Đừng chờ production mới thấy danh sách rỗng. Thiết kế:
- thông điệp,
- CTA,
- illustration nếu cần,
- trạng thái ẩn của filter/tab vô dụng.

## Bước 7 - Giảm đường kẻ
Trước mỗi border, thử lần lượt:
1. spacing,
2. background khác nhẹ,
3. shadow subtle,
4. border nếu vẫn cần.

## Bước 8 - Thêm finishing touch có kiểm soát
Chọn rất ít:
- icon thay bullet,
- accent border,
- background tint/pattern,
- custom selected states.

Không cần dùng tất cả cùng lúc.

## Bước 9 - Tìm một cơ hội “thoát khỏi component mặc định”
Chỉ ở nơi thật sự quan trọng:
- dropdown giàu nội dung,
- plan selection,
- table có hierarchy,
- radio -> selectable card.

## Bước 10 - So với reference và học thêm
Sau khi hoàn thiện, đặt cạnh một UI bạn đánh giá cao và hỏi:
- Họ làm gì mà mình không nghĩ tới?
- Khác biệt nằm ở layout, type, color, shadow hay detail?

---

# Checklist tổng

## Checklist nền tảng trước khi gọi một màn hình là “ổn”

## 1. Chức năng
- [ ] Màn hình phục vụ một nhiệm vụ người dùng rõ ràng.
- [ ] Action chính dễ nhận ra.
- [ ] Không có chức năng “hứa trước” mà sản phẩm chưa hỗ trợ.

## 2. Hierarchy
- [ ] Primary / secondary / tertiary phân biệt được.
- [ ] Không phải mọi thứ đều bold, to hoặc nhiều màu.
- [ ] Action phụ không cạnh tranh với action chính.
- [ ] Destructive action không bị làm nổi quá mức khi chưa cần.

## 3. Spacing và layout
- [ ] Có spacing scale.
- [ ] Khoảng trong nhóm nhỏ hơn khoảng giữa nhóm.
- [ ] Component không bị kéo rộng chỉ vì màn hình rộng.
- [ ] Grid không ép phần tử co giãn vô lý.
- [ ] Responsive không đơn giản là thu nhỏ đồng tỷ lệ.

## 4. Typography
- [ ] Có type scale.
- [ ] Font đọc tốt ở kích thước UI.
- [ ] Paragraph không quá dài.
- [ ] Line-height phù hợp với size và width.
- [ ] Text khác size trên cùng hàng được kiểm tra baseline.

## 5. Personality và consistency
- [ ] Font, màu, radius và câu chữ cùng một hướng cảm xúc.
- [ ] Các component tương tự dùng cùng quy tắc.
- [ ] Không có hàng loạt giá trị “gần giống nhau nhưng khác nhau”.

## 6. Giảm nhiễu
- [ ] Label thừa đã được bỏ hoặc giảm emphasis.
- [ ] Icon nặng đã được cân bằng contrast.
- [ ] Border/shadow chỉ xuất hiện khi có lý do.
- [ ] Link không đồng loạt cạnh tranh bằng màu nổi.

---

## Checklist hoàn thiện

## 1. Typography
- [ ] Link phụ không cạnh tranh với CTA chính.
- [ ] Text dài căn theo hướng đọc tự nhiên.
- [ ] Number columns căn phải khi cần so sánh.
- [ ] ALL CAPS có tracking phù hợp.
- [ ] Letter-spacing chỉ được chỉnh khi có lý do.

## 2. Color system
- [ ] Có grey scale đủ dùng.
- [ ] Primary/accent colors có shade scale rõ.
- [ ] Không có hàng loạt one-off colors.
- [ ] Shade sáng/tối không bị washed out.
- [ ] Grey temperature có chủ đích.

## 3. Accessibility
- [ ] Contrast được kiểm tra, không chỉ đoán bằng mắt.
- [ ] Primary/secondary text vẫn giữ hierarchy.
- [ ] Không dùng màu là tín hiệu duy nhất.
- [ ] Positive/negative/status có icon/label/ký hiệu bổ sung.

## 4. Depth
- [ ] Hướng ánh sáng nhất quán.
- [ ] Shadow tương ứng elevation.
- [ ] Có scale shadow hữu hạn.
- [ ] Flat UI vẫn có tín hiệu layer khi cần.
- [ ] Overlap không che nội dung và vẫn ổn responsive.

## 5. Images
- [ ] Ảnh production đủ chất lượng.
- [ ] Text trên ảnh có contrast ổn định.
- [ ] Icon/screenshot không bị scale sai intended size.
- [ ] User-uploaded images được crop trong khung ổn định.
- [ ] Ảnh nền gần màu UI không bị bleed mất ranh giới.

## 6. Finishing touches
- [ ] Empty state được thiết kế nghiêm túc.
- [ ] Border thừa đã được thay bằng spacing/background/shadow khi hợp.
- [ ] Accent color được dùng tiết chế.
- [ ] Decoration background không cạnh tranh với content.
- [ ] Native/default elements chỉ custom khi có lợi ích rõ.

## 7. Học tiếp
- [ ] Tôi có thói quen phân tích quyết định bất ngờ trong design đẹp.
- [ ] Tôi có rebuild reference để luyện mắt thay vì chỉ xem.
- [ ] Mỗi lần luyện tôi ghi lại insight có thể tái sử dụng.

---

# Tóm tắt toàn bộ cuốn sách bằng 27 nguyên tắc

1. **Bắt đầu từ tính năng, không bắt đầu từ cái vỏ của app.**
2. **Giải quyết cấu trúc trước, chi tiết thị giác sau.**
3. **Thiết kế theo vòng lặp nhỏ và làm bản thật sớm.**
4. **Chọn một tính cách và giữ font, màu, radius, ngôn ngữ nhất quán với nó.**
5. **Giới hạn lựa chọn bằng hệ thống để giảm decision fatigue.**
6. **Hierarchy quan trọng hơn trang trí: không phải mọi thứ đều có trọng lượng ngang nhau.**
7. **Muốn một thứ nổi bật, đôi khi hãy giảm nhấn những thứ xung quanh.**
8. **Dùng label, màu semantics, grid và tỷ lệ như công cụ — không như luật cứng.**
9. **Whitespace và spacing truyền đạt cấu trúc, không phải diện tích lãng phí.**
10. **Đừng kéo mọi thứ rộng ra hoặc scale tất cả theo cùng tỷ lệ.**
11. **Typography cần hệ thống: type scale, font dễ đọc, line length hợp lý, baseline đúng và line-height theo ngữ cảnh.**
12. **Một UI tốt giúp người dùng biết nhìn đâu, hiểu cái gì thuộc với nhau và biết hành động nào quan trọng nhất mà không cần suy nghĩ nhiều.**
13. **Link không cần nổi bằng màu nếu weight/contrast hoặc hover đã đủ.**
14. **Căn chữ theo khả năng đọc; text dài thường cần một trục bắt đầu ổn định.**
15. **Letter-spacing là tinh chỉnh: siết heading khi cần, nới ALL CAPS để dễ đọc.**
16. **HSL giúp bạn suy nghĩ về hue, saturation và lightness thay vì mã màu rời rạc.**
17. **Palette thực tế cần nhiều family và nhiều shade hơn một dải 5 màu đẹp mắt.**
18. **Định nghĩa shade trước để tránh hàng chục màu gần giống nhau.**
19. **Lightness, saturation và perceived brightness không phải cùng một thứ.**
20. **Grey có thể warm/cool bằng cách pha hue nhẹ.**
21. **Accessibility không bắt buộc UI phải xấu; có thể flip contrast hoặc điều chỉnh hue.**
22. **Màu phải hỗ trợ thông tin, không được là cách duy nhất truyền đạt thông tin.**
23. **Depth hiệu quả đến từ logic ánh sáng, elevation, màu và overlap - không phải shadow ngẫu nhiên.**
24. **Ảnh tốt, contrast ổn định và asset đúng intended size quyết định rất nhiều đến độ polish.**
25. **Empty state, border, background và control mặc định đều là cơ hội để hoàn thiện UI.**
26. **Pattern quen thuộc là điểm bắt đầu; khi component quan trọng, presentation có thể được nghĩ lại.**
27. **Cách nâng trình lâu dài là phân tích quyết định lạ trong design tốt và tự rebuild chúng để hiểu chi tiết.**

# Phạm vi nguồn đã dùng

- PDF: **Refactoring UI — Adam Wathan & Steve Schoger**
- Phạm vi: **toàn bộ 218 trang**
- Nội dung được chuyển hóa theo trình tự của sách:
  - Starting from Scratch — trang 6-28
  - Hierarchy is Everything — trang 29-54
  - Layout and Spacing — trang 55-86
  - Designing Text — trang 87-117
  - Working with Color — trang 118-148
  - Creating Depth — trang 149-172
  - Working with Images — trang 173-190
  - Finishing Touches — trang 191-214
  - Leveling Up — trang 215-218

> Đây là bản diễn giải thực hành dành cho người mới, không phải bản dịch nguyên văn.
