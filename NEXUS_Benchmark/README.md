# NEXUS Automated Local AI Benchmark Suite

Automated performance, resource, and qualitative benchmarking suite for local Ollama models on Windows 11 (Intel Core i3-1215U, 16 GB RAM).

## Structure
- `benchmark.py`: Complete automated test runner executing cold-start, warm-start, resource telemetry, quality tests, and embedding validation.
- `config.json`: Configuration for local Ollama endpoints, sampling frequencies, and test prompts.
- `prompts/`: Standardized prompt fixtures (General, Reasoning, Planning, Coding, Instruction Following).
- `results/`: Raw JSON benchmark metrics and CSV summary tables.
- `reports/`: Evidence-based final Markdown performance report with model recommendations.

## Usage
Run directly with Python:
```bash
python benchmark.py
```
