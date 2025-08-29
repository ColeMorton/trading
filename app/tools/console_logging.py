"""
Console Logging Infrastructure

This module provides a separation between terminal output and file logging,
implementing Rich-based console output with proper categorization and visual hierarchy.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, Union

from rich.console import Console
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
from rich.status import Status
from rich.table import Table
from rich.text import Text

from .setup_logging import setup_logging


class ConsoleLogger:
    """
    Enhanced console logger with Rich formatting and structured output.
    
    Provides clean separation between terminal output and file logging,
    with proper visual hierarchy and progress tracking.
    """
    
    def __init__(
        self,
        console: Optional[Console] = None,
        show_time: bool = False,
        verbose: bool = False,
        quiet: bool = True
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
        self._progress_stack = []
        self._status_stack = []
        
    def success(self, message: str, **kwargs) -> None:
        """Display success message with green checkmark."""
        if not self.quiet:
            self.console.print(f"[green]✅ {message}[/green]", **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Display error message with red X."""
        self.console.print(f"[red]❌ {message}[/red]", **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Display warning message with yellow warning sign."""
        if not self.quiet:
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
                self.console.print(f"\n[bold yellow]💡 {message}[/bold yellow]", **kwargs)
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
        show_percentage: bool = True
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
            columns.extend([
                TextColumn("•"),
                TextColumn("[progress.data]{task.fields[speed]}"),
            ])
        
        columns.append(TimeElapsedColumn())
        
        return Progress(
            *columns,
            console=self.console,
            expand=True,
            refresh_per_second=10
        )
    
    def live_table_context(self, table: Table):
        """Create a live updating table context."""
        return Live(table, console=self.console, refresh_per_second=4)


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
        log_subdir: Optional[str] = None,
        console_options: Optional[Dict[str, Any]] = None
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
        self.file_log, self.file_log_close, logger, file_handler = setup_logging(
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
            self.console_log.info(f"Execution completed in {execution_time:.2f} seconds")
        
        # Close file logging
        self.file_log_close()


@contextmanager
def console_logging_context(
    module_name: str,
    log_file: str,
    level: int = logging.INFO,
    mode: str = "w",
    log_subdir: Optional[str] = None,
    verbose: bool = False,
    quiet: bool = True,
    show_time: bool = False
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
    console_options = {
        'verbose': verbose,
        'quiet': quiet,
        'show_time': show_time
    }
    
    context = ConsoleLoggingContext(
        module_name=module_name,
        log_file=log_file,
        level=level,
        mode=mode,
        log_subdir=log_subdir,
        console_options=console_options
    )
    
    with context as (file_log, console_log):
        yield file_log, console_log