"""
Ticker Processor Module

This module handles the processing of individual tickers and coordinates
strategy execution for multiple tickers.
"""

from collections.abc import Callable
from typing import Any

from app.strategies.ma_cross.exceptions import (
    MACrossDataError,
    MACrossExecutionError,
    MACrossSyntheticTickerError,
)
from app.tools.error_context import error_context
from app.tools.strategy.signal_processing import process_ticker_portfolios


class TickerProcessor:
    """
    Manages ticker processing and strategy execution.

    This class encapsulates the logic for processing individual tickers
    and coordinating strategy execution across multiple tickers.
    """

    def __init__(self, log: Callable[[str, str], None]):
        """
        Initialize the ticker processor.

        Args:
            log: Logging function
        """
        self.log = log

    def execute_strategy(
        self,
        config: dict[str, Any],
        strategy_type: str,
        progress_update_fn: Any | None | None = None,
    ) -> list[dict[str, Any]]:
        """
        Execute a strategy for all configured tickers.

        Args:
            config: Configuration dictionary
            strategy_type: Type of strategy to execute (e.g., 'SMA', 'EMA')
            progress_tracker: Optional progress tracking object

        Returns:
            List of best portfolios from strategy execution

        Raises:
            MACrossExecutionError: If strategy execution fails
        """
        with error_context(
            f"Executing strategy {strategy_type}",
            self.log,
            {Exception: MACrossExecutionError},
            reraise=True,
        ):
            # Automatically choose optimal execution method based on ticker count
            tickers = config.get("TICKER", [])
            if isinstance(tickers, str):
                tickers = [tickers]

            # Process each ticker using unified signal processing
            all_portfolios = []
            # Store original ticker count and calculate global total for progress calculation
            original_ticker_count = len(tickers)
            # Each ticker should contribute an equal share of the global progress
            global_progress_per_ticker = config.get("_GLOBAL_PROGRESS_PER_TICKER")

            for ticker in tickers:
                self.log(f"Processing ticker: {ticker}")

                # Create ticker-specific config
                ticker_config = config.copy()
                ticker_config["TICKER"] = ticker
                # Preserve original ticker count and global progress allocation for accurate progress calculation
                ticker_config["_ORIGINAL_TICKER_COUNT"] = original_ticker_count
                if global_progress_per_ticker is not None:
                    ticker_config["_GLOBAL_PROGRESS_PER_TICKER"] = (
                        global_progress_per_ticker
                    )

                # Use unified signal processing that supports both MA and MACD
                portfolios_df = process_ticker_portfolios(
                    ticker,
                    ticker_config,
                    self.log,
                    progress_update_fn=progress_update_fn,
                )

                if portfolios_df is not None and len(portfolios_df) > 0:
                    # Convert to dictionaries and add to collection
                    ticker_portfolios = portfolios_df.to_dicts()
                    all_portfolios.extend(ticker_portfolios)
                    self.log(
                        f"Processed {len(ticker_portfolios)} portfolios for {ticker}",
                    )
                else:
                    self.log(f"No portfolios generated for {ticker}", "warning")

            return all_portfolios

    def process_ticker(
        self,
        ticker: str,
        config: dict[str, Any],
        progress_tracker: Any | None | None = None,
    ) -> dict[str, Any] | None:
        """
        Process a single ticker through the portfolio analysis pipeline.

        Args:
            ticker: Ticker symbol to process
            config: Configuration dictionary
            progress_tracker: Optional progress tracking object

        Returns:
            Best portfolio for the ticker if found, None otherwise

        Raises:
            MACrossDataError: If ticker data processing fails
        """
        with error_context(
            f"Processing ticker {ticker}",
            self.log,
            {Exception: MACrossDataError},
            reraise=True,
        ):
            # Create ticker-specific config
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker

            # Use unified signal processing
            portfolios_df = process_ticker_portfolios(ticker, ticker_config, self.log)

            if portfolios_df is not None and len(portfolios_df) > 0:
                # Return the first (best) portfolio as a dictionary
                return portfolios_df.to_dicts()[0]
            return None

    def _format_ticker(self, ticker: str, use_synthetic: bool) -> str:
        """
        Format ticker symbol consistently.

        Args:
            ticker: Raw ticker symbol
            use_synthetic: Whether synthetic ticker formatting is enabled

        Returns:
            Formatted ticker symbol
        """
        if use_synthetic and isinstance(ticker, str) and "/" in ticker:
            return ticker.replace("/", "_")
        return ticker

    def _extract_synthetic_components(
        self,
        ticker: str,
        config: dict[str, Any],
    ) -> None:
        """
        Extract components from synthetic ticker and update config.

        Args:
            ticker: Synthetic ticker symbol (e.g., 'BTC_USD')
            config: Configuration dictionary to update

        Raises:
            MACrossSyntheticTickerError: If synthetic ticker parsing fails
        """
        with error_context(
            f"Extracting synthetic ticker components from {ticker}",
            self.log,
            {
                ValueError: MACrossSyntheticTickerError,
                Exception: MACrossSyntheticTickerError,
            },
            reraise=True,
        ):
            if "_" in ticker:
                parts = ticker.split("_")
                if len(parts) >= 2 and parts[0] and parts[1]:
                    config["TICKER_1"] = parts[0]
                    if "TICKER_2" not in config:
                        config["TICKER_2"] = parts[1]
                    self.log(
                        f"Extracted ticker components: {config['TICKER_1']} and {config['TICKER_2']}",
                        "info",
                    )
                else:
                    msg = f"Invalid synthetic ticker format: {ticker}"
                    raise ValueError(msg)
            else:
                msg = f"Not a synthetic ticker: {ticker}"
                raise ValueError(msg)
