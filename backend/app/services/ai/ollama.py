"""
Ollama AI Provider for NEXUS.
Phase 2.2: Connection detection, version discovery, tag inspection, and role mapping.

Strict constraints:
- Localhost only (http://127.0.0.1:11434).
- No downloads, no real inference, no model loading or unloading in Phase 2.2.
- Respect external process and model ownership.
- Zero background polling.
"""
import urllib.request
import urllib.error
import json
import socket
from typing import Dict, List, Any, Optional, AsyncGenerator
from app.services.ai.base import BaseAIProvider

OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Confirmed architecture role assignments
TAG_TO_ROLE_MAP = {
    "gemma3:1b": "default_assistant",
    "qwen2.5-coder:1.5b": "coding_assistant",
    "phi4-mini:latest": "restricted_reasoning",
    "nomic-embed-text:latest": "memory_embeddings",
    "qwen3:1.7b": "optional",
}


class OllamaAIProvider(BaseAIProvider):
    def __init__(self, base_url: str = OLLAMA_BASE_URL, timeout_sec: float = 2.0):
        # Strict security constraint: must always be localhost
        if "127.0.0.1" not in base_url and "localhost" not in base_url:
            raise ValueError(f"Security violation: Ollama endpoint must be localhost (127.0.0.1), got {base_url}")
        self.base_url = base_url
        self.timeout_sec = timeout_sec
        self._cached_version: Optional[str] = None
        self._last_available: Optional[bool] = None

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        ver = self._cached_version or "local"
        return f"Ollama Local Engine (v{ver})"

    @property
    def loaded_model(self) -> Optional[str]:
        # Phase 2.2 is discovery-only. NEXUS does not claim ownership of any running model.
        return None

    async def is_available(self) -> bool:
        """
        Safely inspects if the local Ollama daemon is reachable on 127.0.0.1:11434.
        Never starts, restarts, or terminates Ollama.
        """
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/version",
                headers={"User-Agent": "NEXUS-Core/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    self._cached_version = data.get("version", "unknown")
                    self._last_available = True
                    return True
        except (urllib.error.URLError, socket.timeout, ConnectionRefusedError, OSError):
            self._last_available = False
            self._cached_version = None
        except Exception:
            self._last_available = False
            self._cached_version = None
        return False

    async def get_version(self) -> Optional[str]:
        if not self._cached_version:
            await self.is_available()
        return self._cached_version

    async def detect_hardware(self) -> Dict[str, Any]:
        """Detect local hardware profile and Ollama integration status."""
        avail = await self.is_available()
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
            "ollama_available": avail,
            "ollama_version": self._cached_version,
            "ollama_endpoint": self.base_url,
            "provider_type": "ollama",
            "phase": "2.2-discovery"
        }

    async def list_models(self) -> List[Dict[str, Any]]:
        """
        Discovers installed models from Ollama /api/tags and maps them to NEXUS roles.
        Uses exact discovered tags. Does not assume a model exists if absent from /api/tags.
        """
        if not await self.is_available():
            return []

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"User-Agent": "NEXUS-Core/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status != 200:
                    return []
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return []

        raw_models = payload.get("models", [])
        discovered: List[Dict[str, Any]] = []

        for m in raw_models:
            tag = m.get("name", "")
            size_bytes = m.get("size", 0)
            size_gb = round(size_bytes / (1024 ** 3), 2)
            modified_at = m.get("modified_at", "")
            digest = m.get("digest", "")
            details = m.get("details", {})

            # Exact role mapping
            role = TAG_TO_ROLE_MAP.get(tag, "unassigned")

            # Extract or deduce architecture family
            family = details.get("family", "")
            if not family:
                if "gemma" in tag:
                    family = "gemma"
                elif "qwen" in tag:
                    family = "qwen"
                elif "phi" in tag:
                    family = "phi"
                elif "nomic" in tag:
                    family = "nomic"
                else:
                    family = "unknown"

            discovered.append({
                "name": tag,
                "role": role,
                "size_gb": size_gb,
                "size_bytes": size_bytes,
                "family": family,
                "parameter_size": details.get("parameter_size", ""),
                "quantization_level": details.get("quantization_level", ""),
                "modified_at": modified_at,
                "digest": digest,
                "is_installed": True,
                "is_loaded": False,  # Phase 2.2: discovery only, no loading
                "is_mock": False,
                "provider": "ollama",
                "status": "ready_local"
            })

        return discovered

    async def inspect_running_models_unowned(self) -> List[Dict[str, Any]]:
        """
        Inspects pre-existing models in /api/ps without claiming ownership or unloading.
        Strict ownership protection for Phase 2.2.
        """
        if not await self.is_available():
            return []
        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/ps",
                headers={"User-Agent": "NEXUS-Core/1.0"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    models = payload.get("models", [])
                    return [
                        {
                            "name": m.get("name", ""),
                            "size_vram_gb": round(m.get("size_vram", 0) / (1024 ** 3), 2),
                            "expires_at": m.get("expires_at", ""),
                            "ownership": "external_unowned"
                        }
                        for m in models
                    ]
        except Exception:
            pass
        return []

    async def load_model(self, model_name: str, is_explicit_confirmation: bool = False) -> Dict[str, Any]:
        """In Phase 2.2, model loading is explicitly disabled (Discovery only)."""
        return {
            "success": False,
            "error": "Model loading is disabled in Phase 2.2 (Discovery Only). Scheduled for Phase 2.3+.",
            "phase": "2.2",
            "provider": "ollama"
        }

    async def unload_model(self, model_name: str) -> bool:
        """In Phase 2.2, model unloading is explicitly disabled (Discovery only)."""
        return False

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> Dict[str, Any]:
        """In Phase 2.2, real inference is disabled. Returns status explanation."""
        return {
            "provider": "ollama",
            "is_mock_response": False,
            "phase": "2.2",
            "reply": (
                "NEXUS Phase 2.2 Local AI Discovery: Local Ollama engine is connected and reachable. "
                "Real token generation is scheduled for Phase 2.3 (Gemma 3:1B Streaming)."
            ),
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        res = await self.generate_response(messages, model_name)
        yield res["reply"]
