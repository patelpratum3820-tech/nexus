# Contributing to NEXUS

Thank you for your interest in contributing to NEXUS.

NEXUS is a local-first AI desktop workspace built with Python (FastAPI), TypeScript (Electron), and React. Because NEXUS interacts directly with local hardware and model runtimes, all contributions must respect our safety and resource management invariants.

---

## Architecture Principles to Respect

1. **Hardware Safety**: Never weaken the admission boundaries ($2.0\text{ GB}$ minimum available RAM, $80\%$ maximum CPU load).
2. **Process Ownership**: Never terminate or manipulate external system processes or independent Ollama daemons.
3. **Local Loopback Perimeter**: All backend services must strictly bind to `127.0.0.1`. Do not introduce external telemetry or remote network dependencies.
4. **Single Active Model Invariant**: Only one local LLM should be loaded into RAM at any given time on constrained hardware.

---

## Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Ollama (installed locally on `127.0.0.1:11434` with `gemma3:1b`)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Frontend & Desktop Setup
```bash
# Frontend
cd frontend
npm install

# Desktop (Electron)
cd ../desktop
npm install
```

---

## Running Verification Suites

Before opening a pull request, ensure all test suites pass without warnings:

```bash
# Run all backend unit & integration tests
python -m unittest discover -s backend/tests -p "test_*.py"

# Build frontend production bundle
npm --prefix frontend run build

# Build Electron TypeScript bundle
npm --prefix desktop run build
```

---

## Pull Request Guidelines

- Branch naming: `feature/<feature-name>` or `fix/<fix-name>`.
- Commit messages: Use conventional commits (e.g., `feat:`, `fix:`, `docs:`, `test:`).
- Document new endpoints in `docs/API_REFERENCE.md`.
- Ensure new tests accompany any behavioral changes.
