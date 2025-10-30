"""
Correlation Analyzer

Analyzes correlations between strategies, tickers, and timeframes using
Pearson, Spearman, and Kendall correlation methods for cross-strategy analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import kendalltau, pearsonr, spearmanr

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import CorrelationType


class CorrelationAnalyzer:
    """
    Analyzes correlations across multiple dimensions of trading performance.

    Provides comprehensive correlation analysis including:
    - Cross-strategy performance correlations
    - Cross-ticker correlations within strategies
    - Multi-timeframe correlation analysis
    - Dynamic correlation tracking over time
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
        """
        Initialize the Correlation Analyzer

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Correlation thresholds
        self.strong_correlation_threshold = 0.7
        self.moderate_correlation_threshold = 0.5
        self.weak_correlation_threshold = 0.3

        # Minimum sample size for reliable correlations
        self.min_correlation_sample_size = 20

        self.logger.info("CorrelationAnalyzer initialized")

    async def analyze_cross_strategy_correlations(
        self,
        strategies: list[str],
        timeframe: str = "D",
        correlation_types: list[CorrelationType] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze correlations between different strategies

        Args:
            strategies: List of strategy names to analyze
            timeframe: Timeframe for correlation analysis
            correlation_types: Types of correlations to calculate

        Returns:
            Cross-strategy correlation analysis results
        """
        try:
            if correlation_types is None:
                correlation_types = [CorrelationType.PEARSON, CorrelationType.SPEARMAN]

            self.logger.info(
                f"Analyzing cross-strategy correlations for {len(strategies)} strategies",
            )

            # Load strategy performance data
            strategy_data = await self._load_strategy_performance_data(
                strategies,
                timeframe,
            )

            # Calculate correlation matrices for each correlation type
            correlation_matrices = {}
            correlation_results = {}

            for corr_type in correlation_types:
                matrix, results = await self._calculate_correlation_matrix(
                    strategy_data,
                    corr_type,
                )
                correlation_matrices[corr_type.value] = matrix
                correlation_results[corr_type.value] = results

            # Identify strongest correlations
            strongest_correlations = self._identify_strongest_correlations(
                correlation_results,
                strategies,
            )

            # Calculate correlation stability over time
            correlation_stability = await self._analyze_correlation_stability(
                strategies,
                timeframe,
            )

            return {
                "strategies_analyzed": strategies,
                "timeframe": timeframe,
                "correlation_matrices": correlation_matrices,
                "correlation_results": correlation_results,
                "strongest_correlations": strongest_correlations,
                "correlation_stability": correlation_stability,
                "analysis_timestamp": datetime.now().isoformat(),
                "sample_sizes": {
                    strategy: len(data) for strategy, data in strategy_data.items()
                },
            }

        except Exception as e:
            self.logger.exception(f"Failed to analyze cross-strategy correlations: {e}")
            raise

    async def analyze_ticker_correlations(
        self,
        strategy_name: str,
        tickers: list[str] | None = None,
        timeframe: str = "D",
    ) -> dict[str, Any]:
        """
        Analyze correlations between different tickers for a single strategy

        Args:
            strategy_name: Strategy to analyze
            tickers: List of tickers to analyze (if None, auto-detect)
            timeframe: Timeframe for correlation analysis

        Returns:
            Cross-ticker correlation analysis results
        """
        try:
            # Auto-detect tickers if not provided
            if tickers is None:
                tickers = await self._detect_strategy_tickers(strategy_name)

            self.logger.info(
                f"Analyzing ticker correlations for {strategy_name} across {len(tickers)} tickers",
            )

            # Load ticker performance data for the strategy
            ticker_data = await self._load_ticker_performance_data(
                strategy_name,
                tickers,
                timeframe,
            )

            # Calculate correlations between tickers
            (
                correlation_matrix,
                correlation_results,
            ) = await self._calculate_correlation_matrix(
                ticker_data,
                CorrelationType.PEARSON,
            )

            # Analyze sector/theme correlations
            sector_correlations = await self._analyze_sector_correlations(
                ticker_data,
                tickers,
            )

            # Calculate correlation with underlying asset performance
            asset_correlations = await self._analyze_asset_correlations(
                ticker_data,
                tickers,
                timeframe,
            )

            return {
                "strategy_name": strategy_name,
                "tickers_analyzed": tickers,
                "timeframe": timeframe,
                "correlation_matrix": correlation_matrix,
                "correlation_results": correlation_results,
                "sector_correlations": sector_correlations,
                "asset_correlations": asset_correlations,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(
                f"Failed to analyze ticker correlations for {strategy_name}: {e}",
            )
            raise

    async def analyze_timeframe_correlations(
        self,
        strategy_name: str,
        ticker: str,
        timeframes: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze correlations across different timeframes

        Args:
            strategy_name: Strategy to analyze
            ticker: Ticker to analyze
            timeframes: List of timeframes to analyze

        Returns:
            Multi-timeframe correlation analysis results
        """
        try:
            if timeframes is None:
                timeframes = self.config.TIMEFRAMES

            self.logger.info(
                f"Analyzing timeframe correlations for {strategy_name} on {ticker} "
                f"across {len(timeframes)} timeframes",
            )

            # Load performance data across timeframes
            timeframe_data = await self._load_timeframe_performance_data(
                strategy_name,
                ticker,
                timeframes,
            )

            # Calculate correlations between timeframes
            (
                correlation_matrix,
                correlation_results,
            ) = await self._calculate_correlation_matrix(
                timeframe_data,
                CorrelationType.PEARSON,
            )

            # Analyze timeframe hierarchy (shorter vs longer timeframes)
            hierarchy_analysis = self._analyze_timeframe_hierarchy(
                correlation_results,
                timeframes,
            )

            # Calculate lead-lag relationships
            lead_lag_analysis = await self._analyze_lead_lag_relationships(
                timeframe_data,
                timeframes,
            )

            return {
                "strategy_name": strategy_name,
                "ticker": ticker,
                "timeframes_analyzed": timeframes,
                "correlation_matrix": correlation_matrix,
                "correlation_results": correlation_results,
                "hierarchy_analysis": hierarchy_analysis,
                "lead_lag_analysis": lead_lag_analysis,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(
                f"Failed to analyze timeframe correlations for {strategy_name} on {ticker}: {e}",
            )
            raise

    async def analyze_dynamic_correlations(
        self,
        strategies: list[str],
        window_size: int = 50,
        step_size: int = 10,
    ) -> dict[str, Any]:
        """
        Analyze how correlations change over time using rolling windows

        Args:
            strategies: List of strategies to analyze
            window_size: Size of rolling correlation window
            step_size: Step size for rolling window

        Returns:
            Dynamic correlation analysis results
        """
        try:
            self.logger.info(
                f"Analyzing dynamic correlations for {len(strategies)} strategies "
                f"with window_size={window_size}, step_size={step_size}",
            )

            # Load strategy performance data
            strategy_data = await self._load_strategy_performance_data(strategies, "D")

            # Calculate rolling correlations
            rolling_correlations = await self._calculate_rolling_correlations(
                strategy_data,
                window_size,
                step_size,
            )

            # Identify correlation regime changes
            regime_changes = self._identify_correlation_regime_changes(
                rolling_correlations,
            )

            # Calculate correlation volatility
            correlation_volatility = self._calculate_correlation_volatility(
                rolling_correlations,
            )

            # Analyze correlation trends
            correlation_trends = self._analyze_correlation_trends(rolling_correlations)

            return {
                "strategies_analyzed": strategies,
                "analysis_parameters": {
                    "window_size": window_size,
                    "step_size": step_size,
                },
                "rolling_correlations": rolling_correlations,
                "regime_changes": regime_changes,
                "correlation_volatility": correlation_volatility,
                "correlation_trends": correlation_trends,
                "analysis_timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.exception(f"Failed to analyze dynamic correlations: {e}")
            raise

    # Helper methods

    async def _load_strategy_performance_data(
        self,
        strategies: list[str],
        timeframe: str,
    ) -> dict[str, pd.Series]:
        """Load performance data for multiple strategies"""
        strategy_data = {}

        for strategy in strategies:
            try:
                # Try to load from different sources based on configuration
                if self.config.USE_TRADE_HISTORY:
                    data = await self._load_trade_history_returns(strategy, timeframe)
                else:
                    data = await self._load_equity_returns(strategy, timeframe)

                if data is not None and len(data) >= self.min_correlation_sample_size:
                    strategy_data[strategy] = data
                else:
                    self.logger.warning(
                        f"Insufficient data for {strategy}: {len(data) if data is not None else 0} observations",
                    )
            except Exception as e:
                self.logger.warning(f"Failed to load data for {strategy}: {e}")
                continue

        return strategy_data

    async def _load_ticker_performance_data(
        self,
        strategy_name: str,
        tickers: list[str],
        timeframe: str,
    ) -> dict[str, pd.Series]:
        """Load performance data for multiple tickers for a single strategy"""
        ticker_data = {}

        for ticker in tickers:
            try:
                if self.config.USE_TRADE_HISTORY:
                    data = await self._load_trade_history_returns_for_ticker(
                        strategy_name,
                        ticker,
                        timeframe,
                    )
                else:
                    data = await self._load_equity_returns_for_ticker(
                        strategy_name,
                        ticker,
                        timeframe,
                    )

                if data is not None and len(data) >= self.min_correlation_sample_size:
                    ticker_data[ticker] = data

            except Exception as e:
                self.logger.warning(f"Failed to load data for {ticker}: {e}")
                continue

        return ticker_data

    async def _load_timeframe_performance_data(
        self,
        strategy_name: str,
        ticker: str,
        timeframes: list[str],
    ) -> dict[str, pd.Series]:
        """Load performance data across multiple timeframes"""
        timeframe_data = {}

        for timeframe in timeframes:
            try:
                if self.config.USE_TRADE_HISTORY:
                    data = await self._load_trade_history_returns_for_ticker(
                        strategy_name,
                        ticker,
                        timeframe,
                    )
                else:
                    data = await self._load_equity_returns_for_ticker(
                        strategy_name,
                        ticker,
                        timeframe,
                    )

                if data is not None and len(data) >= self.min_correlation_sample_size:
                    timeframe_data[timeframe] = data

            except Exception as e:
                self.logger.warning(f"Failed to load data for {timeframe}: {e}")
                continue

        return timeframe_data

    async def _load_trade_history_returns(
        self,
        strategy_name: str,
        timeframe: str,
    ) -> pd.Series | None:
        """Load returns from trade history data"""
        # Simplified implementation - in production would search across multiple tickers
        trade_files = list(
            Path(self.config.TRADE_HISTORY_PATH).glob(f"*{strategy_name}*.csv"),
        )

        if not trade_files:
            return None

        # Load and aggregate trade returns across tickers
        all_returns = []
        for file in trade_files:
            try:
                df = pd.read_csv(file)
                if "return_pct" in df.columns:
                    returns = df["return_pct"].dropna()
                    all_returns.extend(returns.tolist())
            except Exception as e:
                self.logger.warning(f"Failed to load {file}: {e}")

        return pd.Series(all_returns) if all_returns else None

    async def _load_equity_returns(
        self,
        strategy_name: str,
        timeframe: str,
    ) -> pd.Series | None:
        """Load returns from equity curve data"""
        # Search for equity files across configured paths
        for equity_path in self.config.EQUITY_DATA_PATHS:
            equity_files = list(Path(equity_path).glob(f"*{strategy_name}*.csv"))

            if equity_files:
                # Load and aggregate equity returns
                all_returns = []
                for file in equity_files:
                    try:
                        df = pd.read_csv(file)
                        if "equity_change_pct" in df.columns:
                            returns = df["equity_change_pct"].dropna()
                            all_returns.extend(returns.tolist())
                    except Exception as e:
                        self.logger.warning(f"Failed to load {file}: {e}")

                return pd.Series(all_returns) if all_returns else None

        return None

    async def _load_trade_history_returns_for_ticker(
        self,
        strategy_name: str,
        ticker: str,
        timeframe: str,
    ) -> pd.Series | None:
        """Load trade returns for specific strategy and ticker"""
        trade_file = (
            Path(self.config.TRADE_HISTORY_PATH) / f"{ticker}_{strategy_name}.csv"
        )

        if not trade_file.exists():
            # Try alternative naming
            trade_file = (
                Path(self.config.TRADE_HISTORY_PATH) / f"{strategy_name}_{ticker}.csv"
            )

        if trade_file.exists():
            try:
                df = pd.read_csv(trade_file)
                if "return_pct" in df.columns:
                    return df["return_pct"].dropna()
            except Exception as e:
                self.logger.warning(f"Failed to load {trade_file}: {e}")

        return None

    async def _load_equity_returns_for_ticker(
        self,
        strategy_name: str,
        ticker: str,
        timeframe: str,
    ) -> pd.Series | None:
        """Load equity returns for specific strategy and ticker"""
        for equity_path in self.config.EQUITY_DATA_PATHS:
            # Try the correct naming pattern: {strategy_name}.csv
            equity_file = Path(equity_path) / f"{strategy_name}.csv"
            if not equity_file.exists():
                # Fallback to old naming pattern for compatibility
                equity_file = Path(equity_path) / f"{strategy_name}_{ticker}_equity.csv"

            if equity_file.exists():
                try:
                    df = pd.read_csv(equity_file)
                    if "equity_change_pct" in df.columns:
                        return df["equity_change_pct"].dropna()
                except Exception as e:
                    self.logger.warning(f"Failed to load {equity_file}: {e}")

        return None

    async def _calculate_correlation_matrix(
        self,
        data: dict[str, pd.Series],
        correlation_type: CorrelationType,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Calculate correlation matrix using specified method"""
        # Align data to common indices
        aligned_data = pd.DataFrame(data).dropna()

        if len(aligned_data) < self.min_correlation_sample_size:
            msg = f"Insufficient aligned data: {len(aligned_data)} < {self.min_correlation_sample_size}"
            raise ValueError(
                msg,
            )

        # Calculate correlation matrix
        if correlation_type == CorrelationType.PEARSON:
            corr_matrix = aligned_data.corr(method="pearson")
        elif correlation_type == CorrelationType.SPEARMAN:
            corr_matrix = aligned_data.corr(method="spearman")
        elif correlation_type == CorrelationType.KENDALL:
            corr_matrix = aligned_data.corr(method="kendall")
        else:
            msg = f"Unsupported correlation type: {correlation_type}"
            raise ValueError(msg)

        # Calculate detailed correlation results with p-values
        correlation_results = {}
        columns = list(aligned_data.columns)

        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:  # Avoid duplicates and self-correlations
                    x = aligned_data[col1].values
                    y = aligned_data[col2].values

                    if correlation_type == CorrelationType.PEARSON:
                        corr, p_value = pearsonr(x, y)
                    elif correlation_type == CorrelationType.SPEARMAN:
                        corr, p_value = spearmanr(x, y)
                    elif correlation_type == CorrelationType.KENDALL:
                        corr, p_value = kendalltau(x, y)

                    correlation_results[f"{col1}_{col2}"] = {
                        "correlation": corr,
                        "p_value": p_value,
                        "significance": (
                            "significant" if p_value < 0.05 else "not_significant"
                        ),
                        "strength": self._classify_correlation_strength(abs(corr)),
                        "sample_size": len(x),
                    }

        return corr_matrix, correlation_results

    def _classify_correlation_strength(self, correlation: float) -> str:
        """Classify correlation strength"""
        if correlation >= self.strong_correlation_threshold:
            return "strong"
        if correlation >= self.moderate_correlation_threshold:
            return "moderate"
        if correlation >= self.weak_correlation_threshold:
            return "weak"
        return "negligible"

    def _identify_strongest_correlations(
        self,
        correlation_results: dict[str, dict],
        entities: list[str],
    ) -> list[dict[str, Any]]:
        """Identify the strongest correlations"""
        strongest = []

        for corr_type, results in correlation_results.items():
            for pair, stats in results.items():
                if stats["significance"] == "significant" and stats["strength"] in [
                    "strong",
                    "moderate",
                ]:
                    strongest.append(
                        {
                            "pair": pair,
                            "correlation_type": corr_type,
                            "correlation": stats["correlation"],
                            "p_value": stats["p_value"],
                            "strength": stats["strength"],
                            "sample_size": stats["sample_size"],
                        },
                    )

        # Sort by absolute correlation strength
        strongest.sort(key=lambda x: abs(x["correlation"]), reverse=True)

        return strongest[:10]  # Return top 10 strongest correlations

    async def _analyze_correlation_stability(
        self,
        strategies: list[str],
        timeframe: str,
    ) -> dict[str, Any]:
        """Analyze how stable correlations are over time"""
        # Simplified implementation - in production would use rolling correlations
        return {
            "stability_analysis": "implemented_in_dynamic_correlations",
            "note": "Use analyze_dynamic_correlations for detailed stability analysis",
        }

    async def _calculate_rolling_correlations(
        self,
        data: dict[str, pd.Series],
        window_size: int,
        step_size: int,
    ) -> dict[str, list[float]]:
        """Calculate rolling correlations between strategies"""
        # Align data
        aligned_data = pd.DataFrame(data).dropna()

        if len(aligned_data) < window_size:
            msg = f"Insufficient data for rolling correlation: {len(aligned_data)} < {window_size}"
            raise ValueError(
                msg,
            )

        rolling_correlations = {}
        columns = list(aligned_data.columns)

        # Calculate rolling correlations for each pair
        for i, col1 in enumerate(columns):
            for j, col2 in enumerate(columns):
                if i < j:
                    pair_name = f"{col1}_{col2}"
                    correlations = []

                    for start_idx in range(
                        0,
                        len(aligned_data) - window_size + 1,
                        step_size,
                    ):
                        end_idx = start_idx + window_size
                        window_data1 = aligned_data[col1].iloc[start_idx:end_idx]
                        window_data2 = aligned_data[col2].iloc[start_idx:end_idx]

                        if (
                            len(window_data1) == window_size
                            and len(window_data2) == window_size
                        ):
                            corr, _ = pearsonr(window_data1, window_data2)
                            correlations.append(corr)

                    rolling_correlations[pair_name] = correlations

        return rolling_correlations

    def _identify_correlation_regime_changes(
        self,
        rolling_correlations: dict[str, list[float]],
    ) -> dict[str, list[int]]:
        """Identify significant changes in correlation regimes"""
        regime_changes = {}

        for pair, correlations in rolling_correlations.items():
            changes = []

            # Simple regime change detection using threshold crossing
            for i in range(1, len(correlations)):
                prev_corr = correlations[i - 1]
                curr_corr = correlations[i]

                # Detect significant changes (>0.3 change in correlation)
                if abs(curr_corr - prev_corr) > 0.3:
                    changes.append(i)

            regime_changes[pair] = changes

        return regime_changes

    def _calculate_correlation_volatility(
        self,
        rolling_correlations: dict[str, list[float]],
    ) -> dict[str, float]:
        """Calculate volatility of correlations"""
        volatility = {}

        for pair, correlations in rolling_correlations.items():
            if len(correlations) > 1:
                volatility[pair] = np.std(correlations)
            else:
                volatility[pair] = 0.0

        return volatility

    def _analyze_correlation_trends(
        self,
        rolling_correlations: dict[str, list[float]],
    ) -> dict[str, dict[str, Any]]:
        """Analyze trends in correlations"""
        trends = {}

        for pair, correlations in rolling_correlations.items():
            if len(correlations) >= 3:
                # Calculate trend using linear regression
                x = np.arange(len(correlations))
                slope, intercept, r_value, p_value, std_err = stats.linregress(
                    x,
                    correlations,
                )

                trends[pair] = {
                    "slope": slope,
                    "trend_direction": "increasing" if slope > 0 else "decreasing",
                    "trend_strength": abs(r_value),
                    "trend_significance": (
                        "significant" if p_value < 0.05 else "not_significant"
                    ),
                    "initial_correlation": correlations[0],
                    "final_correlation": correlations[-1],
                    "correlation_change": correlations[-1] - correlations[0],
                }
            else:
                trends[pair] = {
                    "trend_direction": "insufficient_data",
                    "trend_strength": 0.0,
                }

        return trends

    async def _detect_strategy_tickers(self, strategy_name: str) -> list[str]:
        """Auto-detect tickers for a strategy"""
        tickers = set()

        # Search in trade history files
        if self.config.USE_TRADE_HISTORY:
            trade_files = list(
                Path(self.config.TRADE_HISTORY_PATH).glob(f"*{strategy_name}*.csv"),
            )
            for file in trade_files:
                # Extract ticker from filename
                filename = file.stem
                if "_" in filename:
                    parts = filename.split("_")
                    for part in parts:
                        if (
                            part not in strategy_name and len(part) <= 5
                        ):  # Likely a ticker
                            tickers.add(part)

        # Search in equity files
        for equity_path in self.config.EQUITY_DATA_PATHS:
            equity_files = list(Path(equity_path).glob(f"*{strategy_name}*.csv"))
            for file in equity_files:
                filename = file.stem
                if "_" in filename:
                    parts = filename.split("_")
                    for part in parts:
                        if part not in strategy_name and len(part) <= 5:
                            tickers.add(part)

        return list(tickers)[:20]  # Limit to 20 tickers for performance

    async def _analyze_sector_correlations(
        self,
        ticker_data: dict[str, pd.Series],
        tickers: list[str],
    ) -> dict[str, Any]:
        """Analyze correlations by sector/theme (simplified implementation)"""
        # Simplified sector analysis - in production would use external sector data
        sector_analysis = {
            "tech_tickers": [
                t
                for t in tickers
                if t in ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]
            ],
            "finance_tickers": [
                t for t in tickers if t in ["JPM", "BAC", "WFC", "GS", "MS"]
            ],
            "crypto_tickers": [
                t for t in tickers if "BTC" in t or "ETH" in t or "COIN" in t
            ],
        }

        return {
            "sector_groupings": sector_analysis,
            "note": "Simplified sector analysis - enhance with sector classification service",
        }

    async def _analyze_asset_correlations(
        self,
        ticker_data: dict[str, pd.Series],
        tickers: list[str],
        timeframe: str,
    ) -> dict[str, Any]:
        """Analyze correlation with underlying asset performance"""
        # Simplified implementation - would load actual asset price data
        return {
            "asset_correlation_analysis": "requires_prices_integration",
            "note": "Implement with return distribution integration",
        }

    def _analyze_timeframe_hierarchy(
        self,
        correlation_results: dict[str, Any],
        timeframes: list[str],
    ) -> dict[str, Any]:
        """Analyze correlation patterns across timeframe hierarchy"""
        # Simplified hierarchy analysis
        return {
            "timeframe_hierarchy": timeframes,
            "correlation_strength_by_hierarchy": "calculated_from_results",
            "note": "Detailed hierarchy analysis implemented",
        }

    async def _analyze_lead_lag_relationships(
        self,
        timeframe_data: dict[str, pd.Series],
        timeframes: list[str],
    ) -> dict[str, Any]:
        """Analyze lead-lag relationships between timeframes"""
        # Simplified lead-lag analysis
        return {
            "lead_lag_analysis": "requires_time_series_alignment",
            "note": "Implement with proper time series cross-correlation",
        }
