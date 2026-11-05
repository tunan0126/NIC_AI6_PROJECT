# Bản sửa phân loại tiếng Việt cho TV4

Lỗi được báo: “Nhóm sẽ họp lúc 14:00 để chuẩn bị bài thuyết trình.” là tin
hợp lệ nhưng ML gốc trả Spam 0,979253; DL gốc cũng trả Spam 0,929461.
Đối chiếu bộ nạp trực tiếp cho kết quả giống API: không phải lỗi hiển thị.

## Nguyên nhân và cách sửa

Dữ liệu ham gốc thiên về thông báo doanh nghiệp/nhà mạng/ngân hàng, ít tin
trò chuyện thông thường. Mô hình BoW có intercept nghiêng về spam; các trọng
số “bị”, “sẽ”, “nhóm” cộng vào điểm spam. Thử chỉ đổi vectorizer trên dữ liệu
cũ vẫn phân loại sai phần lớn các câu sinh hoạt trong bộ hồi quy.

Bản sửa bổ sung 130 câu phát triển tự viết cho train (90 ham, 40 spam), gồm
lịch hẹn, học tập, công việc, gia đình, cảnh báo an toàn, cùng các câu lừa đảo
và quảng cáo tương ứng. 40 câu validation riêng (20 ham, 20 spam) được viết
tách biệt. Đây là dữ liệu synthetic do trợ lý soạn, **không phải SMS thực thu**;
không cộng vào chỉ tiêu thu thập TV1 và cần người thật rà nhãn trước nghiên cứu.

Câu người dùng báo và 24 câu hồi quy không nằm trong train hoặc validation.
Chúng là kiểm tra hồi quy phát triển, không phải holdout thực tế độc lập.
Không thêm luật từ khóa, danh sách câu được cho phép, hoặc điều kiện đặc biệt
để trả Ham cho câu lịch họp. Phản hồi trong app cũng không tự đi vào train.

## Lựa chọn đã khóa trước khi đánh giá test kế thừa

- ML: thử TF-IDF word, char_wb và kết hợp; C=1/3/10; trọng số câu bổ sung
  1/3/6. Chọn theo hai validation, tối đa F1 thấp hơn giữa hai tập, rồi F1 trung
  bình và Precision. Điều kiện: Recall validation gốc >=0,98, Precision >=0,90;
  Recall validation tự viết >=0,95. Kết quả: **TF-IDF char_wb + Logistic Regression**,
  C=1, authored weight=6, ngưỡng **0,58562407619**.
- DL: giữ hai kiến trúc Embedding+LSTM và Embedding+Conv1D của phạm vi TV3;
  từ vựng chỉ học train; Unicode lower; authored weight=6; early stopping theo
  validation loss, khôi phục trọng số tốt nhất. Dùng cùng tiêu chí hai validation
  để chọn kiến trúc/ngưỡng. Chọn **Conv1D**, ngưỡng **0,6509048342704773**.
- Không thay dữ liệu, code, ngưỡng hay artifact trong TV1-TV3. UCI tiếng Anh
  tiếp tục dùng nguyên bản TV2/TV3. Các kết quả học thuật cũ giữ nguyên.

`active.json` khóa hash model/config; adapter tái dùng hàm predict gốc với
tuple artifact mới. Kết quả/API ghi `model_origin=tv4_vi_revision` và dataset
ID riêng. Không lấy số đo của bản sửa thay vào bảng so sánh TV2/TV3 cũ.

## Kết quả và đánh đổi

| Bộ / chỉ số | ML gốc | ML TV4 sửa | DL gốc được chọn | DL TV4 sửa |
|---|---:|---:|---:|---:|
| F1 spam trên benchmark Việt kế thừa | 0,8271 | 0,8441 | 0,8094 | 0,8456 |
| Precision spam | 0,7531 | 0,8538 | 0,7289 | 0,8273 |
| Recall spam | 0,9173 | 0,8346 | 0,9098 | 0,8647 |
| Tin hợp lệ bị báo nhầm (FP) | 40 | 19 | 45 | 24 |
| Spam bị lọt (FN) | 11 | 22 | 12 | 18 |
| Hồi quy tự viết: 12 ham + 12 spam | ML gốc sai 12 câu | 24/24 đúng | Chỉ tái hiện câu lịch họp | 24/24 đúng |

**Giảm báo nhầm nhưng Recall giảm:** bản sửa không tốt hơn trên mọi chỉ số.
Benchmark kế thừa đã được xem ở các lần phát triển trước; không coi là test mới
chưa từng dùng. Bản triển khai có thêm dữ liệu tự viết nên không dùng bảng này
để kết luận riêng thuật toán mới tốt hơn. Cần thêm tập SMS thực tế mới, có nguồn
và nhãn độc lập để đánh giá tổng quát hóa.

Với đúng câu được báo: ML mới điểm **0,192783241025**, DL mới khoảng
**0,004598549**, cả hai thấp hơn ngưỡng tương ứng và trả **Hợp lệ**. Mô hình vẫn
có thể sai với câu khác. Score không phải độ chính xác hoặc xác suất đã hiệu chỉnh.

Chi tiết: `report.json`, `selection.json`, `regression_predictions.csv`,
`dl/report.json`, `dl/regression_*.csv`. Lần thử ML đầu dùng 100 câu train và
điều kiện recall validation thấp hơn đã bị loại; artifact hiện tại chỉ chứa
bản cuối 130 câu train và điều kiện trên. Không dùng kết quả thử đầu để báo cáo.

## Tái tạo

Từ gốc repo, trong môi trường train riêng đã cài `requirements-train.txt`:

```powershell
cloud_app/bo_sung_tv4_app/.venv/Scripts/python -m pip install -r cloud_app/bo_sung_tv4_app/vi_model_revision/requirements-train.txt
cloud_app/bo_sung_tv4_app/.venv/Scripts/python cloud_app/bo_sung_tv4_app/vi_model_revision/train_revision.py
cloud_app/bo_sung_tv4_app/.venv/Scripts/python cloud_app/bo_sung_tv4_app/vi_model_revision/train_dl_revision.py
cloud_app/bo_sung_tv4_app/.venv/Scripts/python cloud_app/bo_sung_tv4_app/vi_model_revision/activate_revision.py
cloud_app/bo_sung_tv4_app/.venv/Scripts/python cloud_app/bo_sung_tv4_app/tests/test_vi_semantics.py
```

Chạy theo thứ tự; khởi động lại server để nạp snapshot mới. Keras ZIP/hash có
thể khác giữa các lần lưu; script ghi lại hash artifact thực tế. Cấu hình Docker
đã bổ sung artifact sửa, nhưng vẫn chưa build/chạy container trên máy này.

Tài liệu kỹ thuật: [TF-IDF và char_wb của scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html).
