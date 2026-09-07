"""
Ayurveda RAG API Endpoints
===========================
Provides REST interface to:
- AyurGenixAI Dataset (Kaggle: kagglekirti123/ayurgenixai-ayurvedic-dataset)
- BharatGenAI AyurParam LLM (Hugging Face: bharatgenai/AyurParam)
"""

from typing import List, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from rag.ayur_rag import ayurvedic_rag_engine
from rag.ayurparam_adapter import ayurparam_adapter

router = APIRouter(prefix="/ayurveda", tags=["Ayurveda RAG & AyurParam"])

class AyurvedicRAGQueryRequest(BaseModel):
    query: str = Field(..., description="Symptom text or clinical inquiry")
    language: str = Field("en", description="Language code (en, hi, ta, te, kn, etc.)")
    top_k: int = Field(2, description="Number of knowledge records to retrieve")

class AyurvedicEvaluateRequest(BaseModel):
    chief_complaint: str = Field(..., description="Primary patient symptom or complaint")
    associated_symptoms: Optional[List[str]] = Field(default_factory=list, description="Associated symptoms")
    pain_level: Optional[int] = Field(None, description="Pain score (1-10)")
    language: str = Field("en", description="Language code")

@router.get("/rag/dataset/info")
def get_ayurvedic_dataset_info():
    """
    Returns metadata about the imported AyurGenixAI dataset and BharatGenAI AyurParam LLM.
    """
    return ayurvedic_rag_engine.get_dataset_info()

@router.post("/rag/query")
def query_ayurvedic_rag(req: AyurvedicRAGQueryRequest):
    """
    Performs RAG similarity search on the AyurGenixAI & AyurParam knowledge base.
    """
    records = ayurvedic_rag_engine.retrieve_records(req.query, top_k=req.top_k)
    return {
        "query": req.query,
        "language": req.language,
        "dataset_source": "AyurGenixAI (kagglekirti123/ayurgenixai-ayurvedic-dataset)",
        "model_reference": "AyurParam (bharatgenai/AyurParam)",
        "records": records
    }

@router.post("/rag/evaluate")
def evaluate_ayurvedic_profile(req: AyurvedicEvaluateRequest):
    """
    Generates a full Ayurvedic clinical synthesis using AyurGenixAI dataset & AyurParam reasoning.
    """
    result = ayurparam_adapter.synthesize_ayurvedic_report(
        chief_complaint=req.chief_complaint,
        associated_symptoms=req.associated_symptoms,
        pain_score=req.pain_level,
        language=req.language
    )
    return result
