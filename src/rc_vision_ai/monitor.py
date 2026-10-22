"""Best-effort, local-only resource telemetry using the standard library."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Any


def _linux_memory_mb() -> dict[str, int] | None:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return None
    values: dict[str, int] = {}
    try:
        for line in meminfo.read_text(encoding="utf-8").splitlines():
            key, _, rest = line.partition(":")
            if key in {"MemTotal", "MemAvailable", "MemFree"}:
                values[key] = int(rest.strip().split()[0]) // 1024
    except (OSError, ValueError, IndexError):
        return None
    if "MemTotal" not in values:
        return None
    available = values.get("MemAvailable", values.get("MemFree"))
    result = {"total_mb": values["MemTotal"]}
    if available is not None:
        result["available_mb"] = available
        result["used_mb"] = max(0, result["total_mb"] - available)
    return result


def _thermal_celsius() -> list[float]:
    """Read thermal zones when exposed by the OS; labels may not identify the GPU."""
    readings: list[float] = []
    root = Path("/sys/class/thermal")
    if not root.exists():
        return readings
    for zone in root.glob("thermal_zone*/temp"):
        try:
            raw = float(zone.read_text(encoding="utf-8").strip())
            # Linux thermal sysfs commonly reports millidegrees Celsius.
            celsius = raw / 1000.0 if raw > 1000 else raw
            if -20.0 <= celsius <= 150.0:
                readings.append(round(celsius, 1))
        except (OSError, ValueError):
            continue
    return readings


def collect_telemetry() -> dict[str, Any]:
    """Return only metrics the current platform exposes; missing fields stay unknown."""
    return {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cpu_logical_cores": os.cpu_count(),
        "memory": _linux_memory_mb(),
        "thermal_zone_celsius": _thermal_celsius(),
        "notes": [
            "CPU usage percentage is not sampled by this starter.",
            "GPU utilization and battery telemetry are not assumed available.",
            "Thermal-zone values are device-specific and may not be CPU/GPU temperatures.",
        ],
    }
