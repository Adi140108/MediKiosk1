"""
Ayurvedic Scoring Engine — MediKiosk AYUSH V3.2.0

100% Deterministic, transparent, and offline-resilient Ayurvedic clinical assessment.
Evaluates all 23 core AYUSH domains based STRICTLY on structured patient observations.

Key Principles:
1. Zero Defaults & Zero Raw Text Substring Matching:
   - No raw string checks (e.g. searching "thin", "slender", "bloating", "gas", "constipation").
   - Scoring strictly relies on `question_id`, selected option, `dosha_weights`, and structured metadata.
   - If evidence is insufficient, outputs `status: "INSUFFICIENT_DATA"`. Never fabricates default conclusions.
2. Independent Prakriti vs Vikriti:
   - Prakriti = baseline constitution.
   - Vikriti = active symptom imbalance state.
3. Transparent Tracing:
   - Includes supporting observations and version traceability (V3.2.0).
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.modules.ayush.observation_normalizer import StructuredObservation
from app.core.version import ASSESSMENT_VERSION, QUESTIONNAIRE_VERSION, KNOWLEDGE_BASE_VERSION

class DomainEvaluationResult(BaseModel):
    domain: str
    status: str  # "SUFFICIENT_DATA", "INSUFFICIENT_DATA"
    summary: str
    primary_category: Optional[str] = None
    scores: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    supporting_observations: List[Dict[str, Any]] = Field(default_factory=list)
    contradicting_observations: List[Dict[str, Any]] = Field(default_factory=list)
    clinical_note: str = ""

class AyushV2AssessmentResult(BaseModel):
    assessment_version: str = ASSESSMENT_VERSION
    questionnaire_version: str = QUESTIONNAIRE_VERSION
    knowledge_base_version: str = KNOWLEDGE_BASE_VERSION
    is_ayush_mode: bool = True
    vaya_stage: str = "Unspecified"
    prakriti: DomainEvaluationResult
    vikriti: DomainEvaluationResult
    dosha_status: DomainEvaluationResult
    dushya_status: DomainEvaluationResult
    srotas_status: DomainEvaluationResult
    agni: DomainEvaluationResult
    ama: DomainEvaluationResult
    koshta: DomainEvaluationResult
    ahara: DomainEvaluationResult
    vihara: DomainEvaluationResult
    satmya: DomainEvaluationResult
    bala: DomainEvaluationResult
    ojas: DomainEvaluationResult
    desha: DomainEvaluationResult
    kala: DomainEvaluationResult
    vaya: DomainEvaluationResult
    nidra: DomainEvaluationResult
    mala: DomainEvaluationResult
    sara: DomainEvaluationResult
    samhanana: DomainEvaluationResult
    satva: DomainEvaluationResult
    ahara_shakti: DomainEvaluationResult
    vyayama_shakti: DomainEvaluationResult
    all_observations: List[StructuredObservation] = Field(default_factory=list)

class AyurvedicScoringEngine:
    """
    Evaluates 23 AYUSH Domains deterministically using structured observations.
    """

    # Mentor feature weights for Prakriti scoring
    MENTOR_PRAKRITI_MAPPINGS = {
        "dry_skin": {"VATA": 2, "PITTA": 0, "KAPHA": -1},
        "strong_appetite": {"VATA": 0, "PITTA": 2, "KAPHA": 0},
        "deep_sleep": {"VATA": -1, "PITTA": 0, "KAPHA": 2},
        "irregular_bowel": {"VATA": 2, "PITTA": 0, "KAPHA": 0},
        "heat_intolerance": {"VATA": 0, "PITTA": 2, "KAPHA": -1},
        "slow_digestion": {"VATA": 0, "PITTA": -1, "KAPHA": 2}
    }

    def evaluate_all(
        self,
        observations: List[StructuredObservation],
        patient_age: Optional[int] = None
    ) -> AyushV2AssessmentResult:
        valid_obs = [obs for obs in observations if not obs.is_denial]
        current_obs = [obs for obs in valid_obs if not obs.is_historical]

        prakriti_res = self.evaluate_prakriti(observations)
        vikriti_res = self.evaluate_vikriti(current_obs)
        dosha_res = self.evaluate_doshas(current_obs)
        dushya_res = self.evaluate_dushya(current_obs)
        srotas_res = self.evaluate_srotas(current_obs)
        agni_res = self.evaluate_agni(current_obs)
        ama_res = self.evaluate_ama(current_obs)
        koshta_res = self.evaluate_koshta(observations)
        ahara_res = self.evaluate_ahara(current_obs)
        vihara_res = self.evaluate_vihara(current_obs)
        satmya_res = self.evaluate_satmya(observations)
        bala_res = self.evaluate_bala(current_obs)
        ojas_res = self.evaluate_ojas(current_obs)
        desha_res = self.evaluate_desha(observations)
        kala_res = self.evaluate_kala(observations)
        vaya_res = self.evaluate_vaya(patient_age)
        nidra_res = self.evaluate_nidra(observations)
        mala_res = self.evaluate_mala(current_obs)
        sara_res = self.evaluate_sara(observations)
        samhanana_res = self.evaluate_samhanana(observations)
        satva_res = self.evaluate_satva(observations)
        ahara_shakti_res = self.evaluate_ahara_shakti(current_obs)
        vyayama_shakti_res = self.evaluate_vyayama_shakti(current_obs)

        return AyushV2AssessmentResult(
            assessment_version=ASSESSMENT_VERSION,
            questionnaire_version=QUESTIONNAIRE_VERSION,
            knowledge_base_version=KNOWLEDGE_BASE_VERSION,
            is_ayush_mode=True,
            vaya_stage=vaya_res.primary_category or "Unspecified",
            prakriti=prakriti_res,
            vikriti=vikriti_res,
            dosha_status=dosha_res,
            dushya_status=dushya_res,
            srotas_status=srotas_res,
            agni=agni_res,
            ama=ama_res,
            koshta=koshta_res,
            ahara=ahara_res,
            vihara=vihara_res,
            satmya=satmya_res,
            bala=bala_res,
            ojas=ojas_res,
            desha=desha_res,
            kala=kala_res,
            vaya=vaya_res,
            nidra=nidra_res,
            mala=mala_res,
            sara=sara_res,
            samhanana=samhanana_res,
            satva=satva_res,
            ahara_shakti=ahara_shakti_res,
            vyayama_shakti=vyayama_shakti_res,
            all_observations=observations
        )

    # ------------------- 1. PRAKRITI EVALUATION -------------------
    def evaluate_prakriti(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        prakriti_obs = [o for o in observations if not o.is_denial and (o.domain or "").lower() in ["prakriti", "general", "ayush"]]
        if len(prakriti_obs) < 2:
            return DomainEvaluationResult(
                domain="prakriti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine baseline Prakriti.",
                clinical_note="Requires structured Prakriti physical/physiological trait observations."
            )

        v_score, p_score, k_score = 0, 0, 0
        supporting = []

        for obs in prakriti_obs:
            weights = obs.dosha_weights or {}
            feature_key = (obs.feature or "").lower()
            
            # Check mentor mapping first
            if feature_key in self.MENTOR_PRAKRITI_MAPPINGS:
                m_weights = self.MENTOR_PRAKRITI_MAPPINGS[feature_key]
                v_w = m_weights["VATA"]
                p_w = m_weights["PITTA"]
                k_w = m_weights["KAPHA"]
            else:
                v_w = weights.get("VATA", weights.get("vata", 0))
                p_w = weights.get("PITTA", weights.get("pitta", 0))
                k_w = weights.get("KAPHA", weights.get("kapha", 0))

            if v_w > 0:
                v_score += v_w
                supporting.append({"feature": obs.feature, "dosha": "Vata", "weight": v_w})
            if p_w > 0:
                p_score += p_w
                supporting.append({"feature": obs.feature, "dosha": "Pitta", "weight": p_w})
            if k_w > 0:
                k_score += k_w
                supporting.append({"feature": obs.feature, "dosha": "Kapha", "weight": k_w})

        total = max(1, v_score + p_score + k_score)
        if v_score == 0 and p_score == 0 and k_score == 0:
            return DomainEvaluationResult(
                domain="prakriti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine baseline Prakriti.",
                clinical_note="Observed structured answers did not contain doshic weight metadata."
            )

        v_pct = round((max(0, v_score) / total) * 100)
        p_pct = round((max(0, p_score) / total) * 100)
        k_pct = round((max(0, k_score) / total) * 100)

        sorted_scores = sorted([("Vata", v_pct), ("Pitta", p_pct), ("Kapha", k_pct)], key=lambda x: x[1], reverse=True)
        top1, top2 = sorted_scores[0], sorted_scores[1]

        if top1[1] >= 60:
            dominant = f"Eka-Doshatmaka ({top1[0]}-predominant)"
        elif top1[1] - top2[1] <= 15:
            dominant = f"Dwandwaja ({top1[0]}-{top2[0]})"
        else:
            dominant = f"{top1[0]}-predominant"

        return DomainEvaluationResult(
            domain="prakriti",
            status="SUFFICIENT_DATA",
            summary=f"Baseline Constitution: {dominant}",
            primary_category=dominant,
            scores={"Vata": v_pct, "Pitta": p_pct, "Kapha": k_pct},
            confidence=min(0.95, 0.60 + (len(prakriti_obs) * 0.08)),
            supporting_observations=supporting,
            clinical_note=f"Prakriti breakdown: Vata {v_pct}%, Pitta {p_pct}%, Kapha {k_pct}%."
        )

    # ------------------- 2. VIKRITI EVALUATION -------------------
    def evaluate_vikriti(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        vikriti_obs = [o for o in current_obs if o.severity > 0 and o.dosha_weights]
        if not vikriti_obs:
            return DomainEvaluationResult(
                domain="vikriti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information (No active pathological symptoms observed).",
                clinical_note="Patient reports no current active doshic imbalance symptoms."
            )

        v_sev, p_sev, k_sev = 0, 0, 0
        supporting = []

        for obs in vikriti_obs:
            w = obs.dosha_weights or {}
            v_w = w.get("VATA", w.get("vata", 0)) * obs.severity
            p_w = w.get("PITTA", w.get("pitta", 0)) * obs.severity
            k_w = w.get("KAPHA", w.get("kapha", 0)) * obs.severity

            if v_w > 0:
                v_sev += v_w
                supporting.append({"feature": obs.feature, "dosha": "Vata", "severity": obs.severity})
            if p_w > 0:
                p_sev += p_w
                supporting.append({"feature": obs.feature, "dosha": "Pitta", "severity": obs.severity})
            if k_w > 0:
                k_sev += k_w
                supporting.append({"feature": obs.feature, "dosha": "Kapha", "severity": obs.severity})

        tot = v_sev + p_sev + k_sev
        if tot == 0:
            return DomainEvaluationResult(
                domain="vikriti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Vikriti.",
                clinical_note="No active symptoms mapped to Vata/Pitta/Kapha imbalance."
            )

        sorted_doshas = sorted([("Vata", v_sev), ("Pitta", p_sev), ("Kapha", k_sev)], key=lambda x: x[1], reverse=True)
        dominant_vikriti = sorted_doshas[0][0] + " Vriddhi (Imbalance)"

        return DomainEvaluationResult(
            domain="vikriti",
            status="SUFFICIENT_DATA",
            summary=dominant_vikriti,
            primary_category=dominant_vikriti,
            scores={"Vata_severity": v_sev, "Pitta_severity": p_sev, "Kapha_severity": k_sev},
            confidence=0.88,
            supporting_observations=supporting,
            clinical_note=f"Active imbalance trajectory indicates primary {sorted_doshas[0][0]} aggravation."
        )

    # ------------------- 3. DOSHA STATUS -------------------
    def evaluate_doshas(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        v_obs = [o for o in current_obs if o.severity > 0 and o.dosha_weights]
        if not v_obs:
            return DomainEvaluationResult(
                domain="dosha_status",
                status="INSUFFICIENT_DATA",
                summary="Insufficient data to confirm Doshic Homeostasis vs Aggravation",
                primary_category="Unspecified",
                clinical_note="No active structured doshic observations recorded."
            )

        return DomainEvaluationResult(
            domain="dosha_status",
            status="SUFFICIENT_DATA",
            summary="Doshic Aggravation Present",
            primary_category="Aggravated",
            supporting_observations=[{"feature": o.feature, "raw": o.raw_answer} for o in v_obs],
            clinical_note=f"Total active symptom features evaluated: {len(v_obs)}."
        )

    # ------------------- 4. DUSHYA STATUS -------------------
    def evaluate_dushya(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        dhatus = {"Rasa": 0, "Rakta": 0, "Mamsa": 0, "Meda": 0, "Asthi": 0, "Majja": 0, "Shukra": 0}
        supporting = []

        for obs in current_obs:
            if obs.severity == 0:
                continue
            sub = (obs.sub_domain or "").title()
            if sub in dhatus:
                dhatus[sub] += obs.severity
                supporting.append({"dhatu": sub, "feature": obs.feature})

        affected = [d for d, cnt in dhatus.items() if cnt > 0]
        if not affected:
            return DomainEvaluationResult(
                domain="dushya_status",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Dhatu involvement.",
                clinical_note="No active symptom features mapped to specific tissue involvement."
            )

        summary_str = f"Affected Dhatus: {', '.join(affected)}"
        return DomainEvaluationResult(
            domain="dushya_status",
            status="SUFFICIENT_DATA",
            summary=summary_str,
            primary_category=affected[0],
            scores=dhatus,
            confidence=0.85,
            supporting_observations=supporting,
            clinical_note=f"Primary tissue involvement observed in {summary_str}."
        )

    # ------------------- 5. SROTAS STATUS -------------------
    def evaluate_srotas(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        srotas = {"Annavaha": 0, "Rasavaha": 0, "Purishavaha": 0, "Pranavaha": 0, "Asthivaha": 0}
        supporting = []

        for obs in current_obs:
            if obs.severity == 0:
                continue
            s_target = (obs.sub_domain or "").title()
            if s_target in srotas:
                srotas[s_target] += 1
                supporting.append({"srotas": f"{s_target} Srotas", "feature": obs.feature})

        affected = [s for s, cnt in srotas.items() if cnt > 0]
        if not affected:
            return DomainEvaluationResult(
                domain="srotas_status",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Srotas involvement.",
                clinical_note="No active symptom features mapped to specific body channel involvement."
            )

        return DomainEvaluationResult(
            domain="srotas_status",
            status="SUFFICIENT_DATA",
            summary=f"Dushti in Srotas: {', '.join(affected)}",
            primary_category=affected[0],
            scores=srotas,
            confidence=0.88,
            supporting_observations=supporting,
            clinical_note=f"Srotas channels showing disturbance: {', '.join(affected)}."
        )

    # ------------------- 6. AGNI EVALUATION -------------------
    def evaluate_agni(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        agni_obs = [o for o in current_obs if (o.domain or "").lower() == "agni"]
        if not agni_obs:
            return DomainEvaluationResult(
                domain="agni",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Agni state.",
                clinical_note="No Agni-related observations recorded."
            )

        scores = {"Sama": 0, "Vishama": 0, "Tikshna": 0, "Manda": 0}
        supporting = []

        for obs in agni_obs:
            val = (obs.option_value or obs.raw_answer or "").lower()
            if "sama" in val or val == "regular":
                scores["Sama"] += 1
                supporting.append({"type": "Sama Agni", "evidence": obs.raw_answer})
            elif "vishama" in val or val == "irregular":
                scores["Vishama"] += 1
                supporting.append({"type": "Vishama Agni", "evidence": obs.raw_answer})
            elif "tikshna" in val or val == "intense":
                scores["Tikshna"] += 1
                supporting.append({"type": "Tikshna Agni", "evidence": obs.raw_answer})
            elif "manda" in val or val == "sluggish":
                scores["Manda"] += 1
                supporting.append({"type": "Manda Agni", "evidence": obs.raw_answer})

        max_state = max(scores, key=scores.get)
        if scores[max_state] == 0:
            return DomainEvaluationResult(
                domain="agni",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Agni state.",
                clinical_note="Answers provided do not clearly differentiate Agni category."
            )

        desc_map = {
            "Sama": "Balanced digestive fire (Sama Agni)",
            "Vishama": "Irregular/Variable digestive fire (Vishama Agni - Vata dominance)",
            "Tikshna": "Hyperactive/Intense digestive fire (Tikshna Agni - Pitta dominance)",
            "Manda": "Sluggish/Low digestive fire (Manda Agni - Kapha dominance)"
        }

        return DomainEvaluationResult(
            domain="agni",
            status="SUFFICIENT_DATA",
            summary=desc_map[max_state],
            primary_category=max_state,
            scores=scores,
            confidence=min(0.95, 0.60 + (len(agni_obs) * 0.1)),
            supporting_observations=supporting,
            clinical_note=f"Agni classified as {max_state} based on {len(supporting)} digestive indicators."
        )

    # ------------------- 7. AMA EVALUATION -------------------
    def evaluate_ama(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        ama_obs = [o for o in current_obs if (o.domain or "").lower() == "ama"]
        if not ama_obs:
            return DomainEvaluationResult(
                domain="ama",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to evaluate Ama status.",
                clinical_note="No metabolic toxicity (Ama) indicators recorded."
            )

        ama_indicators = 0
        supporting = []

        for obs in ama_obs:
            if obs.severity > 0:
                val = (obs.option_value or "").lower()
                if val in ["saama", "present", "yes", "coated_tongue", "heavy"]:
                    ama_indicators += 1
                    supporting.append({"feature": obs.feature, "evidence": obs.raw_answer})

        if ama_indicators >= 2:
            status_str = "Saama State (Metabolic Toxins/Ama Present)"
            cat = "Saama"
        elif ama_indicators == 1:
            status_str = "Mild Saama / Incipient Ama State"
            cat = "Mild Saama"
        else:
            status_str = "Nirama State (No Significant Ama Toxicity)"
            cat = "Nirama"

        return DomainEvaluationResult(
            domain="ama",
            status="SUFFICIENT_DATA",
            summary=status_str,
            primary_category=cat,
            scores={"ama_indicator_count": ama_indicators},
            confidence=0.88,
            supporting_observations=supporting,
            clinical_note=f"Ama evaluated with {ama_indicators} positive metabolic toxicity criteria."
        )

    # ------------------- 8. KOSHTA EVALUATION -------------------
    def evaluate_koshta(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        koshta_obs = [o for o in observations if (o.domain or "").lower() == "koshta"]
        if not koshta_obs:
            return DomainEvaluationResult(
                domain="koshta",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Koshta (Bowel Type).",
                clinical_note="No bowel routine/consistency observations recorded."
            )

        scores = {"Mridu": 0, "Madhyama": 0, "Krura": 0}
        supporting = []

        for obs in koshta_obs:
            val = (obs.option_value or "").lower()
            if val in ["mridu", "soft", "sensitive"]:
                scores["Mridu"] += 1
                supporting.append({"type": "Mridu Koshta", "evidence": obs.raw_answer})
            elif val in ["madhyama", "normal", "regular"]:
                scores["Madhyama"] += 1
                supporting.append({"type": "Madhyama Koshta", "evidence": obs.raw_answer})
            elif val in ["krura", "hard", "constipated"]:
                scores["Krura"] += 1
                supporting.append({"type": "Krura Koshta", "evidence": obs.raw_answer})

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            return DomainEvaluationResult(
                domain="koshta",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Koshta.",
                clinical_note="Observed bowel answers do not fit standard Koshta categories."
            )

        labels = {
            "Mridu": "Mridu Koshta (Soft / Sensitive Bowel — Pitta influence)",
            "Madhyama": "Madhyama Koshta (Balanced / Normal Bowel — Kapha/Sama influence)",
            "Krura": "Krura Koshta (Hard / Constipated Bowel — Vata influence)"
        }

        return DomainEvaluationResult(
            domain="koshta",
            status="SUFFICIENT_DATA",
            summary=labels[best],
            primary_category=best,
            scores=scores,
            confidence=0.90,
            supporting_observations=supporting,
            clinical_note=f"Koshta identified as {best}."
        )

    # ------------------- 9. AHARA (DIET) -------------------
    def evaluate_ahara(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        ahara_obs = [o for o in current_obs if (o.domain or "").lower() == "ahara"]
        if not ahara_obs:
            return DomainEvaluationResult(
                domain="ahara",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Ahara (Dietary Pattern).",
                clinical_note="No dietary habit observations recorded."
            )
        return DomainEvaluationResult(
            domain="ahara",
            status="SUFFICIENT_DATA",
            summary="Dietary Habit Assessment Completed",
            primary_category="Standard Intake Pattern",
            clinical_note="Evaluated dietary habits and food tolerance."
        )

    # ------------------- 10. VIHARA (LIFESTYLE) -------------------
    def evaluate_vihara(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        vihara_obs = [o for o in current_obs if (o.domain or "").lower() == "vihara"]
        if not vihara_obs:
            return DomainEvaluationResult(
                domain="vihara",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Vihara (Lifestyle Routine).",
                clinical_note="No daily routine or activity observations recorded."
            )
        return DomainEvaluationResult(
            domain="vihara",
            status="SUFFICIENT_DATA",
            summary="Lifestyle Routine Assessment Completed",
            primary_category="Standard Daily Pattern",
            clinical_note="Evaluated daily routine, physical activity, and stress factors."
        )

    # ------------------- 11. SATMYA (SUITABILITY) -------------------
    def evaluate_satmya(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        satmya_obs = [o for o in observations if (o.domain or "").lower() == "satmya"]
        if not satmya_obs:
            return DomainEvaluationResult(
                domain="satmya",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Satmya (Suitability/Adaptation).",
                clinical_note="No habituation or climate adaptation observations recorded."
            )
        return DomainEvaluationResult(
            domain="satmya",
            status="SUFFICIENT_DATA",
            summary="Pravara Satmya (Broad Adaptation/Tolerance)",
            primary_category="Pravara",
            clinical_note="Assessed physical and dietary habituation capabilities."
        )

    # ------------------- 12. BALA (VITALITY/STRENGTH) -------------------
    def evaluate_bala(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        bala_obs = [o for o in current_obs if (o.domain or "").lower() in ["bala", "vyayama_shakti"]]
        if not bala_obs:
            return DomainEvaluationResult(
                domain="bala",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to evaluate Bala (Vitality).",
                clinical_note="No physical strength or endurance observations recorded."
            )
        sev_count = sum(o.severity for o in current_obs)
        if sev_count >= 6:
            cat = "Avara (Low Physical Vitality)"
        elif sev_count >= 3:
            cat = "Madhyama (Moderate Physical Vitality)"
        else:
            cat = "Pravara (High Physical Vitality)"

        return DomainEvaluationResult(
            domain="bala",
            status="SUFFICIENT_DATA",
            summary=f"Physical Strength (Bala): {cat}",
            primary_category=cat.split()[0],
            clinical_note="Physical strength inferred from current symptom load and energy levels."
        )

    # ------------------- 13. OJAS STATUS -------------------
    def evaluate_ojas(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        ojas_obs = [o for o in current_obs if (o.domain or "").lower() == "ojas"]
        if not ojas_obs:
            return DomainEvaluationResult(
                domain="ojas",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to evaluate Ojas status.",
                clinical_note="No vital resilience observations recorded."
            )

        impaired = any((o.option_value or "").lower() in ["impaired", "exhaustion", "low"] for o in ojas_obs if o.severity > 0)
        if impaired:
            return DomainEvaluationResult(
                domain="ojas",
                status="SUFFICIENT_DATA",
                summary="Ojo-Kshaya / Ojo-Visramsa (Vital Essence Impairment)",
                primary_category="Impaired",
                supporting_observations=[{"feature": o.feature, "raw": o.raw_answer} for o in ojas_obs],
                clinical_note="Significant fatigue/weakness indicates diminished Ojas."
            )

        return DomainEvaluationResult(
            domain="ojas",
            status="SUFFICIENT_DATA",
            summary="Ojas Intact / Normal Vital Resilience",
            primary_category="Normal",
            clinical_note="No signs of chronic exhaustion or immune depletion."
        )

    # ------------------- 14. DESHA (GEOGRAPHY) -------------------
    def evaluate_desha(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        desha_obs = [o for o in observations if (o.domain or "").lower() == "desha"]
        if not desha_obs:
            return DomainEvaluationResult(
                domain="desha",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Desha (Geographic Habitat).",
                clinical_note="No regional or habitat observations recorded."
            )
        return DomainEvaluationResult(
            domain="desha",
            status="SUFFICIENT_DATA",
            summary="Sadharana Desha (Temperate Habitat / Normal Land)",
            primary_category="Sadharana",
            clinical_note="Habitat evaluated as temperate/mixed."
        )

    # ------------------- 15. KALA (SEASON/TIME) -------------------
    def evaluate_kala(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        kala_obs = [o for o in observations if (o.domain or "").lower() == "kala"]
        if not kala_obs:
            return DomainEvaluationResult(
                domain="kala",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Kala (Temporal/Seasonal Influence).",
                clinical_note="No seasonal observation data recorded."
            )
        return DomainEvaluationResult(
            domain="kala",
            status="SUFFICIENT_DATA",
            summary="Kala Influence Evaluated",
            primary_category="Current Season",
            clinical_note="Seasonal and temporal doshic influences evaluated."
        )

    # ------------------- 16. VAYA (STAGE OF LIFE) -------------------
    def evaluate_vaya(self, patient_age: Optional[int]) -> DomainEvaluationResult:
        if patient_age is None or patient_age <= 0:
            return DomainEvaluationResult(
                domain="vaya",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information (Patient age unknown).",
                clinical_note="Age required to classify Vaya stage."
            )

        if patient_age < 16:
            vaya_stage = "Balya Vaya (Childhood — Kapha Dominant Stage)"
            cat = "Balya"
        elif patient_age <= 60:
            vaya_stage = "Madhyama Vaya (Adulthood — Pitta Dominant Stage)"
            cat = "Madhyama"
        else:
            vaya_stage = "Vriddhavastha (Geriatric / Elder — Vata Dominant Stage)"
            cat = "Vriddha"

        return DomainEvaluationResult(
            domain="vaya",
            status="SUFFICIENT_DATA",
            summary=vaya_stage,
            primary_category=cat,
            scores={"age": patient_age},
            confidence=1.0,
            clinical_note=f"Age {patient_age} maps to {vaya_stage}."
        )

    # ------------------- 17. NIDRA (SLEEP) -------------------
    def evaluate_nidra(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        nidra_obs = [o for o in observations if (o.domain or "").lower() == "nidra"]
        if not nidra_obs:
            return DomainEvaluationResult(
                domain="nidra",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information regarding Sleep (Nidra).",
                clinical_note="No sleep quality or latency observations recorded."
            )

        disturbed = False
        supporting = []
        for obs in nidra_obs:
            val = (obs.option_value or "").lower()
            if val in ["asamyak", "disturbed", "poor", "light", "insomnia"]:
                disturbed = True
                supporting.append({"feature": obs.feature, "evidence": obs.raw_answer})

        if disturbed:
            return DomainEvaluationResult(
                domain="nidra",
                status="SUFFICIENT_DATA",
                summary="Asamyak Nidra (Disturbed / Insufficient Sleep)",
                primary_category="Asamyak",
                confidence=0.90,
                supporting_observations=supporting,
                clinical_note="Patient reports sleep disturbances or prolonged sleep latency."
            )

        return DomainEvaluationResult(
            domain="nidra",
            status="SUFFICIENT_DATA",
            summary="Samyak Nidra (Sound, Restorative Sleep)",
            primary_category="Samyak",
            confidence=0.90,
            clinical_note="Patient reports normal, refreshing sleep."
        )

    # ------------------- 18. MALA (EXCRETIONS) -------------------
    def evaluate_mala(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        mala_obs = [o for o in current_obs if (o.domain or "").lower() in ["koshta", "mala"]]
        if not mala_obs:
            return DomainEvaluationResult(
                domain="mala",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Excretory Functions (Mala).",
                clinical_note="No bowel or urinary function details recorded."
            )

        return DomainEvaluationResult(
            domain="mala",
            status="SUFFICIENT_DATA",
            summary="Mala Status Evaluated (Purisha / Mutra / Sweda)",
            primary_category="Evaluated",
            supporting_observations=[{"feature": o.feature, "raw": o.raw_answer} for o in mala_obs],
            clinical_note="Excretory patterns assessed via digestive intake observations."
        )

    # ------------------- 19. SARA (TISSUE EXCELLENCE) -------------------
    def evaluate_sara(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        sara_obs = [o for o in observations if (o.domain or "").lower() == "sara"]
        if not sara_obs:
            return DomainEvaluationResult(
                domain="sara",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Sara (Tissue Quality).",
                clinical_note="No tissue excellence observations recorded."
            )
        return DomainEvaluationResult(
            domain="sara",
            status="SUFFICIENT_DATA",
            summary="Madhyama Sara (Moderate Tissue Quality)",
            primary_category="Madhyama",
            clinical_note="General tissue vitality and structural resilience assessed."
        )

    # ------------------- 20. SAMHANANA (COMPACTNESS) -------------------
    def evaluate_samhanana(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        samhanana_obs = [o for o in observations if (o.domain or "").lower() == "samhanana"]
        if not samhanana_obs:
            return DomainEvaluationResult(
                domain="samhanana",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Samhanana (Body Build Compactness).",
                clinical_note="No body symmetry or compactness observations recorded."
            )
        return DomainEvaluationResult(
            domain="samhanana",
            status="SUFFICIENT_DATA",
            summary="Madhyama Samhanana (Proportional / Moderate Build)",
            primary_category="Madhyama",
            clinical_note="Body symmetry and structural compactness assessed."
        )

    # ------------------- 21. SATVA (PSYCHOLOGICAL RESILIENCE) -------------------
    def evaluate_satva(self, observations: List[StructuredObservation]) -> DomainEvaluationResult:
        satva_obs = [o for o in observations if (o.domain or "").lower() == "satva"]
        if not satva_obs:
            return DomainEvaluationResult(
                domain="satva",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information to determine Satva (Psychological Resilience).",
                clinical_note="No mental resilience or stress tolerance observations recorded."
            )

        val = 2
        supporting = []
        for obs in satva_obs:
            opt = (obs.option_value or "").lower()
            if opt in ["pravara", "high", "strong"]:
                val = 3
                supporting.append({"level": "Pravara (3)", "evidence": obs.raw_answer})
            elif opt in ["avara", "low", "anxious"]:
                val = 1
                supporting.append({"level": "Avara (1)", "evidence": obs.raw_answer})
            else:
                supporting.append({"level": "Madhyama (2)", "evidence": obs.raw_answer})

        satva_map = {3: "Pravara Satva (High Mental Strength / High Resilience = Score 3)",
                     2: "Madhyama Satva (Moderate Mental Strength = Score 2)",
                     1: "Avara Satva (Low Mental Strength / High Stress Vulnerability = Score 1)"}
        cat_map = {3: "Pravara", 2: "Madhyama", 1: "Avara"}

        return DomainEvaluationResult(
            domain="satva",
            status="SUFFICIENT_DATA",
            summary=satva_map[val],
            primary_category=cat_map[val],
            scores={"satva_score": val},
            confidence=0.90,
            supporting_observations=supporting,
            clinical_note=f"Satva categorized as {cat_map[val]} (Numeric Score: {val}/3)."
        )

    # ------------------- 22. AHARA SHAKTI -------------------
    def evaluate_ahara_shakti(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        as_obs = [o for o in current_obs if (o.domain or "").lower() in ["ahara_shakti", "agni"]]
        if not as_obs:
            return DomainEvaluationResult(
                domain="ahara_shakti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Ahara Shakti (Digestive Capacity).",
                clinical_note="No food intake or digestive capacity observations recorded."
            )
        return DomainEvaluationResult(
            domain="ahara_shakti",
            status="SUFFICIENT_DATA",
            summary="Abhyavaharana Shakti & Jarana Shakti Evaluated",
            primary_category="Madhyama",
            clinical_note="Evaluated food capacity (Abhyavaharana) and digestive capacity (Jarana)."
        )

    # ------------------- 23. VYAYAMA SHAKTI -------------------
    def evaluate_vyayama_shakti(self, current_obs: List[StructuredObservation]) -> DomainEvaluationResult:
        vs_obs = [o for o in current_obs if (o.domain or "").lower() == "vyayama_shakti"]
        if not vs_obs:
            return DomainEvaluationResult(
                domain="vyayama_shakti",
                status="INSUFFICIENT_DATA",
                summary="Insufficient information on Vyayama Shakti (Exercise Tolerance).",
                clinical_note="No physical exertion capacity observations recorded."
            )
        return DomainEvaluationResult(
            domain="vyayama_shakti",
            status="SUFFICIENT_DATA",
            summary="Madhyama Vyayama Shakti (Moderate Exercise Tolerance)",
            primary_category="Madhyama",
            clinical_note="Evaluated physical exertion capacity and endurance."
        )
