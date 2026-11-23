"""
NEXUS Multi-tier Memory Engine.
Manages separated tiers:
1. Personal Preferences
2. Project-Specific Memory
3. Temporary Conversation Context
4. Confirmed Decisions
5. Technical Documentation
6. Task History
Features conflict detection, source tracking, and strict project isolation.
"""
import uuid
import time
from typing import Dict, List, Any, Optional
from app.db.database import get_db_cursor


VALID_CATEGORIES = {
    "personal_preference",
    "project_decision",
    "conversation_context",
    "confirmed_decision",
    "technical_doc",
    "task_history"
}


class MemoryService:
    def __init__(self):
        pass

    def add_memory(
        self,
        category: str,
        key: str,
        content: str,
        project_id: Optional[str] = None,
        source: str = "user",
        confidence: float = 1.0
    ) -> Dict[str, Any]:
        """Store a new memory item with conflict detection."""
        if category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")

        mem_id = f"mem_{uuid.uuid4().hex[:8]}"

        with get_db_cursor() as cursor:
            # Conflict detection: check if same key exists in category for same project
            if project_id:
                cursor.execute(
                    "SELECT id, content FROM memories WHERE category = ? AND project_id = ? AND key = ? AND is_active = 1",
                    (category, project_id, key)
                )
            else:
                cursor.execute(
                    "SELECT id, content FROM memories WHERE category = ? AND project_id IS NULL AND key = ? AND is_active = 1",
                    (category, key)
                )
            existing = cursor.fetchone()
            conflict_detected = False
            prior_content = None

            if existing:
                conflict_detected = True
                prior_content = existing["content"]
                # Deactivate previous to maintain immutable history
                cursor.execute("UPDATE memories SET is_active = 0 WHERE id = ?", (existing["id"],))

            cursor.execute(
                """
                INSERT INTO memories (id, category, project_id, key, content, source, confidence, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (mem_id, category, project_id, key, content, source, confidence)
            )

        return {
            "id": mem_id,
            "category": category,
            "key": key,
            "content": content,
            "project_id": project_id,
            "source": source,
            "confidence": confidence,
            "conflict_resolved": conflict_detected,
            "prior_content": prior_content,
            "status": "stored"
        }

    def list_memories(
        self,
        category: Optional[str] = None,
        project_id: Optional[str] = None,
        query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query memories with optional filtering by category, project isolation, and text query."""
        sql = "SELECT * FROM memories WHERE is_active = 1"
        params: List[Any] = []

        if category:
            sql += " AND category = ?"
            params.append(category)

        if project_id is not None:
            sql += " AND project_id = ?"
            params.append(project_id)

        if query:
            sql += " AND (key LIKE ? OR content LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])

        sql += " ORDER BY updated_at DESC"

        with get_db_cursor() as cursor:
            cursor.execute(sql, tuple(params))
            rows = cursor.fetchall()

        return [dict(r) for r in rows]

    def update_memory(self, memory_id: str, new_content: str, confidence: float = 1.0) -> bool:
        """Update existing memory content."""
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                UPDATE memories
                SET content = ?, confidence = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND is_active = 1
                """,
                (new_content, confidence, memory_id)
            )
            return cursor.rowcount > 0

    def delete_memory(self, memory_id: str) -> bool:
        """Soft delete a memory record."""
        with get_db_cursor() as cursor:
            cursor.execute("UPDATE memories SET is_active = 0 WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0
