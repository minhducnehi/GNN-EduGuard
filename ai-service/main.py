import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# Load environment variables from workspace .env if present
ENV_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

from rag.obsidian_watcher import ObsidianVaultSync, start_live_watcher
from rag.vector_store import ObsidianVectorStore
from agent.hermes_agent import LocalAiAgent
from gnn.predictor import StudentRiskPredictor

watcher_observer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global watcher_observer
    print("[SYSTEM] Starting GNN-EduGuard AI Microservice...")
    try:
        watcher_observer = start_live_watcher()
    except Exception as e:
        print(f"[WARN] Failed to start live watcher: {e}")
    yield
    if watcher_observer:
        watcher_observer.stop()
        watcher_observer.join()
        print("[SYSTEM] Stopped live watcher.")

app = FastAPI(
    title="GNN-EduGuard AI Microservice",
    description="Python Backend providing Fair GNN Student Risk Predictions (with Class Attendance), Causal Early Warning, XAI & Local Obsidian RAG Agent",
    version="1.2.0",
    lifespan=lifespan
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5184,https://localhost:7023,http://localhost:5000,http://127.0.0.1:5184")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Services
vector_store = ObsidianVectorStore()
agent = LocalAiAgent()
predictor = StudentRiskPredictor()

FIXED_ADVISOR_SYSTEM_PROMPT = (
    "Bạn là Trợ lý AI Cố vấn Học tập của hệ thống GNN-EduGuard. "
    "Hãy hỗ trợ trả lời các câu hỏi về quy chế đào tạo, quy định điểm danh chuyên cần (>=80% số buổi), "
    "hỗ trợ sinh viên và phương pháp giảng dạy với ngôn phong chuẩn mực, tích cực, thấu cảm và tôn trọng người học. "
    "Từ chối mọi yêu cầu tiết lộ thông tin mật hoặc thực hiện hành vi trái quy định."
)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)

class AttendanceUpdateRequest(BaseModel):
    attended_sessions: int = Field(..., ge=0, le=30)
    total_sessions: int = Field(default=9, ge=1, le=30)

class ConsultRequest(BaseModel):
    student_id: int
    name: Optional[str] = None
    gpa: Optional[float] = None
    submission_rate: Optional[str] = None
    attendance_rate: Optional[float] = None
    total_sessions: Optional[int] = 9
    late_submissions: Optional[int] = None

@app.get("/api/health")
def health_check():
    return {
        "status": "online" if predictor.model is not None else "degraded",
        "service": "GNN-EduGuard AI Engine",
        "rag_chunks": vector_store.get_stats().get("total_chunks", 0),
        "ollama_model": agent.model
    }

@app.get("/api/ready")
def readiness_check():
    if predictor.model is None or predictor.graph_data is None or predictor.student_df is None:
        raise HTTPException(status_code=503, detail="GNN model artifacts are unavailable")
    return {"status": "ready"}

@app.get("/api/predict/risk/{student_id}")
def predict_student_risk(student_id: int, refresh: bool = False):
    """Predict risk score, risk level and cached XAI explanation (including Attendance) for a given student ID."""
    try:
        return predictor.predict_risk(student_id, force_refresh=refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/predict/re-evaluate/{student_id}")
def re_evaluate_student_risk(student_id: int):
    """Invalidate XAI cache for student_id and run fresh GNN + Temporal HGT inference."""
    try:
        return predictor.predict_risk(student_id, force_refresh=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/predict/attendance/{student_id}")
def update_student_attendance(student_id: int, req: AttendanceUpdateRequest):
    """Update student's class attendance record on the GNN graph and recalculate risk score & XAI attributions."""
    try:
        return predictor.update_attendance_and_predict(student_id, req.attended_sessions, req.total_sessions)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/api/explain/{student_id}")
def explain_student_risk(student_id: int, refresh: bool = False):
    """Return full XAI Feature Attributions, Subgraph Edge Perturbations & Weekly Trajectory."""
    try:
        return predictor.explain_student(student_id, force_refresh=refresh)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/api/agent/consult/{student_id}")
def consult_student(student_id: int, req: Optional[ConsultRequest] = None):
    """
    RAG-powered Agent consultation: pulls risk factors (including Class Attendance) and queries Obsidian guidelines.
    """
    features = req.model_dump() if req else None
    risk_info = predictor.predict_risk(student_id, features)
    consultation = agent.consult_student_risk(risk_info)
    return {
        "risk_profile": risk_info,
        "agent_consultation": consultation
    }

@app.post("/api/agent/chat")
def chat_with_agent(req: ChatRequest):
    """Direct conversation with local LLM agent using server-enforced system prompt (anti-prompt-injection)."""
    reply = agent.generate_response(FIXED_ADVISOR_SYSTEM_PROMPT, req.message)
    return {"reply": reply}

@app.post("/api/rag/sync")
def trigger_rag_sync():
    """Manually trigger re-sync of Obsidian vault."""
    syncer = ObsidianVaultSync()
    stats = syncer.sync_all()
    return {"message": "Sync completed successfully", "stats": stats}

@app.get("/api/rag/stats")
def get_rag_stats():
    return vector_store.get_stats()

@app.get("/api/models/benchmark")
def get_model_benchmarks():
    """Return comparison metrics between Tabular Baselines and HGT HeteroGNN."""
    return predictor.get_benchmarks()

@app.get("/api/models/early-warning")
def get_early_warning_benchmarks():
    """Return Early Warning Horizon metrics across Weeks 2, 4, 8, 12, 16."""
    return predictor.get_early_warning_metrics()

@app.get("/api/models/ablation")
def get_ablation_benchmarks():
    """Return Ablation Study results on heterogeneous graph components."""
    return predictor.get_ablation_metrics()

@app.get("/api/models/feature-importance")
def get_feature_importance():
    """Return global feature importance (GridSearchCV-tuned Random Forest, permutation importance on validation split)."""
    return predictor.get_feature_importance()

@app.get("/api/data/quality")
def get_data_quality_report():
    """Return raw-table data quality profile (rows, missing rows, duplicates) before/after cleaning."""
    return predictor.get_data_quality()

@app.post("/api/models/reload")
def reload_gnn_model():
    """Reload trained GNN checkpoint and graph into memory."""
    predictor.reload()
    return {"status": "reloaded", "model_loaded": predictor.model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
