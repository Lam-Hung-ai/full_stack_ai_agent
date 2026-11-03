# Phần III — Layout và spacing: làm giao diện dễ hiểu bằng khoảng trống

## Bài 14 — Bắt đầu với nhiều khoảng trắng hơn bạn nghĩ

### Vấn đề
Khi UI chật, phản xạ thông thường là thêm từng chút margin/padding cho đến khi “đỡ xấu”. Cách này thường chỉ đạt mức vừa đủ không tệ, chứ chưa chắc tạo cảm giác sạch và rõ.

### Mục tiêu
Dùng whitespace như một công cụ tổ chức nội dung, không phải phần diện tích “bị lãng phí”.

### Lý thuyết
Một cách hiệu quả là làm ngược: **bắt đầu rộng rãi hơn mức cần thiết rồi giảm dần**. Việc nhận ra “quá nhiều khoảng trống” thường dễ hơn nhận ra “thiếu một chút khoảng trống”.

### Khi nào áp dụng
- Form, card, settings page.
- Khi UI trông chật hoặc khó quét.
- Khi các nhóm thông tin dính vào nhau.

### Cách làm
1. Tăng padding của container và khoảng cách giữa các nhóm.
2. Nhìn toàn bộ màn hình chứ không chỉ component riêng lẻ.
3. Giảm dần những chỗ thật sự quá rộng.
4. Giữ khoảng cách trong cùng nhóm nhỏ hơn khoảng cách giữa các nhóm.
5. Kiểm tra ở nhiều kích thước màn hình.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Bắt đầu rộng rồi thu lại | Bắt đầu chật rồi “vá” thêm margin |
| Dùng whitespace để nhóm nội dung | Dùng border cho mọi nhóm |
| Xem khoảng trống là một thành phần thiết kế | Cố lấp kín màn hình |

### Ví dụ đúng/sai
**Sai:** Card xác thực hai bước có title, mô tả, input và nút gần sát nhau vì “tiết kiệm không gian”.

**Đúng:** Title và phần form được tách bằng khoảng rõ; các input có nhịp; CTA không dính vào field cuối.

### Lỗi thường gặp
- Đồng nhất “gọn” với “chật”.
- Chỉ tăng padding trong component mà không xem spacing giữa các component.
- Dùng whitespace không theo hệ thống.

### Ngoại lệ
Dashboard cần hiển thị nhiều dữ liệu cùng lúc có thể chủ động dùng mật độ cao hơn. Đây là quyết định có lý do, không phải mặc định.

### Checklist
- [ ] Các nhóm nội dung có đủ “không khí” không?
- [ ] Khoảng giữa nhóm lớn hơn khoảng trong nhóm không?
- [ ] Tôi có đang lấp chỗ trống chỉ vì nó trống không?
- [ ] Mật độ hiện tại có phục vụ nhiệm vụ không?

### Tóm tắt
**Khoảng trắng không phải phần còn dư; nó là công cụ làm rõ cấu trúc.**

---

## Bài 15 — Xây một hệ spacing và sizing

### Vấn đề
Nếu mỗi margin, padding, width đều được chỉnh bằng cảm giác từng pixel, UI sẽ chậm làm và thiếu nhất quán.

### Mục tiêu
Dùng một **scale hữu hạn** cho khoảng cách và kích thước.

### Lý thuyết
Một scale tuyến tính kiểu “cứ bội số 4px” chưa chắc đủ để giảm lựa chọn, vì ở kích thước lớn, chênh 4px gần như không đáng kể. Scale tốt thường có khoảng cách nhỏ ở đầu dưới và tăng dần rõ rệt ở đầu trên. Phần sách gợi ý lấy **16px làm base** và xây các bội/số phần của nó.

Ví dụ scale thực dụng trong phần đã đọc:

`4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 640, 768`

Không phải mọi dự án phải dùng đúng scale này; điểm quan trọng là bạn có **một hệ** thay vì các con số tùy hứng.

### Khi nào áp dụng
- Từ những màn hình đầu của sản phẩm.
- Khi có nhiều margin/padding gần nhau như 19, 21, 23, 26px.
- Khi designer và developer thường xuyên tranh luận về số pixel.

### Cách làm
1. Chọn base dễ làm việc, ví dụ 16px.
2. Tạo các mức nhỏ gần nhau hơn và mức lớn cách nhau rõ hơn.
3. Dùng scale cho padding, gap, margin, width/height khi phù hợp.
4. Khi một giá trị không đủ, thử mức kế tiếp thay vì chỉnh +1px.
5. Chỉ thêm token khi có nhu cầu lặp lại thật.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| 16 → 24 → 32 khi tăng spacing | 21 → 22 → 23 → 24 để “tìm đúng số” |
| Scale có bước nhảy rõ | Scale có quá nhiều giá trị sát nhau |
| Dùng token lặp lại | Nhập con số riêng cho từng màn hình |

### Ví dụ đúng/sai
**Sai:** Card A padding 22px, Card B 25px, Card C 27px dù cùng cấp.

**Đúng:** Cùng dùng `24px`; component lớn hơn có thể dùng `32px`.

### Lỗi thường gặp
- Tạo scale nhưng không dùng nhất quán.
- Quá ám ảnh rằng mọi kích thước phải thuộc scale, kể cả những giá trị phụ thuộc nội dung.
- Dùng linear scale dày đặc làm decision fatigue vẫn còn nguyên.

### Ngoại lệ
Một số kích thước như ảnh theo tỉ lệ, chiều cao do nội dung, hoặc giới hạn responsive có thể không nằm hoàn toàn trong scale.

### Checklist
- [ ] Tôi có spacing scale rõ ràng không?
- [ ] Hai giá trị kề nhau có khác biệt đủ để quyết định nhanh không?
- [ ] Các component tương tự có dùng cùng token không?
- [ ] Có nhiều số “lẻ” không giải thích được không?

### Tóm tắt
**Hệ spacing tốt biến “chọn số” thành “chọn mức”.**

---

## Bài 16 — Không cần lấp đầy toàn bộ màn hình

### Vấn đề
Màn hình desktop rộng khiến người mới có cảm giác phải kéo form, bảng và card rộng ra để “tận dụng không gian”. Kết quả thường là nội dung khó đọc hơn.

### Mục tiêu
Cho mỗi phần tử **đúng lượng không gian nó cần**, không nhiều hơn chỉ vì còn chỗ.

### Lý thuyết
Width tối ưu phụ thuộc nội dung. Một form chỉ cần khoảng 500-600px không trở nên tốt hơn khi kéo lên 1200px. Extra space ở hai bên có thể giúp tập trung hơn.

### Khi nào áp dụng
- Form đăng nhập, settings, checkout.
- Trang nội dung có chiều rộng lớn.
- Responsive layout.

### Cách làm
1. Xác định width hợp lý cho nội dung trước.
2. Dùng `max-width` cho khối không nên giãn vô hạn.
3. Căn giữa hoặc bố trí cột phụ thay vì kéo rộng khối chính.
4. Khi khó thiết kế nhỏ trên canvas lớn, thử bắt đầu từ mobile khoảng ~400px.
5. Mở rộng lên desktop sau, chỉ thay những gì thật sự cần.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Form 500-600px nếu đó là width phù hợp | Form full-width chỉ vì viewport rộng |
| Dùng column phụ để tận dụng không gian | Kéo nội dung chính dài dòng theo chiều ngang |
| Bắt đầu mobile khi cần constraint thật | Tưởng desktop phải “đầy” |

### Ví dụ đúng/sai
**Sai:** Trang đổi mật khẩu rộng 1440px, mỗi input kéo ngang gần hết màn hình.

**Đúng:** Form giữ width gọn; phần còn lại là whitespace hoặc khu vực mô tả riêng.

### Lỗi thường gặp
- Nhầm “responsive” với “mọi thứ đều fluid”.
- Đồng bộ width giữa các khối dù nhu cầu khác nhau.
- Cố kéo content cho thẳng hàng với navigation full-width.

### Ngoại lệ
Bảng dữ liệu nhiều cột, canvas, timeline hoặc dashboard có thể thật sự cần nhiều không gian ngang.

### Checklist
- [ ] Khối này có lý do để rộng như hiện tại không?
- [ ] Max-width có làm nội dung dễ đọc hơn không?
- [ ] Tôi có thể dùng cột phụ thay vì kéo rộng form không?
- [ ] Mobile-first có giúp xác định ưu tiên không?

### Tóm tắt
**Có không gian không đồng nghĩa phải sử dụng hết không gian.**

---

## Bài 17 — Grid hữu ích, nhưng đừng làm nô lệ cho grid

### Vấn đề
Grid 12 cột giúp sắp layout nhanh, nhưng nếu mọi phần tử đều bị ép thành phần trăm theo grid, những thứ nên có width cố định cũng co giãn vô lý.

### Mục tiêu
Dùng grid như công cụ hỗ trợ, không phải luật tối cao.

### Lý thuyết
Không phải phần tử nào cũng nên fluid. Ví dụ sidebar có nội dung cố định thường nên có width phù hợp với nội dung, trong khi main content mới là phần flex. Tương tự, card login có một width tối ưu; nó không nên nhỏ đi khi viewport vẫn còn đủ chỗ.

### Khi nào áp dụng
- Sidebar + content.
- Login/settings card.
- Dashboard card.
- Responsive component.

### Cách làm
1. Hỏi: phần tử này **có cần scale theo viewport không?**
2. Nếu không, dùng fixed width hoặc max-width hợp lý.
3. Cho khu vực cần co giãn nhận phần không gian còn lại.
4. Chỉ shrink component khi viewport thật sự không đủ.
5. Dùng grid bên trong vùng fluid khi nó thực sự giúp bố cục.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Sidebar width theo nội dung | Sidebar luôn 25% vì grid 3/12 |
| Card có max-width tối ưu | Card co nhỏ trên màn hình trung bình dù vẫn còn chỗ |
| Grid phục vụ component | Component phục vụ grid |

### Ví dụ đúng/sai
**Sai:** Sidebar 25%: trên màn hình lớn nó phình vô ích, trên màn hình nhỏ nó co đến mức label wrap.

**Đúng:** Sidebar giữ khoảng width phù hợp; content flex để dùng phần còn lại.

### Lỗi thường gặp
- Tin rằng “on-grid” luôn đồng nghĩa “đúng”.
- Dùng percentage cho avatar/icon dù chúng không nên scale.
- Tạo breakpoint chỉ để giữ tỷ lệ grid, không dựa trên nhu cầu component.

### Ngoại lệ
Gallery ảnh, card catalog hoặc layout marketing có thể hưởng lợi mạnh từ width theo tỷ lệ/grid.

### Checklist
- [ ] Phần tử nào cần fixed/max-width?
- [ ] Phần tử nào thực sự nên fluid?
- [ ] Component có bị co trước khi cần không?
- [ ] Grid đang giải quyết vấn đề hay đang tạo vấn đề?

### Tóm tắt
**Grid là một bộ gợi ý về trật tự, không phải một tôn giáo.**

---

## Bài 18 — Đừng bắt mọi thứ scale theo cùng một tỷ lệ

### Vấn đề
Một cách nghĩ hấp dẫn là: desktop giảm 25% thì mọi thứ — font, padding, heading — cũng giảm 25%. Nhưng cảm nhận thị giác không scale tuyến tính như vậy.

### Mục tiêu
Cho phép từng thuộc tính và từng phần tử **thay đổi độc lập theo ngữ cảnh**.

### Lý thuyết
Những thứ rất lớn trên desktop thường cần thu nhỏ mạnh hơn trên mobile, trong khi text vốn nhỏ chỉ nên giảm ít hoặc không giảm. Tương tự, một button lớn và button nhỏ không nhất thiết là cùng một component được zoom theo tỷ lệ; padding có thể thay đổi không đồng tỷ lệ với font size.

### Khi nào áp dụng
- Responsive typography.
- Button sizes.
- Card responsive.
- Component variants small/medium/large.

### Cách làm
1. Thiết kế từng breakpoint bằng mắt và nhu cầu thật.
2. Giảm heading mạnh hơn body text khi màn hình nhỏ.
3. Không encode mọi quan hệ bằng `em` chỉ vì tiện.
4. Với component size, điều chỉnh font và padding độc lập.
5. Kiểm tra cảm giác “small thật sự nhỏ” và “large thật sự lớn”.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Heading desktop 45px có thể xuống 24px mobile | Giữ cố định `heading = 2.5 × body` mọi breakpoint |
| Small button có padding giảm mạnh | Zoom toàn component theo cùng tỷ lệ |
| Fine-tune độc lập | Ép “tỉ lệ toán học đẹp” lên mọi ngữ cảnh |

### Ví dụ đúng/sai
**Sai:** Body 18→14px, headline vẫn 2.5em nên 45→35px, quá lớn trên mobile.

**Đúng:** Body 14px, headline khoảng 20-24px tùy bố cục.

### Lỗi thường gặp
- Tin rằng proportional = consistent.
- Dùng em lồng nhau làm size trôi khỏi hệ thống.
- Không kiểm tra breakpoint thật.

### Ngoại lệ
Một số icon/illustration có thể scale theo tỷ lệ đồng nhất vì đó là đồ họa, không phải typography/layout chức năng.

### Checklist
- [ ] Heading có thu nhanh hơn body trên màn nhỏ không?
- [ ] Padding có phù hợp từng variant không?
- [ ] Có quan hệ tỷ lệ nào đang tồn tại chỉ vì “đẹp về toán” không?

### Tóm tắt
**Responsive tốt không phải thu nhỏ toàn bộ screenshot; đó là tái cân bằng từng thành phần.**

---

## Bài 19 — Tránh spacing mơ hồ

### Vấn đề
Khi không có border/background phân nhóm, người dùng dựa vào khoảng cách để hiểu thứ nào thuộc cùng nhóm. Nếu khoảng trong nhóm bằng khoảng giữa nhóm, cấu trúc trở nên mơ hồ.

### Mục tiêu
Dùng spacing để truyền đạt **quan hệ**.

### Lý thuyết
Quy tắc cốt lõi: **khoảng cách bên trong một nhóm phải nhỏ hơn khoảng cách xung quanh nhóm**. Đây là cách tạo grouping mà không cần thêm border.

### Khi nào áp dụng
- Label + input.
- Heading + paragraph.
- Bullet list.
- Icon + số liệu/action.
- Các item xếp ngang.

### Cách làm
1. Xác định nhóm logic.
2. Chọn gap nhỏ cho phần tử thuộc cùng nhóm.
3. Chọn gap lớn hơn rõ rệt giữa các nhóm.
4. Kiểm tra cả trục dọc và ngang.
5. Nếu vẫn khó hiểu, mới cân nhắc border/background.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Label cách input 8-12px, nhóm kế tiếp 24px | Mọi khoảng đều 20px |
| Heading gần đoạn nó mô tả | Heading nằm giữa hai đoạn với khoảng cách bằng nhau |
| Action icon và số liệu có gap hợp lý | Các action dàn đều nhưng không biết số nào thuộc icon nào |

### Ví dụ đúng/sai
**Sai:** Label cách input 20px, input cách label kế tiếp cũng 20px → người dùng khó biết label thuộc field nào.

**Đúng:** Label → input 8px; input → nhóm tiếp theo 24px.

### Lỗi thường gặp
- Dùng spacing “đều” để mong trông sạch.
- Chỉ kiểm tra vertical spacing.
- Thêm border để cứu grouping mà spacing vẫn sai.

### Ngoại lệ
Khi có separator rất rõ như card background, table row hoặc divider, spacing có thể gần nhau hơn vì grouping đã được truyền đạt bằng cách khác.

### Checklist
- [ ] Khoảng trong nhóm có nhỏ hơn khoảng ngoài nhóm không?
- [ ] Nhìn nhanh có biết label thuộc input nào không?
- [ ] Heading có gần nội dung của nó hơn nội dung trước không?
- [ ] Horizontal group có rõ quan hệ không?

### Tóm tắt
**Khoảng cách không chỉ để “thoáng”; nó nói cho người dùng biết thứ gì thuộc về nhau.**

---
