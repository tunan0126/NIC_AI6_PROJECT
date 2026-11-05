# TV3 v2 — thử nghiệm DL và quyết định phát hành

**Chưa có DL v2 đạt tiêu chí phát hành. Ứng dụng tiếp tục dùng Conv1D của bản sửa
tiếng Việt trước**, SHA-256 bắt đầu `e0e7903e1fe0`, ngưỡng 0,6509048342704773.
Giữ nguyên artifact đã bàn giao, không sửa kết quả hay hạ tiêu chí để đưa model mới lên.

Đã huấn luyện 11 ứng viên trên dữ liệu TV1 v2, dùng cùng tập val với ML:

| Nhóm thử nghiệm | Số ứng viên | Cách làm | Kết quả |
|---|---:|---|---|
| Từ, khởi tạo mới | 4 | LSTM/Conv1D, seed 42/2026 | Không đạt gate validation |
| Từ, warm-start | 4 | Kế thừa trọng số cũ, ánh xạ embedding sang từ bỏ dấu | Không đạt gate validation |
| Ký tự | 1 | Conv1D hai lớp, chuỗi ký tự bỏ dấu | Không đạt gate validation |
| Hai dạng train | 2 | LSTM/Conv1D; giữ vốn từ gốc, thêm dạng bỏ dấu trong train | Không đạt gate validation |

Gate cố định: nguồn Precision≥0,90 và Recall≥0,95; câu tự viết Precision/Recall≥0,90.
Ngưỡng chọn bằng validation; thử nghiệm hai dạng train còn kiểm tra không làm sai
24 câu hồi quy cũ. Test/challenge không dùng để chọn mô hình hay ngưỡng.
Có early stopping, trọng số cân bằng lớp, lưu epoch/loss và hash trọng số.
Một số ứng viên học train rất tốt nhưng validation không đạt: không dùng accuracy
train để kết luận mô hình tốt. Bỏ dấu cũng làm mất thông tin phân biệt từ.

`experiment_report.json` lưu đủ 11 kết quả validation và đánh giá model giữ lại.
Các trial đầu chỉ còn log; trường `saved_weights_match_trial` phân biệt log và
trọng số còn đúng phiên bản. Trọng số thử nghiệm cùng tên đã được warm-start ghi
lại **trong thư mục v2 mới**, không đụng file của thành viên khác.

| Model đang giữ | Tập | Precision spam | Recall spam | F1 spam | FP / FN |
|---|---|---:|---:|---:|---:|
| Conv1D trước | Benchmark 562 | 0,8273 | 0,8647 | 0,8456 | 24 / 18 |
| Conv1D trước | Challenge tự viết 48 | 0,8519 | 0,9583 | 0,9020 | 4 / 1 |
| Conv1D trước | Hồi quy đã biết 64 | 0,8485 | 0,8750 | 0,8615 | 5 / 4 |

Trên challenge, DL giữ lại có F1 cao hơn ML v2; trên benchmark kế thừa và hồi quy,
ML v2 tốt hơn. Không tuyên bố một mô hình thắng trong mọi tình huống.
Không có tập SMS thực tế mới được rà nhãn độc lập để xác nhận hiệu quả thực tế.

## Các lệnh phục vụ nhóm

Tại gốc repo, Python có dependencies của app và pandas 3.1.1:

```powershell
python deep_learning/bo_sung_tv3_v2/train.py
python deep_learning/bo_sung_tv3_v2/train_char.py
python deep_learning/bo_sung_tv3_v2/train_dual.py
python deep_learning/bo_sung_tv3_v2/evaluate_release.py
```

Ba lệnh train chủ động trả lỗi khi không có ứng viên đạt gate; đó là từ chối phát
hành có chủ đích, không phải lỗi server. Script đầu hiện là bản warm-start.
Không trỏ ứng dụng vào `predict.py`/trọng số thử nghiệm khi chưa có `model_config.json`
hợp lệ. `release_v2.json` của TV4 hiện chỉ kích hoạt ML. Sau khi có dữ liệu thực tế
đã rà nhãn, phát triển tiếp trên train/val rồi nghiệm thu bằng tập test mới đóng băng.
