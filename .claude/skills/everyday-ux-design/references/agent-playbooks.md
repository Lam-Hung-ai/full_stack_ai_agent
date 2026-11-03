# Playbooks để agent áp dụng toàn bộ sách vào công việc UX

> Mỗi workflow là **cách ứng dụng được biên soạn** từ nguồn gốc, không nhất thiết là một quy trình có tên trong sách. Trước mỗi kết luận mang tính lý thuyết, đọc lại guide của chương và nguồn nguyên văn khi có nghi vấn.

## 0. Phân loại nhiệm vụ và chứng cứ

|Yêu cầu người dùng|Đọc ưu tiên|Cách trả lời|
|---|---|---|
|Giải thích khái niệm/sự khác biệt|`concept-atlas.md` + source chapter|Định nghĩa → phân biệt → ví dụ → điều kiện/giới hạn|
|Audit UI, flow, service|Ch1–5 + playbook A|Vấn đề cụ thể → giai đoạn thất bại → nguyên nhân UX → sửa → test|
|Thiết kế sản phẩm mới|Ch2,3,6,7 + playbook B|Goal/activity → nghiên cứu → giả thuyết → prototype → test|
|Chẩn đoán lỗi/thất bại|Ch2,4,5 + playbook C|Timeline → slip/mistake... → nguyên nhân → lớp phòng vệ|
|Thiết kế đa người dùng/khả năng tiếp cận|Ch3,4,6 + playbook D|Đa bối cảnh → constraints → xác nhận người dùng|
|Ưu tiên roadmap/đánh đổi|Ch6,7 + playbook E|Nhu cầu → lợi ích → rủi ro → chi phí → lựa chọn|
|Huấn luyện UX nhập môn|Ch1–7 + playbook F|Bài học thực hành, ví dụ, phản ví dụ, quiz, checklist|
|Trả lời “sách nói gì về X”|`source-map.md` + `source/chapter-*`|Bám nguyên văn; nêu chương/dòng, không gán lời ngoài nguồn|

## A. UX audit toàn luồng

### Input tối thiểu

Mô tả giao diện/ảnh/luồng, người dùng mục tiêu, điều họ muốn làm, môi trường (web/mobile/đồ vật), hạn chế kỹ thuật và mức rủi ro nếu biết. Nếu thiếu chi tiết, lập giả định rõ ràng, không giả làm đã quan sát sản phẩm.

### Cách chạy

1. **Reconstruct goal:** viết một câu “Trong tình huống X, nhóm Y muốn Z để đạt W”. Kiểm tra liệu Z là bước hay mục tiêu gốc; nếu chưa biết đánh dấu giả định.
2. **Map action cycle:** ghi 7 stages. Với mỗi bước, nêu câu hỏi người dùng và thông tin UI hiện có; chỗ không chứng thực đánh `chưa có bằng chứng`.
3. **Evaluate execution gulf:** người dùng thấy lựa chọn không, signifier có đúng không, mapping/ràng buộc có hợp lý không, hành động bị khóa có lý do không.
4. **Evaluate evaluation gulf:** sau thao tác nhìn thấy gì, kết quả có hiểu được không, có thể xác định thành công/lỗi, có đưa ra bước tiếp không.
5. **Check memory:** có bắt nhớ giữa các bước, giữ tiến độ khi gián đoạn, bối cảnh đa thiết bị/cộng tác?
6. **Check error robustness:** phân loại slips/mistakes, chỗ mode sai, khả năng undo, chống bấm lặp, hệ quả an toàn.
7. **Check emotion:** visceral (tin tưởng ban đầu), behavioral (trôi chảy & kỳ vọng), reflective (ghi nhớ và cảm giác kiểm soát).
8. **Check business/ethics:** tradeoff chức năng, người mua vs người dùng, featuritis, yêu cầu an toàn/xã hội.
9. **Synthesize:** bảng `dấu hiệu → bằng chứng → cơ chế → đề xuất → test`. Đừng đề xuất màu/icon khi gốc là quy trình hoặc lỗi hệ thống.
10. **Prioritize:** ưu tiên theo mức nghiêm trọng × tần suất phỏng đoán/có đo × khả năng phục hồi × độ tin cậy của chứng cứ; không đưa điểm số số học giả nếu không có dữ liệu.

### Output mặc định

|Vấn đề|Giai đoạn hành động|Nguyên tắc của sách|Bằng chứng đã có|Giải pháp|Cách kiểm chứng|
|---|---|---|---|---|---|
|Không rõ nút gửi đã hoạt động|Perceive/Interpret|Feedback, Ch1–2|Theo mô tả người dùng, chưa test|Status xử lý, kết quả và recovery|Task test mạng chậm + tỷ lệ nhấn lặp|

Kết luận theo 12 mục khi người dùng muốn báo cáo dạng giáo trình: **Vấn đề → Mục tiêu → Lý thuyết → Khi nào áp dụng → Cách làm → Nên/Không nên → Ví dụ đúng/sai → Lỗi thường gặp → Ngoại lệ → Checklist → Tóm tắt**. Có thể thêm mục Nguồn ở cuối. Không cần gò khuôn 12 mục cho câu hỏi ngắn.

## B. Thiết kế từ zero: hoạt động → flow → UI

**Giai đoạn 1 — đúng vấn đề:** đặt câu hỏi root goal, lập danh sách hoạt động (activities), mô tả nhóm người sử dụng/mua/quản trị; phân kỳ nguyên nhân, kiểm chứng thực địa khi có công cụ/dữ liệu.

**Giai đoạn 2 — hành vi người dùng:** vẽ Seven Stages, các điểm bắt đầu goal-driven / event-driven / opportunistic; nhận diện cách dùng của người mới/chuyên gia và khả năng tiếp cận.

**Giai đoạn 3 — thông tin cần thiết:** phân loại knowledge trong đầu/ngoài thế giới; tạo IA, nhãn, nhóm, mapping; những gì có thể công khai cho user, cần giữ kín.

**Giai đoạn 4 — prototype có ý nghĩa:** vẽ 2–3 phương án khác biệt thực, giải thích affordance vs signifier, feedforward & feedback, happy/error path, bảo vệ tiến độ.

**Giai đoạn 5 — test:** người dùng đại diện, kịch bản cụ thể, ghi kỳ vọng trước, dấu hiệu nhìn thấy, thao tác, lý giải sau, thời gian/lỗi, hành động phục hồi. Không gọi mẫu nhỏ là kết luận nhân quả toàn thị trường.

**Giai đoạn 6 — quyết định:** nêu lựa chọn, lý do, việc chưa kiểm chứng, tradeoffs giữa UX, kỹ thuật, tài chính, đạo đức và lộ trình theo dõi.

### Deliverables gợi ý

Problem statement, activity map, journey 7 stages, bảng kiến thức trong/ngoài đầu, inventory trạng thái UI, bảng error-recovery, phương án prototype, script usability test, decision log.

## C. Phân tích sự cố và lỗi

1. Ghi bằng sự kiện: **ai đang cố làm gì, nhìn thấy gì, đã thực hiện gì, hệ thống phản hồi gì, hậu quả**.
2. Chẩn đoán sơ bộ slip/mistake/vi phạm cố ý/chưa biết. Không kết luận trách nhiệm cá nhân từ log đơn lẻ.
3. Kiểm tra mode, distraction, handoff, thông báo, deadline, đào tạo, khả năng nhìn thấy trạng thái.
4. Dùng Five Whys **đa nhánh** để truy hệ thống (L2460–2536) và Swiss cheese để xét nhiều lớp bảo vệ (L3072–3112).
5. Thiết kế prevention, detection, recovery, learning: signifier/constraint → feedback/check → undo/fallback → reporting.
6. Với tự động hóa, giải thích ai kiểm soát khi hệ thống rơi khỏi vùng ổn định.
7. Nếu thiếu quyền/ngữ cảnh/log, nêu giả thuyết cần điều tra chứ không phán đoán.

**Mẫu khuyến nghị:** “Không nên nói người dùng thiếu cẩn thận; giao diện đặt hai tùy chọn không phân biệt dễ tạo description-similarity slip [Ch5]. Tách nhãn, tăng khác biệt, hiển thị trạng thái và hỗ trợ undo; kiểm chứng qua task test với 10 tình huống giả lập.” Số 10 chỉ là ví dụ kịch bản, **không** có ngưỡng chuẩn từ sách.

## D. Inclusive & cross-cultural UI

1. Không coi trung bình thống kê là con người thật (Ch6 L3539–3550).
2. Xem ai không thể nâng/chạm/nhìn/nghe/tương tác theo cùng cách (Affordance là quan hệ).
3. Kiểm tra chiều đọc/ẩn dụ scroll/timeline và tập quán bản địa (Ch3 L1843–1890).
4. Có thay thế cho audio-only, color-only, gesture-only khi cần; đánh giá loại trừ hoặc kỳ thị do giao diện (Ch6 L3551–3594).
5. Nếu cần tiêu chuẩn trợ năng hiện hành: chỉ khẳng định sau khi tra chuẩn ngoài; nguyên văn sách không thay thế checklist WCAG cập nhật.

## E. Roadmap, featuritis và business constraints

1. Với mỗi đề xuất, hỏi mục tiêu cuối, ai sử dụng, ai trả tiền, tần suất, rủi ro nếu thiếu.
2. Kiểm tra có cách cải tiến **flow** thay vì thêm feature mới.
3. Dự báo tác động complexity/learning/support và technical feasibility; lưu assumptions.
4. Đối với radical innovation, định nghĩa điều gì chưa thể biết ở người dùng hiện tại, lập thử nghiệm có rủi ro kiểm soát.
5. Đánh giá đạo đức và hậu quả lâu dài (thải bỏ, khóa người dùng, bảo mật, thiên vị, tuổi thọ hỗ trợ).
6. Quyết định tradeoff có chủ đích, không dùng UI thay thế chiến lược sản phẩm.

## F. Giảng dạy / thiết kế bài học toàn sách

**Lộ trình:**

1. Ch1: hỏi “nhận ra được thao tác & hiểu hệ thống không?” bằng cửa/công tắc/app.
2. Ch2: vẽ 7 stages của một hành động và phân biệt hai gulfs.
3. Ch3: thử nhớ hướng dẫn 8 bước rồi thiết kế cách để không phải nhớ.
4. Ch4: tìm 4 constraints trên một giao diện đơn giản, rồi kiểm tra khóa thao tác.
5. Ch5: phân biệt slip/mistake qua 3 kịch bản, thêm undo và lớp phòng vệ.
6. Ch6: nhận đề bài có giải pháp sẵn, truy vấn vấn đề gốc, hai diamond và prototype.
7. Ch7: phân tích đề xuất feature từ sale, chống featuritis, tính business/ethics.

**Mẫu bài học:** `Vấn đề → Mục tiêu → Khái niệm nguồn (kèm Ch và line) → Bài tập thực hành → Nên/Không nên → Đúng/Sai → Ngoại lệ → Checklist → Câu hỏi tự kiểm tra → Đáp án có lý do`.

**Mức thành thạo:**

- Beginner: nhận biết tên/định nghĩa, phân biệt cặp dễ nhầm.
- Practitioner: chẩn đoán điểm hỏng trong flow dựa trên quan sát.
- Advanced: thương lượng tradeoffs, hậu quả hệ thống, đa stakeholder và nguyên nhân liên chương.

## G. Hướng dẫn thẩm định độ tin cậy

Dùng nhãn `Nguồn gốc` nếu sự thật có trực tiếp trong tệp sách (dẫn chương + dòng); `Diễn giải ứng dụng` nếu suy luận design cho web/mobile; `Giả thuyết cần kiểm chứng` khi chưa có user data; `Thông tin ngoài sách` nếu người dùng đòi luật/chuẩn/thực trạng công nghệ. Đừng biến một ví dụ trong sách thành thống kê phổ quát hoặc ví dụ UI giả tưởng thành case study thật.

## H. Mẫu đáp án tiêu chuẩn

**Một đoạn chẩn đoán UX:**

> **Hiện tượng:** người dùng bấm Save liên tục vì màn hình không đổi. **Mục tiêu:** đảm bảo người dùng thấy trạng thái lưu và dữ liệu không lặp. **Cơ chế:** Gulf of Evaluation (Ch2) và Feedback (Ch1); hệ thống không xác nhận lệnh đã nhận. **Sửa:** phản hồi đã nhận, trạng thái lưu, hoàn tất/thất bại, nút thử lại rõ; chống gửi trùng nếu có side effect. **Kiểm chứng:** quan sát người mới trong tình huống mạng chậm, đo số lần bấm lặp và khả năng mô tả trạng thái. **Giới hạn:** chưa được xem sản phẩm thật, nên đây là giả thuyết.

**Một đoạn phản biện requirement:**

> “Thêm nút X” là giải pháp, chưa phải vấn đề. Theo **Solving the Correct Problem** và Double Diamond (Ch6), trước tiên ghi mục tiêu thực tế và hoạt động, khảo sát hành vi, sau đó thử nhiều giải pháp để tránh xây đúng tính năng nhưng giải sai nhu cầu.
