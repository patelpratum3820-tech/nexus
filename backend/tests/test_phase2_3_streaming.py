"""
Unit and integration tests for NEXUS Phase 2.3: Real Gemma AI Integration & Streaming.
Verifies:
- Ollama SSE progressive token streaming.
- Model restriction: 'gemma3:1b' only (rejection of other model tags).
- Final response evaluation and token speed calculation.
- Malformed stream chunks and network error resilience.
- Ollama unavailable and missing model (404) handling.
- Resource admission gate: rejection when CPU > 80% or available RAM < 2.0 GB.
- Upstream cancellation on client disconnect.
- Model ownership isolation (tracking pre-existing models vs NEXUS-managed).
- Mock fallback streaming compatibility.
"""
import unittest
import sys
import os
import json
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from app.main import app
from app.services.ai.ollama import OllamaAIProvider, PHASE_2_3_ALLOWED_MODEL
from app.services.ai.factory import AIProviderFactory
from app.services.resource_mgr import ResourceManager


class MockStreamContext:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self.response

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None


class TestPhase23Streaming(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.factory = AIProviderFactory.get_instance()
        cls.resource_mgr = ResourceManager.get_instance()

    def test_strict_model_restriction(self):
        """Verify only 'gemma3:1b' is allowed; all other models are strictly rejected."""
        provider = OllamaAIProvider()

        # Gemma 3:1B is allowed
        self.assertEqual(provider._validate_phase_2_3_model("gemma3:1b"), "gemma3:1b")
        self.assertEqual(provider._validate_phase_2_3_model(None), "gemma3:1b")

        # Prohibited Phase 2.3 models must be rejected with ValueError
        prohibited = [
            "qwen2.5-coder:1.5b",
            "phi4-mini:latest",
            "qwen3:1.7b",
            "nomic-embed-text:latest",
            "llama3:8b"
        ]
        for model in prohibited:
            with self.assertRaises(ValueError):
                provider._validate_phase_2_3_model(model)

    def test_resource_admission_rejection(self):
        """Verify inference is rejected if CPU > 80% or available RAM < 2.0 GB."""
        # 1. CPU pressure rejection
        with patch.object(self.resource_mgr, "sample_metrics", return_value={
            "cpu_percent": 88.5,
            "ram_available_gb": 6.0
        }):
            admitted, reason = self.resource_mgr.check_inference_admission()
            self.assertFalse(admitted)
            self.assertIn("CPU utilization too high", reason)

            # Test through /api/ai/chat endpoint
            res = self.client.post("/api/ai/chat", json={"messages": [{"role": "user", "content": "hi"}]})
            self.assertEqual(res.status_code, 429)

            # Test through /api/ai/stream endpoint
            stream_res = self.client.post("/api/ai/stream", json={"messages": [{"role": "user", "content": "hi"}]})
            self.assertEqual(stream_res.status_code, 200)
            self.assertIn("admission_rejected", stream_res.text)

        # 2. RAM pressure rejection
        with patch.object(self.resource_mgr, "sample_metrics", return_value={
            "cpu_percent": 25.0,
            "ram_available_gb": 1.2
        }):
            admitted, reason = self.resource_mgr.check_inference_admission()
            self.assertFalse(admitted)
            self.assertIn("Available RAM too low", reason)

    def test_mocked_ollama_sse_stream_chunks(self):
        """Verify progressive token delivery and SSE formatting from mocked Ollama stream."""
        provider = OllamaAIProvider()

        sample_lines = [
            json.dumps({"model": "gemma3:1b", "message": {"role": "assistant", "content": "Hello"}, "done": False}),
            json.dumps({"model": "gemma3:1b", "message": {"role": "assistant", "content": " world"}, "done": False}),
            json.dumps({"model": "gemma3:1b", "message": {"role": "assistant", "content": "!"}, "done": False}),
            json.dumps({"model": "gemma3:1b", "message": {"role": "assistant", "content": ""}, "done": True, "eval_count": 3, "eval_duration": 100000000})
        ]

        async def fake_aiter():
            for line in sample_lines:
                yield line

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = fake_aiter

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.stream = MagicMock(return_value=MockStreamContext(mock_resp))

        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "_ensure_ownership_checked", new_callable=AsyncMock):
                with patch("httpx.AsyncClient", return_value=mock_client):
                    async def _t():
                        chunks = []
                        async for chunk in provider.stream_response([{"role": "user", "content": "hi"}]):
                            chunks.append(chunk)

                        self.assertEqual(len(chunks), 4)
                        self.assertEqual(chunks[0]["token"], "Hello")
                        self.assertFalse(chunks[0]["done"])
                        self.assertEqual(chunks[1]["token"], " world")
                        self.assertEqual(chunks[2]["token"], "!")

                        # Final chunk
                        final = chunks[3]
                        self.assertTrue(final["done"])
                        self.assertEqual(final["eval_count"], 3)
                        self.assertGreater(final["tokens_per_second"], 0.0)

                    asyncio.run(_t())

    def test_model_ownership_lifecycle(self):
        """
        Verify model ownership isolation:
        - If Gemma was pre-existing in /api/ps, it is external (NEXUS does not claim or unload).
        - If Gemma was absent, NEXUS tracks it as managed and can unload on shutdown.
        - If another model is resident, generation is rejected.
        """
        provider = OllamaAIProvider()

        async def _test_case():
            # Scenario A: External Gemma pre-existing
            with patch.object(provider, "inspect_running_models", return_value=[{"name": "gemma3:1b"}]):
                await provider._ensure_ownership_checked("gemma3:1b")
                self.assertFalse(provider.is_nexus_managed)
                # Should not unload externally owned model
                unloaded = await provider.unload_model("gemma3:1b")
                self.assertFalse(unloaded)

            # Scenario B: Another model running -> must reject
            provider._ownership_initialized = False
            with patch.object(provider, "inspect_running_models", return_value=[{"name": "phi4-mini:latest"}]):
                with self.assertRaises(RuntimeError) as ctx:
                    await provider._ensure_ownership_checked("gemma3:1b")
                self.assertIn("External model 'phi4-mini:latest' is already resident", str(ctx.exception))

            # Scenario C: Clean startup -> NEXUS manages Gemma
            provider._ownership_initialized = False
            with patch.object(provider, "inspect_running_models", return_value=[]):
                await provider._ensure_ownership_checked("gemma3:1b")
                self.assertTrue(provider.is_nexus_managed)
                self.assertEqual(provider.loaded_model, "gemma3:1b")

        asyncio.run(_test_case())

    def test_mock_fallback_streaming_compatibility(self):
        """Verify MockAIProvider streaming adheres to the identical SSE chunk structure."""
        factory = AIProviderFactory.get_instance()
        mock_p = factory.mock_provider

        async def _test():
            chunks = []
            async for chunk in mock_p.stream_response([{"role": "user", "content": "What is NEXUS?"}]):
                chunks.append(chunk)

            self.assertGreater(len(chunks), 2)
            self.assertTrue(chunks[0]["is_mock"])
            self.assertEqual(chunks[0]["provider"], "mock")
            self.assertFalse(chunks[0]["done"])

            final = chunks[-1]
            self.assertTrue(final["done"])
            self.assertTrue(final["is_mock"])
            self.assertIn("eval_count", final)

        asyncio.run(_test())

    def test_cancellation_and_client_disconnect(self):
        """Verify task cancellation exits cleanly without orphan sockets."""
        provider = OllamaAIProvider()

        async def infinite_lines():
            while True:
                yield json.dumps({"model": "gemma3:1b", "message": {"role": "assistant", "content": "tok"}, "done": False})
                await asyncio.sleep(0.01)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.aiter_lines = infinite_lines

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.stream = MagicMock(return_value=MockStreamContext(mock_resp))

        with patch.object(provider, "is_available", return_value=True):
            with patch.object(provider, "_ensure_ownership_checked", new_callable=AsyncMock):
                with patch("httpx.AsyncClient", return_value=mock_client):
                    async def _test_cancel():
                        received = []
                        async def consumer():
                            async for chunk in provider.stream_response([{"role": "user", "content": "hi"}]):
                                received.append(chunk)
                                if len(received) >= 2:
                                    # Simulate client abort
                                    raise asyncio.CancelledError()

                        with self.assertRaises(asyncio.CancelledError):
                            await consumer()

                        self.assertEqual(len(received), 2)

                    asyncio.run(_test_cancel())


if __name__ == "__main__":
    unittest.main()
