from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class DepartmentId(str, Enum):
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    GENERAL_MEDICINE = "general-medicine"
    ORTHOPEDICS = "orthopedics"
    PEDIATRICS = "pediatrics"
    GASTROENTEROLOGY = "gastroenterology"
    DERMATOLOGY = "dermatology"
    ENT = "ent"
    OPHTHALMOLOGY = "ophthalmology"
    PSYCHIATRY = "psychiatry"
    AYUSH = "ayush"
    KAYACHIKITSA = "kayachikitsa"
    PANCHAKARMA = "panchakarma"
    SHALYA = "shalya"
    SHALAKYA = "shalakya"
    PRASUTI_STRI = "prasuti-stri"
    KAUMARABHRITYA = "kaumarabhritya"
    SWASTHAVRITTA = "swasthavritta"
    AGADATANTRA = "agadatantra"
    EMERGENCY = "emergency"
    UNSPECIFIED = "unspecified"

class RecommendationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    MANUALLY_ASSIGNED = "MANUALLY_ASSIGNED"

class DepartmentInfo(BaseModel):
    id: DepartmentId
    name: str
    display_name: str
    icon: str
    description: str
    enabled: bool = True

class RoutingRecommendation(BaseModel):
    recommendation_id: str
    session_id: str
    patient_id: str
    recommended_department: DepartmentId
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence_level: str = "High"  # High, Medium, Low
    reasoning: str
    matched_evidence: List[str] = Field(default_factory=list)
    alternative_departments: List[Dict[str, Any]] = Field(default_factory=list)
    department_scores: Dict[str, float] = Field(default_factory=dict)
    routing_method: str = "AI_AND_RULE_COMBINED"  # RULE_BASED, AI_ASSISTED, AI_AND_RULE_COMBINED
    status: RecommendationStatus = RecommendationStatus.PENDING_REVIEW
    confirmed_department: Optional[DepartmentId] = None
    confirmed_by_physician_id: Optional[str] = None
    source_type: str = "AI_GENERATED_RECOMMENDATION"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
