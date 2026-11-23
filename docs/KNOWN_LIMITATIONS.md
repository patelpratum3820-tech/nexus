# Known Limitations & Engineering Constraints

Engineering transparency requires documenting what NEXUS cannot do or where real hardware limitations exist.

---

## 1. Confirmed Hardware & Environment Limitations

1. **CPU Inference Bottlenecks:**
   Inference executes on the Intel Core i3-1215U CPU. Without dedicated Nvidia CUDA or tensor cores, models larger than 3B parameters (e.g. 7B or 14B) generate at unacceptably low speeds ($< 4\text{ tokens/sec}$) and cause severe CPU thermal throttling.
2. **Cold-Start Model Runner Latency:**
   When a model is not resident in memory, the initial request encounters a cold-load penalty of $2.5\text{ s} - 4.7\text{ s}$ while Ollama initializes the model runner subprocess and allocates model weights into RAM.
3. **Shared Host Memory Headroom:**
   The Intel UHD integrated graphics uses unified system RAM. When running resource-heavy workloads (such as multiple browser windows or Antigravity builds), available RAM can drop below the $2.0\text{ GB}$ reserve, temporarily blocking new inference requests.

---

## 2. Software & Architecture Limitations

1. **Single Chat Model Scope (Phase 2.3):**
   In Phase 2.3, live inference is enabled strictly for `gemma3:1b`. Dynamic model switching between coding and general models is scheduled for Phase 2.4.
2. **Admission Gate vs. Runtime Preemption:**
   The resource manager checks CPU and RAM before admitting a task. It does not pause or throttle a model mid-sentence if the user opens a heavy external application during active generation.
3. **Absence of Installer Packaging:**
   NEXUS currently runs via node/python development processes. It has not yet been packaged into a standalone signed Windows installer (`.exe` / `.msi`).
