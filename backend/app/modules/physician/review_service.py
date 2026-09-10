import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from app.schemas.physician import (
    ClinicalDraftSummary, PhysicianConfirmPayload, PhysicianDecisionPayload,
    AskPatientQuestionPayload, QueueStatus, PriorityQueueItem
)
from app.schemas.routing import RecommendationStatus, DepartmentId
from app.schemas.redflag import RedFlagSeverity
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.schemas.intake import QuestionItem, QuestionFramework, SocraticStage
from app.core.security import SourceType, log_audit_event, UserRole
from app.db.repositories.intake_repository import IntakeRepository
from app.db.repositories.queue_repository import QueueRepository
from app.db.repositories.timeline_repository import TimelineRepository
from app.db.repositories.patient_repository import PatientRepository
from app.ai.gemma.client import GemmaClient
from app.modules.physician.clinical_analyzer import ClinicalAnalysisEngine, ClinicalAnalysisResult
from rag.ayurparam_adapter import ayurparam_adapter

logger = logging.getLogger("medikiosk.physician.review")

class PhysicianReviewService:
    def __init__(
        self,
        intake_repo: Optional[IntakeRepository] = None,
        queue_repo: Optional[QueueRepository] = None,
        timeline_repo: Optional[TimelineRepository] = None,
        patient_repo: Optional[PatientRepository] = None,
        gemma_client: Optional[GemmaClient] = None
    ):
        self.intake_repo = intake_repo or IntakeRepository()
        self.queue_repo = queue_repo or QueueRepository()
        self.timeline_repo = timeline_repo or TimelineRepository()
        self.patient_repo = patient_repo or PatientRepository()
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
        # CRITICAL: chief_complaint must be ONLY the primary presenting complaint,
        # NOT a concatenation of all patient answers.
        raw_chief = (context.chief_complaint or "").strip() if context else ""
        
        # If the chief complaint looks like it contains multiple comma-separated raw answers
        # (e.g. "Joint swelling, knee is paining, I fell while riding..."), extract only the first phrase.
        if raw_chief and raw_chief.count(",") >= 2 and len(raw_chief) > 80:
            raw_chief = raw_chief.split(",")[0].strip()
        
        complaint = raw_chief if raw_chief else "General clinical evaluation"
        
        # 1. Compile Socratic Dialogue Evidence (strictly matched by question_id)
        qa_evidence_lines = []
        qa_pairs = []  # structured pairs for clinical analysis and synthesis
        for q in questions:
            matching_ans = next((a for a in answers if a.question_id == q.question_id), None)
            if not matching_ans:
                matching_ans = next((a for a in answers if a.sequence == q.sequence and a.question_id not in [o.question_id for o in questions if o != q]), None)
            if matching_ans:
                ans_text = matching_ans.answer or matching_ans.original_answer or ""
                q_text = q.question or ""
                objective = q.objective or ""
                if ans_text:
                    qa_evidence_lines.append(f"Q: {q_text}\nA: {ans_text}")
                    qa_pairs.append({
                        "question": q_text,
                        "answer": ans_text.strip(),
                        "objective": objective,
                        "field": getattr(q, "field", None) or ""
                    })

        # 2. Deep Clinical Analysis & Medical Narrative Synthesis
        analysis_result = ClinicalAnalysisEngine.analyze(
            chief_complaint=complaint,
            qa_pairs=qa_pairs,
            context=context
        )

        sev_val = analysis_result.severity_score
        sev_label = analysis_result.severity_label

        # Attempt Gemma synthesis if available
        gemma_synthesized = ""
        if qa_evidence_lines or complaint:
            try:
                synthesis_prompt = f"""You are an expert clinical documentation specialist. Write a concise, professional History of Present Illness (HPI) narrative for physician review.

Primary Presenting Complaint: {complaint}
Symptom Severity: {sev_val}/10 ({sev_label})

Patient Interview Evidence:
{chr(10).join(qa_evidence_lines)}

STRICT RULES:
1. Write EXACTLY 3-5 sentences as a single cohesive clinical narrative paragraph.
2. SYNTHESIZE and PARAPHRASE the patient's words into professional medical terminology. Do NOT copy patient answers verbatim or join them with commas.
3. Structure chronologically: onset/mechanism → presenting symptoms → severity/characteristics → aggravating/relieving factors → functional impact.
4. NEVER invent symptoms, diagnoses, or exam findings not stated by the patient.
5. DO NOT use lists, bullet points, Q&A format, numbered items, or semicolon-separated phrases.
6. DO NOT include headers, labels, or introductory phrases like "Here is the summary" or "During clinical interview, the patient reported:".
7. DO NOT repeat the same information twice in different forms."""

                gemma_synthesized = await asyncio.wait_for(
                    self.gemma.generate_response(
                        prompt=synthesis_prompt,
                        system_prompt="You are a senior clinical documentation specialist. Your sole task is to convert patient interview transcripts into professional, cohesive HPI narratives. Never echo raw patient language. Always paraphrase into clinical terminology.",
                        temperature=0.15
                    ),
                    timeout=2.5
                )
                gemma_synthesized = gemma_synthesized.strip()
                
                # Robust validation to reject malformed, echoed, or raw-dump AI outputs
                reject_terms = ["q:", "a:", "question:", "answer:", "additional reported details", 
                               "clinical dialogue findings", "here is the", "here's the",
                               "based on the interview", "based on the transcript",
                               "during clinical interview", "patient reported the following"]
                lower_synth = gemma_synthesized.lower()
                
                verbatim_echo_count = 0
                for pair in qa_pairs:
                    raw_ans = pair["answer"].lower().strip()
                    if len(raw_ans) > 15 and raw_ans in lower_synth:
                        verbatim_echo_count += 1
                
                if (len(gemma_synthesized) < 30 or 
                    "ai_unavailable" in lower_synth or 
                    any(term in lower_synth for term in reject_terms) or 
                    gemma_synthesized.count(";") > 4 or 
                    gemma_synthesized.count("\n") > 4 or
                    gemma_synthesized.count(",") > 12 or
                    verbatim_echo_count >= 2):
                    logger.info("Gemma HPI output rejected or unavailable. Using Clinical Analysis Engine narrative.")
                    gemma_synthesized = ""
            except Exception as e:
                logger.warning(f"Gemma HPI synthesis notice (falling back to deterministic narrative): {e}")
                gemma_synthesized = ""

        if gemma_synthesized:
            hpi_full = gemma_synthesized
        else:
            # High-grade medical HPI synthesized by ClinicalAnalysisEngine
            hpi_full = analysis_result.hpi_narrative

        progression = (context.progression if context and context.progression and context.progression != "No acute deterioration noted during intake"
                       else analysis_result.symptom_progression)
        
        # Merge associated symptoms from both context and clinical analysis
        base_assoc = list(context.associated_symptoms) if context and context.associated_symptoms else []
        for s in analysis_result.associated_symptoms:
            if s not in base_assoc:
                base_assoc.append(s)
        associated = base_assoc

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

        # Idempotency: Avoid creating identical duplicate questions if clicked multiple times
        norm_text = question_text.strip().lower()
        for eq in existing_questions:
            if eq.question and eq.question.strip().lower() == norm_text:
                logger.info(f"Targeted question '{question_text}' already exists for session {session_id}, reusing existing item {eq.question_id}")
                return eq

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
