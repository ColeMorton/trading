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
            "STRATEGY_TYPES": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "USE_YEARS": config.use_years,
            "YEARS": config.years,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
            "MULTI_TICKER": is_multi_ticker,
            "USE_SCANNER": config.use_scanner,
            "SCANNER_LIST": config.scanner_list,
            "USE_GBM": config.use_gbm,
            "MINIMUMS": {},
        }

        # Handle ticker configuration based on synthetic mode
        if config.synthetic.use_synthetic:
            # For synthetic mode, don't set TICKER here - let process_synthetic_config handle it
            legacy_config["USE_SYNTHETIC"] = True
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
            legacy_config["TICKER_2"] = config.synthetic.ticker_2
        else:
            # For normal mode, set TICKER as usual
            legacy_config["TICKER"] = ticker_list

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

        # Add parameter ranges for sweeps - prioritize strategy-specific params, fall back to global
        def get_strategy_specific_params(strategy_type: str):
            """Extract strategy-specific parameters with fallback to global parameters."""
            if config.strategy_params and hasattr(
                config.strategy_params, strategy_type
            ):
                strategy_params = getattr(config.strategy_params, strategy_type)
                if strategy_params:
                    return strategy_params
            return None

        # Check all strategy types supported by this service (SMA, EMA)
        strategy_types_to_check = ["SMA", "EMA"]
        strategy_params_found = None

        for strategy_type in strategy_types_to_check:
            if strategy_type in [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ]:
                strategy_params_found = get_strategy_specific_params(strategy_type)
                if strategy_params_found:
                    break

        # CLI overrides take precedence over strategy-specific parameters

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

        # Add USE_CURRENT and USE_DATE configuration
        legacy_config["USE_CURRENT"] = (
            getattr(config.filter, "use_current", False) or False
        )
        legacy_config["USE_DATE"] = getattr(config.filter, "date_filter", None)

        # Add sorting parameters to maintain consistency with MACD
        legacy_config["SORT_BY"] = getattr(config, "sort_by", "Score")
        legacy_config["SORT_ASC"] = getattr(config, "sort_ascending", False)

        # Add skip_analysis flag
        legacy_config["SKIP_ANALYSIS"] = getattr(config, "skip_analysis", False)

        # Add direction configuration
        legacy_config["DIRECTION"] = getattr(config, "direction", "Long")

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

        # Check for strategy-specific MACD parameters first, then fall back to global parameters
        macd_params = None
        if config.strategy_params and config.strategy_params.MACD:
            macd_params = config.strategy_params.MACD

        # Determine parameter sources with priority: strategy-specific > global new format > legacy format
        has_strategy_specific = (
            macd_params is not None
            and macd_params.fast_period_min is not None
            and macd_params.fast_period_max is not None
            and macd_params.slow_period_min is not None
            and macd_params.slow_period_max is not None
            and macd_params.signal_period_min is not None
            and macd_params.signal_period_max is not None
        )

        has_global_new_format = (
            config.fast_period_min is not None
            and config.fast_period_max is not None
            and config.slow_period_min is not None
            and config.slow_period_max is not None
            and config.signal_period_min is not None
            and config.signal_period_max is not None
        )

        has_legacy_format = (
            config.short_window_start is not None
            and config.short_window_end is not None
            and config.long_window_start is not None
            and config.long_window_end is not None
            and config.signal_window_start is not None
            and config.signal_window_end is not None
        )

        if (
            not has_strategy_specific
            and not has_global_new_format
            and not has_legacy_format
        ):
            rprint(f"[red]Missing required MACD parameters[/red]")
            rprint(
                f"[yellow]Ensure your profile contains either:\n"
                + "Strategy-specific: strategy_params.MACD.fast_period_min/max, slow_period_min/max, signal_period_min/max\n"
                + "Global format: fast_period_min/max, slow_period_min/max, signal_period_min/max\n"
                + "OR Legacy format: short_window_start/end, long_window_start/end, signal_window_start/end[/yellow]"
            )
            raise ValueError(f"Incomplete MACD configuration")

        try:
            # Extract parameters with priority: strategy-specific > global new format > legacy format
            if has_strategy_specific:
                fast_min, fast_max = (
                    macd_params.fast_period_min,
                    macd_params.fast_period_max,
                )
                slow_min, slow_max = (
                    macd_params.slow_period_min,
                    macd_params.slow_period_max,
                )
                signal_min, signal_max = (
                    macd_params.signal_period_min,
                    macd_params.signal_period_max,
                )
                step = macd_params.step if macd_params.step is not None else 1
            elif has_global_new_format:
                fast_min, fast_max = config.fast_period_min, config.fast_period_max
                slow_min, slow_max = config.slow_period_min, config.slow_period_max
                signal_min, signal_max = (
                    config.signal_period_min,
                    config.signal_period_max,
                )
                step = getattr(config, "step", 1)
            else:  # has_legacy_format
                fast_min, fast_max = config.short_window_start, config.short_window_end
                slow_min, slow_max = config.long_window_start, config.long_window_end
                signal_min, signal_max = (
                    config.signal_window_start,
                    config.signal_window_end,
                )
                step = getattr(config, "step", 1)

            legacy_config = {
                "STRATEGY_TYPE": "MACD",
                "STRATEGY_TYPES": ["MACD"],
                "SHORT_WINDOW_START": fast_min,
                "SHORT_WINDOW_END": fast_max,
                "LONG_WINDOW_START": slow_min,
                "LONG_WINDOW_END": slow_max,
                "SIGNAL_WINDOW_START": signal_min,
                "SIGNAL_WINDOW_END": signal_max,
                "SIGNAL_PERIOD": signal_min,  # For fallback detection
                "STEP": step,
                "DIRECTION": getattr(config, "direction", "Long"),
                "USE_CURRENT": getattr(config.filter, "use_current", False) or False,
                "USE_DATE": getattr(config.filter, "date_filter", None),
                "USE_HOURLY": getattr(config, "use_hourly", False),
                "USE_4HOUR": getattr(config, "use_4hour", False),
                "USE_2DAY": getattr(config, "use_2day", False),
                "USE_YEARS": getattr(config, "use_years", False),
                "YEARS": getattr(config, "years", None),
                "REFRESH": getattr(config, "refresh", True),
                "MINIMUMS": {},
                # Add sorting parameters from YAML config
                "SORT_BY": getattr(config, "sort_by", "Score"),
                "SORT_ASC": getattr(config, "sort_ascending", False),
                # Add skip_analysis flag
                "SKIP_ANALYSIS": getattr(config, "skip_analysis", False),
            }

            # Handle ticker configuration based on synthetic mode (same as MA Cross service)
            if config.synthetic.use_synthetic:
                # For synthetic mode, don't set TICKER here - let process_synthetic_config handle it
                legacy_config["USE_SYNTHETIC"] = True
                legacy_config["TICKER_1"] = config.synthetic.ticker_1
                legacy_config["TICKER_2"] = config.synthetic.ticker_2
                legacy_config[
                    "MULTI_TICKER"
                ] = False  # Synthetic pairs are treated as single ticker
            else:
                # For normal mode, set TICKER as usual
                legacy_config["TICKER"] = ticker_list
                legacy_config["MULTI_TICKER"] = len(ticker_list) > 1
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


class ATRStrategyService(BaseStrategyService):
    """Service for ATR (Average True Range) Trailing Stop strategy execution."""

    def execute_strategy(self, config: StrategyConfig) -> bool:
        """Execute ATR strategy analysis."""
        try:
            # Import ATR module
            atr_module = importlib.import_module("app.strategies.atr.1_get_portfolios")
            run = atr_module.run

            # Convert config to legacy format
            legacy_config = self.convert_config_to_legacy(config)

            # Execute strategy
            result = run(legacy_config)

            if result:
                rprint("[green]ATR strategy execution completed successfully[/green]")
            else:
                rprint(
                    "[yellow]ATR strategy execution completed with warnings[/yellow]"
                )

            return result

        except Exception as e:
            rprint(f"[red]Error executing ATR strategy: {e}[/red]")
            return False

    def convert_config_to_legacy(self, config: StrategyConfig) -> Dict[str, Any]:
        """Convert CLI configuration to ATR legacy format."""
        try:
            # Handle ticker list based on config type
            ticker_list = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            # Set ATR-specific parameters with defaults
            legacy_config = {
                "STRATEGY_TYPE": "ATR",
                "STRATEGY_TYPES": ["ATR"],
                "ATR_LENGTH_START": getattr(config, "atr_length_min", 2),
                "ATR_LENGTH_END": getattr(config, "atr_length_max", 15),
                "ATR_MULTIPLIER_START": getattr(config, "atr_multiplier_min", 1.5),
                "ATR_MULTIPLIER_END": getattr(config, "atr_multiplier_max", 8.0),
                "ATR_MULTIPLIER_STEP": getattr(config, "atr_multiplier_step", 0.5),
                "STEP": getattr(config, "step", 1),
                "DIRECTION": getattr(config, "direction", "Long"),
                "USE_CURRENT": getattr(config.filter, "use_current", False) or False,
                "USE_DATE": getattr(config.filter, "date_filter", None),
                "USE_HOURLY": getattr(config, "use_hourly", False),
                "USE_4HOUR": getattr(config, "use_4hour", False),
                "USE_2DAY": getattr(config, "use_2day", False),
                "USE_YEARS": getattr(config, "use_years", False),
                "YEARS": getattr(config, "years", None),
                "REFRESH": getattr(config, "refresh", True),
                "MINIMUMS": {},
                # Add sorting parameters from YAML config
                "SORT_BY": getattr(config, "sort_by", "Score"),
                "SORT_ASC": getattr(config, "sort_ascending", False),
                # Add skip_analysis flag
                "SKIP_ANALYSIS": getattr(config, "skip_analysis", False),
                # Add base directory
                "BASE_DIR": ".",
            }

            # Handle ticker configuration based on synthetic mode
            if config.synthetic.use_synthetic:
                # For synthetic mode, don't set TICKER here - let process_synthetic_config handle it
                legacy_config["USE_SYNTHETIC"] = True
                legacy_config["TICKER_1"] = config.synthetic.ticker_1
                legacy_config["TICKER_2"] = config.synthetic.ticker_2
                legacy_config[
                    "MULTI_TICKER"
                ] = False  # Synthetic pairs are treated as single ticker
            else:
                # For normal mode, set TICKER as usual
                legacy_config["TICKER"] = ticker_list
                legacy_config["MULTI_TICKER"] = len(ticker_list) > 1

        except AttributeError as e:
            rprint(f"[red]Error accessing ATR parameters: {e}[/red]")
            raise ValueError(f"ATR configuration error: {e}")

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

        return legacy_config

    def get_supported_strategy_types(self) -> List[str]:
        """Get supported strategy types for ATR."""
        return ["ATR"]
