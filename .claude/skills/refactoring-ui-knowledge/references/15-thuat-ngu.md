# Thuật ngữ UI giải nghĩa cho người mới

> Các mô tả dưới đây là lời diễn giải cho người học, dựa trên những khái niệm xuất hiện trong bản Markdown gốc. Không thay thế định nghĩa kỹ thuật chính thức ngoài nguồn.

## Nội dung và hành vi

- **UI (User Interface) — giao diện người dùng:** phần người dùng nhìn và thao tác với sản phẩm.
- **Feature — tính năng:** việc sản phẩm hỗ trợ người dùng thực hiện, như tìm, đặt, lưu hoặc gửi.
- **Layout — bố cục:** cách đặt các khối trên màn hình.
- **App shell — khung ứng dụng:** navigation, sidebar, header, vùng bao; không phải mục tiêu đầu tiên trong Bài 1.
- **Flow — luồng:** thứ tự các bước người dùng thực hiện để đạt mục tiêu.
- **Input — dữ liệu nhập:** text field, chọn ngày, checkbox, upload.
- **Output — kết quả:** dữ liệu, trạng thái hay phản hồi trả về sau thao tác.
- **Action / CTA — hành động hoặc lời kêu gọi thao tác:** ví dụ `Lưu`, `Thanh toán`, `Tìm chuyến bay`.
- **Primary / secondary / tertiary action:** cấp quan trọng chính / phụ / ít dùng; không hoàn toàn tương đương màu nào trên nút.
- **Wireframe — bản phác bố cục:** mô tả nhóm thông tin, vị trí, tác vụ trước khi chọn visual chi tiết.
- **Low fidelity / high fidelity:** phác thô/thiết kế chi tiết; mục đích khác nhau, không đo chất lượng bằng độ bóng bẩy.
- **Empty state — trạng thái rỗng:** giao diện khi chưa có dữ liệu hoặc kết quả.
- **Edge case — tình huống biên:** dữ liệu quá dài, quá nhiều, trạng thái lỗi, ảnh đặc biệt...

## Thứ bậc và typography

- **Visual hierarchy:** mức quan trọng mà các phần tử *có vẻ* thể hiện trước mắt người dùng.
- **Document hierarchy / semantic hierarchy:** cấu trúc tiêu đề/nội dung về mặt ý nghĩa, không đồng nhất với cỡ chữ hiển thị.
- **Emphasis / de-emphasis:** tăng/giảm độ chú ý có chủ đích.
- **Contrast — tương phản:** mức khác biệt thị giác giữa hai phần; có thể do độ sáng, màu, weight, kích thước.
- **Visual weight — độ nặng thị giác:** lượng chú ý một đối tượng chiếm; icon đặc/đậm thường có trọng lượng lớn.
- **Typography — thiết kế chữ:** font, cỡ, đậm nhạt, khoảng cách, dòng, căn chỉnh.
- **Typeface / font:** hệ chữ / cách triển khai một bộ chữ; tài liệu thường dùng gần tương đương ở cấp cơ bản.
- **Type scale — thang cỡ chữ:** tập cỡ cố định hạn chế để dùng lặp lại.
- **Font weight:** độ đậm của chữ, ví dụ 400 là normal, 600–700 là bold hơn.
- **Baseline:** đường cơ sở để căn chữ có cỡ/kiểu khác nhau trong cùng hàng.
- **Line height:** chiều cao dòng; thường liên quan đến khoảng cách dọc giữa các dòng.
- **Line length:** độ dài dòng, thường xét số ký tự trên một dòng khi đọc đoạn văn.
- **Letter spacing:** khoảng cách giữa ký tự, điều chỉnh có chủ đích cho heading/chữ hoa.
- **Alignment:** căn lề/căn trên cùng một trục, ví dụ trái/giữa/phải.
- **Label:** nhãn gọi tên giá trị hoặc control; **nhãn dữ liệu** có thể lược khi đủ ngữ cảnh, nhưng **nhãn form** phải rõ.
- **Affordance:** dấu hiệu gợi người dùng biết một phần tử có thể tương tác.

## Layout, spacing và responsive

- **Spacing:** khoảng cách giữa hay trong các phần tử.
- **Whitespace / negative space:** khoảng trống giúp phân cấp và nhóm, không nhất thiết màu trắng.
- **Margin:** khoảng bên ngoài khối.
- **Padding:** khoảng bên trong khối.
- **Spacing scale:** bộ số khoảng cách đã chọn trước; giảm quyết định tùy tiện.
- **Grid:** hệ cột/đường tham chiếu để bố cục; là công cụ, không phải luật tuyệt đối.
- **Fluid width:** chiều rộng thay đổi theo không gian sẵn có.
- **Fixed width:** chiều rộng cố định theo giá trị cụ thể trong bối cảnh phù hợp.
- **Max-width:** bề rộng lớn nhất cho phép, giúp nội dung không bị kéo dãn vô ích.
- **Responsive:** UI đáp ứng nhiều kích thước màn hình bằng thay đổi có chủ đích.
- **Breakpoint:** mức kích thước tại đó các quy tắc bố cục đổi kiểu (khái niệm triển khai, không phải token cố định từ sách).
- **Density:** mật độ thông tin trong một vùng; dashboard có thể cần dày hơn landing page.

## Màu, depth, hình ảnh

- **Hue:** loại màu (xanh/đỏ/vàng...) trong HSL.
- **Saturation:** độ bão hòa/độ rực màu.
- **Lightness:** độ sáng theo biểu diễn HSL; không luôn giống perceived brightness.
- **Color palette / shades:** họ màu và các mức sáng/tối dùng trong hệ thống.
- **Neutral / grey:** các màu nền và chữ trung tính; có thể hơi ấm/lạnh.
- **Color accessibility:** sử dụng màu sao cho nhiều người vẫn nhận hiểu được thông tin, cả khi khó phân biệt màu.
- **Depth:** cảm giác lớp/bề mặt trước sau.
- **Shadow:** bóng; có thể gợi bề mặt nhô cao và khoảng cách lớp.
- **Elevation:** cấp độ một thành phần được cảm nhận nổi lên trên mặt nền.
- **Inset:** thành phần có cảm giác lõm xuống bề mặt.
- **Overlap:** đặt các thành phần chồng nhau có chủ ý để tạo quan hệ lớp.
- **Intended size:** cỡ/tỉ lệ mà hình, logo hay icon được thiết kế để hiển thị rõ nhất.
- **Crop / fit:** cắt vùng nhìn / co ảnh để vừa vùng hiển thị.
- **Accent border:** đường viền nhấn với màu có vai trò thị giác.
- **Finishing touches:** các cải tiến cuối để UI tinh tế hơn sau khi cấu trúc đã ổn.

## Hệ thống và thực hành

- **Design system:** tập các quyết định và thành phần dùng lại như token, font, màu, spacing, button states.
- **Design token:** tên đại diện cho giá trị dùng lặp lại, ví dụ `space-3`, `text-sm`, `color-primary-600`.
- **Component:** đơn vị giao diện dùng lại như button, input, card, table.
- **Variant:** biến thể component cho vai trò, cỡ hoặc trạng thái.
- **Polish:** tinh chỉnh độ nhất quán và độ hoàn thiện, không thay thế tính dễ dùng.
- **Before/after:** mô tả trạng thái hiện tại và đề xuất sau sửa để quan sát hiệu quả.

## Lưu ý khi giải thích

Không trộn lẫn **hierarchy thị giác** với **semantic HTML**. Không hiểu "semantics are secondary" là bỏ ý nghĩa hành động hoặc accessibility. Không hiểu "label là phương án cuối" là xóa nhãn cần cho form. Không trình bày các mức token như giá trị bắt buộc của sách nếu nguồn chỉ cho ví dụ.
