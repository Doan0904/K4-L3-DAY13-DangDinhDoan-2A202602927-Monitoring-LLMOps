# Evidence cá nhân

Đặt ảnh hoặc output text dùng để chấm vào thư mục này. Danh sách đầy đủ xem tại [docs/SUBMISSION.md](../../docs/SUBMISSION.md).

Ba output text:

```text
pytest.txt
log-validator.txt
dashboard-validator.txt
```

Đúng năm ảnh runtime:

```text
01-incident-log.png
02-trace-list.png
03-incident-trace.png
04-prompt-versioning.png
05-dashboard-incident.png
```

Ảnh 01 lấy từ `data/logs.jsonl`; ảnh 02–04 lấy từ project Langfuse cá nhân; ảnh 05 lấy từ dashboard. Không mở/chụp trang API Keys và không tách thêm ảnh nếu thông tin đã đọc được.

Từ `submission/REPORT.md`, dẫn ảnh bằng đường dẫn tương đối:

```markdown
![Incident trace](evidence/03-incident-trace.png)
```

Không commit secret, API key, PII thô hoặc evidence của học viên/lớp khác.
