# Công thức áp dụng theo từng loại màn hình

> Các công thức dưới đây **do skill tổng hợp** từ 52 bài trong Markdown; không phải screenshot, layout bắt buộc hoặc bảng mẫu nguyên tác. Luôn xác nhận tác vụ người dùng, nền tảng, lượng dữ liệu và ngoại lệ trước khi áp dụng.

## Mục lục

1. Login/đăng ký
2. Form dài/cài đặt
3. Search/filter/results
4. Dashboard/analytics
5. Data table/admin
6. Product detail & checkout
7. Pricing & plan selector
8. Profile/employee card
9. Article/help/documentation
10. Landing page/hero
11. Feed/timeline/community
12. Empty/error/success states
13. Navigation và menu
14. Media gallery/upload

## 1. Login / đăng ký

**Mục tiêu:** nhập thông tin và hoàn thành đăng nhập/đăng ký, không bị các yếu tố phụ phân tán.

**Khung gợi ý:** tên tác vụ → 2–4 trường thiết yếu → action chính → trợ giúp/quên mật khẩu → luồng thay thế nếu thực sự cần. Cho form bề rộng vừa đủ thay vì full-screen chỉ vì desktop lớn (B16–17). Xếp label gần input, nhóm field với spacing rõ (B19). Dùng nút đăng nhập primary; link phụ không cạnh tranh (B13, B25–26).

**Lưu ý:** không tự xóa nhãn form theo B10; B10 bàn về label của dữ liệu hiển thị. Giữ thông báo lỗi gần trường, rõ lời; nếu có yêu cầu truy cập phải xử lý focus, tương phản và biểu thị lỗi ngoài màu (B35).

**Ngoại lệ:** đăng ký nhiều bước, SSO, pháp lý/bảo mật có thể yêu cầu nội dung bổ sung. Đừng nén thông tin pháp lý quan trọng chỉ để gọn.

## 2. Form dài / trang cài đặt

**Mục tiêu:** cho người dùng tìm đúng nhóm và không nhập nhầm.

**Khung:** nhóm logic → tiêu đề nhóm nhỏ đúng mức → text mô tả phụ → label–control gần nhau → khoảng giữa nhóm đủ lớn → action lưu rõ (B11, B19). Trên desktop, nội dung giải thích có thể thành cột riêng; không kéo input dài vô lý (B16–17). Hệ spacing nhất quán (B15).

**Sai thường gặp:** mọi khoảng cách dọc bằng nhau, tiêu đề quá lớn so với nội dung, tất cả button là primary, phần "Lưu" lẫn trong thứ yếu.

**Ngoại lệ:** cấu hình quản trị dữ liệu dày có thể nén mật độ có chủ đích (B14); nhãn kỹ thuật cần đủ rõ vì người dùng tìm theo thuộc tính (B10).

## 3. Tìm kiếm / lọc / kết quả

**Mục tiêu:** tìm đúng đối tượng và so sánh kết quả.

**Khung:** ô tìm rõ → filter đủ dùng → tình trạng tìm kiếm → kết quả; trong mỗi item, nổi bật tên + thuộc tính dùng để phân biệt; metadata giảm nhấn (B6–10). Ảnh cần kích thước nhất quán; dynamic uploads có fallback (B43–44). Kết quả rỗng giải thích tiêu chí và đề xuất sửa bộ lọc (B48).

**Sai thường gặp:** mọi field trong card có cùng độ đậm; filter panel có background/border nặng hơn kết quả; thông báo "không có" mà không có đường ra.

**Ngoại lệ:** người dùng chuyên nghiệp cần so sánh rất nhiều thuộc tính có thể thích table dày (B14, B50).

## 4. Dashboard / analytics

**Mục tiêu:** thấy chỉ số quan trọng và phát hiện thay đổi nhanh.

**Khung:** summary metric ưu tiên → nhóm theo tác vụ/chủ đề → biểu đồ chi tiết → bộ lọc/context; label của metric có thể nhỏ hơn giá trị nhưng phải hiểu được (B10). Chủ động giảm độ nhấn nav/phần ít dùng (B9). Giữ contrast giữa series, kết hợp kí hiệu hoặc label thay vì màu thuần túy (B35). Chọn mật độ phù hợp nghiệp vụ (B14).

**Sai thường gặp:** 20 card ngang hàng, đường viền mọi nơi, chart chỉ phân biệt đỏ/xanh, giá trị bị làm nhỏ hơn label.

**Ngoại lệ:** dashboard kỹ thuật có yêu cầu quan sát đồng thời dữ liệu dày; ưu tiên chính xác/khả năng quét hơn card to và whitespace thừa.

## 5. Data table / admin list

**Mục tiêu:** quét, lọc, so sánh, sửa hành động trên từng hàng.

**Khung:** hàng có thông tin nhận diện nổi bật; cột số liệu canh có quy luật; header đủ dễ tìm; button action chính trong ngữ cảnh, menu overflow cho việc hiếm; nhẹ border, có thể thay bằng spacing/bề mặt (B10, B13, B49). Duy trì group theo dòng rõ (B19). Dữ liệu liên quan có thể gộp nếu không cần sort riêng (B50).

**Sai thường gặp:** mọi cột có font màu giống nhau, ảnh/avatar làm trọng tâm thay số liệu, nút xóa đỏ mạnh trên mọi hàng.

**Ngoại lệ:** table phân tích yêu cầu sort/filter độc lập; không gộp cột khiến mất thao tác.

## 6. Product detail & checkout

**Mục tiêu:** nhận diện đúng sản phẩm, hiểu giá/trạng thái và mua an toàn.

**Khung:** hình có intended size rõ → title/price → thông số quyết định → CTA nổi bật → thông tin phụ. Dùng giá/định dạng làm tín hiệu mà không bắt buộc lặp label dư (B10). Checkout thường phù hợp chiều rộng vừa đủ (B16). Destructive/secondary actions không được tranh với thanh toán (B13). Thumbnail cắt đẹp và chữ trên ảnh phải đọc được (B41–44).

**Sai thường gặp:** bỏ quá nhiều chữ lên ảnh không có nền bảo vệ; nhiều button màu khác nhau cùng quá nổi; form thanh toán tràn ngang.

**Ngoại lệ:** thông tin pháp lý, chi phí, điều kiện giao dịch không nên bị giảm tương phản đến mức khó tìm.

## 7. Pricing / chọn gói

**Mục tiêu:** so sánh lựa chọn và biết mình đang chọn gì.

**Khung:** plan card có tên/giá/thuộc tính khác nhau thật sự → selected state rõ ràng → action một cấp; xem radio card là biến thể presentation khi phù hợp (B50). Dùng hierarchy và giảm độ nổi option phụ (B6–9). Hạn chế nhãn thừa gây nhiễu (B10).

**Sai thường gặp:** mọi gói được nhấn mạnh như nhau, trạng thái selected chỉ đổi màu, mọi plan có shadow cực mạnh.

**Ngoại lệ:** nhiều lựa chọn đồng chất/hàng chục option có thể nên dùng table hoặc list thay vì card lớn.

## 8. Profile / employee card

**Mục tiêu:** nhận diện một người và đọc thông tin liên hệ nhanh.

**Khung:** tên là thông tin nhận diện chính; vai trò/phòng ban làm phụ; email/điện thoại hiển thị theo format tự giải nghĩa; đừng lặp nhãn "Tên:", "Email:" nếu không cần (B10). Ảnh đại diện có fixed/intended size, không scale với card (B17, B43–44).

**Sai thường gặp:** dàn label-value ngang hàng làm tên mất trọng tâm; icon quá đậm so với chữ (B12).

**Ngoại lệ:** trang chỉnh sửa hồ sơ cần nhãn trường, nội dung kỹ thuật cần label nổi để tìm nhanh.

## 9. Article / documentation / help

**Mục tiêu:** đọc đoạn dài mà không mỏi và tìm tiêu đề nhanh.

**Khung:** bề rộng text hữu hạn (B22); left-alignment với ngôn ngữ đọc trái-sang-phải (B27); line-height điều chỉnh theo line length (B24); type scale có cấp hợp lý (B20); heading gần đoạn theo quan hệ nhóm (B19); inline link phải phân biệt rõ (B25–26); letter spacing tiết chế (B28).

**Sai thường gặp:** paragraph tràn full width desktop, canh giữa cả đoạn dài, liên kết không nhận biết được, heading to quá mức màn hình nhỏ.

**Ngoại lệ:** heading hero ngắn có thể canh giữa nếu cấu trúc tổng thể cho phép, không áp cho đoạn dài.

## 10. Landing page / hero

**Mục tiêu:** truyền đạt lời hứa và hành động chính trong vài giây.

**Khung:** statement → chứng cứ/giải thích → một CTA → hình hỗ trợ. Tính cách nhất quán qua font/màu/radius/ngôn ngữ (B4); không lạm dụng space vô cớ nhưng có thể bắt đầu rộng (B14). Nếu ảnh nền có text overlay, đảm bảo contrast trên mọi vùng ảnh (B42).

**Sai thường gặp:** nhiều illustration/shadow lấn át sản phẩm, typography có quá nhiều size hoặc CTA hầu như không phân biệt.

**Ngoại lệ:** trang editorial nghệ thuật có thể ưu tiên một trải nghiệm khác, miễn không đánh đổi khả năng tìm việc phải làm.

## 11. Feed / timeline / community

**Mục tiêu:** quét nhiều mục theo thời gian, hiểu từng post và hành động.

**Khung:** nhóm avatar, tác giả, thời gian và body bằng hierarchy/spacing; giảm contrast icon nặng (B12); border giữa item chỉ khi spacing/surface không đủ (B49). Action like/reply/share phải nhận diện nhưng không lấn át nội dung (B13).

**Sai thường gặp:** icon quá đen; tất cả timestamp/tác giả/body cùng kích cỡ và màu; không có khoảng giữa post.

**Ngoại lệ:** app có mục tiêu tương tác cực nhanh có thể cần action prominence hơn một feed đọc đơn thuần.

## 12. Empty / error / success / no results

**Mục tiêu:** khi hệ thống không hiển thị dữ liệu bình thường, người dùng vẫn biết tiếp theo là gì.

**Khung:** trạng thái ngắn gọn → nguyên nhân có thể hiểu → một hành động hợp lý nếu có. Empty state không chỉ là chỗ trống (B48). Nếu color biểu thị status, bổ sung icon/text (B35). Đừng đưa CTA không có chức năng thực (B3).

**Sai thường gặp:** "No data" không có hướng xử lý; error chỉ nền đỏ; success dùng icon mà không có message.

**Ngoại lệ:** trong thành phần phụ, empty state có thể tối giản để không làm màn hình quá ồn.

## 13. Navigation / dropdown / menu

**Mục tiêu:** tìm đúng nơi cần đến và biết mình đang ở đâu.

**Khung:** nav structure phát sinh từ tính năng thật (B1); active nav nổi lên bằng cách giảm inactive khác (B9). Dropdown có nhiều nội dung có thể tổ chức section, icon, supporting text và nhiều cột, nhưng cần dễ đọc/dễ thao tác (B50).

**Sai thường gặp:** sidebar quá nổi, active item chỉ khác màu nhẹ trên một hàng toàn màu mạnh; mega menu có trang trí khiến mất đường nhìn.

**Ngoại lệ:** với nav rất ngắn, component mặc định dễ dùng hơn giải pháp tùy biến.

## 14. Media gallery / upload

**Mục tiêu:** giữ sự nhất quán thị giác dù ảnh do người dùng quyết định.

**Khung:** hình hiển thị trong frame có quy tắc crop/fit; fallback cho ảnh hỏng/thiếu; kiểm thử nội dung sáng, tối, chữ trên ảnh (B41–44). Nếu ảnh không đồng nhất kích thước, tối ưu frame cho trường hợp thực tế, không chỉ sample đẹp.

**Sai thường gặp:** overlay text trắng trên mọi ảnh không có hỗ trợ contrast; logo/icon vector phóng quá cỡ dùng; ảnh tỉ lệ dọc ép vào frame ngang méo.

**Ngoại lệ:** khi cần xem trọn nội dung ảnh (biểu đồ, bản vẽ), ưu tiên contain và cho phép zoom thay vì crop đẹp.

## Cách dùng công thức

1. Chọn đúng loại màn hình, xác nhận mục tiêu.
2. Đọc bài nguồn được tham chiếu (bao gồm `Ngoại lệ`).
3. Dùng công thức như **gợi ý khởi đầu**, không sao chép mọi component.
4. Chọn tối đa vài cải tiến có tác động, thử với dữ liệu thật.
5. Nếu mục tiêu người dùng không phù hợp với công thức, ưu tiên mục tiêu chứ không ép khuôn.
