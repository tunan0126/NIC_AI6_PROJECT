# Bổ sung phần bàn giao TV1

Đây là gói bổ sung. Không thay đổi các file dữ liệu, mã và kết quả cũ trong repo.

## Cách chạy

Từ thư mục gốc repo, dùng Python 3.13 và môi trường riêng:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\python -m pip install -r traditional_ml/bo_sung_tv2/requirements-train.txt
.venv\Scripts\python data_features/bo_sung_tv1/prepare_data.py
.venv\Scripts\python data_features/bo_sung_tv1/verify_source.py
```

Chỉ đọc hai file `traditional_ml/TV2_hoc_may/data/raw/train_goc.csv` và
`test_goc.csv`. Đầu ra nằm trong thư mục bổ sung này. Manifest ghi SHA-256
của nguồn và từng CSV đầu ra để TV2/TV3 cố định cùng một phiên bản.

## Quy trình và phạm vi ẩn danh

1. Chuẩn hóa Unicode NFC, gộp khoảng trắng, giữ chữ hoa và dấu câu.
2. Che email thành `[EMAIL]`, mẫu số điện thoại thành `[PHONE]`, dãy số rời
   có ít nhất 4 chữ số thành `[NUMBER]`; che query/fragment của URL. Giữ domain
   để khảo sát và sử dụng Regex. Không truy cập các URL trong tin nhắn.
3. Kiểm tra nhãn chỉ có 0/1. Tin rỗng/nhãn không hợp lệ chuyển vào quarantine.
4. Dùng đúng khóa mẫu câu của mã TV2 gốc. Cách ly TOÀN BỘ nhóm mang nhãn
   trái nhau, thay vì tự đổi nhãn dựa trên từ khóa hay dự đoán của mô hình.
5. Loại bản trùng sau ẩn danh. Tin trùng giữa train và test bị bỏ khỏi train.
6. Giữ test từ nguồn nhóm cung cấp; tách validation theo nhóm bằng
   `StratifiedGroupKFold(8, shuffle=True, random_state=42)` như mã TV2 gốc.

Quy tắc này che được các định dạng nêu trên, không bảo đảm phát hiện mọi tên
người hoặc định danh tự do. Tên riêng và quyền sử dụng dữ liệu cần chủ nguồn
xác nhận. Việc che số có thể gom nhiều tin thành cùng nội dung và làm mất một
số tín hiệu số học; thống kê/kết quả mới cần được báo riêng.

## Đầu ra

| File | Cách dùng |
|---|---|
| `manifest.json` | Phiên bản, nguồn repo, SHA-256, số mẫu và giới hạn |
| `data/train_clean.csv`, `test_clean.csv` | Đầu vào đã xử lý cho mã TV2 gốc |
| `data/train.csv`, `val.csv`, `test.csv` | TV3 đọc trực tiếp, không chia lại; cột `id,text,y` |
| `data/*_source_ids.csv` | Truy từ ID trong từng tập về ID dòng nguồn |
| `data/*_regex_features.csv` | Bảng 13 đặc trưng Regex và nhãn; không dùng làm đầu vào thô cho vectorizer |
| `data/vi_demo_sample.csv` | 133 spam và 50 ham, chọn từ test có sẵn để minh họa |
| `reports/quarantine.csv` | 6 tin/3 nhóm nhãn trái nhau, chưa dùng để huấn luyện/chấm điểm |
| `reports/source_verification.json` | Nguồn công bố cố định theo commit, hash đối chiếu, license và trích dẫn |
| `reports/vi_sourced_sample_150spam_50ham.csv` | 150 spam + 50 ham có nguồn từng bản ghi, tuyển từ corpus công khai |
| `reports/*statistics.csv`, `reports/figures/` | Thống kê và biểu đồ cho báo cáo |

Số mẫu sau xử lý: **train 1.640 (497 spam), validation 235 (71 spam),
test 562 (133 spam)**. ID chỉ duy nhất TRONG MỖI tập; khi gộp nhiều tập,
khóa định danh là `(split, id)`. `source_id` trong bảng ánh xạ là duy nhất toàn bộ.

### Từ điển đặc trưng

`log_` dưới đây có nghĩa là `log(1 + số lượng)`.

| Cột | Ý nghĩa |
|---|---|
| `log_do_dai`, `log_so_tu` | Độ dài ký tự và số từ tách bằng khoảng trắng |
| `co_sdt`, `co_link`, `co_tien` | Cờ có số điện thoại, đường dẫn, dấu/biểu thức tiền |
| `log_ky_tu_dac_biet`, `log_so_chu_so` | Số ký tự ngoài chữ/số/khoảng trắng và số chữ số |
| `ti_le_chu_hoa` | Số chữ hoa chia số ký tự chữ |
| `log_dau_cham_than` | Số dấu chấm than |
| `log_so_the_an_danh`, `co_the_money` | Số thẻ dạng `[...]` và cờ có `[MONEY]` |
| `ti_le_ky_tu_dac_biet`, `co_dau_tieng_viet` | Tỷ lệ ký tự đặc biệt và cờ có dấu tiếng Việt |

Tái dùng hàm Regex của TV2 gốc. Riêng bảng TV1 bổ sung nhận dạng `[PHONE]`
cho cờ `co_sdt`; mã Regex/pipeline của TV2 cũ vẫn giữ nguyên.

## Hồ sơ nguồn và giới hạn phải ghi trong báo cáo

- Đã xác minh hai CSV có sẵn trong repo khớp toàn bộ nội dung và nhãn với
  nguồn công bố `trannguyenthaituan251209/vietnamese_sms_dataset`, commit
  `464a028878023598e16f2f344ee36f7d5d74257f`; khác biệt chỉ là CRLF/LF.
  Hash và URL của từng file nằm trong `reports/source_verification.json`.
- Nhà công bố ghi giấy phép CC BY 4.0. Trích dẫn: Vietnamese SMS Dataset with
  Quality Assurance, Tran Nguyen Thai Tuan et al. (2026). Xem nguồn:
  https://github.com/trannguyenthaituan251209/vietnamese_sms_dataset/blob/464a028878023598e16f2f344ee36f7d5d74257f/README.md
- Bộ 150 spam + 50 ham bổ sung là tuyển tập có nguồn từ corpus công khai,
  không phải nhóm tự xin người dùng cung cấp tin mới; có nguồn/ID cho từng
  bản ghi và ghi rõ các bước biến đổi. Không xem nó là test độc lập với
  mô hình Việt, vì có chung corpus với train/test. Chưa kiểm toán độc lập
  quy trình thu thập của nhà công bố và mọi tên riêng tự do.
- Bộ minh họa 133 spam đáp ứng kích thước minh họa 100-200 tin, nhưng được
  chọn từ dữ liệu cũ, KHÔNG phải một tập mở rộng độc lập hay bộ mới thu thập.
  Không dùng kết quả của bộ con để tuyên bố mô hình tổng quát hóa tốt hơn.
- Các tin chưa thống nhất nhãn được cách ly. Khi chủ dữ liệu xác nhận nhãn,
  tạo phiên bản mới và chạy lại đồng thời ML/DL; không chỉnh test để tăng điểm.
- Test nguồn đã được xem ở các thí nghiệm trước. Bộ mới sau xử lý không
  trở thành một holdout hoàn toàn chưa được dùng.
- UCI là bộ chuẩn tiếng Anh của đề; nguồn chính thức:
  https://archive.ics.uci.edu/dataset/228/sms%2Bspam%2Bcollection
  Bản UCI nằm ở thư mục TV2 cũ và được chạy lại riêng trong gói bổ sung TV2.

## Bàn giao

TV3 dùng các split cố định của gói này cho tiếng Việt và split UCI trong
`traditional_ml/bo_sung_tv2/uci/data/` cho bộ chuẩn. Hai ngôn ngữ có kết quả
riêng. TV4 dùng `traditional_ml/bo_sung_tv2/predict.py` để áp dụng cùng
quy tắc ẩn danh khi dự đoán tiếng Việt.
