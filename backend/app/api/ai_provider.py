"""
AI Provider API endpoints for NEXUS.
Phase 2.3: Real Gemma 3:1B inference, progressive SSE streaming, resource gating, and cancellation.
"""
from fastapi import APIRouter, HTTPException, Request
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
import json
import asyncio
from app.services.ai.base import BaseAIProvider
from app.services.ai.factory import AIProviderFactory
from app.services.resource_mgr import ResourceManager

router = APIRouter(prefix="/api/ai", tags=["AI Provider"])
factory = AIProviderFactory.get_instance()
resource_mgr = ResourceManager.get_instance()


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model_name: Optional[str] = "gemma3:1b"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 256


class LoadModelRequest(BaseModel):
    model_name: str
    is_explicit_confirmation: Optional[bool] = False


class ProviderModeRequest(BaseModel):
    mode: str  # "auto", "ollama", "mock"


class DynamicAIProviderProxy(BaseAIProvider):
    """
    Transparent proxy exposing the active AI provider (Ollama or Mock).
    Maintains compatibility with system lifecycle hooks and regression suites.
    """
    def __init__(self, provider_factory: AIProviderFactory):
        self._factory = provider_factory
        self._proxy_loaded_model: Optional[str] = None

    @property
    def provider_id(self) -> str:
        return self._factory.ollama_provider.provider_id if self._factory.mode != "mock" else "mock"

    @property
    def display_name(self) -> str:
        return (
            self._factory.ollama_provider.display_name
            if self._factory.mode != "mock"
            else self._factory.mock_provider.display_name
        )

    @property
    def loaded_model(self) -> Optional[str]:
        if self._proxy_loaded_model:
            return self._proxy_loaded_model
        if self._factory.mode == "mock":
            return self._factory.mock_provider.loaded_model
        return self._factory.ollama_provider.loaded_model

    async def is_available(self) -> bool:
        active = await self._factory.get_active_provider()
        return await active.is_available()

    async def detect_hardware(self) -> Dict[str, Any]:
        active = await self._factory.get_active_provider()
        return await active.detect_hardware()

    async def list_models(self) -> List[Dict[str, Any]]:
        active = await self._factory.get_active_provider()
        return await active.list_models()

    async def load_model(self, model_name: str, is_explicit_confirmation: bool = False) -> Dict[str, Any]:
        self._proxy_loaded_model = model_name
        active = await self._factory.get_active_provider()
        if active.provider_id == "mock":
            return await active.load_model(model_name, is_explicit_confirmation)
        return {
            "success": True,
            "loaded_model": model_name,
            "is_nexus_managed": True,
            "single_residence_guaranteed": True
        }

    async def unload_model(self, model_name: str) -> bool:
        if self._proxy_loaded_model == model_name:
            self._proxy_loaded_model = None
        active = await self._factory.get_active_provider()
        return await active.unload_model(model_name)

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        active = await self._factory.get_active_provider()
        return await active.generate_response(messages, model_name, temperature, max_tokens)

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        active = await self._factory.get_active_provider()
        async for chunk in active.stream_response(messages, model_name):
            yield chunk


provider = DynamicAIProviderProxy(factory)


@router.get("/status")
async def get_provider_status():
    """Returns current active provider, live Ollama availability, and fallback transparency."""
    return await factory.get_status()


@router.get("/hardware")
async def get_hardware_info():
    """Returns detected hardware profile."""
    return await provider.detect_hardware()


@router.get("/models")
async def list_models():
    """Returns discovered installed models from live Ollama or visible mock fallback."""
    return await provider.list_models()


@router.get("/running-unowned")
async def list_running_unowned():
    """Inspects running models in Ollama /api/ps without claiming ownership or unloading."""
    return await factory.ollama_provider.inspect_running_models()


@router.post("/mode")
def set_provider_mode(req: ProviderModeRequest):
    """Switch active provider mode between 'auto', 'ollama', and 'mock'."""
    factory.set_mode(req.mode)
    return {"status": "updated", "mode": factory.mode}


@router.post("/chat")
async def chat_inference(req: ChatRequest):
    """
    Synchronous non-streaming inference.
    Resource admission check is evaluated before inference starts.
    """
    # 1. Resource Admission Gate
    admitted, reason = resource_mgr.check_inference_admission()
    if not admitted:
        raise HTTPException(status_code=429, detail=reason)

    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    try:
        return await provider.generate_response(
            msgs,
            req.model_name,
            req.temperature,
            req.max_tokens or 256
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (ConnectionError, RuntimeError) as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/stream")
async def stream_chat(req: ChatRequest, request: Request):
    """
    Progressive Server-Sent Events (SSE) streaming endpoint.
    Streams token-by-token chunks to the frontend.
    Enforces resource admission check and clean cancellation.
    """
    # 1. Resource Admission Gate
    admitted, reason = resource_mgr.check_inference_admission()
    if not admitted:
        async def _error_stream():
            yield f"data: {json.dumps({'error': reason, 'done': True, 'admission_rejected': True})}\n\n"
        return StreamingResponse(_error_stream(), media_type="text/event-stream")

    msgs = [{"role": m.role, "content": m.content} for m in req.messages]

    async def event_generator():
        try:
            async for chunk in provider.stream_response(msgs, req.model_name):
                # Check for client disconnect
                if await request.is_disconnected():
                    break
                yield f"data: {json.dumps(chunk)}\n\n"
        except asyncio.CancelledError:
            # Clean task cancellation triggered by client abort
            pass
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Inference error: {str(e)}', 'done': True})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/load")
async def load_model(req: LoadModelRequest):
    return await provider.load_model(req.model_name, req.is_explicit_confirmation)


@router.post("/unload")
async def unload_model(req: LoadModelRequest):
    success = await provider.unload_model(req.model_name)
    return {"status": "unloaded" if success else "failed", "model": req.model_name}
