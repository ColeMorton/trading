"""
Performance Logging Module.

Provides performance-aware logging with phase tracking and bottleneck detection.
"""

from datetime import datetime
import threading
import time
from typing import Any

from rich.table import Table

from app.core.logging_factory import get_logger
from app.ui.console_display import ConsoleDisplay

from .resource_tracker import ResourceTracker


class PerformanceLogger:
    """
    Performance-aware logger with integrated monitoring.

    Combines structured logging with performance metrics and resource tracking.
    """

    def __init__(
        self,
        name: str,
        console: ConsoleDisplay | None = None,
        performance_mode: str = "standard",
        show_resources: bool = False,
    ):
        """
        Initialize performance logger.

        Args:
            name: Logger name
            console: Console display for user output
            performance_mode: Performance monitoring level (minimal/standard/detailed)
            show_resources: Show real-time resource usage
        """
        self.logger = get_logger(name)
        self.console = console or ConsoleDisplay()
        self.performance_mode = performance_mode
        self.show_resources = show_resources

        # Performance tracking
        self._execution_phases: dict[str, dict[str, Any]] = {}
        self._phase_timings: dict[str, float] = {}
        self._performance_alerts: list[str] = []
        self._execution_start_time = None
        self._current_phase = None
        self._lock = threading.Lock()

        # Resource monitoring
        self.resource_tracker = ResourceTracker() if show_resources else None

        # Performance thresholds (in seconds)
        self._phase_thresholds = {
            "data_download": {"target": 15.0, "warning": 30.0, "critical": 60.0},
            "parameter_sweep": {"target": 30.0, "warning": 60.0, "critical": 120.0},
            "backtesting": {"target": 60.0, "warning": 120.0, "critical": 300.0},
            "portfolio_filtering": {"target": 5.0, "warning": 15.0, "critical": 30.0},
            "file_export": {"target": 3.0, "warning": 10.0, "critical": 20.0},
            "strategy_execution": {"target": 10.0, "warning": 30.0, "critical": 60.0},
        }

    def start_execution_monitoring(
        self,
        operation_name: str = "strategy_execution",
    ) -> None:
        """
        Start monitoring overall execution performance.

        Args:
            operation_name: Name of the operation being monitored
        """
        if self.performance_mode == "minimal":
            return

        self._execution_start_time = time.time()
        self._current_phase = None

        if self.resource_tracker and self.show_resources:
            self.resource_tracker.start_monitoring()

        self.logger.info(
            "performance_monitoring_started",
            operation=operation_name,
            mode=self.performance_mode,
        )

    def start_phase(
        self,
        phase_name: str,
        description: str = "",
        estimated_duration: float | None = None,
    ) -> None:
        """
        Start tracking a new execution phase.

        Args:
            phase_name: Name of the phase
            description: Human-readable description
            estimated_duration: Estimated duration in seconds
        """
        if self.performance_mode == "minimal":
            self.console.show_progress(description or phase_name)
            return

        current_time = time.time()

        # End previous phase if exists
        if self._current_phase:
            self.end_phase()

        with self._lock:
            self._current_phase = phase_name
            self._execution_phases[phase_name] = {
                "start_time": current_time,
                "description": description,
                "estimated_duration": estimated_duration,
                "memory_start": (
                    self.resource_tracker.get_memory_usage()
                    if self.resource_tracker
                    else 0
                ),
                "cpu_start": (
                    self.resource_tracker.get_cpu_usage()
                    if self.resource_tracker
                    else 0
                ),
            }

        # Display phase start
        if estimated_duration:
            self.console.show_progress(
                f"🚀 {description or phase_name} (est. {estimated_duration:.1f}s)",
            )
        else:
            self.console.show_progress(f"🚀 {description or phase_name}")

        self.logger.info(
            "phase_started",
            phase=phase_name,
            description=description,
            estimated_duration=estimated_duration,
        )

    def end_phase(
        self,
        success: bool = True,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        End the current execution phase.

        Args:
            success: Whether phase completed successfully
            details: Additional details about phase completion
        """
        if not self._current_phase or self.performance_mode == "minimal":
            return

        current_time = time.time()

        with self._lock:
            phase_info = self._execution_phases.get(self._current_phase, {})
            start_time = phase_info.get("start_time", current_time)
            duration = current_time - start_time

            # Calculate resource delta
            memory_delta = 0
            if self.resource_tracker:
                memory_delta = (
                    self.resource_tracker.get_memory_usage()
                    - phase_info.get("memory_start", 0)
                )

            # Store phase timing
            self._phase_timings[self._current_phase] = {
                "duration": duration,
                "success": success,
                "memory_delta": memory_delta,
                "details": details or {},
            }

            # Check for bottlenecks
            self._detect_bottlenecks(
                self._current_phase,
                duration,
                memory_delta,
                details,
            )

        # Display phase completion
        if success:
            self.console.show_success(
                f"✅ {self._current_phase} completed in {duration:.1f}s",
            )
            self.logger.info(
                "phase_completed",
                phase=self._current_phase,
                duration=duration,
                success=True,
            )
        else:
            self.console.show_error(
                f"❌ {self._current_phase} failed after {duration:.1f}s",
            )
            self.logger.error(
                "phase_failed",
                phase=self._current_phase,
                duration=duration,
                success=False,
            )

        self._current_phase = None

    def _detect_bottlenecks(
        self,
        phase_name: str,
        duration: float,
        memory_delta: float,
        details: dict[str, Any] | None,
    ):
        """
        Detect performance bottlenecks.

        Args:
            phase_name: Name of the phase
            duration: Phase duration in seconds
            memory_delta: Memory usage change
            details: Additional phase details
        """
        thresholds = self._phase_thresholds.get(
            phase_name,
            {"target": 30.0, "warning": 60.0, "critical": 120.0},
        )

        severity = None
        if duration > thresholds["critical"]:
            severity = "critical"
        elif duration > thresholds["warning"]:
            severity = "warning"
        elif duration > thresholds["target"]:
            severity = "info"

        if severity:
            alert = {
                "phase": phase_name,
                "duration": duration,
                "threshold": thresholds[severity],
                "severity": severity,
                "memory_delta": memory_delta,
                "timestamp": datetime.now(),
            }
            self._performance_alerts.append(alert)

            self.logger.warning(
                "performance_bottleneck_detected",
                phase=phase_name,
                duration=duration,
                severity=severity,
                threshold=thresholds[severity],
            )

            if severity == "critical":
                self.console.show_warning(
                    f"🚨 Critical bottleneck in {phase_name}: {duration:.1f}s",
                )

    def complete_execution_monitoring(self) -> None:
        """Complete execution monitoring and display summary."""
        if not self._execution_start_time or self.performance_mode == "minimal":
            return

        if self._current_phase:
            self.end_phase()

        if self.resource_tracker and self.show_resources:
            self.resource_tracker.stop_monitoring()

        total_time = time.time() - self._execution_start_time

        self.logger.info("performance_monitoring_completed", total_duration=total_time)

        # Display execution summary
        if self.performance_mode in ["standard", "detailed"]:
            self._display_execution_summary(total_time)

    def _display_execution_summary(self, total_time: float):
        """
        Display comprehensive execution performance summary.

        Args:
            total_time: Total execution time in seconds
        """
        self.console.show_heading("Performance Summary", level=2)

        table = Table(
            title="🎯 Execution Performance Analysis",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Phase", style="white", no_wrap=True)
        table.add_column("Duration", style="yellow", justify="right")
        table.add_column("Performance", style="green", justify="center")
        table.add_column("% of Total", style="blue", justify="right")

        for phase_name, timing_info in self._phase_timings.items():
            duration = timing_info["duration"]
            pct_total = (duration / total_time) * 100 if total_time > 0 else 0

            thresholds = self._phase_thresholds.get(
                phase_name,
                {"target": 30.0, "warning": 60.0, "critical": 120.0},
            )

            if duration <= thresholds["target"]:
                perf_indicator = "[green]⚡ Excellent[/green]"
            elif duration <= thresholds["warning"]:
                perf_indicator = "[yellow]✅ Good[/yellow]"
            elif duration <= thresholds["critical"]:
                perf_indicator = "[orange]⚠️ Slow[/orange]"
            else:
                perf_indicator = "[red]🚨 Critical[/red]"

            table.add_row(
                phase_name.replace("_", " ").title(),
                f"{duration:.2f}s",
                perf_indicator,
                f"{pct_total:.1f}%",
            )

        # Add total row
        table.add_row("", "", "", "", style="dim")
        table.add_row(
            "[bold]Total Execution[/bold]",
            f"[bold]{total_time:.2f}s[/bold]",
            "",
            "[bold]100.0%[/bold]",
        )

        self.console.show_table(table)

        # Show resource summary if available
        if self.resource_tracker and self.show_resources:
            summary = self.resource_tracker.get_resource_summary()
            if summary:
                self.console.show_info(
                    f"Resource Usage: CPU avg={summary['cpu_avg']:.1f}% max={summary['cpu_max']:.1f}%, "
                    f"Memory avg={summary['memory_avg']:.1f}% max={summary['memory_max']:.1f}%",
                )
