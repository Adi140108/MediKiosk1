"""
Observation Normalizer Module — MediKiosk AYUSH V2

Normalizes raw patient responses (multilingual text or structured options) into
structured observation objects.

Handles:
- Negation detection ("I do not have bloating" -> normalized_value: "absent", severity: 0)
- Frequency & severity classification (present, absent, occasional, frequent, severe, mild, historical)
- Baseline vs. Current (Vikriti) trajectory
- Audit traceability (preserves raw answer)
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class StructuredObservation(BaseModel):
    question_id: str
    domain: str
    sub_domain: Optional[str] = None
    feature: str
    raw_answer: str
    normalized_value: str  # present, absent, occasional, frequent, severe, mild, historical, uncertain, not_answered
    severity: int = 0      # 0 (absent), 1 (mild/occasional), 2 (moderate/frequent), 3 (severe)
    frequency: str = "never"  # never, occasional, frequent, continuous, historical
    is_historical: bool = False
    is_denial: bool = False
    confidence: float = 0.9
    evidence_source: str = "patient"
    dosha_weights: Dict[str, int] = Field(default_factory=dict)
    option_value: Optional[str] = None
    feature_targets: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ObservationNormalizer:
    NEGATION_TERMS = [
        "no", "not", "don't", "dont", "never", "absent", "denies", "neither", "none",
        "नहीं", "ना", "नही", "ಇಲ್ಲ", "ಇಲ್ಲವೇ ಇಲ್ಲ", "ಇಲ್ಲಾ", "ಇಲ್ಲವೇ",
        "இல்லை", "இல்லவே இல்லை", "లేదు", "లేనే లేదు", "అస్సలు లేదు",
        "ഇല്ല", "ഇല്ലവേ ഇല്ല", "ਨਾਹੀ", "ਨਾ"
    ]
    
    HISTORICAL_TERMS = [
        "used to", "in the past", "previously", "earlier", "years ago", "months ago", "not anymore", "cured",
        "पहले था", "पुराना", "पहले होता था", "ಹಿಂದೆ ಇತ್ತು", "ಹಳೆಯದು", "முன்பு இருந்தது", "గతంలో ఉండేది"
    ]

    OCCASIONAL_TERMS = [
        "sometimes", "occasional", "occasionally", "once in a while", "intermittent", "rarely",
        "कभी कभी", "कभी-कभी", "अक्सर नहीं", "ಕೆಲವೊಮ್ಮೆ", "ಅಪರೂಪಕ್ಕೆ", "அப்போதே", "అప్పుడప్పుడు"
    ]

    FREQUENT_TERMS = [
        "always", "every day", "daily", "frequent", "frequently", "continuous", "severe", "intense",
        "हमेशा", "रोजाना", "लगातार", "ಪ್ರತಿದಿನ", "ಸದಾ", "ದಿನವೂ", "எப்போதும்", "ఎల్లప్పుడూ"
    ]

    def normalize(
        self,
        question_id: str,
        domain: str,
        feature: str,
        raw_answer: str,
        option_meta: Optional[Dict[str, Any]] = None,
        sub_domain: Optional[str] = None
    ) -> StructuredObservation:
        text_clean = (raw_answer or "").strip()
        text_lower = text_clean.lower()

        # 1. Check option metadata if provided
        dosha_weights = {}
        option_val = None
        feature_targets = []

        if option_meta:
            dosha_weights = option_meta.get("weights", {}) or option_meta.get("dosha_weights", {})
            option_val = option_meta.get("value") or option_meta.get("label")
            feature_targets = option_meta.get("feature_targets", [])
            
            opt_val = str(option_meta.get("value", "")).lower()
            if "absent" in opt_val or "no" in opt_val or "none" in opt_val:
                return StructuredObservation(
                    question_id=question_id,
                    domain=domain,
                    sub_domain=sub_domain,
                    feature=feature,
                    raw_answer=text_clean,
                    normalized_value="absent",
                    severity=0,
                    frequency="never",
                    is_denial=True,
                    confidence=0.98,
                    dosha_weights=dosha_weights,
                    option_value=option_val,
                    feature_targets=feature_targets
                )

        # 2. Check for explicit negation in free-text answer
        is_negated = any(re.search(rf"\b{re.escape(term)}\b", text_lower) for term in self.NEGATION_TERMS)
        if is_negated and not any(k in text_lower for k in ["not bad", "not severe", "not really a problem"]):
            return StructuredObservation(
                question_id=question_id,
                domain=domain,
                sub_domain=sub_domain,
                feature=feature,
                raw_answer=text_clean,
                normalized_value="absent",
                severity=0,
                frequency="never",
                is_denial=True,
                confidence=0.95
            )

        # 3. Check for historical statement (past symptom, not current)
        is_history = any(re.search(rf"\b{re.escape(term)}\b", text_lower) for term in self.HISTORICAL_TERMS)
        if is_history:
            return StructuredObservation(
                question_id=question_id,
                domain=domain,
                sub_domain=sub_domain,
                feature=feature,
                raw_answer=text_clean,
                normalized_value="historical",
                severity=0,
                frequency="historical",
                is_historical=True,
                confidence=0.90
            )

        # 4. Determine frequency and severity
        is_occasional = any(re.search(rf"\b{re.escape(term)}\b", text_lower) for term in self.OCCASIONAL_TERMS)
        is_frequent = any(re.search(rf"\b{re.escape(term)}\b", text_lower) for term in self.FREQUENT_TERMS)

        if is_frequent:
            norm_val = "frequent"
            sev = 2
            freq = "frequent"
        elif is_occasional:
            norm_val = "occasional"
            sev = 1
            freq = "occasional"
        else:
            norm_val = "present"
            sev = 1
            freq = "present"

        return StructuredObservation(
            question_id=question_id,
            domain=domain,
            sub_domain=sub_domain,
            feature=feature,
            raw_answer=text_clean,
            normalized_value=norm_val,
            severity=sev,
            frequency=freq,
            is_denial=False,
            confidence=0.88,
            dosha_weights=dosha_weights,
            option_value=option_val,
            feature_targets=feature_targets
        )
