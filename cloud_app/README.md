# TV4 - ứng dụng desktop dùng ML/DL thật

Giao diện sáng xanh theo mẫu 1, phục vụ demo cho giảng viên. Đợt này bổ sung các
gói TV1/TV2/TV3 v2 riêng và cập nhật ứng dụng TV4; giữ nguyên code/model gốc
của các thành viên và các phiên bản đã bàn giao trước.
Bản UX cũ ở `bo_sung_tv4_ux` được giữ làm tài liệu thiết kế.

## Giao diện đã làm gọn theo phản hồi

Trang đầu tập trung vào nhập tin và nút kiểm tra. Mặc định Việt + ML, không cần
chọn mô hình trước. Người gửi/ngôn ngữ/DL nằm trong Tùy chọn kiểm tra. Kết quả
hiện nhãn và Báo sai trước, mở điểm/phiên bản khi cần. Hai mục chính: Kiểm tra,
Lịch sử; các chức năng phụ nằm trong Quản lý. Xem `UX_SIMPLIFIED.md` và ảnh
`screens/desktop-simple-*.png`. Bản local đã cập nhật; Ctrl+F5 nếu còn trang cũ.

Gói bàn giao hiện tại: `Bo_sung_TV1_TV4_v2_UI_gon.zip`. Gói và PDF v2 trước
được giữ làm mốc trước khi chỉnh giao diện.

## Chạy trên máy này

Mở **http://127.0.0.1:8080** khi server đang chạy. Thông tin hai tài khoản
được tạo riêng ở `instance/Tai_khoan_demo.txt`; không có mật khẩu cố định
trong code. Có thể tự đăng ký tài khoản ở màn đăng nhập nếu chưa tắt đăng ký.

Để khởi động lại, tại gốc repo:

```powershell
powershell -ExecutionPolicy Bypass -File cloud_app/bo_sung_tv4_app/start.ps1
```

Script tạo môi trường Python 3.13 riêng khi chưa có, cài dependencies, tạo
tài khoản demo nếu chưa tồn tại và chạy Waitress. Chờ dòng `TV4 ready` rồi
mở trình duyệt. Lần đầu cần mạng để cài thư viện. Không chạy đồng thời hai
server cùng cổng 8080. Nhấn Ctrl+C ở cửa sổ server để dừng.

Chạy thủ công khi đã có môi trường:

```powershell
cloud_app/bo_sung_tv4_app/.venv/Scripts/python cloud_app/bo_sung_tv4_app/app.py
```

Gói `Bo_sung_TV1_TV4_v2.zip` gom đủ các thư mục bổ sung cần chạy. Giải nén vào
gốc repo GitHub, giữ cấu trúc thư mục. ZIP không chứa venv, database, mật khẩu.
Xem `BO_SUNG_TV1_TV4_V2.md` ở gốc repo để biết phần việc từng thành viên.

## Phiên bản tiếng Việt đang chạy

ML: **SVM + TF-IDF từ/ký tự v2**, chuẩn hóa dùng chung TV1 v2, ngưỡng
0,574778065562. Trên cùng benchmark 562 tin: F1 0,8615 so với 0,8441 của bản sửa
trước; báo nhầm 19→15, bỏ sót 22→21. 40 câu hồi quy lần trước: 34→38 câu đúng.
Câu lịch họp được báo và bản không dấu hiện đều Hợp lệ; không gán nhãn cứng ở UI.

DL: **giữ Conv1D bản sửa trước**. Cả 11 ứng viên mới chưa đạt gate validation,
nên không đưa lên ứng dụng. DL còn lỗi và có thể khác ML; xem báo cáo TV3 v2.
UCI tiếng Anh giữ nguyên hai artifact trước.

`release_v2.json` chỉ kích hoạt ML v2; khóa config, metadata và phụ thuộc bằng
hash. Artifact sai hash bị từ chối, không âm thầm chuyển về model cũ. Khi thiếu
release v2, bộ nạp còn hỗ trợ bản trước. Kết quả lịch sử giữ đúng phiên bản cũ.
Các tập đã được đánh giá nhiều lần; không gọi benchmark cũ/hồi quy là test thực tế
mới. Challenge 48 câu tự viết có kết quả khác benchmark: DL F1 0,9020, ML 0,8636.
Không có mô hình thắng mọi tập. Chưa có SMS thực tế mới được rà nhãn độc lập.

## Chức năng đã triển khai

- Đăng ký, đăng nhập, đăng xuất thật. Mật khẩu băm scrypt; phiên nằm trong
  SQLite, cookie HttpOnly/SameSite. Đăng nhập xoay token; đăng xuất thu hồi phiên.
- Kiểm tra văn bản tùy ý bằng ML/DL thật, riêng tiếng Việt và UCI tiếng Anh.
  Tái dùng cách suy luận của bộ nạp TV2/TV3; model được nạp và làm nóng trước khi nhận request. Tiếng Việt dùng ML v2 và DL bản trước; tiếng Anh giữ artifact gốc.
- Hiện nhãn, điểm đầy đủ/ngưỡng thật, phiên bản, dataset và thời gian xử lý.
  Giao diện chỉ làm tròn khi hiển thị; cảnh báo khi DL cắt chuỗi.
- Quy tắc chặn/cho phép riêng theo người gửi. Mỗi người gửi chỉ có một luật;
  thay luật ngược lại phải xác nhận phiên bản hiện tại. Luật ưu tiên trước model.
- Lịch sử opt-in, phân trang/lọc, xem chi tiết và xóa nội dung. DB còn dữ liệu
  sau khi tải lại hoặc khởi động lại ứng dụng.
- Phản hồi đúng/sai có nhãn đề xuất, ghi chú và trang xem lại 100 phản hồi gần
  nhất. Phản hồi chờ rà soát; không tự retrain hay sửa nhãn train/test.
- Mỗi truy vấn/sửa/xóa kiểm tra chủ tài khoản ở server. Body `user_id` không
  quyết định chủ bản ghi. Có CSRF, kiểm tra Origin/Host, giới hạn request và CSP.
- Thử lại cùng `request_id` không lưu trùng lịch sử, kể cả hai request đồng thời.

## Demo 5-7 phút

1. Đăng nhập A ở Chrome thường; B ở cửa sổ ẩn danh hoặc máy khác.
2. A chọn mẫu spam, bật lưu, kiểm tra ML; mở thông tin model để đọc điểm/ngưỡng.
3. Đổi DL rồi kiểm tra lại. Nhãn có thể khác ML; giải thích theo kết quả thật.
4. A gửi phản hồi, vào “Phản hồi đã gửi”; B không thấy phản hồi ấy.
5. A chọn mẫu kiểm tra A/B, kiểm tra và chặn DEMO-A; kiểm tra lại để thấy nguồn
   là luật cá nhân và không có điểm model. B dùng cùng mẫu vẫn gọi model riêng.
6. A đổi luật sang cho phép, xác nhận thay thế. Xem lịch sử, tải lại, đăng xuất.

Các tin mẫu là nội dung tự tạo để trình diễn, không phải bộ đánh giá độ chính xác.
Ứng dụng phân loại tin trong giao diện; không kết nối nhà mạng hay chặn SMS hệ điều hành.

## Dữ liệu và giới hạn

`instance/tv4.sqlite3` chứa tài khoản, phiên, luật, metadata dự đoán và phản hồi.
Nội dung SMS chỉ lưu khi bật lưu lịch sử; trước khi lưu gọi `privacy.redact`
của TV1, cả email/số điện thoại trong ghi chú phản hồi cũng được che. Nhánh
UCI vẫn suy luận trên văn bản theo đúng pipeline UCI; che định danh chỉ áp
vào bản lưu, không thay cách suy luận UCI.

Khi không bật lưu, chỉ giữ metadata/ID và dấu băm yêu cầu để đối chiếu phản hồi,
chống lưu trùng. Xóa lịch sử xóa cột nội dung/người gửi đã lưu; metadata tối thiểu
và feedback vẫn được giữ. Luật lưu dấu băm khóa người gửi và tên hiển thị đã che;
không cam kết che mọi tên riêng tự do. Không ghi SMS/password vào log ứng dụng.

Phạm vi giao diện: desktop 1280×720, 1366×768, 1440×900 và 1920×1080. Không làm
mobile. Có focus, nhãn và dialog bàn phím; chưa usability test với giảng viên,
chưa xác nhận toàn bộ WCAG hoặc thử tải lớn. SQLite + một tiến trình Waitress
phù hợp phạm vi demo nhóm; chưa triển khai nhiều replica dùng database chung.

## Kiểm tra đã chạy

**44/44 kiểm tra tự động đạt:** 27 Python/API/tính toàn vẹn/hồi quy và 17
Chromium. Có đối chiếu 4 nhánh ML/DL Việt/UCI với bộ nạp thật; hai tài khoản,
quyền sở hữu, CSRF, luật cá nhân, lưu sau restart, lỗi mạng/thử lại, XSS, desktop.
Kiểm tra v2 gồm hash, train/val không trùng tập bảo vệ sau chuẩn hóa, test gốc
không đổi, Unicode NFC/NFD, có/không dấu ML cùng điểm, tái tạo dự đoán CSV,
khóa bản phát hành và giữ DL/UCI đúng phiên bản.

Log hiện tại: `tests/simple_ui_python.log`, `tests/simple_ui_browser.log`;
`tests/browser_verification.json`. Ảnh chụp thật: `screens/`.

```powershell
cloud_app/bo_sung_tv4_app/.venv/Scripts/python -m unittest discover -s cloud_app/bo_sung_tv4_app/tests -p 'test_*.py' -v
```

Browser test dùng Node.js/Playwright; `TV4_URL` phải trỏ đến server có database
kiểm thử riêng, bật đăng ký. Script tạo dữ liệu/tài khoản tự tạo; không chạy vào
môi trường đang dùng cho buổi bảo vệ. Xem `tests/browser_checks.cjs`.
Các assertion hồi quy không thay thế việc đo Precision/Recall trên SMS mới.

## Docker và cloud

Đọc `CLOUD.md` để build từ gốc repo và triển khai HTTPS trên VPS/Docker host.
Máy hiện tại chưa có Docker Engine; đã kiểm tra cấu trúc COPY/cấu hình nhưng
**chưa build hoặc chạy container**, chưa có URL cloud. Bản Python local đã chạy
và kiểm tra với mô hình thật. Không diễn giải kết quả local thành nghiệm thu cloud.

Tài liệu API: `API.md`. Bộ nạp ở `model_service.py`; mọi ngưỡng lấy từ artifact,
không thay nhãn hoặc sửa điểm để khớp tin mẫu.
