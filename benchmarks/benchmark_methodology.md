# Benchmark Methodology

## 1. Test Procedure

1. **Environmental Stabilization:**
   - Background tasks stabilized for 30 seconds prior to test execution.
   - Initial system RAM and CPU baselines recorded over 10 samples.
2. **Cold Load Test:**
   - Evaluates the duration required for Ollama to spawn the model runner subprocess, allocate memory, and return the first token from an un-cached state.
3. **Warm Generation Test:**
   - 3 consecutive runs per model with equivalent context length.
   - Evaluates median tokens per second, generation latency, and peak RAM consumption.
4. **Telemetry Sampling:**
   - Native Windows API polling at $500\text{ ms}$ intervals during inference.
   - Tracking physical RAM working sets via `GlobalMemoryStatusEx`.
