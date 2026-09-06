import uuid
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.schemas.physician import (
    PriorityQueueItem, ClinicalDraftSummary, PhysicianConfirmPayload,
    PhysicianDecisionPayload, AskPatientQuestionPayload, DepartmentDashboardMetrics,
    QueueStatus
)
from app.schemas.routing import DepartmentId
from app.schemas.redflag import RedFlagSeverity
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.core.security import SourceType
from app.modules.physician.queue_service import PriorityQueueService
from app.modules.physician.review_service import PhysicianReviewService
from app.modules.documents.firestore_service import FirestoreDocumentService
from app.modules.documents.storage_service import StorageService
from app.db.repositories.intake_repository import IntakeRepository
from app.db.repositories.patient_repository import PatientRepository
from app.db.repositories.timeline_repository import TimelineRepository

logger = logging.getLogger("medikiosk.api.physician")
router = APIRouter(prefix="/physician", tags=["physician"])

queue_service = PriorityQueueService()
review_service = PhysicianReviewService()
doc_service = FirestoreDocumentService()
storage_service = StorageService()
intake_repo = IntakeRepository()
patient_repo = PatientRepository()
timeline_repo = TimelineRepository()

DEPARTMENTS = [
    {"id": "cardiology", "display_name": "Cardiology", "icon": "🫀", "description": "Cardiac emergencies, chest pain, arrhythmias & hypertension triage."},
    {"id": "neurology", "display_name": "Neurology", "icon": "🧠", "description": "Stroke, seizures, acute migraines, neurological deficits."},
    {"id": "general-medicine", "display_name": "General Medicine", "icon": "🩺", "description": "General physician, fever, metabolic, and multi-system triage."},
    {"id": "orthopedics", "display_name": "Orthopedics", "icon": "🦴", "description": "Fractures, dislocations, acute joint and spinal pain."},
    {"id": "pediatrics", "display_name": "Pediatrics", "icon": "👶", "description": "Dedicated care for infants, children, and adolescents (Age 0-18)."},
    {"id": "emergency", "display_name": "Emergency / Trauma", "icon": "🚨", "description": "Life-threatening emergencies, trauma, and acute resuscitation."},
    {"id": "gastroenterology", "display_name": "Gastroenterology", "icon": "🍽️", "description": "Acute abdomen, GI bleed, severe gastritis & hepatic disorders."},
    {"id": "dermatology", "display_name": "Dermatology", "icon": "🧴", "description": "Acute skin eruptions, infections, and allergic dermatoses."},
    {"id": "ent", "display_name": "ENT", "icon": "👂", "description": "Ear, nose, throat emergencies, foreign bodies, airway triage."},
    {"id": "ophthalmology", "display_name": "Ophthalmology", "icon": "👁", "description": "Eye trauma, visual loss, acute red eye."},
    {"id": "psychiatry", "display_name": "Psychiatry", "icon": "🧩", "description": "Acute crisis, panic, behavioral triage."},
    {"id": "ayush", "display_name": "AYUSH / Integrative", "icon": "🌿", "description": "Ayurveda, Yoga, and integrative holistic consultation."},
    {"id": "unspecified", "display_name": "Unspecified / Triage Desk", "icon": "📋", "description": "Ambiguous symptoms, complex presentations & manual allocation."}
]

@router.get("/departments")
def list_departments():
    return DEPARTMENTS

@router.get("/departments/{department}/dashboard")
def get_department_dashboard(department: str):
    dept_enum = queue_service.get_department_enum(department)
    metrics = queue_service.get_department_metrics(dept_enum)
    recent_items = queue_service.get_department_queue(dept_enum)
    return {
        "department": department,
        "metrics": metrics.model_dump(),
        "recent_queue": [i.model_dump() for i in recent_items[:10]]
    }

@router.get("/departments/{department}/queue")
@router.get("/queue/{department}")
def get_department_queue(
    department: str,
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    dept_enum = queue_service.get_department_enum(department)
    items = queue_service.get_department_queue(
        department=dept_enum,
        search_query=search,
        severity_filter=severity,
        status_filter=status
    )
    return [i.model_dump() for i in items]

@router.get("/patient/{session_id}")
@router.get("/cases/{session_id}/workspace")
@router.get("/sessions/{session_id}/workspace")
async def get_patient_case_workspace(session_id: str):
    patient = patient_repo.get_patient_by_session(session_id)
    queue_item = queue_service.repo.get_by_session_id(session_id)
    draft_summary = intake_repo.get_draft_summary_by_session(session_id)

    if not patient and queue_item and queue_item.patient_id:
        patient = patient_repo.get_patient(queue_item.patient_id)
    if not patient and draft_summary and draft_summary.patient_id:
        patient = patient_repo.get_patient(draft_summary.patient_id)

    pat_id = patient.patient_id if patient else (queue_item.patient_id if queue_item else "unknown")

    if not draft_summary:
        draft_summary = await review_service.generate_draft_summary(session_id, pat_id)

    rf_result = intake_repo.get_redflag_result(session_id)
    routing = intake_repo.get_routing_by_session(session_id)
    questions = intake_repo.get_questions_by_session(session_id)
    answers = intake_repo.get_answers_by_session(session_id)
    context = intake_repo.get_context_state(session_id)
    timeline = timeline_repo.get_session_timeline(session_id)

    # Fetch genuine documents uploaded for this session
    raw_docs = doc_service.get_documents_by_session(session_id)
    if not raw_docs and patient:
        raw_docs = doc_service.get_documents_by_patient(patient.patient_id)

    documents_with_urls = []
    for doc in raw_docs:
        doc_copy = dict(doc)
        try:
            url, _ = storage_service.get_document_access_url(doc.get("document_id"))
            doc_copy["access_url"] = url
        except Exception:
            doc_copy["access_url"] = doc.get("provider_metadata", {}).get("secure_url") or doc.get("storage_key")
        documents_with_urls.append(doc_copy)

    # If queue item was WAITING, move to IN_REVIEW
    if queue_item and queue_item.status == QueueStatus.WAITING:
        queue_service.update_patient_status(queue_item.queue_id, QueueStatus.IN_REVIEW)

    # Identify information gaps
    missing_gaps = []
    if context:
        if not context.medications: missing_gaps.append({"field": "medications", "label": "Medication History", "status": "Not provided"})
        if not context.allergies: missing_gaps.append({"field": "allergies", "label": "Allergy History", "status": "Not provided"})
        if not context.family_history: missing_gaps.append({"field": "family_history", "label": "Family History", "status": "Not recorded"})
        if not documents_with_urls: missing_gaps.append({"field": "documents", "label": "Previous Medical Records", "status": "No documents uploaded"})

    patient_dict = patient.model_dump() if patient else (
        {
            "patient_id": queue_item.patient_id,
            "name": queue_item.patient_name,
            "age": queue_item.age,
            "gender": queue_item.gender,
            "preferred_language": "en"
        } if queue_item else None
    )

    draft_dict = draft_summary.model_dump() if draft_summary else {}
    rf_dict = rf_result.model_dump() if rf_result else None

    return {
        "patient": patient_dict,
        "queue_item": queue_item.model_dump() if queue_item else None,
        "draft_summary": draft_dict,
        "clinical_brief": draft_dict,
        "red_flag": rf_dict,
        "red_flags": rf_dict,
        "routing": routing.model_dump() if routing else None,
        "information_gaps": missing_gaps,
        "medical_history": {
            "known_conditions": context.known_conditions if context else [],
            "medications": context.medications if context else [],
            "allergies": context.allergies if context else [],
            "family_history": context.family_history if context else [],
            "lifestyle": context.lifestyle if context else [],
            "vitals": context.vitals if context else {},
            "provenance_map": context.provenance_map if context else {}
        },
        "documents": documents_with_urls,
        "ayurvedic_assessment": context.ayurvedic_findings if context else {},
        "questions": [q.model_dump() for q in questions],
        "answers": [a.model_dump() for a in answers],
        "timeline": [t.model_dump() for t in timeline],
        "physician_decision": {
            "confirmed_by": draft_summary.confirmed_by,
            "confirmed_at": draft_summary.confirmed_at.isoformat() if draft_summary.confirmed_at else None,
            "physician_notes": draft_summary.physician_notes,
            "is_draft": draft_summary.is_draft
        } if (draft_summary and not draft_summary.is_draft) else None
    }

@router.post("/cases/{session_id}/reassign_department")
@router.post("/sessions/{session_id}/reassign_department")
def reassign_patient_department(
    session_id: str,
    target_department: str = Query(...),
    physician_id: str = Query("attending_physician"),
    reason: Optional[str] = Query(None)
):
    """
    Directly reassigns a patient to another clinical department queue or escalates to Emergency.
    """
    target_dept_enum = queue_service.get_department_enum(target_department)
    queue_item = queue_service.repo.get_by_session_id(session_id)
    if not queue_item:
        raise HTTPException(status_code=404, detail=f"No active queue item found for session {session_id}")

    old_dept = queue_item.assigned_department or DepartmentId.UNSPECIFIED
    queue_item.assigned_department = target_dept_enum
    queue_item.status = QueueStatus.WAITING

    if target_dept_enum == DepartmentId.EMERGENCY:
        queue_item.overall_severity = RedFlagSeverity.CRITICAL
        queue_item.severity_rank = RedFlagSeverity.get_rank(RedFlagSeverity.CRITICAL)
        queue_item.priority_group = 0
        queue_item.is_red_flag = True

    queue_service.repo.upsert_queue_item(queue_item)

    # Update routing
    routing = intake_repo.get_routing_by_session(session_id)
    if routing:
        routing.confirmed_department = target_dept_enum
        routing.confirmed_by_physician_id = physician_id
        intake_repo.save_routing_recommendation(routing)

    # Log timeline event
    event = TimelineEvent(
        event_id=f"evt_reassign_{session_id}_{uuid.uuid4().hex[:4]}",
        patient_id=queue_item.patient_id,
        session_id=session_id,
        event_type=TimelineEventType.PHYSICIAN_OVERRIDDEN,
        title=f"Transferred to {target_dept_enum.value.title()}",
        description=f"Dr. {physician_id} reassigned patient from {old_dept.value.title()} to {target_dept_enum.value.title()}. Reason: {reason or 'Clinical specialist reassignment'}",
        source_type=SourceType.PHYSICIAN
    )
    timeline_repo.record_event(event)

    return {
        "status": "success",
        "message": f"Patient successfully reassigned to {target_dept_enum.value.title()} department.",
        "assigned_department": target_dept_enum.value
    }

@router.post("/cases/{session_id}/decision")
@router.post("/sessions/{session_id}/decision")
def submit_physician_decision(session_id: str, payload: PhysicianDecisionPayload):
    """
    Physician clinical decision and sign-off endpoint.
    Accepts, modifies, or overrides the AI recommendation with mandatory audit trail.
    """
    try:
        result = review_service.record_physician_decision(session_id, payload)
        return {
            "status": "success",
            "message": "Clinical case decision and sign-off recorded successfully",
            "decision": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cases/{session_id}/ask-question")
@router.post("/sessions/{session_id}/ask_patient")
def ask_patient_targeted_question(session_id: str, payload: AskPatientQuestionPayload):
    """
    Physician sends a focused clarification question to the patient's active session.
    """
    try:
        q = review_service.ask_patient_targeted_question(session_id, payload)
        return {
            "status": "success",
            "message": f"Targeted question '{q.question}' dispatched to patient session.",
            "question": q.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/cases/{session_id}/timeline")
def get_case_timeline(session_id: str):
    events = timeline_repo.get_session_timeline(session_id)
    return [e.model_dump() for e in events]

@router.get("/cases/{session_id}/documents")
def get_case_documents(session_id: str):
    raw_docs = doc_service.get_documents_by_session(session_id)
    docs = []
    for doc in raw_docs:
        doc_copy = dict(doc)
        try:
            url, _ = storage_service.get_document_access_url(doc.get("document_id"))
            doc_copy["access_url"] = url
        except Exception:
            doc_copy["access_url"] = doc.get("provider_metadata", {}).get("secure_url") or doc.get("storage_key")
        docs.append(doc_copy)
    return docs

@router.post("/confirm/{session_id}", include_in_schema=False)
def confirm_patient_case_legacy(session_id: str, payload: PhysicianConfirmPayload):
    try:
        confirmed = review_service.confirm_patient_review(session_id, payload)
        return {
            "status": "success",
            "message": "Clinical case review confirmed successfully",
            "confirmed_summary": confirmed.model_dump()
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
