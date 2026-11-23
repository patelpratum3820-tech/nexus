"""
Automated unit tests for NEXUS Concurrency & Priority Rules.
Verifies single-model residence enforcement, Phi-4-mini explicit restrictions,
Antigravity priority reservation, and mock role catalog.
"""
import unittest
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai.mock import MockAIProvider
from app.services.resource_mgr import ResourceManager
from app.core.config import (
    SINGLE_MODEL_RESIDENCE_ONLY,
    ANTIGRAVITY_PRIORITY_RESERVE_RAM_GB,
    ALLOW_EMBEDDING_CONCURRENCY,
    MODEL_ROLES
)


class TestConcurrencyRules(unittest.TestCase):
    def test_concurrency_configuration(self):
        self.assertTrue(SINGLE_MODEL_RESIDENCE_ONLY, "Single model residence must be strictly enforced")
        self.assertFalse(ALLOW_EMBEDDING_CONCURRENCY, "Embedding concurrency must remain disabled until verified")
        self.assertEqual(ANTIGRAVITY_PRIORITY_RESERVE_RAM_GB, 2.0, "2.0 GB RAM must be reserved for Antigravity & OS priority")
        self.assertEqual(MODEL_ROLES["default_assistant"], "gemma3:1b")
        self.assertEqual(MODEL_ROLES["coding_assistant"], "qwen2.5-coder:1.5b")
        self.assertEqual(MODEL_ROLES["restricted_reasoning"], "phi4-mini:latest")
        self.assertEqual(MODEL_ROLES["memory_embeddings"], "nomic-embed-text:latest")

    def test_single_model_residence_enforcement(self):
        async def _test():
            provider = MockAIProvider()

            # 1. Load default assistant (Gemma 3:1B)
            res1 = await provider.load_model("gemma3:1b")
            self.assertTrue(res1["success"])
            self.assertEqual(res1["loaded_model"], "gemma3:1b")

            # 2. Load coding assistant (Qwen 2.5 Coder 1.5B) -> must displace Gemma
            res2 = await provider.load_model("qwen2.5-coder:1.5b")
            self.assertTrue(res2["success"])
            self.assertEqual(res2["loaded_model"], "qwen2.5-coder:1.5b")

            # 3. Verify only ONE model is resident in list_models()
            models = await provider.list_models()
            loaded_models = [m["name"] for m in models if m.get("is_loaded")]
            self.assertEqual(len(loaded_models), 1)
            self.assertEqual(loaded_models[0], "qwen2.5-coder:1.5b")

        asyncio.run(_test())

    def test_phi4_mini_explicit_confirmation_restriction(self):
        async def _test():
            provider = MockAIProvider()

            # 1. Attempt to load Phi-4-mini without explicit confirmation -> must be rejected
            unconfirmed_res = await provider.load_model("phi4-mini:latest", is_explicit_confirmation=False)
            self.assertFalse(unconfirmed_res["success"])
            self.assertIn("restricted", unconfirmed_res["error"].lower())

            # 2. Attempt to load with explicit user confirmation -> must succeed
            confirmed_res = await provider.load_model("phi4-mini:latest", is_explicit_confirmation=True)
            self.assertTrue(confirmed_res["success"])
            self.assertEqual(confirmed_res["loaded_model"], "phi4-mini:latest")

        asyncio.run(_test())

    def test_antigravity_resource_priority_guard(self):
        mgr = ResourceManager.get_instance()
        metrics = mgr.sample_metrics()

        self.assertTrue(metrics.get("antigravity_priority_active"))
        self.assertGreaterEqual(mgr.min_ram_limit_gb, 2.0)
        self.assertLessEqual(mgr.max_cpu_limit, 80.0)


if __name__ == "__main__":
    unittest.main()
