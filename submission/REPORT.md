# Báo cáo cá nhân — K4-L3B Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:** Vũ Hải Minh
- **MSSV:** 2A202602452
- **Lớp:** K4-L3B
- **Repository URL:** https://github.com/dtc-z/K4-L3-DAY13-VuHaiMinh-2A202602452-Monitoring-LLMOps
- **Commit SHA cuối (nội dung và evidence):** `ca746b704c13e923f70c5cf1f82d4fbc5689c99b`
- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1`
- **Tên project Langfuse cá nhân:** `day13-k4-l3b-2A202602452`

## 2. Evidence index

Bảng này trỏ tới ảnh và output kiểm tra trong `submission/evidence/`; tên evidence gốc bạn đã chụp được giữ nguyên.

| Evidence | Đường dẫn |
|---|---|
| Terminal CP2 ban đầu: pytest, validators, load test | `evidence/03-dashboard-validator-CP2.png` |
| CP4 pytest final: 25 passed | `evidence/01-pytest-final.txt` |
| CP4 log validator sau challenge: 100/100 | `evidence/02-log-validator-final.txt` |
| CP4 dashboard validator: 6/6 | `evidence/03-dashboard-validator-final.txt` |
| Log validator CP0 | `evidence/02-log-validator-CP0.png` |
| Log validator CP1 | `evidence/02-log-validator-CP1.png` |
| Log validator CP2 sau workload | `evidence/02-log-validator-CP2.txt` |
| Dashboard validator CP0 | `evidence/03-dashboard-validator-CP0.png` |
| Dashboard validator CP2 | `evidence/03-dashboard-validator-CP2.png` |
| Structured log CP0 | `evidence/04-structured-log-CP0.png` |
| Structured log CP1 | `evidence/04-structured-log-CP1.png` |
| PII redaction CP1 | `evidence/05-pii-redaction-CP1.png` |
| Langfuse trace list | `evidence/06-trace-list.png` |
| Langfuse trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08a-trace-metadata.png` |
| Generation details | `evidence/08b-generation-details.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt label state after promote (original file kept) | `evidence/10-prompt-rollback.png` |
| Prompt rollback live verification | `evidence/10b-prompt-rollback-live-check.txt` |
| Dashboard runtime viewport (original file kept) | `evidence/11-dashboard-overview.png` |
| Dashboard runtime with all six panels | `evidence/11b-dashboard-overview-full.png` |
| CP3 incident metric dashboard | `evidence/12-incident-metric.png` |
| CP3 incident metric readback | `evidence/12-incident-metric.txt` |
| CP3 correlated incident log screenshot | `evidence/13-incident-log.png` |
| CP3 correlated incident log readback | `evidence/13-incident-log.txt` |
| CP3 Langfuse incident trace | `evidence/14-incident-trace.png` |
| CP3 Langfuse observation API readback | `evidence/14-incident-trace.txt` |
| CP3 incident metric comparison (sanitized log-derived readback) | `evidence/12-incident-metric.txt` |
| CP3 correlated incident log record | `evidence/13-incident-log.txt` |
| CP3 Langfuse observation API readback | `evidence/14-incident-trace.txt` |

Ảnh CP3 12–14 và các bản readback text tương ứng đều có trong evidence folder. Readback text ghi rõ các giá trị có thể khó đọc trong ảnh; không chứa prompt challenge.

## 3. Kết quả kỹ thuật

| Nội dung | Baseline / CP0 | CP1 | CP2 hiện tại | Nhận xét |
|---|---|---|---|---|
| `validate_logs.py` | 30/100 | 100/100 trên 26 records | 100/100 trên 36 records (CP2) | CP2: 15 ID, thiếu trường/enrichment: 0, PII leak: 0. CP4 kiểm tra lại sau challenge: 100/100 trên 59 records, 31 ID, không thiếu trường/enrichment và 0 PII leak (`evidence/02-log-validator-final.txt`). Ảnh CP2 cũ được giữ nguyên. |
| `validate_dashboard.py` | 6/6 | 6/6 | 6/6 | CP4 kiểm tra lại: 6/6 (`evidence/03-dashboard-validator-final.txt`); ảnh CP2 được giữ nguyên. |
| `pytest` | 22 passed | 25 passed | 25 passed | Kiểm tra CP4: 25 passed (`evidence/01-pytest-final.txt`). |
| Traces Langfuse | — | — | 15 trace có đủ cây `lab-agent-run`/`retrieval`/`generation` | Query Langfuse hiện tại trả 75 observations. Trace list ảnh được chụp trước request kiểm chứng mới nên hiển thị khoảng 72 observations. |
| PII leak | — | 0 trên 26 records CP1 | 0 trên 36 records CP2 | CP4 validator kiểm tra 59 records, 31 ID: 0 leak (`evidence/02-log-validator-final.txt`). |
| Latency P50 / P95 / P99; TTFT P95 | — | P95 / TTFT P95: 1396 / 50 ms trên 10 response | 151 / 1638 / 1638 ms; TTFT P95 50 ms trên 15 request | Đọc từ dashboard runtime trong cửa sổ 60 phút; mẫu CP1 và CP2 có số request khác nhau. |
| Error rate / retrieval success | — | Retrieval: 100% (10/10) | Error rate: 0.0%; retrieval success: 100.0% (15/15) | Retrieval success tính trên mọi event có `tool_success`. |
| Traffic / cost | — | — | 15 requests; cost cửa sổ $0.0301 | Dashboard hiển thị average rate 0.25 request/phút. |
| Tokens / quality | — | — | Input 473; output 1,912; quality mean 0.89 | Các metric từ dashboard runtime đầy đủ. |

Các kết quả CP2 được giữ tách biệt với CP3 challenge. Kiểm tra cuối CP4 sau workload challenge: 25 tests passed, log validator 100/100 trên 59 records và dashboard validator 6/6; output nằm trong evidence index.

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:** Middleware xóa contextvars cũ, nhận và trim `x-request-id`; nếu header vắng hoặc rỗng thì tạo `req-` kèm 8 ký tự hex. Middleware bind ID vào structlog contextvars, lưu tại `request.state.correlation_id` để truyền vào agent/trace, rồi trả `x-request-id` và `x-response-time-ms` trong response header.
- **Các metadata được ghi vào structured log:** `correlation_id`, `user_id_hash` (12 ký tự đầu của SHA-256 từ user ID), `session_id`, `feature`, `model` và `env` (`APP_ENV`, mặc định `dev`). User ID thô không được bind vào log. Evidence: `evidence/04-structured-log-CP1.png`.
- **Cách bảo đảm PII được scrub trước khi ghi:** `summarize_text` scrub preview; `scrub_event` đệ quy qua các chuỗi trong trường log và cấu trúc dict/list/tuple để thay email, số điện thoại Việt Nam, CCCD và thẻ thanh toán bằng placeholder. Processor chạy sau khi định dạng exception/stack và trước file JSONL cùng JSON renderer, nên các trường ngoài `payload` cũng được xử lý. Evidence: `evidence/05-pii-redaction-CP1.png`.
- **Cách kiểm chứng kết quả:** `validate_logs.py` đạt 100/100 trên 26 records, không thiếu trường hoặc enrichment, có 10 correlation ID và 0 PII leak (`evidence/02-log-validator-CP1.png`). Đối chiếu thêm structured log và request có PII đã che trong `evidence/04-structured-log-CP1.png` và `evidence/05-pii-redaction-CP1.png`. Ảnh terminal CP2 ban đầu ghi 80/100 trên 1 record trước load test. Lần kiểm tra sau workload đạt 100/100 trên 36 records, 15 correlation ID và 0 PII leak (`evidence/02-log-validator-CP2.txt`); ảnh cũ được giữ nguyên.

## 5. Tracing và prompt versioning

- **Project và traces:** Project Langfuse cá nhân là `day13-k4-l3b-2A202602452`. Trace name là `day13-agent-request`. Query CP2 trả 75 observations và 15 trace có đủ `lab-agent-run`, `retrieval`, `generation`; ảnh trace list được chụp trước request kiểm chứng cuối, khi có khoảng 72 observations. Ảnh challenge CP3 và trace cụ thể được dẫn ở mục 7. Evidence CP2: `evidence/06-trace-list.png`.
- **Cấu trúc trace:** Waterfall cho thấy `lab-agent-run` là root, với child `retrieval` và `generation`. Generation hiển thị model `claude-sonnet-4-5`, prompt `day13-chat - v1`, 129 tokens và cost `$0.001611`; input/output hiển thị null/undefined. Evidence: `evidence/07-trace-waterfall.png` và `evidence/08b-generation-details.png`.
- **Nối trace với log:** Metadata có correlation ID, `feature`, model và prompt metadata. `req-c2e00001` nối với trace v1 `ee940876cdb2a1f4e63d56b516891342`; `req-c2d00001` nối với trace v2 `41b3901f092f17234233d6e10ee8bff4`. Sau rollback, `req-d0b90001` nối với trace `d80e5b4cc2e43f1b833a22ca09f05490` dùng production v1. Evidence metadata: `evidence/08a-trace-metadata.png`; xác nhận rollback mới: `evidence/10b-prompt-rollback-live-check.txt`.
- **Prompt name:** `day13-chat` (text prompt với ba biến `feature`, `docs`, `message`).
- **Version/label baseline:** v1 có `baseline` và `production`.
- **Version/label candidate:** v2 có `candidate` và `latest`; metadata của trace `req-c2d00001` xác nhận v2/production trước rollback.
- **Trace ID theo version:** v1: `ee940876cdb2a1f4e63d56b516891342`; v2: `41b3901f092f17234233d6e10ee8bff4`. Trace kiểm chứng sau rollback, v1: `d80e5b4cc2e43f1b833a22ca09f05490`.
- **Promote/rollback:** `evidence/09-prompt-versions.png` cho thấy v1=`production`/`baseline`, v2=`candidate`/`latest`; `evidence/10-prompt-rollback.png` được giữ nguyên và cho thấy trạng thái sau promote với v2=`production`. Sau đó production đã được rollback qua Langfuse về v1, labels `baseline`/`production`, rồi gửi request thành công; trace mới xác nhận `prompt_source=langfuse`, `prompt_label=production`, `prompt_version=1`. Readback nằm trong `evidence/10b-prompt-rollback-live-check.txt`. Ảnh UI sau rollback chưa có trong evidence folder.

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:** Dashboard local đọc `data/logs.jsonl`, time range 60 phút, refresh 30 giây, timestamp UTC. Contract `config/dashboard.yaml` định nghĩa Latency percentiles and TTFT (ms), Request traffic (requests/min), Error rate and retrieval success (%), Cost over time (USD), Input and output tokens, Quality proxy (score 0–1). Ảnh `evidence/11b-dashboard-overview-full.png` hiển thị đủ cả sáu panel, dữ liệu 36 records/15 requests, P50/P95/P99 = 151/1638/1638 ms, TTFT P95 50 ms, error rate 0.0%, retrieval success 100.0%, cost `$0.0301`, input/output tokens 473/1,912, quality mean 0.89 và thresholds. Ảnh `evidence/11-dashboard-overview.png` được giữ nguyên làm ảnh viewport ban đầu. Validator contract đạt 6/6 (`evidence/03-dashboard-validator-CP2.png`).
- **SLO:** `fast_successful_requests` có cửa sổ 28 ngày và target 99.5%. Một request tốt là `response_sent` với `latency_ms <= 3000`; mẫu số là `request_received`.
- **Error budget:** 0.5% request có thể lỗi hoặc vượt ngưỡng latency. Với 10,000 request, budget là tối đa 50 request xấu (`10,000 × 0.5 / 100`).
- **Ba alert và runbook:** Cả ba là symptom-based, owner `student-2A202602452`, Slack channel `#k4-l3b-alerts`; runbook thực hiện kiểm tra Metrics → Logs → Traces và mitigation trong [`docs/alerts.md`](../docs/alerts.md).
  1. `HighLatencyP95` — warning: P95 `response_sent.latency_ms > 3000 ms` trong 5 phút; [runbook Alert 1](../docs/alerts.md#alert-1).
  2. `HighRequestErrorRate` — critical: `request_failed / request_received > 2%` trong 2 phút; [runbook Alert 2](../docs/alerts.md#alert-2).
  3. `LowRetrievalSuccess` — warning: retrieval success dưới 90% trong 5 phút; [runbook Alert 3](../docs/alerts.md#alert-3).

## 7. Điều tra challenge

- **Challenge ID:** `day13-k4-l3b-monitoring-llmops-v1` (K4); incident `rag_slow`.
- **Khoảng thời gian điều tra:** Incident được bật lúc `2026-09-30T05:09:17.189602Z`. Baseline gồm 10 response từ `05:08:58.967614Z` đến `05:09:00.381431Z`; challenge gồm 5 response từ `05:09:32.523665Z` đến `05:09:43.161241Z`.
- **Triệu chứng từ metrics:** Server-side baseline P50/P95 là `151/1374 ms` (n=10). Trong challenge P50/P95 là `2652/2652 ms` (n=5), khoảng `2651–2652 ms`; cả 5 request đều vượt ngưỡng challenge `2000 ms`. Không dùng client elapsed do concurrency queueing. Percentile theo nearest-rank. Evidence: `evidence/12-incident-metric.txt`.
- **Log line và correlation ID liên quan:** `response_sent`, `2026-09-30T05:09:32.523665Z`, `correlation_id=req-5eb636e8`, `session_id=k4-l3b-challenge-s03`, `feature=monitoring`, `latency_ms=2652`, `tool_success=true`. Evidence: `evidence/13-incident-log.txt`.
- **Trace ID và span gây ảnh hưởng:** Trace `76147b7f1916416fe980e1de4a3d0592` có cùng correlation ID. Root `lab-agent-run` mất `2652 ms`; child `retrieval` mất `2501 ms`; `generation` mất `151 ms`. Evidence: `evidence/14-incident-trace.txt` (Langfuse observation API readback).
- **Root cause:** Challenge inject `rag_slow` thêm khoảng 2.5 giây chờ trong retrieval (`app/mock_rag.py::retrieve`). Trace xác nhận thời gian tăng nằm ở retrieval, còn generation bình thường; log ghi retrieval thành công.
- **Fix action:** Tắt incident bằng `python scripts/inject_incident.py --disable`; sau đó `GET /health` xác nhận `rag_slow`, `tool_fail`, `cost_spike` đều `false`.
- **Preventive measure:** Thêm alert cho feature `monitoring` khi P95 vượt `2000 ms` kèm runbook kiểm tra Metrics → Logs → Traces và bước tắt incident. Alert chung `HighLatencyP95` hiện có ngưỡng `3000 ms`, nên có thể bỏ lỡ mức chậm tái hiện trong challenge; ngưỡng feature-specific này là đề xuất, chưa được cấu hình.
- **Evidence:** Ảnh metric, log, trace là `evidence/12-incident-metric.png`, `evidence/13-incident-log.png`, `evidence/14-incident-trace.png`; các file `.txt` cùng số là readback bổ sung đã scrub.

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:** Dùng một `correlation_id` xuyên suốt middleware, structured logs và Langfuse trace để lần theo từng request; scrub PII tập trung trước khi ghi log để không làm rò dữ liệu qua payload hoặc exception.
- **Một lỗi/blocker đã gặp:** Trong `load_test.py --challenge --concurrency 5`, thời gian phía client tăng do request xếp hàng, nên không đại diện latency xử lý của server. Đối chiếu `latency_ms` trong log và duration của trace để đo đúng phần chậm.
- **Cách tìm nguyên nhân và xử lý:** Dashboard cho thấy P95 tăng từ baseline `1374 ms` lên challenge `2652 ms`; chọn log `req-5eb636e8`; trace cùng ID cho thấy retrieval `2501 ms` trong khi generation `151 ms`. Tắt `rag_slow` và xác nhận mọi incident flag false ở `/health`.
- **Cách hiểu luồng Metrics → Logs → Traces:** Metrics phát hiện thời điểm và loại bất thường; `correlation_id` chọn log cụ thể; trace cùng ID phân rã thời gian theo span để xác định retrieval gây chậm.
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:** Gắn prompt version với trace giúp so sánh v1/v2 và rollback production về bản ổn định; token/cost phát hiện hồi quy chi phí; latency, error rate và error budget cho biết mức ảnh hưởng tới SLO.
- **Điều quan trọng nhất đã học:** Dữ liệu chỉ hữu ích khi các tín hiệu quan sát được nối bằng một ID và được so với baseline; thời gian client khi chạy đồng thời có thể gây kết luận sai về server.
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:** `HighLatencyP95` hiện đặt `3000 ms`, cao hơn mức challenge đo được `2652 ms`; đề xuất alert riêng cho feature `monitoring` ở `2000 ms` chưa được cấu hình. Ảnh UI sau rollback prompt chưa có; trạng thái rollback được xác minh bằng `evidence/10b-prompt-rollback-live-check.txt` và trace v1.

## 9. Checklist trước khi nộp

- [x] Kết quả và evidence thuộc commit SHA nêu ở mục thông tin học viên.
- [x] Tất cả ảnh/output trong evidence index mở được bằng đường dẫn tương đối.
- [x] Incident evidence nối đúng metric → log → trace qua `req-5eb636e8`.
- [x] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [x] Repository chạy lại được theo README; pytest 25 passed, validators đạt yêu cầu.
- [x] Không đưa secret, API key, PII thô hoặc evidence của người khác/lớp khác vào submission.
- [x] Sau khi push: nộp URL repo và commit SHA trên LMS/Codelabs.
