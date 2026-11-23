# NEXUS Feature Roadmap & Implementation Status

This document provides a strict, honest status classification of all features and architectural components within NEXUS.

---

## Status Classification Legend

- **IMPLEMENTED & VERIFIED**: Fully written, integrated into the UI/Electron/FastAPI runtime, and verified with live execution or tests.
- **IMPLEMENTED (TESTS ONLY)**: Backend or unit logic written and tested via automated test suites, pending UI wiring.
- **PARTIALLY IMPLEMENTED**: Basic foundations laid, partial workflows functional, pending remaining phases.
- **PLANNED**: Architecturally specified and scheduled for future milestones; no code exists yet.
- **DEPRECATED / OUT OF SCOPE**: Explicitly rejected or deferred to safeguard hardware stability.

---

## 1. Core Architecture & Runtime Lifecycle

| Feature | Status | Notes / Location |
| :--- | :--- | :--- |
| **Electron + Vite + React Frontend Shell** | **IMPLEMENTED & VERIFIED** | `desktop/src/main.ts`, `frontend/src/` |
| **FastAPI Local Backend** | **IMPLEMENTED & VERIFIED** | `backend/app/main.py` on `127.0.0.1:8000` |
| **Floating Companion Widget** | **IMPLEMENTED & VERIFIED** | Transparent overlay window toggled via tray or hotkeys |
| **Dual Window Lifecycle & Safe Close (H-1)** | **IMPLEMENTED & VERIFIED** | Closing main window hides to companion if companion enabled |
| **Clean Process Termination (Issue A)** | **IMPLEMENTED & VERIFIED** | `process_mgr.py` tracks child PIDs; never kills external Ollama |
| **Auto-Start with Windows** | **DEPRECATED / OUT OF SCOPE** | Disabled by design to preserve user boot time & memory |

---

## 2. Resource Management & Hardware Protection

| Feature | Status | Notes / Location |
| :--- | :--- | :--- |
| **Win32 & psutil CPU/RAM Telemetry** | **IMPLEMENTED & VERIFIED** | Real-time polling via `resource_mgr.py` |
| **Admission Control Safety Boundary** | **IMPLEMENTED & VERIFIED** | Hard minimum $\ge 2.0\text{ GB}$ RAM, max $\le 80\%$ CPU |
| **Task Admission Gate (`admit_task`)** | **IMPLEMENTED & VERIFIED** | Evaluates current load vs requirements before admitting tasks |
| **Persistent Limits in SQLite (M-1)** | **IMPLEMENTED & VERIFIED** | Persists to DB; rejects thresholds that weaken safety |
| **Antigravity IDE Detection & Priority** | **IMPLEMENTED & VERIFIED** | Detects active dev processes; backs off NEXUS workload |
| **Dynamic CPU Throttling / Schedulers** | **PLANNED** | Scheduled for Phase 3 (Process priority pinning) |

---

## 3. Local AI Inference & Provider Integration

| Feature | Status | Notes / Location |
| :--- | :--- | :--- |
| **Ollama Local Provider Discovery** | **IMPLEMENTED & VERIFIED** | Discovers installed models via `127.0.0.1:11434/api/tags` |
| **Ollama Model Pre-existence Tracking** | **IMPLEMENTED & VERIFIED** | Records pre-running models; prevents unloading external workloads |
| **Gemma 3:1B Streaming Inference** | **IMPLEMENTED & VERIFIED** | Live token streaming via SSE at `/api/ai/stream` |
| **Frontend SSE Stream Integration** | **IMPLEMENTED & VERIFIED** | `useAIStream` hook renders streaming tokens in chat UI |
| **Qwen 2.5 Coder 1.5B (Coding Role)** | **PLANNED** | Scheduled for Phase 2.4 |
| **Phi-4-mini (Explicit Confirmation)** | **PLANNED** | Scheduled for Phase 2.5 (High RAM usage gate) |
| **Nomic Embed Text (Embeddings)** | **PLANNED** | Scheduled for Phase 2.6 (Vector memory integration) |
| **Multi-Model Concurrency** | **DEPRECATED / OUT OF SCOPE** | Explicitly blocked on 16GB shared-memory hardware |

---

## 4. UI & User Experience

| Feature | Status | Notes / Location |
| :--- | :--- | :--- |
| **Local Chat Interface** | **IMPLEMENTED & VERIFIED** | Real-time markdown, streaming text, model badge |
| **Live Hardware Metrics Gauge** | **IMPLEMENTED & VERIFIED** | RAM & CPU percentage indicators in desktop header |
| **Resource Settings Panel** | **IMPLEMENTED & VERIFIED** | Configures and validates admission boundaries |
| **Companion Quick AI Prompting** | **PARTIALLY IMPLEMENTED** | Companion window functional; streaming prompt wiring in progress |
| **Voice / Audio Capture** | **PLANNED** | Future post-Phase 3 milestone |
| **Offline Vector Document Search (RAG)** | **PLANNED** | Scheduled for Phase 4 |

---

## 5. Completed vs Upcoming Phases

- [x] **Phase 1**: Core Scaffold, Dual-Window Electron Shell, Resource Manager Baseline.
- [x] **Phase 1.5**: Comprehensive Runtime & Safety Audit.
- [x] **Phase 1.6**: Close Behavior, SQLite Resource Limits Persistence, Win32 Error Fallbacks.
- [x] **Phase 1.7**: Process Ownership Guardrails & Resource Safety Floor Verification.
- [x] **Phase 2.1**: Ollama Integration Preflight & Model Inventory Audit.
- [x] **Phase 2.2**: Local Provider Abstraction & Safe Model Discovery.
- [x] **Phase 2.3**: Real Gemma 3:1B Streaming AI Integration & SSE API.
- [ ] **Phase 2.4**: Role-Based Model Switching (Gemma 3 $\leftrightarrow$ Qwen 2.5 Coder).
- [ ] **Phase 2.5**: Phi-4-mini Safety Dialog & Confirmation Gate.
- [ ] **Phase 2.6**: Nomic Embeddings & Local Vector Store Integration.
- [ ] **Phase 3**: Dynamic Task Scheduling & CPU Pinning.
- [ ] **Phase 4**: Local Document Context & RAG Workflows.
