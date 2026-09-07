"""
AYUSH Master Assessment Knowledge Base

Defines feature indicators, scoring weights, and clinical criteria for:
- Prakriti (Sharira, Digestion, Activity, Sleep, Mind, Other)
- Vikriti (Present imbalance indicators)
- Agni (Sama, Vishama, Tikshna, Manda)
- Ama (Observed toxicity/heaviness indicators)
- Koshta (Mridu, Madhyama, Krura)
- Sara (8 tissues: Twak, Rakta, Mamsa, Meda, Asthi, Majja, Shukra, Satva)
- Samhanana (Structural compactness)
- Satva (Psychological resilience)
- Satmya (Adaptability)
- Ahara Shakti (Abhyavaharana & Jarana)
- Vyayama Shakti (Exercise tolerance)
- Vaya (Age categorization)
- Mala (Purisha, Mutra, Sweda)
- Nidra (Sleep characteristics)
"""

from typing import Dict, Any, List

# Feature indicator scoring table for Prakriti assessment
PRAKRITI_INDICATORS: List[Dict[str, Any]] = [
    # Sharira (Body Build & Physical Traits)
    {
        "feature_id": "build_lean",
        "domain": "SHARIRA",
        "keywords": ["lean", "slender", "thin", "low weight", "narrow frame"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": -1},
        "description": "Lean/slender body frame"
    },
    {
        "feature_id": "build_medium",
        "domain": "SHARIRA",
        "keywords": ["medium build", "moderate weight", "proportionate", "average frame"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Medium build and moderate musculature"
    },
    {
        "feature_id": "build_broad",
        "domain": "SHARIRA",
        "keywords": ["broad", "heavy build", "large frame", "solid", "well-developed"],
        "weights": {"VATA": -1, "PITTA": 0, "KAPHA": 2},
        "description": "Broad/solid frame and well-developed musculature"
    },
    {
        "feature_id": "skin_dry",
        "domain": "SHARIRA",
        "keywords": ["dry skin", "rough skin", "cracked skin"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": 0},
        "description": "Dry or rough skin texture"
    },
    {
        "feature_id": "skin_warm_soft",
        "domain": "SHARIRA",
        "keywords": ["warm skin", "soft skin", "redness", "warmth"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Warm, soft skin with redness tendency"
    },
    {
        "feature_id": "skin_smooth_oily",
        "domain": "SHARIRA",
        "keywords": ["smooth skin", "oily skin", "thick skin", "soft"],
        "weights": {"VATA": 0, "PITTA": 0, "KAPHA": 2},
        "description": "Smooth, oily, or thick skin texture"
    },
    
    # Appetite & Digestion (Agni/Ahara)
    {
        "feature_id": "appetite_irregular",
        "domain": "DIGESTION",
        "keywords": ["irregular appetite", "variable hunger", "bloating", "gassy", "unpredictable hunger"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": 0},
        "description": "Irregular appetite and variable digestion"
    },
    {
        "feature_id": "appetite_strong",
        "domain": "DIGESTION",
        "keywords": ["strong hunger", "intense appetite", "cannot skip meals", "acidity", "frequent hunger"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Strong appetite and intense digestion"
    },
    {
        "feature_id": "appetite_slow",
        "domain": "DIGESTION",
        "keywords": ["slow digestion", "heavy after meals", "can skip meals", "low appetite"],
        "weights": {"VATA": 0, "PITTA": -1, "KAPHA": 2},
        "description": "Moderate to slow digestion pattern"
    },
    
    # Activity & Movement
    {
        "feature_id": "activity_quick",
        "domain": "ACTIVITY",
        "keywords": ["quick movement", "fast speech", "quick walker", "restless"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": 0},
        "description": "Quick movement and rapid pace"
    },
    {
        "feature_id": "activity_purposeful",
        "domain": "ACTIVITY",
        "keywords": ["purposeful", "moderate pace", "determined", "focused movement"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Moderate, purposeful movement"
    },
    {
        "feature_id": "activity_steady",
        "domain": "ACTIVITY",
        "keywords": ["slow movement", "steady pace", "calm movement", "good endurance"],
        "weights": {"VATA": 0, "PITTA": 0, "KAPHA": 2},
        "description": "Slow, steady movement with high endurance"
    },

    # Sleep (Nidra)
    {
        "feature_id": "sleep_light",
        "domain": "SLEEP",
        "keywords": ["light sleep", "interrupted sleep", "wakes easily", "short sleep"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": -1},
        "description": "Light or interrupted sleep pattern"
    },
    {
        "feature_id": "sleep_moderate",
        "domain": "SLEEP",
        "keywords": ["moderate sleep", "sound sleep", "6 to 7 hours"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Moderate sound sleep"
    },
    {
        "feature_id": "sleep_deep",
        "domain": "SLEEP",
        "keywords": ["deep sleep", "prolonged sleep", "heavy sleeper", "hard to wake"],
        "weights": {"VATA": -1, "PITTA": 0, "KAPHA": 2},
        "description": "Deep and prolonged sleep"
    },

    # Mind & Temperament
    {
        "feature_id": "mind_quick_grasp",
        "domain": "MIND",
        "keywords": ["grasps quickly", "forgets quickly", "creative", "anxious", "restless mind"],
        "weights": {"VATA": 2, "PITTA": 0, "KAPHA": 0},
        "description": "Quick comprehension with variable retention"
    },
    {
        "feature_id": "mind_sharp_focused",
        "domain": "MIND",
        "keywords": ["sharp intellect", "focused", "irritable when hungry", "decisive"],
        "weights": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "description": "Sharp intellect and intense focus"
    },
    {
        "feature_id": "mind_calm_receptive",
        "domain": "MIND",
        "keywords": ["calm", "patient", "good memory", "steady mind", "slow to learn but long retention"],
        "weights": {"VATA": 0, "PITTA": 0, "KAPHA": 2},
        "description": "Calm, patient mind with long-term retention"
    },

    # Environmental & Temperature Tolerance
    {
        "feature_id": "temp_cold_intolerant",
        "domain": "ENVIRONMENT",
        "keywords": ["prefers warmth", "intolerant to cold", "cold hands/feet"],
        "weights": {"VATA": 2, "PITTA": -1, "KAPHA": 1},
        "description": "Intolerance to cold weather"
    },
    {
        "feature_id": "temp_heat_intolerant",
        "domain": "ENVIRONMENT",
        "keywords": ["prefers cool", "intolerant to heat", "profuse sweating", "flushing"],
        "weights": {"VATA": -1, "PITTA": 2, "KAPHA": 0},
        "description": "Intolerance to hot weather"
    }
]

# Scoring thresholds & rules for Agni classification
AGNI_CRITERIA = {
    "SAMA_AGNI": {
        "description": "Balanced digestion; comfortable digestion after regular meals",
        "required_indicators": ["comfortable_digestion", "regular_hunger"]
    },
    "VISHAMA_AGNI": {
        "description": "Variable digestion associated with Vata imbalance (bloating, gas, variable hunger)",
        "required_indicators": ["bloating", "variable_hunger", "irregular_bowel"]
    },
    "TIKSHNA_AGNI": {
        "description": "Intense digestion associated with Pitta imbalance (burning, intense hunger, acidity)",
        "required_indicators": ["intense_hunger", "acidity", "burning_sensation"]
    },
    "MANDA_AGNI": {
        "description": "Slow digestion associated with Kapha imbalance (post-meal heaviness, delayed hunger)",
        "required_indicators": ["post_meal_heaviness", "slow_digestion", "delayed_hunger"]
    }
}

# Koshta classification rules
KOSHTA_CRITERIA = {
    "MRIDU": "Soft bowel pattern, easy evacuation, softer stools (Pitta predominant)",
    "MADHYAMA": "Regular bowel pattern, normal evacuation (Kapha/Sama predominant)",
    "KRURA": "Hard stool tendency, dry evacuation, constipation tendency (Vata predominant)"
}

# Status for unvalidated domains
STATUS_CLINICIAN_VALIDATION = "REQUIRES_CLINICIAN_VALIDATION"
