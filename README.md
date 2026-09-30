# K4-L3B — Lab Day 13: Monitoring & LLMOps

> - **Loại repository:** đề bài/starter dành riêng cho lớp K4-L3B
> - **Hình thức làm bài:** cá nhân
> - **Thời gian trên lớp:** 9:00–13:00 (240 phút)
> - **Deadline mặc định:** 23:59:59 trong ngày học, múi giờ Asia/Ho_Chi_Minh

Bạn sẽ biến một AI API “hộp đen” thành hệ thống có thể trả lời ba câu hỏi: **hệ thống có vấn đề gì, request nào bị ảnh hưởng và bước nào là nguyên nhân**. Quy trình điều tra đúng theo slide là **Metrics → Logs → Traces**:

1. Metrics cho biết triệu chứng và khoảng thời gian.
2. Logs giúp tìm request cụ thể qua `correlation_id`.
3. Trace của request đó cho biết span nào chậm hoặc lỗi.

Repo dùng fake LLM nên không cần API key mô hình trả phí. Mỗi học viên tự tạo một project Langfuse riêng để quan sát trace và quản lý prompt version; không dùng project/key dùng chung.

## Kết quả cần đạt

Sau lab, bạn có thể:

- tạo structured log dạng JSON, truyền correlation ID và che PII trước khi ghi log;
- đo latency P50/P95/P99, TTFT, traffic, error, token, cost, retrieval success và quality proxy;
- tạo ít nhất 10 traces trên Langfuse, có span tree đọc được và metadata không chứa PII;
- liên kết trace với prompt name/label/version và chứng minh được một lần rollback;
- dựng dashboard 6 panel, định nghĩa một SLO cùng error budget và ba alert có runbook;
- viết incident note có chuỗi bằng chứng metric → log → trace.

## Sản phẩm phải nộp

- Source đã hoàn thiện các `TODO` bắt buộc.
- `submission/REPORT.md` đã điền và evidence đặt trong `submission/evidence/`.
- Ba output text cho tests, log validator và dashboard validator trên commit cuối.
- Đúng 5 ảnh runtime theo `docs/SUBMISSION.md`; các ảnh được tái sử dụng để chứng minh logging, tracing, prompt, dashboard và incident.
- Một SLO/error budget, ba alert symptom-based có `duration`, kênh Slack và runbook.

## Đọc nhanh để hiểu bài lab

Bài lab không chỉ yêu cầu "thêm log" hay "chụp trace". Mục tiêu chính là tập cách vận hành một ứng dụng LLM khi production có vấn đề. Khi có sự cố, bạn cần đi theo chuỗi bằng chứng:

```text
Metrics -> Logs -> Traces -> Root cause
```

- **Metrics** cho biết hệ thống có triệu chứng gì và xấu từ khoảng thời gian nào.
- **Logs** giúp chọn ra một request cụ thể bị ảnh hưởng bằng `correlation_id`.
- **Traces** cho biết request đó chậm hoặc lỗi ở bước nào, ví dụ retrieval hay LLM generation.
- **Root cause** là kết luận cuối cùng dựa trên bằng chứng, không phải đoán.

Một số thuật ngữ sẽ xuất hiện nhiều trong bài:

| Thuật ngữ | Dùng để trả lời câu hỏi nào? |
|---|---|
| `correlation_id` | Request nào trong log tương ứng với trace nào? |
| Structured log | Request đã xảy ra chuyện gì, có latency/error/token/cost bao nhiêu? |
| Trace/span | Trong một request, bước nào chạy lâu hoặc bị lỗi? |
| PII scrubbing | Log/trace có vô tình lưu email, số điện thoại, CCCD hoặc dữ liệu nhạy cảm không? |
| P50/P95/P99 | Đa số request có nhanh không, nhóm request chậm nhất tệ đến mức nào? |
| TTFT | Người dùng phải chờ bao lâu trước khi LLM bắt đầu trả lời? |
| Retrieval success | RAG có tìm được context phù hợp hay đang thất bại? |
| Quality proxy | Câu trả lời có dấu hiệu giảm chất lượng không, dù chưa chấm thủ công? |
| SLO/error budget | Mức chất lượng nào được xem là đạt, và hệ thống được phép lỗi bao nhiêu? |
| Alert/runbook | Khi metric vượt ngưỡng xấu thì ai cần xử lý và xử lý theo các bước nào? |

## Bắt đầu nhanh

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

Tự đăng ký/đăng nhập [Langfuse Cloud](https://cloud.langfuse.com), tạo project riêng tên `day13-k4-l3b-<MSSV>`, rồi vào **Project Settings → API Keys** để tạo key pair. Điền key của chính project đó vào `.env`:

```dotenv
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_PROMPT_NAME=day13-chat
LANGFUSE_PROMPT_LABEL=production
```

#### Hiểu nhanh về prompt versioning

Trong ứng dụng LLM, prompt không chỉ là một đoạn text phụ trợ. Prompt ảnh hưởng trực tiếp đến chất lượng câu trả lời, latency, token và cost, nên prompt cần được quản lý theo phiên bản giống như code hoặc config.

Trong lab này, prompt được quản lý trên Langfuse bằng ba khái niệm:

- **Prompt name**: tên prompt, ví dụ `day13-chat`.
- **Prompt version**: phiên bản cụ thể của prompt, ví dụ `v1`, `v2`.
- **Prompt label**: nhãn trỏ tới version đang được dùng, ví dụ `production`.

Ví dụ ban đầu:

```text
production -> day13-chat v1
```

Nghĩa là API đang dùng prompt `day13-chat` version 1 cho luồng production. Khi tạo prompt mới, bạn có thể promote label `production` sang version 2:

```text
production -> day13-chat v2
```

Nếu version 2 làm hệ thống xấu đi, ví dụ latency tăng, token/cost tăng hoặc quality giảm, bạn rollback bằng cách chuyển label `production` quay lại version 1:

```text
production -> day13-chat v1
```

Mỗi trace trên Langfuse cần ghi lại `prompt_name`, `prompt_label` và `prompt_version`. Nhờ vậy, khi điều tra incident, bạn biết request đó đã dùng prompt version nào và có bằng chứng để kết luận prompt mới có gây regression hay không.

Trong phần nộp bài, bạn cần có evidence cho prompt `day13-chat` có ít nhất hai version, trace của request dùng từng version và bằng chứng rollback `production` từ version mới về version cũ.

Không chia sẻ key và không chụp màn hình trang hiển thị secret. Xem các bước chi tiết tại [docs/SETUP.md](docs/SETUP.md).

> **Phân biệt evidence:** structured logs nằm ở terminal/`data/logs.jsonl`; Langfuse hiển thị traces/observations và prompt versions. Học viên phải tự chạy workload, tự tạo cả log lẫn trace rồi chụp evidence của mình.

Chạy API ở terminal thứ nhất:

```bash
uvicorn app.main:app --reload --env-file .env
```

Chạy baseline ở terminal thứ hai:

```bash
python scripts/load_test.py
python scripts/validate_logs.py
python scripts/validate_dashboard.py
python -m pytest -q
```

Baseline log chưa đạt là bình thường vì các `TODO` của CP1 chưa được làm. Ghi lại kết quả baseline vào `submission/REPORT.md` trước khi sửa.

## Lộ trình 9:00–13:00 (240 phút)

| Mốc | Thời gian | Việc chính | Hoàn thành khi |
|---|---:|---|---|
| CP0 | 9:00–9:30 (0–30 phút) | Setup, chạy API và baseline | `/health` trả `ok: true`, log được tạo |
| CP1 | 9:30–10:20 (30–80 phút) | Correlation ID, structured log, PII | `validate_logs.py` đạt ít nhất 80/100 |
| CP2 | 10:20–11:40 (80–160 phút) | Trace, prompt, dashboard, SLO/alert | có span tree; dashboard validator đạt 6/6 |
| CP3 | 11:40–12:30 (160–210 phút) | Điều tra challenge K4-L3B | có metric, log và trace cùng một request |
| CP4 | 12:30–13:00 (210–240 phút) | Report, evidence và kiểm tra cuối | tests/validators chạy xong trên commit nộp |

Chi tiết từng checkpoint nằm trong [docs/CHECKPOINTS.md](docs/CHECKPOINTS.md).

## Các phần cần làm

### CP1 — Logging và PII

Mục tiêu CP1 là làm cho mỗi request có một mã theo dõi duy nhất và log an toàn. Mã này phải đi cùng request từ lúc nhận vào, ghi log, tạo trace, đến lúc trả response. Nhờ vậy, khi một request chậm hoặc lỗi, bạn có thể tìm lại đúng request đó mà không cần log dữ liệu nhạy cảm của người dùng.

- `app/middleware.py`: xóa context cũ; nhận `x-request-id` hoặc sinh `req-<8-hex>`; bind ID; trả ID và response time trong header.
- `app/main.py`: bind `user_id_hash`, `session_id`, `feature`, `model`, `env` trước log `request_received`.
- `app/logging_config.py`: chạy PII scrubber trước bước ghi file/render JSON.
- `app/pii.py`: hoàn thiện pattern và tests cho email, điện thoại Việt Nam, CCCD và thẻ thanh toán.

`validate_logs.py` đọc toàn bộ `data/logs.jsonl`. Sau khi lưu baseline, hãy xóa hoặc đổi tên log cũ, khởi động lại API rồi đo lại để không bị tính các dòng chưa scrub.

### CP2 — Tracing, prompt và dashboard

Starter dùng Langfuse Python SDK v4 và mới tạo root observation cho `LabAgent.run`. Bạn cần thêm child observation cho:

- retrieval: loại `retriever` hoặc `span`;
- LLM call: loại `generation`, có model, prompt, `input_tokens`, `output_tokens` và cost.

Về mặt ý tưởng, child observation chỉ là cách đánh dấu từng bước nhỏ trong một request để Langfuse đo thời gian và trạng thái riêng cho từng bước.

Một trace tốt nên đọc được như cây sau:

```text
day13-agent-request
└── lab-agent-run
    ├── retrieval: tìm tài liệu/context liên quan
    └── generation: gọi LLM để sinh câu trả lời
```

Không capture raw prompt/output chứa PII vì người dùng có thể nhập email, số điện thoại, CCCD hoặc nội dung nhạy cảm. Chỉ lưu preview đã scrub và metadata an toàn. Correlation ID phải xuất hiện trong trace metadata để nối trace với log.

Dashboard dùng `data/logs.jsonl` làm nguồn chuẩn và giữ đúng 6 panel trong `config/dashboard.yaml`. Panel latency phải có P50/P95/P99 và TTFT; panel errors phải thể hiện cả retrieval success. Sau đó hoàn thiện:

- `config/slo.yaml`: giải thích hoặc điều chỉnh SLO, tính error budget;
- `config/alert_rules.yaml`: ba alert symptom-based, có duration, severity, owner, Slack channel và runbook;
- `docs/alerts.md`: cách kiểm tra và mitigation cho từng alert.

Mỗi panel trên dashboard nên trả lời một câu hỏi vận hành rõ ràng:

| Panel | Câu hỏi cần trả lời |
|---|---|
| Latency | Request có chậm không? P50/P95/P99 và TTFT đang ở mức nào? |
| Traffic | Hệ thống đang nhận bao nhiêu request theo thời gian? |
| Errors | Error rate có tăng không, retrieval có đang fail không? |
| Cost | Chi phí có tăng bất thường không? |
| Tokens | Input/output token có dài bất thường không? |
| Quality | Quality proxy có giảm dưới mức chấp nhận được không? |

SLO là mục tiêu chất lượng, ví dụ `99.5% request thành công và latency <= 3000ms`. Error budget là phần được phép không đạt SLO, ví dụ SLO 99.5% nghĩa là error budget 0.5%. Alert nên dựa trên triệu chứng quan sát được, ví dụ latency P95 cao, error rate tăng hoặc retrieval success giảm. Runbook là hướng dẫn người trực cần kiểm tra dashboard, lọc log, mở trace và mitigation như thế nào.

### CP3 — Challenge chính thức

Chỉ chạy khi Lab Coach thông báo mở challenge của K4-L3B. Challenge đã được release trong bản mới nhất của starter. Nếu đã fork trước CP3, chọn **Sync fork → Update branch** trên GitHub rồi chạy `git pull --ff-only`; xác nhận có `config/challenge.json` trước khi chạy:

```bash
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5
```

Điều tra theo thứ tự:

1. Xem dashboard để xác định metric xấu và khoảng thời gian.
2. Lọc `data/logs.jsonl`, lấy một `correlation_id` của request bất thường.
3. Tìm trace có cùng `correlation_id`, rồi so sánh các span.
4. Ghi root cause, fix action và preventive measure vào `submission/REPORT.md`.

Không bắt đầu bằng cách đoán root cause hoặc mở trace ngẫu nhiên. Luôn dùng metrics để khoanh vùng triệu chứng trước, dùng logs để chọn request cụ thể, rồi mới dùng trace để tìm bước gây lỗi hoặc chậm.

Không tự tạo, sửa hoặc lấy `config/challenge.json` từ lớp khác. Nếu chưa có file, sync/pull starter mới nhất; không tự đoán nội dung challenge.

## Kiểm tra trước khi nộp

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
git log -1 --oneline
```

- [ ] Không có `.env`, secret, `.venv/`, PII thô hoặc evidence của học viên/lớp khác.
- [ ] Có đúng 3 output text và 5 ảnh runtime theo `docs/SUBMISSION.md`.
- [ ] `submission/REPORT.md` đã đủ; mọi ảnh dùng đường dẫn tương đối và mở được.
- [ ] Bạn demo và giải thích được luồng Metrics → Logs → Traces → Root cause.

## Tên repo bài nộp

Repo này là **repo đề bài**, nên tên chính thức là `K4-L3B-Day13-Monitoring-LLMOps` (mẫu `K4-L3B-TenBai`). Repo bài nộp cá nhân dùng mẫu:

```text
K4-L3-DAY13-HoVaTen-MSSV-Monitoring-LLMOps
```

Ví dụ: `K4-L3-DAY13-NguyenVanAn-123456-Monitoring-LLMOps`. Mỗi học viên nộp URL repo cá nhân và commit SHA cuối trên VLearn LMS/Codelabs. Xem đầy đủ tại [docs/SUBMISSION.md](docs/SUBMISSION.md).

Không push bài làm trực tiếp lên repo đề bài và không dùng chung repo bài nộp với học viên khác.

## Tài liệu trong repo

- [SETUP.md](docs/SETUP.md): cài đặt và xử lý lỗi môi trường.
- [CHECKPOINTS.md](docs/CHECKPOINTS.md): đầu ra và cách tự kiểm tra từng mốc.
- [GUIDE.md](docs/GUIDE.md): gợi ý kỹ thuật khi bị kẹt.
- [PROMPT_VERSIONING.md](docs/PROMPT_VERSIONING.md): prompt v1/v2, label và rollback.
- [DASHBOARD_SETUP.md](docs/DASHBOARD_SETUP.md): mapping dữ liệu cho 6 panel.
- [RUBRIC.md](docs/RUBRIC.md), [RULES.md](docs/RULES.md), [SUBMISSION.md](docs/SUBMISSION.md): cách chấm, quy định và cách nộp.
- [grading-evidence.md](docs/grading-evidence.md): checklist nhanh các ảnh/output cần thu thập.
- [REPORT.md](submission/REPORT.md): báo cáo cá nhân duy nhất cần hoàn thiện.
