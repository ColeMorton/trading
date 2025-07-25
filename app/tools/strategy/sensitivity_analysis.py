"""
Unified Sensitivity Analysis Module

This module consolidates sensitivity analysis functionality across all trading strategies,
eliminating duplication while maintaining strategy-specific behavior through
polymorphism and configuration.
"""

import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from .signal_processing import _detect_strategy_type
from app.tools.stats_converter import convert_stats

# Get configuration
USE_FIXED_SIGNAL_PROC = os.getenv("USE_FIXED_SIGNAL_PROC", "true").lower() == "true"


class SensitivityAnalyzerBase(ABC):
    """
    Abstract base class for sensitivity analyzers.

    This enables strategy-specific sensitivity analysis while maintaining
    a common interface and eliminating code duplication.
    """

    def __init__(self, strategy_type: str):
        """Initialize the sensitivity analyzer.

        Args:
            strategy_type: Type of strategy (SMA, MACD, MEAN_REVERSION, etc.)
        """
        self.strategy_type = strategy_type

    @abstractmethod
    def _calculate_signals(
        self, data: pl.DataFrame, strategy_config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Calculate signals for the strategy with given parameters.

        Args:
            data: Price data DataFrame
            strategy_config: Strategy-specific configuration
            log: Logging function

        Returns:
            DataFrame with signals or None if failed
        """
        pass

    @abstractmethod
    def _check_signal_currency(self, data: pl.DataFrame) -> bool:
        """Check if current signal exists for the strategy.

        Args:
            data: DataFrame with signals

        Returns:
            True if current signal exists
        """
        pass

    @abstractmethod
    def _extract_strategy_parameters(self, **kwargs) -> Dict[str, Any]:
        """Extract strategy-specific parameters from kwargs.

        Returns:
            Dictionary of strategy-specific parameters
        """
        pass

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a single parameter combination using unified logic.

        Args:
            data: Price data DataFrame
            config: Configuration dictionary
            log: Logging function
            **strategy_params: Strategy-specific parameters

        Returns:
            Portfolio statistics if successful, None if failed
        """
        try:
            # Validate data
            if len(data) == 0:
                log(f"Insufficient data for {self.strategy_type} analysis", "warning")
                return None

            # Extract and validate strategy parameters
            strategy_config = self._extract_strategy_parameters(**strategy_params)

            # Add common configuration
            strategy_config.update(
                {
                    "USE_CURRENT": config.get("USE_CURRENT", False),
                    "STRATEGY_TYPE": self.strategy_type,
                }
            )

            # Log parameter combination
            param_str = self._format_parameters(**strategy_params)
            log(f"Analyzing {self.strategy_type} parameters: {param_str}", "info")

            # Check data sufficiency for strategy
            if not self._check_data_sufficiency(data, **strategy_params):
                log(f"Insufficient data for {param_str}", "warning")
                return None

            # Calculate signals using strategy-specific implementation
            temp_data = self._calculate_signals(data.clone(), strategy_config, log)
            if temp_data is None or len(temp_data) == 0:
                log(f"No signals generated for {param_str}", "warning")
                return None

            # Check signal currency
            current = self._check_signal_currency(temp_data)

            # Perform backtesting
            portfolio = backtest_strategy(temp_data, config, log)

            # Convert statistics
            stats = portfolio.stats()

            # Add strategy-specific parameters to stats with proper column name mapping
            parameter_mapping = {
                "short_window": "Short Window",
                "long_window": "Long Window",
                "signal_window": "Signal Window",
                "change_pct": "Change PCT",
            }

            for param, value in strategy_params.items():
                # Use mapped column name if available, otherwise use original parameter name
                column_name = parameter_mapping.get(param, param)
                stats[column_name] = value

            # Add ticker and strategy information from config to ensure proper context preservation
            if "TICKER" in config:
                stats["Ticker"] = config["TICKER"]
            if "STRATEGY_TYPE" in config:
                stats["Strategy Type"] = config["STRATEGY_TYPE"]

            # Convert stats to standard format
            converted_stats = convert_stats(stats, log, config, current)

            return converted_stats

        except Exception as e:
            param_str = self._format_parameters(**strategy_params)
            log(
                f"Failed to process {self.strategy_type} parameters {param_str}: {str(e)}",
                "warning",
            )
            return None

    def analyze_parameter_combinations(
        self,
        data: pl.DataFrame,
        parameter_sets: List[Dict[str, Any]],
        config: Dict[str, Any],
        log: Callable,
    ) -> List[Dict[str, Any]]:
        """Analyze multiple parameter combinations using unified logic.

        Args:
            data: Price data DataFrame
            parameter_sets: List of parameter dictionaries
            config: Configuration dictionary
            log: Logging function

        Returns:
            List of portfolio statistics for each valid combination
        """
        portfolios = []

        for params in parameter_sets:
            result = self.analyze_parameter_combination(data, config, log, **params)
            if result is not None:
                portfolios.append(result)

        return portfolios

    @abstractmethod
    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for the strategy parameters.

        Args:
            data: Price data DataFrame
            **strategy_params: Strategy-specific parameters

        Returns:
            True if data is sufficient
        """
        pass

    @abstractmethod
    def _format_parameters(self, **strategy_params) -> str:
        """Format parameters for logging.

        Args:
            **strategy_params: Strategy-specific parameters

        Returns:
            Formatted parameter string
        """
        pass


class MASensitivityAnalyzer(SensitivityAnalyzerBase):
    """Sensitivity analyzer for Moving Average strategies (SMA/EMA)."""

    def __init__(self, ma_type: str = "SMA"):
        """Initialize MA sensitivity analyzer.

        Args:
            ma_type: Type of moving average (SMA or EMA)
        """
        super().__init__(ma_type)
        self.ma_type = ma_type

    def _calculate_signals(
        self, data: pl.DataFrame, strategy_config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Calculate MA signals."""
        try:
            from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

            return calculate_ma_and_signals(
                data=data,
                short_window=strategy_config.get("short_window"),
                long_window=strategy_config.get("long_window"),
                config=strategy_config,
                log=log,
                strategy_type=self.ma_type,
            )
        except ImportError:
            return None

    def _check_signal_currency(self, data: pl.DataFrame) -> bool:
        """Check if current MA signal exists."""
        try:
            from app.tools.strategy.signal_utils import is_signal_current

            return is_signal_current(data)
        except ImportError:
            return False

    def _extract_strategy_parameters(self, **kwargs) -> Dict[str, Any]:
        """Extract MA-specific parameters."""
        short_window = kwargs.get("short_window") or kwargs.get("short")
        long_window = kwargs.get("long_window") or kwargs.get("long")

        if short_window is None or long_window is None:
            raise ValueError(
                "MA strategy requires short_window and long_window parameters"
            )

        return {
            "short_window": short_window,
            "long_window": long_window,
            "USE_SMA": self.ma_type == "SMA",
        }

    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for MA windows."""
        short_window = strategy_params.get("short_window") or strategy_params.get(
            "short"
        )
        long_window = strategy_params.get("long_window") or strategy_params.get("long")

        max_window = max(short_window or 0, long_window or 0)
        return len(data) >= max_window

    def _format_parameters(self, **strategy_params) -> str:
        """Format MA parameters for logging."""
        short = strategy_params.get("short_window") or strategy_params.get("short")
        long = strategy_params.get("long_window") or strategy_params.get("long")
        return f"Short: {short}, Long: {long}"


class MACDSensitivityAnalyzer(SensitivityAnalyzerBase):
    """Sensitivity analyzer for MACD strategies."""

    def __init__(self):
        super().__init__("MACD")

    def _calculate_signals(
        self, data: pl.DataFrame, strategy_config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Calculate MACD signals."""
        try:
            from app.strategies.macd.tools.signal_generation import (
                generate_macd_signals,
            )

            return generate_macd_signals(data, strategy_config)
        except ImportError:
            return None

    def _check_signal_currency(self, data: pl.DataFrame) -> bool:
        """Check if current MACD signal exists."""
        try:
            from app.tools.strategy.signal_utils import is_signal_current

            return is_signal_current(data)
        except ImportError:
            return False

    def _extract_strategy_parameters(self, **kwargs) -> Dict[str, Any]:
        """Extract MACD-specific parameters."""
        short_window = kwargs.get("short_window")
        long_window = kwargs.get("long_window")
        signal_window = kwargs.get("signal_window")

        if short_window is None or long_window is None or signal_window is None:
            raise ValueError(
                "MACD strategy requires short_window, long_window, and signal_window parameters"
            )

        return {
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
        }

    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for MACD windows."""
        short_window = strategy_params.get("short_window", 0)
        long_window = strategy_params.get("long_window", 0)
        signal_window = strategy_params.get("signal_window", 0)

        max_window = max(short_window, long_window, signal_window)
        return len(data) >= max_window

    def _format_parameters(self, **strategy_params) -> str:
        """Format MACD parameters for logging."""
        short = strategy_params.get("short_window")
        long = strategy_params.get("long_window")
        signal = strategy_params.get("signal_window")
        return f"Short: {short}, Long: {long}, Signal: {signal}"


class MeanReversionSensitivityAnalyzer(SensitivityAnalyzerBase):
    """Sensitivity analyzer for Mean Reversion strategies."""

    def __init__(self):
        super().__init__("MEAN_REVERSION")

    def _calculate_signals(
        self, data: pl.DataFrame, strategy_config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """Calculate Mean Reversion signals."""
        try:
            from app.strategies.mean_reversion.tools.signal_generation import (
                calculate_signals,
            )

            return calculate_signals(data, strategy_config)
        except ImportError:
            return None

    def _check_signal_currency(self, data: pl.DataFrame) -> bool:
        """Check if current Mean Reversion signal exists."""
        try:
            from app.strategies.mean_reversion.tools.signal_generation import (
                is_signal_current,
            )

            return is_signal_current(data)
        except ImportError:
            return False

    def _extract_strategy_parameters(self, **kwargs) -> Dict[str, Any]:
        """Extract Mean Reversion-specific parameters."""
        change_pct = kwargs.get("change_pct")

        if change_pct is None:
            raise ValueError("Mean Reversion strategy requires change_pct parameter")

        return {"change_pct": change_pct}

    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for Mean Reversion analysis."""
        # Mean reversion typically needs minimal data
        return len(data) > 0

    def _format_parameters(self, **strategy_params) -> str:
        """Format Mean Reversion parameters for logging."""
        change_pct = strategy_params.get("change_pct")
        return f"Change PCT: {change_pct}"


class SensitivityAnalyzerFactory:
    """Factory for creating strategy-specific sensitivity analyzers."""

    _analyzers = {
        "SMA": lambda: MASensitivityAnalyzer("SMA"),
        "EMA": lambda: MASensitivityAnalyzer("EMA"),
        "MACD": lambda: MACDSensitivityAnalyzer(),
        "MEAN_REVERSION": lambda: MeanReversionSensitivityAnalyzer(),
        "MA_CROSS": lambda: MASensitivityAnalyzer("SMA"),  # Default to SMA
    }

    @classmethod
    def create_analyzer(cls, strategy_type: str) -> SensitivityAnalyzerBase:
        """Create a sensitivity analyzer for the given strategy type.

        Args:
            strategy_type: Type of strategy

        Returns:
            SensitivityAnalyzerBase: Strategy-specific sensitivity analyzer

        Raises:
            ValueError: If strategy type is not supported
        """
        strategy_type = strategy_type.upper()
        if strategy_type not in cls._analyzers:
            available = ", ".join(cls._analyzers.keys())
            raise ValueError(
                f"Unsupported strategy type: {strategy_type}. Available: {available}"
            )

        return cls._analyzers[strategy_type]()

    @classmethod
    def get_supported_strategies(cls) -> List[str]:
        """Get list of supported strategy types."""
        return list(cls._analyzers.keys())


# Convenience functions for backward compatibility
def analyze_parameter_combination(
    data: pl.DataFrame,
    config: Dict[str, Any],
    log: Callable,
    strategy_type: str = None,
    **strategy_params,
) -> Optional[Dict[str, Any]]:
    """Analyze a parameter combination using unified sensitivity analysis.

    Args:
        data: Price data DataFrame
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)
        **strategy_params: Strategy-specific parameters

    Returns:
        Portfolio statistics if successful, None if failed
    """
    if strategy_type is None:
        strategy_type = _detect_strategy_type(config)

    analyzer = SensitivityAnalyzerFactory.create_analyzer(strategy_type)
    return analyzer.analyze_parameter_combination(data, config, log, **strategy_params)


def analyze_parameter_combinations(
    data: pl.DataFrame,
    parameter_sets: List[Dict[str, Any]],
    config: Dict[str, Any],
    log: Callable,
    strategy_type: str = None,
) -> List[Dict[str, Any]]:
    """Analyze multiple parameter combinations using unified sensitivity analysis.

    Args:
        data: Price data DataFrame
        parameter_sets: List of parameter dictionaries
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        List of portfolio statistics
    """
    if strategy_type is None:
        strategy_type = _detect_strategy_type(config)

    analyzer = SensitivityAnalyzerFactory.create_analyzer(strategy_type)
    return analyzer.analyze_parameter_combinations(data, parameter_sets, config, log)


# Strategy-specific convenience functions for backward compatibility
def analyze_window_combination(
    data: pl.DataFrame, short: int, long: int, config: Dict[str, Any], log: Callable
) -> Optional[Dict[str, Any]]:
    """Analyze MA window combination (backward compatibility function).

    Args:
        data: Price data DataFrame
        short: Short window period
        long: Long window period
        config: Configuration dictionary
        log: Logging function

    Returns:
        Portfolio statistics if successful, None if failed
    """
    strategy_type = config.get("STRATEGY_TYPE", "SMA")
    analyzer = SensitivityAnalyzerFactory.create_analyzer(strategy_type)
    return analyzer.analyze_parameter_combination(
        data, config, log, short_window=short, long_window=long
    )


def analyze_macd_combination(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    signal_window: int,
    config: Dict[str, Any],
    log: Callable,
) -> Optional[Dict[str, Any]]:
    """Analyze MACD parameter combination (convenience function).

    Args:
        data: Price data DataFrame
        short_window: Short-term EMA period
        long_window: Long-term EMA period
        signal_window: Signal line EMA period
        config: Configuration dictionary
        log: Logging function

    Returns:
        Portfolio statistics if successful, None if failed
    """
    analyzer = SensitivityAnalyzerFactory.create_analyzer("MACD")
    return analyzer.analyze_parameter_combination(
        data,
        config,
        log,
        short_window=short_window,
        long_window=long_window,
        signal_window=signal_window,
    )


def analyze_mean_reversion_combination(
    data: pl.DataFrame, change_pct: float, config: Dict[str, Any], log: Callable
) -> Optional[Dict[str, Any]]:
    """Analyze Mean Reversion parameter combination (convenience function).

    Args:
        data: Price data DataFrame
        change_pct: Price change percentage for entry
        config: Configuration dictionary
        log: Logging function

    Returns:
        Portfolio statistics if successful, None if failed
    """
    analyzer = SensitivityAnalyzerFactory.create_analyzer("MEAN_REVERSION")
    return analyzer.analyze_parameter_combination(
        data, config, log, change_pct=change_pct
    )
