from typing import Optional, List, Dict, Any
from app.db.repositories.base import BaseRepository
from app.schemas.intake import QuestionItem, AnswerItem, LiveSummaryItem, PatientContextState
from app.schemas.physician import ClinicalDraftSummary
from app.schemas.redflag import RedFlagEvaluationResult
from app.schemas.routing import RoutingRecommendation

class IntakeRepository(BaseRepository):
    def save_question(self, question: QuestionItem) -> QuestionItem:
        self.set_doc("questions", question.question_id, question.model_dump())
        return question

    def get_questions_by_session(self, session_id: str) -> List[QuestionItem]:
        all_q = self.list_docs("questions")
        session_q = [q for q in all_q if q.get("session_id") == session_id]
        seen = {}
        for q in session_q:
            qid = q.get("question_id")
            if qid:
                seen[qid] = q
            else:
                seen[str(len(seen))] = q
        deduped = list(seen.values())
        deduped.sort(key=lambda x: x.get("sequence", 0))
        return [QuestionItem.model_validate(q) for q in deduped]

    def save_answer(self, answer: AnswerItem) -> AnswerItem:
        self.set_doc("answers", answer.answer_id, answer.model_dump())
        return answer

    def get_answers_by_session(self, session_id: str) -> List[AnswerItem]:
        all_a = self.list_docs("answers")
        session_a = [a for a in all_a if a.get("session_id") == session_id]
        seen = {}
        for a in session_a:
            aid = a.get("answer_id") or a.get("question_id")
            if aid:
                seen[aid] = a
            else:
                seen[str(len(seen))] = a
        deduped = list(seen.values())
        deduped.sort(key=lambda x: x.get("sequence", 0))
        return [AnswerItem.model_validate(a) for a in deduped]

    def save_context_state(self, session_id: str, context: PatientContextState) -> PatientContextState:
        self.set_doc("intake_contexts", session_id, context.model_dump())
        return context

    def get_context_state(self, session_id: str) -> Optional[PatientContextState]:
        data = self.get_doc("intake_contexts", session_id)
        if data:
            return PatientContextState.model_validate(data)
        return None

    def save_live_summary(self, summary: LiveSummaryItem) -> LiveSummaryItem:
        self.set_doc("live_summaries", summary.summary_id, summary.model_dump())
        return summary

    def get_live_summaries(self, session_id: str) -> List[LiveSummaryItem]:
        all_s = self.list_docs("live_summaries")
        session_s = [s for s in all_s if s.get("session_id") == session_id]
        session_s.sort(key=lambda x: x.get("checkpoint_sequence", 0))
        return [LiveSummaryItem.model_validate(s) for s in session_s]

    def save_draft_summary(self, summary: ClinicalDraftSummary) -> ClinicalDraftSummary:
        self.set_doc("clinical_summaries", summary.summary_id, summary.model_dump())
        return summary

    def get_draft_summary_by_session(self, session_id: str) -> Optional[ClinicalDraftSummary]:
        all_s = self.list_docs("clinical_summaries")
        matching = [s for s in all_s if s.get("session_id") == session_id]
        if matching:
            return ClinicalDraftSummary.model_validate(matching[-1])
        return None

    def save_redflag_result(self, result: RedFlagEvaluationResult) -> RedFlagEvaluationResult:
        self.set_doc("redflag_evaluations", result.session_id, result.model_dump())
        return result

    def get_redflag_result(self, session_id: str) -> Optional[RedFlagEvaluationResult]:
        data = self.get_doc("redflag_evaluations", session_id)
        if data:
            return RedFlagEvaluationResult.model_validate(data)
        return None

    def save_routing_recommendation(self, routing: RoutingRecommendation) -> RoutingRecommendation:
        self.set_doc("routing_recommendations", routing.recommendation_id, routing.model_dump())
        return routing

    def get_routing_by_session(self, session_id: str) -> Optional[RoutingRecommendation]:
        all_r = self.list_docs("routing_recommendations")
        matching = [r for r in all_r if r.get("session_id") == session_id]
        if matching:
            return RoutingRecommendation.model_validate(matching[-1])
        return None
