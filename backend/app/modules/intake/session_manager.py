import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.intake import (
    PatientContextState, QuestionItem, AnswerItem, QuestionFramework, SocraticStage
)
from app.core.security import SourceType
from app.db.repositories.intake_repository import IntakeRepository
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine
from app.modules.intake.socratic_engine import SocraticEngine
from app.modules.intake.live_summary import LiveSummaryGenerator
from app.modules.intake.multilingual_questions import get_localized_question, get_localized_options
from app.ai.gemma.client import GemmaClient

logger = logging.getLogger("medikiosk.intake.session_manager")

class IntakeSessionManager:
    def __init__(
        self,
        intake_repo: Optional[IntakeRepository] = None,
        branching_engine: Optional[AdaptiveBranchingEngine] = None,
        socratic_engine: Optional[SocraticEngine] = None,
        live_summary_gen: Optional[LiveSummaryGenerator] = None,
        gemma_client: Optional[GemmaClient] = None
    ):
        self.repo = intake_repo or IntakeRepository()
        self.branching = branching_engine or AdaptiveBranchingEngine()
        self.socratic = socratic_engine or SocraticEngine()
        self.live_summary = live_summary_gen or LiveSummaryGenerator()
        self.gemma = gemma_client or GemmaClient()

    def start_session(
        self,
        session_id: str,
        patient_id: str,
        language: str = "en",
        opd_mode: str = "GENERAL_OPD",
        initial_chief_complaint: Optional[str] = None,
        initial_pain_score: Optional[int] = None,
        known_conditions: Optional[List[str]] = None,
        medications: Optional[List[str]] = None,
        past_medical_history: Optional[str] = None,
        prescription_notes: Optional[str] = None
    ) -> QuestionItem:
        """
        Initializes context state with chief complaint, known chronic conditions,
        current ongoing medications, past medical history, and previous prescription notes.
        """
        conditions_list = [c for c in (known_conditions or []) if c and c.lower() != 'none']
        meds_list = [m for m in (medications or []) if m]

        if initial_chief_complaint and initial_chief_complaint.strip():
            clean_complaint = initial_chief_complaint.strip()
            context = PatientContextState(
                opd_mode=opd_mode,
                mode_at_intake=opd_mode,
                chief_complaint=clean_complaint,
                severity=initial_pain_score or 7,
                known_conditions=conditions_list,
                medications=meds_list,
                past_medical_history=past_medical_history,
                prescription_notes=prescription_notes,
                socratic_stage=SocraticStage.CLARIFY,
                question_count=1
            )
            self.repo.save_context_state(session_id, context)

            # Build narrative for initial answer
            answer_parts = [f"{clean_complaint} (Pain Score: {initial_pain_score or 7}/10)"]
            if conditions_list:
                answer_parts.append(f"Known Conditions: {', '.join(conditions_list)}")
            if meds_list:
                answer_parts.append(f"Daily Medications: {', '.join(meds_list)}")
            if past_medical_history:
                answer_parts.append(f"Past History / Allergies: {past_medical_history}")
            if prescription_notes:
                answer_parts.append(f"Previous Prescription Advice: {prescription_notes}")

            # Store the implicit initial chief complaint answer for complete clinical traceability
            initial_ans = AnswerItem(
                answer_id=f"a_{session_id}_0",
                question_id="initial_chief_complaint",
                session_id=session_id,
                question="Chief Health Complaint, Medical History & Medications",
                answer=" | ".join(answer_parts),
                source_type=SourceType.PATIENT,
                language=language,
                sequence=0
            )
            self.repo.save_answer(initial_ans)

            # Select first clinical follow-up candidate dynamically based on the complaint
            candidate = self.branching.select_next_question_candidate(context, asked_question_ids=["initial_chief_complaint"])
            if candidate:
                cand_id = candidate.get("id", "1")
                default_q = candidate.get("question", "Could you describe when this started and how it feels?")
                localized_q = get_localized_question(cand_id, target_lang=language, default_text=default_q)
                raw_opts = candidate.get("options")
                loc_opts = get_localized_options(cand_id, raw_opts, target_lang=language) if raw_opts else None

                first_question = QuestionItem(
                    question_id=f"q_{session_id}_{cand_id}",
                    session_id=session_id,
                    question=localized_q,
                    objective=candidate.get("objective", "Clarify symptom details"),
                    question_framework=QuestionFramework.AYURVEDIC if candidate.get("category") == "AYURVEDIC" else QuestionFramework.SOCRATIC,
                    socratic_stage=SocraticStage.CLARIFY,
                    ayurvedic_domain=candidate.get("ayurvedic_domain"),
                    display_label=candidate.get("display_label"),
                    options=loc_opts,
                    language=language,
                    sequence=1
                )
                self.repo.save_question(first_question)
                return first_question

        # Fallback if no initial complaint was provided
        context = PatientContextState(
            opd_mode=opd_mode,
            mode_at_intake=opd_mode,
            socratic_stage=SocraticStage.BROAD,
            question_count=1
        )
        self.repo.save_context_state(session_id, context)

        q_text = get_localized_question(
            "initial_chief_complaint",
            target_lang=language,
            default_text="What is the main health concern or symptom bringing you here today?"
        )

        first_question = QuestionItem(
            question_id=f"q_{session_id}_1",
            session_id=session_id,
            question=q_text,
            objective="Identify chief complaint",
            question_framework=QuestionFramework.SOCRATIC,
            socratic_stage=SocraticStage.BROAD,
            language=language,
            sequence=1
        )
        self.repo.save_question(first_question)
        return first_question

    async def process_answer_and_get_next(
        self,
        session_id: str,
        question_id: str,
        answer_text: str,
        source_type: SourceType = SourceType.PATIENT,
        attendant_id: Optional[str] = None,
        language: str = "en"
    ) -> Tuple[Optional[QuestionItem], bool, Optional[str]]:
        """
        Ultra-fast critical path:
        1. Stores answer with full source attribution
        2. Updates patient context state in-memory
        3. Deterministically selects next question or concludes intake
        4. Saves single unified state
        Returns: (next_question_item, is_finished, live_summary_text_if_any)
        """
        context = self.repo.get_context_state(session_id) or PatientContextState()
        existing_questions = self.repo.get_questions_by_session(session_id)
        existing_answers = self.repo.get_answers_by_session(session_id)
        current_q = next((q for q in existing_questions if q.question_id == question_id), None)

        # 1. Store Answer
        ans_count = len(existing_answers) + 1
        answer_item = AnswerItem(
            answer_id=f"a_{session_id}_{ans_count}",
            question_id=question_id,
            session_id=session_id,
            question=current_q.question if current_q else "",
            answer=answer_text,
            source_type=source_type,
            attendant_id=attendant_id,
            language=language,
            sequence=ans_count
        )
        self.repo.save_answer(answer_item)

        # 2. Update context
        self._update_context_from_answer(context, current_q, answer_text)
        context.question_count = ans_count + 1

        # 3. Periodic deterministic live summary checkpoint (at question 3 and 6)
        live_summary_text = None
        if ans_count in [3, 6]:
            answers = existing_answers + [answer_item]
            sum_item = await self.live_summary.generate_checkpoint_summary(session_id, context, answers)
            self.repo.save_live_summary(sum_item)
            live_summary_text = sum_item.summary_text

        # 4. Select next candidate
        prefix = f"q_{session_id}_"
        asked_ids = [
            q.question_id[len(prefix):] if q.question_id.startswith(prefix) else q.question_id
            for q in existing_questions
        ]
        candidate = self.branching.select_next_question_candidate(context, asked_ids)

        if not candidate or context.is_sufficient:
            context.is_sufficient = True
            self.repo.save_context_state(session_id, context)
            return None, True, live_summary_text

        # 5. Build Next Question
        stage = self.socratic.determine_next_stage(context)
        context.socratic_stage = stage
        self.repo.save_context_state(session_id, context)

        next_q_num = ans_count + 1
        cand_id = candidate.get("id", str(next_q_num))
        default_q = candidate.get("question", "Could you provide more details about this?")
        localized_q = get_localized_question(cand_id, target_lang=language, default_text=default_q)
        raw_opts = candidate.get("options")
        loc_opts = get_localized_options(cand_id, raw_opts, target_lang=language) if raw_opts else None

        next_question = QuestionItem(
            question_id=f"q_{session_id}_{cand_id}",
            session_id=session_id,
            question=localized_q,
            objective=candidate.get("objective", "Clarify details"),
            question_framework=QuestionFramework.AYURVEDIC if candidate.get("category") == "AYURVEDIC" else QuestionFramework.SOCRATIC,
            socratic_stage=stage,
            ayurvedic_domain=candidate.get("ayurvedic_domain"),
            display_label=candidate.get("display_label"),
            options=loc_opts,
            language=language,
            sequence=next_q_num
        )
        self.repo.save_question(next_question)
        return next_question, False, live_summary_text

    def _update_context_from_answer(
        self,
        context: PatientContextState,
        question: Optional[QuestionItem],
        answer_text: str
    ):
        clean_ans = answer_text.strip()
        ans_lower = clean_ans.lower()

        if not question or question.objective == "Identify chief complaint":
            context.chief_complaint = clean_ans
            context.known_information.append(f"Chief complaint: {clean_ans}")
            self._extract_entities_from_text(context, clean_ans)
            return

        obj = question.objective if question else ""
        obj_lower = obj.lower()

        if "location" in obj_lower:
            context.location = clean_ans
            context.known_information.append(f"Location: {clean_ans}")
        elif "onset" in obj_lower or "injury" in obj_lower or "trauma" in obj_lower:
            context.onset = clean_ans
            context.known_information.append(f"Onset: {clean_ans}")
        elif "duration" in obj_lower:
            context.duration = clean_ans
            context.known_information.append(f"Duration: {clean_ans}")
        elif "character" in obj_lower or "stiffness" in obj_lower:
            context.character = clean_ans
            context.known_information.append(f"Character: {clean_ans}")
        elif "severity" in obj_lower:
            digits = [int(s) for s in clean_ans.split() if s.isdigit()]
            context.severity = digits[0] if digits else 5
            context.known_information.append(f"Severity: {clean_ans}")
        elif "associated" in obj_lower or "red flag" in obj_lower or "systemic" in obj_lower:
            context.known_information.append(f"Associated symptoms: {clean_ans}")
        elif "aggravating" in obj_lower or "trigger" in obj_lower:
            context.aggravating_factors.append(clean_ans)
            context.known_information.append(f"Aggravating: {clean_ans}")
        elif "relieving" in obj_lower or "relief" in obj_lower:
            context.relieving_factors.append(clean_ans)
            context.known_information.append(f"Relieving: {clean_ans}")

        self._extract_entities_from_text(context, clean_ans)
        
        # Capture Ayurvedic domain findings if question was Ayurvedic
        if question and question.ayurvedic_domain:
            context.ayurvedic_findings[question.ayurvedic_domain] = clean_ans
            context.known_information.append(f"{question.display_label or question.ayurvedic_domain}: {clean_ans}")

    def _extract_entities_from_text(self, context: PatientContextState, text: str):
        import re
        t_lower = text.lower()

        # Extract duration if not set
        if not context.duration:
            dur_match = re.search(r'(\d+|\b(one|two|three|four|five|six|seven|eight|nine|ten)\b)\s*(days?|hours?|weeks?|months?|d|h|w)', t_lower)
            if dur_match:
                context.duration = dur_match.group(0)
            elif "since yesterday" in t_lower:
                context.duration = "since yesterday"
            elif "since morning" in t_lower:
                context.duration = "since morning"

        # Extract severity if not set
        if context.severity is None:
            sev_match = re.search(r'\b(\d{1,2})\s*(?:out of|/)\s*10\b', t_lower)
            if not sev_match:
                sev_match = re.search(r'\brated\s*(\d{1,2})\b', t_lower)
            if not sev_match:
                sev_match = re.search(r'(\d{1,2})\s*/\s*10', t_lower)

            if sev_match:
                try:
                    val = int(sev_match.group(1))
                    if 1 <= val <= 10:
                        context.severity = val
                except ValueError:
                    pass
            elif "severe" in t_lower or "unbearable" in t_lower or "extreme" in t_lower:
                context.severity = 8
            elif "mild" in t_lower or "slight" in t_lower:
                context.severity = 3
            elif "moderate" in t_lower:
                context.severity = 5

        # Extract onset if not set
        if not context.onset:
            if "suddenly" in t_lower or "sudden" in t_lower or "abrupt" in t_lower:
                context.onset = "sudden onset"
            elif "gradually" in t_lower or "gradual" in t_lower or "slowly" in t_lower:
                context.onset = "gradual onset"

        # Extract location if not set
        if not context.location:
            loc_keywords = [
                ("headache", "head"), ("head", "head"), ("chest", "chest"), ("stomach", "abdomen"),
                ("abdomen", "abdomen"), ("belly", "abdomen"), ("knee", "knee"), ("back", "back"),
                ("throat", "throat"), ("leg", "leg"), ("arm", "arm"), ("shoulder", "shoulder"),
                ("joint", "joints"), ("neck", "neck"), ("eye", "eye"), ("ear", "ear")
            ]
            for kw, loc_val in loc_keywords:
                if kw in t_lower:
                    context.location = loc_val
                    break

        # Aggravating / Relieving text cues
        if ("worse" in t_lower or "worsens" in t_lower) and text not in context.aggravating_factors:
            context.aggravating_factors.append(text)
        if ("relief" in t_lower or "relieves" in t_lower or "better" in t_lower) and text not in context.relieving_factors:
            context.relieving_factors.append(text)

        # Associated symptom extractions (with negation guard)
        neg_pattern = r'\b(?:no|not|without|denies|never)\s+(?:[\w]+\s+){0,2}'
        if re.search(r'\bvomit', t_lower) and not re.search(neg_pattern + r'vomit', t_lower):
            if "vomiting" not in context.associated_symptoms: context.associated_symptoms.append("vomiting")
        if re.search(r'\bfever\b', t_lower) and not re.search(neg_pattern + r'fever', t_lower):
            if "fever" not in context.associated_symptoms: context.associated_symptoms.append("fever")
        if re.search(r'\bneck stiffness\b', t_lower) and not re.search(neg_pattern + r'neck stiffness', t_lower):
            if "neck stiffness" not in context.associated_symptoms: context.associated_symptoms.append("neck stiffness")
        if re.search(r'\b(?:vision|blur)', t_lower) and not re.search(neg_pattern + r'(?:vision|blur)', t_lower):
            if "visual disturbance" not in context.associated_symptoms: context.associated_symptoms.append("visual disturbance")
        if re.search(r'\b(?:breath|short)', t_lower) and not re.search(neg_pattern + r'(?:breath|short)', t_lower):
            if "shortness of breath" not in context.associated_symptoms: context.associated_symptoms.append("shortness of breath")
        if re.search(r'\bsweat', t_lower) and not re.search(neg_pattern + r'sweat', t_lower):
            if "diaphoresis" not in context.associated_symptoms: context.associated_symptoms.append("diaphoresis")
