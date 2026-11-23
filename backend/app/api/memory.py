"""
Memory management endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.services.memory import MemoryService

router = APIRouter(prefix="/api/memory", tags=["Memory"])
service = MemoryService()


class MemoryCreateRequest(BaseModel):
    category: str
    key: str
    content: str
    project_id: Optional[str] = None
    source: str = "user"
    confidence: float = 1.0


class MemoryUpdateRequest(BaseModel):
    content: str
    confidence: float = 1.0


@router.get("/list")
def list_memories(
    category: Optional[str] = None,
    project_id: Optional[str] = None,
    query: Optional[str] = None
):
    return service.list_memories(category=category, project_id=project_id, query=query)


@router.post("/add")
def add_memory(req: MemoryCreateRequest):
    try:
        return service.add_memory(
            category=req.category,
            key=req.key,
            content=req.content,
            project_id=req.project_id,
            source=req.source,
            confidence=req.confidence
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{memory_id}")
def update_memory(memory_id: str, req: MemoryUpdateRequest):
    success = service.update_memory(memory_id, req.content, req.confidence)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found or inactive")
    return {"status": "updated", "id": memory_id}


@router.delete("/{memory_id}")
def delete_memory(memory_id: str):
    success = service.delete_memory(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"status": "deleted", "id": memory_id}
