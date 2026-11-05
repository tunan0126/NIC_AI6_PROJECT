# TV1 - Tiền xử lý dữ liệu và Trích xuất đặc trưng (Data Features)

Thư mục này đảm nhiệm toàn bộ quy trình tiền xử lý văn bản, khử nhiễu, mã hóa và trích xuất đặc trưng cho đề tài Phân loại SMS Spam.

## Cấu trúc thư mục
- data/: Toàn bộ tập dữ liệu SMS (tiếng Việt và đối chiếu tiếng Anh) đã gán nhãn, làm sạch và chia train/val/test.
  - clean_v2.csv, meta_v2.csv: Bộ dữ liệu đã khử nhiễu chuẩn hóa mới nhất.
  - 	rain.csv, al.csv, 	est.csv: Các tập dữ liệu phân chia chuẩn.
- i_text.py / i_text_v2.py: Bộ chuẩn hóa ký tự tiếng Việt Unicode, xử lý dấu thanh, viết tắt và tokenize.
- privacy.py: Module che giấu thông tin định danh cá nhân (số điện thoại, email, URL).
- prepare_data.py: Script pipeline thực hiện tiền xử lý và trích xuất đặc trưng Regex.
- udit.py: Kiểm tra tính toàn vẹn và phân bố nhãn của dữ liệu.
