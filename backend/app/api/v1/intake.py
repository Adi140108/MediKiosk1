import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.modules.intake.service import IntakeService
from app.modules.redflags.engine import RedFlagEngine
from app.modules.routing.service import RoutingService
from app.modules.physician.review_service import PhysicianReviewService
from app.db.repositories.patient_repository import PatientRepository
from app.db.repositories.queue_repository import QueueRepository
from app.db.repositories.timeline_repository import TimelineRepository
from app.schemas.physician import PriorityQueueItem, QueueStatus
from app.schemas.redflag import RedFlagSeverity
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.core.security import SourceType

logger = logging.getLogger("medikiosk.api.intake")
router = APIRouter(prefix="/intake", tags=["intake"])

intake_service = IntakeService()
redflag_engine = RedFlagEngine()
routing_service = RoutingService()
review_service = PhysicianReviewService()
patient_repo = PatientRepository()
queue_repo = QueueRepository()
timeline_repo = TimelineRepository()

class StartIntakeRequest(BaseModel):
    patient_id: str
    session_id: Optional[str] = None
    language: str = "en"
    opd_mode: Optional[str] = "GENERAL_OPD"
    is_attendant_assisted: bool = False
    attendant_id: Optional[str] = None
    chief_complaint: Optional[str] = None
    pain_level: Optional[int] = None
    known_conditions: Optional[List[str]] = None
    medications: Optional[List[str]] = None
    past_medical_history: Optional[str] = None
    prescription_notes: Optional[str] = None

class SubmitAnswerRequest(BaseModel):
    session_id: str
    question_id: Optional[str] = "initial_chief_complaint"
    answer: str
    source_type: Optional[SourceType] = SourceType.PATIENT
    attendant_id: Optional[str] = None
    language: Optional[str] = "en"

class UpdateAnswerRequest(BaseModel):
    session_id: str
    question_id: str
    new_answer: str
    physician_id: Optional[str] = "dr_sharma_cardio"

class CompleteIntakeRequest(BaseModel):
    session_id: str
    patient_id: str

@router.post("/start")
def start_intake_session(req: StartIntakeRequest):
    session_id = req.session_id or f"sess_{uuid.uuid4().hex[:8]}"
    patient = patient_repo.get_patient(req.patient_id)
    if patient:
        patient.active_session_id = session_id
        patient_repo.save_patient(patient)

    mode = req.opd_mode or "GENERAL_OPD"
    first_q = intake_service.start_intake(
        session_id=session_id,
        patient_id=req.patient_id,
        language=req.language or "en",
        opd_mode=mode,
        initial_chief_complaint=req.chief_complaint,
        initial_pain_score=req.pain_level,
        known_conditions=req.known_conditions or [],
        medications=req.medications or [],
        past_medical_history=req.past_medical_history,
        prescription_notes=req.prescription_notes
    )
    return {
        "session_id": session_id,
        "question": first_q.model_dump(),
        "is_finished": False
    }

@router.put("/answer")
@router.post("/answer/update")
def update_intake_answer(req: UpdateAnswerRequest):
    updated = intake_service.repo.update_answer_text(
        session_id=req.session_id,
        question_id=req.question_id,
        new_answer_text=req.new_answer,
        edited_by=req.physician_id or "physician"
    )
    if not updated:
        from app.schemas.intake import AnswerItem
        updated = AnswerItem(
            answer_id=f"a_{req.session_id}_{uuid.uuid4().hex[:4]}",
            question_id=req.question_id,
            session_id=req.session_id,
            question="Clinical Inquiry",
            answer=req.new_answer,
            source_type=SourceType.PHYSICIAN
        )
        intake_service.repo.save_answer(updated)
    return {
        "status": "success",
        "answer": updated.model_dump()
    }

@router.post("/answer")
async def submit_intake_answer(req: SubmitAnswerRequest):
    qid = req.question_id or "initial_chief_complaint"
    lang = req.language or "en"
    stype = req.source_type or SourceType.PATIENT

    next_q, is_finished, live_summary = await intake_service.submit_answer(
        session_id=req.session_id,
        question_id=qid,
        answer=req.answer,
        source_type=stype,
        attendant_id=req.attendant_id,
        language=lang
    )

    return {
        "session_id": req.session_id,
        "next_question": next_q.model_dump() if next_q else None,
        "is_finished": is_finished,
        "live_summary": live_summary
    }

@router.post("/complete")
async def complete_intake(req: CompleteIntakeRequest):
    """
    Concludes intake:
    1. Evaluates Deterministic Red Flags & Severity
    2. Runs AI Department Routing Recommendation (PENDING_REVIEW)
    3. Generates Draft Physician Summary (DRAFT_AI_GENERATED)
    4. Places patient into Department Priority Queue (Single entry, sorted by priority)
    5. Records timeline event
    """
    patient = patient_repo.get_patient(req.patient_id)
    patient_name = patient.name if patient else "Unknown Patient"
    patient_age = patient.age if patient else 35
    patient_gender = getattr(patient.gender, "value", patient.gender) if patient else "OTHER"

    context = intake_service.repo.get_context_state(req.session_id)
    if not context:
        raise HTTPException(status_code=400, detail="No intake context found for session")

    # 1. Deterministic Red-Flag evaluation
    rf_result = redflag_engine.evaluate_patient_context(req.session_id, context)
    intake_service.repo.save_redflag_result(rf_result)

    # 2. Department routing
    routing_rec = routing_service.generate_recommendation(
        session_id=req.session_id,
        patient_id=req.patient_id,
        context=context,
        red_flag_result=rf_result,
        patient_age=patient_age
    )

    # 2.5 Run AYUSH 4-Layer Assessment Engine ONLY if in AYUSH OPD mode
    opd_mode_val = str(getattr(context, "opd_mode", "GENERAL_OPD")).upper()
    if "AYUSH" in opd_mode_val:
        from app.modules.ayush.assessment_engine import AyushAssessmentEngine
        ayush_engine = AyushAssessmentEngine()
        session_qa = intake_service.get_session_qa(req.session_id)
        qa_list = []
        for q_item, a_item in zip(session_qa.get("questions", []), session_qa.get("answers", [])):
            qa_list.append({
                "question_id": q_item.get("question_id"),
                "question": q_item.get("question"),
                "answer": a_item.get("answer"),
                "clinical_domain": q_item.get("clinical_domain", "general")
            })

        ayush_eval = ayush_engine.evaluate_assessment(
            qa_pairs=qa_list,
            patient_age=patient_age,
            ayurvedic_findings=context.ayurvedic_findings
        )
        context.ayush_assessment = ayush_eval
    else:
        context.ayurvedic_findings = {}
        context.ayush_assessment = {}

    intake_service.repo.save_context_state(req.session_id, context)

    # 3. Generate Draft Physician Summary
    draft_summary = await review_service.generate_draft_summary(
        session_id=req.session_id,
        patient_id=req.patient_id
    )

    # 4. Insert / Update into Department Priority Queue (Single entry!)
    now_utc = datetime.now(timezone.utc)
    queue_id = f"qitem_{req.session_id}"
    
    # Priority logic
    is_rf = rf_result.has_red_flags
    sev = rf_result.overall_severity
    sev_rank = RedFlagSeverity.get_rank(sev)
    p_group = 0 if is_rf else 1

    opd_mode_val = str(getattr(context, "opd_mode", "GENERAL_OPD"))
    queue_item = PriorityQueueItem(
        queue_id=queue_id,
        patient_id=req.patient_id,
        session_id=req.session_id,
        patient_name=patient_name,
        age=patient_age,
        gender=patient_gender,
        arrival_time=now_utc,
        waiting_time_minutes=0,
        opd_mode=opd_mode_val,
        is_red_flag=is_rf,
        priority_group=p_group,
        overall_severity=sev,
        severity_rank=sev_rank,
        red_flag_details=rf_result.flagged_rules,
        red_flag_summary=rf_result.summary_reason,
        assigned_department=routing_rec.recommended_department,
        recommended_department=routing_rec.recommended_department,
        routing_confidence=routing_rec.confidence,
        status=QueueStatus.WAITING
    )
    queue_repo.upsert_queue_item(queue_item)

    # 5. Timeline Event
    event = TimelineEvent(
        event_id=f"evt_comp_{req.session_id}",
        patient_id=req.patient_id,
        session_id=req.session_id,
        event_type=TimelineEventType.INTAKE_COMPLETED,
        title="Clinical Intake Completed",
        description=f"Intake completed. Red Flag: {sev.value}. Department: {routing_rec.recommended_department.value}.",
        source_type=SourceType.AI_GENERATED
    )
    timeline_repo.record_event(event)

    return {
        "status": "completed",
        "session_id": req.session_id,
        "red_flag": rf_result.model_dump(),
        "routing": routing_rec.model_dump(),
        "draft_summary": draft_summary.model_dump(),
        "queue_item": queue_item.model_dump()
    }

@router.get("/{session_id}/qa")
def get_session_qa(session_id: str):
    return intake_service.get_session_qa(session_id)
