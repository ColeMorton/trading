"""Strategy ID utilities for concurrency analysis.

This module provides functions for generating and parsing standardized strategy IDs
used throughout the concurrency analysis system.
"""

import sys
from pathlib import Path
from typing import Any


# Add the tools module to the path so we can import uuid_utils
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.tools.uuid_utils import (
    generate_strategy_id_from_config as _generate_strategy_id_from_config,
    is_valid_strategy_uuid as _is_valid_strategy_uuid,
    parse_strategy_uuid as _parse_strategy_uuid,
)


def generate_strategy_id(strategy_config: dict[str, Any]) -> str:
    """Generate a standardized strategy ID from a strategy configuration.

    Args:
        strategy_config (Dict[str, Any]): Strategy configuration dictionary

    Returns:
        str: Standardized strategy ID

    Raises:
        ValueError: If required fields are missing from the strategy configuration
    """
    # Use centralized UUID generation
    return _generate_strategy_id_from_config(strategy_config)


def parse_strategy_id(strategy_id: str) -> dict[str, Any]:
    """Parse a strategy ID into its component parts.

    Args:
        strategy_id (str): Strategy ID in the format:
                          - SMA/EMA: {ticker}_{strategy_type}_{fast_period}_{slow_period}
                          - MACD/others: {ticker}_{strategy_type}_{fast_period}_{slow_period}_{signal_period}

    Returns:
        Dict[str, Any]: Dictionary containing the parsed components

    Raises:
        ValueError: If the strategy ID format is invalid
    """
    # Use centralized UUID parsing
    return _parse_strategy_uuid(strategy_id)


def is_valid_strategy_id(strategy_id: str) -> bool:
    """Check if a string is a valid strategy ID.

    Args:
        strategy_id (str): String to validate

    Returns:
        bool: True if the string is a valid strategy ID, False otherwise
    """
    # Use centralized UUID validation
    return _is_valid_strategy_uuid(strategy_id)
