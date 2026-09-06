from typing import List
from app.schemas.redflag import RedFlagSeverity

def determine_highest_severity(severities: List[RedFlagSeverity]) -> RedFlagSeverity:
    """
    Given a list of detected severities, determines the overall highest severity.
    Hierarchy: CRITICAL > HIGH > MEDIUM > LOW > NONE
    """
    if not severities:
        return RedFlagSeverity.NONE

    for target in [RedFlagSeverity.CRITICAL, RedFlagSeverity.HIGH, RedFlagSeverity.MEDIUM, RedFlagSeverity.LOW]:
        if target in severities:
            return target

    return RedFlagSeverity.NONE
