"""
NEXUS Resource Manager.
Provides low-frequency, lightweight monitoring and protection against resource starvation.
Uses native Windows ctypes calls for zero-dependency, microsecond-level telemetry.
"""
import ctypes
import os
import time
import asyncio
from typing import Dict, Any, Optional, List
from app.core.config import (
    MAX_SAFE_CPU_PERCENT,
    MIN_SAFE_AVAILABLE_RAM_GB,
    RESOURCE_SAMPLE_INTERVAL_SEC,
    RESOURCE_IDLE_SAMPLE_INTERVAL_SEC
)
from app.db.database import get_setting, set_setting

class _MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong)]

class ResourceManager:
    _instance: Optional["ResourceManager"] = None

    def __init__(self):
        self.is_monitoring = False
        self.sample_interval = RESOURCE_SAMPLE_INTERVAL_SEC
        self.max_cpu_limit = MAX_SAFE_CPU_PERCENT
        self.min_ram_limit_gb = MIN_SAFE_AVAILABLE_RAM_GB
        self.max_concurrent_tasks = 2
        self.active_workers: List[str] = []
        self._last_cpu_time = 0.0
        self._last_system_times = None
        self._last_metrics: Dict[str, Any] = {
            "cpu_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 16.0,
            "ram_available_gb": 8.0,
            "ram_load_percent": 0.0,
            "process_ram_mb": 0.0,
            "status": "normal",
            "active_tasks_count": 0,
            "can_start_heavy_task": True,
            "timestamp": time.time()
        }
        self._monitor_task: Optional[asyncio.Task] = None
        # Load user-configured limits from SQLite, falling back to safe defaults
        self._load_persisted_settings()

    def _load_persisted_settings(self):
        """Load user-configured limits from SQLite, preserving safe defaults."""
        try:
            persisted_cpu = get_setting("max_cpu_percent")
            if persisted_cpu:
                val = float(persisted_cpu)
                if 50.0 <= val <= 95.0:
                    self.max_cpu_limit = val

            persisted_ram = get_setting("min_ram_limit_gb")
            if persisted_ram:
                val = float(persisted_ram)
                if 1.0 <= val <= 6.0:
                    self.min_ram_limit_gb = val

            persisted_tasks = get_setting("max_concurrent_tasks")
            if persisted_tasks:
                val = int(persisted_tasks)
                if 1 <= val <= 4:
                    self.max_concurrent_tasks = val
        except Exception:
            pass

    def update_and_persist_limits(
        self,
        max_cpu_percent: Optional[float] = None,
        min_ram_gb: Optional[float] = None,
        max_concurrent_tasks: Optional[int] = None
    ) -> Dict[str, Any]:
        """Validate, apply, and persist resource thresholds."""
        if max_cpu_percent is not None:
            if not (50.0 <= max_cpu_percent <= 95.0):
                raise ValueError(f"max_cpu_percent must be between 50.0 and 95.0, got {max_cpu_percent}")
            self.max_cpu_limit = float(max_cpu_percent)
            set_setting("max_cpu_percent", str(self.max_cpu_limit))

        if min_ram_gb is not None:
            if not (1.0 <= min_ram_gb <= 6.0):
                raise ValueError(f"min_ram_gb must be between 1.0 and 6.0, got {min_ram_gb}")
            self.min_ram_limit_gb = float(min_ram_gb)
            set_setting("min_ram_limit_gb", str(self.min_ram_limit_gb))

        if max_concurrent_tasks is not None:
            if not (1 <= max_concurrent_tasks <= 4):
                raise ValueError(f"max_concurrent_tasks must be between 1 and 4, got {max_concurrent_tasks}")
            self.max_concurrent_tasks = int(max_concurrent_tasks)
            set_setting("max_concurrent_tasks", str(self.max_concurrent_tasks))

        return {
            "max_cpu_percent": self.max_cpu_limit,
            "min_ram_gb": self.min_ram_limit_gb,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "active_workers": self.active_workers
        }

    @classmethod
    def get_instance(cls) -> "ResourceManager":
        if cls._instance is None:
            cls._instance = ResourceManager()
        return cls._instance

    def _get_ram_info(self) -> Dict[str, float]:
        """Query physical RAM using Windows GlobalMemoryStatusEx via ctypes."""
        try:
            mem = _MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(_MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                total_gb = mem.ullTotalPhys / (1024 ** 3)
                avail_gb = mem.ullAvailPhys / (1024 ** 3)
                used_gb = total_gb - avail_gb
                return {
                    "total_gb": round(total_gb, 2),
                    "avail_gb": round(avail_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "load_percent": float(mem.dwMemoryLoad)
                }
        except Exception:
            pass
        return {"total_gb": 16.0, "avail_gb": 8.0, "used_gb": 8.0, "load_percent": 50.0}

    def _filetime_to_int(self, ft: _FILETIME) -> int:
        return (ft.dwHighDateTime << 32) + ft.dwLowDateTime

    def _get_system_cpu(self) -> float:
        """Query system CPU usage using GetSystemTimes with low delta."""
        try:
            idle_time = _FILETIME()
            kernel_time = _FILETIME()
            user_time = _FILETIME()
            success = ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle_time),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time)
            )
            if not success:
                return 0.0

            idle = self._filetime_to_int(idle_time)
            kernel = self._filetime_to_int(kernel_time)
            user = self._filetime_to_int(user_time)

            if self._last_system_times is not None:
                last_idle, last_kernel, last_user = self._last_system_times
                idle_delta = idle - last_idle
                kernel_delta = kernel - last_kernel
                user_delta = user - last_user
                total_sys = kernel_delta + user_delta

                if total_sys > 0:
                    cpu_percent = ((total_sys - idle_delta) / total_sys) * 100.0
                    self._last_system_times = (idle, kernel, user)
                    return max(0.0, min(100.0, round(cpu_percent, 1)))

            self._last_system_times = (idle, kernel, user)
            return 0.0
        except Exception:
            return 0.0

    def sample_metrics(self) -> Dict[str, Any]:
        """Perform an instant low-frequency sample of system resources."""
        ram = self._get_ram_info()
        cpu = self._get_system_cpu()

        # Determine health status
        status = "normal"
        can_start_heavy = True

        if ram["avail_gb"] < self.min_ram_limit_gb or cpu > self.max_cpu_limit:
            status = "constrained"
            can_start_heavy = False

        if ram["avail_gb"] < 0.8 or cpu > 95.0:
            status = "critical"
            can_start_heavy = False

        metrics = {
            "cpu_percent": cpu,
            "ram_used_gb": ram["used_gb"],
            "ram_total_gb": ram["total_gb"],
            "ram_available_gb": ram["avail_gb"],
            "ram_load_percent": ram["load_percent"],
            "status": status,
            "active_tasks_count": len(self.active_workers),
            "can_start_heavy_task": can_start_heavy and len(self.active_workers) < self.max_concurrent_tasks,
            "antigravity_priority_active": True,
            "min_ram_headroom_gb": self.min_ram_limit_gb,
            "timestamp": time.time()
        }
        self._last_metrics = metrics
        return metrics

    def get_latest_metrics(self) -> Dict[str, Any]:
        return self._last_metrics

    def register_worker(self, worker_id: str) -> bool:
        """Register a background task worker if within safe limits."""
        if len(self.active_workers) >= self.max_concurrent_tasks:
            return False
        if not self._last_metrics.get("can_start_heavy_task", True):
            return False
        self.active_workers.append(worker_id)
        return True

    def unregister_worker(self, worker_id: str) -> None:
        """Unregister a completed task worker."""
        if worker_id in self.active_workers:
            self.active_workers.remove(worker_id)

    async def start_background_monitoring(self) -> None:
        """Start async low-frequency monitoring loop (5-second intervals)."""
        if self.is_monitoring:
            return
        self.is_monitoring = True

        async def _loop():
            while self.is_monitoring:
                self.sample_metrics()
                await asyncio.sleep(self.sample_interval)

        self._monitor_task = asyncio.create_task(_loop())

    async def stop_background_monitoring(self) -> None:
        """Cleanly stop the monitor task."""
        self.is_monitoring = False
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
