# Chương 4 — Knowing What to Do: Constraints, Discoverability, and Feedback

> Nguồn: `../source/chapter-04.md`, L1891–L2436, trang 123–161. Tập trung làm hành động đúng **dễ thấy và dễ làm**, hành động sai **khó xảy ra**, thay đổi hệ thống **dễ hiểu**.

## 1. Vấn đề

Gặp sản phẩm chưa dùng bao giờ, người dùng không biết đâu là lựa chọn hợp lệ. Nếu thiếu giới hạn hợp lý, quá nhiều hành động đều có vẻ đúng; họ thử-sai, nhầm nút hoặc không biết cách sửa. Thay đổi quy ước quen thuộc (ví dụ thang máy nhập tầng trước khi lên) có thể khiến ngay cả người lành nghề bối rối. [L1891–L1922; L2202–L2250]

## 2. Mục tiêu

Giới hạn không gian hành động bằng cấu trúc hợp lý, cho người dùng thấy dấu hiệu và trạng thái, hướng dẫn họ chọn đúng mà ít ghi nhớ. Dùng giới hạn đủ mạnh để ngăn nguy cơ, nhưng không tạo khóa chặn không thể phục hồi.

## 3. Lý thuyết

### 3.1 Bốn loại constraints

|Loại|Cơ chế|Ví dụ trong nguồn|Ứng dụng UX|
|---|---|---|---|
|**Physical**|Đặc điểm vật lý khiến hành động bất khả thi.|Mảnh Lego chỉ lắp theo một số chiều.|Field loại file chỉ cho đúng định dạng; vô hiệu thao tác không thể làm.|
|**Cultural**|Quy ước do học tập/văn hóa.|Thói quen ứng xử ở nhà hàng, quy ước dấu/biểu tượng.|Giữ mẫu tương tác quen thuộc cho nhóm người mục tiêu.|
|**Semantic**|Ngữ nghĩa nhiệm vụ giới hạn hành động hợp lý.|Người lái phải ngồi trên xe, kính chắn gió đặt phía trước.|Dùng tên/nhóm/chú thích thể hiện mục đích và đối tượng.|
|**Logical**|Loại trừ các khả năng cho tới khi còn vị trí đúng.|Chỉ còn một mảnh Lego chưa lắp.|Wizard chỉ hiển thị bước hợp lệ, chỉ rõ mục thiếu khi hoàn tất.|

Các loại này có thể kết hợp, không loại trừ nhau. Không được gọi một `disabled button` là physical constraint theo nghĩa máy móc mà không giải thích lớp triển khai kỹ thuật và tác động UX. [L1922–L2002]

### 3.2 Affordances, signifiers, constraints, conventions

Affordance nói đến hành động có thể làm; signifier truyền tín hiệu giúp nhận biết; constraint thu hẹp các hành động khả thi/được chấp nhận; convention là khuôn tương tác được xã hội học. Một hình thể vật lý dễ hiểu có thể tự mang signifier, nhưng một sản phẩm cũng có thể phát tín hiệu **sai**. [L2003–L2125; L2188–L2250]

### 3.3 Forcing functions, interlocks, lock-ins, lockouts

- **Forcing function:** cơ chế buộc hoàn thành điều kiện để tránh sai nguy hiểm.
- **Interlock:** ngăn chuỗi thao tác sai thứ tự; ví dụ thiết bị điện ngắt dòng khi mở nắp.
- **Lock-in:** ngăn dừng/bỏ giữa chừng để bảo vệ trạng thái, ví dụ hỏi lưu trước khi thoát app.
- **Lockout:** chặn truy cập hành động/trạng thái nguy hiểm, ví dụ cửa không được mở vào khu vực nguy hiểm.

Đây là phương án mạnh, không nên tùy tiện khóa người dùng trong luồng thương mại hoặc chặn thoát không có lý do. [L2126–L2187]

### 3.4 Conventions và thay đổi mô hình tương tác

Người dùng có kinh nghiệm sẽ dự đoán dựa vào quy ước cũ. Thang máy chọn tầng ở ngoài, rồi hệ thống chỉ định cabin có thể tối ưu vận hành nhưng khiến người mới ngỡ bên trong sẽ có bảng số. Khi đổi quy ước, cần signifier ngay thời điểm chuyển điểm quyết định, feedforward trước hành động và feedback trong suốt tiến trình; chỉ huấn luyện một lần thường chưa đủ. [L2188–L2250]

### 3.5 Case faucet / âm thanh

Vòi nước có thể cần kết hợp xoay/kéo/đẩy, lựa chọn nóng-lạnh, mạnh-yếu và bật-tắt. Khi chiều điều khiển không rõ hoặc không nhất quán, người dùng không thể tiên đoán nước ra. Âm thanh có thể là signifier/feedback hữu ích khi tầm nhìn bị chiếm hoặc đồ vật ở ngoài khung nhìn, nhưng cảnh báo âm thanh phải phân biệt được, không làm mệt mỏi, lưu ý việc máy móc quá im lặng có thể nguy hiểm (nhất là phương tiện di chuyển). [L2251–L2436]

## 4. Khi nào áp dụng

- Cài đặt quản trị, onboarding nhiều bước, upload, cấu hình liên kết, sản phẩm an toàn cao.
- Chức năng liên quan thanh toán, quyền truy cập, xóa dữ liệu, quyền riêng tư, thao tác không thể hoàn tác.
- Thay đổi hành vi người dùng đã quen, đặc biệt UI mới so với hệ cũ.
- Các môi trường cần tín hiệu âm thanh/rung ngoài hình ảnh.

## 5. Cách làm

1. Liệt kê **hành động đúng**, **hành động sai dễ mắc**, **hậu quả** và **trạng thái điều kiện**.
2. Phân loại từng biện pháp: hiển thị signifier, tạo mapping, ràng buộc vật lý/logic/ngữ nghĩa/văn hóa, hay forcing function.
3. Bắt đầu từ cách **gợi ý lựa chọn đúng**, chưa vội chặn; chặn mạnh khi rủi ro đủ lớn.
4. Nếu disabled: giải thích điều kiện kích hoạt; ưu tiên xử lý lỗi tại chỗ thay vì bẫy người dùng.
5. Với thay đổi quy ước: thiết kế chuyển tiếp, thông điệp đúng vị trí, trợ giúp tại thời điểm, trạng thái tương ứng.
6. Với sound/haptic: phân biệt thành công/cảnh báo/nguy hiểm; kiểm tra môi trường ồn, người giảm thính lực, chế độ im lặng và thay thế trực quan.
7. Dùng thử với người chưa từng sử dụng thiết bị; quan sát thao tác không cần người hướng dẫn.

## 6. Nên / Không nên

|Nên|Không nên|
|---|---|
|Giới hạn lựa chọn sai bằng logic và điều kiện rõ ràng.|Để lựa chọn sai trông y hệt lựa chọn đúng.|
|Để người dùng hiểu tại sao bị chặn và cách mở.|Dùng nút disabled vĩnh viễn không giải thích.|
|Xác nhận khi hành động khó khôi phục; có undo khi an toàn.|Bắt xác nhận liên tục các hành động ít rủi ro.|
|Thông báo trước sự thay đổi lớn về cách tương tác.|Đổi quy ước ngầm khiến người quen dùng hành động sai.|
|Kết hợp hình, lời, âm, rung tùy bối cảnh.|Chỉ dựa một tiếng bíp cho các trạng thái khác nhau.|

## 7. Ví dụ đúng/sai

**A. Chọn loại tệp:** sai — cho chọn mọi định dạng, upload xong mới báo không hỗ trợ; đúng — nêu trước `.pdf/.png` và kích thước tối đa, chọn lọc hợp lý khi có thể, báo lỗi tại tệp không hợp lệ.

**B. Thoát khi chưa lưu:** sai — bấm “Đóng” là mất công việc; đúng — tự lưu hoặc hỏi Lưu/Bỏ thay đổi/Ở lại, cảnh báo mức độ rủi ro tương ứng.

**C. Thay đổi thang máy:** sai — cabin không có nút tầng, không có chỉ dẫn ở hành lang; đúng — hướng dẫn chọn tầng *trước khi lên*, chỉ định cabin rõ, nhắc lại trạng thái tại cửa cabin.

**D. Bắt đầu cuộc họp:** sai — nút microphone bật nhưng hiện trạng thái im lặng mơ hồ; đúng — icon và nhãn On/Off rõ ràng, phản hồi cả hình và âm khi phù hợp, thông báo quyền hệ điều hành khi chưa cấp.

## 8. Lỗi thường gặp

- Lạm dụng constraint để ép hoàn thành mục tiêu kinh doanh (dark patterns).
- Coi mọi quy tắc dùng trước đây là trực giác phổ quát.
- Dùng interlock/lockout khiến không có lối thoát an toàn.
- Thông điệp hướng dẫn tách khỏi điều khiển cần giải thích.
- Chỉ kiểm tra trên thiết bị nhìn được UI; quên nghe/khả năng tiếp cận/môi trường.
- Đồng nhất ràng buộc logic giao diện với kiểm soát an ninh; server vẫn phải kiểm tra quyền và dữ liệu.

## 9. Ngoại lệ

- Phần mềm có giao thức kỹ thuật phức tạp có thể cần đào tạo; không vì vậy bỏ signifier.
- Khi khóa thao tác để an toàn, cần đường khôi phục có thẩm quyền, thông báo lý do, cơ chế thoát hiểm phù hợp.
- Chuẩn văn hóa mang tính thời điểm và địa phương; kiểm thử ngoài một nhóm mẫu.
- Âm thanh không phù hợp nơi cần yên tĩnh; tín hiệu thị giác/rung có thể thay thế, nhưng cảnh báo an toàn quan trọng cần thiết kế đa kênh.

## 10. Checklist

- [ ] Người dùng mới biết hành động nào hợp lệ không cần thử sai?
- [ ] Các giới hạn có cùng logic với nhiệm vụ thực?
- [ ] Nút bị chặn cho biết lý do và cách tiếp tục?
- [ ] Có ngăn thao tác nguy hiểm nhưng không ép buộc phi lý?
- [ ] Mọi thay đổi quy ước được thông báo ở đúng vị trí và thời điểm?
- [ ] Audio/visual/haptic truyền đúng mức độ ưu tiên và phù hợp khả năng tiếp cận?
- [ ] Việc sửa sai/thoát lỗi vẫn khả thi?

## 11. Tóm tắt

Đừng chỉ nói người dùng “không được làm X”; thiết kế hành động đúng trở nên rõ, hợp ngữ cảnh và dễ thực hiện, giới hạn đường sai, xây an toàn với khả năng phục hồi. Bốn constraints cùng affordances/signifiers/conventions làm nên discoverability.

## 12. Nguồn

L1891–2436: four constraints L1922–2002; doors/switches/activities L2025–2125; forcing functions L2126–2187; conventions/elevator L2188–2250; faucet L2251–2354; sound L2355–2436.
