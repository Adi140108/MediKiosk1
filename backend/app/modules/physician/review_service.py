import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.schemas.physician import (
    ClinicalDraftSummary, PhysicianConfirmPayload, PhysicianDecisionPayload,
    AskPatientQuestionPayload, QueueStatus
)
from app.schemas.routing import RecommendationStatus, DepartmentId
from app.schemas.redflag import RedFlagSeverity
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.schemas.intake import QuestionItem, QuestionFramework, SocraticStage
from app.core.security import SourceType, log_audit_event, UserRole
from app.db.repositories.intake_repository import IntakeRepository
from app.db.repositories.queue_repository import QueueRepository
from app.db.repositories.timeline_repository import TimelineRepository
from app.ai.gemma.client import GemmaClient

logger = logging.getLogger("medikiosk.physician.review")

class PhysicianReviewService:
    def __init__(
        self,
        intake_repo: Optional[IntakeRepository] = None,
        queue_repo: Optional[QueueRepository] = None,
        timeline_repo: Optional[TimelineRepository] = None,
        gemma_client: Optional[GemmaClient] = None
    ):
        self.intake_repo = intake_repo or IntakeRepository()
        self.queue_repo = queue_repo or QueueRepository()
        self.timeline_repo = timeline_repo or TimelineRepository()
        self.gemma = gemma_client or GemmaClient()

    async def generate_draft_summary(
        self,
        session_id: str,
        patient_id: str
    ) -> ClinicalDraftSummary:
        """
        Creates AI-generated Draft Clinical Summary for the physician.
        Remains strictly DRAFT (is_draft=True) until confirmed by physician.
        """
        context = self.intake_repo.get_context_state(session_id)
        rf_result = self.intake_repo.get_redflag_result(session_id)
        routing = self.intake_repo.get_routing_by_session(session_id)

        complaint = context.chief_complaint if context and context.chief_complaint else "General clinical evaluation"
        hpi_parts = []
        if context:
            if context.onset: hpi_parts.append(f"Onset: {context.onset}")
            if context.location: hpi_parts.append(f"Location: {context.location}")
            if context.duration: hpi_parts.append(f"Duration: {context.duration}")
            if context.character: hpi_parts.append(f"Character: {context.character}")
            if context.severity is not None: hpi_parts.append(f"Severity: {context.severity}/10")

        hpi = ", ".join(hpi_parts) if hpi_parts else "Symptoms recorded during interactive Socratic intake."
        progression = context.progression if context and context.progression else "Not recorded"
        associated = context.associated_symptoms if context else []
        ayurvedic = context.ayurvedic_findings if context else {}
        red_flags = [f.title for f in rf_result.flagged_rules] if rf_result and rf_result.flagged_rules else []
        dept = routing.recommended_department.value if routing else "General Medicine"

        # Build provenance mapping for every fact
        sources = dict(context.provenance_map) if context else {}
        if not sources.get("chief_complaint"): sources["chief_complaint"] = "PATIENT"
        if not sources.get("hpi"): sources["hpi"] = "PATIENT"

        draft = ClinicalDraftSummary(
            summary_id=f"sum_draft_{session_id}_{uuid.uuid4().hex[:6]}",
            session_id=session_id,
            patient_id=patient_id,
            chief_complaint=complaint,
            hpi=hpi,
            symptom_progression=progression,
            associated_symptoms=associated,
            medical_history=context.known_conditions if context else [],
            medications=context.medications if context else [],
            allergies=context.allergies if context else [],
            ayurvedic_assessment=ayurvedic,
            red_flags=red_flags,
            recommended_department=dept,
            source_attribution=sources,
            is_draft=True
        )

        self.intake_repo.save_draft_summary(draft)
        return draft

    def confirm_patient_review(
        self,
        session_id: str,
        payload: PhysicianConfirmPayload
    ) -> ClinicalDraftSummary:
        """
        Confirms draft summary, applies physician notes/edits, and updates status.
        """
        draft = self.intake_repo.get_draft_summary_by_session(session_id)
        if not draft:
            raise ValueError(f"No draft summary found for session {session_id}")

        now_utc = datetime.now(timezone.utc)
        draft.is_draft = False
        draft.confirmed_by = payload.physician_id
        draft.confirmed_at = now_utc
        if payload.edited_summary:
            draft.hpi = payload.edited_summary
        if payload.physician_notes:
            draft.physician_notes = payload.physician_notes

        self.intake_repo.save_draft_summary(draft)

        routing = self.intake_repo.get_routing_by_session(session_id)
        if routing:
            routing.status = RecommendationStatus.CONFIRMED
            routing.confirmed_department = payload.confirmed_department
            routing.confirmed_by_physician_id = payload.physician_id
            self.intake_repo.save_routing_recommendation(routing)

        queue_item = self.queue_repo.get_by_session_id(session_id)
        if queue_item:
            queue_item.status = QueueStatus.COMPLETED
            queue_item.assigned_physician_id = payload.physician_id
            queue_item.assigned_department = payload.confirmed_department
            self.queue_repo.upsert_queue_item(queue_item)

        # Record timeline event
        event = TimelineEvent(
            event_id=f"evt_conf_{session_id}_{uuid.uuid4().hex[:4]}",
            patient_id=draft.patient_id,
            session_id=session_id,
            event_type=TimelineEventType.PHYSICIAN_CONFIRMED,
            title="Physician Review Confirmed",
            description=f"Confirmed by Dr. {payload.physician_id} for {payload.confirmed_department.value}.",
            source_type=SourceType.PHYSICIAN
        )
        self.timeline_repo.record_event(event)

        return draft

    def record_physician_decision(
        self,
        session_id: str,
        payload: PhysicianDecisionPayload
    ) -> Dict[str, Any]:
        """
        Processes full clinical decision & sign-off:
        - Evaluates if AI recommendation was overridden
        - Enforces override reason when changes occur
        - Updates routing, draft summary, and queue status
        - Logs detailed audit trail event
        """
        draft = self.intake_repo.get_draft_summary_by_session(session_id)
        if not draft:
            raise ValueError(f"No clinical summary found for session {session_id}")

        routing = self.intake_repo.get_routing_by_session(session_id)
        original_dept = routing.recommended_department if routing else DepartmentId.GENERAL_MEDICINE

        queue_item = self.queue_repo.get_by_session_id(session_id)
        original_severity = queue_item.overall_severity if queue_item else RedFlagSeverity.NONE

        is_dept_changed = (payload.final_department != original_dept)
        is_priority_changed = (payload.final_priority != original_severity)

        if (is_dept_changed or is_priority_changed) and not payload.override_reason:
            raise ValueError("Override reason is required when altering AI recommended department or priority.")

        now_utc = datetime.now(timezone.utc)

        # 1. Update summary
        draft.is_draft = False
        draft.confirmed_by = payload.physician_id
        draft.confirmed_at = now_utc
        if payload.clinical_notes:
            draft.physician_notes = payload.clinical_notes

        self.intake_repo.save_draft_summary(draft)

        # 2. Update routing
        if routing:
            routing.status = RecommendationStatus.CONFIRMED if not is_dept_changed else RecommendationStatus.MANUALLY_ASSIGNED
            routing.confirmed_department = payload.final_department
            routing.confirmed_by_physician_id = payload.physician_id
            self.intake_repo.save_routing_recommendation(routing)

        # 3. Update queue item
        if queue_item:
            queue_item.status = QueueStatus.COMPLETED
            queue_item.assigned_physician_id = payload.physician_id
            queue_item.assigned_department = payload.final_department
            queue_item.overall_severity = payload.final_priority
            queue_item.severity_rank = RedFlagSeverity.get_rank(payload.final_priority)
            self.queue_repo.upsert_queue_item(queue_item)

        # 4. Record Timeline Event
        event_title = "Physician Override & Sign-Off" if (is_dept_changed or is_priority_changed) else "Physician Review Confirmed"
        override_desc = f"Changed dept: {original_dept.value} -> {payload.final_department.value}. Reason: {payload.override_reason}" if is_dept_changed else f"Confirmed for {payload.final_department.value}."
        
        event = TimelineEvent(
            event_id=f"evt_dec_{session_id}_{uuid.uuid4().hex[:4]}",
            patient_id=draft.patient_id,
            session_id=session_id,
            event_type=TimelineEventType.PHYSICIAN_OVERRIDDEN if is_dept_changed else TimelineEventType.PHYSICIAN_CONFIRMED,
            title=event_title,
            description=f"Dr. {payload.physician_id}: {override_desc}",
            source_type=SourceType.PHYSICIAN
        )
        self.timeline_repo.record_event(event)

        # 5. Security audit logging
        log_audit_event(
            event_type="PHYSICIAN_CLINICAL_DECISION",
            user_id=payload.physician_id,
            role=UserRole.PHYSICIAN,
            session_id=session_id,
            details={
                "original_dept": original_dept.value,
                "final_dept": payload.final_department.value,
                "is_overridden": is_dept_changed or is_priority_changed,
                "override_reason": payload.override_reason
            }
        )

        return {
            "session_id": session_id,
            "physician_id": payload.physician_id,
            "confirmed_at": now_utc.isoformat(),
            "final_department": payload.final_department.value,
            "final_priority": payload.final_priority.value,
            "is_overridden": is_dept_changed or is_priority_changed,
            "status": "COMPLETED"
        }

    def ask_patient_targeted_question(
        self,
        session_id: str,
        payload: AskPatientQuestionPayload
    ) -> QuestionItem:
        """
        Allows attending physician to dispatch a targeted follow-up question to the patient.
        """
        category_prompts = {
            "medication": "Are you currently taking any regular prescription medications, blood thinners, or over-the-counter drugs?",
            "allergy": "Do you have any known allergies to medicines (like penicillin, sulfa), foods, or substances?",
            "duration": "Could you clarify exactly how long these specific symptoms have been occurring?",
            "previous_diagnosis": "Have you ever been diagnosed with heart disease, diabetes, hypertension, asthma, or kidney issues in the past?",
            "family_history": "Is there any family history of early heart attacks, stroke, cancer, or genetic conditions?",
            "other": payload.custom_question or "Could you share any other important medical details with your doctor?"
        }

        question_text = payload.custom_question if payload.custom_question else category_prompts.get(payload.category, category_prompts["other"])
        existing_questions = self.intake_repo.get_questions_by_session(session_id)
        next_seq = len(existing_questions) + 1

        question = QuestionItem(
            question_id=f"q_phys_{session_id}_{next_seq}",
            session_id=session_id,
            question=question_text,
            objective=f"Physician targeted inquiry: {payload.category}",
            question_framework=QuestionFramework.VERIFICATION,
            socratic_stage=SocraticStage.CLARIFY,
            language="en",
            sequence=next_seq
        )
        self.intake_repo.save_question(question)

        # Record timeline event
        draft = self.intake_repo.get_draft_summary_by_session(session_id)
        patient_id = draft.patient_id if draft else "unknown"

        event = TimelineEvent(
            event_id=f"evt_physq_{session_id}_{next_seq}",
            patient_id=patient_id,
            session_id=session_id,
            event_type=TimelineEventType.QUESTION_ASKED,
            title=f"Physician Requested Clarification ({payload.category.title()})",
            description=f"Dr. {payload.physician_id} sent follow-up question: '{question_text}'",
            source_type=SourceType.PHYSICIAN
        )
        self.timeline_repo.record_event(event)

        return question
