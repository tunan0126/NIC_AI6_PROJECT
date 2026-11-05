# API TV4

UI và API cùng origin. JSON UTF-8. Mọi POST/DELETE yêu cầu cookie phiên và
header `X-CSRF-Token` nhận từ `GET /api/session`. Không bật CORS công khai.
Mọi API dữ liệu cá nhân yêu cầu đăng nhập, kiểm tra ownership ở server.

| Method / đường dẫn | Đầu vào / kết quả chính |
|---|---|
| GET `/api/health` | Trạng thái DB/dịch vụ. Không trả dữ liệu cá nhân. |
| GET `/api/session` | Tạo phiên ẩn danh nếu cần; trả `user`, `csrf`, `registration_enabled`. |
| POST `/api/register` | `username`, `display_name`, `password`; trả phiên mới. Có thể tắt bằng env. |
| POST `/api/login` | `username`, `password`; token và CSRF được xoay. |
| POST `/api/logout` | Thu hồi phiên cũ, cấp phiên ẩn danh mới. |
| GET `/api/models` | Danh sách model/ngôn ngữ/kiến trúc/version/ngưỡng/dataset thật. |
| POST `/api/predictions` | `text`, `sender?`, `model`, `language`, `save_history?`, `request_id?`. |
| GET `/api/predictions/{id}` | Chi tiết của chủ phiên, text đã che hoặc null khi không lưu/đã xóa. |
| GET `/api/history?page=1&label=all` | `items`, `total`, `page`, `page_size=20`. label all/spam/ham. |
| DELETE `/api/history` | Xóa nội dung lịch sử riêng; không xóa metadata/feedback/luật. |
| DELETE `/api/history/{id}` | Xóa nội dung một tin của chính người dùng. |
| GET `/api/rules` | Luật riêng, có `id`, `sender_display`, `type`, `version`. |
| POST `/api/rules` | `sender`, `type=block/allow`, `expected_version?`; xung đột trả 409. |
| DELETE `/api/rules/{id}` | Gỡ luật của chính người dùng. |
| POST `/api/feedback` | `prediction_id`, `proposed_label=spam/ham`, `note?`; một phản hồi/lần dự đoán. Gửi lại cập nhật phản hồi. |
| GET `/api/feedback` | 100 phản hồi gần nhất của chủ phiên, trạng thái `pending`. |

## Phân loại

`text` 1-2.000 ký tự; người gửi tối đa 80; `model=ml/dl`; `language=vi/uci`.
`save_history` là boolean, mặc định false. `request_id` tối đa 64 ký tự, client
nên tạo UUID cho một lần kiểm tra và dùng lại khi retry; cùng ID khác đầu vào
bị từ chối 409. Idempotency có phạm vi từng tài khoản.

Kết quả luôn có `prediction_id`, `label`, `decision_source`, `model`, `language`,
`created_at` UTC ISO-8601, `saved`, `latency_ms`. Kết quả do model còn có
`model_origin=tv2/tv3/tv4_vi_revision/tv1_4_v2`. ML tiếng Việt dùng v2; DL giữ phiên bản
sửa riêng TV4, nhánh UCI giữ gốc. Metadata và ngưỡng luôn phản ánh artifact đang nạp. Khi do mô hình: có `score`,
`threshold`, `model_version`, `dataset_id` và `architecture` nếu DL. Nhãn spam
khi `score >= threshold`; giữ nguyên độ chính xác API, chỉ làm tròn khi hiển thị.

Nếu do luật, `decision_source=block/allow`, `rule_id` tồn tại và
`score/threshold/model_version/dataset_id=null`. Mô hình không được gọi.
Nhánh DL trả `truncated`, `input_tokens`, `sequence_length` để UI cảnh báo phần
chuỗi vượt giới hạn. Thời gian xử lý bao gồm thời gian chờ khóa suy luận, không
bao gồm mạng tới trình duyệt hoặc commit DB sau suy luận.

## Luật và ownership

Khóa người gửi chuẩn hóa Unicode NFC, trim và casefold; số điện thoại bỏ khoảng
trắng/chấm/gạch/ngoặc, không tự suy đoán mã quốc gia. Mỗi `(user_id,sender_key)`
chỉ có một luật. Người gửi không nhập thì bỏ qua luật.

Thay luật trái loại trả 409 kèm `existing.version`. UI hỏi xác nhận rồi gửi
lại `expected_version` đúng. Phiên bản cũ bị từ chối nếu đã có thay đổi khác.
ID của người khác trả 404 với đọc/xóa tin, xóa luật hoặc gửi feedback. Server
không tin `user_id` từ body hoặc tham số của client.

## Lỗi

JSON lỗi có `error`. Mã 400 đầu vào sai, 401 chưa đăng nhập/phiên hết hạn,
403 CSRF/Origin/đăng ký tắt, 404 không tồn tại hoặc không thuộc chủ, 409 xung đột,
413 quá lớn, 415 không phải JSON, 429 quá nhanh, 503 lỗi dịch vụ. UI giữ bản nháp
khi lỗi suy luận/kết nối; xóa dữ liệu riêng trên màn hình khi hết phiên/đăng xuất.

Giới hạn hiện có: đăng nhập 20 lần/10 phút/IP, đăng ký 10 lần/giờ/IP, suy luận
60 lần/phút/tài khoản. App không tin X-Forwarded-For tùy ý; khi sau reverse proxy,
giới hạn IP áp vào địa chỉ proxy. Với phạm vi demo nhỏ giữ cấu hình này; khi mở
rộng cần cấu hình trusted proxy/rate limit tại gateway theo topology thật.

Session cookie HttpOnly/SameSite=Lax; cloud HTTPS phải bật `COOKIE_SECURE=1`.
Phản hồi chỉ lưu để rà soát, không cập nhật mô hình hoặc nhãn dataset.

Nguồn kỹ thuật đối chiếu: [Flask Security](https://flask.palletsprojects.com/en/stable/web-security/),
[Waitress Usage](https://docs.pylonsproject.org/projects/waitress/en/latest/usage.html).
