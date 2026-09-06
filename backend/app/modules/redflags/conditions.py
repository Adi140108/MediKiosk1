import re
from typing import List, Dict, Any
from app.schemas.intake import PatientContextState

def match_rule_conditions(rule: Dict[str, Any], context: PatientContextState) -> bool:
    """
    Evaluates whether patient context satisfies the conditions of a red flag rule.
    """
    complaint = (context.chief_complaint or "").lower()
    associated = [s.lower() for s in context.associated_symptoms]
    character = (context.character or "").lower()
    onset = (context.onset or "").lower()

    combined_text = f"{complaint} {character} {onset} {' '.join(associated)} {' '.join(context.known_information)}".lower()

    # 1. Check primary trigger keywords
    keyword_hit = any(kw.lower() in combined_text for kw in rule.get("keywords", []))

    if not keyword_hit:
        return False

    # 2. Check required secondary symptoms if specified
    req_symptoms = rule.get("required_symptoms", [])
    if req_symptoms:
        has_secondary = any(rs in combined_text for rs in req_symptoms)
        # Or if severity is explicitly extreme (e.g. 9 or 10)
        if not has_secondary and (context.severity or 0) < 9:
            return False

    return True
