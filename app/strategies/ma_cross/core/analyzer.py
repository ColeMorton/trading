"""
Core MA Cross Analyzer

This module provides the core analysis logic for MA Cross strategy,
decoupled from file I/O and specific execution contexts.
"""

import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from app.strategies.ma_cross.core.models import (
    AnalysisConfig,
    AnalysisResult,
    SignalInfo,
    TickerResult,
)
from app.strategies.ma_cross.tools.strategy_execution import execute_single_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging


class MACrossAnalyzer:
    """
    Core analyzer for MA Cross strategy.

    This class provides the business logic for MA Cross analysis,
    independent of how it's invoked (CLI, API, etc.).
    """

    def __init__(self, log: Callable | None | None = None):
        """
        Initialize the analyzer.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        self._log = log
        self._log_close = None

        if self._log is None:
            self._log, self._log_close, _, _ = setup_logging(
                "ma_cross_analyzer",
                "analyzer.log",
            )

    def analyze_single(
        self,
        config: AnalysisConfig,
        calculate_metrics: bool = True,
    ) -> TickerResult:
        """
        Analyze a single ticker with the given configuration.

        Args:
            config: Analysis configuration
            calculate_metrics: Whether to calculate portfolio metrics (default: True)

        Returns:
            TickerResult with detected signals and optionally portfolio metrics
        """
        start_time = time.time()

        try:
            self._log(f"Analyzing {config.ticker}")

            # If we need portfolio metrics and have specific windows, use strategy execution
            if calculate_metrics and config.fast_period and config.slow_period:
                # Convert to strategy execution config format
                exec_config = config.to_dict()
                exec_config["STRATEGY_TYPE"] = "SMA" if config.use_sma else "EMA"

                # Execute strategy to get portfolio metrics
                portfolio_stats = execute_single_strategy(
                    config.ticker,
                    exec_config,
                    self._log,
                )

                if portfolio_stats:
                    # Create TickerResult with portfolio metrics
                    result = TickerResult(
                        ticker=config.ticker,
                        processing_time=time.time() - start_time,
                        strategy_type="SMA" if config.use_sma else "EMA",
                        fast_period=config.fast_period,
                        slow_period=config.slow_period,
                        total_trades=int(portfolio_stats.get("Total Trades", 0)),
                        total_return_pct=float(portfolio_stats.get("Total Return", 0)),
                        sharpe_ratio=float(portfolio_stats.get("Sharpe Ratio", 0)),
                        max_drawdown_pct=float(portfolio_stats.get("Max Drawdown", 0)),
                        win_rate_pct=float(portfolio_stats.get("Win Rate", 0)),
                        profit_factor=float(portfolio_stats.get("Profit Factor", 0)),
                        expectancy_per_trade=float(
                            portfolio_stats.get("Expectancy per Trade", 0),
                        ),
                        sortino_ratio=float(portfolio_stats.get("Sortino Ratio", 0)),
                        beats_bnh_pct=float(portfolio_stats.get("Beats BnH %", 0)),
                    )

                    # Also check for current signals
                    data = self._fetch_data(config)
                    if data is not None:
                        signals = self._analyze_signals(data, config)
                        result.signals = signals

                    return result

            # Otherwise, just analyze for signals (original behavior)
            data = self._fetch_data(config)
            if data is None:
                return TickerResult(
                    ticker=config.ticker,
                    error="Failed to fetch price data",
                    processing_time=time.time() - start_time,
                )

            # Analyze for signals
            signals = self._analyze_signals(data, config)

            return TickerResult(
                ticker=config.ticker,
                signals=signals,
                processing_time=time.time() - start_time,
            )

        except Exception as e:
            self._log(f"Error analyzing {config.ticker}: {e!s}", "error")
            return TickerResult(
                ticker=config.ticker,
                error=str(e),
                processing_time=time.time() - start_time,
            )

    def analyze_multiple(self, configs: list[AnalysisConfig]) -> AnalysisResult:
        """
        Analyze multiple tickers with their configurations.

        Args:
            configs: List of analysis configurations

        Returns:
            AnalysisResult with all ticker results
        """
        start_time = time.time()
        results = []

        for config in configs:
            result = self.analyze_single(config)
            results.append(result)

        return AnalysisResult(
            tickers=results,
            total_processing_time=time.time() - start_time,
            config=configs[0] if configs else None,  # Store first config as reference
        )

    def analyze_portfolio(
        self,
        tickers: list[str],
        base_config: AnalysisConfig,
    ) -> AnalysisResult:
        """
        Analyze a portfolio of tickers with the same base configuration.

        Args:
            tickers: List of ticker symbols
            base_config: Base configuration to apply to all tickers

        Returns:
            AnalysisResult with all ticker results
        """
        configs = []
        for ticker in tickers:
            config = AnalysisConfig(
                ticker=ticker,
                strategy_type=base_config.strategy_type,
                use_hourly=base_config.use_hourly,
                direction=base_config.direction,
                fast_period=base_config.fast_period,
                slow_period=base_config.slow_period,
                windows=base_config.windows,
                use_years=base_config.use_years,
                years=base_config.years,
            )
            configs.append(config)

        return self.analyze_multiple(configs)

    def _fetch_data(self, config: AnalysisConfig) -> Any | None:
        """Fetch price data for analysis."""
        try:
            config_dict = config.to_dict()
            config_dict["USE_CURRENT"] = True  # Enable holiday checking

            result = get_data(config.ticker, config_dict, self._log)

            # Handle tuple return from get_data
            if isinstance(result, tuple):
                data, _ = result
            else:
                data = result

            return data

        except Exception as e:
            self._log(f"Error fetching data for {config.ticker}: {e!s}", "error")
            return None

    def _analyze_signals(self, data: Any, config: AnalysisConfig) -> list[SignalInfo]:
        """Analyze data for MA Cross signals."""
        signals = []

        try:
            # If specific windows are provided, analyze just those
            if config.fast_period and config.slow_period:
                signal = self._check_single_window(
                    data,
                    config.fast_period,
                    config.slow_period,
                    config,
                )
                if signal:
                    signals.append(signal)

            # Otherwise, scan window permutations if windows parameter is provided
            elif config.windows and config.windows > 2:
                signals.extend(self._scan_window_permutations(data, config))

            return signals

        except Exception as e:
            self._log(f"Error analyzing signals: {e!s}", "error")
            return []

    def _check_single_window(
        self,
        data: Any,
        fast_period: int,
        slow_period: int,
        config: AnalysisConfig,
    ) -> SignalInfo | None:
        """Check for signal with specific window combination."""
        try:
            # Clone data to avoid modifying original
            import polars as pl

            if hasattr(data, "clone"):
                temp_data = data.clone()
            else:
                temp_data = pl.DataFrame(data)

            # Calculate MA and signals
            ma_type = "SMA" if config.use_sma else "EMA"
            temp_data = calculate_ma_and_signals(
                temp_data,
                fast_period,
                slow_period,
                config.to_dict(),
                self._log,
                ma_type,
            )

            if temp_data is None or len(temp_data) == 0:
                return None

            # Check if signal is current
            from app.tools.strategy.signal_utils import is_signal_current

            if is_signal_current(temp_data, config.to_dict()):
                # Get the last signal
                last_row = temp_data[-1]
                signal_date = last_row["Date"]

                # Convert to datetime if needed
                if isinstance(signal_date, str):
                    signal_date = datetime.fromisoformat(signal_date)

                # Determine signal type based on position
                position_col = (
                    "Position" if "Position" in temp_data.columns else "position"
                )
                signal_type = "BUY" if last_row[position_col] == 1 else "SELL"

                return SignalInfo(
                    ma_type=ma_type,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_date=signal_date,
                    signal_type=signal_type,
                    current=True,
                )

            return None

        except Exception as e:
            self._log(
                f"Error checking window {fast_period}/{slow_period}: {e!s}",
                "error",
            )
            return None

    def _scan_window_permutations(
        self,
        data: Any,
        config: AnalysisConfig,
    ) -> list[SignalInfo]:
        """Scan all window permutations for signals."""
        signals = []

        if not config.windows:
            return signals

        # Generate window ranges
        import numpy as np

        short_windows = list(np.arange(2, config.windows))
        long_windows = list(np.arange(2, config.windows))

        for short in short_windows:
            for long in long_windows:
                if short < long:  # Ensure short is less than long
                    signal = self._check_single_window(data, short, long, config)
                    if signal:
                        signals.append(signal)

        return signals

    def close(self):
        """Clean up resources."""
        if self._log_close:
            self._log_close()
