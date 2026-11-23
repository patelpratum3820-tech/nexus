"""
Abstract Base Class for NEXUS AI Providers.
Ensures uniform interface for Phase 1 Mock and Phase 2+ Local Engines (Ollama, llama.cpp, etc.).
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator


class AIModelInfo:
    def __init__(self, name: str, size_gb: float, context_window: int, supports_vision: bool = False, family: str = "llama", role: str = "general"):
        self.name = name
        self.size_gb = size_gb
        self.context_window = context_window
        self.supports_vision = supports_vision
        self.family = family
        self.role = role

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "size_gb": self.size_gb,
            "context_window": self.context_window,
            "supports_vision": self.supports_vision,
            "family": self.family,
            "role": self.role
        }


class BaseAIProvider(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Unique identifier for this AI provider (e.g. 'mock', 'ollama', 'llamacpp')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if provider engine or service is installed and reachable."""
        pass

    @abstractmethod
    async def detect_hardware(self) -> Dict[str, Any]:
        """Inspect hardware capabilities (GPU/CPU/RAM)."""
        pass

    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """List currently discovered or installed models."""
        pass

    @abstractmethod
    async def load_model(self, model_name: str, is_explicit_confirmation: bool = False) -> Dict[str, Any]:
        """Explicitly load a model into memory. Returns structured status dictionary."""
        pass

    @abstractmethod
    async def unload_model(self, model_name: str) -> bool:
        """Unload model to free system RAM/VRAM."""
        pass

    @abstractmethod
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """Generate a complete text response."""
        pass

    @abstractmethod
    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generated tokens incrementally."""
        pass
