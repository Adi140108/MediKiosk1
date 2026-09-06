import logging
from typing import List, Dict, Any, Optional
from app.ai.gemma.prompts.ayurvedic_questioning import AYURVEDIC_DOMAIN_TEMPLATES

logger = logging.getLogger("medikiosk.intake.ayurveda")

# Clinical correlation: maps symptoms to relevant Ayurvedic assessment domains
SYMPTOM_AYURVEDIC_MAP = {
    "headache": ["NIDRA", "MANASIKA", "VIHARA", "ANUPASHAYA"],
    "head": ["NIDRA", "MANASIKA", "VIHARA"],
    "migraine": ["NIDRA", "MANASIKA", "AHARA", "ANUPASHAYA"],
    "सिर": ["NIDRA", "MANASIKA", "VIHARA"],
    "ತಲೆ": ["NIDRA", "MANASIKA", "VIHARA"],
    "தலை": ["NIDRA", "MANASIKA", "VIHARA"],
    "stomach": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "abdomen": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "abdominal": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "acidity": ["AGNI", "AHARA", "ANUPASHAYA"],
    "digestion": ["AGNI", "AHARA", "MALA"],
    "पेट": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "ಹೊಟ್ಟೆ": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "வயிறு": ["AGNI", "AHARA", "MALA", "UPASHAYA"],
    "chest": ["VIHARA", "MANASIKA", "NIDANA"],
    "सीने": ["VIHARA", "MANASIKA", "NIDANA"],
    "छाती": ["VIHARA", "MANASIKA", "NIDANA"],
    "ಎದೆ": ["VIHARA", "MANASIKA", "NIDANA"],
    "joint": ["VIHARA", "NIDANA", "UPASHAYA", "ANUPASHAYA"],
    "knee": ["VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "back": ["VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "जोड़": ["VIHARA", "NIDANA", "UPASHAYA", "ANUPASHAYA"],
    "घुटने": ["VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "ಕೀಲು": ["VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "skin": ["AHARA", "VIHARA", "NIDANA"],
    "rash": ["AHARA", "VIHARA", "NIDANA"],
    "fever": ["AGNI", "NIDANA", "UPASHAYA"],
    "बुखार": ["AGNI", "NIDANA", "UPASHAYA"],
    "ಜ್ವರ": ["AGNI", "NIDANA", "UPASHAYA"],
    "காய்ச்சல்": ["AGNI", "NIDANA", "UPASHAYA"],
    "cough": ["AHARA", "VIHARA", "NIDANA"],
    "खांसी": ["AHARA", "VIHARA", "NIDANA"],
    "ಕೆಮ್ಮು": ["AHARA", "VIHARA", "NIDANA"]
}

class AyurvedicQuestionEngine:
    """
    Selects relevant Ayurvedic domains based on patient presentation
    and produces patient-friendly questions without technical jargon.
    """
    def get_relevant_domains(self, chief_complaint: str, associated_symptoms: List[str]) -> List[str]:
        complaint_lower = (chief_complaint or "").lower()
        all_text = complaint_lower + " " + " ".join([s.lower() for s in associated_symptoms])

        matched_domains = set()
        for keyword, domains in SYMPTOM_AYURVEDIC_MAP.items():
            if keyword in all_text:
                matched_domains.update(domains)

        if not matched_domains:
            # Default general domains
            matched_domains = {"AGNI", "NIDRA", "AHARA"}

        return list(matched_domains)

    def generate_patient_friendly_question(self, domain: str) -> Dict[str, Any]:
        """
        Returns structured patient-friendly question data.
        """
        template = AYURVEDIC_DOMAIN_TEMPLATES.get(domain.upper())
        if not template:
            return {
                "ayurvedic_domain": domain,
                "display_label": f"({domain.title()})",
                "objective": f"Assess {domain.lower()}",
                "question": f"Could you describe how your {domain.lower()} has been recently? ({domain.title()})"
            }

        return {
            "ayurvedic_domain": template["domain"],
            "display_label": template["display_label"],
            "objective": template["objective"],
            "question": template["default_question"]
        }
