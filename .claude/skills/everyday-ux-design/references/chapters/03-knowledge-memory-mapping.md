# Chương 3 — Knowledge in the Head and in the World

> Nguồn: `../source/chapter-03.md`, dòng gốc L1237–L1890, trang 74–122. Đọc chương này khi làm UI đòi nhớ nhiều, hướng dẫn, biểu mẫu dài, quy trình gián đoạn, bảng điều khiển hoặc đa văn hóa.

## 1. Vấn đề

Người dùng thường vận hành chính xác mà **không nhớ đầy đủ** tính năng, hình dạng, quy tắc. Khi thiết kế đòi họ ghi nhớ những chi tiết tùy tiện, hiệu suất giảm mạnh. Tác giả nhắc đến chiếc xe Saab mà muốn rút chìa phải về số lùi: không có chỉ báo, người dùng không thể tự phát hiện. Ví dụ khác: người dùng nhận diện đồng xu trong đời sống nhưng không thể tái hiện chính xác hoa văn trên đồng xu. [L1237–L1280]

## 2. Mục tiêu

Không bắt người dùng giữ trong đầu mọi tri thức; phân bổ thông tin giữa trí nhớ và môi trường đúng **thời điểm, vị trí, ngữ cảnh**. Đạt “nhớ đủ để phân biệt hành động thích hợp”, thay vì yêu cầu nhớ tuyệt đối. Tận dụng ràng buộc và cấu trúc nhiệm vụ để làm lựa chọn trở nên rõ ràng.

## 3. Lý thuyết chi tiết

### 3.1 Tri thức trong đầu / ngoài thế giới

- **Knowledge in the head:** ký ức, kỹ năng, thói quen, mô hình người dùng học được. Nhanh khi thành thạo nhưng cần thời gian học và dễ sai/lãng quên.
- **Knowledge in the world:** thông tin có thể nhìn/nghe/đọc ngay tại môi trường: nhãn, bảng điều khiển, gợi ý đúng chỗ, thứ tự các lựa chọn, tình trạng hiện tại, nhắc việc.
- Hai loại bổ trợ nhau; một UI tốt cho phép người mới dựa nhiều hơn vào thế giới, còn người chuyên nghiệp dựa nhiều hơn vào trí nhớ và thói quen. **Không** có “cách tối ưu bất biến” cho mọi bối cảnh. [L1259–L1280; L1705–L1734]

### 3.2 Bốn lý do hành vi chính xác dù kiến thức không chính xác

1. Kết hợp tri thức trong đầu và trên thế giới.
2. Hiếm khi cần độ chính xác/độ đầy đủ tuyệt đối: chỉ cần đủ phân biệt lựa chọn.
3. Ràng buộc tự nhiên của môi trường thu hẹp lựa chọn.
4. Ràng buộc và quy ước văn hóa học được hướng dẫn hành động.

**Giới hạn quan trọng:** môi trường đổi hoặc số lựa chọn đổi có thể khiến tri thức “đủ dùng” trở nên không đủ; lúc đó phát sinh lỗi không ngờ. [L1259–L1380]

### 3.3 Memory / trí nhớ

- **Working/short-term memory:** giữ thông tin hiện tại, dung lượng hạn chế, dễ bị phá khi ngắt quãng. Đừng ép người dùng nhớ mã, số hoặc lựa chọn từ trang trước sang trang sau.
- **Long-term memory:** kiến thức tích lũy, hình thành liên hệ có nghĩa; cần học và gợi lại. Không giả định mọi người có cùng kinh nghiệm.
- **Arbitrary knowledge** (không có cấu trúc/ý nghĩa dễ hiểu) khó học hơn kiến thức có liên kết, ví dụ chuỗi lệnh tùy ý khác với quy tắc có logic.
- Tài liệu bàn trí nhớ, cấu trúc/chunking và mô hình gần đúng; tránh suy diễn một con số “giới hạn mục” là chân lý cho mọi trường hợp. [L1381–L1562]

### 3.4 Approximate models & trí nhớ phù hợp đời thật

Tính nhẩm gần đúng, quy tắc “đủ tốt” hoặc mô hình thực dụng có thể tối ưu thời gian hơn thuật toán đầy đủ. Người dùng có thể dùng kỹ năng thủ tục thay cho nhớ các thông số chi tiết. Không ép dùng công thức lý tưởng khi nhiệm vụ chỉ cần kết quả đủ tin cậy; nhưng với yêu cầu chính xác tài chính/an toàn cần kiểm chứng. [L1563–L1644]

### 3.5 Reminding / prospective memory

Nhớ một việc phải làm **trong tương lai** là loại nhiệm vụ khác với nhận diện/nhớ kiến thức. Một lời nhắc chỉ hữu dụng nếu xuất hiện **đúng lúc có thể hành động**. Gắn cảnh báo, nhật ký, thông tin trạng thái với hành động tiếp theo; hỗ trợ quay lại sau khi bị gián đoạn. [L1645–L1704]

### 3.6 Tradeoff giữa world và head

Tri thức bên ngoài dễ đọc, dễ học nhưng phụ thuộc vào sự hiện diện và có thể làm màn hình rối hoặc chậm người dùng thành thạo. Tri thức bên trong cho thao tác nhanh nhưng khó cho người mới, khó chia sẻ và dễ bị quên. Giải pháp thường là **progressive disclosure** và **recognition + shortcuts**: hiển thị lựa chọn cho người mới, hỗ trợ phím tắt/quy trình thành thạo có thể khám phá khi cần; đây là suy luận thực hành từ tradeoff của sách, không phải tên bộ quy tắc nguyên văn. [L1705–L1734]

### 3.7 Memory in multiple heads/devices

Hệ thống cộng tác có thể phân tán tri thức giữa người và thiết bị; nhóm người nhắc nhau hoặc dữ liệu được ghi lại phục vụ bộ nhớ chung. Cần lưu được trạng thái, người chịu trách nhiệm, lịch sử/giải thích quyết định, tránh thông tin sống trong đầu một cá nhân. [L1735–L1776]

### 3.8 Natural mapping, văn hóa, point of view

Mapping giữa vị trí điều khiển và đối tượng cần phản ánh cấu trúc thực, ví dụ nút bếp đặt theo bố cục các bếp thay vì hàng nút không đánh dấu. Tuy nhiên cái gọi là “tự nhiên” phụ thuộc ngôn ngữ, chiều đọc, ẩn dụ chuyển động và đối tượng được xem là di chuyển (nội dung hay khung nhìn). Sách minh họa bằng điều khiển slide và cuộn nội dung: các cách diễn giải trái chiều **đều có thể hợp lý** khi mental model khác nhau. Khi bản địa hóa hoặc thiết kế gesture, phải kiểm tra thực tế. [L1777–L1890]

## 4. Khi nào áp dụng

- Người dùng chuyển màn hình phải nhớ lựa chọn/mã/đơn hàng của màn trước.
- Tác vụ dài, mất mạng, bị gián đoạn, thao tác định kỳ nhưng thưa.
- Sản phẩm có hai nhóm người mới/chuyên gia; cần lối tắt mà không giấu cơ bản.
- Giao diện quốc tế, lịch/timeline, slide, cuộn, hướng chuyển động, ánh xạ vật lý.
- Onboarding/trợ giúp/biểu mẫu nhiều điều kiện và quy tắc.

## 5. Cách làm

1. Liệt kê toàn bộ kiến thức người dùng cần tại mỗi bước và đánh dấu: **nhìn thấy trực tiếp** hay **phải nhớ**.
2. Xóa nhu cầu nhớ vô ích: hiện lựa chọn trước đó, tóm tắt, breadcrumbs, giá trị đã nhập, hướng dẫn đặt cạnh điều khiển.
3. Biến chuỗi tùy tiện thành quan hệ có nghĩa bằng nhóm, tên, hình, thứ tự, ví dụ.
4. Thiết kế checklist/nhắc theo sự kiện khi người dùng thực sự có thể giải quyết, không gửi hàng loạt thông báo khó hành động.
5. Đảm bảo trạng thái và lịch sử không mất khi ngắt quãng, hỗ trợ resume.
6. Xét tốc độ người quen dùng: bộ lọc đã lưu, template, phím tắt tùy chọn; giữ đường thao tác hiển thị cho người mới.
7. Test cross-cultural bằng đối tượng từ những vùng ngôn ngữ/đọc khác nhau; đừng dựa vào câu “tự nhiên phải như vậy”.

## 6. Nên / Không nên

|Nên|Không nên|
|---|---|
|Hiện mã đơn hàng và trạng thái ở nơi người dùng cần dùng.|Yêu cầu ghi nhớ mã từ màn hình trước.|
|Dùng lựa chọn/nhãn gợi nhớ và quan hệ không gian.|Bắt học bảng ký hiệu tùy ý.|
|Tóm tắt các lựa chọn trong checkout trước xác nhận.|Ẩn toàn bộ dữ liệu đã nhập khi sang bước khác.|
|Nhắc theo bối cảnh, có hành động trong thông báo.|Nhắc quá sớm, quá muộn hoặc không làm gì được.|
|Kiểm thử cách hiểu mapping đa văn hóa.|Giả định đọc trái-phải, lên-xuống luôn mang một nghĩa.|

## 7. Ví dụ đúng/sai

**A. Xác nhận giao hàng:** sai — người dùng phải nhớ địa chỉ và khung giờ từ bước 2; đúng — trang xác nhận hiển thị đầy đủ địa chỉ, giờ, phí, nút chỉnh sửa tại chỗ.

**B. Chế độ chỉnh ảnh:** sai — 8 icon vô danh, chức năng nhớ bằng vị trí; đúng — icon kèm tooltip/nhãn, nhóm thao tác có nghĩa, recent actions, phím tắt cho chuyên gia.

**C. Nhắc thanh toán:** sai — popup khi người dùng không thể trả, đóng là mất; đúng — nhắc trước hạn với lý do, số tiền, “Thanh toán” / “Nhắc lại” và trạng thái xử lý.

**D. Bảng điều khiển bếp:** sai — nút xếp thành hàng trong khi vùng bếp xếp hình vuông không thể suy ra; đúng — nút có bố cục khớp các vùng, dùng chỉ báo trạng thái nhiệt.

## 8. Lỗi thường gặp

- Đồng nhất trí nhớ nhận diện với khả năng hồi tưởng chính xác.
- Bắt người dùng nhớ thay vì cho nhận ra ngay trong ngữ cảnh.
- Coi shortcut chuyên gia là cách dùng duy nhất.
- Khẳng định mọi biểu tượng/chiều chuyển động là phổ quát.
- Thêm quá nhiều nhắc nhở đến mức tín hiệu quan trọng mất giá trị.
- Đơn giản hóa quá mức ở nhiệm vụ yêu cầu độ chính xác cao.

## 9. Ngoại lệ

- Công việc chuyên biệt lặp hàng trăm lần/ngày cần tối ưu thao tác chuyên gia mà không xóa đường dễ học.
- Hiển thị thông tin bảo mật chỉ nơi và lúc được phép; world knowledge không đồng nghĩa phơi bày dữ liệu nhạy cảm.
- Tác vụ an toàn cao cần checklist bắt buộc, dù người dùng đã nhớ.
- Ký ức và ánh xạ ảnh hưởng bởi khả năng tiếp cận, kinh nghiệm, ngôn ngữ và văn hóa.

## 10. Checklist

- [ ] Tôi đã xóa yêu cầu ghi nhớ không cần thiết giữa các bước?
- [ ] Trạng thái/ngữ cảnh đủ để quay lại sau gián đoạn?
- [ ] Lựa chọn dễ **nhận ra**, không đòi nhớ bí mật hoặc quy tắc tùy tiện?
- [ ] Thông tin xuất hiện đúng lúc/đúng vị trí hành động?
- [ ] Có đường học dễ và đường nhanh cho người thành thạo?
- [ ] Mapping đã được kiểm chứng với nhiều mental models và văn hóa?
- [ ] Nếu hành động quan trọng, độ chính xác/kiểm tra đã tương ứng rủi ro?

## 11. Tóm tắt

Thiết kế không phải thi trí nhớ. Dùng cấu trúc thế giới để dẫn đường cho người dùng, tận dụng trí nhớ khi có lợi, và thiết kế nhắc việc đúng bối cảnh. Mapping “tự nhiên” cần xét văn hóa và ẩn dụ.

## 12. Nguồn

Chương gốc L1237–1890: bốn lý do nhớ không chính xác vẫn hành động tốt L1259–1280; world knowledge L1281–1380; memory L1381–1562; approximate models L1563–1644; reminders L1645–1704; tradeoff L1705–1734; shared memory L1735–1776; mappings/culture L1777–1890.
