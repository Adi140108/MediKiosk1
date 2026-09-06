import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1 import (
    auth_router,
    patients_router,
    documents_router,
    intake_router,
    physician_router,
    speech_router,
    health_router
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-assisted, physician-in-the-loop clinical intake system with Socratic adaptive questioning and deterministic red-flag triage."
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(physician_router, prefix="/api/v1")
app.include_router(speech_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")

# Static & Frontend Routing
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    from fastapi.responses import FileResponse

    @app.get("/physician", include_in_schema=False)
    @app.get("/physician/", include_in_schema=False)
    @app.get("/physician/{full_path:path}", include_in_schema=False)
    async def serve_physician_portal(full_path: str = ""):
        physician_file = os.path.join(frontend_dir, "physician.html")
        if os.path.exists(physician_file):
            return FileResponse(physician_file)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/diagnostics", include_in_schema=False)
    @app.get("/diagnostics/", include_in_schema=False)
    async def serve_diagnostics_page():
        diag_file = os.path.join(frontend_dir, "diagnostics.html")
        if os.path.exists(diag_file):
            return FileResponse(diag_file)
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    @app.get("/", include_in_schema=False)
    async def serve_patient_kiosk():
        return FileResponse(os.path.join(frontend_dir, "index.html"))

    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
