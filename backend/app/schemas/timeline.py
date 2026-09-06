from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.security import SourceType

class TimelineEventType(str, Enum):
    REGISTRATION = "REGISTRATION"
    CONSENT_CAPTURED = "CONSENT_CAPTURED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    OCR_PROCESSED = "OCR_PROCESSED"
    QUESTION_ASKED = "QUESTION_ASKED"
    ANSWER_RECORDED = "ANSWER_RECORDED"
    LIVE_SUMMARY_GENERATED = "LIVE_SUMMARY_GENERATED"
    RED_FLAG_DETECTED = "RED_FLAG_DETECTED"
    DEPARTMENT_ROUTED = "DEPARTMENT_ROUTED"
    PHYSICIAN_ACCESSED = "PHYSICIAN_ACCESSED"
    PHYSICIAN_CONFIRMED = "PHYSICIAN_CONFIRMED"
    PHYSICIAN_OVERRIDDEN = "PHYSICIAN_OVERRIDDEN"
    INTAKE_COMPLETED = "INTAKE_COMPLETED"

class TimelineEvent(BaseModel):
    event_id: str
    patient_id: str
    session_id: str
    event_type: TimelineEventType
    title: str
    description: str
    source_type: SourceType
    evidence_reference: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
