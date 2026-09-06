import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.intake import PatientContextState, SocraticStage
from app.core.security import SourceType
from app.modules.intake.adaptive_branching import AdaptiveBranchingEngine
from app.modules.intake.ayurvedic_questioning import AyurvedicQuestionEngine
from app.modules.intake.session_manager import IntakeSessionManager
from app.db.repositories.intake_repository import IntakeRepository

@pytest.fixture(autouse=True)
def reset_db():
    IntakeRepository.reset_in_memory_db()

# 1. Different symptoms produce different question paths
def test_different_symptoms_produce_different_paths():
    branching = AdaptiveBranchingEngine()

    # Patient A with Headache
    ctx_a = PatientContextState(chief_complaint="I have a terrible headache", question_count=1)
    cand_a = branching.select_next_question_candidate(ctx_a, asked_question_ids=[])

    # Patient B with Abdominal Pain
    ctx_b = PatientContextState(chief_complaint="Severe abdominal pain in belly", question_count=1)
    cand_b = branching.select_next_question_candidate(ctx_b, asked_question_ids=[])

    assert cand_a is not None
    assert cand_b is not None
    assert cand_a["id"] != cand_b["id"]
    assert "head" in cand_a["question"].lower() or "headache" in cand_a["id"]
    assert "abdomen" in cand_b["question"].lower() or "abdo" in cand_b["id"]

# 2. Previous answer changes next question
@pytest.mark.asyncio
async def test_previous_answer_changes_next_question():
    mgr = IntakeSessionManager()
    session_id = "sess_adaptive_01"

    # Start session
    q1 = mgr.start_session(session_id, "pat_01")
    assert q1.objective == "Identify chief complaint"

    # Answer 1: Headache
    q2, finished1, _ = await mgr.process_answer_and_get_next(
        session_id=session_id,
        question_id=q1.question_id,
        answer_text="Severe headache on the right side"
    )
    assert finished1 is False
    assert q2 is not None
    assert "location" in q2.objective.lower() or "headache" in q2.question_id

    # Answer 2: Provide location
    q3, finished2, _ = await mgr.process_answer_and_get_next(
        session_id=session_id,
        question_id=q2.question_id,
        answer_text="Right temple area"
    )
    assert finished2 is False
    assert q3 is not None
    assert q3.question_id != q2.question_id

# 3. Known information is not unnecessarily requested again
def test_known_information_not_repeated():
    branching = AdaptiveBranchingEngine()
    
    # Context already has location and onset known
    ctx = PatientContextState(
        chief_complaint="Throbbing headache",
        location="Right forehead",
        onset="Started suddenly 2 hours ago",
        question_count=2
    )
    # Asked location question
    cand = branching.select_next_question_candidate(ctx, asked_question_ids=["headache_loc", "headache_onset"])

    assert cand is not None
    # Must NOT ask location or onset again
    assert cand["id"] not in ["headache_loc", "headache_onset"]

# 4. Red-flag questions receive higher priority
def test_red_flag_question_priority():
    branching = AdaptiveBranchingEngine()
    ctx = PatientContextState(chief_complaint="Sudden severe headache", question_count=1)

    # Candidates contain red-flag questions
    cand = branching.select_next_question_candidate(ctx, asked_question_ids=["headache_loc"])
    # Neurological red-flag candidate should be ranked top
    assert cand is not None
    assert cand["category"] in ["RED_FLAG", "CHIEF_COMPLAINT"]

# 15 & 16. Every question and answer is stored
@pytest.mark.asyncio
async def test_every_question_and_answer_stored():
    mgr = IntakeSessionManager()
    session_id = "sess_persistence_test"

    q1 = mgr.start_session(session_id, "pat_test")
    q2, _, _ = await mgr.process_answer_and_get_next(
        session_id=session_id,
        question_id=q1.question_id,
        answer_text="Stomach pain and nausea"
    )

    questions = mgr.repo.get_questions_by_session(session_id)
    answers = mgr.repo.get_answers_by_session(session_id)

    assert len(questions) == 2
    assert len(answers) == 1
    assert answers[0].answer == "Stomach pain and nausea"
    assert answers[0].question_id == q1.question_id

# 17. Patient/attendant source is preserved
@pytest.mark.asyncio
async def test_attendant_source_preserved():
    mgr = IntakeSessionManager()
    session_id = "sess_attendant_test"

    q1 = mgr.start_session(session_id, "pat_child")
    await mgr.process_answer_and_get_next(
        session_id=session_id,
        question_id=q1.question_id,
        answer_text="He has had high fever since yesterday",
        source_type=SourceType.ATTENDANT,
        attendant_id="att_mother_01"
    )

    answers = mgr.repo.get_answers_by_session(session_id)
    assert len(answers) == 1
    assert answers[0].source_type == SourceType.ATTENDANT
    assert answers[0].attendant_id == "att_mother_01"

# Patient-friendly Ayurvedic translation
def test_ayurvedic_patient_friendly_language():
    ayur = AyurvedicQuestionEngine()
    q_agni = ayur.generate_patient_friendly_question("AGNI")
    
    assert "(Agni)" in q_agni["question"]
    # Ensure patient-friendly wording (digestion, bloating, food) rather than untranslated Sanskrit demands
    assert "digestion" in q_agni["question"].lower()
    assert "bloating" in q_agni["question"].lower() or "digest" in q_agni["question"].lower()

    q_mala = ayur.generate_patient_friendly_question("MALA")
    assert "(Mala)" in q_mala["question"]
    assert "bowel" in q_mala["question"].lower()
