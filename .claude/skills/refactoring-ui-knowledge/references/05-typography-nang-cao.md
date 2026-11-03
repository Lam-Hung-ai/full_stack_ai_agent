# Phần V - Hoàn thiện typography

## Bài 26 - Không phải link nào cũng cần nổi bật bằng màu

### Vấn đề
Nếu mọi phần tử có thể click đều được tô màu link nổi bật, một ứng dụng có nhiều action sẽ trở nên ồn. Người dùng nhìn thấy quá nhiều điểm tranh giành sự chú ý, trong khi nhiều link chỉ là hành động phụ.

### Mục tiêu
Làm link **đủ nhận biết theo ngữ cảnh**, nhưng không để các link phụ cạnh tranh với nội dung và hành động quan trọng hơn.

### Lý thuyết
Phần tiếp nối ở trang 110 nhấn mạnh rằng phần lớn link có thể được nhấn nhẹ bằng **font-weight đậm hơn** hoặc **màu chữ tối hơn**, thay vì luôn dùng một màu nổi riêng. Với link rất phụ, có thể chỉ hiện underline hoặc đổi màu khi hover.

Ý chính là: mức độ nhấn của link phải phù hợp với vị trí của nó trong hierarchy.

### Khi nào áp dụng
- Card/list có nhiều vùng click.
- Dashboard với nhiều action phụ.
- Metadata, link “xem thêm”, link phụ trợ.
- Khu vực mà primary CTA đã có màu nhấn mạnh.

### Cách làm
1. Xác định link có nằm trong luồng chính hay chỉ là đường phụ.
2. Với link quan trọng, cho treatment rõ nhưng không nhất thiết phải màu xanh mặc định.
3. Với link thứ cấp, thử tăng font-weight hoặc dùng màu đậm hơn body text.
4. Với link rất phụ, cân nhắc chỉ hiện underline/đổi màu khi hover.
5. Kiểm tra lại toàn màn hình xem link có đang cạnh tranh với CTA chính không.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Nhấn link theo mức độ quan trọng | Cho mọi link cùng một màu nổi |
| Dùng weight hoặc contrast khi đủ | Đồng nhất “clickable” với “phải xanh” |
| Để link phụ lùi xuống hierarchy | Làm link phụ nổi hơn CTA chính |

### Ví dụ đúng/sai
**Sai:** Trong một card sản phẩm, tên sản phẩm, tác giả, category, ngày tháng và “xem chi tiết” đều có màu xanh đậm.

**Đúng:** Tên sản phẩm dùng chữ đậm; metadata dùng màu trung tính; link “xem chi tiết” chỉ đổi màu hoặc underline khi hover.

### Lỗi thường gặp
- Dùng màu link như một quy tắc bất biến.
- Không xét hierarchy của toàn màn hình.
- Làm hover quá tinh tế đến mức người dùng không nhận ra phần tử có thể tương tác.

### Ngoại lệ
Inline link nằm trong đoạn văn dài thường cần dấu hiệu nhận biết rõ hơn, vì xung quanh nó là text không tương tác. Phần này không phủ nhận nhu cầu đó; nó chỉ nói rằng trong application UI, link không nhất thiết phải được nhấn theo cùng một cách.

### Checklist
- [ ] Link quan trọng có nhận ra được không?
- [ ] Link phụ có đang tranh attention với CTA chính không?
- [ ] Có link nào chỉ cần weight/contrast thay vì màu riêng không?
- [ ] Hover/focus vẫn cho người dùng dấu hiệu tương tác rõ ràng không?

### Tóm tắt
**Link cần được nhìn thấy đúng mức, không phải được tô màu nổi bằng mọi giá.**

---

## Bài 27 - Căn chữ để ưu tiên khả năng đọc

### Vấn đề
Người mới thường căn giữa vì thấy “cân đối”, hoặc justify vì trông “chuyên nghiệp”. Nhưng căn chữ đẹp trong một block ngắn có thể trở nên khó đọc khi nội dung dài.

### Mục tiêu
Chọn alignment theo cách mắt người đọc quét nội dung, không theo cảm giác đối xứng đơn thuần.

### Lý thuyết
Với các ngôn ngữ đọc từ trái sang phải như tiếng Anh, phần lớn text nên **căn trái**. Center alignment phù hợp với headline hoặc khối text ngắn, độc lập. Khi đoạn dài hơn khoảng 2-3 dòng, căn trái thường dễ đọc hơn vì mỗi dòng bắt đầu từ cùng một trục.

Sách cũng đưa ra hai trường hợp đặc biệt:
- **Số trong bảng:** căn phải để hàng đơn vị/thập phân dễ so sánh.
- **Justified text:** nếu dùng, nên bật hyphenation để giảm các khoảng trắng bất thường giữa từ.

### Khi nào áp dụng
- Paragraph, description, card copy.
- Hero text hoặc headline ngắn.
- Bảng số liệu.
- Thiết kế muốn mô phỏng phong cách báo/tạp chí in.

### Cách làm
1. Mặc định text dài bằng căn trái.
2. Chỉ center-align các block ngắn như heading, subheading, CTA intro.
3. Nếu block căn giữa vượt quá 2-3 dòng, viết ngắn lại hoặc chuyển sang căn trái.
4. Trong bảng số, căn phải các cột số.
5. Nếu justify, bật hyphenation và kiểm tra khoảng trắng giữa từ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Căn trái paragraph dài | Căn giữa đoạn 5-8 dòng |
| Căn phải cột số | Căn trái số khiến khó so sánh |
| Hyphenate khi justify | Justify rồi chấp nhận khoảng trắng loang lổ |

### Ví dụ đúng/sai
**Sai:** Ba cột tính năng đều căn giữa, trong đó một cột có mô tả dài 5 dòng và nhìn lệch nhịp so với hai cột còn lại.

**Đúng:** Rút gọn copy để các block còn 2-3 dòng, hoặc chuyển phần description dài sang căn trái.

### Lỗi thường gặp
- Căn giữa tất cả vì “landing page hay làm vậy”.
- Căn giữa text dài khiến mắt phải tìm điểm bắt đầu mới ở từng dòng.
- Bảng tài chính căn giữa số.
- Justify mà không để ý khoảng cách từ.

### Ngoại lệ
Justified text có thể hợp với giao diện cố tình mô phỏng ấn phẩm in như magazine/newspaper. Tuy nhiên căn trái vẫn là lựa chọn hợp lệ và đơn giản hơn.

### Checklist
- [ ] Đoạn dài có cùng một trục bắt đầu không?
- [ ] Centered text có dưới khoảng 2-3 dòng không?
- [ ] Cột số có căn phải không?
- [ ] Justified text có hyphenation và khoảng từ ổn không?

### Tóm tắt
**Alignment nên làm cho việc đọc dễ hơn trước khi làm cho bố cục trông đối xứng hơn.**

---

## Bài 28 - Dùng letter-spacing có chủ đích

### Vấn đề
Designer mới thường chỉ chỉnh font-size, weight và line-height mà quên letter-spacing; hoặc ngược lại, chỉnh tracking ở mọi nơi dù typeface đã được thiết kế tốt sẵn.

### Mục tiêu
Biết khi nào nên **để nguyên** letter-spacing và khi nào một thay đổi nhỏ thực sự cải thiện typography.

### Lý thuyết
Quy tắc mặc định của sách là: **tin vào type designer và để letter-spacing yên**. Hai trường hợp phổ biến đáng điều chỉnh:

1. **Headline dùng font có spacing rộng:** có thể giảm letter-spacing để headline cô đọng hơn.
2. **ALL CAPS:** nên tăng letter-spacing vì các chữ hoa có chiều cao giống nhau, ít đặc điểm hình dáng để phân biệt hơn lowercase.

Sách cũng cảnh báo không nên lấy headline font rồi tăng tracking để ép nó hoạt động ở size nhỏ; loại font đó thường không được thiết kế cho body/UI text.

### Khi nào áp dụng
- Heading lớn dùng sans trung tính có tracking rộng.
- Eyebrow label, menu label hoặc badge viết HOA.
- Typography cần compact hơn mà không đổi font.

### Cách làm
1. Trước tiên dùng tracking mặc định.
2. Với heading, nếu cảm giác chữ quá rời, giảm rất nhẹ rồi so sánh.
3. Với ALL CAPS, tăng tracking vừa phải để các chữ tách bạch hơn.
4. Kiểm tra ở kích thước hiển thị thật.
5. Không cố “cứu” một font không phù hợp bằng tracking cực đoan.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Mặc định giữ tracking của font | Chỉnh tracking ở mọi text style |
| Siết nhẹ heading khi cần | Ép headline font dùng cho body nhỏ |
| Nới ALL CAPS để tăng legibility | Viết hoa + tracking chật làm chữ dính |

### Ví dụ đúng/sai
**Sai:** Label `FULL STACK DEVELOPER` dùng tracking mặc định, chữ hoa nhìn thành một khối đặc.

**Đúng:** Tăng letter-spacing vừa phải để từng ký tự tách rõ hơn.

### Lỗi thường gặp
- Dùng số tracking lớn vì nghĩ “cao cấp”.
- Siết chữ body đến mức khó đọc.
- Không test trên font thật hoặc size thật.

### Ngoại lệ
Typeface display được thiết kế riêng cho headline có thể đã có spacing phù hợp, không cần chỉnh. Hãy nhìn kết quả trước khi áp dụng công thức.

### Checklist
- [ ] Tôi đã thử tracking mặc định trước chưa?
- [ ] Headline có thật sự quá rời không?
- [ ] ALL CAPS có đủ khoảng để đọc nhanh không?
- [ ] Tôi có đang dùng tracking để sửa một lựa chọn font sai không?

### Tóm tắt
**Letter-spacing là tinh chỉnh, không phải công cụ sửa mọi vấn đề typography.**

---
