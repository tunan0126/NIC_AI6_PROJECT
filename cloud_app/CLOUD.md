# Chạy Docker và đưa lên cloud

Đã chuẩn bị Dockerfile, Compose, healthcheck, volume DB và reverse proxy Caddy.
Máy hiện tại chưa có Docker Engine nên **chưa build/chạy container**. Chưa
triển khai lên máy chủ trả phí hoặc tạo tài nguyên cloud.

## 1. Chuẩn bị mã và model

Máy chủ cần Docker Engine + Compose, kiến trúc Linux x86-64 và tài nguyên đủ
cho TensorFlow CPU. Đo RAM/thời gian khởi động trước khi chọn gói cloud; chưa
có benchmark container để khẳng định một mức RAM tối thiểu cụ thể.

Trên máy chủ, đặt repo GitHub và giải nén `Bo_sung_TV1_TV4_v2.zip` vào
**gốc repo**, giữ nguyên đường dẫn. Docker cần ML v2, chuẩn hóa TV1 v2,
`release_v2.json` và bản DL giữ lại trong `vi_model_revision/`; không bỏ các
file này khi build. Dockerfile đã thêm COPY của bản ML mới. Không chép `.venv`, `.git` cũ, database
local hoặc file mật khẩu lên kho công khai. Model joblib chỉ dùng artifact của
nhóm, không nhận file tải lên từ người dùng.

## 2. Thử Docker local trước

Từ thư mục gốc repo:

```sh
cd cloud_app/bo_sung_tv4_app
cp .env.example .env
docker compose up --build -d
docker compose logs -f app
```

Windows PowerShell dùng `Copy-Item .env.example .env` thay cho `cp` nếu cần.
Khi thấy `TV4 ready`, mở `http://127.0.0.1:8080`. Cổng app chỉ được publish
trên loopback của máy chạy Docker. Không mở cổng 8080 công khai để bỏ qua HTTPS.

Tạo tài khoản demo mới trong volume của container:

```sh
docker compose exec app python cloud_app/bo_sung_tv4_app/manage.py create-demo-users
docker compose cp app:/data/Tai_khoan_demo.txt ./Tai_khoan_demo.txt
```

Mật khẩu được tạo riêng ở máy chủ. Không đưa file vừa copy vào Git/ZIP.
Đăng ký tài khoản qua UI cũng dùng được khi `ALLOW_REGISTRATION=1`.

## 3. Bật HTTPS cho máy chủ có domain

1. Trỏ bản ghi A/AAAA của domain về máy chủ, mở inbound 80/443 tại firewall.
2. Sửa `.env` theo domain thật, ví dụ:

```dotenv
DOMAIN=sms.your-domain.example
APP_ORIGIN=https://sms.your-domain.example
COOKIE_SECURE=1
ALLOW_REGISTRATION=0
ALLOWED_HOSTS=localhost,127.0.0.1
```

3. `APP_ORIGIN` tự thêm hostname vào danh sách Host cho phép. Giá trị ví dụ
   phải đổi thành domain đã sở hữu, không dùng nguyên `.example`.
4. Chạy:

```sh
docker compose --profile cloud up --build -d
docker compose --profile cloud logs -f app https
```

Caddy nhận HTTPS và chuyển tới app:8080 trong mạng Docker. Chứng chỉ và DB
ở volume riêng, còn sau restart. Điều kiện DNS/cổng/volume phải đúng để Caddy
cấp chứng chỉ. Nếu dùng HTTPS do nền tảng hosting cung cấp, có thể bỏ service
Caddy nhưng vẫn đặt APP_ORIGIN đúng và COOKIE_SECURE=1; giữ volume DB bền vững.

## 4. Nghiệm thu cloud trước bảo vệ

- URL HTTPS mở từ hai máy ngoài máy chủ; đăng nhập A/B ở hai trình duyệt.
- Cả ML/DL Việt/UCI đều trả model_version và threshold đúng `/api/models`.
- A chặn DEMO-A; B kiểm tra cùng tin không dùng luật A. B không xem lịch sử/
  phản hồi A hoặc truy cập ID của A qua API (phải 404).
- Lưu lịch sử, `docker compose restart app`, đăng nhập lại và kiểm tra dữ liệu.
- Thử mất mạng/timeout; cookie có Secure/HttpOnly/SameSite; không bật debugger.
- Kiểm tra healthcheck và log khởi động. Không dùng kết quả kiểm thử Python
  local thay cho các kiểm tra cloud này.

## 5. Dừng và sao lưu

`docker compose down` dừng service, giữ named volume. **Không thêm `-v`** nếu
muốn giữ dữ liệu. Sao lưu DB bằng SQLite backup API hoặc dừng app trước khi copy;
không chỉ copy file `.sqlite3` đang chạy mà bỏ qua WAL.

Ứng dụng chạy một tiến trình, SQLite một volume và khóa suy luận CPU. Chưa
cấu hình nhiều replica. Không tự đổi thành nhiều container cùng ghi SQLite.
Các phiên login nằm trong DB; file DB/mật khẩu cần quyền truy cập phù hợp.

Nguồn đối chiếu: [Dockerfile reference](https://docs.docker.com/reference/dockerfile/),
[Caddy HTTPS](https://caddyserver.com/docs/automatic-https),
[Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).
