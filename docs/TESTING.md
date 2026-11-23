# Verification & Testing Strategy

NEXUS enforces a multi-layered verification strategy combining automated unit tests, regression suites, and live hardware profiling.

---

## 1. Test Suite Summary

Latest execution status: **42 / 42 passed (100%)**

| Test Module | Coverage Scope | Test Count | Status |
| :--- | :--- | :---: | :---: |
| `backend/tests/test_core.py` | SQLite DB init, migrations, memory storage, project CRUD | 3 | Passing |
| `backend/tests/test_concurrency_rules.py` | Single-model residence, Phi-4 gate, reserve constants | 3 | Passing |
| `backend/tests/test_api_endpoints.py` | FastAPI REST endpoints, discovery lifecycle, resource APIs | 9 | Passing |
| `backend/tests/test_phase1_6_fixes.py` | Window close lifecycle simulator, settings DB persistence, type annotations | 5 | Passing |
| `backend/tests/test_phase1_7_consistency.py` | Process ownership isolation, hard safety boundary clamping | 7 | Passing |
| `backend/tests/test_phase2_2_discovery.py` | Local Ollama version parsing, model tag discovery, role mapping, mock fallback | 9 | Passing |
| `backend/tests/test_phase2_3_streaming.py` | SSE progressive streaming, cancellation on disconnect, resource admission gate | 6 | Passing |

---

## 2. Running Automated Tests

To execute the complete backend automated test suite:

```bash
# From repository root
python -m unittest discover -s backend/tests -p "test_*.py"
```

To run frontend and Electron production builds:

```bash
# Verify React 19 TypeScript compilation and Vite packaging
npm --prefix frontend run build

# Verify Electron TypeScript compilation
npm --prefix desktop run build
```

---

## 3. Testing Levels & Limitations

| Level | Verification Scope | Current Evidence |
| :--- | :--- | :--- |
| **Unit Tests** | Function-level logic, boundaries, math, and contracts | 42 passing tests in $1.65\text{ s}$ |
| **Mocked Integration** | HTTP mock streams, JSON chunking, and simulated cancellations | Verified via `unittest.mock` |
| **Live Local AI** | Real Ollama daemon on localhost, real token inference | Verified: $32.5\text{ tok/s}$ on `gemma3:1b` |
| **Production Build** | Static bundle packaging, minification, tree-shaking | Verified: 0 compiler/linter errors |
| **Real-World Deployment** | Packaging into NSIS / MSI installer on clean machines | *Pending future packaging phase* |
