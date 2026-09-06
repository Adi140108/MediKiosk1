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

        # SpO2 regex: SpO2: 98%
        spo2_match = re.search(r'\b(?:SpO2|Oxygen\s*Saturation)[:\s]*([0-9]{2,3})\s*%\b', raw_text, re.IGNORECASE)
        if spo2_match:
            vitals["spo2"] = f"{spo2_match.group(1)}%"
            facts.append(ExtractedClinicalFact(
                fact="Vital: SpO2",
                value=vitals["spo2"],
                category="vital",
                source_document=filename,
                page=page,
                source_text=spo2_match.group(0),
                confidence=0.95
            ))

        # Comprehensive Laboratory Tests Directory
        lab_patterns = [
            (r'\b(?:Hemoglobin|Hb|HGB)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(g/dL|gm/dl|g/l)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Hemoglobin", "12.0 - 16.0 g/dL"),
            (r'\b(?:Total\s*Leukocyte\s*Count|TLC|WBC(?:\s*Count)?)[:\s]*([0-9,]{3,6}(?:\.[0-9]+)?)\s*(/cumm|cells/mcL|/uL|/mm3|x10\^3/uL)?(?:\s*\(?([0-9,\.\s\-–]+)\)?)?\b', "Total Leukocyte Count (WBC)", "4,000 - 11,000 /cumm"),
            (r'\b(?:Platelet\s*Count|Platelets|PLT)[:\s]*([0-9,\.]+(?:\s*(?:Lakhs?|lacs?|k))?)\s*(/cumm|cells/mcL|/uL|/mm3|x10\^3/uL)?(?:\s*\(?([0-9,\.\s\-–]+)\)?)?\b', "Platelet Count", "1.5 - 4.5 Lakhs/cumm"),
            (r'\b(?:RBC(?:\s*Count)?|Red\s*Blood\s*Cells)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mil/uL|million/cumm|x10\^6/uL)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "RBC Count", "4.5 - 5.5 mil/uL"),
            (r'\b(?:Packed\s*Cell\s*Volume|PCV|Hematocrit|HCT)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Packed Cell Volume (PCV)", "36 - 48 %"),
            (r'\b(?:Neutrophils|Polymorphs)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Neutrophils", "40 - 70 %"),
            (r'\b(?:Lymphocytes)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Lymphocytes", "20 - 40 %"),
            (r'\b(?:Eosinophils)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Eosinophils", "1 - 6 %"),
            (r'\b(?:Monocytes)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Monocytes", "2 - 8 %"),
            (r'\b(?:ESR|Erythrocyte\s*Sedimentation\s*Rate)[:\s]*([0-9]{1,3})\s*(mm/hr|mm)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "ESR", "0 - 20 mm/hr"),
            (r'\b(?:Fasting\s*Blood\s*Sugar|FBS|Fasting\s*Glucose)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Fasting Blood Sugar (FBS)", "70 - 100 mg/dL"),
            (r'\b(?:Post\s*Prandial\s*(?:Blood\s*Sugar|Glucose)|PPBS)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Post Prandial Glucose (PPBS)", "< 140 mg/dL"),
            (r'\b(?:Random\s*Blood\s*Sugar|RBS|Blood\s*Glucose)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Random Blood Sugar (RBS)", "70 - 140 mg/dL"),
            (r'\b(?:HbA1c|Glycated\s*Hemoglobin|A1C)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(%|percent)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "HbA1c", "< 5.7 % (Normal)"),
            (r'\b(?:Serum\s*Creatinine|Creatinine|S\.Creatinine)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Serum Creatinine", "0.6 - 1.2 mg/dL"),
            (r'\b(?:Blood\s*Urea|BUN|Urea)[:\s]*([0-9]{1,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Blood Urea / BUN", "15 - 40 mg/dL"),
            (r'\b(?:Serum\s*Uric\s*Acid|Uric\s*Acid)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Uric Acid", "3.5 - 7.2 mg/dL"),
            (r'\b(?:Serum\s*Sodium|Sodium|Na\+)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mEq/L|mmol/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Serum Sodium (Na+)", "135 - 145 mEq/L"),
            (r'\b(?:Serum\s*Potassium|Potassium|K\+)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mEq/L|mmol/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Serum Potassium (K+)", "3.5 - 5.0 mEq/L"),
            (r'\b(?:Total\s*Bilirubin|Bilirubin\s*Total)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Total Bilirubin", "0.2 - 1.2 mg/dL"),
            (r'\b(?:Direct\s*Bilirubin|Bilirubin\s*Direct)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Direct Bilirubin", "0.0 - 0.3 mg/dL"),
            (r'\b(?:SGOT|AST|Aspartate\s*Aminotransferase)[:\s]*([0-9]{1,3}(?:\.[0-9]+)?)\s*(U/L|IU/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "SGOT (AST)", "5 - 40 U/L"),
            (r'\b(?:SGPT|ALT|Alanine\s*Aminotransferase)[:\s]*([0-9]{1,3}(?:\.[0-9]+)?)\s*(U/L|IU/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "SGPT (ALT)", "7 - 56 U/L"),
            (r'\b(?:Alkaline\s*Phosphatase|ALP)[:\s]*([0-9]{1,4}(?:\.[0-9]+)?)\s*(U/L|IU/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Alkaline Phosphatase (ALP)", "44 - 147 U/L"),
            (r'\b(?:Total\s*Cholesterol|Cholesterol\s*Total)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Total Cholesterol", "< 200 mg/dL"),
            (r'\b(?:Serum\s*Triglycerides|Triglycerides|TGL)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "Triglycerides", "< 150 mg/dL"),
            (r'\b(?:HDL\s*Cholesterol|HDL)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "HDL Cholesterol (Good)", "> 40 mg/dL"),
            (r'\b(?:LDL\s*Cholesterol|LDL)[:\s]*([0-9]{2,3}(?:\.[0-9]+)?)\s*(mg/dL|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "LDL Cholesterol", "< 100 mg/dL"),
            (r'\b(?:TSH|Thyroid\s*Stimulating\s*Hormone)[:\s]*([0-9]{1,2}(?:\.[0-9]+)?)\s*(uIU/mL|uIU/ml|mIU/L)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "TSH", "0.4 - 4.5 uIU/mL"),
            (r'\b(?:C-Reactive\s*Protein|CRP|hs-CRP)[:\s]*([0-9]{1,3}(?:\.[0-9]+)?)\s*(mg/L|mg/dl)?(?:\s*\(?([0-9\.\s\-–]+)\)?)?\b', "C-Reactive Protein (CRP)", "< 5.0 mg/L"),
            (r'\b(?:Serum\s*Urine\s*Protein|Urine\s*Albumin)[:\s]*([A-Za-z0-9\+\-]+)\b', "Urine Albumin", "Nil / Negative"),
            (r'\b(?:Urine\s*Sugar|Urine\s*Glucose)[:\s]*([A-Za-z0-9\+\-]+)\b', "Urine Sugar", "Nil / Negative"),
            (r'\b(?:Pus\s*Cells)[:\s]*([0-9\-]+)\s*(?:/hpf|/HPF)?\b', "Urine Pus Cells", "0 - 5 /HPF")
        ]

        already_matched_tests = set()
        for test_pattern, test_name, default_ref in lab_patterns:
            m = re.search(test_pattern, raw_text, re.IGNORECASE)
            if m:
                val = m.group(1)
                unit = m.group(2) or ""
                ref_range = (m.group(3) if len(m.groups()) >= 3 and m.group(3) else default_ref)
                already_matched_tests.add(test_name)
                labs.append({
                    "test": test_name,
                    "value": val,
                    "unit": unit,
                    "reference_range": ref_range,
                    "source_text": m.group(0)
                })
                facts.append(ExtractedClinicalFact(
                    fact=f"Lab: {test_name}",
                    value=f"{val} {unit}".strip(),
                    category="lab_value",
                    source_document=filename,
                    page=page,
                    source_text=m.group(0),
                    confidence=0.92
                ))

        # Rx / Medication patterns: Tab X 500mg, Cap Y 20mg
        for rx_match in re.finditer(r'\b(?:Tab|Tablet|Cap|Capsule|Syp|Syrup|Injection|Inj)\.?\s+([A-Za-z0-9\-]+)\s+([0-9]+(?:\.[0-9]+)?\s*(?:mg|mcg|ml|g)?)\s*(OD|BD|TDS|QID|SOS|HS|once\s*daily|twice\s*daily)?\b', raw_text, re.IGNORECASE):
            drug_name = rx_match.group(1)
            dosage = rx_match.group(2) or ""
            freq = rx_match.group(3) or ""
            meds.append({"name": drug_name, "dosage": dosage, "frequency": freq})
            facts.append(ExtractedClinicalFact(
                fact=f"Medication: {drug_name}",
                value=f"{dosage} {freq}".strip() or "Prescribed",
                category="medication",
                source_document=filename,
                page=page,
                source_text=rx_match.group(0),
                confidence=0.90
            ))

        # Diagnoses & Conditions: Diagnosis: X, Impression: Y
        diag_patterns = [
            r'\b(?:Diagnosis|Impression|Assessment|Clinical\s*Condition)[:\s]+([^\n\r\.\;]{3,80})',
            r'\b(?:Known\s*case\s*of|History\s*of|H/O)[:\s]+([^\n\r\.\;]{3,80})'
        ]
        for dp in diag_patterns:
            for dm in re.finditer(dp, raw_text, re.IGNORECASE):
                cond_text = dm.group(1).strip()
                if cond_text and len(cond_text) > 3 and cond_text not in conditions:
                    conditions.append(cond_text)
                    facts.append(ExtractedClinicalFact(
                        fact="Diagnosis / Impression",
                        value=cond_text,
                        category="condition",
                        source_document=filename,
                        page=page,
                        source_text=dm.group(0),
                        confidence=0.90
                    ))

        return StructuredMedicalDocument(
            document_type="Medical Prescription / Clinical Lab Report",
            raw_text=raw_text,
            overall_confidence=round(confidence, 2),
            facts=facts,
            conditions=conditions,
            medications=meds,
            allergies=[],
            vitals=vitals,
            lab_values=labs
        )
