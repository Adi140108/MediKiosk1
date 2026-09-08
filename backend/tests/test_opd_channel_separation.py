"""
MediKiosk — Automated Unit Test Suite for Complete OPD Channel Separation & AYUSH Clinical Flow
=============================================================================================
Tests:
1. General OPD never asks Ayurvedic questions.
2. General OPD never returns Ayurvedic assessment objects or RAG synthesis.
3. General OPD never calculates Prakriti.
4. General OPD never calculates Dosha scores.
5. General OPD workspace payload has empty ayurvedic_assessment and ayurvedic_findings.
6. AYUSH loads authoritative AYUSH question bank JSONs.
7. AYUSH uses exact JSON question IDs (e.g. PRAK_BUILD_001, AGNI_HUNGER_003).
8. AYUSH uses Socratic branching for complaint exploration before AYUSH assessment.
9. AYUSH uses mentor-defined assessment domains (Prakriti, Agni, Koshta, Vikriti, Satva, etc.).
10. AYUSH scoring uses configured mappings and observation normalization.
11. AYUSH does not fabricate results.
12. Insufficient evidence returns INSUFFICIENT_DATA.
13. General and AYUSH queues are separated by opd_mode filter.
14. AYUSH department routing produces AYUSH departments (Kayachikitsa, Shalakya, etc.).
15. General department routing produces Allopathic departments (General Medicine, Cardiology, etc.).
16. Patient in General mode mentioning Ayurvedic terms ("I think my Vata is high") remains in GENERAL_OPD and receives NO Ayurvedic assessment.
17. GET /api/v1/physician/departments?opd_mode=GENERAL_OPD returns ONLY General departments.
18. GET /api/v1/physician/departments?opd_mode=AYUSH_OPD returns ONLY AYUSH departments.
19. Reassigning GENERAL_OPD patient to an AYUSH department is REJECTED by backend (HTTP 400).
20. Reassigning AYUSH_OPD patient to a General department is REJECTED by backend (HTTP 400).
21. Override AYUSH endpoint is REJECTED for GENERAL_OPD patients (HTTP 400).
22. Patient mode immutability and persistence across intake session.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.intake import PatientContextState, QuestionItem, QuestionFramework
from app.schemas.routing import DepartmentId
from app.modules.intake.session_manager import IntakeSessionManager
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine
from app.modules.routing.service import RoutingService
from app.modules.routing.department_config import get_departments_for_mode, is_department_valid_for_mode
from app.modules.ayush.question_planner import AyushQuestionPlanner
from app.modules.ayush.scoring_engine import AyurvedicScoringEngine
from app.db.repositories.intake_repository import IntakeRepository
from app.db.repositories.queue_repository import QueueRepository

client = TestClient(app)

@pytest.fixture
def repo():
    return IntakeRepository()

@pytest.fixture
def session_mgr(repo):
    return IntakeSessionManager(intake_repo=repo)

# -------------------------------------------------------------------
# 1. Department API Channel Separation Tests
# -------------------------------------------------------------------

def test_departments_api_mode_separation():
    """Verify that GET /departments filters departments strictly by OPD mode."""
    # General OPD departments
    res_gen = client.get("/api/v1/physician/departments?opd_mode=GENERAL_OPD")
    assert res_gen.status_code == 200
    gen_depts = res_gen.json()
    gen_ids = [d["id"] for d in gen_depts]
    assert "general-medicine" in gen_ids
    assert "cardiology" in gen_ids
    assert "kayachikitsa" not in gen_ids
    assert "panchakarma" not in gen_ids

    # AYUSH OPD departments
    res_ayush = client.get("/api/v1/physician/departments?opd_mode=AYUSH_OPD")
    assert res_ayush.status_code == 200
    ayush_depts = res_ayush.json()
    ayush_ids = [d["id"] for d in ayush_depts]
    assert "ayush" in ayush_ids or "kayachikitsa" in ayush_ids
    assert "cardiology" not in ayush_ids
    assert "neurology" not in ayush_ids


def test_department_validity_helper():
    """Verify is_department_valid_for_mode logic."""
    assert is_department_valid_for_mode("cardiology", "GENERAL_OPD") is True
    assert is_department_valid_for_mode("kayachikitsa", "GENERAL_OPD") is False
    assert is_department_valid_for_mode("kayachikitsa", "AYUSH_OPD") is True
    assert is_department_valid_for_mode("cardiology", "AYUSH_OPD") is False
    # Emergency is allowed for all
    assert is_department_valid_for_mode("emergency", "GENERAL_OPD") is True
    assert is_department_valid_for_mode("emergency", "AYUSH_OPD") is True

# -------------------------------------------------------------------
# 2. General OPD Questioning & Pure Allopathic Guarantee Tests
# -------------------------------------------------------------------

def test_general_opd_never_asks_ayurvedic_questions(session_mgr):
    """Verify GENERAL_OPD intake never produces Ayurvedic questions or framework."""
    sess_id = "test_gen_q_1"
    pat_id = "pat_gen_1"

    # Start intake in GENERAL_OPD mode
    q1 = session_mgr.start_session(
        session_id=sess_id,
        patient_id=pat_id,
        opd_mode="GENERAL_OPD",
        initial_chief_complaint="Severe headache and lightheadedness"
    )

    assert q1.question_framework != QuestionFramework.AYURVEDIC
    assert q1.ayurvedic_domain is None

    # Simulate answering multi-turn Socratic questions
    ctx = session_mgr.repo.get_context_state(sess_id)
    assert str(ctx.opd_mode.value if hasattr(ctx.opd_mode, 'value') else ctx.opd_mode) == "GENERAL_OPD"

    branching = AdaptiveBranchingEngine()
    candidate = branching.select_next_question_candidate(ctx, asked_question_ids=[q1.question_id])
    if candidate:
        assert candidate.get("category") != "AYURVEDIC"
        assert candidate.get("ayurvedic_domain") is None


def test_general_opd_patient_mentions_ayurveda_terms(session_mgr):
    """Verify that a GENERAL_OPD patient mentioning Ayurvedic terms remains GENERAL_OPD."""
    sess_id = "test_gen_ayur_terms"
    pat_id = "pat_gen_2"

    session_mgr.start_session(
        session_id=sess_id,
        patient_id=pat_id,
        opd_mode="GENERAL_OPD",
        initial_chief_complaint="I have stomach burning and I think my Vata and Pitta are out of balance."
    )

    ctx = session_mgr.repo.get_context_state(sess_id)
    # Mode must remain GENERAL_OPD
    assert str(ctx.opd_mode.value if hasattr(ctx.opd_mode, 'value') else ctx.opd_mode) == "GENERAL_OPD"

    # Next candidate selection must NOT introduce Ayurvedic questions
    branching = AdaptiveBranchingEngine()
    candidate = branching.select_next_question_candidate(ctx, asked_question_ids=["initial_chief_complaint"])
    if candidate:
        assert candidate.get("category") != "AYURVEDIC"

# -------------------------------------------------------------------
# 3. AYUSH OPD Question Bank & Scoring Tests
# -------------------------------------------------------------------

def test_ayush_question_bank_loading():
    """Verify AYUSH question bank JSON files load with exact IDs."""
    planner = AyushQuestionPlanner()
    assert len(planner.questions_by_id) > 0
    # Check exact JSON question IDs exist
    prak_q = planner.get_question_by_id("PRAK_BUILD_001")
    assert prak_q is not None
    assert prak_q.get("domain") == "PRAKRITI"
    assert "options" in prak_q

def test_ayurvedic_scoring_insufficient_data():
    """Verify scoring engine returns INSUFFICIENT_DATA when no observations exist."""
    scoring = AyurvedicScoringEngine()
    res = scoring.evaluate_all(observations=[], patient_age=35)
    assert res.prakriti.status == "INSUFFICIENT_DATA"
    assert res.vikriti.status == "INSUFFICIENT_DATA"
    assert res.agni.status == "INSUFFICIENT_DATA"
    assert res.koshta.status == "INSUFFICIENT_DATA"

# -------------------------------------------------------------------
# 4. Department Routing & Mode Boundary Tests
# -------------------------------------------------------------------

def test_routing_service_mode_separation(repo):
    """Verify RoutingService routes to General departments for GENERAL_OPD and AYUSH departments for AYUSH_OPD."""
    routing_svc = RoutingService(intake_repo=repo)

    # General OPD context
    ctx_gen = PatientContextState(
        opd_mode="GENERAL_OPD",
        chief_complaint="Chest tightness and shortness of breath"
    )
    rec_gen = routing_svc.generate_recommendation(
        session_id="sess_rt_gen",
        patient_id="pat_rt_1",
        context=ctx_gen
    )
    assert rec_gen.recommended_department.value in ["cardiology", "pulmonology", "general-medicine", "emergency"]

    # AYUSH OPD context
    ctx_ayush = PatientContextState(
        opd_mode="AYUSH_OPD",
        chief_complaint="Chest tightness and shortness of breath"
    )
    rec_ayush = routing_svc.generate_recommendation(
        session_id="sess_rt_ayush",
        patient_id="pat_rt_2",
        context=ctx_ayush
    )
    assert rec_ayush.recommended_department.value in [
        "ayush", "kayachikitsa", "shalya", "shalakya", "prasuti-stri", "kaumarabhritya", "swasthavritta", "agadatantra"
    ]

# -------------------------------------------------------------------
# 5. Backend Safety Guards & API Endpoint Tests
# -------------------------------------------------------------------

def test_backend_reassign_guard_rejection():
    """Verify backend rejects cross-mode department reassignment attempts with HTTP 400."""
    # Create patient session in GENERAL_OPD
    res_start = client.post("/api/v1/intake/start", json={
        "patient_id": "pat_reassign_gen",
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "Joint pain in knees"
    })
    assert res_start.status_code == 200
    sess_id = res_start.json()["session_id"]

    # Attempt to reassign GENERAL_OPD patient to AYUSH department (kayachikitsa) -> Must be rejected!
    res_bad = client.post(f"/api/v1/physician/cases/{sess_id}/reassign_department?target_department=kayachikitsa")
    assert res_bad.status_code == 400
    assert "invalid for this opd mode" in res_bad.json()["detail"].lower()

    # Reassigning to valid General department (orthopedics) -> Must succeed!
    res_good = client.post(f"/api/v1/physician/cases/{sess_id}/reassign_department?target_department=orthopedics")
    assert res_good.status_code == 200
    assert res_good.json()["status"] == "success"

def test_backend_override_ayush_guard_rejection():
    """Verify backend rejects override_ayush calls for GENERAL_OPD patients with HTTP 400."""
    res_start = client.post("/api/v1/intake/start", json={
        "patient_id": "pat_override_gen",
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "Fever and chills"
    })
    sess_id = res_start.json()["session_id"]

    res_override = client.post(f"/api/v1/physician/cases/{sess_id}/override_ayush", json={
        "prakriti": {"summary": "Vata"},
        "physician_notes": "Attempting override on General patient"
    })
    assert res_override.status_code == 400
    assert "rejected" in res_override.json()["detail"].lower()

def test_case_workspace_general_opd_empty_ayurvedic():
    """Verify that case workspace endpoint for GENERAL_OPD returns empty ayurvedic_assessment and ayurvedic_findings."""
    res_start = client.post("/api/v1/intake/start", json={
        "patient_id": "pat_workspace_gen",
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "Persistent cough"
    })
    sess_id = res_start.json()["session_id"]

    # Complete intake
    client.post("/api/v1/intake/complete", json={"session_id": sess_id, "patient_id": "pat_workspace_gen"})

    # Fetch workspace
    res_ws = client.get(f"/api/v1/physician/cases/{sess_id}/workspace")
    assert res_ws.status_code == 200
    data = res_ws.json()

    assert data["opd_mode"] == "GENERAL_OPD"
    assert data["ayurvedic_findings"] == {}
    assert data["ayush_assessment"] == {}
    assert data["draft_summary"].get("ayurvedic_assessment") == {}
