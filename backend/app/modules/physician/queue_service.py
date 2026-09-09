import logging
from datetime import datetime, timezone
from typing import List, Optional
from app.schemas.physician import (
    PriorityQueueItem, QueueStatus, DepartmentDashboardMetrics
)
from app.schemas.redflag import RedFlagSeverity
from app.schemas.routing import DepartmentId
from app.db.repositories.queue_repository import QueueRepository

logger = logging.getLogger("medikiosk.physician.queue")

class PhysicianQueueService:
    def __init__(self, queue_repo: Optional[QueueRepository] = None):
        self.repo = queue_repo or QueueRepository()

    @staticmethod
    def get_department_enum(department_str: str) -> DepartmentId:
        if not department_str:
            return DepartmentId.UNSPECIFIED
        dept_clean = department_str.lower().strip().replace(" ", "-").replace("_", "-")
        for member in DepartmentId:
            if member.value == dept_clean:
                return member
        return DepartmentId.UNSPECIFIED

    def get_department_queue(
        self,
        department: DepartmentId,
        search_query: Optional[str] = None,
        severity_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        opd_mode_filter: Optional[str] = None
    ) -> List[PriorityQueueItem]:
        sev = None
        if severity_filter:
            try:
                sev = RedFlagSeverity(severity_filter.upper())
            except Exception:
                pass
        stat = None
        if status_filter:
            try:
                stat = QueueStatus(status_filter)
            except Exception:
                pass
        return self.get_department_priority_queue(
            department_id=department,
            search_query=search_query,
            severity_filter=sev,
            status_filter=stat,
            opd_mode_filter=opd_mode_filter
        )

    def get_department_metrics(self, department_id: DepartmentId) -> DepartmentDashboardMetrics:
        """
        Computes real-time dynamic queue metrics for the selected department.
        Never returns fabricated numbers.
        """
        all_items = self.repo.list_all_queue_items()
        
        target_val = department_id.value if isinstance(department_id, DepartmentId) else str(department_id).lower().replace("_", "-")
        if target_val == "unspecified":
            dept_items = [
                it for it in all_items
                if not it.assigned_department or (it.assigned_department.value if isinstance(it.assigned_department, DepartmentId) else str(it.assigned_department).lower().replace("_", "-")) == "unspecified"
            ]
        else:
            dept_items = [
                it for it in all_items
                if (it.assigned_department.value if isinstance(it.assigned_department, DepartmentId) else str(it.assigned_department or "").lower().replace("_", "-")) == target_val
            ]

        now_utc = datetime.now(timezone.utc)
        waiting_count = 0
        critical_count = 0
        high_count = 0
        in_review_count = 0
        completed_today = 0
        total_wait_minutes = 0
        active_waiting_items = 0

        for item in dept_items:
            diff = now_utc - item.arrival_time
            item.waiting_time_minutes = max(0, int(diff.total_seconds() / 60))

            if item.status == QueueStatus.WAITING:
                waiting_count += 1
                total_wait_minutes += item.waiting_time_minutes
                active_waiting_items += 1
                if item.overall_severity == RedFlagSeverity.CRITICAL:
                    critical_count += 1
                elif item.overall_severity == RedFlagSeverity.HIGH:
                    high_count += 1

            elif item.status in (QueueStatus.IN_REVIEW, QueueStatus.PHYSICIAN_REVIEW):
                in_review_count += 1
                if item.overall_severity == RedFlagSeverity.CRITICAL:
                    critical_count += 1
                elif item.overall_severity == RedFlagSeverity.HIGH:
                    high_count += 1

            elif item.status == QueueStatus.COMPLETED:
                completed_today += 1

        avg_wait = int(total_wait_minutes / active_waiting_items) if active_waiting_items > 0 else 0

        return DepartmentDashboardMetrics(
            department_id=department_id,
            department_name=department_id.value.replace("-", " ").title(),
            waiting_count=waiting_count,
            critical_count=critical_count,
            high_count=high_count,
            in_review_count=in_review_count,
            completed_today=completed_today,
            average_wait_minutes=avg_wait
        )

    def get_department_priority_queue(
        self,
        department_id: DepartmentId,
        search_query: Optional[str] = None,
        severity_filter: Optional[RedFlagSeverity] = None,
        status_filter: Optional[QueueStatus] = None,
        opd_mode_filter: Optional[str] = None
    ) -> List[PriorityQueueItem]:
        """
        Retrieves and sorts queue items for the chosen department according to the
        Mandatory MediKiosk Priority Algorithm:
        1. Red Flag patients FIRST (Priority Group 0)
        2. Sorted by Severity Rank ASC (CRITICAL -> HIGH -> MEDIUM -> LOW)
        3. Tie-breaker by Arrival Time ASC (Oldest arrival first)
        4. Normal patients NEXT (Priority Group 1), sorted by Arrival Time ASC
        """
        if department_id == DepartmentId.UNSPECIFIED:
            raw_items = self.repo.list_all_queue_items()
            items = [
                it for it in raw_items
                if it.assigned_department == DepartmentId.UNSPECIFIED or it.assigned_department is None
            ]
        else:
            items = self.repo.get_department_queue(department_id)

        now_utc = datetime.now(timezone.utc)
        for item in items:
            diff = now_utc - item.arrival_time
            item.waiting_time_minutes = max(0, int(diff.total_seconds() / 60))

        filtered = []
        for item in items:
            if opd_mode_filter:
                item_mode = (getattr(item, "opd_mode", "GENERAL_OPD") or "GENERAL_OPD").upper()
                if "AYUSH" in opd_mode_filter.upper() and "AYUSH" not in item_mode:
                    continue
                if "GENERAL" in opd_mode_filter.upper() and "AYUSH" in item_mode:
                    continue

            if status_filter:
                if item.status != status_filter:
                    continue
            else:
                if item.status in (QueueStatus.COMPLETED, QueueStatus.CANCELLED):
                    continue

            if severity_filter and item.overall_severity != severity_filter:
                continue

            if search_query:
                q = search_query.lower()
                matches_name = q in item.patient_name.lower()
                matches_id = q in item.patient_id.lower()
                matches_complaint = item.chief_complaint_summary and q in item.chief_complaint_summary.lower()
                if not (matches_name or matches_id or matches_complaint):
                    continue

            filtered.append(item)

        # Priority Sorting: (priority_group, severity_rank, arrival_time)
        def sort_key(item: PriorityQueueItem):
            priority_group = 0 if item.is_red_flag else 1
            severity_rank = RedFlagSeverity.get_rank(item.overall_severity)
            return (priority_group, severity_rank, item.arrival_time)

        filtered.sort(key=sort_key)
        return filtered

    def update_patient_status(
        self,
        queue_id: str,
        new_status: QueueStatus,
        physician_id: Optional[str] = None
    ) -> Optional[PriorityQueueItem]:
        return self.repo.update_queue_status(queue_id, new_status, physician_id)

PriorityQueueService = PhysicianQueueService

