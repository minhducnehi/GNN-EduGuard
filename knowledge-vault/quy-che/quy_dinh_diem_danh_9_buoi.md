---
tags:
  - quy-che
  - diem-danh
  - canh-bao-hoc-vu
aliases:
  - Quy định Điểm danh 9 Buổi
---

# QUY ĐỊNH ĐIỂM DANH CHUYÊN CẦN 9 BUỔI/HỌC KỲ & NGƯỠNG CẤM THI 80%

> Văn bản chi tiết hóa mục chuyên cần trong [[quy-che/quy_che_canh_bao_hoc_vu|Quy chế Cảnh báo Học vụ]] và cung cấp đặc trưng đầu vào `attendance_rate` cho [[gnn-ai/mo_hinh_gnn_eduguard|Mô hình Heterogeneous GNN]].

## 1. Bảng Quy đổi Chuyên cần 9 Buổi/Học kỳ
Trong hệ thống đào tạo học phần tiêu chuẩn (9 buổi học lý thuyết/thực hành tập trung mỗi kỳ):

| Số buổi có mặt | Số buổi vắng | Tỷ lệ chuyên cần (`attendance_rate`) | Trạng thái học vụ & Dự báo GNN |
| :---: | :---: | :---: | :--- |
| **9/9 buổi** | 0 buổi | `100.0%` | Đạt chuẩn chuyên cần xuất sắc |
| **8/9 buổi** | 1 buổi | `88.9%` | Đạt điều kiện dự thi ($\ge 80\%$), **Cảnh báo sớm sát ngưỡng** |
| **7/9 buổi** | 2 buổi | `77.8%` | **Vi phạm ngưỡng $<80\%$** — Nguy cơ cấm thi kết thúc học phần |
| **$\le$ 6/9 buổi** | $\ge 3$ buổi | $\le 66.7\%$ | **Cấm thi học phần** — Kích hoạt [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|Kịch bản Can thiệp Khẩn cấp]] |

## 2. Tác động lên Dự báo AI & Lỗ hổng Kiến thức
- Khi sinh viên vắng mặt ở các buổi học nền tảng (buổi 2–4), sinh viên thường bỏ lỡ kiến thức [[mon-hoc/concept_con_tro_de_quy|Con trỏ & Đệ quy]], dẫn đến không làm được bài tập [[mon-hoc/concept_cay_va_do_thi|Cây Nhị Phân & Đồ Thị]] ở các buổi 6–9.
- Cố vấn học tập cần đối chiếu đồng thời dữ liệu điểm danh và cây khái niệm [[mon-hoc/cau_truc_mon_hoc_va_concept|Cấu trúc Môn học CS201]] để yêu cầu sinh viên học bù ngay khi mới vắng 1/9 buổi.

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[quy-che/quy_che_canh_bao_hoc_vu|QUY CHẾ CẢNH BÁO HỌC VỤ, ĐIỂM DANH CHUYÊN CẦN (9 BUỔI/KỲ) & ĐIỀU KIỆN DỰ THI]] — **Cosine Similarity: `69.8%`** *(Mức độ: Rất mạnh)*
- [[huong-dan-can-thiep/kich_ban_tu_van_sinh_vien_nguy_co|HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO]] — **Cosine Similarity: `59.1%`** *(Mức độ: Mạnh)*
- [[mon-hoc/concept_cay_va_do_thi|CONCEPT LEVEL 2-3: CÂY NHỊ PHÂN & ĐỒ THỊ (TREES & GRAPHS)]] — **Cosine Similarity: `48.3%`** *(Mức độ: Mạnh)*
- [[mon-hoc/concept_con_tro_de_quy|CONCEPT LEVEL 1: CON TRỎ, QUẢN LÝ BỘ NHỚ & ĐỆ QUY (POINTERS & RECURSION)]] — **Cosine Similarity: `46.7%`** *(Mức độ: Mạnh)*
<!-- VECTOR_LINKS_END -->
