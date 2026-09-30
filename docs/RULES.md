# Quy định Day 13 Monitoring & LLMOps

## 1 Hình thức và deadline

- Đây là bài làm cá nhân; mỗi học viên dùng một repository riêng.
- Mỗi học viên tự nộp URL repo cá nhân và commit SHA cuối trên VLearn LMS/Codelabs.
- Deadline mặc định là 23:59:59 ngày diễn ra lab, múi giờ Asia/Ho_Chi_Minh.
- Gia hạn chỉ có hiệu lực khi Lab Coach/Key Coach thông báo chính thức.
- Nộp trễ 0–2 giờ: trừ 10%; trễ 2–12 giờ: trừ 25%; quá 12 giờ: 0 điểm, trừ trường hợp được phê duyệt trước deadline.
- Commit hoặc sửa artifact sau deadline không được dùng để chấm, trừ khi có thông báo gia hạn.

## 2 Sử dụng AI

Được dùng AI coding assistant để giải thích thư viện, phân tích lỗi, gợi ý test hoặc review code. Học viên phải hiểu và bảo vệ được mọi thay đổi đã commit. Không copy-paste mù quáng, không dùng AI để tạo evidence giả hoặc bịa số liệu.

## 3 Hợp tác và liêm chính

- Được thảo luận khái niệm với học viên khác nhưng phải tự triển khai bài của mình.
- Không sao chép source, report, dashboard, screenshot, trace ID hoặc evidence.
- Mỗi học viên phải tự tạo project Langfuse và tự sinh trace/prompt evidence; không dùng project hoặc API key dùng chung.
- `submission/REPORT.md` phải do chính học viên viết và khớp source, evidence cùng lịch sử Git.
- Không xóa log lỗi hoặc chỉnh ảnh để che kết quả không đạt.

## 4 Challenge chính thức

- Chỉ chạy challenge sau khi Lab Coach thông báo mở CP3 và release file trên starter K4-L3B.
- Nếu fork được tạo trước thời điểm release, phải Sync fork/pull mới nhất trước khi chạy.
- Không tự tạo, sửa, thay thế hoặc lấy `config/challenge.json` từ học viên/lớp khác.
- Evidence phải ghi challenge ID và khớp query/seed của repo đã nộp.
- Practice scenarios được phép chạy bất kỳ lúc nào.

## 5 Bảo mật và dữ liệu

- Không commit `.env`, Langfuse secret, API key, token hoặc credential.
- Không ghi PII nguyên văn vào source, log, screenshot hoặc report.
- Dùng dữ liệu thử nghiệm do repo cung cấp; không nhập PII thật.
- Nếu phát hiện key đã commit, phải revoke/rotate ngay và báo cho Lab Coach.
- Screenshot Langfuse được phép hiển thị tên project cá nhân nhưng không được hiển thị public/secret key.

## 6 Evidence trung thực

Mọi kết luận incident phải đi theo Metrics → Logs → Traces và dẫn được ít nhất một metric, một log line/correlation ID cùng một trace ID liên quan. Validator pass nhưng thiếu evidence runtime vẫn không được tính đủ điểm.
