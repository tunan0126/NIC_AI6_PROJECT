# TV4 - UX cho demo và giảng viên

Đây là bộ thiết kế UX desktop theo mẫu sáng xanh người dùng đã chọn.
Phạm vi đã chốt: chỉ máy tính, kiểm tra 1280×720, 1366×768, 1440×900 và
1920×1080; không có giao diện mobile. Ưu tiên demo cho giảng viên. Chỉ thêm thư mục
`cloud_app/bo_sung_tv4_ux/`, không sửa code hoặc mô hình của thành viên khác.

## Mở và thử

Mở `index.html` bằng Chrome/Edge. Không cần cài thư viện để xem nguyên mẫu.
Nếu trình duyệt hạn chế tính năng trên file local, chạy từ thư mục này:

```powershell
py -m http.server 8765 --bind 127.0.0.1
```

Rồi mở `http://127.0.0.1:8765`.

1. Chọn **Mẫu spam**, chọn ML hoặc DL, bấm kiểm tra.
2. Bật lưu nếu muốn thấy bản ghi trong lịch sử riêng.
3. **Báo sai** mở hộp chọn nhãn và ghi chú; Escape hoặc Hủy để thoát.
4. **Mẫu kiểm tra A/B**: ở A, kiểm tra rồi chặn người gửi DEMO-A.
   Kiểm tra lại để thấy luật cá nhân. Đổi B và chọn cùng mẫu để đối chiếu.
5. Mở mục mô phỏng kiểm thử bên dưới form để thử lỗi kết nối và thử lại.
6. Xem **Kịch bản demo** để diễn tập đủ luồng hoặc đặt lại dữ liệu.

Đổi đầu vào/model/người gửi/ngôn ngữ làm kết quả cũ hết hiệu lực. Đổi tài khoản
xóa bản nháp, lỗi và kết quả, nhưng giữ danh sách riêng của từng A/B trong phiên.

## Phạm vi thật của nguyên mẫu

- **Có:** giao diện desktop, form và trạng thái tương tác, feedback modal,
  lịch sử opt-in, quy tắc chặn/cho phép, mô phỏng A/B, kịch bản demo.
- **Giả lập:** kết quả và độ trễ của đúng ba tin mẫu. Nội dung tùy ý được báo
  là cần kết nối mô hình thật; không dùng bộ từ khóa thay cho ML/DL.
- **Chưa có:** API, database, đăng nhập thật, cloud, kiểm soát quyền ở server,
  đồng bộ nhiều máy và phân loại bằng gói mô hình thật.
- Không dùng dropdown A/B để chứng minh bảo mật. Bản thật cần hai phiên đăng
  nhập và kiểm tra quyền đọc/sửa/xóa với mọi API liên quan.
- Dữ liệu chỉ ở bộ nhớ của tab, không gửi mạng, không lưu localStorage; tải
  lại sẽ mất. Dùng tin tự tạo khi trình chiếu. Quy tắc và feedback cũng chỉ
  là dữ liệu phiên; chưa có backend lưu lâu dài.
- Hàm che định danh trong nguyên mẫu là bản đơn giản để minh họa lịch sử.
  Khi tích hợp phải gọi đúng `privacy.redact` của TV1 trên server; không lấy
  helper này thay pipeline TV1 hoặc tuyên bố đã che mọi định danh.

## Tài liệu

- `docs/TV4_UX_PACT_va_quy_trinh.pdf`: tài liệu 12 trang dễ đọc.
- `docs/UX_PACT_QUY_TRINH.md`: nội dung thiết kế có thể chỉnh sửa.
- `docs/AUDIT_MAU_1.md`: audit đầy đủ ba checklist, dựa trên ảnh concept.
- `docs/usability_observations.csv`: mẫu ghi trống cho 5 người × 5 tác vụ.
- `docs/contrast_check.json`: phép tính tương phản các cặp màu thiết kế.
- `screens/`: ảnh concept và ảnh chụp nguyên mẫu desktop/dialog.
- `tests/verification.json`: kết quả kiểm tra tự động nguyên mẫu.

Persona, nhu cầu chi tiết và mục tiêu thời gian là giả thuyết thiết kế. Chưa
phỏng vấn giảng viên hoặc chạy usability test với người thật. Các số PASS
chỉ thuộc kiểm tra phần mềm, không thay kết quả nghiên cứu người dùng.

## Chạy lại kiểm tra nguyên mẫu

Cần Node.js, Playwright và Chromium trong môi trường kiểm thử. Sau khi mở
server local ở trên, dùng môi trường có sẵn Playwright để chạy:

```powershell
node tests/ux_checks.cjs
```

Nếu Playwright được cài ngoài thư mục hiện tại, đặt `PLAYWRIGHT_MODULE` bằng
đường dẫn module. `UX_URL` tùy chọn đổi địa chỉ server. Script kiểm tra luồng
và xuất lại JSON/ảnh; không kiểm tra model hoặc API thật.

## Bước tiếp theo

Chạy 5 tác vụ trong tài liệu với 5 người thật, ghi vấn đề và sửa trước khi
triển khai API/DB/auth/cloud. TV4 sở hữu phần ứng dụng; TV5 nhận tài liệu,
URL và minh chứng sau nghiệm thu để tổng hợp báo cáo. Không sửa code TV1-TV3.
