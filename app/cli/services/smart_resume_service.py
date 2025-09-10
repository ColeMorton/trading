"""
Smart Resume Service

This module provides intelligent resume functionality for strategy execution,
detecting completed analyses and filtering out work that doesn't need to be redone.
"""

import os
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from app.tools.market_hours import (
    MarketType,
    TradingHours,
    detect_market_type,
    get_trading_hours,
)
from app.tools.project_utils import get_project_root


class ResumeAnalysis:
    """Results of smart resume analysis."""

    def __init__(self):
        self.completed_combinations: Set[Tuple[str, str]] = set()  # (ticker, strategy)
        self.stale_combinations: Set[Tuple[str, str]] = set()
        self.missing_combinations: Set[Tuple[str, str]] = set()
        self.total_combinations: int = 0
        self.needs_processing: bool = True

    def add_completed(self, ticker: str, strategy: str):
        """Mark a ticker+strategy combination as completed."""
        self.completed_combinations.add((ticker, strategy))

    def add_stale(self, ticker: str, strategy: str):
        """Mark a ticker+strategy combination as stale."""
        self.stale_combinations.add((ticker, strategy))

    def add_missing(self, ticker: str, strategy: str):
        """Mark a ticker+strategy combination as missing."""
        self.missing_combinations.add((ticker, strategy))

    def get_remaining_combinations(self) -> Set[Tuple[str, str]]:
        """Get combinations that need processing."""
        return self.stale_combinations | self.missing_combinations

    def is_complete(self) -> bool:
        """Check if all combinations are completed and fresh."""
        return len(self.get_remaining_combinations()) == 0


class SmartResumeService:
    """
    Service for intelligent strategy execution resume functionality.

    Analyzes existing output files to determine which ticker+strategy combinations
    have already been completed and are still fresh based on market trading sessions.
    """

    def __init__(self, log: Optional[Callable] = None):
        """
        Initialize smart resume service.

        Args:
            log: Optional logging function
        """
        self.log = log or self._default_log
        self.project_root = Path(get_project_root())

        # Output directories that must all exist for a combination to be "complete"
        self.required_directories = [
            "portfolios",
            "portfolios_filtered",
            "portfolios_metrics",
            "portfolios_best",
        ]

    def _default_log(self, message: str, level: str = "info"):
        """Default logging function."""
        pass

    def analyze_resume_status(self, config: Dict[str, Any]) -> ResumeAnalysis:
        """
        Analyze which ticker+strategy combinations need processing.

        Args:
            config: Strategy configuration dictionary

        Returns:
            ResumeAnalysis: Analysis results with completed/missing combinations
        """
        analysis = ResumeAnalysis()

        # Extract ticker and strategy combinations from config
        tickers = self._extract_tickers_from_config(config)
        strategies = self._extract_strategies_from_config(config)

        analysis.total_combinations = len(tickers) * len(strategies)

        self.log(
            f"Analyzing resume status for {len(tickers)} tickers × {len(strategies)} strategies = {analysis.total_combinations} combinations",
            "info",
        )

        # Check each combination
        for ticker in tickers:
            market_type = detect_market_type(ticker)

            for strategy in strategies:
                if self._is_combination_complete_and_fresh(
                    ticker, strategy, config, market_type
                ):
                    analysis.add_completed(ticker, strategy)
                    self.log(f"✓ {ticker} {strategy} - complete and fresh", "debug")
                elif self._is_combination_stale(ticker, strategy, config, market_type):
                    analysis.add_stale(ticker, strategy)
                    self.log(f"⚠ {ticker} {strategy} - exists but stale", "debug")
                else:
                    analysis.add_missing(ticker, strategy)
                    self.log(f"✗ {ticker} {strategy} - missing or incomplete", "debug")

        # Determine if any processing is needed
        analysis.needs_processing = len(analysis.get_remaining_combinations()) > 0

        return analysis

    def filter_config_for_resume(
        self, config: Dict[str, Any], analysis: ResumeAnalysis
    ) -> Dict[str, Any]:
        """
        Filter configuration to only include combinations that need processing.

        Args:
            config: Original strategy configuration
            analysis: Resume analysis results

        Returns:
            Modified configuration with only remaining work
        """
        if analysis.is_complete():
            # Nothing to process - return config indicating skip
            filtered_config = config.copy()
            filtered_config["_RESUME_SKIP_ALL"] = True
            return filtered_config

        remaining_combinations = analysis.get_remaining_combinations()

        # Extract remaining tickers and strategies
        remaining_tickers = set(combo[0] for combo in remaining_combinations)
        remaining_strategies = set(combo[1] for combo in remaining_combinations)

        # Filter config to only include remaining work
        filtered_config = config.copy()

        # Update ticker list
        if "TICKER" in filtered_config:
            original_tickers = filtered_config["TICKER"]
            if isinstance(original_tickers, str):
                original_tickers = [original_tickers]
            filtered_config["TICKER"] = [
                t for t in original_tickers if t in remaining_tickers
            ]

        # Update strategy types
        if "STRATEGY_TYPES" in filtered_config:
            filtered_config["STRATEGY_TYPES"] = [
                s
                for s in filtered_config["STRATEGY_TYPES"]
                if s in remaining_strategies
            ]

        return filtered_config

    def _extract_tickers_from_config(self, config: Dict[str, Any]) -> List[str]:
        """Extract ticker list from configuration."""
        # Handle synthetic mode
        if config.get("USE_SYNTHETIC", False):
            ticker_1 = config.get("TICKER_1", "")
            ticker_2 = config.get("TICKER_2", "")
            if ticker_1 and ticker_2:
                return [f"{ticker_1}_{ticker_2}"]
            return []

        # Normal mode
        tickers = config.get("TICKER", [])
        if isinstance(tickers, str):
            return [tickers]
        return tickers if tickers else []

    def _extract_strategies_from_config(self, config: Dict[str, Any]) -> List[str]:
        """Extract strategy list from configuration."""
        strategies = config.get("STRATEGY_TYPES", [])
        if not strategies:
            # Fallback to single strategy type
            single_strategy = config.get("STRATEGY_TYPE")
            if single_strategy:
                return [single_strategy]
        return strategies

    def _is_combination_complete_and_fresh(
        self,
        ticker: str,
        strategy: str,
        config: Dict[str, Any],
        market_type: MarketType,
    ) -> bool:
        """
        Check if a ticker+strategy combination is complete and fresh.

        Args:
            ticker: Ticker symbol
            strategy: Strategy type
            config: Configuration dictionary
            market_type: Market type for freshness validation

        Returns:
            True if combination is complete and fresh
        """
        # Check if all required files exist and are non-empty
        if not self._all_files_exist_and_non_empty(ticker, strategy, config):
            return False

        # Check if files are fresh based on market hours
        return self._are_files_fresh(ticker, strategy, config, market_type)

    def _is_combination_stale(
        self,
        ticker: str,
        strategy: str,
        config: Dict[str, Any],
        market_type: MarketType,
    ) -> bool:
        """
        Check if a ticker+strategy combination exists but is stale.

        Args:
            ticker: Ticker symbol
            strategy: Strategy type
            config: Configuration dictionary
            market_type: Market type for freshness validation

        Returns:
            True if combination exists but is stale
        """
        # Must have at least some files existing
        if not self._any_files_exist(ticker, strategy, config):
            return False

        # But files must be stale
        return not self._are_files_fresh(ticker, strategy, config, market_type)

    def _all_files_exist_and_non_empty(
        self, ticker: str, strategy: str, config: Dict[str, Any]
    ) -> bool:
        """Check if all required output files exist and are non-empty."""
        expected_files = self._get_expected_file_paths(ticker, strategy, config)

        for file_path in expected_files:
            if not os.path.exists(file_path):
                return False

            # Check if file is non-empty
            try:
                if os.path.getsize(file_path) == 0:
                    return False
            except OSError:
                return False

        return True

    def _any_files_exist(
        self, ticker: str, strategy: str, config: Dict[str, Any]
    ) -> bool:
        """Check if any output files exist for this combination."""
        expected_files = self._get_expected_file_paths(ticker, strategy, config)

        return any(os.path.exists(file_path) for file_path in expected_files)

    def _are_files_fresh(
        self,
        ticker: str,
        strategy: str,
        config: Dict[str, Any],
        market_type: MarketType,
    ) -> bool:
        """
        Check if files are fresh based on market trading sessions.

        Args:
            ticker: Ticker symbol
            strategy: Strategy type
            config: Configuration dictionary
            market_type: Market type for session determination

        Returns:
            True if files are fresh enough for the market type
        """
        expected_files = self._get_expected_file_paths(ticker, strategy, config)

        # Get the oldest file modification time
        oldest_mtime = None
        for file_path in expected_files:
            if os.path.exists(file_path):
                try:
                    mtime = os.path.getmtime(file_path)
                    if oldest_mtime is None or mtime < oldest_mtime:
                        oldest_mtime = mtime
                except OSError:
                    return False

        if oldest_mtime is None:
            return False

        file_datetime = datetime.fromtimestamp(oldest_mtime)
        current_time = datetime.now()

        if market_type == MarketType.CRYPTO:
            # Crypto: files should be from today (last 24 hours)
            return (current_time - file_datetime).total_seconds() < 86400  # 24 hours
        else:
            # Stock market: files should be from after last market close (4:00 PM ET)
            return self._is_after_last_market_close(file_datetime, current_time)

    def _is_after_last_market_close(
        self, file_datetime: datetime, current_time: datetime
    ) -> bool:
        """Check if file was created after the last market close."""
        trading_hours = get_trading_hours(MarketType.US_STOCK)

        # Convert times to market timezone
        market_tz = trading_hours.timezone
        file_market_time = file_datetime.astimezone(market_tz)
        current_market_time = current_time.astimezone(market_tz)

        # Find the last market close
        if current_market_time.weekday() in trading_hours.trading_days:
            # Today is a trading day
            todays_close = current_market_time.replace(
                hour=trading_hours.end_time.hour,
                minute=trading_hours.end_time.minute,
                second=0,
                microsecond=0,
            )

            if current_market_time.time() > trading_hours.end_time:
                # Market has closed today - use today's close
                last_close = todays_close
            else:
                # Market hasn't closed yet - use previous trading day close
                last_close = self._get_previous_trading_day_close(
                    todays_close, trading_hours
                )
        else:
            # Today is not a trading day - find previous trading day close
            last_close = self._get_previous_trading_day_close(
                current_market_time, trading_hours
            )

        return file_market_time >= last_close

    def _get_previous_trading_day_close(
        self, current_time: datetime, trading_hours: TradingHours
    ) -> datetime:
        """Get the close time of the previous trading day."""
        # Go back day by day until we find a trading day
        check_date = current_time.date()

        for days_back in range(1, 8):  # Check up to a week back
            check_date = current_time.date() - timedelta(days=days_back)
            check_datetime = datetime.combine(check_date, time.min).replace(
                tzinfo=trading_hours.timezone
            )

            if check_datetime.weekday() in trading_hours.trading_days:
                return check_datetime.replace(
                    hour=trading_hours.end_time.hour,
                    minute=trading_hours.end_time.minute,
                    second=0,
                    microsecond=0,
                )

        # Fallback - use a week ago
        week_ago = current_time - timedelta(days=7)
        return week_ago.replace(
            hour=trading_hours.end_time.hour,
            minute=trading_hours.end_time.minute,
            second=0,
            microsecond=0,
        )

    def _get_expected_file_paths(
        self, ticker: str, strategy: str, config: Dict[str, Any]
    ) -> List[str]:
        """
        Generate expected file paths for a ticker+strategy combination.

        Reuses existing export path and filename logic.
        """
        expected_paths = []

        # Create a temporary config for this specific combination
        temp_config = config.copy()
        temp_config["TICKER"] = ticker
        temp_config["STRATEGY_TYPE"] = strategy
        temp_config["STRATEGY_TYPES"] = [strategy]
        temp_config["USE_MA"] = True  # Ensure strategy suffix is included

        # Generate paths for each required directory
        for directory in self.required_directories:
            file_path = self._generate_file_path(temp_config, directory)
            expected_paths.append(file_path)

        return expected_paths

    def _generate_file_path(self, config: Dict[str, Any], export_type: str) -> str:
        """
        Generate file path using existing export logic.

        Reuses logic from export_csv.py for consistency.
        """
        # Import here to avoid circular imports
        from app.tools.export_csv import _get_export_path, _get_filename

        # For portfolios_best and portfolios_metrics, they might be in date subdirectories
        if export_type in ["portfolios_best", "portfolios_metrics"]:
            feature1 = export_type
            feature2 = ""
        else:
            feature1 = export_type
            feature2 = ""

        # Generate export path using existing logic
        export_path = _get_export_path(feature1, config, feature2)

        # Generate filename using existing logic
        filename = _get_filename(config, feature1, feature2)

        return os.path.join(export_path, filename)

    def _extract_ticker_from_filename(self, filename: str) -> str:
        """
        Extract ticker symbol from portfolio filename.

        Reuses logic from PortfolioOrchestrator for consistency.
        """
        # Remove .csv extension first if present
        filename = filename.replace(".csv", "")

        # Extract ticker - everything before the first underscore
        ticker = filename.split("_")[0]

        return ticker

    def get_resume_summary(self, analysis: ResumeAnalysis) -> str:
        """Generate human-readable resume summary."""
        completed_count = len(analysis.completed_combinations)
        stale_count = len(analysis.stale_combinations)
        missing_count = len(analysis.missing_combinations)

        summary_parts = []

        if completed_count > 0:
            summary_parts.append(f"✓ {completed_count} combinations complete and fresh")

        if stale_count > 0:
            summary_parts.append(
                f"⚠ {stale_count} combinations stale (will regenerate)"
            )

        if missing_count > 0:
            summary_parts.append(
                f"✗ {missing_count} combinations missing (will generate)"
            )

        total_to_process = stale_count + missing_count

        if total_to_process == 0:
            summary_parts.append("🎉 All analysis is complete and up-to-date!")
        else:
            summary_parts.append(f"🚀 Processing {total_to_process} combinations")

        return " | ".join(summary_parts)
