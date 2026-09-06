import os
import logging
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
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
from app.templates.embedded_assets import (
    INDEX_HTML,
    PHYSICIAN_HTML,
    DIAGNOSTICS_HTML,
    STYLES_CSS,
    JS_ASSETS,
    LOGO_PNG_BYTES
)

logger = logging.getLogger("medikiosk.main")

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

# Helper to read from disk if available (for live local edits) else fallback to embedded assets
def get_html_content(filename: str, fallback_content: str) -> str:
    for base in ["frontend", "public", os.path.join(os.path.dirname(__file__), "..", "..", "frontend")]:
        p = os.path.join(base, filename)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return fallback_content

@app.get("/", include_in_schema=False)
async def serve_patient_kiosk():
    content = get_html_content("index.html", INDEX_HTML)
    return HTMLResponse(content=content, status_code=200)

@app.get("/physician", include_in_schema=False)
@app.get("/physician/", include_in_schema=False)
@app.get("/physician/{full_path:path}", include_in_schema=False)
async def serve_physician_portal(full_path: str = ""):
    content = get_html_content("physician.html", PHYSICIAN_HTML)
    return HTMLResponse(content=content, status_code=200)

@app.get("/diagnostics", include_in_schema=False)
@app.get("/diagnostics/", include_in_schema=False)
@app.get("/diagnostics/{full_path:path}", include_in_schema=False)
async def serve_diagnostics_page(full_path: str = ""):
    content = get_html_content("diagnostics.html", DIAGNOSTICS_HTML)
    return HTMLResponse(content=content, status_code=200)

@app.get("/css/{file_path:path}", include_in_schema=False)
async def serve_css(file_path: str):
    css_file = os.path.join("frontend", "css", file_path)
    if os.path.exists(css_file):
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                return Response(content=f.read(), media_type="text/css")
        except Exception:
            pass
    return Response(content=STYLES_CSS, media_type="text/css")

@app.get("/js/{file_path:path}", include_in_schema=False)
async def serve_js(file_path: str):
    js_file = os.path.join("frontend", "js", file_path)
    if os.path.exists(js_file):
        try:
            with open(js_file, "r", encoding="utf-8") as f:
                return Response(content=f.read(), media_type="application/javascript")
        except Exception:
            pass
    js_content = JS_ASSETS.get(file_path, "")
    if js_content:
        return Response(content=js_content, media_type="application/javascript")
    return Response(content="// JS not found", status_code=404, media_type="application/javascript")

@app.get("/logo.png", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_logo():
    return Response(content=LOGO_PNG_BYTES, media_type="image/png")

# Optional static directory mount for local uvicorn
for static_candidate in ["frontend", "public"]:
    if os.path.exists(static_candidate):
        try:
            app.mount("/static", StaticFiles(directory=static_candidate), name="static")
            break
        except Exception:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
