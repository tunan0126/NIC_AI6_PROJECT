# Giải thích phần TV3 theo kiến thức đã học

## Mục tiêu và liên hệ slide

Mục tiêu là so sánh hai cách học đặc trưng văn bản bằng mạng nơ-ron với
baseline học máy TV2, trên cùng dữ liệu và cùng chỉ số spam. Kiến trúc trong
gói là lựa chọn triển khai cho đề tài, không phải mọi thông số đều do slide quy định.

| Bước trong mã | Kiến thức slide | Áp dụng trong đề tài |
|---|---|---|
| Cố định train/validation/test | Chương 5, slide 48-58 và 156-160 | Đọc split TV2, validation để quyết định, test để báo cáo |
| Mã hóa số nguyên | Chương 7, slide 85-96 | TextVectorization học từ vựng train và ánh xạ token thành ID |
| Padding | Chương 7, slide 98-101 | Đệm 0 ở cuối để batch có cùng chiều dài; giới hạn chiều dài từ train |
| Embedding | Chương 7, slide 158-169 | Vector 64 chiều được học cùng mô hình; không dùng Word2Vec huấn luyện sẵn |
| LSTM | Chương 7, slide 170-171; Chương 9, slide 69-79 | Đọc chuỗi và xuất một vector; return_sequences=False |
| Convolution và pooling | Chương 7, slide 172-173; Chương 9, slide 5-35 | Conv1D tìm mẫu token lân cận; pooling tổng hợp đặc trưng |
| Sequential, loss và optimizer | Chương 8, slide 155-160 | Keras Sequential, binary_crossentropy, Adam, sigmoid |
| Dropout | Chương 8, slide 66-69 | Dropout 0,3 khi huấn luyện; tắt khi suy luận |
| Precision/Recall/F1 | Chương 5, slide 169-188, 292-311 | Coi spam là lớp dương; đếm FP/FN riêng |

Nguồn slide: các file SIC_AI Chương 5, 7, 8 và 9 trong ZIP người dùng đã cung
cấp. Số slide là vị trí trong tệp, tính cả bìa. Ví dụ LSTM trong bản dịch có
đối số `Bàis=...`; mã TV3 dùng API hợp lệ `LSTM(32, ...)`, không chép lỗi dịch.

Ví dụ Chương 7 slide 172-173 kết hợp Conv1D, MaxPooling1D và LSTM. Gói này
dùng LSTM và bộ phân loại Conv1D riêng để so sánh hai kiến trúc rõ ràng;
GlobalMaxPooling1D là bước tổng hợp đặc trưng được chọn khi triển khai.
EarlyStopping, class_weight và cách chọn chiều dài/ngưỡng là các bổ sung
triển khai, không gán thành yêu cầu nguyên văn của slide.

## Quy trình giải thích khi thuyết trình

1. **Nhận dữ liệu:** giữ nguyên các split của TV1/TV2; tiếng Việt và UCI
   được huấn luyện, đánh giá riêng. Ghi hash để biết đang dùng đúng phiên bản.
2. **Biến văn bản thành số:** học từ vựng chỉ từ train. Mỗi token có ID;
   từ chưa gặp dùng `[UNK]`, phần đệm dùng 0. Chưa dùng tách từ tiếng Việt chuyên dụng.
3. **Học vector từ:** Embedding học biểu diễn 64 chiều trong quá trình
   huấn luyện phân loại. Vector được cập nhật qua gradient cùng các trọng số khác.
4. **LSTM:** xử lý tuần tự chuỗi vector; trạng thái nhớ và các cổng giúp
   điều chỉnh thông tin giữ lại. Lấy đầu ra cuối làm đặc trưng cho tin nhắn.
5. **Conv1D:** cửa sổ kernel 5 quét qua chuỗi embedding để học mẫu cục bộ;
   pooling giữ các tín hiệu nổi bật và biến thành vector cho bộ phân loại.
6. **Ra điểm spam:** Dense 1 với sigmoid tạo điểm trong khoảng 0-1. Dùng
   binary cross entropy và Adam để cập nhật trọng số từ train.
7. **Kiểm soát quá khớp:** dropout; dừng khi val_loss không cải thiện đủ
   trong 3 epoch; khôi phục trọng số tốt nhất. Class weight dựa vào train.
8. **Chọn quyết định:** tối ưu ngưỡng và chọn kiến trúc trên validation.
   Khóa lựa chọn rồi tính Precision, Recall, F1 và confusion matrix trên test.
9. **Bàn giao:** lưu model, vocabulary, cấu hình và hash. TV4 dùng bộ nạp
   để xử lý tin mới giống lúc học, không tự tạo một bộ từ vựng khác.

## Đọc kết quả đúng

- Việt sau review: ML F1 0,8271; LSTM 0,8094; Conv1D 0,8259.
  Validation chọn LSTM (F1 0,9660 so với 0,9655 của Conv1D). Giữ lựa chọn
  đó dù Conv1D cao hơn trên test; không dùng test để đổi kiến trúc.
- UCI: ML F1 0,9603; LSTM 0,9042; Conv1D 0,9266. Với dữ liệu hiện có và
  ngân sách huấn luyện này, baseline ML tốt hơn.
- Trên 498 tin Việt thuộc mẫu câu mới so với train/val: ML 0,7396;
  LSTM 0,7107, Conv1D 0,7330. Số liệu trong `comparison_by_template.csv`
  dùng baseline TV2 sau review. Khoảng cách với mẫu đã thấy cho thấy khó khăn
  khi tổng quát hóa. Khóa mẫu 50 ký tự là phép xấp xỉ, không chứng minh mọi
  tin trong nhóm đều có cùng ý nghĩa.
- Không so F1 tiếng Việt với F1 UCI để kết luận kiến trúc hợp với ngôn ngữ
  nào hơn; dữ liệu, kích thước và độ khó của hai bộ khác nhau.
- Hai model tiếng Việt được học bằng dữ liệu Việt, không phải lấy model
  UCI áp thẳng sang Việt. Tập minh họa TV1 là tập con test, không phải bằng
  chứng tổng quát hóa trên một bộ dữ liệu mới độc lập.
- Train accuracy gần 1 trong khi validation/test thấp hơn là dấu hiệu cần
  theo dõi quá khớp; không trình bày train accuracy như hiệu quả thực tế.

## Câu hỏi dễ gặp khi bảo vệ

**Vì sao dùng embedding thay cho one-hot?** One-hot thưa và nhiều chiều;
embedding dùng vector ít chiều có tham số được học. Ở đây embedding được
học từ đầu cho mục tiêu phân loại spam.

**Vì sao không SMOTE trên chuỗi?** ID từ là mã định danh rời rạc, không phải
đại lượng để nội suy. Dùng class_weight để tăng trọng số lỗi của lớp ít mẫu.

**Vì sao không chọn mô hình có F1 test cao nhất?** Chọn theo test sẽ làm
test tham gia quá trình tối ưu. Gói chọn theo validation và chỉ dùng test
để báo cáo sau khi đã khóa model_config.

**Vì sao DL không luôn tốt hơn?** Mẫu nhỏ, từ hiếm, OOV và mẫu câu mới có
thể khiến mạng học kém hơn biểu diễn TF-IDF. Kết quả này chỉ phản ánh những
cấu hình đã thử, không phủ định mọi kiến trúc học sâu.

**Có thể cam kết điểm này khi chạy thực tế không?** Không. Test được kế
thừa từ các thí nghiệm cũ. TV1 đã đối chiếu nội dung với nguồn công bố,
nhưng chưa đo trên luồng tin mới độc lập hoặc nhiều seed. Trình bày đúng phạm vi.

**TV4 phải nhận những gì?** File `.keras`, preprocessing.json,
model_config.json, predict_dl.py và module ẩn danh TV1. Nạp một lần khi
khởi động; gọi hàm predict cho từng tin.

## API chính thức đã đối chiếu khi triển khai

- TextVectorization: https://www.tensorflow.org/api_docs/python/tf/keras/layers/TextVectorization
- EarlyStopping: https://keras.io/api/callbacks/early_stopping/
- TensorFlow và môi trường cài đặt: https://www.tensorflow.org/install/pip

Các API được đối chiếu để dùng đúng phiên bản hiện tại; tài liệu slide vẫn
là nền kiến thức cho việc chọn và giải thích mô hình.
