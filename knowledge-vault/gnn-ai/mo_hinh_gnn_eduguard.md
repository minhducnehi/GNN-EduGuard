---
tags:
  - gnn-vector
  - rag-knowledge-base
  - xai
aliases:
  - Mô hình Heterogeneous GNN & Vector Graph
---

# KIẾN TRÚC HETEROGENEOUS GNN, GNNEXPLAINER & CHROMADB VECTOR LINKER

> Tài liệu kỹ thuật trung tâm của [[README|Cơ sở Tri thức GNN-EduGuard]], kết nối dự báo rủi ro học tập với [[quy-che/quy_che_canh_bao_hoc_vu|Quy chế Cảnh báo Học vụ]], [[quy-che/quy_dinh_diem_danh_9_buoi|Quy định Điểm danh 9 Buổi/Học kỳ]] và [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|Kịch bản Tư vấn Sinh viên Nguy cơ Cao]].

## 1. Đồ thị Tri thức Không đồng nhất (Heterogeneous Graph - PyTorch Geometric)
- **4 loại nút (Nodes):** `Student` (6 đặc trưng hành vi & chuyên cần 9 buổi), `VLE_Material`, `Quiz`, `Concept` (liên kết với [[mon-hoc/cau_truc_mon_hoc_va_concept|Cấu trúc Môn học CS201]]).
- **3 loại cạnh (Edges):**
  - `(Student)-[:CLICKED]->(VLE_Material)`
  - `(Student)-[:SUBMITTED]->(Quiz)`
  - `(Quiz)-[:TESTS]->(Concept)` (liên kết tới [[mon-hoc/concept_con_tro_de_quy|Con trỏ & Đệ quy]] và [[mon-hoc/concept_cay_va_do_thi|Cây & Đồ thị]])

## 2. Cơ chế Đồng bộ Vector ChromaDB sang Obsidian Graph View
- Hệ thống sử dụng `ObsidianVectorStore` (ChromaDB) kết hợp vector 768 chiều (`nomic-embed-text`) để lưu trữ ngữ nghĩa từng phân đoạn tài liệu.
- Vì **Obsidian Graph View** chỉ vẽ cạnh nối khi có `[[wikilink]]` hoặc `#tag` trong file Markdown, module `ObsidianVaultSync` tự động tính **Cosine Similarity** giữa các vector tài liệu và ghi mục **Liên kết Ngữ nghĩa Vector** vào cuối mỗi ghi chú.

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[README|📚 CƠ SỞ TRI THỨC HỆ THỐNG GNN-EDUGUARD]] — **Cosine Similarity: `73.1%`** *(Mức độ: Rất mạnh)*
- [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO]] — **Cosine Similarity: `49.8%`** *(Mức độ: Mạnh)*
- [[mon-hoc/cau_truc_mon_hoc_va_concept|CẤU TRÚC MÔN HỌC & CÂY KHÁI NIỆM (CONCEPTS)]] — **Cosine Similarity: `48.4%`** *(Mức độ: Mạnh)*
- [[mon-hoc/concept_cay_va_do_thi|CONCEPT LEVEL 2-3: CÂY NHỊ PHÂN & ĐỒ THỊ (TREES & GRAPHS)]] — **Cosine Similarity: `46.4%`** *(Mức độ: Mạnh)*
<!-- VECTOR_LINKS_END -->
