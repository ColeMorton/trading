"""Synthetic ticker processing utilities.

This module provides utilities for processing synthetic tickers,
which are combinations of two individual tickers.
"""

from typing import Any, Dict, Tuple

from app.tools.exceptions import SyntheticTickerError


def process_synthetic_ticker(ticker: str) -> Tuple[str, str]:
    """Process a synthetic ticker string into its components.

    Args:
        ticker: Synthetic ticker string (e.g., "BTC_MSTR")

    Returns:
        Tuple of (ticker1, ticker2)

    Raises:
        SyntheticTickerError: If the ticker format is invalid
    """
    if "_" not in ticker:
        raise SyntheticTickerError(f"Not a synthetic ticker: {ticker}")

    ticker_parts = ticker.split("_")
    if len(ticker_parts) != 2:
        raise SyntheticTickerError(f"Invalid synthetic ticker format: {ticker}")

    return ticker_parts[0], ticker_parts[1]


def create_synthetic_ticker(ticker1: str, ticker2: str) -> str:
    """Create a synthetic ticker from two component tickers.

    Args:
        ticker1: First ticker
        ticker2: Second ticker

    Returns:
        Synthetic ticker string
    """
    return f"{ticker1}_{ticker2}"


def process_synthetic_config(config: Dict[str, Any], log_func=None) -> Dict[str, Any]:
    """Process configuration for synthetic ticker handling.

    Args:
        config: Configuration dictionary
        log_func: Optional logging function

    Returns:
        Updated configuration dictionary

    Raises:
        SyntheticTickerError: If there's an issue with synthetic ticker processing
    """
    if not config.get("USE_SYNTHETIC"):
        if log_func and "TICKER" in config:
            log_func(f"Processing strategy for ticker: {config['TICKER']}")
        return config.copy()

    result = config.copy()

    # Check if this is a global config without a specific ticker
    # (e.g., in app/concurrency/review.py main config)
    if "TICKER" not in config:
        if log_func:
            log_func("Processing global synthetic ticker configuration")

        # For global configs, we just need to ensure TICKER_1 and TICKER_2 are present
        if "TICKER_1" not in config or "TICKER_2" not in config:
            raise SyntheticTickerError(
                "TICKER_1 and TICKER_2 must be specified when USE_SYNTHETIC is True"
            )

        # No need to modify the config further for global configs
        return result

    # Process configs with specific tickers
    if isinstance(config["TICKER"], list):
        # Process multiple synthetic tickers
        if "TICKER_2" not in config:
            raise SyntheticTickerError(
                "TICKER_2 must be specified when USE_SYNTHETIC is True"
            )

        synthetic_tickers = [
            create_synthetic_ticker(ticker, config["TICKER_2"])
            for ticker in config["TICKER"]
        ]

        if log_func:
            log_func(f"Processing strategies for synthetic pairs: {synthetic_tickers}")

        result["TICKER"] = synthetic_tickers
        result["ORIGINAL_TICKERS"] = (
            config["TICKER"].copy()
            if isinstance(config["TICKER"], list)
            else [config["TICKER"]]
        )

    elif isinstance(config["TICKER"], str):
        # Process single synthetic ticker
        if "TICKER_2" not in config:
            raise SyntheticTickerError(
                "TICKER_2 must be specified when USE_SYNTHETIC is True"
            )

        synthetic_ticker = create_synthetic_ticker(config["TICKER"], config["TICKER_2"])

        if log_func:
            log_func(f"Processing strategy for synthetic pair: {synthetic_ticker}")

        result["TICKER"] = synthetic_ticker
        result["ORIGINAL_TICKERS"] = [config["TICKER"]]

    else:
        raise SyntheticTickerError(
            "TICKER must be a string or a list when USE_SYNTHETIC is True"
        )

    return result


def detect_synthetic_ticker(ticker: str) -> bool:
    """Detect if a ticker is synthetic.

    Args:
        ticker: Ticker string

    Returns:
        True if the ticker is synthetic, False otherwise
    """
    return "_" in ticker
