# Chương 5 — Human Error? No, Bad Design

> Nguồn: `../source/chapter-05.md`, L2437–L3188, trang 162–216. Chủ đề: từ “ai sai?” chuyển thành “hệ thống nào khiến sai dễ xảy ra, khó phát hiện, khó sửa?” với ngoại lệ trách nhiệm cá nhân thật sự.

## 1. Vấn đề

Nhân viên bị phân tâm, phải nhớ nhiều việc, làm lâu, chịu áp lực tiến độ và dùng hệ thống khó hiểu; tai nạn xảy ra rồi tổ chức chỉ kết luận “human error”, thay người hoặc tăng đào tạo. Việc đổ lỗi có thể không chạm tới nguyên nhân gốc; cùng một điều kiện sẽ tạo sai sót lặp lại. Những hành động riêng lẻ thường nằm trong chuỗi điều kiện xã hội, tổ chức và kỹ thuật. [L2439–L2536]

## 2. Mục tiêu

- Giảm xác suất sai trước khi hành động, giúp phát hiện sớm khi sai và làm hậu quả có thể phục hồi.
- Điều tra hệ thống: giao diện, quy trình, tải chú ý, thời gian, huấn luyện, quy định, nguồn lực, văn hóa báo cáo.
- Xây **resilience**, khả năng hệ thống tiếp tục hoạt động và thích nghi trước biến động thực tế, thay vì giả định không ai mắc lỗi.

## 3. Lý thuyết và phân loại

### 3.1 Phân tích nguyên nhân gốc và Five Whys

**Root cause analysis** phải tìm điều kiện làm sai sót khả dĩ, thay vì dừng khi phát hiện người bấm nhầm. Hỏi “Tại sao?” lặp nhiều lớp; Five Whys là công cụ tìm hệ quả liên hoàn, nhưng không được gò ép đúng 5 lần hoặc giả định luôn có đúng *một* nguyên nhân. Trong hệ thống phức tạp, nhiều yếu tố độc lập có thể tương tác. [L2460–L2536]

### 3.2 Deliberate violations

Không phải mọi sai lệch đều vô ý: có **vi phạm cố ý**, đôi khi do áp lực văn hóa/khen thưởng tốc độ, điều kiện làm việc hoặc chấp nhận rủi ro. Phân tích động cơ và bối cảnh khác với slips/mistakes; không thể coi tất cả cùng một bệnh. [L2537–L2552]

### 3.3 Slips và mistakes — điểm phân biệt chính

- **Slip:** mục tiêu/kế hoạch cơ bản đúng, nhưng thao tác thực hiện sai hoặc không nhận biết đúng trạng thái. Ví dụ nhấn nút quen thuộc thay nút đúng. Thường xảy ra ở kỹ năng tự động, giai đoạn thực hiện/nhận biết/diễn giải.
- **Mistake:** chọn sai mục tiêu, sai kế hoạch, hiểu sai tình huống/quy tắc hoặc đánh giá sai kết quả. Ví dụ chọn phương án không phù hợp dựa trên mô hình sai. Thuộc tầng ra quyết định cao hơn.
- **Memory lapses** có thể tạo slip (quên một bước đang làm) hoặc mistake (quên mục tiêu/đánh giá trước đó). **Không** phân loại chỉ bằng hậu quả. [L2553–L2615]

### 3.4 Phân lớp slips

- **Capture slip:** hành động quen dùng gần đây chiếm chỗ chuỗi hành động mong muốn (ví dụ theo thói quen).
- **Description-similarity:** hành động lên vật/đối tượng tương tự mục tiêu (ví dụ tên hai người/biểu tượng gần giống).
- **Memory-lapse slip:** quên một thành phần hành động, bỏ vật quên tại thiết bị.
- **Mode-error slip:** cùng điều khiển nghĩa khác nhau theo chế độ; người dùng tưởng hệ thống ở mode khác (ví dụ nút trong chế độ xem/chỉnh sửa).

Chẩn đoán theo mô tả cụ thể trong tài liệu, đừng đoán từ một ảnh UI đơn lẻ. [L2616–L2701]

### 3.5 Phân lớp mistakes

- **Rule-based:** sử dụng quy tắc sai hoặc áp dụng quy tắc đúng cho bối cảnh sai.
- **Knowledge-based:** phải suy luận tình huống mới nhưng mô hình kiến thức chưa đủ hoặc hiểu sai.
- **Memory-lapse mistake:** quên mục tiêu, kế hoạch, đánh giá trước, dẫn đến quyết định không đúng.

Đặt dấu hiệu nhận biết và hướng dẫn tương ứng: rule-based cần dấu hiệu phân biệt trường hợp và hậu quả; knowledge-based cần model/phản hồi để suy luận; lapse cần ghi nhận trạng thái/ngữ cảnh. [L2702–L2791]

### 3.6 Áp lực xã hội, tổ chức và checklist

Yêu cầu phi thực tế, đa nhiệm, không dám báo lỗi, tiến độ khẩn làm tăng nguy cơ. **Checklists** hữu ích cho chuỗi phức tạp/ngắt quãng, đặc biệt khi nhiều người phải phối hợp, nhưng checklist kém thiết kế cũng có thể bị bỏ qua. Phân biệt checklist kiểm tra quan trọng với hình thức bắt tick nhiều lần. [L2792–L2853]

### 3.7 Báo cáo lỗi không trừng phạt và sửa tận gốc

Nhân viên cần cơ chế báo gần sai/điều kiện nguy hiểm để tổ chức học được mà không gây che giấu. Sách thảo luận jidoka (dừng khi thấy bất thường), poka-yoke (thiết kế ngừa sai) và hệ thống báo cáo an toàn hàng không. Điều quan trọng là giải quyết *hệ thống*, không chỉ sửa con người. [L2854–L2887]

### 3.8 Phát hiện sai và thiên lệch hậu nghiệm

Slips thường dễ phát hiện hơn mistakes vì hành động khác dự định, nhưng UI có thể che trạng thái hoặc thiếu tín hiệu. **Hindsight bias**: sau khi tai nạn xảy ra, nguyên nhân nhìn như hiển nhiên; không dùng cái nhìn sau sự kiện để kết luận người dùng trước đó hẳn phải biết. Tái dựng những thông tin họ thực sự có tại thời điểm quyết định. [L2888–L2935]

### 3.9 Thiết kế cho lỗi: phòng ngừa → phát hiện → phục hồi

- **Constraints, forcing functions, mappings, signifiers:** giảm lỗi ở nguồn.
- **Undo / rollback / version history:** giảm tác hại, giữ khả năng quay lại; không phải tác vụ nào cũng đảo ngược được.
- **Confirmations:** chỉ dùng theo mức nguy cơ, tránh xác nhận lặp khiến người dùng click máy móc; cảnh báo đặt đúng thời điểm và phải giải thích hậu quả.
- **Sensibility checks:** kiểm tra độ hợp lý nội dung/chênh lệch lớn bất thường, không chỉ valid syntax.
- **Thử nghiệm mode, ngắt quãng, nhập liệu thiếu, lệnh trùng, recovery:** không dừng ở happy path.

Sách mô tả **Swiss cheese model** của James Reason: các lớp phòng vệ có lỗ hổng; tai nạn xảy ra khi chúng thẳng hàng. Đừng chỉ thêm một lớp cảnh báo rồi tin hệ thống an toàn tuyệt đối. [L2936–L3112]

### 3.10 Khi thiết kế tốt vẫn chưa đủ; automation paradox

Norman **không** phủ nhận con người có khi có lỗi/trách nhiệm thật: xem mục riêng 'When People Really Are at Fault'. Hệ thống phức tạp đòi resilience: giám sát, phục hồi, phát hiện dấu hiệu. Tự động hóa giúp làm nhiệm vụ ổn định nhưng khiến người điều hành ít thực hành, mất nhận thức tình trạng, gặp khó khi tiếp quản ở tình huống hiếm và nguy hiểm — nghịch lý tự động hóa. [L3113–L3188]

## 4. Khi nào áp dụng

- Thanh toán, chuyển tiền, điều khiển hệ thống, xóa tài khoản, bệnh viện, xe, hệ thống công nghiệp.
- Product gây mất dữ liệu, đơn hàng trùng, phân quyền nhầm, cấu hình bất thường.
- Sản phẩm có nhiều chế độ, phím tắt, người dùng làm việc trong môi trường dễ gián đoạn.
- Tổ chức báo cáo lỗi thấp bất thường nhưng khi phỏng vấn nhiều người đều từng gặp.

## 5. Cách làm cho UX audit / incident review

1. Mô tả **sự kiện không quy kết**: người dùng muốn gì, làm gì, thực tế đã xảy ra, hậu quả.
2. Phân loại sơ bộ: slip/mistake/vi phạm cố ý/không đủ bằng chứng.
3. Vẽ timeline với dữ kiện **đã thấy tại thời điểm**; ghi rõ mode, trạng thái, áp lực, deadline, gián đoạn.
4. Five Whys đa nhánh: điều kiện UI, quy trình, doanh nghiệp, kỹ thuật, giám sát; tránh dừng “người dùng bất cẩn”.
5. Đề xuất lớp phòng vệ: giảm hành động nhầm → phân biệt trạng thái → phát hiện bất thường → khôi phục → học từ lỗi.
6. Xếp hạng theo **mức độ hậu quả, tần suất, khả năng phát hiện, khả năng đảo ngược**; ưu tiên lỗi khó khôi phục.
7. Test kịch bản rủi ro ở mức an toàn có kiểm soát: nhấn lặp, mạng chậm, mode sai, thay đổi quyền, tiếp tục sau 10 phút gián đoạn.
8. Đo tỷ lệ phát hiện/khôi phục, lỗi lặp và hậu quả; không chỉ số lần bấm sai.

## 6. Nên / Không nên

|Nên|Không nên|
|---|---|
|Dùng từ trung tính, điều tra môi trường gây lỗi.|Đổ lỗi cho “người dùng ngu/không chịu đọc”.|
|Bảo vệ dữ liệu bằng undo, autosave, phiên bản.|Để một nút nhầm phá hủy vĩnh viễn dữ liệu.|
|Phân biệt rõ các mode và điều kiện nguy hiểm.|Dùng cùng điều khiển hai nghĩa nhưng không có chỉ báo trạng thái.|
|Hỏi vì sao và kiểm chứng nguyên nhân đa lớp.|Dừng phân tích ở con người cuối cùng bấm nút.|
|Báo cáo sự cố để học, có quy trình khắc phục.|Khuyến khích che giấu lỗi vì sợ bị phạt.|
|Kiểm tra thông tin hợp lý, phát hiện bất thường.|Đánh đồng dữ liệu đúng cú pháp với quyết định hợp lý.|

## 7. Ví dụ đúng/sai

**A. Hệ thống hóa đơn:** sai — hai nút `Tạo mới` và `Tạo & gửi` gần giống, không cảnh báo, lỗi gửi hai lần khi chậm. Đúng — nhãn khác biệt/hậu quả rõ, trạng thái gửi, cơ chế chống gửi trùng, lịch sử/thu hồi nếu quy trình cho phép. Chẩn đoán slip/mode/error recovery.

**B. Xóa bản ghi:** sai — xoá không undo; đúng — chuyển thùng rác có khôi phục và mô tả thời gian giữ. Nếu xóa vĩnh viễn theo chính sách, cần cảnh báo đặc biệt, giới hạn quyền và xác nhận phù hợp.

**C. Dashboard cảnh báo:** sai — tất cả 30 sự kiện đều bíp như cấp cứu; đúng — phân cấp, nhóm và xác định nguồn, hành động đề xuất, ghi sự kiện, có phương án dự phòng.

**D. Chốt ca:** sai — một người buộc xác nhận đã hoàn thành tất cả dù thông tin phân tán; đúng — checklist theo vai trò, trạng thái xác minh, lưu dấu và bàn giao rõ.

## 8. Lỗi thường gặp

- Nhầm một sự kiện có hậu quả xấu với sai lầm cá nhân cố ý.
- Từ khóa “human error” thay thế phân tích nguyên nhân thực.
- Confirm mọi thao tác dẫn đến click-through, cảnh báo vô hiệu.
- Không có rollback vì muốn “đơn giản UI”.
- Chỉ thiết kế để lỗi không xảy ra, không thiết kế khi lỗi *vẫn* xảy ra.
- Tự động hóa tất cả rồi bỏ giám sát/khả năng tiếp quản.
- Lạm dụng Five Whys như công thức một nguyên nhân, bỏ qua các lớp rủi ro đồng thời.

## 9. Ngoại lệ

- Có trường hợp người thực hiện cố tình vi phạm hoặc thiếu tuân thủ; cần thẩm định dựa trên dữ kiện. Hệ thống vẫn nên kiểm tra khả năng phòng ngừa.
- Undo không khả thi với tác vụ vật lý/đã chuyển cho bên ngoài; thiết kế kiểm tra trước và khắc phục sau.
- Cảnh báo nghiêm trọng có thể phải làm gián đoạn nhiệm vụ; phân cấp độ ưu tiên theo rủi ro.
- Hệ thống tự động hóa có giới hạn người-máy cụ thể; không thể hứa chế độ fallback nếu chưa thiết kế/kiểm tra.

## 10. Checklist

- [ ] Phân biệt slip, mistake, violation và chưa đủ bằng chứng?
- [ ] Điều tra gốc vượt qua lỗi thao tác bề mặt?
- [ ] Đánh giá deadline, gián đoạn, mode, môi trường, văn hóa tổ chức?
- [ ] Có signal giảm nhầm trước khi làm?
- [ ] Hệ thống phát hiện/cho biết sai kịp thời?
- [ ] Có rollback, undo hoặc phương án phục hồi đáng tin cậy?
- [ ] Cảnh báo chỉ xuất hiện khi giá trị vượt chi phí gây nhiễu?
- [ ] Ghi nhận near-miss và cải thiện thường xuyên?
- [ ] Khi tự động hóa mất hiệu lực, có phương án tiếp quản thực tế?

## 11. Tóm tắt

Sai sót là thuộc tính có thể dự đoán của hệ thống người–máy; thiết kế phải cho phép mắc lỗi nhỏ mà không dẫn đến thiệt hại lớn. Phân loại đúng lỗi, điều tra nhiều tầng, ưu tiên phát hiện và khôi phục, xây resilience; tránh đơn giản hóa trách nhiệm cá nhân.

## 12. Nguồn

Chương L2437–3188: root cause/Five Whys L2460–2536; deliberate violations L2537–2552; slips/mistakes L2553–2791; social pressure/checklists L2792–2853; reporting L2854–2887; detecting/hindsight L2888–2935; designing for error/Swiss cheese L2936–3112; resilience/automation L3113–3188.
