# Bàn giao bổ sung TV1–TV4 v2

> Giao diện đã được làm gọn sau mốc v2 theo phản hồi “quá nhiều mục và chữ”.
> Bản hiện tại: 44/44 kiểm tra (27 Python + 17 trình duyệt); xem
> `cloud_app/bo_sung_tv4_app/UX_SIMPLIFIED.md`. Gói mới:
> `Bo_sung_TV1_TV4_v2_UI_gon.zip`. Số liệu mô hình bên dưới giữ nguyên.


Phục vụ demo desktop cho giảng viên. Tiếp tục nguồn dữ liệu hiện có theo xác nhận
của người dùng; không có SMS thực tế mới đã rà nhãn. Không sửa file đang được Git
theo dõi của các thành viên. Các gói v2 nằm riêng; ứng dụng TV4 được cập nhật để
dùng **ML v2 và DL bản trước**, không coi thử nghiệm DL thất bại là model đã nghiệm thu.

## Mỗi thành viên nhận gì?

| Thành viên | Thư mục | Kết quả / bước tiếp |
|---|---|---|
| TV1 | `data_features/bo_sung_tv1_v2` | Chuẩn hóa chung, chống trùng, nguồn/nhãn, Regex, manifest; 4 tin chờ con người rà nhãn |
| TV2 | `traditional_ml/bo_sung_tv2_v2` | So sánh 20 cấu hình, chọn SVM TF-IDF từ/ký tự; artifact và dự đoán từng tin |
| TV3 | `deep_learning/bo_sung_tv3_v2` | Kết quả 11 thử nghiệm LSTM/Conv1D; chưa đạt gate nên giữ Conv1D cũ |
| TV4 | `cloud_app/bo_sung_tv4_app` | Tích hợp ML mới, thể hiện phiên bản thật, giữ DL đối chiếu; 40 kiểm tra tự động đạt |

Các thư mục v1 và bản thiết kế PACT `cloud_app/bo_sung_tv4_ux` vẫn được giữ.
Tài liệu PACT trước mô tả quy trình/tiêu chí dự kiến; chưa có usability test với
giảng viên thật. Không diễn giải kiểm tra trình duyệt thành nghiên cứu người dùng.

## Số liệu cần trình bày đúng

Precision, Recall, F1 dưới đây là của **lớp spam**. FP là tin hợp lệ bị báo spam;
FN là spam bị bỏ sót. Đối chiếu trên cùng benchmark kế thừa 562 tin:

| Phiên bản | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|
| ML sửa lần trước | 0,8538 | 0,8346 | 0,8441 | 19 | 22 |
| **ML v2 đang chạy** | **0,8819** | **0,8421** | **0,8615** | **15** | **21** |
| DL giữ lại | 0,8273 | 0,8647 | 0,8456 | 24 | 18 |

40 câu lần kiểm tra trước: ML 34/40 → 38/40; DL vẫn 31/40. Đây là các câu đã biết,
không phải bằng chứng tổng quát hóa trên dữ liệu thực tế mới. 24 câu hồi quy cũ
được dùng làm điều kiện phát hành sau khi chọn ngưỡng trên validation.

Challenge 48 câu tự viết, đóng băng trước huấn luyện: ML đúng 42/48, F1 0,8636;
DL đúng 43/48, F1 0,9020. DL có Recall cao hơn nhưng báo nhầm nhiều hơn. Không
khẳng định ML tốt hơn ở mọi tình huống. Test 562 đã được dùng đánh giá trước đây;
các câu tự viết do trợ lý gán nhãn, chưa được con người xác nhận độc lập.

Câu người dùng báo: “Nhóm sẽ họp lúc 14:00 để chuẩn bị bài thuyết trình.” hiện là
Hợp lệ: ML v2 điểm 0,028589708937 < ngưỡng 0,574778065562; DL giữ lại điểm
0,004598545376211405 < ngưỡng 0,6509048342704773. ML cho cùng điểm với bản không
dấu vì dùng chung chuẩn hóa. DL chưa có tính bất biến đó. Điểm không phải xác suất
kết luận đúng hay độ chính xác của ứng dụng. Không hard-code nhãn cho câu mẫu.

## Chạy và demo

Giải nén `Bo_sung_TV1_TV4_v2.zip` vào gốc repo GitHub đã tải, giữ cấu trúc. ZIP gom
các thư mục bổ sung v1/v2 cần cho app, không chứa môi trường Python, DB, mật khẩu.
Ứng dụng cần Python 3.13; lần đầu script cài thư viện theo bản đã khóa.

```powershell
powershell -ExecutionPolicy Bypass -File cloud_app/bo_sung_tv4_app/start.ps1
```

Chờ `TV4 ready`, mở **http://127.0.0.1:8080**. Nếu đã mở trang cũ, Ctrl+F5.
Tài khoản tạo riêng nằm trong `cloud_app/bo_sung_tv4_app/instance/Tai_khoan_demo.txt`.
Mỗi máy mới tự tạo thông tin đăng nhập, không dùng chung mật khẩu trong repo.
Không chạy hai server cùng cổng. Không bật lưu nếu chỉ cần phân loại thử.

Demo 5 phút: A nhập tin → ML → xem điểm/ngưỡng/phiên bản → đổi DL đối chiếu →
báo sai → thêm luật chặn người gửi → B dùng cùng tin không nhận luật của A →
xem lịch sử/feedback riêng → đăng xuất. Hai cửa sổ thường dùng chung cookie;
dùng cửa sổ ẩn danh, hai profile, hoặc hai máy để có hai phiên độc lập.

Docker/HTTPS/cloud: xem `cloud_app/bo_sung_tv4_app/CLOUD.md`. Dockerfile có COPY
ML v2 và chuẩn hóa mới; chưa build/chạy Docker vì máy chưa có Docker Engine,
chưa triển khai cloud. Local dùng Waitress + SQLite, phù hợp demo nhóm nhỏ.

## Kiểm tra và tái tạo

27 Python/API/integrity/hồi quy + 13 Chromium = **40/40 đạt**. Log và ảnh thật:
`cloud_app/bo_sung_tv4_app/tests/release_v2_*`, `tests/browser_verification.json`,
`screens/`. Kiểm tra live 8080 xác nhận đúng ML v2 và DL giữ lại, không dùng kết
quả test client thay cho xác nhận phiên bản server.

```powershell
cloud_app/bo_sung_tv4_app/.venv/Scripts/python -m unittest discover -s cloud_app/bo_sung_tv4_app/tests -p 'test_*.py' -v
```

Muốn huấn luyện lại, cài thêm `pandas==3.1.1` vào môi trường cùng dependencies
runtime; đọc README từng TV. Không dùng kết quả challenge để chỉnh ngưỡng sau
đánh giá. Dữ liệu/chuẩn hóa đổi cần tạo model/hash mới, kiểm tra hồi quy rồi cập
nhật snapshot phát hành; không sửa file model đang chạy bằng tay.

## Quy trình tiếp theo, không giẫm việc nhau

1. **TV1 trước:** người phụ trách rà 4 nhãn nghi vấn, thu SMS có sự đồng ý/ẩn danh,
   chia theo nhóm nguồn/người gửi khi có metadata, đóng băng dữ liệu và manifest.
2. **TV2 và TV3 làm song song:** cùng đọc bản TV1 đã chốt; mỗi người làm trong thư
   mục riêng, chỉ chọn bằng train/val. Xuất model + preprocessing + threshold + hash
   + bảng Precision/Recall/F1 + dự đoán từng tin. Không sửa dữ liệu của TV1.
3. **TV4 sau khi nhận artifact đạt chuẩn:** tích hợp theo manifest, chạy API/browser,
   giữ phiên bản cũ nếu ứng viên không đạt; tổ chức usability test với giảng viên.
4. **TV5:** tổng hợp báo cáo/demo và đối chiếu yêu cầu; có thể chuẩn bị khung tài
   liệu ngay, cập nhật số cuối khi TV2/TV3/TV4 bàn giao. Không tự thay model/nhãn.

Giới hạn còn lại: thiếu test thực tế mới đã rà nhãn; dữ liệu tự viết có thiên lệch;
bỏ dấu mất nghĩa ở một số từ; DL mới chưa đạt gate; chưa nghiệm thu Docker/cloud,
thử tải lớn hay usability với người dùng thật. Ứng dụng phân loại trong web,
không kết nối nhà mạng hoặc tự chặn SMS trên điện thoại.
