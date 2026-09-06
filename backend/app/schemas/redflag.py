from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RedFlagSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NONE = "NONE"

    @classmethod
    def get_rank(cls, severity: "RedFlagSeverity") -> int:
        ranks = {
            cls.CRITICAL: 0,
            cls.HIGH: 1,
            cls.MEDIUM: 2,
            cls.LOW: 3,
            cls.NONE: 4
        }
        return ranks.get(severity, 4)

class RedFlagItem(BaseModel):
    rule_id: str
    title: str
    description: str
    severity: RedFlagSeverity
    category: str  # 'cardiac', 'neurological', 'respiratory', 'trauma', 'pediatric', 'sepsis', 'bleeding'
    matched_symptoms: List[str] = Field(default_factory=list)
    action_required: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RedFlagEvaluationResult(BaseModel):
    session_id: str
    has_red_flags: bool = False
    overall_severity: RedFlagSeverity = RedFlagSeverity.NONE
    flagged_rules: List[RedFlagItem] = Field(default_factory=list)
    triage_category: str = "NORMAL"  # 'EMERGENCY', 'URGENT', 'PRIORITY', 'NORMAL'
    summary_reason: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
