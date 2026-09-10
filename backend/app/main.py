import sys
import os

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import base64
import logging
from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.telemetry import telemetry
from app.api.v1 import (
    auth_router,
    patients_router,
    documents_router,
    intake_router,
    physician_router,
    speech_router,
    health_router,
    diagnostics_router,
    ayurveda_router
)
from app.templates.embedded_assets import (
    INDEX_HTML,
    PHYSICIAN_HTML,
    DIAGNOSTICS_HTML,
    STYLES_CSS,
    LOGO_SVG,
    LOGO_PNG_B64,
    JS_ASSETS
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

# Performance Telemetry & Latency Instrumentation Middleware
@app.middleware("http")
async def performance_telemetry_middleware(request: Request, call_next):
    endpoint = request.url.path
    method = request.method
    telemetry.start_request(endpoint=endpoint, method=method)
    
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        trace = telemetry.end_request(status_code=status_code)
        if trace and 'response' in locals():
            response.headers["X-Response-Time-Ms"] = str(trace["total_duration_ms"])
            if trace["database_duration_ms"] > 0:
                response.headers["X-DB-Time-Ms"] = str(trace["database_duration_ms"])
            if trace["storage_duration_ms"] > 0:
                response.headers["X-Storage-Time-Ms"] = str(trace["storage_duration_ms"])
            if trace["ocr_duration_ms"] > 0:
                response.headers["X-OCR-Time-Ms"] = str(trace["ocr_duration_ms"])
            if trace["ai_duration_ms"] > 0:
                response.headers["X-AI-Time-Ms"] = str(trace["ai_duration_ms"])

# Include API Routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(intake_router, prefix="/api/v1")
app.include_router(physician_router, prefix="/api/v1")
app.include_router(speech_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(diagnostics_router, prefix="/api/v1")
app.include_router(ayurveda_router, prefix="/api/v1")

# Path resolution helpers for local development and deployed builds
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(REPO_ROOT, "frontend")
PUBLIC_DIR = os.path.join(REPO_ROOT, "public")

def get_html_content(filename: str, fallback_content: str) -> str:
    for base in [FRONTEND_DIR, PUBLIC_DIR, "frontend", "public"]:
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
    for base in [FRONTEND_DIR, PUBLIC_DIR, "frontend", "public"]:
        css_file = os.path.join(base, "css", file_path)
        if os.path.exists(css_file):
            try:
                with open(css_file, "r", encoding="utf-8") as f:
                    return Response(content=f.read(), media_type="text/css")
            except Exception:
                pass
    return Response(content=STYLES_CSS, media_type="text/css")

@app.get("/js/{file_path:path}", include_in_schema=False)
async def serve_js(file_path: str):
    for base in [FRONTEND_DIR, PUBLIC_DIR, "frontend", "public"]:
        js_file = os.path.join(base, "js", file_path)
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
async def serve_logo_png():
    for base in [FRONTEND_DIR, PUBLIC_DIR, REPO_ROOT, "frontend", "public", ""]:
        png_candidate = os.path.join(base, "logo.png")
        if os.path.exists(png_candidate):
            try:
                with open(png_candidate, "rb") as f:
                    return Response(content=f.read(), media_type="image/png")
            except Exception:
                pass
    if LOGO_PNG_B64:
        try:
            return Response(content=base64.b64decode(LOGO_PNG_B64), media_type="image/png")
        except Exception:
            pass
    return Response(content=b"", status_code=404)

@app.get("/logo.svg", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_logo_svg():
    for base in [FRONTEND_DIR, PUBLIC_DIR, REPO_ROOT, "frontend", "public", ""]:
        svg_candidate = os.path.join(base, "logo.svg")
        if os.path.exists(svg_candidate):
            try:
                with open(svg_candidate, "r", encoding="utf-8") as f:
                    return Response(content=f.read(), media_type="image/svg+xml")
            except Exception:
                pass
    return Response(content=LOGO_SVG, media_type="image/svg+xml")

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
