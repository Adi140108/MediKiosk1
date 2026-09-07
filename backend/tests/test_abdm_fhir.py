"""
Automated Test Suite for ABDM FHIR Resource Adapter
"""

import pytest
from app.modules.abdm.fhir_adapter import FhirAdapter
from app.schemas.intake import PatientContextState

def test_fhir_patient_resource():
    adapter = FhirAdapter()
    pat_data = {
        "patient_id": "pat_12345",
        "name": "Ramesh Kumar",
        "gender": "male",
        "abha_id": "ABHA-98765432"
    }
    res = adapter.create_patient_resource(pat_data)
    assert res["resourceType"] == "Patient"
    assert res["id"] == "pat_12345"
    assert res["gender"] == "male"
    assert res["name"][0]["text"] == "Ramesh Kumar"

def test_fhir_condition_resource():
    adapter = FhirAdapter()
    res = adapter.create_condition_resource("sess_abc", "pat_12345", "Acute Chest Pain")
    assert res["resourceType"] == "Condition"
    assert res["id"] == "cond_sess_abc"
    assert res["code"]["text"] == "Acute Chest Pain"
    assert res["subject"]["reference"] == "Patient/pat_12345"

def test_fhir_export_bundle():
    adapter = FhirAdapter()
    pat_data = {"patient_id": "pat_99", "name": "Sita Devi", "gender": "female"}
    ctx = PatientContextState(session_id="sess_99", chief_complaint="Stomach pain", severity=7)
    bundle = adapter.export_fhir_bundle("sess_99", pat_data, ctx)
    assert bundle.resourceType == "Bundle"
    assert len(bundle.entry) >= 3  # Patient + Condition + Pain Observation
