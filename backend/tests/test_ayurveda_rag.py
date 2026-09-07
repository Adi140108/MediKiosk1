"""
Unit and Integration Tests for Ayurvedic RAG & BharatGenAI AyurParam
====================================================================
Validates:
- AyurGenixAI Dataset grounding (kagglekirti123/ayurgenixai-ayurvedic-dataset)
- BharatGenAI AyurParam LLM integration (bharatgenai/AyurParam)
- Hybrid dense + sparse RAG search
- Multi-symptom complex (chest + joint pain) synthesis
- REST API endpoints (/api/v1/ayurveda/rag/*)
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app")))

from fastapi.testclient import TestClient
from app.main import app
from rag.ayur_rag import AyurvedicRAGEngine
from rag.ayurparam_adapter import AyurParamLLMAdapter

client = TestClient(app)

def test_ayurvedic_dataset_metadata():
    engine = AyurvedicRAGEngine()
    info = engine.get_dataset_info()
    assert info["dataset_name"] == "AyurGenixAI Ayurvedic Dataset"
    assert "kagglekirti123/ayurgenixai-ayurvedic-dataset" in info["dataset_source"]
    assert "bharatgenai/AyurParam" in info["llm_source"]
    assert info["parameters_count"] == 35
    assert info["indexed_records_count"] >= 7

def test_rag_retrieval_cardiology_hridroga():
    engine = AyurvedicRAGEngine()
    results = engine.retrieve_records("chest pain radiating to arm and palpitations", top_k=1)
    assert len(results) > 0
    top = results[0]
    assert "Hridroga" in top["ayurvedic_nidana"] or "Hridshula" in top["ayurvedic_nidana"]
    assert "Vata" in top["dominant_dosha"] or "Pitta" in top["dominant_dosha"]
    assert any("Arjuna" in herb for herb in top["classical_herbs_formulations"])
    assert "Charaka Samhita" in top["classical_reference"]

def test_rag_retrieval_orthopedics_sandhigata():
    engine = AyurvedicRAGEngine()
    results = engine.retrieve_records("knee joint pain morning stiffness and crepitus", top_k=1)
    assert len(results) > 0
    top = results[0]
    assert "Sandhigata" in top["ayurvedic_nidana"] or "Amavata" in top["ayurvedic_nidana"]
    assert "Vata" in top["dominant_dosha"]
    assert any("Guggulu" in herb or "Shallaki" in herb for herb in top["classical_herbs_formulations"])

def test_rag_retrieval_multi_symptom_chest_and_joint():
    engine = AyurvedicRAGEngine()
    results = engine.retrieve_records("chest and joint pain with breathlessness", top_k=1)
    assert len(results) > 0
    top = results[0]
    assert "Hridroga" in top["ayurvedic_nidana"] or "Vata" in top["dominant_dosha"] or "Sannipata" in top["ayurvedic_nidana"]
    assert len(top["pathya"]) > 0
    assert len(top["apathya"]) > 0

def test_ayurparam_adapter_synthesis():
    adapter = AyurParamLLMAdapter()
    profile = adapter.synthesize_ayurvedic_report(
        chief_complaint="Severe retrosternal burning and acid reflux after meals",
        associated_symptoms=["sour belching", "epigastric burning"],
        pain_score=6,
        language="en"
    )
    assert "Pitta" in profile["dominant_dosha"]
    assert "AyurParam" in profile["dataset_source"] or "AyurGenixAI" in profile["dataset_source"]
    assert len(profile["pathya"]) > 0
    assert len(profile["apathya"]) > 0
    assert "ayurparam_reasoning" in profile

def test_api_ayurveda_dataset_info_endpoint():
    resp = client.get("/api/v1/ayurveda/rag/dataset/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "LOADED_AND_READY"
    assert "kagglekirti123" in data["dataset_source"]

def test_api_ayurveda_rag_query_endpoint():
    resp = client.post("/api/v1/ayurveda/rag/query", json={
        "query": "छाती में दर्द और घबराहट",
        "language": "hi",
        "top_k": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["records"]) > 0
    assert data["model_reference"] == "AyurParam (bharatgenai/AyurParam)"

def test_api_ayurveda_rag_evaluate_endpoint():
    resp = client.post("/api/v1/ayurveda/rag/evaluate", json={
        "chief_complaint": "Joint stiffness in knees and backache",
        "associated_symptoms": ["difficulty bending"],
        "pain_level": 7,
        "language": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "dominant_dosha" in data
    assert "agni_status" in data
    assert "classical_reference" in data
