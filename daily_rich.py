#!/usr/bin/env python3
"""
Enhanced daily.sh replacement with Rich progress bars and visualization.
Provides beautiful terminal output by default, with --quiet mode for automation.
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text


class DailyTradingExecutor:
    """Enhanced daily trading CLI executor with Rich progress bars."""

    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.script_dir = Path(__file__).parent.absolute()
        self.lock_file = self.script_dir / ".daily_execution.lock"
        self.log_dir = self.script_dir / "logs" / "daily"
        self.max_log_files = 30
        self.command_timeout_default = None

        # Allowed trading-cli commands (security whitelist)
        self.allowed_commands = {
            "strategy",
            "portfolio",
            "concurrency",
            "spds",
            "trade-history",
            "positions",
            "seasonality",
            "tools",
            "config",
            "status",
            "init",
            "version",
        }

        # Setup console and logging
        self._setup_console_and_logging()

    def _setup_console_and_logging(self):
        """Configure Rich console and logging based on quiet mode."""
        if self.quiet:
            # Quiet mode: minimal console, no Rich features
            self.console = Console(file=sys.stderr, quiet=True)
            self.use_rich = False
            # Setup basic logging to file only
            self._setup_file_logging()
        else:
            # Rich mode: enhanced console with progress bars on stderr
            self.console = Console(
                file=sys.stderr, force_terminal=True, force_interactive=True, width=120
            )
            self.use_rich = True
            # Setup Rich logging
            self._setup_rich_logging()

    def _setup_rich_logging(self):
        """Setup Rich-enhanced logging."""
        log_file = self.log_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old log files
        self._cleanup_old_logs()

        # Configure logging with Rich handler only
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                RichHandler(
                    console=self.console,
                    show_time=True,
                    show_level=True,
                    show_path=False,
                    markup=True,
                    rich_tracebacks=True,
                ),
                logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            ],
        )
        self.logger = logging.getLogger(__name__)

    def _setup_file_logging(self):
        """Setup file-only logging for quiet mode."""
        log_file = self.log_dir / f"daily_{datetime.now().strftime('%Y%m%d')}.log"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old log files
        self._cleanup_old_logs()

        # Configure basic file logging (no console output in quiet mode)
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] [%(levelname)s] %(message)s",
            handlers=[logging.FileHandler(log_file, mode="w", encoding="utf-8")],
        )
        self.logger = logging.getLogger(__name__)

    def _cleanup_old_logs(self):
        """Remove old log files beyond retention period."""
        if not self.log_dir.exists():
            return

        cutoff_time = time.time() - (self.max_log_files * 24 * 3600)
        for log_file in self.log_dir.glob("daily_*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                except OSError:
                    pass

    def _log_and_print(self, level: str, message: str):
        """Log message using unified Rich logging."""
        # Use only Rich logging - no duplicate console prints
        if level.upper() == "ERROR":
            self.logger.error(message)
        elif level.upper() == "WARN":
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def _create_lock(self) -> bool:
        """Create lock file, return True if successful."""
        if self.lock_file.exists():
            try:
                with open(self.lock_file, "r") as f:
                    lock_pid = int(f.read().strip())

                # Check if process is still running
                try:
                    os.kill(lock_pid, 0)
                    self._log_and_print(
                        "ERROR",
                        f"Another instance is already running (PID: {lock_pid})",
                    )
                    return False
                except OSError:
                    self._log_and_print("WARN", "Stale lock file found, removing...")
                    self.lock_file.unlink()
            except (ValueError, OSError):
                self.lock_file.unlink()

        with open(self.lock_file, "w") as f:
            f.write(str(os.getpid()))

        self._log_and_print("INFO", f"Created lock file with PID {os.getpid()}")
        return True

    def _cleanup_lock(self):
        """Remove lock file."""
        if self.lock_file.exists():
            self.lock_file.unlink()
            self._log_and_print("INFO", "Removed lock file")

    def _validate_dependencies(self) -> bool:
        """Validate required dependencies."""
        required_commands = ["yq", "poetry", "timeout"]
        missing_deps = []

        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_deps.append(cmd)

        if missing_deps:
            self._log_and_print(
                "ERROR", f"Missing required dependencies: {', '.join(missing_deps)}"
            )
            return False

        # Validate trading-cli is available
        try:
            result = subprocess.run(
                ["poetry", "run", "trading-cli", "--help"],
                capture_output=True,
                timeout=30,
                cwd=self.script_dir,
            )
            if result.returncode != 0:
                self._log_and_print(
                    "ERROR", "trading-cli not available or not properly configured"
                )
                return False
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            self._log_and_print("ERROR", "trading-cli validation failed")
            return False

        self._log_and_print("INFO", "All dependencies validated successfully")
        return True

    def _validate_config(self, config_file: Path) -> Tuple[bool, Optional[dict]]:
        """Validate configuration file and return config data."""
        if not config_file.exists():
            self._log_and_print("ERROR", f"Configuration file not found: {config_file}")
            return False, None

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self._log_and_print(
                "ERROR", f"Invalid YAML syntax in configuration file: {e}"
            )
            return False, None

        # Validate required fields
        if not config.get("metadata", {}).get("name"):
            self._log_and_print("ERROR", "Missing required field: metadata.name")
            return False, None

        commands = config.get("config", {}).get("commands", [])
        if not commands:
            self._log_and_print("ERROR", "No commands defined in configuration")
            return False, None

        self._log_and_print(
            "INFO", f"Configuration validated successfully ({len(commands)} commands)"
        )
        return True, config

    def _validate_command(self, command: str) -> bool:
        """Validate command against security whitelist."""
        import re

        # Extract main command from poetry run trading-cli pattern
        # Handle both forms: with and without poetry run prefix
        if "poetry run trading-cli" in command:
            cmd_part = command.split("poetry run trading-cli", 1)[1].strip()
        elif "trading-cli" in command:
            cmd_part = command.split("trading-cli", 1)[1].strip()
        else:
            return False

        # Skip global flags to find the main command
        tokens = cmd_part.split()
        for token in tokens:
            # If token doesn't start with -- or -, it's the subcommand
            if not token.startswith("--") and not token.startswith("-"):
                return token in self.allowed_commands

        # Special case: if only global flags (like --help, --version), allow
        if all(token.startswith("--") or token.startswith("-") for token in tokens):
            return True

        return False

    def _execute_command(
        self,
        name: str,
        command: str,
        timeout: int,
        progress: Optional[Progress] = None,
        task_id: Optional[TaskID] = None,
    ) -> bool:
        """Execute a single command with progress tracking."""
        self._log_and_print("INFO", f"STARTING: {name}")
        self._log_and_print("DEBUG", f"COMMAND: {command}")

        start_time = time.time()

        # Update progress if available
        if progress and task_id is not None:
            progress.update(task_id, description=f"[cyan]{name}[/cyan]")

        try:
            # Create temporary files for output capture
            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".stdout"
            ) as stdout_file, tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".stderr"
            ) as stderr_file:
                # Execute command with timeout (None means no timeout)
                result = subprocess.run(
                    ["bash", "-c", f"cd '{self.script_dir}' && {command}"],
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=timeout,
                    text=True,
                )

                # Read output files
                stdout_file.seek(0)
                stderr_file.seek(0)
                stdout_content = stdout_file.read()
                stderr_content = stderr_file.read()

                # Clean up temp files
                os.unlink(stdout_file.name)
                os.unlink(stderr_file.name)

        except subprocess.TimeoutExpired:
            duration = int(time.time() - start_time)
            self._log_and_print("ERROR", f"TIMEOUT: {name} ({duration}s)")
            return False

        except Exception as e:
            duration = int(time.time() - start_time)
            self._log_and_print("ERROR", f"FAILED: {name} ({duration}s) - {str(e)}")
            return False

        duration = int(time.time() - start_time)

        if result.returncode == 0:
            self._log_and_print("INFO", f"SUCCESS: {name} ({duration}s)")

            # Log warnings if stderr content exists
            if stderr_content.strip():
                self._log_and_print(
                    "WARN", f"Command produced warnings: {stderr_content.strip()}"
                )

            # Update progress to completed
            if progress and task_id is not None:
                progress.update(
                    task_id, completed=100, description=f"[green]✓ {name}[/green]"
                )

            return True
        else:
            self._log_and_print(
                "ERROR", f"FAILED: {name} ({duration}s, exit code: {result.returncode})"
            )

            if stderr_content.strip():
                self._log_and_print("ERROR", f"Error output: {stderr_content.strip()}")

            # Update progress to show failure
            if progress and task_id is not None:
                progress.update(
                    task_id, completed=100, description=f"[red]✗ {name}[/red]"
                )

            return False

    def run(self, config_file: Path, dry_run: bool = False) -> int:
        """Execute daily trading automation with Rich progress bars."""
        # Create lock file
        if not self._create_lock():
            return 2

        try:
            # Initialize
            if not self.quiet:
                self.console.print(
                    Panel.fit(
                        "[bold blue]Daily Trading CLI Automation[/bold blue]\n"
                        f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                        f"PID: {os.getpid()}",
                        border_style="blue",
                    )
                )

            self._log_and_print("INFO", "Starting daily trading CLI automation")

            # Validate environment
            if not self._validate_dependencies():
                return 3

            config_valid, config = self._validate_config(config_file)
            if not config_valid:
                return 5

            # Keep default timeout as None unless explicitly overridden
            # Note: config file default_timeout is ignored per user requirements
            # Only individual command timeouts will be respected

            config_name = config.get("metadata", {}).get("name", "unnamed")
            self._log_and_print("INFO", f"Loaded configuration: {config_name}")

            # Handle dry run
            if dry_run:
                return self._dry_run(config)

            # Execute commands with Rich progress
            return self._execute_commands(config)

        finally:
            self._cleanup_lock()

    def _dry_run(self, config: dict) -> int:
        """Execute dry run validation."""
        self._log_and_print("INFO", "DRY RUN MODE - Configuration validation only")

        commands = config.get("config", {}).get("commands", [])

        if not self.quiet:
            # Create table for dry run results
            table = Table(title="Dry Run Validation Results")
            table.add_column("Command", style="cyan")
            table.add_column("Status", style="magenta")
            table.add_column("Timeout", style="blue")
            table.add_column("Security", style="green")

            for i, cmd_config in enumerate(commands):
                name = cmd_config.get("name", f"Command {i}")
                command = cmd_config.get("command", "")
                enabled = cmd_config.get("enabled", True)
                timeout = cmd_config.get("timeout", self.command_timeout_default)

                # Determine status
                if not enabled:
                    status = "[yellow]DISABLED[/yellow]"
                elif not command:
                    status = "[red]INVALID[/red]"
                else:
                    status = "[green]ENABLED[/green]"

                # Check security
                security = (
                    "[green]✓[/green]"
                    if self._validate_command(command)
                    else "[red]✗[/red]"
                )

                timeout_display = "No timeout" if timeout is None else f"{timeout}s"
                table.add_row(name, status, timeout_display, security)

            self.console.print(table)

        self._log_and_print(
            "INFO", f"Dry run completed successfully ({len(commands)} commands)"
        )
        return 0

    def _execute_commands(self, config: dict) -> int:
        """Execute all commands with Rich progress tracking."""
        commands = config.get("config", {}).get("commands", [])

        # Filter enabled commands
        enabled_commands = [
            (i, cmd)
            for i, cmd in enumerate(commands)
            if cmd.get("enabled", True) and cmd.get("command")
        ]

        if not enabled_commands:
            self._log_and_print("WARN", "No enabled commands to execute")
            return 0

        success_count = 0
        failure_count = 0

        if self.use_rich:
            # Rich mode: progress bars and enhanced output
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TimeRemainingColumn(),
                console=self.console,
                transient=False,
            ) as progress:
                # Create overall progress task
                overall_task = progress.add_task(
                    description="[bold blue]Executing Daily Commands[/bold blue]",
                    total=len(enabled_commands),
                )

                # Execute each command
                for i, (cmd_index, cmd_config) in enumerate(enabled_commands):
                    name = cmd_config.get("name", f"Command {cmd_index}")
                    command = cmd_config.get("command")
                    timeout = cmd_config.get("timeout", self.command_timeout_default)
                    continue_on_failure = cmd_config.get("continue_on_failure", True)

                    # Validate command security
                    if not self._validate_command(command):
                        self._log_and_print(
                            "ERROR", f"SECURITY: Command not allowed: {command}"
                        )
                        failure_count += 1
                        progress.update(overall_task, advance=1)
                        continue

                    # Create individual task for this command
                    cmd_task = progress.add_task(
                        description=f"[cyan]Preparing {name}[/cyan]", total=100
                    )

                    # Execute command
                    if self._execute_command(
                        name, command, timeout, progress, cmd_task
                    ):
                        success_count += 1
                    else:
                        failure_count += 1
                        if not continue_on_failure:
                            self._log_and_print(
                                "ERROR",
                                "Command failed and continue_on_failure is false, stopping execution",
                            )
                            break

                    # Update overall progress
                    progress.update(overall_task, advance=1)

                    # Remove completed command task
                    progress.remove_task(cmd_task)

        else:
            # Quiet mode: execute without Rich features
            for i, (cmd_index, cmd_config) in enumerate(enabled_commands):
                name = cmd_config.get("name", f"Command {cmd_index}")
                command = cmd_config.get("command")
                timeout = cmd_config.get("timeout", self.command_timeout_default)
                continue_on_failure = cmd_config.get("continue_on_failure", True)

                # Validate command security
                if not self._validate_command(command):
                    self._log_and_print(
                        "ERROR", f"SECURITY: Command not allowed: {command}"
                    )
                    failure_count += 1
                    continue

                # Execute command
                if self._execute_command(name, command, timeout):
                    success_count += 1
                else:
                    failure_count += 1
                    if not continue_on_failure:
                        self._log_and_print(
                            "ERROR",
                            "Command failed and continue_on_failure is false, stopping execution",
                        )
                        break

        # Generate summary
        self._generate_summary(success_count, failure_count, len(enabled_commands))

        return 1 if failure_count > 0 else 0

    def _generate_summary(
        self, success_count: int, failure_count: int, total_commands: int
    ):
        """Generate execution summary."""
        if not self.quiet:
            # Rich summary table
            summary_table = Table(title="Execution Summary")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", style="magenta")
            summary_table.add_column("Percentage", style="green")

            success_pct = (
                (success_count / total_commands * 100) if total_commands > 0 else 0
            )
            failure_pct = (
                (failure_count / total_commands * 100) if total_commands > 0 else 0
            )

            summary_table.add_row("Total Commands", str(total_commands), "100%")
            summary_table.add_row(
                "Successful", str(success_count), f"{success_pct:.1f}%"
            )
            summary_table.add_row("Failed", str(failure_count), f"{failure_pct:.1f}%")

            self.console.print(summary_table)

            # Status panel
            if failure_count > 0:
                status_panel = Panel(
                    f"[red]✗ COMPLETED WITH FAILURES[/red]\n"
                    f"Success: {success_count}, Failures: {failure_count}",
                    border_style="red",
                )
            else:
                status_panel = Panel(
                    f"[green]✓ ALL COMMANDS SUCCESSFUL[/green]\n"
                    f"Completed: {success_count}/{total_commands}",
                    border_style="green",
                )

            self.console.print(status_panel)

        # Log summary
        self._log_and_print(
            "INFO",
            f"Execution summary: {success_count} succeeded, {failure_count} failed",
        )

        # Quiet mode: only final status
        if self.quiet:
            if failure_count > 0:
                print(
                    f"FAILED: {success_count} succeeded, {failure_count} failed",
                    file=sys.stderr,
                )
            else:
                print(
                    f"SUCCESS: All {success_count} commands completed", file=sys.stderr
                )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Daily Trading CLI Automation with Rich Progress Bars",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              # Run with Rich progress bars (default)
  %(prog)s --quiet                      # Run in quiet mode (no progress bars)
  %(prog)s --config custom.yaml         # Use custom configuration
  %(prog)s --dry-run                    # Validate configuration only
        """,
    )

    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "daily-config.yaml",
        help="Configuration file path (default: daily-config.yaml)",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Disable all output except final success/error status",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate configuration without executing commands",
    )

    parser.add_argument(
        "--version", action="version", version="daily_rich.py version 1.0"
    )

    args = parser.parse_args()

    # Create executor
    executor = DailyTradingExecutor(quiet=args.quiet)

    try:
        return executor.run(args.config, args.dry_run)
    except KeyboardInterrupt:
        executor._log_and_print("ERROR", "Script interrupted by user")
        return 130
    except Exception as e:
        executor._log_and_print("ERROR", f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
