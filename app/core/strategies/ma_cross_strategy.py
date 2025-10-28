"""
MA Cross Strategy Implementation

This module implements the MA Cross strategy using the Strategy Pattern.
"""

from typing import Any

from app.core.interfaces.strategy import StrategyInterface
from app.tools.project_utils import get_project_root


class MACrossStrategy(StrategyInterface):
    """MA Cross strategy implementation using Strategy Pattern."""

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "MA_CROSS"

    def validate_parameters(self, config: dict[str, Any]) -> bool:
        """Validate MA Cross strategy parameters."""
        try:
            # Check required parameters
            if "TICKER" not in config:
                return False

            strategy_types = config.get("STRATEGY_TYPES", [])
            if not strategy_types:
                return False

            # Validate strategy types are SMA or EMA
            valid_types = {"SMA", "EMA"}
            if not all(st in valid_types for st in strategy_types):
                return False

            # Validate range parameters (preferred) or windows parameter (deprecated)
            fast_range = config.get("FAST_PERIOD_RANGE")
            slow_range = config.get("SLOW_PERIOD_RANGE")

            if fast_range is not None and slow_range is not None:
                # Validate explicit ranges
                if (
                    not isinstance(fast_range, list)
                    or len(fast_range) != 2
                    or not isinstance(slow_range, list)
                    or len(slow_range) != 2
                ):
                    return False
                if (
                    fast_range[0] < 1
                    or fast_range[1] > 200
                    or fast_range[0] >= fast_range[1]
                    or slow_range[0] < 1
                    or slow_range[1] > 200
                    or slow_range[0] >= slow_range[1]
                ):
                    return False
            elif "WINDOWS" in config:
                # Backward compatibility: validate windows parameter
                import warnings

                warnings.warn(
                    "WINDOWS parameter is deprecated. Use FAST_PERIOD_RANGE and SLOW_PERIOD_RANGE instead.",
                    DeprecationWarning,
                    stacklevel=2,
                )
                windows = config.get("WINDOWS", 89)
                if not isinstance(windows, int) or windows < 2 or windows > 200:
                    return False
            # If neither ranges nor WINDOWS specified, use defaults (always valid)

            return True

        except Exception:
            return False

    def get_parameter_ranges(self) -> dict[str, Any]:
        """Get MA Cross strategy parameter ranges and defaults."""
        return {
            "FAST_PERIOD_RANGE": {"min": [1, 1], "max": [199, 200], "default": [5, 89]},
            "SLOW_PERIOD_RANGE": {"min": [1, 1], "max": [199, 200], "default": [8, 89]},
            "WINDOWS": {"min": 2, "max": 200, "default": 89, "deprecated": True},
            "STRATEGY_TYPES": {"options": ["SMA", "EMA"], "default": ["SMA", "EMA"]},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
            "USE_HOURLY": {"type": "boolean", "default": False},
            "USE_YEARS": {"type": "boolean", "default": False},
            "YEARS": {"min": 1, "max": 50, "default": 15},
        }

    def execute(self, config: dict[str, Any], log: Any) -> list[dict[str, Any]]:
        """Execute MA Cross strategy analysis."""
        try:
            # Import the execute_strategy functions from ma_cross module
            from app.strategies.ma_cross.tools.strategy_execution import (
                execute_strategy,
                execute_strategy_concurrent,
            )

            # Ensure BASE_DIR is set in config
            if "BASE_DIR" not in config:
                config["BASE_DIR"] = get_project_root()

            # Get strategy types to analyze
            strategy_types = config.get("STRATEGY_TYPES", ["SMA", "EMA"])

            # Determine optimal execution strategy based on ticker count
            tickers = config.get("TICKER", [])
            if isinstance(tickers, str):
                tickers = [tickers]
            use_concurrent = len(tickers) > 2  # Use concurrent for 3+ tickers

            log(
                f"Processing {len(tickers)} tickers with {'concurrent' if use_concurrent else 'sequential'} execution",
            )

            # Collect all portfolios in a single list
            all_portfolio_dicts = []

            # Execute strategy for each strategy type
            for _i, strategy_type in enumerate(strategy_types):
                log(f"Executing {strategy_type} strategy analysis")

                # Execute the strategy using optimal execution method
                if use_concurrent:
                    portfolios = execute_strategy_concurrent(
                        config,
                        strategy_type,
                        log,
                        None,
                    )
                else:
                    portfolios = execute_strategy(config, strategy_type, log, None)

                log(
                    f"execute_strategy returned {len(portfolios) if portfolios else 0} portfolios for {strategy_type}",
                )

                if portfolios:
                    log(f"First portfolio keys: {list(portfolios[0].keys())}")
                    # Keep portfolios as dictionaries
                    all_portfolio_dicts.extend(portfolios)

            log(f"Total portfolios collected: {len(all_portfolio_dicts)}")
            return all_portfolio_dicts

        except Exception as e:
            log(f"Error in MA Cross strategy execution: {e!s}", "error")
            import traceback

            log(traceback.format_exc(), "error")
            return []
