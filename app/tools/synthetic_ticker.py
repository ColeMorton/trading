"""Synthetic ticker processing utilities.

This module provides utilities for processing synthetic tickers,
which are combinations of two individual tickers.
"""

from typing import Any

from app.tools.exceptions import SyntheticTickerError


def process_synthetic_ticker(ticker: str) -> tuple[str, str]:
    """Process a synthetic ticker string into its components.

    Args:
        ticker: Synthetic ticker string (e.g., "BTC_MSTR")

    Returns:
        Tuple of (ticker1, ticker2)

    Raises:
        SyntheticTickerError: If the ticker format is invalid
    """
    if "_" not in ticker:
        msg = f"Not a synthetic ticker: {ticker}"
        raise SyntheticTickerError(msg)

    ticker_parts = ticker.split("_")
    if len(ticker_parts) != 2:
        msg = f"Invalid synthetic ticker format: {ticker}"
        raise SyntheticTickerError(msg)

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


def process_synthetic_config(config: dict[str, Any], log_func=None) -> dict[str, Any]:
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

    # Check if synthetic processing has already been done
    if config.get("SYNTHETIC_PROCESSED"):
        if log_func:
            log_func("Synthetic ticker already processed, skipping double processing")
        return config.copy()

    # Additional check: if TICKER is already a synthetic ticker format and contains TICKER_2,
    # this might be a second processing attempt
    if "TICKER" in config and isinstance(config["TICKER"], str):
        ticker = config["TICKER"]
        ticker_2 = config.get("TICKER_2", "")
        if "_" in ticker and ticker_2 and ticker.endswith(f"_{ticker_2}"):
            if log_func:
                log_func(
                    f"TICKER {ticker} appears to already contain {ticker_2}, likely already processed. Skipping to prevent double processing.",
                )
            # Mark as processed and return as-is
            result = config.copy()
            result["SYNTHETIC_PROCESSED"] = True
            return result

    result = config.copy()

    # Check if this is a config without a specific TICKER field
    # In this case, create the synthetic ticker from TICKER_1 and TICKER_2
    if "TICKER" not in config:
        if log_func:
            log_func(
                "Processing synthetic ticker configuration from TICKER_1 and TICKER_2",
            )

        # Ensure TICKER_1 and TICKER_2 are present
        if "TICKER_1" not in config or "TICKER_2" not in config:
            msg = "TICKER_1 and TICKER_2 must be specified when USE_SYNTHETIC is True"
            raise SyntheticTickerError(
                msg,
            )

        # Create synthetic ticker from TICKER_1 and TICKER_2
        synthetic_ticker = create_synthetic_ticker(
            config["TICKER_1"],
            config["TICKER_2"],
        )

        if log_func:
            log_func(f"Created synthetic ticker: {synthetic_ticker}")

        result["TICKER"] = synthetic_ticker
        result["ORIGINAL_TICKERS"] = [config["TICKER_1"]]

        # Mark as processed to prevent double processing, but keep USE_SYNTHETIC for data download
        result["SYNTHETIC_PROCESSED"] = True

        return result

    # Process configs with specific tickers
    if isinstance(config["TICKER"], list):
        # Process multiple synthetic tickers
        if "TICKER_2" not in config:
            msg = "TICKER_2 must be specified when USE_SYNTHETIC is True"
            raise SyntheticTickerError(
                msg,
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

        # Mark as processed to prevent double processing, but keep USE_SYNTHETIC for data download
        result["SYNTHETIC_PROCESSED"] = True

    elif isinstance(config["TICKER"], str):
        # Process single synthetic ticker
        if "TICKER_2" not in config:
            msg = "TICKER_2 must be specified when USE_SYNTHETIC is True"
            raise SyntheticTickerError(
                msg,
            )

        # Create synthetic ticker from the provided ticker and TICKER_2
        ticker = config["TICKER"]
        synthetic_ticker = create_synthetic_ticker(ticker, config["TICKER_2"])

        if log_func:
            log_func(f"Processing strategy for synthetic pair: {synthetic_ticker}")

        result["TICKER"] = synthetic_ticker
        result["ORIGINAL_TICKERS"] = [config["TICKER"]]

        # Mark as processed to prevent double processing, but keep USE_SYNTHETIC for data download
        result["SYNTHETIC_PROCESSED"] = True

    else:
        msg = "TICKER must be a string or a list when USE_SYNTHETIC is True"
        raise SyntheticTickerError(
            msg,
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
