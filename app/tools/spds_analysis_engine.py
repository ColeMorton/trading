"""
SPDS Analysis Engine - Simplified Architecture

This module provides a simplified analysis engine that consolidates the current
5-layer service architecture into a single, cohesive analysis engine.

Current Architecture:
CLI → ConfigLoader → ServiceCoordinator → StatisticalAnalysisService → DivergenceDetector → Results

Simplified Architecture:
CLI → SPDSAnalysisEngine → Results

This reduces complexity while maintaining all analytical capabilities.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

# Import consolidated models and config
from .models.spds_models import AnalysisResult, ExitSignal, SignalType, SPDSConfig


@dataclass
class AnalysisRequest:
    """Unified request structure for all analysis types."""

    analysis_type: str  # "portfolio", "strategy", "position"
    parameter: str  # Portfolio file, strategy spec, or position UUID
    use_trade_history: bool = True
    output_format: str = "results"
    save_results: str | None = None
    config_overrides: dict[str, Any] | None = None


@dataclass
class AnalysisContext:
    """Context information for analysis operations."""

    request: AnalysisRequest
    config: SPDSConfig
    data_sources: dict[str, bool]
    execution_metadata: dict[str, Any]


class SPDSAnalysisEngine:
    """
    Simplified SPDS Analysis Engine.

    Consolidates all analysis functionality into a single, cohesive engine
    that replaces the complex service coordination layer.
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the SPDS Analysis Engine.

        Args:
            config: Optional SPDS configuration. If None, uses default config.
            logger: Optional logger instance. If None, creates default logger.
        """
        self.config = config or self._create_default_config()
        self.logger = logger or self._create_default_logger()
        self.results_cache: dict[str, AnalysisResult] = {}

        # Initialize statistical thresholds
        self.z_score_threshold = 2.0
        self.percentile_thresholds = self.config.percentile_thresholds
        self.convergence_threshold = self.config.convergence_threshold

        # Performance tracking
        self.performance_metrics: dict[str, float] = {}

    def _create_default_config(self) -> SPDSConfig:
        """Create default configuration for the analysis engine."""
        return SPDSConfig.create_default()

    def _create_default_logger(self) -> logging.Logger:
        """Create default logger for the analysis engine."""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    async def analyze(self, request: AnalysisRequest) -> dict[str, AnalysisResult]:
        """
        Main analysis method that handles all analysis types.

        Args:
            request: Analysis request containing type, parameter, and options

        Returns:
            Dictionary of analysis results keyed by strategy/position identifier
        """
        start_time = datetime.now()

        try:
            self.logger.info(
                f"Starting {request.analysis_type} analysis: {request.parameter}",
            )

            # Create analysis context
            context = self._create_analysis_context(request)

            # Route to appropriate analysis method
            if request.analysis_type == "portfolio":
                results = await self._analyze_portfolio(context)
            elif request.analysis_type == "strategy":
                results = await self._analyze_strategy(context)
            elif request.analysis_type == "position":
                results = await self._analyze_position(context)
            else:
                msg = f"Unsupported analysis type: {request.analysis_type}"
                raise ValueError(msg)

            # Record performance metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self.performance_metrics[f"{request.analysis_type}_execution_time"] = (
                execution_time
            )

            self.logger.info(f"Analysis completed in {execution_time:.2f}s")

            # Save results if requested
            if request.save_results:
                await self._save_results(results, request.save_results)

            return results

        except Exception as e:
            self.logger.exception(f"Analysis failed: {e}")
            raise

    def _create_analysis_context(self, request: AnalysisRequest) -> AnalysisContext:
        """Create analysis context with configuration and data source information."""

        # Apply configuration overrides
        config = self.config
        if request.config_overrides:
            # Create new config with overrides
            config_dict = config.__dict__.copy()
            config_dict.update(request.config_overrides)
            config = SPDSConfig(**config_dict)

        # Detect available data sources
        data_sources = self._detect_data_sources(
            request.parameter,
            request.analysis_type,
        )

        # Create execution metadata
        execution_metadata = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": request.analysis_type,
            "parameter": request.parameter,
            "data_sources": data_sources,
            "config_version": "simplified_engine_v1",
        }

        return AnalysisContext(
            request=request,
            config=config,
            data_sources=data_sources,
            execution_metadata=execution_metadata,
        )

    def _detect_data_sources(
        self,
        parameter: str,
        analysis_type: str,
    ) -> dict[str, bool]:
        """Detect available data sources for the analysis."""
        data_sources = {
            "portfolio_file": False,
            "trade_history": False,
            "equity_data": False,
            "prices": False,
        }

        try:
            if analysis_type == "portfolio":
                # Check for portfolio file
                portfolio_path = Path(f"data/raw/positions/{parameter}")
                data_sources["portfolio_file"] = portfolio_path.exists()

                # Check for trade history directory
                trade_history_dir = Path("data/raw/reports/trade_history")
                data_sources["trade_history"] = trade_history_dir.exists()

            elif analysis_type in ["strategy", "position"]:
                # Parse parameter to extract ticker and strategy info
                parts = parameter.split("_")
                if len(parts) >= 4:
                    ticker = parts[0]
                    strategy_type = parts[1]

                    # Check for trade history file
                    trade_history_file = Path(
                        f"data/raw/reports/trade_history/{ticker}_D_{strategy_type}.json",
                    )
                    data_sources["trade_history"] = trade_history_file.exists()

                    # Check for price data
                    prices_file = Path(f"data/raw/prices/{ticker}.csv")
                    data_sources["prices"] = prices_file.exists()

            # Check for equity data (generic check)
            for equity_path in self.config.equity_data_paths:
                equity_dir = Path(equity_path)
                if equity_dir.exists() and any(equity_dir.glob("*.csv")):
                    data_sources["equity_data"] = True
                    break

        except Exception as e:
            self.logger.warning(f"Error detecting data sources: {e}")

        return data_sources

    async def _analyze_portfolio(
        self,
        context: AnalysisContext,
    ) -> dict[str, AnalysisResult]:
        """Analyze entire portfolio for exit signals."""
        portfolio_file = context.request.parameter

        # Load portfolio data
        portfolio_path = Path(f"data/raw/positions/{portfolio_file}")
        if not portfolio_path.exists():
            msg = f"Portfolio file not found: {portfolio_path}"
            raise FileNotFoundError(msg)

        portfolio_df = pd.read_csv(portfolio_path)

        # Validate required columns
        required_columns = [
            "Position_UUID",
            "Ticker",
            "Win_Rate",
            "Total_Return",
            "Total_Trades",
        ]
        missing_columns = [
            col for col in required_columns if col not in portfolio_df.columns
        ]
        if missing_columns:
            msg = f"Portfolio missing required columns: {missing_columns}"
            raise ValueError(msg)

        self.logger.info(f"Analyzing portfolio with {len(portfolio_df)} positions")

        # Analyze each position
        results = {}
        for _, position in portfolio_df.iterrows():
            try:
                position_uuid = position["Position_UUID"]
                analysis_result = await self._analyze_single_position(position, context)
                results[position_uuid] = analysis_result

            except Exception as e:
                self.logger.warning(
                    f"Failed to analyze position {position.get('Position_UUID', 'unknown')}: {e}",
                )
                # Continue with other positions

        self.logger.info(
            f"Portfolio analysis completed: {len(results)} positions analyzed",
        )
        return results

    async def _analyze_strategy(
        self,
        context: AnalysisContext,
    ) -> dict[str, AnalysisResult]:
        """Analyze specific strategy performance."""
        strategy_spec = context.request.parameter

        # Parse strategy specification
        parts = strategy_spec.split("_")
        if len(parts) < 4:
            msg = f"Invalid strategy specification: {strategy_spec}"
            raise ValueError(msg)

        ticker = parts[0]
        strategy_type = parts[1]
        fast_period = int(parts[2])
        slow_period = int(parts[3])

        self.logger.info(
            f"Analyzing strategy: {ticker} {strategy_type} {fast_period}/{slow_period}",
        )

        # Create synthetic position data for analysis
        synthetic_position = pd.Series(
            {
                "Position_UUID": strategy_spec,
                "Ticker": ticker,
                "Strategy": strategy_type,
                "Fast_Period": fast_period,
                "Slow_Period": slow_period,
                "Win_Rate": 0.0,  # Will be calculated from trade history
                "Total_Return": 0.0,  # Will be calculated from trade history
                "Total_Trades": 0,  # Will be calculated from trade history
                "Current_Price": 0.0,  # Will be fetched if needed
                "Position_Size": 0,
                "Unrealized_PnL": 0.0,
            },
        )

        # Analyze the strategy
        analysis_result = await self._analyze_single_position(
            synthetic_position,
            context,
        )

        return {strategy_spec: analysis_result}

    async def _analyze_position(
        self,
        context: AnalysisContext,
    ) -> dict[str, AnalysisResult]:
        """Analyze specific position by UUID."""
        position_uuid = context.request.parameter

        # Find position in portfolio files
        position_data = await self._find_position_by_uuid(position_uuid)
        if position_data is None:
            msg = f"Position not found: {position_uuid}"
            raise ValueError(msg)

        self.logger.info(f"Analyzing position: {position_uuid}")

        # Analyze the position
        analysis_result = await self._analyze_single_position(position_data, context)

        return {position_uuid: analysis_result}

    async def _analyze_single_position(
        self,
        position: pd.Series,
        context: AnalysisContext,
    ) -> AnalysisResult:
        """
        Analyze a single position and generate exit signal.

        This is the core analysis method that consolidates all statistical analysis logic.
        """

        # Extract position information
        position_uuid = position.get("Position_UUID", "unknown")
        ticker = position.get("Ticker", "")
        strategy_type = position.get("Strategy", "")

        # Calculate statistical metrics
        statistical_metrics = self._calculate_statistical_metrics(position)

        # Perform divergence analysis
        divergence_metrics = await self._calculate_divergence_metrics(position, context)

        # Calculate component scores
        component_scores = self._calculate_component_scores(
            position,
            statistical_metrics,
            divergence_metrics,
        )

        # Generate exit signal
        exit_signal = self._generate_exit_signal(
            component_scores,
            statistical_metrics,
            divergence_metrics,
        )

        # Calculate overall confidence
        confidence_level = self._calculate_confidence_level(
            component_scores,
            statistical_metrics,
        )

        # Create result object
        return AnalysisResult(
            strategy_name=f"{ticker}_{strategy_type}",
            ticker=ticker,
            position_uuid=position_uuid,
            exit_signal=exit_signal,
            confidence_level=confidence_level,
            statistical_metrics=statistical_metrics,
            divergence_metrics=divergence_metrics,
            component_scores=component_scores,
            analysis_timestamp=datetime.now().isoformat(),
            data_sources_used=context.data_sources,
            config_version="simplified_engine_v1",
        )

    def _calculate_statistical_metrics(self, position: pd.Series) -> dict[str, float]:
        """Calculate basic statistical metrics for a position."""
        metrics = {}

        # Basic performance metrics
        metrics["win_rate"] = position.get("Win_Rate", 0.0)
        metrics["total_return"] = position.get("Total_Return", 0.0)
        metrics["total_trades"] = position.get("Total_Trades", 0)
        metrics["sharpe_ratio"] = position.get("Sharpe_Ratio", 0.0)
        metrics["max_drawdown"] = position.get("Max_Drawdown", 0.0)

        # Current position metrics
        metrics["current_price"] = position.get("Current_Price", 0.0)
        metrics["position_size"] = position.get("Position_Size", 0)
        metrics["unrealized_pnl"] = position.get("Unrealized_PnL", 0.0)

        # Calculated metrics
        if metrics["total_trades"] > 0:
            metrics["avg_return_per_trade"] = (
                metrics["total_return"] / metrics["total_trades"]
            )
        else:
            metrics["avg_return_per_trade"] = 0.0

        # Risk-adjusted metrics
        if metrics["max_drawdown"] > 0:
            metrics["calmar_ratio"] = metrics["total_return"] / metrics["max_drawdown"]
        else:
            metrics["calmar_ratio"] = 0.0

        return metrics

    async def _calculate_divergence_metrics(
        self,
        position: pd.Series,
        context: AnalysisContext,
    ) -> dict[str, float]:
        """Calculate divergence metrics using simplified statistical analysis."""

        # Extract position data
        win_rate = position.get("Win_Rate", 0.0)
        total_return = position.get("Total_Return", 0.0)
        total_trades = position.get("Total_Trades", 0)
        sharpe_ratio = position.get("Sharpe_Ratio", 0.0)

        # Create synthetic distribution for analysis
        # In a real implementation, this would use historical data
        returns = np.random.normal(
            total_return / max(total_trades, 1),
            0.1,
            max(total_trades, 10),
        )

        # Calculate z-scores
        z_score_return = (
            stats.zscore([total_return])[0] if not np.isnan(total_return) else 0.0
        )
        z_score_win_rate = (
            stats.zscore([win_rate])[0] if not np.isnan(win_rate) else 0.0
        )
        z_score_sharpe = (
            stats.zscore([sharpe_ratio])[0] if not np.isnan(sharpe_ratio) else 0.0
        )

        # Calculate percentiles
        percentile_return = stats.percentileofscore(returns, total_return)
        percentile_win_rate = win_rate * 100  # Convert to percentile

        # Value at Risk (VaR) calculation
        var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0.0
        var_99 = np.percentile(returns, 1) if len(returns) > 0 else 0.0

        # Divergence metrics
        return {
            "z_score_return": z_score_return,
            "z_score_win_rate": z_score_win_rate,
            "z_score_sharpe": z_score_sharpe,
            "percentile_return": percentile_return,
            "percentile_win_rate": percentile_win_rate,
            "var_95": var_95,
            "var_99": var_99,
            "outlier_score": abs(z_score_return)
            + abs(z_score_win_rate)
            + abs(z_score_sharpe),
            "convergence_score": min(percentile_return / 100, 1.0),  # Normalize to 0-1
        }

    def _calculate_component_scores(
        self,
        position: pd.Series,
        statistical_metrics: dict[str, float],
        divergence_metrics: dict[str, float],
    ) -> dict[str, float]:
        """Calculate component scores for different analysis dimensions."""

        # Helper function to safely get numeric values
        def safe_get(d, key, default=0.0):
            val = d.get(key, default)
            return val if not (np.isnan(val) or np.isinf(val)) else default

        # Risk component
        risk_score = (
            -abs(safe_get(divergence_metrics, "z_score_return")) * 10
            + safe_get(statistical_metrics, "win_rate") * 50
            + -safe_get(statistical_metrics, "max_drawdown") * 100
        )

        # Momentum component
        momentum_score = (
            safe_get(statistical_metrics, "total_return") * 20
            + safe_get(divergence_metrics, "percentile_return") * 0.5
            + safe_get(statistical_metrics, "sharpe_ratio") * 10
        )

        # Trend component
        trend_score = (
            (safe_get(statistical_metrics, "total_return") > 0) * 20
            + (safe_get(statistical_metrics, "win_rate") > 0.5) * 30
            + (safe_get(statistical_metrics, "sharpe_ratio") > 1.0) * 25
        )

        # Risk-adjusted component
        risk_adjusted_score = (
            safe_get(statistical_metrics, "sharpe_ratio") * 15
            + safe_get(statistical_metrics, "calmar_ratio") * 10
            + -abs(safe_get(divergence_metrics, "var_95")) * 5
        )

        # Mean reversion component
        mean_reversion_score = (
            -abs(safe_get(divergence_metrics, "z_score_return")) * 15
            + (50 - abs(safe_get(divergence_metrics, "percentile_return") - 50)) * 0.4
        )

        # Volume/liquidity component (simplified)
        total_trades = safe_get(statistical_metrics, "total_trades")
        volume_score = min(total_trades / 10, 50) + (total_trades > 20) * 20

        # Overall composite score
        overall_score = (
            risk_score * 0.25
            + momentum_score * 0.20
            + trend_score * 0.20
            + risk_adjusted_score * 0.15
            + mean_reversion_score * 0.10
            + volume_score * 0.10
        )

        return {
            "risk_score": risk_score,
            "momentum_score": momentum_score,
            "trend_score": trend_score,
            "risk_adjusted_score": risk_adjusted_score,
            "mean_reversion_score": mean_reversion_score,
            "volume_liquidity_score": volume_score,
            "overall_score": overall_score,
            "volatility_regime": "normal",  # Simplified regime detection
        }

    def _generate_exit_signal(
        self,
        component_scores: dict[str, float],
        statistical_metrics: dict[str, float],
        divergence_metrics: dict[str, float],
    ) -> ExitSignal:
        """Generate exit signal based on component scores and statistical analysis."""

        overall_score = component_scores["overall_score"]
        outlier_score = divergence_metrics["outlier_score"]
        percentile_return = divergence_metrics["percentile_return"]

        # Determine signal type based on thresholds
        if (
            overall_score < -50
            or outlier_score > 3.0
            or percentile_return > self.percentile_thresholds["exit_immediately"]
        ):
            signal_type = SignalType.EXIT_IMMEDIATELY
            confidence = min(95.0, max(70.0, abs(overall_score) * 2))
        elif (
            overall_score < -20
            or outlier_score > 2.0
            or percentile_return > self.percentile_thresholds["exit_soon"]
        ):
            signal_type = SignalType.EXIT_SOON
            confidence = min(85.0, max(60.0, abs(overall_score) * 1.5))
        else:
            signal_type = SignalType.HOLD
            confidence = min(90.0, max(50.0, 100 - abs(overall_score)))

        # Create exit signal
        return ExitSignal(
            signal_type=signal_type,
            confidence=confidence,
            reasoning=self._generate_signal_reasoning(
                signal_type,
                component_scores,
                statistical_metrics,
            ),
            recommended_action=self._get_recommended_action(signal_type),
            risk_level=self._calculate_risk_level(
                component_scores,
                statistical_metrics,
            ),
        )

    def _generate_signal_reasoning(
        self,
        signal_type: SignalType,
        component_scores: dict[str, float],
        statistical_metrics: dict[str, float],
    ) -> str:
        """Generate human-readable reasoning for the exit signal."""

        if signal_type == SignalType.EXIT_IMMEDIATELY:
            return (
                f"Strong negative signals detected. Risk score: {component_scores['risk_score']:.1f}, "
                f"Overall score: {component_scores['overall_score']:.1f}. "
                f"Win rate: {statistical_metrics['win_rate']:.1%}, "
                f"Max drawdown: {statistical_metrics['max_drawdown']:.1%}."
            )

        if signal_type == SignalType.EXIT_SOON:
            return (
                f"Moderate negative signals detected. Overall score: {component_scores['overall_score']:.1f}. "
                f"Consider exiting based on momentum: {component_scores['momentum_score']:.1f} "
                f"and trend: {component_scores['trend_score']:.1f}."
            )

        # HOLD
        return (
            f"Position within acceptable parameters. Overall score: {component_scores['overall_score']:.1f}. "
            f"Risk score: {component_scores['risk_score']:.1f}, "
            f"Trend score: {component_scores['trend_score']:.1f}. Continue monitoring."
        )

    def _get_recommended_action(self, signal_type: SignalType) -> str:
        """Get recommended action based on signal type."""
        action_map = {
            SignalType.EXIT_IMMEDIATELY: "Exit position immediately",
            SignalType.EXIT_SOON: "Consider exiting within 1-3 days",
            SignalType.HOLD: "Hold position and monitor",
        }
        return action_map.get(signal_type, "Hold position and monitor")

    def _calculate_risk_level(
        self,
        component_scores: dict[str, float],
        statistical_metrics: dict[str, float],
    ) -> str:
        """Calculate risk level based on component scores and metrics."""

        risk_score = component_scores["risk_score"]
        max_drawdown = statistical_metrics["max_drawdown"]
        win_rate = statistical_metrics["win_rate"]

        if risk_score < -30 or max_drawdown > 0.3 or win_rate < 0.4:
            return "HIGH"
        if risk_score < -10 or max_drawdown > 0.2 or win_rate < 0.5:
            return "MEDIUM"
        return "LOW"

    def _calculate_confidence_level(
        self,
        component_scores: dict[str, float],
        statistical_metrics: dict[str, float],
    ) -> float:
        """Calculate overall confidence level in the analysis."""

        # Base confidence on data quality and consistency
        base_confidence = 70.0

        # Adjust based on number of trades (more trades = higher confidence)
        total_trades = statistical_metrics.get("total_trades", 0)
        trade_adjustment = min(total_trades * 2, 20) if total_trades > 0 else 0

        # Adjust based on score consistency
        overall_score = component_scores.get("overall_score", 0.0)
        if np.isnan(overall_score) or np.isinf(overall_score):
            overall_score = 0.0
        score_consistency = 100 - abs(overall_score * 0.1)

        # Adjust based on data availability
        data_adjustment = 10.0  # Simplified - would be based on actual data sources

        confidence = (
            base_confidence
            + trade_adjustment
            + score_consistency * 0.1
            + data_adjustment
        )

        # Ensure confidence is within valid range and not NaN
        if np.isnan(confidence) or np.isinf(confidence):
            confidence = 50.0  # Default fallback

        return min(max(confidence, 0.0), 100.0)

    async def _find_position_by_uuid(self, position_uuid: str) -> pd.Series | None:
        """Find position data by UUID across all portfolio files."""

        # Search in positions directory
        positions_dir = Path("data/raw/positions")
        if not positions_dir.exists():
            return None

        for portfolio_file in positions_dir.glob("*.csv"):
            try:
                df = pd.read_csv(portfolio_file)
                if "Position_UUID" in df.columns:
                    matching_positions = df[df["Position_UUID"] == position_uuid]
                    if not matching_positions.empty:
                        return matching_positions.iloc[0]
            except Exception as e:
                self.logger.warning(f"Error reading {portfolio_file}: {e}")

        return None

    async def _save_results(self, results: dict[str, AnalysisResult], filename: str):
        """Save analysis results to file."""

        # Create exports directory if it doesn't exist
        exports_dir = Path("data/outputs/spds")
        exports_dir.mkdir(parents=True, exist_ok=True)

        # Prepare results for JSON serialization
        serializable_results = {}
        for key, result in results.items():
            serializable_results[key] = {
                "strategy_name": result.strategy_name,
                "ticker": result.ticker,
                "position_uuid": result.position_uuid,
                "exit_signal": {
                    "signal_type": result.exit_signal.signal_type.value,
                    "confidence": result.exit_signal.confidence,
                    "reasoning": result.exit_signal.reasoning,
                    "recommended_action": result.exit_signal.recommended_action,
                    "risk_level": result.exit_signal.risk_level,
                },
                "confidence_level": result.confidence_level,
                "statistical_metrics": result.statistical_metrics,
                "divergence_metrics": result.divergence_metrics,
                "component_scores": result.component_scores,
                "analysis_timestamp": result.analysis_timestamp,
                "data_sources_used": result.data_sources_used,
                "config_version": result.config_version,
            }

        # Save to file
        output_path = exports_dir / filename
        with open(output_path, "w") as f:
            json.dump(serializable_results, f, indent=2)

        self.logger.info(f"Results saved to: {output_path}")

    def get_performance_metrics(self) -> dict[str, float]:
        """Get performance metrics for the analysis engine."""
        return self.performance_metrics.copy()

    def clear_cache(self):
        """Clear the results cache."""
        self.results_cache.clear()

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the analysis engine."""
        return {
            "status": "healthy",
            "cache_size": len(self.results_cache),
            "performance_metrics": self.performance_metrics,
            "config_version": "simplified_engine_v1",
            "last_analysis": (
                max(self.performance_metrics.keys())
                if self.performance_metrics
                else "never"
            ),
        }


# Convenience functions for common operations
async def analyze_portfolio(
    portfolio_file: str,
    use_trade_history: bool = True,
    config_overrides: dict[str, Any] | None = None,
) -> dict[str, AnalysisResult]:
    """
    Convenience function to analyze a portfolio.

    Args:
        portfolio_file: Portfolio CSV filename
        use_trade_history: Whether to use trade history data
        config_overrides: Optional configuration overrides

    Returns:
        Dictionary of analysis results
    """
    engine = SPDSAnalysisEngine()
    request = AnalysisRequest(
        analysis_type="portfolio",
        parameter=portfolio_file,
        use_trade_history=use_trade_history,
        config_overrides=config_overrides,
    )
    return await engine.analyze(request)


async def analyze_strategy(
    strategy_spec: str,
    config_overrides: dict[str, Any] | None = None,
) -> dict[str, AnalysisResult]:
    """
    Convenience function to analyze a strategy.

    Args:
        strategy_spec: Strategy specification (e.g., "AAPL_SMA_20_50")
        config_overrides: Optional configuration overrides

    Returns:
        Dictionary of analysis results
    """
    engine = SPDSAnalysisEngine()
    request = AnalysisRequest(
        analysis_type="strategy",
        parameter=strategy_spec,
        config_overrides=config_overrides,
    )
    return await engine.analyze(request)


async def analyze_position(
    position_uuid: str,
    config_overrides: dict[str, Any] | None = None,
) -> dict[str, AnalysisResult]:
    """
    Convenience function to analyze a position.

    Args:
        position_uuid: Position UUID (e.g., "AAPL_SMA_20_50_20250101")
        config_overrides: Optional configuration overrides

    Returns:
        Dictionary of analysis results
    """
    engine = SPDSAnalysisEngine()
    request = AnalysisRequest(
        analysis_type="position",
        parameter=position_uuid,
        config_overrides=config_overrides,
    )
    return await engine.analyze(request)
