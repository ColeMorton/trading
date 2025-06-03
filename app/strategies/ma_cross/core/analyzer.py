"""
Core MA Cross Analyzer

This module provides the core analysis logic for MA Cross strategy,
decoupled from file I/O and specific execution contexts.
"""

import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from app.strategies.ma_cross.core.models import (
    AnalysisConfig,
    AnalysisResult,
    SignalInfo,
    TickerResult,
)
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.setup_logging import setup_logging


class MACrossAnalyzer:
    """
    Core analyzer for MA Cross strategy.

    This class provides the business logic for MA Cross analysis,
    independent of how it's invoked (CLI, API, etc.).
    """

    def __init__(self, log: Optional[Callable] = None):
        """
        Initialize the analyzer.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        self._log = log
        self._log_close = None

        if self._log is None:
            self._log, self._log_close, _, _ = setup_logging(
                "ma_cross_analyzer", "analyzer.log"
            )

    def analyze_single(self, config: AnalysisConfig) -> TickerResult:
        """
        Analyze a single ticker with the given configuration.

        Args:
            config: Analysis configuration

        Returns:
            TickerResult with detected signals
        """
        start_time = time.time()

        try:
            self._log(f"Analyzing {config.ticker}")

            # Get price data
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
            self._log(f"Error analyzing {config.ticker}: {str(e)}", "error")
            return TickerResult(
                ticker=config.ticker,
                error=str(e),
                processing_time=time.time() - start_time,
            )

    def analyze_multiple(self, configs: List[AnalysisConfig]) -> AnalysisResult:
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
        self, tickers: List[str], base_config: AnalysisConfig
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
                use_sma=base_config.use_sma,
                use_hourly=base_config.use_hourly,
                direction=base_config.direction,
                short_window=base_config.short_window,
                long_window=base_config.long_window,
                windows=base_config.windows,
                use_years=base_config.use_years,
                years=base_config.years,
            )
            configs.append(config)

        return self.analyze_multiple(configs)

    def _fetch_data(self, config: AnalysisConfig) -> Optional[Any]:
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
            self._log(f"Error fetching data for {config.ticker}: {str(e)}", "error")
            return None

    def _analyze_signals(self, data: Any, config: AnalysisConfig) -> List[SignalInfo]:
        """Analyze data for MA Cross signals."""
        signals = []

        try:
            # If specific windows are provided, analyze just those
            if config.short_window and config.long_window:
                signal = self._check_single_window(
                    data, config.short_window, config.long_window, config
                )
                if signal:
                    signals.append(signal)

            # Otherwise, scan window permutations if windows parameter is provided
            elif config.windows and config.windows > 2:
                signals.extend(self._scan_window_permutations(data, config))

            return signals

        except Exception as e:
            self._log(f"Error analyzing signals: {str(e)}", "error")
            return []

    def _check_single_window(
        self, data: Any, short_window: int, long_window: int, config: AnalysisConfig
    ) -> Optional[SignalInfo]:
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
                short_window,
                long_window,
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
                    short_window=short_window,
                    long_window=long_window,
                    signal_date=signal_date,
                    signal_type=signal_type,
                    current=True,
                )

            return None

        except Exception as e:
            self._log(
                f"Error checking window {short_window}/{long_window}: {str(e)}", "error"
            )
            return None

    def _scan_window_permutations(
        self, data: Any, config: AnalysisConfig
    ) -> List[SignalInfo]:
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
