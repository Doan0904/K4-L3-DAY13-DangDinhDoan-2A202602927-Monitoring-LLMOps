# Rubric cá nhân Day 13 Monitoring & LLMOps

Điểm bắt buộc là 100 và được chấm hoàn toàn trên bài làm cá nhân. Bonus tối đa 10 điểm, tổng tối đa 110. Mọi điểm phải có code chạy được và evidence thuộc đúng repository/commit SHA của học viên.

## A. Logging và correlation — 15 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Nhận `x-request-id` hoặc sinh ID hợp lệ, truyền và trả lại qua response header | 6 | middleware, response header và structured log |
| Log JSON có event, timestamp, `correlation_id` và metadata model/env/feature | 4 | `01-incident-log` và source liên quan |
| Log validator đạt tối thiểu 80/100, không rò context giữa request | 5 | `log-validator.txt` và tests |

Không đạt tối đa nếu chỉ hard-code output để vượt validator hoặc log không nối được với trace.

## B. PII protection — 10 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Có rule cho email, điện thoại Việt Nam, CCCD và thẻ thanh toán | 4 | `app/pii.py` và tests |
| PII được scrub trước bước render/ghi file | 3 | logging processor/config và giải thích trong report |
| Log/trace thực tế không còn PII mẫu nguyên văn | 3 | `log-validator.txt`, tests và `03-incident-trace` |

Ảnh chỉ chụp regex hoặc code không thay thế evidence runtime.

## C. Tracing và prompt version — 15 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Có tối thiểu 10 traces do học viên tự tạo trong project Langfuse cá nhân và nối được với log bằng `correlation_id` | 4 | `02-trace-list`, `03-incident-trace` |
| Trace có root, retrieval và generation đúng quan hệ cha-con; có model, token và cost | 4 | `03-incident-trace` |
| Có prompt v1/v2 và trace gắn đúng name/version/label | 4 | `04-prompt-versioning` và trace IDs trong report |
| Chứng minh promote/rollback label `production` | 3 | `04-prompt-versioning` |

Trace không có child observation, chứa PII thô hoặc lấy từ project dùng chung/người khác không được tính.

## D. Dashboard, SLO và alerts — 15 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Dashboard có dữ liệu và đủ 6 panel: latency/TTFT, traffic, errors/retrieval, cost, tokens, quality | 6 | `05-dashboard-incident` |
| Có đơn vị, time range và threshold/SLO line hợp lý | 3 | dashboard runtime |
| Một SLO và error budget được giải thích | 2 | `config/slo.yaml` và report |
| Ba alert symptom-based có duration, severity, owner, Slack channel và runbook | 2 | `config/alert_rules.yaml`, `docs/alerts.md` |
| Dashboard validator đạt 6/6 | 2 | `dashboard-validator.txt` |

Validator 6/6 nhưng không có dashboard runtime vẫn không đạt đủ điểm.

## E. Incident investigation — 15 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Ghi đúng challenge ID, metric bất thường và khoảng thời gian | 3 | `05-dashboard-incident` |
| Tìm log line/`correlation_id` liên quan | 3 | `01-incident-log` |
| Tìm trace có cùng `correlation_id` và span gây ảnh hưởng | 3 | `03-incident-trace` |
| Root cause phù hợp với chuỗi evidence | 3 | report và Q&A |
| Fix action và preventive measure khả thi | 3 | report |

Metric, log và trace không cùng sự cố sẽ không được tính là một investigation hoàn chỉnh.

## F. Integration và khả năng tái hiện — 10 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| Tests chạy trên commit cuối | 5 | `pytest.txt` |
| Repository cài đặt và chạy lại được theo README | 3 | source, requirements và lệnh demo |
| Không có secret, PII thô hoặc artifact không cần thiết | 2 | repository và checklist |

## G. Báo cáo, evidence và hiểu bài — 20 điểm

| Thành phần | Điểm | Bằng chứng |
|---|---:|---|
| `submission/REPORT.md` đầy đủ, rõ ràng và mọi link evidence mở được | 5 | report và evidence |
| Có quyết định kỹ thuật, blocker và cách xử lý cụ thể | 5 | report và Q&A |
| Giải thích được Metrics → Logs → Traces → Root cause | 6 | report và Q&A |
| Giải thích được prompt version, token/cost, SLO hoặc rollback trong vận hành LLM | 4 | report và Q&A |

## H. Bonus — tối đa 10 điểm

Chỉ chấm bonus khi phần bắt buộc chạy được end-to-end:

- Tối đa +5: cost optimization có before/after trên cùng workload.
- Tối đa +5: automation hữu ích như secret/PII scan, dashboard generation hoặc CI.
- Tối đa +5: audit log riêng có schema, retention và truy vấn minh họa.

Tổng bonus không vượt 10 điểm.

## I. Technical gates và vi phạm

- `validate_logs.py` và `validate_dashboard.py` là technical gates, không thay thế evidence runtime hoặc rubric.
- Screenshot không thay thế source/config; source/config không thay thế screenshot runtime.
- Chỉ chấm artifact có trong commit SHA của repository cá nhân đã nộp.

| Vi phạm | Mức xử lý |
|---|---:|
| Commit API key, secret hoặc PII | -20 điểm; có thể 0 điểm nếu rò rỉ nghiêm trọng |
| Sửa/tự tạo challenge chính thức hoặc dùng challenge sai lớp | 0 điểm phần incident; có thể hủy bài nếu làm giả evidence |
| Sao chép source, report, dashboard, trace ID hoặc evidence | 0 điểm toàn bài |
| Làm giả trace, screenshot, log hoặc commit history | 0 điểm toàn bài |
| Nộp repository chung thay vì repository cá nhân | Bài không hợp lệ; yêu cầu nộp lại và có thể trừ 5 điểm |
| Repository không chạy được end-to-end | -15 điểm |
| Hard-code output chỉ để vượt validator | -15 điểm |
| Thiếu `submission/REPORT.md` hoặc evidence bắt buộc | -5 điểm mỗi hạng mục; phần liên quan không có căn cứ để chấm |
| Tên repo hoặc nội dung nộp sai quy ước | Yêu cầu nộp lại; có thể trừ 5 điểm |
| Nộp muộn hoặc sửa bài sau deadline | Áp dụng theo [RULES.md](RULES.md) |

Danh sách và cách đặt evidence xem tại [SUBMISSION.md](SUBMISSION.md) và [grading-evidence.md](grading-evidence.md).
