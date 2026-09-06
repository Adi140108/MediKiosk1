from app.modules.routing.department_config import (
    DEPARTMENTS_REGISTRY, get_all_departments, get_department_by_id
)
from app.modules.routing.symptom_analyzer import analyze_symptoms_for_department
from app.modules.routing.service import RoutingService

__all__ = [
    "DEPARTMENTS_REGISTRY",
    "get_all_departments",
    "get_department_by_id",
    "analyze_symptoms_for_department",
    "RoutingService"
]
