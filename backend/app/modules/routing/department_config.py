from typing import List, Dict, Any
from app.schemas.routing import DepartmentId, DepartmentInfo

# Centralized Department Registry
DEPARTMENTS_REGISTRY: List[DepartmentInfo] = [
    DepartmentInfo(
        id=DepartmentId.CARDIOLOGY,
        name="Cardiology",
        display_name="Cardiology",
        icon="🫀",
        description="Heart and cardiovascular care, chest pain, arrhythmias"
    ),
    DepartmentInfo(
        id=DepartmentId.NEUROLOGY,
        name="Neurology",
        display_name="Neurology",
        icon="🧠",
        description="Brain, spine, nervous system, headaches, stroke risk, seizures"
    ),
    DepartmentInfo(
        id=DepartmentId.ORTHOPEDICS,
        name="Orthopedics",
        display_name="Orthopedics",
        icon="🦴",
        description="Bones, joints, ligaments, fractures, arthritis"
    ),
    DepartmentInfo(
        id=DepartmentId.GENERAL_MEDICINE,
        name="General Medicine",
        display_name="General Medicine",
        icon="🩺",
        description="Adult primary care, systemic illnesses, fever, diabetes, hypertension"
    ),
    DepartmentInfo(
        id=DepartmentId.PEDIATRICS,
        name="Pediatrics",
        display_name="Pediatrics",
        icon="👶",
        description="Infant, child, and adolescent healthcare"
    ),
    DepartmentInfo(
        id=DepartmentId.GASTROENTEROLOGY,
        name="Gastroenterology",
        display_name="Gastroenterology",
        icon="🍽️",
        description="Digestive tract, stomach, liver, acid reflux, bowel disorders"
    ),
    DepartmentInfo(
        id=DepartmentId.DERMATOLOGY,
        name="Dermatology",
        display_name="Dermatology",
        icon="🧴",
        description="Skin, hair, nails, eczema, allergies, rashes"
    ),
    DepartmentInfo(
        id=DepartmentId.ENT,
        name="ENT",
        display_name="ENT",
        icon="👂",
        description="Ear, nose, throat, sinusitis, hearing, vertigo"
    ),
    DepartmentInfo(
        id=DepartmentId.OPHTHALMOLOGY,
        name="Ophthalmology",
        display_name="Ophthalmology",
        icon="👁",
        description="Eye disorders, vision changes, cataracts, infections"
    ),
    DepartmentInfo(
        id=DepartmentId.PSYCHIATRY,
        name="Psychiatry",
        display_name="Psychiatry",
        icon="🧩",
        description="Mental health, anxiety, depression, mood disorders"
    ),
    DepartmentInfo(
        id=DepartmentId.AYUSH,
        name="AYUSH",
        display_name="AYUSH",
        icon="🌿",
        description="Ayurveda, Yoga, Unani, Siddha, and Homeopathy holistic care"
    ),
    DepartmentInfo(
        id=DepartmentId.EMERGENCY,
        name="Emergency",
        display_name="Emergency",
        icon="🚨",
        description="Immediate acute resuscitation, critical trauma, shock"
    ),
    DepartmentInfo(
        id=DepartmentId.UNSPECIFIED,
        name="Unspecified",
        display_name="Unspecified",
        icon="📋",
        description="Unassigned, ambiguous, or multi-system pending clinical triage"
    )
]

def get_all_departments() -> List[DepartmentInfo]:
    return DEPARTMENTS_REGISTRY

def get_department_by_id(dept_id: str) -> DepartmentInfo:
    for dept in DEPARTMENTS_REGISTRY:
        if dept.id.value == dept_id or dept.id == dept_id:
            return dept
    # Default fallback
    return DEPARTMENTS_REGISTRY[-1]  # Unspecified
