# NEXUS Local Model Benchmarks

## 1. Verified Model Inventory

All models evaluated in NEXUS were pre-installed on the host development machine. No models were downloaded over the network during benchmarking or execution:

| Model Tag | Disk Footprint | Primary Architecture Role | Rationale in NEXUS Ecosystem |
| :--- | :--- | :--- | :--- |
| **`gemma3:1b`** | $\sim 0.77\text{ GB}$ ($806\text{ MB}$) | `default_assistant` | Lowest cold-load latency ($2.51\text{ s}$), rapid token delivery, and light memory overhead. |
| **`qwen2.5-coder:1.5b`** | $\sim 0.94\text{ GB}$ ($986\text{ MB}$) | `coding_assistant` | High code synthesis capability, $16\text{k}$ context window, under $1.1\text{ GB}$ RAM footprint. |
| **`phi4-mini:latest`** | $\sim 2.38\text{ GB}$ ($2.49\text{ GB}$) | `restricted_reasoning` | High reasoning density; heavy memory allocation requires explicit user confirmation. |
| **`qwen3:1.7b`** | $\sim 1.30\text{ GB}$ ($1.36\text{ GB}$) | `optional` | Optional experimental model; deprioritized due to higher latency on low-power CPU. |
| **`nomic-embed-text:latest`** | $\sim 0.26\text{ GB}$ ($274\text{ MB}$) | `memory_embeddings` | 768-dimensional text embedding extraction for semantic retrieval and long-term memory. |

---

## 2. Individual Model Performance Benchmarks

The following baseline metrics were gathered under controlled conditions with background applications minimized:

| Model Tag | Cold Load Time | Warm Generation Speed | Warm Latency | Peak System RAM | RAM Delta | Average CPU | Evaluation Score* |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Gemma 3:1B** | $2.51\text{ s}$ | **$26.99\text{ tok/s}$** | $19.23\text{ s}$ | $10.44\text{ GB}$ | $+0.87\text{ GB}$ | $53.9\%$ | $4.4 / 5$ |
| **Qwen 2.5 Coder 1.5B** | $1.94\text{ s}$ | **$25.64\text{ tok/s}$** | $20.11\text{ s}$ | $10.70\text{ GB}$ | $+1.09\text{ GB}$ | $53.7\%$ | $4.0 / 5$ |
| **Qwen3 1.7B** | $2.70\text{ s}$ | **$20.21\text{ tok/s}$** | $25.48\text{ s}$ | $11.36\text{ GB}$ | $+1.78\text{ GB}$ | $57.7\%$ | $3.0 / 5$ |
| **Phi-4-mini** | $4.72\text{ s}$ | **$11.12\text{ tok/s}$** | $17.80\text{ s}$ | $12.18\text{ GB}$ | $+2.75\text{ GB}$ | $54.3\%$ | $4.8 / 5$ |
| **Nomic Embed Text** | Instant | *N/A (Embedding)* | $0.702\text{ s}$ batch | $9.77\text{ GB}$ | $+0.12\text{ GB}$ | $29.4\%$ | *N/A* |

*\*Note: Evaluation scores reflect subjective prompt comprehension and accuracy during developer smoke testing, not standardized MMLU/HumanEval benchmarks.*

---

## 3. Concurrent Workload Benchmark (Antigravity IDE Active)

To verify feasibility during active development, models were tested while Google Antigravity was actively compiling and editing code:

| Scenario / Active Workload | Peak System RAM | Min Available RAM | Average CPU | Peak CPU | Generation Speed | Recovery Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Antigravity Active Baseline** | $9.85\text{ GB}$ | $5.85\text{ GB}$ | $19.9\%$ | $28.8\%$ | *N/A* | $0\text{ s}$ |
| **Antigravity + Gemma 3:1B** | $10.69\text{ GB}$ | $5.01\text{ GB}$ | $67.9\%$ | $79.6\%$ | **$25.86\text{ tok/s}$** | $4\text{ s}$ |
| **Antigravity + Qwen Coder 1.5B** | $10.95\text{ GB}$ | $4.75\text{ GB}$ | $65.7\%$ | $76.6\%$ | **$23.88\text{ tok/s}$** | $4\text{ s}$ |
| **Antigravity + Phi-4-mini** | $12.60\text{ GB}$ | $3.10\text{ GB}$ | $64.5\%$ | $88.0\%$ | **$10.12\text{ tok/s}$** | $4\text{ s}$ |
| **Antigravity + Nomic Embed** | $9.93\text{ GB}$ | $5.77\text{ GB}$ | $50.2\%$ | $50.2\%$ | $0.208\text{ s/vec}$ | $3\text{ s}$ |

### Architectural Takeaway:
`gemma3:1b` and `qwen2.5-coder:1.5b` preserve over $4.7\text{ GB}$ of available system RAM and keep peak CPU under $80\%$, confirming their fitness for concurrent developer operations. Conversely, `phi4-mini` draws peak CPU up to $88.0\%$ and decreases available memory to $3.10\text{ GB}$, justifying its restriction behind an explicit confirmation gate.

---

## 4. Live Verification Milestone (Phase 2.3)

In Phase 2.3, real inference was verified end-to-end on `gemma3:1b`:
- **Prompt:** `"What is 2 + 2? Answer concisely in one sentence."`
- **Output:** `"Two plus two equals four."`
- **Time to First Token (TTFT):** $3.697\text{ s}$ (includes cold model-runner process initialization)
- **Generation Tokens:** $7\text{ tokens}$
- **Pure Generation Duration:** $0.215\text{ s}$
- **Measured Token Generation Speed:** **$32.5\text{ tokens/second}$**
- **Lifecycle Cleanup:** Model was safely evicted via `keep_alive: 0`, leaving 0 models in Ollama memory and the service running.
