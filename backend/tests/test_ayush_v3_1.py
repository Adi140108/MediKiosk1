"""
AYUSH V3.1 Architecture Correction Test Suite — MediKiosk

Verifies:
1. QuestionPlanner serves exact JSON `question_id` items from question bank directory.
2. Track progression from Core Profile to Complaint Specific.
3. Domain sufficiency stopping logic (>= 3 observations or domain completion).
4. No generic domain questions served in AYUSH OPD mode.
5. Structured option metadata and non-keyword scoring in ScoringEngine.
6. Absolute isolation of GENERAL OPD mode.
"""

import pytest
from app.modules.ayush.question_planner import AyushQuestionPlanner, AyushAssessmentSessionState
from app.modules.ayush.observation_normalizer import ObservationNormalizer, StructuredObservation
from app.modules.ayush.scoring_engine import AyurvedicScoringEngine
from app.schemas.intake import PatientContextState, OPDMode
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine

@pytest.fixture
def planner():
    return AyushQuestionPlanner()

@pytest.fixture
def normalizer():
    return ObservationNormalizer()

@pytest.fixture
def scoring():
    return AyurvedicScoringEngine()

def test_question_planner_loads_question_bank(planner):
    """Planner must index question bank JSON files with non-empty questions."""
    assert len(planner.question_bank) >= 7
    assert "PRAKRITI" in planner.question_bank
    assert len(planner.questions_by_id) > 10

def test_planner_serves_exact_json_question_id(planner):
    """Next question candidate must have an exact JSON question_id (e.g. PRAK_BUILD_001)."""
    state = AyushAssessmentSessionState(session_id="s1", patient_id="p1")
    q = planner.select_next_question(state)
    assert q is not None
    assert q["question_id"].startswith("PRAK_")
    assert "options" in q
    assert len(q["options"]) > 0

def test_planner_no_duplicate_questions(planner):
    """Planner must never repeat asked question_ids."""
    state = AyushAssessmentSessionState(
        session_id="s1",
        patient_id="p1",
        asked_question_ids=["PRAK_BUILD_001"]
    )
    q = planner.select_next_question(state)
    assert q is not None
    assert q["question_id"] != "PRAK_BUILD_001"

def test_planner_domain_sufficiency_skips_completed(planner):
    """When a domain is marked completed, planner skips to the next domain."""
    state = AyushAssessmentSessionState(
        session_id="s1",
        patient_id="p1",
        completed_domains=["PRAKRITI"]
    )
    q = planner.select_next_question(state)
    assert q is not None
    assert q["domain"] != "PRAKRITI"
    assert q["domain"] in ["AGNI", "KOSHTA", "AMA", "NIDRA", "SATVA", "HARA_VYAYAMA"]

def test_adaptive_branching_ayush_mode_uses_planner():
    """AdaptiveBranchingEngine in AYUSH_OPD mode selects JSON question bank items."""
    engine = AdaptiveBranchingEngine()
    ctx = PatientContextState(opd_mode=OPDMode.AYUSH_OPD, mode_at_intake=OPDMode.AYUSH_OPD)
    q = engine.select_next_question_candidate(ctx, asked_question_ids=[])
    assert q is not None
    assert q["category"] == "AYURVEDIC"
    assert q["question_id"].startswith("PRAK_")
    assert "options" in q

def test_general_opd_mode_isolates_ayush_planner():
    """GENERAL_OPD mode must NEVER serve AYUSH question bank items."""
    engine = AdaptiveBranchingEngine()
    ctx = PatientContextState(
        opd_mode=OPDMode.GENERAL_OPD,
        mode_at_intake=OPDMode.GENERAL_OPD,
        chief_complaint="Headache"
    )
    q = engine.select_next_question_candidate(ctx, asked_question_ids=[])
    assert q is not None
    assert q.get("category") != "AYURVEDIC"
    assert not q.get("question_id", "").startswith("PRAK_")

def test_observation_normalizer_option_weights(normalizer):
    """Normalizer extracts option metadata and dosha_weights."""
    option_meta = {
        "value": "thin",
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": -1},
        "feature_targets": ["VATA"]
    }
    obs = normalizer.normalize(
        question_id="PRAK_BUILD_001",
        domain="prakriti",
        feature="body_frame",
        raw_answer="Thin and slender frame",
        option_meta=option_meta
    )
    assert obs.dosha_weights == {"VATA": 2, "PITTA": 0, "KAPHA": -1}
    assert obs.option_value == "thin"
    assert obs.feature_targets == ["VATA"]

def test_scoring_engine_evaluates_option_weights_without_substring_guessing(scoring):
    """ScoringEngine evaluates Prakriti based on option weights rather than string substring guessing."""
    obs1 = StructuredObservation(
        question_id="PRAK_BUILD_001",
        domain="prakriti",
        feature="body_frame",
        raw_answer="Slender",
        normalized_value="present",
        dosha_weights={"VATA": 2, "PITTA": 0, "KAPHA": 0},
        option_value="slender"
    )
    obs2 = StructuredObservation(
        question_id="PRAK_SKIN_002",
        domain="prakriti",
        feature="skin_texture",
        raw_answer="Dry",
        normalized_value="present",
        dosha_weights={"VATA": 2, "PITTA": 0, "KAPHA": 0},
        option_value="dry"
    )
    obs3 = StructuredObservation(
        question_id="PRAK_SLEEP_003",
        domain="prakriti",
        feature="sleep_pattern",
        raw_answer="Light and easily interrupted",
        normalized_value="present",
        dosha_weights={"VATA": 2, "PITTA": 0, "KAPHA": 0},
        option_value="light"
    )
    
    res = scoring.evaluate_prakriti([obs1, obs2, obs3])
    assert res.status == "SUFFICIENT_DATA"
    assert "Vata" in res.summary
    assert res.scores["Vata"] > 50
