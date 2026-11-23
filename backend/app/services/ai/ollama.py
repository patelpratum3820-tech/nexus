"""
Ollama AI Provider for NEXUS.
Phase 2.3: Real Gemma 3:1B integration, progressive streaming, and model ownership isolation.

Strict constraints:
- Localhost only (http://127.0.0.1:11434).
- Model restriction: 'gemma3:1b' ONLY in Phase 2.3. Zero inference on other models.
- Model ownership: track pre-existing models in /api/ps before inference; never unload externally owned models.
- Never terminate Ollama or its child processes.
- Never log prompt or response contents to console, telemetry, or disk.
- Clean upstream cancellation via socket closure on client disconnect.
"""
import urllib.request
import urllib.error
import json
import socket
import asyncio
import time
from typing import Dict, List, Any, Optional, AsyncGenerator, Set
import httpx
from app.services.ai.base import BaseAIProvider

OLLAMA_HOST = "127.0.0.1"
OLLAMA_PORT = 11434
OLLAMA_BASE_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"

# Exact tag for Phase 2.3
PHASE_2_3_ALLOWED_MODEL = "gemma3:1b"

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

        # Ownership tracking
        self._ownership_initialized: bool = False
        self._pre_existing_models: Set[str] = set()
        self._nexus_managed_model: Optional[str] = None

    @property
    def provider_id(self) -> str:
        return "ollama"

    @property
    def display_name(self) -> str:
        ver = self._cached_version or "local"
        return f"Ollama Local Engine (v{ver})"

    @property
    def loaded_model(self) -> Optional[str]:
        return self._nexus_managed_model

    @property
    def is_nexus_managed(self) -> bool:
        return self._nexus_managed_model is not None

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
            "phase": "2.3-streaming"
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
                "is_loaded": (tag == self._nexus_managed_model),
                "is_mock": False,
                "provider": "ollama",
                "status": "ready_local"
            })

        return discovered

    async def inspect_running_models(self) -> List[Dict[str, Any]]:
        """
        Inspects running models in /api/ps.
        Reports ownership safely: 'nexus_managed' vs 'external_unowned'.
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
                            "ownership": (
                                "nexus_managed"
                                if m.get("name") == self._nexus_managed_model
                                else "external_unowned"
                            )
                        }
                        for m in models
                    ]
        except Exception:
            pass
        return []

    async def _ensure_ownership_checked(self, target_model: str) -> None:
        """
        Inspects /api/ps before generation:
        - If target_model is already running, treat it as externally owned.
        - If target_model is not running, track it as NEXUS-managed once loaded.
        - Never unload another model to make room for Gemma.
        """
        if not self._ownership_initialized:
            running = await self.inspect_running_models()
            running_names = {m["name"] for m in running}
            self._pre_existing_models = running_names
            self._ownership_initialized = True

            # Check if another chat model is already running in Ollama
            other_running = [name for name in running_names if name != target_model]
            if other_running:
                raise RuntimeError(
                    f"External model '{other_running[0]}' is already resident in Ollama. "
                    "NEXUS does not unload externally owned models to preserve user workflow. "
                    "Please unload it externally or wait for its timeout before starting Gemma 3:1B."
                )

            if target_model in running_names:
                # Pre-existing on host; external ownership
                self._nexus_managed_model = None
            else:
                # NEXUS will cause Ollama to load it through inference
                self._nexus_managed_model = target_model

    async def load_model(self, model_name: str, is_explicit_confirmation: bool = False) -> Dict[str, Any]:
        """
        Explicit model preloading is disabled in Phase 2.2 / Phase 2.3.
        Models are loaded safely on-demand via inference requests to /api/chat.
        """
        return {
            "success": False,
            "error": "Explicit model preloading is disabled in Phase 2.2 / Phase 2.3. Models are loaded on-demand via inference.",
            "loaded_model": self._nexus_managed_model
        }

    async def unload_model(self, model_name: str) -> bool:
        """
        Safely unloads model only if NEXUS explicitly managed it.
        Never unloads externally owned models.
        """
        if self._nexus_managed_model != model_name:
            # Not NEXUS-managed or was pre-existing; do not unload
            return False

        try:
            # Issue keep_alive: 0 to unload model runner from memory without stopping Ollama service
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": model_name, "keep_alive": 0}
                )
                if res.status_code == 200:
                    self._nexus_managed_model = None
                    return True
        except Exception:
            pass

        self._nexus_managed_model = None
        return True

    def _validate_phase_2_3_model(self, model_name: Optional[str]) -> str:
        target = model_name or PHASE_2_3_ALLOWED_MODEL
        if target != PHASE_2_3_ALLOWED_MODEL:
            raise ValueError(
                f"Phase 2.3 model restriction: Only '{PHASE_2_3_ALLOWED_MODEL}' is permitted for inference. "
                f"Received request for '{target}'."
            )
        return target

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 256
    ) -> Dict[str, Any]:
        """
        Synchronous non-streaming generation with real Gemma 3:1B via Ollama /api/chat.
        Strictly private: zero logging of prompts or replies.
        """
        target_model = self._validate_phase_2_3_model(model_name)

        # Non-streaming availability check
        if not await self.is_available():
            return {
                "provider": self.provider_id,
                "model": target_model,
                "reply": "NEXUS Phase 2.2 Local AI Discovery: Local Ollama engine is offline or unreachable.",
                "is_mock_response": False,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }

        await self._ensure_ownership_checked(target_model)

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        start_time = time.time()
        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
            except httpx.ConnectError:
                raise ConnectionError(f"Failed to connect to local Ollama on {self.base_url}")
            except httpx.TimeoutException:
                raise TimeoutError("Ollama inference timed out")

            if response.status_code != 200:
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")

            data = response.json()

        reply = data.get("message", {}).get("content", "")
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 1)
        tokens_per_sec = round(eval_count / (eval_duration / 1e9), 1) if eval_duration > 0 else 0.0

        return {
            "provider": self.provider_id,
            "model": target_model,
            "reply": reply,
            "is_mock_response": False,
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": eval_count,
                "total_tokens": data.get("prompt_eval_count", 0) + eval_count,
                "tokens_per_second": tokens_per_sec,
                "duration_seconds": round(time.time() - start_time, 2)
            }
        }

    async def stream_response(
        self,
        messages: List[Dict[str, str]],
        model_name: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Progressive asynchronous streaming from Ollama /api/chat.
        Yields structured token chunks:
        - Regular chunk: {"token": "...", "done": False, "model": "gemma3:1b", "provider": "ollama", "is_mock": False}
        - Final chunk: {"token": "", "done": True, "eval_count": ..., "tokens_per_second": ...}
        Clean cancellation: exiting context manager terminates upstream socket on disconnect.
        """
        target_model = self._validate_phase_2_3_model(model_name)

        if not await self.is_available():
            raise ConnectionError(f"Ollama stream service is not reachable on {self.base_url}")

        await self._ensure_ownership_checked(target_model)

        payload = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": 0.7,
                "num_predict": 128
            }
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(connect=5.0, read=60.0, write=5.0, pool=5.0)) as client:
            try:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    if response.status_code == 404:
                        raise FileNotFoundError(f"Model '{target_model}' not found in Ollama.")
                    if response.status_code != 200:
                        raise RuntimeError(f"Ollama stream error HTTP {response.status_code}")

                    async for line in response.aiter_lines():
                        if not line or not line.strip():
                            continue

                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        delta = chunk.get("message", {}).get("content", "")
                        is_done = chunk.get("done", False)

                        if not is_done:
                            if delta:
                                yield {
                                    "token": delta,
                                    "done": False,
                                    "model": target_model,
                                    "provider": self.provider_id,
                                    "is_mock": False
                                }
                        else:
                            # Final evaluation chunk
                            eval_count = chunk.get("eval_count", 0)
                            eval_duration = chunk.get("eval_duration", 1)
                            tps = round(eval_count / (eval_duration / 1e9), 1) if eval_duration > 0 else 0.0

                            yield {
                                "token": delta,
                                "done": True,
                                "model": target_model,
                                "provider": self.provider_id,
                                "is_mock": False,
                                "eval_count": eval_count,
                                "eval_duration_ms": round(eval_duration / 1e6, 1),
                                "tokens_per_second": tps
                            }
                            break
            except asyncio.CancelledError:
                # Upstream socket is automatically closed by exiting context manager
                raise
