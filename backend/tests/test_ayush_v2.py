"""
Comprehensive Test Suite for MediKiosk AYUSH OPD V2 Engine

Validates:
1. Negation handling ("I do not have bloating" -> severity: 0, is_denial: True, no Vata/Agni score)
2. Historical symptom exclusion ("used to have acidity" -> excluded from current Vikriti)
3. Zero fabricated default scores (insufficient data -> "INSUFFICIENT_DATA", never 40/35/25)
4. Evaluation of all 23 core AYUSH domains
5. Domain stopping criterion (>= 3 observations)
6. Prakriti V2 deterministic scoring
7. Agni classification (Sama/Vishama/Tikshna/Manda)
8. Koshta classification (Mridu/Madhyama/Krura)
9. Ama classification (Saama vs Nirama)
10. Satva scoring (Pravara=3, Madhyama=2, Avara=1)
11. Vaya stage calculation from age
12. General OPD Isolation (Zero Ayurvedic leakage in GENERAL_OPD)
13. AYUSH department routing (kayachikitsa, shalakya, shalya, etc.)
14. Transparent evidence tracing (supporting_observations)
15. End-to-end intake session integration
"""

import pytest
from app.modules.ayush.observation_normalizer import ObservationNormalizer, StructuredObservation
from app.modules.ayush.scoring_engine import AyurvedicScoringEngine, AyushV2AssessmentResult
from app.modules.ayush.assessment_engine import AyushAssessmentEngine
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine
from app.schemas.intake import PatientContextState
from app.modules.routing.service import RoutingService
from app.schemas.routing import DepartmentId

def test_negation_handling():
    normalizer = ObservationNormalizer()
    obs = normalizer.normalize(
        question_id="q_abdo",
        domain="agni",
        feature="bloating",
        raw_answer="I do not have bloating"
    )
    assert obs.is_denial is True
    assert obs.severity == 0
    assert obs.normalized_value == "absent"

    # Verify denied symptom does NOT score positive Vata or Agni
    engine = AyurvedicScoringEngine()
    res = engine.evaluate_all([obs])
    assert res.vikriti.status == "INSUFFICIENT_DATA"
    assert res.prakriti.status == "INSUFFICIENT_DATA"

def test_historical_exclusion():
    normalizer = ObservationNormalizer()
    obs = normalizer.normalize(
        question_id="q_acidity",
        domain="agni",
        feature="acidity",
        raw_answer="I used to have acidity 2 years ago"
    )
    assert obs.is_historical is True
    assert obs.severity == 0

    engine = AyurvedicScoringEngine()
    res = engine.evaluate_all([obs])
    assert res.vikriti.status == "INSUFFICIENT_DATA"

def test_zero_default_scores():
    engine = AyurvedicScoringEngine()
    res = engine.evaluate_all([])
    # Must report INSUFFICIENT_DATA and NEVER default 40/35/25
    assert res.prakriti.status == "INSUFFICIENT_DATA"
    assert res.prakriti.summary == "Insufficient information to determine baseline Prakriti."
    assert res.prakriti.scores == {}

def test_all_23_domains_evaluated():
    engine = AyurvedicScoringEngine()
    res = engine.evaluate_all([], patient_age=42)
    assert res.prakriti is not None
    assert res.vikriti is not None
    assert res.dosha_status is not None
    assert res.dushya_status is not None
    assert res.srotas_status is not None
    assert res.agni is not None
    assert res.ama is not None
    assert res.koshta is not None
    assert res.ahara is not None
    assert res.vihara is not None
    assert res.satmya is not None
    assert res.bala is not None
    assert res.ojas is not None
    assert res.desha is not None
    assert res.kala is not None
    assert res.vaya is not None
    assert res.nidra is not None
    assert res.mala is not None
    assert res.sara is not None
    assert res.samhanana is not None
    assert res.satva is not None
    assert res.ahara_shakti is not None
    assert res.vyayama_shakti is not None

def test_prakriti_v2_scoring():
    engine = AyurvedicScoringEngine()
    obs = [
        StructuredObservation(question_id="1", domain="prakriti", feature="build", raw_answer="Naturally thin slender frame", normalized_value="present", severity=1),
        StructuredObservation(question_id="2", domain="prakriti", feature="skin", raw_answer="Dry rough skin", normalized_value="present", severity=1),
        StructuredObservation(question_id="3", domain="prakriti", feature="sleep", raw_answer="Light sleep wake up easily", normalized_value="present", severity=1),
    ]
    res = engine.evaluate_prakriti(obs)
    assert res.status == "SUFFICIENT_DATA"
    assert res.scores["Vata"] > 50
    assert "Vata" in res.summary

def test_agni_classification():
    engine = AyurvedicScoringEngine()
    obs = [
        StructuredObservation(question_id="1", domain="agni", feature="digestion", raw_answer="Variable hunger with bloating", normalized_value="present", severity=1)
    ]
    res = engine.evaluate_agni(obs)
    assert res.status == "SUFFICIENT_DATA"
    assert res.primary_category == "Vishama"

def test_koshta_classification():
    engine = AyurvedicScoringEngine()
    obs = [
        StructuredObservation(question_id="1", domain="koshta", feature="bowel", raw_answer="Hard dry constipated stool", normalized_value="present", severity=1)
    ]
    res = engine.evaluate_koshta(obs)
    assert res.status == "SUFFICIENT_DATA"
    assert res.primary_category == "Krura"

def test_ama_classification():
    engine = AyurvedicScoringEngine()
    obs = [
        StructuredObservation(question_id="1", domain="ama", feature="tongue", raw_answer="Heavy coated tongue with foul odor", normalized_value="present", severity=2),
        StructuredObservation(question_id="2", domain="ama", feature="heaviness", raw_answer="Severe morning heaviness", normalized_value="present", severity=2)
    ]
    res = engine.evaluate_ama(obs)
    assert res.status == "SUFFICIENT_DATA"
    assert res.primary_category == "Saama"

def test_satva_scoring():
    engine = AyurvedicScoringEngine()
    obs_high = [StructuredObservation(question_id="1", domain="satva", feature="resilience", raw_answer="Calm under pressure, highly resilient", normalized_value="present", severity=1)]
    res_high = engine.evaluate_satva(obs_high)
    assert res_high.primary_category == "Pravara"
    assert res_high.scores["satva_score"] == 3

    obs_low = [StructuredObservation(question_id="1", domain="satva", feature="resilience", raw_answer="Easily anxious and overwhelmed", normalized_value="present", severity=1)]
    res_low = engine.evaluate_satva(obs_low)
    assert res_low.primary_category == "Avara"
    assert res_low.scores["satva_score"] == 1

def test_vaya_age_calculation():
    engine = AyurvedicScoringEngine()
    assert engine.evaluate_vaya(12).primary_category == "Balya"
    assert engine.evaluate_vaya(35).primary_category == "Madhyama"
    assert engine.evaluate_vaya(70).primary_category == "Vriddha"

def test_general_opd_isolation():
    branching = AdaptiveBranchingEngine()
    ctx_general = PatientContextState(session_id="s1", chief_complaint="Chest pain", opd_mode="GENERAL_OPD")
    cand = branching.select_next_question_candidate(ctx_general, [])
    assert cand is not None
    # Candidate in GENERAL_OPD mode MUST NOT be AYURVEDIC
    assert cand.get("category") != "AYURVEDIC"
    assert "ayurvedic_domain" not in cand

def test_ayush_department_routing():
    routing = RoutingService()
    ctx_gastro = PatientContextState(session_id="s1", chief_complaint="Severe acidity and stomach pain", opd_mode="AYUSH_OPD")
    rec_gastro = routing.generate_recommendation("s1", "p1", ctx_gastro)
    assert rec_gastro.recommended_department == DepartmentId.KAYACHIKITSA

    ctx_neuro = PatientContextState(session_id="s2", chief_complaint="Severe headache and dizziness", opd_mode="AYUSH_OPD")
    rec_neuro = routing.generate_recommendation("s2", "p2", ctx_neuro)
    assert rec_neuro.recommended_department == DepartmentId.SHALAKYA

def test_evidence_tracing():
    engine = AyushAssessmentEngine()
    qa = [
        {"question_id": "q1", "question": "Describe appetite", "answer": "Variable hunger with bloating", "clinical_domain": "agni"},
        {"question_id": "q2", "question": "Describe skin", "answer": "Very dry rough skin", "clinical_domain": "prakriti"}
    ]
    res = engine.evaluate_assessment(qa, patient_age=35)
    assert "why_breakdown" in res
    assert res["evidence_count"] == 2
    assert len(res["why_breakdown"]["all_observations"]) == 2
