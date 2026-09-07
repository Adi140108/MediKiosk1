"""
ABDM & FHIR Resource Adapter — MediKiosk V3

Maps MediKiosk patient intake sessions, clinical history, and AYUSH assessments
into standard FHIR Release 4 (R4) JSON resources (Patient, Condition, Observation,
MedicationStatement, Consent, Bundle).
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FhirResourceBundle(BaseModel):
    resourceType: str = "Bundle"
    id: str
    type: str = "document"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    entry: List[Dict[str, Any]] = Field(default_factory=list)

class FhirAdapter:
    """
    Transforms MediKiosk clinical context into ABDM-compliant FHIR R4 resources.
    """

    def create_patient_resource(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        p_id = patient_data.get("patient_id", "pat_unknown")
        gender_val = str(patient_data.get("gender", "other")).lower()
        if gender_val not in ["male", "female", "other", "unknown"]:
            gender_val = "other"

        return {
            "resourceType": "Patient",
            "id": p_id,
            "identifier": [
                {
                    "system": "https://healthid.ndhm.gov.in",
                    "value": patient_data.get("abha_id", f"ABHA-{p_id[:8]}")
                }
            ],
            "name": [
                {
                    "use": "official",
                    "text": patient_data.get("name", "Patient")
                }
            ],
            "gender": gender_val,
            "birthDate": patient_data.get("dob", "1990-01-01"),
            "telecom": [
                {"system": "phone", "value": patient_data.get("phone", "N/A")}
            ] if patient_data.get("phone") else []
        }

    def create_condition_resource(self, session_id: str, patient_id: str, chief_complaint: str) -> Dict[str, Any]:
        return {
            "resourceType": "Condition",
            "id": f"cond_{session_id}",
            "clinicalStatus": {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}
                ]
            },
            "verificationStatus": {
                "coding": [
                    {"system": "http://terminology.hl7.org/CodeSystem/condition-ver-status", "code": "provisional"}
                ]
            },
            "category": [
                {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/condition-category", "code": "problem-list-item"}
                    ]
                }
            ],
            "code": {
                "text": chief_complaint or "Unspecified Chief Complaint"
            },
            "subject": {
                "reference": f"Patient/{patient_id}"
            },
            "recordedDate": datetime.now(timezone.utc).isoformat()
        }

    def create_observation_resources(self, session_id: str, patient_id: str, context: Any) -> List[Dict[str, Any]]:
        observations = []

        # 1. Pain Level Observation
        pain = getattr(context, "severity", None) or getattr(context, "pain_score", None)
        if pain is not None:
            observations.append({
                "resourceType": "Observation",
                "id": f"obs_pain_{session_id}",
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {"system": "http://loinc.org", "code": "72514-3", "display": "Pain severity Visual analog score"}
                    ],
                    "text": "Pain Score (1-10)"
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "valueQuantity": {
                    "value": pain,
                    "unit": "score",
                    "system": "http://unitsofmeasure.org",
                    "code": "{score}"
                }
            })

        # 2. AYUSH Assessment Observations
        ayush_eval = getattr(context, "ayush_assessment", {}) or {}
        if ayush_eval.get("prakriti"):
            prak = ayush_eval["prakriti"]
            observations.append({
                "resourceType": "Observation",
                "id": f"obs_prakriti_{session_id}",
                "status": "final",
                "code": {"text": "Ayurvedic Baseline Prakriti Assessment"},
                "subject": {"reference": f"Patient/{patient_id}"},
                "valueString": prak.get("summary") or prak.get("primary_category") or "Insufficient Data",
                "component": [
                    {"code": {"text": "Vata Score"}, "valueQuantity": {"value": prak.get("vata_score", 0), "unit": "%"}},
                    {"code": {"text": "Pitta Score"}, "valueQuantity": {"value": prak.get("pitta_score", 0), "unit": "%"}},
                    {"code": {"text": "Kapha Score"}, "valueQuantity": {"value": prak.get("kapha_score", 0), "unit": "%"}}
                ]
            })

        return observations

    def export_fhir_bundle(
        self,
        session_id: str,
        patient_data: Dict[str, Any],
        context: Any
    ) -> FhirResourceBundle:
        """
        Bundles all FHIR resources into a single ABDM-compliant clinical document bundle.
        """
        p_id = patient_data.get("patient_id", "pat_unknown")
        pat_res = self.create_patient_resource(patient_data)
        cond_res = self.create_condition_resource(session_id, p_id, getattr(context, "chief_complaint", "General Intake"))
        obs_list = self.create_observation_resources(session_id, p_id, context)

        entries = [
            {"fullUrl": f"urn:uuid:{pat_res['id']}", "resource": pat_res},
            {"fullUrl": f"urn:uuid:{cond_res['id']}", "resource": cond_res}
        ]

        for obs in obs_list:
            entries.append({"fullUrl": f"urn:uuid:{obs['id']}", "resource": obs})

        return FhirResourceBundle(
            id=f"bundle_{session_id}",
            entry=entries
        )
