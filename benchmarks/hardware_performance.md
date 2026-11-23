# Hardware Performance & Telemetry Analysis

Analysis of hardware resource consumption during local model execution on Intel Core i3-1215U.

## 1. Concurrent Antigravity IDE Workload

Testing measured how local inference impacts an active developer session running Google Antigravity:

```
[System RAM Utilization Profile]
Idle Baseline:     █████████░░░░░░░░░░░  9.85 GB
Gemma 3:1B:        ██████████░░░░░░░░░░  10.69 GB (+0.84 GB)
Qwen Coder 1.5B:   ██████████░░░░░░░░░░  10.95 GB (+1.10 GB)
Phi-4-mini:        ████████████░░░░░░░░  12.60 GB (+2.75 GB)
```

## 2. Recovery Time & Thermal Decay

After model completion, memory was released back to the operating system within **3 to 4 seconds**. The Intel UHD graphics dynamic buffer contracted immediately upon model process termination.
