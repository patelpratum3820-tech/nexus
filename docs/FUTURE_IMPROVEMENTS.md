# Future Improvements & Research Roadmap

## 1. High-Priority Engineering Enhancements

- **Dynamic Model Switching (Phase 2.4):**
  Implement transparent eviction and loading to support seamless on-demand switching between `gemma3:1b` (general assistant) and `qwen2.5-coder:1.5b` (specialized programming assistant).
- **Explicit Phi-4 Confirmation Modal (Phase 2.4):**
  Implement an in-app confirmation dialog explaining memory impact before loading `phi4-mini:latest`.
- **Semantic Vector Storage & Retrieval (Phase 2.6):**
  Integrate `nomic-embed-text:latest` to extract 768-dimensional document and requirement embeddings, enabling semantic search and context injection without cloud dependencies.
- **Dynamic Context Length Tuning:**
  Automatically truncate or expand the local context window based on available RAM headroom.

---

## 2. Long-Term Exploratory Goals

- **Local Audio & Speech Interfaces:**
  Offline wake-word detection and local speech-to-text (e.g. Whisper.cpp) running on low-power background threads.
- **Local Network Mobile Sync:**
  Zero-cloud pairing with mobile devices on the same local Wi-Fi subnet for seamless notification delivery and companion status mirroring.
- **Standalone Distribution Packaging:**
  Automated multi-platform packaging via Electron Forge or NSIS, bundling runtime prerequisites.
