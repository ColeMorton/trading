"""
Stop Loss Configuration Module.

This module provides a centralized configuration system for stop loss settings,
allowing for consistent application of stop loss rules across the system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class StopLossMode(Enum):
    """Enumeration of stop loss modes."""

    DISABLED = "disabled"  # No stop loss applied
    OPTIONAL = "optional"  # Only apply if explicitly defined in strategy
    REQUIRED = "required"  # Always apply (use default if not defined)


@dataclass
class StopLossConfig:
    """Configuration for stop loss application."""

    mode: StopLossMode = StopLossMode.OPTIONAL
    default_value: float = 0.05  # Default 5% stop loss
    use_candle_close: bool = True  # Use candle close for stop loss calculation
    reset_after_trigger: bool = True  # Reset position after stop loss trigger


def get_stop_loss_value(
    strategy_config: Dict[str, Any], global_config: Dict[str, Any]
) -> Optional[float]:
    """Get the stop loss value for a strategy, respecting the global configuration.

    Args:
        strategy_config: Strategy-specific configuration
        global_config: Global system configuration

    Returns:
        Optional[float]: Stop loss value or None if stop loss is disabled
    """
    # Extract stop loss configuration
    stop_loss_config = _extract_stop_loss_config(global_config)

    # Check if stop loss is disabled globally
    if stop_loss_config.mode == StopLossMode.DISABLED:
        return None

    # Get strategy-specific stop loss if available
    strategy_stop_loss = strategy_config.get("STOP_LOSS")

    # Apply rules based on mode
    if stop_loss_config.mode == StopLossMode.OPTIONAL:
        # Only use stop loss if explicitly defined in strategy
        return strategy_stop_loss
    else:  # REQUIRED mode
        # Use strategy-specific value if available, otherwise use default
        return (
            strategy_stop_loss
            if strategy_stop_loss is not None
            else stop_loss_config.default_value
        )


def _extract_stop_loss_config(config: Dict[str, Any]) -> StopLossConfig:
    """Extract stop loss configuration from global config.

    Args:
        config: Global configuration dictionary

    Returns:
        StopLossConfig: Stop loss configuration object
    """
    stop_loss_config = StopLossConfig()

    # Extract mode
    if "STOP_LOSS_MODE" in config:
        mode_str = config["STOP_LOSS_MODE"]
        try:
            stop_loss_config.mode = StopLossMode(mode_str)
        except ValueError:
            # Invalid mode, keep default
            pass

    # Extract default value
    if "DEFAULT_STOP_LOSS" in config:
        default_value = config["DEFAULT_STOP_LOSS"]
        if isinstance(default_value, (int, float)) and 0 < default_value < 1:
            stop_loss_config.default_value = default_value

    # Extract candle close setting
    if "SL_CANDLE_CLOSE" in config:
        stop_loss_config.use_candle_close = bool(config["SL_CANDLE_CLOSE"])

    # Extract reset setting
    if "SL_RESET_AFTER_TRIGGER" in config:
        stop_loss_config.reset_after_trigger = bool(config["SL_RESET_AFTER_TRIGGER"])

    return stop_loss_config
