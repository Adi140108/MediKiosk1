"""
AYUSH OPD 23-Domain Assessment Engine V2 — MediKiosk

Integrates:
- Observation Normalizer (negation safety, severity 0 for denied, frequency classification)
- Deterministic Ayurvedic Scoring Engine (23 domains, evidence tracing, zero default fallbacks)
- Version metadata: assessment_version: "2.0", questionnaire_version: "2.0", knowledge_base_version: "2.0"
"""

from typing import Dict, Any, List, Optional
from app.modules.ayush.observation_normalizer import ObservationNormalizer, StructuredObservation
from app.modules.ayush.scoring_engine import AyurvedicScoringEngine, AyushV2AssessmentResult

class AyushAssessmentEngine:
    def __init__(self):
        self.normalizer = ObservationNormalizer()
        self.scoring_engine = AyurvedicScoringEngine()

    def evaluate_assessment(
        self,
        qa_pairs: List[Dict[str, Any]],
        patient_age: Optional[int] = 35,
        ayurvedic_findings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes 23-Domain Assessment V2.
        Parses QA pairs into structured observations, evaluates using the deterministic scoring engine,
        and returns a complete structured dictionary with explicit evidence breakdown and versions.
        """
        ayurvedic_findings = ayurvedic_findings or {}
        
        # 1. Normalize QA pairs into StructuredObservations
        observations: List[StructuredObservation] = []
        for item in qa_pairs:
            q_id = str(item.get("question_id", "q_gen"))
            domain = str(item.get("clinical_domain", item.get("domain", "prakriti")))
            feature = str(item.get("question", item.get("feature", "intake_observation")))
            raw_answer = str(item.get("answer", ""))
            sub_domain = item.get("sub_domain")
            option_meta = item.get("option_meta")

            obs = self.normalizer.normalize(
                question_id=q_id,
                domain=domain,
                feature=feature,
                raw_answer=raw_answer,
                option_meta=option_meta,
                sub_domain=sub_domain
            )
            observations.append(obs)

        # 2. Run deterministic scoring across all 23 domains
        v2_result: AyushV2AssessmentResult = self.scoring_engine.evaluate_all(
            observations=observations,
            patient_age=patient_age
        )

        # 3. Format dictionary for compatibility with API and Physician Dashboard
        res_dict = v2_result.model_dump()

        # Add top-level backwards compatibility fields
        prak_res = v2_result.prakriti
        res_dict["prakriti"]["vata_score"] = prak_res.scores.get("Vata", 0)
        res_dict["prakriti"]["pitta_score"] = prak_res.scores.get("Pitta", 0)
        res_dict["prakriti"]["kapha_score"] = prak_res.scores.get("Kapha", 0)
        res_dict["prakriti"]["predominant_pattern"] = prak_res.primary_category or prak_res.summary
        res_dict["prakriti"]["confidence"] = "Insufficient Data" if prak_res.status == "INSUFFICIENT_DATA" else "High"

        # Evidence breakdown trace
        res_dict["evidence_count"] = len([o for o in observations if not o.is_denial])
        res_dict["why_breakdown"] = {
            "matched_features": prak_res.supporting_observations,
            "prakriti_supporting": prak_res.supporting_observations,
            "vikriti_supporting": v2_result.vikriti.supporting_observations,
            "agni_supporting": v2_result.agni.supporting_observations,
            "koshta_supporting": v2_result.koshta.supporting_observations,
            "all_observations": [o.model_dump() for o in observations]
        }

        return res_dict
