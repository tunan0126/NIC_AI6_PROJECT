# TV3 học sâu cho đề tài 18

Gói này làm trọn phần học sâu: chuẩn bị biểu diễn chuỗi, LSTM và Conv1D bằng
Keras, huấn luyện trên UCI và tiếng Việt, so sánh ML/DL, lưu mô hình và bộ
từ vựng, xuất dự đoán/biểu đồ và bộ nạp cho TV4. Chỉ thêm thư mục TV3 mới;
không sửa file của các thành viên khác.

## 1 Kết quả đã chạy

Các chỉ số dưới đây tính riêng cho lớp spam, cùng test với mô hình ML TV2
trong gói bổ sung. Mô hình DL được chọn bằng F1 validation, không chọn theo test.

| Bộ | Mô hình | Precision | Recall | F1 spam | FP | FN |
|---|---|---:|---:|---:|---:|---:|
| Tiếng Việt | ML TV2 | 0,7531 | 0,9173 | 0,8271 | 40 | 11 |
| Tiếng Việt | LSTM | 0,7289 | 0,9098 | 0,8094 | 45 | 12 |
| Tiếng Việt | Conv1D | 0,7562 | 0,9098 | 0,8259 | 39 | 12 |
| UCI | ML TV2 | 1,0000 | 0,9237 | 0,9603 | 0 | 10 |
| UCI | LSTM | 0,9077 | 0,9008 | 0,9042 | 12 | 13 |
| UCI | Conv1D | 0,9375 | 0,9160 | 0,9266 | 8 | 11 |

Sau sửa chuẩn hóa Unicode và huấn luyện lại, validation chọn LSTM cho tiếng
Việt và Conv1D cho UCI. Dù Conv1D có điểm test Việt cao hơn LSTM, vẫn giữ
lựa chọn theo validation. ML TV2 có F1 test cao hơn cả hai mô hình DL ở cả
hai bộ. Không thay đổi nhãn hoặc chọn cấu hình theo điểm test.

Kết quả chi tiết: `vi/results/summary.json`, `uci/results/summary.json` và
`*/results/comparison_ml_dl.csv`. `test_by_template.csv` phân tích riêng tin
có mẫu đã thấy trong train/val và mẫu mới; đây là phân tích sau khi khóa mô hình.

## 2 Dữ liệu và tiền xử lý

Cần có gói bổ sung TV1/TV2 trước khi dùng gói này.

| Bộ | Đọc split từ | train / val / test | Độ dài chuỗi | Từ vựng |
|---|---|---|---:|---:|
| Việt | `traditional_ml/bo_sung_tv2/vi/data/` | 1640 / 235 / 562 | 80 | 6373 |
| UCI | `traditional_ml/bo_sung_tv2/uci/data/` | 3619 / 517 / 1035 | 33 | 10797 |

Mỗi file có `id,text,y`, ham=0 và spam=1. Không chia lại hoặc trộn dữ liệu hai
ngôn ngữ. Script kiểm tra ID/nội dung/nhãn test khớp dự đoán ML trước khi chạy.
Hash CSV nguồn được lưu vào `model_config.json`.

1. `TextVectorization` tách token theo khoảng trắng; tiếng Việt dùng hàm
   `unicode_lower` chung với bộ nạp, gọi `tf.strings.lower(..., encoding="utf-8")`.
   UCI giữ cách chuẩn hóa `lower` của bản trước. Cả hai đều giữ dấu câu/thẻ.
2. `adapt()` CHỈ nhận train. Validation/test có từ mới thì nhận token OOV
   `[UNK]` (ID 1), không thêm vào từ vựng. ID 0 dành cho padding.
3. Chiều dài lấy percentile 95 số token của train, giới hạn 24-160. Chuỗi
   ngắn đệm 0 ở cuối; chuỗi dài bị cắt. Đây là lựa chọn triển khai của gói.
4. Lưu toàn bộ vocabulary và cấu hình trong `preprocessing.json`, để lúc
   dự đoán dùng đúng ID đã học, không học lại bộ xử lý trên tin mới.
5. Với tiếng Việt, dữ liệu đã qua ẩn danh TV1. `predict_dl.py` gọi cùng
   `privacy.redact` khi nhận tin mới. Không dùng quy tắc Việt cho UCI.

## 3 Kiến trúc và huấn luyện

**LSTM:** Input số nguyên -> Embedding 64 chiều, mask_zero=True -> LSTM 32
nút, return_sequences=False -> Dropout 0,3 -> Dense 1, sigmoid.

**Conv1D:** Input số nguyên -> Embedding 64 chiều -> Conv1D 64 filters,
kernel 5, ReLU -> MaxPooling1D 2 -> GlobalMaxPooling1D -> Dense 32 ReLU ->
Dropout 0,3 -> Dense 1, sigmoid. Đây là bộ phân loại Conv1D độc lập, không
gọi nó là kiến trúc Conv1D+LSTM kết hợp trong ví dụ slide 172-173.

- Loss: binary_crossentropy; optimizer: Adam, learning_rate=0,001.
- Batch 32; tối đa 18 epoch; seed 42; bật phép toán xác định của TensorFlow.
- `class_weight` chỉ tính từ nhãn train để xử lý mất cân bằng; không SMOTE
  trên chuỗi ID vì nội suy ID token không có ý nghĩa ngôn ngữ.
- EarlyStopping theo val_loss, patience 3, min_delta 0,001;
  restore_best_weights=True. Validation không dùng để cập nhật trọng số qua gradient.
- Chọn ngưỡng tối đa F1 trên validation; nếu hòa ưu tiên Precision cao hơn.
- Chọn kiến trúc bằng validation F1, phá hòa bằng validation Precision.
  Khóa `model_config.json` trước bước tính chỉ số test của hai mô hình DL.

Đã dừng sớm: Việt LSTM 5 epoch (khôi phục epoch 2), Conv1D 10 (epoch 7);
UCI LSTM 8 (epoch 5), Conv1D 7 (epoch 4). Đây là một seed và một cấu hình
kiến trúc cho mỗi loại, chưa phải khảo sát siêu tham số hay kiểm định nhiều seed.

## 4 Chạy trên Windows

Đã chạy thực tế trên CPU Windows, Python 3.13.8, TensorFlow 2.21.0 và Keras
3.15.1. Dùng môi trường riêng để không thay thư viện TV1/TV2:

```powershell
py -3.13 -m venv deep_learning/bo_sung_tv3/.venv
deep_learning/bo_sung_tv3/.venv/Scripts/python -m pip install -r deep_learning/bo_sung_tv3/requirements.txt
deep_learning/bo_sung_tv3/.venv/Scripts/python deep_learning/bo_sung_tv3/train_dl.py
deep_learning/bo_sung_tv3/.venv/Scripts/python deep_learning/bo_sung_tv3/compare_templates.py
deep_learning/bo_sung_tv3/.venv/Scripts/python deep_learning/bo_sung_tv3/check_handoff.py
```

Các lệnh chạy từ gốc repo. Thêm `--language vi` hoặc `--language uci` vào
`train_dl.py` để chạy một bộ; `--epochs` chỉ thay ngân sách epoch. Tái chạy
sẽ ghi đè ĐẦU RA TV3 cùng ngôn ngữ. Không cần huấn luyện lại để dùng các
model có sẵn trong gói. Có notebook `chay_tren_colab.ipynb` nếu muốn dùng Colab.

## 5 Bàn giao TV4

Ví dụ tại gốc repo:

```powershell
deep_learning/bo_sung_tv3/.venv/Scripts/python deep_learning/bo_sung_tv3/predict_dl.py --language vi --text "Ma OTP la 123456"
deep_learning/bo_sung_tv3/.venv/Scripts/python deep_learning/bo_sung_tv3/predict_dl.py --language uci --text "Free prize! Call now"
```

`load_model(language)` tự lấy mô hình đã được validation chọn. Có thể chỉ
định thêm `architecture="lstm"` hoặc `"conv1d"` để so sánh. Gọi một lần khi
ứng dụng khởi động, sau đó gọi `predict(text, loaded)` cho từng tin. Kết quả
có nhãn, score, ngưỡng, kiến trúc, phiên bản model và dataset. Score là điểm
mô hình, không phải cam kết xác suất tin đó đúng/sai.

`score` trả đầy đủ độ chính xác dùng để so ngưỡng, nên nhãn luôn khớp phép
so sánh trên kết quả trả về. Chỉ làm tròn khi hiển thị lên giao diện.

Model `.keras` nhận chuỗi số nguyên; dùng cùng `preprocessing.json` và
`model_config.json` qua bộ nạp, không đưa chuỗi thô trực tiếp vào model.
Không tự dùng ngưỡng 0,5 thay ngưỡng trong config. Bộ nạp kiểm tra hash
model và preprocessing. Phần API, tài khoản và giao diện vẫn thuộc TV4.

## 6 Đầu ra cho báo cáo và kiểm tra

- `*/models/*.keras`: hai model và bản tóm tắt lớp/tham số.
- `*/preprocessing.json`: từ vựng, cách mã hóa, chiều dài và padding.
- `*/model_config.json`: ngưỡng, seed, class_weight, phiên bản thư viện,
  hash nguồn, tiêu chí chọn và model được chọn.
- `*/results/pred_lstm_test.csv`, `pred_conv1d_test.csv`: cùng ID test với ML.
- `*/results/pred_dl_test.csv`: dự đoán của model DL được validation chọn.
- `*/results/history_*.csv`, `*/figures/history_*.png`: lịch sử và biểu đồ.
- `*/results/errors_*.csv`, `*/figures/confusion_*.png`: lỗi FP/FN và ma trận.
- `*/figures/comparison_ml_dl.png`: so sánh trên cùng test của từng ngôn ngữ.
- `GIAI_THICH_THEO_SLIDE.md`: giải thích và trả lời khi bảo vệ.
- `training.log`, `training_vi_unicode.log`, `verification.log`: log huấn luyện
  hiện tại và 5 kiểm tra, gồm hồi quy chữ hoa có dấu và điểm sát ngưỡng.

Kiểm tra: vocabulary chỉ chứa token train, split khớp hash, ID kết quả
khớp test, model và vectorizer tải lại tái hiện điểm/nhãn đã lưu, chỉ số
khớp dự đoán, chọn đúng theo validation, từ chối nội dung rỗng, và không
thay file cũ hoặc gói bổ sung TV1/TV2.

## 7 Giới hạn phải nói rõ

- Nguồn công bố của tiếng Việt đã được TV1 xác minh theo nội dung và nhãn;
  xem hồ sơ nguồn ở gói TV1. Không gọi tuyển tập công khai đó là tin mới nhóm
  tự thu thập; các giới hạn ẩn danh/nhãn vẫn theo README TV1.
- Test là benchmark kế thừa mà nhóm đã dùng trong các thí nghiệm trước.
- Chọn ngưỡng trên validation nhỏ có thể quá khớp; dữ liệu mẫu mới khó hơn
  mẫu đã thấy. Chênh lệch nhỏ không chứng minh mô hình tốt hơn nói chung.
- TF TextVectorization dùng token theo khoảng trắng; gói chưa bổ sung bộ
  tách từ tiếng Việt chuyên dụng. Từ vựng quá hiếm/OOV và cắt chuỗi có thể
  làm mất thông tin.
- Hai model của mỗi bộ được huấn luyện riêng theo ngôn ngữ, không phải mô
  hình đa ngôn ngữ hay kiểm thử chuyển ngôn ngữ UCI sang tiếng Việt.

Kiến thức slide và hướng dẫn API dùng ở `GIAI_THICH_THEO_SLIDE.md`.
