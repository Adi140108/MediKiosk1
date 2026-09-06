from typing import Dict, List, Tuple, Any
from app.schemas.routing import DepartmentId

DEPARTMENT_KEYWORD_RULES: Dict[DepartmentId, List[str]] = {
    DepartmentId.CARDIOLOGY: ["chest pain", "angina", "palpitation", "arrhythmia", "shortness of breath on exertion", "chest pressure", "sweating with chest discomfort", "radiating chest pain"],
    DepartmentId.NEUROLOGY: ["migraine", "dizziness", "vertigo", "seizure", "numbness", "stroke", "tremor", "loss of balance", "facial droop", "slurred speech", "paralysis"],
    DepartmentId.ORTHOPEDICS: ["joint pain", "knee pain", "bone fracture", "severe back pain", "arthritis", "sprain", "shoulder pain", "swelling in joint", "morning stiffness", "dislocation"],
    DepartmentId.GASTROENTEROLOGY: ["severe stomach pain", "acid reflux", "bloating", "vomiting blood", "chronic diarrhea", "jaundice", "abdominal cramps", "gastric burning", "black stools"],
    DepartmentId.DERMATOLOGY: ["skin rash", "severe itching", "eczema", "psoriasis", "acne", "hair fall", "skin lesion", "hives", "red spots", "dermatitis"],
    DepartmentId.ENT: ["severe ear pain", "hearing loss", "tonsillitis", "sinusitis", "nasal blockage", "tinnitus", "ear discharge", "foreign body in ear"],
    DepartmentId.OPHTHALMOLOGY: ["eye pain", "blurred vision", "cataract", "red eye", "double vision", "visual disturbance", "eye discharge", "corneal injury"],
    DepartmentId.PSYCHIATRY: ["anxiety", "severe depression", "panic attacks", "insomnia", "hallucinations", "extreme stress", "bipolar", "suicidal ideation"],
    DepartmentId.PEDIATRICS: ["child fever", "infant vomiting", "pediatric rash", "growth concerns", "childhood cough", "infant distress"],
    DepartmentId.AYUSH: ["chronic indigestion", "holistic wellness", "ayurvedic rejuvenation", "vata imbalance", "pitta", "kapha", "mandagni", "dosha consultation"],
    DepartmentId.GENERAL_MEDICINE: ["fever", "fatigue", "body ache", "malaise", "cough", "cold", "unexplained weight loss", "chills", "weakness", "mild headache", "general checkup", "viral fever", "routine consultation", "normal symptoms"]
}

def analyze_symptoms_for_department(
    symptoms_text: str,
    patient_age: int = 30
) -> Tuple[DepartmentId, float, str, str, List[str], List[Dict[str, Any]], Dict[str, float]]:
    """
    Evaluates patient symptoms, age, and clinical presentation for department triage:
    1. Patients aged 0-18 are strictly routed to Pediatrics.
    2. Common/mild/normal symptoms without focal sub-specialty findings route to General Medicine.
    3. Specific sub-specialties require distinct clinical keyword matches with sufficient confidence.
    """
    text = symptoms_text.lower()

    # Rule 1: Pediatric Age Protocol (0 to 18 years)
    if 0 <= patient_age <= 18:
        return (
            DepartmentId.PEDIATRICS,
            0.95,
            "High",
            f"Pediatric patient (Age {patient_age} <= 18 yrs) routed to Pediatrics for specialized age-appropriate clinical care.",
            [f"Pediatric age group ({patient_age} yrs <= 18)", "Pediatric clinical triage protocol"],
            [{"department": DepartmentId.GENERAL_MEDICINE.value, "score": 0.05}],
            {DepartmentId.PEDIATRICS.value: 0.95, DepartmentId.GENERAL_MEDICINE.value: 0.05}
        )

    # Score sub-specialties
    raw_scores: Dict[DepartmentId, float] = {}
    matched_kws: Dict[DepartmentId, List[str]] = {}

    for dept, keywords in DEPARTMENT_KEYWORD_RULES.items():
        count = 0.0
        hits = []
        for kw in keywords:
            if kw in text:
                count += 1.0
                hits.append(kw.title())
        if count > 0:
            raw_scores[dept] = count
            matched_kws[dept] = hits

    # Rule 2: Normal / Mild / Constitutional symptoms route to General Medicine
    if not raw_scores:
        return (
            DepartmentId.GENERAL_MEDICINE,
            0.85,
            "High",
            "General / constitutional symptoms or routine clinical consultation. Routed to General Medicine.",
            ["Primary care / general clinical evaluation", "General constitutional presentation"],
            [{"department": DepartmentId.UNSPECIFIED.value, "score": 0.15}],
            {DepartmentId.GENERAL_MEDICINE.value: 0.85, DepartmentId.UNSPECIFIED.value: 0.15}
        )

    # Normalize raw scores to probabilities summing to 1.0
    total_raw = sum(raw_scores.values())
    dept_scores: Dict[str, float] = {
        dept.value: round(score / total_raw, 2)
        for dept, score in sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    }

    sorted_depts = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    best_dept, best_raw = sorted_depts[0]
    best_prob = dept_scores[best_dept.value]
    runner_up = sorted_depts[1] if len(sorted_depts) > 1 else None

    matched_evidence = matched_kws.get(best_dept, [])
    alternatives = [
        {"department": d.value, "score": dept_scores[d.value]}
        for d, _ in sorted_depts[1:4]
    ]

    # Ambiguity handling: If runner-up is very close or top score is low, offer alternatives
    is_ambiguous = False
    if runner_up:
        diff = best_prob - dept_scores[runner_up[0].value]
        if diff < 0.12 and best_prob < 0.60:
            is_ambiguous = True

    if is_ambiguous:
        return (
            DepartmentId.GENERAL_MEDICINE,
            best_prob,
            "Medium",
            f"Multi-system symptoms ({best_dept.value.title()} vs {runner_up[0].value.title()}). Routed to General Medicine for comprehensive primary evaluation.",
            matched_evidence,
            [{"department": best_dept.value, "score": best_prob}] + alternatives,
            dept_scores
        )

    conf_level = "High" if best_prob >= 0.70 else "Medium"
    reasoning = f"Matched primary clinical symptoms for {best_dept.value.title()}: {', '.join(matched_evidence)}."

    return (
        best_dept,
        best_prob,
        conf_level,
        reasoning,
        matched_evidence,
        alternatives,
        dept_scores
    )
