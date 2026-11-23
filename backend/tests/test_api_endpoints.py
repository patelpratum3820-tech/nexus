"""
End-to-End API Integration Tests for NEXUS FastAPI Backend.
Uses FastAPI TestClient to verify all REST endpoints in isolation.
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from starlette.testclient import TestClient
from app.main import app
from app.db.database import init_db


class TestAPIEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.client = TestClient(app)

    def test_root_and_health(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "NEXUS Core")

        health = self.client.get("/api/system/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "healthy")

    def test_resources_endpoints(self):
        metrics = self.client.get("/api/resources/metrics")
        self.assertEqual(metrics.status_code, 200)
        data = metrics.json()
        self.assertIn("cpu_percent", data)
        self.assertIn("ram_available_gb", data)
        self.assertIn("status", data)

        limits = self.client.get("/api/resources/limits")
        self.assertEqual(limits.status_code, 200)

        # Update limits
        update = self.client.post("/api/resources/limits", json={"max_cpu_percent": 80.0})
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["limits"]["max_cpu_percent"], 80.0)

    def test_discovery_flow(self):
        # 1. Start session
        start = self.client.post(
            "/api/discovery/start",
            json={"title": "Store App", "initial_prompt": "I want to build an e-commerce store"}
        )
        self.assertEqual(start.status_code, 200)
        session = start.json()
        session_id = session["session_id"]
        q = session["current_question"]
        self.assertIsNotNone(q)

        # 2. Answer question
        ans = self.client.post(
            "/api/discovery/answer",
            json={
                "session_id": session_id,
                "question_id": q["id"],
                "question_text": q["text"],
                "answer_type": q["type"],
                "answer_value": ["Web (Desktop & Mobile Browser)"],
                "is_confirmed": True
            }
        )
        self.assertEqual(ans.status_code, 200)

        # 3. Check partial spec
        spec = self.client.get(f"/api/discovery/spec/{session_id}")
        self.assertEqual(spec.status_code, 200)
        self.assertEqual(spec.json()["title"], "Store App")

    def test_memory_crud(self):
        # Add memory
        add_res = self.client.post(
            "/api/memory/add",
            json={
                "category": "technical_doc",
                "key": "framework_choice",
                "content": "React 19 with Tailwind CSS",
                "source": "architect"
            }
        )
        self.assertEqual(add_res.status_code, 200)
        mem_id = add_res.json()["id"]

        # List memories
        list_res = self.client.get("/api/memory/list?category=technical_doc")
        self.assertEqual(list_res.status_code, 200)
        items = list_res.json()
        self.assertTrue(any(i["id"] == mem_id for i in items))

        # Delete memory
        del_res = self.client.delete(f"/api/memory/{mem_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_projects_crud_and_approval(self):
        # Create project
        create = self.client.post(
            "/api/projects/create",
            json={"name": "Alpha Project", "description": "Phase 1 test project"}
        )
        self.assertEqual(create.status_code, 200)
        proj_id = create.json()["id"]

        # Approve project
        approve = self.client.post(f"/api/projects/{proj_id}/approve")
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.json()["new_state"], "active")

    def test_ai_provider_simulation(self):
        # Hardware inspect
        hw = self.client.get("/api/ai/hardware")
        self.assertEqual(hw.status_code, 200)
        self.assertFalse(hw.json()["has_nvidia_gpu"])

        # Models catalog
        models = self.client.get("/api/ai/models")
        self.assertEqual(models.status_code, 200)
        self.assertGreater(len(models.json()), 0)

        # Chat
        chat = self.client.post(
            "/api/ai/chat",
            json={"messages": [{"role": "user", "content": "What is NEXUS?"}]}
        )
        self.assertEqual(chat.status_code, 200)
        self.assertIn("NEXUS", chat.json()["reply"])


if __name__ == "__main__":
    unittest.main()
