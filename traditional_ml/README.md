# TV2 - Học máy truyền thống (Traditional Machine Learning)

Thư mục này chứa toàn bộ các mô hình học máy truyền thống (LinearSVC, Random Forest, MultinomialNB,...) kết hợp trích xuất đặc trưng TF-IDF (từ & ký tự) để phân loại tin nhắn rác SMS.

## Cấu trúc thư mục
- `model/`: Mô hình tối ưu được lựa chọn cho tiếng Việt (LinearSVC với trích xuất TF-IDF đa n-gram).
  - `model.joblib`: File trọng số mô hình đã qua tinh chỉnh.
  - `config.json`: Cấu hình tham số và ngưỡng phân loại tối ưu (threshold: 0.575).
  - `version.json`, `selection.json`: Báo cáo chọn mô hình và định danh hash.
- `uci/`: Mô hình đối chiếu trên tập dữ liệu tiếng Anh quốc tế (UCI SMS Spam Dataset).
- `predict.py`: Script giao diện chung nạp mô hình và thực hiện dự đoán suy luận cho cả tiếng Việt và tiếng Anh.
- `train_ml.py`: Mã nguồn huấn luyện mô hình và tối ưu hóa tham số.
- `features_regex.py`: Module trích xuất đặc trưng số lượng liên kết, số điện thoại, từ khóa nhạy cảm.
- `results/`: Biểu đồ phân tích độ chính xác, ma trận nhầm lẫn (Confusion Matrix), đường cong PR và phân bố nhãn.
