"""
Ticker Processor Module

This module handles the processing of individual tickers and coordinates
strategy execution for multiple tickers.
"""

from typing import Any, Callable, Dict, List, Optional

from app.strategies.ma_cross.exceptions import (
    MACrossDataError,
    MACrossExecutionError,
    MACrossSyntheticTickerError,
)
from app.strategies.ma_cross.tools.strategy_execution import (
    execute_strategy,
    process_single_ticker,
)
from app.tools.error_context import error_context


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
        config: Dict[str, Any],
        strategy_type: str,
        progress_tracker: Optional[Any] | None = None,
    ) -> List[Dict[str, Any]]:
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
            return execute_strategy(config, strategy_type, self.log, progress_tracker)

    def process_ticker(
        self,
        ticker: str,
        config: Dict[str, Any],
        progress_tracker: Optional[Any] | None = None,
    ) -> Optional[Dict[str, Any]]:
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
            return process_single_ticker(ticker, config, self.log, progress_tracker)

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
        self, ticker: str, config: Dict[str, Any]
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
                    raise ValueError(f"Invalid synthetic ticker format: {ticker}")
            else:
                raise ValueError(f"Not a synthetic ticker: {ticker}")
