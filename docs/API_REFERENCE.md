# NEXUS Core API Reference

The NEXUS backend exposes a REST and Server-Sent Events (SSE) API on `http://127.0.0.1:8765`.

---

## 1. AI Provider Endpoints (`/api/ai`)

### `GET /api/ai/status`
Returns live provider resolution status, Ollama reachability, and fallback notices.
- **Response `200 OK`:**
  ```json
  {
    "active_provider_id": "ollama",
    "active_display_name": "Ollama Local Engine (v0.40.3)",
    "mode": "auto",
    "ollama_available": true,
    "ollama_version": "0.40.3",
    "ollama_endpoint": "http://127.0.0.1:11434",
    "is_mock_fallback": false,
    "fallback_notice": null,
    "phase": "2.3-streaming"
  }
  ```

### `GET /api/ai/models`
Discovers installed local models from Ollama `/api/tags` and maps NEXUS architectural roles.
- **Response `200 OK`:**
  ```json
  [
    {
      "name": "gemma3:1b",
      "role": "default_assistant",
      "size_gb": 0.75,
      "size_bytes": 806067407,
      "family": "gemma3",
      "is_installed": true,
      "is_loaded": false,
      "is_mock": false,
      "provider": "ollama",
      "status": "ready_local"
    }
  ]
  ```

### `POST /api/ai/stream`
Progressive Server-Sent Events (SSE) token streaming endpoint. Evaluates resource admission before initiating inference.
- **Request Body:**
  ```json
  {
    "messages": [
      {"role": "user", "content": "What is 2 + 2?"}
    ],
    "model_name": "gemma3:1b",
    "temperature": 0.7
  }
  ```
- **SSE Stream Output:**
  ```
  data: {"token": "Two", "done": false, "model": "gemma3:1b", "provider": "ollama", "is_mock": false}

  data: {"token": " plus two is four.", "done": false, "model": "gemma3:1b", "provider": "ollama", "is_mock": false}

  data: {"token": "", "done": true, "model": "gemma3:1b", "provider": "ollama", "is_mock": false, "eval_count": 7, "eval_duration_ms": 215.3, "tokens_per_second": 32.5}
  ```

---

## 2. Resource Management Endpoints (`/api/resources`)

### `GET /api/resources/metrics`
Samples real-time hardware telemetry via native Win32 system calls.
- **Response `200 OK`:**
  ```json
  {
    "cpu_percent": 12.4,
    "ram_used_gb": 10.23,
    "ram_total_gb": 16.0,
    "ram_available_gb": 5.77,
    "ram_load_percent": 64.0,
    "status": "normal",
    "active_tasks_count": 0,
    "can_start_heavy_task": true,
    "antigravity_priority_active": true,
    "min_ram_headroom_gb": 2.0,
    "max_cpu_threshold_percent": 80.0
  }
  ```

### `POST /api/resources/limits`
Updates user-configured resource boundaries, persisting them into SQLite. Rejects weakening hard safety limits ($> 80\%$ CPU or $< 2.0\text{ GB}$ RAM) with `400 Bad Request`.
- **Request Body:**
  ```json
  {
    "max_cpu_percent": 75.0,
    "min_ram_gb": 2.5,
    "max_concurrent_tasks": 2
  }
  ```
- **Response `200 OK`:** Returns updated effective limits dictionary.
