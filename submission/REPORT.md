# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Chỉ cần 3 output text và 5 ảnh runtime; dùng đường dẫn tương đối, ví dụ `evidence/03-incident-trace.png`.

## 1. Thông tin học viên

- **Họ và tên:** Đặng Đỉnh Đoàn
- **MSSV:** 2A202602927
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/Doan0904/K4-L3-DAY13-DangDinhDoan-2A202602927-Monitoring-LLMOps
- **Commit SHA cuối:** 697b846a2b6812646068df27cac3de080a3c97b3
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602927`

## 2. Evidence index

Giữ đúng ba output text và năm ảnh dưới đây. Không tách thêm ảnh; nếu cần giải thích, ghi bằng chữ trong các mục sau.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | [evidence/pytest.txt](evidence/pytest.txt) |
| Log validator | [evidence/log-validator.txt](evidence/log-validator.txt) |
| Dashboard validator | [evidence/dashboard-validator.txt](evidence/dashboard-validator.txt) |
| Structured log + incident log | [evidence/01-incident-log.png](evidence/01-incident-log.png) |
| Trace list | [evidence/02-trace-list.png](evidence/02-trace-list.png) |
| Trace waterfall + metadata + incident trace | [evidence/03-incident-trace.png](evidence/03-incident-trace.png) |
| Prompt versions + promote/rollback | [evidence/04-prompt-versioning.png](evidence/04-prompt-versioning.png) |
| Dashboard + incident metric | [evidence/05-dashboard-incident.png](evidence/05-dashboard-incident.png) |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 (20/21 dòng thiếu `correlation_id`, thiếu enrichment) | 100/100 (199 dòng, 101 correlation ID) | Validator đọc toàn bộ file nên đã đổi log baseline ra khỏi `data/logs.jsonl` trước khi đo lại |
| `validate_dashboard.py` | 6/6 | 6/6 | Contract giữ nguyên; dashboard runtime dựng bằng `scripts/dashboard.py` |
| `pytest` | 22 passed | 37 passed | Thêm test PII (CCCD, thẻ, hộ chiếu), correlation/context leak, lỗi 500, span tree, dashboard, alert/SLO |
| Số traces hợp lệ | 0 (chưa có key) | 26 (10 load test + 6 bước prompt + 5 challenge + 5 sau fix), mỗi trace có 3 observations | Request đầu tiên của mỗi instance ~1.3–1.5s do fetch prompt lần đầu (cache lạnh), sau đó ~153ms |
| Số PII leak | 0 (starter đã dùng `summarize_text`) | 0 | Scrubber nay chạy trên mọi field trước khi ghi file, không chỉ preview |
| Latency P95 / TTFT P95 | 150 ms / 50 ms | Bình thường: 153 ms / 50 ms; trong challenge: 2660 ms / 50 ms; sau fix: 153 ms / 50 ms | TTFT không đổi còn latency tăng → bước chậm nằm trước generation |
| Retrieval success rate | 100% | Bình thường 100%; cửa sổ có practice `tool_fail`: 83.1% | Panel errors chuyển sang BREACH (error rate 16.9% > 2%) |

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** [`app/middleware.py`](../app/middleware.py) gọi `clear_contextvars()` ở đầu mỗi request, nhận `x-request-id` nếu hợp lệ (`^[A-Za-z0-9._-]{1,64}$`, chống log injection) hoặc sinh `req-<8-hex>`, `bind_contextvars(correlation_id=...)`, lưu vào `request.state` để truyền vào agent/trace và trả về qua header `x-request-id` và `x-response-time-ms`. Response lỗi 500 cũng trả `correlation_id` trong body.
- **Các metadata được ghi vào structured log:** [`app/main.py`](../app/main.py) bind `user_id_hash` (SHA-256 cắt 12 ký tự, không log `user_id` gốc), `session_id`, `feature`, `model`, `env` trước log `request_received`; `response_sent` có thêm `latency_ms`, `ttft_ms`, `tokens_in/out`, `cost_usd`, `quality_score`, `tool_name`, `tool_success`; `request_failed` có `error_type`, `tool_success=false`.
- **Cách bảo đảm PII được scrub trước khi ghi:** [`app/logging_config.py`](../app/logging_config.py) đăng ký `scrub_event` sau `format_exc_info` (để cả exception text cũng được scrub) và **trước** `JsonlFileProcessor`/`JSONRenderer`. `scrub_event` duyệt đệ quy mọi giá trị chuỗi (kể cả dict/list lồng nhau). [`app/pii.py`](../app/pii.py) có pattern email, thẻ thanh toán, CCCD 12 số, điện thoại VN (`0`/`+84`, có dấu cách/chấm/gạch), hộ chiếu VN; thẻ chạy trước điện thoại/CCCD để không bị redact một phần.
- **Cách kiểm chứng kết quả:** [`tests/test_pii.py`](../tests/test_pii.py), [`tests/test_logging_context.py`](../tests/test_logging_context.py) (ID sinh/nhận, header, không rò context giữa 2 request, không còn PII trong file log); runtime ở log validator và structured log trong ảnh `01-incident-log.png`.

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:** [02-trace-list.png](evidence/02-trace-list.png) nhìn thấy tên project `day13-k4-l3b-2A202602927`; mỗi trace có metadata `correlation_id` trùng với dòng log trong `data/logs.jsonl` của tôi (tra bằng `python scripts/find_trace.py --cid <id>`).
- **Cấu trúc root/retrieval/generation observations:** trace `day13-agent-request` → root `lab-agent-run` (agent, `@observe`) → `retrieval` (retriever: input `query_preview` đã scrub, output `doc_count`, level `ERROR` khi retrieval lỗi) và `llm-generation` (generation: `model`, `usage_details` input/output, `cost_details` input/output/total, `completion_start_time` = TTFT). Code: [`app/agent.py`](../app/agent.py) (`_retrieve`, `_generate`), helper `start_observation` trong [`app/tracing.py`](../app/tracing.py). Đã kiểm tra quan hệ cha-con bằng OTel in-memory exporter và test [`tests/test_agent_prompt_trace.py`](../tests/test_agent_prompt_trace.py).
- **Cách nối trace với log:** `correlation_id` được đưa vào trace metadata qua `propagate_attributes(metadata=...)`; trên Langfuse filter metadata `correlation_id`, ở log dùng `python scripts/query_logs.py --cid <id>`.
- **Prompt name:** `day13-chat`
- **Version/label baseline:** v1 — labels `baseline`, `production` (ban đầu)
- **Version/label candidate:** v2 — label `candidate` (thêm yêu cầu trả lời tối đa 3 bullet, giữ 3 biến `feature`/`docs`/`message`)
- **Trace ID của mỗi version** (cùng input *"Explain why metrics traces and logs work together"*, chi tiết ở ảnh `04-prompt-versioning.png`):

  | Bước | Label | correlation_id | Trace ID | prompt_version |
  |---|---|---|---|---|
  | Chạy baseline | `baseline` | `req-206f35ff` | `40066ca2a0784fd2867350d055c53f80` | 1 |
  | Chạy candidate | `candidate` | `req-95faa45b` | `617b79ba86e2ffd727896d4d9b90495a` | 2 |
  | Sau promote `production` → v2 | `production` | `req-0f5a7272` | `7ef8b6fca56100406298f4ebe4360b25` | 2 |
  | Sau rollback `production` → v1 | `production` | `req-3a5450b3` | `3cf9853ee4f9a1849674a80232a13860` | 1 |
- **Cách promote và rollback `production`:** chuyển label `production` sang v2 (`python scripts/prompt_versions.py promote --version 2` hoặc trên UI), chạy 1 request và kiểm tra `prompt_version=2` trong trace; sau đó rollback `production` về v1 và kiểm tra lại. Không cần sửa code vì app chỉ hỏi Langfuse theo `LANGFUSE_PROMPT_NAME` + `LANGFUSE_PROMPT_LABEL`. Lưu ý app cache prompt 60 giây.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** [`scripts/dashboard.py`](../scripts/dashboard.py) đọc `data/logs.jsonl` và [`config/dashboard.yaml`](../config/dashboard.yaml): latency P50/P95/P99 + TTFT P95, traffic (req/phút), error rate + breakdown `error_type` + retrieval success, cost theo phút + tổng, tokens in/out, quality mean. Mỗi panel có unit, threshold (đường đỏ nét đứt + nhãn OK/BREACH), time range 60 phút, auto refresh 30 giây (`--serve`).
- **SLO và lý do chọn:** [`config/slo.yaml`](../config/slo.yaml) — 99.5% request `response_sent` với `latency_ms ≤ 3000` trên tổng `request_received`, cửa sổ 28 ngày. Baseline P95 ≈ 153 ms nên 3000 ms có dư địa lớn và khớp threshold của dashboard contract; request lỗi không có `response_sent` nên tự động bị tính là xấu.
- **Cách tính error budget:** budget = 0.5% tổng request. 10,000 request / 28 ngày → tối đa 50 request lỗi hoặc > 3000 ms. Trong đợt practice `tool_fail` (cửa sổ 60 phút đến 02:49 UTC) có 11/65 request lỗi (16.9%) → burn rate ≈ 16.9 / 0.5 ≈ 34 lần, tức budget 28 ngày sẽ cạn trong < 1 ngày nếu kéo dài.
- **Ba alert và runbook tương ứng:** [`config/alert_rules.yaml`](../config/alert_rules.yaml), runbook [`docs/alerts.md`](../docs/alerts.md):
  1. `HighLatencyP95` (warning, 5m, `#k4-l3b-alerts`): P95 > 1500 ms. Đặt thấp hơn SLO line vì practice `rag_slow` chỉ lên 2653 ms — alert ở 3000 ms sẽ bỏ sót.
  2. `HighErrorRateOrRetrievalFailure` (critical, 3m, `#k4-l3b-oncall`): error rate > 2% hoặc retrieval success < 90%.
  3. `CostPerRequestSpike` (warning, 10m, `#k4-l3b-alerts`): cost trung bình/request > 0.005 USD (≈ 2× baseline 0.0023) hoặc `tokens_out` trung bình > 300 (baseline ≈ 145) — đo theo request nên không kêu khi chỉ traffic tăng.

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (cohort K4, seed 1312, 5 query feature `monitoring`, `latency_threshold_ms=2000`)
- **Khoảng thời gian điều tra:** 2026-09-30 04:09:20 → 04:09:33 UTC (workload challenge); đối chứng trước sự cố 03:06–03:11 UTC; kiểm chứng sau fix 04:12 UTC.
- **Triệu chứng từ metrics:** latency P50/P95/P99 = 2653/2660/2660 ms (trước đó P50 152 ms), 5/5 request vượt 2000 ms, trong khi TTFT P95 giữ 50 ms, error rate 0%, retrieval success 100%, tokens/cost bình thường (ảnh dashboard ở [05-dashboard-incident.png](evidence/05-dashboard-incident.png)). Alert `HighLatencyP95` (> 1500 ms) sẽ bắn; panel latency của contract (ngưỡng 3000 ms) vẫn hiện OK.
- **Log line và correlation ID liên quan:** `response_sent` `correlation_id=req-7bc7209c`, `feature=monitoring`, `latency_ms=2660`, `ttft_ms=50`, `tokens_out=104`, `tool_success=true`, ts `04:09:22.925Z` (ảnh structured log ở [01-incident-log.png](evidence/01-incident-log.png)). Cả 5 request challenge đều có dạng này.
- **Trace ID và span gây ảnh hưởng:** trace `cf90bac90e7321d7b538444a6898f62c` (metadata `correlation_id=req-7bc7209c`): `lab-agent-run` 2664 ms, trong đó **`retrieval` 2502 ms (~94%)**, `llm-generation` 152 ms (bằng baseline), prompt `day13-chat` v1 (không đổi). 4 trace còn lại đều có retrieval ≈ 2501 ms (ảnh trace ở [03-incident-trace.png](evidence/03-incident-trace.png)).
- **Root cause:** bước retrieval (RAG/vector store) chậm thêm ~2.5 s mỗi request (sự cố `rag_slow` được bật lúc 04:09:04 theo log `incident_enabled`). LLM generation, prompt version và token/cost đều không đổi nên không phải nguyên nhân. Vì agent chạy đồng bộ trong endpoint async, các request đồng thời bị xếp hàng nên người dùng chờ lâu hơn nữa (response log cách nhau đúng ~2.66 s).
- **Fix action:** khôi phục retrieval về trạng thái bình thường (`python scripts/inject_incident.py --disable`), chạy lại cùng workload challenge: latency server 152–153 ms, span retrieval 0 ms (trace `8da8485137b429364937b8b03ad14c75`).
- **Preventive measure:** (1) giữ alert `HighLatencyP95` ở 1500 ms thay vì dựa vào ngưỡng 3000 ms; thêm alert riêng trên duration span retrieval (ví dụ P95 retrieval > 500 ms trong 5 phút); (2) đặt timeout + fallback cho retrieval (quá 800 ms thì trả lời với context rỗng/cached và log `tool_success=false`) để một dependency chậm không kéo cả request; (3) chạy agent trong threadpool (`run_in_threadpool`) để request chậm không chặn event loop; (4) runbook [Alert 1](../docs/alerts.md#alert-1) đã ghi bước so sánh TTFT với latency và mở span retrieval.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** scrub PII ở tầng logging processor (đệ quy mọi field, đặt sau `format_exc_info`, trước writer) thay vì chỉ dựa vào `summarize_text` ở từng chỗ gọi log. Starter đã có 0 leak nhờ preview, nhưng bất kỳ field mới nào (ví dụ `payload.detail` của exception) sẽ lọt; đặt ở processor thì mọi log đều được bảo vệ mặc định.
- **Một lỗi/blocker đã gặp:** sau khi sửa CP1, validator vẫn báo lỗi vì đọc cả log baseline cũ; ngoài ra preview 80 ký tự làm cắt mất phần sau của message nên evidence PII ban đầu không thấy số thẻ.
- **Cách tìm nguyên nhân và xử lý:** ghi lại kết quả baseline (xem cột Baseline ở mục 3), chuyển log cũ ra khỏi `data/logs.jsonl`, khởi động lại API rồi đo lại; với evidence PII thì gửi 2 request ngắn (email+điện thoại, CCCD+thẻ) và thêm `grep -c` trên toàn file log.
- **Cách hiểu luồng Metrics → Logs → Traces:** metrics (dashboard) cho biết triệu chứng và khoảng thời gian (ví dụ P95 tăng từ 153 ms lên 2653 ms trong khi TTFT vẫn 50 ms); logs lọc trong khoảng đó để lấy một `correlation_id` cụ thể; trace cùng `correlation_id` cho biết span nào chiếm thời gian/lỗi (`retrieval` hay `llm-generation`). Chỉ kết luận root cause khi cả ba cùng chỉ về một bước.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** prompt là "config" ảnh hưởng trực tiếp latency, token và cost; gắn `prompt_version` vào trace giúp biết regression bắt đầu từ version nào, và rollback chỉ là chuyển label `production` mà không cần deploy code. SLO/error budget quyết định khi nào phải dừng thay đổi để ưu tiên ổn định.
- **Điều quan trọng nhất đã học:** Hiểu được tầm quan trọng của việc kết hợp cả 3 cột trụ Observability (Metrics, Logs, Traces) trong vận hành hệ thống LLM. Metrics giúp phát hiện triệu chứng bất thường, Logs giúp khoanh vùng request cụ thể qua correlation_id, và Traces giúp tìm ra chính xác bước gây lỗi hoặc chậm (như bước retrieval) mà không cần phỏng đoán. Đồng thời, biết cách quản lý prompt versioning để dễ dàng rollback khi có sự cố.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** endpoint `/chat` là `async` nhưng agent chạy đồng bộ nên với concurrency 5 request bị xếp hàng: client thấy ~13 s trong practice `rag_slow` trong khi `latency_ms` phía server chỉ ~2.65 s. Dashboard dựa trên `latency_ms` server nên chưa phản ánh thời gian chờ hàng đợi. Quality score vẫn là heuristic đơn giản.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA cuối.
- [x] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [x] Có đúng 3 file text và 5 ảnh runtime theo hướng dẫn.
- [x] Incident evidence nối đúng metric → log → trace.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README.
- [x] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [x] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
