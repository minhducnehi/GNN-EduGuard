---
tags:
  - ml-experiments
  - evaluation
  - accuracy
  - f1-score
aliases:
  - Kết quả Huấn luyện ML Bước 4
---

# 🤖 Báo cáo Huấn luyện & Đánh giá Mô hình ML (Bước 4)

Báo cáo này tổng hợp kết quả huấn luyện thực tế trên 3 bộ dữ liệu mới thu thập (đã loại bỏ các biến gây **Data Leakage** ở kịch bản Early Warning).

---

## 1. OULAD Full (`32,593` lượt đăng ký, tổng hợp từ `10.65M` dòng VLE)
- **Biến mục tiêu:** Nhị phân (`Withdrawn / Fail` = `1` chiếm `52.8%`, `Pass / Distinction` = `0`).
- **Chống Data Leakage:** Đã loại bỏ hoàn toàn `date_unregistration` và `id_student`.

| Mô hình | Accuracy | F1-Macro | F1-Risk | AUC-ROC |
| :--- | :---: | :---: | :---: | :---: |
| LogisticRegression | `0.9169` | `0.9168` | `0.9187` | `0.9665` |
| RandomForest | `0.9330` | `0.9329` | `0.9341` | `0.9792` |
| HistGradientBoosting | `0.9357` | `0.9357` | `0.9372` | `0.9799` |

---

## 2. UCI Student Dropout & Academic Success (`4,424` SV, 3 lớp)
- **Biến mục tiêu:** `Graduate`, `Dropout`, `Enrolled`.

### Kịch bản A: Đầy đủ 36 đặc trưng (HK1 + HK2)
| Mô hình | Accuracy | F1-Macro |
| :--- | :---: | :---: |
| LogisticRegression | `0.7684` | `0.6826` |
| RandomForest | `0.7672` | `0.6842` |
| HistGradientBoosting | `0.7605` | `0.6967` |

### Kịch bản B: Early Warning (Ẩn toàn bộ điểm HK2)
| Mô hình | Accuracy | F1-Macro |
| :--- | :---: | :---: |
| LogisticRegression | `0.7345` | `0.6120` |
| RandomForest | `0.7356` | `0.6293` |
| HistGradientBoosting | `0.7141` | `0.6345` |

**Top đặc trưng quan trọng nhất (Random Forest):**
- `Curricular units 2nd sem (approved)`: `0.1519`
- `Curricular units 2nd sem (grade)`: `0.0982`
- `Curricular units 1st sem (approved)`: `0.087`
- `Curricular units 1st sem (grade)`: `0.0648`
- `Admission grade`: `0.0425`
- `Tuition fees up to date`: `0.042`
- `Curricular units 2nd sem (evaluations)`: `0.0402`
- `Age at enrollment`: `0.0382`

---

## 3. UCI Student Performance — Toán + Tiếng Bồ Đào Nha (`1,044` HS)
- **Biến mục tiêu:** `At-Risk` (`G3 < 10`, chiếm `22.0%`).

### Kịch bản A: Có điểm `G1, G2`
| Mô hình | Accuracy | F1-Macro | F1-Risk | AUC-ROC |
| :--- | :---: | :---: | :---: | :---: |
| LogisticRegression | `0.8995` | `0.8548` | `0.7742` | `0.9699` |
| RandomForest | `0.9091` | `0.8666` | `0.7912` | `0.9740` |
| HistGradientBoosting | `0.8995` | `0.8570` | `0.7789` | `0.9689` |

### Kịch bản B: Early Warning (Ẩn `G1, G2`, chỉ dùng `absences`, `failures`, hành vi)
| Mô hình | Accuracy | F1-Macro | F1-Risk | AUC-ROC |
| :--- | :---: | :---: | :---: | :---: |
| LogisticRegression | `0.8182` | `0.6812` | `0.4722` | `0.7730` |
| RandomForest | `0.8038` | `0.6356` | `0.3881` | `0.8292` |
| HistGradientBoosting | `0.7943` | `0.6644` | `0.4557` | `0.8106` |

---

## 🔗 Liên kết Tri thức
- Sơ đồ đường giăng tổng thể: [[00_Master_Graph]]
- So sánh với GNN-EduGuard hiện có: [[datasets/eduguard_processed_data]]
- Chi tiết từng bộ dữ liệu: [[datasets/oulad_dataset]] | [[datasets/uci_dropout_success]] | [[datasets/uci_student_performance]]

<!-- VECTOR_LINKS_START -->
---
## 🔗 Liên kết Ngữ nghĩa Vector (ChromaDB Semantic Links)
> *Tự động tính toán bởi `ObsidianVaultSync` & `ChromaDB` (768-dim Vector Cosine Similarity) giúp hiển thị mạng lưới liên kết ngữ nghĩa trực tiếp trên **Obsidian Graph View**.*

- [[datasets/eduguard_processed_data|🧪 Kết quả Benchmark hiện có của `GNN-EduGuard`]] — **Cosine Similarity: `46.7%`** *(Mức độ: Mạnh)*
- [[datasets/uci_dropout_success|🎓 Bộ dữ liệu UCI Student Dropout & Academic Success]] — **Cosine Similarity: `29.0%`** *(Mức độ: Liên quan)*
- [[00_Master_Graph|🕸️ 00_Master_Graph — Bản đồ Tri thức & Đường giăng Dữ liệu Toàn hệ thống]] — **Cosine Similarity: `27.9%`** *(Mức độ: Liên quan)*
- [[datasets/uci_student_performance|📈 Bộ dữ liệu UCI Student Performance (`student-mat` & `student-por`)]] — **Cosine Similarity: `18.3%`** *(Mức độ: Liên quan)*
<!-- VECTOR_LINKS_END -->
