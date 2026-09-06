from typing import List, Dict, Any
from app.schemas.redflag import RedFlagSeverity

# Deterministic Clinical Safety Rules
CLINICAL_RED_FLAG_RULES = [
    {
        "rule_id": "RF_CARD_01",
        "title": "Suspected Acute Coronary Syndrome",
        "category": "cardiac",
        "severity": RedFlagSeverity.CRITICAL,
        "keywords": ["chest pain", "chest pressure", "left arm pain", "jaw pain", "crushing chest"],
        "required_symptoms": ["shortness of breath", "sweating", "diaphoresis", "radiation"],
        "description": "Chest pain with radiation to arm/jaw or accompanied by shortness of breath/sweating.",
        "action_required": "Immediate ECG and Emergency/Cardiology Triage"
    },
    {
        "rule_id": "RF_NEURO_01",
        "title": "Suspected Intracranial Event / Thunderclap Headache",
        "category": "neurological",
        "severity": RedFlagSeverity.CRITICAL,
        "keywords": ["thunderclap", "worst headache", "sudden severe headache", "neck stiffness"],
        "required_symptoms": ["vomiting", "neck stiffness", "altered consciousness", "visual disturbance"],
        "description": "Sudden onset severe headache with neurological deficits, vomiting, or meningism.",
        "action_required": "Immediate Neurological assessment & Neuroimaging"
    },
    {
        "rule_id": "RF_RESP_01",
        "title": "Severe Respiratory Distress",
        "category": "respiratory",
        "severity": RedFlagSeverity.CRITICAL,
        "keywords": ["unable to breathe", "severe breathlessness", "gasping", "cyanosis", "stridor"],
        "required_symptoms": [],
        "description": "Severe difficulty breathing or airway compromise.",
        "action_required": "Immediate High-Flow Oxygen and Respiratory Triage"
    },
    {
        "rule_id": "RF_BLEED_01",
        "title": "Active Gastrointestinal / Massive Bleeding",
        "category": "bleeding",
        "severity": RedFlagSeverity.HIGH,
        "keywords": ["vomiting blood", "hematemesis", "black tarry stool", "melena", "rectal bleeding"],
        "required_symptoms": [],
        "description": "Evidence of significant active internal gastrointestinal bleeding.",
        "action_required": "Urgent IV Access, Fluid Resuscitation & GI Consult"
    },
    {
        "rule_id": "RF_SEPSIS_01",
        "title": "Systemic Infection / Sepsis Risk",
        "category": "sepsis",
        "severity": RedFlagSeverity.HIGH,
        "keywords": ["high fever", "rigors", "extreme lethargy", "confusion", "rapid heart rate"],
        "required_symptoms": [],
        "description": "High fever with altered sensorium or circulatory compromise.",
        "action_required": "Blood cultures, Lactate, IV Antibiotics"
    },
    {
        "rule_id": "RF_TRAUMA_01",
        "title": "Acute Bone Fracture / Deformity",
        "category": "trauma",
        "severity": RedFlagSeverity.MEDIUM,
        "keywords": ["bone fracture", "visible bone deformity", "unable to bear weight", "severe trauma"],
        "required_symptoms": [],
        "description": "Suspected acute fracture, significant swelling or restricted mobility following trauma.",
        "action_required": "Splinting and Urgent Orthopedic X-Ray"
    },
    {
        "rule_id": "RF_VISION_01",
        "title": "Acute Vision Loss / Eye Trauma",
        "category": "ophthalmology",
        "severity": RedFlagSeverity.HIGH,
        "keywords": ["sudden vision loss", "chemical eye injury", "severe eye pain", "flashes and floaters"],
        "required_symptoms": [],
        "description": "Sudden reduction in vision or chemical injury to the eye.",
        "action_required": "Emergency Eye Irrigation / Urgent Ophthalmology consult"
    }
]
