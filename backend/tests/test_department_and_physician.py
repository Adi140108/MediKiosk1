import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.physician import PriorityQueueItem, QueueStatus, PhysicianConfirmPayload
from app.schemas.redflag import RedFlagSeverity
from app.schemas.routing import DepartmentId, RecommendationStatus
from app.modules.physician.queue_service import PhysicianQueueService
from app.modules.physician.review_service import PhysicianReviewService
from app.modules.routing.department_config import get_all_departments, get_department_by_id
from app.db.repositories.queue_repository import QueueRepository
from app.db.repositories.intake_repository import IntakeRepository
from app.db.repositories.timeline_repository import TimelineRepository

@pytest.fixture(autouse=True)
def reset_db():
    QueueRepository.reset_in_memory_db()
    IntakeRepository.reset_in_memory_db()
    TimelineRepository.reset_in_memory_db()

# 11 & 12. Department isolation & selection
def test_department_queue_isolation():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    # Cardiology patient
    p_cardio = PriorityQueueItem(
        queue_id="q_cardio_01",
        patient_id="pat_c1",
        session_id="sess_c1",
        patient_name="Cardio Patient",
        age=50,
        gender="MALE",
        arrival_time=now,
        assigned_department=DepartmentId.CARDIOLOGY,
        recommended_department=DepartmentId.CARDIOLOGY
    )

    # Neurology patient
    p_neuro = PriorityQueueItem(
        queue_id="q_neuro_01",
        patient_id="pat_n1",
        session_id="sess_n1",
        patient_name="Neuro Patient",
        age=40,
        gender="FEMALE",
        arrival_time=now,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    queue_service.repo.upsert_queue_item(p_cardio)
    queue_service.repo.upsert_queue_item(p_neuro)

    # Fetch Neurology queue
    neuro_queue = queue_service.get_department_priority_queue(DepartmentId.NEUROLOGY)
    neuro_ids = [it.patient_id for it in neuro_queue]
    
    assert "pat_n1" in neuro_ids
    assert "pat_c1" not in neuro_ids  # Must NOT show cardiology patient

    # Fetch Cardiology queue
    cardio_queue = queue_service.get_department_priority_queue(DepartmentId.CARDIOLOGY)
    cardio_ids = [it.patient_id for it in cardio_queue]
    
    assert "pat_c1" in cardio_ids
    assert "pat_n1" not in cardio_ids

# 13 & 14. Unspecified dashboard & priority
def test_unspecified_queue_and_priority():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    # Normal unassigned patient
    p_unassigned_norm = PriorityQueueItem(
        queue_id="q_unspec_norm",
        patient_id="pat_u_norm",
        session_id="sess_u_norm",
        patient_name="Unspecified Normal",
        age=30,
        gender="MALE",
        arrival_time=now - timedelta(minutes=20),
        is_red_flag=False,
        priority_group=1,
        overall_severity=RedFlagSeverity.NONE,
        severity_rank=4,
        assigned_department=DepartmentId.UNSPECIFIED,
        recommended_department=DepartmentId.UNSPECIFIED
    )

    # Critical unassigned patient
    p_unassigned_crit = PriorityQueueItem(
        queue_id="q_unspec_crit",
        patient_id="pat_u_crit",
        session_id="sess_u_crit",
        patient_name="Unspecified Critical",
        age=65,
        gender="FEMALE",
        arrival_time=now - timedelta(minutes=5),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.CRITICAL,
        severity_rank=0,
        assigned_department=DepartmentId.UNSPECIFIED,
        recommended_department=DepartmentId.UNSPECIFIED
    )

    queue_service.repo.upsert_queue_item(p_unassigned_norm)
    queue_service.repo.upsert_queue_item(p_unassigned_crit)

    unspec_queue = queue_service.get_department_priority_queue(DepartmentId.UNSPECIFIED)
    assert len(unspec_queue) == 2
    # Critical must be first even with shorter wait
    assert unspec_queue[0].queue_id == "q_unspec_crit"
    assert unspec_queue[1].queue_id == "q_unspec_norm"

# 20 & 21. AI Summary remains draft until confirmed by physician
@pytest.mark.asyncio
async def test_ai_summary_draft_and_confirmation():
    review_svc = PhysicianReviewService()
    session_id = "sess_review_01"
    patient_id = "pat_rev_01"

    # Generate draft summary
    draft = await review_svc.generate_draft_summary(session_id, patient_id)
    assert draft.is_draft is True
    assert draft.confirmed_by is None
    assert draft.confirmed_at is None

    # Physician confirms
    payload = PhysicianConfirmPayload(
        physician_id="dr_sharma_101",
        confirmed_department=DepartmentId.NEUROLOGY,
        edited_summary="Confirmed migraine with aura. Advised rest and hydration.",
        physician_notes="Follow up in 1 week if not improved."
    )
    confirmed = review_svc.confirm_patient_review(session_id, payload)

    assert confirmed.is_draft is False
    assert confirmed.confirmed_by == "dr_sharma_101"
    assert confirmed.confirmed_at is not None
    assert "Confirmed migraine" in confirmed.hpi

# 25. Search and filtering preserves priority ordering
def test_search_and_filtering():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    p1 = PriorityQueueItem(
        queue_id="q_ortho_1",
        patient_id="pat_ortho_john",
        session_id="sess_o1",
        patient_name="John Doe",
        age=45,
        gender="MALE",
        arrival_time=now - timedelta(minutes=10),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.HIGH,
        severity_rank=1,
        assigned_department=DepartmentId.ORTHOPEDICS,
        recommended_department=DepartmentId.ORTHOPEDICS
    )

    p2 = PriorityQueueItem(
        queue_id="q_ortho_2",
        patient_id="pat_ortho_jane",
        session_id="sess_o2",
        patient_name="Jane Smith",
        age=35,
        gender="FEMALE",
        arrival_time=now - timedelta(minutes=5),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.CRITICAL,
        severity_rank=0,
        assigned_department=DepartmentId.ORTHOPEDICS,
        recommended_department=DepartmentId.ORTHOPEDICS
    )

    queue_service.repo.upsert_queue_item(p1)
    queue_service.repo.upsert_queue_item(p2)

    # Search for 'Jane'
    search_res = queue_service.get_department_priority_queue(DepartmentId.ORTHOPEDICS, search_query="Jane")
    assert len(search_res) == 1
    assert search_res[0].patient_name == "Jane Smith"

# 26. Patient status transitions work
def test_patient_status_transitions():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    item = PriorityQueueItem(
        queue_id="q_status_test",
        patient_id="pat_st",
        session_id="sess_st",
        patient_name="Status Test",
        age=28,
        gender="MALE",
        arrival_time=now,
        status=QueueStatus.WAITING,
        assigned_department=DepartmentId.DERMATOLOGY,
        recommended_department=DepartmentId.DERMATOLOGY
    )
    queue_service.repo.upsert_queue_item(item)

    # Transition to IN_REVIEW
    updated = queue_service.update_patient_status("q_status_test", QueueStatus.IN_REVIEW, physician_id="dr_derm")
    assert updated.status == QueueStatus.IN_REVIEW
    assert updated.assigned_physician_id == "dr_derm"

    # Transition to COMPLETED
    completed = queue_service.update_patient_status("q_status_test", QueueStatus.COMPLETED)
    assert completed.status == QueueStatus.COMPLETED
