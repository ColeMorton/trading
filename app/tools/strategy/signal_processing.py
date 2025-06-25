"""
Unified Signal Processing Module

This module consolidates signal processing functionality across all trading strategies,
eliminating duplication while maintaining strategy-specific behavior through
polymorphism and configuration.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional

import polars as pl

from app.tools.get_data import get_data
from app.tools.strategy.unified_config import ConfigValidator


class SignalProcessorBase(ABC):
    """
    Abstract base class for signal processors.

    This enables strategy-specific signal processing while maintaining
    a common interface and eliminating code duplication.
    """

    def __init__(self, strategy_type: str):
        """Initialize the signal processor.

        Args:
            strategy_type: Type of strategy (SMA, MACD, MEAN_REVERSION, etc.)
        """
        self.strategy_type = strategy_type

    @abstractmethod
    def generate_current_signals(
        self, config: Dict[str, Any], log: Callable
    ) -> pl.DataFrame:
        """Generate current signals for the strategy.

        Args:
            config: Strategy configuration
            log: Logging function

        Returns:
            DataFrame of current signals
        """
        pass

    @abstractmethod
    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a specific parameter combination.

        Args:
            data: Price data DataFrame
            config: Strategy configuration
            log: Logging function
            **strategy_params: Strategy-specific parameters

        Returns:
            Portfolio result dictionary or None
        """
        pass

    def process_current_signals(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Process current signals for a ticker using unified processing logic.

        Args:
            ticker: The ticker symbol to process
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame of portfolios or None if processing fails
        """
        config_copy = config.copy()
        config_copy["TICKER"] = ticker

        try:
            # Validate configuration using unified system
            validation_result = ConfigValidator.validate_base_config(config_copy)
            if not validation_result["is_valid"]:
                log(
                    f"Invalid configuration for {ticker}: {validation_result['errors']}",
                    "error",
                )
                return None

            # Generate and validate current signals using strategy-specific implementation
            current_signals = self.generate_current_signals(config_copy, log)
            if len(current_signals) == 0:
                direction = config.get("DIRECTION", "Long")
                log(
                    f"No current signals found for {ticker} {direction} {self.strategy_type}",
                    "warning",
                )
                return None

            direction = config.get("DIRECTION", "Long")
            log(f"Current signals for {ticker} {direction} {self.strategy_type}")

            # Get and validate price data
            data = get_data(ticker, config_copy, log)
            if data is None:
                log(f"Failed to get price data for {ticker}", "error")
                return None

            # Process each signal using strategy-specific parameter analysis
            portfolios = []
            for row in current_signals.iter_rows(named=True):
                # Create strategy config for this combination
                strategy_config = config_copy.copy()

                # Strategy-specific parameter extraction and analysis
                result = self._process_signal_row(data, row, strategy_config, log)
                if result is not None:
                    portfolios.append(result)

            return pl.DataFrame(portfolios) if portfolios else None

        except Exception as e:
            log(f"Failed to process current signals for {ticker}: {str(e)}", "error")
            return None

    def process_ticker_portfolios(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Process portfolios for a single ticker using unified logic.

        Args:
            ticker: The ticker symbol to process
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame of portfolios or None if processing fails
        """
        try:
            if config.get("USE_CURRENT", False):
                return self.process_current_signals(ticker, config, log)
            else:
                # Use strategy-specific portfolio processing
                portfolios = self._process_full_ticker_analysis(ticker, config, log)
                if portfolios is None:
                    log(f"Failed to process {ticker}", "error")
                    return None

                portfolios_df = (
                    pl.DataFrame(portfolios)
                    if isinstance(portfolios, list)
                    else portfolios
                )
                direction = config.get("DIRECTION", "Long")
                log(f"Results for {ticker} {direction} {self.strategy_type}")
                return portfolios_df

        except Exception as e:
            log(f"Failed to process ticker portfolios for {ticker}: {str(e)}", "error")
            return None

    def _process_signal_row(
        self,
        data: pl.DataFrame,
        row: Dict[str, Any],
        config: Dict[str, Any],
        log: Callable,
    ) -> Optional[Dict[str, Any]]:
        """Process a single signal row. Strategy-specific implementations can override."""
        # Extract strategy-specific parameters from the row
        strategy_params = self._extract_strategy_parameters(row)

        # Update config with row-specific parameters
        strategy_config = config.copy()
        strategy_config.update(strategy_params)

        # Use strategy-specific parameter analysis
        return self.analyze_parameter_combination(
            data, strategy_config, log, **strategy_params
        )

    @abstractmethod
    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract strategy-specific parameters from a signal row.

        Args:
            row: Signal row data

        Returns:
            Dictionary of strategy-specific parameters
        """
        pass

    @abstractmethod
    def _process_full_ticker_analysis(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[Any]:
        """Process full ticker analysis. Strategy implementations handle their specific logic.

        Args:
            ticker: Ticker symbol
            config: Configuration dictionary
            log: Logging function

        Returns:
            Portfolio results
        """
        pass


class MASignalProcessor(SignalProcessorBase):
    """Signal processor for Moving Average strategies (SMA/EMA)."""

    def __init__(self, ma_type: str = "SMA"):
        """Initialize MA signal processor.

        Args:
            ma_type: Type of moving average (SMA or EMA)
        """
        super().__init__(ma_type)
        self.ma_type = ma_type

    def generate_current_signals(
        self, config: Dict[str, Any], log: Callable
    ) -> pl.DataFrame:
        """Generate current signals for MA strategy."""
        try:
            # Import strategy-specific signal generation
            from app.strategies.ma_cross.tools.signal_generation import (
                generate_current_signals,
            )

            return generate_current_signals(config, log)
        except ImportError:
            log(f"Failed to import MA signal generation for {self.ma_type}", "error")
            return pl.DataFrame()

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze MA parameter combination."""
        try:
            # Import strategy-specific analysis
            from app.strategies.ma_cross.tools.sensitivity_analysis import (
                analyze_window_combination,
            )

            short_window = strategy_params.get("short_window") or config.get(
                "SHORT_WINDOW"
            )
            long_window = strategy_params.get("long_window") or config.get(
                "LONG_WINDOW"
            )

            return analyze_window_combination(
                data=data,
                short_window=short_window,
                long_window=long_window,
                config=config,
                log=log,
            )
        except ImportError:
            log("Failed to import MA sensitivity analysis", "error")
            return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract MA-specific parameters."""
        return {
            "short_window": row.get("Short Window"),
            "long_window": row.get("Long Window"),
        }

    def _process_full_ticker_analysis(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[Any]:
        """Process full MA ticker analysis."""
        try:
            from app.tools.portfolio.processing import process_single_ticker

            return process_single_ticker(ticker, config, log)
        except ImportError:
            log("Failed to import portfolio processing", "error")
            return None


class MACDSignalProcessor(SignalProcessorBase):
    """Signal processor for MACD strategies."""

    def __init__(self):
        super().__init__("MACD")

    def generate_current_signals(
        self, config: Dict[str, Any], log: Callable
    ) -> pl.DataFrame:
        """Generate current signals for MACD strategy."""
        try:
            from app.strategies.macd.tools.signal_generation import (
                generate_current_signals,
            )

            return generate_current_signals(config, log)
        except ImportError:
            log("Failed to import MACD signal generation", "error")
            return pl.DataFrame()

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze MACD parameter combination."""
        try:
            from app.strategies.macd.tools.sensitivity_analysis import (
                analyze_parameter_combination,
            )

            short_window = strategy_params.get("short_window") or config.get(
                "SHORT_WINDOW"
            )
            long_window = strategy_params.get("long_window") or config.get(
                "LONG_WINDOW"
            )
            signal_window = strategy_params.get("signal_window") or config.get(
                "SIGNAL_WINDOW"
            )

            return analyze_parameter_combination(
                data=data,
                short_window=short_window,
                long_window=long_window,
                signal_window=signal_window,
                config=config,
                log=log,
            )
        except ImportError:
            log("Failed to import MACD sensitivity analysis", "error")
            return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract MACD-specific parameters."""
        return {
            "short_window": row.get("Short Window"),
            "long_window": row.get("Long Window"),
            "signal_window": row.get("Signal Window"),
        }

    def _process_full_ticker_analysis(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[Any]:
        """Process full MACD ticker analysis."""
        try:
            from app.tools.portfolio.processing import process_single_ticker

            return process_single_ticker(ticker, config, log)
        except ImportError:
            log("Failed to import portfolio processing", "error")
            return None


class MeanReversionSignalProcessor(SignalProcessorBase):
    """Signal processor for Mean Reversion strategies."""

    def __init__(self):
        super().__init__("MEAN_REVERSION")

    def generate_current_signals(
        self, config: Dict[str, Any], log: Callable
    ) -> pl.DataFrame:
        """Generate current signals for Mean Reversion strategy."""
        try:
            from app.strategies.mean_reversion.tools.signal_generation import (
                generate_current_signals,
            )

            return generate_current_signals(config, log)
        except ImportError:
            log("Failed to import Mean Reversion signal generation", "error")
            return pl.DataFrame()

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze Mean Reversion parameter combination."""
        try:
            from app.strategies.mean_reversion.tools.sensitivity_analysis import (
                analyze_parameter_combination,
            )

            change_pct = strategy_params.get("change_pct") or config.get("CHANGE_PCT")

            return analyze_parameter_combination(
                data=data, change_pct=change_pct, config=config, log=log
            )
        except ImportError:
            log("Failed to import Mean Reversion sensitivity analysis", "error")
            return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract Mean Reversion-specific parameters."""
        return {"change_pct": row.get("Change PCT")}

    def _process_full_ticker_analysis(
        self, ticker: str, config: Dict[str, Any], log: Callable
    ) -> Optional[Any]:
        """Process full Mean Reversion ticker analysis."""
        try:
            from app.strategies.mean_reversion.tools.portfolio_processing import (
                process_single_ticker,
            )

            return process_single_ticker(ticker, config, log)
        except ImportError:
            log("Failed to import Mean Reversion portfolio processing", "error")
            return None


class SignalProcessorFactory:
    """Factory for creating strategy-specific signal processors."""

    _processors = {
        "SMA": lambda: MASignalProcessor("SMA"),
        "EMA": lambda: MASignalProcessor("EMA"),
        "MACD": lambda: MACDSignalProcessor(),
        "MEAN_REVERSION": lambda: MeanReversionSignalProcessor(),
        "MA_CROSS": lambda: MASignalProcessor("SMA"),  # Default to SMA
    }

    @classmethod
    def create_processor(cls, strategy_type: str) -> SignalProcessorBase:
        """Create a signal processor for the given strategy type.

        Args:
            strategy_type: Type of strategy

        Returns:
            SignalProcessorBase: Strategy-specific signal processor

        Raises:
            ValueError: If strategy type is not supported
        """
        strategy_type = strategy_type.upper()
        if strategy_type not in cls._processors:
            available = ", ".join(cls._processors.keys())
            raise ValueError(
                f"Unsupported strategy type: {strategy_type}. Available: {available}"
            )

        return cls._processors[strategy_type]()

    @classmethod
    def get_supported_strategies(cls) -> list[str]:
        """Get list of supported strategy types."""
        return list(cls._processors.keys())


# Convenience functions for backward compatibility
def process_current_signals(
    ticker: str, config: Dict[str, Any], log: Callable, strategy_type: str = None
) -> Optional[pl.DataFrame]:
    """Process current signals using unified signal processing.

    Args:
        ticker: Ticker symbol
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        DataFrame of portfolios or None
    """
    if strategy_type is None:
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

    processor = SignalProcessorFactory.create_processor(strategy_type)
    return processor.process_current_signals(ticker, config, log)


def process_ticker_portfolios(
    ticker: str, config: Dict[str, Any], log: Callable, strategy_type: str = None
) -> Optional[pl.DataFrame]:
    """Process ticker portfolios using unified signal processing.

    Args:
        ticker: Ticker symbol
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        DataFrame of portfolios or None
    """
    if strategy_type is None:
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

    processor = SignalProcessorFactory.create_processor(strategy_type)
    return processor.process_ticker_portfolios(ticker, config, log)
