---
tags:
  - dataset
  - oulad
  - lms
  - knowledge-graph
aliases:
  - OULAD Full Dataset
source: open+university+learning+analytics+dataset.zip
processed_by: qwen2.5:3b
---

# 📊 Bộ dữ liệu OULAD (Open University Learning Analytics Dataset)

## 1. Tóm tắt từ Ollama (`qwen2.5:3b`)
### Tóm Tắt Về Bộ Dữ Liệu OULAD

#### 1. Mục đích
Bộ dữ liệu OULAD được tạo ra để cung cấp dữ liệu về các khóa học, sinh viên và các hoạt động của môi trường học tập trực tuyến (VLE) tại Đại học Quốc gia Anh. Mục đích chính là cung cấp thông tin phân tích học tập để các nhà nghiên cứu và chuyên gia có thể phân tích và hiểu rõ hơn về cách sinh viên tương tác với các khóa học và bài kiểm tra.

#### 2. Các Bảng Chính & Khóa Liên Kết
- **Bảng chính:**
  - **courses.csv:** Thông tin về các khóa học, bao gồm mã khóa học, mã presentation, và thời lượng của khóa học.
  - **assessments.csv:** Thông tin về các bài kiểm tra, bao gồm mã khóa học, mã presentation, số ID của bài kiểm tra, loại bài kiểm tra và ngày kiểm tra.

- **Khóa liên kết:**
  - Mã khóa học (code_module) trong bảng `courses.csv` và `assessments.csv` liên kết với nhau.
  - Mã presentation (code_presentation) trong bảng `courses.csv` và `assessments.csv` cũng liên kết với nhau.

#### 3. Biến Mục Tiêu
- **Biến mục tiêu chính:**
  - **code_module:** Mã khóa học (nominal)
  - **code_presentation:** Mã presentation (nominal)
  - **id_assessment:** Số ID của bài kiểm tra (integer)
  - **assessment_type:** Loại bài kiểm tra (nominal)
  - **date:** Ngày kiểm tra (integer)

Bộ dữ liệu OULAD cung cấp một nguồn dữ liệu đáng tin cậy cho các nghiên cứu về phân tích học tập, cho phép các nhà nghiên cứu hiểu rõ hơn về cách sinh viên tương tác với các khóa học và bài kiểm tra.

## 2. Thống kê thực tế & Đối chiếu với EduGuard
| Bảng | OULAD Full (Rows x Cols) | EduGuard Raw (Rows x Cols) | Khóa chính / Khóa ngoại |
| :--- | :--- | :--- | :--- |
| `courses.csv` | `22 x 3` | `4 x 3` | `(code_module, code_presentation)` |
| `assessments.csv` | `206 x 6` | `16 x 7` | `id_assessment`, `(code_module, code_presentation)` |
| `vle.csv` | `6,364 x 6` | `72 x 7` | `id_site`, `(code_module, code_presentation)` |
| `studentInfo.csv` | `32,593 x 12` | `300 x 12` | `id_student`, `(code_module, code_presentation)` |
| `studentRegistration.csv` | `32,593 x 5` | `300 x 5` | `id_student`, `(code_module, code_presentation)` |
| `studentAssessment.csv` | `173,912 x 5` | `879 x 5` | `id_assessment`, `id_student` |
| `studentVle.csv` | `10,655,280 x 6` | `2,200 x 6` | `id_student`, `id_site`, `(code_module, code_presentation)` |
| `studentAttendance.csv` | *Không có* | `2,700 x 6` | `id_student`, `code_module`, `concept_idx` |

## 3. Liên kết tri thức
- Xem tổng quan đường giăng: [[00_Master_Graph]]
- Mô hình GNN sử dụng dữ liệu này: [[gnn-ai/mo_hinh_gnn_eduguard]]
- Quy định điểm danh 9 buổi (nguồn gốc `studentAttendance.csv`): [[quy-che/quy_dinh_diem_danh_9_buoi]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `49.1%`** *(Mức độ: Mạnh)*
- [[datasets/uci_student_performance|📈 Bộ dữ liệu UCI Student Performance (`student-mat` & `student-por`)]] — **Cosine Similarity: `30.4%`** *(Mức độ: Liên quan)*
- [[datasets/uci_dropout_success|🎓 Bộ dữ liệu UCI Student Dropout & Academic Success]] — **Cosine Similarity: `26.0%`** *(Mức độ: Liên quan)*
- [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO]] — **Cosine Similarity: `24.2%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
