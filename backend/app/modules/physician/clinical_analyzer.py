"""
MediKiosk Clinical Analysis & Narrative Synthesis Engine
Transforms patient intake dialogue, pain scores, and medical history into
rigorous, physician-grade History of Present Illness (HPI) narratives and
clinical documentation.

Never dumps raw colloquial patient transcripts verbatim.
Parses medical semantics: acuity, chronology, injury mechanism, pain character,
functional impairment, objective local signs, modulating factors, and negative rule-outs.
Uses word-boundary regexes and negation awareness to avoid false substring collisions.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.intake import PatientContextState

logger = logging.getLogger("medikiosk.clinical_analyzer")

class ClinicalAnalysisResult:
    def __init__(
        self,
        hpi_narrative: str,
        symptom_progression: str,
        severity_score: int,
        severity_label: str,
        chronology_text: str,
        mechanism_text: Optional[str],
        aggravating_factors: List[str],
        relieving_factors: List[str],
        objective_signs: List[str],
        negative_findings: List[str],
        associated_symptoms: List[str]
    ):
        self.hpi_narrative = hpi_narrative
        self.symptom_progression = symptom_progression
        self.severity_score = severity_score
        self.severity_label = severity_label
        self.chronology_text = chronology_text
        self.mechanism_text = mechanism_text
        self.aggravating_factors = aggravating_factors
        self.relieving_factors = relieving_factors
        self.objective_signs = objective_signs
        self.negative_findings = negative_findings
        self.associated_symptoms = associated_symptoms


class ClinicalAnalysisEngine:
    """
    Expert clinical documentation synthesizer.
    Analyzes multi-turn dialogue answers and context to produce a structured,
    cohesive, and professional medical HPI summary.
    """

    @classmethod
    def analyze(
        cls,
        chief_complaint: str,
        qa_pairs: List[Dict[str, Any]],
        context: Optional[PatientContextState] = None
    ) -> ClinicalAnalysisResult:
        all_answers_text = " ".join([p.get("answer", "") for p in qa_pairs])
        combined_text = f"{chief_complaint} {all_answers_text}".lower()

        # ── 1. Severity Extraction ──
        severity_score = cls._extract_severity(all_answers_text, context)
        if severity_score >= 8:
            severity_label = "Severe"
        elif severity_score >= 6:
            severity_label = "Moderate-to-Severe"
        elif severity_score >= 4:
            severity_label = "Moderate"
        else:
            severity_label = "Mild"

        # ── 2. Chronology & Onset ──
        duration_phrase, onset_type = cls._extract_chronology(combined_text, context)

        # ── 3. Mechanism of Injury / Etiology / Trigger ──
        mechanism = cls._extract_mechanism(combined_text)

        # ── 4. Pain Character & Quality ──
        pain_character = cls._extract_pain_character(combined_text)

        # ── 5. Functional Limitations ──
        functional_impact = cls._extract_functional_impact(combined_text)

        # ── 6. Objective Signs & Local Features ──
        objective_signs = cls._extract_objective_signs(combined_text)

        # ── 7. Negative Findings & Rule-outs ──
        negatives = cls._extract_negatives(combined_text)

        # ── 8. Aggravating Factors ──
        aggravating = cls._extract_aggravating(combined_text, qa_pairs)

        # ── 9. Relieving Factors ──
        relieving = cls._extract_relieving(combined_text, qa_pairs)

        # ── 10. Associated Symptoms ──
        associated = cls._extract_associated(combined_text, context)

        # ── 11. Medicalize Chief Complaint ──
        medical_complaint, anatomical_site = cls._medicalize_complaint(chief_complaint)

        # ── 12. Build Cohesive Medical HPI Narrative ──
        sentences = []

        # Sentence 1: Presentation & Chief Complaint
        acuity_str = "acute-onset" if onset_type == "acute" else ("insidiously progressive" if onset_type == "gradual" else "clinical presentation of")
        if anatomical_site:
            sentences.append(
                f"Patient presents with an {acuity_str} {medical_complaint} primarily involving the {anatomical_site}."
            )
        else:
            sentences.append(
                f"Patient presents with an {acuity_str} complaint of {medical_complaint}."
            )

        # Sentence 2: Chronology and Mechanism
        chrono_parts = []
        if duration_phrase:
            chrono_parts.append(f"Symptoms originated approximately {duration_phrase}")
        else:
            chrono_parts.append("Symptoms have been active prior to presentation")

        if mechanism:
            chrono_parts.append(f"following {mechanism}")
        
        sentences.append(" ".join(chrono_parts) + ".")

        # Sentence 3: Pain Intensity, Character & Functional Impairment
        char_clause = f"characterized as {pain_character}" if pain_character else "noted"
        severity_clause = f"graded at {severity_score}/10 ({severity_label.lower()})"
        
        if functional_impact:
            sentences.append(
                f"Pain intensity is {severity_clause} and {char_clause}, causing {functional_impact}."
            )
        else:
            sentences.append(
                f"Symptom severity is {severity_clause} and {char_clause}."
            )

        # Sentence 4: Objective Physical Signs & Negative Rule-Outs
        signs_and_negs = []
        if objective_signs:
            signs_and_negs.append(f"Clinical features indicate {', '.join(objective_signs)}")
        if negatives:
            neg_text = "; ".join(negatives)
            if signs_and_negs:
                signs_and_negs.append(f"with {neg_text}")
            else:
                signs_and_negs.append(f"Clinical assessment confirms {neg_text}")
        
        if signs_and_negs:
            sentences.append(" ".join(signs_and_negs) + ".")

        # Sentence 5: Modulating Factors
        modulating_parts = []
        if aggravating:
            modulating_parts.append(f"exacerbated by {cls._join_natural(aggravating)}")
        if relieving:
            modulating_parts.append(f"partially mitigated by {cls._join_natural(relieving)}")
        
        if modulating_parts:
            sentences.append(f"Symptoms are {' and '.join(modulating_parts)}.")

        # Assemble clean paragraph
        hpi_narrative = " ".join(sentences)

        # Trajectory
        if duration_phrase:
            progression_text = f"Active {duration_phrase} course; severity rated {severity_score}/10 ({severity_label}) with functional limitation"
        else:
            progression_text = f"Persistent {severity_label.lower()} presentation rated {severity_score}/10"

        return ClinicalAnalysisResult(
            hpi_narrative=hpi_narrative,
            symptom_progression=progression_text,
            severity_score=severity_score,
            severity_label=severity_label,
            chronology_text=duration_phrase or "acute",
            mechanism_text=mechanism,
            aggravating_factors=aggravating,
            relieving_factors=relieving,
            objective_signs=objective_signs,
            negative_findings=negatives,
            associated_symptoms=associated
        )

    # ─────────────────────────────────────────────────────────────
    # Internal Clinical Parsing Subroutines
    # ─────────────────────────────────────────────────────────────

    @classmethod
    def _is_negated(cls, term: str, text: str) -> bool:
        """Checks if a term is preceded by negation (e.g. 'no open wound', 'without fever', 'denies vomiting')."""
        pattern = rf'\b(?:no|not|without|denies|denied|never)\s+(?:[\w]+\s+){{0,3}}{re.escape(term)}'
        return bool(re.search(pattern, text, re.IGNORECASE))

    @classmethod
    def _join_natural(cls, items: List[str]) -> str:
        if not items:
            return ""
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return f"{items[0]} and {items[1]}"
        return f"{', '.join(items[:-1])}, and {items[-1]}"

    @classmethod
    def _extract_severity(cls, text: str, context: Optional[PatientContextState]) -> int:
        m = re.search(r'\b(\d{1,2})\s*(?:out of|/)\s*10\b', text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val

        m = re.search(r'\brated\s*(\d{1,2})\b', text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val

        m = re.search(r'\bpain\s*(?:is|level|score)?\s*(\d{1,2})\b', text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return val

        if context and context.severity is not None:
            return context.severity

        # Qualitative fallback
        lower = text.lower()
        if re.search(r'\b(?:unbearable|excruciating|severe|extreme)\b', lower):
            return 8
        if re.search(r'\b(?:moderate|medium|distressing)\b', lower):
            return 5
        if re.search(r'\b(?:mild|slight|minor)\b', lower):
            return 3

        return 5

    @classmethod
    def _extract_chronology(cls, text: str, context: Optional[PatientContextState]) -> Tuple[str, str]:
        onset_type = "acute"
        if re.search(r'\b(?:sudden|suddenly|abrupt|abruptly)\b', text) or "all of a sudden" in text:
            onset_type = "acute"
        elif re.search(r'\b(?:gradual|gradually|slowly)\b', text) or "over time" in text:
            onset_type = "gradual"

        m = re.search(r'\b(\d+)\s*(?:day|days)\s*ago\b', text)
        if m:
            return f"{m.group(1)} days prior to presentation", onset_type

        m = re.search(r'\b(?:for|since)\s*(\d+)\s*(?:day|days)\b', text)
        if m:
            return f"over the past {m.group(1)} days", onset_type

        m = re.search(r'\b(\d+)\s*(?:hour|hours)\s*ago\b', text)
        if m:
            return f"{m.group(1)} hours prior to presentation", onset_type

        m = re.search(r'\b(\d+)\s*(?:week|weeks)\s*ago\b', text)
        if m:
            return f"{m.group(1)} weeks prior to presentation", "subacute"

        if re.search(r'\byesterday\b', text):
            return "yesterday (approximately 24 hours prior)", "acute"
        if re.search(r'\bthis morning\b', text):
            return "earlier today", "acute"

        if context and context.duration:
            return context.duration, onset_type

        return "", onset_type

    @classmethod
    def _extract_mechanism(cls, text: str) -> Optional[str]:
        mechanisms = []

        # Twisting / rotational trauma
        if re.search(r'\b(?:twist|twisted|twisting)\b', text):
            mechanisms.append("a mechanical twisting injury")
        elif re.search(r'\b(?:fell|fall|falling|slip|slipped)\b', text):
            mechanisms.append("mechanical trauma sustained from a fall")
        elif re.search(r'\b(?:hit|struck|accident|collision)\b', text):
            mechanisms.append("blunt physical trauma")
        elif re.search(r'\b(?:lifting heavy|heavy lifting|heavy weight|strained by lifting)\b', text):
            mechanisms.append("musculoskeletal strain secondary to heavy physical lifting")

        # Context of sports / athletic activity
        sports = []
        for s in ["badminton", "cricket", "football", "soccer", "tennis", "running", "basketball", "gym"]:
            if re.search(rf'\b{s}\b', text):
                sports.append(s)
        
        if sports:
            sport_str = f"during athletic activity ({', '.join(sports)})"
            if mechanisms:
                return f"{mechanisms[0]} {sport_str}"
            return sport_str

        # Dietary / gastrointestinal triggers
        if re.search(r'\b(?:spicy|street food|oily food)\b', text):
            return "dietary provocation associated with ingestion of spicy or irritant foods"
        if "empty stomach" in text:
            return "fasting or prolonged inter-meal intervals"

        # Exertional triggers (e.g. stairs, climbing)
        if re.search(r'\b(?:climbing stairs|running upstairs|physical exertion)\b', text):
            return "acute physical exertion"

        if mechanisms:
            return mechanisms[0]

        return None

    @classmethod
    def _extract_pain_character(cls, text: str) -> Optional[str]:
        qualities = []
        if re.search(r'\bthrobbing\b', text) and not cls._is_negated("throbbing", text):
            qualities.append("throbbing and pulsatile")
        if re.search(r'\b(?:sharp|stabbing)\b', text) and not cls._is_negated("sharp", text):
            qualities.append("sharp and lancinating")
        if re.search(r'\b(?:dull ache|dull aching|aching pain)\b', text) and not cls._is_negated("dull", text):
            qualities.append("a persistent dull ache")
        if re.search(r'\bburning\b', text) and not cls._is_negated("burning", text):
            qualities.append("burning in nature")
        if re.search(r'\b(?:cramping|spasm)\b', text) and not cls._is_negated("cramping", text):
            qualities.append("spasmodic cramping")
        if re.search(r'\b(?:crushing|pressure|oppressive)\b', text) or re.search(r'\bheavy pressure\b', text):
            qualities.append("oppressive constrictive pressure")
        if re.search(r'\b(?:stiff|stiffness)\b', text) and not cls._is_negated("stiffness", text) and not cls._is_negated("stiff", text):
            qualities.append("marked joint stiffness")

        return ", ".join(qualities) if qualities else None

    @classmethod
    def _extract_functional_impact(cls, text: str) -> Optional[str]:
        impacts = []
        if re.search(r'\b(?:weight|bearing weight|putting weight)\b', text) and not cls._is_negated("weight", text):
            impacts.append("marked difficulty and intolerance during weight-bearing and ambulation")
        elif re.search(r'\b(?:limp|limping|inability to walk)\b', text):
            impacts.append("functional impairment with significant ambulatory compromise")
        
        if re.search(r'\bsleep\b', text) and not cls._is_negated("sleep", text):
            impacts.append("sleep disruption")
        if re.search(r'\b(?:daily work|daily activities|routine tasks)\b', text):
            impacts.append("restriction in activities of daily living")

        return " and ".join(impacts) if impacts else None

    @classmethod
    def _extract_objective_signs(cls, text: str) -> List[str]:
        signs = []
        if re.search(r'\b(?:fluid|fluid buildup|effusion)\b', text) and not cls._is_negated("fluid", text):
            signs.append("intra-articular joint effusion with fluid accumulation")
        if re.search(r'\b(?:warmth|warm|heat)\b', text) and not cls._is_negated("warmth", text) and not cls._is_negated("warm", text):
            signs.append("localized hyperthermia (warmth)")
        if re.search(r'\b(?:swelling|swollen)\b', text) and not cls._is_negated("swelling", text) and not cls._is_negated("swollen", text):
            signs.append("periarticular soft tissue edema")
        if re.search(r'\b(?:redness|erythema)\b', text) and not cls._is_negated("redness", text):
            signs.append("associated cutaneous erythema")
        if re.search(r'\b(?:stiff|stiffness)\b', text) and not cls._is_negated("stiffness", text) and not cls._is_negated("stiff", text):
            signs.append("restricted range of joint motion")
        if re.search(r'\b(?:bloating|distention|acid reflux)\b', text) and not cls._is_negated("bloating", text):
            signs.append("abdominal distention and dyspeptic fullness")
        return signs

    @classmethod
    def _extract_negatives(cls, text: str) -> List[str]:
        negs = []
        if cls._is_negated("open wound", text) or cls._is_negated("wound", text) or cls._is_negated("cut", text) or cls._is_negated("laceration", text):
            negs.append("absence of open cutaneous wounds or skin breakdown")
        if cls._is_negated("fever", text) or cls._is_negated("chills", text):
            negs.append("absence of febrile illness or constitutional symptoms")
        if cls._is_negated("numbness", text) or cls._is_negated("tingling", text) or cls._is_negated("paresthesia", text):
            negs.append("intact distal neurovascular function without paresthesias")
        if cls._is_negated("blood", text) or cls._is_negated("bleeding", text):
            negs.append("denial of overt hemorrhage or bleeding")
        if cls._is_negated("vomit", text) or cls._is_negated("vomiting", text) or cls._is_negated("emesis", text):
            negs.append("absence of emesis")
        if cls._is_negated("neck stiffness", text):
            negs.append("absence of meningeal signs or nuchal rigidity")
        return negs

    @classmethod
    def _extract_aggravating(cls, text: str, qa_pairs: List[Dict[str, Any]]) -> List[str]:
        factors = []
        if re.search(r'\b(?:putting weight|bearing weight|axial loading)\b', text):
            factors.append("weight-bearing and axial loading")
        elif re.search(r'\bweight\b', text) and not cls._is_negated("weight", text):
            factors.append("weight-bearing")
        
        if re.search(r'\b(?:walking|running|movement|mobilization|bending)\b', text) and not cls._is_negated("movement", text):
            factors.append("active joint mobilization")
        if re.search(r'\b(?:bright light|light)\b', text) and not cls._is_negated("light", text):
            factors.append("bright environmental light (photophobia)")
        if re.search(r'\b(?:loud sound|sound|noise)\b', text) and not cls._is_negated("sound", text):
            factors.append("auditory stimuli (phonophobia)")
        if re.search(r'\b(?:spicy food|after eating|after meals|postprandial)\b', text):
            factors.append("postprandial intake")
        if re.search(r'\b(?:exertion|straining|stairs|climbing)\b', text):
            factors.append("physical exertion")
        return factors

    @classmethod
    def _extract_relieving(cls, text: str, qa_pairs: List[Dict[str, Any]]) -> List[str]:
        factors = []
        if re.search(r'\b(?:ice|ice pack|ice packs|cold compress)\b', text):
            factors.append("local cryotherapy (ice pack application)")
        if re.search(r'\b(?:resting|rest|lying down)\b', text) and not cls._is_negated("rest", text):
            factors.append("non-weight-bearing physical rest")
        if re.search(r'\b(?:warm compress|hot compress|heat pack)\b', text):
            factors.append("local thermotherapy")
        if re.search(r'\b(?:antacid|antacids)\b', text):
            factors.append("over-the-counter antacids")
        if re.search(r'\b(?:dark room|quiet room|dark quiet)\b', text) or (re.search(r'\bdark\b', text) and re.search(r'\bquiet\b', text)):
            factors.append("sensory deprivation in a dark, quiet room")
        if re.search(r'\b(?:painkiller|pain medication|paracetamol|ibuprofen|analgesic)\b', text):
            factors.append("oral analgesic medication")
        return factors

    @classmethod
    def _extract_associated(cls, text: str, context: Optional[PatientContextState]) -> List[str]:
        assoc = []
        if re.search(r'\b(?:nausea|nauseous)\b', text) and not cls._is_negated("nausea", text):
            assoc.append("Nausea")
        if re.search(r'\b(?:vomit|vomiting|emesis)\b', text) and not cls._is_negated("vomit", text) and not cls._is_negated("vomiting", text):
            assoc.append("Vomiting")
        if re.search(r'\b(?:dizziness|lightheaded|lightheadedness)\b', text) and not cls._is_negated("dizziness", text):
            assoc.append("Dizziness / Lightheadedness")
        if re.search(r'\b(?:short of breath|shortness of breath|breathlessness|dyspnea)\b', text) and not cls._is_negated("breath", text):
            assoc.append("Dyspnea")
        if re.search(r'\b(?:sweat|sweating|diaphoresis)\b', text) and not cls._is_negated("sweat", text) and not cls._is_negated("sweating", text):
            assoc.append("Diaphoresis")
        if re.search(r'\b(?:warmth|heat)\b', text) and not cls._is_negated("warmth", text):
            assoc.append("Local hyperthermia (warmth)")
        if re.search(r'\b(?:effusion|fluid buildup)\b', text) and not cls._is_negated("fluid", text):
            assoc.append("Joint effusion")
        if re.search(r'\bswelling\b', text) and not cls._is_negated("swelling", text):
            assoc.append("Periarticular swelling")

        if context and context.associated_symptoms:
            for s in context.associated_symptoms:
                s_title = s.title()
                if s_title not in assoc:
                    assoc.append(s_title)

        return assoc

    @classmethod
    def _medicalize_complaint(cls, complaint: str) -> Tuple[str, Optional[str]]:
        comp_lower = complaint.lower().strip()

        # Anatomical site detection
        site = None
        if "right knee" in comp_lower:
            site = "right knee joint"
        elif "left knee" in comp_lower:
            site = "left knee joint"
        elif "knee" in comp_lower:
            site = "knee articulation"
        elif "shoulder" in comp_lower:
            site = "shoulder joint"
        elif "ankle" in comp_lower:
            site = "ankle joint"
        elif "head" in comp_lower:
            site = "cranial region"
        elif "chest" in comp_lower:
            site = "anterior thoracic region"
        elif "abdomen" in comp_lower or "stomach" in comp_lower or "belly" in comp_lower:
            site = "epigastric / abdominal area"
        elif "back" in comp_lower or "spine" in comp_lower:
            site = "lumbar spine"

        # Clinical formulation
        if "swelling" in comp_lower and "pain" in comp_lower:
            if "throbbing" in comp_lower:
                return "throbbing arthralgia accompanied by marked periarticular swelling", site
            return "pain and associated inflammatory swelling / effusion", site
        elif "throbbing pain" in comp_lower:
            return "severe throbbing pain", site
        elif "headache" in comp_lower or "head" in comp_lower:
            return "severe cephalalgia", site
        elif "chest pain" in comp_lower or "chest" in comp_lower:
            return "acute retrosternal thoracic distress", site
        elif "burning" in comp_lower and ("stomach" in comp_lower or "abdomen" in comp_lower):
            return "burning epigastric distress / dyspepsia", site
        elif "pain" in comp_lower:
            return "localized pain and distress", site

        # Fallback to cleaned complaint
        clean = comp_lower
        for p in ["patient presents with", "complaint of", "i have", "suffering from"]:
            clean = clean.replace(p, "").strip()
        return clean or "clinical symptoms", site
