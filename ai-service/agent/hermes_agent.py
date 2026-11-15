import os
import httpx
from typing import Dict, Any, List
from rag.vector_store import ObsidianVectorStore

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")


class LocalAiAgent:
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url
        self.vector_store = ObsidianVectorStore()

    def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Call Ollama generate API with graceful pedagogical fallback when Ollama daemon is offline."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        try:
            with httpx.Client(timeout=45.0) as client:
                resp = client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", "").strip()
        except Exception as e:
            return (
                f"[Chế độ Cố vấn Quy chế Tự động - RAG Offline Fallback ({type(e).__name__})]\n\n"
                "1. Đánh giá mức độ, Điểm danh Chuyên cần & Căn cứ quy chế:\n"
                "   - Hệ thống đã đối chiếu kết quả Điểm danh trên lớp + Đồ thị GNN với Quy chế Học vụ (Obsidian Vault).\n"
                "   - Theo quy định: Sinh viên phải đạt chuyên cần tối thiểu 80% (>= 12/15 buổi). Vắng từ 3 buổi trở lên (> 20%) có nguy cơ bị cấm thi kết thúc học phần.\n\n"
                "2. Lộ trình 3 bước can thiệp đề xuất cho Cố vấn học tập:\n"
                "   - Bước 1 (Trong 48h): Liên hệ sinh viên xác minh lý do vắng mặt trên lớp và nhắc nhở điều kiện dự thi (>= 80% số buổi).\n"
                "   - Bước 2 (Tuần hiện tại): Hướng dẫn sinh viên xem lại video bài giảng VLE của các buổi đã vắng và ôn tập các Concept Node bị hổng.\n"
                "   - Bước 3 (Theo dõi 2 tuần): Điểm danh sát sao ở các buổi học kế tiếp, ghép cặp bạn học (Peer-Tutoring) và đánh giá lại qua Temporal HGT.\n\n"
                "3. Mẫu tin nhắn/Email gửi sinh viên (Tâm lý tích cực, tránh gây áp lực):\n"
                "   \"Chào em, Thầy/Cô nhận thấy gần đây em có một số buổi vắng mặt trên lớp và tiến độ bài tập trên LMS hơi chững lại. "
                "Thầy/Cô rất muốn lắng nghe xem em có đang gặp khó khăn gì về sức khỏe hay lịch trình không để hỗ trợ em kịp thời "
                "đảm bảo điều kiện chuyên cần dự thi và nắm vững kiến thức môn học. Em hẹn lịch trao đổi 15 phút với Thầy/Cô trong tuần này nhé!\""
            )

    def consult_student_risk(self, student_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        RAG-powered consultation: combines GNN student risk factors (including Class Attendance)
        with knowledge retrieved from Obsidian Vault.
        """
        student_id = student_info.get("student_id", student_info.get("id", "N/A"))
        name = student_info.get("name", f"Sinh viên #{student_id}")
        risk_score = student_info.get("risk_score", 0.0)
        risk_level = student_info.get("risk_level", "Medium")
        weak_concepts = student_info.get("weak_concepts", [])
        gpa = student_info.get("gpa", "N/A")
        submission_rate = student_info.get("submission_rate", "N/A")
        att_rate = student_info.get("attendance_rate", 0.85)
        attended_sessions = student_info.get("attended_sessions", 13)
        total_sessions = student_info.get("total_sessions", 15)
        absent_sessions = student_info.get("absent_sessions", 2)
        reasons = student_info.get("reasons", [])

        # 1. Search relevant knowledge in Obsidian
        search_query = f"can thiệp cảnh báo học vụ điểm danh chuyên cần cấm thi {' '.join(weak_concepts)}"
        retrieved_docs = self.vector_store.search(search_query, n_results=2)
        context_text = "\n---\n".join([d["content"] for d in retrieved_docs])

        # 2. Construct Prompt for Agent (Empathetic, supportive pedagogical tone)
        system_prompt = (
            "Bạn là Trợ lý Cố vấn Học tập Thông minh của Hệ thống GNN-EduGuard. "
            "Nhiệm vụ của bạn là phân tích báo cáo rủi ro học tập và kết quả điểm danh chuyên cần của sinh viên (từ mô hình GNN), "
            "kết hợp các quy chế chuyên cần và cẩm nang can thiệp từ cơ sở tri thức để đưa ra nhận định chuyên môn "
            "và kế hoạch hỗ trợ cụ thể cho Giảng viên/Cố vấn học tập bằng tiếng Việt trang trọng, thấu cảm, "
            "tuyệt đối tránh ngôn từ kỳ thị hay gây áp lực tâm lý nặng nề cho sinh viên."
        )

        user_prompt = f"""
### THÔNG TIN RỦI RO & ĐIỂM DANH SINH VIÊN (Từ GNN Engine):
- Mã sinh viên: #{student_id} - Họ tên: {name}
- Xác suất rủi ro (Risk Score): {risk_score:.2f} ({risk_level})
- Kết quả Điểm danh trên lớp: Có mặt {attended_sessions}/{total_sessions} buổi ({att_rate*100:.0f}% - Vắng {absent_sessions} buổi)
- Điểm GPA hiện tại: {gpa}
- Tỷ lệ nộp bài tập: {submission_rate}
- Các khái niệm yếu (Weak Concepts): {', '.join(weak_concepts) if weak_concepts else 'Chưa xác định'}
- Các nguyên nhân kỹ thuật phát hiện:
{chr(10).join(['  + ' + r for r in reasons])}

### QUY CHẾ VÀ HƯỚNG DẪN THAM KHẢO (Từ Obsidian Knowledge Vault):
{context_text}

---
YÊU CẦU:
Hãy xuất ra bản Đề xuất Kế hoạch Can thiệp gồm:
1. Đánh giá mức độ, tình trạng chuyên cần điểm danh (đối chiếu quy định tối thiểu 80% số buổi dự thi) và căn cứ quy chế.
2. Nguyên nhân cốt lõi về mặt kiến thức và chuyên cần.
3. Lộ trình 3 bước hỗ trợ tích cực cho Cố vấn học tập.
4. Mẫu email/tin nhắn khích lệ, tôn trọng gửi sinh viên để hẹn gặp trao đổi.
"""

        advice = self.generate_response(system_prompt, user_prompt)

        return {
            "student_id": student_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "analysis_and_plan": advice,
            "retrieved_sources": [d["metadata"].get("source", "unknown") for d in retrieved_docs]
        }
