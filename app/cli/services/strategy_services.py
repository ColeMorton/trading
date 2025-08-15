"""
Strategy Service Layer

This module provides strategy-specific service implementations that
wrap underlying strategy modules with consistent CLI-compatible interfaces.
"""

import importlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from rich import print as rprint

from ..models.strategy import StrategyConfig


class BaseStrategyService(ABC):
    """Abstract base class for strategy services."""

    @abstractmethod
    def execute_strategy(self, config: StrategyConfig) -> bool:
        """
        Execute strategy analysis with the given configuration.

        Args:
            config: Strategy configuration model

        Returns:
            True if execution successful, False otherwise
        """
        pass

    @abstractmethod
    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """
        Convert CLI configuration to legacy format expected by strategy module.

        Args:
            config: Strategy configuration model

        Returns:
            Legacy configuration dictionary
        """
        pass

    @abstractmethod
    def get_supported_strategy_types(self) -> List[str]:
        """Get list of strategy types supported by this service."""
        pass


class MAStrategyService(BaseStrategyService):
    """Service for MA Cross strategy execution."""

    def execute_strategy(self, config: StrategyConfig) -> bool:
        """Execute MA Cross strategy analysis."""
        try:
            # Import MA Cross module
            ma_cross_module = importlib.import_module(
                "app.strategies.ma_cross.1_get_portfolios"
            )
            run = ma_cross_module.run

            # Convert config to legacy format
            legacy_config = self.convert_config_to_legacy(config)

            # Execute strategy
            return run(legacy_config)

        except Exception as e:
            rprint(f"[red]Error executing MA Cross strategy: {e}[/red]")
            return False

    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """Convert CLI config to MA Cross legacy format."""
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Automatically detect multi-ticker based on ticker list length
        is_multi_ticker = len(ticker_list) > 1

        # Base legacy config structure
        legacy_config = {
            "TICKER": ticker_list,
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "MULTI_TICKER": is_multi_ticker,
            "USE_SCANNER": config.use_scanner,
            "SCANNER_LIST": config.scanner_list,
            "USE_GBM": config.use_gbm,
            "MINIMUMS": {},
        }

        # Add minimum criteria
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"][
                "EXPECTANCY_PER_TRADE"
            ] = config.minimums.expectancy_per_trade
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

        # Add synthetic ticker configuration
        if config.synthetic.use_synthetic:
            legacy_config["USE_SYNTHETIC"] = True
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
            legacy_config["TICKER_2"] = config.synthetic.ticker_2

        # Add parameter ranges for sweeps if specified
        if config.fast_period_range:
            legacy_config["FAST_PERIOD_RANGE"] = config.fast_period_range
        if config.slow_period_range:
            legacy_config["SLOW_PERIOD_RANGE"] = config.slow_period_range

        # Add specific periods if provided
        if config.fast_period:
            legacy_config["FAST_PERIOD"] = config.fast_period
        if config.slow_period:
            legacy_config["SLOW_PERIOD"] = config.slow_period

        # Add USE_CURRENT configuration
        legacy_config["USE_CURRENT"] = getattr(config, "use_current", False) or False

        # Add sorting parameters to maintain consistency with MACD
        legacy_config["SORT_BY"] = getattr(config, "sort_by", "Score")
        legacy_config["SORT_ASC"] = getattr(config, "sort_ascending", False)

        # Add skip_analysis flag
        legacy_config["SKIP_ANALYSIS"] = getattr(config, "skip_analysis", False)

        return legacy_config

    def get_supported_strategy_types(self) -> List[str]:
        """Get supported strategy types for MA Cross."""
        return ["SMA", "EMA"]


class MACDStrategyService(BaseStrategyService):
    """Service for MACD strategy execution."""

    def execute_strategy(self, config: StrategyConfig) -> bool:
        """Execute MACD strategy analysis."""
        try:
            # Import MACD module
            macd_module = importlib.import_module(
                "app.strategies.macd.1_get_portfolios"
            )
            run = macd_module.run

            # Convert config to legacy format
            legacy_config = self.convert_config_to_legacy(config)

            # Execute strategy
            return run(legacy_config)

        except Exception as e:
            rprint(f"[red]Error executing MACD strategy: {e}[/red]")
            return False

    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """Convert CLI config to MACD legacy format with direct YAML parameter mapping."""
        # Convert ticker to list format
        ticker_list = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )

        # Direct mapping from YAML config to MACD parameters with fail-fast validation
        required_params = [
            "short_window_start",
            "short_window_end",
            "long_window_start",
            "long_window_end",
            "signal_window_start",
            "signal_window_end",
        ]

        # Check for required parameters
        missing_params = []
        for param in required_params:
            value = getattr(config, param, None)
            if value is None:
                missing_params.append(param)

        if missing_params:
            rprint(f"[red]Missing required MACD parameters: {missing_params}[/red]")
            rprint(
                f"[yellow]Ensure your profile contains: short_window_start, short_window_end, long_window_start, long_window_end, signal_window_start, signal_window_end[/yellow]"
            )
            raise ValueError(f"Incomplete MACD configuration: missing {missing_params}")

        try:
            legacy_config = {
                "TICKER": ticker_list,
                "STRATEGY_TYPE": "MACD",
                "STRATEGY_TYPES": ["MACD"],
                "SHORT_WINDOW_START": config.short_window_start,
                "SHORT_WINDOW_END": config.short_window_end,
                "LONG_WINDOW_START": config.long_window_start,
                "LONG_WINDOW_END": config.long_window_end,
                "SIGNAL_WINDOW_START": config.signal_window_start,
                "SIGNAL_WINDOW_END": config.signal_window_end,
                "SIGNAL_WINDOW": config.signal_window_start,  # For fallback detection
                "STEP": getattr(config, "step", 1),
                "DIRECTION": getattr(config, "direction", "Long"),
                "USE_CURRENT": getattr(config, "use_current", False) or False,
                "USE_HOURLY": getattr(config, "use_hourly", False),
                "USE_4HOUR": getattr(config, "use_4hour", False),
                "USE_YEARS": getattr(config, "use_years", False),
                "YEARS": getattr(config, "years", None),
                "REFRESH": getattr(config, "refresh", True),
                "MULTI_TICKER": len(ticker_list) > 1,
                "MINIMUMS": {},
                # Add sorting parameters from YAML config
                "SORT_BY": getattr(config, "sort_by", "Score"),
                "SORT_ASC": getattr(config, "sort_ascending", False),
                # Add skip_analysis flag
                "SKIP_ANALYSIS": getattr(config, "skip_analysis", False),
            }
        except AttributeError as e:
            rprint(f"[red]Error accessing MACD parameters: {e}[/red]")
            raise ValueError(f"MACD configuration error: {e}")

        # Add minimum criteria (same as MA Cross)
        if config.minimums.win_rate is not None:
            legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
        if config.minimums.trades is not None:
            legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
        if config.minimums.expectancy_per_trade is not None:
            legacy_config["MINIMUMS"][
                "EXPECTANCY_PER_TRADE"
            ] = config.minimums.expectancy_per_trade
        if config.minimums.profit_factor is not None:
            legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
        if config.minimums.sortino_ratio is not None:
            legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
        if config.minimums.beats_bnh is not None:
            legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

        return legacy_config

    def get_supported_strategy_types(self) -> List[str]:
        """Get supported strategy types for MACD."""
        return ["MACD"]
