# Phần IV — Typography: làm chữ dễ đọc và nhất quán

## Bài 20 — Thiết lập type scale

### Vấn đề
Một UI không có hệ thống thường dùng gần như mọi kích thước chữ từ 10px đến 24px. Hậu quả là màn hình trông không nhất quán, đồng thời bạn mất thời gian cân nhắc từng pixel.

### Mục tiêu
Tạo một **type scale hữu hạn** đủ linh hoạt cho UI nhưng đủ chặt để ra quyết định nhanh.

### Lý thuyết
Scale tuyến tính hoặc modular scale thuần toán học nghe hấp dẫn nhưng có thể sinh ra số lẻ và những bước nhảy không phù hợp với UI. Phần sách đã đọc đề xuất cách thực dụng hơn: **chọn scale thủ công**.

Một scale ví dụ trong sách:

`12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72px`

Đây là ví dụ, không phải luật bắt buộc. Điều quan trọng là số lượng size được giới hạn và mỗi size có vai trò rõ.

Ngoài ra, phần đã đọc cảnh báo việc xây type scale bằng `em` lồng nhau vì giá trị thực có thể trôi khỏi scale; `px` hoặc `rem` giúp kiểm soát tốt hơn.

### Khi nào áp dụng
- Ngay khi dự án có hơn vài màn hình.
- Khi designer/developer đang dùng nhiều font size gần giống nhau.
- Khi heading và body không có quy ước.

### Cách làm
1. Chọn body mặc định, thường quanh 16px nếu phù hợp sản phẩm.
2. Chọn 1-2 size nhỏ hơn cho metadata/caption.
3. Chọn 2-4 size lớn hơn cho section title, page title, hero.
4. Đảm bảo bước nhảy nhỏ ở vùng text nhỏ và rõ hơn ở vùng headline lớn.
5. Gán tên token, ví dụ `text-sm`, `text-base`, `text-lg`, `title-md`, `display-lg`.
6. Không tạo size mới chỉ vì một màn hình “thiếu 1px”.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng scale hữu hạn | Có 13px, 14px, 15px, 16px, 17px tùy chỗ |
| Hand-craft scale theo nhu cầu UI | Ép mọi size theo golden ratio |
| Dùng px/rem để giữ scale ổn định | Dùng em lồng nhau làm computed size lệch |

### Ví dụ đúng/sai
**Sai:** Card A dùng 15px, Card B 17px, modal 19px, table 13px, tất cả không có lý do.

**Đúng:** Body 16px, metadata 14px, section title 20px, page title 30px, display 48px; chỉ dùng các mức đã định nghĩa.

### Lỗi thường gặp
- Tạo scale quá ít size nên designer phải phá hệ thống liên tục.
- Tạo scale quá nhiều size nên mất tác dụng.
- Dùng size như công cụ hierarchy duy nhất.

### Ngoại lệ
Một chiến dịch marketing hoặc màn hình đặc biệt có thể cần display size ngoài scale UI chính. Nên coi đó là ngoại lệ có chủ ý.

### Checklist
- [ ] Có một danh sách font size chính thức không?
- [ ] Mỗi size có vai trò tương đối rõ không?
- [ ] Có size nào chỉ xuất hiện một lần và không giải thích được không?
- [ ] Nested text có trôi khỏi scale không?

### Tóm tắt
**Type scale giúp chữ trông có hệ thống và giúp bạn ngừng tranh luận về từng pixel.**

---

## Bài 21 — Chọn font “tốt” theo cách an toàn

### Vấn đề
Người mới khó đánh giá chất lượng typeface vì có hàng nghìn lựa chọn và nhiều chi tiết typography cần thời gian để phát triển con mắt.

### Mục tiêu
Có một quy trình chọn font đủ an toàn mà không cần trở thành chuyên gia type design.

### Lý thuyết
Phần sách đã đọc đưa ra các cách giảm rủi ro:
- UI thường an toàn với **sans-serif trung tính**.
- Một font family có nhiều weight thường cho thấy nó được đầu tư nghiêm túc và cũng linh hoạt hơn.
- Font cho text nhỏ cần chú trọng legibility; typeface quá condensed hoặc x-height thấp có thể khó đọc.
- Mức độ phổ biến là một tín hiệu thực dụng khi bạn chưa có trực giác typography.
- Quan sát font mà các đội thiết kế tốt đang dùng giúp xây dựng “con mắt” theo thời gian.

### Khi nào áp dụng
- Khi dự án chưa có brand font.
- Khi bạn đang chọn font đầu tiên cho product UI.
- Khi có quá nhiều lựa chọn và không biết bắt đầu từ đâu.

### Cách làm
1. Bắt đầu bằng sans-serif trung tính, dễ đọc.
2. Ưu tiên family có nhiều weight thực sự hữu dụng.
3. Test ở kích thước UI nhỏ, không chỉ nhìn headline lớn.
4. Tránh font quá condensed cho body/interface text.
5. Xem các font phổ biến hoặc font từ sản phẩm có typography tốt để thu hẹp lựa chọn.
6. Kiểm tra số, dấu câu, chữ hoa/thường và tiếng Việt nếu sản phẩm dùng tiếng Việt.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Test font ở 14-16px | Chọn font vì logo sample 72px trông đẹp |
| Dùng family có nhiều weight | Chọn font chỉ có Regular/Bold nếu sản phẩm cần nhiều hierarchy |
| Ưu tiên legibility | Dùng condensed display face cho bảng dữ liệu |

### Ví dụ đúng/sai
**Sai:** Chọn một font cá tính, chữ thấp và hẹp cho toàn bộ dashboard vì banner trông “premium”.

**Đúng:** Dùng sans dễ đọc cho UI; nếu cần personality, dùng font đặc trưng ở heading/marketing có kiểm soát.

### Lỗi thường gặp
- Chọn font bằng screenshot marketing thay vì thử dữ liệu thật.
- Dùng quá nhiều font family.
- Không kiểm tra tiếng Việt có đủ dấu và hiển thị đẹp.
- Chọn weight giả do trình duyệt tự tổng hợp.

### Ngoại lệ
Brand mạnh có thể yêu cầu typeface đặc thù. Khi đó vẫn cần một strategy cho text nhỏ nếu brand font không tối ưu cho UI.

### Checklist
- [ ] Font có dễ đọc ở size nhỏ không?
- [ ] Có đủ weight cần dùng không?
- [ ] Chữ số và ký tự đặc biệt ổn không?
- [ ] Hỗ trợ tiếng Việt tốt không?
- [ ] Tôi chọn font vì nhu cầu hay chỉ vì “trông lạ”?

### Tóm tắt
**Khi chưa có trực giác typography, chọn font an toàn và dễ đọc tốt hơn chọn font gây ấn tượng nhưng khó dùng.**

---

## Bài 22 — Giữ độ dài dòng trong vùng dễ đọc

### Vấn đề
Text paragraph thường bị kéo theo width của layout. Trên desktop rộng, một dòng có thể quá dài, khiến mắt khó quay về đúng dòng tiếp theo.

### Mục tiêu
Tối ưu trải nghiệm đọc thay vì chỉ “fit content vào layout”.

### Lý thuyết
Phần đã đọc đưa ra vùng an toàn khoảng **45-75 ký tự mỗi dòng** cho paragraph. Trên web, một gợi ý thực dụng là width khoảng **20-35em**, tùy font và ngữ cảnh.

Một content area có thể rộng để chứa ảnh hoặc component, nhưng paragraph bên trong không nhất thiết phải rộng bằng toàn bộ content area.

### Khi nào áp dụng
- Article, help center, onboarding copy.
- Mô tả dài trong settings.
- Landing page có đoạn text dài.

### Cách làm
1. Đưa nội dung thật vào layout.
2. Ước lượng 45-75 ký tự/dòng.
3. Dùng `max-width` riêng cho paragraph.
4. Không kéo paragraph rộng theo ảnh/banner lớn.
5. Test với text dài, không chỉ lorem ngắn.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Paragraph có max-width riêng | Text chạy 120-150 ký tự/dòng |
| Content container rộng nhưng text column hẹp hơn | Bắt mọi phần tử cùng width |
| Ưu tiên khả năng đọc | Căn layout cho “thẳng mép” bằng mọi giá |

### Ví dụ đúng/sai
**Sai:** Trang tài liệu 1200px, paragraph cũng 1200px.

**Đúng:** Trang vẫn 1200px để chứa hình/diagram; paragraph giới hạn khoảng 640-760px tùy font.

### Lỗi thường gặp
- Dùng width của image làm width của text.
- Chỉ kiểm tra màn hình laptop nhỏ, không kiểm tra desktop lớn.
- Giảm font size để “fit” thay vì giới hạn line length.

### Ngoại lệ
Bảng, code block, data visualization và nội dung có cấu trúc khác paragraph không tuân theo quy tắc ký tự/dòng này theo cùng cách.

### Checklist
- [ ] Paragraph có quá dài trên desktop không?
- [ ] Có thể đặt max-width riêng cho text không?
- [ ] Độ dài dòng nằm gần vùng 45-75 ký tự không?
- [ ] Font size vẫn thoải mái sau khi giới hạn width không?

### Tóm tắt
**Đừng để chiều rộng màn hình quyết định chiều rộng đoạn văn.**

---

## Bài 23 — Căn theo baseline, không phải luôn căn giữa

### Vấn đề
Khi hai đoạn text khác font size nằm cùng một hàng, căn giữa theo hộp bounding box có thể khiến chữ trông lệch dù về toán học là “center”.

### Mục tiêu
Tạo alignment tự nhiên theo cách mắt người đọc cảm nhận chữ.

### Lý thuyết
Chữ có **baseline** — đường tưởng tượng mà các ký tự “đứng” trên đó. Khi text size khác nhau nằm gần nhau, căn baseline thường tạo cảm giác gọn hơn vertical-center.

### Khi nào áp dụng
- Title lớn + action text nhỏ cùng hàng.
- Giá lớn + đơn vị nhỏ.
- Số liệu + label.
- Navigation có chữ nhiều size.

### Cách làm
1. Xác định các text cùng một hàng có size khác nhau.
2. Thử căn baseline trước.
3. So với center alignment ở khoảng cách thực tế.
4. Chọn phương án tạo một đường đọc tự nhiên hơn.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Căn baseline cho text khác size | Mặc định `align-items: center` cho mọi hàng chữ |
| Nhìn optical alignment | Chỉ tin bounding box |
| Test khi text đứng gần nhau | Chỉ nhìn component phóng to |

### Ví dụ đúng/sai
**Sai:** Giá `1.250.000` 32px và `/tháng` 14px được căn center, làm đơn vị “lơ lửng”.

**Đúng:** Cả hai cùng baseline, đơn vị nằm tự nhiên cạnh giá.

### Lỗi thường gặp
- Dùng center vì flexbox mặc định dễ.
- Không để ý baseline khi text size chênh lớn.
- Cố căn bằng margin thủ công theo từng content.

### Ngoại lệ
Nếu text đi cùng icon hoặc control không phải chữ, center alignment có thể phù hợp hơn. Hãy xét loại phần tử thực tế.

### Checklist
- [ ] Có nhiều font size trên cùng một hàng không?
- [ ] Tôi đã thử baseline alignment chưa?
- [ ] Có margin “chữa lệch” bất thường không?

### Tóm tắt
**Khi căn chữ với chữ, baseline thường là mốc thị giác tốt hơn tâm của hộp.**

---

## Bài 24 — Line-height phải thay đổi theo độ dài dòng và font size

### Vấn đề
Một quy tắc kiểu “line-height luôn 1.5” nghe đơn giản nhưng không phù hợp mọi loại text. Dòng dài cần nhiều khoảng cách hơn; heading lớn thường cần ít hơn.

### Mục tiêu
Chọn line-height dựa trên **line length** và **font size**, không dùng một số cố định cho toàn bộ sản phẩm.

### Lý thuyết
Hai quan hệ quan trọng trong phần đã đọc:

1. **Dòng càng dài → line-height thường cần lớn hơn.** Mắt phải di chuyển xa từ cuối dòng về đầu dòng tiếp theo nên cần khoảng dọc rõ hơn để không lạc dòng.
2. **Font càng lớn → line-height tương đối có thể nhỏ hơn.** Text nhỏ cần nhiều trợ giúp để tìm dòng tiếp theo; headline lớn có thể dùng line-height gần 1.

Sách minh họa rằng nội dung hẹp có thể dùng khoảng 1.5, còn nội dung rất rộng có thể cần cao hơn; với headline lớn, line-height 1 có thể ổn.

### Khi nào áp dụng
- Paragraph dài.
- Responsive typography.
- Card description nhỏ.
- Heading nhiều dòng.

### Cách làm
1. Chọn font size trước.
2. Chọn width/line length thực tế.
3. Với body nhỏ/dòng dài, tăng line-height.
4. Với heading lớn, giảm line-height để tránh khoảng trống dư.
5. Test bằng đoạn nhiều dòng thực, không chỉ một dòng.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Body 14-16px có line-height rộng rãi | Dùng 1.1 cho paragraph dài |
| Heading lớn dùng line-height chặt hơn | Dùng 1.5 cho 48px heading tạo khoảng rời rạc |
| Điều chỉnh theo width | Một line-height cho mọi breakpoint |

### Ví dụ đúng/sai
**Sai:** Body 14px rộng 800px nhưng line-height 1.2; người đọc dễ lạc dòng.

**Đúng:** Hoặc giới hạn width, hoặc tăng line-height. Heading 48px có thể dùng line-height gần 1-1.1 nếu hình dáng font cho phép.

### Lỗi thường gặp
- Copy line-height từ design system khác mà không xét font.
- Tăng line-height quá nhiều thay vì sửa line length.
- Dùng line-height nhỏ cho text nhỏ chỉ vì muốn card thấp hơn.

### Ngoại lệ
Single-line controls như button/input label không cần line-height theo logic paragraph; chúng thường dựa nhiều vào height/padding của control.

### Checklist
- [ ] Paragraph dài có đủ khoảng dọc không?
- [ ] Heading có bị “lỏng” quá không?
- [ ] Responsive width thay đổi nhưng line-height có cần đổi không?
- [ ] Tôi đã test đoạn 3-5 dòng thật chưa?

### Tóm tắt
**Line-height không phải hằng số; nó là câu trả lời cho kích thước chữ và quãng đường mắt phải đọc.**

---

## Bài 25 — Không phải link nào cũng cần màu nổi

> Lưu ý phạm vi: trong nửa đầu PDF, trang 109 mới bắt đầu mục này. Vì vậy bài này chỉ tóm lược những gì xuất hiện đến hết trang 109.

### Vấn đề
Trong một đoạn văn bình thường, link cần khác biệt để người đọc nhận ra nó có thể click. Nhưng trong một giao diện mà rất nhiều thứ đều là link/action, nếu mọi link đều dùng màu nổi theo kiểu bài viết, màn hình sẽ trở nên quá ồn.

### Mục tiêu
Dùng visual treatment cho link theo **ngữ cảnh**, không áp một style “link xanh nổi bật” cho mọi nơi.

### Lý thuyết
Mức độ cần làm link nổi bật phụ thuộc vào môi trường xung quanh:
- Trong paragraph có nhiều text không tương tác, link cần dễ phân biệt.
- Trong application UI nơi nhiều phần tử đã có tính tương tác, quá nhiều màu link có thể cạnh tranh attention.

### Khi nào áp dụng
- Article/help text có inline link.
- Card/list nơi title, thumbnail, metadata đều có thể click.
- Dashboard có nhiều text action.

### Cách làm
1. Xác định người dùng có cần nhận ra link ngay trong ngữ cảnh không.
2. Với inline link trong đoạn văn, tạo khác biệt rõ ràng.
3. Với UI có nhiều vùng tương tác, tránh biến mọi link thành điểm nhấn màu mạnh.
4. Luôn giữ affordance và khả năng nhận biết đủ cho use case.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Inline link trong paragraph nhìn ra được | Link hòa hoàn toàn vào body text |
| Link-heavy UI dùng treatment tiết chế | Mọi title/action đều màu xanh chói |
| Xét hierarchy tổng thể | Style link tách rời khỏi ngữ cảnh |

### Ví dụ đúng/sai
**Sai:** Một news/card grid có title, tác giả, category, timestamp đều màu xanh chỉ vì tất cả đều click được.

**Đúng:** Chỉ các phần cần emphasis có treatment mạnh; các vùng khác vẫn có khả năng tương tác nhưng không đồng loạt “hét lên”.

### Lỗi thường gặp
- Đồng nhất “clickable” với “phải màu xanh”.
- Làm link quá giống text bình thường trong paragraph.
- Không xét việc màu link có cạnh tranh với primary action hay không.

### Ngoại lệ
Các yêu cầu accessibility và quy ước sản phẩm có thể yêu cầu dấu hiệu tương tác rõ hơn. Phần PDF sau trang 109 có thể bổ sung chi tiết, nhưng tài liệu này chủ động không sử dụng vì nằm ngoài nửa đầu được yêu cầu.

### Checklist
- [ ] Inline link trong đoạn văn có nhận biết được không?
- [ ] UI có quá nhiều chữ màu link không?
- [ ] Treatment của link có phá hierarchy không?
- [ ] Người dùng vẫn hiểu phần tử nào có thể tương tác không?

### Tóm tắt
**Link cần đủ rõ để dùng, nhưng không phải link nào cũng phải trở thành điểm nhấn thị giác.**

---
