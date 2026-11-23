# Local Model Comparison Analysis

Comprehensive evaluation of installed local models under equivalent developer workloads.

## 1. Summary Comparison

| Model | Parameter Size | Disk Footprint | Cold Load | Generation Speed | Latency | Peak RAM | Avg CPU | Quality* | NEXUS Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Gemma 3:1B** | $1\text{B}$ | $0.77\text{ GB}$ | $2.51\text{ s}$ | **$26.99\text{ tok/s}$** | $19.23\text{ s}$ | $10.44\text{ GB}$ | $53.9\%$ | $4.4 / 5$ | `default_assistant` |
| **Qwen 2.5 Coder 1.5B** | $1.5\text{B}$ | $0.94\text{ GB}$ | $1.94\text{ s}$ | **$25.64\text{ tok/s}$** | $20.11\text{ s}$ | $10.70\text{ GB}$ | $53.7\%$ | $4.0 / 5$ | `coding_assistant` |
| **Qwen3 1.7B** | $1.7\text{B}$ | $1.30\text{ GB}$ | $2.70\text{ s}$ | **$20.21\text{ tok/s}$** | $25.48\text{ s}$ | $11.36\text{ GB}$ | $57.7\%$ | $3.0 / 5$ | `optional` |
| **Phi-4-mini** | $3.8\text{B}$ | $2.38\text{ GB}$ | $4.72\text{ s}$ | **$11.12\text{ tok/s}$** | $17.80\text{ s}$ | $12.18\text{ GB}$ | $54.3\%$ | $4.8 / 5$ | `restricted_reasoning` |
| **Nomic Embed Text** | $137\text{M}$ | $0.26\text{ GB}$ | Instant | *N/A* | $0.702\text{ s}$ | $9.77\text{ GB}$ | $29.4\%$ | *N/A* | `memory_embeddings` |

*\*Quality ratings represent subjective prompt adherence and accuracy evaluated during developer smoke tests.*

---

## 2. Key Engineering Observations

- **Gemma 3:1B:** Fastest load time, exceptionally low memory footprint, and high throughput. Ideal as the everyday conversational assistant and dynamic island companion.
- **Qwen 2.5 Coder 1.5B:** Achieves generation speeds above $25\text{ tokens/sec}$ while demonstrating high coding accuracy on TypeScript and Python tasks.
- **Phi-4-mini:** Exhibits exceptional reasoning density, but draws peak system RAM to $12.18\text{ GB}$ (+2.75 GB delta) and drops generation throughput to $11.12\text{ tok/s}$.
- **Nomic Embed Text:** Instant vector generation ($0.208\text{ s/vector}$) with negligible memory footprint (+120 MB delta).
