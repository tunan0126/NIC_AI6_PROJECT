# TV3 - Học sâu (Deep Learning)

Thư mục này chứa toàn bộ các mô hình học sâu (Convolutional 1D Neural Network - Conv1D và Long Short-Term Memory - LSTM) để phân loại tin nhắn rác SMS tiếng Việt và tiếng Anh.

## Cấu trúc thư mục
- `vi/`: Mô hình tối ưu cho tiếng Việt.
  - `models/`: Trọng số mô hình `conv1d.keras` và `lstm.keras`.
  - `model_config.json`: Cấu hình tham số và ngưỡng phân loại tối ưu (threshold: 0.528).
  - `preprocessing.json`: Tập từ vựng và cấu hình TextVectorization Unicode.
- `uci/`: Mô hình đối chiếu trên tập dữ liệu tiếng Anh quốc tế (UCI SMS Dataset).
  - `models/`: Trọng số mô hình `conv1d.keras` và `lstm.keras`.
  - `model_config.json`, `preprocessing.json`.
- `experiments/`: Các thử nghiệm nâng cao (mô hình Character-level, Dual-representation, seed variations).
- `predict_dl.py`: Script giao diện chung nạp mô hình học sâu và thực hiện dự đoán suy luận.
- `text_processing.py`: Module tiền xử lý chuỗi văn bản, chuẩn hóa ký tự Unicode và tokenization cho Keras.
- `chay_tren_colab.ipynb`: Notebook Jupyter huấn luyện mô hình trên Google Colab GPU/TPU.
- `GIAI_THICH_THEO_SLIDE.md`: Tài liệu diễn giải kiến trúc mô hình phục vụ báo cáo thuyết trình.
