# Checkpoints Day 13 Monitoring & LLMOps

Lab diễn ra từ 9:00 đến 13:00, tổng thời lượng 240 phút. Mỗi checkpoint chỉ hoàn thành khi có sản phẩm, hiểu được nguyên lý và chạy được bước tự kiểm tra tương ứng.

## Tổng quan thời gian

| Mốc | Thời gian | Trọng tâm | Sản phẩm chính | Tự kiểm tra |
|---|---:|---|---|---|
| CP0 | 9:00–9:30 (0:00–0:30) | Setup và baseline | API, `data/logs.jsonl`, baseline validators | `/health`, load test, pytest |
| CP1 | 9:30–10:20 (0:30–1:20) | Logging và PII | Correlation ID, metadata, redaction | `validate_logs.py` ≥ 80/100 |
| CP2 | 10:20–11:40 (1:20–2:40) | Metrics, traces, prompt và dashboard | ≥10 traces, prompt v1/v2, 6 panel | dashboard `6/6 panel` |
| CP3 | 11:40–12:30 (2:40–3:30) | Challenge chính thức | Root cause có metric, log và trace | evidence khớp challenge ID |
| CP4 | 12:30–13:00 (3:30–4:00) | Báo cáo và demo | `REPORT.md`, evidence, commit SHA | full test + secret scan |

Đây là bài cá nhân. Trong mỗi checkpoint, hãy ghi correlation ID, trace ID và kết quả vào `submission/REPORT.md`. Bộ 5 ảnh cuối chỉ chụp sau CP3 để một ảnh có thể chứng minh nhiều tiêu chí; CP4 dùng để lưu ba output text và kiểm tra link.

## CP0 Setup và baseline

### Cần làm

- Làm theo [SETUP.md](SETUP.md).
- Tự tạo project Langfuse Cloud tên `day13-k4-l3b-<MSSV>` và cấu hình key của chính bạn trong `.env`.
- Chạy API, load test và các public tests.
- Lưu kết quả baseline của `validate_logs.py` và `validate_dashboard.py`.

### Cần hiểu

- Langfuse quản lý trace/prompt; `data/logs.jsonl` là structured log và nguồn dashboard. Hai nguồn khác nhau nhưng cùng có `correlation_id`.
- Baseline chưa đạt validator là bình thường vì repo chứa TODO dành cho học viên.

### Hoàn thành khi

```powershell
python scripts/load_test.py
python scripts/validate_logs.py
python scripts/validate_dashboard.py
python -m pytest -q
```

API trả `ok: true`, log được tạo, trace xuất hiện trong đúng project Langfuse cá nhân và bạn ghi lại baseline thực tế.

## CP1 Logging và PII

### Cần làm

- Tạo hoặc nhận `x-request-id` theo format `req-<8-hex>`.
- Xóa context cũ và bind correlation ID trước khi xử lý request.
- Bind `user_id_hash`, `session_id`, `feature`, `model`, `env`.
- Đăng ký PII processor trước JSON renderer/file writer.
- Bổ sung pattern cần thiết và test email, điện thoại, CCCD, thẻ.
- Trước khi đo lại, lưu bản baseline rồi xóa hoặc đổi tên `data/logs.jsonl`; validator đọc toàn bộ file nên log cũ từ trước khi sửa code vẫn bị tính lỗi.

### Cần hiểu

- Correlation ID nối log trong một request; trace ID nối các span phân tán.
- Redaction phải xảy ra trước khi dữ liệu được serialize hoặc ghi xuống file.

### Hoàn thành khi

`python scripts/validate_logs.py` đạt tối thiểu 80/100, không còn PII nguyên văn trong sample log và response trả lại correlation ID hợp lệ.

## CP2 Metrics traces prompt và dashboard

### Cần làm

- Tự chạy workload để tạo tối thiểu 10 traces trong project Langfuse cá nhân; không dùng trace ID của người khác.
- Dùng API observation của Langfuse Python SDK v4 để tách child observation cho retrieval và LLM; starter mới chỉ có root observation cho `LabAgent.run`.
- Làm theo [PROMPT_VERSIONING.md](PROMPT_VERSIONING.md) để tạo prompt v1/v2.
- Chạy cùng input với hai label và thực hiện một lần đổi label hoặc rollback.
- Dựng đúng sáu panel theo [`../config/dashboard.yaml`](../config/dashboard.yaml).
- Giải thích hoặc điều chỉnh một SLO, tính error budget, rồi hoàn thiện ba alert (có duration, Slack channel) và runbook.

### Cần hiểu

- P95/P99 phản ánh tail latency tốt hơn average.
- Prompt version phải đến từ Langfuse; không hard-code metadata giả.
- Validator chỉ kiểm tra contract, không chứng minh dashboard runtime dùng đúng dữ liệu.

### Hoàn thành khi

- `python scripts/validate_dashboard.py` báo `HỢP LỆ: 6/6 panel`.
- Evidence có danh sách trace, waterfall, hai prompt version, rollback và dashboard có time range, đơn vị, threshold; panel latency có TTFT và panel errors có retrieval success.

## CP3 Challenge chính thức

### Cần làm

Sau khi Lab Coach thông báo mở CP3, sync fork và pull bản mới nhất để nhận `config/challenge.json` chính thức của K4-L3B. Không sửa hoặc thay file bằng challenge lớp khác:

```powershell
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5
```

1. Xác định triệu chứng và khoảng thời gian trên dashboard/metrics.
2. Lọc log trong khoảng đó và lấy một correlation ID bất thường.
3. Tìm trace có cùng correlation ID.
4. Khoanh vùng span gây ảnh hưởng.
5. Kết luận root cause, fix action và preventive measure.

### Cần hiểu

Một kết luận incident chỉ hợp lệ khi metric, log và trace cùng chỉ về một nguyên nhân. Challenge ID, seed và query phải khớp file chính thức trong starter L3B mới nhất.

### Hoàn thành khi

Report dẫn được metric cụ thể, correlation ID/log line, trace ID, root cause và đề xuất xử lý có thể kiểm chứng.

## CP4 Báo cáo và demo

### Cần làm

- Hoàn thiện báo cáo cá nhân duy nhất tại `submission/REPORT.md`.
- Thu đúng 3 output text và 5 ảnh runtime theo `docs/SUBMISSION.md`; tái sử dụng ảnh logging/tracing/dashboard cho incident, không chụp trùng.
- Đặt evidence trong `submission/evidence/` và dẫn bằng đường dẫn tương đối.
- Chạy lại tests và validators trên commit cuối.
- Rà `.env`, secret, PII và file cache trước khi push.

### Hoàn thành khi

- Demo được luồng Metrics → Logs → Traces → Root cause.
- Các ảnh/output đọc được, đúng commit nộp và không chứa secret/PII.
- Bạn giải thích được các quyết định kỹ thuật và blocker trong báo cáo/Q&A.
- URL repo cá nhân và commit SHA cuối đã được nộp trước deadline.
