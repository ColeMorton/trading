"""
Portfolio Monte Carlo Manager for Concurrent Analysis.

Orchestrates Monte Carlo parameter robustness testing across multiple tickers
in a portfolio using concurrent processing with proper resource management.
"""

import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import polars as pl

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.error_handling.exceptions import (
    ConcurrencyAnalysisError,
    ConcurrencyError,
)
from app.concurrency.tools.monte_carlo.config import MonteCarloConfig
from app.concurrency.tools.monte_carlo.core import (
    MonteCarloAnalyzer,
    MonteCarloPortfolioResult,
)
from app.tools.download_data import download_data


# Define Monte Carlo specific error
class MonteCarloAnalysisError(ConcurrencyAnalysisError):
    """Error during Monte Carlo analysis."""

    pass


@dataclass
class MonteCarloProgressTracker:
    """Track progress of Monte Carlo analysis across portfolio."""

    total_tickers: int = 0
    completed_tickers: int = 0
    current_ticker: Optional[str] = None
    start_time: Optional[float] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)

    def update(self, ticker: str, status: str = "processing") -> None:
        """Update progress for a ticker."""
        self.current_ticker = ticker
        if status == "completed":
            self.completed_tickers += 1
        elif status == "error":
            self.completed_tickers += 1

    def add_error(self, ticker: str, error: Exception) -> None:
        """Add error to tracking."""
        self.errors.append(
            {
                "ticker": ticker,
                "error": str(error),
                "type": type(error).__name__,
            }
        )

    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.total_tickers == 0:
            return 0.0
        return (self.completed_tickers / self.total_tickers) * 100


class MonteCarloAnalysisError(ConcurrencyError):
    """Raised when Monte Carlo analysis fails."""

    def __init__(
        self,
        message: str,
        ticker: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, context)
        self.ticker = ticker
        if ticker:
            self.context["ticker"] = ticker


class PortfolioMonteCarloManager:
    """Manages Monte Carlo analysis across a portfolio of tickers.

    This class orchestrates concurrent Monte Carlo parameter robustness testing
    for multiple tickers, following the concurrency module's patterns for
    resource management, error handling, and progress tracking.
    """

    def __init__(
        self,
        config: MonteCarloConfig,
        max_workers: Optional[int] = None,
        log: Optional[Callable[[str, str], None]] = None,
    ):
        """Initialize the portfolio Monte Carlo manager.

        Args:
            config: Monte Carlo configuration
            max_workers: Maximum concurrent workers (defaults to CPU count)
            log: Logging function following concurrency patterns
        """
        self.config = config
        self.max_workers = max_workers or 4  # Conservative default
        self.log = log or self._default_log
        self.analyzer = MonteCarloAnalyzer(config, log)
        self.progress_tracker = MonteCarloProgressTracker()
        self.results: Dict[str, MonteCarloPortfolioResult] = {}

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging function."""
        print(f"[{level.upper()}] {message}")

    def analyze_portfolio(
        self, portfolio_strategies: List[Dict[str, Any]]
    ) -> Dict[str, MonteCarloPortfolioResult]:
        """Analyze parameter robustness for individual strategies in portfolio.

        Args:
            portfolio_strategies: List of strategy dictionaries with ticker,
                                  parameters, and other strategy information

        Returns:
            Dictionary mapping strategy IDs to Monte Carlo results

        Raises:
            MonteCarloAnalysisError: If analysis fails
        """
        if not self.config.is_enabled():
            self.log("Monte Carlo analysis is disabled", "info")
            return {}

        if not portfolio_strategies:
            self.log("No strategies found for Monte Carlo analysis", "warning")
            return {}

        # Assign strategy IDs for individual analysis
        strategies_with_ids = self._assign_strategy_ids(portfolio_strategies)

        self.progress_tracker.total_tickers = len(strategies_with_ids)
        self.log(
            f"Starting Monte Carlo analysis for {len(strategies_with_ids)} individual strategies",
            "info",
        )

        # Process strategies concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures_to_strategy = {
                executor.submit(
                    self._analyze_strategy_with_error_handling, strategy_id, strategy
                ): strategy_id
                for strategy_id, strategy in strategies_with_ids.items()
            }

            # Process completed tasks
            for future in as_completed(futures_to_strategy):
                strategy_id = futures_to_strategy[future]
                try:
                    result = future.result()
                    if result:
                        self.results[strategy_id] = result
                        self.progress_tracker.update(strategy_id, "completed")
                        self.log(
                            f"Completed {strategy_id} ({self.progress_tracker.get_progress_percentage():.1f}%)",
                            "info",
                        )
                except Exception as e:
                    self.progress_tracker.add_error(strategy_id, e)
                    self.progress_tracker.update(strategy_id, "error")
                    self.log(f"Error analyzing {strategy_id}: {str(e)}", "error")

        # Log summary
        self._log_analysis_summary()

        return self.results

    def _assign_strategy_ids(
        self, portfolio_strategies: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Assign unique IDs to each strategy for individual analysis.

        Args:
            portfolio_strategies: List of strategy dictionaries

        Returns:
            Dictionary mapping strategy IDs to strategy data
        """
        strategies_with_ids = {}

        for i, strategy in enumerate(portfolio_strategies):
            # Create unique strategy ID
            ticker = (
                strategy.get("ticker")
                or strategy.get("Ticker")
                or strategy.get("TICKER")
            )
            strategy_type = (
                strategy.get("STRATEGY_TYPE")
                or strategy.get("MA Type")
                or strategy.get("Strategy Type")
            )

            if not strategy_type:
                raise ValueError(
                    f"Strategy type must be explicitly specified for Monte Carlo analysis. Strategy: {ticker or f'Strategy_{i+1}'}"
                )

            short = (
                strategy.get("SHORT_WINDOW")
                or strategy.get("Window Short")
                or strategy.get("Short Window")
                or "X"
            )
            long = (
                strategy.get("LONG_WINDOW")
                or strategy.get("Window Long")
                or strategy.get("Long Window")
                or "Y"
            )

            # Get signal window for MACD strategies
            signal = (
                strategy.get("SIGNAL_WINDOW") or strategy.get("Signal Window") or "0"
            )

            if ticker:
                strategy_id = f"{ticker}_{strategy_type}_{short}_{long}_{signal}"
            else:
                strategy_id = f"Strategy_{i+1}_{strategy_type}_{short}_{long}_{signal}"

            # Ensure unique IDs
            base_id = strategy_id
            counter = 1
            while strategy_id in strategies_with_ids:
                strategy_id = f"{base_id}_{counter}"
                counter += 1

            strategies_with_ids[strategy_id] = strategy

        return strategies_with_ids

    def _analyze_strategy_with_error_handling(
        self, strategy_id: str, strategy: Dict[str, Any]
    ) -> Optional[MonteCarloPortfolioResult]:
        """Analyze a single strategy with error handling.

        Args:
            strategy_id: Unique strategy identifier
            strategy: Strategy configuration dictionary

        Returns:
            Monte Carlo result or None if analysis fails
        """
        try:
            self.progress_tracker.update(strategy_id, "processing")

            # Extract ticker, parameters, and strategy type
            ticker = (
                strategy.get("ticker")
                or strategy.get("Ticker")
                or strategy.get("TICKER")
            )
            short = (
                strategy.get("SHORT_WINDOW")
                or strategy.get("Window Short")
                or strategy.get("Short Window")
            )
            long = (
                strategy.get("LONG_WINDOW")
                or strategy.get("Window Long")
                or strategy.get("Long Window")
            )
            strategy_type = (
                strategy.get("STRATEGY_TYPE")
                or strategy.get("MA Type")
                or strategy.get("Strategy Type")
            )

            if not strategy_type:
                raise ValueError(
                    f"Strategy type must be explicitly specified for {strategy_id}. No default strategy type is allowed."
                )

            if not ticker or not short or not long:
                raise MonteCarloAnalysisError(
                    f"Missing required fields for {strategy_id}", ticker=ticker
                )

            # Download price data
            data = self._download_ticker_data(ticker)
            if data is None or len(data) < 100:  # Minimum data requirement
                raise MonteCarloAnalysisError(
                    f"Insufficient data for {ticker}", ticker=ticker
                )

            # Create parameter combinations for this specific strategy
            base_parameters = [(int(short), int(long))]
            parameter_combinations = self._generate_parameter_variations(
                base_parameters
            )

            # Analyze parameter stability for this strategy
            result = self.analyzer.analyze_parameter_stability(
                strategy_id, data, parameter_combinations, strategy_type, strategy
            )

            return result

        except MonteCarloAnalysisError:
            raise
        except Exception as e:
            raise MonteCarloAnalysisError(
                f"Monte Carlo analysis failed for {strategy_id}: {str(e)}",
                ticker=ticker,
                context={"strategy": strategy},
            )

    def _generate_parameter_variations(
        self, base_parameters: List[Tuple[int, int]]
    ) -> List[Tuple[int, int]]:
        """Generate parameter variations around base parameters for a single strategy.

        Args:
            base_parameters: List with single (short, long) tuple for the strategy

        Returns:
            List of parameter variations to test
        """
        if not base_parameters:
            return []

        base_short, base_long = base_parameters[0]  # Single strategy
        variations = set()

        # Add the original combination
        variations.add((base_short, base_long))

        # Add variations: ±1, ±2, ±3 for each parameter
        for short_delta in [-3, -2, -1, 1, 2, 3]:
            for long_delta in [-3, -2, -1, 1, 2, 3]:
                new_short = max(5, base_short + short_delta)  # Minimum window of 5
                new_long = max(
                    new_short + 1, base_long + long_delta
                )  # Long must be > short

                if new_short < new_long and new_long < 100:  # Reasonable max window
                    variations.add((new_short, new_long))

        # Limit total variations to respect configuration
        variations_list = sorted(list(variations))
        max_variations = min(self.config.max_parameters_to_test, len(variations_list))

        return variations_list[:max_variations]

    def _group_strategies_by_ticker(
        self, portfolio_strategies: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group strategies by ticker symbol."""
        ticker_strategies = {}

        for strategy in portfolio_strategies:
            # Support multiple field name formats
            ticker = (
                strategy.get("ticker")
                or strategy.get("Ticker")
                or strategy.get("TICKER")
            )
            if not ticker:
                self.log(
                    f"Strategy missing ticker field, skipping: {list(strategy.keys())[:5]}",
                    "warning",
                )
                continue

            if ticker not in ticker_strategies:
                ticker_strategies[ticker] = []

            ticker_strategies[ticker].append(strategy)

        return ticker_strategies

    def _analyze_ticker_with_error_handling(
        self, ticker: str, strategies: List[Dict[str, Any]]
    ) -> Optional[MonteCarloPortfolioResult]:
        """Analyze a single ticker with error handling.

        Args:
            ticker: Ticker symbol
            strategies: List of strategies for this ticker

        Returns:
            Monte Carlo result or None if analysis fails
        """
        try:
            self.progress_tracker.update(ticker, "processing")

            # Download price data
            data = self._download_ticker_data(ticker)
            if data is None or len(data) < 100:  # Minimum data requirement
                raise MonteCarloAnalysisError(
                    f"Insufficient data for {ticker}", ticker=ticker
                )

            # Extract parameter combinations from strategies
            parameter_combinations = self._extract_parameter_combinations(strategies)

            if not parameter_combinations:
                self.log(f"No valid parameters found for {ticker}", "warning")
                return None

            # Run Monte Carlo analysis
            result = self.analyzer.analyze_parameter_stability(
                ticker=ticker, data=data, parameter_combinations=parameter_combinations
            )

            return result

        except Exception as e:
            raise MonteCarloAnalysisError(
                f"Monte Carlo analysis failed for {ticker}: {str(e)}",
                ticker=ticker,
                context={"strategies_count": len(strategies)},
            )

    def _download_ticker_data(self, ticker: str) -> Optional[pl.DataFrame]:
        """Download price data for ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Price data DataFrame or None if download fails
        """
        try:
            # Create basic config for data download
            config = {
                "BASE_DIR": ".",
                "USE_HOURLY": False,
                "USE_YEARS": True,
                "YEARS": 3,
                "REFRESH": False,  # Use cached data when available
            }

            # Use existing download_data function from tools
            data = download_data(ticker, config, self.log)

            if data is None or data.is_empty():
                self.log(f"No data available for {ticker}", "warning")
                return None

            # Ensure required columns exist
            required_columns = ["Date", "Open", "High", "Low", "Close"]
            missing_columns = [
                col for col in required_columns if col not in data.columns
            ]

            if missing_columns:
                self.log(f"Missing columns for {ticker}: {missing_columns}", "warning")
                return None

            return data

        except Exception as e:
            self.log(f"Error downloading data for {ticker}: {str(e)}", "error")
            return None

    def _extract_parameter_combinations(
        self, strategies: List[Dict[str, Any]]
    ) -> List[Tuple[int, int]]:
        """Extract and expand parameter combinations for robustness testing.

        Args:
            strategies: List of strategy dictionaries

        Returns:
            List of parameter combinations including variations around base parameters
        """
        base_combinations = set()

        # Extract base combinations from strategies
        for strategy in strategies:
            # Check for MA Cross parameters with flexible field names
            ma_type = (
                strategy.get("STRATEGY_TYPE")
                or strategy.get("MA Type")
                or strategy.get("Strategy Type")
            )
            short = (
                strategy.get("SHORT_WINDOW")
                or strategy.get("Window Short")
                or strategy.get("Short Window")
            )
            long = (
                strategy.get("LONG_WINDOW")
                or strategy.get("Window Long")
                or strategy.get("Long Window")
            )

            if (
                ma_type
                and short
                and long
                and isinstance(short, (int, float))
                and isinstance(long, (int, float))
            ):
                base_combinations.add((int(short), int(long)))

        # Generate variations around base combinations for robustness testing
        expanded_combinations = set()

        for short, long in base_combinations:
            # Add the original combination
            expanded_combinations.add((short, long))

            # Add variations: ±1, ±2, ±3 for each parameter
            for short_delta in [-3, -2, -1, 1, 2, 3]:
                for long_delta in [-3, -2, -1, 1, 2, 3]:
                    new_short = max(5, short + short_delta)  # Minimum window of 5
                    new_long = max(
                        new_short + 1, long + long_delta
                    )  # Long must be > short

                    if new_short < new_long and new_long < 100:  # Reasonable max window
                        expanded_combinations.add((new_short, new_long))

        # Limit total combinations to respect configuration
        combinations_list = sorted(list(expanded_combinations))
        max_combinations = min(
            self.config.max_parameters_to_test, len(combinations_list)
        )

        return combinations_list[:max_combinations]

    def _log_analysis_summary(self) -> None:
        """Log summary of Monte Carlo analysis."""
        total = self.progress_tracker.total_tickers
        completed = self.progress_tracker.completed_tickers
        errors = len(self.progress_tracker.errors)
        successful = completed - errors

        self.log(f"\nMonte Carlo Analysis Summary:", "info")
        self.log(f"  Total tickers: {total}", "info")
        self.log(f"  Successful: {successful}", "info")
        self.log(f"  Failed: {errors}", "info")

        if self.progress_tracker.errors:
            self.log("\nErrors encountered:", "warning")
            for error_info in self.progress_tracker.errors[:5]:  # Show first 5 errors
                self.log(f"  {error_info['ticker']}: {error_info['error']}", "warning")

            if len(self.progress_tracker.errors) > 5:
                self.log(
                    f"  ... and {len(self.progress_tracker.errors) - 5} more", "warning"
                )

    def get_portfolio_stability_metrics(self) -> Dict[str, float]:
        """Calculate portfolio-wide stability metrics.

        Returns:
            Dictionary of portfolio-level metrics
        """
        if not self.results:
            return {
                "portfolio_stability_score": 0.0,
                "average_parameter_robustness": 0.0,
                "stable_tickers_percentage": 0.0,
            }

        stability_scores = []
        robustness_scores = []
        stable_tickers = 0

        for ticker, result in self.results.items():
            stability_scores.append(result.portfolio_stability_score)

            # Calculate average robustness across all parameters for this ticker
            if result.parameter_results:
                ticker_robustness = sum(
                    pr.parameter_robustness for pr in result.parameter_results
                ) / len(result.parameter_results)
                robustness_scores.append(ticker_robustness)

                # Count as stable if has stable parameters
                if any(pr.is_stable for pr in result.parameter_results):
                    stable_tickers += 1

        return {
            "portfolio_stability_score": sum(stability_scores) / len(stability_scores)
            if stability_scores
            else 0.0,
            "average_parameter_robustness": sum(robustness_scores)
            / len(robustness_scores)
            if robustness_scores
            else 0.0,
            "stable_tickers_percentage": (stable_tickers / len(self.results)) * 100
            if self.results
            else 0.0,
        }

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get parameter recommendations based on Monte Carlo analysis.

        Returns:
            List of recommendations for each ticker
        """
        recommendations = []

        for ticker, result in self.results.items():
            if result.recommended_parameters:
                recommendations.append(
                    {
                        "ticker": ticker,
                        "recommended_parameters": result.recommended_parameters,
                        "stability_score": result.portfolio_stability_score,
                        "confidence": "high"
                        if result.portfolio_stability_score > 0.8
                        else "medium",
                        "parameter_count": len(result.parameter_results),
                    }
                )

        # Sort by stability score (highest first)
        return sorted(recommendations, key=lambda x: x["stability_score"], reverse=True)
