# Bàn giao phần bổ sung TV1 và TV2

Bản bổ sung dựa trên commit `b2df6fd0aa85e09654abf3dfe237faa1115627e7`.
Toàn bộ file cũ được giữ nguyên. Không có sửa đổi cho TV3, TV4 hoặc TV5.

## Trong gói có gì

- `data_features/bo_sung_tv1/`: quy trình ẩn danh bổ sung, dữ liệu chia sẵn,
  bảng đặc trưng Regex, biểu đồ khảo sát, manifest/hash và 6 tin cách ly nhãn.
- `traditional_ml/bo_sung_tv2/`: lệnh chạy lại mã TV2 nguyên bản, kết quả
  tiếng Việt/UCI trong hai thư mục riêng, pipeline, bộ nạp cho TV4 và kiểm tra.
- File hướng dẫn này.

Nếu nhận file ZIP, giải nén vào GỐC bản repo đã tải từ GitHub. Vì mọi đường
dẫn đều mới, không cần ghi đè file cũ. Nếu máy bạn đã có những thư mục bổ sung
này do một lần nhận trước, giữ lại bản trước khi thay thế chúng.

## Dùng ngay cho phần của bạn

1. TV3 đọc `traditional_ml/bo_sung_tv2/README.md`; dùng các tập trong
   `traditional_ml/bo_sung_tv2/vi/data/` và `uci/data/`, không chia lại.
2. TV4 dùng `traditional_ml/bo_sung_tv2/predict.py`; mô hình đã sẵn sàng
   để gọi suy luận và chưa có API/giao diện vì đó là phần việc TV4.
3. Khi báo cáo, dùng kết quả cuối sau review: F1 spam UCI 0,9603; Việt 0,8271.
   Bộ Việt mới có split khác bản cũ; không tuyên bố tăng chất lượng bằng
   cách so trực tiếp F1 cũ và mới.

## Chạy và kiểm tra

Đã chạy bằng Python 3.13.8. Tại gốc repo:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r traditional_ml/bo_sung_tv2/requirements-train.txt
.venv\Scripts\python traditional_ml/bo_sung_tv2/check_handoff.py
```

Không phải huấn luyện lại để dùng mô hình. Muốn tái tạo dữ liệu và thí nghiệm:

```powershell
.venv\Scripts\python data_features/bo_sung_tv1/prepare_data.py
.venv\Scripts\python data_features/bo_sung_tv1/verify_source.py
.venv\Scripts\python traditional_ml/bo_sung_tv2/train_supplement.py
```

Đọc các README riêng để hiểu quy trình, file đầu ra và cách tích hợp.

## Cập nhật sau review

Đã tìm và đối chiếu nguồn công bố của bộ tiếng Việt; nội dung và nhãn khớp
sau chuẩn hóa CRLF/LF. Hồ sơ nguồn, commit, hash, giấy phép do nhà công bố
ghi và tập tuyển 150 spam + 50 ham nằm trong thư mục reports của TV1.
Đây là tuyển tập từ corpus công khai, không phải tin mới nhóm xin từ người
dùng và không phải test độc lập với mô hình Việt. Sáu tin mâu thuẫn nhãn
vẫn được cách ly. Quy tắc tự động không bảo đảm che mọi tên riêng tự do.

Bước chọn TV2 mới xét cả BoW lẫn TF-IDF, không thay thế mã gốc. Vì tuân theo
validation thay vì chọn theo test, model Việt sau review có F1 0,8271.

Bản bổ sung nằm trên máy, chưa được đẩy lên GitHub. Chỉ thêm các đường dẫn
mới nêu trên khi nhóm muốn đưa vào kho chung.
