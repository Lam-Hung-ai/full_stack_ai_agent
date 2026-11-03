# Phần X - Tiếp tục nâng trình

## Bài 51 - Học từ những quyết định mà bạn “không nghĩ ra được”

### Vấn đề
Chỉ nhìn thiết kế đẹp và nói “đẹp thật” không giúp bạn hiểu vì sao nó đẹp. Bạn cần biến việc ngắm design thành việc phân tích quyết định.

### Mục tiêu
Xây thư viện ý tưởng trong đầu bằng cách phát hiện những lựa chọn khác với thói quen của chính mình.

### Lý thuyết
Sách đề xuất câu hỏi:

**“Designer có làm điều gì ở đây mà mình sẽ không bao giờ nghĩ tới không?”**

Ví dụ được nêu:
- Invert màu background của datepicker.
- Đặt button bên trong input thay vì bên ngoài.
- Dùng hai màu chữ khác nhau trong cùng headline.

Những quyết định “không trực giác” này là nơi bạn học được công cụ mới.

### Khi nào áp dụng
- Mỗi khi gặp website/app bạn thích.
- Khi xây moodboard/reference.
- Khi muốn thoát khỏi pattern lặp lại của bản thân.

### Cách làm
1. Chọn một interface bạn thật sự thích.
2. Không dừng ở “màu đẹp/font đẹp”.
3. Ghi lại 3-5 quyết định bạn sẽ không tự nghĩ ra.
4. Mô tả tác dụng của từng quyết định: hierarchy, grouping, affordance, personality...
5. Thử áp dụng nguyên lý tương tự vào bài toán khác, không copy nguyên visual.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Phân tích quyết định cụ thể | Chỉ lưu screenshot rồi quên |
| Học nguyên lý | Copy pixel-for-pixel vào sản phẩm khác |
| So với thói quen của bản thân | Chỉ săn trend |

### Ví dụ đúng/sai
**Sai:** Lưu 200 screenshot “inspiration” nhưng không biết mình thích điểm nào.

**Đúng:** Ghi chú: “CTA được đặt trong input giúp nhóm hành động thành một unit; headline dùng hai tone text để hierarchy mà không đổi size.”

### Lỗi thường gặp
- Chỉ chú ý màu và font.
- Copy visual không hiểu context.
- Không thử chuyển insight thành nguyên tắc dùng lại.

### Ngoại lệ
Một quyết định hay trong sản phẩm khác chưa chắc phù hợp sản phẩm của bạn. Mục tiêu là mở rộng vocabulary, không biến mọi reference thành template.

### Checklist
- [ ] Tôi đã chỉ ra được quyết định cụ thể nào làm mình bất ngờ chưa?
- [ ] Tôi hiểu nó giải quyết vấn đề gì không?
- [ ] Tôi có thể diễn giải thành nguyên lý không?
- [ ] Tôi có tránh copy nguyên context không?

### Tóm tắt
**Muốn học từ design đẹp, hãy tìm những quyết định bạn chưa từng nghĩ tới, không chỉ những thứ bạn thấy đẹp mắt.**

---

## Bài 52 - Rebuild giao diện yêu thích từ đầu

### Vấn đề
Nhìn một giao diện đã hoàn thiện khiến nhiều chi tiết nhỏ trở nên “vô hình”. Bạn thấy kết quả tổng thể nhưng không nhận ra line-height, spacing, shadow hay crop nào đang tạo ra độ polish.

### Mục tiêu
Rèn mắt bằng cách tái tạo design **từ đầu mà không xem developer tools**, để buộc bản thân đoán và so sánh.

### Lý thuyết
Sách xem đây là một trong những cách tốt nhất để nhận ra tiểu tiết. Khi bản rebuild “gần đúng nhưng vẫn khác”, bạn buộc phải tìm nguyên nhân và tự phát hiện những kỹ thuật như:
- Heading cần line-height chặt hơn.
- Uppercase text cần letter-spacing.
- Shadow có thể gồm nhiều lớp.
- Ảnh cần crop theo cách cụ thể.

Quá trình so sai khác chính là bài học.

### Khi nào áp dụng
- Luyện UI cá nhân.
- Học một visual style mới.
- Khi bạn biết lý thuyết nhưng “mắt chưa ra”.

### Cách làm
1. Chọn một màn hình không quá phức tạp.
2. Chỉ nhìn reference bằng mắt, không inspect CSS/dev tools.
3. Rebuild layout, type, spacing, color, shadow.
4. Đặt hai phiên bản cạnh nhau.
5. Ghi từng khác biệt bạn nhận ra.
6. Điều chỉnh rồi lặp lại.
7. Sau buổi luyện, viết 3-5 nguyên tắc đã học được.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Rebuild để luyện mắt | Copy code rồi coi như đã học |
| So sánh sai khác | Chỉ cố đạt giống bằng mắt mà không ghi insight |
| Rút ra nguyên tắc | Dùng lại nguyên thiết kế trong sản phẩm thương mại của mình |

### Ví dụ đúng/sai
**Sai:** Inspect website, copy CSS shadow/font-size rồi kết luận “mình làm giống rồi”.

**Đúng:** Tự ước lượng trước, so sánh sau, phát hiện vì sao version của mình nặng hơn: heading line-height quá rộng và shadow chỉ có một lớp.

### Lỗi thường gặp
- Chọn màn hình quá phức tạp rồi bỏ cuộc.
- Chỉ tập trung pixel accuracy mà không học nguyên lý.
- Không ghi lại điều mới phát hiện.

### Ngoại lệ
Đây là bài tập học tập. Khi làm sản phẩm thật, vẫn phải tôn trọng brand, context và yêu cầu riêng; không nên biến rebuild thành copy trực tiếp.

### Checklist
- [ ] Tôi đã chọn reference đủ nhỏ để hoàn thành chưa?
- [ ] Tôi có tránh inspect trước khi tự đoán không?
- [ ] Tôi có đặt hai bản cạnh nhau không?
- [ ] Tôi rút ra được ít nhất 3 insight cụ thể không?

### Tóm tắt
**Tái tạo một UI từ đầu là cách biến “mắt thấy đẹp” thành kỹ năng nhận ra các quyết định tạo nên cái đẹp đó.**

---
