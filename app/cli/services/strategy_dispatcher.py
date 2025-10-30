"""
Strategy Dispatcher

This module provides unified strategy dispatch functionality, routing
CLI commands to appropriate strategy services based on configuration.
"""

import time
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from app.tools.console_logging import ConsoleLogger, PerformanceAwareConsoleLogger
from app.tools.project_utils import get_project_root

from ..models.strategy import (
    StrategyConfig,
    StrategyExecutionSummary,
    StrategyPortfolioResults,
    StrategyType,
)
from .batch_processing_service import BatchProcessingService
from .smart_resume_service import SmartResumeService
from .strategy_services import (
    ATRStrategyService,
    BaseStrategyService,
    COMPStrategyService,
    MACDStrategyService,
    MAStrategyService,
    SMAAtrStrategyService,
)


class StrategyDispatcher:
    """
    Dispatches strategy execution to appropriate service implementations.

    This class provides a unified interface for strategy execution while
    routing to strategy-specific implementations based on configuration.
    """

    def __init__(self, console: ConsoleLogger = None):
        """
        Initialize dispatcher with available strategy services.

        Args:
            console: Console logger for user-facing output
        """
        self.console = console or ConsoleLogger()
        # Initialize services with console logger
        self._services: dict[str, BaseStrategyService] = {
            "MA": MAStrategyService(console=self.console),
            "MACD": MACDStrategyService(console=self.console),
            "ATR": ATRStrategyService(console=self.console),
            "SMA_ATR": SMAAtrStrategyService(console=self.console),
            "COMP": COMPStrategyService(console=self.console),
        }

        # Initialize smart resume service with compatible logging
        def log_wrapper(message, level="info"):
            if hasattr(self.console, level):
                getattr(self.console, level)(message)

        self.resume_service = SmartResumeService(log=log_wrapper)

        # Initialize batch processing service
        self.batch_service = None  # Will be initialized when needed

    def _extract_strategy_parameters(
        self,
        config: StrategyConfig,
        strategy_type: StrategyType | str,
    ) -> dict[str, int | None]:
        """
        Extract strategy-specific parameters from StrategyConfig with proper fallback hierarchy.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to extract parameters for

        Returns:
            Dictionary with parameter values (fast_min, fast_max, slow_min, slow_max, signal_min, signal_max)
        """
        # Convert to string value
        if hasattr(strategy_type, "value"):
            strategy_value = strategy_type.value
        else:
            strategy_value = str(strategy_type).upper()

        # Initialize with defaults
        params: dict[str, int | None] = {
            "fast_min": None,
            "fast_max": None,
            "slow_min": None,
            "slow_max": None,
            "signal_min": None,
            "signal_max": None,
        }

        # Priority 1: Strategy-specific parameters from strategy_params
        if config.strategy_params:
            strategy_specific = None
            if strategy_value == "SMA" and config.strategy_params.SMA:
                strategy_specific = config.strategy_params.SMA
            elif strategy_value == "EMA" and config.strategy_params.EMA:
                strategy_specific = config.strategy_params.EMA
            elif strategy_value == "MACD" and config.strategy_params.MACD:
                strategy_specific = config.strategy_params.MACD
            elif strategy_value == "ATR" and config.strategy_params.ATR:
                strategy_specific = config.strategy_params.ATR
            elif (
                strategy_value == "SMA_ATR"
                and hasattr(config.strategy_params, "SMA_ATR")
                and config.strategy_params.SMA_ATR
            ):
                strategy_specific = config.strategy_params.SMA_ATR

            if strategy_specific:
                params.update(
                    {
                        "fast_min": strategy_specific.fast_period_min,
                        "fast_max": strategy_specific.fast_period_max,
                        "slow_min": strategy_specific.slow_period_min,
                        "slow_max": strategy_specific.slow_period_max,
                        "signal_min": strategy_specific.signal_period_min,
                        "signal_max": strategy_specific.signal_period_max,
                    },
                )

        # Priority 2: Global CLI parameters (only if strategy-specific not already set)
        if config.fast_period_min is not None and params["fast_min"] is None:
            params["fast_min"] = config.fast_period_min
        if config.fast_period_max is not None and params["fast_max"] is None:
            params["fast_max"] = config.fast_period_max
        if config.slow_period_min is not None and params["slow_min"] is None:
            params["slow_min"] = config.slow_period_min
        if config.slow_period_max is not None and params["slow_max"] is None:
            params["slow_max"] = config.slow_period_max
        if config.signal_period_min is not None and params["signal_min"] is None:
            params["signal_min"] = config.signal_period_min
        if config.signal_period_max is not None and params["signal_max"] is None:
            params["signal_max"] = config.signal_period_max

        # Priority 3: Legacy parameters (for backward compatibility)
        if params["fast_min"] is None and config.short_window_start is not None:
            params["fast_min"] = config.short_window_start
        if params["fast_max"] is None and config.short_window_end is not None:
            params["fast_max"] = config.short_window_end
        if params["slow_min"] is None and config.long_window_start is not None:
            params["slow_min"] = config.long_window_start
        if params["slow_max"] is None and config.long_window_end is not None:
            params["slow_max"] = config.long_window_end
        if params["signal_min"] is None and config.signal_window_start is not None:
            params["signal_min"] = config.signal_window_start
        if params["signal_max"] is None and config.signal_window_end is not None:
            params["signal_max"] = config.signal_window_end

        # Priority 4: Hard-coded defaults per strategy type
        defaults = {
            "SMA": {"fast_min": 5, "fast_max": 88, "slow_min": 8, "slow_max": 89},
            "EMA": {"fast_min": 5, "fast_max": 88, "slow_min": 8, "slow_max": 89},
            "MACD": {
                "fast_min": 5,
                "fast_max": 20,
                "slow_min": 8,
                "slow_max": 34,
                "signal_min": 5,
                "signal_max": 20,
            },
            "ATR": {"fast_min": 5, "fast_max": 30, "slow_min": 10, "slow_max": 50},
            "SMA_ATR": {
                "fast_min": 10,
                "fast_max": 50,
                "slow_min": 20,
                "slow_max": 100,
            },
        }

        strategy_defaults = defaults.get(strategy_value, defaults["SMA"])
        for key, default_value in strategy_defaults.items():
            if params[key] is None:
                params[key] = default_value

        return params

    def _analyze_cached_results(
        self,
        config: StrategyConfig,
        resume_analysis,
    ) -> dict[str, Any]:
        """
        PHASE 1: Analyze cached results from existing CSV files.

        Args:
            config: Strategy configuration
            resume_analysis: Resume analysis results

        Returns:
            Dictionary with comprehensive cached result analysis
        """
        from collections import defaultdict

        import polars as pl

        project_root = Path(get_project_root())
        analysis: dict[str, Any] = {
            "export_summary": defaultdict(
                lambda: {"files": 0, "portfolios": 0, "exists": False},
            ),
            "best_strategies": [],
            "file_paths": [],
            "total_portfolios": 0,
            "ticker_strategies": set(),
        }

        # FIX: Updated export directories to match SmartResumeService and export_csv.py paths
        # Both use data/raw/ as base directory, not data/outputs/
        export_dirs = {
            "Raw Portfolios": ("data/raw/portfolios", ""),
            "Filtered Portfolios": ("data/raw/portfolios_filtered", ""),
            "Metrics Analysis": ("data/raw/portfolios_metrics", ""),
            "Best Strategies": ("data/raw/portfolios_best", ""),
        }

        # Analyze each ticker+strategy combination
        for ticker, strategy in resume_analysis.completed_combinations:
            analysis["ticker_strategies"].add((ticker, strategy))

            # FIX: Handle different filename formats with timeframe suffixes
            # Look for files with patterns like BTC-USD_D_SMA_ATR.csv or BTC-USD_SMA_ATR.csv
            possible_patterns = [
                f"{ticker}_{strategy}.csv",
                f"{ticker}_D_{strategy}.csv",  # Daily timeframe
                f"{ticker}_H_{strategy}.csv",  # Hourly timeframe
                f"{ticker}_4H_{strategy}.csv",  # 4-hour timeframe
                f"{ticker}_2D_{strategy}.csv",  # 2-day timeframe
            ]

            # FIX: Also use glob patterns for more flexible matching
            glob_patterns = [
                f"*{ticker}*{strategy}*.csv",  # Most flexible
                f"{ticker}*{strategy}.csv",  # Ticker prefix
            ]

            # Check each export type
            for export_name, (export_path, _) in export_dirs.items():
                full_dir = project_root / export_path

                # FIX: For best and metrics, check date subdirectories
                if export_name in ["Best Strategies", "Metrics Analysis"]:
                    # First check direct path, then date subdirectories
                    search_dirs = [full_dir]
                    if full_dir.exists():
                        # Add all subdirectories that look like dates (YYYYMMDD)
                        for subdir in full_dir.iterdir():
                            if (
                                subdir.is_dir()
                                and len(subdir.name) == 8
                                and subdir.name.isdigit()
                            ):
                                search_dirs.append(subdir)
                else:
                    search_dirs = [full_dir]

                # FIX: Try multiple filename patterns and directories
                file_found = False
                for search_dir in search_dirs:
                    if not search_dir.exists():
                        continue

                    for pattern in possible_patterns:
                        file_path = search_dir / pattern

                        # Debug logging to diagnose path issues
                        if hasattr(self.console, "debug"):
                            self.console.debug(f"Checking for file: {file_path}")

                        if file_path.exists():
                            file_found = True
                            analysis["export_summary"][export_name]["exists"] = True
                            analysis["export_summary"][export_name]["files"] += 1

                            # Count portfolios in CSV
                            try:
                                df = pl.read_csv(file_path)
                                portfolio_count = len(df)
                                analysis["export_summary"][export_name][
                                    "portfolios"
                                ] += portfolio_count

                                if export_name == "Raw Portfolios":
                                    analysis["total_portfolios"] += portfolio_count

                                # Extract best strategy info from best results
                                if export_name == "Best Strategies" and len(df) > 0:
                                    try:
                                        best_row = df.row(0, named=True)
                                        analysis["best_strategies"].append(
                                            {
                                                "ticker": ticker,
                                                "strategy": strategy,
                                                "fast_period": best_row.get(
                                                    "Fast Period",
                                                    "N/A",
                                                ),
                                                "slow_period": best_row.get(
                                                    "Slow Period",
                                                    "N/A",
                                                ),
                                                "total_return": float(
                                                    best_row.get("Total Return [%]", 0),
                                                ),
                                                "win_rate": float(
                                                    best_row.get("Win Rate [%]", 0),
                                                ),
                                                "max_drawdown": float(
                                                    best_row.get("Max Drawdown [%]", 0),
                                                ),
                                                "total_trades": int(
                                                    best_row.get("Total Trades", 0),
                                                ),
                                            },
                                        )
                                    except (KeyError, ValueError, TypeError) as e:
                                        self.console.warning(
                                            f"Error extracting best strategy from {ticker}_{strategy}: {e}",
                                        )

                                # Add file path
                                analysis["file_paths"].append(
                                    {
                                        "type": export_name,
                                        "path": str(file_path),
                                        "portfolios": portfolio_count,
                                    },
                                )

                                # Only process the first found file to avoid duplicates
                                break

                            except Exception as e:
                                self.console.warning(f"Error reading {file_path}: {e}")

                        if file_found:
                            break  # Stop searching patterns if file was found

                # FIX: If no exact match found, try glob patterns
                if not file_found:
                    for search_dir in search_dirs:
                        if not search_dir.exists():
                            continue

                        for glob_pattern in glob_patterns:
                            matching_files = list(search_dir.glob(glob_pattern))

                            if matching_files:
                                # Use the first matching file
                                file_path = matching_files[0]
                                file_found = True

                                if hasattr(self.console, "debug"):
                                    self.console.debug(
                                        f"Found file via glob pattern: {file_path}",
                                    )

                                analysis["export_summary"][export_name]["exists"] = True
                                analysis["export_summary"][export_name]["files"] += 1

                                # Count portfolios in CSV
                                try:
                                    df = pl.read_csv(file_path)
                                    portfolio_count = len(df)
                                    analysis["export_summary"][export_name][
                                        "portfolios"
                                    ] += portfolio_count

                                    if export_name == "Raw Portfolios":
                                        analysis["total_portfolios"] += portfolio_count

                                    # Extract best strategy info from best results
                                    if export_name == "Best Strategies" and len(df) > 0:
                                        try:
                                            best_row = df.row(0, named=True)
                                            analysis["best_strategies"].append(
                                                {
                                                    "ticker": ticker,
                                                    "strategy": strategy,
                                                    "fast_period": best_row.get(
                                                        "Fast Period",
                                                        "N/A",
                                                    ),
                                                    "slow_period": best_row.get(
                                                        "Slow Period",
                                                        "N/A",
                                                    ),
                                                    "total_return": float(
                                                        best_row.get(
                                                            "Total Return [%]",
                                                            0,
                                                        ),
                                                    ),
                                                    "win_rate": float(
                                                        best_row.get("Win Rate [%]", 0),
                                                    ),
                                                    "max_drawdown": float(
                                                        best_row.get(
                                                            "Max Drawdown [%]",
                                                            0,
                                                        ),
                                                    ),
                                                    "total_trades": int(
                                                        best_row.get("Total Trades", 0),
                                                    ),
                                                },
                                            )
                                        except (KeyError, ValueError, TypeError) as e:
                                            self.console.warning(
                                                f"Error extracting best strategy: {e}",
                                            )

                                    # Add file path
                                    analysis["file_paths"].append(
                                        {
                                            "type": export_name,
                                            "path": str(file_path),
                                            "portfolios": portfolio_count,
                                        },
                                    )

                                    break  # Only use first matching file

                                except Exception as e:
                                    self.console.warning(
                                        f"Error reading {file_path}: {e}",
                                    )

                            if file_found:
                                break

        return analysis

    def _display_cached_results_summary(
        self,
        analysis: dict[str, Any],
        config: StrategyConfig,
    ):
        """
        PHASE 2: Display comprehensive Rich CLI summary for cached results.

        Args:
            analysis: Cached result analysis
            config: Strategy configuration
        """
        console = Console()

        # Export Summary Table
        export_table = Table(
            title="📁 Export Summary",
            show_header=True,
            header_style="bold magenta",
        )
        export_table.add_column("Export Type", style="cyan", no_wrap=True)
        export_table.add_column("Files", justify="center", style="green")
        export_table.add_column("Portfolios", justify="center", style="yellow")
        export_table.add_column("Status", justify="center")

        for export_type, data in analysis["export_summary"].items():
            status = "✅ Complete" if data["exists"] else "❌ Missing"
            export_table.add_row(
                export_type,
                str(data["files"]),
                f"{data['portfolios']:,}",
                status,
            )

        console.print(export_table)
        console.print()

        # Best Strategy Results Panel
        if analysis["best_strategies"]:
            for best_strategy in analysis["best_strategies"]:
                strategy_info = f"{best_strategy['strategy']} ({best_strategy['fast_period']}/{best_strategy['slow_period']})"
                performance = f"+{best_strategy['total_return']:.1f}% Return, {best_strategy['win_rate']:.1f}% Win Rate"
                risk = f"{best_strategy['max_drawdown']:.1f}% Max Drawdown, {best_strategy['total_trades']} Trades"

                best_strategy_panel = Panel.fit(
                    f"[bold cyan]Ticker:[/bold cyan] {best_strategy['ticker']}\n"
                    f"[bold cyan]Strategy:[/bold cyan] {strategy_info}\n"
                    f"[bold green]Performance:[/bold green] {performance}\n"
                    f"[bold yellow]Risk:[/bold yellow] {risk}",
                    title="🏆 Best Strategy Results",
                    border_style="green",
                )
                console.print(best_strategy_panel)
                console.print()

        # File Path Links
        if analysis["file_paths"]:
            console.print("[bold blue]📁 Generated Files:[/bold blue]")
            file_icons = {
                "Raw Portfolios": "📊",
                "Filtered Portfolios": "🔽",
                "Metrics Analysis": "📈",
                "Best Strategies": "🏆",
            }

            # Group files by type for better organization
            files_by_type: dict[str, list[dict[str, Any]]] = {}
            for file_info in analysis["file_paths"]:
                file_type = file_info["type"]
                if file_type not in files_by_type:
                    files_by_type[file_type] = []
                files_by_type[file_type].append(file_info)

            for file_type in [
                "Raw Portfolios",
                "Filtered Portfolios",
                "Metrics Analysis",
                "Best Strategies",
            ]:
                if file_type in files_by_type:
                    icon = file_icons.get(file_type, "📄")
                    total_portfolios = sum(
                        f["portfolios"] for f in files_by_type[file_type]
                    )

                    if len(files_by_type[file_type]) == 1:
                        file_info = files_by_type[file_type][0]
                        # Make path relative for cleaner display
                        relative_path = str(
                            Path(file_info["path"]).relative_to(Path.cwd()),
                        )
                        console.print(
                            f"{icon} [cyan]{file_type}:[/cyan] [link]{relative_path}[/link] [dim]({file_info['portfolios']:,} portfolios)[/dim]",
                        )
                    else:
                        console.print(
                            f"{icon} [cyan]{file_type}:[/cyan] [dim]{len(files_by_type[file_type])} files ({total_portfolios:,} total portfolios)[/dim]",
                        )
            console.print()
        else:
            console.print(
                "[yellow]⚠️  No cached files found - this might indicate an issue with resume detection[/yellow]",
            )
            console.print()

    def _calculate_parameter_combinations(
        self,
        config: StrategyConfig,
        strategy_type: StrategyType | str,
    ) -> int:
        """
        Calculate expected parameter combinations for a strategy type.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to calculate combinations for

        Returns:
            Estimated number of parameter combinations
        """
        try:
            # Convert to string value
            if hasattr(strategy_type, "value"):
                strategy_value = strategy_type.value
            else:
                strategy_value = str(strategy_type).upper()

            # Extract parameters using proper hierarchy
            params = self._extract_strategy_parameters(config, strategy_type)

            if strategy_value in ["SMA", "EMA"]:
                # MA strategies: fast_period × slow_period (with fast < slow constraint)
                fast_min, fast_max = params["fast_min"], params["fast_max"]
                slow_min, slow_max = params["slow_min"], params["slow_max"]

                # Ensure all values are set
                assert fast_min is not None and fast_max is not None
                assert slow_min is not None and slow_max is not None

                # Calculate valid combinations where fast < slow
                total_combinations = 0
                for fast in range(fast_min, fast_max + 1):
                    valid_slow_min = max(fast + 1, slow_min)
                    if valid_slow_min <= slow_max:
                        total_combinations += slow_max - valid_slow_min + 1

                return total_combinations

            if strategy_value == "MACD":
                # MACD strategy: fast_period × slow_period × signal_period (with slow > fast constraint)
                fast_min, fast_max = params["fast_min"], params["fast_max"]
                slow_min, slow_max = params["slow_min"], params["slow_max"]
                signal_min, signal_max = params["signal_min"], params["signal_max"]

                # Ensure all values are set
                assert fast_min is not None and fast_max is not None
                assert slow_min is not None and slow_max is not None
                assert signal_min is not None and signal_max is not None

                # Calculate valid fast/slow combinations where slow > fast
                valid_fast_slow_pairs = 0
                for fast in range(fast_min, fast_max + 1):
                    valid_slow_min = max(fast + 1, slow_min)
                    if valid_slow_min <= slow_max:
                        valid_fast_slow_pairs += slow_max - valid_slow_min + 1

                # Multiply by signal period combinations
                signal_combinations = signal_max - signal_min + 1
                return valid_fast_slow_pairs * signal_combinations

            if strategy_value == "ATR":
                # ATR strategy: Based on ATR-specific parameters or conservative estimate
                if (
                    config.atr_length_min
                    and config.atr_length_max
                    and config.atr_multiplier_min
                    and config.atr_multiplier_max
                ):
                    length_combinations = (
                        config.atr_length_max - config.atr_length_min + 1
                    )
                    multiplier_step = config.atr_multiplier_step or 0.1
                    multiplier_combinations = (
                        int(
                            (config.atr_multiplier_max - config.atr_multiplier_min)
                            / multiplier_step,
                        )
                        + 1
                    )
                    return length_combinations * multiplier_combinations
                return 500  # Conservative estimate for ATR

            if strategy_value == "SMA_ATR":
                # SMA_ATR strategy: Combines SMA periods and ATR parameters
                # Extract parameters using proper hierarchy
                params = self._extract_strategy_parameters(config, strategy_type)

                # Calculate SMA combinations with STEP optimization (fast < slow)
                fast_min, fast_max = params["fast_min"], params["fast_max"]
                slow_min, slow_max = params["slow_min"], params["slow_max"]

                # Ensure all values are set
                assert fast_min is not None and fast_max is not None
                assert slow_min is not None and slow_max is not None

                # Get SMA step size for optimization (critical for performance)
                sma_step = 1  # Default to 1 if not specified
                if (
                    hasattr(config, "strategy_params")
                    and config.strategy_params
                    and hasattr(config.strategy_params, "SMA_ATR")
                    and config.strategy_params.SMA_ATR
                ):
                    sma_step = config.strategy_params.SMA_ATR.step or 1
                elif hasattr(config, "step"):
                    sma_step = config.step or 1

                sma_combinations = 0
                for fast in range(fast_min, fast_max + 1, sma_step):
                    for slow in range(slow_min, slow_max + 1, sma_step):
                        if fast < slow:
                            sma_combinations += 1

                # Calculate ATR combinations using discrete length values if available
                if hasattr(config, "atr_length_range") and config.atr_length_range:
                    # Use discrete ATR length values (optimized)
                    length_combinations = len(config.atr_length_range)
                elif (
                    hasattr(config, "atr_length_min")
                    and hasattr(config, "atr_length_max")
                    and config.atr_length_min is not None
                    and config.atr_length_max is not None
                ):
                    # Fallback to continuous range
                    length_combinations = (
                        config.atr_length_max - config.atr_length_min + 1
                    )
                else:
                    # Default discrete values
                    length_combinations = 6  # [3, 5, 7, 9, 11, 13]

                # Calculate ATR multiplier combinations
                if (
                    hasattr(config, "atr_multiplier_min")
                    and hasattr(config, "atr_multiplier_max")
                    and hasattr(config, "atr_multiplier_step")
                    and config.atr_multiplier_min is not None
                    and config.atr_multiplier_max is not None
                    and config.atr_multiplier_step is not None
                ):
                    multiplier_step = config.atr_multiplier_step
                    multiplier_combinations = (
                        int(
                            (config.atr_multiplier_max - config.atr_multiplier_min)
                            / multiplier_step,
                        )
                        + 1
                    )
                else:
                    # Default multiplier combinations
                    multiplier_combinations = 3  # [1.0, 2.5, 4.0] with step 1.5

                atr_combinations = length_combinations * multiplier_combinations
                total = sma_combinations * atr_combinations

                # Debug logging for parameter calculation
                if hasattr(self.console, "debug"):
                    self.console.debug("SMA_ATR parameter calculation:")
                    self.console.debug(
                        f"  SMA combinations (step={sma_step}): {sma_combinations}",
                    )
                    self.console.debug(
                        f"  ATR length combinations: {length_combinations}",
                    )
                    self.console.debug(
                        f"  ATR multiplier combinations: {multiplier_combinations}",
                    )
                    self.console.debug(f"  Total: {total}")

                return total

            # Unknown strategy type - return conservative estimate
            return 100

        except Exception:
            # If calculation fails, return conservative estimate
            return 100

    def _calculate_actual_current_signal_combinations(
        self,
        config: StrategyConfig,
        strategy_type: StrategyType | str,
    ) -> int:
        """
        Calculate actual current signal combinations when USE_CURRENT mode is enabled.

        This pre-analyzes current signals across all configured tickers to determine
        the exact number of combinations that will be processed, providing accurate
        progress tracking for USE_CURRENT mode.

        Args:
            config: Strategy configuration model
            strategy_type: Strategy type to analyze

        Returns:
            Actual number of current signal combinations across all tickers
        """
        try:
            from app.tools.strategy.signal_processing import SignalProcessorFactory

            # Convert to string value
            if hasattr(strategy_type, "value"):
                strategy_value = strategy_type.value
            else:
                strategy_value = str(strategy_type).upper()

            # Create signal processor for this strategy type
            processor = SignalProcessorFactory.create_processor(strategy_value)

            # Convert config to legacy format for signal processing
            legacy_config = self._convert_strategy_config_to_legacy(config)

            # Get ticker list
            tickers = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            total_current_signals = 0

            # Pre-analyze current signals for each ticker
            for ticker in tickers:
                try:
                    # Create ticker-specific config
                    ticker_config = legacy_config.copy()
                    ticker_config["TICKER"] = ticker

                    # DEBUG: Check if parameter ranges are present
                    self.console.debug(
                        f"Ticker {ticker} config has FAST_PERIOD_RANGE: {ticker_config.get('FAST_PERIOD_RANGE')}",
                    )
                    self.console.debug(
                        f"Ticker {ticker} config has SLOW_PERIOD_RANGE: {ticker_config.get('SLOW_PERIOD_RANGE')}",
                    )

                    # Generate current signals for this ticker
                    current_signals = processor.generate_current_signals(
                        ticker_config,
                        lambda msg, level="info": getattr(self.console, level)(msg),
                    )

                    signal_count = (
                        len(current_signals) if current_signals is not None else 0
                    )
                    total_current_signals += signal_count

                    self.console.debug(
                        f"Ticker {ticker}: {signal_count} current signals",
                    )

                except Exception as e:
                    self.console.warning(
                        f"Failed to pre-analyze signals for {ticker}: {e}",
                    )
                    # Continue with other tickers
                    continue

            return total_current_signals

        except Exception as e:
            self.console.error(
                f"Error calculating actual current signal combinations: {e}",
            )
            # Fallback to theoretical calculation as conservative estimate
            ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1
            combinations_per_ticker = self._calculate_parameter_combinations(
                config,
                strategy_type,
            )
            return ticker_count * combinations_per_ticker

    def execute_strategy(self, config: StrategyConfig) -> StrategyExecutionSummary:
        """
        Execute strategy analysis using appropriate service.

        For mixed strategy types, executes each strategy sequentially to ensure
        all requested strategies generate their respective CSV files.

        Args:
            config: Strategy configuration model

        Returns:
            StrategyExecutionSummary with comprehensive execution results
        """
        start_time = time.time()

        # Initialize execution summary
        summary = StrategyExecutionSummary(
            execution_time=0.0,
            success_rate=0.0,
            successful_strategies=0,
            total_strategies=0,
            tickers_processed=[],
            strategy_types=[],
        )

        # Batch Processing Logic
        if getattr(config, "batch", False):
            batch_size = getattr(config, "batch_size", None)
            batch_file_path = getattr(config, "batch_file_path", "data/raw/batch.csv")

            if batch_size is None:
                self.console.error(
                    "Batch size must be specified when batch mode is enabled",
                )
                summary.execution_time = time.time() - start_time
                return summary

            # Initialize batch service
            self.batch_service = BatchProcessingService(
                batch_file_path=batch_file_path,
                console=self.console,
            )

            # Validate batch file
            if not self.batch_service.validate_batch_file():
                self.console.error("Batch file validation failed")
                summary.execution_time = time.time() - start_time
                return summary

            # Get original ticker list
            original_tickers = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            # Clean old entries from batch file
            cleaned_count = self.batch_service.clean_old_entries()
            if cleaned_count > 0:
                self.console.info(
                    f"Cleaned {cleaned_count} old entries from batch file",
                )

            # Create resume check function for smart batch selection
            def resume_check_function(ticker: str) -> bool:
                """Check if a ticker needs processing based on resume analysis."""
                if getattr(config, "refresh", False):
                    # If refresh is enabled, all tickers need processing
                    return True

                # Create single-ticker config for resume analysis
                single_ticker_config = config.model_copy(deep=True)
                single_ticker_config.ticker = ticker
                single_ticker_config.batch = False

                # Convert to legacy format and analyze
                legacy_config = self._convert_strategy_config_to_legacy(
                    single_ticker_config,
                )
                ticker_resume_analysis = self.resume_service.analyze_resume_status(
                    legacy_config,
                )

                # Return True if ticker needs processing (not complete)
                return not ticker_resume_analysis.is_complete()

            # Get tickers that actually need processing using resume-aware selection
            pending_tickers = self.batch_service.get_tickers_needing_processing(
                original_tickers,
                batch_size,
                resume_check_function,
            )

            if not pending_tickers:
                self.console.success(
                    "All tickers have been processed today. Nothing to do.",
                )
                summary.execution_time = time.time() - start_time
                summary.success_rate = 1.0
                summary.tickers_processed = []
                return summary

            # Display batch status
            self.batch_service.display_batch_status(original_tickers)

            # Update config with batch-selected tickers
            config.ticker = pending_tickers

            self.console.heading(
                f"Batch Processing: {len(pending_tickers)} tickers",
                level=2,
            )
            self.console.info(f"Processing tickers: {', '.join(pending_tickers)}")

            # Resume analysis summary for selected tickers
            self.console.info(
                f"📋 Resume Analysis: ✓ Selected {len(pending_tickers)} tickers that need processing",
            )

        # Smart Resume Analysis (unless refresh is enabled or in batch mode)
        # Skip resume analysis for batch mode since it's already handled during batch selection
        if not getattr(config, "refresh", False) and not getattr(
            config,
            "batch",
            False,
        ):
            # Convert StrategyConfig to legacy format for resume analysis
            legacy_config = self._convert_strategy_config_to_legacy(config)

            # Analyze what work has already been completed
            resume_analysis = self.resume_service.analyze_resume_status(legacy_config)

            # Show resume summary
            resume_summary = self.resume_service.get_resume_summary(resume_analysis)
            self.console.info(f"📋 Resume Analysis: {resume_summary}")

            # If everything is complete, skip execution with ENHANCED CLI OUTPUT
            if resume_analysis.is_complete():
                self.console.success(
                    "🎉 All analysis is complete and up-to-date! Skipping execution.",
                )

                # PHASE 1 & 2: Analyze cached results and display Rich CLI summary
                try:
                    cached_analysis = self._analyze_cached_results(
                        config,
                        resume_analysis,
                    )
                    self._display_cached_results_summary(cached_analysis, config)

                    # Update summary with actual portfolio count from cached analysis
                    summary.total_portfolios_generated = cached_analysis.get(
                        "total_portfolios",
                        0,
                    )
                except Exception as e:
                    self.console.warning(f"Error analyzing cached results: {e}")

                summary.execution_time = time.time() - start_time
                summary.success_rate = 1.0
                summary.successful_strategies = len(config.strategy_types)
                summary.total_strategies = len(config.strategy_types)
                summary.strategy_types = [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
                summary.tickers_processed = (
                    config.ticker
                    if isinstance(config.ticker, list)
                    else [config.ticker]
                )
                return summary

            # Filter config to only process remaining work
            filtered_legacy_config = self.resume_service.filter_config_for_resume(
                legacy_config,
                resume_analysis,
            )

            # Convert back to StrategyConfig format
            config = self._convert_legacy_to_strategy_config(
                filtered_legacy_config,
                config,
            )

            if filtered_legacy_config.get("_RESUME_SKIP_ALL", False):
                self.console.success(
                    "🎉 All analysis is complete and up-to-date! Skipping execution.",
                )

                # PHASE 1 & 2: Enhanced CLI output for secondary skip check
                try:
                    cached_analysis = self._analyze_cached_results(
                        config,
                        resume_analysis,
                    )
                    self._display_cached_results_summary(cached_analysis, config)

                    # Update summary with actual portfolio count from cached analysis
                    summary.total_portfolios_generated = cached_analysis.get(
                        "total_portfolios",
                        0,
                    )
                except Exception as e:
                    self.console.warning(f"Error analyzing cached results: {e}")

                summary.execution_time = time.time() - start_time
                summary.success_rate = 1.0
                summary.successful_strategies = len(config.strategy_types)
                summary.total_strategies = len(config.strategy_types)
                return summary

        # Display enhanced strategy header
        ticker_str = (
            ", ".join(config.ticker)
            if isinstance(config.ticker, list)
            else str(config.ticker)
        )
        strategy_names = [
            st.value if hasattr(st, "value") else str(st)
            for st in config.strategy_types
        ]

        self.console.strategy_header(
            ticker=ticker_str,
            strategy_types=strategy_names,
            profile=getattr(config, "profile_name", None),
        )

        # Start performance monitoring if using PerformanceAwareConsoleLogger
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            # Estimate total phases based on configuration
            total_phases = 1  # Always have strategy execution phase
            if not config.skip_analysis:
                total_phases += 2  # Data download + backtesting phases
            total_phases += 2  # Portfolio processing + file export phases

            self.console.info(
                f"🎯 Starting strategy execution with {total_phases} phases",
            )
        # Check if we should skip analysis and run portfolio processing only
        if config.skip_analysis:
            if isinstance(self.console, PerformanceAwareConsoleLogger):
                with self.console.performance_context(
                    "portfolio_processing",
                    "Processing existing portfolios",
                    5.0,
                ) as phase:
                    success = self._execute_skip_analysis_mode(config)
                    phase.add_detail("portfolios_processed", "existing")
            else:
                self.console.info(
                    "Skip analysis mode enabled - processing existing portfolios",
                )
                success = self._execute_skip_analysis_mode(config)

            summary.execution_time = time.time() - start_time
            summary.success_rate = 1.0 if success else 0.0
            summary.successful_strategies = 1 if success else 0
            summary.total_strategies = 1
            return summary

        # Handle mixed strategy types by executing each strategy individually
        if len(config.strategy_types) > 1:
            return self._execute_mixed_strategies(config, summary, start_time)

        # Handle batch processing by processing tickers individually
        if getattr(config, "batch", False) and self.batch_service:
            return self._execute_batch_processing(config, summary, start_time)

        # Single strategy: use original logic
        strategy_service = self._determine_single_service(config.strategy_types[0])

        if not strategy_service:
            self.console.error(
                "No compatible service found for specified strategy type",
            )
            summary.execution_time = time.time() - start_time
            summary.success_rate = 0.0
            summary.total_strategies = 1
            return summary

        # Execute using the determined service with holistic progress tracking
        if isinstance(self.console, PerformanceAwareConsoleLogger):
            strategy_name = (
                config.strategy_types[0].value
                if hasattr(config.strategy_types[0], "value")
                else str(config.strategy_types[0])
            )

            # Calculate total combinations across all tickers for holistic progress
            ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1

            if config.use_current:
                # When USE_CURRENT is enabled, calculate actual current signal combinations
                self.console.info(
                    "🔍 Pre-analyzing current signals to calculate accurate progress...",
                )
                actual_combinations = (
                    self._calculate_actual_current_signal_combinations(
                        config,
                        config.strategy_types[0],
                    )
                )
                total_combinations = actual_combinations
                self.console.info(
                    f"📊 Current signal combinations found: {total_combinations:,} (filtered from theoretical maximum)",
                )
            else:
                # Use theoretical combinations for full parameter sweeps
                combinations_per_ticker = self._calculate_parameter_combinations(
                    config,
                    config.strategy_types[0],
                )
                total_combinations = ticker_count * combinations_per_ticker
                self.console.info(
                    f"📊 Total parameter combinations: {total_combinations:,}",
                )

            # Use holistic progress context that will be updated by actual work
            progress_description = f"🚀 {strategy_name} strategy ({total_combinations:,} parameters across {ticker_count} tickers)"
            if config.use_current:
                progress_description += " - current signals only"

            with self.console.progress_context(progress_description) as progress:
                # Use determinate progress bar - signal processing already calculates correct increments
                task_description = (
                    f"Analyzing {total_combinations:,} parameter combinations"
                )
                if config.use_current:
                    task_description += " for current signals"

                task = progress.add_task(task_description, total=total_combinations)

                completed_combinations = 0

                # Create progress update function that services can call directly
                def update_progress(combinations_completed: int):
                    nonlocal completed_combinations
                    completed_combinations += combinations_completed
                    progress.update(task, completed=completed_combinations)

                # Execute strategy with progress update function
                success = strategy_service.execute_strategy(
                    config,
                    progress_update_fn=update_progress,
                )

                # Validate progress reached expected total
                if completed_combinations < total_combinations:
                    # Note: This is expected - progress checkpoints are saved at intervals
                    # for performance. All combinations are still analyzed.
                    self.console.debug(
                        f"Progress checkpoints: {completed_combinations}/{total_combinations} saved (all combinations analyzed)",
                    )
                    # Force progress bar to 100% to avoid visual confusion
                    progress.update(task, completed=total_combinations)
        else:
            # Execute without progress tracking for basic console
            success = strategy_service.execute_strategy(config)

        # Populate summary for single strategy execution
        summary.execution_time = time.time() - start_time
        summary.success_rate = 1.0 if success else 0.0
        summary.successful_strategies = 1 if success else 0
        summary.total_strategies = 1
        summary.strategy_types = [
            (
                config.strategy_types[0].value
                if hasattr(config.strategy_types[0], "value")
                else str(config.strategy_types[0])
            ),
        ]

        # Process tickers
        if isinstance(config.ticker, list):
            summary.tickers_processed = config.ticker
        else:
            summary.tickers_processed = [config.ticker]

        # Extract actual portfolio results from generated files
        if success:
            portfolio_result = self._extract_portfolio_results_from_files(
                ticker=(
                    summary.tickers_processed[0]
                    if summary.tickers_processed
                    else "Unknown"
                ),
                strategy_type=summary.strategy_types[0],
                config=config,
            )
            summary.add_portfolio_result(portfolio_result)

        return summary

    def _extract_portfolio_results_from_files(
        self,
        ticker: str,
        strategy_type: str,
        config: StrategyConfig,
    ) -> StrategyPortfolioResults:
        """
        Extract actual portfolio results by reading generated CSV files.

        Args:
            ticker: Ticker symbol
            strategy_type: Strategy type string
            config: Strategy configuration

        Returns:
            StrategyPortfolioResults with actual counts and best configuration
        """
        from pathlib import Path

        import pandas as pd

        # Determine timeframe suffix
        if config.use_4hour:
            timeframe = "4H"
        elif config.use_2day:
            timeframe = "2D"
        elif config.use_hourly:
            timeframe = "H"
        else:
            timeframe = "D"

        # Build file paths
        base_dir = Path(config.base_dir)
        file_base = f"{ticker}_{timeframe}_{strategy_type}"

        portfolios_file = base_dir / "data/raw/portfolios" / f"{file_base}.csv"
        filtered_file = base_dir / "data/raw/portfolios_filtered" / f"{file_base}.csv"
        metrics_file = base_dir / "data/raw/portfolios_metrics" / f"{file_base}.csv"
        best_file = base_dir / "data/raw/portfolios_best" / f"{file_base}.csv"

        # Initialize result
        result = StrategyPortfolioResults(
            ticker=ticker,
            strategy_type=strategy_type,
            total_portfolios=0,
            filtered_portfolios=0,
            extreme_value_portfolios=0,
            files_exported=[],
        )

        # Extract counts from files
        try:
            if portfolios_file.exists():
                df = pd.read_csv(portfolios_file)
                result.total_portfolios = len(df)
                result.files_exported.append(str(portfolios_file))

            if filtered_file.exists():
                df = pd.read_csv(filtered_file)
                result.filtered_portfolios = len(df)
                result.files_exported.append(str(filtered_file))

            if metrics_file.exists():
                df = pd.read_csv(metrics_file)
                result.extreme_value_portfolios = len(df)
                result.files_exported.append(str(metrics_file))

            # Extract best configuration and metrics from portfolios_best
            if best_file.exists():
                df = pd.read_csv(best_file)
                result.files_exported.append(str(best_file))

                if len(df) > 0:
                    best_row = df.iloc[0]

                    # Build best config string based on strategy type
                    fast = best_row.get("Fast Period", "")
                    slow = best_row.get("Slow Period", "")
                    exit_fast = best_row.get("Exit Fast Period")
                    exit_slow = best_row.get("Exit Slow Period")

                    if strategy_type == "SMA_ATR":
                        # Include exit parameters for hybrid strategies
                        if pd.notna(exit_fast) and pd.notna(exit_slow):
                            result.best_config = f"{fast}/{slow} + ATR({int(exit_fast)}, {exit_slow:.1f})"
                        else:
                            result.best_config = f"{fast}/{slow}"
                    elif strategy_type in ["SMA", "EMA"]:
                        result.best_config = f"{fast}/{slow}"
                    elif strategy_type == "MACD":
                        signal = best_row.get("Signal Period", "")
                        result.best_config = f"{fast}/{slow}/{signal}"
                    elif strategy_type == "ATR":
                        # ATR strategy uses exit parameters as primary params
                        if pd.notna(exit_fast) and pd.notna(exit_slow):
                            result.best_config = (
                                f"ATR({int(exit_fast)}, {exit_slow:.1f})"
                            )
                        else:
                            result.best_config = "ATR"

                    # Extract performance metrics
                    result.best_score = best_row.get("Score", None)
                    win_rate_pct = best_row.get("Win Rate [%]", None)
                    if win_rate_pct is not None:
                        result.win_rate = float(win_rate_pct) / 100.0

                    result.avg_win = best_row.get("Avg Winning Trade [%]", None)
                    result.avg_loss = best_row.get("Avg Losing Trade [%]", None)

        except Exception as e:
            self.console.debug(f"Error extracting portfolio results: {e}")

        return result

    def _execute_mixed_strategies(
        self,
        config: StrategyConfig,
        summary: StrategyExecutionSummary,
        start_time: float,
    ) -> StrategyExecutionSummary:
        """
        Execute multiple strategy types sequentially.

        This ensures that each strategy type (SMA, EMA, MACD, ATR) generates
        its own separate CSV files as required.

        Args:
            config: Strategy configuration with multiple strategy types
            summary: StrategyExecutionSummary object to populate
            start_time: Execution start time for timing calculations

        Returns:
            StrategyExecutionSummary with comprehensive execution results
        """
        results = []
        summary.total_strategies = len(config.strategy_types)
        summary.strategy_types = [
            st.value if hasattr(st, "value") else str(st)
            for st in config.strategy_types
        ]

        # Process tickers
        if isinstance(config.ticker, list):
            summary.tickers_processed = config.ticker
        else:
            summary.tickers_processed = [config.ticker]

        self.console.heading(
            f"Executing {len(config.strategy_types)} strategies",
            level=2,
        )

        # Calculate total combinations across all strategies and tickers for holistic progress
        ticker_count = len(config.ticker) if isinstance(config.ticker, list) else 1
        use_current_mode = getattr(config, "use_current", False)

        if use_current_mode:
            # When USE_CURRENT is enabled, calculate actual current signal combinations for all strategies
            self.console.info(
                "🔍 Pre-analyzing current signals across all strategies to calculate accurate progress...",
            )
            total_combinations = 0
            strategy_details = []

            for strategy_type in config.strategy_types:
                actual_combinations = (
                    self._calculate_actual_current_signal_combinations(
                        config,
                        strategy_type,
                    )
                )
                total_combinations += actual_combinations
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )
                strategy_details.append(f"{strategy_name}")
                self.console.debug(
                    f"{strategy_name}: {actual_combinations} current signals",
                )

            self.console.info(
                f"📊 Current signal combinations across all strategies: {total_combinations:,} (filtered from theoretical maximum)",
            )
        else:
            # Use theoretical combinations for full parameter sweeps
            total_combinations = 0
            strategy_details = []

            for strategy_type in config.strategy_types:
                combinations = self._calculate_parameter_combinations(
                    config,
                    strategy_type,
                )
                total_combinations += ticker_count * combinations
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )
                strategy_details.append(f"{strategy_name}")

            self.console.info(
                f"📊 Total parameter combinations across all strategies: {total_combinations:,}",
            )

        # Execute strategies with holistic progress tracking
        # Show progress bar for parameter sweeps (>10 combinations) OR USE_CURRENT mode (always valuable)
        should_show_progress = isinstance(
            self.console,
            PerformanceAwareConsoleLogger,
        ) and (total_combinations > 10 or use_current_mode)

        if should_show_progress:
            ", ".join(strategy_details)
            progress_description = f"📊 Processing {total_combinations:,} combinations across {len(config.strategy_types)} strategies × {ticker_count} tickers"
            if use_current_mode:
                progress_description += " - current signals only"

            with self.console.progress_context(progress_description) as progress:
                # Use determinate progress bar - signal processing already calculates correct increments
                task_description = (
                    f"Analyzing {total_combinations:,} parameter combinations"
                )
                if use_current_mode:
                    task_description += " for current signals"

                task = progress.add_task(task_description, total=total_combinations)

                completed_combinations = 0

                # Create progress update function for holistic tracking
                def update_progress(combinations_completed: int):
                    nonlocal completed_combinations
                    completed_combinations += combinations_completed
                    progress.update(task, completed=completed_combinations)

                # Store global progress allocation for accurate multi-ticker progress calculation
                ticker_count = (
                    len(config.ticker) if isinstance(config.ticker, list) else 1
                )
                global_progress_per_ticker = (
                    total_combinations / ticker_count
                    if ticker_count > 0
                    else total_combinations
                )

                # Execute each strategy with progress update function
                for _i, strategy_type in enumerate(config.strategy_types):
                    strategy_name = (
                        strategy_type.value
                        if hasattr(strategy_type, "value")
                        else str(strategy_type)
                    )

                    # Create single-strategy config
                    single_config = self._create_single_strategy_config(
                        config,
                        strategy_type,
                    )

                    # Add global progress allocation for accurate multi-ticker progress
                    if hasattr(single_config, "__dict__"):
                        single_config.__dict__["_GLOBAL_PROGRESS_PER_TICKER"] = (
                            global_progress_per_ticker
                        )
                    else:
                        # Fallback for dict-like configs
                        single_config._GLOBAL_PROGRESS_PER_TICKER = (
                            global_progress_per_ticker
                        )

                    # Get appropriate service for this strategy type
                    service = self._determine_single_service(strategy_type)

                    if not service:
                        self.console.error(
                            f"No service found for strategy type: {strategy_type}",
                        )
                        results.append(False)
                        continue

                    # Execute strategy with progress update function
                    success = service.execute_strategy(
                        single_config,
                        progress_update_fn=update_progress,
                    )
                    results.append(success)

                    # Create portfolio result for this strategy execution
                    if success:
                        portfolio_result = self._extract_portfolio_results_from_files(
                            ticker=(
                                summary.tickers_processed[0]
                                if summary.tickers_processed
                                else "Unknown"
                            ),
                            strategy_type=(
                                strategy_type.value
                                if hasattr(strategy_type, "value")
                                else str(strategy_type)
                            ),
                            config=single_config,
                        )
                        summary.add_portfolio_result(portfolio_result)

                        self.console.success(
                            f"{strategy_type} strategy completed successfully",
                        )
                    else:
                        self.console.error(f"{strategy_type} strategy failed")

                # Validate progress reached expected total after all strategies
                if completed_combinations < total_combinations:
                    # Note: This is expected - progress checkpoints are saved at intervals
                    # for performance. All combinations are still analyzed.
                    self.console.debug(
                        f"Progress checkpoints: {completed_combinations}/{total_combinations} saved (all combinations analyzed)",
                    )
                    # Force progress bar to 100% to avoid visual confusion
                    progress.update(task, completed=total_combinations)
        else:
            # Fallback execution without holistic progress for small jobs or basic console
            for _i, strategy_type in enumerate(config.strategy_types):
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )

                # Create single-strategy config
                single_config = self._create_single_strategy_config(
                    config,
                    strategy_type,
                )

                # Get appropriate service for this strategy type
                service = self._determine_single_service(strategy_type)

                if not service:
                    self.console.error(
                        f"No service found for strategy type: {strategy_type}",
                    )
                    results.append(False)
                    continue

                # Execute strategy without progress callback
                success = service.execute_strategy(single_config)
                results.append(success)

                # Create portfolio result for this strategy execution
                if success:
                    portfolio_result = self._extract_portfolio_results_from_files(
                        ticker=(
                            summary.tickers_processed[0]
                            if summary.tickers_processed
                            else "Unknown"
                        ),
                        strategy_type=(
                            strategy_type.value
                            if hasattr(strategy_type, "value")
                            else str(strategy_type)
                        ),
                        config=single_config,
                    )
                    summary.add_portfolio_result(portfolio_result)

                    self.console.success(
                        f"{strategy_type} strategy completed successfully",
                    )
                else:
                    self.console.error(f"{strategy_type} strategy failed")

        all(results)
        successful_count = sum(results)

        # Update summary with final statistics
        summary.successful_strategies = successful_count
        summary.success_rate = successful_count / len(results) if results else 0.0
        summary.execution_time = time.time() - start_time

        # Show completion summary with enhanced formatting
        if successful_count == len(results):
            self.console.completion_banner(
                f"All {len(results)} strategies completed successfully",
            )
            # Show basic results summary
            self.console.results_summary_table(
                portfolios_generated=successful_count,
                files_exported=len(results)
                * 4,  # Estimate: base, filtered, metrics, best
            )
        else:
            self.console.warning(
                f"Mixed results: {successful_count}/{len(results)} strategies successful",
            )

        return summary

    def _create_single_strategy_config(
        self,
        original_config: StrategyConfig,
        strategy_type: StrategyType | str,
    ) -> StrategyConfig:
        """
        Create a single-strategy configuration from a multi-strategy config.

        Args:
            original_config: Original configuration with multiple strategies
            strategy_type: Single strategy type to create config for

        Returns:
            New StrategyConfig with only the specified strategy type
        """
        # Import here to avoid circular imports
        from copy import deepcopy

        # Create a deep copy of the original config
        single_config = deepcopy(original_config)

        # Ensure strategy_type is a StrategyType enum
        if isinstance(strategy_type, str):
            # Convert string to StrategyType enum
            strategy_enum = StrategyType(strategy_type.upper())
        else:
            strategy_enum = strategy_type

        # Set strategy_types to contain only the current strategy
        single_config.strategy_types = [strategy_enum]

        return single_config

    def _determine_single_service(
        self,
        strategy_type: StrategyType | str,
    ) -> BaseStrategyService | None:
        """
        Determine service for a single strategy type.

        Args:
            strategy_type: Single strategy type

        Returns:
            Appropriate service or None if not found
        """
        # Convert to string value
        if hasattr(strategy_type, "value"):
            strategy_value = strategy_type.value
        else:
            strategy_value = str(strategy_type).upper()

        # Route to appropriate service
        if strategy_value == StrategyType.MACD.value:
            return self._services["MACD"]
        if strategy_value in [StrategyType.SMA.value, StrategyType.EMA.value]:
            return self._services["MA"]
        if strategy_value == StrategyType.ATR.value:
            return self._services["ATR"]
        if strategy_value == StrategyType.SMA_ATR.value:
            return self._services["SMA_ATR"]
        if strategy_value == StrategyType.COMP.value:
            return self._services["COMP"]
        self.console.error(f"Unsupported strategy type: {strategy_value}")
        return None

    def _determine_service(
        self,
        strategy_types: list[StrategyType | str],
    ) -> BaseStrategyService | None:
        """
        Determine which service to use based on strategy types.

        Args:
            strategy_types: List of strategy types from configuration

        Returns:
            Appropriate strategy service or None if no match
        """
        # Convert strategy types to string values (handle both enum and string inputs)
        strategy_type_values = []
        for st in strategy_types:
            if hasattr(st, "value"):  # StrategyType enum
                strategy_type_values.append(st.value)
            else:  # String - convert to uppercase for case-insensitive matching
                strategy_type_values.append(str(st).upper())

        # Check for MACD strategy
        if StrategyType.MACD.value in strategy_type_values:
            if len(strategy_types) > 1:
                self.console.warning(
                    "Multiple strategy types specified with MACD. Using MACD service.",
                )
            return self._services["MACD"]

        # Check for MA strategies (SMA, EMA)
        ma_strategies = [StrategyType.SMA.value, StrategyType.EMA.value]
        if any(st in strategy_type_values for st in ma_strategies):
            return self._services["MA"]

        # Check for ATR strategy
        if StrategyType.ATR.value in strategy_type_values:
            if len(strategy_types) > 1:
                self.console.warning(
                    "Multiple strategy types specified with ATR. Using mixed strategy execution.",
                )
            return self._services["ATR"]

        # Check for SMA_ATR strategy
        if StrategyType.SMA_ATR.value in strategy_type_values:
            if len(strategy_types) > 1:
                self.console.warning(
                    "Multiple strategy types specified with SMA_ATR. Using mixed strategy execution.",
                )
            return self._services["SMA_ATR"]

        # Check for COMP strategy
        if StrategyType.COMP.value in strategy_type_values:
            if len(strategy_types) > 1:
                self.console.warning(
                    "Multiple strategy types specified with COMP. Using mixed strategy execution.",
                )
            return self._services["COMP"]

        # No compatible service found
        self.console.error(f"Unsupported strategy types: {strategy_type_values}")
        self.console.debug(
            "Supported strategy types: SMA, EMA, MACD, ATR, SMA_ATR, COMP",
        )
        return None

    def get_available_services(self) -> list[str]:
        """Get list of available strategy services."""
        return list(self._services.keys())

    def get_supported_strategy_types(self) -> dict[str, list[str]]:
        """Get mapping of services to their supported strategy types."""
        return {
            service_name: service.get_supported_strategy_types()
            for service_name, service in self._services.items()
        }

    def validate_strategy_compatibility(
        self,
        strategy_types: list[StrategyType | str],
    ) -> bool:
        """
        Validate that strategy types are compatible with available services.

        For mixed strategies, validates that each individual strategy type
        is supported by an available service.

        Args:
            strategy_types: List of strategy types to validate

        Returns:
            True if all strategy types are compatible, False otherwise
        """
        # For mixed strategies, validate each one individually
        if len(strategy_types) > 1:
            return all(
                self._determine_single_service(strategy_type) is not None
                for strategy_type in strategy_types
            )

        # For single strategy, use original logic
        return self._determine_service(strategy_types) is not None

    def _execute_skip_analysis_mode(self, config: StrategyConfig) -> bool:
        """
        Execute skip analysis mode - load existing portfolios and process them.

        Args:
            config: Strategy configuration model

        Returns:
            True if portfolio processing successful, False otherwise
        """
        try:
            from app.tools.logging_context import logging_context
            from app.tools.orchestration import PortfolioOrchestrator

            # Convert config to legacy format for PortfolioOrchestrator
            legacy_config = self._convert_config_to_legacy_for_skip_mode(config)

            # Create PortfolioOrchestrator and run in skip mode
            with logging_context("strategy_dispatcher", "skip_analysis.log") as log:
                orchestrator = PortfolioOrchestrator(log)
                return orchestrator.run(legacy_config)

        except Exception as e:
            self.console.error(f"Error in skip analysis mode: {e}")
            return False

    def _convert_config_to_legacy_for_skip_mode(
        self,
        config: StrategyConfig,
    ) -> dict[str, Any]:
        """
        Convert StrategyConfig to legacy format for PortfolioOrchestrator in skip mode.

        Args:
            config: Strategy configuration model

        Returns:
            Dictionary in legacy config format with skip_analysis enabled
        """
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Create minimal legacy config for skip mode
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "BASE_DIR": str(config.base_dir),  # Required for CSV export
            "skip_analysis": True,  # Ensure skip mode is enabled
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
            "MINIMUMS": {},
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

        # Add minimum criteria
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"]["EXPECTANCY_PER_TRADE"] = (
                config.minimums.expectancy_per_trade
            )
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

        return legacy_config

    def _convert_strategy_config_to_legacy(
        self,
        config: StrategyConfig,
    ) -> dict[str, Any]:
        """
        Convert StrategyConfig to legacy format for resume analysis.

        Args:
            config: Strategy configuration model

        Returns:
            Legacy configuration dictionary
        """
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Base legacy config
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "BASE_DIR": str(config.base_dir),
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
            "USE_CURRENT": config.use_current,
            "USE_DATE": (
                getattr(config.filter, "date_filter", None)
                if hasattr(config, "filter")
                else None
            ),
            "DIRECTION": getattr(config, "direction", "Long"),
            "REFRESH": getattr(config, "refresh", True),
        }

        # Handle synthetic mode
        if config.synthetic.use_synthetic:
            legacy_config["USE_SYNTHETIC"] = True
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
            legacy_config["TICKER_2"] = config.synthetic.ticker_2

        # Add parameter ranges for strategy processing
        def get_strategy_specific_params(strategy_type: str):
            """Extract strategy-specific parameters with fallback to global parameters."""
            if config.strategy_params and hasattr(
                config.strategy_params,
                strategy_type,
            ):
                strategy_params = getattr(config.strategy_params, strategy_type)
                if strategy_params:
                    return strategy_params
            return None

        # Check supported strategy types (SMA, EMA for MA strategies)
        strategy_types_to_check = ["SMA", "EMA", "MACD", "ATR", "SMA_ATR"]
        strategy_params_found = None

        for strategy_type in strategy_types_to_check:
            if strategy_type in [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ]:
                strategy_params_found = get_strategy_specific_params(strategy_type)
                if strategy_params_found:
                    break

        # Fast period range mapping - prioritize CLI overrides
        if config.fast_period_min is not None and config.fast_period_max is not None:
            legacy_config["FAST_PERIOD_RANGE"] = (
                config.fast_period_min,
                config.fast_period_max,
            )
        elif (
            strategy_params_found
            and strategy_params_found.fast_period_min is not None
            and strategy_params_found.fast_period_max is not None
        ):
            legacy_config["FAST_PERIOD_RANGE"] = (
                strategy_params_found.fast_period_min,
                strategy_params_found.fast_period_max,
            )
        elif config.fast_period_range:
            legacy_config["FAST_PERIOD_RANGE"] = config.fast_period_range

        # Slow period range mapping - prioritize CLI overrides
        if config.slow_period_min is not None and config.slow_period_max is not None:
            legacy_config["SLOW_PERIOD_RANGE"] = (
                config.slow_period_min,
                config.slow_period_max,
            )
        elif (
            strategy_params_found
            and strategy_params_found.slow_period_min is not None
            and strategy_params_found.slow_period_max is not None
        ):
            legacy_config["SLOW_PERIOD_RANGE"] = (
                strategy_params_found.slow_period_min,
                strategy_params_found.slow_period_max,
            )
        elif config.slow_period_range:
            legacy_config["SLOW_PERIOD_RANGE"] = config.slow_period_range

        # Add specific periods if provided
        if config.fast_period:
            legacy_config["FAST_PERIOD"] = config.fast_period
        if config.slow_period:
            legacy_config["SLOW_PERIOD"] = config.slow_period

        return legacy_config

    def _convert_legacy_to_strategy_config(
        self,
        legacy_config: dict[str, Any],
        original_config: StrategyConfig,
    ) -> StrategyConfig:
        """
        Convert filtered legacy config back to StrategyConfig format.

        Args:
            legacy_config: Filtered legacy configuration
            original_config: Original StrategyConfig for reference

        Returns:
            Updated StrategyConfig with filtered ticker/strategy lists
        """
        from copy import deepcopy

        # Create a deep copy of the original config
        filtered_config = deepcopy(original_config)

        # Update with filtered values
        filtered_tickers = legacy_config.get("TICKER", [])
        if filtered_tickers:
            filtered_config.ticker = (
                filtered_tickers if len(filtered_tickers) > 1 else filtered_tickers[0]
            )

        filtered_strategies = legacy_config.get("STRATEGY_TYPES", [])
        if filtered_strategies:
            # Convert string strategy types back to StrategyType enums
            strategy_enums = []
            for strategy_str in filtered_strategies:
                try:
                    strategy_enums.append(StrategyType(strategy_str.upper()))
                except ValueError:
                    # Handle unknown strategy types gracefully
                    self.console.warning(f"Unknown strategy type: {strategy_str}")

            filtered_config.strategy_types = strategy_enums

        return filtered_config

    def _execute_batch_processing(
        self,
        config: StrategyConfig,
        summary: StrategyExecutionSummary,
        start_time: float,
    ) -> StrategyExecutionSummary:
        """
        Execute batch processing by processing tickers individually.

        Args:
            config: Strategy configuration with batch settings
            summary: Execution summary to update
            start_time: Start time for execution timing

        Returns:
            Updated StrategyExecutionSummary with batch processing results
        """
        tickers_to_process = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        successful_tickers = []
        failed_tickers = []

        self.console.heading(
            f"Batch Processing: {len(tickers_to_process)} tickers",
            level=2,
        )

        for idx, ticker in enumerate(tickers_to_process, 1):
            self.console.info(
                f"Processing ticker {idx}/{len(tickers_to_process)}: {ticker}",
            )

            # Create a copy of config for single ticker
            single_ticker_config = config.model_copy(deep=True)
            single_ticker_config.ticker = ticker
            single_ticker_config.batch = (
                False  # Disable batch mode for individual execution
            )

            try:
                # Handle mixed strategy types or single strategy
                if len(config.strategy_types) > 1:
                    ticker_summary = self._execute_mixed_strategies(
                        single_ticker_config,
                        StrategyExecutionSummary(
                            execution_time=0.0,
                            success_rate=0.0,
                            successful_strategies=0,
                            total_strategies=0,
                            tickers_processed=[],
                            strategy_types=[],
                        ),
                        time.time(),
                    )
                    success = ticker_summary.success_rate > 0
                else:
                    # Single strategy execution
                    strategy_service = self._determine_single_service(
                        config.strategy_types[0],
                    )
                    if not strategy_service:
                        self.console.error(
                            f"No compatible service found for strategy type: {config.strategy_types[0]}",
                        )
                        success = False
                    else:
                        success = strategy_service.execute_strategy(
                            single_ticker_config,
                        )

                if success:
                    # Update batch file with successful completion
                    batch_update_success = self.batch_service.update_ticker_status(
                        ticker,
                    )
                    if batch_update_success:
                        successful_tickers.append(ticker)
                        self.console.success(
                            f"✅ {ticker} processed successfully and batch file updated",
                        )
                    else:
                        self.console.warning(
                            f"⚠️  {ticker} processed successfully but batch file update failed",
                        )
                        successful_tickers.append(ticker)  # Still count as success
                else:
                    failed_tickers.append(ticker)
                    self.console.error(f"❌ {ticker} processing failed")

            except Exception as e:
                failed_tickers.append(ticker)
                self.console.error(f"❌ {ticker} processing failed with error: {e}")

        # Update summary with batch processing results
        summary.execution_time = time.time() - start_time
        summary.tickers_processed = successful_tickers
        summary.successful_strategies = len(successful_tickers)
        summary.total_strategies = len(tickers_to_process)
        summary.success_rate = (
            len(successful_tickers) / len(tickers_to_process)
            if tickers_to_process
            else 0.0
        )
        summary.strategy_types = [
            st.value if hasattr(st, "value") else str(st)
            for st in config.strategy_types
        ]

        # Display batch processing summary
        self.console.heading("Batch Processing Summary", level=2)
        self.console.success(
            f"Successfully processed: {len(successful_tickers)} tickers",
        )
        if failed_tickers:
            self.console.error(f"Failed to process: {len(failed_tickers)} tickers")
            self.console.info(f"Failed tickers: {', '.join(failed_tickers)}")

        if successful_tickers:
            self.console.info(f"Processed tickers: {', '.join(successful_tickers)}")

        # Show updated batch status
        original_tickers = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )
        self.batch_service.display_batch_status(original_tickers)

        return summary
