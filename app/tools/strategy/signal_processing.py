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
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
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

            # Calculate progress increment for USE_CURRENT mode
            # Since the dispatcher now sets the progress bar total to actual current signals,
            # we can use simple 1:1 progress increments (1 per signal processed)
            current_signals_count = len(current_signals)
            progress_increment = 1  # Each current signal = 1 progress unit

            # Process signals without individual progress bars (unified tracking handled at CLI level)
            for row in current_signals.iter_rows(named=True):
                # Create strategy config for this combination
                strategy_config = config_copy.copy()

                # Strategy-specific parameter extraction and analysis
                result = self._process_signal_row(data, row, strategy_config, log)
                if result is not None:
                    portfolios.append(result)

                # Update progress for USE_CURRENT mode (1 per signal processed)
                if progress_update_fn:
                    progress_update_fn(progress_increment)

            return pl.DataFrame(portfolios) if portfolios else None

        except Exception as e:
            log(f"Failed to process current signals for {ticker}: {str(e)}", "error")
            return None

    def process_ticker_portfolios(
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
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
            # USE_CURRENT fast path - process only current signals without full analysis
            if config.get("USE_CURRENT", False):
                return self.process_current_signals(
                    ticker, config, log, progress_update_fn
                )

            # Regular path - run full parameter sweep analysis
            portfolios = self._process_full_ticker_analysis(
                ticker, config, log, progress_update_fn
            )
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                return None

            portfolios_df = (
                pl.DataFrame(portfolios) if isinstance(portfolios, list) else portfolios
            )

            direction = config.get("DIRECTION", "Long")
            log(f"Results for {ticker} {direction} {self.strategy_type}")
            return portfolios_df

        except Exception as e:
            log(f"Failed to process ticker portfolios for {ticker}: {str(e)}", "error")
            return None

    def _filter_by_current_signals(
        self, portfolios_df: pl.DataFrame, current_signals: pl.DataFrame, log: Callable
    ) -> pl.DataFrame:
        """Filter portfolios to only include those with current signals.

        Args:
            portfolios_df: DataFrame of all portfolios
            current_signals: DataFrame of current signals
            log: Logging function

        Returns:
            Filtered DataFrame containing only portfolios with current signals
        """
        # Extract parameters from current signals to match against portfolios
        signal_params = self._extract_signal_parameters_for_filtering(current_signals)

        # Filter portfolios based on matching parameters
        filtered = portfolios_df
        for param_name, param_values in signal_params.items():
            if param_name in portfolios_df.columns:
                filtered = filtered.filter(pl.col(param_name).is_in(param_values))

        return filtered

    def _extract_signal_parameters_for_filtering(
        self, current_signals: pl.DataFrame
    ) -> Dict[str, list]:
        """Extract parameter values from current signals for filtering.

        Strategy-specific implementations should override this to extract
        the relevant parameters.

        Args:
            current_signals: DataFrame of current signals

        Returns:
            Dictionary mapping parameter names to lists of values
        """
        return {}

    def _calculate_total_combinations(self, config: Dict[str, Any]) -> int:
        """Calculate total parameter combinations for progress tracking.

        Args:
            config: Configuration dictionary

        Returns:
            Total number of parameter combinations
        """
        # Strategy-specific implementations should override this.
        # Default implementation returns a conservative estimate.
        if self.strategy_type in ["SMA", "EMA"]:
            # MA strategies: fast_period × slow_period (with fast < slow constraint)
            fast_range = config.get("FAST_PERIOD_RANGE", (2, 89))
            slow_range = config.get("SLOW_PERIOD_RANGE", (3, 89))

            fast_min, fast_max = fast_range
            slow_min, slow_max = slow_range

            # Calculate valid combinations where fast < slow
            total_combinations = 0
            for fast in range(fast_min, fast_max + 1):
                valid_slow_min = max(fast + 1, slow_min)
                if valid_slow_min <= slow_max:
                    total_combinations += slow_max - valid_slow_min + 1

            return total_combinations

        elif self.strategy_type == "MACD":
            # MACD strategy: fast_period × slow_period × signal_period
            fast_min = config.get("SHORT_WINDOW_START", 2)
            fast_max = config.get("SHORT_WINDOW_END", 18)
            slow_min = config.get("LONG_WINDOW_START", 4)
            slow_max = config.get("LONG_WINDOW_END", 36)
            signal_min = config.get("SIGNAL_WINDOW_START", 2)
            signal_max = config.get("SIGNAL_WINDOW_END", 18)
            step = config.get("STEP", 2)

            # Calculate valid combinations where slow > fast
            valid_combinations = 0
            for fast in range(fast_min, fast_max + 1, step):
                for slow in range(slow_min, slow_max + 1, step):
                    if slow > fast:
                        signal_combinations = (signal_max - signal_min) // step + 1
                        valid_combinations += signal_combinations

            return valid_combinations

        # Conservative fallback
        return 100

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
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> Optional[Any]:
        """Process full ticker analysis. Strategy implementations handle their specific logic.

        Args:
            ticker: Ticker symbol
            config: Configuration dictionary
            log: Logging function
            progress_update_fn: Optional progress update function for holistic tracking

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
            from app.tools.strategy.sensitivity_analysis import (
                analyze_window_combination,
            )

            fast_period = strategy_params.get("fast_period") or config.get(
                "FAST_PERIOD"
            )
            slow_period = strategy_params.get("slow_period") or config.get(
                "SLOW_PERIOD"
            )

            return analyze_window_combination(
                data=data,
                fast_period=fast_period,
                slow_period=slow_period,
                config=config,
                log=log,
            )
        except ImportError:
            log("Failed to import MA sensitivity analysis", "error")
            return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract MA-specific parameters."""
        return {
            "fast_period": row.get("Fast Period"),
            "slow_period": row.get("Slow Period"),
        }

    def _extract_signal_parameters_for_filtering(
        self, current_signals: pl.DataFrame
    ) -> Dict[str, list]:
        """Extract MA parameter values from current signals for filtering."""
        if len(current_signals) == 0:
            return {}

        return {
            "Fast Period": current_signals["Fast Period"].to_list(),
            "Slow Period": current_signals["Slow Period"].to_list(),
        }

    def _process_full_ticker_analysis(
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> Optional[Any]:
        """Process full MA ticker analysis."""
        try:
            from app.tools.portfolio.processing import process_single_ticker

            return process_single_ticker(ticker, config, log, progress_update_fn)
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

            fast_period = strategy_params.get("fast_period") or config.get(
                "FAST_PERIOD"
            )
            slow_period = strategy_params.get("slow_period") or config.get(
                "SLOW_PERIOD"
            )
            signal_period = strategy_params.get("signal_period") or config.get(
                "SIGNAL_PERIOD"
            )

            return analyze_parameter_combination(
                data=data,
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period,
                config=config,
                log=log,
            )
        except ImportError:
            log("Failed to import MACD sensitivity analysis", "error")
            return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract MACD-specific parameters."""
        return {
            "fast_period": row.get("Fast Period"),
            "slow_period": row.get("Slow Period"),
            "signal_period": row.get("Signal Period"),
        }

    def _extract_signal_parameters_for_filtering(
        self, current_signals: pl.DataFrame
    ) -> Dict[str, list]:
        """Extract MACD parameter values from current signals for filtering."""
        if len(current_signals) == 0:
            return {}

        return {
            "Fast Period": current_signals["Fast Period"].to_list(),
            "Slow Period": current_signals["Slow Period"].to_list(),
            "Signal Period": current_signals["Signal Period"].to_list(),
        }

    def _process_full_ticker_analysis(
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> Optional[Any]:
        """Process full MACD ticker analysis."""
        try:
            from app.strategies.macd.tools.portfolio_processing import (
                process_single_ticker,
            )

            return process_single_ticker(ticker, config, log, progress_update_fn)
        except ImportError:
            log("Failed to import MACD portfolio processing", "error")
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
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> Optional[Any]:
        """Process full Mean Reversion ticker analysis."""
        try:
            from app.strategies.mean_reversion.tools.portfolio_processing import (
                process_single_ticker,
            )

            return process_single_ticker(ticker, config, log, progress_update_fn)
        except ImportError:
            log("Failed to import Mean Reversion portfolio processing", "error")
            return None


class ATRSignalProcessor(SignalProcessorBase):
    """Signal processor for ATR Trailing Stop strategies."""

    def __init__(self):
        super().__init__("ATR")

    def generate_current_signals(
        self, config: Dict[str, Any], log: Callable
    ) -> pl.DataFrame:
        """Generate current signals for ATR strategy."""
        # For now, return empty DataFrame as ATR focuses on parameter sweep analysis
        # This can be enhanced later to support current signal analysis
        log("ATR current signals analysis not yet implemented", "warning")
        return pl.DataFrame()

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: Dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> Optional[Dict[str, Any]]:
        """Analyze a specific ATR parameter combination."""
        # This method is used for current signals analysis
        # For ATR, we focus on full ticker analysis instead
        return None

    def _extract_strategy_parameters(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Extract ATR-specific parameters from a signal row."""
        return {
            "ATR_LENGTH": row.get("ATR_Length", row.get("ATR Length", 14)),
            "ATR_MULTIPLIER": row.get("ATR_Multiplier", row.get("ATR Multiplier", 2.0)),
        }

    def _process_full_ticker_analysis(
        self,
        ticker: str,
        config: Dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> Optional[Any]:
        """Process full ATR ticker analysis."""
        try:
            from app.strategies.atr.tools.strategy_execution import execute_strategy

            # Create ticker-specific config
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker

            # Execute ATR strategy with parameter sweep
            return execute_strategy(ticker_config, "ATR", log, progress_update_fn)
        except ImportError:
            log("Failed to import ATR strategy execution", "error")
            return None


class SignalProcessorFactory:
    """Factory for creating strategy-specific signal processors."""

    _processors = {
        "SMA": lambda: MASignalProcessor("SMA"),
        "EMA": lambda: MASignalProcessor("EMA"),
        "MACD": lambda: MACDSignalProcessor(),
        "MEAN_REVERSION": lambda: MeanReversionSignalProcessor(),
        "MA_CROSS": lambda: MASignalProcessor("SMA"),  # Default to SMA
        "ATR": lambda: ATRSignalProcessor(),
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


def _detect_strategy_type(config: Dict[str, Any]) -> str:
    """
    Detect strategy type from configuration parameters.

    Args:
        config: Configuration dictionary

    Returns:
        Strategy type string (MACD, SMA, etc.)
    """
    # Check if explicitly set
    if "STRATEGY_TYPE" in config and config["STRATEGY_TYPE"]:
        return config["STRATEGY_TYPE"]

    # Detect MACD by presence of signal period parameters
    has_signal_window = any(
        key in config
        for key in ["SIGNAL_WINDOW_START", "SIGNAL_WINDOW_END", "signal_period"]
    )

    if has_signal_window:
        return "MACD"

    # Default to SMA for backward compatibility
    return "SMA"


# Convenience functions for backward compatibility
def process_current_signals(
    ticker: str,
    config: Dict[str, Any],
    log: Callable,
    strategy_type: str = None,
    progress_update_fn=None,
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
        strategy_type = _detect_strategy_type(config)

    processor = SignalProcessorFactory.create_processor(strategy_type)
    return processor.process_current_signals(ticker, config, log, progress_update_fn)


def process_ticker_portfolios(
    ticker: str,
    config: Dict[str, Any],
    log: Callable,
    strategy_type: str = None,
    progress_update_fn=None,
) -> Optional[pl.DataFrame]:
    """Process ticker portfolios using unified signal processing.

    Args:
        ticker: Ticker symbol
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        DataFrame of portfolios sorted by configured criteria or None
    """
    if strategy_type is None:
        strategy_type = _detect_strategy_type(config)

    processor = SignalProcessorFactory.create_processor(strategy_type)
    portfolios_df = processor.process_ticker_portfolios(
        ticker, config, log, progress_update_fn
    )

    if portfolios_df is not None and len(portfolios_df) > 0:
        # Apply consistent sorting using configuration
        sort_by = config.get("SORT_BY", "Score")
        sort_asc = config.get("SORT_ASC", False)

        if sort_by in portfolios_df.columns:
            portfolios_df = portfolios_df.sort(sort_by, descending=not sort_asc)
            if log:
                log(
                    f"Sorted portfolios by {sort_by} ({'ascending' if sort_asc else 'descending'})"
                )
        else:
            if log:
                log(
                    f"Warning: Sort column '{sort_by}' not found in portfolios, skipping sort",
                    "warning",
                )

    return portfolios_df
