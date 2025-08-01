"""
Portfolio Statistical Analysis - Simplified Interface

This module provides a clean, portfolio-centric interface for the Statistical
Performance Divergence System. Just specify a portfolio and whether to use
trade history - everything else is handled automatically.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from .config.statistical_analysis_config import SPDSConfig, StatisticalAnalysisConfig
from .models.statistical_analysis_models import StatisticalAnalysisResult
from .services.statistical_analysis_service import StatisticalAnalysisService
from .uuid_utils import parse_strategy_uuid


class PortfolioStatisticalAnalyzer:
    """
    Simplified portfolio-based statistical analyzer.

    Usage:
        # Analyze portfolio with trade history
        analyzer = PortfolioStatisticalAnalyzer("risk_on.csv", use_trade_history=True)
        results = await analyzer.analyze()

        # Analyze portfolio with equity curves
        analyzer = PortfolioStatisticalAnalyzer("conservative.csv", use_trade_history=False)
        results = await analyzer.analyze()
    """

    def __init__(
        self,
        portfolio: str,
        use_trade_history: bool = True,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize portfolio analyzer.

        Args:
            portfolio: Portfolio filename (e.g., "risk_on.csv")
            use_trade_history: Use trade history (True) or equity curves (False)
            logger: Optional logger instance
        """
        self.portfolio = portfolio
        self.use_trade_history = use_trade_history
        self.logger = logger or logging.getLogger(__name__)

        # Create configuration
        self.config = StatisticalAnalysisConfig.create(portfolio, use_trade_history)

        # Initialize service
        self.service = StatisticalAnalysisService(
            config=self.config, logger=self.logger
        )

        # Cache loaded data
        self._portfolio_data: Optional[pd.DataFrame] = None
        self._trade_history_data: Optional[pd.DataFrame] = None

        self.logger.info(
            f"Portfolio analyzer initialized for '{portfolio}' with "
            f"trade_history={use_trade_history}"
        )

    def load_portfolio(self) -> pd.DataFrame:
        """Load portfolio CSV from ./data/raw/strategies/"""
        if self._portfolio_data is not None:
            return self._portfolio_data

        portfolio_path = self.config.get_portfolio_file_path()

        if not portfolio_path.exists():
            raise FileNotFoundError(f"Portfolio file not found: {portfolio_path}")

        self.logger.info(f"Loading portfolio from: {portfolio_path}")
        self._portfolio_data = pd.read_csv(portfolio_path)

        self.logger.info(
            f"Loaded {len(self._portfolio_data)} strategies from portfolio"
        )
        return self._portfolio_data

    def load_trade_history(self) -> Optional[pd.DataFrame]:
        """Load trade history CSV from ./data/raw/positions/ (same filename as portfolio)"""
        if not self.use_trade_history:
            return None

        if self._trade_history_data is not None:
            return self._trade_history_data

        trade_history_path = self.config.get_trade_history_file_path()

        if not trade_history_path.exists():
            if self.config.FALLBACK_TO_EQUITY:
                self.logger.info(
                    f"Trade history file not found: {trade_history_path}. "
                    f"Using equity curve analysis (fallback mode enabled). "
                    f"This is normal when analyzing strategies without individual trade data."
                )
                return None
            else:
                raise FileNotFoundError(
                    f"Trade history file not found: {trade_history_path}"
                )

        self.logger.info(f"Loading trade history from: {trade_history_path}")
        self._trade_history_data = pd.read_csv(trade_history_path)

        self.logger.info(f"Loaded {len(self._trade_history_data)} trades from history")
        return self._trade_history_data

    async def analyze(
        self, detailed: bool = False
    ) -> Dict[str, StatisticalAnalysisResult]:
        """
        Analyze entire portfolio and return results for all strategies.

        Args:
            detailed: If True, include component score calculations

        Returns:
            Dictionary mapping strategy names to analysis results
        """
        portfolio_data = self.load_portfolio()
        trade_history_data = self.load_trade_history()

        # CRITICAL FIX: Load position context for the entire portfolio
        # This is needed to prevent BUY signals for already-held positions
        portfolio_name = self.portfolio.replace(".csv", "")
        position_context = await self.service._load_position_context(portfolio_name)

        if position_context:
            self.logger.info(
                f"Loaded position context with {len(position_context)} positions for portfolio {portfolio_name}"
            )
        else:
            self.logger.info(
                f"No position context found for portfolio {portfolio_name}"
            )

        results = {}

        # Extract unique strategies from portfolio
        strategies = self._extract_strategies_from_portfolio(portfolio_data)

        self.logger.info(f"Analyzing {len(strategies)} strategies from portfolio")

        for strategy_info in strategies:
            try:
                result = await self._analyze_strategy(
                    strategy_info, trade_history_data, detailed, position_context
                )
                results[strategy_info["strategy_name"]] = result

            except Exception as e:
                self.logger.error(
                    f"Failed to analyze strategy {strategy_info['strategy_name']}: {e}"
                )
                # Continue with other strategies

        self.logger.info(f"Completed analysis of {len(results)} strategies")
        return results

    def get_exit_signals(
        self, results: Dict[str, StatisticalAnalysisResult]
    ) -> Dict[str, str]:
        """
        Extract exit signals from analysis results.

        Args:
            results: Analysis results from analyze()

        Returns:
            Dictionary mapping strategy names to exit signals
        """
        signals = {}

        for strategy_name, result in results.items():
            # Check for exit_signal field (ProbabilisticExitSignal object)
            if hasattr(result, "exit_signal") and result.exit_signal:
                if hasattr(result.exit_signal, "signal_type"):
                    if hasattr(result.exit_signal.signal_type, "value"):
                        signals[strategy_name] = result.exit_signal.signal_type.value
                    else:
                        signals[strategy_name] = str(result.exit_signal.signal_type)
                else:
                    signals[strategy_name] = "HOLD"  # Default
            elif hasattr(result, "exit_signals") and result.exit_signals:
                # Legacy field name
                signals[strategy_name] = result.exit_signals.primary_signal
            else:
                signals[strategy_name] = "HOLD"  # Default

        return signals

    def get_summary_report(
        self, results: Dict[str, StatisticalAnalysisResult]
    ) -> Dict[str, Any]:
        """
        Generate summary report of portfolio analysis.

        Args:
            results: Analysis results from analyze()

        Returns:
            Summary statistics and recommendations
        """
        exit_signals = self.get_exit_signals(results)

        signal_counts = {}
        for signal in exit_signals.values():
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        high_confidence_count = 0
        total_strategies = len(results)

        for result in results.values():
            # Check multiple ways to get confidence
            confidence = 0.5  # Default

            # Try overall_confidence field directly
            if hasattr(result, "overall_confidence"):
                confidence = result.overall_confidence
                # Convert to fraction if percentage
                if confidence > 1.0:
                    confidence = confidence / 100.0
            # Try exit_signal.confidence
            elif (
                hasattr(result, "exit_signal")
                and result.exit_signal
                and hasattr(result.exit_signal, "confidence")
            ):
                confidence = result.exit_signal.confidence
                # Convert to fraction if percentage
                if confidence > 1.0:
                    confidence = confidence / 100.0
            # Try confidence_metrics.overall_confidence
            elif (
                hasattr(result, "confidence_metrics")
                and result.confidence_metrics
                and hasattr(result.confidence_metrics, "overall_confidence")
            ):
                confidence = result.confidence_metrics.overall_confidence
                # Convert to fraction if percentage
                if confidence > 1.0:
                    confidence = confidence / 100.0

            # Count as high confidence if > 50% (adjusted for statistical analysis context)
            if confidence > 0.5:
                high_confidence_count += 1

        return {
            "portfolio": self.portfolio,
            "total_strategies": total_strategies,
            "use_trade_history": self.use_trade_history,
            "signal_distribution": signal_counts,
            "high_confidence_analyses": high_confidence_count,
            "confidence_rate": high_confidence_count / total_strategies
            if total_strategies > 0
            else 0,
            "immediate_exits": signal_counts.get("EXIT_IMMEDIATELY", 0),
            "strong_sells": signal_counts.get("STRONG_SELL", 0),
            "holds": signal_counts.get("HOLD", 0),
        }

    def _extract_strategies_from_portfolio(
        self, portfolio_data: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """Extract strategy information from portfolio CSV."""
        strategies = []

        for _, row in portfolio_data.iterrows():
            # First try to parse Position_UUID if available (for live_signals.csv format)
            position_uuid = row.get("Position_UUID", "")
            if position_uuid:
                try:
                    # Parse Position_UUID like "MA_SMA_78_82_0_2025-04-14"
                    parsed = parse_strategy_uuid(position_uuid)
                    ticker = parsed.get("ticker", "UNKNOWN")
                    strategy_type = parsed.get("strategy_type", "SMA")
                    short_window = parsed.get("short_window", "")
                    long_window = parsed.get("long_window", "")

                    # Strategy name should include ticker to match Position_UUID pattern
                    if str(short_window) and str(long_window):
                        strategy_name = f"{ticker}_{strategy_type}_{short_window}_{long_window}"  # e.g. "MA_SMA_78_82"
                    else:
                        strategy_name = f"{ticker}_{strategy_type}"

                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse Position_UUID '{position_uuid}': {e}"
                    )
                    # Fall back to manual extraction
                    ticker = row.get(
                        "Ticker", row.get("ticker", row.get("Symbol", "UNKNOWN"))
                    )
                    strategy_type = row.get(
                        "Strategy Type", row.get("strategy_type", "SMA")
                    )
                    short_window = row.get("Short Window", row.get("short_window", ""))
                    long_window = row.get("Long Window", row.get("long_window", ""))
                    strategy_name = (
                        f"{strategy_type}_{short_window}_{long_window}"
                        if str(short_window) and str(long_window)
                        else strategy_type
                    )
            else:
                # Handle other CSV formats with separate columns
                ticker = row.get(
                    "Ticker", row.get("ticker", row.get("Symbol", "UNKNOWN"))
                )
                strategy_type = row.get(
                    "Strategy Type", row.get("strategy_type", "SMA")
                )
                short_window = row.get("Short Window", row.get("short_window", ""))
                long_window = row.get("Long Window", row.get("long_window", ""))

                # Strategy name should include ticker to match Position_UUID pattern
                if ticker != "UNKNOWN" and str(short_window) and str(long_window):
                    strategy_name = f"{ticker}_{strategy_type}_{short_window}_{long_window}"  # e.g. "MA_SMA_78_82"
                else:
                    # Fallback to existing logic for other formats
                    strategy_name = row.get(
                        "strategy_name", row.get("Strategy", "UNKNOWN")
                    )

            strategy_info = {
                "strategy_name": strategy_name,
                "ticker": ticker,
                "allocation": row.get("allocation", row.get("Allocation", 0.0)),
                "strategy_type": strategy_type,
                "short_window": short_window,
                "long_window": long_window,
            }

            # Add any additional columns as metadata
            for col in portfolio_data.columns:
                if col not in [
                    "strategy_name",
                    "ticker",
                    "allocation",
                    "Strategy",
                    "Ticker",
                    "Symbol",
                    "Allocation",
                    "Strategy Type",
                    "Short Window",
                    "Long Window",
                ]:
                    strategy_info[col.lower().replace(" ", "_")] = row[col]

            strategies.append(strategy_info)

        return strategies

    async def _analyze_strategy(
        self,
        strategy_info: Dict[str, Any],
        trade_history_data: Optional[pd.DataFrame],
        detailed: bool = False,
        position_context: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> StatisticalAnalysisResult:
        """Analyze individual strategy from portfolio."""
        strategy_name = strategy_info["strategy_name"]
        ticker = strategy_info["ticker"]

        # Filter trade history for this strategy if available
        strategy_trade_data = None
        if trade_history_data is not None:
            # Check if trade history has strategy_name column
            if "strategy_name" in trade_history_data.columns:
                strategy_trades = trade_history_data[
                    trade_history_data["strategy_name"] == strategy_name
                ]
            else:
                # Try multiple matching approaches for trade history
                strategy_trades = None

                # Approach 1: Position_UUID pattern matching
                if "Position_UUID" in trade_history_data.columns:
                    # Match against Position_UUID pattern (e.g., MA_SMA_78_82_2025-04-14)
                    strategy_pattern = f"{strategy_name}_"  # e.g., "MA_SMA_78_82_"
                    strategy_trades = trade_history_data[
                        trade_history_data["Position_UUID"].str.startswith(
                            strategy_pattern
                        )
                    ]
                    if not strategy_trades.empty:
                        self.logger.info(
                            f"Found {len(strategy_trades)} trades using Position_UUID pattern matching"
                        )

                # Approach 2: Exact component matching (fallback if Position_UUID matching failed)
                if (
                    strategy_trades is None or strategy_trades.empty
                ) and "Ticker" in trade_history_data.columns:
                    strategy_trades = trade_history_data[
                        (trade_history_data["Ticker"] == ticker)
                        & (
                            trade_history_data["Strategy_Type"]
                            == strategy_info.get("strategy_type", "SMA")
                        )
                        & (
                            trade_history_data["Short_Window"].astype(str)
                            == str(strategy_info.get("short_window", ""))
                        )
                        & (
                            trade_history_data["Long_Window"].astype(str)
                            == str(strategy_info.get("long_window", ""))
                        )
                    ]

                # Approach 3: Fuzzy UUID matching if exact matching fails
                if strategy_trades is None or len(strategy_trades) == 0:
                    strategy_trades = self._fuzzy_match_trade_history(
                        trade_history_data, strategy_name, ticker, strategy_info
                    )

            if strategy_trades is not None and len(strategy_trades) > 0:
                strategy_trade_data = strategy_trades.to_dict("records")
                self.logger.info(
                    f"Found {len(strategy_trades)} trade history records for {strategy_name}"
                )
            else:
                self.logger.info(
                    f"No trade history found for {strategy_name} (ticker: {ticker}) - using equity curve analysis"
                )

        # CRITICAL FIX: Check for open position in position context
        position_data = None
        if position_context:
            position_data = self.service._find_matching_position(
                strategy_name, position_context
            )
            if position_data:
                self.logger.info(
                    f"Found open position for {strategy_name}: {position_data.get('current_unrealized_pnl', 0):.1%} P&L, {position_data.get('days_since_entry', 0)} days held"
                )

        # Use the existing service method with position context
        result = await self.service.analyze_position(
            strategy_name=strategy_name,
            ticker=ticker,
            current_position_data=strategy_trade_data,
        )

        # CRITICAL FIX: If there's an open position, override the signal generation
        if position_data and self.service._is_position_open(position_data):
            self.logger.info(
                f"Overriding signal generation for open position {strategy_name}"
            )

            # Use position-aware signal generation instead of generic signal generation
            position_aware_signal = await self.service._generate_position_aware_signal(
                result.strategy_analysis,
                result.asset_analysis,
                result.dual_layer_convergence,
                result.asset_divergence,
                result.strategy_divergence,
                position_data,
                component_scores=result.raw_analysis_data.get("component_scores")
                if result.raw_analysis_data
                else None,
            )

            # Replace the exit signal with position-aware signal
            result.exit_signal = position_aware_signal

            # Update recommendation summary for position
            signal_type = position_aware_signal.signal_type
            confidence = position_aware_signal.confidence

            if signal_type.name.startswith("STRONG_BUY") or signal_type.name.startswith(
                "BUY"
            ):
                result.recommendation_summary = f"Position already held ({position_data.get('current_unrealized_pnl', 0):.1%} P&L, {position_data.get('days_since_entry', 0)} days). Signal: {signal_type.name} - Continue holding."
            else:
                result.recommendation_summary = f"Position held ({position_data.get('current_unrealized_pnl', 0):.1%} P&L, {position_data.get('days_since_entry', 0)} days). Exit signal: {signal_type.name} (confidence: {confidence:.1f}%)"

            self.logger.info(
                f"Updated signal for open position {strategy_name}: {signal_type.name} with {confidence:.1f}% confidence"
            )

        # Extract MFE/MAE directly from trade data and attach to result for export
        if strategy_trade_data:
            try:
                # Extract MFE/MAE values from the trade data
                mfe_values = []
                mae_values = []
                for trade in strategy_trade_data:
                    mfe_val = trade.get("Max_Favourable_Excursion", 0.0)
                    mae_val = trade.get("Max_Adverse_Excursion", 0.0)
                    if mfe_val != 0.0:
                        mfe_values.append(float(mfe_val))
                    if mae_val != 0.0:
                        mae_values.append(float(mae_val))

                # Calculate averages if we have data
                avg_mfe = sum(mfe_values) / len(mfe_values) if mfe_values else 0.0
                avg_mae = sum(mae_values) / len(mae_values) if mae_values else 0.0

                # Store in result as temporary attributes for later extraction
                result._temp_trade_mfe = avg_mfe
                result._temp_trade_mae = avg_mae
                result._temp_trade_data = strategy_trade_data

                self.logger.info(
                    f"Extracted MFE/MAE for {strategy_name}: MFE={avg_mfe:.4f}, MAE={avg_mae:.4f}"
                )

            except Exception as e:
                self.logger.error(
                    f"Failed to extract MFE/MAE from trade data for {strategy_name}: {e}"
                )

        # Add component score calculation if detailed analysis is requested
        if detailed:
            try:
                from .market_data_analyzer import MarketDataAnalyzer

                self.logger.info(f"Calculating component scores for {ticker}")
                market_analyzer = MarketDataAnalyzer(ticker, self.logger)

                # Fetch data and calculate component scores
                if market_analyzer.fetch_data():
                    analysis_result = await market_analyzer.analyze(
                        include_components=True
                    )
                    component_scores = analysis_result.get("component_scores", {})

                    if component_scores:
                        # Store component scores in the raw_analysis_data field
                        if result.raw_analysis_data is None:
                            result.raw_analysis_data = {}
                        result.raw_analysis_data["component_scores"] = component_scores
                        self.logger.info(
                            f"Added component scores for {ticker}: {len(component_scores)} components"
                        )

                        # Apply component score override to exit signal
                        result = self.service.update_exit_signal_with_component_scores(
                            result, component_scores
                        )
                    else:
                        self.logger.warning(
                            f"No component scores returned for {ticker}"
                        )
                else:
                    self.logger.warning(
                        f"Failed to fetch market data for component scores: {ticker}"
                    )

            except Exception as e:
                self.logger.error(
                    f"Failed to calculate component scores for {strategy_name}: {e}"
                )

        return result

    def _fuzzy_match_trade_history(
        self, trade_history_data, strategy_name, ticker, strategy_info
    ):
        """
        Fuzzy match trade history using Position_UUID pattern matching.
        Handles UUIDs like 'RJF_SMA_68_77_2025-06-23' for strategy 'RJF_SMA_68_77'
        """
        import re

        import pandas as pd

        if "Position_UUID" not in trade_history_data.columns:
            return None

        # Extract strategy components for fuzzy matching
        strategy_type = strategy_info.get("strategy_type", "SMA")
        short_window = str(strategy_info.get("short_window", ""))
        long_window = str(strategy_info.get("long_window", ""))

        # Create expected strategy prefix pattern
        expected_prefix = f"{ticker}_{strategy_type}_{short_window}_{long_window}"

        self.logger.info(
            f"Fuzzy matching for {strategy_name}: expected_prefix={expected_prefix}"
        )

        # Pattern to match UUID with date suffix: {strategy_prefix}_{YYYYMMDD}
        date_pattern = r"_\d{8}$"

        matched_rows = []

        for idx, row in trade_history_data.iterrows():
            position_uuid = str(row["Position_UUID"])

            # Remove date suffix if present
            uuid_without_date = re.sub(date_pattern, "", position_uuid)

            # Check if the UUID matches our expected strategy pattern
            if uuid_without_date == expected_prefix:
                matched_rows.append(row)
                self.logger.info(
                    f"Fuzzy matched trade history: {position_uuid} -> {strategy_name}"
                )

        if matched_rows:
            return pd.DataFrame(matched_rows)
        else:
            # Try broader matching - just ticker and strategy type
            broader_pattern = f"{ticker}_{strategy_type}"
            for idx, row in trade_history_data.iterrows():
                position_uuid = str(row["Position_UUID"])
                uuid_without_date = re.sub(date_pattern, "", position_uuid)

                if uuid_without_date.startswith(broader_pattern):
                    matched_rows.append(row)
                    self.logger.info(
                        f"Broad fuzzy matched trade history: {position_uuid} -> {strategy_name}"
                    )

            if matched_rows:
                return pd.DataFrame(matched_rows)

        return None


# Convenience function for quick analysis
async def analyze_portfolio(
    portfolio: str, use_trade_history: bool = True
) -> Tuple[Dict[str, StatisticalAnalysisResult], Dict[str, Any]]:
    """
    Quick portfolio analysis function.

    Args:
        portfolio: Portfolio filename (e.g., "risk_on.csv")
        use_trade_history: Use trade history (True) or equity curves (False)

    Returns:
        Tuple of (analysis_results, summary_report)

    Example:
        results, summary = await analyze_portfolio("risk_on.csv", use_trade_history=True)

        print(f"Portfolio: {summary['portfolio']}")
        print(f"Immediate exits: {summary['immediate_exits']}")
        print(f"Strong sells: {summary['strong_sells']}")
    """
    analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
    results = await analyzer.analyze()
    summary = analyzer.get_summary_report(results)

    return results, summary


# Example usage
if __name__ == "__main__":

    async def example():
        # Example 1: Analyze risk_on portfolio with trade history
        print("=== Risk On Portfolio with Trade History ===")
        analyzer1 = PortfolioStatisticalAnalyzer("risk_on.csv", use_trade_history=True)
        results1 = await analyzer1.analyze()
        summary1 = analyzer1.get_summary_report(results1)

        print(f"Total strategies: {summary1['total_strategies']}")
        print(f"Immediate exits: {summary1['immediate_exits']}")
        print(f"Confidence rate: {summary1['confidence_rate']:.1%}")

        # Example 2: Analyze conservative portfolio with equity curves
        print("\n=== Conservative Portfolio with Equity Curves ===")
        analyzer2 = PortfolioStatisticalAnalyzer(
            "conservative.csv", use_trade_history=False
        )
        results2 = await analyzer2.analyze()
        summary2 = analyzer2.get_summary_report(results2)

        print(f"Total strategies: {summary2['total_strategies']}")
        print(f"Signal distribution: {summary2['signal_distribution']}")

        # Example 3: Quick analysis function
        print("\n=== Quick Analysis ===")
        results3, summary3 = await analyze_portfolio(
            "momentum.csv", use_trade_history=True
        )
        print(f"Quick analysis complete for {summary3['total_strategies']} strategies")

    # Run example
    asyncio.run(example())
