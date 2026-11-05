# Nguồn dữ liệu bổ sung cho bản sửa TV4

Các câu trong train_authored.csv và validation_authored.csv do trợ lý viết để
bổ sung những ngữ cảnh thiếu trong dữ liệu gốc: học tập, lịch hẹn, gia đình,
bạn bè, tin cảnh báo an toàn và các mẫu quảng cáo/lừa đảo tương ứng.
Không phải SMS mới thu thập từ người dùng; không cộng vào chỉ tiêu TV1.
Nhãn do người viết gán theo nội dung. Cần nhóm/giảng viên rà lại trước nghiên cứu chính thức.

Hai file được tách theo câu viết riêng; không chia ngẫu nhiên các bản sao.
Câu lỗi người dùng báo và bộ vi_semantic_cases.json không được đưa vào train/validation.
Validation tự tạo chỉ phục vụ phát triển; không đại diện lưu lượng SMS thật.
Benchmark gốc giữ nguyên; kết quả bản sửa phải báo riêng với TV2/TV3.
