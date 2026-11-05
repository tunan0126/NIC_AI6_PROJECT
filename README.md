# Đề tài 18: Phát hiện tin nhắn rác (SMS Spam) bằng Machine Learning & Deep Learning trên nền tảng Cloud

Dự án Capstone AI xây dựng hệ thống thông minh tự động phân loại tin nhắn rác SMS tiếng Việt và tiếng Anh quốc tế, ứng dụng các mô hình học máy truyền thống và học sâu hiện đại, triển khai ứng dụng web cloud với giao diện người dùng chuyên nghiệp.

---

## 🏛️ Cấu trúc dự án theo phân công thành viên

Dự án được phân bổ khoa học theo 5 vai trò thành viên:

| Thư mục | Vai trò | Trách nhiệm chính |
|---|---|---|
| [`data_features/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/data_features) | **TV1** - Dữ liệu & Đặc trưng | Thu thập, làm sạch, khử nhiễu, chuẩn hóa Unicode tiếng Việt, che giấu thông tin PII và trích xuất đặc trưng Regex. |
| [`traditional_ml/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/traditional_ml) | **TV2** - Machine Learning | Huấn luyện và đánh giá các mô hình học máy (LinearSVC, Random Forest, MultinomialNB) kết hợp TF-IDF từ và ký tự. |
| [`deep_learning/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/deep_learning) | **TV3** - Deep Learning | Xây dựng và tinh chỉnh các mạng nơ-ron học sâu (Conv1D và LSTM) xử lý chuỗi văn bản. |
| [`cloud_app/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/cloud_app) | **TV4** - Web & Cloud | Phát triển REST API, ứng dụng web Flask, giao diện SmartSMS AI responsive và đóng gói Docker container. |
| [`evaluation_deliverables/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/evaluation_deliverables) & [`docs/`](file:///D:/Capstone/NIC_AI6_PROJECT_review/docs) | **TV5** - Báo cáo & Nghiệm thu | Biên bản đánh giá hiệu năng mô hình, ma trận nhầm lẫn (Confusion Matrix), tài liệu PACT UX và slide thuyết trình. |

---

## 🚀 Hướng dẫn khởi chạy ứng dụng (TV4)

### 1. Cài đặt môi trường
Yêu cầu Python 3.10+ (khuyến nghị Python 3.11 - 3.13):

```bash
cd cloud_app
pip install -r requirements.txt
```

### 2. Chạy ứng dụng Web cục bộ
```bash
python app.py
```
Truy cập giao diện tại: `http://localhost:8080` (hoặc cổng cấu hình).

### 3. Tài khoản đăng nhập demo
* Quản trị: `admin` / `Admin@123456`
* Người dùng thử nghiệm: `demo_a` / `Demo@123456`
* Có hỗ trợ tự đăng ký tài khoản mới trực tiếp trên giao diện web.

---

## 📊 Kết quả mô hình nổi bật
* **Mô hình tiếng Việt tối ưu:** LinearSVC + TF-IDF (F1-Score đạt **0.8615**, độ chính xác vượt trội trên tập kiểm thử mở rộng).
* **Mô hình học sâu đối chiếu:** Conv1D & LSTM đạt Recall cao, nhận diện tốt các mẫu tin nhắn biến thể tinh vi.
