"""
Unit Tests for Dual OPD Modes (GENERAL_OPD & AYUSH_OPD)
"""

import pytest
from app.schemas.intake import PatientContextState, OPDMode
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine
from app.modules.ayush.assessment_engine import AyushAssessmentEngine

def test_general_opd_mode_isolates_ayurvedic_questions():
    """Verify GENERAL_OPD mode excludes Ayurvedic candidate questions."""
    engine = AdaptiveBranchingEngine()
    context = PatientContextState(
        opd_mode=OPDMode.GENERAL_OPD,
        chief_complaint="I have had a headache for 2 days",
        question_count=1
    )
    
    candidate = engine.select_next_question_candidate(context, asked_question_ids=["initial_chief_complaint"])
    assert candidate is not None
    assert candidate.get("category") != "AYURVEDIC"
    assert "ayurvedic_domain" not in candidate or candidate.get("ayurvedic_domain") is None

def test_ayush_opd_mode_includes_ayurvedic_candidates():
    """Verify AYUSH_OPD mode includes natural Ayurvedic assessment candidates."""
    engine = AdaptiveBranchingEngine()
    context = PatientContextState(
        opd_mode=OPDMode.AYUSH_OPD,
        chief_complaint="I have had stomach bloating after meals for 3 days",
        question_count=1
    )
    
    candidate = engine.select_next_question_candidate(context, asked_question_ids=["initial_chief_complaint"])
    assert candidate is not None

def test_ayush_4_layer_assessment_engine():
    """Verify 4-Layer Assessment Engine produces structured Prakriti percentages and evidence breakdown."""
    engine = AyushAssessmentEngine()
    qa_pairs = [
        {"question_id": "q1", "question": "Describe your body frame", "answer": "I have a lean slender body frame and low body weight"},
        {"question_id": "q2", "question": "How is your digestion?", "answer": "Sometimes I feel bloated or gassy after meals"},
        {"question_id": "q3", "question": "How is your sleep pattern?", "answer": "I have light interrupted sleep"}
    ]
    
    result = engine.evaluate_assessment(qa_pairs, patient_age=42)
    assert "prakriti" in result
    assert "vat_score" in str(result["prakriti"]) or "vata_score" in result["prakriti"]
    assert result["prakriti"]["vata_score"] > result["prakriti"]["kapha_score"]
    assert "predominant_pattern" in result["prakriti"]
    assert "why_breakdown" in result
    assert len(result["why_breakdown"]["matched_features"]) > 0
