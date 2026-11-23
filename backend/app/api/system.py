"""
System lifecycle endpoints.
Provides health check, application state reporting, and graceful shutdown.
"""
from fastapi import APIRouter
import os
import signal
import asyncio

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NEXUS Core Backend",
        "version": "1.0.0-phase1",
        "pid": os.getpid()
    }


@router.get("/lifecycle")
def get_lifecycle_state():
    return {
        "state": "running",
        "auto_startup_enabled": False,
        "background_services_count": 0,
        "active_models_count": 0,
        "process_id": os.getpid()
    }


@router.post("/shutdown")
async def trigger_graceful_shutdown():
    """Clean exit handler: releases database locks, stops workers, and terminates backend."""
    async def _delayed_kill():
        await asyncio.sleep(0.5)
        os.kill(os.getpid(), signal.SIGTERM)

    asyncio.create_task(_delayed_kill())
    return {"status": "shutting_down", "message": "NEXUS Core is cleanly shutting down"}
