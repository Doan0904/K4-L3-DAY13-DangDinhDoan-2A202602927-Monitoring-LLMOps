# Hướng dẫn nộp bài cá nhân Day 13

## 1. Hình thức và tên repository

Đây là **bài lab cá nhân**. Mỗi học viên làm và nộp một repository riêng theo mẫu:

```text
K4-L3-DAY13-HoVaTen-MSSV-Monitoring-LLMOps
```

Ví dụ:

```text
K4-L3-DAY13-NguyenVanAn-123456-Monitoring-LLMOps
```

Tên viết không dấu, không khoảng trắng và ngăn cách bằng dấu `-`. Không dùng tên nhóm và không nộp chung repository với học viên khác.

## 2. Nộp ở đâu và nộp thông tin gì?

Mỗi học viên tự nộp trên VLearn LMS/Codelabs:

1. URL repository cá nhân.
2. Commit SHA cuối dùng để chấm.

Deadline mặc định là 23:59:59 ngày diễn ra lab theo múi giờ Asia/Ho_Chi_Minh. Nếu có thông báo khác, dùng mốc chính thức mới nhất của Lab Coach/Key Coach.

Commit SHA phải tồn tại trên remote và chứa đầy đủ source, config, `submission/REPORT.md` và evidence. Các thay đổi sau deadline không được dùng để chấm nếu không có thông báo gia hạn.

## 3. Cấu trúc bắt buộc

```text
K4-L3-DAY13-HoVaTen-MSSV-Monitoring-LLMOps/
├── app/                         # source đã hoàn thiện
├── config/                      # dashboard, SLO và alert; challenge không nộp cùng evidence
├── data/                        # input mẫu; không commit log chứa PII
├── docs/
│   └── alerts.md                # runbook cho ba alert
├── scripts/                     # load test, incident và validators
├── tests/                       # public tests và test bổ sung
├── submission/
│   ├── REPORT.md                # báo cáo cá nhân duy nhất
│   └── evidence/
│       ├── README.md
│       └── các file evidence
├── README.md
├── requirements.txt
└── .env.example
```

Không tạo `TEAM.md`, group report hoặc báo cáo thành viên riêng. Toàn bộ kết quả và phần giải thích của học viên nằm trong `submission/REPORT.md`.

## 4. Quy tắc chung cho evidence

Evidence phải chứng minh kết quả chạy trên đúng commit SHA được nộp:

- Ảnh phải đọc được tên màn hình/panel, giá trị, time range và ID liên quan.
- Không cắt mất thông tin cần đối chiếu, nhưng phải che secret và PII.
- Dùng dữ liệu test của repo; không dùng dữ liệu thật của người dùng.
- Test và validator lưu dạng `.txt`; không cần chụp màn hình terminal.
- Source, YAML, runbook và commit được dẫn bằng đường dẫn/link; không cần chụp toàn bộ code.
- Mọi đường dẫn trong report phải là đường dẫn tương đối và mở được trên GitHub.
- Không dùng source, report, trace ID hoặc evidence của học viên khác/lớp khác.
- Các ảnh trace/prompt phải lấy từ project Langfuse cá nhân `day13-k4-l3b-<MSSV>`; ảnh nên nhìn thấy tên project nhưng tuyệt đối không mở/chụp trang API Keys.

Chỉ nộp đúng **5 ảnh runtime**. Mỗi ảnh được tái sử dụng cho nhiều tiêu chí để tránh chụp trùng. Không gọi ảnh trace Langfuse là “log”; dùng `correlation_id` để chứng minh log và trace thuộc cùng request.

Từ `submission/REPORT.md`, dẫn ảnh như sau:

```markdown
![Incident trace](evidence/03-incident-trace.png)
```

Không dùng đường dẫn cục bộ như `C:\Users\...` hoặc `/home/student/...`.

## 5. Evidence bắt buộc: 3 file text và 5 ảnh

### 5.1. Ba kết quả lệnh — lưu dạng text

macOS/Linux:

```bash
python -m pytest -q 2>&1 | tee submission/evidence/pytest.txt
python scripts/validate_logs.py 2>&1 | tee submission/evidence/log-validator.txt
python scripts/validate_dashboard.py 2>&1 | tee submission/evidence/dashboard-validator.txt
```

Windows PowerShell:

```powershell
python -m pytest -q 2>&1 | Tee-Object -FilePath submission/evidence/pytest.txt
python scripts/validate_logs.py 2>&1 | Tee-Object -FilePath submission/evidence/log-validator.txt
python scripts/validate_dashboard.py 2>&1 | Tee-Object -FilePath submission/evidence/dashboard-validator.txt
```

### 5.2. Năm ảnh runtime

| Ảnh | Chụp màn hình nào | Một ảnh được dùng để chứng minh |
|---|---|---|
| `01-incident-log.png` | Log của request bất thường trong `data/logs.jsonl` | structured log, metadata và incident log |
| `02-trace-list.png` | Trang Langfuse Traces có ít nhất 10 traces | project cá nhân và số lượng traces |
| `03-incident-trace.png` | Trace cùng `correlation_id` với ảnh 01 | waterfall, metadata và span gây sự cố |
| `04-prompt-versioning.png` | Trace `production` v2 và trang prompt sau rollback đặt cạnh nhau | v1/v2, labels, promote và rollback |
| `05-dashboard-incident.png` | Dashboard cuối sau khi chạy challenge | 6 panel và metric bất thường của incident |

### 5.3. Cách chụp rõ ràng

1. **Ảnh 01 — log:** mở `data/logs.jsonl` bằng VS Code, tìm `correlation_id` của request bất thường và bật Word Wrap bằng `Alt+Z`. Chụp dòng log đọc được `event`, `correlation_id`, model, env, feature và latency/error. PII được kiểm tra bằng `log-validator.txt` và tests, không cần ảnh riêng.
2. **Ảnh 02 — trace list:** mở project Langfuse cá nhân → **Traces**, chọn time range chứa lần chạy mới nhất, thu gọn sidebar. Ảnh phải thấy tên project và ít nhất 10 dòng trace.
3. **Ảnh 03 — incident trace:** tìm đúng `correlation_id` ở ảnh 01, mở trace và expand root/retrieval/generation. Ảnh phải thấy trace ID, span tree, duration/status, correlation ID, prompt version/label, token và cost.
4. **Ảnh 04 — prompt:** làm theo [PROMPT_VERSIONING.md](PROMPT_VERSIONING.md). Đặt trace `production` v2 bên trái và trang versions sau rollback bên phải; chụp toàn màn hình.
5. **Ảnh 05 — dashboard:** chọn time range 60 phút chứa challenge, thu gọn sidebar và zoom 70–80%. Ảnh phải thấy đủ 6 panel, đơn vị, threshold/SLO line và metric bất thường. Nếu trang dài trên Chrome/Edge: nhấn `F12` → `Ctrl + Shift + P` (`Command + Shift + P` trên macOS) → gõ **Capture full size screenshot** → Enter; hoặc export một PNG từ công cụ dashboard.

Windows có thể dùng `Win + Shift + S`; macOS dùng `Command + Shift + 4`. Không ghép, chỉnh sửa hoặc làm sai lệch ảnh.

## 6. Nội dung không cần chụp ảnh

Không cần screenshot các file sau vì giảng viên kiểm tra trực tiếp trên commit:

- `config/slo.yaml`;
- `config/alert_rules.yaml`;
- `docs/alerts.md`;
- source code và tests;
- commit history;
- kết quả pytest/validator vì đã lưu thành `.txt`.

Trong `submission/REPORT.md`, hãy dẫn đúng file, section hoặc commit liên quan.

## 7. Yêu cầu riêng cho incident

Evidence incident chỉ hợp lệ khi ba tín hiệu cùng chỉ về một request hoặc cùng khoảng sự cố:

```text
Metric bất thường
        ↓
Log có correlation_id
        ↓
Trace có cùng correlation_id
        ↓
Span gây ảnh hưởng
        ↓
Root cause và hành động xử lý
```

`REPORT.md` phải ghi challenge ID, khoảng thời gian, metric cụ thể, log line/`correlation_id`, trace ID, span gây ảnh hưởng, root cause, fix action và preventive measure.

`config/challenge.json` được release trong starter K4-L3B tại CP3. Nếu fork cũ chưa có file, Sync fork/pull bản mới nhất. Không sửa, tự tạo, thay thế hoặc lấy file từ lớp khác.

## 8. Nội dung báo cáo cá nhân

Hoàn thiện trực tiếp `submission/REPORT.md`. Báo cáo phải có:

- họ tên, MSSV, lớp, repository URL và commit SHA;
- kết quả baseline và kết quả cuối;
- cách triển khai logging, PII, tracing và prompt version;
- dashboard, SLO, error budget và alerts;
- chuỗi điều tra incident;
- một quyết định kỹ thuật và lý do;
- một lỗi/blocker cùng cách xử lý;
- giải thích luồng Metrics → Logs → Traces;
- vai trò của prompt version, token/cost, SLO hoặc rollback;
- điều học được và hạn chế còn lại;
- đường dẫn tới toàn bộ evidence bắt buộc.

Nội dung phải do chính học viên thực hiện và khớp với source, evidence cùng lịch sử Git của repository cá nhân.

## 9. Không được nộp

- `.env`, Langfuse secret, API key hoặc token.
- PII nguyên văn trong log, trace, screenshot hoặc report.
- `.venv/`, cache, dependency đã cài hoặc file sinh ra không phục vụ chấm.
- Source, report, trace ID hoặc evidence của học viên/lớp khác.
- Trace/prompt lấy từ project dùng chung hoặc project của người khác.
- Evidence giả hoặc ảnh đã chỉnh sửa làm sai lệch kết quả.
- `config/challenge.json` đã bị tự ý sửa, thay thế hoặc lấy từ lớp khác.
- Ảnh dashboard trống hoặc ảnh không đọc được thông tin cần chấm.

## 10. Kiểm tra trước khi push

Chạy trên commit cuối:

```bash
python -m pytest -q
python scripts/validate_logs.py
python scripts/validate_dashboard.py
git status --short
git log -1 --oneline
```

Checklist cuối:

- [ ] Source và TODO bắt buộc đã hoàn thành bằng repository cá nhân.
- [ ] Có `pytest.txt`, `log-validator.txt` và `dashboard-validator.txt`.
- [ ] Có đúng 5 ảnh runtime theo bảng evidence.
- [ ] Có tối thiểu 10 traces tự tạo trong project Langfuse cá nhân, waterfall, metadata và prompt rollback.
- [ ] Ảnh Langfuse nhìn thấy tên project cá nhân nhưng không lộ API key/secret.
- [ ] Dashboard đủ 6 panel; SLO/error budget và 3 alert/runbook đã hoàn thiện.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] `submission/REPORT.md` đã điền đầy đủ.
- [ ] Không có secret, PII thô hoặc nội dung sao chép từ người khác/lớp khác.
- [ ] Tất cả link/ảnh mở được trực tiếp trên GitHub.
- [ ] URL repo cá nhân và commit SHA cuối đã được nộp.
