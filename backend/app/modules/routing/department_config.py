from typing import List, Dict, Any, Optional
from app.schemas.routing import DepartmentId, DepartmentInfo

# General OPD Department Registry (Single Source of Truth)
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
        display_name="Emergency / Trauma",
        icon="🚨",
        description="Immediate acute resuscitation, critical trauma, shock"
    ),
    DepartmentInfo(
        id=DepartmentId.GENERAL_UNSPECIFIED,
        name="General Unspecified",
        display_name="General Unspecified / Triage Desk",
        icon="📋",
        description="Unassigned, ambiguous, or multi-system General OPD triage"
    )
]

# AYUSH OPD Department Registry (Single Source of Truth)
AYUSH_DEPARTMENTS: List[DepartmentInfo] = [
    DepartmentInfo(
        id=DepartmentId.AYUSH,
        name="AYUSH",
        display_name="AYUSH / Ayurveda Main OPD",
        icon="🌿",
        description="Ayurvedic general outpatient care, Prakriti constitution assessment and holistic triage"
    ),
    DepartmentInfo(
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
    ),
    DepartmentInfo(
        id=DepartmentId.EMERGENCY,
        name="Emergency",
        display_name="Emergency / Trauma",
        icon="🚨",
        description="Emergency escalation safety net"
    ),
    DepartmentInfo(
        id=DepartmentId.AYUSH_UNSPECIFIED,
        name="AYUSH Unspecified",
        display_name="AYUSH Unspecified / Triage Desk",
        icon="📋",
        description="Unassigned or ambiguous AYUSH clinical presentation awaiting specialized assessment"
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
    dept_str = str(getattr(dept_id, "value", dept_id)).lower()
    for dept in DEPARTMENTS_REGISTRY:
        if dept.id.value.lower() == dept_str or dept.id.name.lower() == dept_str:
            return dept
    # Default fallback per mode if not found
    return GENERAL_DEPARTMENTS[-1]

def is_department_valid_for_mode(dept_id: str, opd_mode: str) -> bool:
    mode = str(opd_mode or "GENERAL_OPD").upper()
    dept_str = str(getattr(dept_id, "value", dept_id)).lower()
    
    # Emergency is allowed in both modes as explicit critical safety escalation
    if dept_str == DepartmentId.EMERGENCY.value.lower():
        return True

    valid_list = AYUSH_DEPARTMENTS if "AYUSH" in mode else GENERAL_DEPARTMENTS
    return any(d.id.value.lower() == dept_str for d in valid_list)
