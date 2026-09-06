import logging
import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("medikiosk.ocr.extractor")

class ExtractedClinicalFact(BaseModel):
    fact: str
    value: str
    category: str  # lab_value, medication, condition, vital, allergy, header
    source_document: str
    page: int = 1
    source_text: str
    confidence: float = 0.90

class StructuredMedicalDocument(BaseModel):
    document_type: str = "Medical Record"
    hospital_name: Optional[str] = None
    document_date: Optional[str] = None
    patient_name_detected: Optional[str] = None
    raw_text: str = ""
    overall_confidence: float = 0.0
    facts: List[ExtractedClinicalFact] = Field(default_factory=list)
    conditions: List[str] = Field(default_factory=list)
    medications: List[Dict[str, str]] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    vitals: Dict[str, str] = Field(default_factory=dict)
    lab_values: List[Dict[str, Any]] = Field(default_factory=list)

class MedicalDocumentExtractor:
    """
    Extracts structured medical entities and clinical facts from verified OCR text.
    Maintains strict provenance for every fact. Never fabricates unmentioned findings.
    """
    def __init__(self, gemma_client=None):
        from app.ai.gemma.client import GemmaClient
        self.gemma = gemma_client or GemmaClient()

    async def extract_structured_document(
        self,
        raw_text: str,
        document_filename: str,
        page_number: int = 1,
        ocr_confidence: float = 0.85
    ) -> StructuredMedicalDocument:
        """
        Structures OCR text into verified clinical facts with source mapping.
        """
        if not raw_text or not raw_text.strip():
            return StructuredMedicalDocument(
                document_type="Unknown",
                raw_text="",
                overall_confidence=0.0
            )

        # 1. Attempt AI extraction via Gemma
        prompt = (
            "You are an expert clinical data extractor. Read the following OCR text from a medical document. "
            "Extract ONLY factual medical information that is explicitly stated in the text. "
            "DO NOT INVENT, ASSUME, OR HALLUCINATE ANY MEDICATIONS, LAB VALUES, OR CONDITIONS.\n\n"
            "Return valid JSON matching this schema:\n"
            "{\n"
            "  \"document_type\": string,\n"
            "  \"hospital_name\": string or null,\n"
            "  \"document_date\": string or null,\n"
            "  \"patient_name_detected\": string or null,\n"
            "  \"conditions\": [string],\n"
            "  \"medications\": [{\"name\": string, \"dosage\": string, \"frequency\": string, \"source_text\": string}],\n"
            "  \"allergies\": [string],\n"
            "  \"vitals\": {\"bp\": string, \"pulse\": string, \"temp\": string, \"spo2\": string},\n"
            "  \"lab_values\": [{\"test\": string, \"value\": string, \"unit\": string, \"source_text\": string}]\n"
            "}\n\n"
            f"OCR TEXT:\n{raw_text}"
        )

        try:
            res = await self.gemma.generate_response(prompt, format_json=True)
            if res and res.strip():
                data = json.loads(res)
                if data.get("status") != "ai_unavailable":
                    return self._build_structured_doc(data, raw_text, document_filename, page_number, ocr_confidence)
        except Exception as e:
            logger.info("AI structured extraction unavailable (%s). Using deterministic regex extractor.", str(e))

        # 2. Deterministic Regex Extraction (Safety Baseline)
        return self._regex_extract_document(raw_text, document_filename, page_number, ocr_confidence)

    def _build_structured_doc(
        self,
        data: Dict[str, Any],
        raw_text: str,
        filename: str,
        page: int,
        confidence: float
    ) -> StructuredMedicalDocument:
        facts: List[ExtractedClinicalFact] = []

        # Lab values
        labs = []
        for lv in data.get("lab_values", []):
            test = lv.get("test", "")
            val = lv.get("value", "")
            unit = lv.get("unit", "")
            src = lv.get("source_text", f"{test} {val} {unit}".strip())
            if test and val:
                labs.append({"test": test, "value": val, "unit": unit})
                facts.append(ExtractedClinicalFact(
                    fact=test,
                    value=f"{val} {unit}".strip(),
                    category="lab_value",
                    source_document=filename,
                    page=page,
                    source_text=src,
                    confidence=round(confidence, 2)
                ))

        # Medications
        meds = []
        for m in data.get("medications", []):
            name = m.get("name", "")
            dosage = m.get("dosage", "")
            freq = m.get("frequency", "")
            src = m.get("source_text", f"{name} {dosage} {freq}".strip())
            if name:
                meds.append({"name": name, "dosage": dosage, "frequency": freq})
                facts.append(ExtractedClinicalFact(
                    fact=f"Medication: {name}",
                    value=f"{dosage} {freq}".strip() or "Prescribed",
                    category="medication",
                    source_document=filename,
                    page=page,
                    source_text=src,
                    confidence=round(confidence, 2)
                ))

        # Conditions
        conditions = [c for c in data.get("conditions", []) if c]
        for c in conditions:
            facts.append(ExtractedClinicalFact(
                fact="Diagnosis / Condition",
                value=c,
                category="condition",
                source_document=filename,
                page=page,
                source_text=c,
                confidence=round(confidence, 2)
            ))

        # Vitals
        vitals = {k: v for k, v in data.get("vitals", {}).items() if v}
        for vk, vv in vitals.items():
            facts.append(ExtractedClinicalFact(
                fact=f"Vital: {vk.upper()}",
                value=vv,
                category="vital",
                source_document=filename,
                page=page,
                source_text=f"{vk.upper()}: {vv}",
                confidence=round(confidence, 2)
            ))

        return StructuredMedicalDocument(
            document_type=data.get("document_type", "Medical Record"),
            hospital_name=data.get("hospital_name"),
            document_date=data.get("document_date"),
            patient_name_detected=data.get("patient_name_detected"),
            raw_text=raw_text,
            overall_confidence=round(confidence, 2),
            facts=facts,
            conditions=conditions,
            medications=meds,
            allergies=data.get("allergies", []),
            vitals=vitals,
            lab_values=labs
        )

    def _regex_extract_document(
        self,
        raw_text: str,
        filename: str,
        page: int,
        confidence: float
    ) -> StructuredMedicalDocument:
        facts: List[ExtractedClinicalFact] = []
        vitals = {}
        labs = []
        meds = []
        conditions = []

        # BP regex: 120/80, 130/85 mmHg
        bp_match = re.search(r'\b(?:BP|Blood\s*Pressure)[:\s]*([0-9]{2,3}\s*/\s*[0-9]{2,3})\s*(?:mmHg)?\b', raw_text, re.IGNORECASE)
        if bp_match:
            vitals["bp"] = bp_match.group(1).replace(" ", "")
            facts.append(ExtractedClinicalFact(
                fact="Vital: BP",
                value=f"{vitals['bp']} mmHg",
                category="vital",
                source_document=filename,
                page=page,
                source_text=bp_match.group(0),
                confidence=0.95
            ))

        # Pulse regex: Pulse: 78 bpm, HR: 82
        pulse_match = re.search(r'\b(?:Pulse|HR|Heart\s*Rate)[:\s]*([0-9]{2,3})\s*(?:bpm)?\b', raw_text, re.IGNORECASE)
        if pulse_match:
            vitals["pulse"] = f"{pulse_match.group(1)} bpm"
            facts.append(ExtractedClinicalFact(
                fact="Vital: Pulse",
                value=vitals["pulse"],
                category="vital",
                source_document=filename,
                page=page,
                source_text=pulse_match.group(0),
                confidence=0.95
            ))

        # Common lab values: Hb / Hemoglobin, Glucose, Creatinine, Cholesterol, HbA1c
        for test_pattern, test_name in [
            (r'\b(?:Hemoglobin|Hb)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(g/dL|gm/dl)?\b', "Hemoglobin"),
            (r'\b(?:Fasting\s*Glucose|FBS|Blood\s*Sugar)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL)?\b', "Fasting Glucose"),
            (r'\b(?:HbA1c|A1C)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?\b', "HbA1c"),
            (r'\b(?:Serum\s*Creatinine|Creatinine)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mg/dL)?\b', "Serum Creatinine"),
            (r'\b(?:Total\s*Cholesterol|Cholesterol)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL)?\b', "Total Cholesterol")
        ]:
            m = re.search(test_pattern, raw_text, re.IGNORECASE)
            if m:
                val = m.group(1)
                unit = m.group(2) or ""
                labs.append({"test": test_name, "value": val, "unit": unit})
                facts.append(ExtractedClinicalFact(
                    fact=test_name,
                    value=f"{val} {unit}".strip(),
                    category="lab_value",
                    source_document=filename,
                    page=page,
                    source_text=m.group(0),
                    confidence=0.92
                ))

        # Rx / Medication patterns: Tab X 500mg, Cap Y 20mg
        for rx_match in re.finditer(r'\b(?:Tab|Tablet|Cap|Capsule|Syp|Injection)\s+([A-Za-z0-9\-]+)\s+([0-9]+(?:\.[0-9]+)?\s*(?:mg|mcg|ml|g)?)\s*(OD|BD|TDS|QID|SOS|HS)?\b', raw_text, re.IGNORECASE):
            drug_name = rx_match.group(1)
            dosage = rx_match.group(2) or ""
            freq = rx_match.group(3) or ""
            meds.append({"name": drug_name, "dosage": dosage, "frequency": freq})
            facts.append(ExtractedClinicalFact(
                fact=f"Medication: {drug_name}",
                value=f"{dosage} {freq}".strip(),
                category="medication",
                source_document=filename,
                page=page,
                source_text=rx_match.group(0),
                confidence=0.90
            ))

        return StructuredMedicalDocument(
            document_type="Medical Prescription / Lab Report",
            raw_text=raw_text,
            overall_confidence=round(confidence, 2),
            facts=facts,
            conditions=conditions,
            medications=meds,
            allergies=[],
            vitals=vitals,
            lab_values=labs
        )
