# Evidence dùng để chấm bài

Danh sách chính thức, quy tắc chụp và cách nộp nằm tại [SUBMISSION.md](SUBMISSION.md). File này là checklist nhanh khi bạn thu thập evidence cá nhân.

## Evidence runtime bắt buộc

Ba output text:

- [ ] `pytest.txt`.
- [ ] `log-validator.txt` đạt tối thiểu 80/100 và không phát hiện PII leak.
- [ ] `dashboard-validator.txt` đạt 6/6.

Đúng năm ảnh:

- [ ] `01-incident-log.png`: structured log và incident log.
- [ ] `02-trace-list.png`: project cá nhân và tối thiểu 10 traces.
- [ ] `03-incident-trace.png`: waterfall, metadata và incident span.
- [ ] `04-prompt-versioning.png`: v1/v2, labels, promote và rollback.
- [ ] `05-dashboard-incident.png`: 6 panel và incident metric.

## Artifact kiểm tra trực tiếp trên repo

Không cần chụp toàn bộ code. Dẫn link tới:

- `config/slo.yaml` và phần giải thích error budget trong `submission/REPORT.md`;
- `config/alert_rules.yaml` và `docs/alerts.md`;
- source, tests và commit history;
- `submission/REPORT.md`.

## Chất lượng evidence

- Evidence phải thuộc commit SHA được nộp và đúng challenge của lớp.
- Ảnh phải đọc được thông tin dùng để chấm, không phải ảnh trang trống.
- Che secret và PII; không dùng dữ liệu thật.
- Trace/prompt phải thuộc project cá nhân `day13-k4-l3b-<MSSV>`; không chụp trang API Keys.
- Đặt file trong `submission/evidence/`.
- Dẫn đường dẫn tương đối từ report, ví dụ `evidence/03-incident-trace.png`.
- Metric, log và trace của incident phải cùng chỉ về một nguyên nhân.
