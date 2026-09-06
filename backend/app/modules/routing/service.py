import logging
import uuid
from typing import Optional
from app.schemas.intake import PatientContextState
from app.schemas.routing import RoutingRecommendation, RecommendationStatus, DepartmentId
from app.schemas.redflag import RedFlagEvaluationResult, RedFlagSeverity
from app.modules.routing.symptom_analyzer import analyze_symptoms_for_department
from app.db.repositories.intake_repository import IntakeRepository

logger = logging.getLogger("medikiosk.routing.service")

class RoutingService:
    def __init__(self, intake_repo: Optional[IntakeRepository] = None):
        self.repo = intake_repo or IntakeRepository()

    def generate_recommendation(
        self,
        session_id: str,
        patient_id: str,
        context: PatientContextState,
        red_flag_result: Optional[RedFlagEvaluationResult] = None,
        patient_age: int = 30
    ) -> RoutingRecommendation:
        """
        Generates an AI Department Routing Recommendation (PENDING_REVIEW) with
        confidence scores, alternative candidates, evidence mapping, and ambiguity handling.
        """
        complaint = context.chief_complaint or ""
        associated = " ".join(context.associated_symptoms)
        known = " ".join(context.known_information)
        full_text = f"{complaint} {associated} {known}"

        (
            dept,
            confidence,
            confidence_level,
            reasoning,
            matched_evidence,
            alternatives,
            dept_scores
        ) = analyze_symptoms_for_department(full_text, patient_age)

        # Critical red flag recommendation adjustment
        if red_flag_result and red_flag_result.overall_severity == RedFlagSeverity.CRITICAL:
            reasoning = f"[🚨 CRITICAL RED FLAG DETECTED] Priority Emergency/Specialty Review: {reasoning}"

        rec = RoutingRecommendation(
            recommendation_id=f"rec_{session_id}_{uuid.uuid4().hex[:8]}",
            session_id=session_id,
            patient_id=patient_id,
            recommended_department=dept,
            confidence=confidence,
            confidence_level=confidence_level,
            reasoning=reasoning,
            matched_evidence=matched_evidence,
            alternative_departments=alternatives,
            department_scores=dept_scores,
            routing_method="AI_AND_RULE_COMBINED",
            status=RecommendationStatus.PENDING_REVIEW,
            source_type="AI_GENERATED_RECOMMENDATION"
        )
        self.repo.save_routing_recommendation(rec)
        logger.info("Generated department recommendation for %s: %s (confidence: %.2f)", session_id, dept.value, confidence)
        return rec
