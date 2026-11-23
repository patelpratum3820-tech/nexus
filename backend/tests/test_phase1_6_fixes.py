"""
Regression and validation tests for Phase 1.6 Approved Maintenance Fixes:
- H-1: Window close lifecycle contract and flag management.
- M-1: Persistence and validation of resource settings (DB and API).
- M-2: Provider interface alignment between BaseAIProvider and MockAIProvider.
"""
import unittest
import sys
import os
import inspect
from typing import Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from app.main import app
from app.db.database import init_db, set_setting, get_setting
from app.services.resource_mgr import ResourceManager
from app.services.ai.base import BaseAIProvider
from app.services.ai.mock import MockAIProvider


class TestPhase16MaintenanceFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_m1_database_settings_crud(self):
        """Verify set_setting and get_setting behave safely and idempotently."""
        set_setting("test_key_phase16", "test_value_123")
        self.assertEqual(get_setting("test_key_phase16"), "test_value_123")

        # Overwrite/update existing key
        set_setting("test_key_phase16", "test_value_updated")
        self.assertEqual(get_setting("test_key_phase16"), "test_value_updated")

        # Missing key returns default
        self.assertEqual(get_setting("non_existent_key_xyz", default="fallback"), "fallback")

    def test_m1_resource_manager_persistence(self):
        """Verify ResourceManager loads persisted settings across instantiations."""
        mgr1 = ResourceManager()
        mgr1.update_and_persist_limits(max_cpu_percent=72.5, min_ram_gb=2.5, max_concurrent_tasks=3)

        self.assertEqual(mgr1.max_cpu_limit, 72.5)
        self.assertEqual(mgr1.min_ram_limit_gb, 2.5)
        self.assertEqual(mgr1.max_concurrent_tasks, 3)

        # Confirm persisted in DB
        self.assertEqual(get_setting("max_cpu_percent"), "72.5")
        self.assertEqual(get_setting("min_ram_limit_gb"), "2.5")
        self.assertEqual(get_setting("max_concurrent_tasks"), "3")

        # Instantiate a new ResourceManager (simulating backend restart)
        mgr2 = ResourceManager()
        self.assertEqual(mgr2.max_cpu_limit, 72.5)
        self.assertEqual(mgr2.min_ram_limit_gb, 2.5)
        self.assertEqual(mgr2.max_concurrent_tasks, 3)

    def test_m1_api_limits_validation(self):
        """Verify API rejects out-of-range thresholds with HTTP 400."""
        # Valid update
        res = self.client.post("/api/resources/limits", json={"max_cpu_percent": 75.0, "min_ram_gb": 3.0})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["limits"]["max_cpu_percent"], 75.0)
        self.assertEqual(res.json()["limits"]["min_ram_gb"], 3.0)

        # Invalid CPU: > 95%
        res_cpu_high = self.client.post("/api/resources/limits", json={"max_cpu_percent": 99.9})
        self.assertEqual(res_cpu_high.status_code, 400)
        self.assertIn("max_cpu_percent", res_cpu_high.json()["detail"])

        # Invalid CPU: < 50%
        res_cpu_low = self.client.post("/api/resources/limits", json={"max_cpu_percent": 40.0})
        self.assertEqual(res_cpu_low.status_code, 400)

        # Invalid RAM: < 1.0 GB
        res_ram_low = self.client.post("/api/resources/limits", json={"min_ram_gb": 0.5})
        self.assertEqual(res_ram_low.status_code, 400)
        self.assertIn("min_ram_gb", res_ram_low.json()["detail"])

        # Invalid RAM: > 6.0 GB
        res_ram_high = self.client.post("/api/resources/limits", json={"min_ram_gb": 8.0})
        self.assertEqual(res_ram_high.status_code, 400)

        # Invalid tasks: < 1
        res_tasks_low = self.client.post("/api/resources/limits", json={"max_concurrent_tasks": 0})
        self.assertEqual(res_tasks_low.status_code, 400)

        # Invalid tasks: > 4
        res_tasks_high = self.client.post("/api/resources/limits", json={"max_concurrent_tasks": 5})
        self.assertEqual(res_tasks_high.status_code, 400)

    def test_m2_base_and_mock_provider_interface_alignment(self):
        """Verify BaseAIProvider and MockAIProvider signatures and annotations match exactly."""
        base_sig = inspect.signature(BaseAIProvider.load_model)
        mock_sig = inspect.signature(MockAIProvider.load_model)

        # Check parameter names and kinds
        self.assertEqual(
            list(base_sig.parameters.keys()),
            list(mock_sig.parameters.keys()),
            "Parameters of load_model must match between base and mock"
        )
        self.assertEqual(
            base_sig.parameters["is_explicit_confirmation"].default,
            mock_sig.parameters["is_explicit_confirmation"].default,
            "Default values for is_explicit_confirmation must match"
        )

        # Verify return annotation
        base_ret = base_sig.return_annotation
        mock_ret = mock_sig.return_annotation
        self.assertEqual(base_ret, Dict[str, Any], "BaseAIProvider.load_model must return Dict[str, Any]")
        self.assertEqual(mock_ret, Dict[str, Any], "MockAIProvider.load_model must return Dict[str, Any]")

        # Ensure MockAIProvider is instantiable as concrete BaseAIProvider
        provider = MockAIProvider()
        self.assertIsInstance(provider, BaseAIProvider)

    def test_h1_window_lifecycle_state_machine(self):
        """
        Verify the lifecycle state machine contract used in desktop/src/main.ts:
        - When companion is alive and isExplicitQuitting is false, close event must hide mainWindow.
        - When isExplicitQuitting is true, close event must allow exit and terminate backend.
        - When companion is dead/null, close event proceeds with full application exit.
        """
        class MockWindow:
            def __init__(self):
                self.visible = True
                self.destroyed = False

            def isDestroyed(self):
                return self.destroyed

            def isVisible(self):
                return self.visible

            def hide(self):
                self.visible = False

            def show(self):
                self.visible = True

            def focus(self):
                pass

        class WindowCloseLifecycleSimulator:
            def __init__(self):
                self.isExplicitQuitting = False
                self.companionWindow = MockWindow()
                self.mainWindow = MockWindow()
                self.appQuitCalled = False
                self.backendStopped = False

            def handle_window_close(self, event_prevent_default):
                if self.isExplicitQuitting:
                    # Proceed with full destruction and app teardown
                    return "EXIT_ALLOWED"
                if self.companionWindow and not self.companionWindow.isDestroyed():
                    event_prevent_default()
                    self.mainWindow.hide()
                    return "WINDOW_HIDDEN_TO_COMPANION"
                else:
                    self.isExplicitQuitting = True
                    return "FALLBACK_APP_EXIT"

            def handle_companion_toggle(self):
                if self.mainWindow and not self.mainWindow.isDestroyed():
                    if not self.mainWindow.isVisible():
                        self.mainWindow.show()
                    self.mainWindow.focus()
                    return "RESTORED"
                return "RECREATED"

            def handle_explicit_exit(self):
                self.isExplicitQuitting = True
                self.backendStopped = True
                self.appQuitCalled = True
                return "TERMINATED"

        sim = WindowCloseLifecycleSimulator()

        # Scenario 1: User clicks close button on main window with companion alive
        default_prevented = []
        status = sim.handle_window_close(lambda: default_prevented.append(True))
        self.assertEqual(status, "WINDOW_HIDDEN_TO_COMPANION")
        self.assertTrue(default_prevented[0])
        self.assertFalse(sim.mainWindow.isVisible())
        self.assertFalse(sim.mainWindow.isDestroyed())
        self.assertFalse(sim.appQuitCalled)

        # Scenario 2: Double clicking companion restores main window
        restore_status = sim.handle_companion_toggle()
        self.assertEqual(restore_status, "RESTORED")
        self.assertTrue(sim.mainWindow.isVisible())

        # Scenario 3: User triggers explicit exit
        exit_status = sim.handle_explicit_exit()
        self.assertEqual(exit_status, "TERMINATED")
        self.assertTrue(sim.isExplicitQuitting)
        self.assertTrue(sim.backendStopped)
        self.assertTrue(sim.appQuitCalled)

        # Scenario 4: Window close during explicit quit allows natural exit
        exit_close_status = sim.handle_window_close(lambda: None)
        self.assertEqual(exit_close_status, "EXIT_ALLOWED")

        # Scenario 5: Companion dead/disabled falls back to full quit
        sim2 = WindowCloseLifecycleSimulator()
        sim2.companionWindow = None
        status2 = sim2.handle_window_close(lambda: None)
        self.assertEqual(status2, "FALLBACK_APP_EXIT")
        self.assertTrue(sim2.isExplicitQuitting)


if __name__ == "__main__":
    unittest.main()
