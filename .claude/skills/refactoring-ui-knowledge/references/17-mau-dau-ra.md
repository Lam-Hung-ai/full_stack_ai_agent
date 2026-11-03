# Mẫu đầu ra cho UI Agent

> Dùng như khuôn **linh hoạt**, không áp mọi heading lên mọi câu hỏi. Mọi đề xuất vẫn cần đọc bài liên quan và phân biệt bằng chứng với suy luận.

## Mục lục

1. Mẫu thiết kế màn hình mới
2. Mẫu audit từ screenshot
3. Mẫu refactor UI có code
4. Mẫu design system
5. Mẫu bài giảng 11 phần
6. Mẫu ghi nhận các giả định

## 1. Mẫu thiết kế UI mới

```markdown
# Đề xuất UI — [Tên tác vụ/màn hình]

## Người dùng cần gì?
- Người dùng: [...]
- Tác vụ: [...]
- Kết quả thành công: [...]
- Giới hạn sản phẩm/thiết bị: [...]

## Nội dung và thứ tự
- Nhóm 1: [nội dung và lý do]
- Nhóm 2: [...]
- Primary action: [...]
- Secondary/tertiary: [...]

## Skeleton/wireframe bằng lời
[Những khối chính và quan hệ nhóm; có thể kèm ASCII sketch nhỏ khi hữu ích]

## Visual rules
- Hierarchy: [...]
- Spacing/width: [...]
- Typography: [...]
- Color/semantic: [...]
- Depth/imagery/polish: [...]

## Responsive và trạng thái
| Tình huống | Cách UI thay đổi |
|---|---|
| Màn hình hẹp | ... |
| Nhiều dữ liệu | ... |
| Không có dữ liệu | ... |
| Lỗi/đang xử lý | ... |

## Ví dụ sai/đúng
- Sai: [...]
- Đúng: [...]

## Checklist bàn giao
- [ ] ...

## Tài liệu tham khảo trong skill
- Bài N: [tên/logic liên quan]

## Chưa xác nhận
- [...]
```

## 2. Mẫu audit giao diện đã có

```markdown
# UI review — [Màn hình]

## Điều quan sát được
[...] (phân biệt screenshot, code, diễn giải của người dùng)

## 3 vấn đề đáng sửa nhất
| Mức độ | Dấu hiệu nhìn thấy | Hệ quả | Sửa thế nào | Bài nguồn |
|---|---|---|---|---|
| P1 | ... | ... | ... | B6, B9 |

## Before → After
- [Vùng 1]: hiện tại → đề xuất; vì sao; ngoại lệ.
- [Vùng 2]: ...

## Không nên sửa ngay
[Những chỗ polish không gây vấn đề hoặc thông tin chưa đủ]

## Kiểm tra lại
- [ ] Contrast và hiển thị màu
- [ ] Mobile/desktop
- [ ] Dữ liệu dài/rỗng
- [ ] Keyboard/touch/focus

## Những điều chưa thể kết luận
[...]
```

## 3. Mẫu refactor UI có code

```markdown
## Phạm vi
Tôi sẽ thay [components] để giải quyết [tác vụ/vấn đề].

## Thay đổi
- [Component]: [đổi token/spacing/hierarchy/states]
- [Component]: [...]

## Lý do
- Bài N — [...].

## Hành vi được giữ nguyên
- [...]

## Đã kiểm chứng
- [Điều đã thực sự chạy/xem được]

## Cần kiểm chứng thêm
- [Responsive, contrast, interactions nếu chưa đo]
```

Đừng phát biểu "đã render" nếu không có công cụ; với code phải ưu tiên diff nhỏ, không tạo file/ngữ nghĩa mới không cần thiết.

## 4. Mẫu xây design system

```markdown
# UI foundations

## Personality
- 2–3 tính từ + lý do theo nhóm người dùng.

## Typography
- Font chính, scale size, weights, line-height rules.

## Spacing và sizing
- Token names, scale, ví dụ component, ngoại lệ density.

## Colors
- Brand families, shade ramp, neutrals, text/surface/status.
- Phương pháp kiểm thử contrast và dấu hiệu ngoài màu.

## Surface & depth
- Radius, border, shadow/elevation và khi dùng.

## Components
| Tên | Variants | States | Rules | Bài nguồn |
|---|---|---|---|---|
| Button | primary/secondary/tertiary | default/focus/disabled/loading | ... | B13 |

## Do/Don't
- ...

## Kiểm chứng
- ...
```

Token cụ thể phải được suy ra từ hệ hiện tại của sản phẩm hoặc được đề xuất có ghi chú; không mặc định mọi giá trị cụ thể là sách yêu cầu.

## 5. Mẫu bài giảng theo đúng Markdown nguồn

```markdown
# Bài [N] — [tên bài]

## Vấn đề
[Người mới thường làm sai ở đâu]
## Mục tiêu
[Kết quả muốn đạt]
## Lý thuyết
[Giải thích nguyên nhân và nguyên tắc]
## Khi nào áp dụng
[Ngữ cảnh]
## Cách làm
[Trình tự từng bước]
## Nên / Không nên
[Bảng đối chiếu]
## Ví dụ đúng/sai
[Ví dụ cụ thể]
## Lỗi thường gặp
[Đặc điểm của lỗi]
## Ngoại lệ
[Trường hợp không áp dụng máy móc]
## Checklist
[- [ ] ...]
## Tóm tắt
[Một câu nhớ lâu]
```

Đọc bài tương ứng trong file chương trước khi điền nội dung; đừng "sáng tác" từ chỉ một dòng trong index.

## 6. Ghi nhận assumptions, nguồn, suy luận

Khi thiếu dữ liệu, dùng ba câu ngắn:

- **Quan sát/nguồn:** "Trong ảnh ..." hoặc "Theo Bài N trong Markdown ...".
- **Giả định:** "Mình đang giả định màn này ưu tiên ...".
- **Đề xuất ứng dụng:** "Một cách triển khai có thể là ..., cần thử với ...".

Nếu có xung đột giữa style người dùng yêu cầu và lời khuyên của Markdown, trước hết bảo toàn yêu cầu người dùng cùng usability/accessibility cần thiết; nêu trade-off chứ không bí mật đổi brief.
