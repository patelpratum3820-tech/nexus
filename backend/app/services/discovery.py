"""
NEXUS Adaptive Project Discovery Engine.
Provides question decision graphs, dynamic adaptive questioning,
and specification generation based on confirmed user answers.
"""
import uuid
import json
from typing import Dict, List, Any, Optional
from app.db.database import get_db_cursor


DEFAULT_DISCOVERY_FLOWS = {
    "ecommerce": [
        {
            "id": "ecom_platform_target",
            "text": "What platforms are you targeting for this e-commerce project?",
            "type": "multiselect",
            "options": ["Web (Desktop & Mobile Browser)", "Mobile App (iOS & Android)", "Progressive Web App (PWA)"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "architecture"
        },
        {
            "id": "ecom_catalog_size",
            "text": "Approximately how many products will your initial catalog feature?",
            "type": "choice",
            "options": ["Small boutique (< 50 items)", "Medium store (50 - 1,000 items)", "Large marketplace (1,000+ items)"],
            "allow_custom": False,
            "allow_not_sure": True,
            "category": "scope"
        },
        {
            "id": "ecom_payment_gateways",
            "text": "Which payment providers or gateways do you need to support?",
            "type": "multiselect",
            "options": ["Stripe / Credit Cards", "PayPal", "Apple Pay / Google Pay", "Cash on Delivery", "Cryptocurrency"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "integrations"
        },
        {
            "id": "ecom_user_accounts",
            "text": "Do customers need user accounts to purchase, or should guest checkout be supported?",
            "type": "choice",
            "options": ["Guest checkout allowed & optional accounts", "Mandatory user registration", "Social login only (Google / Apple)"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "features"
        },
        {
            "id": "ecom_tech_preference",
            "text": "Do you have an existing tech stack preference, or should NEXUS recommend one?",
            "type": "choice",
            "options": ["Recommend the optimal lightweight stack", "Next.js / React + Node.js", "Python (FastAPI / Django)", "Shopify / Headless Shopify"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "technical"
        }
    ],
    "general_software": [
        {
            "id": "gen_project_type",
            "text": "What type of software are you looking to create?",
            "type": "choice",
            "options": ["Web Application", "Desktop Application", "Mobile App", "CLI Tool / API Service", "Automation Script"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "architecture"
        },
        {
            "id": "gen_primary_audience",
            "text": "Who is the primary audience or user for this tool?",
            "type": "choice",
            "options": ["Personal use / Internal team", "B2B / Enterprise clients", "B2C / General public", "Open-source community"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "scope"
        },
        {
            "id": "gen_data_storage",
            "text": "How should data be stored and managed?",
            "type": "choice",
            "options": ["Local-first (SQLite / Local files)", "Cloud database (PostgreSQL / Supabase)", "No database / Stateless"],
            "allow_custom": True,
            "allow_not_sure": True,
            "category": "technical"
        }
    ]
}


class DiscoveryService:
    def __init__(self):
        pass

    def start_session(self, title: str, initial_prompt: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discovery session and generate initial adaptive questions."""
        session_id = f"disc_{uuid.uuid4().hex[:8]}"

        with get_db_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO discovery_sessions (id, project_id, title, initial_prompt, status)
                VALUES (?, ?, ?, ?, 'in_progress')
                """,
                (session_id, project_id, title, initial_prompt)
            )

        # Detect topic
        lower_prompt = initial_prompt.lower()
        if any(w in lower_prompt for w in ["shop", "store", "commerce", "cart", "product", "checkout"]):
            flow_key = "ecommerce"
        else:
            flow_key = "general_software"

        first_question = DEFAULT_DISCOVERY_FLOWS[flow_key][0]
        return {
            "session_id": session_id,
            "title": title,
            "initial_prompt": initial_prompt,
            "flow_type": flow_key,
            "total_questions_estimated": len(DEFAULT_DISCOVERY_FLOWS[flow_key]),
            "current_question": first_question,
            "status": "in_progress"
        }

    def submit_answer(
        self,
        session_id: str,
        question_id: str,
        question_text: str,
        answer_type: str,
        answer_value: Any,
        is_confirmed: bool = True
    ) -> Dict[str, Any]:
        """Record an answer and return the next adaptive question or completed spec."""
        answer_id = f"ans_{uuid.uuid4().hex[:8]}"
        val_str = json.dumps(answer_value) if not isinstance(answer_value, str) else answer_value

        with get_db_cursor() as cursor:
            # Upsert answer for this question in this session
            cursor.execute(
                """
                DELETE FROM discovery_answers WHERE session_id = ? AND question_id = ?
                """,
                (session_id, question_id)
            )
            cursor.execute(
                """
                INSERT INTO discovery_answers (id, session_id, question_id, question_text, answer_type, answer_value, is_confirmed)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (answer_id, session_id, question_id, question_text, answer_type, val_str, 1 if is_confirmed else 0)
            )

            # Retrieve session info
            cursor.execute("SELECT initial_prompt FROM discovery_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            initial_prompt = row["initial_prompt"] if row else ""

            # Check answered questions
            cursor.execute("SELECT question_id FROM discovery_answers WHERE session_id = ?", (session_id,))
            answered_ids = {r["question_id"] for r in cursor.fetchall()}

        # Pick flow
        lower_prompt = initial_prompt.lower()
        flow_key = "ecommerce" if any(w in lower_prompt for w in ["shop", "store", "commerce", "cart"]) else "general_software"
        flow = DEFAULT_DISCOVERY_FLOWS[flow_key]

        next_q = None
        for q in flow:
            if q["id"] not in answered_ids:
                next_q = q
                break

        if next_q is not None:
            return {
                "session_id": session_id,
                "status": "in_progress",
                "next_question": next_q,
                "answered_count": len(answered_ids),
                "total_questions": len(flow)
            }

        # All questions answered -> Generate Specification
        spec = self.generate_specification(session_id)
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE discovery_sessions SET status = 'completed' WHERE id = ?", (session_id,))

        return {
            "session_id": session_id,
            "status": "completed",
            "specification": spec
        }

    def generate_specification(self, session_id: str) -> Dict[str, Any]:
        """Compile confirmed decisions and assumptions into a structured specification."""
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM discovery_sessions WHERE id = ?", (session_id,))
            session = cursor.fetchone()
            if not session:
                return {}

            cursor.execute("SELECT * FROM discovery_answers WHERE session_id = ?", (session_id,))
            answers = cursor.fetchall()

        confirmed_decisions = []
        assumptions = []

        for a in answers:
            try:
                val = json.loads(a["answer_value"])
            except Exception:
                val = a["answer_value"]

            item = {
                "question": a["question_text"],
                "decision": val,
                "type": a["answer_type"]
            }
            if a["is_confirmed"]:
                confirmed_decisions.append(item)
            else:
                assumptions.append(item)

        spec = {
            "title": session["title"],
            "initial_goal": session["initial_prompt"],
            "confirmed_decisions": confirmed_decisions,
            "assumptions": assumptions,
            "recommended_architecture": {
                "frontend": "React / Next.js with Tailwind CSS",
                "backend": "Modular Python FastAPI or Node.js REST API",
                "database": "SQLite (Local Dev) / PostgreSQL (Production)",
                "state_management": "Lightweight event-driven stores"
            },
            "status": "pending_user_approval",
            "next_steps": [
                "Review specification and confirm remaining assumptions",
                "Click 'Approve Specification' to initialize project repository structure",
                "Generate architecture diagrams and component hierarchy"
            ]
        }
        return spec
