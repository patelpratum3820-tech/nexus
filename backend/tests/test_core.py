"""
Automated unit tests for NEXUS Backend (Phase 1).
Validates SQLite database, Resource Manager, Discovery Engine,
Multi-tier Memory, and Mock AI Provider.
"""
import unittest
import os
import sys

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import init_db, get_db_cursor
from app.services.resource_mgr import ResourceManager
from app.services.discovery import DiscoveryService
from app.services.memory import MemoryService
from app.services.ai.mock import MockAIProvider
import asyncio


class TestNexusBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_database_initialization(self):
        with get_db_cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cursor.fetchall()}
            self.assertIn("projects", tables)
            self.assertIn("discovery_sessions", tables)
            self.assertIn("discovery_answers", tables)
            self.assertIn("memories", tables)
            self.assertIn("resource_logs", tables)

    def test_resource_manager_metrics(self):
        mgr = ResourceManager.get_instance()
        metrics = mgr.sample_metrics()
        self.assertIn("ram_total_gb", metrics)
        self.assertIn("ram_available_gb", metrics)
        self.assertIn("status", metrics)
        self.assertGreater(metrics["ram_total_gb"], 0)
        self.assertIn(metrics["status"], ["normal", "constrained", "critical"])

    def test_discovery_flow_and_spec_generation(self):
        service = DiscoveryService()
        session = service.start_session("Test Ecom", "I want to build an e-commerce website")
        self.assertEqual(session["status"], "in_progress")
        self.assertEqual(session["flow_type"], "ecommerce")

        session_id = session["session_id"]
        # Answer first question
        ans_res = service.submit_answer(
            session_id=session_id,
            question_id="ecom_platform_target",
            question_text="Platforms?",
            answer_type="multiselect",
            answer_value=["Web (Desktop & Mobile Browser)"],
            is_confirmed=True
        )
        self.assertEqual(ans_res["status"], "in_progress")
        self.assertIn("next_question", ans_res)

        # Generate partial specification
        spec = service.generate_specification(session_id)
        self.assertEqual(spec["title"], "Test Ecom")
        self.assertEqual(len(spec["confirmed_decisions"]), 1)

    def test_multitier_memory_engine(self):
        mem = MemoryService()
        res = mem.add_memory(
            category="personal_preference",
            key="theme_mode",
            content="deep_obsidian",
            source="user"
        )
        self.assertEqual(res["status"], "stored")

        # Conflict detection test: update same key
        res2 = mem.add_memory(
            category="personal_preference",
            key="theme_mode",
            content="obsidian_purple_accent",
            source="user"
        )
        self.assertTrue(res2["conflict_resolved"])
        self.assertEqual(res2["prior_content"], "deep_obsidian")

        # Retrieve active memories
        active = mem.list_memories(category="personal_preference")
        keys = [m["key"] for m in active if m["content"] == "obsidian_purple_accent"]
        self.assertIn("theme_mode", keys)

    def test_mock_ai_provider(self):
        async def _test():
            provider = MockAIProvider()
            hw = await provider.detect_hardware()
            self.assertEqual(hw["has_nvidia_gpu"], False)
            self.assertIn("Intel", hw["gpu_name"])

            models = await provider.list_models()
            self.assertGreater(len(models), 0)

            resp = await provider.generate_response([{"role": "user", "content": "Help me build a store"}])
            self.assertIn("e-commerce", resp["reply"].lower())

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
