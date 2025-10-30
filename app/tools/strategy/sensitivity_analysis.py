"""
Unified Sensitivity Analysis Module

This module consolidates sensitivity analysis functionality across all trading strategies,
eliminating duplication while maintaining strategy-specific behavior through
polymorphism and configuration.
"""

import os
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

import polars as pl

from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats

from .signal_processing import _detect_strategy_type


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
        self,
        data: pl.DataFrame,
        strategy_config: dict[str, Any],
        log: Callable,
    ) -> pl.DataFrame | None:
        """Calculate signals for the strategy with given parameters.

        Args:
            data: Price data DataFrame
            strategy_config: Strategy-specific configuration
            log: Logging function

        Returns:
            DataFrame with signals or None if failed
        """

    @abstractmethod
    def _check_signal_currency(self, data: pl.DataFrame) -> bool:
        """Check if current signal exists for the strategy.

        Args:
            data: DataFrame with signals

        Returns:
            True if current signal exists
        """

    @abstractmethod
    def _extract_strategy_parameters(self, **kwargs) -> dict[str, Any]:
        """Extract strategy-specific parameters from kwargs.

        Returns:
            Dictionary of strategy-specific parameters
        """

    def analyze_parameter_combination(
        self,
        data: pl.DataFrame,
        config: dict[str, Any],
        log: Callable,
        **strategy_params,
    ) -> dict[str, Any] | None:
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
                    "DIRECTION": config.get(
                        "DIRECTION",
                        "Long",
                    ),  # Preserve direction parameter
                },
            )

            # Log parameter combination
            param_str = self._format_parameters(**strategy_params)
            log(f"Analyzing {self.strategy_type} parameters: {param_str}", "debug")

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
                "fast_period": "Fast Period",
                "slow_period": "Slow Period",
                "signal_period": "Signal Period",
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
            return convert_stats(stats, log, config, current)

        except Exception as e:
            param_str = self._format_parameters(**strategy_params)
            log(
                f"Failed to process {self.strategy_type} parameters {param_str}: {e!s}",
                "warning",
            )
            return None

    def analyze_parameter_combinations(
        self,
        data: pl.DataFrame,
        parameter_sets: list[dict[str, Any]],
        config: dict[str, Any],
        log: Callable,
        parallel: bool = True,
        progress_update_fn=None,
    ) -> list[dict[str, Any]]:
        """Analyze multiple parameter combinations using unified logic.

        Args:
            data: Price data DataFrame
            parameter_sets: List of parameter dictionaries
            config: Configuration dictionary
            log: Logging function
            parallel: Enable parallel processing for large parameter sets

        Returns:
            List of portfolio statistics for each valid combination
        """
        # Use external progress tracking if provided (no local progress displays)
        if progress_update_fn:
            # Use parallel processing for large parameter sets when external progress is tracked
            if parallel and len(parameter_sets) > 10:
                return self._analyze_combinations_parallel(
                    data,
                    parameter_sets,
                    config,
                    log,
                    progress_update_fn,
                )

            # Sequential processing with external progress tracking
            portfolios = []
            for _i, params in enumerate(parameter_sets):
                result = self.analyze_parameter_combination(data, config, log, **params)
                if result is not None:
                    portfolios.append(result)

                # Update external progress after each combination
                progress_update_fn(1)

            return portfolios

        # No external progress - use local progress displays
        if parallel and len(parameter_sets) > 10:
            return self._analyze_combinations_parallel(
                data,
                parameter_sets,
                config,
                log,
                None,
            )

        # Sequential processing for small sets or when parallel is disabled
        portfolios = []
        for _i, params in enumerate(parameter_sets):
            result = self.analyze_parameter_combination(data, config, log, **params)
            if result is not None:
                portfolios.append(result)

        return portfolios

    def _analyze_combinations_parallel(
        self,
        data: pl.DataFrame,
        parameter_sets: list[dict[str, Any]],
        config: dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> list[dict[str, Any]]:
        """Analyze parameter combinations using parallel processing."""
        try:
            from app.tools.console_logging import PerformanceAwareConsoleLogger
            from app.tools.processing import parallel_parameter_sweep

            # Use external progress update function if provided (no local progress displays allowed)
            if progress_update_fn:
                log(
                    f"🚀 Starting parallel analysis of {len(parameter_sets)} {self.strategy_type} parameter combinations",
                    "info",
                )

                # Create wrapper function without progress update (handled by parallel executor)
                def strategy_wrapper_with_external_progress(
                    params: dict[str, Any],
                ) -> dict[str, Any] | None:
                    return self.analyze_parameter_combination(
                        data,
                        config,
                        log,
                        **params,
                    )

                # Use parallel parameter sweep with external progress callback
                batch_size = max(1, len(parameter_sets) // (os.cpu_count() or 4))
                results = parallel_parameter_sweep(
                    parameter_combinations=parameter_sets,
                    strategy_fn=strategy_wrapper_with_external_progress,
                    batch_size=batch_size,
                    timeout=None,
                    progress_callback=progress_update_fn,
                )

            else:
                # Check if we have access to enhanced progress display
                log_self = log.__self__ if hasattr(log, "__self__") else None
                use_enhanced_progress = isinstance(
                    log_self,
                    PerformanceAwareConsoleLogger,
                )

                if use_enhanced_progress:
                    console_logger = log.__self__

                    # Use enhanced progress context for large parameter sets
                    with console_logger.parameter_progress_context(
                        self.strategy_type,
                        len(parameter_sets),
                    ) as progress:
                        # Initialize task fields based on performance mode
                        task_fields = {
                            "rate": "0",
                            "workers": f"{os.cpu_count() or 4}",
                            "eta": "calculating...",
                        }

                        # Add memory field for detailed modes
                        if console_logger.show_resources:
                            import psutil

                            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                            task_fields["memory"] = f"{memory_mb:.0f}"

                        task = progress.add_task(
                            f"Analyzing {self.strategy_type} parameters...",
                            total=len(parameter_sets),
                            **task_fields,
                        )

                        log(
                            f"🚀 Starting parallel analysis of {len(parameter_sets)} {self.strategy_type} parameter combinations",
                            "info",
                        )

                        # Create wrapper function with enhanced progress updates
                        completed_count = 0
                        import time

                        start_time = time.time()

                        def strategy_wrapper_with_progress(
                            params: dict[str, Any],
                        ) -> dict[str, Any] | None:
                            nonlocal completed_count
                            result = self.analyze_parameter_combination(
                                data,
                                config,
                                log,
                                **params,
                            )
                            completed_count += 1

                            # Calculate processing metrics
                            elapsed = time.time() - start_time
                            rate = completed_count / elapsed if elapsed > 0 else 0

                            # Calculate ETA
                            remaining = len(parameter_sets) - completed_count
                            eta_seconds = remaining / rate if rate > 0 else 0
                            if eta_seconds > 3600:
                                eta_str = f"{eta_seconds / 3600:.1f}h"
                            elif eta_seconds > 60:
                                eta_str = f"{eta_seconds / 60:.1f}m"
                            else:
                                eta_str = f"{eta_seconds:.0f}s"

                            # Update progress with adaptive frequency
                            update_frequency = 5 if len(parameter_sets) < 100 else 10
                            if (
                                completed_count % update_frequency == 0
                                or completed_count == len(parameter_sets)
                            ):
                                update_fields = {
                                    "rate": f"{rate:.1f}",
                                    "workers": f"{os.cpu_count() or 4}",
                                    "eta": eta_str,
                                }

                                # Add memory monitoring for detailed modes
                                if console_logger.show_resources:
                                    try:
                                        import psutil

                                        memory_mb = (
                                            psutil.Process().memory_info().rss
                                            / 1024
                                            / 1024
                                        )
                                        update_fields["memory"] = f"{memory_mb:.0f}"
                                    except ImportError:
                                        pass

                                progress.update(
                                    task,
                                    completed=completed_count,
                                    **update_fields,
                                )

                            return result

                        # Use parallel parameter sweep
                        batch_size = max(
                            1,
                            len(parameter_sets) // (os.cpu_count() or 4),
                        )
                        results = parallel_parameter_sweep(
                            parameter_combinations=parameter_sets,
                            strategy_fn=strategy_wrapper_with_progress,
                            batch_size=batch_size,
                            timeout=None,
                            progress_callback=None,  # Internal progress tracking handled by wrapper
                        )

                        # Final progress update
                        elapsed = time.time() - start_time
                        final_rate = completed_count / elapsed if elapsed > 0 else 0
                        final_fields = {
                            "rate": f"{final_rate:.1f}",
                            "workers": f"{os.cpu_count() or 4}",
                            "eta": "complete",
                        }

                        if console_logger.show_resources:
                            try:
                                import psutil

                                memory_mb = (
                                    psutil.Process().memory_info().rss / 1024 / 1024
                                )
                                final_fields["memory"] = f"{memory_mb:.0f}"
                            except ImportError:
                                pass

                        progress.update(
                            task,
                            completed=len(parameter_sets),
                            **final_fields,
                        )
                else:
                    # Fallback to basic logging without enhanced progress
                    log(
                        f"🚀 Starting parallel analysis of {len(parameter_sets)} {self.strategy_type} parameter combinations",
                        "info",
                    )

                    # Create wrapper function for strategy analysis
                    def strategy_wrapper(
                        params: dict[str, Any],
                    ) -> dict[str, Any] | None:
                        return self.analyze_parameter_combination(
                            data,
                            config,
                            log,
                            **params,
                        )

                    # Use parallel parameter sweep with CPU-bound executor
                    batch_size = max(1, len(parameter_sets) // (os.cpu_count() or 4))
                    log(
                        f"⚙️  Using {os.cpu_count() or 4} CPU cores with batch size {batch_size}",
                        "info",
                    )

                    results = parallel_parameter_sweep(
                        parameter_combinations=parameter_sets,
                        strategy_fn=strategy_wrapper,
                        batch_size=batch_size,
                        timeout=None,
                        progress_callback=None,  # No external progress tracking
                    )

            # Filter out None results
            valid_portfolios = [result for result in results if result is not None]

            log(
                f"✅ Parallel processing complete: {len(valid_portfolios)}/{len(parameter_sets)} successful",
                "info",
            )
            return valid_portfolios

        except ImportError:
            log(
                "Parallel processing not available, falling back to sequential",
                "warning",
            )
            return self._analyze_combinations_sequential(
                data,
                parameter_sets,
                config,
                log,
                progress_update_fn,
            )
        except Exception as e:
            log(
                f"Parallel processing failed: {e}, falling back to sequential",
                "warning",
            )
            return self._analyze_combinations_sequential(
                data,
                parameter_sets,
                config,
                log,
                progress_update_fn,
            )

    def _analyze_combinations_sequential(
        self,
        data: pl.DataFrame,
        parameter_sets: list[dict[str, Any]],
        config: dict[str, Any],
        log: Callable,
        progress_update_fn=None,
    ) -> list[dict[str, Any]]:
        """Fallback sequential processing."""
        portfolios = []
        for params in parameter_sets:
            result = self.analyze_parameter_combination(data, config, log, **params)
            if result is not None:
                portfolios.append(result)

            # Update external progress if function provided
            if progress_update_fn:
                progress_update_fn(1)

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

    @abstractmethod
    def _format_parameters(self, **strategy_params) -> str:
        """Format parameters for logging.

        Args:
            **strategy_params: Strategy-specific parameters

        Returns:
            Formatted parameter string
        """


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
        self,
        data: pl.DataFrame,
        strategy_config: dict[str, Any],
        log: Callable,
    ) -> pl.DataFrame | None:
        """Calculate MA signals."""
        try:
            from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

            return calculate_ma_and_signals(
                data=data,
                fast_period=strategy_config.get("fast_period"),
                slow_period=strategy_config.get("slow_period"),
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

    def _extract_strategy_parameters(self, **kwargs) -> dict[str, Any]:
        """Extract MA-specific parameters."""
        # Support both new and legacy parameter names
        fast_period = (
            kwargs.get("fast_period")
            or kwargs.get("fast_period")
            or kwargs.get("short")
        )
        slow_period = (
            kwargs.get("slow_period") or kwargs.get("slow_period") or kwargs.get("long")
        )

        if fast_period is None or slow_period is None:
            msg = "MA strategy requires fast_period and slow_period parameters"
            raise ValueError(
                msg,
            )

        return {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "USE_SMA": self.ma_type == "SMA",
        }

    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for MA periods."""
        fast_period = (
            strategy_params.get("fast_period")
            or strategy_params.get("fast_period")
            or strategy_params.get("short")
        )
        slow_period = (
            strategy_params.get("slow_period")
            or strategy_params.get("slow_period")
            or strategy_params.get("long")
        )

        max_period = max(fast_period or 0, slow_period or 0)
        return len(data) >= max_period

    def _format_parameters(self, **strategy_params) -> str:
        """Format MA parameters for logging."""
        fast = (
            strategy_params.get("fast_period")
            or strategy_params.get("fast")
            or strategy_params.get("short")
        )
        slow = (
            strategy_params.get("slow_period")
            or strategy_params.get("slow")
            or strategy_params.get("long")
        )
        return f"Short: {fast}, Long: {slow}"


class MACDSensitivityAnalyzer(SensitivityAnalyzerBase):
    """Sensitivity analyzer for MACD strategies."""

    def __init__(self):
        super().__init__("MACD")

    def _calculate_signals(
        self,
        data: pl.DataFrame,
        strategy_config: dict[str, Any],
        log: Callable,
    ) -> pl.DataFrame | None:
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

    def _extract_strategy_parameters(self, **kwargs) -> dict[str, Any]:
        """Extract MACD-specific parameters."""
        # Support both new and legacy parameter names
        fast_period = kwargs.get("fast_period") or kwargs.get("fast_period")
        slow_period = kwargs.get("slow_period") or kwargs.get("slow_period")
        signal_period = kwargs.get("signal_period") or kwargs.get("signal_period")

        if fast_period is None or slow_period is None or signal_period is None:
            msg = "MACD strategy requires fast_period, slow_period, and signal_period parameters"
            raise ValueError(
                msg,
            )

        return {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
        }

    def _check_data_sufficiency(self, data: pl.DataFrame, **strategy_params) -> bool:
        """Check if data is sufficient for MACD periods."""
        fast_period = strategy_params.get("fast_period") or strategy_params.get(
            "fast_period",
            0,
        )
        slow_period = strategy_params.get("slow_period") or strategy_params.get(
            "slow_period",
            0,
        )
        signal_period = strategy_params.get("signal_period") or strategy_params.get(
            "signal_period",
            0,
        )

        max_period = max(fast_period, slow_period, signal_period)
        return len(data) >= max_period

    def _format_parameters(self, **strategy_params) -> str:
        """Format MACD parameters for logging."""
        fast = (
            strategy_params.get("fast_period")
            or strategy_params.get("fast")
            or strategy_params.get("short")
        )
        slow = (
            strategy_params.get("slow_period")
            or strategy_params.get("slow")
            or strategy_params.get("long")
        )
        signal = strategy_params.get("signal_period") or strategy_params.get("signal")
        return f"Short: {fast}, Long: {slow}, Signal: {signal}"


class MeanReversionSensitivityAnalyzer(SensitivityAnalyzerBase):
    """Sensitivity analyzer for Mean Reversion strategies."""

    def __init__(self):
        super().__init__("MEAN_REVERSION")

    def _calculate_signals(
        self,
        data: pl.DataFrame,
        strategy_config: dict[str, Any],
        log: Callable,
    ) -> pl.DataFrame | None:
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

    def _extract_strategy_parameters(self, **kwargs) -> dict[str, Any]:
        """Extract Mean Reversion-specific parameters."""
        change_pct = kwargs.get("change_pct")

        if change_pct is None:
            msg = "Mean Reversion strategy requires change_pct parameter"
            raise ValueError(msg)

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
            msg = f"Unsupported strategy type: {strategy_type}. Available: {available}"
            raise ValueError(
                msg,
            )

        return cls._analyzers[strategy_type]()

    @classmethod
    def get_supported_strategies(cls) -> list[str]:
        """Get list of supported strategy types."""
        return list(cls._analyzers.keys())


# Convenience functions for backward compatibility
def analyze_parameter_combination(
    data: pl.DataFrame,
    config: dict[str, Any],
    log: Callable,
    strategy_type: str | None = None,
    **strategy_params,
) -> dict[str, Any] | None:
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
    parameter_sets: list[dict[str, Any]],
    config: dict[str, Any],
    log: Callable,
    strategy_type: str | None = None,
    parallel: bool = True,
    progress_update_fn=None,
) -> list[dict[str, Any]]:
    """Analyze multiple parameter combinations using unified sensitivity analysis.

    Args:
        data: Price data DataFrame
        parameter_sets: List of parameter dictionaries
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)
        parallel: Enable parallel processing for large parameter sets

    Returns:
        List of portfolio statistics
    """
    if strategy_type is None:
        strategy_type = _detect_strategy_type(config)

    analyzer = SensitivityAnalyzerFactory.create_analyzer(strategy_type)
    return analyzer.analyze_parameter_combinations(
        data,
        parameter_sets,
        config,
        log,
        parallel=parallel,
        progress_update_fn=progress_update_fn,
    )


# Strategy-specific convenience functions for backward compatibility
def analyze_window_combination(
    data: pl.DataFrame,
    fast_period: int | None = None,
    slow_period: int | None = None,
    short: int | None = None,
    long: int | None = None,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> dict[str, Any] | None:
    """Analyze MA window combination (supports both new and legacy parameter names).

    Args:
        data: Price data DataFrame
        fast_period: Fast period (new parameter name)
        slow_period: Slow period (new parameter name)
        short: Fast period (legacy parameter name)
        long: Slow period (legacy parameter name)
        config: Configuration dictionary
        log: Logging function

    Returns:
        Portfolio statistics if successful, None if failed
    """
    # Handle both new and legacy parameter names
    fast = fast_period or short
    slow = slow_period or long

    if fast is None or slow is None:
        msg = "Must provide either fast_period/slow_period or short/long parameters"
        raise ValueError(
            msg,
        )

    strategy_type = config.get("STRATEGY_TYPE", "SMA")
    analyzer = SensitivityAnalyzerFactory.create_analyzer(strategy_type)
    return analyzer.analyze_parameter_combination(
        data,
        config,
        log,
        fast_period=fast,
        slow_period=slow,
    )


def analyze_macd_combination(
    data: pl.DataFrame,
    fast_period: int | None = None,
    slow_period: int | None = None,
    signal_period: int | None = None,
    config: dict[str, Any] | None = None,
    log: Callable | None = None,
) -> dict[str, Any] | None:
    """Analyze MACD parameter combination (supports both new and legacy parameter names).

    Args:
        data: Price data DataFrame
        fast_period: Fast EMA period (new parameter name)
        slow_period: Slow EMA period (new parameter name)
        signal_period: Signal line EMA period (new parameter name)
        fast_period: Short-term EMA period (legacy parameter name)
        slow_period: Long-term EMA period (legacy parameter name)
        signal_period: Signal line EMA period (legacy parameter name)
        config: Configuration dictionary
        log: Logging function

    Returns:
        Portfolio statistics if successful, None if failed
    """
    # Handle both new and legacy parameter names
    fast = fast_period or fast_period
    slow = slow_period or slow_period
    signal = signal_period or signal_period

    if fast is None or slow is None or signal is None:
        msg = "Must provide either fast_period/slow_period/signal_period or fast_period/slow_period/signal_period parameters"
        raise ValueError(
            msg,
        )

    analyzer = SensitivityAnalyzerFactory.create_analyzer("MACD")
    return analyzer.analyze_parameter_combination(
        data,
        config,
        log,
        fast_period=fast,
        slow_period=slow,
        signal_period=signal,
    )


def analyze_mean_reversion_combination(
    data: pl.DataFrame,
    change_pct: float,
    config: dict[str, Any],
    log: Callable,
) -> dict[str, Any] | None:
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
        data,
        config,
        log,
        change_pct=change_pct,
    )


def analyze_single_portfolio(
    signal_data: pl.DataFrame,
    config: dict[str, Any],
    log: Callable,
    strategy_type: str | None = None,
) -> dict[str, Any] | None:
    """Analyze a single portfolio with pre-generated signals.

    This function performs portfolio analysis on signal data that has already been generated,
    typically used by strategy-specific modules that have their own signal generation logic.

    Args:
        signal_data: DataFrame containing pre-generated signals
        config: Configuration dictionary
        log: Logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        Portfolio statistics if successful, None if failed
    """
    try:
        # Validate input data
        if signal_data is None or len(signal_data) == 0:
            log("No signal data provided for portfolio analysis", "warning")
            return None

        # Auto-detect strategy type if not provided
        if strategy_type is None:
            strategy_type = _detect_strategy_type(config)

        # Perform backtesting on the signal data
        portfolio = backtest_strategy(signal_data, config, log)

        # Convert statistics
        stats = portfolio.stats()

        # Add strategy information to stats
        if "TICKER" in config:
            stats["Ticker"] = config["TICKER"]
        if strategy_type:
            stats["Strategy Type"] = strategy_type

        # Check signal currency (if signal data has the necessary structure)
        current = False
        try:
            from app.tools.strategy.signal_utils import is_signal_current

            current = is_signal_current(signal_data)
        except (ImportError, Exception):
            # Default to False if we can't determine signal currency
            current = False

        # Convert stats to standard format
        return convert_stats(stats, log, config, current)

    except Exception as e:
        log(f"Failed to analyze single portfolio: {e!s}", "error")
        return None
