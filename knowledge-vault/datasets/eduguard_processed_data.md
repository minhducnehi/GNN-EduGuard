---
tags:
  - benchmark
  - gnn-eduguard
  - metrics
aliases:
  - Benchmark GNN-EduGuard
source: ai-service/gnn/data/processed/benchmark_summary.json
---

# 🧪 Kết quả Benchmark hiện có của `GNN-EduGuard`

| Mô hình | F1-Macro | F1-Risk | Recall-Risk | Precision-Risk | AUC-ROC |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Logistic Regression | 0.9754 | 0.9831 | 1.0 | 0.9667 | 1.0 |
| Random Forest | 0.9527 | 0.9643 | 0.931 | 1.0 | 0.9978 |
| Gradient Boosting | 0.95 | 0.9667 | 1.0 | 0.9355 | 0.9957 |
| HGT (HeteroGNN) | 0.8804 | 0.9123 | 0.8966 | 0.9286 | 0.9741 |
| HGT + LSTM (Temporal) | 0.8963 | 0.9355 | 1.0 | 0.8788 | 0.9892 |

> [!NOTE]
> Các chỉ số trên được đo trên tập mẫu `300` sinh viên trong `ai-service/gnn/data/raw/`. Để đánh giá tổng quát hơn, cần đối chiếu với kết quả huấn luyện trên bộ dữ liệu mới (OULAD Full / UCI Dropout / Student Performance) tại [[ml-experiments/ket_qua_huan_luyen_ml]].

## Liên kết tri thức
- [[00_Master_Graph]]
- [[gnn-ai/mo_hinh_gnn_eduguard]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[ml-experiments/ket_qua_huan_luyen_ml|🤖 Báo cáo Huấn luyện & Đánh giá Mô hình ML (Bước 4)]] — **Cosine Similarity: `46.7%`** *(Mức độ: Mạnh)*
- [[bao-cao-tuan/phieu_dang_ky_va_tien_do|🗓️ Hồ sơ Đăng ký & Tiến độ Đồ án Chuyên ngành (Tuần 1 – Tuần 4)]] — **Cosine Similarity: `20.3%`** *(Mức độ: Liên quan)*
- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `18.4%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
