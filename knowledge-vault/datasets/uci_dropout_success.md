---
tags:
  - dataset
  - uci-dropout
  - tabular-ml
aliases:
  - UCI Student Dropout and Academic Success
source: predict+students+dropout+and+academic+success (1).zip & archive.zip
processed_by: qwen2.5:3b
---

# 🎓 Bộ dữ liệu UCI Student Dropout & Academic Success

## 1. Kiểm tra chất lượng & Trùng lặp dữ liệu
- **Phát hiện trùng lặp:** `archive.zip/original.csv` và `predict+students+dropout+and+academic+success (1).zip/data.csv` giống nhau **100% từng byte** (`MD5: ee29c9ee9ea60654b5bb0a161c0a473d`, `533,230 bytes`).
- **Kích thước:** `4,424` dòng × `37` cột, `0` giá trị null, delimiter `;`, encoding UTF-8 BOM.
- **Lỗi tên cột cần làm sạch:** `'Daytime/evening attendance\t'` (dư ký tự tab) và `'Nacionality'` (sai chính tả).
- **Phân bố biến mục tiêu (`Target`):** `Graduate`: `2209`, `Dropout`: `1421`, `Enrolled`: `794`.

## 2. Phân nhóm thuộc tính (Ollama `qwen2.5:3b`)
Để phân nhóm các thuộc tính thành 4 nhóm (Nhân khẩu học, Kinh tế-Xã hội, Học lực HK1-HK2, Kinh tế vĩ mô), tôi sẽ phân loại dựa trên nội dung và ý nghĩa của các thuộc tính. Dưới đây là cách phân nhóm:

1. **Nhân khẩu học**: 
   - Marital status (Trạng thái hôn nhân)
   - Application mode (Phương thức đăng ký)
   - Application order (Số thứ tự đăng ký)
   - Course (Khóa học)
   - Daytime/evening attendance (Học ban ngày/ban đêm)
   - Previous qualification (Tín chỉ trước)
   - Previous qualification (điểm) (Tín chỉ trước)
   - Nacionality (Quốc tịch)
   - Mother's qualification (Tín chỉ mẹ)
   - Father's qualification (Tín chỉ cha)
   - Mother's occupation (Chức vụ mẹ)
   - Father's occupation (Chức vụ cha)
   - Admission grade (Điểm nhập học)
   - Displaced (Di cư)
   - Educational special needs (Yêu cầu học tập đặc biệt)
   - Debtor (Người vay)
   - Tuition fees up to date (Tín dụng học phí)
   - Gender (Giới tính)
   - Scholarship holder (Người nhận học bổng)
   - Age at enrollment (Tuổi nhập học)
   - International (Quốc tế)
   - Unemployment rate (Tỷ lệ thất nghiệp)
   - Inflation rate (Tỷ lệ lạm phát)
   - GDP (GDP)

2. **Kinh tế-Xã hội**: 
   - Tuition fees up to date (Tín dụng học phí)
   - International (Quốc tế)
   - Unemployment rate (Tỷ lệ thất nghiệp)
   - Inflation rate (Tỷ lệ lạm phát)
   - GDP (GDP)

3. **Học lực HK1-HK2**: 
   - Curricular units 1st sem (credited) (Tín chỉ 1 học kỳ)
   - Curricular units 1st sem (enrolled) (Đăng ký 1 học kỳ)
   - Curricular units 1st sem (evaluations) (Đánh giá 1 học kỳ)
   - Curricular units 1st sem (approved) (Phê duyệt 1 học kỳ)
   - Curricular units 1st sem (grade) (Điểm 1 học kỳ)
   - Curricular units 1st sem (without evaluations) (Không đánh giá 1 học kỳ)
   - Curricular units 2nd sem (credited) (Tín chỉ 2 học kỳ)
   - Curricular units 2nd sem (enrolled) (Đăng ký 2 học kỳ)
   - Curricular units 2nd sem (evaluations) (Đánh giá 2 học kỳ)
   - Curricular units 2nd sem (approved) (Phê duyệt 2 học kỳ)
   - Curricular units 2nd sem (grade) (Điểm 2 học kỳ)
   - Curricular units 2nd sem (without evaluations) (Không đánh giá 2 học kỳ)

4. **Kinh tế vĩ mô**: 
   - Tuition fees up to date (Tín dụng học phí)
   - International (Quốc tế)
   - Unemployment rate (Tỷ lệ thất nghiệp)
   - Inflation rate (Tỷ lệ lạm phát)
   - GDP (GDP)

Như vậy, các thuộc tính đã được phân loại thành 4 nhóm theo yêu cầu.

## 3. Liên kết tri thức
- Sơ đồ tổng thể & đường giăng ẩn sang OULAD: [[00_Master_Graph]]
- Kết quả huấn luyện ML: [[ml-experiments/ket_qua_huan_luyen_ml]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `29.6%`** *(Mức độ: Liên quan)*
- [[ml-experiments/ket_qua_huan_luyen_ml|🤖 Báo cáo Huấn luyện & Đánh giá Mô hình ML (Bước 4)]] — **Cosine Similarity: `29.0%`** *(Mức độ: Liên quan)*
- [[datasets/uci_student_performance|📈 Bộ dữ liệu UCI Student Performance (`student-mat` & `student-por`)]] — **Cosine Similarity: `27.6%`** *(Mức độ: Liên quan)*
- [[datasets/oulad_dataset|📊 Bộ dữ liệu OULAD (Open University Learning Analytics Dataset)]] — **Cosine Similarity: `26.0%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
