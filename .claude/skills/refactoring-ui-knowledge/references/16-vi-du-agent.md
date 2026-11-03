# Ví dụ về cách một agent vận dụng nguyên tắc vào công việc

> **Ví dụ mới do skill biên soạn**, không phải các màn hình minh họa gốc từ sách. Mỗi ví dụ nêu mối liên hệ tới Bài N; để có toàn bộ lý thuyết, đúng/sai và ngoại lệ, đọc bài tương ứng trong 10 file chương.

## Ví dụ 1 — Audit dashboard với nhiều điểm tranh attention

### Input

> "Dashboard nội bộ của tôi có sidebar xanh đậm, 12 KPI card và 8 chart. Có 3 nút 'Export', 'Invite', 'Refresh' đều nền xanh. Hãy góp ý UI."

### Cách agent phải phân tích

1. **Tác vụ chính còn thiếu:** chưa biết người dùng đến để theo dõi KPI hay thực hiện công việc khác. Có thể tiếp tục bằng giả định là "xem tổng quan" và đề nghị xác nhận.
2. **Hierarchy:** nhiều KPI và chart cùng prominence có nguy cơ không có ưu tiên (B6). Không vội thêm màu mới; cân nhắc giảm nhấn nội dung phụ (B9).
3. **Sidebar:** nền đậm có thể cạnh tranh với khu vực nội dung (B9), nhưng không thể kết luận từ mô tả rằng nó chắc chắn sai.
4. **Actions:** phân loại tác vụ; `Refresh` thường tiện ích nhẹ, `Export` có thể secondary, `Invite` có thể primary nếu mục tiêu màn hình là mời người dùng — không quyết định chỉ từ từ ngữ (B13).
5. **Density:** dashboard có thể cần thông tin dày, nên không ép whitespace như landing page (B14).
6. **Data state:** cần trường hợp có ít dữ liệu, loading và chart không có kết quả (B48).

### Đầu ra mẫu

**Ưu tiên P1:** Xác định 1–3 KPI phục vụ quyết định đầu tiên; tăng weight/contrast tương đối ở nhóm này, giảm độ nổi ở phần còn lại. Bài 6, 9.

**Ưu tiên P1:** Xếp lại ba actions theo tần suất và mức quan trọng của nhiệm vụ thay vì cho cả ba cùng nền xanh. Bài 13.

**Ưu tiên P2:** Thử sidebar màu nền nhẹ/không có surface riêng để giảm cạnh tranh với nội dung. Bài 9; **không áp dụng** nếu sidebar là thao tác chính và cần điều hướng dày.

**Để xác minh:** cần ảnh chụp và mục tiêu chính của dashboard; không khẳng định vấn đề contrast khi chưa đo.

### Điều tránh

Không viết "Tô dashboard theo palette 2026, tăng border radius lên 16px, thêm shadow" trước khi hiểu người dùng nhìn chỉ số nào.

---

## Ví dụ 2 — Thiết kế màn đăng nhập từ yêu cầu một câu

### Input

> "Thiết kế trang đăng nhập cho phần mềm kế toán B2B, chỉ có email và mật khẩu."

### Cách làm dựa theo nguồn

- Từ tính năng: 2 input, action `Đăng nhập`, xử lý lỗi/quên mật khẩu (B1).
- Personality: đáng tin cậy, rõ ràng; chữ và màu nhất quán, không cần hoạt hình vui nhộn (B4).
- Layout: một card có width hạn chế, ở desktop không kéo full-width; ở mobile co trong lề an toàn (B16–18).
- Spacing: cặp label/input là một nhóm, khoảng giữa các nhóm lớn hơn (B19).
- Hierarchy: `Đăng nhập` là primary; `Quên mật khẩu` là link thứ cấp (B13, B25–26).
- Type scale: chỉ một vài size thực cần (B20); contrast và trạng thái lỗi không chỉ qua đỏ (B34–35).
- Không thiết kế kết nối SSO/đăng ký nếu chưa có chức năng (B3).

### UI spec gợi ý

```markdown
Mục tiêu: đăng nhập nhanh, ít bước và hiểu lỗi.
Thông tin: Email (label), Mật khẩu (label), Quên mật khẩu (link), Đăng nhập (primary).
Thứ bậc: tiêu đề > nút primary > field labels > trợ giúp.
Bề rộng: card không chiếm cả desktop; responsive ở màn hình hẹp.
Khoảng cách: dùng scale của sản phẩm, nhóm field tách rõ.
Trạng thái: default, focus, invalid email, sai mật khẩu, đang gửi, thành công.
Kiểm tra: chữ lỗi có text, không chỉ màu; các trường không tràn ở viewport nhỏ.
```

Các giá trị pixel chưa có là chủ ý: chưa biết design system/kích thước mục tiêu. Khi user cần code cụ thể, chọn token hoặc giá trị và đánh dấu là đề xuất.

### Điều tránh

Không thiết kế nhiều button cùng màu nổi, không chèn ảnh lớn che mất form. Không nhầm "label là phương án cuối" với "xóa label email/mật khẩu".

---

## Ví dụ 3 — Cải tiến bảng danh sách đơn hàng có nhiều viền

### Input

> "Bảng đơn hàng có viền quanh từng ô, mỗi row có avatar, tên khách, email, trạng thái, tổng tiền, nút Xem/Sửa/Xóa. Cách làm gọn lại?"

### Chẩn đoán

- Viền mọi cell tạo nhiều đường cạnh tranh; dùng spacing, background nhẹ hoặc chỉ separator cần thiết để giữ cấu trúc (B49).
- Tên khách/ID đơn nên nổi hơn email/timestamp khi đây là thông tin nhận diện (B6–7, B10).
- Icon/avatar có thể nổi quá nhiều; giảm contrast/giữ cỡ theo intended size (B12, B43).
- Xóa có thể là action tertiary trong row, nhưng nên có dialog xác nhận nổi bật khi người dùng thực sự xóa (B13).
- Status không chỉ bằng đỏ/xanh, cần label như `Đã trả`, `Chờ xử lý` (B35).

### Phương án sau

1. Giữ một separator mềm theo hàng hoặc background xen kẽ nếu nó làm phân nhóm tốt hơn; không loại bỏ mọi đường một cách mù quáng.
2. Nhóm tên + email cùng một ô; giữ khả năng sort theo các field riêng nếu nghiệp vụ cần (ngoại lệ B50).
3. Tổng tiền căn theo cột, status có label rõ, cỡ chữ thuộc type scale.
4. Nút `Xem` dễ thấy, `Sửa` phụ, `Xóa` đặt vào menu hoặc link nhẹ theo context.
5. Thử với họ tên dài, nhiều dòng, status dài và 1000 hàng.

### Cách nói chuyện tốt

"Bảng đang dùng viền để phân biệt mọi nhóm. Trước tiên giảm viền theo ô và tăng phân cấp tên khách; đây là hai thay đổi giúp quét bảng nhanh hơn (B6, B49). Nếu bảng dùng cho nhập liệu như spreadsheet, có thể cần giữ đường kẻ rõ hơn — đó là ngoại lệ sử dụng."

### Điều tránh

Không cam kết "xóa hết viền sẽ tốt" hoặc "gộp tên+email chắc chắn tốt" nếu người dùng cần sort/export hai dữ liệu độc lập.

---

## Ví dụ 4 — Text trên ảnh banner không đọc được

### Input

> "Hero banner dùng ảnh upload bất kỳ; chữ trắng trên ảnh lúc đọc được lúc không."

### Cách làm

B42–44 khuyến nghị thiết kế với tương phản chữ ổn định, đừng chỉ chọn ảnh sample đẹp. Agent có thể đề xuất một vùng phủ/overlay hoặc panel nền đủ ổn định, đổi vị trí text, crop có chủ đích hay dùng ảnh chứa khu vực ít chi tiết. Nếu chọn overlay, phải kiểm chứng trên ảnh sáng và tối thật. Khi cần, fallback về text trên nền riêng thay vì chữ trên ảnh.

**Ngoại lệ:** nếu sản phẩm yêu cầu xem ảnh gốc không bị che, dùng panel bên cạnh/ngoài ảnh tốt hơn overlay.

**Không suy đoán:** chưa có ảnh thật thì không khẳng định mức opacity cụ thể bảo đảm contrast; đó là giá trị phải thử.

---

## Ví dụ 5 — Hỏi lý thuyết dành cho người mới

### Input

> "Vì sao không nên để mọi thứ cùng màu đậm? Giải thích từng bước cho người không biết UI."

### Mẫu phản hồi theo 11 mục (nội dung rút gọn ở đây)

- **Vấn đề:** mọi thứ tranh sự chú ý và người dùng không biết đọc đâu trước.
- **Mục tiêu:** làm nội dung chính rõ hơn nội dung phụ.
- **Lý thuyết:** visual hierarchy là tầm quan trọng mà các phần tử trông như đang thể hiện (B6).
- **Khi nào:** trang có nhiều metric, navigation, button và metadata.
- **Cách làm:** xác định nội dung chính → giảm nhấn phần phụ → so sánh ở mức xám → dùng weight/contrast/size có tiết chế (B7–9).
- **Nên/không nên:** ưu tiên thông tin cần hành động / không bôi đậm tất cả label.
- **Ví dụ sai:** mọi hàng là chữ đen đậm. **Đúng:** tên/số liệu chính rõ hơn metadata.
- **Lỗi thường gặp:** chỉ làm text phụ nhỏ xíu, gây khó đọc (B7).
- **Ngoại lệ:** nhãn technical specs cần dễ tìm bằng mắt (B10).
- **Checklist:** hành động chính có thấy? text phụ có đọc được? Các cấp thông tin rõ?
- **Tóm tắt:** nhấn đúng thứ cần xem bằng cách giảm tranh attention.

**Lưu ý:** ví dụ trên dùng trình tự từ nguồn để giảng giải; khi user yêu cầu một bài đầy đủ, đọc và thể hiện đầy đủ 11 phần từ chapter file, không dựa vào lời rút gọn này.
