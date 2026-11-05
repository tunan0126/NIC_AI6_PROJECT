# TV1 v2 — dữ liệu và tiền xử lý

Gói bổ sung riêng; giữ nguyên dữ liệu/code của các thành viên. Người dùng xác nhận
chưa có SMS thực tế đã rà nhãn mới, nên tiếp tục nguồn hiện có và ghi rõ giới hạn.

| Tập | Số dòng | Mục đích |
|---|---:|---|
| train | 1.834 | Học mô hình; nguồn công khai + câu phát triển tự viết |
| val | 299 | Chọn mô hình/ngưỡng; chấm riêng nguồn công khai và tự viết |
| test | 562 | Benchmark kế thừa, giữ nguyên nội dung/nhãn; đã được dùng đánh giá trước đây |
| challenge | 48 | Câu mới tự viết, đóng băng trước huấn luyện; không phải SMS thực tế độc lập |
| regression | 64 | Câu đã biết: 24 câu cũ + 40 câu kiểm tra lần trước; không dùng fit |

24 câu hồi quy cũ còn được dùng làm điều kiện phát hành sau khi ngưỡng được chọn
trên validation. Vì vậy không dùng số đúng trên hồi quy để tuyên bố khả năng tổng quát.
Mọi tập có `source`, `review_status`, `group`, `input_key`; loại trùng theo đầu vào
chuẩn hóa và ngăn train/val trùng với các tập kiểm tra. Manifest chứa SHA-256.

`vi_text_v2.py`: NFC, che định danh bằng hàm TV1 cũ, viết thường, bỏ dấu tiếng Việt,
chuẩn hóa khoảng trắng. Dùng chung khi huấn luyện/suy luận ML v2; không chứa luật
gán nhãn theo từ khóa hay câu mẫu. Bỏ dấu giúp cùng một tin có/không dấu cho cùng
đầu vào, nhưng làm mất phân biệt một số từ đồng âm; đây là đánh đổi cần báo cáo.
Đặc trưng Regex được trích trên văn bản trước bỏ dấu/viết thường để giữ tỷ lệ chữ hoa.

Nguồn kế thừa: [vietnamese_sms_dataset, commit 464a028](https://github.com/trannguyenthaituan251209/vietnamese_sms_dataset/tree/464a028878023598e16f2f344ee36f7d5d74257f),
README nguồn công bố CC BY 4.0. `full_dataset.csv` có cùng 2.991 tin với nguồn
đã có, không bổ sung được SMS mới. Chi tiết `reports/source_audit.json`.
Các câu tự viết được gắn nhãn bởi trợ lý, **chưa được con người xác nhận độc lập**.

## Rà nhãn còn lại

`reports/label_review_queue.csv` có 4 dòng nghi vấn. Người phụ trách đọc toàn ngữ
cảnh, xem tin có được người nhận yêu cầu hay không, điền `reviewer`,
`confirmed_label`, `review_status`. Không đổi nhãn chỉ vì mô hình dự đoán khác.
Nếu thiếu bối cảnh, giữ `needs_human_review`. Hiện không tự thay nhãn gốc.
Ham: hội thoại, thông báo giao dịch được yêu cầu, cảnh báo/phân tích lừa đảo.
Spam: quảng cáo không được yêu cầu, dụ nhận thưởng/đóng phí, yêu cầu OTP/mật khẩu.

## Tái tạo

Tại gốc repo, dùng Python có pandas/numpy và scikit-learn như môi trường huấn luyện:

```powershell
python data_features/bo_sung_tv1_v2/prepare_v2.py
python data_features/bo_sung_tv1_v2/audit.py
```

Đổi dữ liệu/chuẩn hóa cần huấn luyện lại, tạo hash mới và kiểm tra phát hành.
Không sửa test để làm đẹp kết quả. Bộ 150 spam từ TV1 trước vẫn là mẫu từ nguồn
kế thừa, không trở thành tập độc lập chỉ vì được xuất sang một file khác.
