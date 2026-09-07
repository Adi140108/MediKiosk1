import logging
from typing import List, Dict, Any, Optional
from app.ai.gemma.prompts.ayurvedic_questioning import AYURVEDIC_DOMAIN_TEMPLATES

logger = logging.getLogger("medikiosk.intake.ayurveda")

# Clinical correlation: maps symptoms to relevant Ayurvedic assessment domains
SYMPTOM_AYURVEDIC_MAP = {
    "headache": ["PRAKRITI", "NIDRA", "MANASIKA", "VIHARA", "ANUPASHAYA"],
    "head": ["PRAKRITI", "NIDRA", "MANASIKA", "VIHARA"],
    "migraine": ["PRAKRITI", "NIDRA", "MANASIKA", "AHARA", "ANUPASHAYA"],
    "stomach": ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "AHARA", "MALA", "UPASHAYA"],
    "abdomen": ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "AHARA", "MALA", "UPASHAYA"],
    "abdominal": ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "AHARA", "MALA", "UPASHAYA"],
    "acidity": ["PRAKRITI", "AGNI", "AMA", "AHARA", "ANUPASHAYA"],
    "digestion": ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "AHARA", "MALA"],
    "chest": ["PRAKRITI", "VIHARA", "MANASIKA", "NIDANA"],
    "joint": ["PRAKRITI", "VIHARA", "NIDANA", "UPASHAYA", "ANUPASHAYA"],
    "knee": ["PRAKRITI", "VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "back": ["PRAKRITI", "VIHARA", "UPASHAYA", "ANUPASHAYA"],
    "skin": ["PRAKRITI", "AHARA", "VIHARA", "NIDANA"],
    "rash": ["PRAKRITI", "AHARA", "VIHARA", "NIDANA"],
    "fever": ["PRAKRITI", "AGNI", "AMA", "NIDANA", "UPASHAYA"],
    "cough": ["PRAKRITI", "AHARA", "VIHARA", "NIDANA"]
}

DEFAULT_AYURVEDIC_DOMAINS = ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "NIDRA", "SATVA", "AHARA", "VIHARA"]

class AyurvedicQuestionEngine:
    """
    Selects relevant Ayurvedic domains based on patient presentation
    and produces patient-friendly questions without technical jargon.
    """
    def get_relevant_domains(self, chief_complaint: str, associated_symptoms: List[str]) -> List[str]:
        complaint_lower = (chief_complaint or "").lower()
        all_text = complaint_lower + " " + " ".join([s.lower() for s in associated_symptoms])

        matched_domains = []
        for keyword, domains in SYMPTOM_AYURVEDIC_MAP.items():
            if keyword in all_text:
                for d in domains:
                    if d not in matched_domains:
                        matched_domains.append(d)

        # Include default core AYUSH domains to ensure thorough 26-domain coverage
        for d in DEFAULT_AYURVEDIC_DOMAINS:
            if d not in matched_domains:
                matched_domains.append(d)

        return matched_domains

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
