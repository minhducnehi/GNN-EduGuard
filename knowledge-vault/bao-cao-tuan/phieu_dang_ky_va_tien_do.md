---
tags:
  - bao-cao-tuan
  - tien-do-dacn
  - hutech
aliases:
  - Tiến độ ĐACN Vũ Minh Đức
sources:
  - VuMinhDuc-2380614671.pdf
  - VuMinhDuc-2380614671-tuan2.pdf
  - vuMinhDuc-2380614671-tuần3.pdf
  - VuMinhDuc-2380614671-tuan4.pdf
processed_by: qwen2.5:3b
---

# 🗓️ Hồ sơ Đăng ký & Tiến độ Đồ án Chuyên ngành (Tuần 1 – Tuần 4)

## 1. Thông tin hành chính
- **Sinh viên:** Vũ Minh Đức (`2380614671`) — Lớp `23DTHC3` (HUTECH, Khoa CNTT, CNPM)
- **Giảng viên hướng dẫn:** Trình Đồng Thạch Trúc
- **Đề tài:** *Dự đoán nguy cơ học tập của sinh viên bằng đồ thị tương tác học tập và GNN*

## 2. Bảng đối chiếu Tiến độ PDF ↔ Mã nguồn `GNN-EduGuard`
| Tuần | Thời gian | Nội dung trong PDF | Module tương ứng trong `GNN-EduGuard` |
| :--- | :--- | :--- | :--- |
| **Tuần 1** | `12/10 – 18/10/2026` | Tìm hiểu dữ liệu LMS (OULAD) | `ai-service/gnn/data_loader.py`, `data_quality.py` |
| **Tuần 2** | `19/10 – 25/10/2026` | Tạo database & xây dựng đồ thị | `ai-service/gnn/build_graph.py`, `Data/ApplicationDbContext.cs` |
| **Tuần 3** | `26/10 – 01/11/2026` | Xây dựng baseline, trích xuất đặc trưng | `ai-service/gnn/baseline.py`, `student_features.csv` |
| **Tuần 4** | `02/11 – 08/11/2026` | Xây dựng kiến trúc mô hình GNN | `ai-service/gnn/models/hgt_model.py`, `temporal_model.py`, `train.py` |

## 3. Tóm tắt lộ trình (Ollama `qwen2.5:3b`)
Dựa trên thông tin các phiếu đăng ký và tiến độ đồ án chuyên ngành, lộ trình thực hiện và mục tiêu đề tài của SV Vũ Minh Đức có thể được tóm tắt như sau: 

Mục tiêu đề tài là dự đoán nguy cơ học tập của sinh viên dựa trên đồ thị tương tác học tập và GNN. GVHD là Trình Đồng Thạch Trúc. 

Lộ trình cụ thể bao gồm:
- Tuần 1: Tìm hiểu dữ liệu từ hệ thống quản lý học tập (OULAD).
- Tuần 2: Tạo database và xây dựng đồ thị tương tác.
- Tuần 3: Xây dựng baseline và trích xuất đặc trưng.
- Tuần 4: Xây dựng kiến trúc mô hình GNN.

Đây là lộ trình thực hiện cho đề tài, với mục tiêu chính là phát triển một mô hình dự đoán nguy cơ học tập dựa trên dữ liệu học tập của sinh viên.

## 4. Liên kết tri thức
- Sơ đồ kiến trúc & đường giăng tổng thể: [[00_Master_Graph]]
- Chi tiết mô hình GNN: [[gnn-ai/mo_hinh_gnn_eduguard]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO]] — **Cosine Similarity: `36.3%`** *(Mức độ: Liên quan)*
- [[README|📚 CƠ SỞ TRI THỨC HỆ THỐNG GNN-EDUGUARD]] — **Cosine Similarity: `26.8%`** *(Mức độ: Liên quan)*
- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `26.6%`** *(Mức độ: Liên quan)*
- [[datasets/uci_student_performance|📈 Bộ dữ liệu UCI Student Performance (`student-mat` & `student-por`)]] — **Cosine Similarity: `23.7%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
