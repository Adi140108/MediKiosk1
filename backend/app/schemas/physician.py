from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.redflag import RedFlagSeverity, RedFlagItem
from app.schemas.routing import DepartmentId, RecommendationStatus
from app.schemas.intake import QuestionItem, AnswerItem, LiveSummaryItem

class QueueStatus(str, Enum):
    WAITING = "WAITING"
    IN_REVIEW = "IN_REVIEW"
    PHYSICIAN_REVIEW = "PHYSICIAN_REVIEW"
    COMPLETED = "COMPLETED"
    REFERRED = "REFERRED"
    CANCELLED = "CANCELLED"

class PriorityQueueItem(BaseModel):
    queue_id: str
    patient_id: str
    session_id: str
    patient_name: str
    age: int
    gender: str
    arrival_time: datetime
    waiting_time_minutes: int = 0
    
    # Priority classification
    opd_mode: str = "GENERAL_OPD"
    is_red_flag: bool = False
    priority_group: int = 1  # 0 for Red Flag, 1 for Normal
    overall_severity: RedFlagSeverity = RedFlagSeverity.NONE
    severity_rank: int = 4  # 0: Critical, 1: High, 2: Medium, 3: Low, 4: None
    red_flag_details: List[RedFlagItem] = Field(default_factory=list)
    red_flag_summary: Optional[str] = None
    
    # Chief complaint summary for smart queue card
    chief_complaint_summary: Optional[str] = None
    duration_summary: Optional[str] = None
    
    # Routing
    assigned_department: DepartmentId
    recommended_department: DepartmentId
    routing_confidence: float = 0.85
    routing_status: RecommendationStatus = RecommendationStatus.PENDING_REVIEW
    
    # Queue Management
    status: QueueStatus = QueueStatus.WAITING
    assigned_physician_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepartmentDashboardMetrics(BaseModel):
    department_id: DepartmentId
    department_name: str
    waiting_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    in_review_count: int = 0
    completed_today: int = 0
    average_wait_minutes: int = 0

class ClinicalDraftSummary(BaseModel):
    summary_id: str
    session_id: str
    patient_id: str
    chief_complaint: str
    hpi: str  # History of Present Illness
    symptom_progression: str
    associated_symptoms: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    ayurvedic_assessment: Dict[str, Any] = Field(default_factory=dict)
    red_flags: List[str] = Field(default_factory=list)
    recommended_department: str
    is_draft: bool = True
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    physician_notes: Optional[str] = None
    source_attribution: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PhysicianConfirmPayload(BaseModel):
    physician_id: str
    confirmed_department: DepartmentId
    edited_summary: Optional[str] = None
    physician_notes: Optional[str] = None
    clinical_findings: Optional[Dict[str, Any]] = None
    prescription_notes: Optional[str] = None

class PhysicianDecisionPayload(BaseModel):
    physician_id: str
    decision_type: str = "ACCEPT"  # ACCEPT, OVERRIDE_DEPARTMENT, OVERRIDE_PRIORITY, ESCALATE_EMERGENCY, REQUEST_INFO
    final_department: DepartmentId
    final_priority: RedFlagSeverity = RedFlagSeverity.NONE
    override_reason: Optional[str] = None
    clinical_notes: Optional[str] = None
    prescriptions: Optional[str] = None

class AskPatientQuestionPayload(BaseModel):
    physician_id: str
    category: str = "other"  # medication, allergy, duration, previous_diagnosis, family_history, other
    custom_question: Optional[str] = None
