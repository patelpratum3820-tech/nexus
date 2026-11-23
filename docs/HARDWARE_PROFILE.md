# Hardware Profile & Engineering Constraints

## 1. Development & Benchmark Hardware Specification

NEXUS was developed, profiled, and benchmarked directly on the following target consumer machine:

| Component | Hardware Specification | Architectural Implications |
| :--- | :--- | :--- |
| **System Model** | ASUS VivoBook 15 (X1504ZA Series) | Portable laptop with integrated low-power cooling |
| **Processor (CPU)** | Intel Core i3-1215U (12th Gen Alder Lake) | Hybrid architecture: 2 Performance cores + 4 Efficient cores |
| **Cores / Threads** | 6 physical cores / 8 logical threads | Heterogeneous execution; scheduling priority critical |
| **Clock Frequencies** | Base 1.20 GHz / Max Turbo up to 4.40 GHz | Aggressive thermal throttling occurs under sustained multi-thread loads |
| **System Memory (RAM)** | 16.0 GB DDR4 (3200 MT/s) | Shared memory architecture; no dedicated GPU VRAM |
| **Graphics (GPU)** | Integrated Intel UHD Graphics | Dynamic system memory allocation shared with OS and applications |
| **Primary Storage** | 512 GB PCIe 3.0 NVMe SSD | Rapid model cold loads; sequential read speeds up to 2.4 GB/s |
| **Operating System** | Microsoft Windows 11 Home (x64) | Win32 API access for memory/CPU measurement |
| **AI Runtime Engine** | Ollama (v0.40.3) | Local daemon bound to `127.0.0.1:11434` |

---

## 2. Hardware Resource Constraints

### 2.1 Shared System Memory Dynamics
Because the Intel UHD Graphics architecture lacks dedicated VRAM, system RAM is shared concurrently across:
1. Windows 11 Kernel and background system services ($\sim 4.5\text{ GB}$).
2. Google Antigravity IDE and language server processes ($\sim 2.5\text{ GB}$).
3. Desktop development tools and browser tabs ($\sim 2.0\text{ GB}$).
4. Local Ollama inference runner ($\sim 0.8\text{ GB} - 2.5\text{ GB}$ depending on model size).

Under normal active development, available system memory hovers between $5.5\text{ GB}$ and $7.0\text{ GB}$. If an AI workload consumes more than $4.0\text{ GB}$ of RAM, paging file thrashing and OS memory pressure occur.

### 2.2 Thermal Budget & Turbo Frequency Decay
The Intel Core i3-1215U has a 15W Base TDP and a 55W Maximum Turbo Power. Under short token bursts ($< 10\text{ seconds}$), P-cores boost to 4.4 GHz, achieving generation speeds above 30 tokens/sec on 1B models. Under sustained stress benchmarks exceeding 60 seconds, thermal dissipation limits clock frequencies to base levels ($\sim 1.8 - 2.4\text{ GHz}$), reducing token throughput by approximately $20-30\%$.

### 2.3 Antigravity IDE Priority Reservation
NEXUS is engineered as a developer companion running alongside Google Antigravity. To prevent IDE editor latency, code completion freezing, or compilation stutter:
- At least **2.0 GB** of physical RAM is strictly reserved for the operating system and Antigravity.
- System CPU utilization exceeding **80%** rejects new inference tasks before CPU starvation impacts the development environment.
