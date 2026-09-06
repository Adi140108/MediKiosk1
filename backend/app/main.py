import os
import logging
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, FileResponse
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

def find_frontend_dir() -> str:
    """Discovers public or frontend directory across local development and Vercel serverless environments."""
    candidate_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "public")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "public")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend")),
        os.path.abspath(os.path.join(os.getcwd(), "public")),
        os.path.abspath(os.path.join(os.getcwd(), "frontend")),
        "/var/task/public",
        "/var/task/frontend",
        os.path.abspath("./public"),
        os.path.abspath("./frontend"),
    ]
    for p in candidate_paths:
        if os.path.exists(p) and os.path.isdir(p) and os.path.exists(os.path.join(p, "index.html")):
            return p
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

frontend_dir = find_frontend_dir()

def read_frontend_file(filename: str) -> str:
    fdir = find_frontend_dir()
    filepath = os.path.join(fdir, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
            
    # Recursive fallback across repository tree
    for search_root in [os.getcwd(), "/var/task", os.path.abspath(".")]:
        if os.path.exists(search_root):
            for root, _, files in os.walk(search_root):
                if filename in files:
                    try:
                        with open(os.path.join(root, filename), "r", encoding="utf-8") as f:
                            content = f.read()
                            if content:
                                return content
                    except Exception:
                        pass
    return ""

@app.get("/", include_in_schema=False)
async def serve_patient_kiosk():
    html = read_frontend_file("index.html")
    if html:
        return HTMLResponse(content=html, status_code=200)
    return HTMLResponse(content="<h1>MediKiosk Patient Intake System</h1><p>Initializing...</p>", status_code=200)

@app.get("/physician", include_in_schema=False)
@app.get("/physician/", include_in_schema=False)
@app.get("/physician/{full_path:path}", include_in_schema=False)
async def serve_physician_portal(full_path: str = ""):
    html = read_frontend_file("physician.html")
    if html:
        return HTMLResponse(content=html, status_code=200)
    index_html = read_frontend_file("index.html")
    return HTMLResponse(content=index_html, status_code=200)

@app.get("/diagnostics", include_in_schema=False)
@app.get("/diagnostics/", include_in_schema=False)
@app.get("/diagnostics/{full_path:path}", include_in_schema=False)
async def serve_diagnostics_page(full_path: str = ""):
    html = read_frontend_file("diagnostics.html")
    if html:
        return HTMLResponse(content=html, status_code=200)
    index_html = read_frontend_file("index.html")
    return HTMLResponse(content=index_html, status_code=200)

@app.get("/css/{file_path:path}", include_in_schema=False)
async def serve_css(file_path: str):
    fdir = find_frontend_dir()
    full_path = os.path.join(fdir, "css", file_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="text/css")
    return Response(content="/* CSS not found */", status_code=404, media_type="text/css")

@app.get("/js/{file_path:path}", include_in_schema=False)
async def serve_js(file_path: str):
    fdir = find_frontend_dir()
    full_path = os.path.join(fdir, "js", file_path)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return Response(content=f.read(), media_type="application/javascript")
    return Response(content="// JS not found", status_code=404, media_type="application/javascript")

@app.get("/assets/{file_path:path}", include_in_schema=False)
async def serve_assets(file_path: str):
    fdir = find_frontend_dir()
    full_path = os.path.join(fdir, "assets", file_path)
    if os.path.exists(full_path):
        with open(full_path, "rb") as f:
            media = "image/png" if file_path.endswith(".png") else "application/octet-stream"
            return Response(content=f.read(), media_type=media)
    return Response(status_code=404)

@app.get("/logo.png", include_in_schema=False)
@app.get("/favicon.ico", include_in_schema=False)
async def serve_logo():
    fdir = find_frontend_dir()
    for candidate in [
        os.path.join(fdir, "logo.png"),
        os.path.join(fdir, "assets", "logo.png"),
        os.path.abspath("./logo.png"),
        os.path.abspath("./public/logo.png"),
        os.path.abspath("./frontend/logo.png")
    ]:
        if os.path.exists(candidate):
            with open(candidate, "rb") as f:
                return Response(content=f.read(), media_type="image/png")
    return Response(status_code=404)

if os.path.exists(frontend_dir):
    try:
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
