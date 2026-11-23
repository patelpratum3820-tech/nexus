"""
Configuration module for NEXUS Local-First AI OS.
Safe defaults, no auto-startup, strictly local file boundaries.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SQLITE_DB_PATH = DATA_DIR / "nexus.db"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765

# Resource Management Defaults
RESOURCE_SAMPLE_INTERVAL_SEC = 5.0
RESOURCE_IDLE_SAMPLE_INTERVAL_SEC = 15.0
MAX_SAFE_CPU_PERCENT = 80.0
MIN_SAFE_AVAILABLE_RAM_GB = 2.0

# Antigravity & OS Priority Constraints
ANTIGRAVITY_PRIORITY_RESERVE_RAM_GB = 2.0
SINGLE_MODEL_RESIDENCE_ONLY = True
ALLOW_EMBEDDING_CONCURRENCY = False

# Safe environment settings
ALLOW_BACKGROUND_INDEXING = False
AUTO_START_LOCAL_MODELS = False
ENABLE_AUTO_STARTUP = False

# Confirmed Model Role Assignments (Approved by Concurrency Benchmark)
MODEL_ROLES = {
    "default_assistant": "gemma3:1b",
    "coding_assistant": "qwen2.5-coder:1.5b",
    "restricted_reasoning": "phi4-mini:latest",
    "memory_embeddings": "nomic-embed-text:latest",
    "optional": "qwen3:1.7b"
}
