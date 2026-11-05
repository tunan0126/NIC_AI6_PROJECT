# TV2 v2 — học máy tiếng Việt

20 cấu hình: BoW, TF-IDF từ, TF-IDF ký tự, kết hợp từ/ký tự; mỗi biểu diễn chạy
Naive Bayes, Logistic Regression C=1/C=3, SVM hiệu chỉnh điểm và Random Forest.
Xử lý lệch lớp bằng trọng số; câu phát triển tự viết có trọng số 3.
SVM hiệu chỉnh bằng 3 fold nhóm; đặc trưng được fit trên train, không fit val/test.

Chọn theo min(F1 nguồn, F1 tự viết) trên validation, rồi mean F1 và min Precision.
Điều kiện: nguồn P≥0,90/R≥0,95; tự viết P/R≥0,90. Sau chọn ngưỡng, 24 câu hồi quy
đã biết phải không phát sinh lỗi. Không dùng test/challenge để chọn cấu hình/ngưỡng.

Đã chọn **SVM + TF-IDF từ/ký tự**, ngưỡng **0,574778065562**.
Mô hình dùng chuẩn hóa TV1 v2; không thay nhãn bằng luật từ khóa hay sửa điểm ở UI.

| Đánh giá | Precision spam | Recall spam | F1 spam | Báo nhầm ham | Bỏ sót spam |
|---|---:|---:|---:|---:|---:|
| Benchmark cũ 562 tin — ML sửa lần trước | 0,8538 | 0,8346 | 0,8441 | 19 | 22 |
| Cùng benchmark — ML v2 | 0,8819 | 0,8421 | 0,8615 | 15 | 21 |
| Challenge tự viết 48 tin — ML v2 | 0,9500 | 0,7917 | 0,8636 | 1 | 5 |
| Hồi quy đã biết 64 tin — ML v2 | 0,9688 | 0,9688 | 0,9688 | 1 | 1 |

40 câu lần kiểm tra trước: 38/40 đúng, tăng từ 34/40; đây là kiểm tra hồi quy đã
biết, không phải độ chính xác trên SMS thực tế mới. Challenge: 42/48 đúng.
Vẫn có lỗi; đọc `pred_*.csv` để xem từng trường hợp.

`attempt_initial_report.json` ghi ứng viên đầu tốt hơn trên benchmark nhưng làm sai
một câu hồi quy cũ; không phát hành ứng viên đó. Bản cuối không được chọn bằng
cách lấy điểm benchmark cao nhất. `selection.json` lưu đủ 20 cấu hình của lần cuối.

Chạy `python traditional_ml/bo_sung_tv2_v2/train.py` từ gốc repo với cùng phiên bản
dependencies của ứng dụng và pandas 3.1.1. `predict.py` nạp artifact, kiểm tra hash
model/normalizer. `version.json` khóa dataset và mã huấn luyện. Pipeline dùng
FunctionTransformer nên phải kèm `data_features/bo_sung_tv1_v2/vi_text_v2.py`.
Nhánh UCI tiếng Anh giữ nguyên artifact đã bàn giao trước đây.
