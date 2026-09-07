from enum import IntEnum
from typing import List, Dict, Any

class QuestionPriorityTier(IntEnum):
    RED_FLAG_SAFETY = 1       # Emergency / Critical ruling out
    CHIEF_COMPLAINT = 2       # Location, onset, duration
    SYMPTOM_CHARACTER = 3     # Character, severity, radiation
    ASSOCIATED_SYMPTOMS = 4   # Additional symptoms
    AYURVEDIC_ASSESSMENT = 5  # Relevant Agni/Mala/Nidra/Ahara/Vihara
    LIFESTYLE_CONTEXT = 6     # Daily routine, stress
    SUFFICIENT_STOP = 7       # Finished

def calculate_candidate_priority(candidate: Dict[str, Any], opd_mode: str = "GENERAL_OPD") -> int:
    """
    Ranks candidate question objectives according to clinical safety, intake hierarchy, and OPD mode.
    """
    category = candidate.get("category", "")
    if category == "RED_FLAG":
        return QuestionPriorityTier.RED_FLAG_SAFETY

    # In AYUSH OPD mode, prioritize Ayurvedic questions directly after emergency red flags
    if "AYUSH" in (opd_mode or "").upper() and (category == "AYURVEDIC" or candidate.get("ayurvedic_domain")):
        return QuestionPriorityTier.RED_FLAG_SAFETY + 1  # Tier 2 (before general questions)

    if category == "CHIEF_COMPLAINT" or candidate.get("objective") in ["Determine location", "Determine onset", "Determine duration"]:
        return QuestionPriorityTier.CHIEF_COMPLAINT
    if candidate.get("objective") in ["Determine character", "Determine severity", "Determine radiation"]:
        return QuestionPriorityTier.SYMPTOM_CHARACTER
    if category == "ASSOCIATED":
        return QuestionPriorityTier.ASSOCIATED_SYMPTOMS
    if category == "AYURVEDIC":
        return QuestionPriorityTier.AYURVEDIC_ASSESSMENT
    if category == "LIFESTYLE":
        return QuestionPriorityTier.LIFESTYLE_CONTEXT
    return QuestionPriorityTier.SUFFICIENT_STOP
