import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.config import settings
from backend.app.db.database import init_db
from backend.app.api.routes_persona import router as persona_router
from backend.app.api.routes_session import router as session_router
from backend.app.api.routes_auth import router as auth_router
from backend.app.api.routes_dashboard import router as dashboard_router

# Initialize database schema
init_db()

app = FastAPI(
    title=settings.app_name,
    description="Adversarial Voice AI Sales & Negotiation Simulator with Emotion Engine and Moment-by-Moment Leverage Replay.",
    version="1.0.0"
)

# CORS setup for web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(persona_router)
app.include_router(session_router)

# Mount Static Files
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
def serve_index():
    no_cache = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache", "Expires": "0"}
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file, headers=no_cache)
    root_index = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "index.html")
    if os.path.exists(root_index):
        return FileResponse(root_index, headers=no_cache)
    return {"message": "VerbalPause API is running. Open /docs for Swagger UI."}


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "VerbalPause Voice Engine",
        "groq_configured": bool(settings.groq_api_key),
        "tavily_configured": bool(settings.tavily_api_key)
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=port, reload=False)
