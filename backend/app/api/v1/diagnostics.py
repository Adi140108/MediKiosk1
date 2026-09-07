import logging
from fastapi import APIRouter
from app.core.telemetry import telemetry

logger = logging.getLogger("medikiosk.api.diagnostics")
router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])

@router.get("/performance")
def get_performance_diagnostics():
    """
    Returns live performance telemetry and subsystem latency metrics:
    - total_duration_ms
    - database_duration_ms
    - storage_duration_ms
    - ocr_duration_ms
    - ai_duration_ms
    - translation_duration_ms
    Never logs or returns patient PII.
    """
    return telemetry.get_summary()
