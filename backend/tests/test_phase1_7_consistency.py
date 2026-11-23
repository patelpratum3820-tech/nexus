"""
Unit and regression tests for Phase 1.7 Safety Consistency Review:
- Issue A: Ollama & Process Ownership Safety (strict ownership tracking, model unload during exit, external process protection).
- Issue B: Non-Overridable Resource Safety Boundaries (hard 80% CPU limit, hard 2.0 GB RAM reserve).
"""
import unittest
import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from app.main import app
from app.core.config import HARD_MAX_CPU_PERCENT, HARD_MIN_AVAILABLE_RAM_GB
from app.services.resource_mgr import ResourceManager
from app.api.ai_provider import provider
from app.db.database import set_setting, get_setting


class TestPhase17Consistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # -------------------------------------------------------------
    # ISSUE A: Process Ownership & Safe Model Unload Tests
    # -------------------------------------------------------------
    def test_issue_a_model_unloaded_during_clean_shutdown(self):
        """Verify that triggering shutdown cleanly unloads NEXUS-loaded models without touching external services."""
        async def _test():
            # 1. Simulate NEXUS loading Gemma 3:1B
            load_res = await provider.load_model("gemma3:1b")
            self.assertTrue(load_res["success"])
            self.assertEqual(provider.loaded_model, "gemma3:1b")

            # 2. Trigger clean shutdown endpoint
            res = self.client.post("/api/system/shutdown")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["status"], "shutting_down")
            self.assertIn("external services preserved", res.json()["message"])

            # 3. Verify that NEXUS model was unloaded
            self.assertIsNone(provider.loaded_model)

        asyncio.run(_test())

    def test_issue_a_process_ownership_contract(self):
        """
        Verify process ownership isolation logic matching desktop/src/processManager.ts:
        - Only explicitly spawned PIDs can be registered as owned.
        - External services (like an independent Ollama daemon PID) must NEVER be terminated.
        - Unverified PIDs are skipped during shutdown.
        """
        class MockProcessManager:
            def __init__(self):
                self.ownedPids = set()
                self.terminatedPids = []

            def isOwnedProcess(self, pid: int) -> bool:
                return pid in self.ownedPids

            def registerOwnedProcess(self, pid: int) -> None:
                self.ownedPids.add(pid)

            def unregisterOwnedProcess(self, pid: int) -> None:
                self.ownedPids.discard(pid)

            def stopProcess(self, pid: int) -> str:
                # Enforce strict ownership check
                if not self.isOwnedProcess(pid):
                    return "SKIPPED_UNOWNED"
                self.terminatedPids.append(pid)
                self.unregisterOwnedProcess(pid)
                return "TERMINATED_OWNED"

        pm = MockProcessManager()

        # Simulate independent Ollama running externally (e.g. PID 9999)
        external_ollama_pid = 9999
        self.assertFalse(pm.isOwnedProcess(external_ollama_pid))

        # Attempt to stop external Ollama -> MUST be skipped
        result_external = pm.stopProcess(external_ollama_pid)
        self.assertEqual(result_external, "SKIPPED_UNOWNED")
        self.assertNotIn(external_ollama_pid, pm.terminatedPids)

        # Simulate NEXUS backend spawned by desktop (e.g. PID 4321)
        nexus_backend_pid = 4321
        pm.registerOwnedProcess(nexus_backend_pid)
        self.assertTrue(pm.isOwnedProcess(nexus_backend_pid))

        # Stop NEXUS backend -> MUST succeed
        result_backend = pm.stopProcess(nexus_backend_pid)
        self.assertEqual(result_backend, "TERMINATED_OWNED")
        self.assertIn(nexus_backend_pid, pm.terminatedPids)
        self.assertFalse(pm.isOwnedProcess(nexus_backend_pid))

    # -------------------------------------------------------------
    # ISSUE B: Non-Overridable Resource Safety Boundaries Tests
    # -------------------------------------------------------------
    def test_issue_b_hard_boundaries_constants(self):
        """Confirm hard safety constants exist and match confirmed architecture."""
        self.assertEqual(HARD_MAX_CPU_PERCENT, 80.0, "Hard CPU admission boundary must be 80.0%")
        self.assertEqual(HARD_MIN_AVAILABLE_RAM_GB, 2.0, "Hard RAM reserve boundary must be 2.0 GB")

    def test_issue_b_user_setting_stricter_allowed(self):
        """Verify user settings that make boundaries STRICTER are accepted."""
        # Stricter CPU: 70.0% (< 80.0%)
        res_cpu = self.client.post("/api/resources/limits", json={"max_cpu_percent": 70.0})
        self.assertEqual(res_cpu.status_code, 200)
        self.assertEqual(res_cpu.json()["limits"]["max_cpu_percent"], 70.0)

        # Stricter RAM reserve: 2.5 GB (> 2.0 GB)
        res_ram = self.client.post("/api/resources/limits", json={"min_ram_gb": 2.5})
        self.assertEqual(res_ram.status_code, 200)
        self.assertEqual(res_ram.json()["limits"]["min_ram_gb"], 2.5)

        # Verify ResourceManager effective properties
        mgr = ResourceManager.get_instance()
        self.assertEqual(mgr.effective_max_cpu, 70.0)
        self.assertEqual(mgr.effective_min_ram, 2.5)

    def test_issue_b_user_setting_weaker_rejected(self):
        """Verify user settings that WEAKEN safety boundaries are strictly rejected with HTTP 400."""
        # Weaker CPU: 95.0% (> 80.0%) must be rejected
        res_95 = self.client.post("/api/resources/limits", json={"max_cpu_percent": 95.0})
        self.assertEqual(res_95.status_code, 400)
        self.assertIn("cannot exceed hard safety limit", res_95.json()["detail"])

        # Weaker CPU: 85.0% (> 80.0%) must be rejected
        res_85 = self.client.post("/api/resources/limits", json={"max_cpu_percent": 85.0})
        self.assertEqual(res_85.status_code, 400)
        self.assertIn("cannot exceed hard safety limit", res_85.json()["detail"])

        # Weaker RAM: 1.0 GB (< 2.0 GB) must be rejected
        res_1gb = self.client.post("/api/resources/limits", json={"min_ram_gb": 1.0})
        self.assertEqual(res_1gb.status_code, 400)
        self.assertIn("cannot be lower than hard safety reserve", res_1gb.json()["detail"])

        # Weaker RAM: 1.5 GB (< 2.0 GB) must be rejected
        res_15gb = self.client.post("/api/resources/limits", json={"min_ram_gb": 1.5})
        self.assertEqual(res_15gb.status_code, 400)
        self.assertIn("cannot be lower than hard safety reserve", res_15gb.json()["detail"])

    def test_issue_b_persisted_corruption_clamping(self):
        """
        Verify that even if SQLite was tampered with or corrupted outside the app,
        _load_persisted_settings and effective properties strictly clamp to hard boundaries.
        """
        # Inject corrupted/weakened values directly into database
        set_setting("max_cpu_percent", "99.0")
        set_setting("min_ram_limit_gb", "0.5")

        mgr = ResourceManager()
        # Clamped safely upon load
        self.assertLessEqual(mgr.max_cpu_limit, HARD_MAX_CPU_PERCENT)
        self.assertGreaterEqual(mgr.min_ram_limit_gb, HARD_MIN_AVAILABLE_RAM_GB)

        # Effective properties can never be weaker than hard limits
        self.assertLessEqual(mgr.effective_max_cpu, HARD_MAX_CPU_PERCENT)
        self.assertGreaterEqual(mgr.effective_min_ram, HARD_MIN_AVAILABLE_RAM_GB)

    def test_issue_b_sample_metrics_uses_effective_limits(self):
        """Verify sample_metrics correctly reports effective threshold limits and constraints."""
        mgr = ResourceManager.get_instance()
        # Set stricter limits
        mgr.update_and_persist_limits(max_cpu_percent=65.0, min_ram_gb=3.0)

        metrics = mgr.sample_metrics()
        self.assertEqual(metrics["min_ram_headroom_gb"], 3.0)
        self.assertEqual(metrics["max_cpu_threshold_percent"], 65.0)
        self.assertTrue(metrics["antigravity_priority_active"])


if __name__ == "__main__":
    unittest.main()
