import logging
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger("medikiosk.security")

class UserRole(str, Enum):
    PATIENT = "PATIENT"
    ATTENDANT = "ATTENDANT"
    PHYSICIAN = "PHYSICIAN"
    ADMIN = "ADMIN"

class SourceType(str, Enum):
    PATIENT = "PATIENT"
    ATTENDANT = "ATTENDANT"
    DOCUMENT = "DOCUMENT"
    PHYSICIAN = "PHYSICIAN"
    AI_GENERATED = "AI_GENERATED"

def log_audit_event(
    event_type: str,
    user_id: str,
    role: UserRole,
    details: Dict[str, Any],
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Structured security & compliance audit logging.
    Never logs credentials, keys, or raw medical secrets.
    """
    event = {
        "event_type": event_type,
        "user_id": user_id,
        "role": role.value if isinstance(role, UserRole) else str(role),
        "session_id": session_id,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logger.info("AUDIT_EVENT: %s | User: %s | Role: %s | Session: %s", event_type, user_id, role, session_id)
    return event
