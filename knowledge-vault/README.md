---
tags:
  - hub
  - gnn-vector
  - rag-knowledge-base
aliases:
  - GNN-EduGuard Vault Hub
---

# 📚 CƠ SỞ TRI THỨC HỆ THỐNG GNN-EDUGUARD

Chào mừng bạn đến với Vault tri thức của hệ thống **GNN-EduGuard**!

Thư mục này đóng vai trò là **Kho Tri Thức (Knowledge Base & Vector Graph)** chuyên môn để AI Agent (`Qwen 2.5 3B` / `Hermes`) và mô hình [[gnn-ai/mo_hinh_gnn_eduguard|Mô hình Heterogeneous GNN & GNNExplainer]] tra cứu thông qua cơ chế **RAG (Retrieval-Augmented Generation)** kết hợp **ChromaDB Vector Store**.

---

## 🗂 Cấu Trúc Mạng Lưới Tri Thức (Knowledge & Vector Graph)

1. **Quy chế & Chuyên cần (`quy-che/`):**
   - [[quy-che/quy_che_canh_bao_hoc_vu|Quy chế Cảnh báo Học vụ & Điều kiện Dự thi]] (`#quy-che`)
   - [[quy-che/quy_dinh_diem_danh_9_buoi|Quy định Điểm danh Chuyên cần 9 Buổi/Học kỳ & Ngưỡng Cấm thi 80%]] (`#diem-danh`)
2. **Môn học & Cây Khái niệm (`mon-hoc/`):**
   - [[mon-hoc/cau_truc_mon_hoc_va_concept|Cấu trúc Môn học & Cây Khái niệm CS201]] (`#mon-hoc`)
   - [[mon-hoc/concept_con_tro_de_quy|Concept Level 1: Con trỏ, Bộ nhớ & Đệ quy (Pointers & Recursion)]] (`#concept`)
   - [[mon-hoc/concept_cay_va_do_thi|Concept Level 2-3: Cây Nhị Phân & Đồ Thị (Trees & Graphs)]] (`#concept`)
3. **Hướng dẫn Can thiệp Sư phạm (`huong-dan-can-thiep/`):**
   - [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|Kịch bản Tư vấn & Can thiệp Sinh viên Nguy cơ Cao]] (`#can-thiep`)
4. **Kiến trúc AI & Vector Graph (`gnn-ai/`):**
   - [[gnn-ai/mo_hinh_gnn_eduguard|Kiến trúc Heterogeneous GNN, GNNExplainer & ChromaDB Vector Linker]] (`#gnn-vector`)

---

## ⚡ Cơ Chế Đồng Bộ Vector Tự Động (ChromaDB <-> Obsidian Graph View)
- Mỗi khi bạn tạo hoặc chỉnh sửa ghi chú trong thư mục này, tiến trình nền (`ai-service/rag/obsidian_watcher.py`) sẽ:
  1. Băm nhỏ nội dung (*chunking*) và nhúng thành vector 768 chiều (`nomic-embed-text`) lưu vào **ChromaDB**.
  2. Tính toán **Độ tương đồng Cosine (Cosine Similarity)** giữa toàn bộ các vector tài liệu và tự động chèn mục **`## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)`** dạng `[[wikilink]]` vào cuối mỗi file để hiển thị trực quan các đường nối vector trên **Obsidian Graph View**.

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[gnn-ai/mo_hinh_gnn_eduguard|KIẾN TRÚC HETEROGENEOUS GNN, GNNEXPLAINER & CHROMADB VECTOR LINKER]] — **Cosine Similarity: `73.1%`** *(Mức độ: Rất mạnh)*
- [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO]] — **Cosine Similarity: `52.5%`** *(Mức độ: Mạnh)*
- [[mon-hoc/cau_truc_mon_hoc_va_concept|CẤU TRÚC MÔN HỌC & CÂY KHÁI NIỆM (CONCEPTS)]] — **Cosine Similarity: `50.7%`** *(Mức độ: Mạnh)*
- [[mon-hoc/concept_cay_va_do_thi|CONCEPT LEVEL 2-3: CÂY NHỊ PHÂN & ĐỒ THỊ (TREES & GRAPHS)]] — **Cosine Similarity: `46.2%`** *(Mức độ: Mạnh)*
<!-- VECTOR_LINKS_END -->
