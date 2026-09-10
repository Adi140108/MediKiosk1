import logging
import uuid
from typing import Optional
from app.schemas.intake import PatientContextState
from app.schemas.routing import RoutingRecommendation, RecommendationStatus, DepartmentId
from app.schemas.redflag import RedFlagEvaluationResult, RedFlagSeverity
from app.modules.routing.symptom_analyzer import analyze_symptoms_for_department
from app.modules.routing.department_config import is_department_valid_for_mode
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
        Generates an AI Department Routing Recommendation (PENDING_REVIEW) strictly isolated by opd_mode:
        - GENERAL_OPD: Only routes to General departments (fallback: GENERAL_UNSPECIFIED).
        - AYUSH_OPD: Only routes to AYUSH departments (fallback: AYUSH_UNSPECIFIED).
        - Critical Red Flags: Escalation to EMERGENCY permitted as an explicit safety override.
        """
        complaint = context.chief_complaint or ""
        associated = " ".join(context.associated_symptoms)
        known = " ".join(context.known_information)
        full_text = f"{complaint} {associated} {known}"
        opd_mode_str = str(getattr(context, "opd_mode", "GENERAL_OPD")).upper()

        (
            dept,
            confidence,
            confidence_level,
            reasoning,
            matched_evidence,
            alternatives,
            dept_scores
        ) = analyze_symptoms_for_department(full_text, patient_age, opd_mode=opd_mode_str)

        if "AYUSH" in opd_mode_str:
            # Map allopathic triage recommendation to corresponding AYUSH clinical specialty
            dept_key = getattr(dept, "value", str(dept)).lower()
            ayush_str_mapping = {
                "cardiology": DepartmentId.KAYACHIKITSA,
                "pulmonology": DepartmentId.KAYACHIKITSA,
                "gastroenterology": DepartmentId.KAYACHIKITSA,
                "general-medicine": DepartmentId.KAYACHIKITSA,
                "general_medicine": DepartmentId.KAYACHIKITSA,
                "neurology": DepartmentId.SHALAKYA,
                "ent": DepartmentId.SHALAKYA,
                "ophthalmology": DepartmentId.SHALAKYA,
                "orthopedics": DepartmentId.SHALYA,
                "pediatrics": DepartmentId.KAUMARABHRITYA,
                "dermatology": DepartmentId.AGADATANTRA,
                "psychiatry": DepartmentId.SWASTHAVRITTA,
                "ayush": DepartmentId.KAYACHIKITSA,
                "kayachikitsa": DepartmentId.KAYACHIKITSA,
                "panchakarma": DepartmentId.PANCHAKARMA,
                "shalya": DepartmentId.SHALYA,
                "shalakya": DepartmentId.SHALAKYA,
                "prasuti-stri": DepartmentId.PRASUTI_STRI,
                "kaumarabhritya": DepartmentId.KAUMARABHRITYA,
                "swasthavritta": DepartmentId.SWASTHAVRITTA,
                "agadatantra": DepartmentId.AGADATANTRA,
                "unspecified": DepartmentId.AYUSH_UNSPECIFIED,
                "general-unspecified": DepartmentId.AYUSH_UNSPECIFIED,
                "general_unspecified": DepartmentId.AYUSH_UNSPECIFIED,
                "ayush-unspecified": DepartmentId.AYUSH_UNSPECIFIED,
                "ayush_unspecified": DepartmentId.AYUSH_UNSPECIFIED
            }
            default_ayush = DepartmentId.AYUSH_UNSPECIFIED if (
                dept_key in ["unspecified", "general-unspecified", "general_unspecified", "ayush-unspecified", "ayush_unspecified"]
                or dept in [DepartmentId.UNSPECIFIED, DepartmentId.GENERAL_UNSPECIFIED, DepartmentId.AYUSH_UNSPECIFIED]
            ) else DepartmentId.KAYACHIKITSA
            dept = ayush_str_mapping.get(dept_key, default_ayush)
            reasoning = f"[AYUSH OPD MODE] Routed to {dept.value.upper()} for Ayurvedic evaluation, Agni/Prakriti assessment, and holistic treatment."
        else:
            # Ensure GENERAL_OPD recommendation is strictly an allopathic department
            ayush_depts = [DepartmentId.AYUSH, DepartmentId.KAYACHIKITSA, DepartmentId.PANCHAKARMA, DepartmentId.SHALYA, DepartmentId.SHALAKYA, DepartmentId.PRASUTI_STRI, DepartmentId.KAUMARABHRITYA, DepartmentId.SWASTHAVRITTA, DepartmentId.AGADATANTRA]
            if dept in ayush_depts or getattr(dept, "value", str(dept)).lower() in ["ayush", "kayachikitsa", "panchakarma", "shalya", "shalakya", "prasuti-stri", "kaumarabhritya", "swasthavritta", "agadatantra"]:
                dept = DepartmentId.GENERAL_MEDICINE

        # Enforce Mode + Department Validation
        if not is_department_valid_for_mode(dept.value, opd_mode_str):
            if "AYUSH" in opd_mode_str:
                dept = DepartmentId.AYUSH_UNSPECIFIED
                reasoning = "[AYUSH OPD MODE] Unspecified/Insufficient evidence for sub-specialty. Routed to AYUSH_UNSPECIFIED."
            else:
                dept = DepartmentId.GENERAL_UNSPECIFIED
                reasoning = "[GENERAL OPD MODE] Unspecified/Insufficient evidence for sub-specialty. Routed to GENERAL_UNSPECIFIED."

        # Critical red flag recommendation adjustment
        if red_flag_result and red_flag_result.overall_severity == RedFlagSeverity.CRITICAL:
            dept = DepartmentId.EMERGENCY
            reasoning = f"[CRITICAL RED FLAG DETECTED] Priority Emergency Escalation Override: {reasoning}"

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
        logger.info("Generated department recommendation for %s in %s: %s (confidence: %.2f)",
                    session_id, opd_mode_str, dept.value, confidence)
        return rec
