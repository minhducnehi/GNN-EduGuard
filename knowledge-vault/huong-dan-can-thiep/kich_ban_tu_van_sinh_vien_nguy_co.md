---
tags:
  - can-thiep
  - co-van-hoc-tap
  - rag-knowledge-base
aliases:
  - Kịch bản Tư vấn Sinh viên Nguy cơ Cao
---

# HƯỚNG DẪN CỐ VẤN HỌC TẬP: CAN THIỆP SINH VIÊN CÓ NGUY CƠ CAO

> Cẩm nang hành động thuộc [[README|Cơ sở Tri thức GNN-EduGuard]], phối hợp cùng [[quy-che/quy_che_canh_bao_hoc_vu|Quy chế Cảnh báo Học vụ]] và báo cáo giải thích từ [[gnn-ai/mo_hinh_gnn_eduguard|Mô hình Heterogeneous GNN & GNNExplainer]].

## 1. Phân loại mức độ rủi ro (Risk Levels - Ngưỡng chuẩn 0.70)
- **🔴 Nguy cơ Cao (Risk Score >= 0.70):**
  - Sinh viên có dấu hiệu bỏ rơi học tập: nộp bài tập dưới 50%, điểm trung bình kiểm tra dưới 4.0/10, hoặc vi phạm [[quy-che/quy_dinh_diem_danh_9_buoi|Quy định Điểm danh Chuyên cần 9 Buổi/Học kỳ]] (vắng $\ge 2/9$ buổi, chuyên cần $< 80\%$, nguy cơ cấm thi).
  - *Hành động bắt buộc:* Cố vấn học tập chủ động gửi email cảnh báo và hẹn lịch gặp trực tiếp (offline hoặc online) trong vòng 5 ngày làm việc.
- **🟡 Nguy cơ Trung bình (0.40 <= Risk Score < 0.70):**
  - Sinh viên có kết quả tụt dốc cục bộ ở một số bài tập (ví dụ [[mon-hoc/concept_con_tro_de_quy|Con trỏ & Đệ quy]]), vắng 1/9 buổi học (chuyên cần 89% sát ngưỡng), hoặc có xu hướng nộp bài muộn.
  - *Hành động:* Hệ thống tự động gửi thông báo nhắc nhở nộp bài tập bù và gợi ý tài liệu ôn tập các khái niệm còn yếu trong [[mon-hoc/cau_truc_mon_hoc_va_concept|Cấu trúc Môn học & Cây Khái niệm CS201]].

## 2. Kịch bản Trao đổi & Tư vấn Sư phạm
Khi liên hệ với sinh viên có nguy cơ:
1. **Lắng nghe & Thấu cảm:** Không vội vàng phán xét; tìm hiểu nguyên nhân (hoàn cảnh gia đình, đi làm thêm quá giờ, áp lực tâm lý, hoặc khó tiếp thu kiến thức môn học).
2. **Khai thác lỗ hổng kiến thức bằng XAI:** Đối chiếu với báo cáo giải thích của [[gnn-ai/mo_hinh_gnn_eduguard|GNNExplainer]] để chỉ ra chính xác các khái niệm môn học mà sinh viên đang bị hổng (như [[mon-hoc/concept_con_tro_de_quy|Con trỏ & Đệ quy]] hoặc [[mon-hoc/concept_cay_va_do_thi|Cây & Đồ thị]]).
3. **Thỏa thuận Lộ trình Học bù (Recovery Plan):** Lập kế hoạch đi học đầy đủ các buổi còn lại trong 9 buổi/kỳ, nộp bổ sung các bài tập tự luyện và kết nối sinh viên với nhóm trợ giảng / bạn học hỗ trợ (Peer Tutoring).

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[quy-che/quy_che_canh_bao_hoc_vu|QUY CHẾ CẢNH BÁO HỌC VỤ, ĐIỂM DANH CHUYÊN CẦN (9 BUỔI/KỲ) & ĐIỀU KIỆN DỰ THI]] — **Cosine Similarity: `59.6%`** *(Mức độ: Mạnh)*
- [[quy-che/quy_dinh_diem_danh_9_buoi|QUY ĐỊNH ĐIỂM DANH CHUYÊN CẦN 9 BUỔI/HỌC KỲ & NGƯỠNG CẤM THI 80%]] — **Cosine Similarity: `59.1%`** *(Mức độ: Mạnh)*
- [[README|📚 CƠ SỞ TRI THỨC HỆ THỐNG GNN-EDUGUARD]] — **Cosine Similarity: `52.5%`** *(Mức độ: Mạnh)*
- [[mon-hoc/cau_truc_mon_hoc_va_concept|CẤU TRÚC MÔN HỌC & CÂY KHÁI NIỆM (CONCEPTS)]] — **Cosine Similarity: `51.5%`** *(Mức độ: Mạnh)*
<!-- VECTOR_LINKS_END -->
