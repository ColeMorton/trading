"""
MACD Strategy Implementation

This module implements the MACD strategy using the Strategy Pattern.
"""

from typing import Any

from app.core.interfaces.strategy import StrategyInterface
from app.tools.project_utils import get_project_root


class MACDStrategy(StrategyInterface):
    """MACD strategy implementation using Strategy Pattern."""

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "MACD"

    def validate_parameters(self, config: dict[str, Any]) -> bool:
        """Validate MACD strategy parameters."""
        try:
            # Check required parameters
            if "TICKER" not in config:
                return False

            # Validate MACD window parameters
            short_start = config.get("SHORT_WINDOW_START", 2)
            short_end = config.get("SHORT_WINDOW_END", 18)
            long_start = config.get("LONG_WINDOW_START", 4)
            long_end = config.get("LONG_WINDOW_END", 36)
            signal_start = config.get("SIGNAL_WINDOW_START", 2)
            signal_end = config.get("SIGNAL_WINDOW_END", 18)
            step = config.get("STEP", 1)

            # Validate ranges
            if not all(
                isinstance(x, int) and x > 0
                for x in [
                    short_start,
                    short_end,
                    long_start,
                    long_end,
                    signal_start,
                    signal_end,
                    step,
                ]
            ):
                return False

            # Validate window relationships
            if (
                short_start >= short_end
                or long_start >= long_end
                or signal_start >= signal_end
            ):
                return False

            # Validate that slow period is larger than fast period at minimum
            if long_start <= short_start:
                return False

            # Validate step size is reasonable
            return not step > min(
                short_end - short_start,
                long_end - long_start,
                signal_end - signal_start,
            )

        except Exception:
            return False

    def get_parameter_ranges(self) -> dict[str, Any]:
        """Get MACD strategy parameter validation ranges (no defaults)."""
        return {
            "SHORT_WINDOW_START": {"min": 1, "max": 50},
            "SHORT_WINDOW_END": {"min": 1, "max": 50},
            "LONG_WINDOW_START": {"min": 1, "max": 100},
            "LONG_WINDOW_END": {"min": 1, "max": 100},
            "SIGNAL_WINDOW_START": {"min": 1, "max": 50},
            "SIGNAL_WINDOW_END": {"min": 1, "max": 50},
            "STEP": {"min": 1, "max": 10},
            "DIRECTION": {"options": ["Long", "Short"]},
            "USE_HOURLY": {"type": "boolean"},
            "USE_YEARS": {"type": "boolean"},
            "YEARS": {"min": 1, "max": 50},
        }

    def execute(self, config: dict[str, Any], log: Any) -> list[dict[str, Any]]:
        """Execute MACD strategy analysis."""
        try:
            # Import the MACD strategy execution functions
            from app.strategies.macd import run

            # Ensure BASE_DIR is set in config
            if "BASE_DIR" not in config:
                config["BASE_DIR"] = get_project_root()

            log("Starting MACD strategy execution")

            # Convert API config format to MACD config format
            macd_config = self._convert_config_to_macd_format(config)

            log(f"Converted config: {macd_config}")

            # Execute MACD strategy using the existing MACD implementation
            portfolios = run(macd_config)

            log(
                f"MACD strategy returned {len(portfolios) if portfolios else 0} portfolios"
            )

            if portfolios:
                log(f"First portfolio keys: {list(portfolios[0].keys())}")
                return portfolios
            return []

        except Exception as e:
            log(f"Error in MACD strategy execution: {e!s}", "error")
            import traceback

            log(traceback.format_exc(), "error")
            return []

    def _convert_config_to_macd_format(self, config: dict[str, Any]) -> dict[str, Any]:
        """Convert API config format to MACD Next config format."""
        # Get ticker(s) - required parameter
        ticker = config["TICKER"]  # Fail fast if missing
        if isinstance(ticker, list):
            ticker = ticker[0]  # MACD Next handles single ticker

        # Convert to MACD Next format - all parameters required from config
        macd_config = {
            "TICKER": ticker,
            "TIMEFRAME": "D" if not config["USE_HOURLY"] else "H",
            "TYPE": "MACD",
            "DIRECTION": config["DIRECTION"],
            "SHORT_WINDOW_START": config["SHORT_WINDOW_START"],
            "SHORT_WINDOW_END": config["SHORT_WINDOW_END"],
            "LONG_WINDOW_START": config["LONG_WINDOW_START"],
            "LONG_WINDOW_END": config["LONG_WINDOW_END"],
            "SIGNAL_WINDOW_START": config["SIGNAL_WINDOW_START"],
            "SIGNAL_WINDOW_END": config["SIGNAL_WINDOW_END"],
            "STEP": config["STEP"],
            "USE_CURRENT": config["USE_CURRENT"],
            "USE_YEARS": config["USE_YEARS"],
            "YEARS": float(config["YEARS"]),
            "EXPORT_RESULTS": True,
            "FILTER_PORTFOLIOS": True,
            "SELECT_BEST": True,
        }

        return macd_config
