"""
AI Provider Factory for NEXUS.
Detects live local Ollama engine availability and falls back visibly to MockAIProvider when unavailable.
Strictly distinguishes real Ollama status from mock simulation in API responses.
"""
from typing import Dict, Any, Optional
from app.services.ai.base import BaseAIProvider
from app.services.ai.mock import MockAIProvider
from app.services.ai.ollama import OllamaAIProvider


class AIProviderFactory:
    _instance: Optional["AIProviderFactory"] = None

    def __init__(self, default_mode: str = "auto"):
        self._mode = default_mode  # "auto", "ollama", "mock"
        self._mock_provider = MockAIProvider()
        self._ollama_provider = OllamaAIProvider()

    @classmethod
    def get_instance(cls) -> "AIProviderFactory":
        if cls._instance is None:
            cls._instance = AIProviderFactory()
        return cls._instance

    def set_mode(self, mode: str) -> None:
        if mode not in ("auto", "ollama", "mock"):
            raise ValueError(f"Invalid provider mode: {mode}. Must be 'auto', 'ollama', or 'mock'.")
        self._mode = mode

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def mock_provider(self) -> MockAIProvider:
        return self._mock_provider

    @property
    def ollama_provider(self) -> OllamaAIProvider:
        return self._ollama_provider

    async def get_active_provider(self) -> BaseAIProvider:
        """
        Resolves the appropriate active provider.
        - If mode is 'mock': returns MockAIProvider.
        - If mode is 'ollama': returns OllamaAIProvider.
        - If mode is 'auto': probes Ollama availability.
          If reachable -> OllamaAIProvider.
          If unreachable -> visibly falls back to MockAIProvider.
        """
        if self._mode == "mock":
            return self._mock_provider

        if self._mode == "ollama":
            return self._ollama_provider

        # Auto mode: probe real local Ollama
        if await self._ollama_provider.is_available():
            return self._ollama_provider

        return self._mock_provider

    async def get_status(self) -> Dict[str, Any]:
        """Provides full transparency into active provider and fallback status."""
        ollama_avail = await self._ollama_provider.is_available()
        active = await self.get_active_provider()
        is_fallback = (active.provider_id == "mock" and self._mode != "mock")

        return {
            "active_provider_id": active.provider_id,
            "active_display_name": active.display_name,
            "mode": self._mode,
            "ollama_available": ollama_avail,
            "ollama_version": await self._ollama_provider.get_version(),
            "ollama_endpoint": "http://127.0.0.1:11434",
            "is_mock_fallback": is_fallback,
            "fallback_notice": (
                "NOTICE: Ollama service is unavailable. Operating in visible MOCK SIMULATION mode."
                if is_fallback else None
            ),
            "phase": "2.2-discovery"
        }
