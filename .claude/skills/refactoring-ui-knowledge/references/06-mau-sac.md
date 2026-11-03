# Phần VI - Làm việc với màu sắc

## Bài 29 - Dùng HSL để suy nghĩ về màu

### Vấn đề
Hex và RGB rất phổ biến nhưng khó giúp người mới hiểu mối quan hệ giữa các màu. Hai màu trông gần nhau có thể có mã hex không hề “gần nhau” về mặt trực giác.

### Mục tiêu
Dùng một mô hình màu giúp bạn suy nghĩ theo ba thuộc tính trực quan: **hue, saturation, lightness**.

### Lý thuyết
HSL mô tả màu bằng:
- **Hue:** vị trí trên bánh xe màu, đo bằng độ. 0° đỏ, 120° xanh lá, 240° xanh dương.
- **Saturation:** độ rực/màu sắc. 0% là xám, 100% là rất rực.
- **Lightness:** mức gần đen hoặc trắng. 0% đen, 100% trắng, khoảng 50% là màu thuần ở hue đó.

Sách cũng phân biệt HSL với HSB: “lightness” trong HSL không giống “brightness” trong HSB. Với web, sách ưu tiên HSL vì trình duyệt hiểu trực tiếp HSL.

### Khi nào áp dụng
- Xây palette cho web.
- Tạo các biến thể sáng/tối của một màu.
- Muốn hiểu tại sao một màu thay đổi khi chỉnh độ rực hoặc độ sáng.

### Cách làm
1. Xác định hue chính của màu thương hiệu.
2. Quan sát saturation để biết màu đang rực hay trung tính.
3. Quan sát lightness để biết màu gần đen/trắng đến đâu.
4. Khi tạo biến thể, chỉnh từng thuộc tính có chủ đích thay vì nhảy giữa các hex ngẫu nhiên.
5. Ghi lại các giá trị trong hệ thống màu cố định.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Nghĩ theo hue/saturation/lightness | Tạo màu mới bằng cách chọn hex tùy hứng |
| Dùng HSL để hiểu quan hệ màu | Nhầm lightness với HSB brightness |
| Ghi palette thành token | Mỗi component tự chọn một màu mới |

### Ví dụ đúng/sai
**Sai:** Cần một blue nhạt hơn nên kéo color picker đến khi “có vẻ ổn”, tạo thêm một mã hex không liên quan đến scale.

**Đúng:** Giữ hue gần màu gốc, điều chỉnh lightness/saturation có chủ đích rồi đưa shade vào palette.

### Lỗi thường gặp
- Chỉ thay lightness mà quên saturation.
- Hiểu 100% lightness là “màu rực nhất”; trong HSL nó là trắng.
- Dùng HSL nhưng vẫn tạo vô hạn màu không qua hệ thống.

### Ngoại lệ
Thiết kế software có thể hiển thị HSB/HSV mặc định. Điều quan trọng trong ngữ cảnh của sách không phải tên công cụ, mà là hiểu thuộc tính màu bạn đang thay đổi và dùng một hệ thống nhất quán.

### Checklist
- [ ] Tôi phân biệt được hue/saturation/lightness không?
- [ ] Shade mới có quan hệ rõ với màu gốc không?
- [ ] Tôi có đang tạo màu mới ngoài palette không?
- [ ] Với web, token màu có thể biểu diễn nhất quán không?

### Tóm tắt
**HSL biến màu từ “mã khó nhớ” thành ba quyết định mà mắt người dễ hiểu.**

---

## Bài 30 - Một palette thực tế cần nhiều màu hơn bạn nghĩ

### Vấn đề
Palette 5 màu trông đẹp trên một dải mẫu nhưng thường không đủ để xây UI thật. Khi bắt đầu làm text, background, control, trạng thái và biểu đồ, bạn sẽ nhanh chóng thiếu lựa chọn.

### Mục tiêu
Xây palette có đủ phạm vi để làm sản phẩm thực tế mà không phải chế thêm màu ngẫu nhiên trong lúc thiết kế.

### Lý thuyết
Sách chia palette UI thành ba nhóm:

1. **Greys:** dùng cho text, background, panel, form control; thường cần khoảng 8-10 shade.
2. **Primary color(s):** thường 1, có thể 2 màu chính; cũng cần khoảng 5-10 shade.
3. **Accent colors:** dùng cho feature nổi bật hoặc trạng thái ngữ nghĩa như destructive, warning, positive; mỗi màu cũng cần nhiều shade.

Với UI phức tạp có chart, calendar, tag/category, tổng số màu accent có thể nhiều hơn đáng kể. Sách nêu rằng một UI phức tạp có thể cần tới khoảng mười màu khác nhau, mỗi màu lại có 5-10 shade.

### Khi nào áp dụng
- Bắt đầu design system.
- Sản phẩm có form, dashboard, alert, status, chart.
- Team thường xuyên “thiếu một màu xám ở giữa”.

### Cách làm
1. Tạo grey scale đủ rộng trước.
2. Chọn 1-2 primary colors và tạo nhiều shade.
3. Liệt kê các semantic states thật sự cần: error/destructive, warning, positive, info...
4. Với dữ liệu phân loại, bổ sung accent colors khi cần.
5. Đặt tên/token để tái sử dụng thay vì copy mã màu bằng tay.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Có nhiều shade trong từng family | Chỉ có 1 blue, 1 red, 1 green |
| Dùng dark grey thay true black | Lạm dụng #000 ở mọi text |
| Accent theo nhu cầu thật | Chọn 5 màu đẹp rồi ép mọi use case vào đó |

### Ví dụ đúng/sai
**Sai:** Design system chỉ có `gray-light`, `gray`, `gray-dark`; sau một tuần xuất hiện thêm 12 mã xám rải rác trong file.

**Đúng:** Có grey scale 8-10 mức, đủ cho primary text, secondary text, border, muted background và panel.

### Lỗi thường gặp
- Palette ít màu nhưng nhiều “one-off color”.
- Không có shade siêu nhạt cho tinted background.
- Không có shade tối cho text trên background nhạt.
- Dùng quá nhiều accent nhưng không có vai trò rõ.

### Ngoại lệ
UI rất nhỏ có thể không cần đầy đủ 10 màu x 10 shade. Mục tiêu là có **đủ lựa chọn để không phải phá hệ thống**, không phải đạt một số lượng bắt buộc.

### Checklist
- [ ] Grey scale có đủ cho text/background/border không?
- [ ] Primary color có light và dark shade không?
- [ ] Semantic states có màu riêng khi thật sự cần không?
- [ ] Chart/tag có cần accent bổ sung không?
- [ ] Có màu nào đang tồn tại chỉ vì “lúc đó thấy đẹp” không?

### Tóm tắt
**Palette UI tốt không phải một dải 5 màu đẹp; nó là kho lựa chọn có hệ thống cho hàng chục tình huống thật.**

---

## Bài 31 - Định nghĩa shade từ đầu, đừng tạo tại chỗ

### Vấn đề
Nếu mỗi lần cần blue nhạt/tối hơn bạn lại gọi `lighten()`, `darken()` hoặc kéo color picker, rất nhanh bạn sẽ có hàng chục biến thể gần giống nhau.

### Mục tiêu
Tạo một **scale shade cố định** trước, sau đó chỉ chọn từ scale đó.

### Lý thuyết
Quy trình trong sách:
1. Chọn **base color** - shade ở giữa, thường là màu dùng tốt cho button background.
2. Chọn **darkest** dựa trên use case như text.
3. Chọn **lightest** dựa trên use case như tinted background.
4. Điền các shade ở giữa bằng cách chia khoảng.

Một scale 9 mức dễ tổ chức bằng tên 100-900: base 500, sáng nhất 100, tối nhất 900; sau đó điền 300/700 rồi 200/400/600/800.

### Khi nào áp dụng
- Bất kỳ palette primary/accent nào.
- Grey scale.
- Team đang có quá nhiều màu gần giống nhau.

### Cách làm
1. Chọn base theo component thật, ví dụ button.
2. Dùng component có cả text + tinted background, như alert, để tìm hai đầu scale.
3. Chia scale thành 5-10 shade; 9 là cấu trúc tiện dùng.
4. So sánh các shade cạnh nhau, đảm bảo mỗi mức đủ khác.
5. Dùng palette trong UI thật rồi tinh chỉnh nhẹ nếu cần.
6. Tránh thêm shade mới trừ khi có lý do rõ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Chọn màu theo ngữ cảnh sử dụng | Tạo shade bằng công thức rồi tin tuyệt đối |
| Fill gaps theo từng khoảng | Tạo 35 màu “blue gần giống nhau” |
| Tinh chỉnh bằng mắt sau khi dùng thật | Thêm shade mới mỗi khi một màn hình thấy thiếu |

### Ví dụ đúng/sai
**Sai:** Mỗi alert có một mã blue riêng vì designer đã dùng `lighten(base, x%)` với x khác nhau.

**Đúng:** Alert dùng `blue-100` làm nền, `blue-900` cho text, button dùng `blue-500`, hover chọn từ scale có sẵn.

### Lỗi thường gặp
- Tin rằng palette có thể được tạo hoàn toàn bằng toán.
- Chọn edge shades mà không có use case.
- Các shade gần nhau đến mức không phân biệt được.

### Ngoại lệ
Sau khi áp palette vào UI thật, điều chỉnh saturation/lightness của một số shade là bình thường. Sách nhấn mạnh hãy **tin mắt hơn con số**, nhưng đừng biến mỗi điều chỉnh thành một shade mới vô hạn.

### Checklist
- [ ] Base shade có use case cụ thể không?
- [ ] Darkest/lightest có use case cụ thể không?
- [ ] Mỗi shade liền kề đủ khác nhau không?
- [ ] Tôi đang chọn từ scale thay vì color picker không?
- [ ] Shade mới có thật sự cần thiết không?

### Tóm tắt
**Tạo shade một lần để dùng nhiều lần; đừng tái phát minh cùng một màu ở mỗi component.**

---

## Bài 32 - Đừng để lightness làm mất độ rực

### Vấn đề
Bạn tạo một màu sáng hơn bằng cách tăng lightness, nhưng kết quả trở nên bạc màu. Tạo màu tối hơn thì lại xỉn và gần đen.

### Mục tiêu
Giữ cho các shade sáng/tối vẫn có cảm giác thuộc cùng một color family và không mất cường độ màu.

### Lý thuyết
Trong HSL, khi lightness tiến gần 0% hoặc 100%, tác động của saturation yếu đi. Vì thế, nếu chỉ tăng/giảm lightness mà giữ nguyên saturation, các shade ở hai đầu dễ bị wash out.

Sách đưa ra hai chiến lược:
- Tăng saturation khi shade đi xa khỏi khoảng 50% lightness.
- Dùng **perceived brightness** của hue: các hue không sáng như nhau dù có cùng HSL lightness. Có thể xoay hue nhẹ về phía hue sáng hơn hoặc tối hơn để thay đổi cảm giác sáng/tối mà giữ cường độ tốt hơn.

Các vùng hue được sách dùng làm điểm tham chiếu:
- Sáng hơn: gần 60°, 180°, 300°.
- Tối hơn: gần 0°, 120°, 240°.

Hue shift chỉ nên nhỏ, khoảng không quá 20-30° để shade vẫn trông như cùng một màu.

### Khi nào áp dụng
- Xây scale cho màu rực.
- Màu vàng/cyan/magenta dễ bị nhạt hoặc bẩn khi đổi lightness.
- Cần dark shade giàu màu thay vì nâu/xám xỉn.

### Cách làm
1. Bắt đầu từ base color.
2. Khi làm sáng/tối, quan sát saturation có bị suy yếu về cảm nhận không.
3. Tăng saturation nếu cần.
4. Với màu đã 100% saturation, thử xoay hue nhẹ về hướng có perceived brightness phù hợp.
5. Chỉ hue-shift một lượng nhỏ rồi so sánh toàn scale.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Quan sát cảm giác màu, không chỉ HSL number | Giữ saturation cố định cho mọi shade |
| Hue-shift nhẹ để giữ intensity | Xoay hue 60-90° làm đổi hẳn color family |
| So sánh cả scale | Tối ưu từng shade tách rời |

### Ví dụ đúng/sai
**Sai:** Yellow base khi làm dark chỉ giảm lightness, kết quả chuyển thành màu nâu xỉn.

**Đúng:** Khi giảm lightness, xoay hue nhẹ về orange và điều chỉnh saturation để shade tối vẫn ấm, giàu màu.

### Lỗi thường gặp
- Nghĩ lightness bằng perceived brightness.
- Thấy shade washed out nhưng tiếp tục chỉ chỉnh lightness.
- Hue shift quá xa.

### Ngoại lệ
Không phải màu nào cũng cần hue rotation. Sách mô tả đây là kỹ thuật hữu ích đặc biệt khi cần giữ intensity; nếu scale trông ổn chỉ bằng saturation/lightness thì không cần phức tạp hóa.

### Checklist
- [ ] Shade sáng/tối có bị bạc màu không?
- [ ] Tôi đã thử tăng saturation chưa?
- [ ] Base đã 100% saturation thì có cần hue shift nhẹ không?
- [ ] Hue shift có dưới khoảng 20-30° không?
- [ ] Cả family vẫn được nhận ra là cùng một màu không?

### Tóm tắt
**Đổi lightness không đồng nghĩa với đổi brightness cảm nhận; hãy giữ intensity bằng saturation và hue khi cần.**

---

## Bài 33 - Grey không nhất thiết phải hoàn toàn xám

### Vấn đề
Grey 0% saturation có thể khiến UI trung tính nhưng cũng dễ vô hồn. Trong khi đó nhiều giao diện “xám” đẹp thực chất đang dùng grey pha màu.

### Mục tiêu
Dùng **color temperature** để khiến grey scale hỗ trợ personality của sản phẩm.

### Lý thuyết
True grey có saturation 0%. Nhưng grey có thể được pha hue nhẹ:
- Pha blue -> cảm giác **cool**.
- Pha yellow/orange -> cảm giác **warm**.

Để temperature nhất quán, khi đi ra các shade rất sáng/tối cần tăng saturation tương ứng; nếu không, các shade biên dễ bị washed out so với shade giữa.

### Khi nào áp dụng
- Dashboard/SaaS cần cảm giác cool, kỹ thuật.
- Brand muốn warm, thân thiện hơn.
- Neutral palette trông quá “dead”.

### Cách làm
1. Chọn hướng cool hoặc warm phù hợp personality.
2. Thêm một lượng hue rất nhỏ vào grey scale.
3. So sánh toàn scale, đặc biệt các shade sáng/tối.
4. Tăng saturation ở edge shades nếu chúng mất temperature.
5. Dùng grey scale đó nhất quán cho text, border, surface.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Pha màu nhẹ có chủ đích | Mỗi shade xám lệch sang một hue khác nhau |
| Giữ temperature nhất quán | Edge shades trở về neutral ngẫu nhiên |
| Chọn mức saturation theo mood | Nghĩ “grey” bắt buộc saturation = 0 |

### Ví dụ đúng/sai
**Sai:** Một UI dùng blue-grey cho card, neutral-grey cho border, warm-grey cho text mà không có chủ đích.

**Đúng:** Toàn bộ neutral scale nghiêng nhẹ sang blue, tạo cảm giác mát và đồng nhất.

### Lỗi thường gặp
- Pha quá nhiều màu khiến “grey” thành màu rõ rệt.
- Dùng cùng saturation ở mọi lightness và bị wash out.
- Không gắn grey temperature với personality tổng thể.

### Ngoại lệ
Nếu sản phẩm cần neutral thật sự hoặc đã có brand colors rất mạnh, grey gần 0% saturation có thể là lựa chọn đúng. Kỹ thuật tint grey là tùy chọn, không phải yêu cầu bắt buộc.

### Checklist
- [ ] Neutral palette đang cool, warm hay neutral có chủ đích?
- [ ] Các shade biên còn giữ temperature không?
- [ ] Grey có hỗ trợ personality không?
- [ ] Có shade nào nhìn lệch hẳn khỏi family không?

### Tóm tắt
**Grey cũng là màu; pha nhiệt độ nhẹ có thể làm cả giao diện có cá tính hơn.**

---

## Bài 34 - Accessible không có nghĩa là phải xấu

### Vấn đề
Khi cố tăng contrast cho text trên nền màu, người mới thường làm nền rất tối hoặc text gần trắng hoàn toàn. Kết quả có thể đạt contrast nhưng phá hierarchy, vì những panel phụ bỗng trở thành điểm hút mắt nhất.

### Mục tiêu
Đáp ứng contrast theo hướng vẫn giữ được hierarchy và personality của UI.

### Lý thuyết
Theo ngưỡng được sách nêu, WCAG khuyến nghị:
- Text bình thường dưới khoảng 18px: contrast tối thiểu **4.5:1**.
- Text lớn: tối thiểu **3:1**.

Hai kỹ thuật chính trong sách:

1. **Flip the contrast:** thay vì white text trên nền màu tối, dùng text màu tối trên nền màu rất nhạt. Màu vẫn hiện diện nhưng bớt áp đảo.
2. **Rotate the hue:** với colored text trên colored background, nếu chỉ tăng lightness thì text thứ cấp dễ tiến quá gần trắng. Có thể xoay hue về màu có perceived brightness cao hơn như cyan, magenta hoặc yellow để tăng contrast mà vẫn giữ màu.

### Khi nào áp dụng
- Alert/banner màu.
- Tag/status.
- Secondary text trong panel màu tối.
- Component cần màu nhưng không nên thành focus chính.

### Cách làm
1. Đo contrast thay vì đoán bằng mắt.
2. Nếu white-on-color bắt bạn dùng nền quá tối, thử đảo thành dark-on-light.
3. Nếu secondary colored text chưa đủ contrast, thử điều chỉnh hue thay vì chỉ tăng lightness.
4. Kiểm tra hierarchy sau khi đạt contrast.
5. So sánh primary/secondary text để đảm bảo chúng vẫn khác cấp.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Đạt contrast và kiểm tra hierarchy | Làm mọi panel màu thành khối rất tối |
| Flip contrast khi hợp | Cố giữ white-on-color bằng mọi giá |
| Dùng hue để tăng perceived brightness | Đẩy mọi secondary text gần trắng |

### Ví dụ đúng/sai
**Sai:** Một status nhỏ cần readable nên dùng nền đỏ cực tối + text trắng, khiến nó nổi hơn cả CTA.

**Đúng:** Dùng nền đỏ rất nhạt + text đỏ đậm, vẫn đọc rõ nhưng không chiếm focus.

### Lỗi thường gặp
- Chỉ kiểm tra đẹp mà không kiểm tra contrast.
- Chỉ kiểm tra contrast mà không kiểm tra hierarchy.
- Primary và secondary text trở nên cùng độ sáng.

### Ngoại lệ
Khi component thực sự cần thu hút attention mạnh, nền màu tối có thể đúng. Vấn đề không phải dark background, mà là dùng nó cho phần tử vốn không nên là focus.

### Checklist
- [ ] Contrast đạt ngưỡng sách nêu cho loại text chưa?
- [ ] Component có đang nổi quá mức cần thiết không?
- [ ] Có thể flip contrast không?
- [ ] Primary và secondary text vẫn khác nhau rõ không?

### Tóm tắt
**Accessibility và hierarchy không đối lập; hãy thay cấu trúc contrast thay vì chỉ làm mọi thứ tối hơn.**

---

## Bài 35 - Đừng dùng màu như tín hiệu duy nhất

### Vấn đề
Nếu một metric tốt/xấu chỉ khác nhau bằng xanh/đỏ, người bị color blindness có thể không phân biệt được. Tương tự, chart nhiều đường chỉ khác hue có thể trở nên khó hiểu.

### Mục tiêu
Đảm bảo thông tin vẫn hiểu được khi người dùng không phân biệt được màu như bạn mong đợi.

### Lý thuyết
Màu nên **hỗ trợ** một thông điệp mà thiết kế đã truyền đạt bằng cách khác, chứ không nên là kênh duy nhất.

Ví dụ trong sách:
- Metric positive/negative: thêm icon để chỉ tăng/giảm.
- Biểu đồ: dùng khác biệt về **độ sáng/tối (contrast)** thay vì chỉ dùng các hue khác nhau, vì light-dark thường dễ phân biệt hơn.

### Khi nào áp dụng
- Status success/error.
- Chart/graph.
- Metric card.
- Form validation.
- Calendar/category/tag.

### Cách làm
1. Xác định thông tin nào hiện đang phụ thuộc hoàn toàn vào màu.
2. Thêm icon, label, pattern hoặc ký hiệu khác.
3. Với chart, tạo khác biệt bằng lightness/contrast khi có thể.
4. Kiểm tra thiết kế ở grayscale để xem thông tin còn hiểu được không.
5. Giữ màu như lớp hỗ trợ tăng tốc nhận diện.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Màu + icon/label | Chỉ đỏ/xanh để nói xấu/tốt |
| Tăng contrast giữa series | Nhiều hue có độ sáng tương tự |
| Kiểm tra grayscale | Giả định ai cũng phân biệt màu giống nhau |

### Ví dụ đúng/sai
**Sai:** +12% và -8% chỉ khác nhau bằng green/red text.

**Đúng:** Dùng mũi tên lên/xuống hoặc dấu +/-, đồng thời vẫn dùng màu để tăng tốc nhận diện.

### Lỗi thường gặp
- Tưởng thêm nhiều màu là thêm nhiều thông tin.
- Không có label trên legend/chart.
- Icon chỉ mang tính trang trí, không làm rõ nghĩa.

### Ngoại lệ
Màu vẫn rất hữu ích khi được dùng như tín hiệu bổ sung. Sách không khuyên bỏ màu, mà khuyên **không phụ thuộc vào màu một mình**.

### Checklist
- [ ] Bỏ màu đi, người dùng còn hiểu trạng thái không?
- [ ] Positive/negative có dấu hiệu khác ngoài màu không?
- [ ] Các series chart có đủ khác biệt về contrast không?
- [ ] Màu đang hỗ trợ hay đang gánh toàn bộ ý nghĩa?

### Tóm tắt
**Thiết kế phải truyền đạt ý nghĩa trước; màu chỉ nên làm thông điệp đó nhanh và rõ hơn.**

---
