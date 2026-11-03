# Phần I — Bắt đầu thiết kế từ con số 0

## Bài 1 — Bắt đầu từ một tính năng, không phải “khung app”

### Vấn đề
Người mới thường mở Figma rồi lập tức hỏi: thanh điều hướng đặt trên hay bên trái, logo ở đâu, nội dung full-width hay nằm trong container. Những câu hỏi này đến quá sớm vì bạn chưa biết sản phẩm thực sự cần hiển thị và cho phép người dùng làm gì.

### Mục tiêu
Thiết kế **một luồng chức năng cụ thể** trước, để các quyết định về navigation và bố cục tổng thể xuất hiện từ nhu cầu thật thay vì từ tưởng tượng.

### Lý thuyết
Một sản phẩm không phải là một “vỏ giao diện”; nó là tập hợp các tính năng. Khi chưa thiết kế một vài tính năng, bạn chưa có đủ dữ liệu để biết cấu trúc app nên như thế nào. Vì thế, điểm xuất phát tốt nhất là một hành động người dùng cần hoàn thành.

### Khi nào áp dụng
- Khi bắt đầu một sản phẩm mới.
- Khi bạn nhìn màn hình trắng và không biết đặt gì ở đâu.
- Khi team đang tranh luận quá lâu về navbar/sidebar nhưng chưa có màn hình chức năng thực tế.

### Cách làm
1. Viết một câu: **“Người dùng cần làm việc gì?”**
2. Chọn một tác vụ nhỏ nhưng có giá trị, ví dụ: tìm chuyến bay, tạo hóa đơn, thêm thành viên, đặt lịch.
3. Liệt kê dữ liệu đầu vào, kết quả đầu ra và hành động chính.
4. Thiết kế đúng phần đó trước.
5. Sau khi có 2-3 tính năng, mới quyết định app cần sidebar, tab, top navigation hay cách tổ chức khác.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Bắt đầu bằng một tác vụ cụ thể | Bắt đầu bằng việc “design toàn bộ app” |
| Liệt kê input, output, action | Chọn layout vì “app khác cũng làm vậy” |
| Để nhu cầu chức năng dẫn dắt cấu trúc | Chốt navigation khi chưa biết các màn hình chính |

### Ví dụ đúng/sai
**Sai:** “Tôi sẽ làm dashboard. Trước tiên vẽ sidebar 240px, logo, menu 8 mục, rồi tính sau.”

**Đúng:** “Người dùng cần tìm đơn hàng theo mã. Màn hình đầu tiên cần ô tìm kiếm, bộ lọc trạng thái, danh sách kết quả và hành động xem chi tiết.”

### Lỗi thường gặp
- Nhầm “layout” với “sản phẩm”.
- Dành nhiều giờ cho header, icon, logo trước khi luồng chính tồn tại.
- Thiết kế menu với hàng loạt mục giả định, sau đó phải làm lại khi tính năng thay đổi.

### Ngoại lệ
Nếu bạn đang **mở rộng một sản phẩm đã có design system và navigation ổn định**, bạn có thể dùng shell hiện có ngay. Nhưng phần nội dung của tính năng mới vẫn nên được thiết kế từ nhu cầu thực tế.

### Checklist
- [ ] Tôi có thể mô tả tác vụ người dùng bằng một câu.
- [ ] Tôi biết input nào cần nhập.
- [ ] Tôi biết kết quả nào cần hiển thị.
- [ ] Tôi biết hành động chính là gì.
- [ ] Tôi chưa chốt layout toàn app chỉ vì thói quen.

### Tóm tắt
**Thiết kế hành vi trước, thiết kế cái vỏ sau.** Một tính năng thật cho bạn dữ liệu tốt hơn hàng chục phỏng đoán về layout.

---

## Bài 2 — Chi tiết để sau

### Vấn đề
Người mới rất dễ mắc kẹt ở font nào đẹp hơn, shadow 10% hay 15%, icon nào “xịn”, màu xanh nào hợp. Những chi tiết này tiêu tốn năng lượng trong lúc câu hỏi quan trọng hơn — cấu trúc và ưu tiên — vẫn chưa được giải quyết.

### Mục tiêu
Tách giai đoạn **tìm giải pháp** khỏi giai đoạn **trau chuốt thị giác**.

### Lý thuyết
Ở giai đoạn sớm, bạn cần thử nhiều ý tưởng nhanh. Độ trung thực thấp giúp não tập trung vào bố cục, thứ bậc và chức năng. Thiết kế xám còn buộc spacing, kích thước và contrast phải tự làm tốt nhiệm vụ trước khi màu sắc xuất hiện.

### Khi nào áp dụng
- Khi bắt đầu một màn hình hoặc feature mới.
- Khi bạn chỉnh đi chỉnh lại màu/font nhưng layout vẫn chưa ổn.
- Khi một phương án chưa được xác nhận nhưng mockup đã quá chi tiết.

### Cách làm
1. Phác bằng giấy, wireframe hoặc khối xám.
2. Chỉ dùng vài mức chữ và vài mức xám.
3. Chốt: nhóm nào ở đâu, nội dung nào quan trọng, action nào chính.
4. Khi cấu trúc ổn, mới thêm font, màu, icon, shadow và micro-details.
5. Xem wireframe là đồ dùng tạm: quyết định xong thì chuyển sang bản thật.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng grayscale ở giai đoạn đầu | Dùng palette hoàn chỉnh ngay từ phút đầu |
| Thử nhiều layout thô | Đánh bóng một phương án chưa chắc đúng |
| Xem wireframe là công cụ suy nghĩ | Xem wireframe như sản phẩm phải “hoàn hảo” |

### Ví dụ đúng/sai
**Sai:** Form đăng ký chưa biết cần 3 hay 7 trường nhưng đã mất 30 phút chọn shadow, gradient và icon mắt.

**Đúng:** Trước tiên dùng khối xám để kiểm tra thứ tự trường, nhóm thông tin, CTA và thông báo lỗi. Sau khi luồng ổn mới làm visual.

### Lỗi thường gặp
- Đồng nhất “high fidelity” với “tiến độ”.
- Dành quá nhiều thời gian cho mockup không tương tác.
- Dùng màu để cứu hierarchy yếu.

### Ngoại lệ
Nếu bạn đang làm **một component nhỏ trong design system đã chín**, chi tiết visual có thể được áp dụng ngay vì hệ thống đã xác định phần lớn quyết định.

### Checklist
- [ ] Màn hình có hiểu được khi bỏ hết màu không?
- [ ] Người dùng có nhìn ra action chính không?
- [ ] Tôi đã thử hơn một cách bố trí chưa?
- [ ] Chi tiết tôi đang chỉnh có ảnh hưởng đến cấu trúc không?

### Tóm tắt
**Đừng giải bài toán pixel khi bài toán cấu trúc còn chưa xong.**

---

## Bài 3 — Đừng thiết kế quá nhiều trước khi làm thật

### Vấn đề
Cố thiết kế toàn bộ sản phẩm, mọi trạng thái và mọi edge case trước khi có thứ gì chạy thật khiến bạn phải giải quá nhiều bài toán bằng tưởng tượng.

### Mục tiêu
Làm việc theo chu kỳ ngắn: **thiết kế phiên bản nhỏ → làm thật → dùng thử → sửa → tiếp tục**.

### Lý thuyết
Một giao diện hoạt động sẽ bộc lộ những vấn đề mà mockup tĩnh khó cho thấy. Việc cố dự đoán mọi tình huống trước thường làm tăng độ phức tạp và làm trì hoãn giá trị có thể giao sớm.

### Khi nào áp dụng
- Khi sản phẩm còn mới hoặc yêu cầu chưa ổn định.
- Khi feature có nhiều edge case chưa rõ.
- Khi team đang “vẽ hết rồi mới code”.

### Cách làm
1. Chọn **phiên bản hữu ích nhỏ nhất** của tính năng.
2. Bỏ các phần nice-to-have khỏi bản đầu.
3. Thiết kế đủ để triển khai.
4. Làm bản chạy được.
5. Quan sát vấn đề thật rồi quay lại thiết kế.
6. Lặp lại cho tính năng tiếp theo.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Ship phiên bản nhỏ nhưng dùng được | Giữ feature lại vì một phần phụ chưa làm được |
| Thiết kế theo vòng lặp | Thiết kế 100 màn hình trước khi thử |
| Ưu tiên chức năng cốt lõi | Ngầm hứa trong UI những thứ chưa thể xây |

### Ví dụ đúng/sai
**Sai:** Hệ thống bình luận chưa thể upload file nhưng UI đã thiết kế khu vực attachment như tính năng bắt buộc, khiến cả module bị trì hoãn.

**Đúng:** Ship bình luận văn bản trước. Attachment trở thành vòng sau.

### Lỗi thường gặp
- Đưa “tương lai” vào UI hiện tại.
- Thiết kế mọi trạng thái hiếm trước khi luồng chính hoạt động.
- Nghĩ rằng làm mockup nhiều sẽ loại bỏ hết bất ngờ khi code.

### Ngoại lệ
Các lĩnh vực có ràng buộc nghiêm ngặt như thanh toán, bảo mật, pháp lý hoặc quy trình an toàn có thể cần phân tích trạng thái và lỗi kỹ hơn trước khi triển khai. Tuy vậy vẫn nên chia nhỏ phạm vi thay vì cố hoàn thiện cả sản phẩm cùng lúc.

### Checklist
- [ ] Bản đầu có nhỏ nhất mà vẫn hữu ích không?
- [ ] Có phần nice-to-have nào đang chặn việc giao không?
- [ ] UI có hứa một chức năng team chưa chắc làm được không?
- [ ] Tôi có kế hoạch thử bản chạy thật sớm không?

### Tóm tắt
**Thiết kế đủ để làm, làm đủ để học, rồi thiết kế tiếp.**

---

## Bài 4 — Chọn “tính cách” cho giao diện

### Vấn đề
Một UI có thể đúng chức năng nhưng vẫn “không ra chất”: quá vui với sản phẩm tài chính, quá lạnh với sản phẩm cộng đồng, hoặc mỗi khu vực mang một phong cách khác nhau.

### Mục tiêu
Xác định cảm giác chủ đạo của sản phẩm và thể hiện nó nhất quán bằng typography, màu sắc, bo góc và ngôn ngữ.

### Lý thuyết
“Tính cách” không phải thứ mơ hồ hoàn toàn. Nó được truyền qua những quyết định cụ thể:
- **Font:** serif thường gợi cảm giác cổ điển/trang trọng; sans bo tròn có thể vui hơn; sans trung tính ít áp đặt cá tính.
- **Màu:** màu khác nhau tạo cảm giác khác nhau; quan trọng là chọn hướng phù hợp thay vì tin tuyệt đối vào “tâm lý học màu”.
- **Border radius:** góc vuông thường nghiêm túc hơn; bo nhiều có thể thân thiện/vui hơn.
- **Ngôn ngữ:** câu chữ trang trọng hay gần gũi thay đổi cảm nhận mạnh không kém màu và font.

### Khi nào áp dụng
- Khi bắt đầu định hướng visual cho sản phẩm.
- Khi UI trông “lắp ghép”.
- Khi nhiều designer tạo màn hình không đồng nhất.

### Cách làm
1. Chọn 2-3 tính từ mô tả cảm giác: ví dụ **tin cậy, rõ ràng, bình tĩnh**.
2. Xem các sản phẩm mà nhóm người dùng mục tiêu thường dùng.
3. Chọn font, màu chính, radius và tone of voice cùng phục vụ tính cách đó.
4. Dùng nhất quán xuyên suốt component.
5. Tham khảo thị trường nhưng tránh sao chép trực tiếp đối thủ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Viết ra tính cách bằng từ cụ thể | Nói “đẹp, hiện đại” nhưng không định nghĩa |
| Giữ radius, tone, font nhất quán | Chỗ vuông, chỗ bo tròn tùy hứng |
| Quan sát sản phẩm người dùng quen thuộc | Copy nguyên visual của đối thủ |

### Ví dụ đúng/sai
**Sai:** Ứng dụng quản trị doanh nghiệp dùng font vui nhộn, màu neon, nút pill rất lớn và copy hài hước ở mọi bước xác nhận quan trọng.

**Đúng:** Chọn sans dễ đọc, radius vừa phải, màu nhấn tiết chế và câu chữ rõ ràng để tạo cảm giác chuyên nghiệp nhưng không lạnh lùng.

### Lỗi thường gặp
- Nghĩ tính cách chỉ nằm ở màu.
- Chọn font “lạ” nhưng khó đọc.
- Copywriting không cùng giọng với visual.
- Trộn nhiều kiểu radius.

### Ngoại lệ
Một sản phẩm có thể có **khu vực khác mood** (ví dụ trang marketing vui hơn dashboard quản trị), nhưng sự khác biệt phải có chủ ý và vẫn chia sẻ nền tảng hệ thống.

### Checklist
- [ ] Tôi có 2-3 tính từ mô tả tính cách không?
- [ ] Font hỗ trợ cảm giác đó và vẫn dễ đọc không?
- [ ] Radius nhất quán không?
- [ ] Cách viết câu chữ có cùng tone không?
- [ ] Thiết kế có quá giống đối thủ không?

### Tóm tắt
**Tính cách UI là kết quả của nhiều quyết định nhỏ nhưng nhất quán.**

---

## Bài 5 — Giới hạn lựa chọn bằng hệ thống

### Vấn đề
Nếu mỗi lần thiết kế bạn đều được chọn từ hàng triệu màu, hàng nghìn font và vô hạn giá trị pixel, bạn sẽ mất thời gian cho những khác biệt rất nhỏ.

### Mục tiêu
Biến các quyết định lặp lại thành **một tập lựa chọn hữu hạn**.

### Lý thuyết
Hệ thống làm giảm “decision fatigue”. Thay vì hỏi “13 hay 14px?”, bạn chỉ chọn từ scale đã định nghĩa. Khi các lựa chọn đủ khác nhau, bạn có thể so sánh và loại trừ nhanh.

### Khi nào áp dụng
- Gần như mọi dự án có hơn vài màn hình.
- Khi UI xuất hiện nhiều giá trị gần giống nhau.
- Khi nhiều người cùng thiết kế/coding.

### Cách làm
1. Định nghĩa trước scale cho font size, spacing, radius, shadow và màu.
2. Khi cần chọn, thử một giá trị bạn đoán phù hợp.
3. So sánh với giá trị ngay nhỏ hơn và lớn hơn.
4. Loại các phương án rõ ràng không hợp.
5. Nếu một quyết định lặp lại nhiều lần, biến nó thành token/quy ước.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Chọn từ scale hữu hạn | Mở color picker mỗi lần cần một màu |
| Tạo quy tắc sau khi thấy quyết định lặp lại | Cố định nghĩa mọi token trước khi bắt đầu |
| Dùng process of elimination | Tinh chỉnh 1px hàng chục lần |

### Ví dụ đúng/sai
**Sai:** Icon có các kích thước 17, 19, 22, 25, 27px tùy màn hình.

**Đúng:** Dùng scale 12, 16, 24, 32px; thử 16 và hai giá trị lân cận để chọn.

### Lỗi thường gặp
- Tạo hệ thống quá chặt khiến không có lựa chọn phù hợp.
- Có token nhưng vẫn dùng giá trị tùy ý ngoài hệ thống.
- Tạo hệ thống khổng lồ trước khi có nhu cầu thật.

### Ngoại lệ
Một giá trị ngoài hệ thống có thể hợp lý cho **trường hợp đặc biệt có lý do rõ ràng**. Nếu ngoại lệ xuất hiện nhiều, hãy xem xét bổ sung token thay vì tiếp tục phá quy ước.

### Checklist
- [ ] Font size có scale không?
- [ ] Spacing có scale không?
- [ ] Màu có palette/shade định sẵn không?
- [ ] Radius và shadow có số lượng hữu hạn không?
- [ ] Có giá trị lẻ nào chỉ vì “kéo cho vừa mắt” không?

### Tóm tắt
**Thiết kế nhanh hơn khi bạn không phải phát minh lại mọi con số.**

---
