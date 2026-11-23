"""
Main FastAPI entrypoint for NEXUS.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.services.resource_mgr import ResourceManager
from app.api.system import router as system_router
from app.api.resources import router as resources_router
from app.api.discovery import router as discovery_router
from app.api.memory import router as memory_router
from app.api.projects import router as projects_router
from app.api.ai_provider import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database tables
    init_db()
    # Start low-frequency resource protection monitor
    res_mgr = ResourceManager.get_instance()
    await res_mgr.start_background_monitoring()
    yield
    # Graceful shutdown: stop monitoring loop and release locks
    await res_mgr.stop_background_monitoring()


app = FastAPI(
    title="NEXUS Local-First AI OS Core",
    version="1.0.0-phase1",
    lifespan=lifespan
)

# Enable CORS for local desktop and webview clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system_router)
app.include_router(resources_router)
app.include_router(discovery_router)
app.include_router(memory_router)
app.include_router(projects_router)
app.include_router(ai_router)


@app.get("/")
def root():
    return {
        "name": "NEXUS Core",
        "description": "Local-First Personal AI Operating System Backend",
        "status": "ready",
        "phase": 1
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8765, reload=False, log_level="info")
