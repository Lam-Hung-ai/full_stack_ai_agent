# Rubric đánh giá giao diện và kiểm tra chất lượng

> **Công cụ của skill, không phải hệ thống điểm của tác giả.** Bảng điểm giúp agent ưu tiên những thay đổi có tác động thực. Khi tuyên bố nguyên tắc của Refactoring UI, mở đúng bài nguồn. Không chấm kết luận dựa trên ảnh nếu thuộc tính chỉ đo được qua tương tác hoặc mã nguồn.

## Mục lục

1. Các nguồn bằng chứng
2. Rubric tám chiều
3. Mức độ ưu tiên
4. Các phép kiểm cụ thể
5. Báo cáo mẫu
6. Quy tắc dừng

## 1. Phân loại độ chắc chắn

- **Đã quan sát:** ví dụ screenshot cho thấy mọi button đều cùng contrast; đoạn văn quá dài hoặc ảnh hiển thị tràn vùng.
- **Đã đo/kiểm thử:** ví dụ contrast ratio đo bằng công cụ và môi trường; button nhận focus khi dùng bàn phím; UI render tại kích thước cụ thể.
- **Có khả năng/rủi ro:** ví dụ ảnh người dùng tải lên có thể thiếu tương phản; trên mobile dài hơn có thể overflow, nhưng chưa có viewport test.
- **Chưa đủ thông tin:** không thấy empty state, typography token hay focus; không thể khẳng định lỗi/đạt.

Mỗi nhận xét dài hạn nên gắn một loại bằng chứng. Không tạo điểm giả chính xác từ ảnh chụp thấp độ phân giải.

## 2. Chấm tám chiều (0–3)

Điểm chỉ nhằm giúp tổ chức công việc: **0 = cản tác vụ hoặc vi phạm rõ**, **1 = yếu**, **2 = dùng được/còn cải thiện**, **3 = rõ và nhất quán**, **N/A = không liên quan/chưa kiểm chứng**.

| Chiều | Hỏi gì? | Các bài nguồn |
|---|---|---|
| A. Task focus | Người dùng biết phải làm gì, action chính ở đâu? | 1–3, 6, 13 |
| B. Hierarchy | Primary/secondary/tertiary có phân cấp, không tranh attention? | 6–13 |
| C. Grouping & layout | Nhóm rõ; spacing và chiều rộng phục vụ nội dung? | 14–19 |
| D. Typography | Font, line length, line-height, alignment, link dễ đọc? | 20–28 |
| E. Color & state meaning | Màu có hệ thống và không là tín hiệu duy nhất? | 29–35 |
| F. Depth & media | Shadow/elevation, hình ảnh, text-over-image có chủ đích? | 36–44 |
| G. Completion | Empty/long/error states, borders, defaults xử lý phù hợp? | 45–50, 3 |
| H. Consistency & learnability | Có hệ token; pattern hợp kỳ vọng; có quy trình lặp? | 4–5, 15, 20, 31, 50–52 |

**Đừng tính trung bình khi thiếu nhiều dữ liệu.** Ví dụ chỉ có screenshot desktop thì "responsive" phải ghi chưa kiểm tra. Một lỗi cản tác vụ quan trọng hơn nhiều lỗi trang trí nhỏ cho dù tổng điểm cao.

## 3. Ưu tiên P0–P3

- **P0: Cản tác vụ / nguy cơ nghiêm trọng.** Ví dụ nút submit bị che, chữ cảnh báo không đọc được, thông tin cần thiết bị mất, ý nghĩa success/error chỉ có màu khiến người dùng không phân biệt được.
- **P1: Gây sai/nhầm đáng kể.** Ví dụ label bị hiểu nhầm, hai CTA cùng nổi nhưng ý nghĩa khác hẳn, vùng click không có dấu hiệu nhận diện, nội dung chính bị sidebar lấn át.
- **P2: Làm trải nghiệm chậm/hơi khó đọc.** Ví dụ type scale phân mảnh, spacing chưa nhất quán, column quá rộng, image crop chưa lý tưởng.
- **P3: Polish tùy chọn.** Ví dụ shadow nhòe nhẹ, accent border/corner chưa đồng đều, hình nền chưa hợp personality.

Ưu tiên dựa trên **mức ảnh hưởng đến hành vi**, không chỉ sự nổi bật về màu sắc.

## 4. Các phép kiểm mang tính thao tác

### 4.1. Test grayscale (B2, B6–9, B35)

Ẩn màu hoặc chuyển ảnh screenshot sang xám; xem liệu mắt còn tìm được mục chính, trạng thái xấu/tốt còn phân biệt bằng icon/label, và phần bị de-emphasize có còn đọc được không. Grayscale test là công cụ hỗ trợ; không thay thế kiểm tra screen reader/contrast.

### 4.2. Test hierarchy nhìn lướt (B6–13)

Yêu cầu người chưa biết trang trả lời: "Màn hình này dùng làm gì?", "Nút chính là gì?", "Nội dung cần đọc đầu tiên?". Đánh dấu nếu người xem bị CTA phụ, nhãn, hình trang trí làm nhiễu. Không dùng kết quả một người như kiểm chứng khoa học.

### 4.3. Test nhóm bằng khoảng cách (B19)

Đánh dấu từng cặp liên quan: label–input, title–description, icon–metric, item–action. Khoảng cách giữa các nhóm cần lớn hơn khoảng cách trong nhóm nếu không có separator rõ. Kiểm tra ngang lẫn dọc.

### 4.4. Test hệ giá trị (B5, B15, B20, B31)

Xem token của text/spacing/radius/color; nếu xuất hiện nhiều giá trị sát nhau do tinh chỉnh tùy tiện, gom về scale có phân biệt rõ. Không đổi giá trị chỉ vì nó không chia hết cho 4; bản gốc không cổ vũ scale tuyến tính cứng.

### 4.5. Test chiều rộng và reflow (B16–18, B22)

Thử viewport hẹp/vừa/rộng nếu có khả năng. Kiểm tra form có rộng bất hợp lý, sidebar co quá hẹp, heading tỷ lệ quá lớn trên mobile, line length quá dài, button overflow, nội dung bị cắt.

### 4.6. Test text (B20–28)

Quan sát body content có quá dày hay quá nhạt, line-height có đủ cho đoạn dài, left alignment với nội dung dài, baseline của icon/text và chữ khác cỡ, ALL CAPS bị sát chữ. Không mặc định cùng line-height cho mọi heading/body.

### 4.7. Test tương phản và semantic (B13, B34–35)

- Dùng công cụ nếu muốn kết luận một cặp màu có đạt chuẩn truy cập; nếu không có công cụ, ghi "cần đo".
- Thử trường hợp không phân biệt hue: success/error cần chữ, icon, pattern hay ký hiệu.
- Kiểm tra trạng thái focus, hover, disabled và selected bằng tương tác khi có điều kiện.
- Ngoại lệ: hành động phá hủy có thể được đặt ở cấp phụ trên màn hình, nhưng xác nhận phá hủy phải dễ nhận biết.

### 4.8. Test media & polish (B36–50)

Thử ảnh rất sáng/rất tối; ảnh chân dung vuông/dọc/ngang; ảnh lỗi; thumbnail dùng sai intended size; grid có hàng rỗng. Phân biệt khi nào shadow biểu diễn elevation và khi nào chỉ là noise. Kiểm tra border có thể thay bằng spacing/background/shadow mềm hơn không.

## 5. Mẫu báo cáo áp dụng

```markdown
## Tóm tắt
Tác vụ: [một câu]. Điểm đáng sửa nhất: [P0/P1...].

## Phát hiện có căn cứ
| Ưu tiên | Quan sát (đã thấy/chưa đo) | Tác động tới người dùng | Đề xuất | Nguồn |
|---|---|---|---|---|
| P1 | [thực tế nhìn thấy] | [hệ quả] | [thay đổi] | Bài N |

## Đề xuất bố cục trước/sau
- Trước: [...]
- Sau: [...]
- Điều kiện: [...]

## Kiểm thử cần chạy
- [ ] Mobile/desktop
- [ ] Contrast
- [ ] Empty/error/long content
- [ ] Focus/touch

## Chưa thể kết luận
[Những thứ thiếu bằng chứng.]
```

## 6. Quy tắc dừng

Dừng polishing khi (a) người dùng hoàn thành tác vụ rõ ràng, (b) UI đủ nhất quán, (c) các điều kiện quan trọng đã được kiểm tra, và (d) các thay đổi trang trí thêm không có lợi ích rõ. Quy tắc dừng xuất phát từ tinh thần B2/B3/B45–50: đừng mắc kẹt ở tiểu tiết; đây không phải điểm dừng chính thức trong sách.
