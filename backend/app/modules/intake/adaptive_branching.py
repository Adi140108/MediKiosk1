import logging
from typing import Dict, Any, List, Optional
from app.schemas.intake import PatientContextState, SocraticStage
from app.modules.intake.ayurvedic_questioning import AyurvedicQuestionEngine
from app.modules.intake.question_priority import calculate_candidate_priority
from app.modules.intake.socratic_engine import SocraticEngine

logger = logging.getLogger("medikiosk.intake.branching")

# Symptom-specific question pathways and objective definitions
SYMPTOM_PATHWAYS = {
    "headache": [
        {"id": "headache_loc", "objective": "Determine location", "category": "CHIEF_COMPLAINT", "field": "location", "question": "Where exactly in your head do you feel the pain — on one side, all over, in the forehead, or at the back?"},
        {"id": "headache_onset", "objective": "Determine onset", "category": "CHIEF_COMPLAINT", "field": "onset", "question": "Did this headache start suddenly all of a sudden, or did it develop gradually over time?"},
        {"id": "headache_char", "objective": "Determine character", "category": "SYMPTOM_CHARACTER", "field": "character", "question": "How would you describe the headache — throbbing, dull ache, sharp, or pressing pressure?"},
        {"id": "headache_redflag_neuro", "objective": "Check neurological red flags", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Have you noticed any vomiting, vision changes, weakness in limbs, or neck stiffness with this headache?"},
        {"id": "headache_trigger", "objective": "Assess triggers", "category": "LIFESTYLE", "field": "aggravating_factors", "question": "Does bright light, loud sound, or physical exertion make the headache worse?"}
    ],
    "abdominal_pain": [
        {"id": "abdo_loc", "objective": "Determine location", "category": "CHIEF_COMPLAINT", "field": "location", "question": "Where in your abdomen is the discomfort located — upper, lower, central, right, or left side?"},
        {"id": "abdo_food_rel", "objective": "Assess food relationship", "category": "CHIEF_COMPLAINT", "field": "aggravating_factors", "question": "Does the pain start right after eating, or does it happen when you have an empty stomach?"},
        {"id": "abdo_char", "objective": "Determine character", "category": "SYMPTOM_CHARACTER", "field": "character", "question": "Is the stomach pain cramping, burning, dull, or sharp?"},
        {"id": "abdo_redflag", "objective": "Check red flag bleeding/fever", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Have you had high fever, persistent vomiting, or any blood in your vomit or stool?"}
    ],
    "chest_pain": [
        {"id": "chest_redflag_rad", "objective": "Determine radiation", "category": "RED_FLAG", "field": "location", "question": "Does the chest discomfort spread to your left arm, shoulder, neck, jaw, or back?"},
        {"id": "chest_onset", "objective": "Determine onset and breath", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Are you experiencing shortness of breath, sweating, or lightheadedness along with the chest pain?"},
        {"id": "chest_char", "objective": "Determine character", "category": "SYMPTOM_CHARACTER", "field": "character", "question": "How does the chest sensation feel — heaviness, squeezing pressure, sharp, or burning?"}
    ],
    "joint_pain": [
        {"id": "joint_loc", "objective": "Determine location", "category": "CHIEF_COMPLAINT", "field": "location", "question": "Which specific joints are hurting or swollen — knees, shoulders, hips, fingers, or spine?"},
        {"id": "joint_duration", "objective": "Determine morning stiffness", "category": "SYMPTOM_CHARACTER", "field": "character", "question": "Do you feel stiff in the mornings, and how long does it take for the stiffness to ease?"},
        {"id": "joint_trauma", "objective": "Assess injury history", "category": "CHIEF_COMPLAINT", "field": "onset", "question": "Did this pain start after a recent fall, twist, injury, or physical strain?"}
    ]
}

class AdaptiveBranchingEngine:
    def __init__(
        self,
        ayurvedic_engine: Optional[AyurvedicQuestionEngine] = None,
        socratic_engine: Optional[SocraticEngine] = None
    ):
        self.ayurvedic = ayurvedic_engine or AyurvedicQuestionEngine()
        self.socratic = socratic_engine or SocraticEngine()

    def identify_missing_information(self, context: PatientContextState) -> List[str]:
        missing = []
        if not context.chief_complaint:
            missing.append("chief_complaint")
        if not context.location:
            missing.append("location")
        if not context.onset:
            missing.append("onset")
        if not context.duration:
            missing.append("duration")
        if context.severity is None:
            missing.append("severity")
        if not context.character:
            missing.append("character")
        if not context.associated_symptoms:
            missing.append("associated_symptoms")
        return missing

    def select_next_question_candidate(
        self,
        context: PatientContextState,
        asked_question_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Dynamically chooses the next question candidate based on symptom branching,
        missing information, red-flag priorities, and Ayurvedic relevance.
        """
        complaint = (context.chief_complaint or "").lower()
        missing = self.identify_missing_information(context)
        context.missing_information = missing

        # 1. Check if we should stop
        if context.question_count >= 10 or (len(missing) == 0 and context.question_count >= 4):
            context.is_sufficient = True
            return None

        candidates: List[Dict[str, Any]] = []

        # 2. Determine symptom pathway
        pathway_key = None
        if "head" in complaint or "migraine" in complaint:
            pathway_key = "headache"
        elif "stomach" in complaint or "abdo" in complaint or "belly" in complaint:
            pathway_key = "abdominal_pain"
        elif "chest" in complaint or "heart" in complaint:
            pathway_key = "chest_pain"
        elif "joint" in complaint or "knee" in complaint or "back" in complaint or "bone" in complaint:
            pathway_key = "joint_pain"

        if pathway_key and pathway_key in SYMPTOM_PATHWAYS:
            for item in SYMPTOM_PATHWAYS[pathway_key]:
                field = item.get("field")
                # Do not ask if we already know this field or question was already asked
                if field and getattr(context, field, None) and item["id"] in asked_question_ids:
                    continue
                if item["id"] not in asked_question_ids:
                    candidates.append(item)

        # 3. Add relevant Ayurvedic candidates
        relevant_domains = self.ayurvedic.get_relevant_domains(context.chief_complaint or "", context.associated_symptoms)
        for domain in relevant_domains:
            q_id = f"ayur_{domain.lower()}"
            if q_id not in asked_question_ids:
                ayur_item = self.ayurvedic.generate_patient_friendly_question(domain)
                candidates.append({
                    "id": q_id,
                    "objective": ayur_item["objective"],
                    "category": "AYURVEDIC",
                    "ayurvedic_domain": ayur_item["ayurvedic_domain"],
                    "display_label": ayur_item["display_label"],
                    "question": ayur_item["question"]
                })

        # 4. Fallback general clinical questions if no candidate from pathway
        if not candidates:
            if "duration" in missing and "gen_duration" not in asked_question_ids:
                candidates.append({
                    "id": "gen_duration",
                    "objective": "Determine duration",
                    "category": "CHIEF_COMPLAINT",
                    "question": "How many days or hours have you been experiencing this?"
                })
            elif "severity" in missing and "gen_severity" not in asked_question_ids:
                candidates.append({
                    "id": "gen_severity",
                    "objective": "Determine severity",
                    "category": "SYMPTOM_CHARACTER",
                    "question": "On a scale from 1 (mild) to 10 (unbearable), how severe is your discomfort right now?"
                })

        if not candidates:
            context.is_sufficient = True
            return None

        # 5. Sort candidates by Priority Tier (Red Flag > Chief Complaint > Character > Ayurvedic > Lifestyle)
        candidates.sort(key=calculate_candidate_priority)
        return candidates[0]
