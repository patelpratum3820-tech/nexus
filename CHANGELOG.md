# Changelog

All notable changes to the NEXUS architecture and codebase are documented here.

## [Phase 2.3] - 2026-11-23
### Added
- Real-time token streaming using `gemma3:1b` over HTTP SSE (`/api/ai/stream`).
- Frontend chat integration with progressive markdown rendering via `useAIStream`.
- Async streaming client in `OllamaAIProvider.stream_response()`.
- Unit and integration tests in `test_phase2_3_streaming.py` (15 tests).

## [Phase 2.2] - 2026-11-23
### Added
- Local AI provider abstraction (`AIProvider`, `OllamaAIProvider`).
- Read-only model discovery against `http://127.0.0.1:11434/api/tags`.
- Pre-existing model tracking to protect unmanaged Ollama instances.
- Endpoints `/api/ai/status` and `/api/ai/models`.

## [Phase 2.1] - 2026-11-23
### Added
- Ollama preflight verification suite.
- Architecture decisions on single chat model residency and admission floors.

## [Phase 1.7] - 2026-11-23
### Changed
- Process ownership separation: NEXUS never sends termination signals to external Ollama instances.
- Enforced hard resource limits ($2.0\text{ GB}$ minimum RAM reserve, $80\%$ maximum CPU cap) that reject weaker user configurations.

## [Phase 1.6] - 2026-11-23
### Added
- Dual-window close lifecycle: main window hides to companion widget when companion is running.
- SQLite persistence for resource admission thresholds.
- Win32 memory measurement fallback routines.

## [Phase 1.0] - 2026-11-23
### Added
- Project initialization with Electron, React/TypeScript, and FastAPI backend.
- Baseline resource manager and admission gate.
