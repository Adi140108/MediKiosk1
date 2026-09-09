import logging
from typing import Dict, Any, List, Optional
from app.schemas.intake import PatientContextState, SocraticStage
from app.modules.intake.question_priority import calculate_candidate_priority
from app.modules.intake.socratic_engine import SocraticEngine
from app.modules.ayush.question_planner import AyushQuestionPlanner, AyushAssessmentSessionState

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
    ],
    "fever_respiratory": [
        {"id": "fever_pattern", "objective": "Determine fever pattern", "category": "CHIEF_COMPLAINT", "field": "character", "question": "Does the fever stay high continuously or come and go with chills and sweating?"},
        {"id": "fever_cough", "objective": "Check respiratory symptoms", "category": "SYMPTOM_CHARACTER", "field": "associated_symptoms", "question": "Do you have a dry cough, cough with mucus/phlegm, or difficulty breathing?"},
        {"id": "fever_redflag", "objective": "Check respiratory red flags", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Are you having chest pain, severe shortness of breath, or blue discoloration of lips?"}
    ],
    "skin_allergy": [
        {"id": "skin_loc", "objective": "Determine location", "category": "CHIEF_COMPLAINT", "field": "location", "question": "Where on your body is the rash or itching located — face, arms, legs, or all over?"},
        {"id": "skin_trigger", "objective": "Assess allergic triggers", "category": "LIFESTYLE", "field": "aggravating_factors", "question": "Did this start after using new soap, cosmetics, medication, or eating specific foods?"}
    ],
    "weakness_fatigue": [
        {"id": "fatigue_onset", "objective": "Determine onset", "category": "CHIEF_COMPLAINT", "field": "onset", "question": "Did the fatigue or dizziness come on suddenly today or has it developed gradually over weeks?"},
        {"id": "fatigue_assoc", "objective": "Check anemia and systemic signs", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Have you noticed paleness, fainting spells, breathlessness on climbing stairs, or dark stools?"}
    ],
    "gastro_nausea": [
        {"id": "gastro_freq", "objective": "Assess frequency", "category": "SYMPTOM_CHARACTER", "field": "character", "question": "How many times have you had loose stools or vomiting today, and can you keep liquids down?"},
        {"id": "gastro_fever", "objective": "Check fever and dehydration", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Do you feel extreme thirst, dry mouth, weakness, or high fever with the stomach upset?"}
    ],
    "urinary_flank": [
        {"id": "urinary_char", "objective": "Assess dysuria", "category": "CHIEF_COMPLAINT", "field": "character", "question": "Is there severe burning pain during urination, or high frequency and urgency?"},
        {"id": "urinary_redflag", "objective": "Check flank pain and fever", "category": "RED_FLAG", "field": "associated_symptoms", "question": "Do you have severe back/side flank pain, high fever with chills, or blood in urine?"}
    ]
}

def is_candidate_already_addressed(cand: Dict[str, Any], context: PatientContextState) -> bool:
    field = cand.get("field")
    obj = (cand.get("objective") or "").lower()
    cand_id = cand.get("id", "")

    if field == "duration" or "duration" in obj or cand_id == "gen_duration":
        if context.duration and len(str(context.duration).strip()) > 0:
            return True
    if field == "location" or "location" in obj or cand_id == "gen_location":
        if context.location and len(str(context.location).strip()) > 0:
            return True
    if field == "onset" or "onset" in obj or cand_id == "gen_onset":
        if context.onset and len(str(context.onset).strip()) > 0:
            return True
    if field == "severity" or "severity" in obj or cand_id == "gen_severity":
        if context.severity is not None and str(context.severity) != "0":
            return True
    if field == "character" or "character" in obj or cand_id == "gen_character":
        if context.character and len(str(context.character).strip()) > 0:
            return True
    return False

class AdaptiveBranchingEngine:
    def __init__(
        self,
        socratic_engine: Optional[SocraticEngine] = None,
        ayush_planner: Optional[AyushQuestionPlanner] = None
    ):
        self.socratic = socratic_engine or SocraticEngine()
        self.ayush_planner = ayush_planner or AyushQuestionPlanner()

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

    def calculate_confidence_score(self, context: PatientContextState) -> float:
        score = 0.0
        if context.chief_complaint:
            score += 0.25
        if context.location:
            score += 0.15
        if context.onset:
            score += 0.15
        if context.duration:
            score += 0.15
        if context.severity is not None:
            score += 0.10
        if context.character:
            score += 0.10
        if context.associated_symptoms and len(context.associated_symptoms) > 0:
            score += 0.10
        return min(1.0, score)

    def select_next_question_candidate(
        self,
        context: PatientContextState,
        asked_question_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Hard OPD Mode Boundary Question Selection:
        GENERAL_OPD: General Socratic planner only. AYUSH questions are strictly excluded.
        AYUSH_OPD:
          Phase 1: Safety / Red flags
          Phase 2: Socratic complaint clarification
          Phase 3: Core AYUSH profile & complaint-specific assessment planner questions
          Phase 4: Stop when evidence is sufficient.
        """
        mode_str = str(getattr(context, "opd_mode", "GENERAL_OPD")).upper()
        is_ayush = "AYUSH" in mode_str

        complaint = (context.chief_complaint or "").lower()
        missing = self.identify_missing_information(context)
        context.missing_information = missing

        confidence = self.calculate_confidence_score(context)

        asked_interview_ids = [qid for qid in asked_question_ids if qid != "initial_chief_complaint"]
        asked_count = len(asked_interview_ids)

        # 1. Termination logic
        if asked_count >= 10:
            context.is_sufficient = True
            return None

        min_required = 6 if is_ayush else 4
        if asked_count >= min_required and confidence >= 0.85 and len(missing) == 0:
            context.is_sufficient = True
            return None

        candidates: List[Dict[str, Any]] = []

        # 2. Symptom pathway matching (Socratic Clinical Clarification)
        head_keywords = ["headache", "head ache", "head pain", "migraine", "सिरदर्द", "सरदर्द", "सिर दर्द", "सर दर्द", "सिर", "माथा", "कपाल", "तलेनोवु", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42>", "தலைவலி", "தலை", "తలనొప్పి", "తల", "തലവേദന", "തല", "মাথাব্যথা", "মাথা", "માથાનો દુખાવો", "માથું", "ਸਿਰ ਦਰਦ", "ਸਿਰ", "head"]
        chest_keywords = ["chest", "heart", "cardio", "सीने", "छाती", "हृदय", "सीना", "दिल", "एदे", "<ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "மார்", "மார்பு", "மார்புவலி", "గుండె", "ఛాతీ", "ఛాతీనొప్పి", "നെഞ്ച്", "നെഞ്ചുവേദന", "বুক", "বুকে ব্যথা", "છાતી", "છાતીમાં", "ਛਾਤੀ"]
        joint_keywords = ["joint", "knee", "back", "bone", "spine", "arthritis", "जोड़", "घुटने", "कमर", "पीठ", "हड्डी", "कंधा", "<ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "மூட்டு", "மூட்டுவலி", "முழங்கால்", "முதுகு", "కీలు", "మోకాలు", "వెన్ను", "కీళ్లనొప్పి", "സന്ധി", "മുട്ട്", "സന്ധിവേദന", "হাঁটু", "জয়েন্ট", "સાંધા", "ઘૂંટણ", "સાંધાનો દુખાવો", "ਜੋੜ", "ਗੋਡੇ"]
        abdo_keywords = ["stomach", "abdo", "abdomen", "belly", "gastric", "acidity", "पेट", "आमाशय", "जठर", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "വയிறு", "வயிற்றுவலி", "కడుపు", "కడుపునొప్పి", "വയർ", "വയറുവേദന", "પેટ", "પેટનો દુખાવો", "ਪੇਟ", "ਪੇਟ ਦਰਦ", "পেট", "পেটে ব্যথা"]
        fever_keywords = ["fever", "cough", "cold", "flu", "throat", "chills", "phlegm", "sore throat", "बुखार", "खांसी", "जुकाम", "सर्दी", "गले", "कफ", "ਜੁਕਾਮ", "ਬੁਖਾਰ", "ਕਾਸੀ", "জ্বর", "কাশি", "તાવ", "ઉધરસ", "జ్వరం", "దగ్గు", "பாய்ச்சல்", "இருமல்", "ಜ್ವರ", "ಕೆಮ್ಮು", "പനി", "ചുമ"]
        skin_keywords = ["rash", "itching", "skin", "allergy", "lesion", "red spots", "खुजली", "दाद", "त्वचा", "ચામડી", "ਖੁਜਲੀ", "চুলকানি", "દાદર", "துடைக்கும்", "சருமம்", "చర్మం", "దురద", "ചൊറിച്ചിൽ", "ചർമ്മം"]
        fatigue_keywords = ["tired", "weakness", "fatigue", "dizziness", "giddiness", "faint", "थकान", "कमजोरी", "चक्कर", "સુસ્ત", "કમજોરી", "દાદર", "ਥਕਾਵਟ", "ਕਮਜ਼ੋਰੀ", "দুর্বলতা", "சோர்வு", "தலைசுற்றல்", "నీరసం", "తలతిరుగుడు", "ക്ഷീണം", "തലകറക്കം"]
        gastro_keywords = ["vomit", "diarrhea", "loose motion", "nausea", "indigestion", "दस्त", "उल्टी", "जी मिचलाना", "<ctrl42><ctrl42><ctrl42><ctrl42><ctrl42><ctrl42>", "வாந்தி", "பேதி", "வாந்தி உணர்வு", "వికారము", "విరోచనాలు", "ഛർദ്ദി", "വയറിളക്കം", "বমি", "পাতলা পায়খানা", "ઝાડા", "ઉલટી"]
        urinary_keywords = ["urine", "urination", "burning urine", "kidney", "dysuria", "पेशाब", "मूत्र", "મૂત્ર", "ਪਿਸ਼ਾਬ", "மூത്രം", "మూత్రం", "മൂത്രം"]

        matched_pathways: List[str] = []
        if any(k in complaint for k in chest_keywords): matched_pathways.append("chest_pain")
        if any(k in complaint for k in joint_keywords): matched_pathways.append("joint_pain")
        if any(k in complaint for k in abdo_keywords): matched_pathways.append("abdominal_pain")
        if any(k in complaint for k in head_keywords): matched_pathways.append("headache")
        if any(k in complaint for k in fever_keywords): matched_pathways.append("fever_respiratory")
        if any(k in complaint for k in skin_keywords): matched_pathways.append("skin_allergy")
        if any(k in complaint for k in fatigue_keywords): matched_pathways.append("weakness_fatigue")
        if any(k in complaint for k in gastro_keywords): matched_pathways.append("gastro_nausea")
        if any(k in complaint for k in urinary_keywords): matched_pathways.append("urinary_flank")

        for pathway_key in matched_pathways:
            if pathway_key in SYMPTOM_PATHWAYS:
                for item in SYMPTOM_PATHWAYS[pathway_key]:
                    if item["id"] not in asked_question_ids and not is_candidate_already_addressed(item, context):
                        candidates.append(item)

        if not is_ayush:
            # Strictly GENERAL_OPD: add general Socratic fallback exploration questions
            fallback_pool = [
                {"id": "gen_duration", "objective": "Determine duration", "category": "CHIEF_COMPLAINT", "field": "duration", "question": "How many days or hours have you been experiencing this health problem?"},
                {"id": "gen_severity", "objective": "Determine severity", "category": "SYMPTOM_CHARACTER", "field": "severity", "question": "On a scale from 1 (mild) to 10 (unbearable), how severe is your discomfort right now?"},
                {"id": "gen_aggravating", "objective": "Assess aggravating factors", "category": "LIFESTYLE", "field": "aggravating_factors", "question": "What specific activities, foods, movements, or postures make your symptoms worse or better?"},
                {"id": "gen_impact", "objective": "Assess daily life impact", "category": "LIFESTYLE", "field": "lifestyle_impact", "question": "How is this health issue affecting your sleep, daily work, appetite, or energy levels?"},
                {"id": "gen_prev_episodes", "objective": "Assess previous history", "category": "HISTORY", "field": "past_episodes", "question": "Have you ever experienced similar health problems or symptoms in the past?"},
                {"id": "gen_med_relief", "objective": "Assess medication response", "category": "MEDICATION", "field": "medication_response", "question": "Have you taken any medicines or home remedies for this today, and did they provide any relief?"},
                {"id": "gen_systemic_assoc", "objective": "Check associated systemic symptoms", "category": "SYSTEMIC_EXPLORATION", "field": "associated_symptoms", "question": "Are you experiencing any other symptoms like fever, fatigue, dizziness, nausea, or sweating?"}
            ]
            for fallback_item in fallback_pool:
                if fallback_item["id"] not in asked_question_ids and not is_candidate_already_addressed(fallback_item, context):
                    candidates.append(fallback_item)

            if not candidates:
                context.is_sufficient = True
                return None

            candidates.sort(key=lambda c: calculate_candidate_priority(c, opd_mode="GENERAL_OPD"))
            return candidates[0]

        else:
            # Strictly AYUSH_OPD Mode
            # If red flags or symptom clarification candidates exist, prioritize them first
            if candidates:
                candidates.sort(key=lambda c: calculate_candidate_priority(c, opd_mode="AYUSH_OPD"))
                return candidates[0]

            # Next Phase: AYUSH Core & Complaint-Specific Assessment Questions via AyushQuestionPlanner
            state = AyushAssessmentSessionState(
                session_id=getattr(context, "session_id", "active_session"),
                patient_id=getattr(context, "patient_id", "patient"),
                opd_mode="AYUSH_OPD",
                asked_question_ids=list(asked_question_ids)
            )
            ayush_q = self.ayush_planner.select_next_question(state, asked_ids=list(asked_question_ids))
            if ayush_q:
                q_text = ayush_q.get("patient_text") or ayush_q.get("question") or ayush_q.get("question_patient_language", {}).get("en") or ayush_q.get("question_en") or ayush_q.get("text", "")
                feature_targets = ayush_q.get("feature_targets") or []
                feature_str = ", ".join(feature_targets) if isinstance(feature_targets, list) else str(feature_targets)
                if not feature_str:
                    feature_str = ayush_q.get("sub_domain") or ayush_q.get("domain", "")

                obj_str = ayush_q.get("objective") or f"Assess {ayush_q.get('domain')} - {feature_str}"
                disp_label = ayush_q.get("ayurvedic_label") or f"{ayush_q.get('domain')} ({feature_str})"

                return {
                    "id": ayush_q.get("question_id"),
                    "question_id": ayush_q.get("question_id"),
                    "objective": obj_str,
                    "category": "AYURVEDIC",
                    "ayurvedic_domain": str(ayush_q.get("domain", "AYUSH")).lower(),
                    "display_label": disp_label,
                    "question": q_text,
                    "options": ayush_q.get("options", []),
                    "answer_type": ayush_q.get("answer_type", "single_choice"),
                    "feature": feature_str
                }

            # If AYUSH question planner is exhausted and sufficiency is reached
            context.is_sufficient = True
            return None
