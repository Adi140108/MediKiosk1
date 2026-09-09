from typing import List, Optional, Dict, Any
from app.db.repositories.base import BaseRepository
from app.schemas.physician import PriorityQueueItem, QueueStatus
from app.schemas.routing import DepartmentId

class QueueRepository(BaseRepository):
    COLLECTION = "department_queues"

    def upsert_queue_item(self, item: PriorityQueueItem) -> PriorityQueueItem:
        self.set_doc(self.COLLECTION, item.queue_id, item.model_dump())
        return item

    def get_queue_item(self, queue_id: str) -> Optional[PriorityQueueItem]:
        data = self.get_doc(self.COLLECTION, queue_id)
        if data:
            return PriorityQueueItem.model_validate(data)
        return None

    def get_by_session_id(self, session_id: str) -> Optional[PriorityQueueItem]:
        items = self.list_docs(self.COLLECTION)
        for d in items:
            if d.get("session_id") == session_id:
                return PriorityQueueItem.model_validate(d)
        return None

    def get_department_queue(self, department: DepartmentId) -> List[PriorityQueueItem]:
        items = self.list_docs(self.COLLECTION)
        matching = []
        target_val = department.value if isinstance(department, DepartmentId) else str(department).lower().replace("_", "-")
        for d in items:
            try:
                item = PriorityQueueItem.model_validate(d)
                dept_val = item.assigned_department.value if isinstance(item.assigned_department, DepartmentId) else str(item.assigned_department or "").lower().replace("_", "-")
                if dept_val == target_val:
                    matching.append(item)
            except Exception:
                pass
        return matching

    def list_all_queue_items(self) -> List[PriorityQueueItem]:
        items = self.list_docs(self.COLLECTION)
        valid_items = []
        for d in items:
            try:
                valid_items.append(PriorityQueueItem.model_validate(d))
            except Exception:
                pass
        return valid_items

    def update_queue_status(self, queue_id: str, new_status: QueueStatus, physician_id: Optional[str] = None) -> Optional[PriorityQueueItem]:
        item = self.get_queue_item(queue_id)
        if not item:
            return None
        item.status = new_status
        if physician_id:
            item.assigned_physician_id = physician_id
        return self.upsert_queue_item(item)
