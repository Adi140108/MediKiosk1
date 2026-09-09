from fastapi.testclient import TestClient
from app.main import app

def test_full_flow():
    client = TestClient(app)
    # 1. Health check
    res = client.get("/api/v1/health")
    print(f"[1] Health check status: {res.status_code}, response: {res.json()}")
    assert res.status_code == 200

    # 2. Test Pediatric Patient (Age 7)
    ped_reg = {
        "name": "Aarav Sharma (Child)",
        "age": 7,
        "gender": "MALE",
        "phone": "+919876543210",
        "preferred_language": "en",
        "is_attendant_assisted": True
    }
    res = client.post("/api/v1/patients/register", json=ped_reg)
    print(f"[2] Pediatric registration status: {res.status_code}")
    assert res.status_code == 200
    ped_patient = res.json()
    ped_patient_id = ped_patient["patient_id"]

    # Start intake
    res = client.post("/api/v1/intake/start", json={"patient_id": ped_patient_id, "language": "en"})
    assert res.status_code == 200
    ped_start = res.json()
    ped_session_id = ped_start["session_id"]
    q1 = ped_start["question"]

    # Answer question
    res = client.post("/api/v1/intake/answer", json={
        "session_id": ped_session_id,
        "question_id": q1["question_id"],
        "answer": "Mild cough and runny nose for 2 days"
    })
    assert res.status_code == 200

    # Complete intake
    res = client.post("/api/v1/intake/complete", json={
        "session_id": ped_session_id,
        "patient_id": ped_patient_id
    })
    assert res.status_code == 200
    ped_complete = res.json()
    ped_dept = ped_complete.get("routing", {}).get("recommended_department")
    print(f"[2] Pediatric (Age 7) Department Assigned: {ped_dept}")
    assert ped_dept == "pediatrics", f"Expected pediatrics, got {ped_dept}"

    # 3. Test Adult with Mild/General Symptoms (Age 35)
    adult_reg = {
        "name": "Sneha Patel",
        "age": 35,
        "gender": "FEMALE",
        "phone": "+919876543211",
        "preferred_language": "en"
    }
    res = client.post("/api/v1/patients/register", json=adult_reg)
    assert res.status_code == 200
    adult_patient = res.json()
    adult_patient_id = adult_patient["patient_id"]

    # Start adult intake
    res = client.post("/api/v1/intake/start", json={"patient_id": adult_patient_id, "language": "en"})
    assert res.status_code == 200
    adult_start = res.json()
    adult_session_id = adult_start["session_id"]
    aq1 = adult_start["question"]

    # Answer adult question
    res = client.post("/api/v1/intake/answer", json={
        "session_id": adult_session_id,
        "question_id": aq1["question_id"],
        "answer": "Feeling tired with a mild headache since yesterday morning, normal cold symptoms"
    })
    assert res.status_code == 200

    # Complete adult intake
    res = client.post("/api/v1/intake/complete", json={
        "session_id": adult_session_id,
        "patient_id": adult_patient_id
    })
    assert res.status_code == 200
    adult_complete = res.json()
    adult_dept = adult_complete.get("routing", {}).get("recommended_department")
    print(f"[3] Adult (Age 35, mild symptoms) Department Assigned: {adult_dept}")
    assert adult_dept == "general-medicine", f"Expected general-medicine, got {adult_dept}"

    # 4. Test Physician Case Workspace retrieval (checks 'is_draft' & full structure)
    res = client.get(f"/api/v1/physician/patient/{adult_session_id}")
    print(f"[4] Physician Case Workspace status: {res.status_code}")
    assert res.status_code == 200
    workspace = res.json()
    print(f"    - Patient Name: {workspace.get('patient', {}).get('full_name')}")
    print(f"    - Draft Summary is_draft: {workspace.get('draft_summary', {}).get('is_draft')}")
    print(f"    - Assigned Department: {workspace.get('queue_item', {}).get('assigned_department')}")

    # 5. Test Doctor Department Reassignment (e.g. from general-medicine -> cardiology)
    reassign_res = client.post(
        f"/api/v1/physician/cases/{adult_session_id}/reassign_department",
        params={
            "target_department": "cardiology",
            "physician_id": "dr_kapoor_general",
            "reason": "Patient mentioned palpitations during clinical intake review"
        }
    )
    print(f"[5] Reassign Department status: {reassign_res.status_code}, response: {reassign_res.json()}")
    assert reassign_res.status_code == 200
    assert reassign_res.json()["assigned_department"] == "cardiology"

    # Verify new queue in cardiology
    res = client.get("/api/v1/physician/queue/cardiology")
    assert res.status_code == 200
    cardio_queue = res.json()
    cardio_sessions = [item["session_id"] for item in cardio_queue]
    print(f"[5] Cardiology Queue Sessions: {cardio_sessions}")
    assert adult_session_id in cardio_sessions

    # 6. Test Doctor Sign-Off Decision
    decision_payload = {
        "physician_id": "dr_sharma_cardio",
        "decision_type": "CONFIRM_TRANSFER",
        "final_department": "cardiology",
        "final_priority": "MEDIUM",
        "physician_notes": "Reviewed ECG and vitals; transferred to cardiology observation.",
        "override_reason": "Specialist evaluation required"
    }
    dec_res = client.post(f"/api/v1/physician/cases/{adult_session_id}/decision", json=decision_payload)
    print(f"[6] Doctor Decision Sign-off status: {dec_res.status_code}, response: {dec_res.json()}")
    assert dec_res.status_code == 200

    # 7. Test Emergency Escalation
    esc_res = client.post(
        f"/api/v1/physician/cases/{adult_session_id}/reassign_department",
        params={
            "target_department": "emergency",
            "physician_id": "dr_sharma_cardio",
            "reason": "Acute hemodynamic collapse during observation"
        }
    )
    print(f"[7] Escalate to Emergency status: {esc_res.status_code}, response: {esc_res.json()}")
    assert esc_res.status_code == 200
    assert esc_res.json()["assigned_department"] == "emergency"

    # Verify patient is in Emergency queue with CRITICAL severity
    em_res = client.get("/api/v1/physician/queue/emergency")
    assert em_res.status_code == 200
    em_queue = em_res.json()
    em_item = next((it for it in em_queue if it["session_id"] == adult_session_id), None)
    assert em_item is not None
    print(f"[7] Emergency Queue Item Severity: {em_item.get('overall_severity')}")
    assert em_item.get("overall_severity") == "CRITICAL"

    print("\n ALL VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_full_flow()
