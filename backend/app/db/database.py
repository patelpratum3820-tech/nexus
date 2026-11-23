"""
SQLite Database manager with WAL mode and transaction safety for NEXUS.
"""
import sqlite3
from typing import Generator
from contextlib import contextmanager
from app.core.config import SQLITE_DB_PATH


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(SQLITE_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency and resilience on SSD
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def init_db() -> None:
    """Initialize schema tables if they do not exist."""
    with get_db_cursor() as cursor:
        # Projects table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'planning', -- planning, active, paused, completed
            spec_json TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Discovery Sessions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovery_sessions (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            title TEXT NOT NULL,
            initial_prompt TEXT,
            status TEXT DEFAULT 'in_progress', -- in_progress, completed, archived
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """)

        # Discovery Answers table (Adaptive Q&A)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovery_answers (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            answer_type TEXT NOT NULL, -- choice, multiselect, text, skip
            answer_value TEXT NOT NULL,
            is_confirmed INTEGER DEFAULT 0, -- 0 = assumption, 1 = confirmed decision
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES discovery_sessions(id) ON DELETE CASCADE
        );
        """)

        # Multi-tier Memory Store
        # Categories: personal_preference, project_decision, conversation_context, technical_spec, task_history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            project_id TEXT,
            key TEXT NOT NULL,
            content TEXT NOT NULL,
            source TEXT DEFAULT 'user', -- user, discovery_engine, system
            confidence REAL DEFAULT 1.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        """)

        # Resource Event Audit Log (Low-frequency, circular/retained)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resource_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            cpu_percent REAL,
            ram_used_gb REAL,
            ram_total_gb REAL,
            active_workers INTEGER DEFAULT 0,
            event_type TEXT DEFAULT 'heartbeat'
        );
        """)
