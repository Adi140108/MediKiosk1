import asyncio
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
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
from app.modules.routing.department_config import get_departments_for_mode, is_department_valid_for_mode
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

@router.get("/departments")
def list_departments(opd_mode: Optional[str] = "GENERAL_OPD"):
    """Returns single source of truth department registry from department_config.py."""
    depts = get_departments_for_mode(opd_mode)
    return [d.model_dump() for d in depts]

@router.get("/departments/{department}/dashboard")
def get_department_dashboard(department: str, opd_mode: Optional[str] = Query("GENERAL_OPD")):
    """Mode-aware department dashboard metrics and queue."""
    dept_enum = queue_service.get_department_enum(department)
    metrics = queue_service.get_department_metrics(dept_enum, opd_mode=opd_mode)
    recent_items = queue_service.get_department_queue(dept_enum, opd_mode_filter=opd_mode)
    return {
        "department": department,
        "opd_mode": opd_mode,
        "metrics": metrics.model_dump(),
        "recent_queue": [i.model_dump() for i in recent_items[:10]]
    }

@router.get("/departments/{department}/queue")
@router.get("/queue/{department}")
def get_department_queue(
    department: str,
    search: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    opd_mode: Optional[str] = Query(None)
):
    dept_enum = queue_service.get_department_enum(department)
    items = queue_service.get_department_queue(
        department=dept_enum,
        search_query=search,
        severity_filter=severity,
        status_filter=status,
        opd_mode_filter=opd_mode
    )
    return [i.model_dump() for i in items]

@router.get("/patient/{session_id}")
@router.get("/cases/{session_id}")
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

    if not draft_summary or (draft_summary.is_draft and ("during clinical interview, the patient reported" in (draft_summary.hpi or "").lower() or "additional reported details" in (draft_summary.hpi or "").lower())):
        try:
            draft_summary = await asyncio.wait_for(review_service.generate_draft_summary(session_id, pat_id), timeout=3.5)
        except Exception as e:
            logger.warning(f"Draft summary generation notice (fast fallback): {e}")
            context_obj = intake_repo.get_context_state(session_id)
            cc = context_obj.chief_complaint if (context_obj and context_obj.chief_complaint) else "General clinical evaluation"
            draft_summary = ClinicalDraftSummary(
                summary_id=f"sum_draft_{session_id}",
                session_id=session_id,
                patient_id=pat_id,
                chief_complaint=cc,
                hpi=f"Patient presents for clinical evaluation with complaint: {cc}.",
                is_draft=True
            )

    rf_result = intake_repo.get_redflag_result(session_id)
    routing = intake_repo.get_routing_by_session(session_id)
    questions = intake_repo.get_questions_by_session(session_id) or []
    answers = intake_repo.get_answers_by_session(session_id) or []
    context = intake_repo.get_context_state(session_id)
    timeline = timeline_repo.get_session_timeline(session_id)

    raw_intake_mode = context.mode_at_intake if (context and context.mode_at_intake) else (
        context.opd_mode if (context and context.opd_mode) else (queue_item.opd_mode if queue_item else "GENERAL_OPD")
    )
    mode_at_intake_val = str(getattr(raw_intake_mode, "value", raw_intake_mode)).upper()
    is_ayush = "AYUSH" in mode_at_intake_val

    # Strict Physician Dashboard Mode Isolation:
    # 1. GENERAL_OPD: NEVER calculate or dynamically generate any AYUSH assessment. Clear draft summary ayurvedic fields.
    # 2. AYUSH_OPD: Only display stored assessment from intake. Never trigger fresh LLM/RAG recalculation.
    if not is_ayush:
        if draft_summary:
            draft_summary.ayurvedic_assessment = {}
        ayush_assessment_dict = {}
        ayurvedic_findings_dict = {}
    else:
        stored_ayush = context.ayush_assessment if (context and context.ayush_assessment) else None
        if stored_ayush:
            ayush_assessment_dict = stored_ayush if isinstance(stored_ayush, dict) else stored_ayush.model_dump()
            if draft_summary:
                draft_summary.ayurvedic_assessment = ayush_assessment_dict
        else:
            ayush_assessment_dict = {
                "status": "INSUFFICIENT_DATA",
                "summary": "AYUSH assessment unavailable / insufficient data"
            }
            if draft_summary:
                draft_summary.ayurvedic_assessment = ayush_assessment_dict
        ayurvedic_findings_dict = context.ayurvedic_findings if (context and context.ayurvedic_findings) else {}

    raw_docs = doc_service.get_documents_by_session(session_id)
    if not raw_docs and patient:
        raw_docs = doc_service.get_documents_by_patient(patient.patient_id)

    documents_with_urls = []
    for doc in raw_docs:
        doc_copy = dict(doc)
        doc_id = doc.get("document_id")
        file_endpoint = f"/api/v1/documents/{doc_id}/file" if doc_id else ""
        try:
            url, _ = storage_service.get_document_access_url(doc_id)
            if url and (url.startswith("http://") or url.startswith("https://")):
                doc_copy["access_url"] = url
            else:
                doc_copy["access_url"] = file_endpoint or url
        except Exception:
            doc_copy["access_url"] = file_endpoint or doc.get("provider_metadata", {}).get("secure_url") or doc.get("storage_key")
        documents_with_urls.append(doc_copy)

    if queue_item and queue_item.status == QueueStatus.WAITING:
        queue_service.update_patient_status(queue_item.queue_id, QueueStatus.IN_REVIEW)

    missing_gaps = []
    if context:
        if not context.medications: missing_gaps.append({"field": "medications", "label": "Medication History", "status": "Not provided"})
        if not context.allergies: missing_gaps.append({"field": "allergies", "label": "Allergy History", "status": "Not provided"})
        if not context.family_history: missing_gaps.append({"field": "family_history", "label": "Family History", "status": "Not recorded"})
        if not documents_with_urls: missing_gaps.append({"field": "documents", "label": "Previous Medical Records", "status": "No documents uploaded"})

    if not rf_result:
        rf_sev = queue_item.overall_severity.value if (queue_item and hasattr(queue_item.overall_severity, 'value')) else (queue_item.overall_severity if queue_item else "NONE")
        is_rf = rf_sev in ("CRITICAL", "HIGH")
        rf_dict = {
            "is_red_flag": is_rf,
            "overall_severity": rf_sev,
            "severity_rank": 0 if rf_sev == "CRITICAL" else (1 if rf_sev == "HIGH" else 4),
            "flagged_rules": [],
            "flagged_reasons": [queue_item.red_flag_summary] if (queue_item and queue_item.red_flag_summary) else [],
            "triage_rationale": queue_item.red_flag_summary if (queue_item and queue_item.red_flag_summary) else "Standard OPD consultation priority based on deterministic clinical intake."
        }
    else:
        rf_dict = rf_result.model_dump()
        if not rf_dict.get("triage_rationale"):
            rf_dict["triage_rationale"] = (
                "Critical clinical red flags detected requiring urgent attending evaluation."
                if rf_dict.get("overall_severity") == "CRITICAL"
                else "Evaluated against deterministic red flag safety protocols."
            )

    if not routing:
        target_dept = queue_item.assigned_department.value if (queue_item and hasattr(queue_item.assigned_department, 'value')) else (queue_item.assigned_department if queue_item else ("ayush-unspecified" if is_ayush else "general-medicine"))
        routing_dict = {
            "recommended_department": target_dept,
            "assigned_department": target_dept,
            "confidence": queue_item.routing_confidence if queue_item else 0.85,
            "reasoning": "Symptom pattern matching and patient chief complaint aligned with this clinical specialty."
        }
    else:
        routing_dict = routing.model_dump()
        if not routing_dict.get("reasoning"):
            routing_dict["reasoning"] = "Symptom pattern matching and patient chief complaint aligned with this clinical specialty."

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
    if draft_dict:
        if "hpi" in draft_dict and not draft_dict.get("hpi_narrative"):
            draft_dict["hpi_narrative"] = draft_dict["hpi"]
        elif "hpi_narrative" in draft_dict and not draft_dict.get("hpi"):
            draft_dict["hpi"] = draft_dict["hpi_narrative"]

    return {
        "opd_mode": mode_at_intake_val,
        "mode_at_intake": mode_at_intake_val,
        "patient": patient_dict,
        "queue_item": queue_item.model_dump() if queue_item else None,
        "draft_summary": draft_dict,
        "clinical_brief": draft_dict,
        "red_flag": rf_dict,
        "red_flags": rf_dict,
        "routing": routing_dict,
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
        "ayurvedic_findings": ayurvedic_findings_dict,
        "ayush_assessment": ayush_assessment_dict,
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

class OverrideAyushRequest(BaseModel):
    prakriti: Optional[Dict[str, Any]] = None
    agni: Optional[Dict[str, Any]] = None
    koshta: Optional[Dict[str, Any]] = None
    physician_notes: Optional[str] = None
    physician_id: str = "dr_ayush_specialist"

@router.post("/cases/{session_id}/override_ayush")
def override_ayush_assessment(session_id: str, req: OverrideAyushRequest):
    context = intake_repo.get_context_state(session_id)
    if not context:
        raise HTTPException(status_code=400, detail="Intake context not found")
    raw_mode = context.mode_at_intake or context.opd_mode
    if "AYUSH" not in str(raw_mode).upper():
        raise HTTPException(status_code=400, detail="AYUSH assessment override is rejected for GENERAL_OPD patients.")
    
    current_eval = context.ayush_assessment or {}
    override_log = current_eval.get("physician_overrides", [])
    
    if req.prakriti:
        override_log.append({
            "field": "prakriti",
            "original": current_eval.get("prakriti"),
            "override": req.prakriti,
            "by": req.physician_id,
            "reason": req.physician_notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        current_eval["prakriti"] = req.prakriti

    if req.agni:
        override_log.append({
            "field": "agni",
            "original": current_eval.get("agni"),
            "override": req.agni,
            "by": req.physician_id,
            "reason": req.physician_notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        current_eval["agni"] = req.agni

    current_eval["physician_overrides"] = override_log
    context.ayush_assessment = current_eval
    intake_repo.save_context_state(session_id, context)

    event = TimelineEvent(
        event_id=f"evt_override_{session_id}_{uuid.uuid4().hex[:4]}",
        patient_id=req.physician_id,
        session_id=session_id,
        event_type=TimelineEventType.PHYSICIAN_REVIEWED,
        title="Ayurvedic Assessment Overridden by Physician",
        description=f"Assessment fields modified by {req.physician_id}. Reason: {req.physician_notes or 'Clinician review'}.",
        source_type=SourceType.PHYSICIAN
    )
    timeline_repo.record_event(event)

    return {"status": "success", "ayush_assessment": current_eval}

@router.post("/cases/{session_id}/reassign_department")
@router.post("/sessions/{session_id}/reassign_department")
@router.post("/cases/{session_id}/reassign")
@router.post("/patient/{session_id}/reassign")
def reassign_patient_department(
    session_id: str,
    target_department: str = Query(...),
    physician_id: str = Query("attending_physician"),
    reason: Optional[str] = Query(None)
):
    context = intake_repo.get_context_state(session_id)
    queue_item = queue_service.repo.get_by_session_id(session_id)
    raw_mode = context.mode_at_intake if (context and context.mode_at_intake) else (context.opd_mode if (context and context.opd_mode) else (queue_item.opd_mode if queue_item else "GENERAL_OPD"))
    opd_mode_str = str(getattr(raw_mode, "value", raw_mode)).upper()

    if not is_department_valid_for_mode(target_department, opd_mode_str):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign patient in mode '{opd_mode_str}' to department '{target_department}'. Department is invalid for this OPD mode."
        )

    target_dept_enum = queue_service.get_department_enum(target_department)
    if not queue_item:
        patient = patient_repo.get_patient_by_session(session_id)
        draft_summary = intake_repo.get_draft_summary_by_session(session_id)
        pat_id = patient.patient_id if patient else (draft_summary.patient_id if draft_summary else "unknown")
        pat_name = patient.name if patient else "Patient"
        pat_age = patient.age if patient else 45
        pat_gender = patient.gender if patient else "MALE"
        queue_item = PriorityQueueItem(
            queue_id=f"q_{session_id}",
            patient_id=pat_id,
            session_id=session_id,
            patient_name=pat_name,
            age=pat_age,
            gender=pat_gender,
            arrival_time=datetime.now(timezone.utc),
            opd_mode=opd_mode_str,
            assigned_department=target_dept_enum,
            recommended_department=target_dept_enum,
            status=QueueStatus.WAITING,
            overall_severity=RedFlagSeverity.CRITICAL if target_dept_enum == DepartmentId.EMERGENCY else RedFlagSeverity.NONE,
            severity_rank=0 if target_dept_enum == DepartmentId.EMERGENCY else 3,
            priority_group=0 if target_dept_enum == DepartmentId.EMERGENCY else 1,
            is_red_flag=True if target_dept_enum == DepartmentId.EMERGENCY else False,
            chief_complaint_summary=draft_summary.chief_complaint if draft_summary else "Transferred patient"
        )

    old_dept = queue_item.assigned_department or DepartmentId.UNSPECIFIED
    queue_item.assigned_department = target_dept_enum
    queue_item.status = QueueStatus.WAITING

    if target_dept_enum == DepartmentId.EMERGENCY:
        queue_item.overall_severity = RedFlagSeverity.CRITICAL
        queue_item.severity_rank = RedFlagSeverity.get_rank(RedFlagSeverity.CRITICAL)
        queue_item.priority_group = 0
        queue_item.is_red_flag = True

    queue_service.repo.upsert_queue_item(queue_item)

    routing = intake_repo.get_routing_by_session(session_id)
    if routing:
        routing.confirmed_department = target_dept_enum
        routing.confirmed_by_physician_id = physician_id
        intake_repo.save_routing_recommendation(routing)

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
        doc_id = doc.get("document_id")
        file_endpoint = f"/api/v1/documents/{doc_id}/file" if doc_id else ""
        try:
            url, _ = storage_service.get_document_access_url(doc_id)
            if url and (url.startswith("http://") or url.startswith("https://")):
                doc_copy["access_url"] = url
            else:
                doc_copy["access_url"] = file_endpoint or url
        except Exception:
            doc_copy["access_url"] = file_endpoint or doc.get("provider_metadata", {}).get("secure_url") or doc.get("storage_key")
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
