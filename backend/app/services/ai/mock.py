"""
Deterministic Mock AI Provider for NEXUS Phase 1.
Provides simulated model catalog, hardware diagnostics, and responses
without model weights, downloads, or background GPU/CPU burn.
"""
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from app.services.ai.base import BaseAIProvider, AIModelInfo


class MockAIProvider(BaseAIProvider):
    def __init__(self):
        self._loaded_model: Optional[str] = None
        self._available_models = [
            AIModelInfo("gemma3:1b", size_gb=0.77, context_window=8192, family="gemma", role="default_assistant"),
            AIModelInfo("qwen2.5-coder:1.5b", size_gb=0.94, context_window=16384, family="qwen", role="coding_assistant"),
            AIModelInfo("phi4-mini:latest", size_gb=2.38, context_window=16384, family="phi", role="restricted_reasoning"),
            AIModelInfo("nomic-embed-text:latest", size_gb=0.26, context_window=8192, family="nomic", role="memory_embeddings"),
            AIModelInfo("qwen3:1.7b", size_gb=1.30, context_window=8192, family="qwen", role="optional"),
        ]

    @property
    def provider_id(self) -> str:
        return "mock"

    @property
    def display_name(self) -> str:
        return "Phase 1 Simulation Provider (Single-Residence & Antigravity Priority Enforced)"

    @property
    def loaded_model(self) -> Optional[str]:
        return self._loaded_model

    async def is_available(self) -> bool:
        return True

    async def detect_hardware(self) -> Dict[str, Any]:
        """Simulate hardware inspection for Intel Core i3-1215U machine."""
        return {
            "has_nvidia_gpu": False,
            "gpu_name": "Intel(R) UHD Graphics (Integrated)",
            "vram_gb": 0.0,
            "cpu_arch": "x86_64",
            "cpu_cores": 6,
            "cpu_threads": 8,
            "recommended_execution_device": "CPU (AVX2-optimized)",
            "safe_max_model_param_b": "3B",
            "concurrency_policy": "Single chat model residence only (Never concurrent)",
            "notes": "Low power i3 laptop profile: recommended 1B-1.5B quantized models (gemma3:1b, qwen2.5-coder:1.5b)."
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        models = [m.to_dict() for m in self._available_models]
        for m in models:
            m["is_loaded"] = (m["name"] == self._loaded_model)
            m["status"] = "ready_in_mock_cache"
        return models

    async def load_model(self, model_name: str, is_explicit_confirmation: bool = False) -> Dict[str, Any]:
        # Enforce Phi-4-mini restriction
        if "phi4-mini" in model_name and not is_explicit_confirmation:
            return {
                "success": False,
                "error": "Phi-4-mini is restricted to explicit use only. Requires user confirmation before loading.",
                "loaded_model": self._loaded_model
            }

        # Enforce single chat model residence: unload any prior model before loading new one
        if self._loaded_model and self._loaded_model != model_name:
            prior = self._loaded_model
            self._loaded_model = None

        self._loaded_model = model_name
        return {
            "success": True,
            "loaded_model": self._loaded_model,
            "single_residence_guaranteed": True
        }

    async def unload_model(self, model_name: str) -> bool:
        if self._loaded_model == model_name:
            self._loaded_model = None
        return True

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        user_msg = messages[-1].get("content", "") if messages else ""

        # Deterministic intelligent mock responses
        if "ecommerce" in user_msg.lower() or "store" in user_msg.lower():
            reply = (
                "Welcome to NEXUS Project Discovery. I've detected that you're aiming to build an e-commerce platform. "
                "Before writing code or choosing templates, we need to clarify essential constraints such as "
                "target platforms (Web vs. Mobile), catalog size, payment gateways, and authentication requirements. "
                "I have prepared an adaptive discovery session in your Central Workspace."
            )
        elif "help" in user_msg.lower() or "what can you do" in user_msg.lower():
            reply = (
                "I am NEXUS, your local-first personal AI operating system workspace. "
                "In this Phase 1 foundation, I provide:\n"
                "• Modular Project Management & Specification\n"
                "• Adaptive Requirement Discovery\n"
                "• Multi-tier Memory & Preference Isolation\n"
                "• Real-time Low-Impact Hardware Resource Protection\n"
                "• Dynamic Island companion interactions"
            )
        else:
            reply = (
                f"NEXUS Phase 1 simulated response: I have captured your thought: '{user_msg}'. "
                "This action is staged in memory. In Phase 2, local AI engines (such as Ollama or llama.cpp) "
                "will run directly on your hardware without cloud telemetry."
            )

        return {
            "provider": self.provider_id,
            "model": model_name or "mock-llama3.2-1b",
            "reply": reply,
            "usage": {
                "prompt_tokens": len(user_msg.split()),
                "completion_tokens": len(reply.split()),
                "total_tokens": len(user_msg.split()) + len(reply.split())
            }
        }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        res = await self.generate_response(messages, model_name)
        words = res["reply"].split(" ")
        for w in words:
            yield w + " "
            await asyncio.sleep(0.02)
