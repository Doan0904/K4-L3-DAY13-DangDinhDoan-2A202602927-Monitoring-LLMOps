# Hướng dẫn chụp evidence

File này hướng dẫn cách chụp ảnh/output để nộp bài. Danh sách chính thức vẫn nằm trong [SUBMISSION.md](SUBMISSION.md); file này chỉ giải thích cụ thể hơn từng ảnh cần chụp gì.

## Nguyên tắc chung

- Đặt toàn bộ evidence trong `submission/evidence/`.
- Có thể dùng ảnh `.png` hoặc output text `.txt` cho test/validator.
- Ảnh phải đọc được chữ, số liệu, ID và tên màn hình liên quan.
- Không chụp hoặc commit `.env`, API key, secret key, token.
- Không để lộ PII thô như email thật, số điện thoại thật, CCCD thật.
- Ảnh Langfuse nên nhìn thấy tên project cá nhân `day13-k4-l3b-<MSSV>`, nhưng tuyệt đối không mở trang API Keys.
- Dùng đường dẫn tương đối trong `submission/REPORT.md`, ví dụ:

```markdown
![Trace waterfall](evidence/07-trace-waterfall.png)
```

## 01-pytest

Chụp terminal sau khi chạy:

```bash
python -m pytest -q
```

Ảnh hoặc file text cần thấy:

- lệnh đã chạy;
- số test pass/fail;
- không bị cắt mất dòng kết quả cuối.

Tên gợi ý:

```text
submission/evidence/01-pytest.png
```

## 02-log-validator

Chụp terminal sau khi chạy:

```bash
python scripts/validate_logs.py
```

Cần thấy:

- lệnh đã chạy;
- điểm validator;
- kết quả đạt tối thiểu yêu cầu của lab.

Tên gợi ý:

```text
submission/evidence/02-log-validator.png
```

## 03-dashboard-validator

Chụp terminal sau khi chạy:

```bash
python scripts/validate_dashboard.py
```

Cần thấy:

- lệnh đã chạy;
- kết quả dashboard hợp lệ;
- đủ 6/6 panel nếu validator hiển thị số panel.

Tên gợi ý:

```text
submission/evidence/03-dashboard-validator.png
```

## 04-structured-log

Chụp terminal hoặc mở `data/logs.jsonl` để chụp một vài dòng log JSON.

Cần thấy các field quan trọng:

- `ts`;
- `event`;
- `correlation_id`;
- `service`;
- `feature`;
- `model`;
- `env`;
- `latency_ms` nếu là log response.

Không cần chụp quá nhiều dòng. Chỉ cần đủ để chứng minh log có cấu trúc và có metadata.

Tên gợi ý:

```text
submission/evidence/04-structured-log.png
```

## 05-pii-redaction

Chụp bằng chứng rằng input có PII giả nhưng log đã được che.

Cách làm gợi ý:

1. Gửi một request test chứa PII giả, ví dụ email giả, số điện thoại giả, CCCD giả hoặc số thẻ giả.
2. Mở log tương ứng trong terminal hoặc `data/logs.jsonl`.
3. Chụp phần log cho thấy dữ liệu đã thành dạng `[REDACTED_...]`.

Cần thấy:

- PII không còn nguyên văn trong log;
- log vẫn còn `correlation_id`;
- không dùng PII thật của người dùng.

Tên gợi ý:

```text
submission/evidence/05-pii-redaction.png
```

## 06-trace-list

Chụp danh sách traces trong Langfuse.

Cần thấy:

- tên project cá nhân `day13-k4-l3b-<MSSV>`;
- danh sách tối thiểu 10 traces do bạn tự chạy workload tạo ra;
- time range gần thời điểm bạn chạy lab.

Không chụp trang API Keys.

Tên gợi ý:

```text
submission/evidence/06-trace-list.png
```

## 07-trace-waterfall

Mở một trace cụ thể trên Langfuse và chụp waterfall/span tree.

Cần thấy:

- root trace/request;
- span/observation cho agent;
- span/observation cho retrieval;
- span/observation cho generation;
- quan hệ cha-con nhìn được.

Tên gợi ý:

```text
submission/evidence/07-trace-waterfall.png
```

## 08-trace-metadata

Mở metadata của trace hoặc observation liên quan.

Cần thấy:

- `correlation_id`;
- model;
- prompt name/label/version;
- token hoặc usage;
- cost nếu có;
- không có raw PII.

Tên gợi ý:

```text
submission/evidence/08-trace-metadata.png
```

## 09-prompt-versions

Chụp màn hình prompt trong Langfuse.

Cần thấy:

- prompt name, ví dụ `day13-chat`;
- tối thiểu hai version;
- các label liên quan như `baseline`, `candidate`, `production` nếu bạn dùng theo hướng dẫn.

Tên gợi ý:

```text
submission/evidence/09-prompt-versions.png
```

## 10-prompt-rollback

Chụp bằng chứng promote hoặc rollback prompt.

Cần thấy một trong hai kiểu bằng chứng:

- trước/sau khi label `production` chuyển version;
- hoặc trace IDs chứng minh request trước và sau dùng version khác nhau.

Trong `submission/REPORT.md`, ghi rõ trace ID nào dùng version nào.

Tên gợi ý:

```text
submission/evidence/10-prompt-rollback.png
```

## 11-dashboard-overview

Chụp dashboard runtime có dữ liệu thật.

Cần thấy:

- đủ 6 panel hoặc tách thành nhiều ảnh nếu một ảnh không đọc rõ;
- tên panel;
- time range;
- đơn vị;
- threshold hoặc SLO line nếu có;
- dữ liệu không bị trống.

Nếu một ảnh quá nhỏ, có thể tách:

```text
11a-dashboard-latency-errors.png
11b-dashboard-cost-token-quality.png
```

Tên gợi ý:

```text
submission/evidence/11-dashboard-overview.png
```

## 12-incident-metric

Chụp dashboard hoặc metrics cho thấy sự cố trong challenge.

Cần thấy:

- metric bất thường;
- khoảng thời gian xảy ra;
- giá trị đủ đọc để đối chiếu với report.

Không cần kết luận root cause trong ảnh này. Ảnh này chỉ chứng minh triệu chứng.

Tên gợi ý:

```text
submission/evidence/12-incident-metric.png
```

## 13-incident-log

Chụp log line đại diện cho request bất thường.

Cần thấy:

- `event` liên quan;
- `correlation_id`;
- metric/log field bất thường nếu có;
- thời gian gần với ảnh metric.

Log này phải nối được với trace ở ảnh `14-incident-trace`.

Tên gợi ý:

```text
submission/evidence/13-incident-log.png
```

## 14-incident-trace

Mở trace có cùng `correlation_id` với ảnh log.

Cần thấy:

- trace hoặc metadata có cùng `correlation_id`;
- span/observation bất thường;
- đủ thông tin để giải thích root cause trong report.

Không chụp trang chứa secret hoặc API key.

Tên gợi ý:

```text
submission/evidence/14-incident-trace.png
```

## Cách kiểm tra nhanh trước khi nộp

Trước khi nộp, mở lại `submission/REPORT.md` trên GitHub hoặc local preview và kiểm tra:

- mọi ảnh/link đều mở được;
- ảnh đủ lớn để đọc chữ;
- không có secret/PII;
- evidence thuộc đúng commit cuối;
- incident metric, log và trace nối được với nhau;
- report không dẫn đường dẫn cục bộ như `C:\...` hoặc `/Users/...`.

Nếu ảnh nào không đọc rõ, hãy chụp lại hoặc tách thành nhiều ảnh nhỏ hơn.
