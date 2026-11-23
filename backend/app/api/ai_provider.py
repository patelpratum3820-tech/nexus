"""
AI Provider API endpoints for NEXUS.
Phase 2.2: Live Ollama connection, version discovery, tag inspection, and role mapping.
Includes transparent fallback to MockAIProvider when Ollama is unreachable.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.services.ai.base import BaseAIProvider
from app.services.ai.factory import AIProviderFactory

router = APIRouter(prefix="/api/ai", tags=["AI Provider"])
factory = AIProviderFactory.get_instance()


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


class ProviderModeRequest(BaseModel):
    mode: str  # "auto", "ollama", "mock"


class DynamicAIProviderProxy(BaseAIProvider):
    """
    Transparent proxy exposing the active AI provider (Ollama or Mock).
    Maintains compatibility with system lifecycle hooks and regression suites.
    In Phase 2.2, zero load/unload/inference commands are sent to Ollama.
    """
    def __init__(self, provider_factory: AIProviderFactory):
        self._factory = provider_factory
        self._nexus_loaded_model: Optional[str] = None

    @property
    def provider_id(self) -> str:
        return self._factory.ollama_provider.provider_id if self._factory.mode != "mock" else "mock"

    @property
    def display_name(self) -> str:
        return self._factory.ollama_provider.display_name if self._factory.mode != "mock" else self._factory.mock_provider.display_name

    @property
    def loaded_model(self) -> Optional[str]:
        return self._nexus_loaded_model

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
        # Enforce Phi-4 confirmation requirement
        if "phi4-mini" in model_name and not is_explicit_confirmation:
            return {
                "success": False,
                "error": "Phi-4-mini is restricted to explicit use only. Requires user confirmation before loading.",
                "loaded_model": self._nexus_loaded_model
            }

        # Single-model residence: displace prior model
        self._nexus_loaded_model = model_name
        return {
            "success": True,
            "loaded_model": self._nexus_loaded_model,
            "single_residence_guaranteed": True,
            "note": "Phase 2.2 discovery mode: tracked locally without issuing Ollama engine load commands."
        }

    async def unload_model(self, model_name: str) -> bool:
        if self._nexus_loaded_model == model_name:
            self._nexus_loaded_model = None
        return True

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        active = await self._factory.get_active_provider()
        return await active.generate_response(messages, model_name, temperature, max_tokens)

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
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
    return await factory.ollama_provider.inspect_running_models_unowned()


@router.post("/mode")
def set_provider_mode(req: ProviderModeRequest):
    """Switch active provider mode between 'auto', 'ollama', and 'mock'."""
    factory.set_mode(req.mode)
    return {"status": "updated", "mode": factory.mode}


@router.post("/chat")
async def chat_inference(req: ChatRequest):
    """Executes safe response (Phase 2.2 discovery status notice or mock simulation)."""
    msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    return await provider.generate_response(msgs, req.model_name, req.temperature)


@router.post("/load")
async def load_model(req: LoadModelRequest):
    return await provider.load_model(req.model_name, req.is_explicit_confirmation)


@router.post("/unload")
async def unload_model(req: LoadModelRequest):
    success = await provider.unload_model(req.model_name)
    return {"status": "unloaded" if success else "failed", "model": req.model_name}
