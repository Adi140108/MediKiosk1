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
from rag.ayurparam_adapter import ayurparam_adapter

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
        Creates high-quality, articulate AI-generated Draft Clinical Summary for the physician.
        Synthesizes Socratic interview Q&A, pain scores, relieving/aggravating factors,
        genuine document evidence, and Ayurvedic holistic dosha observations.
        Remains strictly DRAFT (is_draft=True) until confirmed by physician.
        """
        context = self.intake_repo.get_context_state(session_id)
        rf_result = self.intake_repo.get_redflag_result(session_id)
        routing = self.intake_repo.get_routing_by_session(session_id)
        questions = self.intake_repo.get_questions_by_session(session_id) or []
        answers = self.intake_repo.get_answers_by_session(session_id) or []

        # Compile rich chief complaint and symptom text
        complaint_terms = []
        if context and context.chief_complaint:
            complaint_terms.append(context.chief_complaint)
        if context and hasattr(context, "associated_symptoms") and context.associated_symptoms:
            for s in context.associated_symptoms:
                if s not in complaint_terms:
                    complaint_terms.append(s)
        for a in answers:
            ans_text = a.answer or a.original_answer or ""
            if ans_text and len(ans_text) < 80 and ans_text not in complaint_terms:
                complaint_terms.append(ans_text)

        complaint = ", ".join(complaint_terms) if complaint_terms else "General clinical evaluation"
        
        # 1. Compile Socratic Dialogue Evidence (for Gemma synthesis prompt)
        qa_evidence_lines = []
        qa_answer_only_parts = []
        for q in questions:
            matching_ans = next((a for a in answers if a.question_id == q.question_id or a.sequence == q.sequence), None)
            if matching_ans:
                ans_text = matching_ans.answer or matching_ans.original_answer or ""
                if ans_text:
                    qa_evidence_lines.append(f"Q: {q.question}\nA: {ans_text}")
                    qa_answer_only_parts.append(ans_text)

        # 2. Build Cohesive AI-Synthesized Clinical HPI Narrative
        sev_val = context.severity if context and context.severity is not None else 7
        sev_label = "Severe" if sev_val >= 7 else ("Moderate" if sev_val >= 4 else "Mild")

        timeline_parts = []
        if context and context.onset: timeline_parts.append(f"onset {context.onset}")
        if context and context.duration: timeline_parts.append(f"duration {context.duration}")
        if context and context.location: timeline_parts.append(f"located in {context.location}")
        if context and context.character: timeline_parts.append(f"described as {context.character}")
        timeline_phrase = ", ".join(timeline_parts) if timeline_parts else ""

        # Attempt Gemma synthesis
        gemma_synthesized = ""
        if qa_evidence_lines or complaint:
            try:
                synthesis_prompt = f"""You are an expert clinical documentation specialist. Write a concise, detailed History of Present Illness (HPI) narrative for physician review.

Patient Chief Complaint: {complaint}
Symptom Severity: {sev_val}/10 ({sev_label})
Clinical Timeline & Characteristics: {timeline_phrase if timeline_phrase else 'Documented during intake'}

Patient Interview Dialogue Evidence:
{chr(10).join(qa_evidence_lines)}

INSTRUCTIONS:
- Write a flowing 3-4 sentence clinical narrative paragraph in standard medical documentation format.
- Synthesize all patient statements, radiation, triggers, relieving factors, and associated symptoms into a single cohesive paragraph.
- DO NOT list questions or use bullet points.
- DO NOT include headings or meta text. Write ONLY the clinical narrative paragraph."""

                gemma_synthesized = await self.gemma.generate_response(
                    prompt=synthesis_prompt,
                    system_prompt="You are a senior clinical documentation specialist writing HPI narratives for physician review. Be concise, accurate, and use standard medical documentation style.",
                    temperature=0.15
                )
                gemma_synthesized = gemma_synthesized.strip()
                if len(gemma_synthesized) < 20 or "ai_unavailable" in gemma_synthesized.lower() or "Q:" in gemma_synthesized:
                    gemma_synthesized = ""
            except Exception as e:
                logger.warning(f"Gemma HPI synthesis notice: {e}")
                gemma_synthesized = ""

        if gemma_synthesized:
            hpi_full = gemma_synthesized
        else:
            # High-quality deterministic clinical narrative synthesis fallback (no bullet points, no Q&A lists)
            time_sentence = f" with {timeline_phrase}" if timeline_phrase else ""
            ans_clean = [a for a in qa_answer_only_parts if len(a) > 2 and a.lower() not in ["no", "none", "n/a", "no trigger"]]
            details_sentence = f" Additional reported details: {'; '.join(ans_clean)}." if ans_clean else ""
            hpi_full = f"Patient presents with {complaint}{time_sentence}. Symptom severity is rated at Level {sev_val}/10 ({sev_label}).{details_sentence} Patient has been routed for clinical evaluation."

        progression = context.progression if context and context.progression else "No acute deterioration noted during intake"
        associated = context.associated_symptoms if context and context.associated_symptoms else []

        # 3. Dynamic Ayurvedic Dosha & Agni Synthesis using AyurGenixAI Dataset & BharatGenAI AyurParam (ONLY in AYUSH OPD mode)
        opd_mode_str = str(getattr(context, "opd_mode", "GENERAL_OPD")).upper() if context else "GENERAL_OPD"
        is_ayush = "AYUSH" in opd_mode_str
        ayurvedic = {}
        if is_ayush:
            ayurvedic = dict(context.ayurvedic_findings) if context and context.ayurvedic_findings else {}
            try:
                rag_assessment = ayurparam_adapter.synthesize_ayurvedic_report(
                    chief_complaint=complaint,
                    associated_symptoms=associated,
                    pain_score=context.severity if context else None
                )
                # Merge RAG evaluation into ayurvedic dictionary
                for k, v in rag_assessment.items():
                    ayurvedic[k] = v
            except Exception as e:
                logger.warning(f"Ayurvedic RAG synthesis notice: {e}")

        red_flags = [f.title for f in rf_result.flagged_rules] if rf_result and rf_result.flagged_rules else []
        dept = routing.recommended_department.value if routing else "General Medicine"

        # 4. Provenance tracking
        sources = dict(context.provenance_map) if context else {}
        if not sources.get("chief_complaint"): sources["chief_complaint"] = "PATIENT"
        if not sources.get("hpi"): sources["hpi"] = "AI_CLINICAL_SYNTHESIS"

        med_history = list(context.known_conditions) if context and context.known_conditions else []
        if context and context.past_medical_history:
            med_history.append(f"Past History/Allergies: {context.past_medical_history}")
        if context and context.prescription_notes:
            med_history.append(f"Dictated Previous Advice: {context.prescription_notes}")

        med_list = list(context.medications) if context and context.medications else []

        draft = ClinicalDraftSummary(
            summary_id=f"sum_draft_{session_id}_{uuid.uuid4().hex[:6]}",
            session_id=session_id,
            patient_id=patient_id,
            chief_complaint=complaint,
            hpi=hpi_full,
            symptom_progression=progression,
            associated_symptoms=associated,
            medical_history=med_history,
            medications=med_list,
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
            patient = self.patient_repo.get_patient_by_session(session_id)
            pat_id = patient.patient_id if patient else "unknown"
            draft = ClinicalDraftSummary(
                summary_id=f"draft_{session_id}",
                session_id=session_id,
                patient_id=pat_id,
                chief_complaint="Clinical Consultation",
                hpi_narrative="Patient clinical record prepared for physician review.",
                associated_symptoms=[],
                red_flag_findings=[],
                recommended_department=payload.final_department,
                confidence_score=0.9,
                is_draft=False
            )
            self.intake_repo.save_draft_summary(draft)

        routing = self.intake_repo.get_routing_by_session(session_id)
        original_dept = routing.recommended_department if routing else payload.final_department

        queue_item = self.queue_repo.get_by_session_id(session_id)
        original_severity = queue_item.overall_severity if queue_item else payload.final_priority

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
        if not queue_item:
            patient = self.patient_repo.get_patient_by_session(session_id)
            pat_id = patient.patient_id if patient else draft.patient_id
            pat_name = patient.name if patient else "Patient"
            queue_item = PriorityQueueItem(
                queue_id=f"q_{session_id}",
                patient_id=pat_id,
                session_id=session_id,
                patient_name=pat_name,
                age=patient.age if patient else 45,
                gender=patient.gender if patient else "MALE",
                arrival_time=now_utc,
                assigned_department=payload.final_department,
                recommended_department=payload.final_department,
                status=QueueStatus.COMPLETED,
                overall_severity=payload.final_priority,
                severity_rank=RedFlagSeverity.get_rank(payload.final_priority),
                priority_group=0 if payload.final_priority == RedFlagSeverity.CRITICAL else 1,
                is_red_flag=True if payload.final_priority == RedFlagSeverity.CRITICAL else False,
                chief_complaint_summary=draft.chief_complaint
            )
        else:
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
