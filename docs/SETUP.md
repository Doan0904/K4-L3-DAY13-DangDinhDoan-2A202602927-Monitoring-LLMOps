# Chuẩn bị môi trường K4-L3B Day 13

Các lệnh dưới đây chạy từ thư mục gốc của repository cá nhân. Không chia sẻ `.env` với học viên khác hoặc giữa hai lớp.

## Yêu cầu

- Python 3.11 trở lên.
- Git.
- Một tài khoản Langfuse Cloud do chính học viên đăng ký.
- Docker Desktop chỉ cần khi tự chọn chạy Langfuse local.

## 1. Tạo virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## 2. Tự tạo project Langfuse Cloud

Mỗi học viên dùng **project riêng**, không dùng chung project hoặc API key với bạn khác:

1. Mở [Langfuse Cloud](https://cloud.langfuse.com) và tự đăng ký/đăng nhập.
2. Tạo project tên `day13-k4-l3b-<MSSV>`, ví dụ `day13-k4-l3b-123456`.
3. Trong project, mở **Project Settings → API Keys** và tạo một key pair.
4. Copy public key và secret key vào `.env` của repo cá nhân:

```dotenv
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

5. Lưu `.env`, khởi động lại API, chạy `python scripts/load_test.py`, rồi mở đúng project để kiểm tra trace mới.

Không commit/chia sẻ `.env`, không gửi key cho bạn khác và không để key xuất hiện trong screenshot. Nếu chưa cấu hình key, app vẫn chạy bằng prompt local nhưng phần trace/prompt evidence chưa hoàn thành. Cấu hình môi trường này theo [tài liệu SDK chính thức của Langfuse](https://langfuse.com/docs/observability/sdk/overview).

> `data/logs.jsonl` là **structured log của ứng dụng**. Langfuse là nơi xem **traces/observations và prompt versions**. Hai nguồn này được nối bằng `correlation_id`; Langfuse không thay thế file log trong lab này.

## 3. Tùy chọn: chạy Langfuse local bằng Docker Compose

Phần này không bắt buộc và không được cộng điểm riêng. Chỉ dùng khi bạn không thể dùng Langfuse Cloud và máy có Docker Desktop đủ tài nguyên. Dù chạy local, mỗi học viên vẫn phải tự tạo project và tự sinh trace của mình.

Ở một thư mục nằm ngoài repo bài nộp:

```bash
git clone https://github.com/langfuse/langfuse.git langfuse-local
cd langfuse-local
docker compose up -d
```

Chờ container `langfuse-web` sẵn sàng, sau đó mở `http://localhost:3000`, tạo project và lấy public/secret key. Trong repo lab, đặt:

```dotenv
LANGFUSE_BASE_URL=http://localhost:3000
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

Khi kết thúc buổi lab, dừng stack từ thư mục `langfuse-local`:

```bash
docker compose down
```

Không dùng `docker compose down -v` nếu còn cần dữ liệu trace/prompt trong volume. Xem hướng dẫn cập nhật tại [Langfuse Docker Compose](https://langfuse.com/self-hosting/deployment/docker-compose).

## 4. Kiểm tra cài đặt

Terminal 1:

```bash
uvicorn app.main:app --reload --env-file .env
```

Terminal 2:

```bash
python scripts/load_test.py
python scripts/validate_logs.py
python scripts/validate_dashboard.py
python -m pytest -q
```

API mặc định chạy tại `http://127.0.0.1:8000`; health check ở `/health`, metrics ở `/metrics`.

## Lỗi thường gặp

- PowerShell chặn `Activate.ps1`: chạy `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi activate lại.
- `ModuleNotFoundError`: kiểm tra virtual environment đã được activate và chạy lại `pip install -r requirements.txt`.
- `ModuleNotFoundError: No module named 'app'` hoặc `'scripts'` khi chạy test: dùng `python -m pytest -q` từ thư mục gốc thay vì gọi `pytest` trực tiếp.
- Không có `data/logs.jsonl`: bảo đảm API đang chạy trước khi chạy load test.
- Không thấy trace: xác nhận key thuộc đúng project cá nhân, kiểm tra ba biến `LANGFUSE_*`, khởi động lại API rồi chạy lại load test; đợi vài giây và chọn time range gần nhất trên Langfuse.
- Trace ghi `prompt_source=local-fallback`: kiểm tra host/key và prompt name/label trong `.env`.
- Docker local không lên: chạy `docker compose ps`, kiểm tra Docker Desktop và tài nguyên máy; ưu tiên quay về project cá nhân trên Langfuse Cloud.
- Thiếu challenge ở CP3: trên fork chọn **Sync fork → Update branch**, sau đó chạy `git pull --ff-only` và kiểm tra lại `config/challenge.json`; không lấy file từ lớp khác.
