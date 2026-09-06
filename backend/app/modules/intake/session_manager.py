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
from app.modules.intake.multilingual_questions import get_localized_question
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

    def start_session(self, session_id: str, patient_id: str, language: str = "en") -> QuestionItem:
        """
        Initializes context state and issues the initial Broad Socratic question in patient's language.
        """
        context = PatientContextState(
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
        1. Stores answer with full source attribution
        2. Updates patient context state
        3. Dynamically selects next question or concludes intake
        Returns: (next_question_item, is_finished, live_summary_text_if_any)
        """
        context = self.repo.get_context_state(session_id) or PatientContextState()
        existing_questions = self.repo.get_questions_by_session(session_id)
        current_q = next((q for q in existing_questions if q.question_id == question_id), None)

        # 1. Store Answer
        ans_count = len(self.repo.get_answers_by_session(session_id)) + 1
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

        # 3. Check for periodic live summary checkpoint (e.g., at question 3 and 6)
        live_summary_text = None
        if ans_count in [3, 6]:
            answers = self.repo.get_answers_by_session(session_id)
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

        next_question = QuestionItem(
            question_id=f"q_{session_id}_{cand_id}",
            session_id=session_id,
            question=localized_q,
            objective=candidate.get("objective", "Clarify details"),
            question_framework=QuestionFramework.AYURVEDIC if candidate.get("category") == "AYURVEDIC" else QuestionFramework.SOCRATIC,
            socratic_stage=stage,
            ayurvedic_domain=candidate.get("ayurvedic_domain"),
            display_label=candidate.get("display_label"),
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
            return

        obj = question.objective
        if "location" in obj.lower():
            context.location = clean_ans
            context.known_information.append(f"Location: {clean_ans}")
        elif "onset" in obj.lower():
            context.onset = clean_ans
            context.known_information.append(f"Onset: {clean_ans}")
        elif "duration" in obj.lower():
            context.duration = clean_ans
            context.known_information.append(f"Duration: {clean_ans}")
        elif "character" in obj.lower():
            context.character = clean_ans
            context.known_information.append(f"Character: {clean_ans}")
        elif "severity" in obj.lower():
            # Try to extract integer
            digits = [int(s) for s in clean_ans.split() if s.isdigit()]
            context.severity = digits[0] if digits else 5
            context.known_information.append(f"Severity: {clean_ans}")
        elif "associated" in obj.lower() or "red flag" in obj.lower():
            if "vomit" in ans_lower:
                context.associated_symptoms.append("vomiting")
            if "fever" in ans_lower:
                context.associated_symptoms.append("fever")
            if "stiff" in ans_lower:
                context.associated_symptoms.append("neck stiffness")
            if "vision" in ans_lower or "blur" in ans_lower:
                context.associated_symptoms.append("visual disturbance")
            if "breath" in ans_lower or "short" in ans_lower:
                context.associated_symptoms.append("shortness of breath")
            if "sweat" in ans_lower:
                context.associated_symptoms.append("diaphoresis")
            context.known_information.append(f"Associated symptoms: {clean_ans}")
        
        # Capture Ayurvedic domain findings if question was Ayurvedic
        if question.ayurvedic_domain:
            context.ayurvedic_findings[question.ayurvedic_domain] = clean_ans
            context.known_information.append(f"{question.display_label or question.ayurvedic_domain}: {clean_ans}")
