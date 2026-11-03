# Bộ kiểm thử năng lực của agent UX dựa trên 7 chương

> Mục đích: kiểm tra Skill có áp dụng hiểu biết thật từ nguồn, tránh trả lời qua loa hoặc trộn lẫn kiến thức ngoài. Mỗi ca gồm tiêu chí đạt, không cần lặp nguyên văn đáp án.

|ID|Câu hỏi kiểm thử|Điểm buộc phải có trong đáp án|Điều không được làm|
|---|---|---|---|
|T01|“Một nút có icon là affordance hay signifier?”|Khả năng chạm vs tín hiệu vị trí/cách chạm; Ch1 L375–476|Đồng nhất mọi icon là affordance|
|T02|“Khách bấm Gửi 5 lần vì chẳng thấy gì.”|Gulf of Evaluation, feedback, nhận lệnh/trạng thái, tránh side effect lặp|Quy người dùng thiếu kiên nhẫn|
|T03|“Nút 1/2/3 bật 3 đèn theo bố cục khác.”|Mapping không gian + kiến thức trong world|Chỉ khuyên thay màu|
|T04|“Thiết kế trải nghiệm 7 stages của thanh toán.”|Goal, plan, specify, perform, perceive, interpret, compare, pre/post info|Nhầm 7 principles là 7 stages|
|T05|“Người mới và chuyên gia cần cùng một editor.”|Tradeoff world/head + shortcut cho expert, signifier cho novice|Bắt mọi người nhớ keyboard shortcut|
|T06|“Timeline tương lai bên phải có đúng phổ quát?”|Ảnh hưởng văn hóa, chiều đọc và metaphor chuyển động|Khẳng định phổ quát|
|T07|“Chỉ cần một popup xác nhận tất cả xóa dữ liệu?”|Cảnh báo phù hợp rủi ro; undo, lock-in, chi phí habituation|Đề xuất confirm cho mọi click|
|T08|“Tôi nhấn nút sai dù biết quy trình.”|Slip vs mistake, capture/description/mode, không kết tội|Cho là mistake chắc chắn|
|T09|“AI tự động ổn nhưng khi hỏng nhân viên không biết tiếp quản.”|Paradox of automation; feedback, monitoring, handoff, skills; giả định rõ|Nói tự động hóa loại bỏ sai hoàn toàn|
|T10|“Tôi được yêu cầu tạo tính năng X ngay.”|Correct problem, double diamond, research, alternatives|Tự chốt UI theo yêu cầu|
|T11|“Ứng dụng nhiều chức năng có nên xóa 80%?”|Complexity vs confusion, activity + featuritis, tần suất/giá trị|Cho rằng tất cả tính năng ít dùng vô nghĩa|
|T12|“Sản phẩm đẹp, người dùng khó dùng, doanh thu vẫn cao.”|Visceral/behavioral/reflective; purchaser vs user; success đa chiều|Đồng nhất bán chạy với usable|
|T13|“Tôi cần toàn bộ chi tiết nhóm lỗi chương 5.”|Capture, similarity, memory, mode + rules, knowledge, lapses, violations; source lines|Chỉ nói lỗi do thiết kế chung chung|
|T14|“Tại sao chứng từ cũ thiếu dữ liệu khi bị gián đoạn?”|Working memory, prospective memory, state persistence, recover|Giải pháp chỉ đào tạo thêm|
|T15|“Design thinking Norman có đúng 5 bước cố định?”|Double diamond + iterative HCD + real world constraints|Gọi quy trình tuyến tính cứng|
|T16|“Bộ chuẩn WCAG 2026 Norman đề xuất cụ thể gì?”|Nói rõ nguồn sách không cung cấp chuẩn hiện hành; cần nguồn khác nếu muốn|Bịa tiêu chuẩn nằm trong sách|
|T17|“Viết chương trình học cho UX newbie đủ 7 chương.”|Bài học đủ chủ đề, bài tập, phản ví dụ và checklist, chỗ giao thoa|Chỉ tập trung Ch1–2|
|T18|“Phân tích thiết kế kém nhưng pháp lý yêu cầu bước khó.”|Trình bày ngoại lệ an toàn, bảo mật, anti-dark pattern, tradeoff|Khuyên loại xác thực vô điều kiện|
|T19|“Tại sao sự cố chỉ do một người bấm sai?”|Root cause, Swiss cheese, đa nguyên nhân, trách nhiệm đúng mức|Phán đoán trách nhiệm từ bề mặt|
|T20|“Chính xác từ nào Norman dùng về bếp/tủ lạnh?”|Tìm file nguồn, dẫn line cụ thể, phân biệt paraphrase|Dẫn cụm từ chưa tìm thấy|

## Thang chấm nội bộ (mỗi câu 0–3)

- **0:** Sai khái niệm hoặc bịa nguồn.
- **1:** Đúng thuật ngữ nhưng thiếu cơ chế và hành động kiểm chứng.
- **2:** Đúng cơ chế, có đề xuất hữu dụng và có nguồn phù hợp.
- **3:** Đúng cơ chế, chọn nhiều nguyên tắc liên quan, đánh dấu giới hạn/giả thuyết, đề xuất test thực tế và viện dẫn phù hợp.

Tổng điểm tối đa 60. Bộ kiểm thử này do Skill biên soạn; **không** phải thang đo chính thức của Norman hoặc nghiên cứu bên ngoài. Khi agent phản hồi chưa đạt, sửa hướng dẫn trong SKILL.md/reference tương ứng và thử lại.
