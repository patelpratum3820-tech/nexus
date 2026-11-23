"""
Resource management endpoints for NEXUS.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.resource_mgr import ResourceManager

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
        "max_cpu_percent": mgr.max_cpu_limit,
        "min_ram_gb": mgr.min_ram_limit_gb,
        "max_concurrent_tasks": mgr.max_concurrent_tasks,
        "active_workers": mgr.active_workers
    }


@router.post("/limits")
def update_limits(req: LimitUpdateRequest):
    if req.max_cpu_percent is not None:
        mgr.max_cpu_limit = req.max_cpu_percent
    if req.min_ram_gb is not None:
        mgr.min_ram_limit_gb = req.min_ram_gb
    if req.max_concurrent_tasks is not None:
        mgr.max_concurrent_tasks = req.max_concurrent_tasks
    return {"status": "updated", "limits": get_limits()}
