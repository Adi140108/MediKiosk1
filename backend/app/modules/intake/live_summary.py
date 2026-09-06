import logging
from typing import List, Optional
from app.ai.gemma.client import GemmaClient
from app.schemas.intake import PatientContextState, LiveSummaryItem, AnswerItem

logger = logging.getLogger("medikiosk.intake.live_summary")

class LiveSummaryGenerator:
    def __init__(self, gemma_client: Optional[GemmaClient] = None):
        self.gemma = gemma_client or GemmaClient()

    async def generate_checkpoint_summary(
        self,
        session_id: str,
        context: PatientContextState,
        recent_answers: List[AnswerItem]
    ) -> LiveSummaryItem:
        """
        Generates a concise verification summary for the patient.
        """
        complaint = context.chief_complaint or "discomfort"
        location = f" in {context.location}" if context.location else ""
        duration = f" for {context.duration}" if context.duration else ""
        char = f" ({context.character})" if context.character else ""

        summary_text = f"I understand you are experiencing {complaint}{location}{char}{duration}. Let me ask a couple more questions to complete your review."

        summary_item = LiveSummaryItem(
            summary_id=f"sum_{session_id}_{context.question_count}",
            session_id=session_id,
            summary_text=summary_text,
            checkpoint_sequence=context.question_count
        )
        return summary_item
