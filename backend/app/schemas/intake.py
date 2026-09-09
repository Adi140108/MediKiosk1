from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.core.security import SourceType

class OPDMode(str, Enum):
    GENERAL_OPD = "GENERAL_OPD"
    AYUSH_OPD = "AYUSH_OPD"

class QuestionFramework(str, Enum):
    SOCRATIC = "SOCRATIC"
    AYURVEDIC = "AYURVEDIC"
    RED_FLAG = "RED_FLAG"
    CHIEF_COMPLAINT = "CHIEF_COMPLAINT"
    EXPLORATORY = "EXPLORATORY"
    VERIFICATION = "VERIFICATION"

class SocraticStage(str, Enum):
    BROAD = "BROAD"
    CLARIFY = "CLARIFY"
    EXPLORE = "EXPLORE"
    VERIFY = "VERIFY"
    SUFFICIENT = "SUFFICIENT"
    STOP = "STOP"

class QuestionItem(BaseModel):
    question_id: str
    session_id: str
    question: str
    objective: str
    question_framework: QuestionFramework = QuestionFramework.SOCRATIC
    socratic_stage: SocraticStage = SocraticStage.BROAD
    clinical_domain: str = "general"
    ayurvedic_domain: Optional[str] = None  # e.g., 'AGNI', 'MALA', 'NIDRA', 'AHARA', 'VIHARA'
    display_label: Optional[str] = None  # e.g. '(Agni)', '(Digestion)'
    options: Optional[List[Any]] = None
    language: str = "en"
    sequence: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnswerItem(BaseModel):
    answer_id: str
    question_id: str
    session_id: str
    question: str
    answer: str  # Normalized or active answer for processing
    original_answer: Optional[str] = None  # Exact patient utterance in native language
    original_language: Optional[str] = "en"
    normalized_answer: Optional[str] = None  # English clinical translation if translated
    normalized_language: Optional[str] = "en"
    translation_status: Optional[str] = "verified"  # verified, unavailable, error
    translation_provider: Optional[str] = None
    source_type: SourceType = SourceType.PATIENT
    attendant_id: Optional[str] = None
    language: str = "en"
    extracted_facts: Dict[str, Any] = Field(default_factory=dict)
    sequence: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LiveSummaryItem(BaseModel):
    summary_id: str
    session_id: str
    summary_text: str
    checkpoint_sequence: int
    is_confirmed_by_user: bool = False
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientContextState(BaseModel):
    opd_mode: OPDMode = OPDMode.GENERAL_OPD
    mode_at_intake: str = "GENERAL_OPD"
    questionnaire_version: str = "v1.0"
    assessment_version: str = "AYUSH_ASSESSMENT_V1"

    chief_complaint: Optional[str] = None
    location: Optional[str] = None
    onset: Optional[str] = None
    duration: Optional[str] = None
    severity: Optional[int] = None
    character: Optional[str] = None
    progression: Optional[str] = None
    associated_symptoms: List[str] = Field(default_factory=list)
    aggravating_factors: List[str] = Field(default_factory=list)
    relieving_factors: List[str] = Field(default_factory=list)
    known_conditions: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    past_medical_history: Optional[str] = None
    prescription_notes: Optional[str] = None
    family_history: List[str] = Field(default_factory=list)
    lifestyle: List[str] = Field(default_factory=list)
    vitals: Dict[str, str] = Field(default_factory=dict)
    
    # Ayurvedic specific context & structured assessment
    ayurvedic_findings: Dict[str, Any] = Field(default_factory=dict)  # agni, mala, nidra, ahara, vihara, etc.
    ayush_assessment: Dict[str, Any] = Field(default_factory=dict)
    
    # Information & Source Tracking (Provenance)
    provenance_map: Dict[str, str] = Field(default_factory=dict)  # fact_key -> "PATIENT" | "ATTENDANT" | "DOCUMENT" | "PHYSICIAN"
    known_information: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    red_flag_requirements: List[str] = Field(default_factory=list)
    
    socratic_stage: SocraticStage = SocraticStage.BROAD
    is_sufficient: bool = False
    question_count: int = 0
