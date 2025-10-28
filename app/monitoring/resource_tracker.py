"""
Resource Tracking Module.

Monitors CPU, memory, and system resource usage.
"""

from datetime import datetime
import threading
import time
from typing import Any

import psutil
from rich.console import Console


class ResourceTracker:
    """
    Track system resource usage (CPU, memory).

    Provides real-time resource monitoring for performance analysis.
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize resource tracker.

        Args:
            console: Rich console for display output
        """
        self.console = console or Console()
        self._resource_snapshots: list[dict[str, Any]] = []
        self._resource_monitor_active = False
        self._resource_monitor_thread = None
        self._lock = threading.Lock()

    def get_memory_usage(self) -> float:
        """
        Get current memory usage percentage.

        Returns:
            Memory usage as percentage
        """
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

    def get_cpu_usage(self) -> float:
        """
        Get current CPU usage percentage.

        Returns:
            CPU usage as percentage
        """
        try:
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0

    def display_resource_status(self):
        """Display current resource usage status with live meters."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            memory_gb = memory.used / (1024**3)

            # Create resource meters
            self._display_resource_meters(cpu_percent, memory.percent, memory_gb)

        except Exception:
            pass  # Silent failure

    def _display_resource_meters(
        self, cpu_percent: float, memory_percent: float, memory_gb: float,
    ):
        """
        Display live resource meters with visual indicators.

        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            memory_gb: Memory used in GB
        """
        # Create CPU meter
        cpu_bar_width = 20
        cpu_filled = int((cpu_percent / 100) * cpu_bar_width)
        cpu_empty = cpu_bar_width - cpu_filled

        # CPU color coding
        if cpu_percent < 50:
            cpu_color = "green"
            cpu_icon = "🟢"
        elif cpu_percent < 80:
            cpu_color = "yellow"
            cpu_icon = "🟡"
        else:
            cpu_color = "red"
            cpu_icon = "🔴"

        cpu_meter = f"[{cpu_color}]{'█' * cpu_filled}[/{cpu_color}]{'░' * cpu_empty}"

        # Create Memory meter
        mem_bar_width = 20
        mem_filled = int((memory_percent / 100) * mem_bar_width)
        mem_empty = mem_bar_width - mem_filled

        # Memory color coding
        if memory_percent < 50:
            mem_color = "green"
            mem_icon = "🟢"
        elif memory_percent < 80:
            mem_color = "yellow"
            mem_icon = "🟡"
        else:
            mem_color = "red"
            mem_icon = "🔴"

        mem_meter = f"[{mem_color}]{'█' * mem_filled}[/{mem_color}]{'░' * mem_empty}"

        # Display meters
        self.console.print(
            f"   📊 {cpu_icon} CPU:  {cpu_meter} [{cpu_color}]{cpu_percent:5.1f}%[/{cpu_color}]",
        )
        self.console.print(
            f"   💾 {mem_icon} Memory: {mem_meter} [{mem_color}]{memory_percent:5.1f}% ({memory_gb:.1f}GB)[/{mem_color}]",
        )

    def start_monitoring(self):
        """Start background resource monitoring."""
        if self._resource_monitor_active:
            return

        self._resource_monitor_active = True
        self._resource_monitor_thread = threading.Thread(
            target=self._resource_monitor_loop, daemon=True,
        )
        self._resource_monitor_thread.start()

    def stop_monitoring(self):
        """Stop background resource monitoring."""
        self._resource_monitor_active = False
        if self._resource_monitor_thread:
            self._resource_monitor_thread.join(timeout=1.0)

    def _resource_monitor_loop(self):
        """Background loop for resource monitoring."""
        while self._resource_monitor_active:
            try:
                snapshot = {
                    "timestamp": datetime.now(),
                    "cpu_percent": psutil.cpu_percent(interval=None),
                    "memory_percent": psutil.virtual_memory().percent,
                    "memory_used_gb": psutil.virtual_memory().used / (1024**3),
                }

                with self._lock:
                    self._resource_snapshots.append(snapshot)
                    # Keep last 100 snapshots
                    if len(self._resource_snapshots) > 100:
                        self._resource_snapshots = self._resource_snapshots[-100:]

                time.sleep(2.0)  # Sample every 2 seconds

            except Exception:
                pass  # Silent failure to avoid disrupting execution

    def get_resource_summary(self) -> dict[str, Any]:
        """
        Get summary of resource usage.

        Returns:
            Dictionary with resource usage statistics
        """
        with self._lock:
            if not self._resource_snapshots:
                return {}

            cpu_values = [s["cpu_percent"] for s in self._resource_snapshots]
            mem_values = [s["memory_percent"] for s in self._resource_snapshots]

            return {
                "cpu_avg": sum(cpu_values) / len(cpu_values),
                "cpu_max": max(cpu_values),
                "cpu_min": min(cpu_values),
                "memory_avg": sum(mem_values) / len(mem_values),
                "memory_max": max(mem_values),
                "memory_min": min(mem_values),
                "sample_count": len(self._resource_snapshots),
            }
