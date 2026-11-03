# Phần VII - Tạo chiều sâu

## Bài 36 - Mô phỏng một nguồn sáng nhất quán

### Vấn đề
Nhiều người thêm highlight, border và shadow theo cảm tính để làm button “nổi” hoặc input “lõm”. Khi các hiệu ứng không tuân theo cùng một logic ánh sáng, UI dễ trông giả và lộn xộn.

### Mục tiêu
Tạo cảm giác raised/inset bằng cách mô phỏng cách ánh sáng ngoài đời tác động lên bề mặt.

### Lý thuyết
Sách dùng một quy tắc nền tảng: **ánh sáng đến từ phía trên**.

- Bề mặt **raised**: cạnh trên nhận nhiều ánh sáng hơn nên sáng; phía dưới che ánh sáng nên có shadow tối.
- Bề mặt **inset**: phần mép trên bị khuất sáng nên tối; cạnh dưới hướng lên phía nguồn sáng nên sáng.

Khi nhìn màn hình, người dùng thường nhìn hơi từ trên xuống, nên các tín hiệu top-light/bottom-shadow này phù hợp với cảm nhận tự nhiên.

### Khi nào áp dụng
- Button cần cảm giác raised.
- Input, checkbox, “well” cần cảm giác inset.
- UI cần chút chiều sâu nhưng không muốn hiệu ứng nặng.

### Cách làm
1. Quyết định component cần raised hay inset.
2. Với raised: thêm top highlight nhỏ và shadow tối hơi lệch xuống.
3. Với inset: thêm dark inset shadow phía trên và highlight nhẹ phía dưới.
4. Chọn màu highlight bằng tay thay vì luôn overlay white bán trong suốt, để tránh làm màu bị mất saturation.
5. Giữ blur radius nhỏ nếu đang mô phỏng cạnh/bề mặt thật.
6. Dừng khi hiệu ứng vừa đủ để não nhận ra chiều sâu.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Giữ một hướng ánh sáng nhất quán | Component này sáng từ trên, component khác sáng từ trái |
| Shadow nhỏ, có lý do | Thêm blur lớn chỉ vì trông “fancy” |
| Mô phỏng vật lý ở mức vừa đủ | Cố làm UI giống đồ vật thật hoàn toàn |

### Ví dụ đúng/sai
**Sai:** Button có highlight dưới, shadow trên và outer glow, khiến không rõ nó nổi hay lõm.

**Đúng:** Button có cạnh trên sáng nhẹ và shadow tối nhỏ bên dưới, đủ tạo cảm giác nhô khỏi nền.

### Lỗi thường gặp
- Dùng white overlay làm highlight khiến màu gốc bị nhạt.
- Blur quá nhiều cho shadow sát bề mặt.
- Raised và inset dùng cùng một treatment.
- Tinh chỉnh quá lâu để đạt “photorealistic”.

### Ngoại lệ
Flat design có thể không cần mô phỏng ánh sáng bằng highlight/shadow. Sách xem đây là một công cụ tạo depth, không phải yêu cầu bắt buộc cho mọi style.

### Checklist
- [ ] Tôi biết component đang raised hay inset không?
- [ ] Hướng sáng của toàn UI có nhất quán không?
- [ ] Shadow có đúng phía không?
- [ ] Hiệu ứng có vừa đủ thay vì mô phỏng quá mức không?

### Tóm tắt
**Muốn depth trông tự nhiên, hãy nghĩ như một nguồn sáng đang chiếu từ trên xuống.**

---

## Bài 37 - Dùng shadow để biểu diễn elevation

### Vấn đề
Nếu shadow chỉ được chọn theo kiểu “cái nào đẹp”, các component cùng loại có thể dùng shadow khác nhau và người dùng không nhận được tín hiệu nhất quán về lớp nào đang gần họ hơn.

### Mục tiêu
Biến shadow thành một **hệ thống elevation** thay vì một hiệu ứng trang trí ngẫu nhiên.

### Lý thuyết
Shadow cho phép đặt phần tử lên một trục z ảo:
- Shadow nhỏ, blur chặt -> phần tử chỉ hơi nổi khỏi nền.
- Shadow trung bình -> dropdown/popover nổi cao hơn content.
- Shadow lớn, blur rộng -> modal gần người dùng hơn và thu hút focus mạnh hơn.

Sách khuyên tạo một tập shadow cố định; khoảng **5 mức thường đã đủ**.

### Khi nào áp dụng
- Button, card.
- Dropdown/popover.
- Modal/dialog.
- Drag-and-drop.
- Pressed state.

### Cách làm
1. Chọn shadow nhỏ nhất cho elevation thấp.
2. Chọn shadow lớn nhất cho modal/elevation cao.
3. Điền 2-3 mức ở giữa.
4. Gắn từng component vào một elevation có ý nghĩa.
5. Với drag, tăng shadow khi item được nhấc lên.
6. Với pressed button, giảm shadow hoặc bỏ shadow để tạo cảm giác bị ấn xuống.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Thiết kế shadow theo vị trí z | Chọn shadow theo sở thích từng màn hình |
| Có scale cố định | 20 shadow gần giống nhau |
| Dùng shadow thay đổi theo interaction | Pressed state vẫn “bay” cao như bình thường |

### Ví dụ đúng/sai
**Sai:** Modal và button đều dùng cùng một shadow nhỏ nên modal không tách khỏi nền.

**Đúng:** Button dùng elevation thấp, dropdown trung bình, modal cao hơn rõ ràng.

### Lỗi thường gặp
- Nghĩ shadow lớn hơn chỉ là “đẹp hơn”.
- Tăng shadow nhưng không tăng ý nghĩa elevation.
- Mỗi designer dùng một công thức shadow khác nhau.

### Ngoại lệ
Một style flat có thể biểu diễn elevation bằng color, overlap hoặc solid shadow thay vì shadow blur. Điều quan trọng là hierarchy không gian phải nhất quán.

### Checklist
- [ ] Shadow có tương ứng với độ cao của component không?
- [ ] Có một scale shadow hữu hạn không?
- [ ] Modal có cảm giác gần hơn dropdown không?
- [ ] Drag/pressed state có phản ánh chuyển động z không?

### Tóm tắt
**Đừng hỏi “shadow nào đẹp”; hãy hỏi “component này đang ở đâu trên trục z?”.**

---

## Bài 38 - Một shadow đẹp có thể gồm hai shadow

### Vấn đề
Một box-shadow duy nhất đôi khi khó vừa mềm tự nhiên ở xa vừa sắc nét gần mép element. Khi tăng blur, cạnh bị mờ; khi giảm blur, shadow lại quá cứng.

### Mục tiêu
Tách hai nhiệm vụ của shadow thành hai lớp để kiểm soát tốt hơn.

### Lý thuyết
Sách mô tả hai thành phần:

1. **Shadow lớn, mềm:** offset dọc nhiều hơn, blur lớn hơn; mô phỏng bóng do nguồn sáng trực tiếp.
2. **Shadow nhỏ, tối:** offset ít hơn, blur nhỏ; mô phỏng vùng ngay dưới object nơi ambient light khó lọt vào.

Khi object càng cao khỏi surface, shadow tối sát mép do thiếu ambient light sẽ yếu dần. Vì vậy ở elevation cao, shadow thứ hai nên rất nhẹ hoặc biến mất.

### Khi nào áp dụng
- Card cần shadow tinh tế.
- Popover/dropdown.
- Hệ thống elevation nhiều cấp.

### Cách làm
1. Tạo soft shadow lớn để định footprint tổng.
2. Thêm tight shadow nhỏ hơn để định nghĩa cạnh.
3. Ở elevation thấp, giữ tight shadow rõ hơn.
4. Khi elevation tăng, giảm dần tight shadow.
5. Kiểm tra cả shadow trên nền sáng và các surface khác nhau.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Mỗi shadow có một nhiệm vụ | Chồng shadow ngẫu nhiên đến khi “thấy đẹp” |
| Tight shadow giảm khi elevation tăng | Shadow sát mép luôn đậm ở mọi độ cao |
| Giữ soft shadow tinh tế | Dùng hai shadow đều quá tối |

### Ví dụ đúng/sai
**Sai:** Card cao nhất vẫn có viền shadow tối sắc ngay sát mép, khiến cảm giác như nó đang dính gần surface.

**Đúng:** Card thấp có tight contact shadow; modal cao có soft shadow rộng, contact shadow rất nhẹ.

### Lỗi thường gặp
- Hai shadow cùng blur/offset nên không tạo thêm kiểm soát.
- Shadow thứ hai quá đậm trông như border.
- Không thay đổi công thức theo elevation.

### Ngoại lệ
Không phải component nào cũng cần hai shadow. Với UI đơn giản, một shadow đủ tốt sẽ tốt hơn một công thức phức tạp không cần thiết.

### Checklist
- [ ] Soft shadow đang làm nhiệm vụ “bóng xa” không?
- [ ] Tight shadow đang định nghĩa cạnh gần không?
- [ ] Tight shadow có giảm ở elevation cao không?
- [ ] Tổng shadow vẫn subtle không?

### Tóm tắt
**Hai shadow hữu ích khi một lớp chịu trách nhiệm cho ánh sáng trực tiếp và một lớp cho vùng tối sát bề mặt.**

---

## Bài 39 - Flat design vẫn có thể có chiều sâu

### Vấn đề
Nhiều người hiểu “flat” là loại bỏ hoàn toàn mọi tín hiệu depth. Kết quả có thể làm các surface khó phân biệt và hierarchy không gian bị phẳng theo nghĩa tiêu cực.

### Mục tiêu
Tạo depth mà vẫn giữ thẩm mỹ flat.

### Lý thuyết
Sách đưa ra hai cách:

1. **Depth bằng màu:** với các shade cùng family, phần sáng hơn thường cảm giác gần hơn; phần tối hơn cảm giác xa/lõm hơn.
2. **Solid shadow:** shadow ngắn, lệch dọc và không blur, giúp card/button tách khỏi nền nhưng vẫn giữ vẻ graphic/flat.

### Khi nào áp dụng
- Design style không dùng gradient/blur shadow.
- Card cần tách khỏi page background.
- Input/well cần cảm giác inset bằng surface color.

### Cách làm
1. Chọn background base.
2. Dùng surface sáng hơn background để tạo cảm giác raised.
3. Dùng surface tối hơn background để tạo cảm giác inset.
4. Nếu cần thêm tách lớp, dùng shadow có offset nhưng blur = 0.
5. Giữ logic này nhất quán xuyên suốt component.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng chênh lệch shade có chủ đích | Mọi surface cùng màu và không có tín hiệu depth |
| Solid shadow khi hợp style | Thêm blur shadow chỉ vì “UI cần shadow” |
| Giữ depth tối giản | Flat = hoàn toàn không có hierarchy không gian |

### Ví dụ đúng/sai
**Sai:** Form, page background và disabled panel dùng cùng một grey, chỉ phân biệt bằng text.

**Đúng:** Card đăng nhập sáng hơn nền; vùng secondary panel tối hơn nhẹ để cảm giác lùi xuống.

### Lỗi thường gặp
- Chênh màu quá nhỏ nên không thấy.
- Chênh màu quá lớn phá subtle hierarchy.
- Dùng màu sáng/tối không nhất quán với elevation.

### Ngoại lệ
Một thiết kế siêu tối giản có thể chủ ý dùng cùng surface color và dựa vào spacing/typography. Nhưng khi cần depth, không nhất thiết phải quay lại skeuomorphism.

### Checklist
- [ ] Surface raised có sáng hơn nền không?
- [ ] Inset area có tối hơn khi phù hợp không?
- [ ] Có cần solid shadow không blur không?
- [ ] Style vẫn giữ được tinh thần flat không?

### Tóm tắt
**Flat không có nghĩa là không có depth; chỉ là bạn truyền depth bằng những tín hiệu đơn giản hơn.**

---

## Bài 40 - Overlap để tạo layer

### Vấn đề
Nếu mọi phần tử đều nằm gọn trong container riêng và không bao giờ vượt ranh giới, layout dễ trông như một chuỗi hộp phẳng, thiếu cảm giác layer.

### Mục tiêu
Dùng overlap có chủ đích để tạo quan hệ trước/sau và giúp các khu vực nối với nhau.

### Lý thuyết
Một element vượt qua ranh giới của hai background khiến não hiểu rằng nó nằm **trên** cả hai surface. Overlap có thể áp dụng ở:
- Card bắc qua hai section.
- Component cao hơn parent và nhô ra hai phía.
- Control nổi trên carousel.
- Avatar/image chồng nhau.

Với ảnh chồng nhau, sách khuyên dùng một “invisible border” cùng màu background để tạo khe nhỏ, tránh ảnh va màu trực tiếp.

### Khi nào áp dụng
- Hero chuyển sang content section.
- Pricing card/banner.
- Carousel control.
- Avatar stack.

### Cách làm
1. Xác định hai surface cần kết nối.
2. Cho một element quan trọng vượt qua đường chuyển tiếp.
3. Giữ overlap đủ rõ để tạo layer nhưng không làm layout khó hiểu.
4. Với ảnh/avatars, thêm border cùng màu background để tạo khoảng đệm thị giác.
5. Kiểm tra responsive để overlap không che nội dung.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Overlap ở điểm có ý nghĩa | Cho nhiều element đè nhau chỉ để trang trí |
| Tạo gap giữa ảnh chồng | Để ảnh có màu gần nhau va trực tiếp |
| Kiểm tra mobile | Dùng offset cố định gây vỡ layout |

### Ví dụ đúng/sai
**Sai:** Ba avatar chồng lên nhau không có separator, màu nền ảnh hòa vào nhau thành một khối khó đọc.

**Đúng:** Mỗi avatar có border cùng màu nền, vẫn thấy layer nhưng ranh giới rõ.

### Lỗi thường gặp
- Overlap che text/CTA.
- Dùng quá nhiều layer cùng lúc.
- Không xử lý responsive.
- Border ảnh chồng quá đậm, biến thành viền trang trí.

### Ngoại lệ
UI dữ liệu dày hoặc enterprise cần tối đa sự ổn định có thể ít dùng overlap. Đây là kỹ thuật tạo layer, không phải bắt buộc.

### Checklist
- [ ] Overlap có làm rõ layer không?
- [ ] Element có che nội dung quan trọng không?
- [ ] Ảnh chồng có separator đủ tinh tế không?
- [ ] Mobile layout có còn ổn không?

### Tóm tắt
**Một element đi qua ranh giới surface là cách rất mạnh để biến layout phẳng thành nhiều lớp.**

---
