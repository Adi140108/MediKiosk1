from typing import List, Optional, Dict, Any
from app.db.repositories.base import BaseRepository
from app.schemas.timeline import TimelineEvent

class TimelineRepository(BaseRepository):
    COLLECTION = "timeline_events"

    def record_event(self, event: TimelineEvent) -> TimelineEvent:
        self.set_doc(self.COLLECTION, event.event_id, event.model_dump())
        return event

    def get_patient_timeline(self, patient_id: str) -> List[TimelineEvent]:
        all_events = self.list_docs(self.COLLECTION)
        patient_events = [e for e in all_events if e.get("patient_id") == patient_id]
        patient_events.sort(key=lambda x: x.get("timestamp", ""))
        return [TimelineEvent.model_validate(e) for e in patient_events]

    def get_session_timeline(self, session_id: str) -> List[TimelineEvent]:
        all_events = self.list_docs(self.COLLECTION)
        session_events = [e for e in all_events if e.get("session_id") == session_id]
        session_events.sort(key=lambda x: x.get("timestamp", ""))
        return [TimelineEvent.model_validate(e) for e in session_events]
