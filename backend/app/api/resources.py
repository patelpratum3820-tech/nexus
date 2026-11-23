"""
Resource management endpoints for NEXUS.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.resource_mgr import ResourceManager
from app.core.config import HARD_MAX_CPU_PERCENT, HARD_MIN_AVAILABLE_RAM_GB

router = APIRouter(prefix="/api/resources", tags=["Resources"])
mgr = ResourceManager.get_instance()


class LimitUpdateRequest(BaseModel):
    max_cpu_percent: Optional[float] = None
    min_ram_gb: Optional[float] = None
    max_concurrent_tasks: Optional[int] = None


@router.get("/metrics")
def get_metrics():
    """Retrieve instantaneous or cached system metrics."""
    return mgr.sample_metrics()


@router.get("/limits")
def get_limits():
    return {
        "max_cpu_percent": mgr.effective_max_cpu,
        "min_ram_gb": mgr.effective_min_ram,
        "max_concurrent_tasks": mgr.max_concurrent_tasks,
        "active_workers": mgr.active_workers,
        "hard_boundaries": {
            "max_cpu_percent": HARD_MAX_CPU_PERCENT,
            "min_ram_gb": HARD_MIN_AVAILABLE_RAM_GB
        }
    }


@router.post("/limits")
def update_limits(req: LimitUpdateRequest):
    try:
        updated = mgr.update_and_persist_limits(
            max_cpu_percent=req.max_cpu_percent,
            min_ram_gb=req.min_ram_gb,
            max_concurrent_tasks=req.max_concurrent_tasks
        )
        return {"status": "updated", "limits": updated}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
