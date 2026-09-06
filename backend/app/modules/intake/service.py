import logging
from typing import Optional, Dict, Any, List, Tuple
from app.modules.intake.session_manager import IntakeSessionManager
from app.db.repositories.intake_repository import IntakeRepository
from app.schemas.intake import QuestionItem, AnswerItem, LiveSummaryItem, PatientContextState
from app.core.security import SourceType

logger = logging.getLogger("medikiosk.intake.service")

class IntakeService:
    def __init__(self, session_manager: Optional[IntakeSessionManager] = None):
        self.session_manager = session_manager or IntakeSessionManager()
        self.repo = self.session_manager.repo

    def start_intake(self, session_id: str, patient_id: str, language: str = "en") -> QuestionItem:
        return self.session_manager.start_session(session_id, patient_id, language)

    async def submit_answer(
        self,
        session_id: str,
        question_id: str,
        answer: str,
        source_type: SourceType = SourceType.PATIENT,
        attendant_id: Optional[str] = None,
        language: str = "en"
    ) -> Tuple[Optional[QuestionItem], bool, Optional[str]]:
        return await self.session_manager.process_answer_and_get_next(
            session_id=session_id,
            question_id=question_id,
            answer_text=answer,
            source_type=source_type,
            attendant_id=attendant_id,
            language=language
        )

    def get_session_qa(self, session_id: str) -> Dict[str, Any]:
        questions = self.repo.get_questions_by_session(session_id)
        answers = self.repo.get_answers_by_session(session_id)
        context = self.repo.get_context_state(session_id)
        live_summaries = self.repo.get_live_summaries(session_id)
        return {
            "session_id": session_id,
            "questions": [q.model_dump() for q in questions],
            "answers": [a.model_dump() for a in answers],
            "context": context.model_dump() if context else None,
            "live_summaries": [s.model_dump() for s in live_summaries]
        }
