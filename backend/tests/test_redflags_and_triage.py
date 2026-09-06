import os
import sys
import pytest
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.intake import PatientContextState
from app.schemas.redflag import RedFlagSeverity
from app.schemas.physician import PriorityQueueItem, QueueStatus
from app.schemas.routing import DepartmentId
from app.modules.redflags.engine import RedFlagEngine
from app.modules.physician.queue_service import PhysicianQueueService
from app.db.repositories.queue_repository import QueueRepository

@pytest.fixture(autouse=True)
def reset_db():
    QueueRepository.reset_in_memory_db()

# 5. Multiple red flags resolve to highest applicable severity
def test_multiple_red_flags_resolve_to_highest_severity():
    engine = RedFlagEngine()
    
    # Patient with both GI bleeding (HIGH) and Thunderclap headache with vomiting (CRITICAL)
    ctx = PatientContextState(
        chief_complaint="Worst headache of my life and vomiting blood",
        associated_symptoms=["vomiting", "hematemesis", "neck stiffness"],
        severity=10
    )
    result = engine.evaluate_patient_context("sess_multi_rf", ctx)

    assert result.has_red_flags is True
    assert len(result.flagged_rules) >= 2
    # Highest severity must resolve to CRITICAL
    assert result.overall_severity == RedFlagSeverity.CRITICAL
    assert result.triage_category == "EMERGENCY"

# 6, 7, 8, 9, 10, 24. Mandatory Deterministic Priority Sorting & Tie-Breakers
def test_priority_queue_sorting_and_tie_breakers():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    # 1. Normal patient (arrived 40 mins ago) - Long waiting normal case
    p_normal_old = PriorityQueueItem(
        queue_id="q_norm_old",
        patient_id="pat_01",
        session_id="sess_01",
        patient_name="Normal Old Patient",
        age=45,
        gender="MALE",
        arrival_time=now - timedelta(minutes=40),
        is_red_flag=False,
        priority_group=1,
        overall_severity=RedFlagSeverity.NONE,
        severity_rank=4,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # 2. Normal patient (arrived 10 mins ago)
    p_normal_new = PriorityQueueItem(
        queue_id="q_norm_new",
        patient_id="pat_02",
        session_id="sess_02",
        patient_name="Normal New Patient",
        age=30,
        gender="FEMALE",
        arrival_time=now - timedelta(minutes=10),
        is_red_flag=False,
        priority_group=1,
        overall_severity=RedFlagSeverity.NONE,
        severity_rank=4,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # 3. Medium red flag patient (arrived 25 mins ago)
    p_medium = PriorityQueueItem(
        queue_id="q_med",
        patient_id="pat_03",
        session_id="sess_03",
        patient_name="Medium RF Patient",
        age=50,
        gender="MALE",
        arrival_time=now - timedelta(minutes=25),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.MEDIUM,
        severity_rank=2,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # 4. High red flag patient (arrived 15 mins ago)
    p_high = PriorityQueueItem(
        queue_id="q_high",
        patient_id="pat_04",
        session_id="sess_04",
        patient_name="High RF Patient",
        age=60,
        gender="MALE",
        arrival_time=now - timedelta(minutes=15),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.HIGH,
        severity_rank=1,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # 5. Critical red flag patient 1 (arrived 5 mins ago) - Just arrived critical case
    p_critical_recent = PriorityQueueItem(
        queue_id="q_crit_recent",
        patient_id="pat_05",
        session_id="sess_05",
        patient_name="Critical Recent Patient",
        age=55,
        gender="FEMALE",
        arrival_time=now - timedelta(minutes=5),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.CRITICAL,
        severity_rank=0,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # 6. Critical red flag patient 2 (arrived 20 mins ago) - Older critical case
    p_critical_older = PriorityQueueItem(
        queue_id="q_crit_older",
        patient_id="pat_06",
        session_id="sess_06",
        patient_name="Critical Older Patient",
        age=70,
        gender="MALE",
        arrival_time=now - timedelta(minutes=20),
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.CRITICAL,
        severity_rank=0,
        assigned_department=DepartmentId.NEUROLOGY,
        recommended_department=DepartmentId.NEUROLOGY
    )

    # Save to repo in random order
    for item in [p_normal_new, p_normal_old, p_high, p_medium, p_critical_recent, p_critical_older]:
        queue_service.repo.upsert_queue_item(item)

    # Fetch sorted priority queue
    queue = queue_service.get_department_priority_queue(DepartmentId.NEUROLOGY)

    # Verify order:
    # 1. Critical Older (0 min tie-breaker)
    # 2. Critical Recent
    # 3. High
    # 4. Medium
    # 5. Normal Old (40 min waiting)
    # 6. Normal New (10 min waiting)

    expected_ids = [
        "q_crit_older",
        "q_crit_recent",
        "q_high",
        "q_med",
        "q_norm_old",
        "q_norm_new"
    ]
    actual_ids = [item.queue_id for item in queue]
    assert actual_ids == expected_ids

    # 10. Red-flag cases appear before normal cases
    # 24. Waiting time does NOT override critical priority (Critical recent (5m) > Normal old (40m))
    assert actual_ids[0] == "q_crit_older"
    assert actual_ids[1] == "q_crit_recent"
    assert actual_ids[2] == "q_high"
    assert actual_ids[3] == "q_med"
    assert actual_ids[4] == "q_norm_old"
    assert actual_ids[5] == "q_norm_new"

# 22. Multiple red flags do not create duplicate queue entries
def test_no_duplicate_queue_entries_for_multiple_red_flags():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)

    # Upsert single patient multiple times (e.g., during intake updates)
    item1 = PriorityQueueItem(
        queue_id="q_single_pat_01",
        patient_id="pat_single",
        session_id="sess_single",
        patient_name="Single Patient",
        age=40,
        gender="FEMALE",
        arrival_time=now,
        is_red_flag=True,
        priority_group=0,
        overall_severity=RedFlagSeverity.CRITICAL,
        severity_rank=0,
        assigned_department=DepartmentId.CARDIOLOGY,
        recommended_department=DepartmentId.CARDIOLOGY
    )
    queue_service.repo.upsert_queue_item(item1)
    queue_service.repo.upsert_queue_item(item1)

    cardio_queue = queue_service.get_department_priority_queue(DepartmentId.CARDIOLOGY)
    matching = [it for it in cardio_queue if it.patient_id == "pat_single"]
    assert len(matching) == 1

# 23. Waiting time is calculated correctly
def test_waiting_time_calculation():
    queue_service = PhysicianQueueService()
    now = datetime.now(timezone.utc)
    arrival = now - timedelta(minutes=35)

    item = PriorityQueueItem(
        queue_id="q_wait_test",
        patient_id="pat_wait",
        session_id="sess_wait",
        patient_name="Wait Test Patient",
        age=30,
        gender="MALE",
        arrival_time=arrival,
        assigned_department=DepartmentId.GENERAL_MEDICINE,
        recommended_department=DepartmentId.GENERAL_MEDICINE
    )
    queue_service.repo.upsert_queue_item(item)

    queue = queue_service.get_department_priority_queue(DepartmentId.GENERAL_MEDICINE)
    assert len(queue) == 1
    assert queue[0].waiting_time_minutes >= 34
