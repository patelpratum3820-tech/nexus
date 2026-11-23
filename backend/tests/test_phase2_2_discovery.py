"""
Unit and integration tests for NEXUS Phase 2.2: Ollama Connection & Model Discovery.
Verifies:
- Ollama availability detection (reachable and unavailable).
- Version response parsing.
- Model tag discovery and exact role mapping.
- Unknown model tag handling and missing models.
- Malformed API response resilience.
- Security boundary (localhost only, rejects remote URLs).
- Mock fallback transparency (mock mode clearly identified, never disguised as real AI).
- Strict non-inference: no model loading, unloading, downloads, or real inference.
"""
import unittest
import sys
import os
import asyncio
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from app.main import app
from app.services.ai.ollama import OllamaAIProvider, TAG_TO_ROLE_MAP
from app.services.ai.factory import AIProviderFactory


class TestPhase22Discovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.factory = AIProviderFactory.get_instance()

    def test_security_localhost_endpoint_enforcement(self):
        """Verify OllamaAIProvider strictly enforces localhost and rejects remote endpoints."""
        # Localhost is valid
        p_valid = OllamaAIProvider("http://127.0.0.1:11434")
        self.assertEqual(p_valid.base_url, "http://127.0.0.1:11434")

        # Remote / LAN / Arbitrary URL must be rejected
        with self.assertRaises(ValueError):
            OllamaAIProvider("http://192.168.1.50:11434")

        with self.assertRaises(ValueError):
            OllamaAIProvider("https://remote-ai.example.com")

    def test_live_or_mocked_ollama_version_and_availability(self):
        """Verify Ollama service availability detection and version reading."""
        provider = OllamaAIProvider()

        async def _test():
            is_avail = await provider.is_available()
            # If Ollama is running on this machine (confirmed 0.40.3)
            if is_avail:
                version = await provider.get_version()
                self.assertIsNotNone(version)
                self.assertEqual(version, "0.40.3")
                self.assertIn("0.40.3", provider.display_name)
            else:
                self.assertFalse(is_avail)

        asyncio.run(_test())

    def test_version_parsing_mocked(self):
        """Verify version response parsing across standard and edge-case payloads."""
        provider = OllamaAIProvider()

        # 1. Standard version response
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'{"version": "0.40.3"}'
            mock_open.return_value.__enter__.return_value = mock_resp

            async def _t1():
                avail = await provider.is_available()
                self.assertTrue(avail)
                ver = await provider.get_version()
                self.assertEqual(ver, "0.40.3")

            asyncio.run(_t1())

        # 2. Malformed version response
        with patch("urllib.request.urlopen") as mock_open:
            mock_resp = MagicMock()
            mock_resp.status = 200
            mock_resp.read.return_value = b'invalid json string'
            mock_open.return_value.__enter__.return_value = mock_resp

            async def _t2():
                # Should handle json error gracefully
                avail = await provider.is_available()
                self.assertFalse(avail)

            asyncio.run(_t2())

    def test_model_tag_discovery_and_exact_role_mapping(self):
        """Verify exact role mapping and discovery parsing from Ollama /api/tags."""
        provider = OllamaAIProvider()

        sample_tags_payload = {
            "models": [
                {
                    "name": "gemma3:1b",
                    "size": 806067407,
                    "details": {"family": "gemma", "parameter_size": "1B", "quantization_level": "Q4_K_M"}
                },
                {
                    "name": "qwen2.5-coder:1.5b",
                    "size": 986062089,
                    "details": {"family": "qwen", "parameter_size": "1.5B", "quantization_level": "Q4_K_M"}
                },
                {
                    "name": "phi4-mini:latest",
                    "size": 2491876774,
                    "details": {"family": "phi", "parameter_size": "3.8B", "quantization_level": "Q4_K_M"}
                },
                {
                    "name": "nomic-embed-text:latest",
                    "size": 274302450,
                    "details": {"family": "nomic", "parameter_size": "137M", "quantization_level": "F16"}
                },
                {
                    "name": "qwen3:1.7b",
                    "size": 1359293444,
                    "details": {"family": "qwen", "parameter_size": "1.7B", "quantization_level": "Q4_K_M"}
                },
                {
                    "name": "unknown-experimental:3b",
                    "size": 1900000000,
                    "details": {"family": "llama", "parameter_size": "3B", "quantization_level": "Q4_0"}
                }
            ]
        }

        with patch.object(provider, "is_available", return_value=True):
            with patch("urllib.request.urlopen") as mock_open:
                import json
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.read.return_value = json.dumps(sample_tags_payload).encode("utf-8")
                mock_open.return_value.__enter__.return_value = mock_resp

                async def _t():
                    models = await provider.list_models()
                    self.assertEqual(len(models), 6)

                    roles_by_name = {m["name"]: m["role"] for m in models}
                    self.assertEqual(roles_by_name["gemma3:1b"], "default_assistant")
                    self.assertEqual(roles_by_name["qwen2.5-coder:1.5b"], "coding_assistant")
                    self.assertEqual(roles_by_name["phi4-mini:latest"], "restricted_reasoning")
                    self.assertEqual(roles_by_name["nomic-embed-text:latest"], "memory_embeddings")
                    self.assertEqual(roles_by_name["qwen3:1.7b"], "optional")
                    self.assertEqual(roles_by_name["unknown-experimental:3b"], "unassigned")

                    # Verify no models are marked as loaded in Phase 2.2
                    for m in models:
                        self.assertFalse(m["is_loaded"])
                        self.assertTrue(m["is_installed"])
                        self.assertFalse(m["is_mock"])
                        self.assertEqual(m["provider"], "ollama")

                asyncio.run(_t())

    def test_missing_models_in_api_tags(self):
        """Verify models absent from /api/tags are NOT assumed to exist."""
        provider = OllamaAIProvider()

        # Simulate Ollama only having gemma3:1b installed
        sparse_payload = {
            "models": [
                {"name": "gemma3:1b", "size": 806067407, "details": {"family": "gemma"}}
            ]
        }

        with patch.object(provider, "is_available", return_value=True):
            with patch("urllib.request.urlopen") as mock_open:
                import json
                mock_resp = MagicMock()
                mock_resp.status = 200
                mock_resp.read.return_value = json.dumps(sparse_payload).encode("utf-8")
                mock_open.return_value.__enter__.return_value = mock_resp

                async def _t():
                    models = await provider.list_models()
                    self.assertEqual(len(models), 1)
                    names = [m["name"] for m in models]
                    self.assertIn("gemma3:1b", names)
                    self.assertNotIn("qwen2.5-coder:1.5b", names)
                    self.assertNotIn("phi4-mini:latest", names)

                asyncio.run(_t())

    def test_ollama_unavailable_and_connection_timeout(self):
        """Verify graceful error handling and empty list when Ollama daemon is down."""
        provider = OllamaAIProvider("http://127.0.0.1:11434", timeout_sec=0.1)

        import urllib.error
        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Connection refused")):
            async def _t():
                avail = await provider.is_available()
                self.assertFalse(avail)
                models = await provider.list_models()
                self.assertEqual(models, [])

            asyncio.run(_t())

    def test_mock_fallback_transparency(self):
        """Verify factory provides complete transparency when falling back to Mock provider."""
        factory = AIProviderFactory()

        async def _test():
            # Force mock mode
            factory.set_mode("mock")
            active = await factory.get_active_provider()
            self.assertEqual(active.provider_id, "mock")

            status = await factory.get_status()
            self.assertEqual(status["active_provider_id"], "mock")
            self.assertEqual(status["mode"], "mock")

            # Reset to auto
            factory.set_mode("auto")

        asyncio.run(_test())

    def test_phase2_2_strict_non_inference_and_non_loading(self):
        """
        Verify that in Phase 2.2:
        - OllamaAIProvider.load_model returns success: False (does not issue engine load commands).
        - OllamaAIProvider.unload_model returns False.
        - OllamaAIProvider.generate_response returns status notice without real inference.
        """
        provider = OllamaAIProvider()

        async def _test():
            load_res = await provider.load_model("gemma3:1b")
            self.assertFalse(load_res["success"])
            self.assertIn("disabled in Phase 2.2", load_res["error"])

            unload_res = await provider.unload_model("gemma3:1b")
            self.assertFalse(unload_res)

            chat_res = await provider.generate_response([{"role": "user", "content": "Hello"}])
            self.assertIn("Phase 2.2 Local AI Discovery", chat_res["reply"])
            self.assertFalse(chat_res["is_mock_response"])

        asyncio.run(_test())

    def test_api_status_and_models_endpoints(self):
        """Verify /api/ai/status and /api/ai/models HTTP endpoints."""
        status_res = self.client.get("/api/ai/status")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertIn("active_provider_id", status_data)
        self.assertIn("ollama_available", status_data)
        self.assertIn("ollama_endpoint", status_data)

        models_res = self.client.get("/api/ai/models")
        self.assertEqual(models_res.status_code, 200)
        models_data = models_res.json()
        self.assertIsInstance(models_data, list)
        if len(models_data) > 0:
            first = models_data[0]
            self.assertIn("name", first)
            self.assertIn("role", first)


if __name__ == "__main__":
    unittest.main()
