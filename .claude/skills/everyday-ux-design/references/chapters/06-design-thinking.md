# Chương 6 — Design Thinking

> Nguồn: `../source/chapter-06.md`, L3189–L3751, trang 217–257. Trọng tâm: trước khi chọn giải pháp, hãy xác định **đúng vấn đề**; thực tế thiết kế diễn ra trong hệ ràng buộc và xung đột yêu cầu.

## 1. Vấn đề

Tổ chức đưa cho team một “vấn đề” đã được xác định sẵn và yêu cầu giải ngay; nhóm đôi khi tạo giải pháp xuất sắc cho điều **không phải nhu cầu gốc**. Khi có deadline, ngân sách và chính trị nội bộ, quy trình nghiên cứu–lặp lý tưởng không được phép diễn ra nguyên vẹn. [L3191–L3228; L3447–L3496]

## 2. Mục tiêu

- Phân biệt **problem finding** và **problem solving**, ưu tiên giải đúng nhu cầu.
- Tạo chu kỳ quan sát, tạo ý tưởng, prototype, test và chỉnh sửa dựa vào thực tế.
- Chấp nhận nhiều góc nhìn người dùng, người mua, vận hành, kỹ thuật, kinh doanh và cộng đồng.
- Thiết kế đủ đơn giản để *hiểu*, không ngộ nhận rằng mọi hệ thống có thể loại bỏ độ phức tạp cần thiết.

## 3. Lý thuyết

### 3.1 Solve the correct problem

Không nhận yêu cầu tính năng làm chân lý: người dùng có thể xin nút “In báo cáo” vì họ cần chia sẻ kết quả dễ hơn; in chỉ là một phương án. Truy mục tiêu sau cùng, xem lại bối cảnh thực và kiểm tra định nghĩa vấn đề trước khi thiết kế giải pháp. [L3203–L3228]

### 3.2 Double Diamond

**Diamond 1 — problem space:** mở rộng khám phá bằng quan sát/nghiên cứu → thu hẹp để định nghĩa vấn đề đúng.

**Diamond 2 — solution space:** mở rộng các phương án → thu hẹp qua prototype và đánh giá để chọn hướng phù hợp.

Bốn động tác **diverge/converge** tạo cân bằng khám phá và ra quyết định. Khung là mô hình nhận thức, không phải chuỗi họp cứng hoặc bảo đảm thành công. [L3229–L3247]

### 3.3 Human-Centered Design cycle

- **Observation:** nghiên cứu con người trong hoạt động thực; phỏng vấn chưa đủ, cần thấy hành vi/thói quen/khó khăn không được nói ra.
- **Idea generation:** phân kỳ giải pháp, tránh khóa vào ý tưởng đầu tiên.
- **Prototyping:** tạo bản mô phỏng đủ để thử giả thuyết, từ phác thảo, vật liệu thô đến mô phỏng tương tác.
- **Testing:** kiểm chứng bằng người và hoạt động đại diện nhóm mục tiêu, quan sát hành vi thay vì chỉ hỏi “thích không?”.
- **Iteration:** cập nhật mô hình vấn đề và giải pháp từ kết quả, lặp tới khi đủ tốt theo ràng buộc.

**Design research vs market research:** bổ trợ nhưng khác câu hỏi. Design nghiên cứu nhu cầu, cách dùng trong bối cảnh; marketing nghiên cứu thị trường, kênh, ưu tiên người mua và triển vọng kinh doanh. Không được gọi doanh số tiềm năng là bằng chứng sản phẩm usable. [L3248–L3382]

### 3.4 Activity-centered vs human-centered

HCD quan tâm đối tượng thực; khi thiết kế sản phẩm cho vô số nhóm người khác nhau, việc tập trung vào **activity** (hoạt động lớn, liên quan xã hội/mục tiêu) giúp duy trì tính phổ biến. Không đồng nhất activity với **task** (bước nhỏ). Ví dụ hoạt động đi mua sắm gồm lập danh sách, đi lại, tìm món, cân nhắc, mua, vận chuyển. Tối ưu click một task có thể phá trải nghiệm toàn hoạt động. [L3383–L3418]

### 3.5 Iterative vs linear, và Norman’s Law

Lý tưởng: làm mẫu nhanh, thử, sửa lặp. Thực tế: thời gian, ngân sách, lựa chọn đã phê duyệt, phối hợp phòng ban và ràng buộc kỹ thuật tạo tiến trình pha trộn, không chạy một đường thẳng hay vòng tròn sạch. **Norman’s Law** diễn tả việc dự án thường bước vào quy trình đã chịu chậm tiến độ/vượt ngân sách. Đừng hứa mọi dự án có thể thực hiện “đủ tất cả bước” mà không ưu tiên. [L3419–L3496]

### 3.6 Multiple conflicting requirements; thiết kế bao trùm

Một sản phẩm phải dung hòa người dùng cuối, người trả tiền, đội kỹ thuật, người duy trì, người sản xuất và tổ chức; không có “người dùng trung bình” đại diện hoàn hảo. Thiết kế cho những người có giới hạn vận động, giác quan, nhận thức, độ tuổi hoặc khả năng tiếp cận đặc thù có thể làm sản phẩm tốt cho nhiều người. Tuy nhiên thiết kế trợ giúp có thể bị kỳ thị khi hình thức khiến người sử dụng không muốn bị gắn nhãn. [L3497–L3594]

### 3.7 Complexity vs confusion

Độ phức tạp có thể bắt nguồn từ hoạt động thực, không thể cứ xóa tính năng mà “thiết kế tối giản” thành công. Khác biệt: **complexity** phản ánh số lượng/chất của việc cần giải quyết; **confusion** là người dùng không hiểu làm gì, vì sao. Mục tiêu quản lý độ phức tạp bằng cấu trúc, nhóm, mapping, quy ước và feedback. [L3595–L3608]

### 3.8 Standardization, conventions, deliberate difficulty

Tiêu chuẩn làm người dùng học một lần và chuyển khả năng sang nhiều sản phẩm; xây tiêu chuẩn lại có chi phí phối hợp, xung đột lợi ích và có thể bị công nghệ mới vượt qua. Thiết kế dễ dùng không luôn thích hợp: bảo mật, phòng truy cập, trò chơi/thử thách hoặc chống hành vi nguy hiểm có thể **cố ý làm một số thao tác khó**, nhưng phải xác định đúng đối tượng và mục đích. Không lấy mục này biện hộ cho dark patterns. [L3609–L3747]

## 4. Khi nào áp dụng

- Product discovery/định hình roadmap chưa rõ vấn đề.
- Đội ngũ có tranh chấp tính năng và định nghĩa thành công.
- UX sprint, dịch vụ đa bên, thiết kế sản phẩm cho nhiều nhóm người/khả năng tiếp cận.
- Dự án deadline nặng; cần chọn mức nghiên cứu/kiểm chứng khả thi và minh bạch rủi ro.
- Hệ thống dày chức năng cần giảm confusion mà không loại bỏ công việc cần thiết.

## 5. Cách làm — quy trình từ yêu cầu mơ hồ đến thiết kế kiểm chứng

1. **Intake:** ghi yêu cầu gốc, giả thuyết đang có, hạn chế thời gian/nguồn lực/định nghĩa thành công.
2. **Diverge problem:** quan sát các nhóm người và **activity** thực, phỏng vấn, kiểm tra hỗ trợ/ảnh chụp dữ liệu khi có, liệt kê nhiều nguyên nhân khả dĩ.
3. **Converge problem:** mô tả người dùng + ngữ cảnh + nhu cầu + hậu quả hiện tại + minh chứng + giả thuyết chưa xác thực. Nêu điều *chưa biết*.
4. **Diverge solutions:** phát triển vài phương án khác bản chất (đơn giản hóa thao tác, đổi quy trình, tự động hóa, trợ giúp/loại bỏ bước).
5. **Prototype:** chọn độ trung thực tối thiểu đủ thử câu hỏi; không vội vẽ pixel-perfect.
6. **Test:** đặt nhiệm vụ thực, quan sát người dùng đại diện, ghi dự đoán trước khi bấm, kết quả, chỗ nhầm, cảm xúc.
7. **Converge solution:** cân nhắc giá trị người dùng, rủi ro, khả thi, khả năng tiếp cận, chi phí, kinh doanh. Nêu tradeoff bằng chữ.
8. **Iterate:** sửa ít nhất điểm thất bại lớn nhất; nếu kết quả làm thay đổi định nghĩa vấn đề, quay lại khám phá.
9. **Handoff & follow-up:** bàn giao kịch bản trạng thái thường/lỗi, giả định, bằng chứng, tiêu chí kiểm chứng sau phát hành.

## 6. Nên / Không nên

|Nên|Không nên|
|---|---|
|Thẩm định bản chất vấn đề trước khi đóng khung giải pháp.|Nhận feature request là định nghĩa vấn đề cuối cùng.|
|Nghiên cứu hoạt động, bối cảnh, hành vi quan sát được.|Chỉ hỏi “muốn giao diện màu gì?”.|
|Phác nhiều giải pháp và test nhanh.|Chốt UI đắt tiền rồi mới hỏi người dùng.|
|Cân bằng nhiều ràng buộc và lưu lại đánh đổi.|Tuyên bố chỉ usability quan trọng, bỏ qua vận hành/chi phí.|
|Thiết kế hỗ trợ người có khả năng khác nhau.|Dùng hình mẫu “người trung bình” không có thật để loại ngoại lệ.|
|Dùng tiêu chuẩn giúp học nhanh nơi hợp lý.|Phá quy ước chỉ để trông sáng tạo.|

## 7. Ví dụ đúng/sai

**A. “Thêm bộ lọc”.** Sai — làm 25 filter vì sales yêu cầu; đúng — nghiên cứu vì sao người dùng không tìm thấy dữ liệu, có thể cần bộ lọc cơ bản, preset, tìm kiếm tốt, hoặc cấu trúc danh mục.

**B. Quy trình quản lý công việc.** Sai — tối ưu thời gian click “Hoàn thành” nhưng bỏ bước đánh giá/phê duyệt cốt lõi; đúng — phân tích cả activity (lập kế hoạch → phân công → theo dõi → báo cáo), giảm confusion tại mỗi handoff.

**C. Thiết bị dành cho người lớn tuổi.** Sai — tạo chế độ mặc định hình thức kỳ thị khiến người dùng né dùng; đúng — khả năng tiếp cận tích hợp tự nhiên, tùy chỉnh, test thái độ/ngữ cảnh.

**D. Sản phẩm nhiều chức năng.** Sai — giấu hết option cao cấp và khiến chức năng chuyên môn không thể tìm; đúng — nhóm theo activity/độ ưu tiên, progressive disclosure, tìm kiếm, lối tắt chuyên nghiệp.

## 8. Lỗi thường gặp

- Double Diamond bị biến thành lịch workshop không có bằng chứng thực.
- Coi user interview là nguồn sự thật tuyệt đối khi hành vi và lời nói khác nhau.
- Chỉ so sánh các phiên bản của **một** giải pháp đã chọn.
- Lấy cảm nhận thuận tiện trong test mẫu nhỏ làm bằng chứng tổng quát.
- Diễn giải “đơn giản là tốt” thành cắt bỏ độ phức tạp thiết yếu.
- Bỏ qua người mua, người bảo trì, nhóm dễ bị loại trừ, ràng buộc kỹ thuật.
- Không ghi giả định và rủi ro khi phải rút ngắn vòng lặp.

## 9. Ngoại lệ

- Không phải mọi việc đều cần nghiên cứu sâu; task nhỏ/rủi ro thấp có thể kiểm thử nhẹ, nhưng phải gọi rõ giới hạn bằng chứng.
- Với công nghệ mới chưa có người dùng thành thạo, hoạt động/mục tiêu và mô phỏng bối cảnh quan trọng hơn hỏi “anh/chị muốn tính năng nào?”.
- An toàn, pháp lý, quyền truy cập có thể yêu cầu bước xác nhận dù tăng ma sát.
- Có hoạt động như giải đố cần chủ ý khó; độ khó phải là một phần mục tiêu người dùng chứ không ép cho lợi ích nhà cung cấp.

## 10. Checklist

- [ ] Định nghĩa vấn đề dựa trên nhu cầu, không chỉ yêu cầu tính năng?
- [ ] Có bằng chứng/quan sát xác nhận hoạt động thực?
- [ ] Đã khảo sát nhiều giả thuyết vấn đề và nhiều phương án giải pháp?
- [ ] Prototype trả lời được câu hỏi thiết kế cần xác minh?
- [ ] Test với người/bối cảnh tương thích hoạt động?
- [ ] Chỉ rõ các tradeoffs, giới hạn dữ liệu và rủi ro chưa thử?
- [ ] Đã xét nhóm khác biệt về khả năng tiếp cận, văn hóa, kinh nghiệm?
- [ ] Phần phức tạp bắt buộc được **giải thích/điều hướng** thay vì xóa bừa?

## 11. Tóm tắt

Design thinking bắt đầu bằng hỏi “đúng vấn đề là gì?” rồi liên tục học từ con người, thử giải pháp, kiểm chứng và đổi hướng. Mô hình hai kim cương và vòng lặp HCD giúp làm việc có kỷ luật; thực tế doanh nghiệp đòi cân bằng tradeoff và hoạt động xuyên nhiều vai trò.

## 12. Nguồn

Chương L3189–3751: correct problem L3203–3228; double diamond L3229–3247; HCD L3248–3382; activity vs task L3383–3418; iterative + real-world L3419–3496; stakeholder/accessibility L3497–3594; complexity L3595–3608; standards L3609–3701; deliberate difficulty L3702–3747.
