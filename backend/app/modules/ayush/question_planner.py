"""
AYUSH Question Planner & Session State Module — MediKiosk V3.2.0

Single Source of Truth:
Loads and indexes all question-bank JSON files under `backend/app/modules/ayush/question_bank/`.
Orchestrates question selection by exact `question_id` (e.g. PRAK_BUILD_001, AGNI_HUNGER_003).

Features:
- Two-Track Assessment:
  - Track A: AYUSH Core Profile (Baseline Prakriti, Agni, Koshta, Nidra, Satva)
  - Track B: Complaint-Specific Ayurvedic Assessment (Nidana, Samprapti, Vikriti)
- Domain-Specific Sufficiency: Dynamic criteria based on feature coverage and question bank specifications (NOT a universal 3-count rule).
- Non-LLM, Data-Driven Execution: 100% deterministic decision logic based on JSON priority, dependencies, required_for, and feature_targets.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.core.version import ASSESSMENT_VERSION, QUESTIONNAIRE_VERSION, KNOWLEDGE_BASE_VERSION

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
    assessment_version: str = ASSESSMENT_VERSION
    questionnaire_version: str = QUESTIONNAIRE_VERSION
    knowledge_base_version: str = KNOWLEDGE_BASE_VERSION

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

    def _is_domain_sufficient(self, domain: str, evidence_count: int, asked_questions_in_domain: List[str]) -> bool:
        """Domain-specific sufficiency check based on mentor requirements."""
        domain_q_count = len(self.questions_by_domain.get(domain, []))
        if domain_q_count == 0:
            return True

        if domain == "PRAKRITI":
            # Multi-dimensional coverage required (minimum 3-4 feature domains answered or all questions)
            return len(asked_questions_in_domain) >= min(4, domain_q_count)
        elif domain == "AGNI":
            # Requires hunger & digestion response
            return len(asked_questions_in_domain) >= min(2, domain_q_count)
        elif domain == "NIDRA":
            # Requires sleep pattern response
            return len(asked_questions_in_domain) >= min(1, domain_q_count)
        elif domain == "SATVA":
            # Requires mental resilience response
            return len(asked_questions_in_domain) >= min(1, domain_q_count)
        elif domain == "KOSHTA":
            return len(asked_questions_in_domain) >= min(1, domain_q_count)
        else:
            return len(asked_questions_in_domain) >= min(2, domain_q_count)

    def select_next_question(
        self,
        session_state: AyushAssessmentSessionState,
        asked_ids: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Determines the next exact JSON question candidate by `question_id`.
        Enforces Track A (Core Profile) -> Track B (Complaint Specific) progression
        and domain-specific sufficiency criteria.
        """
        asked = set(session_state.asked_question_ids + (asked_ids or []))

        core_domain_sequence = ["PRAKRITI", "AGNI", "KOSHTA", "AMA", "NIDRA", "SATVA", "HARA_VYAYAMA"]
        complaint_domain_sequence = ["NIDANA", "SAMPRAPTI", "PRAMANA"]

        # Track A: Core Profile
        for domain in core_domain_sequence:
            domain_questions = self.questions_by_domain.get(domain, [])
            asked_in_domain = [q.get("question_id") for q in domain_questions if q.get("question_id") in asked]
            evidence_count = len(asked_in_domain)

            if self._is_domain_sufficient(domain, evidence_count, asked_in_domain) or domain in session_state.completed_domains:
                if domain not in session_state.completed_domains:
                    session_state.completed_domains.append(domain)
                continue

            for q in domain_questions:
                q_id = q.get("question_id")
                if q_id and q_id not in asked:
                    return q

        # Track B: Complaint Specific
        session_state.active_track = "COMPLAINT_SPECIFIC"
        for domain in complaint_domain_sequence:
            domain_questions = self.questions_by_domain.get(domain, [])
            asked_in_domain = [q.get("question_id") for q in domain_questions if q.get("question_id") in asked]
            evidence_count = len(asked_in_domain)

            if self._is_domain_sufficient(domain, evidence_count, asked_in_domain) or domain in session_state.completed_domains:
                if domain not in session_state.completed_domains:
                    session_state.completed_domains.append(domain)
                continue

            for q in domain_questions:
                q_id = q.get("question_id")
                if q_id and q_id not in asked:
                    return q

        return None

    def get_question_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        return self.questions_by_id.get(question_id)
