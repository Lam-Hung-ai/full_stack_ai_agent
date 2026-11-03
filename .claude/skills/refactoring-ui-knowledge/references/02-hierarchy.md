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
