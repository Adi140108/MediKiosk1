"""
AYUSH Question Planner & Session State Module — MediKiosk V3.1

Single Source of Truth:
Loads and indexes all question-bank JSON files under `backend/app/modules/ayush/question_bank/`.
Orchestrates question selection by exact `question_id` (e.g. PRAK_BUILD_001, AGNI_HUNGER_003).

Features:
- Two-Track Assessment:
  - Track A: AYUSH Core Profile (Baseline Prakriti, Agni, Koshta, Nidra, Satva)
  - Track B: Complaint-Specific Ayurvedic Assessment (Nidana, Samprapti, Vikriti)
- Domain Sufficiency: Stops asking questions for a domain when evidence threshold (>= 3 valid observations or all domain questions completed) is reached.
- Non-LLM, Data-Driven Execution: 100% deterministic decision logic based on JSON priority, dependencies, required_for, and feature_targets.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("medikiosk.ayush.question_planner")

class AyushAssessmentSessionState(BaseModel):
    session_id: str
    patient_id: str
    opd_mode: str = "AYUSH_OPD"
    mode_at_intake: str = "AYUSH_OPD"
    current_question_id: Optional[str] = None
    asked_question_ids: List[str] = Field(default_factory=list)
    answered_question_ids: List[str] = Field(default_factory=list)
    skipped_question_ids: List[str] = Field(default_factory=list)
    completed_domains: List[str] = Field(default_factory=list)
    domain_evidence_count: Dict[str, int] = Field(default_factory=dict)
    active_track: str = "CORE_PROFILE"  # "CORE_PROFILE" or "COMPLAINT_SPECIFIC"
    chief_complaint: str = ""
    assessment_version: str = "3.1"
    questionnaire_version: str = "3.1"
    knowledge_base_version: str = "3.1"

class AyushQuestionPlanner:
    def __init__(self, question_bank_dir: Optional[str] = None):
        if question_bank_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            question_bank_dir = os.path.join(base_dir, "question_bank")

        self.question_bank_dir = question_bank_dir
        self.question_bank: Dict[str, Dict[str, Any]] = {}
        self.questions_by_id: Dict[str, Dict[str, Any]] = {}
        self.questions_by_domain: Dict[str, List[Dict[str, Any]]] = {}
        self.load_question_bank()

    def load_question_bank(self):
        """Loads and indexes all JSON question bank files."""
        if not os.path.exists(self.question_bank_dir):
            logger.warning("Question bank directory not found: %s", self.question_bank_dir)
            return

        for fname in sorted(os.listdir(self.question_bank_dir)):
            if fname.endswith(".json"):
                fpath = os.path.join(self.question_bank_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        domain = data.get("domain", fname.replace(".json", "")).upper()
                        self.question_bank[domain] = data
                        
                        q_list = data.get("questions", [])
                        self.questions_by_domain[domain] = q_list
                        for q in q_list:
                            q_id = q.get("question_id")
                            if q_id:
                                q["domain"] = domain
                                self.questions_by_id[q_id] = q
                except Exception as e:
                    logger.error("Error loading question bank file %s: %s", fname, str(e))

        logger.info("Loaded AYUSH Question Bank: %d domains, %d total questions indexed.",
                    len(self.question_bank), len(self.questions_by_id))

    def select_next_question(
        self,
        session_state: AyushAssessmentSessionState,
        asked_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determines the next exact JSON question candidate by `question_id`.
        Enforces Track A (Core Profile) -> Track B (Complaint Specific) progression
        and domain stopping criteria.
        """
        asked = set(session_state.asked_question_ids + (asked_ids or []))

        # Core Profile Domain Priority sequence
        core_domain_sequence = ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "NIDRA", "SATVA", "HARA_VYAYAMA"]
        complaint_domain_sequence = ["NIDANA", "SAMPRAPTI", "PRAMANA"]

        # Track A: Core Profile
        for domain in core_domain_sequence:
            evidence_count = session_state.domain_evidence_count.get(domain, 0)
            if evidence_count >= 3 or domain in session_state.completed_domains:
                continue

            domain_questions = self.questions_by_domain.get(domain, [])
            for q in domain_questions:
                q_id = q.get("question_id")
                if q_id and q_id not in asked:
                    # Check prerequisites/dependencies if defined
                    req_questions = q.get("required_for", [])
                    if any(req not in session_state.answered_question_ids for req in req_questions):
                        continue
                    return q

            # Mark domain completed if all questions asked
            if domain not in session_state.completed_domains:
                session_state.completed_domains.append(domain)

        # Transition to Track B: Complaint Specific
        session_state.active_track = "COMPLAINT_SPECIFIC"
        for domain in complaint_domain_sequence:
            evidence_count = session_state.domain_evidence_count.get(domain, 0)
            if evidence_count >= 3 or domain in session_state.completed_domains:
                continue

            domain_questions = self.questions_by_domain.get(domain, [])
            for q in domain_questions:
                q_id = q.get("question_id")
                if q_id and q_id not in asked:
                    return q

            if domain not in session_state.completed_domains:
                session_state.completed_domains.append(domain)

        # All AYUSH domains sufficiently evaluated
        return None

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        return self.questions_by_id.get(question_id)
