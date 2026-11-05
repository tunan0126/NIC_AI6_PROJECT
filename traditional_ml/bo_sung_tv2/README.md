# Bổ sung phần bàn giao TV2

Gói này dùng mã `TV2_hoc_may/train_ml.py` nguyên bản để chạy các thí nghiệm
và xuất sang thư mục MỚI. Không ghi đè dữ liệu, mã, notebook hay kết quả cũ.

## Kết quả của mô hình đã xuất và kiểm tra tải lại

| Bộ dữ liệu | Train / val / test | Mô hình được chọn trên validation | Precision spam | Recall spam | F1 spam |
|---|---|---|---:|---:|---:|
| UCI tiếng Anh | 3619 / 517 / 1035 | Random Forest + TF-IDF + Regex, balanced | 1,0000 | 0,9237 | 0,9603 |
| Tiếng Việt bổ sung | 1640 / 235 / 562 | Logistic Regression + BoW, balanced | 0,7531 | 0,9173 | 0,8271 |

- UCI: TP 121, TN 904, FP 0, FN 10; ngưỡng 0,5.
- Tiếng Việt: TP 122, TN 389, FP 40, FN 11; ngưỡng đọc từ `vi/model/config.json`.
- Các thí nghiệm giữ nguyên phạm vi mã TV2: 8 tổ hợp BoW/TF-IDF x 4 mô hình,
  các cách xử lý mất cân bằng (19 cấu hình hợp lệ, NB không có class_weight),
  so sánh Regex, tìm tham số, chọn ngưỡng bằng validation và CV 5-fold.
- Kết quả cuối ở `vi/results/ket_qua_cuoi.json` và
  `uci/results/ket_qua_cuoi.json`. Từng nhãn dự đoán ở `results/pred_ml_test.csv`.

Sau review, `select_complete.py` bổ sung bước chọn độc lập xét **27 ứng viên**,
gồm BoW và TF-IDF. Không sửa hàm chọn trong `TV2_hoc_may/train_ml.py`.
Tất cả ứng viên được chấm validation trước; grid search chỉ dùng train.
Danh sách đầy đủ: `results/selection_all_candidates_val.csv`.

Với tiếng Việt, BoW + Logistic Regression có F1 validation ban đầu 0,9524,
cao hơn RF + SMOTE 0,9510 nên được đưa vào tinh chỉnh/chọn ngưỡng. F1 test
cuối giảm so với bản RF cũ. Giữ đúng quy tắc chọn theo validation, không
đổi lại RF vì đã thấy điểm test cao hơn. Bản trước chọn trong nhóm TF-IDF
được giữ qua log thí nghiệm; không dùng 0,8551 làm điểm của model đang bàn giao.

Tiếng Việt đã ẩn danh bổ sung, loại trùng lại và cách ly nhóm nhãn mâu thuẫn,
nên test/validation KHÁC bản GitHub ban đầu. Không so điểm giữa hai phiên
bản dữ liệu để tuyên bố thuật toán cải thiện. UCI và tiếng Việt cũng là hai
thí nghiệm khác ngôn ngữ, không gộp điểm hay so trực tiếp để xếp hạng chất lượng dữ liệu.

## Tái chạy

Tại gốc repo, sau khi cài `requirements-train.txt`:

```powershell
.venv\Scripts\python data_features/bo_sung_tv1/prepare_data.py
.venv\Scripts\python traditional_ml/bo_sung_tv2/train_supplement.py
.venv\Scripts\python traditional_ml/bo_sung_tv2/check_handoff.py
```

Có thể thêm `--language vi` hoặc `--language uci` vào lệnh huấn luyện để chạy
một bộ. Gói UCI dùng cách chia random/stratify seed 42 tương thích bản UCI cũ.
Gói Việt dùng group-validation và kiểm tra các split KHỚP từng byte với TV1.
Không sửa `train_ml.py` cũ. Mỗi bộ có log chạy riêng `training.log`.

`train_supplement.py` gọi lại mã gốc trước, sau đó chạy bước chọn đầy đủ mới
và đối chiếu model xuất. `selection_fix.log` là log bổ sung sau review.
Các bảng A/B/C gốc là số đo từng thí nghiệm; cấu hình cuối nằm trong JSON
sau bước chọn đủ BoW/TF-IDF.

## Bàn giao TV3

- Tiếng Việt: dùng `vi/data/train.csv`, `val.csv`, `test.csv` hoặc bản giống
  hệt trong `data_features/bo_sung_tv1/data/`. Dataset ID:
  `vi-supplement-969f31901e68`.
- UCI: dùng `uci/data/train.csv`, `val.csv`, `test.csv`.
- Cột `id,text,y`; ham=0, spam=1. ID có phạm vi trong từng tập. Không chia lại.
- Chỉ học từ vựng/tokenizer từ train; chọn siêu tham số/EarlyStopping bằng val.
- Xuất `pred_dl_test.csv` gồm `id,text,y_true,y_pred,score`, cùng thứ tự test.
- Dùng `evaluate.py` của TV2 gốc để chấm tập hai lớp. Không cần viết lại phần ML.
- Test nguồn đã được nhóm xem qua ở các lần chạy trước. Ghi rõ đây là bộ
  benchmark kế thừa, không phải tập test mới hoàn toàn chưa được sử dụng.

## Bàn giao TV4

Cài `requirements-deploy.txt` của gói bổ sung và giữ nguyên cấu trúc repo.
Ví dụ tại gốc repo:

```powershell
.venv\Scripts\python traditional_ml/bo_sung_tv2/predict.py --language vi --text "Ma OTP la 123456"
.venv\Scripts\python traditional_ml/bo_sung_tv2/predict.py --language uci --text "Free prize! Call now"
```

Trong ứng dụng, import `load_model`, gọi một lần lúc khởi động rồi gọi
`predict(text, loaded)` cho từng tin. Hàm trả `label`, `score`, `threshold`,
`model_version`, `dataset_id`, `language`. Điểm mô hình là điểm dự đoán,
không phải cam kết xác suất đúng của từng tin.

- Nhánh Việt gọi đúng `privacy.redact` như lúc chuẩn bị dữ liệu.
- `model.joblib` tiếng Việt đã gồm vectorizer và bộ phân loại; bộ UCI có
  thêm Regex và cần module `TV2_hoc_may/features_regex.py` nguyên bản.
- Không tự dùng `model.predict()` rồi bỏ qua ngưỡng trong config.
- Dùng `predict.py` bổ sung: xác suất được làm tròn 12 chữ số trước so ngưỡng,
  xử lý ổn định trường hợp sát 0,5. Pipeline xuất được đặt suy luận một luồng;
  không huấn luyện lại hay chọn lại ngưỡng bằng test ở bước kiểm tra xuất.
- `training_report_before_export_check.json` giữ kết quả trước bước đối chiếu
  xuất; log huấn luyện có thể in các giá trị trung gian đó. Dùng
  `ket_qua_cuoi.json` sau kiểm tra xuất và `pred_ml_test.csv` để báo cáo.
- Chỉ mở file joblib do nhóm tạo/kiểm soát. `version.json` ghi hash mô hình,
  hash mã huấn luyện nguồn và phiên bản thư viện đã dùng.

## Tình trạng bàn giao và giới hạn

Các kiểm tra đã chạy: ẩn danh có thể áp dụng lại không đổi, dấu câu/chữ hoa
được giữ, nguồn gốc và CSV khớp hash, không trùng nội dung giữa các tập,
không trùng mẫu train/val tiếng Việt, nhóm quarantine không lọt vào split,
gói model tải lại dự đoán khớp CSV và chỉ số, và file cũ không bị sửa.

Nguồn công bố của hai CSV Việt đã được xác minh theo nội dung và nhãn sau
chuẩn hóa xuống dòng; xem `data_features/bo_sung_tv1/reports/source_verification.json`
và README TV1 để trích dẫn. Chưa kiểm toán độc lập mọi tên riêng hoặc quy
trình thu thập của nhà công bố. Không tự sửa nhãn theo kết quả dự đoán.

Mã TV2 gốc có hiển thị điểm test của các cấu hình trong bảng thí nghiệm.
Gói bổ sung giữ nguyên quy trình đó theo yêu cầu giữ mã cũ; việc chọn
mô hình/tham số/ngưỡng trong mã dựa vào validation/CV. Không diễn giải kết
quả như một nghiên cứu có test hoàn toàn chưa từng ảnh hưởng quyết định.
