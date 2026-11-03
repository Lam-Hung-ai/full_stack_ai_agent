# Phần IX - Finishing touches

## Bài 45 - “Nâng cấp” những thứ mặc định trước khi thêm đồ trang trí mới

### Vấn đề
Khi UI trông hơi nhạt, phản xạ thường là thêm illustration, decorative shape hoặc một component mới. Nhưng đôi khi chính các phần tử đã có sẵn vẫn còn rất “mặc định” và chưa được khai thác.

### Mục tiêu
Tạo cảm giác polished bằng cách cải thiện những element đang hiện diện thay vì tăng độ phức tạp của layout.

### Lý thuyết
Sách đưa ra một số ví dụ:
- Bullet list -> thay bullet bằng icon phù hợp như checkmark, arrow hoặc icon theo chủ đề.
- Testimonial -> biến dấu ngoặc kép thành visual element lớn hơn, có màu.
- Link -> dùng weight/màu hoặc custom underline.
- Checkbox/radio -> dùng brand color ở selected state thay vì browser default.

Điểm chung: không phải thêm thông tin mới, mà **tạo personality từ element đã cần có**.

### Khi nào áp dụng
- Landing page trông “đúng nhưng nhạt”.
- Form có nhiều native controls.
- Testimonial, feature list, pricing section.

### Cách làm
1. Liệt kê những element mặc định: bullet, link, checkbox, radio, quote.
2. Chọn 1-2 loại đáng nâng cấp nhất.
3. Áp brand color hoặc icon có ý nghĩa.
4. Giữ treatment nhất quán ở mọi nơi cùng loại.
5. Dừng trước khi mỗi element đều trở thành decoration.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Làm element sẵn có giàu personality hơn | Thêm decoration vô nghĩa chỉ để lấp chỗ |
| Icon phù hợp nội dung | Dùng icon ngẫu nhiên cho mọi bullet |
| Brand color ở selected state | Làm control custom nhưng khó nhận biết trạng thái |

### Ví dụ đúng/sai
**Sai:** Feature list có bullet chấm tròn mặc định, phía sau lại thêm một illustration lớn chỉ để “trang trí”.

**Đúng:** Dùng check icon hoặc icon chủ đề cho từng bullet, đủ làm section có điểm nhấn mà không cần thêm layout phức tạp.

### Lỗi thường gặp
- Custom control làm mất affordance.
- Dùng quá nhiều icon khác style.
- Underline link quá dày và cạnh tranh với text.

### Ngoại lệ
Khi native controls quan trọng về consistency/accessibility của platform, có thể giữ nguyên. Tinh thần bài là tìm cơ hội nâng cấp hợp lý, không bắt buộc custom mọi thứ.

### Checklist
- [ ] Có element mặc định nào đang làm UI trông chưa polished không?
- [ ] Có thể dùng brand color thay vì thêm element mới không?
- [ ] Icon/decoration có liên quan đến nội dung không?
- [ ] Các control vẫn dễ nhận biết và dùng được không?

### Tóm tắt
**Trước khi thêm thứ mới, hãy xem những thứ đang có có thể được làm tốt hơn không.**

---

## Bài 46 - Thêm màu bằng accent border

### Vấn đề
Không phải team nào cũng có illustration hoặc photography đẹp. Một layout đúng hierarchy vẫn có thể trông hơi nhạt nếu toàn bộ surface đều trung tính.

### Mục tiêu
Thêm visual flair bằng một kỹ thuật rất đơn giản: đường viền màu nhấn ở vị trí có chủ đích.

### Lý thuyết
Accent border có thể xuất hiện:
- Trên đầu card.
- Dưới active navigation item.
- Dọc cạnh alert.
- Dưới headline.
- Dọc trên cùng của toàn layout.

Một hình chữ nhật màu nhỏ có thể khiến component trông “designed” hơn mà không cần kỹ năng illustration.

### Khi nào áp dụng
- Card trung tính.
- Active nav/tab.
- Alert/message.
- Section heading.
- App shell hoặc marketing page quá phẳng.

### Cách làm
1. Chọn một màu từ palette có sẵn.
2. Chọn một vị trí rõ vai trò: active, highlight, grouping.
3. Dùng border mảnh hoặc short accent thay vì tô cả surface.
4. Giữ cùng độ dày/logic giữa các component tương tự.
5. Kiểm tra xem accent có đang tạo hierarchy đúng không.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng accent border ở điểm có ý nghĩa | Rải đường màu lên mọi card |
| Lấy màu từ system | Thêm màu mới chỉ vì border |
| Giữ thickness nhất quán | Mỗi màn hình một kiểu accent khác nhau |

### Ví dụ đúng/sai
**Sai:** Mỗi card pricing có một border top màu khác nhau không có semantics, làm trang trở thành cầu vồng.

**Đúng:** Dùng một accent color nhất quán để đánh dấu plan nổi bật hoặc active state.

### Lỗi thường gặp
- Accent border quá dày thành block trang trí nặng.
- Dùng quá nhiều màu.
- Không có liên hệ giữa accent và state/hierarchy.

### Ngoại lệ
Nếu UI đã có ảnh, gradient, illustration hoặc color surface mạnh, accent border có thể dư thừa. Đây là giải pháp cho nơi cần chút điểm nhấn, không phải lớp bắt buộc.

### Checklist
- [ ] Border có vai trò rõ không?
- [ ] Màu có thuộc palette không?
- [ ] Accent có lặp nhất quán không?
- [ ] Có đang dùng quá nhiều accent cùng lúc không?

### Tóm tắt
**Một đường màu nhỏ, đúng chỗ, thường hiệu quả hơn một khối trang trí lớn không có lý do.**

---

## Bài 47 - Trang trí background mà không phá readability

### Vấn đề
Sau khi hierarchy, spacing và typography đã ổn, layout vẫn có thể hơi đơn điệu. Nếu giải bằng decoration quá mạnh, content lại bị lấn át.

### Mục tiêu
Thêm texture và nhịp điệu cho background nhưng vẫn giữ nội dung là focus.

### Lý thuyết
Sách đưa ra ba nhóm kỹ thuật:

1. **Đổi màu background:** dùng surface khác để tách section; có thể dùng gradient nhẹ. Với gradient, sách gợi ý hai hue không cách nhau quá khoảng 30° để kết quả tự nhiên hơn.
2. **Repeating pattern:** có thể phủ toàn nền hoặc chỉ dọc một cạnh; giữ contrast pattern/background thấp.
3. **Simple shape/illustration:** đặt shape, đoạn pattern hoặc graphic đơn giản ở vị trí cụ thể; vẫn giữ contrast thấp.

### Khi nào áp dụng
- Landing page có nhiều section trắng nối nhau.
- Pricing/feature panel cần tách nhẹ.
- Footer/CTA section cần personality.

### Cách làm
1. Chỉ chọn vài section cần khác background.
2. Bắt đầu bằng color shift nhẹ.
3. Nếu dùng gradient, giữ hai hue gần nhau.
4. Nếu dùng pattern/shape, giảm contrast đến mức content luôn thắng.
5. Kiểm tra responsive: graphic không che text hay tạo vùng rối.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Background hỗ trợ phân section | Mỗi section một kiểu decoration khác nhau |
| Pattern contrast thấp | Pattern đậm cạnh tranh với paragraph |
| Shape đơn giản | Decoration chạm/che content |

### Ví dụ đúng/sai
**Sai:** Section pricing có pattern đậm ngay sau giá và CTA, làm chữ khó đọc.

**Đúng:** Pattern rất nhạt chỉ xuất hiện ở edge hoặc vùng trống, content vẫn có contrast mạnh nhất.

### Lỗi thường gặp
- Gradient có hue cách nhau quá xa và trông rực bất ngờ.
- Pattern lặp dày gây moiré/visual noise.
- Decoration không tính đến mobile crop.

### Ngoại lệ
UI utilitarian hoặc data-dense có thể không cần decoration background. Sách đặt phần này ở “finishing touches”, nghĩa là chỉ nên dùng sau khi nền tảng đã ổn.

### Checklist
- [ ] Background có giúp tách section không?
- [ ] Contrast decoration có thấp hơn content không?
- [ ] Gradient có quá nhiều hue không?
- [ ] Mobile có giữ readability không?

### Tóm tắt
**Background có thể thú vị hơn mà không cần trở thành nội dung chính.**

---

## Bài 48 - Empty state là màn hình thật, không phải phần dư

### Vấn đề
Designer thường dành nhiều thời gian cho trạng thái đầy dữ liệu mẫu đẹp, nhưng người dùng mới lại nhìn thấy một màn hình trống đầu tiên. Nếu empty state chỉ có “No data”, trải nghiệm mở đầu sẽ rất yếu.

### Mục tiêu
Biến empty state thành một trạng thái có giá trị: giải thích, định hướng và thúc đẩy hành động tiếp theo.

### Lý thuyết
Với feature phụ thuộc user-generated content, empty state nên là **priority**. Sách đề xuất:
- Thêm illustration/image để thu hút attention.
- Nhấn mạnh CTA giúp người dùng tạo nội dung đầu tiên.
- Ẩn tabs, filters và supporting UI vô dụng cho đến khi có dữ liệu.

Empty state thường là lần đầu người dùng tương tác với feature, nên nó không nên là một khoảng trống lạnh lẽo.

### Khi nào áp dụng
- Danh sách contacts chưa có ai.
- Project/task list mới.
- Dashboard chưa có dữ liệu.
- Saved items, favorites, uploads.

### Cách làm
1. Thiết kế empty state cùng lúc với populated state.
2. Viết một câu giải thích ngắn: ở đây sẽ có gì.
3. Đặt CTA rõ để tạo item đầu tiên.
4. Thêm visual nếu giúp context thú vị hơn.
5. Ẩn filters/tabs/actions chưa có tác dụng.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| CTA tạo nội dung đầu tiên | Chỉ hiện “No data” |
| Ẩn supporting UI chưa dùng được | Hiện 10 filter cho danh sách rỗng |
| Xem empty state là first-run experience | Chờ đến cuối mới thiết kế |

### Ví dụ đúng/sai
**Sai:** Trang “Discounts” trống nhưng vẫn có filter bar, sort, pagination và table header; giữa trang chỉ có chữ “No discounts”.

**Đúng:** Ẩn UI không cần thiết, hiển thị illustration nhẹ, mô tả lợi ích và nút “Create discount”.

### Lỗi thường gặp
- CTA yếu hoặc không có.
- Empty state không giải thích người dùng nên làm gì.
- Vẫn giữ toàn bộ chrome của populated state.

### Ngoại lệ
Một số empty state do lỗi hệ thống hoặc permission khác với “chưa có dữ liệu”. Bài này nói về empty state bình thường của feature chưa có content.

### Checklist
- [ ] Người dùng có biết tại sao màn hình trống không?
- [ ] Có next action rõ không?
- [ ] Supporting UI vô dụng đã ẩn chưa?
- [ ] Empty state có cùng quality với populated state không?

### Tóm tắt
**Trạng thái rỗng thường là điểm bắt đầu của người dùng, nên hãy thiết kế nó như một màn hình chính thức.**

---

## Bài 49 - Dùng ít border hơn

### Vấn đề
Border là cách nhanh nhất để tách element, nên người mới dễ dùng border cho mọi hàng, mọi card, mọi section. Kết quả là UI đầy đường kẻ và cảm giác chật chội.

### Mục tiêu
Tạo separation bằng những tín hiệu nhẹ hơn trước khi resort to border.

### Lý thuyết
Sách gợi ý ba thay thế:

1. **Box shadow:** outline element nhẹ hơn border, đặc biệt khi surface element khác màu background.
2. **Hai background color khác nhau:** chỉ cần chênh nhẹ cũng đủ phân vùng.
3. **Thêm spacing:** khoảng cách lớn hơn giữa group là một separator không cần thêm UI.

### Khi nào áp dụng
- List/card dày đặc border.
- Dialog/form có nhiều section.
- Table-like layouts.

### Cách làm
1. Xác định border nào đang thực sự truyền đạt cấu trúc.
2. Với card/surface, thử shadow nhẹ.
3. Với hai vùng liền nhau, thử đổi surface color.
4. Với nhóm nội dung, tăng spacing giữa nhóm.
5. Chỉ giữ border nơi separation vẫn chưa đủ rõ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng spacing/background trước | Kẻ border quanh mọi thứ |
| Shadow subtle khi hợp | Shadow và border cùng lúc không cần thiết |
| Giữ border có chức năng | Giữ border vì “component mặc định có” |

### Ví dụ đúng/sai
**Sai:** Contact picker có border quanh container, border từng row, border search box, border footer và border giữa mọi group.

**Đúng:** Dùng surface/shadow cho container, spacing hoặc background nhẹ cho group; chỉ giữ line nơi thật sự cần.

### Lỗi thường gặp
- Xóa border nhưng spacing không đủ nên grouping mơ hồ.
- Dùng shadow nặng hơn cả border cũ.
- Surface color khác quá nhiều làm layout bị chia vụn.

### Ngoại lệ
Data table cần scan theo hàng/cột hoặc component có boundary quan trọng có thể vẫn cần border. Mục tiêu là **không dùng border như phản xạ đầu tiên**.

### Checklist
- [ ] Border này có nhiệm vụ gì?
- [ ] Có thể thay bằng spacing không?
- [ ] Có thể thay bằng background khác nhẹ không?
- [ ] Shadow có làm distinction tinh tế hơn không?
- [ ] UI sau khi bỏ border có dễ hiểu hơn không?

### Tóm tắt
**Separation có thể đến từ khoảng cách, surface và depth; border chỉ là một trong nhiều công cụ.**

---

## Bài 50 - Đừng để “component phải trông như thế này” giới hạn thiết kế

### Vấn đề
Chúng ta thường có hình mẫu cố định: dropdown là hộp trắng + list; table là cột dữ liệu thuần text; radio là vòng tròn cạnh label. Những khuôn này giúp nhanh nhưng cũng dễ giới hạn giải pháp.

### Mục tiêu
Giữ semantics và chức năng, nhưng cho phép presentation được thiết kế lại khi component là phần quan trọng của trải nghiệm.

### Lý thuyết
Sách minh họa:
- Dropdown có thể chia section, nhiều cột, icon, supporting text.
- Table có thể gộp các field liên quan nếu không cần sort riêng; có thể có image, status color, hierarchy.
- Radio buttons quan trọng có thể trở thành selectable cards.

Constraints rất hữu ích, nhưng đôi khi một chút tự do giúp UI tiến lên cấp độ khác.

### Khi nào áp dụng
- Navigation mega menu/dropdown.
- Data table không chỉ để tính toán thô.
- Plan picker, pricing selector, onboarding choices.
- Component quan trọng nhưng default presentation quá nghèo.

### Cách làm
1. Tách **semantics/behavior** khỏi hình dạng mặc định.
2. Hỏi: người dùng thực sự cần so sánh, chọn hay khám phá cái gì?
3. Nếu dropdown chứa nội dung phong phú, chia nhóm và thêm hierarchy.
4. Nếu table có field liên quan, gộp khi không cần sort riêng.
5. Nếu radio choice là quyết định quan trọng, chuyển thành cards có selected state rõ.
6. Đảm bảo interaction vẫn quen và dễ hiểu.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Thiết kế presentation theo nhiệm vụ | Phá semantics chỉ để trông khác |
| Gộp data liên quan khi hợp | Gộp cột cần sort/filter độc lập |
| Selectable cards cho lựa chọn quan trọng | Biến mọi radio nhỏ thành card lớn |

### Ví dụ đúng/sai
**Sai:** Chọn subscription plan bằng 4 dòng radio nhỏ dù đây là quyết định chính của màn hình.

**Đúng:** Mỗi plan là một selectable card với dung lượng, giá và trạng thái selected rõ.

### Lỗi thường gặp
- “Sáng tạo” khiến component không còn dễ nhận biết.
- Tăng visual complexity nhưng không tăng hiểu biết.
- Gộp data làm mất khả năng sort/filter cần thiết.

### Ngoại lệ
Component phổ biến, ít quan trọng hoặc cần tốc độ thao tác cao thường nên giữ pattern quen thuộc. Không phải cái gì cũng cần reinvent.

### Checklist
- [ ] Component mặc định có đang giới hạn thông tin cần truyền đạt không?
- [ ] Behavior/semantics vẫn rõ không?
- [ ] Sự thay đổi có giúp scan/chọn/so sánh tốt hơn không?
- [ ] Có đang sáng tạo chỉ để khác biệt không?

### Tóm tắt
**Pattern quen thuộc là điểm bắt đầu, không phải luật hình thức bất biến.**

---
