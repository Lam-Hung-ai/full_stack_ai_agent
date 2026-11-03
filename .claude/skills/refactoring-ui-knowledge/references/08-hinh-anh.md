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
