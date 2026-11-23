"""
AI Provider API endpoints for Phase 1.
Operates via the MockAIProvider (zero model download, zero background GPU/CPU burn).
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.ai.mock import MockAIProvider

router = APIRouter(prefix="/api/ai", tags=["AI Provider"])
provider = MockAIProvider()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model_name: Optional[str] = None
    temperature: Optional[float] = 0.7


class LoadModelRequest(BaseModel):
    model_name: str
    is_explicit_confirmation: Optional[bool] = False


@router.get("/hardware")
async def get_hardware_info():
    """Returns detected hardware profile."""
    return await provider.detect_hardware()


@router.get("/models")
async def list_models():
    """Returns discovered/available models without loading them."""
    return await provider.list_models()


@router.post("/chat")
async def chat_inference(req: ChatRequest):
    """Executes safe simulation chat in Phase 1."""
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    return await provider.generate_response(msgs, req.model_name, req.temperature)


@router.post("/load")
async def load_model(req: LoadModelRequest):
    res = await provider.load_model(req.model_name, req.is_explicit_confirmation)
    return res


@router.post("/unload")
async def unload_model(req: LoadModelRequest):
    success = await provider.unload_model(req.model_name)
    return {"status": "unloaded" if success else "failed", "model": req.model_name}
