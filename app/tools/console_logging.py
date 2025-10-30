"""
Console Logging Infrastructure

This module provides a separation between terminal output and file logging,
implementing Rich-based console output with proper categorization and visual hierarchy.
Enhanced with integrated performance monitoring for strategy execution optimization.
"""

import logging
import threading
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any

import psutil
from rich.box import ROUNDED
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.rule import Rule
from rich.status import Status
from rich.table import Table

from .setup_logging import setup_logging


class ConsoleLogger:
    """
    Enhanced console logger with Rich formatting and structured output.

    Provides clean separation between terminal output and file logging,
    with proper visual hierarchy and progress tracking.
    """

    def __init__(
        self,
        console: Console | None = None,
        show_time: bool = False,
        verbose: bool = False,
        quiet: bool = True,
    ):
        """
        Initialize console logger.

        Args:
            console: Rich console instance (creates new if None)
            show_time: Whether to show timestamps in terminal output
            verbose: Enable verbose terminal output
            quiet: Suppress non-essential terminal output (default: True)
        """
        self.console = console or Console()
        self.show_time = show_time
        self.verbose = verbose
        self.quiet = quiet
        self._progress_stack: list[Progress] = []
        self._status_stack: list[Any] = []

    def success(self, message: str, **kwargs) -> None:
        """Display success message with green checkmark."""
        # Always show success messages, even in quiet mode
        self.console.print(f"[green]✅ {message}[/green]", **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Display error message with red X."""
        # Always show error messages, even in quiet mode
        self.console.print(f"[red]❌ {message}[/red]", **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Display warning message with yellow warning sign."""
        if not self.quiet:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]", **kwargs)

    def verbose_warning(self, message: str, **kwargs) -> None:
        """Display warning message only in verbose mode."""
        if self.verbose and not self.quiet:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]", **kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Display info message with blue info icon."""
        if not self.quiet:
            self.console.print(f"[blue]ℹ️  {message}[/blue]", **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        """Display debug message (only in verbose mode)."""
        if self.verbose and not self.quiet:
            self.console.print(f"[dim]🔍 {message}[/dim]", **kwargs)

    def progress(self, message: str, **kwargs) -> None:
        """Display progress message with gear icon."""
        if not self.quiet:
            self.console.print(f"[cyan]⚙️  {message}[/cyan]", **kwargs)

    def heading(self, message: str, level: int = 1, **kwargs) -> None:
        """Display heading with appropriate formatting."""
        if not self.quiet:
            if level == 1:
                self.console.print(f"\n[bold cyan]🚀 {message}[/bold cyan]", **kwargs)
            elif level == 2:
                self.console.print(f"\n[bold blue]📊 {message}[/bold blue]", **kwargs)
            elif level == 3:
                self.console.print(
                    f"\n[bold yellow]💡 {message}[/bold yellow]",
                    **kwargs,
                )
            else:
                self.console.print(f"\n[bold white]• {message}[/bold white]", **kwargs)

    def section(self, title: str, content: str = "", **kwargs) -> None:
        """Display content in a panel section."""
        if not self.quiet:
            if content:
                panel = Panel(content, title=title, border_style="blue")
            else:
                panel = Panel(title, border_style="blue")
            self.console.print(panel, **kwargs)

    def table(self, table: Table, **kwargs) -> None:
        """Display a Rich table."""
        if not self.quiet:
            self.console.print(table, **kwargs)

    def status_context(self, message: str, spinner: str = "dots"):
        """Create a status context for operations."""
        return Status(message, console=self.console, spinner=spinner)

    def progress_context(
        self,
        description: str = "Processing...",
        show_speed: bool = False,
        show_percentage: bool = True,
    ):
        """Create a progress context for operations with progress bars."""
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ]

        if show_percentage:
            columns.append(TaskProgressColumn())

        if show_speed:
            columns.extend(
                [
                    TextColumn("•"),
                    TextColumn("[progress.data]{task.fields[speed]}"),
                ],
            )

        columns.append(TimeElapsedColumn())

        return Progress(
            *columns,
            console=self.console,
            expand=True,
            refresh_per_second=10,
        )

    def live_table_context(self, table: Table):
        """Create a live updating table context."""
        return Live(table, console=self.console, refresh_per_second=4)

    def data_summary_table(self, ticker: str, data_info: dict[str, Any]) -> None:
        """Display market data summary in a formatted table."""
        if self.quiet:
            return

        table = Table(
            title=f"📊 Market Data Summary: {ticker}",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="blue",
        )
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Format values nicely
        if "date_range" in data_info:
            table.add_row("Date Range", data_info["date_range"])
        if "price_range" in data_info:
            table.add_row("Price Range", data_info["price_range"])
        if "avg_volume" in data_info:
            volume = data_info["avg_volume"]
            if isinstance(volume, int | float):
                table.add_row("Avg Volume", f"{volume:,.0f}")
            else:
                table.add_row("Avg Volume", str(volume))
        if "frequency" in data_info:
            table.add_row("Frequency", data_info["frequency"])
        if "records_count" in data_info:
            table.add_row("Records", f"{data_info['records_count']:,}")

        self.console.print(table)

    def strategy_header(
        self,
        ticker: str,
        strategy_types: list[str],
        profile: str | None = None,
    ) -> None:
        """Display strategy analysis header with enhanced formatting."""
        if self.quiet:
            return

        title = f"🎯 Strategy Analysis: {ticker}"
        if len(strategy_types) == 1:
            subtitle = f"Strategy: {strategy_types[0]}"
        else:
            subtitle = f"Strategies: {', '.join(strategy_types)}"

        if profile:
            subtitle += f" | Profile: {profile}"

        content = f"[bold white]{subtitle}[/bold white]"

        panel = Panel(
            content,
            title=title,
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 2),
        )

        self.console.print("\n")
        self.console.print(panel)

    def results_summary_table(
        self,
        portfolios_generated: int,
        best_config: str | None = None,
        files_exported: int | None = None,
    ) -> None:
        """Display analysis results summary."""
        if self.quiet:
            return

        table = Table(
            title="📈 Analysis Summary",
            show_header=False,
            box=ROUNDED,
            border_style="green",
        )
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Portfolios Generated", f"{portfolios_generated:,}")
        if best_config:
            table.add_row("Best Configuration", best_config)
        if files_exported:
            table.add_row("Files Exported", str(files_exported))

        self.console.print(table)

    def phase_separator(self, title: str) -> None:
        """Display a visual separator between major phases."""
        if self.quiet:
            return

        rule = Rule(f"[bold blue]{title}[/bold blue]", style="blue")
        self.console.print(rule)

    def completion_banner(self, message: str = "Analysis Complete") -> None:
        """Display a completion banner."""
        if self.quiet:
            return

        panel = Panel(
            f"[bold green]✅ {message}[/bold green]",
            border_style="green",
            box=ROUNDED,
            padding=(0, 2),
        )
        self.console.print(panel)


class ConsoleLoggingContext:
    """
    Context manager that provides both file logging and enhanced console output.

    Separates concerns between detailed file logging and clean terminal output.
    """

    def __init__(
        self,
        module_name: str,
        log_file: str,
        level: int = logging.INFO,
        mode: str = "w",
        log_subdir: str | None = None,
        console_options: dict[str, Any] | None = None,
    ):
        """
        Initialize console logging context.

        Args:
            module_name: Name of the module for logging identification
            log_file: Name of the log file
            level: File logging level
            mode: File mode ('w' or 'a')
            log_subdir: Optional subdirectory for log files
            console_options: Options for console logger (verbose, quiet, etc.)
        """
        self.module_name = module_name
        self.log_file = log_file
        self.level = level
        self.mode = mode
        self.log_subdir = log_subdir
        self.console_options = console_options or {}

        # These will be set in __enter__
        self.file_log = None
        self.file_log_close = None
        self.console_log = None
        self.start_time = None

    def __enter__(self):
        """Enter the logging context."""
        # Set up file logging
        self.file_log, self.file_log_close, _logger, _file_handler = setup_logging(
            module_name=self.module_name,
            log_file=self.log_file,
            level=self.level,
            mode=self.mode,
            log_subdir=self.log_subdir,
        )

        # Set up console logging
        self.console_log = ConsoleLogger(**self.console_options)

        # Track timing
        self.start_time = time.time()

        return self.file_log, self.console_log

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the logging context."""
        # Calculate execution time
        execution_time = time.time() - self.start_time

        # Log completion to file
        self.file_log(f"Total execution time: {execution_time:.2f} seconds")

        # Show completion on console (unless quiet)
        if not self.console_log.quiet:
            self.console_log.info(
                f"Execution completed in {execution_time:.2f} seconds",
            )

        # Close file logging
        self.file_log_close()


@contextmanager
def console_logging_context(
    module_name: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = "w",
    log_subdir: str | None = None,
    verbose: bool = False,
    quiet: bool = True,
    show_time: bool = False,
):
    """
    Context manager for enhanced console and file logging.

    Provides clean separation between detailed file logs and user-friendly console output.

    Args:
        module_name: Name of the module for logging identification
        log_file: Name of the log file
        level: File logging level (default: logging.INFO)
        mode: File mode ('w' for write, 'a' for append) (default: 'w')
        log_subdir: Optional subdirectory for log files
        verbose: Enable verbose console output
        quiet: Suppress non-essential console output (default: True)
        show_time: Show timestamps in console output

    Yields:
        tuple: (file_log_function, console_logger)

    Example:
        with console_logging_context('strategy', 'analysis.log', verbose=True) as (file_log, console):
            console.heading("Starting Analysis")
            file_log("Detailed technical information")
            console.success("Analysis completed successfully")
    """
    console_options = {"verbose": verbose, "quiet": quiet, "show_time": show_time}

    context = ConsoleLoggingContext(
        module_name=module_name,
        log_file=log_file,
        level=level,
        mode=mode,
        log_subdir=log_subdir,
        console_options=console_options,
    )

    with context as (file_log, console_log):
        yield file_log, console_log


class PerformanceAwareConsoleLogger(ConsoleLogger):
    """
    Enhanced console logger with integrated performance monitoring.

    Extends ConsoleLogger with real-time performance metrics, execution phase tracking,
    resource usage monitoring, and optimization insights for strategy execution.
    """

    def __init__(
        self,
        console: Console | None = None,
        show_time: bool = False,
        verbose: bool = False,
        quiet: bool = True,
        performance_mode: str = "minimal",
        show_resources: bool = False,
        profile_execution: bool = False,
    ):
        """
        Initialize performance-aware console logger.

        Args:
            console: Rich console instance
            show_time: Whether to show timestamps
            verbose: Enable verbose output
            quiet: Suppress non-essential output
            performance_mode: Performance monitoring level (minimal/standard/detailed/benchmark)
            show_resources: Show real-time resource usage
            profile_execution: Enable detailed execution profiling
        """
        super().__init__(console, show_time, verbose, quiet)

        self.performance_mode = performance_mode
        self.show_resources = show_resources
        self.profile_execution = profile_execution

        # Performance tracking
        self._execution_phases: dict[str, dict[str, Any]] = {}
        self._phase_timings: dict[str, dict[str, float]] = {}
        self._resource_snapshots: list[dict[str, Any]] = []
        self._performance_alerts: list[dict[str, Any]] = []
        self._execution_start_time = None
        self._current_phase = None
        self._lock = threading.Lock()

        # Resource monitoring
        self._resource_monitor_active = False
        self._resource_monitor_thread = None

        # Performance thresholds with bottleneck categories (in seconds)
        self._phase_thresholds = {
            "data_download": {"target": 15.0, "warning": 30.0, "critical": 60.0},
            "parameter_sweep": {"target": 30.0, "warning": 60.0, "critical": 120.0},
            "backtesting": {"target": 60.0, "warning": 120.0, "critical": 300.0},
            "portfolio_filtering": {"target": 5.0, "warning": 15.0, "critical": 30.0},
            "file_export": {"target": 3.0, "warning": 10.0, "critical": 20.0},
            "strategy_execution": {"target": 10.0, "warning": 30.0, "critical": 60.0},
        }

        # Bottleneck pattern tracking
        self._bottleneck_patterns: list[dict[str, Any]] = []
        self._phase_trend_history: dict[str, list[float]] = {}

        # Import performance monitoring systems
        try:
            from ..performance_tracker import get_strategy_performance_tracker
            from ..processing.performance_monitor import get_performance_monitor

            self._strategy_tracker = get_strategy_performance_tracker()
            self._performance_monitor = get_performance_monitor()
            self._monitoring_available = True
        except ImportError:
            self._monitoring_available = False

    def start_execution_monitoring(self, operation_name: str = "strategy_execution"):
        """Start monitoring overall execution performance."""
        if not self._monitoring_available or self.performance_mode == "minimal":
            return

        self._execution_start_time = time.time()
        self._current_phase = None

        # Start resource monitoring if requested
        if self.show_resources and not self._resource_monitor_active:
            self._start_resource_monitoring()

        if self.performance_mode in ["detailed", "benchmark"]:
            self.info(
                f"🔍 Performance monitoring started ({self.performance_mode} mode)",
            )

    def start_phase(
        self,
        phase_name: str,
        description: str = "",
        estimated_duration: float | None = None,
    ):
        """Start tracking a new execution phase."""
        if self.performance_mode == "minimal":
            # For strategy execution, show essential progress even in minimal mode
            # Always display progress for strategy-related phases to provide user feedback
            if (
                phase_name
                in [
                    "strategy_execution",
                    "data_download",
                    "backtesting",
                    "portfolio_processing",
                ]
                or "strategy" in phase_name.lower()
            ):
                # Show essential progress for strategy execution phases
                if not self.quiet:
                    self.progress(f"⚙️  {description or phase_name}")
            else:
                # Standard minimal behavior for other phases
                self.progress(f"{description or phase_name}")
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
                "memory_start": self._get_memory_usage(),
                "cpu_start": self._get_cpu_usage(),
            }

        # Display phase start
        if estimated_duration:
            self.progress(
                f"🚀 {description or phase_name} (est. {estimated_duration:.1f}s)",
            )
        else:
            self.progress(f"🚀 {description or phase_name}")

        # Show resource usage if enabled
        if self.show_resources:
            self._display_resource_status()

    def end_phase(self, success: bool = True, details: dict[str, Any] | None = None):
        """End the current execution phase."""
        if not self._current_phase or self.performance_mode == "minimal":
            return

        current_time = time.time()

        with self._lock:
            phase_info = self._execution_phases.get(self._current_phase, {})
            start_time = phase_info.get("start_time", current_time)
            duration = current_time - start_time

            # Calculate resource delta
            memory_delta = self._get_memory_usage() - phase_info.get("memory_start", 0)

            # Store phase timing
            self._phase_timings[self._current_phase] = {
                "duration": duration,
                "success": success,
                "memory_delta": memory_delta,
                "details": details or {},
            }

            # Enhanced bottleneck identification
            self._detect_bottlenecks(
                self._current_phase,
                duration,
                memory_delta,
                details,
            )

        # Display phase completion
        if success:
            self.success(f"✅ {self._current_phase} completed in {duration:.1f}s")

            # Show performance analysis
            if self.performance_mode in ["standard", "detailed", "benchmark"]:
                self._display_phase_performance(self._current_phase, duration, details)
        else:
            self.error(f"❌ {self._current_phase} failed after {duration:.1f}s")

        self._current_phase = None

    def _detect_bottlenecks(
        self,
        phase_name: str,
        duration: float,
        memory_delta: float,
        details: dict[str, Any] | None,
    ):
        """Enhanced bottleneck detection with pattern analysis and actionable insights."""
        thresholds = self._phase_thresholds.get(
            phase_name,
            {"target": 30.0, "warning": 60.0, "critical": 120.0},
        )

        # Determine severity level
        severity = None
        bottleneck_type = None
        recommendations = []

        if duration > thresholds["critical"]:
            severity = "critical"
            bottleneck_type = "performance_critical"
        elif duration > thresholds["warning"]:
            severity = "warning"
            bottleneck_type = "performance_degraded"
        elif duration > thresholds["target"]:
            severity = "info"
            bottleneck_type = "performance_suboptimal"

        if severity:
            # Analyze bottleneck patterns and generate recommendations
            if phase_name == "data_download":
                if duration > thresholds["critical"]:
                    recommendations.extend(
                        [
                            "Enable data caching with --cache-data flag",
                            "Consider reducing the number of tickers or date range",
                            "Check network connectivity and Yahoo Finance API response times",
                        ],
                    )
                elif duration > thresholds["warning"]:
                    recommendations.append(
                        "Consider using cached data for repeated analysis",
                    )

            elif phase_name == "parameter_sweep":
                param_count = details.get("parameter_combinations", 0) if details else 0
                if param_count > 1000:
                    recommendations.extend(
                        [
                            f"Reduce parameter combinations (current: {param_count})",
                            "Use more targeted parameter ranges",
                            "Enable batch processing with --batch-size flag",
                        ],
                    )
                elif duration > thresholds["warning"]:
                    recommendations.append("Consider reducing parameter sweep ranges")

            elif phase_name == "backtesting":
                ticker_count = details.get("tickers", 0) if details else 0
                if memory_delta > 50:  # >50% memory increase
                    recommendations.extend(
                        [
                            "Enable memory optimization with --memory-optimization flag",
                            "Process tickers in smaller batches",
                            f"High memory usage detected (+{memory_delta:.1f}%)",
                        ],
                    )
                elif ticker_count > 5:
                    recommendations.append(
                        f"Consider processing {ticker_count} tickers in smaller batches",
                    )

            elif phase_name == "portfolio_filtering":
                if duration > thresholds["warning"]:
                    recommendations.extend(
                        [
                            "Optimize filtering criteria to reduce dataset size",
                            "Consider pre-filtering data before analysis",
                            "Use more selective minimum requirements",
                        ],
                    )

            elif phase_name == "file_export":
                if duration > thresholds["warning"]:
                    recommendations.extend(
                        [
                            "Consider exporting to Parquet format for better performance",
                            "Reduce exported columns if not all metrics are needed",
                            "Check disk I/O performance and available space",
                        ],
                    )

            # Store bottleneck alert
            alert = {
                "phase": phase_name,
                "duration": duration,
                "threshold": thresholds[severity],
                "severity": severity,
                "bottleneck_type": bottleneck_type,
                "memory_delta": memory_delta,
                "recommendations": recommendations,
                "timestamp": datetime.now(),
            }
            self._performance_alerts.append(alert)

            # Track patterns for trend analysis
            self._track_bottleneck_patterns(phase_name, duration, severity)

            # Display immediate alert for critical issues
            if severity == "critical" and not self.quiet:
                self.warning(
                    f"🚨 Critical bottleneck detected in {phase_name}: {duration:.1f}s",
                )
                if recommendations:
                    self.info(f"💡 Quick fix: {recommendations[0]}")

    def _track_bottleneck_patterns(
        self,
        phase_name: str,
        duration: float,
        severity: str,
    ):
        """Track bottleneck patterns for trend analysis."""
        if phase_name not in self._phase_trend_history:
            self._phase_trend_history[phase_name] = []

        self._phase_trend_history[phase_name].append(
            {"duration": duration, "severity": severity, "timestamp": datetime.now()},
        )

        # Keep last 10 measurements for trend analysis
        if len(self._phase_trend_history[phase_name]) > 10:
            self._phase_trend_history[phase_name] = self._phase_trend_history[
                phase_name
            ][-10:]

        # Detect patterns (3+ consecutive slowdowns)
        recent_history = self._phase_trend_history[phase_name][-3:]
        if len(recent_history) >= 3 and all(
            h["severity"] in ["warning", "critical"] for h in recent_history
        ):
            pattern = {
                "phase": phase_name,
                "pattern_type": "consistent_degradation",
                "occurrences": len(recent_history),
                "avg_duration": sum(h["duration"] for h in recent_history)
                / len(recent_history),
                "recommendation": f"Persistent performance issues in {phase_name} - consider system optimization",
            }
            self._bottleneck_patterns.append(pattern)

    def complete_execution_monitoring(self):
        """Complete execution monitoring and display summary."""
        if not self._monitoring_available or self.performance_mode == "minimal":
            return

        if self._current_phase:
            self.end_phase()

        # Stop resource monitoring
        if self._resource_monitor_active:
            self._stop_resource_monitoring()

        total_time = time.time() - (self._execution_start_time or time.time())

        # Display execution summary based on performance mode
        self._display_execution_summary(total_time)

    def _display_phase_performance(
        self,
        phase_name: str,
        duration: float,
        details: dict[str, Any] | None,
    ):
        """Display detailed phase performance information."""
        if self.quiet:
            return

        # Get phase thresholds for context
        thresholds = self._phase_thresholds.get(
            phase_name,
            {"target": 30.0, "warning": 60.0, "critical": 120.0},
        )
        target_threshold = thresholds["target"]

        # Color code based on performance against multiple thresholds
        if duration <= target_threshold:
            color = "green"
            status = "⚡ Excellent"
        elif duration <= thresholds["warning"]:
            color = "yellow"
            status = "✅ Good"
        elif duration <= thresholds["critical"]:
            color = "orange"
            status = "⚠️ Slow"
        else:
            color = "red"
            status = "🚨 Critical"

        self.console.print(
            f"   [{color}]Performance: {status} ({duration:.1f}s vs {target_threshold:.1f}s target)[/{color}]",
        )

        # Show bottleneck analysis for slower phases
        if duration > target_threshold and self.performance_mode == "detailed":
            bottleneck_severity = (
                "critical"
                if duration > thresholds["critical"]
                else "warning"
                if duration > thresholds["warning"]
                else "info"
            )
            self.console.print(
                f"   [dim]• Bottleneck Level: {bottleneck_severity.upper()}[/dim]",
            )

        # Show additional details if available
        if details and self.performance_mode == "detailed":
            for key, value in details.items():
                if isinstance(value, int | float):
                    self.console.print(f"   [dim]• {key}: {value:,.2f}[/dim]")
                else:
                    self.console.print(f"   [dim]• {key}: {value}[/dim]")

    def _display_execution_summary(self, total_time: float):
        """Display comprehensive execution performance summary."""
        if self.quiet:
            return

        self.heading("Performance Summary", level=2)

        # Create performance summary table
        table = Table(
            title="🎯 Execution Performance Analysis",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Phase", style="white", no_wrap=True)
        table.add_column("Duration", style="yellow", justify="right")
        table.add_column("Performance", style="green", justify="center")
        table.add_column("% of Total", style="blue", justify="right")

        # Add phase data with enhanced bottleneck analysis
        for phase_name, timing_info in self._phase_timings.items():
            duration = timing_info["duration"]
            pct_total = (duration / total_time) * 100 if total_time > 0 else 0

            # Performance indicator using new threshold structure
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

        self.table(table)

        # Show enhanced performance alerts with recommendations
        if self._performance_alerts:
            self._display_bottleneck_analysis()

        # Show bottleneck patterns if detected
        if self._bottleneck_patterns:
            self._display_bottleneck_patterns()

        # Show optimization recommendations
        if self.performance_mode in ["detailed", "benchmark"]:
            self._display_optimization_recommendations()

    def _display_bottleneck_analysis(self):
        """Display detailed bottleneck analysis with actionable recommendations."""
        critical_alerts = [
            a for a in self._performance_alerts if a["severity"] == "critical"
        ]
        warning_alerts = [
            a for a in self._performance_alerts if a["severity"] == "warning"
        ]

        if critical_alerts:
            self.heading("🚨 Critical Bottlenecks Detected", level=3)
            for alert in critical_alerts:
                self.console.print(
                    f"   [red]🚨 {alert['phase'].replace('_', ' ').title()}: {alert['duration']:.1f}s[/red]",
                )
                self.console.print(
                    f"   [dim]   Target: {self._phase_thresholds[alert['phase']]['target']:.1f}s | Critical: {alert['threshold']:.1f}s[/dim]",
                )

                # Show top recommendations
                if alert.get("recommendations"):
                    self.console.print("   [yellow]💡 Recommended Actions:[/yellow]")
                    for i, rec in enumerate(
                        alert["recommendations"][:2],
                        1,
                    ):  # Top 2 recommendations
                        self.console.print(f"   [dim]   {i}. {rec}[/dim]")
                self.console.print()

        elif warning_alerts:
            self.warning(f"⚠️ {len(warning_alerts)} performance bottlenecks detected:")
            for alert in warning_alerts:
                self.console.print(
                    f"   [yellow]⚠️ {alert['phase'].replace('_', ' ').title()}: {alert['duration']:.1f}s[/yellow]",
                )
                if alert.get("recommendations") and self.performance_mode == "detailed":
                    self.console.print(
                        f"   [dim]💡 {alert['recommendations'][0]}[/dim]"
                    )

    def _display_bottleneck_patterns(self):
        """Display detected bottleneck patterns for system optimization."""
        self.heading("🔍 Performance Pattern Analysis", level=3)

        for pattern in self._bottleneck_patterns:
            if pattern["pattern_type"] == "consistent_degradation":
                self.console.print(
                    f"   [orange]📉 Consistent degradation in {pattern['phase'].replace('_', ' ').title()}[/orange]",
                )
                self.console.print(
                    f"   [dim]   • {pattern['occurrences']} consecutive slow executions[/dim]",
                )
                self.console.print(
                    f"   [dim]   • Average duration: {pattern['avg_duration']:.1f}s[/dim]",
                )
                self.console.print(
                    f"   [yellow]💡 {pattern['recommendation']}[/yellow]"
                )
                self.console.print()

    def _display_optimization_recommendations(self):
        """Display performance optimization recommendations based on execution analysis."""
        recommendations = []
        priority_recommendations = []

        # Analyze phase timings for smart recommendations
        for phase_name, timing_info in self._phase_timings.items():
            duration = timing_info["duration"]
            thresholds = self._phase_thresholds.get(
                phase_name,
                {"target": 30.0, "warning": 60.0, "critical": 120.0},
            )

            # Priority recommendations for critical bottlenecks
            if duration > thresholds["critical"]:
                if phase_name == "data_download":
                    priority_recommendations.append(
                        "🔄 URGENT: Enable data caching - download times are critical",
                    )
                elif phase_name == "parameter_sweep":
                    priority_recommendations.append(
                        "⚙️ URGENT: Reduce parameter combinations - sweep time is critical",
                    )
                elif phase_name == "backtesting":
                    priority_recommendations.append(
                        "🚀 URGENT: Enable memory optimization - backtesting time is critical",
                    )
                elif phase_name == "portfolio_filtering":
                    priority_recommendations.append(
                        "🎯 URGENT: Optimize filtering criteria - processing time is critical",
                    )

            # Standard recommendations for warning-level issues
            elif duration > thresholds["warning"]:
                if phase_name == "data_download":
                    recommendations.append(
                        "🔄 Consider caching data for repeated analysis",
                    )
                elif phase_name == "parameter_sweep":
                    recommendations.append("⚙️ Consider tightening parameter ranges")
                elif phase_name == "backtesting":
                    recommendations.append(
                        "🚀 Consider smaller date ranges or batch processing",
                    )
                elif phase_name == "portfolio_filtering":
                    recommendations.append(
                        "🎯 Consider more selective filtering criteria",
                    )

        # Memory-based recommendations with enhanced analysis
        if self.show_resources and self._resource_snapshots:
            max_memory = max(
                snap.get("memory_percent", 0) for snap in self._resource_snapshots
            )
            avg_memory = sum(
                snap.get("memory_percent", 0) for snap in self._resource_snapshots
            ) / len(self._resource_snapshots)

            if max_memory > 90:
                priority_recommendations.append(
                    f"💾 URGENT: Critical memory usage ({max_memory:.1f}%) - enable memory optimization immediately",
                )
            elif max_memory > 80:
                recommendations.append(
                    f"💾 High memory usage detected ({max_memory:.1f}%) - consider memory optimization flags",
                )
            elif avg_memory > 70:
                recommendations.append(
                    f"💾 Sustained high memory usage ({avg_memory:.1f}% avg) - monitor for memory leaks",
                )

        # System-level optimization based on overall execution time
        total_execution_time = time.time() - (self._execution_start_time or time.time())
        if total_execution_time > 300:  # >5 minutes
            priority_recommendations.append(
                "⏱️ Long execution time detected - consider breaking into smaller batches",
            )

        # Display recommendations by priority
        if priority_recommendations:
            self.heading("🚨 Priority Optimizations", level=3)
            for rec in priority_recommendations:
                self.console.print(f"   [red]{rec}[/red]")

        if recommendations:
            self.heading("💡 Performance Optimizations", level=3)
            for rec in recommendations:
                self.info(f"   {rec}")

        # Overall system health assessment
        if not priority_recommendations and not recommendations:
            self.info(
                "✅ No significant performance issues detected - system running optimally",
            )

    def _start_resource_monitoring(self):
        """Start background resource monitoring."""
        if self._resource_monitor_active:
            return

        self._resource_monitor_active = True
        self._resource_monitor_thread = threading.Thread(
            target=self._resource_monitor_loop,
            daemon=True,
        )
        self._resource_monitor_thread.start()

    def _stop_resource_monitoring(self):
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

    def _display_resource_status(self):
        """Display current resource usage status with live meters."""
        if self.quiet or not self.show_resources:
            return

        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()

            # Create live resource meters
            self._display_resource_meters(
                cpu_percent,
                memory.percent,
                memory.used / (1024**3),
            )

        except Exception:
            pass  # Silent failure

    def _display_resource_meters(
        self,
        cpu_percent: float,
        memory_percent: float,
        memory_gb: float,
    ):
        """Display live resource meters with visual indicators."""
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

    def _get_memory_usage(self) -> float:
        """Get current memory usage percentage."""
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return psutil.cpu_percent(interval=None)
        except Exception:
            return 0.0

    def create_live_resource_dashboard(self, phase_name: str, description: str = ""):
        """Create a live updating resource dashboard for long-running phases."""
        return LiveResourceDashboard(self, phase_name, description)

    def performance_context(
        self,
        phase_name: str,
        description: str = "",
        estimated_duration: float | None = None,
    ):
        """Create a performance monitoring context for a phase."""
        return PerformancePhaseContext(
            self,
            phase_name,
            description,
            estimated_duration,
        )

    def parameter_progress_context(
        self,
        strategy_name: str,
        total_combinations: int,
        show_parallel_workers: bool = True,
    ):
        """Create enhanced progress context for parameter sweep operations.

        Args:
            strategy_name: Name of the strategy being analyzed
            total_combinations: Total number of parameter combinations
            show_parallel_workers: Show parallel worker utilization

        Returns:
            Enhanced Progress instance with nested progress bars and real-time metrics
        """
        # Determine performance level for progress display
        if self.performance_mode == "minimal":
            # Minimal mode: basic progress bar only
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TimeElapsedColumn(),
            ]
        elif self.performance_mode == "standard":
            # Standard mode: progress + rate + workers
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=35),
                TaskProgressColumn(),
                TextColumn("•"),
                TextColumn("[blue]{task.fields[rate]}/sec[/blue]"),
                TimeElapsedColumn(),
            ]
            if show_parallel_workers:
                columns.insert(
                    -1,
                    TextColumn("[dim]({task.fields[workers]} workers)[/dim]"),
                )
        else:
            # Detailed/benchmark mode: full metrics
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn("•"),
                TextColumn("[blue]{task.fields[rate]}/sec[/blue]"),
                TextColumn("•"),
                TextColumn("[green]ETA: {task.fields[eta]}[/green]"),
                TimeElapsedColumn(),
            ]
            if show_parallel_workers:
                columns.insert(
                    -2,
                    TextColumn("[dim]({task.fields[workers]} workers)[/dim]"),
                )

            # Add memory monitoring for detailed modes
            if self.show_resources:
                columns.insert(
                    -1,
                    TextColumn("[yellow]Mem: {task.fields[memory]}MB[/yellow]"),
                )

        # Calculate adaptive refresh rate based on total combinations
        if total_combinations < 50:
            refresh_rate = 8  # High refresh for small sets
        elif total_combinations < 500:
            refresh_rate = 4  # Standard refresh for medium sets
        else:
            refresh_rate = 2  # Lower refresh for large sets to reduce CPU overhead

        # Always show progress bars for strategy execution contexts
        # Progress bars provide essential user feedback regardless of quiet/minimal settings
        disable_progress = False

        return Progress(
            *columns,
            console=self.console,
            expand=True,
            refresh_per_second=refresh_rate,
            disable=disable_progress,
        )

    def info(self, message: str, **kwargs) -> None:
        """Display info message with enhanced strategy execution awareness."""
        # Respect quiet mode when explicitly set
        if self.quiet:
            return

        # For strategy execution contexts, show enhanced info
        if self._current_phase and (
            "strategy" in self._current_phase.lower()
            or self._current_phase.endswith("_execution")
            or self._current_phase
            in ["data_download", "backtesting", "portfolio_processing"]
        ):
            # Show strategy execution info with enhanced formatting
            self.console.print(f"[blue]ℹ️  {message}[/blue]", **kwargs)
        else:
            # Use base class behavior for other contexts
            super().info(message, **kwargs)

    def progress(self, message: str, **kwargs) -> None:
        """Display progress message with enhanced strategy execution awareness."""
        # Respect quiet mode when explicitly set
        if self.quiet:
            return

        # For strategy execution contexts, show enhanced progress
        if self._current_phase and (
            "strategy" in self._current_phase.lower()
            or self._current_phase
            in ["data_download", "backtesting", "portfolio_processing"]
        ):
            # Show strategy execution progress with enhanced formatting
            self.console.print(f"[cyan]⚙️  {message}[/cyan]", **kwargs)
        else:
            # Use base class behavior for other contexts
            super().progress(message, **kwargs)

    def heading(self, message: str, level: int = 1, **kwargs) -> None:
        """Display heading with enhanced strategy execution awareness."""
        # Respect quiet mode when explicitly set
        if self.quiet:
            return

        # For strategy execution contexts, show enhanced headings
        if self._current_phase and (
            "strategy" in self._current_phase.lower()
            or self._current_phase
            in ["data_download", "backtesting", "portfolio_processing"]
        ):
            # Show strategy execution headings with enhanced formatting
            if level == 1:
                self.console.print(f"\n[bold cyan]🚀 {message}[/bold cyan]", **kwargs)
            elif level == 2:
                self.console.print(f"\n[bold blue]📊 {message}[/bold blue]", **kwargs)
            elif level == 3:
                self.console.print(
                    f"\n[bold yellow]💡 {message}[/bold yellow]",
                    **kwargs,
                )
            else:
                self.console.print(f"\n[bold white]• {message}[/bold white]", **kwargs)
        else:
            # Use base class behavior for other contexts
            super().heading(message, level, **kwargs)


class LiveResourceDashboard:
    """Live updating resource dashboard for long-running phases."""

    def __init__(
        self,
        logger: PerformanceAwareConsoleLogger,
        phase_name: str,
        description: str,
    ):
        self.logger = logger
        self.phase_name = phase_name
        self.description = description
        self.start_time = None
        self.live_display = None
        self.update_active = False

    def __enter__(self):
        if not self.logger.show_resources or self.logger.quiet:
            return self

        self.start_time = time.time()
        self.update_active = True

        # Create live updating layout
        layout = Layout()
        layout.split_column(
            Layout(name="phase", size=3),
            Layout(name="resources", size=4),
        )

        self.live_display = Live(
            layout,
            console=self.logger.console,
            refresh_per_second=2,
        )
        self.live_display.start()

        # Start update thread
        self._update_thread = threading.Thread(
            target=self._update_dashboard,
            daemon=True,
        )
        self._update_thread.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.update_active = False
        if self.live_display:
            self.live_display.stop()

        # Show final resource status
        if not self.logger.quiet and self.logger.show_resources:
            elapsed = time.time() - (self.start_time or time.time())
            self.logger.info(f"📊 Phase completed in {elapsed:.1f}s")

    def _update_dashboard(self):
        """Update the live dashboard with current resource usage."""
        while self.update_active and self.live_display:
            try:
                if not self.live_display.is_started:
                    break

                elapsed = time.time() - (self.start_time or time.time())
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                memory_gb = memory.used / (1024**3)

                # Update phase info
                phase_panel = Panel(
                    f"[bold cyan]{self.description}[/bold cyan]\n"
                    f"[dim]Elapsed: {elapsed:.1f}s[/dim]",
                    title=f"🚀 {self.phase_name}",
                    border_style="cyan",
                )

                # Create resource meters table
                resource_table = Table(show_header=False, box=None, padding=(0, 1))
                resource_table.add_column("Metric", style="white", no_wrap=True)
                resource_table.add_column("Meter", style="white")
                resource_table.add_column("Value", style="white", justify="right")

                # CPU meter
                cpu_bar_width = 15
                cpu_filled = int((cpu_percent / 100) * cpu_bar_width)
                cpu_empty = cpu_bar_width - cpu_filled
                cpu_color = (
                    "green"
                    if cpu_percent < 50
                    else "yellow"
                    if cpu_percent < 80
                    else "red"
                )
                cpu_meter = (
                    f"[{cpu_color}]{'█' * cpu_filled}[/{cpu_color}]{'░' * cpu_empty}"
                )

                resource_table.add_row(
                    "CPU",
                    cpu_meter,
                    f"[{cpu_color}]{cpu_percent:5.1f}%[/{cpu_color}]",
                )

                # Memory meter
                mem_bar_width = 15
                mem_filled = int((memory.percent / 100) * mem_bar_width)
                mem_empty = mem_bar_width - mem_filled
                mem_color = (
                    "green"
                    if memory.percent < 50
                    else "yellow"
                    if memory.percent < 80
                    else "red"
                )
                mem_meter = (
                    f"[{mem_color}]{'█' * mem_filled}[/{mem_color}]{'░' * mem_empty}"
                )

                resource_table.add_row(
                    "Memory",
                    mem_meter,
                    f"[{mem_color}]{memory.percent:5.1f}% ({memory_gb:.1f}GB)[/{mem_color}]",
                )

                resource_panel = Panel(
                    resource_table,
                    title="📊 Resource Usage",
                    border_style="blue",
                )

                # Update layout
                if hasattr(self.live_display, "renderable") and hasattr(
                    self.live_display.renderable,
                    "children",
                ):
                    self.live_display.renderable["phase"].update(phase_panel)
                    self.live_display.renderable["resources"].update(resource_panel)

                time.sleep(0.5)  # Update every 500ms

            except Exception:
                break  # Exit on any error to avoid disrupting execution


class PerformancePhaseContext:
    """Context manager for tracking execution phases with performance monitoring."""

    def __init__(
        self,
        logger: PerformanceAwareConsoleLogger,
        phase_name: str,
        description: str,
        estimated_duration: float | None,
    ):
        self.logger = logger
        self.phase_name = phase_name
        self.description = description
        self.estimated_duration = estimated_duration
        self.success = True
        self.details: dict[str, Any] = {}

    def __enter__(self):
        self.logger.start_phase(
            self.phase_name,
            self.description,
            self.estimated_duration,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.success = exc_type is None
        self.logger.end_phase(self.success, self.details)

    def add_detail(self, key: str, value: Any):
        """Add a detail to be displayed with phase completion."""
        self.details[key] = value
