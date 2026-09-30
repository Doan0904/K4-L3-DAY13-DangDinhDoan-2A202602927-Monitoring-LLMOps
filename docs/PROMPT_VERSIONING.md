# Prompt versioning — bản ngắn gọn

Mục tiêu là tạo hai version trong cùng một prompt, thử từng version, đưa v2 lên `production` rồi rollback về v1.

## Ba khái niệm cần nhớ

| Khái niệm | Trong bài lab |
|---|---|
| Prompt name | Luôn là `day13-chat` |
| Version | v1 là bản cũ, v2 là bản mới |
| Label | `baseline` → v1, `candidate` → v2, `production` → bản đang chạy |

App lấy prompt theo hai dòng trong `.env`:

```dotenv
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

## Bước 1 — Tạo v1

Trong project Langfuse cá nhân, mở **Prompt Management** và tạo **Text prompt**:

- Name: `day13-chat`
- Labels: `baseline`, `production`
- Nội dung:

```text
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

Phải giữ đúng ba biến `{{feature}}`, `{{docs}}`, `{{message}}`.

## Bước 2 — Tạo v2

Mở lại `day13-chat` và tạo version mới trong cùng prompt, không tạo prompt name khác. Ví dụ:

```text
Answer in no more than three concise bullet points.
Feature={{feature}}
Docs={{docs}}
Question={{message}}
```

Gắn label `candidate` cho v2. Label `latest` do Langfuse tự tạo không thay thế `candidate`.

## Bước 3 — Kiểm tra hai version

Lần 1:

1. Đặt `LANGFUSE_PROMPT_LABEL=baseline`.
2. Restart API.
3. Chạy `python scripts/load_test.py`.
4. Ghi lại một trace ID có `prompt_label=baseline`, `prompt_version=1`.

Lần 2:

1. Đổi thành `LANGFUSE_PROMPT_LABEL=candidate`.
2. Restart API và chạy lại cùng workload.
3. Ghi lại một trace ID có `prompt_label=candidate`, `prompt_version=2`.

Hai trace ID được ghi vào `submission/REPORT.md`; không cần chụp riêng hai trace này.

## Bước 4 — Promote và rollback

1. Chuyển label `production` từ v1 sang v2 trên Langfuse.
2. Đặt `LANGFUSE_PROMPT_LABEL=production`, restart API và chạy một request.
3. Mở trace mới, xác nhận `prompt_label=production`, `prompt_version=2`; giữ tab này để chụp evidence.
4. Chuyển label `production` từ v2 về v1. Đây là rollback.

## Chỉ chụp một ảnh

Tên file: `submission/evidence/04-prompt-versioning.png`.

1. Sau rollback, mở trace `production` v2 ở một cửa sổ Langfuse.
2. Mở trang versions của `day13-chat` ở cửa sổ thứ hai.
3. Đặt hai cửa sổ cạnh nhau, thu gọn sidebar và zoom 80–90%.
4. Bên trái phải thấy trace ID, `prompt_label=production`, `prompt_version=2`.
5. Bên phải phải thấy `day13-chat`, v1 có `baseline` + `production`, v2 có `candidate`.
6. Chụp toàn màn hình. Không mở trang API Keys và không để lộ secret/PII.

Một ảnh này chứng minh cả promote lên v2 và rollback về v1.

## Nếu không thấy đúng version

- `prompt_source=local`: app chưa nhận Langfuse key.
- `prompt_source=local-fallback`: kiểm tra project, key, base URL, prompt name và label.
- Vẫn thấy version cũ: restart API vì SDK có cache prompt.
- Báo thiếu biến: kiểm tra đúng `feature`, `docs`, `message` với hai dấu ngoặc nhọn.

## Hoàn thành khi

- [ ] `day13-chat` có v1 và v2, giữ đủ ba biến.
- [ ] Report có trace ID của baseline v1 và candidate v2.
- [ ] Đã chạy `production` v2 và rollback `production` về v1.
- [ ] Có đúng một ảnh `04-prompt-versioning.png` đọc được đầy đủ thông tin.
