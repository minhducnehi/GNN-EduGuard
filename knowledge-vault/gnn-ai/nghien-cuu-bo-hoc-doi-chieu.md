# Đối chiếu nghiên cứu bỏ học với GNN-EduGuard

Ngày kiểm tra: 2026-11-17. Danh sách người dùng cung cấp là **tên và mô tả, không có URL trực tiếp**. Các liên kết dưới đây dẫn đến bản do tạp chí, tác giả, kho trường hoặc chủ sở hữu dữ liệu phát hành. Không diễn giải kết quả của một tập dữ liệu như bằng chứng hiệu quả trên tập dữ liệu khác.

| Tài liệu được nêu | Xác minh từ nguồn gốc | Ý nghĩa cho dự án |
|---|---|---|
| [ĐH Thủ Dầu Một, nghiên cứu OULAD (2026)](https://journal.tdmu.edu.vn/index.php/tdmujs/en/article/download/2241/2219/2233) | Có bài báo; so sánh LR, RF, XGBoost trên OULAD, AUC báo cáo khoảng 0,847–0,877. OULAD có VLE, điểm và nhân khẩu học. | Bổ sung XGBoost chỉ khi đánh giá cùng split, cùng mốc dự báo và cho thấy lợi ích thực sự. |
| [Tạp chí Giáo chức Việt Nam, “Dự đoán khả năng bỏ học...”](https://tapchigiaochuc.com.vn/j/tcgc/article/view/1453?lang=vi-VN) | Có bài báo; dùng LR/RF với dữ liệu Đại học Phan Thiết. Trang tóm tắt báo accuracy RF 90,66%, LR 85,16%. | Dùng làm ngữ cảnh trong nước, không nhập con số accuracy vào benchmark của dự án. |
| [“Ứng dụng các mô hình học máy...”](https://jst.tnu.edu.vn/jst/article/view/12201) | Bài gốc được tìm thấy tại **TNU Journal of Science and Technology**, không phải hồ sơ STI như mô tả. Dùng dữ liệu chuẩn 4.424 mẫu, 36 đặc trưng và NN/RF/SVM. | Đối chiếu với UCI, kiểm tra quy trình cân bằng tập dữ liệu trước khi sao chép. |
| [JFM, Vũ Sơn Tùng & Trần Thanh Phong (2022)](https://jfm.edu.vn/index.php/jfm/article/view/273) | Có bài gốc: 250 sinh viên vừa học vừa làm, hồi quy Binary Logistic; các yếu tố được tóm tắt gồm thời khóa biểu, bảo lưu, chương trình và dịch vụ học tập. | Các yếu tố hỗ trợ sinh viên có thể bổ sung vào quy trình can thiệp; không có dữ liệu tương ứng để đưa vào model hiện tại. |
| [“Prediction of Student Dropout Risk Using Multi Factor ML...”](https://www.server.riverpublishers.com/pdf/ebook/chapter/RP_9788743817109C37.pdf) | Tìm được bản chương sách do nhà xuất bản lưu trữ. Tác giả so sánh RF/XGBoost/CatBoost với yếu tố vắng học và tương tác. Không xác minh được mô tả “đăng trên ResearchGate” như nguồn gốc chính. | Gợi ý kiểm tra tác động của chuyên cần bằng ablation, không tự suy ra nhân quả. |
| [Heliyon: South Korean distance university (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11145199/) | Có bài gốc trên PMC: 144.540 bản ghi theo kỳ 2018–2022; phân tích khác biệt theo giới và theo kỳ. | Đánh giá sai số theo giới và theo kỳ; chưa có căn cứ đưa giới vào dự đoán cá nhân. |
| [Aulck và cộng sự, arXiv (2016)](https://arxiv.org/abs/1606.06364) | Có bài gốc trên >32.500 sinh viên, sử dụng nhân khẩu học và bảng điểm. Bài cho thấy dữ liệu một học kỳ có thể giúp dự đoán. | Cần định nghĩa mốc dự báo và tránh dùng dữ liệu sau mốc đó. Không xác minh việc bài dùng điểm danh tại lớp. |
| [Vaarma & Li, Tampere (2024)](https://researchportal.tuni.fi/files/111919547/Predicting_student_dropouts.pdf) | Có bản tác giả; nghiên cứu so sánh dữ liệu bảng điểm, nhân khẩu học và Moodle theo tháng. Con số “>36.000” trong mô tả có vẻ là **nghiên cứu khác được bài này trích dẫn**, không phải cỡ mẫu chắc chắn của chính bài. | Đánh giá theo nhiều thời điểm, kiểm tra giá trị bổ sung của LMS so với bảng điểm. |
| [UCI Predict Students' Dropout and Academic Success](https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success) | Dữ liệu 4.424 hồ sơ, 36 đặc trưng, ba lớp. Trường **Daytime/evening attendance** là hình thức học ngày/đêm, **không phải tỷ lệ điểm danh/vắng buổi**. | Chỉ dùng làm benchmark riêng với schema riêng; không ghép cột này vào `attendance_rate`. |
| [Open University OULAD](https://research.stem.open.ac.uk/ouanalyse/dataset/) | Nguồn chính mô tả bảng khóa học, sinh viên, đánh giá và tương tác VLE. **Không có bảng điểm danh tại lớp `studentAttendance.csv` chuẩn**. | Phân biệt rõ dữ liệu OULAD gốc, VLE activity và bảng điểm danh tổng hợp do dự án tạo. |

## Quyết định áp dụng

1. Giữ giới tính ngoài các đặc trưng dự đoán cá nhân hiện tại; dùng để kiểm tra sai số theo nhóm. Bài Heliyon phát hiện khác biệt trong bối cảnh đại học trực tuyến Hàn Quốc, không chứng minh rằng thêm giới sẽ cải thiện công bằng ở bối cảnh khác.
2. Giữ Logistic Regression/RF làm đối chứng. Chỉ thêm thuật toán mới sau khi có cùng dữ liệu, mốc dự báo và giao thức kiểm định. Bảng benchmark hiện tại trên dữ liệu tổng hợp đã cho LR tốt hơn HGT.
3. Dùng `recognition_evaluation.json` để xem hiệu năng theo tuần, Brier và nhóm. Trước triển khai thực tế cần dữ liệu đa kỳ để đánh giá theo thời gian, phân biệt `Fail` và `Withdrawn` nếu mục tiêu là bỏ học thực sự, và xác minh nguồn điểm danh tại lớp.

## Giới hạn tra cứu

- Không có URL/DOI trực tiếp trong danh sách ban đầu; các kết quả trên là đối chiếu theo nhan đề và nội dung ở nguồn gốc tìm được.
- Không tải toàn bộ bộ dữ liệu hoặc kiểm tra từng bảng số liệu trong mọi PDF; các khẳng định định lượng ở đây chỉ dùng phần có thể xác minh từ trang/bản bài gốc.
