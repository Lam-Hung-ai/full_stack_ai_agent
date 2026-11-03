# Quy trình thực thi chi tiết cho UI Agent

> Đây là quy trình **vận dụng** do skill xây từ `SOURCE-markdown-nguyen-ban.md`. Khi viện dẫn một nhận định của tác giả, đọc nội dung bài tương ứng trong các file chương. Mọi yêu cầu về tool, token, test hay mức ưu tiên trong tài liệu này là quy ước vận hành của skill, không phải trích nguyên văn cuốn sách.

## Mục lục

1. Phân loại công việc
2. Quy trình từ bài toán tới UI mới
3. Quy trình cải thiện UI hiện hữu
4. Quy trình làm việc với code
5. Xây design system
6. Xử lý nhiều phương án/trade-off
7. Kiểm thử biến thể và trạng thái
8. Cách giao tiếp và bàn giao

## 1. Phân loại công việc

| Tín hiệu đầu vào | Chế độ | Đọc nguồn trước | Sản phẩm mong đợi |
|---|---|---|---|
| "Thiết kế màn X" với luồng nghiệp vụ | Design | 1–5, 6–19, phần liên quan | mô hình thông tin + UI spec + trạng thái |
| "Nhìn UI này có gì sai" với ảnh | Audit | 6–19, 20–35, chủ đề bề mặt | vấn đề có bằng chứng + phương án sửa |
| "Cải thiện giao diện" với HTML/CSS/React | Refactor | 5, 6–19, 20–35, 45–50 | thay đổi có kiểm soát + test |
| "Làm thống nhất UI" | Design system | 4–5, 15, 20, 29–38 | token + quy tắc component |
| "Giải thích X là gì" | Teaching | bài X nguyên vẹn + glossary | bài học 11 mục khi cần |
| "Tại sao A hơn B" | Compare | bài ứng dụng + ngoại lệ | bảng so sánh theo nhiệm vụ |
| "Tối ưu trang toàn diện" | End-to-end | các chương 1–10 | phân tích → sửa → validation |

Nếu thiếu thông tin, chỉ hỏi điều khiến không thể làm bước tiếp theo: đối tượng người dùng, tác vụ chính, thiết bị mục tiêu, dữ liệu bắt buộc. Với brief đủ rõ, tự nêu giả định có thể thay đổi và tiến hành.

## 2. Từ bài toán đến UI mới

### 2.1. Khởi động với công việc thực

Viết thông tin tối thiểu: người dùng là ai; khi nào họ đến; họ cần hoàn thành gì; tiêu chí thành công; lỗi đáng tránh. Bắt đầu bằng một feature nhỏ, không tạo navbar/sidebar trước khi đủ ngữ cảnh (B1). Phân rõ:

- **Input:** người dùng điền/chọn/tải lên gì.
- **Output:** họ nhận được dữ liệu hay trạng thái gì.
- **Action chính:** xác nhận/tìm/đặt/mua/lưu.
- **Action phụ:** hủy, trở về, xem trợ giúp, reset.
- **Biến thể nội dung:** trống, một mục, rất nhiều mục, rất dài, lỗi, đang tải.

### 2.2. Xác định thông tin và phân nhóm

Xây sơ đồ theo nhóm chức năng thay vì mỹ thuật. Với form: một nhãn gần một trường; khoảng cách trong cặp nhỏ hơn khoảng cách giữa các cặp (B19). Với card: thông tin nhận diện → thông tin quyết định → thông tin bổ sung → hành động. Xác nhận nhóm bằng cách nhìn dưới dạng xám (B2).

### 2.3. Thiết kế hierarchy trước màu

Gán từng mục mức **P1 (thiết yếu)**, **P2 (hữu ích)**, **P3 (phụ)**. Cho mục P1 sử dụng tổ hợp vị trí, weight, kích cỡ, contrast; hạ độ nổi mục P3 trước khi làm P1 quá đậm (B6–9). Không nhầm label dữ liệu với form label (B10). Action primary/secondary/tertiary theo thứ tự ưu tiên tác vụ (B13).

Kiểm tra nhanh: người lần đầu có thể chỉ ra chức năng chính trong 5 giây không? *5 giây là bài test vận hành của skill*, không phải ngưỡng của sách.

### 2.4. Dàn trang và quy mô

Dùng hệ spacing hạn chế và có nhịp; ưu tiên không gian thoáng rồi điều chỉnh mật độ (B14–15). Giữ nội dung tại chiều rộng phục vụ mục đích của nó; dùng `max-width` với form/tài liệu cần bề ngang hạn chế, không mở full width vô cớ (B16–17). Cho hình, sidebar, text và CTA scale theo nhu cầu riêng; không giảm cùng phần trăm một cách tự động (B18).

Khi mobile: ưu tiên luồng tuyến tính và vùng tương tác; khi desktop: không kéo giãn form chỉ vì nhiều không gian. Đây là phần áp dụng logic nguồn, không phải breakpoint mặc định của sách.

### 2.5. Hệ chữ

Chọn type scale hữu hạn (B20), font đảm bảo đọc tốt (B21), độ dài dòng phù hợp (B22), căn theo baseline khi nội dung có cỡ khác nhau (B23), line-height biến đổi theo cỡ chữ/độ rộng dòng (B24), link có affordance theo ngữ cảnh (B25–26), alignment có trục đọc ổn định (B27), letter spacing theo loại nội dung (B28).

Không tự tạo nhiều size gần nhau khi token hiện có đã đủ. Đừng giảm text quan trọng quá nhỏ chỉ để ép các thành phần vừa một hàng.

### 2.6. Hệ màu

Xây family màu với nhiều shade (B29–31), điều chỉnh saturation khi lightness thay đổi (B32), có thể thêm sắc lạnh/ấm cho neutral (B33); kiểm tra độ tương phản trên từng nền cụ thể (B34). Thông tin trạng thái phải có ký hiệu/nhãn khác màu (B35). Không suy ra "WCAG pass" từ cảm nhận thị giác: kiểm tra thật bằng công cụ khi có khả năng.

### 2.7. Elevation, images, polish

Nếu dùng depth, tuân thủ một hướng sáng và quy tắc cấp độ shadow (B36–39). Overlap chỉ khi gợi nhóm/lớp có chủ ý (B40). Chọn ảnh chất lượng, xử lý chữ trên ảnh và intended size, tính tới ảnh do người dùng cung cấp (B41–44). Cải thiện default controls, accent, nền, empty state, giảm border và cân nhắc pattern sáng tạo theo giá trị tác vụ (B45–50).

### 2.8. Vòng lặp hoàn thiện

1. Tạo phương án tối giản hữu ích, tránh hứa tính năng chưa làm (B3).
2. Thử nội dung thật, tương tác có thể kiểm tra, lỗi/empty/long data.
3. Đo hiệu quả theo mục tiêu đã chọn, không chỉ hỏi "có đẹp không".
4. Sửa điểm cản tác vụ trước, rồi mới chỉnh polish.
5. Chốt specs: container width, token spacing/type/color, states, các trường hợp ngoại lệ.

## 3. Review một UI đang có

### 3.1. Thu thập bằng chứng

Ghi nhận những gì thực sự nhìn thấy: bố cục, vùng chính, một số màu, thứ tự, kích cỡ tương đối, label và CTA. Nếu ảnh không thể hiện mobile/hover/error, phải ghi "chưa quan sát được", không bịa.

### 3.2. Trình tự chẩn đoán

**Lớp A: tác vụ.** Có thấy action chính, dữ liệu cần quyết định, bước tiếp theo không? Nội dung nào không phục vụ mục tiêu?

**Lớp B: hierarchy.** Có quá nhiều phần tử cùng nổi; heading/header/sidebar lấn át nội dung; secondary xám quá nhạt; destructive action đỏ lấn át CTA không?

**Lớp C: spacing và width.** Có khoảng cách đều khiến label/input mất nhóm; nội dung kéo ngang quá dài; card nở vô ích; sidebar thu nhỏ bất thường không?

**Lớp D: typography và color.** Có 10 font size không hệ thống; paragraph dài khó đọc; line-height không tương ứng; trạng thái chỉ dựa hue; text trên ảnh mất tương phản không?

**Lớp E: depth và polish.** Border dày đặc; shadow tùy tiện; empty state thiếu hướng dẫn; ảnh bị crop sai hoặc chất lượng thấp?

### 3.3. Đề xuất sửa có thể triển khai

Mỗi lỗi: `Quan sát → Tác động → Sửa theo bước cụ thể → Bài nguồn → Ngoại lệ → Cách thử`.

Ví dụ: "Label `Tên` cách input 16px, input cách label nhóm sau 16px → nhóm mơ hồ → đổi thành 8px trong cặp và 24px giữa cặp; token minh họa, cần kiểm chứng thiết kế thực tế → B19; ngoại lệ form cực dày cần điều chỉnh nhịp." Không khẳng định các giá trị ví dụ này là mặc định nguyên tác.

### 3.4. Lọc cải tiến thừa

Mỗi đề xuất phải trả lời ít nhất một câu: giúp **nhìn đúng**, **đọc dễ**, **hiểu nhóm**, **chọn đúng**, **tương tác dễ**, **nhất quán**, hoặc **vừa trên thiết bị**? Nếu không, xếp vào tùy chọn polish.

## 4. Làm việc với source code

1. Tìm hiểu cấu trúc component hiện có và design tokens, đừng thay toàn bộ UI tùy hứng.
2. Giữ semantics và behavior; không biến link thành nút hoặc ngược lại chỉ vì trình bày.
3. Ưu tiên sửa token/variant chung thay vì hard-code nhiều chỗ.
4. Nếu thay đổi spacing/size gây reflow, kiểm chứng ít nhất một viewport hẹp và một viewport rộng khi có môi trường phù hợp.
5. Với dynamic data, kiểm thử null/empty/long/localized strings.
6. Khi không thể chạy hay render code, ghi rõ chưa xác minh thay vì nhận là test pass.
7. Tài liệu này không quy định framework; CSS/Tailwind/React chỉ là hiện thực hóa theo context user.

## 5. Design system có kiểm soát

Xây theo thứ tự:

1. Mục tiêu sản phẩm và visual personality (B4).
2. Bộ font và thang chữ, font weight, line height (B5, B20–24).
3. Spacing/sizing tokens có khoảng cách nhận biết được (B5, B15).
4. Palette HSL, neutrals và shades cho surface/text/actions/status (B29–35).
5. Border radius/border/shadow/elevation hệ thống (B5, B36–39, B49).
6. Các component/variant: primary, secondary, tertiary; normal/hover/focus/disabled/error/loading/selected, tùy tính năng.
7. Quy tắc responsive, density, long content, dark/background images nếu có yêu cầu.

Đừng biến mọi giá trị minh họa từ sách thành token cố định. Hệ thống cần đủ giới hạn để giảm băn khoăn, đủ linh hoạt để phục vụ ngữ cảnh.

## 6. So sánh hai phương án hoặc trade-off

Ví dụ A dùng header lớn, B dùng header nhỏ. Đặt cùng dữ liệu và tác vụ; so theo **tốc độ tìm thông tin**, **độ đọc**, **mức chiếm chỗ**, **responsive**, **khả năng dùng**. Không tuyên bố "B tốt hơn" chỉ vì trông gọn. Nếu cả hai hợp trong bối cảnh khác nhau, nêu rõ điều kiện chọn.

Các trade-off quan trọng:

- Thoáng **vs** dữ liệu dày (B14).
- Dấu hiệu tương tác nổi **vs** nhiều điểm tranh attention (B13, B25–26).
- Grid đồng nhất **vs** đúng chiều rộng từng nội dung (B16–17).
- Nhiều màu ngữ nghĩa **vs** một hierarchy yên tĩnh (B29–35).
- Chống lóa/flat **vs** depth để nhận biết elevation (B36–40).
- Sáng tạo component **vs** khả năng nhận biết và sử dụng (B50).

## 7. Matrix kiểm thử trạng thái

| Trạng thái | Câu hỏi | Bài liên quan |
|---|---|---|
| Không có dữ liệu | Có hướng dẫn tiếp theo không? | 48 |
| Có 1 mục | Bố cục có trống rỗng/giãn quá mức? | 14, 16 |
| Có hàng trăm mục | Density và phân nhóm còn quét được không? | 6, 14, 19 |
| Chữ rất dài | Có tràn/ellipsis sai, line-wrap khó hiểu? | 18, 22, 24, 27 |
| Ảnh quá sáng/tối | Chữ trên ảnh còn tương phản không? | 42 |
| Ảnh upload méo, sai tỷ lệ | Có crop/fit/fallback chấp nhận được không? | 43–44 |
| Bàn phím/chạm | Link/control còn nhận diện và thao tác? | 13, 25–26, 35 |
| Error/success | Có thông điệp/biểu tượng ngoài màu không? | 13, 35 |
| Màn hình hẹp | Cỡ thành phần có co có chủ đích? | 16–18 |
| Nhiều CTA | Có xác định primary không? | 6, 9, 13 |

## 8. Giao tiếp và bàn giao

Khi nói với beginner, giảm jargon và giải nghĩa; khi làm với lập trình viên, bổ sung token, component/state và test. Cả hai đều cần lý do theo hành vi người dùng.

Mẫu diễn đạt tốt: "Nút `Lưu` và `Xóa` cùng màu nổi khiến hai thao tác cạnh tranh; giảm `Xóa` thành hành động phụ trên màn hình và đặt xác nhận khi xóa thật (B13). Chỉ làm vậy nếu dễ tìm lại thao tác xóa, đặc biệt với quyền admin."

Mẫu diễn đạt chưa đủ: "Làm nút xóa nhỏ và nhìn hiện đại hơn."

Trong câu trả lời cuối, không trích toàn văn chương. Tham chiếu Bài N và tóm tắt lập luận ở mức cần thiết; để người dùng yêu cầu mở rộng khi muốn đào sâu.
