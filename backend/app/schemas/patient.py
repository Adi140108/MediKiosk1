from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.core.security import SourceType

class Gender(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"

class IdentityType(str, Enum):
    ABHA = "ABHA"
    TEMP_DEV = "TEMP_DEV"
    AADHAAR_MOCK = "AADHAAR_MOCK"
    HOSPITAL_ID = "HOSPITAL_ID"

class PatientRegistrationRequest(BaseModel):
    name: str
    age: int
    gender: Gender
    phone: Optional[str] = None
    abha_id: Optional[str] = None
    identity_type: IdentityType = IdentityType.TEMP_DEV
    preferred_language: str = "en"
    is_attendant_assisted: bool = False

class AttendantRegistrationRequest(BaseModel):
    name: str
    phone: str
    relationship_to_patient: str  # e.g., 'Parent', 'Spouse', 'Child', 'Sibling', 'Guardian', 'Other'
    attendant_id: Optional[str] = None
    consent_given: bool = True
    authorization_details: Optional[str] = None

class ConsentRecord(BaseModel):
    consent_id: str
    patient_id: str
    session_id: str
    given_by: SourceType
    attendant_id: Optional[str] = None
    data_processing_agreed: bool = True
    ai_assistance_agreed: bool = True
    teleconsult_agreed: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PatientProfile(BaseModel):
    patient_id: str
    abha_id: Optional[str] = None
    name: str
    age: int
    gender: Gender
    phone: Optional[str] = None
    preferred_language: str = "en"
    registered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_temporary_identity: bool = False
    active_session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
