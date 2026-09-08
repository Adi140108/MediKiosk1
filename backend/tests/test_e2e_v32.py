"""
MediKiosk V3.2.0 Integration & E2E Test Suite

Tests complete execution paths:
1. GENERAL_OPD: UI/API -> session -> Socratic planner -> answer -> zero AYUSH -> General routing -> General dashboard.
2. AYUSH_OPD: UI/API -> session -> Socratic complaint -> AYUSH question bank -> structured answer -> stored AYUSH assessment -> AYUSH routing -> AYUSH dashboard.
3. Cross-mode boundary enforcement:
   - General patient mentioning "Vata" remains GENERAL_OPD.
   - Mismatched department reassignment attempts are rejected.
   - Ambiguous routing falls back to AYUSH_UNSPECIFIED or GENERAL_UNSPECIFIED without silent guessing.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.schemas.intake import OPDMode
from app.schemas.routing import DepartmentId
from app.modules.routing.department_config import is_department_valid_for_mode

client = TestClient(app)

def test_general_opd_end_to_end_flow():
    """Verify complete GENERAL_OPD channel execution path."""
    # 1. Register Patient
    reg_resp = client.post("/api/v1/patients/register", json={
        "name": "General Test Patient",
        "age": 42,
        "gender": "MALE",
        "mobile": "+919876543210"
    })
    assert reg_resp.status_code == 200
    patient_id = reg_resp.json()["patient_id"]

    # 2. Start Intake in GENERAL_OPD mode
    start_resp = client.post("/api/v1/intake/start", json={
        "patient_id": patient_id,
        "language": "en",
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "Severe stomach pain right after eating"
    })
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    first_q = start_data["question"]
    
    assert first_q.get("question_framework") != "AYURVEDIC"
    assert not first_q.get("question_id", "").startswith("PRAK_")

    # 3. Answer Socratic Questions
    ans_resp = client.post("/api/v1/intake/answer", json={
        "session_id": session_id,
        "question_id": first_q["question_id"],
        "answer": "It burns in upper stomach and gets worse after greasy food."
    })
    assert ans_resp.status_code == 200
    ans_data = ans_resp.json()
    next_q = ans_data.get("next_question")
    if next_q:
        assert next_q.get("question_framework") != "AYURVEDIC"
        assert not next_q.get("question_id", "").startswith("PRAK_")

    # 4. Complete Intake
    comp_resp = client.post("/api/v1/intake/complete", json={
        "session_id": session_id,
        "patient_id": patient_id
    })
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    rec_dept = comp_data["routing"]["recommended_department"]
    assert is_department_valid_for_mode(rec_dept, "GENERAL_OPD")
    assert rec_dept != "kayachikitsa"

    # 5. Fetch Physician Workspace & verify complete isolation
    work_resp = client.get(f"/api/v1/physician/cases/{session_id}/workspace")
    assert work_resp.status_code == 200
    work_data = work_resp.json()

    assert work_data["opd_mode"] == "GENERAL_OPD"
    assert work_data["ayush_assessment"] == {}
    assert work_data["ayurvedic_findings"] == {}


def test_ayush_opd_end_to_end_flow():
    """Verify complete AYUSH_OPD channel execution path."""
    # 1. Register Patient
    reg_resp = client.post("/api/v1/patients/register", json={
        "name": "Ayush Test Patient",
        "age": 35,
        "gender": "FEMALE",
        "mobile": "+919876543211"
    })
    assert reg_resp.status_code == 200
    patient_id = reg_resp.json()["patient_id"]

    # 2. Start Intake in AYUSH_OPD mode
    start_resp = client.post("/api/v1/intake/start", json={
        "patient_id": patient_id,
        "language": "en",
        "opd_mode": "AYUSH_OPD",
        "chief_complaint": "Chronic indigestion and irregular bowel movements"
    })
    assert start_resp.status_code == 200
    start_data = start_resp.json()
    session_id = start_data["session_id"]
    first_q = start_data["question"]

    # 3. Answer questions until AYUSH question planner serves structured AYUSH questions
    q_curr = first_q
    for _ in range(5):
        if not q_curr:
            break
        ans_resp = client.post("/api/v1/intake/answer", json={
            "session_id": session_id,
            "question_id": q_curr["question_id"],
            "answer": "Option dry skin and irregular hunger"
        })
        assert ans_resp.status_code == 200
        q_curr = ans_resp.json().get("next_question")

    # 4. Complete Intake
    comp_resp = client.post("/api/v1/intake/complete", json={
        "session_id": session_id,
        "patient_id": patient_id
    })
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()

    rec_dept = comp_data["routing"]["recommended_department"]
    assert is_department_valid_for_mode(rec_dept, "AYUSH_OPD")

    # 5. Fetch Physician Workspace & verify stored AYUSH assessment display
    work_resp = client.get(f"/api/v1/physician/cases/{session_id}/workspace")
    assert work_resp.status_code == 200
    work_data = work_resp.json()

    assert work_data["opd_mode"] == "AYUSH_OPD"
    assert "ayush_assessment" in work_data
    assert work_data["ayush_assessment"] != {}


def test_general_patient_mentioning_ayurvedic_terms_remains_general():
    """General patient mentioning 'Vata' or 'Ayurveda' must remain GENERAL_OPD."""
    reg_resp = client.post("/api/v1/patients/register", json={
        "name": "Vata Mention Patient",
        "age": 50,
        "gender": "FEMALE",
        "mobile": "+919876543212"
    })
    patient_id = reg_resp.json()["patient_id"]

    start_resp = client.post("/api/v1/intake/start", json={
        "patient_id": patient_id,
        "language": "en",
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "I think my Vata is high and causing severe joint pain"
    })
    session_id = start_resp.json()["session_id"]

    comp_resp = client.post("/api/v1/intake/complete", json={
        "session_id": session_id,
        "patient_id": patient_id
    })
    rec_dept = comp_resp.json()["routing"]["recommended_department"]

    assert rec_dept in [DepartmentId.ORTHOPEDICS.value, DepartmentId.GENERAL_MEDICINE.value, DepartmentId.GENERAL_UNSPECIFIED.value]
    assert rec_dept != "kayachikitsa"


def test_department_reassignment_mode_validation():
    """Backend must reject transferring a General patient to an AYUSH department or vice-versa."""
    # Create General patient
    reg_resp = client.post("/api/v1/patients/register", json={
        "name": "Transfer Patient",
        "age": 28,
        "gender": "MALE",
        "mobile": "+919876543213"
    })
    patient_id = reg_resp.json()["patient_id"]

    start_resp = client.post("/api/v1/intake/start", json={
        "patient_id": patient_id,
        "opd_mode": "GENERAL_OPD",
        "chief_complaint": "Mild fever and cough"
    })
    session_id = start_resp.json()["session_id"]

    client.post("/api/v1/intake/complete", json={
        "session_id": session_id,
        "patient_id": patient_id
    })

    # Attempt to reassign General patient to Kayachikitsa -> MUST BE REJECTED (HTTP 400)
    reassign_resp = client.post(
        f"/api/v1/physician/cases/{session_id}/reassign_department?target_department=kayachikitsa"
    )
    assert reassign_resp.status_code == 400
    assert "Department is invalid for this OPD mode" in reassign_resp.json()["detail"]


def test_unspecified_department_fallback():
    """Unmapped AYUSH routing must yield AYUSH_UNSPECIFIED (never Kayachikitsa)."""
    reg_resp = client.post("/api/v1/patients/register", json={
        "name": "Unspecified Patient",
        "age": 30,
        "gender": "MALE",
        "mobile": "+919876543214"
    })
    patient_id = reg_resp.json()["patient_id"]

    start_resp = client.post("/api/v1/intake/start", json={
        "patient_id": patient_id,
        "opd_mode": "AYUSH_OPD",
        "chief_complaint": "Non-specific malaise and vague discomfort"
    })
    session_id = start_resp.json()["session_id"]

    comp_resp = client.post("/api/v1/intake/complete", json={
        "session_id": session_id,
        "patient_id": patient_id
    })
    rec_dept = comp_resp.json()["routing"]["recommended_department"]
    assert rec_dept == DepartmentId.AYUSH_UNSPECIFIED.value
