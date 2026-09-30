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
- SLI/SLO liên quan: latency của SLO `fast_successful_requests`; good request phải có `latency_ms <= 3000`.
- Điều kiện và thời gian duy trì: P95 của `response_sent.latency_ms` lớn hơn 3000 ms liên tục trong 5 phút.
- Ảnh hưởng tới người dùng: người dùng phải đợi lâu hơn trước khi nhận câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** xác nhận thời điểm P95 vượt 3000 ms, so sánh P50/P95/P99 và TTFT để biết độ trễ ảnh hưởng phần lớn request hay chỉ một nhóm.
  2. **Logs:** lọc `response_sent` trong khoảng thời gian đó với `latency_ms > 3000`, lấy `correlation_id`, `session_id`, `feature` và model; không đưa nội dung thô của request vào incident note.
  3. **Traces:** mở trace Langfuse có cùng `correlation_id`; so sánh thời lượng `retrieval` và `generation` để định vị bước chậm.
- Mitigation tạm thời: nếu generation tăng sau thay đổi prompt, rollback label `production` về version ổn định; nếu retrieval chậm, khôi phục cấu hình retrieval gần nhất hoặc tắt practice incident đang bật. Chạy lại một request và xác nhận P95 giảm.
- Owner: `student-2A202602452`

## Alert 2

- Tên: `HighRequestErrorRate`
- Severity: `critical`
- Duration: `2m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: tỷ lệ request lỗi trong SLO `fast_successful_requests`.
- Điều kiện và thời gian duy trì: `request_failed / request_received > 2%` liên tục trong 2 phút.
- Ảnh hưởng tới người dùng: một phần request không nhận được câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** xác nhận error rate và số request trong cùng cửa sổ; xem alert có đủ lưu lượng để đại diện cho tình trạng hiện tại không.
  2. **Logs:** lọc event `request_failed`, nhóm theo `error_type` và `tool_name`, rồi lấy một `correlation_id` bị ảnh hưởng.
  3. **Traces:** mở trace cùng `correlation_id`; kiểm tra trạng thái và thời lượng các child observation để xem lỗi xuất hiện ở retrieval hay generation.
- Mitigation tạm thời: tắt practice incident gây lỗi nếu đang bật; nếu lỗi bắt đầu sau một thay đổi prompt, rollback `production`; gửi một request kiểm tra sau mitigation và theo dõi error rate trong ít nhất 2 phút.
- Owner: `student-2A202602452`

## Alert 3

- Tên: `LowRetrievalSuccess`
- Severity: `warning`
- Duration: `5m`
- Kênh thông báo: Slack `#k4-l3b-alerts`
- SLI/SLO liên quan: retrieval success guardrail tối thiểu 90%.
- Điều kiện và thời gian duy trì: tỷ lệ `tool_success == true` trên mọi event có `tool_success` nhỏ hơn 90% liên tục trong 5 phút. Mẫu số gồm cả `response_sent` và `request_failed` có trường này.
- Ảnh hưởng tới người dùng: câu trả lời có thể thiếu tài liệu liên quan hoặc request có thể thất bại khi truy xuất.
- Ba bước kiểm tra đầu tiên:
  1. **Metrics:** xác nhận retrieval success rate, số event trong mẫu số và thời gian bắt đầu giảm.
  2. **Logs:** lọc cả `response_sent` lẫn `request_failed` có `tool_success == false`, rồi chọn một `correlation_id` đại diện.
  3. **Traces:** mở trace cùng `correlation_id`; kiểm tra observation `retrieval`, trạng thái và `doc_count` trong metadata của `lab-agent-run`.
- Mitigation tạm thời: khôi phục corpus/cấu hình retrieval gần nhất; nếu đang mô phỏng incident `tool_fail`, tắt scenario đó. Chạy request với câu hỏi có tài liệu đã biết và xác nhận retrieval thành công trước khi đóng alert.
- Owner: `student-2A202602452`
