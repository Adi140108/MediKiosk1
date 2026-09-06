import logging
from typing import List, Optional
from app.schemas.intake import PatientContextState
from app.schemas.redflag import (
    RedFlagItem, RedFlagSeverity, RedFlagEvaluationResult
)
from app.modules.redflags.rules import CLINICAL_RED_FLAG_RULES
from app.modules.redflags.conditions import match_rule_conditions
from app.modules.redflags.severity import determine_highest_severity
from app.modules.redflags.triage import assign_triage_category

logger = logging.getLogger("medikiosk.redflags.engine")

class RedFlagEngine:
    """
    Deterministic Red-Flag Clinical Safety & Triage Engine.
    Evaluates structured patient context against configured rules.
    Assigns overall severity as highest applicable severity.
    """
    def __init__(self, rules: Optional[List[dict]] = None):
        self.rules = rules or CLINICAL_RED_FLAG_RULES

    def evaluate_patient_context(
        self,
        session_id: str,
        context: PatientContextState
    ) -> RedFlagEvaluationResult:
        flagged_items: List[RedFlagItem] = []

        for rule in self.rules:
            if match_rule_conditions(rule, context):
                flagged_item = RedFlagItem(
                    rule_id=rule["rule_id"],
                    title=rule["title"],
                    description=rule["description"],
                    severity=rule["severity"],
                    category=rule["category"],
                    matched_symptoms=list(context.associated_symptoms),
                    action_required=rule["action_required"]
                )
                flagged_items.append(flagged_item)

        if not flagged_items:
            return RedFlagEvaluationResult(
                session_id=session_id,
                has_red_flags=False,
                overall_severity=RedFlagSeverity.NONE,
                flagged_rules=[],
                triage_category="NORMAL",
                summary_reason=None
            )

        # Multiple red flags: evaluate all, resolve to highest applicable severity
        severities = [item.severity for item in flagged_items]
        highest_severity = determine_highest_severity(severities)
        priority_group, triage_category = assign_triage_category(highest_severity)

        summary_reason = f"Detected {len(flagged_items)} red flag condition(s): " + ", ".join([f.title for f in flagged_items])

        logger.info("RedFlag evaluated for session %s: %s (Severity: %s)", session_id, triage_category, highest_severity)

        return RedFlagEvaluationResult(
            session_id=session_id,
            has_red_flags=True,
            overall_severity=highest_severity,
            flagged_rules=flagged_items,
            triage_category=triage_category,
            summary_reason=summary_reason
        )
