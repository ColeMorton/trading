"""
Portfolio Loader Compatibility Module

This module provides backward compatibility functions for the legacy portfolio loader.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.tools.portfolio.loader import load_portfolio_from_csv, load_portfolio_from_json
from app.tools.portfolio.types import StrategyConfig


def load_portfolio_from_path(
    file_path: str,
    log: Callable[[str, str], None],
    config: dict[str, Any],
) -> list[StrategyConfig]:
    """
    Compatibility function that mimics the behavior of the legacy load_portfolio function.

    Args:
        file_path: Path to the portfolio file
        log: Logging function for status updates
        config: Configuration dictionary

    Returns:
        List of strategy configurations
    """
    path = Path(file_path)
    if not path.exists():
        log(f"Portfolio file not found: {path}", "error")
        msg = f"Portfolio file not found: {path}"
        raise FileNotFoundError(msg)

    extension = path.suffix.lower()
    if extension == ".json":
        return load_portfolio_from_json(path, log, config)
    if extension == ".csv":
        return load_portfolio_from_csv(path, log, config)
    error_msg = f"Unsupported file type: {extension}. Must be .json or .csv"
    log(error_msg, "error")
    raise ValueError(error_msg)
