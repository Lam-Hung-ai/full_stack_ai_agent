# Hướng dẫn thiết kế UI cho người bắt đầu từ số 0

> Tài liệu này là bản hướng dẫn thực hành được viết lại từ **toàn bộ PDF Refactoring UI (218 trang)** của Adam Wathan & Steve Schoger. Nội dung được diễn giải bằng tiếng Việt cho người chưa có nền tảng UI, tập trung vào cách ra quyết định và cách áp dụng trong thực tế thay vì học thuộc các “mẹo làm đẹp”.
>
> Mỗi bài giữ cùng một cấu trúc: **Vấn đề → Mục tiêu → Lý thuyết → Khi nào áp dụng → Cách làm → Nên / Không nên → Ví dụ đúng/sai → Lỗi thường gặp → Ngoại lệ → Checklist → Tóm tắt**.

---

## Cách dùng tài liệu

Nếu bạn mới hoàn toàn, hãy học tuần tự từ **Bài 1 đến Bài 52**. Nếu bạn đang sửa một màn hình cụ thể, có thể nhảy đến nhóm phù hợp:

- **Bắt đầu thiết kế:** Bài 1-5
- **Hierarchy / thứ bậc thị giác:** Bài 6-13
- **Layout và spacing:** Bài 14-19
- **Typography:** Bài 20-28
- **Màu sắc:** Bài 29-35
- **Chiều sâu:** Bài 36-40
- **Hình ảnh:** Bài 41-44
- **Finishing touches:** Bài 45-50
- **Tiếp tục nâng trình:** Bài 51-52

---

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
# Phần II — Hierarchy: làm cho người dùng biết điều gì quan trọng

## Bài 6 — Không phải mọi phần tử đều quan trọng như nhau

### Vấn đề
Một UI thường trở nên “ồn” khi tiêu đề, số liệu, mô tả, nút, link và icon đều cố gây chú ý ngang nhau. Người dùng phải tự tìm xem nên nhìn đâu trước.

### Mục tiêu
Tạo **visual hierarchy**: mức độ quan trọng của nội dung phải nhìn thấy được ngay bằng mắt.

### Lý thuyết
Một giao diện dễ đọc thường có 3 tầng:
1. **Primary:** điều người dùng cần thấy hoặc làm trước.
2. **Secondary:** thông tin hỗ trợ.
3. **Tertiary:** thông tin ít quan trọng nhưng vẫn cần tìm được.

Hierarchy không chỉ đến từ font size. Nó được tạo bằng kích thước, độ đậm, contrast, màu sắc, khoảng cách và vị trí.

### Khi nào áp dụng
- Khi màn hình có nhiều thành phần.
- Khi người khác nhìn UI và hỏi “tôi nên bấm cái nào?”.
- Khi mọi thứ trông như cùng một khối thông tin.

### Cách làm
1. Liệt kê các phần tử trên màn hình.
2. Gắn nhãn Primary / Secondary / Tertiary.
3. Làm nổi bật primary.
4. Chủ động làm nhẹ secondary và tertiary.
5. Kiểm tra bằng cách nheo mắt hoặc zoom nhỏ: thứ quan trọng nhất có còn nổi bật không?

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Chỉ có một vài điểm nhấn | Làm tất cả đều bold và đậm |
| De-emphasize nội dung phụ | Chỉ biết “thêm màu” để làm nổi bật |
| Tạo thứ tự đọc rõ | Để người dùng tự giải mã |

### Ví dụ đúng/sai
**Sai:** Card đơn hàng: mã đơn, tên khách, ngày, trạng thái, tổng tiền và 4 action đều cùng 16px semibold, màu đen.

**Đúng:** Tổng tiền và mã đơn nổi bật; tên khách và trạng thái mức trung bình; ngày tạo và metadata nhẹ hơn; chỉ action chính có visual mạnh.

### Lỗi thường gặp
- “Mọi thứ quan trọng” nên không có gì thật sự nổi bật.
- Dùng quá nhiều màu nhấn.
- Tạo hierarchy khác nhau giữa các card giống nhau.

### Ngoại lệ
Màn hình dữ liệu chuyên sâu như bảng giao dịch có thể cần mật độ thông tin cao. Hierarchy lúc này tinh tế hơn nhưng vẫn phải tồn tại.

### Checklist
- [ ] Tôi biết phần tử số 1 trên màn hình là gì.
- [ ] Có phân tầng primary / secondary / tertiary.
- [ ] Người dùng nhìn nhanh vẫn hiểu đâu là nội dung chính.
- [ ] Nội dung phụ không cạnh tranh với action chính.

### Tóm tắt
**Một UI trông “được thiết kế” khi mức độ quan trọng được thể hiện rõ, không phải khi mọi thứ được trang trí nhiều.**

---

## Bài 7 — Kích thước không phải công cụ hierarchy duy nhất

### Vấn đề
Nếu chỉ dùng font size để tạo hierarchy, tiêu đề sẽ phình quá lớn còn nội dung phụ sẽ nhỏ đến mức khó đọc.

### Mục tiêu
Kết hợp **size + weight + color/contrast** để tạo thứ bậc mà vẫn giữ khả năng đọc.

### Lý thuyết
Một đoạn chữ có thể nổi bật vì:
- lớn hơn,
- đậm hơn,
- tối hơn,
- nằm ở vị trí ưu tiên hơn.

Vì vậy không cần tăng size quá mạnh. Nội dung hỗ trợ cũng không cần thu nhỏ quá mức; có thể chỉ giảm contrast.

### Khi nào áp dụng
- Khi headline quá lớn so với card.
- Khi text phụ phải xuống dưới 12-14px chỉ để “nhẹ đi”.
- Khi card có nhiều cấp thông tin.

### Cách làm
1. Giữ body text ở kích thước đọc thoải mái.
2. Dùng 2 mức weight chính: normal và semibold/bold.
3. Dùng 2-3 mức màu chữ: primary, secondary, tertiary.
4. Chỉ tăng size khi thật sự cần.
5. Tránh font weight quá mảnh cho UI nhỏ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng màu mềm hơn cho metadata | Thu metadata xuống quá nhỏ |
| Dùng semibold cho nội dung chính | Cho mọi text đều bold |
| Dùng 2-3 mức màu chữ | Tạo 7 mức xám rất khó phân biệt |

### Ví dụ đúng/sai
**Sai:** Tiêu đề card 32px, body 14px, chú thích 10px.

**Đúng:** Tiêu đề 20px semibold, body 16px normal, chú thích 14px với màu nhẹ hơn.

### Lỗi thường gặp
- Đồng nhất “quan trọng” với “to”.
- Dùng font weight dưới 400 cho text nhỏ.
- Giảm size và giảm contrast cùng lúc quá nhiều khiến nội dung biến mất.

### Ngoại lệ
Hero marketing có thể dùng chênh lệch size rất lớn để tạo hiệu ứng. Nhưng trong UI thao tác hằng ngày, hierarchy thường nên tiết chế hơn.

### Checklist
- [ ] Có text nào quá nhỏ chỉ vì muốn giảm nhấn không?
- [ ] Có headline nào quá lớn so với không gian không?
- [ ] Tôi có thể dùng weight hoặc color thay vì tăng size không?

### Tóm tắt
**Hierarchy tốt là sự phối hợp, không phải cuộc thi xem chữ nào to nhất.**

---

## Bài 8 — Không dùng chữ xám “nhạt” theo kiểu máy móc trên nền màu

### Vấn đề
Trên nền trắng, chữ xám nhạt có thể tạo cảm giác secondary. Nhưng trên nền màu, cùng cách làm thường khiến chữ trông bẩn, mờ hoặc như disabled.

### Mục tiêu
Giảm emphasis bằng **contrast phù hợp với nền**, không phải bằng một màu xám dùng ở mọi nơi.

### Lý thuyết
Điều tạo cảm giác “nhẹ hơn” là **độ tương phản thấp hơn so với nền**. Vì thế trên nền xanh, màu chữ secondary nên thường là một màu cùng họ với nền nhưng sáng/tối vừa đủ, thay vì lấy xám trung tính hoặc trắng giảm opacity một cách máy móc.

### Khi nào áp dụng
- Banner, card màu, sidebar màu.
- Text trên background có hình/pattern.
- Badge, status block, hero section.

### Cách làm
1. Xác định màu nền.
2. Giữ hue gần với màu nền nếu phù hợp.
3. Điều chỉnh saturation/lightness để giảm contrast.
4. Kiểm tra text không trông “disabled”.
5. Với ảnh/pattern, tránh opacity thấp khiến nền xuyên qua chữ gây khó đọc.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Chọn màu secondary riêng cho nền màu | Dùng một màu #999 cho mọi nền |
| Giữ chữ có màu “thật” | Dùng trắng opacity thấp ở mọi trường hợp |
| Kiểm tra readability | Chỉ nhìn đẹp ở screenshot tĩnh |

### Ví dụ đúng/sai
**Sai:** Sidebar xanh đậm, text phụ là `rgba(255,255,255,0.45)` và gần như biến mất trên pattern.

**Đúng:** Dùng một shade xanh rất sáng/ít bão hòa nhưng opaque, vẫn nhẹ hơn text chính và ổn định trên nền.

### Lỗi thường gặp
- Nghĩ “secondary = grey”.
- Dùng opacity làm giải pháp mặc định.
- Không kiểm tra contrast trong trạng thái hover/disabled.

### Ngoại lệ
Opacity vẫn có thể dùng nếu background đơn giản và bạn kiểm soát tốt kết quả, nhưng không nên là phản xạ mặc định.

### Checklist
- [ ] Màu chữ phụ có hòa với nền không?
- [ ] Chữ có trông như disabled không?
- [ ] Nền ảnh/pattern có xuyên qua text gây nhiễu không?
- [ ] Text chính vẫn nổi bật hơn rõ ràng không?

### Tóm tắt
**Hãy giảm contrast có chủ ý, không phải cứ “làm xám đi”.**

---

## Bài 9 — Muốn một thứ nổi bật hơn? Hãy làm những thứ xung quanh nhẹ đi

### Vấn đề
Bạn có thể đã tăng màu, tăng weight, thêm background nhưng phần tử quan trọng vẫn chưa nổi vì các phần tử khác cũng quá mạnh.

### Mục tiêu
Tạo điểm nhấn bằng **de-emphasis tương đối**.

### Lý thuyết
Emphasis là quan hệ giữa các phần tử. Nếu mọi thứ cùng đậm, tăng thêm một chút cho phần tử chính không tạo nhiều khác biệt. Ngược lại, giảm contrast của phần tử cạnh tranh có thể làm điểm chính nổi lên ngay mà không cần “trang trí” thêm.

### Khi nào áp dụng
- Active navigation chưa rõ.
- Sidebar đang cạnh tranh với content.
- Có quá nhiều nút/card cùng độ nổi.

### Cách làm
1. Xác định phần tử phải thu hút mắt.
2. Liệt kê các phần tử đang cạnh tranh.
3. Giảm contrast, background hoặc weight của phần tử phụ.
4. So sánh lại trước/sau.
5. Chỉ tăng emphasis của phần tử chính nếu vẫn cần.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Làm item inactive nhẹ hơn | Thêm highlight ngày càng mạnh cho active item |
| Cho sidebar hòa vào page background nếu phù hợp | Đóng hộp mọi khu vực bằng nền riêng |
| Tạo contrast tương đối | Tạo “đấu trường màu sắc” |

### Ví dụ đúng/sai
**Sai:** Tab active màu xanh; tab inactive vẫn đen đậm semibold nên active không rõ.

**Đúng:** Tab active đen/xanh đậm; tab inactive xám vừa, weight normal.

### Lỗi thường gặp
- Cứ thêm border, shadow, color để nhấn.
- Không xem toàn màn hình, chỉ nhìn component riêng lẻ.
- Làm secondary quá mờ đến mức khó dùng.

### Ngoại lệ
Thông tin cảnh báo/critical có thể cần emphasis cao độc lập với hierarchy bình thường.

### Checklist
- [ ] Tôi đã thử giảm nhấn phần tử xung quanh chưa?
- [ ] Active/inactive có phân biệt bằng mắt không?
- [ ] Secondary vẫn đủ đọc và đủ discoverable không?

### Tóm tắt
**Đôi khi cách nhanh nhất để tăng âm lượng cho một tiếng là giảm âm lượng của phần còn lại.**

---

## Bài 10 — Label là phương án cuối, không phải mặc định

### Vấn đề
Hiển thị dữ liệu theo mẫu `Label: Value` cho mọi trường khiến tất cả thông tin có trọng lượng ngang nhau và giao diện trông như bảng dữ liệu thô.

### Mục tiêu
Dùng **format, context và câu chữ** để giảm label thừa, nhờ đó hierarchy rõ hơn.

### Lý thuyết
Nhiều dữ liệu tự nói lên ý nghĩa qua định dạng:
- email nhìn là biết email,
- số tiền nhìn là biết giá,
- số điện thoại có format đặc trưng.

Nếu cần label, label thường chỉ là **supporting content**; giá trị mới là điều người dùng quan tâm. Tuy nhiên ở trang thông tin dày đặc, người dùng có thể quét theo label, lúc đó label cần nổi hơn.

### Khi nào áp dụng
- Card hồ sơ, sản phẩm, bất động sản.
- Dashboard số liệu.
- Màn hình chi tiết nhiều field.

### Cách làm
1. Hỏi: “Không có label, người dùng có hiểu giá trị không?”
2. Nếu có, bỏ label.
3. Nếu gần hiểu, thử gộp thành cụm tự nhiên: `12 sản phẩm còn lại`, `3 phòng ngủ`.
4. Nếu vẫn cần label, làm label nhẹ hơn value.
5. Nếu người dùng chủ yếu tìm theo label (ví dụ thông số kỹ thuật), cho label đủ nổi để scan.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| `3 phòng ngủ` | `Phòng ngủ: 3` nếu ngữ cảnh đã rõ |
| Làm value nổi hơn label trong dashboard | Cho label và value cùng weight |
| Nhấn label trong bảng thông số nếu người dùng tìm theo tên thuộc tính | Luôn coi value là thứ phải nổi nhất |

### Ví dụ đúng/sai
**Sai:** `Tên: Nguyễn An`, `Chức vụ: Designer`, `Email: an@...`, `Điện thoại: ...` đều cùng style.

**Đúng:** `Nguyễn An` nổi bật, `Product Designer` phía dưới, email và số điện thoại nhẹ hơn; không cần “Tên/Chức vụ/Email”.

### Lỗi thường gặp
- Bỏ label ở nơi dữ liệu mơ hồ.
- Dùng label quá đậm.
- Không phân biệt trang “đọc giá trị” với trang “tìm thuộc tính”.

### Ngoại lệ
Form nhập liệu là câu chuyện khác: label có vai trò accessibility và hướng dẫn nhập, không nên áp dụng quy tắc này một cách máy móc.

### Checklist
- [ ] Label nào có thể bỏ mà không mất nghĩa?
- [ ] Có thể gộp label vào câu tự nhiên không?
- [ ] Nếu giữ label, hierarchy có đúng không?
- [ ] Người dùng quét theo label hay theo value?

### Tóm tắt
**Đừng biến mọi dữ liệu thành cặp “nhãn: giá trị”. Hãy để ngữ cảnh làm việc khi có thể.**

---

## Bài 11 — Tách semantic hierarchy khỏi visual hierarchy

### Vấn đề
Trên web, bạn có thể dùng `h1`, `h2`, `h3` đúng nghĩa semantic nhưng vô thức style chúng theo kích thước mặc định “h1 phải rất to, h2 nhỏ hơn...”, dẫn đến UI application có title quá lớn.

### Mục tiêu
Dùng semantic markup cho cấu trúc/accessibility, nhưng **style theo vai trò thị giác thực tế**.

### Lý thuyết
Một section title có thể là heading về mặt tài liệu nhưng chỉ đóng vai trò label hỗ trợ trong UI. Semantic và visual không bắt buộc phải có cùng độ lớn.

### Khi nào áp dụng
- Settings page, dashboard, admin UI.
- Màn hình có nhiều section title.
- Khi heading chiếm quá nhiều attention so với nội dung.

### Cách làm
1. Chọn HTML element theo nghĩa và accessibility.
2. Xác định vai trò thị giác của nó: primary hay supporting.
3. Style size/weight/contrast theo vai trò đó.
4. Nếu nội dung tự giải thích, heading có thể rất nhỏ hoặc thậm chí ẩn thị giác nhưng vẫn giữ semantic phù hợp.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| `h1` semantic nhưng 16-20px nếu phù hợp UI | “h1 luôn 48px” |
| Ưu tiên nội dung chính | Để section title cướp sự chú ý |
| Giữ markup có nghĩa | Chọn thẻ chỉ vì style mặc định |

### Ví dụ đúng/sai
**Sai:** Trang “Quản lý tài khoản” có title 48px trong khi form mới là nơi người dùng cần tập trung.

**Đúng:** Title 18-20px, rõ nhưng không lấn át form.

### Lỗi thường gặp
- Đồng nhất hierarchy tài liệu với hierarchy thị giác.
- Dùng heading tag chỉ để lấy font size mặc định.
- Bỏ semantic hoàn toàn để “trông đẹp”.

### Ngoại lệ
Bài viết dài, documentation và landing page thường có mối liên hệ chặt hơn giữa document hierarchy và visual hierarchy.

### Checklist
- [ ] Heading có đúng semantic không?
- [ ] Heading có đang lớn hơn vai trò thực tế không?
- [ ] Nội dung chính có được ưu tiên thị giác không?

### Tóm tắt
**Chọn element vì ý nghĩa; chọn style vì hierarchy.**

---

## Bài 12 — Cân bằng “độ nặng” và contrast

### Vấn đề
Icon đặc, chữ bold hoặc border dày có thể trông quá nặng dù kích thước không lớn. Ngược lại, border mảnh màu sáng có thể gần như biến mất.

### Mục tiêu
Cân bằng thị giác bằng cách điều chỉnh **weight** và **contrast** như hai biến bù trừ.

### Lý thuyết
Phần tử chiếm nhiều “diện tích mực” thường cảm giác nặng hơn. Khi không thể thay đổi weight (ví dụ icon dạng solid), giảm contrast có thể làm nó nhẹ đi. Khi một phần tử quá nhẹ vì contrast thấp, tăng thickness có thể giúp nó rõ hơn mà không cần dùng màu tối gắt.

### Khi nào áp dụng
- Icon cạnh text.
- Divider/border.
- Navigation có nhiều icon.
- Component trông “nặng” dù màu đã đúng.

### Cách làm
1. So sánh diện tích thị giác của icon/text/border.
2. Nếu icon quá mạnh: dùng màu mềm hơn.
3. Nếu border quá mờ: tăng từ 1px lên 2px trước khi làm màu tối hơn.
4. Kiểm tra tổng thể chứ không chỉ giá trị CSS.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Icon nặng → contrast thấp hơn | Icon và text cùng màu đen tuyệt đối |
| Border nhạt → có thể dày hơn | Luôn làm border tối hơn |
| Cân bằng bằng nhiều biến | Chỉ chỉnh size |

### Ví dụ đúng/sai
**Sai:** Sidebar icon solid màu đen nằm cạnh label normal, khiến mắt nhìn icon trước text.

**Đúng:** Giữ label đậm hơn, icon dùng màu xám nhẹ hơn.

### Lỗi thường gặp
- Nghĩ hai phần tử cùng màu là “nhất quán” dù weight khác nhau.
- Border 1px quá nhạt nhưng tiếp tục làm nhạt hơn vì sợ “noisy”.
- Tăng size để sửa vấn đề vốn là contrast.

### Ngoại lệ
Icon trạng thái quan trọng có thể cần contrast cao hơn text cạnh nó để báo lỗi/cảnh báo.

### Checklist
- [ ] Icon có đang lấn text không?
- [ ] Border có thấy đủ mà không gắt không?
- [ ] Tôi đã thử đổi contrast trước khi đổi size chưa?

### Tóm tắt
**Weight và contrast có thể bù trừ nhau. Hãy cân bằng cảm giác, không chỉ thông số.**

---

## Bài 13 — Thiết kế action theo hierarchy trước, semantics sau

### Vấn đề
Người mới thường nghĩ: “Delete là nguy hiểm nên phải đỏ to”, “Publish là tích cực nên phải xanh”, “Edit là action nên phải có button”. Kết quả là mọi action đều có visual mạnh và màn hình trở nên bận.

### Mục tiêu
Thể hiện mức độ ưu tiên của action trước; semantics như destructive/success chỉ là một lớp thông tin bổ sung.

### Lý thuyết
Phần lớn màn hình có:
- **1 primary action**,
- một vài **secondary actions**,
- vài **tertiary actions**.

Primary nên rõ nhất; secondary rõ nhưng không nổi bằng; tertiary discoverable nhưng nhẹ. Một destructive action không tự động trở thành primary chỉ vì nó nguy hiểm.

### Khi nào áp dụng
- Card có nhiều nút.
- Form có Save/Cancel/Delete.
- Màn hình quản trị.

### Cách làm
1. Hỏi: người dùng thường đến màn hình này để làm gì?
2. Đặt action đó là primary.
3. Secondary dùng outline/low-contrast style.
4. Tertiary có thể là text/link style.
5. Destructive action chỉ dùng “đỏ mạnh” khi nó thực sự là action chính trong bước xác nhận.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| 1 primary rõ ràng | 3 nút solid cùng cường độ |
| Delete nhẹ ở màn hình chính, mạnh trong confirmation | Delete đỏ to ở mọi nơi |
| Secondary/tertiary có style nhẹ hơn | Dùng màu semantics để quyết định toàn bộ hierarchy |

### Ví dụ đúng/sai
**Sai:** Card sản phẩm có `Xóa` đỏ solid, `Sửa` xanh solid, `Xuất bản` xanh lá solid — cả ba cùng nổi.

**Đúng:** `Xuất bản` là primary; `Sửa` secondary; `Xóa` là text/action nhẹ. Khi mở modal xác nhận xóa, `Xóa` mới trở thành primary destructive.

### Lỗi thường gặp
- Nút nào cũng solid.
- Dùng màu đỏ làm “còi báo động” quá sớm.
- Không phân biệt tần suất và mục tiêu chính.

### Ngoại lệ
Một workflow khẩn cấp có thể có destructive action là action chính ngay trên màn hình, nhưng đây phải là quyết định theo ngữ cảnh, không phải quy tắc màu.

### Checklist
- [ ] Có đúng một primary action không?
- [ ] Secondary có rõ nhưng nhẹ hơn không?
- [ ] Tertiary có thể tìm thấy mà không chiếm attention không?
- [ ] Destructive action chỉ mạnh khi đúng ngữ cảnh không?

### Tóm tắt
**Màu của action không quyết định độ quan trọng; mục tiêu của người dùng mới quyết định.**

---
# Phần III — Layout và spacing: làm giao diện dễ hiểu bằng khoảng trống

## Bài 14 — Bắt đầu với nhiều khoảng trắng hơn bạn nghĩ

### Vấn đề
Khi UI chật, phản xạ thông thường là thêm từng chút margin/padding cho đến khi “đỡ xấu”. Cách này thường chỉ đạt mức vừa đủ không tệ, chứ chưa chắc tạo cảm giác sạch và rõ.

### Mục tiêu
Dùng whitespace như một công cụ tổ chức nội dung, không phải phần diện tích “bị lãng phí”.

### Lý thuyết
Một cách hiệu quả là làm ngược: **bắt đầu rộng rãi hơn mức cần thiết rồi giảm dần**. Việc nhận ra “quá nhiều khoảng trống” thường dễ hơn nhận ra “thiếu một chút khoảng trống”.

### Khi nào áp dụng
- Form, card, settings page.
- Khi UI trông chật hoặc khó quét.
- Khi các nhóm thông tin dính vào nhau.

### Cách làm
1. Tăng padding của container và khoảng cách giữa các nhóm.
2. Nhìn toàn bộ màn hình chứ không chỉ component riêng lẻ.
3. Giảm dần những chỗ thật sự quá rộng.
4. Giữ khoảng cách trong cùng nhóm nhỏ hơn khoảng cách giữa các nhóm.
5. Kiểm tra ở nhiều kích thước màn hình.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Bắt đầu rộng rồi thu lại | Bắt đầu chật rồi “vá” thêm margin |
| Dùng whitespace để nhóm nội dung | Dùng border cho mọi nhóm |
| Xem khoảng trống là một thành phần thiết kế | Cố lấp kín màn hình |

### Ví dụ đúng/sai
**Sai:** Card xác thực hai bước có title, mô tả, input và nút gần sát nhau vì “tiết kiệm không gian”.

**Đúng:** Title và phần form được tách bằng khoảng rõ; các input có nhịp; CTA không dính vào field cuối.

### Lỗi thường gặp
- Đồng nhất “gọn” với “chật”.
- Chỉ tăng padding trong component mà không xem spacing giữa các component.
- Dùng whitespace không theo hệ thống.

### Ngoại lệ
Dashboard cần hiển thị nhiều dữ liệu cùng lúc có thể chủ động dùng mật độ cao hơn. Đây là quyết định có lý do, không phải mặc định.

### Checklist
- [ ] Các nhóm nội dung có đủ “không khí” không?
- [ ] Khoảng giữa nhóm lớn hơn khoảng trong nhóm không?
- [ ] Tôi có đang lấp chỗ trống chỉ vì nó trống không?
- [ ] Mật độ hiện tại có phục vụ nhiệm vụ không?

### Tóm tắt
**Khoảng trắng không phải phần còn dư; nó là công cụ làm rõ cấu trúc.**

---

## Bài 15 — Xây một hệ spacing và sizing

### Vấn đề
Nếu mỗi margin, padding, width đều được chỉnh bằng cảm giác từng pixel, UI sẽ chậm làm và thiếu nhất quán.

### Mục tiêu
Dùng một **scale hữu hạn** cho khoảng cách và kích thước.

### Lý thuyết
Một scale tuyến tính kiểu “cứ bội số 4px” chưa chắc đủ để giảm lựa chọn, vì ở kích thước lớn, chênh 4px gần như không đáng kể. Scale tốt thường có khoảng cách nhỏ ở đầu dưới và tăng dần rõ rệt ở đầu trên. Phần sách gợi ý lấy **16px làm base** và xây các bội/số phần của nó.

Ví dụ scale thực dụng trong phần đã đọc:

`4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 192, 256, 384, 512, 640, 768`

Không phải mọi dự án phải dùng đúng scale này; điểm quan trọng là bạn có **một hệ** thay vì các con số tùy hứng.

### Khi nào áp dụng
- Từ những màn hình đầu của sản phẩm.
- Khi có nhiều margin/padding gần nhau như 19, 21, 23, 26px.
- Khi designer và developer thường xuyên tranh luận về số pixel.

### Cách làm
1. Chọn base dễ làm việc, ví dụ 16px.
2. Tạo các mức nhỏ gần nhau hơn và mức lớn cách nhau rõ hơn.
3. Dùng scale cho padding, gap, margin, width/height khi phù hợp.
4. Khi một giá trị không đủ, thử mức kế tiếp thay vì chỉnh +1px.
5. Chỉ thêm token khi có nhu cầu lặp lại thật.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| 16 → 24 → 32 khi tăng spacing | 21 → 22 → 23 → 24 để “tìm đúng số” |
| Scale có bước nhảy rõ | Scale có quá nhiều giá trị sát nhau |
| Dùng token lặp lại | Nhập con số riêng cho từng màn hình |

### Ví dụ đúng/sai
**Sai:** Card A padding 22px, Card B 25px, Card C 27px dù cùng cấp.

**Đúng:** Cùng dùng `24px`; component lớn hơn có thể dùng `32px`.

### Lỗi thường gặp
- Tạo scale nhưng không dùng nhất quán.
- Quá ám ảnh rằng mọi kích thước phải thuộc scale, kể cả những giá trị phụ thuộc nội dung.
- Dùng linear scale dày đặc làm decision fatigue vẫn còn nguyên.

### Ngoại lệ
Một số kích thước như ảnh theo tỉ lệ, chiều cao do nội dung, hoặc giới hạn responsive có thể không nằm hoàn toàn trong scale.

### Checklist
- [ ] Tôi có spacing scale rõ ràng không?
- [ ] Hai giá trị kề nhau có khác biệt đủ để quyết định nhanh không?
- [ ] Các component tương tự có dùng cùng token không?
- [ ] Có nhiều số “lẻ” không giải thích được không?

### Tóm tắt
**Hệ spacing tốt biến “chọn số” thành “chọn mức”.**

---

## Bài 16 — Không cần lấp đầy toàn bộ màn hình

### Vấn đề
Màn hình desktop rộng khiến người mới có cảm giác phải kéo form, bảng và card rộng ra để “tận dụng không gian”. Kết quả thường là nội dung khó đọc hơn.

### Mục tiêu
Cho mỗi phần tử **đúng lượng không gian nó cần**, không nhiều hơn chỉ vì còn chỗ.

### Lý thuyết
Width tối ưu phụ thuộc nội dung. Một form chỉ cần khoảng 500-600px không trở nên tốt hơn khi kéo lên 1200px. Extra space ở hai bên có thể giúp tập trung hơn.

### Khi nào áp dụng
- Form đăng nhập, settings, checkout.
- Trang nội dung có chiều rộng lớn.
- Responsive layout.

### Cách làm
1. Xác định width hợp lý cho nội dung trước.
2. Dùng `max-width` cho khối không nên giãn vô hạn.
3. Căn giữa hoặc bố trí cột phụ thay vì kéo rộng khối chính.
4. Khi khó thiết kế nhỏ trên canvas lớn, thử bắt đầu từ mobile khoảng ~400px.
5. Mở rộng lên desktop sau, chỉ thay những gì thật sự cần.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Form 500-600px nếu đó là width phù hợp | Form full-width chỉ vì viewport rộng |
| Dùng column phụ để tận dụng không gian | Kéo nội dung chính dài dòng theo chiều ngang |
| Bắt đầu mobile khi cần constraint thật | Tưởng desktop phải “đầy” |

### Ví dụ đúng/sai
**Sai:** Trang đổi mật khẩu rộng 1440px, mỗi input kéo ngang gần hết màn hình.

**Đúng:** Form giữ width gọn; phần còn lại là whitespace hoặc khu vực mô tả riêng.

### Lỗi thường gặp
- Nhầm “responsive” với “mọi thứ đều fluid”.
- Đồng bộ width giữa các khối dù nhu cầu khác nhau.
- Cố kéo content cho thẳng hàng với navigation full-width.

### Ngoại lệ
Bảng dữ liệu nhiều cột, canvas, timeline hoặc dashboard có thể thật sự cần nhiều không gian ngang.

### Checklist
- [ ] Khối này có lý do để rộng như hiện tại không?
- [ ] Max-width có làm nội dung dễ đọc hơn không?
- [ ] Tôi có thể dùng cột phụ thay vì kéo rộng form không?
- [ ] Mobile-first có giúp xác định ưu tiên không?

### Tóm tắt
**Có không gian không đồng nghĩa phải sử dụng hết không gian.**

---

## Bài 17 — Grid hữu ích, nhưng đừng làm nô lệ cho grid

### Vấn đề
Grid 12 cột giúp sắp layout nhanh, nhưng nếu mọi phần tử đều bị ép thành phần trăm theo grid, những thứ nên có width cố định cũng co giãn vô lý.

### Mục tiêu
Dùng grid như công cụ hỗ trợ, không phải luật tối cao.

### Lý thuyết
Không phải phần tử nào cũng nên fluid. Ví dụ sidebar có nội dung cố định thường nên có width phù hợp với nội dung, trong khi main content mới là phần flex. Tương tự, card login có một width tối ưu; nó không nên nhỏ đi khi viewport vẫn còn đủ chỗ.

### Khi nào áp dụng
- Sidebar + content.
- Login/settings card.
- Dashboard card.
- Responsive component.

### Cách làm
1. Hỏi: phần tử này **có cần scale theo viewport không?**
2. Nếu không, dùng fixed width hoặc max-width hợp lý.
3. Cho khu vực cần co giãn nhận phần không gian còn lại.
4. Chỉ shrink component khi viewport thật sự không đủ.
5. Dùng grid bên trong vùng fluid khi nó thực sự giúp bố cục.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Sidebar width theo nội dung | Sidebar luôn 25% vì grid 3/12 |
| Card có max-width tối ưu | Card co nhỏ trên màn hình trung bình dù vẫn còn chỗ |
| Grid phục vụ component | Component phục vụ grid |

### Ví dụ đúng/sai
**Sai:** Sidebar 25%: trên màn hình lớn nó phình vô ích, trên màn hình nhỏ nó co đến mức label wrap.

**Đúng:** Sidebar giữ khoảng width phù hợp; content flex để dùng phần còn lại.

### Lỗi thường gặp
- Tin rằng “on-grid” luôn đồng nghĩa “đúng”.
- Dùng percentage cho avatar/icon dù chúng không nên scale.
- Tạo breakpoint chỉ để giữ tỷ lệ grid, không dựa trên nhu cầu component.

### Ngoại lệ
Gallery ảnh, card catalog hoặc layout marketing có thể hưởng lợi mạnh từ width theo tỷ lệ/grid.

### Checklist
- [ ] Phần tử nào cần fixed/max-width?
- [ ] Phần tử nào thực sự nên fluid?
- [ ] Component có bị co trước khi cần không?
- [ ] Grid đang giải quyết vấn đề hay đang tạo vấn đề?

### Tóm tắt
**Grid là một bộ gợi ý về trật tự, không phải một tôn giáo.**

---

## Bài 18 — Đừng bắt mọi thứ scale theo cùng một tỷ lệ

### Vấn đề
Một cách nghĩ hấp dẫn là: desktop giảm 25% thì mọi thứ — font, padding, heading — cũng giảm 25%. Nhưng cảm nhận thị giác không scale tuyến tính như vậy.

### Mục tiêu
Cho phép từng thuộc tính và từng phần tử **thay đổi độc lập theo ngữ cảnh**.

### Lý thuyết
Những thứ rất lớn trên desktop thường cần thu nhỏ mạnh hơn trên mobile, trong khi text vốn nhỏ chỉ nên giảm ít hoặc không giảm. Tương tự, một button lớn và button nhỏ không nhất thiết là cùng một component được zoom theo tỷ lệ; padding có thể thay đổi không đồng tỷ lệ với font size.

### Khi nào áp dụng
- Responsive typography.
- Button sizes.
- Card responsive.
- Component variants small/medium/large.

### Cách làm
1. Thiết kế từng breakpoint bằng mắt và nhu cầu thật.
2. Giảm heading mạnh hơn body text khi màn hình nhỏ.
3. Không encode mọi quan hệ bằng `em` chỉ vì tiện.
4. Với component size, điều chỉnh font và padding độc lập.
5. Kiểm tra cảm giác “small thật sự nhỏ” và “large thật sự lớn”.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Heading desktop 45px có thể xuống 24px mobile | Giữ cố định `heading = 2.5 × body` mọi breakpoint |
| Small button có padding giảm mạnh | Zoom toàn component theo cùng tỷ lệ |
| Fine-tune độc lập | Ép “tỉ lệ toán học đẹp” lên mọi ngữ cảnh |

### Ví dụ đúng/sai
**Sai:** Body 18→14px, headline vẫn 2.5em nên 45→35px, quá lớn trên mobile.

**Đúng:** Body 14px, headline khoảng 20-24px tùy bố cục.

### Lỗi thường gặp
- Tin rằng proportional = consistent.
- Dùng em lồng nhau làm size trôi khỏi hệ thống.
- Không kiểm tra breakpoint thật.

### Ngoại lệ
Một số icon/illustration có thể scale theo tỷ lệ đồng nhất vì đó là đồ họa, không phải typography/layout chức năng.

### Checklist
- [ ] Heading có thu nhanh hơn body trên màn nhỏ không?
- [ ] Padding có phù hợp từng variant không?
- [ ] Có quan hệ tỷ lệ nào đang tồn tại chỉ vì “đẹp về toán” không?

### Tóm tắt
**Responsive tốt không phải thu nhỏ toàn bộ screenshot; đó là tái cân bằng từng thành phần.**

---

## Bài 19 — Tránh spacing mơ hồ

### Vấn đề
Khi không có border/background phân nhóm, người dùng dựa vào khoảng cách để hiểu thứ nào thuộc cùng nhóm. Nếu khoảng trong nhóm bằng khoảng giữa nhóm, cấu trúc trở nên mơ hồ.

### Mục tiêu
Dùng spacing để truyền đạt **quan hệ**.

### Lý thuyết
Quy tắc cốt lõi: **khoảng cách bên trong một nhóm phải nhỏ hơn khoảng cách xung quanh nhóm**. Đây là cách tạo grouping mà không cần thêm border.

### Khi nào áp dụng
- Label + input.
- Heading + paragraph.
- Bullet list.
- Icon + số liệu/action.
- Các item xếp ngang.

### Cách làm
1. Xác định nhóm logic.
2. Chọn gap nhỏ cho phần tử thuộc cùng nhóm.
3. Chọn gap lớn hơn rõ rệt giữa các nhóm.
4. Kiểm tra cả trục dọc và ngang.
5. Nếu vẫn khó hiểu, mới cân nhắc border/background.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Label cách input 8-12px, nhóm kế tiếp 24px | Mọi khoảng đều 20px |
| Heading gần đoạn nó mô tả | Heading nằm giữa hai đoạn với khoảng cách bằng nhau |
| Action icon và số liệu có gap hợp lý | Các action dàn đều nhưng không biết số nào thuộc icon nào |

### Ví dụ đúng/sai
**Sai:** Label cách input 20px, input cách label kế tiếp cũng 20px → người dùng khó biết label thuộc field nào.

**Đúng:** Label → input 8px; input → nhóm tiếp theo 24px.

### Lỗi thường gặp
- Dùng spacing “đều” để mong trông sạch.
- Chỉ kiểm tra vertical spacing.
- Thêm border để cứu grouping mà spacing vẫn sai.

### Ngoại lệ
Khi có separator rất rõ như card background, table row hoặc divider, spacing có thể gần nhau hơn vì grouping đã được truyền đạt bằng cách khác.

### Checklist
- [ ] Khoảng trong nhóm có nhỏ hơn khoảng ngoài nhóm không?
- [ ] Nhìn nhanh có biết label thuộc input nào không?
- [ ] Heading có gần nội dung của nó hơn nội dung trước không?
- [ ] Horizontal group có rõ quan hệ không?

### Tóm tắt
**Khoảng cách không chỉ để “thoáng”; nó nói cho người dùng biết thứ gì thuộc về nhau.**

---
# Phần IV — Typography: làm chữ dễ đọc và nhất quán

## Bài 20 — Thiết lập type scale

### Vấn đề
Một UI không có hệ thống thường dùng gần như mọi kích thước chữ từ 10px đến 24px. Hậu quả là màn hình trông không nhất quán, đồng thời bạn mất thời gian cân nhắc từng pixel.

### Mục tiêu
Tạo một **type scale hữu hạn** đủ linh hoạt cho UI nhưng đủ chặt để ra quyết định nhanh.

### Lý thuyết
Scale tuyến tính hoặc modular scale thuần toán học nghe hấp dẫn nhưng có thể sinh ra số lẻ và những bước nhảy không phù hợp với UI. Phần sách đã đọc đề xuất cách thực dụng hơn: **chọn scale thủ công**.

Một scale ví dụ trong sách:

`12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72px`

Đây là ví dụ, không phải luật bắt buộc. Điều quan trọng là số lượng size được giới hạn và mỗi size có vai trò rõ.

Ngoài ra, phần đã đọc cảnh báo việc xây type scale bằng `em` lồng nhau vì giá trị thực có thể trôi khỏi scale; `px` hoặc `rem` giúp kiểm soát tốt hơn.

### Khi nào áp dụng
- Ngay khi dự án có hơn vài màn hình.
- Khi designer/developer đang dùng nhiều font size gần giống nhau.
- Khi heading và body không có quy ước.

### Cách làm
1. Chọn body mặc định, thường quanh 16px nếu phù hợp sản phẩm.
2. Chọn 1-2 size nhỏ hơn cho metadata/caption.
3. Chọn 2-4 size lớn hơn cho section title, page title, hero.
4. Đảm bảo bước nhảy nhỏ ở vùng text nhỏ và rõ hơn ở vùng headline lớn.
5. Gán tên token, ví dụ `text-sm`, `text-base`, `text-lg`, `title-md`, `display-lg`.
6. Không tạo size mới chỉ vì một màn hình “thiếu 1px”.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng scale hữu hạn | Có 13px, 14px, 15px, 16px, 17px tùy chỗ |
| Hand-craft scale theo nhu cầu UI | Ép mọi size theo golden ratio |
| Dùng px/rem để giữ scale ổn định | Dùng em lồng nhau làm computed size lệch |

### Ví dụ đúng/sai
**Sai:** Card A dùng 15px, Card B 17px, modal 19px, table 13px, tất cả không có lý do.

**Đúng:** Body 16px, metadata 14px, section title 20px, page title 30px, display 48px; chỉ dùng các mức đã định nghĩa.

### Lỗi thường gặp
- Tạo scale quá ít size nên designer phải phá hệ thống liên tục.
- Tạo scale quá nhiều size nên mất tác dụng.
- Dùng size như công cụ hierarchy duy nhất.

### Ngoại lệ
Một chiến dịch marketing hoặc màn hình đặc biệt có thể cần display size ngoài scale UI chính. Nên coi đó là ngoại lệ có chủ ý.

### Checklist
- [ ] Có một danh sách font size chính thức không?
- [ ] Mỗi size có vai trò tương đối rõ không?
- [ ] Có size nào chỉ xuất hiện một lần và không giải thích được không?
- [ ] Nested text có trôi khỏi scale không?

### Tóm tắt
**Type scale giúp chữ trông có hệ thống và giúp bạn ngừng tranh luận về từng pixel.**

---

## Bài 21 — Chọn font “tốt” theo cách an toàn

### Vấn đề
Người mới khó đánh giá chất lượng typeface vì có hàng nghìn lựa chọn và nhiều chi tiết typography cần thời gian để phát triển con mắt.

### Mục tiêu
Có một quy trình chọn font đủ an toàn mà không cần trở thành chuyên gia type design.

### Lý thuyết
Phần sách đã đọc đưa ra các cách giảm rủi ro:
- UI thường an toàn với **sans-serif trung tính**.
- Một font family có nhiều weight thường cho thấy nó được đầu tư nghiêm túc và cũng linh hoạt hơn.
- Font cho text nhỏ cần chú trọng legibility; typeface quá condensed hoặc x-height thấp có thể khó đọc.
- Mức độ phổ biến là một tín hiệu thực dụng khi bạn chưa có trực giác typography.
- Quan sát font mà các đội thiết kế tốt đang dùng giúp xây dựng “con mắt” theo thời gian.

### Khi nào áp dụng
- Khi dự án chưa có brand font.
- Khi bạn đang chọn font đầu tiên cho product UI.
- Khi có quá nhiều lựa chọn và không biết bắt đầu từ đâu.

### Cách làm
1. Bắt đầu bằng sans-serif trung tính, dễ đọc.
2. Ưu tiên family có nhiều weight thực sự hữu dụng.
3. Test ở kích thước UI nhỏ, không chỉ nhìn headline lớn.
4. Tránh font quá condensed cho body/interface text.
5. Xem các font phổ biến hoặc font từ sản phẩm có typography tốt để thu hẹp lựa chọn.
6. Kiểm tra số, dấu câu, chữ hoa/thường và tiếng Việt nếu sản phẩm dùng tiếng Việt.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Test font ở 14-16px | Chọn font vì logo sample 72px trông đẹp |
| Dùng family có nhiều weight | Chọn font chỉ có Regular/Bold nếu sản phẩm cần nhiều hierarchy |
| Ưu tiên legibility | Dùng condensed display face cho bảng dữ liệu |

### Ví dụ đúng/sai
**Sai:** Chọn một font cá tính, chữ thấp và hẹp cho toàn bộ dashboard vì banner trông “premium”.

**Đúng:** Dùng sans dễ đọc cho UI; nếu cần personality, dùng font đặc trưng ở heading/marketing có kiểm soát.

### Lỗi thường gặp
- Chọn font bằng screenshot marketing thay vì thử dữ liệu thật.
- Dùng quá nhiều font family.
- Không kiểm tra tiếng Việt có đủ dấu và hiển thị đẹp.
- Chọn weight giả do trình duyệt tự tổng hợp.

### Ngoại lệ
Brand mạnh có thể yêu cầu typeface đặc thù. Khi đó vẫn cần một strategy cho text nhỏ nếu brand font không tối ưu cho UI.

### Checklist
- [ ] Font có dễ đọc ở size nhỏ không?
- [ ] Có đủ weight cần dùng không?
- [ ] Chữ số và ký tự đặc biệt ổn không?
- [ ] Hỗ trợ tiếng Việt tốt không?
- [ ] Tôi chọn font vì nhu cầu hay chỉ vì “trông lạ”?

### Tóm tắt
**Khi chưa có trực giác typography, chọn font an toàn và dễ đọc tốt hơn chọn font gây ấn tượng nhưng khó dùng.**

---

## Bài 22 — Giữ độ dài dòng trong vùng dễ đọc

### Vấn đề
Text paragraph thường bị kéo theo width của layout. Trên desktop rộng, một dòng có thể quá dài, khiến mắt khó quay về đúng dòng tiếp theo.

### Mục tiêu
Tối ưu trải nghiệm đọc thay vì chỉ “fit content vào layout”.

### Lý thuyết
Phần đã đọc đưa ra vùng an toàn khoảng **45-75 ký tự mỗi dòng** cho paragraph. Trên web, một gợi ý thực dụng là width khoảng **20-35em**, tùy font và ngữ cảnh.

Một content area có thể rộng để chứa ảnh hoặc component, nhưng paragraph bên trong không nhất thiết phải rộng bằng toàn bộ content area.

### Khi nào áp dụng
- Article, help center, onboarding copy.
- Mô tả dài trong settings.
- Landing page có đoạn text dài.

### Cách làm
1. Đưa nội dung thật vào layout.
2. Ước lượng 45-75 ký tự/dòng.
3. Dùng `max-width` riêng cho paragraph.
4. Không kéo paragraph rộng theo ảnh/banner lớn.
5. Test với text dài, không chỉ lorem ngắn.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Paragraph có max-width riêng | Text chạy 120-150 ký tự/dòng |
| Content container rộng nhưng text column hẹp hơn | Bắt mọi phần tử cùng width |
| Ưu tiên khả năng đọc | Căn layout cho “thẳng mép” bằng mọi giá |

### Ví dụ đúng/sai
**Sai:** Trang tài liệu 1200px, paragraph cũng 1200px.

**Đúng:** Trang vẫn 1200px để chứa hình/diagram; paragraph giới hạn khoảng 640-760px tùy font.

### Lỗi thường gặp
- Dùng width của image làm width của text.
- Chỉ kiểm tra màn hình laptop nhỏ, không kiểm tra desktop lớn.
- Giảm font size để “fit” thay vì giới hạn line length.

### Ngoại lệ
Bảng, code block, data visualization và nội dung có cấu trúc khác paragraph không tuân theo quy tắc ký tự/dòng này theo cùng cách.

### Checklist
- [ ] Paragraph có quá dài trên desktop không?
- [ ] Có thể đặt max-width riêng cho text không?
- [ ] Độ dài dòng nằm gần vùng 45-75 ký tự không?
- [ ] Font size vẫn thoải mái sau khi giới hạn width không?

### Tóm tắt
**Đừng để chiều rộng màn hình quyết định chiều rộng đoạn văn.**

---

## Bài 23 — Căn theo baseline, không phải luôn căn giữa

### Vấn đề
Khi hai đoạn text khác font size nằm cùng một hàng, căn giữa theo hộp bounding box có thể khiến chữ trông lệch dù về toán học là “center”.

### Mục tiêu
Tạo alignment tự nhiên theo cách mắt người đọc cảm nhận chữ.

### Lý thuyết
Chữ có **baseline** — đường tưởng tượng mà các ký tự “đứng” trên đó. Khi text size khác nhau nằm gần nhau, căn baseline thường tạo cảm giác gọn hơn vertical-center.

### Khi nào áp dụng
- Title lớn + action text nhỏ cùng hàng.
- Giá lớn + đơn vị nhỏ.
- Số liệu + label.
- Navigation có chữ nhiều size.

### Cách làm
1. Xác định các text cùng một hàng có size khác nhau.
2. Thử căn baseline trước.
3. So với center alignment ở khoảng cách thực tế.
4. Chọn phương án tạo một đường đọc tự nhiên hơn.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Căn baseline cho text khác size | Mặc định `align-items: center` cho mọi hàng chữ |
| Nhìn optical alignment | Chỉ tin bounding box |
| Test khi text đứng gần nhau | Chỉ nhìn component phóng to |

### Ví dụ đúng/sai
**Sai:** Giá `1.250.000` 32px và `/tháng` 14px được căn center, làm đơn vị “lơ lửng”.

**Đúng:** Cả hai cùng baseline, đơn vị nằm tự nhiên cạnh giá.

### Lỗi thường gặp
- Dùng center vì flexbox mặc định dễ.
- Không để ý baseline khi text size chênh lớn.
- Cố căn bằng margin thủ công theo từng content.

### Ngoại lệ
Nếu text đi cùng icon hoặc control không phải chữ, center alignment có thể phù hợp hơn. Hãy xét loại phần tử thực tế.

### Checklist
- [ ] Có nhiều font size trên cùng một hàng không?
- [ ] Tôi đã thử baseline alignment chưa?
- [ ] Có margin “chữa lệch” bất thường không?

### Tóm tắt
**Khi căn chữ với chữ, baseline thường là mốc thị giác tốt hơn tâm của hộp.**

---

## Bài 24 — Line-height phải thay đổi theo độ dài dòng và font size

### Vấn đề
Một quy tắc kiểu “line-height luôn 1.5” nghe đơn giản nhưng không phù hợp mọi loại text. Dòng dài cần nhiều khoảng cách hơn; heading lớn thường cần ít hơn.

### Mục tiêu
Chọn line-height dựa trên **line length** và **font size**, không dùng một số cố định cho toàn bộ sản phẩm.

### Lý thuyết
Hai quan hệ quan trọng trong phần đã đọc:

1. **Dòng càng dài → line-height thường cần lớn hơn.** Mắt phải di chuyển xa từ cuối dòng về đầu dòng tiếp theo nên cần khoảng dọc rõ hơn để không lạc dòng.
2. **Font càng lớn → line-height tương đối có thể nhỏ hơn.** Text nhỏ cần nhiều trợ giúp để tìm dòng tiếp theo; headline lớn có thể dùng line-height gần 1.

Sách minh họa rằng nội dung hẹp có thể dùng khoảng 1.5, còn nội dung rất rộng có thể cần cao hơn; với headline lớn, line-height 1 có thể ổn.

### Khi nào áp dụng
- Paragraph dài.
- Responsive typography.
- Card description nhỏ.
- Heading nhiều dòng.

### Cách làm
1. Chọn font size trước.
2. Chọn width/line length thực tế.
3. Với body nhỏ/dòng dài, tăng line-height.
4. Với heading lớn, giảm line-height để tránh khoảng trống dư.
5. Test bằng đoạn nhiều dòng thực, không chỉ một dòng.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Body 14-16px có line-height rộng rãi | Dùng 1.1 cho paragraph dài |
| Heading lớn dùng line-height chặt hơn | Dùng 1.5 cho 48px heading tạo khoảng rời rạc |
| Điều chỉnh theo width | Một line-height cho mọi breakpoint |

### Ví dụ đúng/sai
**Sai:** Body 14px rộng 800px nhưng line-height 1.2; người đọc dễ lạc dòng.

**Đúng:** Hoặc giới hạn width, hoặc tăng line-height. Heading 48px có thể dùng line-height gần 1-1.1 nếu hình dáng font cho phép.

### Lỗi thường gặp
- Copy line-height từ design system khác mà không xét font.
- Tăng line-height quá nhiều thay vì sửa line length.
- Dùng line-height nhỏ cho text nhỏ chỉ vì muốn card thấp hơn.

### Ngoại lệ
Single-line controls như button/input label không cần line-height theo logic paragraph; chúng thường dựa nhiều vào height/padding của control.

### Checklist
- [ ] Paragraph dài có đủ khoảng dọc không?
- [ ] Heading có bị “lỏng” quá không?
- [ ] Responsive width thay đổi nhưng line-height có cần đổi không?
- [ ] Tôi đã test đoạn 3-5 dòng thật chưa?

### Tóm tắt
**Line-height không phải hằng số; nó là câu trả lời cho kích thước chữ và quãng đường mắt phải đọc.**

---

## Bài 25 — Không phải link nào cũng cần màu nổi

> Lưu ý phạm vi: trong nửa đầu PDF, trang 109 mới bắt đầu mục này. Vì vậy bài này chỉ tóm lược những gì xuất hiện đến hết trang 109.

### Vấn đề
Trong một đoạn văn bình thường, link cần khác biệt để người đọc nhận ra nó có thể click. Nhưng trong một giao diện mà rất nhiều thứ đều là link/action, nếu mọi link đều dùng màu nổi theo kiểu bài viết, màn hình sẽ trở nên quá ồn.

### Mục tiêu
Dùng visual treatment cho link theo **ngữ cảnh**, không áp một style “link xanh nổi bật” cho mọi nơi.

### Lý thuyết
Mức độ cần làm link nổi bật phụ thuộc vào môi trường xung quanh:
- Trong paragraph có nhiều text không tương tác, link cần dễ phân biệt.
- Trong application UI nơi nhiều phần tử đã có tính tương tác, quá nhiều màu link có thể cạnh tranh attention.

### Khi nào áp dụng
- Article/help text có inline link.
- Card/list nơi title, thumbnail, metadata đều có thể click.
- Dashboard có nhiều text action.

### Cách làm
1. Xác định người dùng có cần nhận ra link ngay trong ngữ cảnh không.
2. Với inline link trong đoạn văn, tạo khác biệt rõ ràng.
3. Với UI có nhiều vùng tương tác, tránh biến mọi link thành điểm nhấn màu mạnh.
4. Luôn giữ affordance và khả năng nhận biết đủ cho use case.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Inline link trong paragraph nhìn ra được | Link hòa hoàn toàn vào body text |
| Link-heavy UI dùng treatment tiết chế | Mọi title/action đều màu xanh chói |
| Xét hierarchy tổng thể | Style link tách rời khỏi ngữ cảnh |

### Ví dụ đúng/sai
**Sai:** Một news/card grid có title, tác giả, category, timestamp đều màu xanh chỉ vì tất cả đều click được.

**Đúng:** Chỉ các phần cần emphasis có treatment mạnh; các vùng khác vẫn có khả năng tương tác nhưng không đồng loạt “hét lên”.

### Lỗi thường gặp
- Đồng nhất “clickable” với “phải màu xanh”.
- Làm link quá giống text bình thường trong paragraph.
- Không xét việc màu link có cạnh tranh với primary action hay không.

### Ngoại lệ
Các yêu cầu accessibility và quy ước sản phẩm có thể yêu cầu dấu hiệu tương tác rõ hơn. Phần PDF sau trang 109 có thể bổ sung chi tiết, nhưng tài liệu này chủ động không sử dụng vì nằm ngoài nửa đầu được yêu cầu.

### Checklist
- [ ] Inline link trong đoạn văn có nhận biết được không?
- [ ] UI có quá nhiều chữ màu link không?
- [ ] Treatment của link có phá hierarchy không?
- [ ] Người dùng vẫn hiểu phần tử nào có thể tương tác không?

### Tóm tắt
**Link cần đủ rõ để dùng, nhưng không phải link nào cũng phải trở thành điểm nhấn thị giác.**

---

# Phần V - Hoàn thiện typography

## Bài 26 - Không phải link nào cũng cần nổi bật bằng màu

### Vấn đề
Nếu mọi phần tử có thể click đều được tô màu link nổi bật, một ứng dụng có nhiều action sẽ trở nên ồn. Người dùng nhìn thấy quá nhiều điểm tranh giành sự chú ý, trong khi nhiều link chỉ là hành động phụ.

### Mục tiêu
Làm link **đủ nhận biết theo ngữ cảnh**, nhưng không để các link phụ cạnh tranh với nội dung và hành động quan trọng hơn.

### Lý thuyết
Phần tiếp nối ở trang 110 nhấn mạnh rằng phần lớn link có thể được nhấn nhẹ bằng **font-weight đậm hơn** hoặc **màu chữ tối hơn**, thay vì luôn dùng một màu nổi riêng. Với link rất phụ, có thể chỉ hiện underline hoặc đổi màu khi hover.

Ý chính là: mức độ nhấn của link phải phù hợp với vị trí của nó trong hierarchy.

### Khi nào áp dụng
- Card/list có nhiều vùng click.
- Dashboard với nhiều action phụ.
- Metadata, link “xem thêm”, link phụ trợ.
- Khu vực mà primary CTA đã có màu nhấn mạnh.

### Cách làm
1. Xác định link có nằm trong luồng chính hay chỉ là đường phụ.
2. Với link quan trọng, cho treatment rõ nhưng không nhất thiết phải màu xanh mặc định.
3. Với link thứ cấp, thử tăng font-weight hoặc dùng màu đậm hơn body text.
4. Với link rất phụ, cân nhắc chỉ hiện underline/đổi màu khi hover.
5. Kiểm tra lại toàn màn hình xem link có đang cạnh tranh với CTA chính không.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Nhấn link theo mức độ quan trọng | Cho mọi link cùng một màu nổi |
| Dùng weight hoặc contrast khi đủ | Đồng nhất “clickable” với “phải xanh” |
| Để link phụ lùi xuống hierarchy | Làm link phụ nổi hơn CTA chính |

### Ví dụ đúng/sai
**Sai:** Trong một card sản phẩm, tên sản phẩm, tác giả, category, ngày tháng và “xem chi tiết” đều có màu xanh đậm.

**Đúng:** Tên sản phẩm dùng chữ đậm; metadata dùng màu trung tính; link “xem chi tiết” chỉ đổi màu hoặc underline khi hover.

### Lỗi thường gặp
- Dùng màu link như một quy tắc bất biến.
- Không xét hierarchy của toàn màn hình.
- Làm hover quá tinh tế đến mức người dùng không nhận ra phần tử có thể tương tác.

### Ngoại lệ
Inline link nằm trong đoạn văn dài thường cần dấu hiệu nhận biết rõ hơn, vì xung quanh nó là text không tương tác. Phần này không phủ nhận nhu cầu đó; nó chỉ nói rằng trong application UI, link không nhất thiết phải được nhấn theo cùng một cách.

### Checklist
- [ ] Link quan trọng có nhận ra được không?
- [ ] Link phụ có đang tranh attention với CTA chính không?
- [ ] Có link nào chỉ cần weight/contrast thay vì màu riêng không?
- [ ] Hover/focus vẫn cho người dùng dấu hiệu tương tác rõ ràng không?

### Tóm tắt
**Link cần được nhìn thấy đúng mức, không phải được tô màu nổi bằng mọi giá.**

---

## Bài 27 - Căn chữ để ưu tiên khả năng đọc

### Vấn đề
Người mới thường căn giữa vì thấy “cân đối”, hoặc justify vì trông “chuyên nghiệp”. Nhưng căn chữ đẹp trong một block ngắn có thể trở nên khó đọc khi nội dung dài.

### Mục tiêu
Chọn alignment theo cách mắt người đọc quét nội dung, không theo cảm giác đối xứng đơn thuần.

### Lý thuyết
Với các ngôn ngữ đọc từ trái sang phải như tiếng Anh, phần lớn text nên **căn trái**. Center alignment phù hợp với headline hoặc khối text ngắn, độc lập. Khi đoạn dài hơn khoảng 2-3 dòng, căn trái thường dễ đọc hơn vì mỗi dòng bắt đầu từ cùng một trục.

Sách cũng đưa ra hai trường hợp đặc biệt:
- **Số trong bảng:** căn phải để hàng đơn vị/thập phân dễ so sánh.
- **Justified text:** nếu dùng, nên bật hyphenation để giảm các khoảng trắng bất thường giữa từ.

### Khi nào áp dụng
- Paragraph, description, card copy.
- Hero text hoặc headline ngắn.
- Bảng số liệu.
- Thiết kế muốn mô phỏng phong cách báo/tạp chí in.

### Cách làm
1. Mặc định text dài bằng căn trái.
2. Chỉ center-align các block ngắn như heading, subheading, CTA intro.
3. Nếu block căn giữa vượt quá 2-3 dòng, viết ngắn lại hoặc chuyển sang căn trái.
4. Trong bảng số, căn phải các cột số.
5. Nếu justify, bật hyphenation và kiểm tra khoảng trắng giữa từ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Căn trái paragraph dài | Căn giữa đoạn 5-8 dòng |
| Căn phải cột số | Căn trái số khiến khó so sánh |
| Hyphenate khi justify | Justify rồi chấp nhận khoảng trắng loang lổ |

### Ví dụ đúng/sai
**Sai:** Ba cột tính năng đều căn giữa, trong đó một cột có mô tả dài 5 dòng và nhìn lệch nhịp so với hai cột còn lại.

**Đúng:** Rút gọn copy để các block còn 2-3 dòng, hoặc chuyển phần description dài sang căn trái.

### Lỗi thường gặp
- Căn giữa tất cả vì “landing page hay làm vậy”.
- Căn giữa text dài khiến mắt phải tìm điểm bắt đầu mới ở từng dòng.
- Bảng tài chính căn giữa số.
- Justify mà không để ý khoảng cách từ.

### Ngoại lệ
Justified text có thể hợp với giao diện cố tình mô phỏng ấn phẩm in như magazine/newspaper. Tuy nhiên căn trái vẫn là lựa chọn hợp lệ và đơn giản hơn.

### Checklist
- [ ] Đoạn dài có cùng một trục bắt đầu không?
- [ ] Centered text có dưới khoảng 2-3 dòng không?
- [ ] Cột số có căn phải không?
- [ ] Justified text có hyphenation và khoảng từ ổn không?

### Tóm tắt
**Alignment nên làm cho việc đọc dễ hơn trước khi làm cho bố cục trông đối xứng hơn.**

---

## Bài 28 - Dùng letter-spacing có chủ đích

### Vấn đề
Designer mới thường chỉ chỉnh font-size, weight và line-height mà quên letter-spacing; hoặc ngược lại, chỉnh tracking ở mọi nơi dù typeface đã được thiết kế tốt sẵn.

### Mục tiêu
Biết khi nào nên **để nguyên** letter-spacing và khi nào một thay đổi nhỏ thực sự cải thiện typography.

### Lý thuyết
Quy tắc mặc định của sách là: **tin vào type designer và để letter-spacing yên**. Hai trường hợp phổ biến đáng điều chỉnh:

1. **Headline dùng font có spacing rộng:** có thể giảm letter-spacing để headline cô đọng hơn.
2. **ALL CAPS:** nên tăng letter-spacing vì các chữ hoa có chiều cao giống nhau, ít đặc điểm hình dáng để phân biệt hơn lowercase.

Sách cũng cảnh báo không nên lấy headline font rồi tăng tracking để ép nó hoạt động ở size nhỏ; loại font đó thường không được thiết kế cho body/UI text.

### Khi nào áp dụng
- Heading lớn dùng sans trung tính có tracking rộng.
- Eyebrow label, menu label hoặc badge viết HOA.
- Typography cần compact hơn mà không đổi font.

### Cách làm
1. Trước tiên dùng tracking mặc định.
2. Với heading, nếu cảm giác chữ quá rời, giảm rất nhẹ rồi so sánh.
3. Với ALL CAPS, tăng tracking vừa phải để các chữ tách bạch hơn.
4. Kiểm tra ở kích thước hiển thị thật.
5. Không cố “cứu” một font không phù hợp bằng tracking cực đoan.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Mặc định giữ tracking của font | Chỉnh tracking ở mọi text style |
| Siết nhẹ heading khi cần | Ép headline font dùng cho body nhỏ |
| Nới ALL CAPS để tăng legibility | Viết hoa + tracking chật làm chữ dính |

### Ví dụ đúng/sai
**Sai:** Label `FULL STACK DEVELOPER` dùng tracking mặc định, chữ hoa nhìn thành một khối đặc.

**Đúng:** Tăng letter-spacing vừa phải để từng ký tự tách rõ hơn.

### Lỗi thường gặp
- Dùng số tracking lớn vì nghĩ “cao cấp”.
- Siết chữ body đến mức khó đọc.
- Không test trên font thật hoặc size thật.

### Ngoại lệ
Typeface display được thiết kế riêng cho headline có thể đã có spacing phù hợp, không cần chỉnh. Hãy nhìn kết quả trước khi áp dụng công thức.

### Checklist
- [ ] Tôi đã thử tracking mặc định trước chưa?
- [ ] Headline có thật sự quá rời không?
- [ ] ALL CAPS có đủ khoảng để đọc nhanh không?
- [ ] Tôi có đang dùng tracking để sửa một lựa chọn font sai không?

### Tóm tắt
**Letter-spacing là tinh chỉnh, không phải công cụ sửa mọi vấn đề typography.**

---

# Phần VI - Làm việc với màu sắc

## Bài 29 - Dùng HSL để suy nghĩ về màu

### Vấn đề
Hex và RGB rất phổ biến nhưng khó giúp người mới hiểu mối quan hệ giữa các màu. Hai màu trông gần nhau có thể có mã hex không hề “gần nhau” về mặt trực giác.

### Mục tiêu
Dùng một mô hình màu giúp bạn suy nghĩ theo ba thuộc tính trực quan: **hue, saturation, lightness**.

### Lý thuyết
HSL mô tả màu bằng:
- **Hue:** vị trí trên bánh xe màu, đo bằng độ. 0° đỏ, 120° xanh lá, 240° xanh dương.
- **Saturation:** độ rực/màu sắc. 0% là xám, 100% là rất rực.
- **Lightness:** mức gần đen hoặc trắng. 0% đen, 100% trắng, khoảng 50% là màu thuần ở hue đó.

Sách cũng phân biệt HSL với HSB: “lightness” trong HSL không giống “brightness” trong HSB. Với web, sách ưu tiên HSL vì trình duyệt hiểu trực tiếp HSL.

### Khi nào áp dụng
- Xây palette cho web.
- Tạo các biến thể sáng/tối của một màu.
- Muốn hiểu tại sao một màu thay đổi khi chỉnh độ rực hoặc độ sáng.

### Cách làm
1. Xác định hue chính của màu thương hiệu.
2. Quan sát saturation để biết màu đang rực hay trung tính.
3. Quan sát lightness để biết màu gần đen/trắng đến đâu.
4. Khi tạo biến thể, chỉnh từng thuộc tính có chủ đích thay vì nhảy giữa các hex ngẫu nhiên.
5. Ghi lại các giá trị trong hệ thống màu cố định.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Nghĩ theo hue/saturation/lightness | Tạo màu mới bằng cách chọn hex tùy hứng |
| Dùng HSL để hiểu quan hệ màu | Nhầm lightness với HSB brightness |
| Ghi palette thành token | Mỗi component tự chọn một màu mới |

### Ví dụ đúng/sai
**Sai:** Cần một blue nhạt hơn nên kéo color picker đến khi “có vẻ ổn”, tạo thêm một mã hex không liên quan đến scale.

**Đúng:** Giữ hue gần màu gốc, điều chỉnh lightness/saturation có chủ đích rồi đưa shade vào palette.

### Lỗi thường gặp
- Chỉ thay lightness mà quên saturation.
- Hiểu 100% lightness là “màu rực nhất”; trong HSL nó là trắng.
- Dùng HSL nhưng vẫn tạo vô hạn màu không qua hệ thống.

### Ngoại lệ
Thiết kế software có thể hiển thị HSB/HSV mặc định. Điều quan trọng trong ngữ cảnh của sách không phải tên công cụ, mà là hiểu thuộc tính màu bạn đang thay đổi và dùng một hệ thống nhất quán.

### Checklist
- [ ] Tôi phân biệt được hue/saturation/lightness không?
- [ ] Shade mới có quan hệ rõ với màu gốc không?
- [ ] Tôi có đang tạo màu mới ngoài palette không?
- [ ] Với web, token màu có thể biểu diễn nhất quán không?

### Tóm tắt
**HSL biến màu từ “mã khó nhớ” thành ba quyết định mà mắt người dễ hiểu.**

---

## Bài 30 - Một palette thực tế cần nhiều màu hơn bạn nghĩ

### Vấn đề
Palette 5 màu trông đẹp trên một dải mẫu nhưng thường không đủ để xây UI thật. Khi bắt đầu làm text, background, control, trạng thái và biểu đồ, bạn sẽ nhanh chóng thiếu lựa chọn.

### Mục tiêu
Xây palette có đủ phạm vi để làm sản phẩm thực tế mà không phải chế thêm màu ngẫu nhiên trong lúc thiết kế.

### Lý thuyết
Sách chia palette UI thành ba nhóm:

1. **Greys:** dùng cho text, background, panel, form control; thường cần khoảng 8-10 shade.
2. **Primary color(s):** thường 1, có thể 2 màu chính; cũng cần khoảng 5-10 shade.
3. **Accent colors:** dùng cho feature nổi bật hoặc trạng thái ngữ nghĩa như destructive, warning, positive; mỗi màu cũng cần nhiều shade.

Với UI phức tạp có chart, calendar, tag/category, tổng số màu accent có thể nhiều hơn đáng kể. Sách nêu rằng một UI phức tạp có thể cần tới khoảng mười màu khác nhau, mỗi màu lại có 5-10 shade.

### Khi nào áp dụng
- Bắt đầu design system.
- Sản phẩm có form, dashboard, alert, status, chart.
- Team thường xuyên “thiếu một màu xám ở giữa”.

### Cách làm
1. Tạo grey scale đủ rộng trước.
2. Chọn 1-2 primary colors và tạo nhiều shade.
3. Liệt kê các semantic states thật sự cần: error/destructive, warning, positive, info...
4. Với dữ liệu phân loại, bổ sung accent colors khi cần.
5. Đặt tên/token để tái sử dụng thay vì copy mã màu bằng tay.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Có nhiều shade trong từng family | Chỉ có 1 blue, 1 red, 1 green |
| Dùng dark grey thay true black | Lạm dụng #000 ở mọi text |
| Accent theo nhu cầu thật | Chọn 5 màu đẹp rồi ép mọi use case vào đó |

### Ví dụ đúng/sai
**Sai:** Design system chỉ có `gray-light`, `gray`, `gray-dark`; sau một tuần xuất hiện thêm 12 mã xám rải rác trong file.

**Đúng:** Có grey scale 8-10 mức, đủ cho primary text, secondary text, border, muted background và panel.

### Lỗi thường gặp
- Palette ít màu nhưng nhiều “one-off color”.
- Không có shade siêu nhạt cho tinted background.
- Không có shade tối cho text trên background nhạt.
- Dùng quá nhiều accent nhưng không có vai trò rõ.

### Ngoại lệ
UI rất nhỏ có thể không cần đầy đủ 10 màu x 10 shade. Mục tiêu là có **đủ lựa chọn để không phải phá hệ thống**, không phải đạt một số lượng bắt buộc.

### Checklist
- [ ] Grey scale có đủ cho text/background/border không?
- [ ] Primary color có light và dark shade không?
- [ ] Semantic states có màu riêng khi thật sự cần không?
- [ ] Chart/tag có cần accent bổ sung không?
- [ ] Có màu nào đang tồn tại chỉ vì “lúc đó thấy đẹp” không?

### Tóm tắt
**Palette UI tốt không phải một dải 5 màu đẹp; nó là kho lựa chọn có hệ thống cho hàng chục tình huống thật.**

---

## Bài 31 - Định nghĩa shade từ đầu, đừng tạo tại chỗ

### Vấn đề
Nếu mỗi lần cần blue nhạt/tối hơn bạn lại gọi `lighten()`, `darken()` hoặc kéo color picker, rất nhanh bạn sẽ có hàng chục biến thể gần giống nhau.

### Mục tiêu
Tạo một **scale shade cố định** trước, sau đó chỉ chọn từ scale đó.

### Lý thuyết
Quy trình trong sách:
1. Chọn **base color** - shade ở giữa, thường là màu dùng tốt cho button background.
2. Chọn **darkest** dựa trên use case như text.
3. Chọn **lightest** dựa trên use case như tinted background.
4. Điền các shade ở giữa bằng cách chia khoảng.

Một scale 9 mức dễ tổ chức bằng tên 100-900: base 500, sáng nhất 100, tối nhất 900; sau đó điền 300/700 rồi 200/400/600/800.

### Khi nào áp dụng
- Bất kỳ palette primary/accent nào.
- Grey scale.
- Team đang có quá nhiều màu gần giống nhau.

### Cách làm
1. Chọn base theo component thật, ví dụ button.
2. Dùng component có cả text + tinted background, như alert, để tìm hai đầu scale.
3. Chia scale thành 5-10 shade; 9 là cấu trúc tiện dùng.
4. So sánh các shade cạnh nhau, đảm bảo mỗi mức đủ khác.
5. Dùng palette trong UI thật rồi tinh chỉnh nhẹ nếu cần.
6. Tránh thêm shade mới trừ khi có lý do rõ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Chọn màu theo ngữ cảnh sử dụng | Tạo shade bằng công thức rồi tin tuyệt đối |
| Fill gaps theo từng khoảng | Tạo 35 màu “blue gần giống nhau” |
| Tinh chỉnh bằng mắt sau khi dùng thật | Thêm shade mới mỗi khi một màn hình thấy thiếu |

### Ví dụ đúng/sai
**Sai:** Mỗi alert có một mã blue riêng vì designer đã dùng `lighten(base, x%)` với x khác nhau.

**Đúng:** Alert dùng `blue-100` làm nền, `blue-900` cho text, button dùng `blue-500`, hover chọn từ scale có sẵn.

### Lỗi thường gặp
- Tin rằng palette có thể được tạo hoàn toàn bằng toán.
- Chọn edge shades mà không có use case.
- Các shade gần nhau đến mức không phân biệt được.

### Ngoại lệ
Sau khi áp palette vào UI thật, điều chỉnh saturation/lightness của một số shade là bình thường. Sách nhấn mạnh hãy **tin mắt hơn con số**, nhưng đừng biến mỗi điều chỉnh thành một shade mới vô hạn.

### Checklist
- [ ] Base shade có use case cụ thể không?
- [ ] Darkest/lightest có use case cụ thể không?
- [ ] Mỗi shade liền kề đủ khác nhau không?
- [ ] Tôi đang chọn từ scale thay vì color picker không?
- [ ] Shade mới có thật sự cần thiết không?

### Tóm tắt
**Tạo shade một lần để dùng nhiều lần; đừng tái phát minh cùng một màu ở mỗi component.**

---

## Bài 32 - Đừng để lightness làm mất độ rực

### Vấn đề
Bạn tạo một màu sáng hơn bằng cách tăng lightness, nhưng kết quả trở nên bạc màu. Tạo màu tối hơn thì lại xỉn và gần đen.

### Mục tiêu
Giữ cho các shade sáng/tối vẫn có cảm giác thuộc cùng một color family và không mất cường độ màu.

### Lý thuyết
Trong HSL, khi lightness tiến gần 0% hoặc 100%, tác động của saturation yếu đi. Vì thế, nếu chỉ tăng/giảm lightness mà giữ nguyên saturation, các shade ở hai đầu dễ bị wash out.

Sách đưa ra hai chiến lược:
- Tăng saturation khi shade đi xa khỏi khoảng 50% lightness.
- Dùng **perceived brightness** của hue: các hue không sáng như nhau dù có cùng HSL lightness. Có thể xoay hue nhẹ về phía hue sáng hơn hoặc tối hơn để thay đổi cảm giác sáng/tối mà giữ cường độ tốt hơn.

Các vùng hue được sách dùng làm điểm tham chiếu:
- Sáng hơn: gần 60°, 180°, 300°.
- Tối hơn: gần 0°, 120°, 240°.

Hue shift chỉ nên nhỏ, khoảng không quá 20-30° để shade vẫn trông như cùng một màu.

### Khi nào áp dụng
- Xây scale cho màu rực.
- Màu vàng/cyan/magenta dễ bị nhạt hoặc bẩn khi đổi lightness.
- Cần dark shade giàu màu thay vì nâu/xám xỉn.

### Cách làm
1. Bắt đầu từ base color.
2. Khi làm sáng/tối, quan sát saturation có bị suy yếu về cảm nhận không.
3. Tăng saturation nếu cần.
4. Với màu đã 100% saturation, thử xoay hue nhẹ về hướng có perceived brightness phù hợp.
5. Chỉ hue-shift một lượng nhỏ rồi so sánh toàn scale.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Quan sát cảm giác màu, không chỉ HSL number | Giữ saturation cố định cho mọi shade |
| Hue-shift nhẹ để giữ intensity | Xoay hue 60-90° làm đổi hẳn color family |
| So sánh cả scale | Tối ưu từng shade tách rời |

### Ví dụ đúng/sai
**Sai:** Yellow base khi làm dark chỉ giảm lightness, kết quả chuyển thành màu nâu xỉn.

**Đúng:** Khi giảm lightness, xoay hue nhẹ về orange và điều chỉnh saturation để shade tối vẫn ấm, giàu màu.

### Lỗi thường gặp
- Nghĩ lightness bằng perceived brightness.
- Thấy shade washed out nhưng tiếp tục chỉ chỉnh lightness.
- Hue shift quá xa.

### Ngoại lệ
Không phải màu nào cũng cần hue rotation. Sách mô tả đây là kỹ thuật hữu ích đặc biệt khi cần giữ intensity; nếu scale trông ổn chỉ bằng saturation/lightness thì không cần phức tạp hóa.

### Checklist
- [ ] Shade sáng/tối có bị bạc màu không?
- [ ] Tôi đã thử tăng saturation chưa?
- [ ] Base đã 100% saturation thì có cần hue shift nhẹ không?
- [ ] Hue shift có dưới khoảng 20-30° không?
- [ ] Cả family vẫn được nhận ra là cùng một màu không?

### Tóm tắt
**Đổi lightness không đồng nghĩa với đổi brightness cảm nhận; hãy giữ intensity bằng saturation và hue khi cần.**

---

## Bài 33 - Grey không nhất thiết phải hoàn toàn xám

### Vấn đề
Grey 0% saturation có thể khiến UI trung tính nhưng cũng dễ vô hồn. Trong khi đó nhiều giao diện “xám” đẹp thực chất đang dùng grey pha màu.

### Mục tiêu
Dùng **color temperature** để khiến grey scale hỗ trợ personality của sản phẩm.

### Lý thuyết
True grey có saturation 0%. Nhưng grey có thể được pha hue nhẹ:
- Pha blue -> cảm giác **cool**.
- Pha yellow/orange -> cảm giác **warm**.

Để temperature nhất quán, khi đi ra các shade rất sáng/tối cần tăng saturation tương ứng; nếu không, các shade biên dễ bị washed out so với shade giữa.

### Khi nào áp dụng
- Dashboard/SaaS cần cảm giác cool, kỹ thuật.
- Brand muốn warm, thân thiện hơn.
- Neutral palette trông quá “dead”.

### Cách làm
1. Chọn hướng cool hoặc warm phù hợp personality.
2. Thêm một lượng hue rất nhỏ vào grey scale.
3. So sánh toàn scale, đặc biệt các shade sáng/tối.
4. Tăng saturation ở edge shades nếu chúng mất temperature.
5. Dùng grey scale đó nhất quán cho text, border, surface.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Pha màu nhẹ có chủ đích | Mỗi shade xám lệch sang một hue khác nhau |
| Giữ temperature nhất quán | Edge shades trở về neutral ngẫu nhiên |
| Chọn mức saturation theo mood | Nghĩ “grey” bắt buộc saturation = 0 |

### Ví dụ đúng/sai
**Sai:** Một UI dùng blue-grey cho card, neutral-grey cho border, warm-grey cho text mà không có chủ đích.

**Đúng:** Toàn bộ neutral scale nghiêng nhẹ sang blue, tạo cảm giác mát và đồng nhất.

### Lỗi thường gặp
- Pha quá nhiều màu khiến “grey” thành màu rõ rệt.
- Dùng cùng saturation ở mọi lightness và bị wash out.
- Không gắn grey temperature với personality tổng thể.

### Ngoại lệ
Nếu sản phẩm cần neutral thật sự hoặc đã có brand colors rất mạnh, grey gần 0% saturation có thể là lựa chọn đúng. Kỹ thuật tint grey là tùy chọn, không phải yêu cầu bắt buộc.

### Checklist
- [ ] Neutral palette đang cool, warm hay neutral có chủ đích?
- [ ] Các shade biên còn giữ temperature không?
- [ ] Grey có hỗ trợ personality không?
- [ ] Có shade nào nhìn lệch hẳn khỏi family không?

### Tóm tắt
**Grey cũng là màu; pha nhiệt độ nhẹ có thể làm cả giao diện có cá tính hơn.**

---

## Bài 34 - Accessible không có nghĩa là phải xấu

### Vấn đề
Khi cố tăng contrast cho text trên nền màu, người mới thường làm nền rất tối hoặc text gần trắng hoàn toàn. Kết quả có thể đạt contrast nhưng phá hierarchy, vì những panel phụ bỗng trở thành điểm hút mắt nhất.

### Mục tiêu
Đáp ứng contrast theo hướng vẫn giữ được hierarchy và personality của UI.

### Lý thuyết
Theo ngưỡng được sách nêu, WCAG khuyến nghị:
- Text bình thường dưới khoảng 18px: contrast tối thiểu **4.5:1**.
- Text lớn: tối thiểu **3:1**.

Hai kỹ thuật chính trong sách:

1. **Flip the contrast:** thay vì white text trên nền màu tối, dùng text màu tối trên nền màu rất nhạt. Màu vẫn hiện diện nhưng bớt áp đảo.
2. **Rotate the hue:** với colored text trên colored background, nếu chỉ tăng lightness thì text thứ cấp dễ tiến quá gần trắng. Có thể xoay hue về màu có perceived brightness cao hơn như cyan, magenta hoặc yellow để tăng contrast mà vẫn giữ màu.

### Khi nào áp dụng
- Alert/banner màu.
- Tag/status.
- Secondary text trong panel màu tối.
- Component cần màu nhưng không nên thành focus chính.

### Cách làm
1. Đo contrast thay vì đoán bằng mắt.
2. Nếu white-on-color bắt bạn dùng nền quá tối, thử đảo thành dark-on-light.
3. Nếu secondary colored text chưa đủ contrast, thử điều chỉnh hue thay vì chỉ tăng lightness.
4. Kiểm tra hierarchy sau khi đạt contrast.
5. So sánh primary/secondary text để đảm bảo chúng vẫn khác cấp.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Đạt contrast và kiểm tra hierarchy | Làm mọi panel màu thành khối rất tối |
| Flip contrast khi hợp | Cố giữ white-on-color bằng mọi giá |
| Dùng hue để tăng perceived brightness | Đẩy mọi secondary text gần trắng |

### Ví dụ đúng/sai
**Sai:** Một status nhỏ cần readable nên dùng nền đỏ cực tối + text trắng, khiến nó nổi hơn cả CTA.

**Đúng:** Dùng nền đỏ rất nhạt + text đỏ đậm, vẫn đọc rõ nhưng không chiếm focus.

### Lỗi thường gặp
- Chỉ kiểm tra đẹp mà không kiểm tra contrast.
- Chỉ kiểm tra contrast mà không kiểm tra hierarchy.
- Primary và secondary text trở nên cùng độ sáng.

### Ngoại lệ
Khi component thực sự cần thu hút attention mạnh, nền màu tối có thể đúng. Vấn đề không phải dark background, mà là dùng nó cho phần tử vốn không nên là focus.

### Checklist
- [ ] Contrast đạt ngưỡng sách nêu cho loại text chưa?
- [ ] Component có đang nổi quá mức cần thiết không?
- [ ] Có thể flip contrast không?
- [ ] Primary và secondary text vẫn khác nhau rõ không?

### Tóm tắt
**Accessibility và hierarchy không đối lập; hãy thay cấu trúc contrast thay vì chỉ làm mọi thứ tối hơn.**

---

## Bài 35 - Đừng dùng màu như tín hiệu duy nhất

### Vấn đề
Nếu một metric tốt/xấu chỉ khác nhau bằng xanh/đỏ, người bị color blindness có thể không phân biệt được. Tương tự, chart nhiều đường chỉ khác hue có thể trở nên khó hiểu.

### Mục tiêu
Đảm bảo thông tin vẫn hiểu được khi người dùng không phân biệt được màu như bạn mong đợi.

### Lý thuyết
Màu nên **hỗ trợ** một thông điệp mà thiết kế đã truyền đạt bằng cách khác, chứ không nên là kênh duy nhất.

Ví dụ trong sách:
- Metric positive/negative: thêm icon để chỉ tăng/giảm.
- Biểu đồ: dùng khác biệt về **độ sáng/tối (contrast)** thay vì chỉ dùng các hue khác nhau, vì light-dark thường dễ phân biệt hơn.

### Khi nào áp dụng
- Status success/error.
- Chart/graph.
- Metric card.
- Form validation.
- Calendar/category/tag.

### Cách làm
1. Xác định thông tin nào hiện đang phụ thuộc hoàn toàn vào màu.
2. Thêm icon, label, pattern hoặc ký hiệu khác.
3. Với chart, tạo khác biệt bằng lightness/contrast khi có thể.
4. Kiểm tra thiết kế ở grayscale để xem thông tin còn hiểu được không.
5. Giữ màu như lớp hỗ trợ tăng tốc nhận diện.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Màu + icon/label | Chỉ đỏ/xanh để nói xấu/tốt |
| Tăng contrast giữa series | Nhiều hue có độ sáng tương tự |
| Kiểm tra grayscale | Giả định ai cũng phân biệt màu giống nhau |

### Ví dụ đúng/sai
**Sai:** +12% và -8% chỉ khác nhau bằng green/red text.

**Đúng:** Dùng mũi tên lên/xuống hoặc dấu +/-, đồng thời vẫn dùng màu để tăng tốc nhận diện.

### Lỗi thường gặp
- Tưởng thêm nhiều màu là thêm nhiều thông tin.
- Không có label trên legend/chart.
- Icon chỉ mang tính trang trí, không làm rõ nghĩa.

### Ngoại lệ
Màu vẫn rất hữu ích khi được dùng như tín hiệu bổ sung. Sách không khuyên bỏ màu, mà khuyên **không phụ thuộc vào màu một mình**.

### Checklist
- [ ] Bỏ màu đi, người dùng còn hiểu trạng thái không?
- [ ] Positive/negative có dấu hiệu khác ngoài màu không?
- [ ] Các series chart có đủ khác biệt về contrast không?
- [ ] Màu đang hỗ trợ hay đang gánh toàn bộ ý nghĩa?

### Tóm tắt
**Thiết kế phải truyền đạt ý nghĩa trước; màu chỉ nên làm thông điệp đó nhanh và rõ hơn.**

---
# Phần VII - Tạo chiều sâu

## Bài 36 - Mô phỏng một nguồn sáng nhất quán

### Vấn đề
Nhiều người thêm highlight, border và shadow theo cảm tính để làm button “nổi” hoặc input “lõm”. Khi các hiệu ứng không tuân theo cùng một logic ánh sáng, UI dễ trông giả và lộn xộn.

### Mục tiêu
Tạo cảm giác raised/inset bằng cách mô phỏng cách ánh sáng ngoài đời tác động lên bề mặt.

### Lý thuyết
Sách dùng một quy tắc nền tảng: **ánh sáng đến từ phía trên**.

- Bề mặt **raised**: cạnh trên nhận nhiều ánh sáng hơn nên sáng; phía dưới che ánh sáng nên có shadow tối.
- Bề mặt **inset**: phần mép trên bị khuất sáng nên tối; cạnh dưới hướng lên phía nguồn sáng nên sáng.

Khi nhìn màn hình, người dùng thường nhìn hơi từ trên xuống, nên các tín hiệu top-light/bottom-shadow này phù hợp với cảm nhận tự nhiên.

### Khi nào áp dụng
- Button cần cảm giác raised.
- Input, checkbox, “well” cần cảm giác inset.
- UI cần chút chiều sâu nhưng không muốn hiệu ứng nặng.

### Cách làm
1. Quyết định component cần raised hay inset.
2. Với raised: thêm top highlight nhỏ và shadow tối hơi lệch xuống.
3. Với inset: thêm dark inset shadow phía trên và highlight nhẹ phía dưới.
4. Chọn màu highlight bằng tay thay vì luôn overlay white bán trong suốt, để tránh làm màu bị mất saturation.
5. Giữ blur radius nhỏ nếu đang mô phỏng cạnh/bề mặt thật.
6. Dừng khi hiệu ứng vừa đủ để não nhận ra chiều sâu.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Giữ một hướng ánh sáng nhất quán | Component này sáng từ trên, component khác sáng từ trái |
| Shadow nhỏ, có lý do | Thêm blur lớn chỉ vì trông “fancy” |
| Mô phỏng vật lý ở mức vừa đủ | Cố làm UI giống đồ vật thật hoàn toàn |

### Ví dụ đúng/sai
**Sai:** Button có highlight dưới, shadow trên và outer glow, khiến không rõ nó nổi hay lõm.

**Đúng:** Button có cạnh trên sáng nhẹ và shadow tối nhỏ bên dưới, đủ tạo cảm giác nhô khỏi nền.

### Lỗi thường gặp
- Dùng white overlay làm highlight khiến màu gốc bị nhạt.
- Blur quá nhiều cho shadow sát bề mặt.
- Raised và inset dùng cùng một treatment.
- Tinh chỉnh quá lâu để đạt “photorealistic”.

### Ngoại lệ
Flat design có thể không cần mô phỏng ánh sáng bằng highlight/shadow. Sách xem đây là một công cụ tạo depth, không phải yêu cầu bắt buộc cho mọi style.

### Checklist
- [ ] Tôi biết component đang raised hay inset không?
- [ ] Hướng sáng của toàn UI có nhất quán không?
- [ ] Shadow có đúng phía không?
- [ ] Hiệu ứng có vừa đủ thay vì mô phỏng quá mức không?

### Tóm tắt
**Muốn depth trông tự nhiên, hãy nghĩ như một nguồn sáng đang chiếu từ trên xuống.**

---

## Bài 37 - Dùng shadow để biểu diễn elevation

### Vấn đề
Nếu shadow chỉ được chọn theo kiểu “cái nào đẹp”, các component cùng loại có thể dùng shadow khác nhau và người dùng không nhận được tín hiệu nhất quán về lớp nào đang gần họ hơn.

### Mục tiêu
Biến shadow thành một **hệ thống elevation** thay vì một hiệu ứng trang trí ngẫu nhiên.

### Lý thuyết
Shadow cho phép đặt phần tử lên một trục z ảo:
- Shadow nhỏ, blur chặt -> phần tử chỉ hơi nổi khỏi nền.
- Shadow trung bình -> dropdown/popover nổi cao hơn content.
- Shadow lớn, blur rộng -> modal gần người dùng hơn và thu hút focus mạnh hơn.

Sách khuyên tạo một tập shadow cố định; khoảng **5 mức thường đã đủ**.

### Khi nào áp dụng
- Button, card.
- Dropdown/popover.
- Modal/dialog.
- Drag-and-drop.
- Pressed state.

### Cách làm
1. Chọn shadow nhỏ nhất cho elevation thấp.
2. Chọn shadow lớn nhất cho modal/elevation cao.
3. Điền 2-3 mức ở giữa.
4. Gắn từng component vào một elevation có ý nghĩa.
5. Với drag, tăng shadow khi item được nhấc lên.
6. Với pressed button, giảm shadow hoặc bỏ shadow để tạo cảm giác bị ấn xuống.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Thiết kế shadow theo vị trí z | Chọn shadow theo sở thích từng màn hình |
| Có scale cố định | 20 shadow gần giống nhau |
| Dùng shadow thay đổi theo interaction | Pressed state vẫn “bay” cao như bình thường |

### Ví dụ đúng/sai
**Sai:** Modal và button đều dùng cùng một shadow nhỏ nên modal không tách khỏi nền.

**Đúng:** Button dùng elevation thấp, dropdown trung bình, modal cao hơn rõ ràng.

### Lỗi thường gặp
- Nghĩ shadow lớn hơn chỉ là “đẹp hơn”.
- Tăng shadow nhưng không tăng ý nghĩa elevation.
- Mỗi designer dùng một công thức shadow khác nhau.

### Ngoại lệ
Một style flat có thể biểu diễn elevation bằng color, overlap hoặc solid shadow thay vì shadow blur. Điều quan trọng là hierarchy không gian phải nhất quán.

### Checklist
- [ ] Shadow có tương ứng với độ cao của component không?
- [ ] Có một scale shadow hữu hạn không?
- [ ] Modal có cảm giác gần hơn dropdown không?
- [ ] Drag/pressed state có phản ánh chuyển động z không?

### Tóm tắt
**Đừng hỏi “shadow nào đẹp”; hãy hỏi “component này đang ở đâu trên trục z?”.**

---

## Bài 38 - Một shadow đẹp có thể gồm hai shadow

### Vấn đề
Một box-shadow duy nhất đôi khi khó vừa mềm tự nhiên ở xa vừa sắc nét gần mép element. Khi tăng blur, cạnh bị mờ; khi giảm blur, shadow lại quá cứng.

### Mục tiêu
Tách hai nhiệm vụ của shadow thành hai lớp để kiểm soát tốt hơn.

### Lý thuyết
Sách mô tả hai thành phần:

1. **Shadow lớn, mềm:** offset dọc nhiều hơn, blur lớn hơn; mô phỏng bóng do nguồn sáng trực tiếp.
2. **Shadow nhỏ, tối:** offset ít hơn, blur nhỏ; mô phỏng vùng ngay dưới object nơi ambient light khó lọt vào.

Khi object càng cao khỏi surface, shadow tối sát mép do thiếu ambient light sẽ yếu dần. Vì vậy ở elevation cao, shadow thứ hai nên rất nhẹ hoặc biến mất.

### Khi nào áp dụng
- Card cần shadow tinh tế.
- Popover/dropdown.
- Hệ thống elevation nhiều cấp.

### Cách làm
1. Tạo soft shadow lớn để định footprint tổng.
2. Thêm tight shadow nhỏ hơn để định nghĩa cạnh.
3. Ở elevation thấp, giữ tight shadow rõ hơn.
4. Khi elevation tăng, giảm dần tight shadow.
5. Kiểm tra cả shadow trên nền sáng và các surface khác nhau.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Mỗi shadow có một nhiệm vụ | Chồng shadow ngẫu nhiên đến khi “thấy đẹp” |
| Tight shadow giảm khi elevation tăng | Shadow sát mép luôn đậm ở mọi độ cao |
| Giữ soft shadow tinh tế | Dùng hai shadow đều quá tối |

### Ví dụ đúng/sai
**Sai:** Card cao nhất vẫn có viền shadow tối sắc ngay sát mép, khiến cảm giác như nó đang dính gần surface.

**Đúng:** Card thấp có tight contact shadow; modal cao có soft shadow rộng, contact shadow rất nhẹ.

### Lỗi thường gặp
- Hai shadow cùng blur/offset nên không tạo thêm kiểm soát.
- Shadow thứ hai quá đậm trông như border.
- Không thay đổi công thức theo elevation.

### Ngoại lệ
Không phải component nào cũng cần hai shadow. Với UI đơn giản, một shadow đủ tốt sẽ tốt hơn một công thức phức tạp không cần thiết.

### Checklist
- [ ] Soft shadow đang làm nhiệm vụ “bóng xa” không?
- [ ] Tight shadow đang định nghĩa cạnh gần không?
- [ ] Tight shadow có giảm ở elevation cao không?
- [ ] Tổng shadow vẫn subtle không?

### Tóm tắt
**Hai shadow hữu ích khi một lớp chịu trách nhiệm cho ánh sáng trực tiếp và một lớp cho vùng tối sát bề mặt.**

---

## Bài 39 - Flat design vẫn có thể có chiều sâu

### Vấn đề
Nhiều người hiểu “flat” là loại bỏ hoàn toàn mọi tín hiệu depth. Kết quả có thể làm các surface khó phân biệt và hierarchy không gian bị phẳng theo nghĩa tiêu cực.

### Mục tiêu
Tạo depth mà vẫn giữ thẩm mỹ flat.

### Lý thuyết
Sách đưa ra hai cách:

1. **Depth bằng màu:** với các shade cùng family, phần sáng hơn thường cảm giác gần hơn; phần tối hơn cảm giác xa/lõm hơn.
2. **Solid shadow:** shadow ngắn, lệch dọc và không blur, giúp card/button tách khỏi nền nhưng vẫn giữ vẻ graphic/flat.

### Khi nào áp dụng
- Design style không dùng gradient/blur shadow.
- Card cần tách khỏi page background.
- Input/well cần cảm giác inset bằng surface color.

### Cách làm
1. Chọn background base.
2. Dùng surface sáng hơn background để tạo cảm giác raised.
3. Dùng surface tối hơn background để tạo cảm giác inset.
4. Nếu cần thêm tách lớp, dùng shadow có offset nhưng blur = 0.
5. Giữ logic này nhất quán xuyên suốt component.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng chênh lệch shade có chủ đích | Mọi surface cùng màu và không có tín hiệu depth |
| Solid shadow khi hợp style | Thêm blur shadow chỉ vì “UI cần shadow” |
| Giữ depth tối giản | Flat = hoàn toàn không có hierarchy không gian |

### Ví dụ đúng/sai
**Sai:** Form, page background và disabled panel dùng cùng một grey, chỉ phân biệt bằng text.

**Đúng:** Card đăng nhập sáng hơn nền; vùng secondary panel tối hơn nhẹ để cảm giác lùi xuống.

### Lỗi thường gặp
- Chênh màu quá nhỏ nên không thấy.
- Chênh màu quá lớn phá subtle hierarchy.
- Dùng màu sáng/tối không nhất quán với elevation.

### Ngoại lệ
Một thiết kế siêu tối giản có thể chủ ý dùng cùng surface color và dựa vào spacing/typography. Nhưng khi cần depth, không nhất thiết phải quay lại skeuomorphism.

### Checklist
- [ ] Surface raised có sáng hơn nền không?
- [ ] Inset area có tối hơn khi phù hợp không?
- [ ] Có cần solid shadow không blur không?
- [ ] Style vẫn giữ được tinh thần flat không?

### Tóm tắt
**Flat không có nghĩa là không có depth; chỉ là bạn truyền depth bằng những tín hiệu đơn giản hơn.**

---

## Bài 40 - Overlap để tạo layer

### Vấn đề
Nếu mọi phần tử đều nằm gọn trong container riêng và không bao giờ vượt ranh giới, layout dễ trông như một chuỗi hộp phẳng, thiếu cảm giác layer.

### Mục tiêu
Dùng overlap có chủ đích để tạo quan hệ trước/sau và giúp các khu vực nối với nhau.

### Lý thuyết
Một element vượt qua ranh giới của hai background khiến não hiểu rằng nó nằm **trên** cả hai surface. Overlap có thể áp dụng ở:
- Card bắc qua hai section.
- Component cao hơn parent và nhô ra hai phía.
- Control nổi trên carousel.
- Avatar/image chồng nhau.

Với ảnh chồng nhau, sách khuyên dùng một “invisible border” cùng màu background để tạo khe nhỏ, tránh ảnh va màu trực tiếp.

### Khi nào áp dụng
- Hero chuyển sang content section.
- Pricing card/banner.
- Carousel control.
- Avatar stack.

### Cách làm
1. Xác định hai surface cần kết nối.
2. Cho một element quan trọng vượt qua đường chuyển tiếp.
3. Giữ overlap đủ rõ để tạo layer nhưng không làm layout khó hiểu.
4. Với ảnh/avatars, thêm border cùng màu background để tạo khoảng đệm thị giác.
5. Kiểm tra responsive để overlap không che nội dung.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Overlap ở điểm có ý nghĩa | Cho nhiều element đè nhau chỉ để trang trí |
| Tạo gap giữa ảnh chồng | Để ảnh có màu gần nhau va trực tiếp |
| Kiểm tra mobile | Dùng offset cố định gây vỡ layout |

### Ví dụ đúng/sai
**Sai:** Ba avatar chồng lên nhau không có separator, màu nền ảnh hòa vào nhau thành một khối khó đọc.

**Đúng:** Mỗi avatar có border cùng màu nền, vẫn thấy layer nhưng ranh giới rõ.

### Lỗi thường gặp
- Overlap che text/CTA.
- Dùng quá nhiều layer cùng lúc.
- Không xử lý responsive.
- Border ảnh chồng quá đậm, biến thành viền trang trí.

### Ngoại lệ
UI dữ liệu dày hoặc enterprise cần tối đa sự ổn định có thể ít dùng overlap. Đây là kỹ thuật tạo layer, không phải bắt buộc.

### Checklist
- [ ] Overlap có làm rõ layer không?
- [ ] Element có che nội dung quan trọng không?
- [ ] Ảnh chồng có separator đủ tinh tế không?
- [ ] Mobile layout có còn ổn không?

### Tóm tắt
**Một element đi qua ranh giới surface là cách rất mạnh để biến layout phẳng thành nhiều lớp.**

---

# Phần VIII - Làm việc với hình ảnh

## Bài 41 - Ảnh tốt quan trọng hơn việc “cứu” ảnh xấu bằng UI

### Vấn đề
Một layout tốt vẫn có thể trông nghiệp dư nếu ảnh chất lượng kém, ánh sáng xấu hoặc composition yếu.

### Mục tiêu
Đảm bảo chất lượng hình ảnh đủ tốt trước khi cố tối ưu typography, card hoặc decoration xung quanh.

### Lý thuyết
Sách nói rất thẳng: **bad photos will ruin a design**. Nếu dự án cần photography mà bạn không phải photographer giỏi, có hai hướng:
1. Thuê photographer chuyên nghiệp nếu cần nội dung rất đặc thù.
2. Dùng stock photography chất lượng cao nếu nhu cầu generic hơn.

Sách cảnh báo không nên thiết kế bằng placeholder đẹp rồi giả định sau này có thể chụp bằng điện thoại và thay vào mà chất lượng vẫn giữ nguyên.

### Khi nào áp dụng
- Real estate, food, travel, ecommerce.
- Landing page dùng hero photography.
- Profile/content card dựa nhiều vào hình.

### Cách làm
1. Quyết định ảnh là nội dung cốt lõi hay chỉ hỗ trợ.
2. Nếu cần ảnh riêng cho sản phẩm/không gian/con người, đầu tư chụp chuyên nghiệp.
3. Nếu cần ảnh minh họa chung, dùng stock chất lượng cao.
4. Test design với loại ảnh gần giống nguồn thật từ sớm.
5. Không duyệt layout dựa trên ảnh placeholder vượt xa chất lượng asset thực tế.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng ảnh thật hoặc realistic sample sớm | Dùng placeholder hoàn hảo rồi “tính sau” |
| Đầu tư lighting/composition | Nghĩ camera tốt là đủ |
| Chọn stock phù hợp nội dung | Chọn ảnh đẹp nhưng sai bối cảnh |

### Ví dụ đúng/sai
**Sai:** Card listing bất động sản dùng mockup ảnh kiến trúc tuyệt đẹp; production thay bằng ảnh tối, lệch và low-res nên toàn UI xuống chất lượng.

**Đúng:** Từ giai đoạn design đã test bằng ảnh gần với chất lượng thật và xây card chịu được điều kiện đó.

### Lỗi thường gặp
- Đổ lỗi cho UI khi asset gốc kém.
- Crop ảnh yếu khiến chủ thể bị cắt.
- Placeholder tạo kỳ vọng không thực tế.

### Ngoại lệ
Một số UI không cần photography; illustration hoặc icon có thể phù hợp hơn. Bài này áp dụng khi ảnh thật là một phần của thiết kế.

### Checklist
- [ ] Ảnh có đủ chất lượng ở kích thước hiển thị không?
- [ ] Asset production có tương đương placeholder không?
- [ ] Crop và composition có hỗ trợ content không?
- [ ] Nếu cần ảnh riêng, có nên dùng photographer không?

### Tóm tắt
**Không có amount of polish nào bù được ảnh tệ nếu photography là phần lớn diện tích UI.**

---

## Bài 42 - Text trên ảnh cần contrast ổn định

### Vấn đề
Ảnh có vùng sáng và tối thay đổi liên tục. White text có thể rõ trên vùng tối nhưng biến mất trên vùng sáng; dark text gặp vấn đề ngược lại.

### Mục tiêu
Giảm độ biến thiên của background để text luôn đọc được, thay vì đổi màu text theo từng bức ảnh.

### Lý thuyết
Sách đề xuất bốn kỹ thuật:

1. **Overlay:** black overlay giúp light text nổi; white overlay giúp dark text nổi.
2. **Lower image contrast:** giảm dynamics của ảnh; sau đó điều chỉnh brightness để bù nếu cần.
3. **Colorize:** giảm contrast -> desaturate -> thêm solid fill với multiply blend mode, giúp ảnh hòa với brand colors.
4. **Text shadow:** dùng shadow giống glow, blur lớn và không offset, để tăng contrast quanh chữ mà giữ ảnh dynamic hơn.

### Khi nào áp dụng
- Hero image có headline.
- Card có text overlay.
- Banner/campaign image.

### Cách làm
1. Đừng đổi text color ngẫu nhiên cho từng ảnh.
2. Quan sát vùng ảnh nằm sau text có biến thiên mạnh không.
3. Thử overlay đơn giản trước.
4. Nếu overlay làm cả ảnh quá tối/sáng, giảm contrast trực tiếp trên ảnh.
5. Nếu cần đồng bộ brand, colorize.
6. Nếu muốn giữ nhiều detail, thêm subtle text glow/shadow và giảm contrast ít hơn.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Làm background ổn định hơn | Cứ đổi white/dark text theo từng ảnh |
| Overlay có mục tiêu | Overlay quá mạnh làm ảnh mất giá trị |
| Text shadow blur lớn, không offset | Shadow sắc và lệch trông như hiệu ứng trang trí |

### Ví dụ đúng/sai
**Sai:** Headline trắng nằm trên hero có nửa bầu trời trắng, nên chữ mất hoàn toàn khi responsive crop thay đổi.

**Đúng:** Dùng overlay tối nhẹ hoặc giảm contrast ảnh để vùng phía sau text luôn đủ ổn định.

### Lỗi thường gặp
- Chỉ test một crop/viewport.
- Overlay giải quyết readability nhưng phá toàn bộ tonal quality của ảnh.
- Text shadow offset lớn trông cũ và nặng.

### Ngoại lệ
Nếu text được đặt trong một solid panel riêng không chồng lên ảnh, không cần can thiệp ảnh mạnh. Mục tiêu là consistent contrast ở nơi text thực sự nằm trên ảnh.

### Checklist
- [ ] Text còn đọc được ở mọi vùng crop không?
- [ ] Overlay có quá mạnh không?
- [ ] Image contrast/brightness đã cân lại chưa?
- [ ] Text shadow có subtle và không offset không?

### Tóm tắt
**Khi text trên ảnh khó đọc, nhiều lúc lỗi nằm ở ảnh chứ không nằm ở màu chữ.**

---

## Bài 43 - Mỗi hình/icon có một kích thước “được thiết kế cho nó”

### Vấn đề
Vector không bị vỡ khi scale, nhưng điều đó không có nghĩa icon 16px sẽ đẹp khi phóng lên 64px. Screenshot cũng có thể trở nên vô dụng nếu thu nhỏ quá nhiều.

### Mục tiêu
Tôn trọng **intended size** của asset và chủ động thiết kế phiên bản phù hợp cho từng kích thước.

### Lý thuyết
Sách nêu ba tình huống:

- **Không phóng icon nhỏ quá lớn:** icon 16-24px thiếu detail để trở thành illustration lớn; trông chunky.
- **Không thu screenshot quá nhỏ:** UI text 16px có thể thành vài pixel và không đọc được.
- **Không thu icon lớn xuống cực nhỏ:** logo/detail lớn khi ép thành favicon 16px sẽ thành “mush”.

Giải pháp:
- Icon nhỏ nhưng cần chiếm nhiều diện tích -> giữ icon gần size gốc, đặt trong shape/background lớn hơn.
- Screenshot -> chụp viewport nhỏ hơn, crop một phần, hoặc vẽ simplified UI.
- Small icon/favicon -> vẽ lại phiên bản tối giản ở target size.

### Khi nào áp dụng
- Feature section có icon lớn.
- Product screenshots trên marketing page.
- Logo/favicon/app icon.

### Cách làm
1. Xác định target size thực tế.
2. Hỏi asset hiện tại được vẽ/thiết kế cho size nào.
3. Nếu cần lớn hơn, thêm container thay vì chỉ scale icon.
4. Nếu screenshot quá chi tiết, crop hoặc làm simplified version.
5. Nếu icon/logo quá phức tạp ở size nhỏ, redraw phiên bản đơn giản.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Thiết kế asset theo target size | “SVG nên scale vô hạn là được” |
| Crop screenshot theo nội dung cần kể | Thu cả app xuống mức text không đọc được |
| Simplify favicon | Shrink logo chi tiết 128px xuống 16px |

### Ví dụ đúng/sai
**Sai:** Icon outline 20px được phóng lên 80px cho feature card, nhìn dày và nghèo chi tiết.

**Đúng:** Giữ icon khoảng intended size, đặt trong circle/square lớn có background color.

### Lỗi thường gặp
- Đồng nhất “không vỡ pixel” với “vẫn đẹp”.
- Screenshot marketing cố nhét toàn app.
- Không có asset variant cho small size.

### Ngoại lệ
Một illustration/vector được thiết kế để responsive ở nhiều size có thể scale tốt. Vấn đề là scale ngoài mục đích thiết kế, không phải vector bản thân nó.

### Checklist
- [ ] Asset có được vẽ cho target size không?
- [ ] Screenshot text còn đọc được không?
- [ ] Có thể crop thay vì shrink không?
- [ ] Small icon có cần simplified variant không?

### Tóm tắt
**Chất lượng scale không chỉ là độ phân giải; đó còn là lượng detail phù hợp với kích thước.**

---

## Bài 44 - Thiết kế để chịu được ảnh do người dùng upload

### Vấn đề
User-uploaded content không obey art direction của bạn. Ảnh có đủ aspect ratio, màu nền, crop và chất lượng khác nhau, dễ phá card grid hoặc hòa lẫn với background.

### Mục tiêu
Tạo “khung an toàn” để nội dung người dùng đa dạng nhưng bố cục vẫn ổn định.

### Lý thuyết
Sách tập trung vào hai vấn đề:

1. **Control shape and size:** đừng hiển thị ảnh ở intrinsic aspect ratio nếu điều đó làm layout nhảy loạn. Đặt ảnh trong fixed container và crop phần thừa; ví dụ dùng `background-size: cover`.
2. **Prevent background bleed:** nếu màu nền ảnh gần màu UI background, ảnh mất ranh giới. Thay vì border rõ, dùng subtle inner box shadow hoặc semi-transparent inner border.

### Khi nào áp dụng
- Avatar/profile.
- Marketplace/ecommerce listings.
- Social feed.
- Gallery/card grid.

### Cách làm
1. Chọn aspect ratio cho từng loại image slot.
2. Center/crop ảnh để luôn fit slot.
3. Test với ảnh cực ngang, cực dọc, nền trắng, nền tối.
4. Thêm inner shadow rất nhẹ nếu ảnh dễ bleed vào surface.
5. Nếu inset look không phù hợp, dùng semi-transparent inner border.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Fixed image container | Để mọi ảnh quyết định chiều cao card |
| Crop có chủ đích | Co kéo ảnh méo tỉ lệ |
| Inner shadow subtle | Border màu cứng dễ clash với ảnh |

### Ví dụ đúng/sai
**Sai:** Grid restaurant dùng ảnh intrinsic ratio, một card cao gấp đôi card khác làm layout rối.

**Đúng:** Tất cả ảnh nằm trong slot cùng tỷ lệ và dùng cover crop.

### Lỗi thường gặp
- Chỉ test bằng ảnh đẹp cùng kích thước.
- Border đậm quanh ảnh gây clash màu.
- Crop làm mất chủ thể vì không kiểm tra focal point.

### Ngoại lệ
Ở một gallery nơi aspect ratio bản thân ảnh là nội dung quan trọng, có thể giữ intrinsic ratio. Nhưng khi ảnh chỉ là thumbnail trong UI, ổn định layout thường quan trọng hơn.

### Checklist
- [ ] Image slot có aspect ratio cố định không?
- [ ] Ảnh portrait/landscape đều xử lý ổn không?
- [ ] Nền ảnh trắng có hòa vào UI background không?
- [ ] Inner shadow/border có đủ subtle không?

### Tóm tắt
**Bạn không kiểm soát ảnh người dùng, nhưng bạn có thể kiểm soát khung mà ảnh được phép sống trong đó.**

---
# Phần IX - Finishing touches

## Bài 45 - “Nâng cấp” những thứ mặc định trước khi thêm đồ trang trí mới

### Vấn đề
Khi UI trông hơi nhạt, phản xạ thường là thêm illustration, decorative shape hoặc một component mới. Nhưng đôi khi chính các phần tử đã có sẵn vẫn còn rất “mặc định” và chưa được khai thác.

### Mục tiêu
Tạo cảm giác polished bằng cách cải thiện những element đang hiện diện thay vì tăng độ phức tạp của layout.

### Lý thuyết
Sách đưa ra một số ví dụ:
- Bullet list -> thay bullet bằng icon phù hợp như checkmark, arrow hoặc icon theo chủ đề.
- Testimonial -> biến dấu ngoặc kép thành visual element lớn hơn, có màu.
- Link -> dùng weight/màu hoặc custom underline.
- Checkbox/radio -> dùng brand color ở selected state thay vì browser default.

Điểm chung: không phải thêm thông tin mới, mà **tạo personality từ element đã cần có**.

### Khi nào áp dụng
- Landing page trông “đúng nhưng nhạt”.
- Form có nhiều native controls.
- Testimonial, feature list, pricing section.

### Cách làm
1. Liệt kê những element mặc định: bullet, link, checkbox, radio, quote.
2. Chọn 1-2 loại đáng nâng cấp nhất.
3. Áp brand color hoặc icon có ý nghĩa.
4. Giữ treatment nhất quán ở mọi nơi cùng loại.
5. Dừng trước khi mỗi element đều trở thành decoration.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Làm element sẵn có giàu personality hơn | Thêm decoration vô nghĩa chỉ để lấp chỗ |
| Icon phù hợp nội dung | Dùng icon ngẫu nhiên cho mọi bullet |
| Brand color ở selected state | Làm control custom nhưng khó nhận biết trạng thái |

### Ví dụ đúng/sai
**Sai:** Feature list có bullet chấm tròn mặc định, phía sau lại thêm một illustration lớn chỉ để “trang trí”.

**Đúng:** Dùng check icon hoặc icon chủ đề cho từng bullet, đủ làm section có điểm nhấn mà không cần thêm layout phức tạp.

### Lỗi thường gặp
- Custom control làm mất affordance.
- Dùng quá nhiều icon khác style.
- Underline link quá dày và cạnh tranh với text.

### Ngoại lệ
Khi native controls quan trọng về consistency/accessibility của platform, có thể giữ nguyên. Tinh thần bài là tìm cơ hội nâng cấp hợp lý, không bắt buộc custom mọi thứ.

### Checklist
- [ ] Có element mặc định nào đang làm UI trông chưa polished không?
- [ ] Có thể dùng brand color thay vì thêm element mới không?
- [ ] Icon/decoration có liên quan đến nội dung không?
- [ ] Các control vẫn dễ nhận biết và dùng được không?

### Tóm tắt
**Trước khi thêm thứ mới, hãy xem những thứ đang có có thể được làm tốt hơn không.**

---

## Bài 46 - Thêm màu bằng accent border

### Vấn đề
Không phải team nào cũng có illustration hoặc photography đẹp. Một layout đúng hierarchy vẫn có thể trông hơi nhạt nếu toàn bộ surface đều trung tính.

### Mục tiêu
Thêm visual flair bằng một kỹ thuật rất đơn giản: đường viền màu nhấn ở vị trí có chủ đích.

### Lý thuyết
Accent border có thể xuất hiện:
- Trên đầu card.
- Dưới active navigation item.
- Dọc cạnh alert.
- Dưới headline.
- Dọc trên cùng của toàn layout.

Một hình chữ nhật màu nhỏ có thể khiến component trông “designed” hơn mà không cần kỹ năng illustration.

### Khi nào áp dụng
- Card trung tính.
- Active nav/tab.
- Alert/message.
- Section heading.
- App shell hoặc marketing page quá phẳng.

### Cách làm
1. Chọn một màu từ palette có sẵn.
2. Chọn một vị trí rõ vai trò: active, highlight, grouping.
3. Dùng border mảnh hoặc short accent thay vì tô cả surface.
4. Giữ cùng độ dày/logic giữa các component tương tự.
5. Kiểm tra xem accent có đang tạo hierarchy đúng không.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng accent border ở điểm có ý nghĩa | Rải đường màu lên mọi card |
| Lấy màu từ system | Thêm màu mới chỉ vì border |
| Giữ thickness nhất quán | Mỗi màn hình một kiểu accent khác nhau |

### Ví dụ đúng/sai
**Sai:** Mỗi card pricing có một border top màu khác nhau không có semantics, làm trang trở thành cầu vồng.

**Đúng:** Dùng một accent color nhất quán để đánh dấu plan nổi bật hoặc active state.

### Lỗi thường gặp
- Accent border quá dày thành block trang trí nặng.
- Dùng quá nhiều màu.
- Không có liên hệ giữa accent và state/hierarchy.

### Ngoại lệ
Nếu UI đã có ảnh, gradient, illustration hoặc color surface mạnh, accent border có thể dư thừa. Đây là giải pháp cho nơi cần chút điểm nhấn, không phải lớp bắt buộc.

### Checklist
- [ ] Border có vai trò rõ không?
- [ ] Màu có thuộc palette không?
- [ ] Accent có lặp nhất quán không?
- [ ] Có đang dùng quá nhiều accent cùng lúc không?

### Tóm tắt
**Một đường màu nhỏ, đúng chỗ, thường hiệu quả hơn một khối trang trí lớn không có lý do.**

---

## Bài 47 - Trang trí background mà không phá readability

### Vấn đề
Sau khi hierarchy, spacing và typography đã ổn, layout vẫn có thể hơi đơn điệu. Nếu giải bằng decoration quá mạnh, content lại bị lấn át.

### Mục tiêu
Thêm texture và nhịp điệu cho background nhưng vẫn giữ nội dung là focus.

### Lý thuyết
Sách đưa ra ba nhóm kỹ thuật:

1. **Đổi màu background:** dùng surface khác để tách section; có thể dùng gradient nhẹ. Với gradient, sách gợi ý hai hue không cách nhau quá khoảng 30° để kết quả tự nhiên hơn.
2. **Repeating pattern:** có thể phủ toàn nền hoặc chỉ dọc một cạnh; giữ contrast pattern/background thấp.
3. **Simple shape/illustration:** đặt shape, đoạn pattern hoặc graphic đơn giản ở vị trí cụ thể; vẫn giữ contrast thấp.

### Khi nào áp dụng
- Landing page có nhiều section trắng nối nhau.
- Pricing/feature panel cần tách nhẹ.
- Footer/CTA section cần personality.

### Cách làm
1. Chỉ chọn vài section cần khác background.
2. Bắt đầu bằng color shift nhẹ.
3. Nếu dùng gradient, giữ hai hue gần nhau.
4. Nếu dùng pattern/shape, giảm contrast đến mức content luôn thắng.
5. Kiểm tra responsive: graphic không che text hay tạo vùng rối.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Background hỗ trợ phân section | Mỗi section một kiểu decoration khác nhau |
| Pattern contrast thấp | Pattern đậm cạnh tranh với paragraph |
| Shape đơn giản | Decoration chạm/che content |

### Ví dụ đúng/sai
**Sai:** Section pricing có pattern đậm ngay sau giá và CTA, làm chữ khó đọc.

**Đúng:** Pattern rất nhạt chỉ xuất hiện ở edge hoặc vùng trống, content vẫn có contrast mạnh nhất.

### Lỗi thường gặp
- Gradient có hue cách nhau quá xa và trông rực bất ngờ.
- Pattern lặp dày gây moiré/visual noise.
- Decoration không tính đến mobile crop.

### Ngoại lệ
UI utilitarian hoặc data-dense có thể không cần decoration background. Sách đặt phần này ở “finishing touches”, nghĩa là chỉ nên dùng sau khi nền tảng đã ổn.

### Checklist
- [ ] Background có giúp tách section không?
- [ ] Contrast decoration có thấp hơn content không?
- [ ] Gradient có quá nhiều hue không?
- [ ] Mobile có giữ readability không?

### Tóm tắt
**Background có thể thú vị hơn mà không cần trở thành nội dung chính.**

---

## Bài 48 - Empty state là màn hình thật, không phải phần dư

### Vấn đề
Designer thường dành nhiều thời gian cho trạng thái đầy dữ liệu mẫu đẹp, nhưng người dùng mới lại nhìn thấy một màn hình trống đầu tiên. Nếu empty state chỉ có “No data”, trải nghiệm mở đầu sẽ rất yếu.

### Mục tiêu
Biến empty state thành một trạng thái có giá trị: giải thích, định hướng và thúc đẩy hành động tiếp theo.

### Lý thuyết
Với feature phụ thuộc user-generated content, empty state nên là **priority**. Sách đề xuất:
- Thêm illustration/image để thu hút attention.
- Nhấn mạnh CTA giúp người dùng tạo nội dung đầu tiên.
- Ẩn tabs, filters và supporting UI vô dụng cho đến khi có dữ liệu.

Empty state thường là lần đầu người dùng tương tác với feature, nên nó không nên là một khoảng trống lạnh lẽo.

### Khi nào áp dụng
- Danh sách contacts chưa có ai.
- Project/task list mới.
- Dashboard chưa có dữ liệu.
- Saved items, favorites, uploads.

### Cách làm
1. Thiết kế empty state cùng lúc với populated state.
2. Viết một câu giải thích ngắn: ở đây sẽ có gì.
3. Đặt CTA rõ để tạo item đầu tiên.
4. Thêm visual nếu giúp context thú vị hơn.
5. Ẩn filters/tabs/actions chưa có tác dụng.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| CTA tạo nội dung đầu tiên | Chỉ hiện “No data” |
| Ẩn supporting UI chưa dùng được | Hiện 10 filter cho danh sách rỗng |
| Xem empty state là first-run experience | Chờ đến cuối mới thiết kế |

### Ví dụ đúng/sai
**Sai:** Trang “Discounts” trống nhưng vẫn có filter bar, sort, pagination và table header; giữa trang chỉ có chữ “No discounts”.

**Đúng:** Ẩn UI không cần thiết, hiển thị illustration nhẹ, mô tả lợi ích và nút “Create discount”.

### Lỗi thường gặp
- CTA yếu hoặc không có.
- Empty state không giải thích người dùng nên làm gì.
- Vẫn giữ toàn bộ chrome của populated state.

### Ngoại lệ
Một số empty state do lỗi hệ thống hoặc permission khác với “chưa có dữ liệu”. Bài này nói về empty state bình thường của feature chưa có content.

### Checklist
- [ ] Người dùng có biết tại sao màn hình trống không?
- [ ] Có next action rõ không?
- [ ] Supporting UI vô dụng đã ẩn chưa?
- [ ] Empty state có cùng quality với populated state không?

### Tóm tắt
**Trạng thái rỗng thường là điểm bắt đầu của người dùng, nên hãy thiết kế nó như một màn hình chính thức.**

---

## Bài 49 - Dùng ít border hơn

### Vấn đề
Border là cách nhanh nhất để tách element, nên người mới dễ dùng border cho mọi hàng, mọi card, mọi section. Kết quả là UI đầy đường kẻ và cảm giác chật chội.

### Mục tiêu
Tạo separation bằng những tín hiệu nhẹ hơn trước khi resort to border.

### Lý thuyết
Sách gợi ý ba thay thế:

1. **Box shadow:** outline element nhẹ hơn border, đặc biệt khi surface element khác màu background.
2. **Hai background color khác nhau:** chỉ cần chênh nhẹ cũng đủ phân vùng.
3. **Thêm spacing:** khoảng cách lớn hơn giữa group là một separator không cần thêm UI.

### Khi nào áp dụng
- List/card dày đặc border.
- Dialog/form có nhiều section.
- Table-like layouts.

### Cách làm
1. Xác định border nào đang thực sự truyền đạt cấu trúc.
2. Với card/surface, thử shadow nhẹ.
3. Với hai vùng liền nhau, thử đổi surface color.
4. Với nhóm nội dung, tăng spacing giữa nhóm.
5. Chỉ giữ border nơi separation vẫn chưa đủ rõ.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Dùng spacing/background trước | Kẻ border quanh mọi thứ |
| Shadow subtle khi hợp | Shadow và border cùng lúc không cần thiết |
| Giữ border có chức năng | Giữ border vì “component mặc định có” |

### Ví dụ đúng/sai
**Sai:** Contact picker có border quanh container, border từng row, border search box, border footer và border giữa mọi group.

**Đúng:** Dùng surface/shadow cho container, spacing hoặc background nhẹ cho group; chỉ giữ line nơi thật sự cần.

### Lỗi thường gặp
- Xóa border nhưng spacing không đủ nên grouping mơ hồ.
- Dùng shadow nặng hơn cả border cũ.
- Surface color khác quá nhiều làm layout bị chia vụn.

### Ngoại lệ
Data table cần scan theo hàng/cột hoặc component có boundary quan trọng có thể vẫn cần border. Mục tiêu là **không dùng border như phản xạ đầu tiên**.

### Checklist
- [ ] Border này có nhiệm vụ gì?
- [ ] Có thể thay bằng spacing không?
- [ ] Có thể thay bằng background khác nhẹ không?
- [ ] Shadow có làm distinction tinh tế hơn không?
- [ ] UI sau khi bỏ border có dễ hiểu hơn không?

### Tóm tắt
**Separation có thể đến từ khoảng cách, surface và depth; border chỉ là một trong nhiều công cụ.**

---

## Bài 50 - Đừng để “component phải trông như thế này” giới hạn thiết kế

### Vấn đề
Chúng ta thường có hình mẫu cố định: dropdown là hộp trắng + list; table là cột dữ liệu thuần text; radio là vòng tròn cạnh label. Những khuôn này giúp nhanh nhưng cũng dễ giới hạn giải pháp.

### Mục tiêu
Giữ semantics và chức năng, nhưng cho phép presentation được thiết kế lại khi component là phần quan trọng của trải nghiệm.

### Lý thuyết
Sách minh họa:
- Dropdown có thể chia section, nhiều cột, icon, supporting text.
- Table có thể gộp các field liên quan nếu không cần sort riêng; có thể có image, status color, hierarchy.
- Radio buttons quan trọng có thể trở thành selectable cards.

Constraints rất hữu ích, nhưng đôi khi một chút tự do giúp UI tiến lên cấp độ khác.

### Khi nào áp dụng
- Navigation mega menu/dropdown.
- Data table không chỉ để tính toán thô.
- Plan picker, pricing selector, onboarding choices.
- Component quan trọng nhưng default presentation quá nghèo.

### Cách làm
1. Tách **semantics/behavior** khỏi hình dạng mặc định.
2. Hỏi: người dùng thực sự cần so sánh, chọn hay khám phá cái gì?
3. Nếu dropdown chứa nội dung phong phú, chia nhóm và thêm hierarchy.
4. Nếu table có field liên quan, gộp khi không cần sort riêng.
5. Nếu radio choice là quyết định quan trọng, chuyển thành cards có selected state rõ.
6. Đảm bảo interaction vẫn quen và dễ hiểu.

### Nên / Không nên
| Nên | Không nên |
|---|---|
| Thiết kế presentation theo nhiệm vụ | Phá semantics chỉ để trông khác |
| Gộp data liên quan khi hợp | Gộp cột cần sort/filter độc lập |
| Selectable cards cho lựa chọn quan trọng | Biến mọi radio nhỏ thành card lớn |

### Ví dụ đúng/sai
**Sai:** Chọn subscription plan bằng 4 dòng radio nhỏ dù đây là quyết định chính của màn hình.

**Đúng:** Mỗi plan là một selectable card với dung lượng, giá và trạng thái selected rõ.

### Lỗi thường gặp
- “Sáng tạo” khiến component không còn dễ nhận biết.
- Tăng visual complexity nhưng không tăng hiểu biết.
- Gộp data làm mất khả năng sort/filter cần thiết.

### Ngoại lệ
Component phổ biến, ít quan trọng hoặc cần tốc độ thao tác cao thường nên giữ pattern quen thuộc. Không phải cái gì cũng cần reinvent.

### Checklist
- [ ] Component mặc định có đang giới hạn thông tin cần truyền đạt không?
- [ ] Behavior/semantics vẫn rõ không?
- [ ] Sự thay đổi có giúp scan/chọn/so sánh tốt hơn không?
- [ ] Có đang sáng tạo chỉ để khác biệt không?

### Tóm tắt
**Pattern quen thuộc là điểm bắt đầu, không phải luật hình thức bất biến.**

---

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

# Quy trình thực hành 1 — Thiết kế một màn hình UI từ đầu

Phần này gom các nguyên tắc trong 25 bài thành một quy trình đơn giản cho người mới.

## Bước 1 — Viết nhiệm vụ người dùng
Ví dụ: “Người dùng cần tạo một hóa đơn mới.”

Đừng bắt đầu bằng sidebar, màu sắc hay logo.

## Bước 2 — Liệt kê nội dung tối thiểu
- Khách hàng
- Danh sách sản phẩm/dịch vụ
- Số lượng/đơn giá
- Tổng tiền
- Hạn thanh toán
- Nút tạo hóa đơn

## Bước 3 — Phác grayscale
Chỉ dùng khối, text giả lập và 2-3 mức xám. Chưa chọn màu thương hiệu, shadow hay icon chi tiết.

## Bước 4 — Xếp hierarchy
- Primary: tổng tiền + nút tạo hóa đơn
- Secondary: khách hàng, danh sách item
- Tertiary: ghi chú, metadata

## Bước 5 — Nhóm bằng spacing
Các field liên quan đứng gần nhau. Khoảng giữa các nhóm lớn hơn khoảng trong nhóm.

## Bước 6 — Áp hệ thống
Ví dụ:

```text
Spacing: 4, 8, 12, 16, 24, 32, 48, 64...
Type:    12, 14, 16, 18, 20, 24, 30, 36, 48...
Radius:  4, 8, 12 (ví dụ dự án tự chọn)
```

> Hai scale spacing/type đầu tiên bám theo ví dụ trong phần PDF đã đọc; scale radius ở đây chỉ là ví dụ minh họa cách giới hạn lựa chọn, không phải con số được PDF quy định trong nửa đầu.

## Bước 7 — Kiểm tra width
Form có cần full-width không? Nếu không, đặt max-width. Paragraph có quá dài không? Nếu có, giới hạn line length.

## Bước 8 — Kiểm tra typography
- Text size có nằm trong scale không?
- Font có dễ đọc ở size nhỏ không?
- Text khác size trên một hàng có nên căn baseline không?
- Line-height có hợp với font size và line length không?

## Bước 9 — Áp personality
Sau khi cấu trúc ổn, mới thêm font, màu, radius và tone phù hợp với tính cách sản phẩm.

## Bước 10 — Giảm nhiễu
Nếu UI vẫn bận, đừng thêm hiệu ứng. Hãy thử:
- làm text phụ nhẹ hơn,
- giảm background/border thừa,
- giảm emphasis của action phụ,
- bỏ label không cần thiết,
- tăng whitespace.

---

# Quy trình thực hành 2 — Hoàn thiện một màn hình sau khi layout cơ bản đã ổn

Phần này gom nửa sau của sách thành một quy trình đơn giản để bạn dùng trên một màn hình thật.

## Bước 1 - Kiểm tra typography cuối cùng
- Link có nổi đúng mức không?
- Paragraph dài đã căn trái chưa?
- Number column đã căn phải chưa?
- Heading/ALL CAPS có cần chỉnh letter-spacing không?

## Bước 2 - Chuẩn hóa palette
Tạo hoặc rà soát:

```text
Greys:      khoảng 8-10 shade nếu sản phẩm cần đủ dải
Primary:    1-2 color family, mỗi family khoảng 5-10 shade
Accents:    semantic/feature colors theo nhu cầu thật
```

Không thêm shade ngoài hệ thống chỉ vì một màn hình “thiếu đúng một màu”.

## Bước 3 - Kiểm tra accessibility của màu
- Contrast text/background có đạt ngưỡng được sách nêu không?
- Nếu nền màu phải tối quá mới đọc được white text, thử flip contrast.
- Màu có đang là tín hiệu duy nhất không?

## Bước 4 - Xác định depth
Hỏi từng component:
- Nằm cùng mặt phẳng?
- Raised nhẹ?
- Dropdown/popover?
- Modal?
- Inset?

Sau đó chọn color/shadow/elevation tương ứng thay vì thêm effect ngẫu nhiên.

## Bước 5 - Kiểm tra ảnh
- Ảnh có đủ chất lượng không?
- Text trên ảnh có contrast ổn định không?
- Screenshot/icon có đang bị scale ngoài intended size không?
- User-uploaded images có container/crop ổn định không?

## Bước 6 - Làm empty state
Đừng chờ production mới thấy danh sách rỗng. Thiết kế:
- thông điệp,
- CTA,
- illustration nếu cần,
- trạng thái ẩn của filter/tab vô dụng.

## Bước 7 - Giảm đường kẻ
Trước mỗi border, thử lần lượt:
1. spacing,
2. background khác nhẹ,
3. shadow subtle,
4. border nếu vẫn cần.

## Bước 8 - Thêm finishing touch có kiểm soát
Chọn rất ít:
- icon thay bullet,
- accent border,
- background tint/pattern,
- custom selected states.

Không cần dùng tất cả cùng lúc.

## Bước 9 - Tìm một cơ hội “thoát khỏi component mặc định”
Chỉ ở nơi thật sự quan trọng:
- dropdown giàu nội dung,
- plan selection,
- table có hierarchy,
- radio -> selectable card.

## Bước 10 - So với reference và học thêm
Sau khi hoàn thiện, đặt cạnh một UI bạn đánh giá cao và hỏi:
- Họ làm gì mà mình không nghĩ tới?
- Khác biệt nằm ở layout, type, color, shadow hay detail?

---

# Checklist tổng

## Checklist nền tảng trước khi gọi một màn hình là “ổn”

## 1. Chức năng
- [ ] Màn hình phục vụ một nhiệm vụ người dùng rõ ràng.
- [ ] Action chính dễ nhận ra.
- [ ] Không có chức năng “hứa trước” mà sản phẩm chưa hỗ trợ.

## 2. Hierarchy
- [ ] Primary / secondary / tertiary phân biệt được.
- [ ] Không phải mọi thứ đều bold, to hoặc nhiều màu.
- [ ] Action phụ không cạnh tranh với action chính.
- [ ] Destructive action không bị làm nổi quá mức khi chưa cần.

## 3. Spacing và layout
- [ ] Có spacing scale.
- [ ] Khoảng trong nhóm nhỏ hơn khoảng giữa nhóm.
- [ ] Component không bị kéo rộng chỉ vì màn hình rộng.
- [ ] Grid không ép phần tử co giãn vô lý.
- [ ] Responsive không đơn giản là thu nhỏ đồng tỷ lệ.

## 4. Typography
- [ ] Có type scale.
- [ ] Font đọc tốt ở kích thước UI.
- [ ] Paragraph không quá dài.
- [ ] Line-height phù hợp với size và width.
- [ ] Text khác size trên cùng hàng được kiểm tra baseline.

## 5. Personality và consistency
- [ ] Font, màu, radius và câu chữ cùng một hướng cảm xúc.
- [ ] Các component tương tự dùng cùng quy tắc.
- [ ] Không có hàng loạt giá trị “gần giống nhau nhưng khác nhau”.

## 6. Giảm nhiễu
- [ ] Label thừa đã được bỏ hoặc giảm emphasis.
- [ ] Icon nặng đã được cân bằng contrast.
- [ ] Border/shadow chỉ xuất hiện khi có lý do.
- [ ] Link không đồng loạt cạnh tranh bằng màu nổi.

---

## Checklist hoàn thiện

## 1. Typography
- [ ] Link phụ không cạnh tranh với CTA chính.
- [ ] Text dài căn theo hướng đọc tự nhiên.
- [ ] Number columns căn phải khi cần so sánh.
- [ ] ALL CAPS có tracking phù hợp.
- [ ] Letter-spacing chỉ được chỉnh khi có lý do.

## 2. Color system
- [ ] Có grey scale đủ dùng.
- [ ] Primary/accent colors có shade scale rõ.
- [ ] Không có hàng loạt one-off colors.
- [ ] Shade sáng/tối không bị washed out.
- [ ] Grey temperature có chủ đích.

## 3. Accessibility
- [ ] Contrast được kiểm tra, không chỉ đoán bằng mắt.
- [ ] Primary/secondary text vẫn giữ hierarchy.
- [ ] Không dùng màu là tín hiệu duy nhất.
- [ ] Positive/negative/status có icon/label/ký hiệu bổ sung.

## 4. Depth
- [ ] Hướng ánh sáng nhất quán.
- [ ] Shadow tương ứng elevation.
- [ ] Có scale shadow hữu hạn.
- [ ] Flat UI vẫn có tín hiệu layer khi cần.
- [ ] Overlap không che nội dung và vẫn ổn responsive.

## 5. Images
- [ ] Ảnh production đủ chất lượng.
- [ ] Text trên ảnh có contrast ổn định.
- [ ] Icon/screenshot không bị scale sai intended size.
- [ ] User-uploaded images được crop trong khung ổn định.
- [ ] Ảnh nền gần màu UI không bị bleed mất ranh giới.

## 6. Finishing touches
- [ ] Empty state được thiết kế nghiêm túc.
- [ ] Border thừa đã được thay bằng spacing/background/shadow khi hợp.
- [ ] Accent color được dùng tiết chế.
- [ ] Decoration background không cạnh tranh với content.
- [ ] Native/default elements chỉ custom khi có lợi ích rõ.

## 7. Học tiếp
- [ ] Tôi có thói quen phân tích quyết định bất ngờ trong design đẹp.
- [ ] Tôi có rebuild reference để luyện mắt thay vì chỉ xem.
- [ ] Mỗi lần luyện tôi ghi lại insight có thể tái sử dụng.

---

# Tóm tắt toàn bộ cuốn sách bằng 27 nguyên tắc

1. **Bắt đầu từ tính năng, không bắt đầu từ cái vỏ của app.**
2. **Giải quyết cấu trúc trước, chi tiết thị giác sau.**
3. **Thiết kế theo vòng lặp nhỏ và làm bản thật sớm.**
4. **Chọn một tính cách và giữ font, màu, radius, ngôn ngữ nhất quán với nó.**
5. **Giới hạn lựa chọn bằng hệ thống để giảm decision fatigue.**
6. **Hierarchy quan trọng hơn trang trí: không phải mọi thứ đều có trọng lượng ngang nhau.**
7. **Muốn một thứ nổi bật, đôi khi hãy giảm nhấn những thứ xung quanh.**
8. **Dùng label, màu semantics, grid và tỷ lệ như công cụ — không như luật cứng.**
9. **Whitespace và spacing truyền đạt cấu trúc, không phải diện tích lãng phí.**
10. **Đừng kéo mọi thứ rộng ra hoặc scale tất cả theo cùng tỷ lệ.**
11. **Typography cần hệ thống: type scale, font dễ đọc, line length hợp lý, baseline đúng và line-height theo ngữ cảnh.**
12. **Một UI tốt giúp người dùng biết nhìn đâu, hiểu cái gì thuộc với nhau và biết hành động nào quan trọng nhất mà không cần suy nghĩ nhiều.**
13. **Link không cần nổi bằng màu nếu weight/contrast hoặc hover đã đủ.**
14. **Căn chữ theo khả năng đọc; text dài thường cần một trục bắt đầu ổn định.**
15. **Letter-spacing là tinh chỉnh: siết heading khi cần, nới ALL CAPS để dễ đọc.**
16. **HSL giúp bạn suy nghĩ về hue, saturation và lightness thay vì mã màu rời rạc.**
17. **Palette thực tế cần nhiều family và nhiều shade hơn một dải 5 màu đẹp mắt.**
18. **Định nghĩa shade trước để tránh hàng chục màu gần giống nhau.**
19. **Lightness, saturation và perceived brightness không phải cùng một thứ.**
20. **Grey có thể warm/cool bằng cách pha hue nhẹ.**
21. **Accessibility không bắt buộc UI phải xấu; có thể flip contrast hoặc điều chỉnh hue.**
22. **Màu phải hỗ trợ thông tin, không được là cách duy nhất truyền đạt thông tin.**
23. **Depth hiệu quả đến từ logic ánh sáng, elevation, màu và overlap - không phải shadow ngẫu nhiên.**
24. **Ảnh tốt, contrast ổn định và asset đúng intended size quyết định rất nhiều đến độ polish.**
25. **Empty state, border, background và control mặc định đều là cơ hội để hoàn thiện UI.**
26. **Pattern quen thuộc là điểm bắt đầu; khi component quan trọng, presentation có thể được nghĩ lại.**
27. **Cách nâng trình lâu dài là phân tích quyết định lạ trong design tốt và tự rebuild chúng để hiểu chi tiết.**

# Phạm vi nguồn đã dùng

- PDF: **Refactoring UI — Adam Wathan & Steve Schoger**
- Phạm vi: **toàn bộ 218 trang**
- Nội dung được chuyển hóa theo trình tự của sách:
  - Starting from Scratch — trang 6-28
  - Hierarchy is Everything — trang 29-54
  - Layout and Spacing — trang 55-86
  - Designing Text — trang 87-117
  - Working with Color — trang 118-148
  - Creating Depth — trang 149-172
  - Working with Images — trang 173-190
  - Finishing Touches — trang 191-214
  - Leveling Up — trang 215-218

> Đây là bản diễn giải thực hành dành cho người mới, không phải bản dịch nguyên văn.
