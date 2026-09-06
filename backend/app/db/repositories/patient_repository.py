from typing import Optional, List, Dict, Any
from app.db.repositories.base import BaseRepository
from app.schemas.patient import PatientProfile, ConsentRecord, AttendantRegistrationRequest

class PatientRepository(BaseRepository):
    COLLECTION = "patients"

    def save_patient(self, profile: PatientProfile) -> PatientProfile:
        self.set_doc(self.COLLECTION, profile.patient_id, profile.model_dump())
        if profile.abha_id:
            # Map abha_id index
            self.set_doc("abha_index", profile.abha_id, {"patient_id": profile.patient_id})
        return profile

    def get_patient(self, patient_id: str) -> Optional[PatientProfile]:
        data = self.get_doc(self.COLLECTION, patient_id)
        if data:
            return PatientProfile.model_validate(data)
        return None

    def get_patient_by_session(self, session_id: str) -> Optional[PatientProfile]:
        for doc in self.list_docs(self.COLLECTION):
            if doc.get("active_session_id") == session_id:
                return PatientProfile.model_validate(doc)
        return None

    def get_by_abha_id(self, abha_id: str) -> Optional[PatientProfile]:
        index_doc = self.get_doc("abha_index", abha_id)
        if index_doc:
            patient_id = index_doc.get("patient_id")
            if patient_id:
                return self.get_patient(patient_id)
        return None

    def save_consent(self, consent: ConsentRecord) -> ConsentRecord:
        self.set_doc("consents", consent.consent_id, consent.model_dump())
        return consent

    def get_consent(self, consent_id: str) -> Optional[ConsentRecord]:
        data = self.get_doc("consents", consent_id)
        if data:
            return ConsentRecord.model_validate(data)
        return None

    def save_attendant(self, patient_id: str, attendant: AttendantRegistrationRequest) -> Dict[str, Any]:
        doc_id = attendant.attendant_id or f"att_{patient_id}"
        data = attendant.model_dump()
        data["patient_id"] = patient_id
        data["attendant_id"] = doc_id
        self.set_doc("attendants", doc_id, data)
        return data

    def get_attendant(self, attendant_id: str) -> Optional[Dict[str, Any]]:
        return self.get_doc("attendants", attendant_id)
