import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.patient import (
    PatientProfile, PatientRegistrationRequest, AttendantRegistrationRequest, ConsentRecord, IdentityType
)
from app.schemas.timeline import TimelineEvent, TimelineEventType
from app.core.security import SourceType, UserRole, log_audit_event
from app.db.repositories.patient_repository import PatientRepository
from app.db.repositories.timeline_repository import TimelineRepository

router = APIRouter(prefix="/patients", tags=["patients"])
patient_repo = PatientRepository()
timeline_repo = TimelineRepository()

@router.post("/register", response_model=PatientProfile)
def register_patient(req: PatientRegistrationRequest):
    patient_id = req.abha_id or f"pat_{uuid.uuid4().hex[:8]}"
    is_temp = req.identity_type == IdentityType.TEMP_DEV

    profile = PatientProfile(
        patient_id=patient_id,
        abha_id=req.abha_id,
        name=req.name,
        age=req.age,
        gender=req.gender,
        phone=req.phone,
        preferred_language=req.preferred_language,
        is_temporary_identity=is_temp
    )
    patient_repo.save_patient(profile)

    # Log timeline & audit
    event = TimelineEvent(
        event_id=f"evt_reg_{patient_id}",
        patient_id=patient_id,
        session_id=f"sess_{patient_id}",
        event_type=TimelineEventType.REGISTRATION,
        title="Patient Registered",
        description=f"Patient {req.name} registered (Identity: {req.identity_type.value}).",
        source_type=SourceType.PATIENT
    )
    timeline_repo.record_event(event)

    log_audit_event(
        event_type="PATIENT_REGISTERED",
        user_id=patient_id,
        role=UserRole.PATIENT,
        details={"name": req.name, "identity_type": req.identity_type.value}
    )
    return profile

@router.post("/{patient_id}/attendant")
def add_attendant(patient_id: str, req: AttendantRegistrationRequest):
    patient = patient_repo.get_patient(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    att_data = patient_repo.save_attendant(patient_id, req)
    
    log_audit_event(
        event_type="ATTENDANT_ADDED",
        user_id=patient_id,
        role=UserRole.ATTENDANT,
        details={"attendant_name": req.name, "relationship": req.relationship_to_patient}
    )
    return {"status": "success", "attendant": att_data}

@router.post("/{patient_id}/consent")
def submit_consent(patient_id: str, session_id: str, is_attendant: bool = False, attendant_id: str = None):
    consent = ConsentRecord(
        consent_id=f"con_{uuid.uuid4().hex[:8]}",
        patient_id=patient_id,
        session_id=session_id,
        given_by=SourceType.ATTENDANT if is_attendant else SourceType.PATIENT,
        attendant_id=attendant_id,
        data_processing_agreed=True,
        ai_assistance_agreed=True,
        teleconsult_agreed=True
    )
    patient_repo.save_consent(consent)

    event = TimelineEvent(
        event_id=f"evt_con_{session_id}",
        patient_id=patient_id,
        session_id=session_id,
        event_type=TimelineEventType.CONSENT_CAPTURED,
        title="Clinical & Data Consent Captured",
        description=f"Informed consent provided by {consent.given_by.value}.",
        source_type=consent.given_by
    )
    timeline_repo.record_event(event)
    return {"status": "success", "consent": consent.model_dump()}
