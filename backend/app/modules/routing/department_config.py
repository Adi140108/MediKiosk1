from typing import List, Dict, Any, Optional
from app.schemas.routing import DepartmentId, DepartmentInfo

# General OPD Department Registry
GENERAL_DEPARTMENTS: List[DepartmentInfo] = [
    DepartmentInfo(
        id=DepartmentId.GENERAL_MEDICINE,
        name="General Medicine",
        display_name="General Medicine",
        icon="🩺",
        description="Adult primary care, systemic illnesses, fever, diabetes, hypertension"
    ),
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

# AYUSH OPD Department Registry
AYUSH_DEPARTMENTS: List[DepartmentInfo] = [
    DepartmentInfo(
        id=DepartmentId.AYUSH,
        name="AYUSH",
        display_name="AYUSH / Ayurveda Main OPD",
        icon="🌿",
        description="Ayurvedic general outpatient care, Prakriti constitution assessment and holistic triage"
    ),
    DepartmentInfo(
        id=DepartmentId.KAYACHIKITS,
        name="Kayachikitsa",
        display_name="Kayachikitsa (Internal Medicine)",
        icon="🍵",
        description="Agni, Dhatu, Ama, systemic illnesses, digestive and metabolic disorders"
    ) if hasattr(DepartmentId, 'KAYACHIKITS') else DepartmentInfo(
        id=DepartmentId.KAYACHIKITSA,
        name="Kayachikitsa",
        display_name="Kayachikitsa (Internal Medicine)",
        icon="🍵",
        description="Agni, Dhatu, Ama, systemic illnesses, digestive and metabolic disorders"
    ),
    DepartmentInfo(
        id=DepartmentId.PANCHAKARMA,
        name="Panchakarma",
        display_name="Panchakarma (Detox & Purification)",
        icon="🪔",
        description="Shodhana therapy, Vamana, Virechana, Basti, Nasya and bio-cleansing evaluations"
    ),
    DepartmentInfo(
        id=DepartmentId.SHALYA,
        name="Shalya",
        display_name="Shalya Tantra (General & Structural Care)",
        icon="🗡️",
        description="Musculoskeletal, joint pain, spinal care, and structural Ayurvedic management"
    ),
    DepartmentInfo(
        id=DepartmentId.SHALAKYA,
        name="Shalakya",
        display_name="Shalakya Tantra (ENT & Eye / Urdhvanga)",
        icon="👁️",
        description="Head, ear, nose, throat, and ocular disorders in Ayurveda"
    ),
    DepartmentInfo(
        id=DepartmentId.PRASUTI_STRI,
        name="Prasuti & Stri Roga",
        display_name="Prasuti Tantra & Stree Roga",
        icon="🌺",
        description="Ayurvedic women's health, maternal wellness, and gynecological care"
    ),
    DepartmentInfo(
        id=DepartmentId.KAUMARABHRITYA,
        name="Kaumarabhritya",
        display_name="Kaumarabhritya (Pediatrics)",
        icon="👶",
        description="Balaroga, infant care, pediatric growth and immune health in Ayurveda"
    ),
    DepartmentInfo(
        id=DepartmentId.SWASTHAVRITTA,
        name="Swasthavritta",
        display_name="Swasthavritta & Yoga (Preventive Care)",
        icon="🧘",
        description="Dinacharya, Ritucharya, Ahara, Vihara, preventive health and lifestyle medicine"
    ),
    DepartmentInfo(
        id=DepartmentId.AGADATANTRA,
        name="Agadatantra",
        display_name="Agada Tantra (Toxicology & Allergies)",
        icon="🧪",
        description="Environmental allergies, toxicities, skin hypersensitivities and insect bites"
    )
]

DEPARTMENTS_REGISTRY: List[DepartmentInfo] = GENERAL_DEPARTMENTS + AYUSH_DEPARTMENTS

def get_all_departments() -> List[DepartmentInfo]:
    return DEPARTMENTS_REGISTRY

def get_departments_for_mode(opd_mode: Optional[str] = "GENERAL_OPD") -> List[DepartmentInfo]:
    mode = str(opd_mode or "GENERAL_OPD").upper()
    if "AYUSH" in mode:
        return AYUSH_DEPARTMENTS
    return GENERAL_DEPARTMENTS

def get_department_by_id(dept_id: str) -> DepartmentInfo:
    for dept in DEPARTMENTS_REGISTRY:
        if dept.id.value == dept_id or dept.id == dept_id:
            return dept
    # Default fallback
    return GENERAL_DEPARTMENTS[-1]  # Unspecified

def is_department_valid_for_mode(dept_id: str, opd_mode: str) -> bool:
    mode = str(opd_mode or "GENERAL_OPD").upper()
    valid_list = AYUSH_DEPARTMENTS if "AYUSH" in mode else GENERAL_DEPARTMENTS
    # Emergency is always allowed as a safety net
    if dept_id in [DepartmentId.EMERGENCY.value, DepartmentId.EMERGENCY]:
        return True
    return any(dept.id.value == dept_id or dept.id == dept_id for dept in valid_list)

