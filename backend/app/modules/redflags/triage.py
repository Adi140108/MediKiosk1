from typing import Tuple
from app.schemas.redflag import RedFlagSeverity

def assign_triage_category(highest_severity: RedFlagSeverity) -> Tuple[int, str]:
    """
    Returns (priority_group, triage_category)
    Priority group 0: Red Flag (Critical, High, Medium, Low)
    Priority group 1: Normal (Non-red flag cases)
    """
    if highest_severity == RedFlagSeverity.CRITICAL:
        return 0, "EMERGENCY"
    elif highest_severity == RedFlagSeverity.HIGH:
        return 0, "URGENT"
    elif highest_severity in (RedFlagSeverity.MEDIUM, RedFlagSeverity.LOW):
        return 0, "PRIORITY"
    else:
        return 1, "NORMAL"
