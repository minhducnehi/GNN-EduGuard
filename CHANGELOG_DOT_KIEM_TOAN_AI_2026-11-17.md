# Tổng kết đợt kiểm toán và cải thiện GNN-EduGuard

Ngày: 2026-11-17

## Phạm vi

Đợt này kiểm tra luồng ASP.NET Core → FastAPI → mô hình GNN, pipeline tạo dữ liệu/huấn luyện, chất lượng nhận diện nguy cơ học vụ, và đối chiếu các nghiên cứu về bỏ học sinh viên. Không chạy lại quá trình huấn luyện toàn bộ mô hình và không triển khai production.

## Những thay đổi đã thực hiện

### Bảo vệ quyền truy cập sinh viên

- `GNN-EduGuard/Controllers/Api/PredictionsApiController.cs`: lọc danh sách theo phạm vi vai trò/lớp; kiểm tra quyền trước khi trả chi tiết hoặc tư vấn cho một sinh viên; trả `404` khi sinh viên không tồn tại.
- Mục đích: API trước đó thiếu các giới hạn đã có ở giao diện MVC, có thể trả dữ liệu sinh viên ngoài phạm vi được giao.

### Ngăn kết quả nhận diện sai hoặc giả

- `ai-service/gnn/explainer.py`: mã sinh viên không tồn tại không còn bị ép về node đầu/cuối; thay bằng lỗi rõ ràng.
- `ai-service/main.py`: endpoint dự đoán/giải thích trả `404` cho mã sinh viên không tồn tại; `/api/health` báo `degraded` khi thiếu mô hình và `/api/ready` trả `503` cho đến khi các artifact cần thiết sẵn sàng.
- `ai-service/gnn/predictor.py`: khi thiếu checkpoint hoặc graph, không còn trả điểm nguy cơ cố định `0.78` và mức `High` giả.

### Bảo vệ dữ liệu đầu vào huấn luyện

- `ai-service/run_pipeline.py`: chỉ tạo dữ liệu tổng hợp khi có cờ `--generate-synthetic`; chạy mặc định kiểm tra đủ tám CSV đầu vào.
- `ai-service/gnn/build_graph.py`: loại bỏ các nhánh tự ghi đè CSV bằng dữ liệu tổng hợp khi thiếu tệp, ít hơn 250 sinh viên hoặc dùng `force_regen=True`; thiếu tệp giờ báo lỗi.
- Mục đích: giữ nguyên dữ liệu nghiên cứu hoặc dữ liệu thật được cung cấp và tránh benchmark âm thầm chuyển sang dữ liệu tổng hợp.

### Đánh giá mô hình và kiểm thử

- `ai-service/evaluate_recognition.py`: đọc checkpoint đã lưu và đánh giá trên tập test; báo precision, recall, ROC-AUC, Brier score, tỷ lệ nguy cơ quan sát/dự đoán, khoảng tin cậy bootstrap, nhóm giới tính/môn học, các mốc tuần 2/4/8/12/16 và số trường hợp `Fail`/`Withdrawn` được đánh dấu.
- `ai-service/recognition_evaluation.json`: kết quả đánh giá có thể tạo lại bằng `ai-service/.venv/Scripts/python.exe ai-service/evaluate_recognition.py`.
- `ai-service/tests/test_api.py` và `ai-service/tests/test_pipeline_safety.py`: kiểm thử hồi quy cho ID không tồn tại, thiếu mô hình, chống ghi đè dữ liệu và nhóm đánh giá chỉ có một nhãn.

## Kết quả đo được

Tập test hiện có gồm **45 hồ sơ tổng hợp**, trong đó **29 hồ sơ mang nhãn nguy cơ** (`Fail` hoặc `Withdrawn`).

| Mô hình | Recall | Precision | Brier score |
|---|---:|---:|---:|
| HGT tĩnh | 0,897 | 0,929 | 0,100 |
| HGT theo thời gian, tuần 2 | 0,793 | 0,852 | 0,185 |
| HGT theo thời gian, tuần 16 | 1,000 | 0,879 | 0,080 |

Trong 14 hồ sơ `Withdrawn` của tập test, HGT tĩnh đánh dấu 13 và mô hình tuần 2 đánh dấu 11. Đây là số đếm trên dữ liệu tổng hợp của mô hình huấn luyện bằng **nhãn gộp `Fail`/`Withdrawn`**, không phải độ chính xác đã xác nhận cho dự đoán bỏ học thực tế. Khoảng tin cậy recall tuần 2 là 0,640–0,929, cho thấy độ bất định còn lớn.

## Nghiên cứu được đối chiếu

- `knowledge-vault/gnn-ai/nghien-cuu-bo-hoc-doi-chieu.md` ghi đối chiếu từng nghiên cứu/bộ dữ liệu trong danh sách người dùng, liên kết nguồn và giới hạn xác minh.
- [OULAD gốc](https://research.stem.open.ac.uk/ouanalyse/dataset/) có dữ liệu tương tác VLE, không có bảng điểm danh lớp `studentAttendance.csv` chuẩn. Bảng điểm danh 9 buổi của dự án là phần mở rộng tổng hợp.
- [UCI Predict Students' Dropout and Academic Success](https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success) có trường “Daytime/evening attendance” chỉ ca học ngày/đêm, không phải tỷ lệ điểm danh.
- Vì vậy, chưa đưa giới tính vào đặc trưng dự đoán cá nhân và chưa sao chép chỉ số từ các bài báo vào benchmark của dự án. Kết quả theo giới hiện chỉ phục vụ kiểm tra sai số, không đủ cỡ mẫu để kết luận công bằng.

## Kiểm tra đã chạy

- `ai-service/.venv/Scripts/python.exe -m pytest ai-service/tests -q`: **29 passed**, một cảnh báo `FutureWarning` từ PyTorch.
- `dotnet build GNN-EduGuard.slnx --no-restore`: **thành công**, 0 warning, 0 error.
- `python -m compileall -q ai-service`: không có lỗi cú pháp.
- `git diff --check`: không có lỗi khoảng trắng.

## Giới hạn và việc tiếp theo

1. **Ưu tiên cao:** kiểm định trên dữ liệu sinh viên thật được phép sử dụng, với nhiều kỳ học để chia theo thời gian; xác định riêng nhãn *bỏ học* và *trượt môn*. Dữ liệu hiện tại chỉ có một kỳ tổng hợp.
2. **Ưu tiên cao:** bảo vệ các endpoint FastAPI bằng xác thực giữa dịch vụ; thay tài khoản demo có mật khẩu cố định và kiểm soát fallback dữ liệu mock của ASP.NET Core trước khi đưa dữ liệu thật vào.
3. **Ưu tiên vừa:** đo độ hiệu chuẩn và sai số theo nhóm trên mẫu đủ lớn; so sánh GNN với Logistic Regression/Random Forest cùng dữ liệu, cùng thời điểm dự báo. Benchmark tổng hợp hiện chưa chứng minh GNN vượt mô hình đơn giản.
4. **Ưu tiên vừa:** kiểm thử tích hợp khi Docker, PostgreSQL và Ollama sẵn sàng. Docker server không phản hồi trong đợt kiểm toán nên chưa xác minh được triển khai container.

Chi tiết kỹ thuật và lệnh chạy lại được lưu trong `ML_DEPLOYMENT_AUDIT.md`.
