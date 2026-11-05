# Điều chỉnh giao diện: bớt lựa chọn, rõ bước tiếp theo

Phản hồi trực tiếp của người dùng: **“Quá nhiều mục và chữ, khó biết bấm đâu.”**
Phạm vi: desktop, demo cho nhóm và giảng viên; giữ hướng màu sáng xanh đã chọn.

## Thay đổi chính

| Trước | Hiện tại |
|---|---|
| 5 mục trong menu bên trái, banner và ghi chú dài | 2 mục chính trên đầu: Kiểm tra / Lịch sử; phần phụ vào Quản lý |
| Phải đọc cả người gửi, ngôn ngữ, mô hình trước khi kiểm tra | Mặc định Việt + ML; mở Tùy chọn kiểm tra khi cần đổi |
| Kết quả chen nhãn, điểm, phiên bản, giải thích, luật | Nhãn và Báo sai hiện trước; điểm/model và luật mở rộng khi cần |
| Lịch sử xem trước chiếm thêm một khối ở trang kiểm tra | Xem lịch sử ở trang riêng |
| Tin mẫu luôn tự điền cả người gửi | Mẫu thường chỉ điền nội dung; mẫu A/B mới điền DEMO-A |
| Gửi feedback chỉ có thông báo chung | Xác nhận ngay ở kết quả, có nút Xem phản hồi |

Luồng thường: **nhập/dán tin hoặc chọn mẫu → Kiểm tra tin nhắn → đọc nhãn**.
Một nút chính màu xanh. Không phải mở tùy chọn trước khi dùng.
Nút Xóa nội dung chỉ xóa bản nháp, giữ lựa chọn mô hình/ngôn ngữ/trạng thái lưu.
Đổi đầu vào hoặc lựa chọn lưu hủy kết quả/yêu cầu thử lại cũ để tránh hiểu nhầm.
Mở/đóng tùy chọn không làm mất bản nháp.

Chức năng phụ vẫn truy cập được:

- Lịch sử: mục trên đầu.
- Chặn/Cho phép, Phản hồi, Hướng dẫn demo: menu Quản lý.
- Chọn DL/tiếng Anh/người gửi/mẫu A-B: Tùy chọn kiểm tra.
- Điểm, ngưỡng, phiên bản, dataset: Điểm và thông tin mô hình dưới kết quả.
- Đã nhập người gửi: Quy tắc người gửi dưới kết quả; khi luật đang quyết định,
  phần này mở sẵn để người dùng có thể thay luật.

## Kiểm tra thực tế

17/17 kịch bản Chromium đạt, bao gồm 13 luồng cũ được điều chỉnh theo vị trí điều
khiển mới và 4 kiểm tra UX: màn hình mặc định gọn; chọn mẫu/kiểm tra không cần
cấu hình; mở chi tiết/menu bằng bàn phím; xóa bản nháp giữ tùy chọn.
27/27 kiểm tra Python/API/tính toàn vẹn/hồi quy vẫn đạt. Tổng **44/44**.
Độ rộng kiểm tra: 1280, 1366, 1440, 1920; nút kiểm tra thấy được ở 1366×768.
Có kiểm tra hai tài khoản, lưu/xem lại lịch sử, quyền sở hữu, feedback, luật,
retry không trùng, đăng nhập/đăng xuất, XSS và CSP.

Log: `tests/simple_ui_python.log`, `tests/simple_ui_browser.log`,
`tests/browser_verification.json`. Ảnh chụp: `screens/desktop-simple-*.png`.
Các kiểm tra này xác nhận hành vi và bố cục; chưa phải usability test với giảng
viên thật. Cần người dùng thử trực tiếp để xác nhận trải nghiệm phù hợp.

TV1/TV2/TV3, artifact, ngưỡng và API suy luận không thay đổi trong đợt chỉnh UI.
Gói `Bo_sung_TV1_TV4_v2.zip` và PDF v2 trước là mốc bàn giao trước khi chỉnh giao
diện; gói mới có hậu tố `_UI_gon`. Tài liệu PACT cũ được giữ làm mốc thiết kế ban đầu.
