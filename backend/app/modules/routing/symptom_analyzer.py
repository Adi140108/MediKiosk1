from typing import Dict, List, Tuple, Any, Optional
from app.schemas.routing import DepartmentId

# General OPD keyword rules (No AYUSH keywords!)
GENERAL_DEPARTMENT_KEYWORD_RULES: Dict[DepartmentId, List[str]] = {
    DepartmentId.CARDIOLOGY: ["chest pain", "chest tightness", "angina", "palpitation", "arrhythmia", "shortness of breath", "shortness of breath on exertion", "chest pressure", "sweating with chest discomfort", "radiating chest pain", "heart pain", "cardiac"],
    DepartmentId.NEUROLOGY: ["migraine", "severe headache", "thunderclap headache", "head pain", "dizziness", "vertigo", "seizure", "numbness", "stroke", "tremor", "loss of balance", "facial droop", "slurred speech", "paralysis"],
    DepartmentId.ORTHOPEDICS: ["joint pain", "knee pain", "leg pain", "back pain", "bone fracture", "severe back pain", "arthritis", "sprain", "shoulder pain", "swelling in joint", "morning stiffness", "dislocation"],
    DepartmentId.GASTROENTEROLOGY: ["stomach pain", "severe stomach pain", "abdominal pain", "belly ache", "acid reflux", "bloating", "vomiting blood", "chronic diarrhea", "jaundice", "abdominal cramps", "gastric burning", "black stools"],
    DepartmentId.DERMATOLOGY: ["skin rash", "severe itching", "itching", "allergy", "eczema", "psoriasis", "acne", "hair fall", "skin lesion", "hives", "red spots", "dermatitis"],
    DepartmentId.ENT: ["ear pain", "severe ear pain", "hearing loss", "tonsillitis", "sinusitis", "nasal blockage", "tinnitus", "ear discharge", "foreign body in ear", "sore throat"],
    DepartmentId.OPHTHALMOLOGY: ["eye pain", "blurred vision", "cataract", "red eye", "double vision", "visual disturbance", "eye discharge", "corneal injury", "vision loss"],
    DepartmentId.PSYCHIATRY: ["anxiety", "severe depression", "depression", "panic attacks", "insomnia", "hallucinations", "extreme stress", "bipolar", "suicidal ideation"],
    DepartmentId.PEDIATRICS: ["child fever", "infant vomiting", "pediatric rash", "growth concerns", "childhood cough", "infant distress"],
    DepartmentId.GENERAL_MEDICINE: ["headache", "mild headache", "fever", "fatigue", "body ache", "malaise", "cough", "cold", "unexplained weight loss", "chills", "weakness", "general checkup", "viral fever", "routine consultation", "normal symptoms"]
}

# AYUSH OPD keyword rules
AYUSH_DEPARTMENT_KEYWORD_RULES: Dict[DepartmentId, List[str]] = {
    DepartmentId.KAYACHIKITSA: ["indigestion", "agni", "digestive fire", "metabolic", "dhatu", "ama", "fever", "jwara", "gastro", "constipation", "stomach pain", "acid reflux", "chest tightness", "shortness of breath", "fatigue"],
    DepartmentId.PANCHAKARMA: ["detox", "shodhana", "panchakarma", "purification", "vamana", "virechana", "basti", "nasya", "chronic toxin", "saama"],
    DepartmentId.SHALYA: ["joint pain", "musculoskeletal", "spine", "fracture", "structural", "shalya", "back pain", "knee pain", "bone pain"],
    DepartmentId.SHALAKYA: ["headache", "migraine", "ear pain", "eye pain", "throat", "sinusitis", "shalakya", "nasal", "head pain", "shirah shoola"],
    DepartmentId.PRASUTI_STRI: ["maternal", "gynecological", "menstrual", "pregnancy", "stree roga", "prasuti"],
    DepartmentId.KAUMARABHRITYA: ["child", "pediatric", "infant", "balaroga", "kaumarabhritya"],
    DepartmentId.SWASTHAVRITTA: ["preventive", "yoga", "lifestyle", "dinacharya", "ritucharya", "swasthavritta", "wellness", "stress"],
    DepartmentId.AGADATANTRA: ["allergy", "toxicity", "skin rash", "insect bite", "agada", "poisoning", "itching"]
}

def analyze_symptoms_for_department(
    symptoms_text: str,
    patient_age: int = 30,
    opd_mode: str = "GENERAL_OPD"
) -> Tuple[DepartmentId, float, str, str, List[str], List[Dict[str, Any]], Dict[str, float]]:
    """
    Evaluates patient symptoms, age, and mode for department triage.
    GENERAL_OPD: Only routes to General departments. Returns GENERAL_UNSPECIFIED if evidence is ambiguous/insufficient.
    AYUSH_OPD: Only routes to AYUSH departments. Returns AYUSH_UNSPECIFIED if evidence is ambiguous/insufficient.
    """
    text = symptoms_text.lower()
    is_ayush = "AYUSH" in str(opd_mode or "GENERAL_OPD").upper()

    # Rule 1: Pediatric Age Protocol (0 to 18 years)
    if 0 <= patient_age <= 18:
        target_dept = DepartmentId.KAUMARABHRITYA if is_ayush else DepartmentId.PEDIATRICS
        fallback_dept = DepartmentId.AYUSH if is_ayush else DepartmentId.GENERAL_MEDICINE
        return (
            target_dept,
            0.95,
            "High",
            f"Pediatric patient (Age {patient_age} <= 18 yrs) routed to {target_dept.value.title()} for specialized age-appropriate clinical care.",
            [f"Pediatric age group ({patient_age} yrs <= 18)", "Pediatric clinical triage protocol"],
            [{"department": fallback_dept.value, "score": 0.05}],
            {target_dept.value: 0.95, fallback_dept.value: 0.05}
        )

    rules = AYUSH_DEPARTMENT_KEYWORD_RULES if is_ayush else GENERAL_DEPARTMENT_KEYWORD_RULES
    default_unspecified = DepartmentId.AYUSH_UNSPECIFIED if is_ayush else DepartmentId.GENERAL_UNSPECIFIED
    default_primary = DepartmentId.AYUSH if is_ayush else DepartmentId.GENERAL_MEDICINE

    raw_scores: Dict[DepartmentId, float] = {}
    matched_kws: Dict[DepartmentId, List[str]] = {}

    for dept, keywords in rules.items():
        count = 0.0
        hits = []
        for kw in keywords:
            if kw in text:
                count += 1.0
                hits.append(kw.title())
        if count > 0:
            raw_scores[dept] = count
            matched_kws[dept] = hits

    if not raw_scores:
        return (
            default_unspecified,
            0.50,
            "Low",
            f"Insufficient or unmapped evidence for specific specialty. Routed to {default_unspecified.value.title()}.",
            ["Unmapped or ambiguous clinical presentation"],
            [{"department": default_primary.value, "score": 0.50}],
            {default_unspecified.value: 0.50, default_primary.value: 0.50}
        )

    total_raw = sum(raw_scores.values())
    dept_scores: Dict[str, float] = {
        dept.value: round(score / total_raw, 2)
        for dept, score in sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    }

    sorted_depts = sorted(raw_scores.items(), key=lambda x: x[1], reverse=True)
    best_dept, best_raw = sorted_depts[0]
    best_prob = dept_scores[best_dept.value]

    matched_evidence = matched_kws.get(best_dept, [])
    alternatives = [
        {"department": d.value, "score": dept_scores[d.value]}
        for d, _ in sorted_depts[1:4]
    ]

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
