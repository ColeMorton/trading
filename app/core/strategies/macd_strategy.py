"""
MACD Strategy Implementation

This module implements the MACD strategy using the Strategy Pattern.
"""

from typing import Any, Dict, List, Optional

from app.core.interfaces.strategy import StrategyInterface
from app.tools.project_utils import get_project_root


class MACDStrategy(StrategyInterface):
    """MACD strategy implementation using Strategy Pattern."""

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "MACD"

    def validate_parameters(self, config: Dict[str, Any]) -> bool:
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

            # Validate that long window is larger than short window at minimum
            if long_start <= short_start:
                return False

            # Validate step size is reasonable
            if step > min(
                short_end - short_start,
                long_end - long_start,
                signal_end - signal_start,
            ):
                return False

            return True

        except Exception:
            return False

    def get_parameter_ranges(self) -> Dict[str, Any]:
        """Get MACD strategy parameter ranges and defaults."""
        return {
            "SHORT_WINDOW_START": {"min": 2, "max": 50, "default": 2},
            "SHORT_WINDOW_END": {"min": 3, "max": 100, "default": 18},
            "LONG_WINDOW_START": {"min": 4, "max": 100, "default": 4},
            "LONG_WINDOW_END": {"min": 5, "max": 200, "default": 36},
            "SIGNAL_WINDOW_START": {"min": 2, "max": 50, "default": 2},
            "SIGNAL_WINDOW_END": {"min": 3, "max": 100, "default": 18},
            "STEP": {"min": 1, "max": 10, "default": 1},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
            "USE_HOURLY": {"type": "boolean", "default": False},
            "USE_YEARS": {"type": "boolean", "default": False},
            "YEARS": {"min": 1, "max": 50, "default": 15},
        }

    def execute(self, config: Dict[str, Any], log: Any) -> List[Dict[str, Any]]:
        """Execute MACD strategy analysis."""
        try:
            # Import the MACD strategy execution functions
            from app.strategies.macd_next import run

            # Ensure BASE_DIR is set in config
            if "BASE_DIR" not in config:
                config["BASE_DIR"] = get_project_root()

            log("Starting MACD strategy execution")

            # Convert API config format to MACD Next config format
            macd_config = self._convert_config_to_macd_format(config)

            log(f"Converted config: {macd_config}")

            # Execute MACD strategy using the existing MACD Next implementation
            portfolios = run(macd_config)

            log(
                f"MACD strategy returned {len(portfolios) if portfolios else 0} portfolios"
            )

            if portfolios:
                log(f"First portfolio keys: {list(portfolios[0].keys())}")
                return portfolios
            else:
                return []

        except Exception as e:
            log(f"Error in MACD strategy execution: {str(e)}", "error")
            import traceback

            log(traceback.format_exc(), "error")
            return []

    def _convert_config_to_macd_format(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert API config format to MACD Next config format."""
        # Get ticker(s)
        ticker = config.get("TICKER", "BTC-USD")
        if isinstance(ticker, list):
            ticker = ticker[0]  # MACD Next handles single ticker

        # Convert to MACD Next format
        macd_config = {
            "TICKER": ticker,
            "TIMEFRAME": "D" if not config.get("USE_HOURLY", False) else "H",
            "TYPE": "MACD",
            "DIRECTION": config.get("DIRECTION", "Long"),
            "SHORT_WINDOW_START": config.get("SHORT_WINDOW_START", 2),
            "SHORT_WINDOW_END": config.get("SHORT_WINDOW_END", 18),
            "LONG_WINDOW_START": config.get("LONG_WINDOW_START", 4),
            "LONG_WINDOW_END": config.get("LONG_WINDOW_END", 36),
            "SIGNAL_WINDOW_START": config.get("SIGNAL_WINDOW_START", 2),
            "SIGNAL_WINDOW_END": config.get("SIGNAL_WINDOW_END", 18),
            "STEP": config.get("STEP", 1),
            "USE_CURRENT": config.get("USE_CURRENT", True),
            "USE_YEARS": config.get("USE_YEARS", False),
            "YEARS": float(config.get("YEARS", 15)),
            "EXPORT_RESULTS": True,
            "FILTER_PORTFOLIOS": True,
            "SELECT_BEST": True,
        }

        return macd_config
