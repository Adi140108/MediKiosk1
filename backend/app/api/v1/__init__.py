from app.api.v1.auth import router as auth_router
from app.api.v1.patients import router as patients_router
from app.api.v1.documents import router as documents_router
from app.api.v1.intake import router as intake_router
from app.api.v1.physician import router as physician_router
from app.api.v1.speech import router as speech_router
from app.api.v1.health import router as health_router
from app.api.v1.diagnostics import router as diagnostics_router

__all__ = [
    "auth_router",
    "patients_router",
    "documents_router",
    "intake_router",
    "physician_router",
    "speech_router",
    "health_router",
    "diagnostics_router"
]
