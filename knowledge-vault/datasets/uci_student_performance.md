---
tags:
  - dataset
  - student-performance
  - tabular-ml
aliases:
  - UCI Student Performance (Mat & Por)
source: student+performance.zip
processed_by: qwen2.5:3b
---

# 📈 Bộ dữ liệu UCI Student Performance (`student-mat` & `student-por`)

## 1. Thống kê thực tế
- `student-mat.csv` (Môn Toán): `395` học sinh × `33` cột (`0` null).
- `student-por.csv` (Tiếng Bồ Đào Nha): `649` học sinh × `33` cột (`0` null).
- **Đường giăng nội bộ:** Có **`382` học sinh học chung cả 2 môn** (ghép theo 13 thuộc tính nhân khẩu học trong `student-merge.R`), cho phép phân tích rủi ro lan truyền đa môn học.

## 2. Tóm tắt thuộc tính (Ollama `qwen2.5:3b`)
Bộ dữ liệu Student Performance (Toán & Tiếng Bồ Đào Nha) gồm 382 sinh viên, được chia thành hai tập dữ liệu: student-mat.csv (cho môn Toán) và student-por.csv (cho Tiếng Bồ Đào Nha). Các thuộc tính chính bao gồm thông tin về trường học, giới tính, độ tuổi, địa chỉ nhà, số lượng thành viên trong gia đình, tình trạng của cha mẹ, giáo dục của cha mẹ, công việc của cha mẹ, lý do chọn trường, người giám hộ, thời gian đi học, thời gian học tập, số lần bỏ học, hỗ trợ học tập gia đình, học phí, hoạt động ngoại khóa, đi học thêm, đi học thêm môn Toán hoặc Tiếng Bồ Đào Nha, chất lượng mối quan hệ gia đình, thời gian rảnh sau giờ học, hoạt động ngoài giờ học, thời gian uống rượu vào buổi tối, sức khỏe hiện tại, và số lần bỏ học. Điểm G1, G2, G3 liên quan đến kết quả học tập trong hai kỳ học và kỳ cuối cùng. Các biến hành vi như absences, studytime, failures, Dalc/Walc được nhấn mạnh, vì chúng có thể ảnh hưởng đến kết quả học tập.

## 3. Liên kết tri thức
- Đường giăng `absences` ↔ `studentAttendance.csv` & `G1/G2/G3` ↔ `score`: [[00_Master_Graph]]
- Kết quả huấn luyện ML: [[ml-experiments/ket_qua_huan_luyen_ml]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `43.8%`** *(Mức độ: Liên quan)*
- [[datasets/oulad_dataset|📊 Bộ dữ liệu OULAD (Open University Learning Analytics Dataset)]] — **Cosine Similarity: `30.4%`** *(Mức độ: Liên quan)*
- [[quy-che/quy_che_canh_bao_hoc_vu|QUY CHẾ CẢNH BÁO HỌC VỤ, ĐIỂM DANH CHUYÊN CẦN (9 BUỔI/KỲ) & ĐIỀU KIỆN DỰ THI]] — **Cosine Similarity: `27.9%`** *(Mức độ: Liên quan)*
- [[datasets/uci_dropout_success|🎓 Bộ dữ liệu UCI Student Dropout & Academic Success]] — **Cosine Similarity: `27.6%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
