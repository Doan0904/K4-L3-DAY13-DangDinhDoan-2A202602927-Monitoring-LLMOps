# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert mẫu để tham khảo

Ví dụ dưới đây minh họa mức độ cụ thể cần có. Học viên không cần copy nguyên, nhưng ba alert trong bài nộp nên rõ ràng tương tự: điều kiện là gì, kéo dài bao lâu, ảnh hưởng tới user ra sao và người trực cần kiểm tra gì trước.

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 3000ms` trong 5 phút
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn trước khi nhận câu trả lời
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard latency để xác nhận P95/P99 và khoảng thời gian tăng.
  2. Lọc `data/logs.jsonl` trong khoảng đó, lấy một `correlation_id` có `latency_ms` cao.
  3. Mở trace cùng `correlation_id` trên Langfuse, so sánh các span chính để xác định bước nào bất thường.
- Mitigation tạm thời: dựa trên evidence thực tế để rollback prompt, khôi phục cấu hình liên quan, tắt practice scenario hoặc giảm tải khi demo.
- Owner: `student-<MSSV>`

## Alert 1

- Tên: `HighLatencyP95`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: latency P95 của `response_sent.latency_ms`; SLO `fast_successful_requests` (99.5% request thành công và ≤ 3000ms / 28 ngày, xem [`config/slo.yaml`](../config/slo.yaml)).
- Điều kiện và thời gian duy trì: `p95(latency_ms) > 1500ms` liên tục trong 5 phút. Baseline P95 ≈ 153ms nên 1500ms (~10× baseline) là regression rõ ràng; đặt thấp hơn SLO line 3000ms để cảnh báo trước khi đốt error budget (practice `rag_slow` cho P95 ≈ 2650ms, vẫn dưới 3000ms).
- Ảnh hưởng tới người dùng: người dùng phải chờ lâu hơn nhiều trước khi nhận câu trả lời; với concurrency cao, request xếp hàng nên thời gian chờ phía client còn lớn hơn `latency_ms`.
- Ba bước kiểm tra đầu tiên:
  1. Mở dashboard (`python scripts/dashboard.py --serve`), panel **Latency percentiles and TTFT**: xác nhận P95/P99 và khoảng thời gian tăng. So sánh với TTFT P95: nếu TTFT vẫn ~50ms mà latency tăng, bước chậm nằm ngoài phần sinh token đầu tiên (thường là retrieval).
  2. Lọc log trong khoảng đó: `python scripts/query_logs.py --event response_sent --min-latency 1500 --since <ts> --fields ts,correlation_id,latency_ms,ttft_ms,feature`, chọn một `correlation_id`.
  3. Mở Langfuse project `day13-k4-l3b-2A202602927` → Traces, filter metadata `correlation_id = <id>`; so sánh duration của span `retrieval` và `llm-generation` trong waterfall.
- Mitigation tạm thời: nếu span `retrieval` chậm → tắt/khôi phục cấu hình retrieval (practice: `python scripts/inject_incident.py --scenario rag_slow --disable`), bật cache hoặc giảm top-k; nếu `llm-generation` chậm sau khi đổi prompt → rollback label `production` về version trước; khi demo có thể giảm concurrency.
- Owner: `student-2A202602927`

## Alert 2

- Tên: `HighErrorRateOrRetrievalFailure`
- Severity: `critical`
- Duration: `3m`
- Kênh thông báo: Slack `#k4-l3b-oncall`
- SLI/SLO liên quan: error rate = `count(request_failed) / count(request_received)`; retrieval success = `tool_success == true` trên các event có `tool_name == "retrieval"`. Mỗi request lỗi tiêu trực tiếp error budget 0.5% của SLO; guardrail `error_rate_pct_max: 2` và `retrieval_success_rate_pct_min: 90`.
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` **hoặc** `retrieval success < 90%` liên tục 3 phút. Duration ngắn hơn alert latency vì lỗi 500 ảnh hưởng người dùng ngay và burn rate rất cao (19.6% lỗi ≈ 39× tốc độ đốt budget cho phép).
- Ảnh hưởng tới người dùng: nhận HTTP 500 (`{"detail": ..., "correlation_id": ...}`) hoặc câu trả lời không có context tài liệu.
- Ba bước kiểm tra đầu tiên:
  1. Dashboard panel **Error rate and retrieval success**: xem error rate %, breakdown theo `error_type` và retrieval success %, xác định thời điểm bắt đầu.
  2. `python scripts/query_logs.py --event request_failed --since <ts>`: đọc `error_type`, `tool_name`, `tool_success`, `payload.detail` (đã scrub PII) và lấy `correlation_id`.
  3. Mở trace cùng `correlation_id` trên Langfuse: observation nào có level `ERROR` (span `retrieval` → lỗi vector store; `llm-generation` → lỗi model/provider).
- Mitigation tạm thời: nếu lỗi ở retrieval → failover/khôi phục vector store (practice: `python scripts/inject_incident.py --scenario tool_fail --disable`), tạm trả lời fallback "không tìm thấy tài liệu" thay vì 500; nếu lỗi bắt đầu ngay sau deploy/đổi prompt → rollback.
- Owner: `student-2A202602927`

## Alert 3

- Tên: `CostPerRequestSpike`
- Severity: `warning`
- Duration: `10m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: `avg(response_sent.cost_usd)` và `avg(response_sent.tokens_out)`; guardrail `daily_cost_usd_max: 2.5` trong [`config/slo.yaml`](../config/slo.yaml).
- Điều kiện và thời gian duy trì: chi phí trung bình mỗi request `> 0.005 USD` (baseline ≈ 0.0023) **hoặc** `tokens_out` trung bình `> 300` (baseline ≈ 145) liên tục 10 phút. Đo theo request nên không bị kích hoạt chỉ vì traffic tăng.
- Ảnh hưởng tới người dùng: câu trả lời dài bất thường/chậm hơn; về vận hành có nguy cơ vượt budget ngày.
- Ba bước kiểm tra đầu tiên:
  1. Dashboard panel **Cost over time** và **Input and output tokens**: cost tăng trong khi panel **Request traffic** không tăng → chi phí mỗi request tăng; xem `tokens_out` hay `tokens_in` tăng.
  2. `python scripts/query_logs.py --event response_sent --min-tokens-out 300 --since <ts> --fields ts,correlation_id,tokens_in,tokens_out,cost_usd`: lấy `correlation_id`.
  3. Mở trace cùng `correlation_id`: xem generation `llm-generation` (usage/cost, model) và metadata `prompt_version`/`prompt_label` của root observation để biết có đổi prompt/model không.
- Mitigation tạm thời: rollback label `production` về prompt version cũ nếu spike trùng thời điểm promote; đặt `max_tokens` cho output; chuyển model rẻ hơn cho feature không quan trọng; practice: `python scripts/inject_incident.py --scenario cost_spike --disable`.
- Owner: `student-2A202602927`
