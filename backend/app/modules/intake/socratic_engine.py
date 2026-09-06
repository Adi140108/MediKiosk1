import logging
from typing import Optional, Dict, Any, List
from app.schemas.intake import SocraticStage, PatientContextState

logger = logging.getLogger("medikiosk.intake.socratic")

class SocraticEngine:
    """
    Drives the Socratic clinical inquiry progression:
    BROAD -> CLARIFY -> EXPLORE -> VERIFY -> SUFFICIENT -> STOP
    """
    def determine_next_stage(self, context: PatientContextState) -> SocraticStage:
        if not context.chief_complaint:
            return SocraticStage.BROAD

        # If location, duration, or onset are missing -> CLARIFY
        if not context.location or not context.duration or not context.onset:
            return SocraticStage.CLARIFY

        # If character, severity, or associated symptoms are missing -> EXPLORE
        if not context.character or context.severity is None or not context.associated_symptoms:
            return SocraticStage.EXPLORE

        # If we have core facts but haven't verified or checked lifestyle -> VERIFY
        if context.question_count < 8 and not context.is_sufficient:
            return SocraticStage.VERIFY

        return SocraticStage.SUFFICIENT

    def get_objective_for_stage(self, stage: SocraticStage, missing_info: List[str]) -> str:
        if stage == SocraticStage.BROAD:
            return "Identify chief complaint"
        
        if stage == SocraticStage.CLARIFY:
            if "location" in missing_info:
                return "Determine location"
            if "onset" in missing_info:
                return "Determine onset"
            if "duration" in missing_info:
                return "Determine duration"
            return "Clarify symptom details"

        if stage == SocraticStage.EXPLORE:
            if "character" in missing_info:
                return "Determine character"
            if "severity" in missing_info:
                return "Determine severity"
            if "associated_symptoms" in missing_info:
                return "Identify associated symptoms"
            return "Explore aggravating and relieving factors"

        if stage == SocraticStage.VERIFY:
            return "Verify clinical understanding and assess lifestyle context"

        return "Stop intake"
