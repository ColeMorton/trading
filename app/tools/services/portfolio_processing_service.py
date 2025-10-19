"""
Portfolio Processing Service

This module handles portfolio data processing, conversion, and metrics calculation.
It provides utilities for converting portfolio dictionaries to metrics and
processing portfolio data with proper validation.
"""

# API removed - creating local definitions
from dataclasses import dataclass
import glob
from typing import Any


@dataclass
class PortfolioMetrics:
    """Portfolio metrics."""

    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float


class PortfolioProcessor:
    """Basic portfolio processor."""

    def __init__(self):
        pass

    def process_portfolios(
        self, portfolios: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process portfolios."""
        # Basic processing logic
        return portfolios

    def calculate_metrics(self, portfolio: dict[str, Any]) -> PortfolioMetrics:
        """Calculate portfolio metrics."""
        # Basic metrics calculation
        return PortfolioMetrics(
            total_return=0.0, win_rate=0.0, sharpe_ratio=0.0, max_drawdown=0.0
        )


from app.core.interfaces import LoggingInterface


class PortfolioProcessingServiceError(Exception):
    """Exception raised by PortfolioProcessingService."""

    pass


class PortfolioProcessingService:
    """
    Handles portfolio data processing and conversion.

    This service is responsible for:
    - Converting portfolio dictionaries to PortfolioMetrics
    - Portfolio data validation and processing
    - Export path collection and management
    - Portfolio deduplication and filtering
    """

    def __init__(self, logger: LoggingInterface):
        """Initialize the portfolio processing service."""
        self.logger = logger
        self.portfolio_processor = PortfolioProcessor()

    def convert_portfolios_to_metrics(
        self, portfolio_dicts: list[dict[str, Any]], log
    ) -> list[PortfolioMetrics]:
        """
        Convert portfolio dictionaries to PortfolioMetrics objects.

        Args:
            portfolio_dicts: List of portfolio dictionaries
            log: Logging function

        Returns:
            List of PortfolioMetrics objects
        """
        return self.portfolio_processor.convert_portfolios_to_metrics(
            portfolio_dicts, log
        )

    def process_and_deduplicate_portfolios(
        self, all_portfolio_dicts: list[dict[str, Any]], log
    ) -> tuple[list[PortfolioMetrics], list[dict[str, Any]]]:
        """
        Process portfolios and return both metrics and deduplicated dictionaries.

        Args:
            all_portfolio_dicts: List of portfolio dictionaries
            log: Logging function

        Returns:
            Tuple of (portfolio_metrics, deduplicated_portfolios)
        """
        portfolio_metrics = []
        deduplicated_portfolios = []

        if all_portfolio_dicts:
            # Convert to PortfolioMetrics
            portfolio_metrics = self.convert_portfolios_to_metrics(
                all_portfolio_dicts, log
            )

            # Deduplicate portfolios for response
            seen_portfolios = set()
            for portfolio_dict in all_portfolio_dicts:
                # Create a key for deduplication based on core attributes
                dedup_key = self._create_deduplication_key(portfolio_dict)

                if dedup_key not in seen_portfolios:
                    seen_portfolios.add(dedup_key)
                    deduplicated_portfolios.append(portfolio_dict)

            log(
                f"Processed {len(all_portfolio_dicts)} portfolios into {len(portfolio_metrics)} metrics "
                f"and {len(deduplicated_portfolios)} deduplicated portfolios"
            )
        else:
            log("No portfolios found in analysis results")

        return portfolio_metrics, deduplicated_portfolios

    def _create_deduplication_key(self, portfolio_dict: dict[str, Any]) -> str:
        """Create a unique key for portfolio deduplication."""
        # Use key attributes to create a unique identifier
        ticker = portfolio_dict.get("ticker", "unknown")
        strategy_type = portfolio_dict.get("strategy_type", "unknown")
        timeframe = portfolio_dict.get("timeframe", "unknown")

        # Include key parameters that make portfolios unique
        fast_period = portfolio_dict.get("fast_period", "")
        slow_period = portfolio_dict.get("slow_period", "")

        return f"{ticker}_{strategy_type}_{timeframe}_{fast_period}_{slow_period}"

    def collect_export_paths(
        self, config: dict[str, Any], strategy_types: list[str], log
    ) -> dict[str, list[str]]:
        """
        Collect paths of exported portfolio CSV files.

        Args:
            config: Strategy configuration
            strategy_types: List of strategy types analyzed
            log: Logging function

        Returns:
            Dictionary with export paths organized by type
        """
        export_paths = {"portfolios": [], "portfolios_filtered": []}

        try:
            # Get ticker list
            tickers = []
            if isinstance(config.get("TICKER"), str):
                tickers = [config["TICKER"]]
            elif isinstance(config.get("TICKER"), list):
                tickers = config["TICKER"]

            # Construct expected file paths for each ticker and strategy type
            for ticker in tickers:
                # Format ticker for filename (replace special characters)
                ticker_formatted = ticker.replace("-", "-").replace("/", "_")

                for strategy_type in strategy_types:
                    # Check for portfolio files
                    portfolio_pattern = (
                        f"data/raw/strategies/{ticker_formatted}_*_{strategy_type}.csv"
                    )
                    portfolio_files = glob.glob(portfolio_pattern)
                    export_paths["portfolios"].extend(portfolio_files)

                    # Check for filtered portfolio files
                    filtered_pattern = f"data/raw/strategies/filtered/{ticker_formatted}_*_{strategy_type}.csv"
                    filtered_files = glob.glob(filtered_pattern)
                    export_paths["portfolios_filtered"].extend(filtered_files)

            # Remove duplicates and sort
            export_paths["portfolios"] = sorted(set(export_paths["portfolios"]))
            export_paths["portfolios_filtered"] = sorted(
                set(export_paths["portfolios_filtered"])
            )

            log(
                f"Found {len(export_paths['portfolios'])} portfolio files and "
                f"{len(export_paths['portfolios_filtered'])} filtered files"
            )

        except Exception as e:
            log(f"Error collecting export paths: {e!s}", "error")

        return export_paths

    def validate_portfolio_data(self, portfolio_dict: dict[str, Any], log) -> bool:
        """
        Validate portfolio dictionary contains required fields.

        Args:
            portfolio_dict: Portfolio dictionary to validate
            log: Logging function

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["ticker", "strategy_type", "timeframe"]

        for field in required_fields:
            if field not in portfolio_dict:
                log(f"Portfolio missing required field: {field}", "warning")
                return False

        return True

    def calculate_portfolio_summary(
        self, portfolios: list[dict[str, Any]], log
    ) -> dict[str, Any]:
        """
        Calculate summary statistics for a collection of portfolios.

        Args:
            portfolios: List of portfolio dictionaries
            log: Logging function

        Returns:
            Dictionary with summary statistics
        """
        if not portfolios:
            return {"total_count": 0, "summary": "No portfolios to summarize"}

        summary = {
            "total_count": len(portfolios),
            "tickers": set(),
            "strategy_types": set(),
            "timeframes": set(),
        }

        try:
            for portfolio in portfolios:
                if self.validate_portfolio_data(portfolio, log):
                    summary["tickers"].add(portfolio.get("ticker", "unknown"))
                    summary["strategy_types"].add(
                        portfolio.get("strategy_type", "unknown")
                    )
                    summary["timeframes"].add(portfolio.get("timeframe", "unknown"))

            # Convert sets to lists for JSON serialization
            summary["tickers"] = sorted(summary["tickers"])
            summary["strategy_types"] = sorted(summary["strategy_types"])
            summary["timeframes"] = sorted(summary["timeframes"])

            log(
                f"Portfolio summary: {summary['total_count']} portfolios, "
                f"{len(summary['tickers'])} tickers, "
                f"{len(summary['strategy_types'])} strategy types"
            )

        except Exception as e:
            log(f"Error calculating portfolio summary: {e!s}", "error")
            summary["error"] = str(e)

        return summary

    def filter_portfolios_by_criteria(
        self, portfolios: list[dict[str, Any]], criteria: dict[str, Any], log
    ) -> list[dict[str, Any]]:
        """
        Filter portfolios based on specified criteria.

        Args:
            portfolios: List of portfolio dictionaries
            criteria: Filtering criteria (e.g., {"ticker": "BTC-USD", "min_return": 0.1})
            log: Logging function

        Returns:
            Filtered list of portfolios
        """
        if not criteria:
            return portfolios

        filtered = []

        try:
            for portfolio in portfolios:
                include = True

                # Check each criterion
                for key, value in criteria.items():
                    if key.startswith("min_"):
                        # Numeric minimum threshold
                        field = key[4:]  # Remove "min_" prefix
                        portfolio_value = portfolio.get(field, 0)
                        if portfolio_value < value:
                            include = False
                            break
                    elif key.startswith("max_"):
                        # Numeric maximum threshold
                        field = key[4:]  # Remove "max_" prefix
                        portfolio_value = portfolio.get(field, float("inf"))
                        if portfolio_value > value:
                            include = False
                            break
                    # Exact match
                    elif portfolio.get(key) != value:
                        include = False
                        break

                if include:
                    filtered.append(portfolio)

            log(
                f"Filtered {len(portfolios)} portfolios to {len(filtered)} based on criteria: {criteria}"
            )

        except Exception as e:
            log(f"Error filtering portfolios: {e!s}", "error")
            return portfolios  # Return original list on error

        return filtered
