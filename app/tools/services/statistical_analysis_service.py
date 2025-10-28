"""
Statistical Analysis Service

Core service for the Statistical Performance Divergence System (SPDS).
Orchestrates dual-layer statistical analysis, divergence detection, and
probabilistic exit signal generation following existing service patterns.
"""

import asyncio
import contextlib
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..analysis.bootstrap_validator import BootstrapValidator
from ..analysis.divergence_detector import DivergenceDetector
from ..analysis.trade_history_analyzer import TradeHistoryAnalyzer
from ..config.statistical_analysis_config import SPDSConfig, get_spds_config
from ..models.statistical_analysis_models import (
    AssetDistributionAnalysis,
    BootstrapResults,
    ConfidenceLevel,
    DataSource,
    DivergenceMetrics,
    DualLayerConvergence,
    DualSourceConvergence,
    EquityAnalysis,
    PercentileMetrics,
    ProbabilisticExitSignal,
    SignalType,
    StatisticalAnalysisResult,
    StatisticalMetrics,
    StrategyDistributionAnalysis,
    TradeHistoryAnalysis,
    TradeHistoryMetrics,
    VaRMetrics,
)
from ..processing.memory_optimizer import get_memory_optimizer
from .strategy_data_coordinator import (
    DataCoordinationConfig,
    StrategyDataCoordinator,
    StrategyDataCoordinatorError,
)


class StatisticalAnalysisService:
    """
    Core statistical analysis service following existing service patterns.

    Provides dual-layer statistical analysis with asset distribution and
    strategy/trade history analysis for divergence detection and exit
    signal generation.
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
        enable_memory_optimization: bool = True,
        data_coordinator: StrategyDataCoordinator | None = None,
        use_coordinator: bool = True,
    ):
        """
        Initialize the Statistical Analysis Service with central data coordination

        Args:
            config: SPDS configuration instance
            logger: Logger instance for service operations
            enable_memory_optimization: Enable memory optimization features
            data_coordinator: Central data coordinator instance
            use_coordinator: Whether to use coordinator for data loading (recommended)
        """
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)
        self.enable_memory_optimization = enable_memory_optimization
        self.use_coordinator = use_coordinator

        # Initialize central data coordinator
        if use_coordinator:
            if data_coordinator:
                self.data_coordinator = data_coordinator
            else:
                # Create new coordinator with optimized configuration
                coordinator_config = DataCoordinationConfig(
                    enable_validation=True,
                    enable_auto_refresh=True,
                    max_data_age_minutes=30,
                    enable_memory_optimization=enable_memory_optimization,
                    concurrent_loading=True,
                )
                self.data_coordinator = StrategyDataCoordinator(
                    logger=self.logger, config=coordinator_config
                )
            self.logger.info(
                "StatisticalAnalysisService initialized with central data coordinator"
            )
        else:
            self.data_coordinator = None
            self.logger.warning(
                "StatisticalAnalysisService initialized without data coordinator (legacy mode)"
            )

        # Initialize components
        self.divergence_detector = DivergenceDetector(
            config=self.config, logger=self.logger
        )
        self.trade_history_analyzer = TradeHistoryAnalyzer(
            config=self.config, logger=self.logger
        )
        self.bootstrap_validator = BootstrapValidator(
            config=self.config, logger=self.logger
        )

        # Memory optimization
        if self.enable_memory_optimization:
            self.memory_optimizer = get_memory_optimizer()
        else:
            self.memory_optimizer = None

        # Position context cache
        self._position_cache: dict[str, dict[str, dict[str, Any]]] = {}
        self._position_cache_timestamp: float | None = None

        # Service metrics
        self.metrics = {
            "analyses_performed": 0,
            "dual_layer_analyses": 0,
            "trade_history_analyses": 0,
            "position_aware_analyses": 0,
            "bootstrap_validations": 0,
            "high_confidence_signals": 0,
            "total_processing_time": 0.0,
            "coordinator_cache_hits": 0,
            "coordinator_data_loads": 0,
        }

        self.logger.info(
            f"StatisticalAnalysisService initialized with "
            f"USE_TRADE_HISTORY={self.config.USE_TRADE_HISTORY}, "
            f"memory_optimization={self.enable_memory_optimization}, "
            f"coordinator_enabled={self.use_coordinator}"
        )

    # =================== POSITION CONTEXT INTEGRATION ===================

    async def _load_position_context(
        self, portfolio_name: str
    ) -> dict[str, dict[str, Any]]:
        """
        Load position context data from positions/{portfolio}.csv

        Args:
            portfolio_name: Portfolio filename (e.g., "protected.csv")

        Returns:
            Dictionary mapping position UUIDs to position data
        """
        try:
            # Cache check - refresh every 5 minutes
            current_time = datetime.now()
            if (
                self._position_cache_timestamp
                and (current_time - self._position_cache_timestamp).seconds < 300
                and portfolio_name in self._position_cache
            ):
                self.logger.debug(f"Using cached position data for {portfolio_name}")
                return self._position_cache[portfolio_name]

            # Determine position file path - ensure .csv extension
            if not portfolio_name.endswith(".csv"):
                portfolio_name = f"{portfolio_name}.csv"
            position_file_path = Path("data/raw/positions") / portfolio_name

            if not position_file_path.exists():
                self.logger.warning(f"Position file not found: {position_file_path}")
                return {}

            # Load position data
            self.logger.info(f"Loading position context from: {position_file_path}")

            if self.enable_memory_optimization and self.memory_optimizer:
                import polars as pl

                try:
                    # Use Polars for efficient loading
                    df = pl.read_csv(str(position_file_path))
                    position_data = df.to_pandas().to_dict("records")
                except Exception:
                    # Fallback to pandas
                    import pandas as pd

                    df = pd.read_csv(position_file_path)
                    position_data = df.to_dict("records")
            else:
                # Standard pandas loading
                import pandas as pd

                df = pd.read_csv(position_file_path)
                position_data = df.to_dict("records")

            # Create UUID mapping
            position_map = {}
            for pos in position_data:
                if "Position_UUID" in pos:
                    position_map[pos["Position_UUID"]] = pos
                else:
                    # Fallback: create UUID from strategy components
                    strategy_uuid = self._create_strategy_uuid_from_position(pos)
                    if strategy_uuid:
                        position_map[strategy_uuid] = pos

            # Cache the results
            self._position_cache[portfolio_name] = position_map
            self._position_cache_timestamp = current_time

            self.logger.info(
                f"Loaded {len(position_map)} positions for {portfolio_name}"
            )
            return position_map

        except Exception as e:
            self.logger.error(
                f"Error loading position context for {portfolio_name}: {e}"
            )
            return {}

    def _create_strategy_uuid_from_position(
        self, position_data: dict[str, Any]
    ) -> str | None:
        """Create strategy UUID from position components"""
        try:
            ticker = position_data.get("Ticker", "")
            strategy_type = position_data.get("Strategy_Type", "")
            fast_period = position_data.get("Fast_Period", "")
            slow_period = position_data.get("Slow_Period", "")
            signal_period = position_data.get("Signal_Period", 0)

            if signal_period and signal_period != 0:
                return f"{ticker}_{strategy_type}_{fast_period}_{slow_period}_{signal_period}"
            return f"{ticker}_{strategy_type}_{fast_period}_{slow_period}"
        except Exception:
            return None

    def _find_matching_position(
        self, strategy_name: str, position_map: dict[str, dict[str, Any]]
    ) -> dict[str, Any] | None:
        """
        Find matching position data for a given strategy name

        Args:
            strategy_name: Strategy identifier (e.g., "FFIV_SMA_14_45")
            position_map: Position data mapping

        Returns:
            Position data if found, None otherwise
        """
        try:
            # Direct UUID match
            if strategy_name in position_map:
                return position_map[strategy_name]

            # Pattern matching for variations
            for position_uuid, position_data in position_map.items():
                if strategy_name in position_uuid or position_uuid.startswith(
                    strategy_name
                ):
                    return position_data

            # Component-based matching
            strategy_parts = strategy_name.split("_")
            if len(strategy_parts) >= 4:  # TICKER_TYPE_SHORT_LONG
                ticker = strategy_parts[0]
                for position_uuid, position_data in position_map.items():
                    if position_data.get("Ticker") == ticker and strategy_name.replace(
                        "_", ""
                    ) in position_uuid.replace("_", ""):
                        return position_data

            return None

        except Exception as e:
            self.logger.error(f"Error finding position match for {strategy_name}: {e}")
            return None

    def _is_position_open(self, position_data: dict[str, Any] | None) -> bool:
        """Check if position is currently open"""
        if not position_data:
            return False
        return position_data.get("Status", "").upper() == "OPEN"

    def _get_position_metrics(self, position_data: dict[str, Any]) -> dict[str, Any]:
        """Extract key position metrics for analysis"""
        try:
            return {
                "status": position_data.get("Status", ""),
                "days_since_entry": position_data.get("Days_Since_Entry", 0),
                "current_unrealized_pnl": position_data.get(
                    "Current_Unrealized_PnL", 0.0
                ),
                "mfe": position_data.get("Max_Favourable_Excursion", 0.0),
                "mae": position_data.get("Max_Adverse_Excursion", 0.0),
                "mfe_mae_ratio": position_data.get("MFE_MAE_Ratio", 0.0),
                "trade_quality": position_data.get("Trade_Quality", ""),
                "excursion_status": position_data.get("Current_Excursion_Status", ""),
                "entry_price": position_data.get("Avg_Entry_Price", 0.0),
                "entry_timestamp": position_data.get("Entry_Timestamp", ""),
            }
        except Exception as e:
            self.logger.error(f"Error extracting position metrics: {e}")
            return {}

    async def _generate_position_aware_signal(
        self,
        strategy_analysis: "StrategyDistributionAnalysis",
        asset_analysis: "AssetDistributionAnalysis",
        dual_layer_convergence: "DualLayerConvergence",
        asset_divergence: "DivergenceMetrics",
        strategy_divergence: "DivergenceMetrics",
        position_data: dict[str, Any] | None,
        component_scores: dict[str, Any] | None = None,
    ) -> "ProbabilisticExitSignal":
        """
        Generate position-aware signals based on whether position is open or represents new opportunity

        Args:
            strategy_analysis: Strategy performance analysis
            asset_analysis: Asset distribution analysis
            dual_layer_convergence: Convergence between analysis layers
            asset_divergence: Asset divergence metrics
            strategy_divergence: Strategy divergence metrics
            position_data: Position context data (if any)
            component_scores: Component scores for override logic

        Returns:
            Position-appropriate signal
        """
        try:
            if position_data and self._is_position_open(position_data):
                # Generate exit signals for open positions
                self.metrics["position_aware_analyses"] += 1
                return await self._generate_exit_signals_for_open_position(
                    strategy_analysis,
                    asset_analysis,
                    dual_layer_convergence,
                    asset_divergence,
                    strategy_divergence,
                    position_data,
                    component_scores,
                )
            # Generate entry signals for new opportunities (existing logic)
            return await self._generate_exit_signal(
                asset_analysis,
                strategy_analysis,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                position_data,
                component_scores,
            )

        except Exception as e:
            self.logger.error(f"Error in position-aware signal generation: {e}")
            # Fallback to existing signal generation
            return await self._generate_exit_signal(
                asset_analysis,
                strategy_analysis,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                position_data,
                component_scores,
            )

    async def _generate_exit_signals_for_open_position(
        self,
        strategy_analysis: "StrategyDistributionAnalysis",
        asset_analysis: "AssetDistributionAnalysis",
        dual_layer_convergence: "DualLayerConvergence",
        asset_divergence: "DivergenceMetrics",
        strategy_divergence: "DivergenceMetrics",
        position_data: dict[str, Any],
        component_scores: dict[str, Any] | None = None,
    ) -> "ProbabilisticExitSignal":
        """
        Generate exit signals for open positions using position-specific metrics

        Args:
            strategy_analysis: Strategy performance analysis
            asset_analysis: Asset distribution analysis
            dual_layer_convergence: Layer convergence metrics
            asset_divergence: Asset divergence metrics
            strategy_divergence: Strategy divergence metrics
            position_data: Open position data with MFE/MAE metrics
            component_scores: Component scores for analysis

        Returns:
            Exit-focused signal for open position
        """
        try:
            position_metrics = self._get_position_metrics(position_data)

            # Analyze position-specific exit factors
            self._analyze_position_exit_factors(position_metrics)

            # Calculate position-aware signal strength
            primary_strength = self._calculate_position_exit_strength(
                position_metrics,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
            )

            # Use actual position performance for secondary strength
            secondary_strength = self._calculate_position_performance_strength(
                position_metrics
            )

            # Asset analysis for tertiary strength (market context)
            tertiary_strength = self._calculate_tertiary_signal_strength(
                asset_analysis, strategy_analysis
            )

            # Enhanced position-specific contributions
            asset_layer_contribution = self._calculate_asset_layer_contribution(
                asset_analysis, asset_divergence
            )

            # Use actual position metrics instead of theoretical
            position_performance_contribution = (
                self._calculate_position_performance_contribution(position_metrics)
            )

            # Determine signal type based on position context
            signal_type = self._determine_position_exit_signal_type(
                position_metrics,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                component_scores,
            )

            # Calculate position-aware confidence
            confidence = self._calculate_position_exit_confidence(
                position_metrics,
                primary_strength,
                secondary_strength,
                tertiary_strength,
                dual_layer_convergence,
            )

            # Generate position-aware exit signal
            from ..models.statistical_analysis_models import (
                ConfidenceLevel,
                ProbabilisticExitSignal,
            )

            # Calculate missing required fields
            sample_size = position_metrics.get("days_since_entry", 30)
            confidence_level = (
                ConfidenceLevel.HIGH
                if sample_size >= 30
                else (
                    ConfidenceLevel.MEDIUM if sample_size >= 15 else ConfidenceLevel.LOW
                )
            )

            return ProbabilisticExitSignal(
                signal_type=signal_type,
                confidence=confidence * 100,  # Convert to percentage
                primary_signal_strength=primary_strength,
                secondary_signal_strength=secondary_strength,
                tertiary_signal_strength=tertiary_strength,
                asset_layer_contribution=asset_layer_contribution,
                trade_history_contribution=position_performance_contribution,
                equity_curve_contribution=position_performance_contribution
                * 0.8,  # Derived
                dual_layer_score=dual_layer_convergence.convergence_score,
                timeframe_score=0.8,  # Position analysis uses single timeframe
                risk_adjusted_score=tertiary_strength,
                source_reliability_score=0.9,  # High reliability for position data
                sample_size_confidence=min(sample_size / 30.0, 1.0),
                statistical_validity=confidence_level,
                combined_source_confidence=position_performance_contribution,
                expected_upside=self._estimate_position_exit_upside(
                    position_metrics, signal_type
                ),
                expected_timeline=self._estimate_position_exit_timeline(
                    position_metrics, signal_type
                ),
                risk_warning=self._generate_position_risk_warning(
                    position_metrics, signal_type
                ),
            )

        except Exception as e:
            self.logger.error(f"Error generating exit signals for open position: {e}")
            # Fallback to standard signal generation
            return await self._generate_exit_signal(
                asset_analysis,
                strategy_analysis,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                position_data,
                component_scores,
            )

    async def _generate_entry_signals_for_new_strategy(
        self,
        strategy_analysis: "StrategyDistributionAnalysis",
        asset_analysis: "AssetDistributionAnalysis",
        dual_layer_convergence: "DualLayerConvergence",
        asset_divergence: "DivergenceMetrics",
        strategy_divergence: "DivergenceMetrics",
        component_scores: dict[str, Any] | None = None,
    ) -> "ProbabilisticExitSignal":
        """
        Generate entry signals for new strategy opportunities (wrapper around existing logic)

        This maintains the existing signal generation for strategies without open positions
        """
        try:
            return await self._generate_exit_signal(
                asset_analysis,
                strategy_analysis,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                None,
                component_scores,
            )
        except Exception as e:
            self.logger.error(f"Error generating entry signals for new strategy: {e}")
            raise

    # =================== END POSITION CONTEXT INTEGRATION ===================

    async def analyze_position(
        self,
        strategy_name: str,
        ticker: str,
        current_position_data: dict[str, Any] | None = None,
        use_trade_history: bool | None = None,
    ) -> StatisticalAnalysisResult:
        """
        Perform comprehensive statistical analysis for a position

        Args:
            strategy_name: Strategy identifier
            ticker: Asset ticker symbol
            current_position_data: Current position data (if any)
            use_trade_history: Override USE_TRADE_HISTORY config

        Returns:
            Complete statistical analysis result
        """
        start_time = datetime.now()

        try:
            # Determine data source configuration
            use_trade_history = (
                use_trade_history
                if use_trade_history is not None
                else self.config.USE_TRADE_HISTORY
            )

            self.logger.info(
                f"Starting analysis for {strategy_name} on {ticker}, use_trade_history={use_trade_history}"
            )

            # Layer 1: Asset distribution analysis
            asset_analysis = await self._analyze_asset_distribution(ticker)

            # Layer 2: Strategy performance analysis
            strategy_analysis = await self._analyze_strategy_performance(
                strategy_name, ticker, use_trade_history
            )

            # Divergence detection for both layers
            asset_divergence = await self._detect_asset_divergence(
                asset_analysis, current_position_data
            )

            strategy_divergence = await self._detect_strategy_divergence(
                strategy_analysis, current_position_data
            )

            # Dual-layer convergence analysis
            dual_layer_convergence = await self._analyze_dual_layer_convergence(
                asset_analysis, strategy_analysis, asset_divergence, strategy_divergence
            )

            # Probabilistic exit signal generation
            exit_signal = await self._generate_exit_signal(
                asset_analysis,
                strategy_analysis,
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                current_position_data,
                component_scores=None,  # Component scores handled later via update method
            )

            # Trade history metrics (if available)
            trade_history_metrics = None
            if use_trade_history:
                try:
                    trade_history_metrics = await self._get_trade_history_metrics(
                        strategy_name, ticker
                    )
                except Exception as e:
                    self.logger.warning(f"Could not load trade history metrics: {e}")

            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                asset_analysis, strategy_analysis, dual_layer_convergence, exit_signal
            )

            # Generate recommendation summary
            recommendation_summary = self._generate_recommendation_summary(
                exit_signal, dual_layer_convergence, overall_confidence
            )

            # Extract raw analysis data for backtesting parameter generation
            raw_analysis_data = self._extract_raw_analysis_data(
                current_position_data,
                use_trade_history,
                strategy_analysis,
                asset_analysis,
            )

            # Generate source agreement summary
            source_agreement_summary = self._generate_source_agreement_summary(
                strategy_analysis
            )

            # Generate data quality assessment
            data_quality_assessment = self._generate_data_quality_assessment(
                strategy_analysis
            )

            # Create complete result
            result = StatisticalAnalysisResult(
                strategy_name=strategy_name,
                ticker=ticker,
                analysis_timestamp=datetime.now(),
                asset_analysis=asset_analysis,
                strategy_analysis=strategy_analysis,
                asset_divergence=asset_divergence,
                strategy_divergence=strategy_divergence,
                trade_history_divergence=None,  # Can be populated later for source-specific divergence
                equity_curve_divergence=None,  # Can be populated later for source-specific divergence
                dual_layer_convergence=dual_layer_convergence,
                exit_signal=exit_signal,
                trade_history_metrics=trade_history_metrics,
                overall_confidence=overall_confidence,
                recommendation_summary=recommendation_summary,
                source_agreement_summary=source_agreement_summary,
                data_quality_assessment=data_quality_assessment,
                configuration_hash=self._get_config_hash(),
                data_sources_used=self._get_data_sources_used(use_trade_history),
                raw_analysis_data=raw_analysis_data,
            )

            # Update metrics
            processing_time = (datetime.now() - start_time).total_seconds()
            self._update_metrics(result, processing_time)

            self.logger.info(
                f"Analysis completed for {strategy_name} on {ticker} in {processing_time:.2f}s, "
                f"signal={exit_signal.signal_type}, confidence={overall_confidence:.1f}%"
            )

            return result

        except Exception as e:
            self.logger.error(f"Analysis failed for {strategy_name} on {ticker}: {e}")
            raise

    async def _analyze_asset_distribution(
        self, ticker: str
    ) -> AssetDistributionAnalysis:
        """Analyze asset-level return distribution (Layer 1) using coordinated data loading"""
        try:
            # Use coordinator for data loading if available
            if self.use_coordinator and self.data_coordinator:
                # Try to get coordinated strategy data first
                try:
                    strategy_data = self.data_coordinator.get_strategy_data(
                        strategy_identifier=ticker, force_refresh=False
                    )
                    if strategy_data and hasattr(strategy_data, "raw_analysis_data"):
                        # Extract asset distribution from coordinated data
                        return self._extract_asset_analysis_from_coordinated_data(
                            strategy_data, ticker
                        )
                except (StrategyDataCoordinatorError, AttributeError):
                    self.logger.debug(
                        f"Coordinator data not available for {ticker}, falling back to direct file access"
                    )

            # Fallback to direct file loading (legacy method)
            distribution_file = (
                Path(self.config.RETURN_DISTRIBUTION_PATH) / f"{ticker}.json"
            )

            if not distribution_file.exists():
                raise FileNotFoundError(
                    f"Return distribution data not found for {ticker}"
                )

            with open(distribution_file) as f:
                distribution_data = json.load(f)

            # Handle both old and new JSON structures
            if "timeframe_analysis" in distribution_data:
                # New structure
                timeframe_analysis = distribution_data["timeframe_analysis"]
                timeframe_data = timeframe_analysis.get(
                    "D", timeframe_analysis.get(next(iter(timeframe_analysis.keys())))
                )

                # Extract statistics from new structure
                desc_stats = timeframe_data["descriptive_statistics"]
                stats = StatisticalMetrics(
                    mean=desc_stats["mean"],
                    median=desc_stats["median"],
                    std=desc_stats["std_dev"],
                    min=desc_stats["min"],
                    max=desc_stats["max"],
                    skewness=desc_stats["skewness"],
                    kurtosis=desc_stats["kurtosis"],
                    count=timeframe_data["returns_count"],
                )

                # Create percentile metrics from new structure
                percentile_data = timeframe_data["percentiles"]
                percentiles = PercentileMetrics(
                    p5=percentile_data["5"],
                    p10=percentile_data["10"],
                    p25=percentile_data["25"],
                    p50=percentile_data["50"],
                    p75=percentile_data["75"],
                    p90=percentile_data["90"],
                    p95=percentile_data["95"],
                    p99=percentile_data["99"],
                )

                # Create VaR metrics from new structure
                var_data = timeframe_data["value_at_risk"]
                var_metrics = VaRMetrics(
                    var_95=var_data["var_95"],
                    var_99=var_data["var_99"],
                    expected_shortfall_95=var_data["var_95"]
                    * 1.2,  # Estimate if not available
                    expected_shortfall_99=var_data["var_99"]
                    * 1.2,  # Estimate if not available
                )

                # Get current analysis data
                current_analysis = timeframe_data.get("current_return_analysis", {})
                current_return = current_analysis.get("value")
                current_percentile = current_analysis.get("percentile_rank")

                # Calculate regime score from new structure
                regime_score = self._calculate_regime_score_new(desc_stats)

            else:
                # Old structure (fallback)
                timeframe_data = distribution_data.get(
                    "D", distribution_data.get(next(iter(distribution_data.keys())))
                )

                # Create statistical metrics
                stats = StatisticalMetrics(
                    mean=timeframe_data["mean"],
                    median=timeframe_data["median"],
                    std=timeframe_data["std"],
                    min=timeframe_data["min"],
                    max=timeframe_data["max"],
                    skewness=timeframe_data["skewness"],
                    kurtosis=timeframe_data["kurtosis"],
                    count=timeframe_data["count"],
                )

                # Create percentile metrics
                percentiles = PercentileMetrics(
                    p5=timeframe_data["percentiles"]["5"],
                    p10=timeframe_data["percentiles"]["10"],
                    p25=timeframe_data["percentiles"]["25"],
                    p50=timeframe_data["percentiles"]["50"],
                    p75=timeframe_data["percentiles"]["75"],
                    p90=timeframe_data["percentiles"]["90"],
                    p95=timeframe_data["percentiles"]["95"],
                    p99=timeframe_data["percentiles"]["99"],
                )

                # Create VaR metrics
                var_metrics = VaRMetrics(
                    var_95=timeframe_data["var"]["95"],
                    var_99=timeframe_data["var"]["99"],
                    expected_shortfall_95=timeframe_data.get(
                        "expected_shortfall", {}
                    ).get("95", timeframe_data["var"]["95"] * 1.2),
                    expected_shortfall_99=timeframe_data.get(
                        "expected_shortfall", {}
                    ).get("99", timeframe_data["var"]["99"] * 1.2),
                )

                current_return = timeframe_data.get("current_return")
                current_percentile = timeframe_data.get("current_percentile")
                regime_score = self._calculate_regime_score(timeframe_data)

            # Determine volatility regime
            volatility_regime = self._classify_volatility_regime(stats.std)

            # Get dates for new structure
            if "timeframe_analysis" in distribution_data:
                data_range = distribution_data.get("data_range", {})
                period_start = data_range.get("start_date", "2020-01-01")
                period_end = data_range.get("end_date", "2025-01-01")
                last_updated = distribution_data.get(
                    "analysis_date", datetime.now().isoformat()
                )
            else:
                period_start = timeframe_data.get("period_start", "2020-01-01")
                period_end = timeframe_data.get("period_end", "2025-01-01")
                last_updated = timeframe_data.get(
                    "last_updated", datetime.now().isoformat()
                )

            return AssetDistributionAnalysis(
                ticker=ticker,
                timeframe="D",  # Default timeframe
                data_source=DataSource.RETURN_DISTRIBUTION,
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                current_return=current_return,
                current_percentile=current_percentile,
                regime_score=regime_score,
                volatility_regime=volatility_regime,
                last_updated=(
                    datetime.fromisoformat(last_updated)
                    if isinstance(last_updated, str)
                    else last_updated
                ),
                sample_period_start=(
                    datetime.fromisoformat(period_start).date()
                    if isinstance(period_start, str)
                    else period_start
                ),
                sample_period_end=(
                    datetime.fromisoformat(period_end).date()
                    if isinstance(period_end, str)
                    else period_end
                ),
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze asset distribution for {ticker}: {e}")
            raise

    async def _analyze_strategy_performance(
        self,
        strategy_name: str,
        ticker: str,
        use_trade_history: bool | None = None,
        enable_dual_source: bool = True,
    ) -> StrategyDistributionAnalysis:
        """Enhanced strategy-level performance distribution analysis (Layer 2) with dual-source support"""
        try:
            # Use coordinator for data loading if available
            if self.use_coordinator and self.data_coordinator:
                try:
                    strategy_data = self.data_coordinator.get_strategy_data(
                        strategy_identifier=strategy_name, force_refresh=False
                    )
                    if strategy_data:
                        self.metrics["coordinator_cache_hits"] += 1
                        # Extract strategy distribution analysis from coordinated data
                        return self._extract_strategy_analysis_from_coordinated_data(
                            strategy_data, use_trade_history
                        )
                except StrategyDataCoordinatorError:
                    self.logger.debug(
                        f"Coordinator data not available for {strategy_name}, falling back to analysis"
                    )
                    self.metrics["coordinator_data_loads"] += 1

            # Determine analysis mode based on configuration and data availability
            if enable_dual_source:
                # Check availability of both data sources
                trade_history_available = await self._check_trade_history_availability(
                    strategy_name, ticker
                )
                equity_data_available = await self._check_equity_data_availability(
                    strategy_name, ticker
                )

                if trade_history_available and equity_data_available:
                    # Both sources available - perform dual-source analysis
                    self.logger.info(
                        f"Performing dual-source analysis for {strategy_name} on {ticker}"
                    )
                    return await self._analyze_combined_strategy_performance(
                        strategy_name, ticker
                    )
                if trade_history_available and (
                    use_trade_history is None or use_trade_history
                ):
                    # Only trade history available or preferred
                    self.logger.info(
                        f"Using trade history analysis for {strategy_name} on {ticker}"
                    )
                    return await self._analyze_trade_history_performance(
                        strategy_name, ticker
                    )
                if equity_data_available:
                    # Only equity data available or fallback
                    self.logger.info(
                        f"Using equity curve analysis for {strategy_name} on {ticker}"
                    )
                    return await self._analyze_equity_curve_performance(
                        strategy_name, ticker
                    )
                raise FileNotFoundError(
                    f"No data sources available for {strategy_name} on {ticker}"
                )

            # Legacy single-source mode (for compatibility)
            if use_trade_history:
                return await self._analyze_trade_history_performance(
                    strategy_name, ticker
                )
            return await self._analyze_equity_curve_performance(strategy_name, ticker)

        except Exception as e:
            self.logger.error(
                f"Error in strategy performance analysis for {strategy_name}: {e}"
            )
            raise

    async def _analyze_trade_history_performance(
        self, strategy_name: str, ticker: str
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy performance using trade history data"""
        try:
            # Use trade history analyzer
            trade_data = await self.trade_history_analyzer.analyze_strategy_trades(
                strategy_name, ticker
            )

            # Convert trade data to strategy distribution analysis
            confidence_level = self.config.get_confidence_level(
                trade_data["total_trades"]
            )
            confidence_score = self.config.get_confidence_threshold(
                trade_data["total_trades"]
            )

            # Bootstrap validation for small samples
            bootstrap_results = None
            if self.config.should_use_bootstrap(trade_data["total_trades"]):
                bootstrap_results = await self._perform_bootstrap_validation(
                    trade_data["returns"]
                )

            return StrategyDistributionAnalysis(
                strategy_name=strategy_name,
                ticker=ticker,
                timeframe="trade_level",
                data_sources_used=[DataSource.TRADE_HISTORY],
                data_source=DataSource.TRADE_HISTORY,
                statistics=trade_data["return_statistics"],
                percentiles=trade_data["return_percentiles"],
                var_metrics=trade_data["var_metrics"],
                win_rate=trade_data.get("win_rate"),
                profit_factor=trade_data.get("profit_factor"),
                sharpe_ratio=trade_data.get("sharpe_ratio"),
                max_drawdown=self._safe_max_drawdown(trade_data.get("max_drawdown")),
                mfe_statistics=trade_data.get("mfe_statistics"),
                mae_statistics=trade_data.get("mae_statistics"),
                duration_statistics=trade_data.get("duration_statistics"),
                bootstrap_results=bootstrap_results,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                combined_confidence=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to analyze trade history for {strategy_name} on {ticker}: {e}"
            )

            # Fallback to equity curve analysis if enabled
            if self.config.FALLBACK_TO_EQUITY:
                self.logger.info(
                    f"Falling back to equity curve analysis for {strategy_name}"
                )
                return await self._analyze_equity_curve_performance(
                    strategy_name, ticker
                )
            raise

    async def _analyze_equity_curve_performance(
        self, strategy_name: str, ticker: str
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy performance using equity curve data"""
        try:
            # Search for equity data files with enhanced pattern matching
            equity_file = None
            for equity_path in self.config.EQUITY_DATA_PATHS:
                equity_dir = Path(equity_path)
                if not equity_dir.exists():
                    continue

                # Pattern 1: Exact strategy name
                potential_file = equity_dir / f"{strategy_name}.csv"
                if potential_file.exists():
                    equity_file = potential_file
                    break

                # Pattern 2: Legacy naming with ticker and equity suffix
                potential_file_old = equity_dir / f"{strategy_name}_{ticker}_equity.csv"
                if potential_file_old.exists():
                    equity_file = potential_file_old
                    break

                # Pattern 3: Ticker + Strategy pattern (e.g., PWR_SMA_66_78.csv)
                if "_" in strategy_name:
                    parts = strategy_name.split("_")
                    if len(parts) >= 3:  # ticker_type_window1_window2
                        potential_file_ticker = (
                            equity_dir
                            / f"{ticker}_{parts[-3]}_{parts[-2]}_{parts[-1]}.csv"
                        )
                        if potential_file_ticker.exists():
                            equity_file = potential_file_ticker
                            break

                # Pattern 4: Glob pattern matching for flexible file discovery
                import glob

                pattern_searches = [
                    f"{ticker}*{strategy_name.split('_')[-1]}*.csv",  # ticker + last component
                    f"{ticker}_*.csv",  # any file starting with ticker
                    f"*{strategy_name.replace(ticker + '_', '')}*.csv",  # strategy part without ticker
                ]

                for pattern in pattern_searches:
                    glob_pattern = str(equity_dir / pattern)
                    matches = glob.glob(glob_pattern)
                    if matches:
                        equity_file = Path(matches[0])
                        self.logger.info(
                            f"Found equity data file for {strategy_name} using pattern '{pattern}': {equity_file}"
                        )
                        break

                if equity_file:
                    break

            if not equity_file:
                raise FileNotFoundError(
                    f"Equity data not found for {strategy_name} on {ticker}"
                )

            # Load and process equity data
            if self.enable_memory_optimization:
                df = self.memory_optimizer.read_csv_optimized(str(equity_file))
            else:
                df = pd.read_csv(equity_file)

            # Calculate returns from equity curve
            if "equity_change_pct" in df.columns:
                returns = df["equity_change_pct"].dropna()
            elif "equity" in df.columns:
                returns = df["equity"].pct_change().dropna()
            else:
                raise ValueError("No suitable equity column found in data")

            # Calculate statistics
            stats = self._calculate_statistical_metrics(returns)
            percentiles = self._calculate_percentile_metrics(returns)
            var_metrics = self._calculate_var_metrics(returns)

            # Additional strategy metrics
            win_rate = (returns > 0).mean() if len(returns) > 0 else None
            # Profit factor with division by zero protection
            negative_returns_sum = returns[returns < 0].sum()
            positive_returns_sum = returns[returns > 0].sum()
            profit_factor = None
            if len(returns[returns < 0]) > 0 and negative_returns_sum != 0:
                pf_value = positive_returns_sum / abs(negative_returns_sum)
                if np.isfinite(pf_value):
                    profit_factor = pf_value
            sharpe_ratio = (
                returns.mean() / returns.std() * np.sqrt(252)
                if returns.std() > 0
                else None
            )
            max_drawdown = self._calculate_max_drawdown(
                df.get("equity", returns.cumsum())
            )

            # Confidence assessment
            confidence_level = self.config.get_confidence_level(len(returns))
            confidence_score = self.config.get_confidence_threshold(len(returns))

            # Bootstrap validation for small samples
            bootstrap_results = None
            if self.config.should_use_bootstrap(len(returns)):
                bootstrap_results = await self._perform_bootstrap_validation(returns)

            return StrategyDistributionAnalysis(
                strategy_name=strategy_name,
                ticker=ticker,
                timeframe="D",  # Assuming daily equity data
                data_sources_used=[DataSource.EQUITY_CURVES],
                data_source=DataSource.EQUITY_CURVES,
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=self._safe_max_drawdown(max_drawdown),
                bootstrap_results=bootstrap_results,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
                combined_confidence=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to analyze equity curve for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _check_trade_history_availability(
        self, strategy_name: str, ticker: str
    ) -> bool:
        """Check if trade history data is available for the strategy"""
        try:
            # Use trade history analyzer to check availability
            trade_data = await self.trade_history_analyzer.analyze_strategy_trades(
                strategy_name, ticker
            )
            return trade_data is not None and trade_data.get("total_trades", 0) > 0
        except Exception:
            return False

    async def _check_equity_data_availability(
        self, strategy_name: str, ticker: str
    ) -> bool:
        """Check if equity curve data is available for the strategy with enhanced pattern matching"""
        try:
            # Search for equity data files with multiple naming patterns
            for equity_path in self.config.EQUITY_DATA_PATHS:
                equity_dir = Path(equity_path)
                if not equity_dir.exists():
                    continue

                # Pattern 1: Exact strategy name
                potential_file = equity_dir / f"{strategy_name}.csv"
                if potential_file.exists():
                    return True

                # Pattern 2: Legacy naming with ticker and equity suffix
                potential_file_old = equity_dir / f"{strategy_name}_{ticker}_equity.csv"
                if potential_file_old.exists():
                    return True

                # Pattern 3: Ticker + Strategy pattern (e.g., PWR_SMA_66_78.csv)
                if "_" in strategy_name:
                    # Try different combinations based on strategy name components
                    parts = strategy_name.split("_")
                    if len(parts) >= 3:  # ticker_type_window1_window2
                        potential_file_ticker = (
                            equity_dir
                            / f"{ticker}_{parts[-3]}_{parts[-2]}_{parts[-1]}.csv"
                        )
                        if potential_file_ticker.exists():
                            return True

                # Pattern 4: Search by glob patterns for flexible matching
                import glob

                pattern_searches = [
                    f"{ticker}*{strategy_name.split('_')[-1]}*.csv",  # ticker + last component
                    f"{ticker}_*.csv",  # any file starting with ticker
                    f"*{strategy_name.replace(ticker + '_', '')}*.csv",  # strategy part without ticker
                ]

                for pattern in pattern_searches:
                    glob_pattern = str(equity_dir / pattern)
                    matches = glob.glob(glob_pattern)
                    if matches:
                        self.logger.info(
                            f"Found equity data file for {strategy_name}: {matches[0]}"
                        )
                        return True

            return False
        except Exception as e:
            self.logger.warning(
                f"Error checking equity data availability for {strategy_name}: {e}"
            )
            return False

    async def _analyze_combined_strategy_performance(
        self, strategy_name: str, ticker: str
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy performance using BOTH trade history AND equity curve data"""
        try:
            # Perform both analyses in parallel
            trade_analysis_task = self._analyze_trade_history_performance_raw(
                strategy_name, ticker
            )
            equity_analysis_task = self._analyze_equity_curve_performance_raw(
                strategy_name, ticker
            )

            trade_analysis, equity_analysis = await asyncio.gather(
                trade_analysis_task, equity_analysis_task, return_exceptions=True
            )

            # Handle analysis results
            trade_history_analysis = None
            equity_curve_analysis = None

            if not isinstance(trade_analysis, Exception):
                trade_history_analysis = trade_analysis
                self.logger.info(
                    f"Trade history analysis completed for {strategy_name}"
                )
            else:
                self.logger.warning(
                    f"Trade history analysis failed for {strategy_name}: {trade_analysis}"
                )

            if not isinstance(equity_analysis, Exception):
                equity_curve_analysis = equity_analysis
                self.logger.info(f"Equity curve analysis completed for {strategy_name}")
            else:
                self.logger.warning(
                    f"Equity curve analysis failed for {strategy_name}: {equity_analysis}"
                )

            # Ensure at least one analysis succeeded
            if trade_history_analysis is None and equity_curve_analysis is None:
                raise ValueError(
                    f"Both trade history and equity analysis failed for {strategy_name}"
                )

            # Combine analyses and calculate convergence
            return await self._combine_strategy_analyses(
                strategy_name=strategy_name,
                ticker=ticker,
                trade_history_analysis=trade_history_analysis,
                equity_analysis=equity_curve_analysis,
            )

        except Exception as e:
            self.logger.error(
                f"Failed combined analysis for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _detect_asset_divergence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        current_position_data: dict | None,
    ) -> DivergenceMetrics:
        """Detect divergence in asset-level performance"""
        return await self.divergence_detector.detect_asset_divergence(
            asset_analysis, current_position_data
        )

    async def _detect_strategy_divergence(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict | None,
    ) -> DivergenceMetrics:
        """Detect divergence in strategy-level performance"""
        return await self.divergence_detector.detect_strategy_divergence(
            strategy_analysis, current_position_data
        )

    async def _analyze_dual_layer_convergence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
    ) -> DualLayerConvergence:
        """Analyze convergence between asset and strategy layers"""
        return await self.divergence_detector.analyze_dual_layer_convergence(
            asset_analysis, strategy_analysis, asset_divergence, strategy_divergence
        )

    # =================== POSITION-SPECIFIC ANALYSIS METHODS ===================

    def _analyze_position_exit_factors(
        self, position_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Analyze position-specific factors that influence exit decisions"""
        try:
            days_held = position_metrics.get("days_since_entry", 0)
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mfe = position_metrics.get("mfe", 0.0)
            mae = position_metrics.get("mae", 0.0)

            return {
                "duration_factor": min(days_held / 60.0, 1.0),  # Normalize to 60 days
                "profit_factor": max(
                    min(current_pnl / 0.2, 1.0), -1.0
                ),  # Normalize to 20%
                "mfe_utilization": current_pnl / mfe if mfe > 0 else 0.0,
                "risk_factor": (
                    mae / 0.1 if mae > 0 else 0.0
                ),  # Risk relative to 10% drawdown
                "trade_quality": position_metrics.get("trade_quality", "").lower(),
            }
        except Exception as e:
            self.logger.error(f"Error analyzing position exit factors: {e}")
            return {}

    def _calculate_position_exit_strength(
        self,
        position_metrics: dict[str, Any],
        dual_layer_convergence: "DualLayerConvergence",
        asset_divergence: "DivergenceMetrics",
        strategy_divergence: "DivergenceMetrics",
    ) -> float:
        """Calculate position-specific exit signal strength"""
        try:
            exit_factors = self._analyze_position_exit_factors(position_metrics)

            # Base strength from market analysis
            base_strength = (
                dual_layer_convergence.convergence_score * 0.4
                + asset_divergence.percentile_rank / 100.0 * 0.3
                + strategy_divergence.percentile_rank / 100.0 * 0.3
            )

            # Position-specific adjustments
            duration_adjustment = exit_factors.get("duration_factor", 0) * 0.2
            profit_adjustment = abs(exit_factors.get("profit_factor", 0)) * 0.15

            position_strength = base_strength + duration_adjustment + profit_adjustment
            return max(0.1, min(1.0, position_strength))

        except Exception as e:
            self.logger.error(f"Error calculating position exit strength: {e}")
            return 0.5

    def _calculate_position_performance_strength(
        self, position_metrics: dict[str, Any]
    ) -> float:
        """Calculate strength based on actual position performance"""
        try:
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mfe = position_metrics.get("mfe", 0.0)
            mae = position_metrics.get("mae", 0.0)
            days_held = position_metrics.get("days_since_entry", 0)

            # Performance relative to potential
            mfe_utilization = current_pnl / mfe if mfe > 0 else 0.5

            # Time-adjusted performance
            time_factor = min(days_held / 30.0, 2.0)  # Normalize around 30 days

            # Risk-adjusted performance
            risk_adj_performance = (
                current_pnl / max(mae, 0.01) if mae > 0 else current_pnl
            )

            performance_strength = (
                mfe_utilization * 0.4
                + risk_adj_performance * 0.3
                + (1.0 / max(time_factor, 0.5)) * 0.3  # Shorter holds get bonus
            )

            return max(0.1, min(1.0, performance_strength))

        except Exception as e:
            self.logger.error(f"Error calculating position performance strength: {e}")
            return 0.5

    def _calculate_position_performance_contribution(
        self, position_metrics: dict[str, Any]
    ) -> float:
        """Calculate position performance contribution to signal confidence"""
        try:
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mfe = position_metrics.get("mfe", 0.0)
            mae = position_metrics.get("mae", 0.0)
            trade_quality = position_metrics.get("trade_quality", "").lower()

            # Base contribution from current performance
            pnl_contribution = min(abs(current_pnl) / 0.15, 1.0)  # Normalize to 15%

            # MFE/MAE ratio contribution
            mfe_mae_ratio = mfe / max(mae, 0.001)
            ratio_contribution = min(
                mfe_mae_ratio / 5.0, 1.0
            )  # Normalize to ratio of 5

            # Trade quality bonus
            quality_bonus = {"excellent": 0.2, "good": 0.1, "poor": -0.1}.get(
                trade_quality, 0.0
            )

            total_contribution = (
                pnl_contribution + ratio_contribution
            ) / 2.0 + quality_bonus
            return max(0.1, min(1.0, total_contribution))

        except Exception as e:
            self.logger.error(
                f"Error calculating position performance contribution: {e}"
            )
            return 0.5

    def _determine_position_exit_signal_type(
        self,
        position_metrics: dict[str, Any],
        dual_layer_convergence: "DualLayerConvergence",
        asset_divergence: "DivergenceMetrics",
        strategy_divergence: "DivergenceMetrics",
        component_scores: dict[str, Any] | None = None,
    ) -> "SignalType":
        """Determine exit signal type for open position based on position-specific factors"""
        try:
            from ..models.statistical_analysis_models import SignalType

            days_held = position_metrics.get("days_since_entry", 0)
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mfe = position_metrics.get("mfe", 0.0)
            mae = position_metrics.get("mae", 0.0)

            # Position-specific exit logic

            # 1. Time-based exits (held > 60 days)
            if days_held > 60:
                if current_pnl > 0.1:  # Profitable long-term position
                    return SignalType.SELL
                if current_pnl < -0.1:  # Losing long-term position
                    return SignalType.STRONG_SELL

            # 2. Profit-taking exits
            if current_pnl > 0.15:  # 15%+ profit
                # Check if near MFE peak
                mfe_utilization = current_pnl / mfe if mfe > 0 else 0
                if mfe_utilization > 0.8:  # Near peak performance
                    return SignalType.STRONG_SELL
                return SignalType.SELL

            # 3. Risk management exits
            if current_pnl < -0.1:  # 10%+ loss
                if mae > 0.15:  # Significant drawdown experienced
                    return SignalType.EXIT_IMMEDIATELY
                return SignalType.STRONG_SELL

            # 4. Market-based exits (use existing logic for market conditions)
            max_percentile = max(
                asset_divergence.percentile_rank, strategy_divergence.percentile_rank
            )

            if dual_layer_convergence.convergence_score > 0.8 and max_percentile > 90:
                return SignalType.STRONG_SELL
            if max_percentile > 80:
                return SignalType.SELL

            # 5. Component score overrides for open positions
            if component_scores:
                component_override = self._check_component_score_override(
                    component_scores, SignalType.HOLD
                )
                if component_override and component_override in [
                    SignalType.SELL,
                    SignalType.STRONG_SELL,
                    SignalType.EXIT_IMMEDIATELY,
                ]:
                    return component_override

            # Default to hold for positions within normal ranges
            return SignalType.HOLD

        except Exception as e:
            self.logger.error(f"Error determining position exit signal type: {e}")
            return SignalType.HOLD

    def _calculate_position_exit_confidence(
        self,
        position_metrics: dict[str, Any],
        primary_strength: float,
        secondary_strength: float,
        tertiary_strength: float,
        dual_layer_convergence: "DualLayerConvergence",
    ) -> float:
        """Calculate confidence for position exit signals"""
        try:
            # Base confidence from signal strengths
            base_confidence = (
                primary_strength + secondary_strength + tertiary_strength
            ) / 3.0

            # Position-specific confidence adjustments
            days_held = position_metrics.get("days_since_entry", 0)
            trade_quality = position_metrics.get("trade_quality", "").lower()
            mfe_mae_ratio = position_metrics.get("mfe", 0) / max(
                position_metrics.get("mae", 0.001), 0.001
            )

            # Experience bonus (longer holds have more data)
            experience_bonus = min(days_held / 30.0, 1.0) * 0.1

            # Quality bonus
            quality_bonus = {"excellent": 0.15, "good": 0.05, "poor": -0.1}.get(
                trade_quality, 0.0
            )

            # Risk management bonus (good MFE/MAE ratio)
            risk_bonus = min(mfe_mae_ratio / 3.0, 1.0) * 0.1

            # Convergence bonus
            convergence_bonus = dual_layer_convergence.convergence_score * 0.1

            total_confidence = (
                base_confidence
                + experience_bonus
                + quality_bonus
                + risk_bonus
                + convergence_bonus
            )

            return max(0.1, min(1.0, total_confidence))

        except Exception as e:
            self.logger.error(f"Error calculating position exit confidence: {e}")
            return 0.5

    def _estimate_position_exit_upside(
        self, position_metrics: dict[str, Any], signal_type: "SignalType"
    ) -> float | None:
        """Estimate remaining upside for open position"""
        try:
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mfe = position_metrics.get("mfe", 0.0)

            # Remaining upside based on historical peak
            remaining_to_peak = max(0, mfe - current_pnl)

            from ..models.statistical_analysis_models import SignalType

            if signal_type == SignalType.EXIT_IMMEDIATELY:
                return min(remaining_to_peak * 0.2, 0.02)  # Very limited upside
            if signal_type == SignalType.STRONG_SELL:
                return min(remaining_to_peak * 0.4, 0.05)  # Limited upside
            if signal_type == SignalType.SELL:
                return min(remaining_to_peak * 0.6, 0.08)  # Some upside possible
            return None  # Hold - upside unknown

        except Exception as e:
            self.logger.error(f"Error estimating position exit upside: {e}")
            return None

    def _estimate_position_exit_timeline(
        self, position_metrics: dict[str, Any], signal_type: "SignalType"
    ) -> str | None:
        """Estimate timeline for position exit execution"""
        try:
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            days_held = position_metrics.get("days_since_entry", 0)

            from ..models.statistical_analysis_models import SignalType

            if signal_type == SignalType.EXIT_IMMEDIATELY:
                return "Immediate" if current_pnl < -0.1 else "Same day"
            if signal_type == SignalType.STRONG_SELL:
                if days_held > 60:
                    return "1-2 days"  # Faster exit for long holds
                return "2-3 days"
            if signal_type == SignalType.SELL:
                if current_pnl > 0.1:
                    return "3-5 days"  # Gradual profit taking
                return "1-3 days"  # Faster exit for losses
            return None  # Hold

        except Exception as e:
            self.logger.error(f"Error estimating position exit timeline: {e}")
            return None

    def _generate_position_risk_warning(
        self, position_metrics: dict[str, Any], signal_type: "SignalType"
    ) -> str | None:
        """Generate position-specific risk warnings"""
        try:
            days_held = position_metrics.get("days_since_entry", 0)
            current_pnl = position_metrics.get("current_unrealized_pnl", 0.0)
            mae = position_metrics.get("mae", 0.0)

            warnings = []

            if days_held > 60:
                warnings.append(f"Long-term position ({days_held} days)")

            if current_pnl < -0.1:
                warnings.append(f"Significant loss ({current_pnl:.1%})")

            if mae > 0.15:
                warnings.append(f"High drawdown experienced ({mae:.1%})")

            from ..models.statistical_analysis_models import SignalType

            if signal_type in [SignalType.STRONG_SELL, SignalType.EXIT_IMMEDIATELY]:
                warnings.append("Consider immediate exit")

            return "; ".join(warnings) if warnings else None

        except Exception as e:
            self.logger.error(f"Error generating position risk warning: {e}")
            return None

    # =================== END POSITION-SPECIFIC ANALYSIS METHODS ===================

    async def _generate_exit_signal(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        dual_layer_convergence: DualLayerConvergence,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
        current_position_data: dict | None,
        component_scores: dict[str, Any] | None = None,
    ) -> ProbabilisticExitSignal:
        """Enhanced probabilistic exit signal generation with multi-source confidence weighting"""
        try:
            # Calculate signal strength for each layer
            primary_strength = self._calculate_primary_signal_strength(
                dual_layer_convergence, asset_divergence, strategy_divergence
            )
            secondary_strength = self._calculate_secondary_signal_strength(
                strategy_analysis, current_position_data
            )
            tertiary_strength = self._calculate_tertiary_signal_strength(
                asset_analysis, strategy_analysis
            )

            # Enhanced multi-source signal contributions
            asset_layer_contribution = self._calculate_asset_layer_contribution(
                asset_analysis, asset_divergence
            )

            trade_history_contribution = None
            equity_curve_contribution = None
            intra_strategy_consistency = None
            source_divergence_warning = None

            # Calculate source-specific contributions for dual-source analysis
            if (
                strategy_analysis.trade_history_analysis
                and strategy_analysis.equity_analysis
                and strategy_analysis.dual_source_convergence
            ):
                trade_history_contribution = self._calculate_trade_history_contribution(
                    strategy_analysis.trade_history_analysis
                )
                equity_curve_contribution = self._calculate_equity_curve_contribution(
                    strategy_analysis.equity_analysis
                )

                # Calculate intra-strategy consistency
                intra_strategy_consistency = (
                    strategy_analysis.dual_source_convergence.convergence_score
                )

                # Generate source divergence warning if needed
                if strategy_analysis.dual_source_convergence.has_significant_divergence:
                    source_divergence_warning = (
                        f"Significant divergence detected between trade history and equity curve analysis. "
                        f"Convergence score: {strategy_analysis.dual_source_convergence.convergence_score:.2f}"
                    )

            # Enhanced multi-source confidence assessment
            data_source_confidence = self._calculate_data_source_confidence(
                asset_analysis, strategy_analysis
            )

            combined_source_confidence = self._calculate_combined_source_confidence(
                data_source_confidence, strategy_analysis
            )

            source_reliability_score = self._calculate_source_reliability_score(
                strategy_analysis, dual_layer_convergence
            )

            # Calculate component scores with multi-source enhancements
            dual_layer_score = dual_layer_convergence.convergence_score
            triple_layer_score = dual_layer_convergence.triple_layer_convergence
            timeframe_score = dual_layer_convergence.cross_timeframe_score
            risk_adjusted_score = self._calculate_risk_adjusted_score(
                asset_analysis, strategy_analysis
            )

            # Enhanced sample size confidence with multi-source weighting
            sample_size_confidence = self._calculate_enhanced_sample_size_confidence(
                strategy_analysis, combined_source_confidence
            )

            # Determine signal type with multi-source analysis
            signal_type = self._determine_enhanced_signal_type(
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                primary_strength,
                strategy_analysis,
                component_scores,
            )

            # Enhanced confidence calculation with multi-source weighting
            base_confidence = self._calculate_enhanced_base_confidence(
                primary_strength,
                secondary_strength,
                tertiary_strength,
                asset_layer_contribution,
                trade_history_contribution,
                equity_curve_contribution,
            )

            adjusted_confidence = (
                base_confidence * sample_size_confidence * combined_source_confidence
            )

            # Enhanced expected outcomes with multi-source insights
            expected_upside = self._estimate_enhanced_expected_upside(
                signal_type, asset_divergence, strategy_divergence, strategy_analysis
            )
            expected_timeline = self._estimate_expected_timeline(
                signal_type, strategy_analysis
            )
            risk_warning = self._generate_enhanced_risk_warning(
                signal_type,
                strategy_analysis,
                dual_layer_convergence,
                source_divergence_warning,
            )

            return ProbabilisticExitSignal(
                signal_type=signal_type,
                confidence=min(adjusted_confidence, 100.0),
                primary_signal_strength=primary_strength,
                secondary_signal_strength=secondary_strength,
                tertiary_signal_strength=tertiary_strength,
                asset_layer_contribution=asset_layer_contribution,
                trade_history_contribution=trade_history_contribution,
                equity_curve_contribution=equity_curve_contribution,
                dual_layer_score=dual_layer_score,
                triple_layer_score=triple_layer_score,
                timeframe_score=timeframe_score,
                risk_adjusted_score=risk_adjusted_score,
                intra_strategy_consistency=intra_strategy_consistency,
                source_reliability_score=source_reliability_score,
                sample_size_confidence=sample_size_confidence,
                statistical_validity=strategy_analysis.confidence_level,
                data_source_confidence=data_source_confidence,
                combined_source_confidence=combined_source_confidence,
                expected_upside=expected_upside,
                expected_timeline=expected_timeline,
                risk_warning=risk_warning,
                source_divergence_warning=source_divergence_warning,
            )

        except Exception as e:
            self.logger.error(f"Failed to generate exit signal: {e}")
            # Return default HOLD signal with all required fields
            return ProbabilisticExitSignal(
                signal_type=SignalType.HOLD,
                confidence=50.0,
                primary_signal_strength=0.5,
                secondary_signal_strength=0.5,
                tertiary_signal_strength=0.5,
                asset_layer_contribution=0.5,
                trade_history_contribution=None,
                equity_curve_contribution=None,
                dual_layer_score=0.5,
                triple_layer_score=None,
                timeframe_score=0.5,
                risk_adjusted_score=0.5,
                intra_strategy_consistency=None,
                source_reliability_score=0.5,
                sample_size_confidence=0.5,
                statistical_validity=ConfidenceLevel.LOW,
                data_source_confidence={},
                combined_source_confidence=0.5,
                expected_upside=None,
                expected_timeline=None,
                risk_warning="Analysis failed - using default HOLD signal",
                source_divergence_warning=None,
            )

    # Helper methods

    def _safe_max_drawdown(self, value: float | None) -> float | None:
        """Safely handle max_drawdown values, converting NaN/inf to valid values"""
        if value is None:
            return None
        if np.isnan(value) or np.isinf(value):
            return 0.0  # Valid max_drawdown fallback
        return min(value, 0.0)  # Ensure it's <= 0

    def _calculate_statistical_metrics(
        self, data: pd.Series | np.ndarray | list
    ) -> StatisticalMetrics:
        """Calculate basic statistical metrics from data"""
        data = np.array(data)

        # Handle empty data
        if len(data) == 0:
            return StatisticalMetrics(
                mean=0.0,
                median=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                skewness=0.0,
                kurtosis=0.0,
                count=0,
            )

        # Filter out non-finite values for calculations
        finite_data = data[np.isfinite(data)]
        if len(finite_data) == 0:
            return StatisticalMetrics(
                mean=0.0,
                median=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                skewness=0.0,
                kurtosis=0.0,
                count=len(data),
            )

        # Calculate metrics with fallbacks for NaN results
        def safe_float(value, fallback=0.0):
            return fallback if np.isnan(value) or np.isinf(value) else float(value)

        return StatisticalMetrics(
            mean=safe_float(np.mean(finite_data)),
            median=safe_float(np.median(finite_data)),
            std=safe_float(np.std(finite_data)),
            min=safe_float(np.min(finite_data)),
            max=safe_float(np.max(finite_data)),
            skewness=self._calculate_skewness(finite_data),
            kurtosis=self._calculate_kurtosis(finite_data),
            count=len(data),
        )

    def _calculate_percentile_metrics(
        self, data: pd.Series | np.ndarray | list
    ) -> PercentileMetrics:
        """Calculate percentile metrics from data"""
        data = np.array(data)

        # Handle empty data
        if len(data) == 0:
            return PercentileMetrics(
                p5=0.0, p10=0.0, p25=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0
            )

        # Filter out non-finite values
        finite_data = data[np.isfinite(data)]
        if len(finite_data) == 0:
            return PercentileMetrics(
                p5=0.0, p10=0.0, p25=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0
            )

        def safe_percentile(data, percentile, fallback=0.0):
            try:
                value = np.percentile(data, percentile)
                return fallback if np.isnan(value) or np.isinf(value) else float(value)
            except Exception:
                return fallback

        return PercentileMetrics(
            p5=safe_percentile(finite_data, 5),
            p10=safe_percentile(finite_data, 10),
            p25=safe_percentile(finite_data, 25),
            p50=safe_percentile(finite_data, 50),
            p75=safe_percentile(finite_data, 75),
            p90=safe_percentile(finite_data, 90),
            p95=safe_percentile(finite_data, 95),
            p99=safe_percentile(finite_data, 99),
        )

    def _calculate_var_metrics(self, data: pd.Series | np.ndarray | list) -> VaRMetrics:
        """Calculate VaR metrics from data"""
        data = np.array(data)

        # Handle empty data
        if len(data) == 0:
            return VaRMetrics(
                var_95=0.0,
                var_99=0.0,
                expected_shortfall_95=0.0,
                expected_shortfall_99=0.0,
            )

        # Filter out non-finite values
        finite_data = data[np.isfinite(data)]
        if len(finite_data) == 0:
            return VaRMetrics(
                var_95=0.0,
                var_99=0.0,
                expected_shortfall_95=0.0,
                expected_shortfall_99=0.0,
            )

        def safe_percentile(data, percentile, fallback=0.0):
            try:
                value = np.percentile(data, percentile)
                return fallback if np.isnan(value) or np.isinf(value) else float(value)
            except Exception:
                return fallback

        var_95 = safe_percentile(finite_data, 5)  # 95% VaR (5th percentile)
        var_99 = safe_percentile(finite_data, 1)  # 99% VaR (1st percentile)

        # Calculate expected shortfall (CVaR) with safety checks
        def safe_es(data, var_threshold, fallback=0.0):
            try:
                tail_data = data[data <= var_threshold]
                if len(tail_data) > 0:
                    es_value = np.mean(tail_data)
                    return (
                        fallback
                        if np.isnan(es_value) or np.isinf(es_value)
                        else float(es_value)
                    )
                return var_threshold
            except Exception:
                return fallback

        es_95 = safe_es(finite_data, var_95, var_95)
        es_99 = safe_es(finite_data, var_99, var_99)

        return VaRMetrics(
            var_95=var_95,
            var_99=var_99,
            expected_shortfall_95=es_95,
            expected_shortfall_99=es_99,
        )

    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness of data"""
        n = len(data)
        if n < 3:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0

        # Additional safety check for division by zero
        denominator = (n - 1) * (n - 2)
        if denominator == 0:
            return 0.0

        result = (n / denominator) * np.sum(((data - mean) / std) ** 3)

        # Ensure result is finite
        if np.isnan(result) or np.isinf(result):
            return 0.0

        return result

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        n = len(data)
        if n < 4:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0

        # Additional safety checks for division by zero
        denominator1 = (n - 1) * (n - 2) * (n - 3)
        denominator2 = (n - 2) * (n - 3)
        if denominator1 == 0 or denominator2 == 0:
            return 0.0

        result = (n * (n + 1) / denominator1) * np.sum(
            ((data - mean) / std) ** 4
        ) - 3 * (n - 1) ** 2 / denominator2

        # Ensure result is finite
        if np.isnan(result) or np.isinf(result):
            return 0.0

        return result

    def _calculate_max_drawdown(self, equity_series: pd.Series | np.ndarray) -> float:
        """Calculate maximum drawdown from equity series"""
        try:
            equity = np.array(equity_series)
            if len(equity) == 0:
                return 0.0

            # Handle NaN/inf values in input
            if np.any(np.isnan(equity)) or np.any(np.isinf(equity)):
                # Filter out NaN/inf values
                equity = equity[np.isfinite(equity)]
                if len(equity) == 0:
                    return 0.0

            peak = np.maximum.accumulate(equity)

            # Avoid division by zero
            safe_peak = np.where(peak == 0, 1.0, peak)
            drawdown = (equity - peak) / safe_peak

            # If all peaks are zero, return 0 (no drawdown)
            if np.all(peak == 0):
                return 0.0

            max_dd = float(np.min(drawdown))

            # Ensure result is finite and negative or zero
            if np.isnan(max_dd) or np.isinf(max_dd):
                return 0.0

            return min(max_dd, 0.0)
        except Exception as e:
            self.logger.warning(f"Error calculating max drawdown: {e}")
            return 0.0

    async def _perform_bootstrap_validation(
        self, data: pd.Series | np.ndarray | list
    ) -> BootstrapResults:
        """Perform bootstrap validation for small samples"""
        return await self.bootstrap_validator.validate_sample(data)

    async def _get_trade_history_metrics(
        self, strategy_name: str, ticker: str
    ) -> TradeHistoryMetrics:
        """Get trade history metrics if available"""
        return await self.trade_history_analyzer.get_trade_metrics(
            strategy_name, ticker
        )

    def _calculate_regime_score(self, timeframe_data: dict) -> float:
        """Calculate market regime score based on distribution characteristics"""
        # Simple regime scoring based on skewness and volatility
        skewness = timeframe_data.get("skewness", 0)
        volatility = timeframe_data.get("std", 0)

        # Normalize to [-1, 1] range
        regime_score = np.tanh(skewness * 0.5 - volatility * 0.3)
        return float(regime_score)

    def _calculate_regime_score_new(self, desc_stats: dict) -> float:
        """Calculate market regime score for new JSON structure"""
        # Simple regime scoring based on skewness and volatility
        skewness = desc_stats.get("skewness", 0)
        volatility = desc_stats.get("std_dev", 0)

        # Normalize to [-1, 1] range
        regime_score = np.tanh(skewness * 0.5 - volatility * 0.3)
        return float(regime_score)

    def _classify_volatility_regime(self, volatility: float) -> str:
        """Classify volatility regime"""
        if volatility < 0.01:
            return "low"
        if volatility > 0.03:
            return "high"
        return "medium"

    def _calculate_primary_signal_strength(
        self,
        convergence: DualLayerConvergence,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
    ) -> float:
        """Calculate primary signal strength from dual-layer convergence"""
        return min(
            convergence.convergence_score
            + (asset_div.rarity_score + strategy_div.rarity_score) / 2,
            1.0,
        )

    def _calculate_secondary_signal_strength(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: dict | None,
    ) -> float:
        """Calculate secondary signal strength from multi-timeframe analysis"""
        # Base strength from confidence level
        base_strength = strategy_analysis.confidence_score

        # Adjust based on sample size
        if strategy_analysis.statistics.count >= self.config.OPTIMAL_SAMPLE_SIZE:
            return min(base_strength * 1.1, 1.0)
        if strategy_analysis.statistics.count >= self.config.PREFERRED_SAMPLE_SIZE:
            return base_strength
        return base_strength * 0.8

    def _calculate_tertiary_signal_strength(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate tertiary signal strength from risk-adjusted metrics"""
        # Risk adjustment based on VaR and volatility with NaN handling
        try:
            asset_var_95 = asset_analysis.var_metrics.var_95
            strategy_var_95 = strategy_analysis.var_metrics.var_95

            # Handle NaN or invalid VaR values
            if np.isnan(asset_var_95) or np.isinf(asset_var_95):
                asset_var_score = 0.5  # Neutral fallback
            else:
                asset_var_score = 1.0 - abs(asset_var_95) / 0.1  # Normalize by 10%

            if np.isnan(strategy_var_95) or np.isinf(strategy_var_95):
                strategy_var_score = 0.5  # Neutral fallback
            else:
                strategy_var_score = 1.0 - abs(strategy_var_95) / 0.1

            combined_score = (asset_var_score + strategy_var_score) / 2
            return max(min(combined_score, 1.0), 0.0)
        except Exception:
            # Fallback to neutral score if any error occurs
            return 0.5

    def _calculate_risk_adjusted_score(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate risk-adjusted score combining both layers"""
        try:
            # Sharpe ratio-like calculation with NaN handling
            asset_mean = asset_analysis.statistics.mean
            asset_std = asset_analysis.statistics.std
            strategy_mean = strategy_analysis.statistics.mean
            strategy_std = strategy_analysis.statistics.std

            # Handle NaN or invalid values
            if (
                np.isnan(asset_mean)
                or np.isinf(asset_mean)
                or np.isnan(asset_std)
                or np.isinf(asset_std)
                or asset_std <= 0
            ):
                asset_score = 0.0
            else:
                asset_score = asset_mean / max(asset_std, 0.001)

            if (
                np.isnan(strategy_mean)
                or np.isinf(strategy_mean)
                or np.isnan(strategy_std)
                or np.isinf(strategy_std)
                or strategy_std <= 0
            ):
                strategy_score = 0.0
            else:
                strategy_score = strategy_mean / max(strategy_std, 0.001)

            # Normalize to [0, 1] with NaN protection
            combined_score = (asset_score + strategy_score) / 2
            if np.isnan(combined_score) or np.isinf(combined_score):
                return 0.5  # Neutral fallback

            # Sigmoid normalization with bounds checking
            sigmoid_score = 1 / (1 + np.exp(-combined_score))
            return max(min(sigmoid_score, 1.0), 0.0)
        except Exception:
            # Fallback to neutral score if any error occurs
            return 0.5

    def _determine_signal_type(
        self,
        convergence: DualLayerConvergence,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
        primary_strength: float,
    ) -> SignalType:
        """Determine signal type based on analysis results - Complete Entry/Exit System"""
        # Get the minimum and maximum percentile ranks for comprehensive analysis
        min_percentile_rank = min(
            asset_div.percentile_rank, strategy_div.percentile_rank
        )
        max_percentile_rank = max(
            asset_div.percentile_rank, strategy_div.percentile_rank
        )

        # ENTRY SIGNALS - Low percentiles indicate undervalued conditions (good entries)
        # Entry signals always require dual-layer convergence >= 0.7
        if convergence.convergence_score >= 0.7:
            # Check for strong buy conditions (bottom 10%)
            if min_percentile_rank <= self.config.get_percentile_threshold(
                "strong_buy"
            ) and max_percentile_rank <= self.config.get_percentile_threshold(
                "strong_buy"
            ):
                return SignalType.STRONG_BUY

            # Check for buy conditions (bottom 20%)
            if min_percentile_rank <= self.config.get_percentile_threshold(
                "buy"
            ) and max_percentile_rank <= self.config.get_percentile_threshold("buy"):
                return SignalType.BUY

        # EXIT SIGNALS - High percentiles indicate overvalued conditions (good exits)
        # Check for immediate exit conditions
        if (
            convergence.convergence_score > 0.85
            and asset_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
            and strategy_div.percentile_rank
            > self.config.get_percentile_threshold("exit_immediately")
        ):
            return SignalType.EXIT_IMMEDIATELY

        # Check for strong sell conditions
        if (
            convergence.convergence_score > 0.70
            and max_percentile_rank
            > self.config.get_percentile_threshold("strong_sell")
        ):
            return SignalType.STRONG_SELL

        # Check for sell conditions
        if (
            convergence.convergence_score > 0.60
            and max_percentile_rank > self.config.get_percentile_threshold("sell")
        ):
            return SignalType.SELL

        # Default to hold (20-70% percentile range)
        return SignalType.HOLD

    def _estimate_expected_upside(
        self,
        signal_type: SignalType,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
    ) -> float | None:
        """Estimate expected upside based on signal type - Complete Entry/Exit System"""
        # Entry signals - significant upside potential
        if signal_type == SignalType.STRONG_BUY:
            return 25.0  # High upside potential from undervalued entry
        if signal_type == SignalType.BUY:
            return 15.0  # Good upside potential from entry opportunity
        # Neutral signal
        if signal_type == SignalType.HOLD:
            return None  # Hold - upside unknown
        # Exit signals - limited remaining upside
        if signal_type == SignalType.SELL:
            return 10.0  # Some upside possible before exit
        if signal_type == SignalType.STRONG_SELL:
            return 5.0  # Limited upside remaining
        if signal_type == SignalType.EXIT_IMMEDIATELY:
            return 2.0  # Minimal upside expected
        return None  # Unknown signal type

    def _estimate_expected_timeline(
        self, signal_type: SignalType, strategy_analysis: StrategyDistributionAnalysis
    ) -> str | None:
        """Estimate expected timeline for signal execution - Complete Entry/Exit System"""
        # Entry signals - time to potential realization
        if signal_type == SignalType.STRONG_BUY:
            return "1-4 weeks"  # Time for undervalued entry to realize gains
        if signal_type == SignalType.BUY:
            return "2-6 weeks"  # Time for entry opportunity to develop
        # Neutral signal
        if signal_type == SignalType.HOLD:
            return None  # No specific timeline
        # Exit signals - urgency-based timelines
        if signal_type == SignalType.SELL:
            return "3-7 days"  # Moderate exit urgency
        if signal_type == SignalType.STRONG_SELL:
            return "1-3 days"  # High exit urgency
        if signal_type == SignalType.EXIT_IMMEDIATELY:
            return "Immediate"  # Maximum urgency
        return None

    def _generate_risk_warning(
        self,
        signal_type: SignalType,
        strategy_analysis: StrategyDistributionAnalysis,
        convergence: DualLayerConvergence,
    ) -> str | None:
        """Generate risk warning based on analysis"""
        warnings = []

        if strategy_analysis.confidence_level == ConfidenceLevel.LOW:
            warnings.append("Low sample size - reduced confidence")

        if convergence.convergence_score < 0.5:
            warnings.append("Low dual-layer convergence - conflicting signals")

        if strategy_analysis.statistics.std > 0.05:  # High volatility
            warnings.append("High volatility detected")

        return "; ".join(warnings) if warnings else None

    def _calculate_overall_confidence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        convergence: DualLayerConvergence,
        exit_signal: ProbabilisticExitSignal,
    ) -> float:
        """Calculate overall analysis confidence"""
        try:
            # Weight different confidence factors
            signal_confidence = (
                exit_signal.confidence
                if exit_signal and hasattr(exit_signal, "confidence")
                else 50.0
            )
            convergence_confidence = (
                convergence.convergence_score * 100
                if convergence and hasattr(convergence, "convergence_score")
                else 50.0
            )
            sample_size_confidence = (
                strategy_analysis.confidence_score * 100
                if strategy_analysis and hasattr(strategy_analysis, "confidence_score")
                else 50.0
            )
            data_quality_confidence = (
                90.0
                if asset_analysis
                and hasattr(asset_analysis, "statistics")
                and hasattr(asset_analysis.statistics, "count")
                and asset_analysis.statistics.count > 1000
                else 70.0
            )

            # Enhanced debug logging
            self.logger.info(
                f"Confidence calculation inputs: "
                f"exit_signal={exit_signal is not None}, "
                f"convergence={convergence is not None}, "
                f"strategy_analysis={strategy_analysis is not None}, "
                f"asset_analysis={asset_analysis is not None}"
            )

            self.logger.info(
                f"Confidence values: signal={signal_confidence:.1f}, "
                f"convergence={convergence_confidence:.1f}, "
                f"sample_size={sample_size_confidence:.1f}, "
                f"data_quality={data_quality_confidence:.1f}"
            )

            # Weighted average
            weights = [
                0.4,
                0.3,
                0.2,
                0.1,
            ]  # Signal, convergence, sample size, data quality
            confidences = [
                signal_confidence,
                convergence_confidence,
                sample_size_confidence,
                data_quality_confidence,
            ]

            calculated_confidence = sum(
                w * c for w, c in zip(weights, confidences, strict=False)
            )
            self.logger.info(
                f"Final calculated confidence: {calculated_confidence:.1f}"
            )

            return calculated_confidence

        except Exception as e:
            self.logger.error(f"Failed to calculate overall confidence: {e}")
            return 50.0  # Default confidence

    def _generate_recommendation_summary(
        self,
        exit_signal: ProbabilisticExitSignal,
        convergence: DualLayerConvergence,
        overall_confidence: float,
    ) -> str:
        """Generate human-readable recommendation summary"""
        signal_descriptions = {
            SignalType.EXIT_IMMEDIATELY: "Strong statistical exhaustion detected - exit immediately",
            SignalType.STRONG_SELL: "High probability of diminishing returns - consider exiting soon",
            SignalType.SELL: "Performance approaching statistical limits - prepare to exit",
            SignalType.HOLD: "Continue monitoring position - no immediate exit required",
            SignalType.TIME_EXIT: "Time-based exit criteria met",
        }

        base_summary = signal_descriptions.get(
            exit_signal.signal_type, "Unknown signal"
        )

        # Add confidence qualifier
        if overall_confidence >= 90:
            confidence_qualifier = "Very high confidence"
        elif overall_confidence >= 75:
            confidence_qualifier = "High confidence"
        elif overall_confidence >= 60:
            confidence_qualifier = "Moderate confidence"
        else:
            confidence_qualifier = "Low confidence"

        # Add convergence information
        if convergence.convergence_score >= 0.85:
            convergence_qualifier = "strong dual-layer agreement"
        elif convergence.convergence_score >= 0.70:
            convergence_qualifier = "moderate dual-layer agreement"
        else:
            convergence_qualifier = "weak dual-layer agreement"

        return f"{base_summary}. {confidence_qualifier} with {convergence_qualifier}."

    def _get_config_hash(self) -> str:
        """Generate configuration hash for reproducibility"""
        import hashlib

        config_str = str(sorted(self.config.to_dict().items()))
        return hashlib.md5(config_str.encode(), usedforsecurity=False).hexdigest()[:8]

    def _get_data_sources_used(self, use_trade_history: bool) -> list[DataSource]:
        """Get list of data sources used in analysis"""
        sources = [DataSource.RETURN_DISTRIBUTION]
        if use_trade_history:
            sources.append(DataSource.TRADE_HISTORY)
        else:
            sources.append(DataSource.EQUITY_CURVES)
        return sources

    def _update_metrics(
        self, result: StatisticalAnalysisResult, processing_time: float
    ):
        """Update service metrics"""
        self.metrics["analyses_performed"] += 1
        self.metrics["total_processing_time"] += processing_time

        if len(result.data_sources_used) > 1:
            self.metrics["dual_layer_analyses"] += 1

        if DataSource.TRADE_HISTORY in result.data_sources_used:
            self.metrics["trade_history_analyses"] += 1

        if result.strategy_analysis.bootstrap_results:
            self.metrics["bootstrap_validations"] += 1

        if result.overall_confidence >= 85:
            self.metrics["high_confidence_signals"] += 1

    def get_service_metrics(self) -> dict[str, Any]:
        """Get service performance metrics"""
        metrics = self.metrics.copy()
        if metrics["analyses_performed"] > 0:
            metrics["average_processing_time"] = (
                metrics["total_processing_time"] / metrics["analyses_performed"]
            )
            metrics["dual_layer_percentage"] = (
                metrics["dual_layer_analyses"] / metrics["analyses_performed"]
            ) * 100
            metrics["high_confidence_percentage"] = (
                metrics["high_confidence_signals"] / metrics["analyses_performed"]
            ) * 100
        return metrics

    async def health_check(self) -> dict[str, Any]:
        """Perform service health check including coordinator status"""
        health_status = {
            "service": "StatisticalAnalysisService",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "use_trade_history": self.config.USE_TRADE_HISTORY,
                "memory_optimization": self.enable_memory_optimization,
                "bootstrap_enabled": self.config.ENABLE_BOOTSTRAP,
                "coordinator_enabled": self.use_coordinator,
            },
            "metrics": self.get_service_metrics(),
        }

        # Check coordinator health if enabled
        if self.use_coordinator and self.data_coordinator:
            try:
                coordinator_status = self.data_coordinator.get_coordination_status()
                health_status["coordinator_status"] = coordinator_status

                # Check if coordinator has critical issues
                data_sources = coordinator_status.get("data_sources", {})
                if not any(data_sources.values()):
                    health_status["status"] = "degraded"
                    health_status[
                        "coordinator_warning"
                    ] = "No data sources available via coordinator"

            except Exception as coord_error:
                health_status["status"] = "degraded"
                health_status["coordinator_error"] = str(coord_error)

        # Check data source availability (legacy fallback)
        try:
            return_dist_path = Path(self.config.RETURN_DISTRIBUTION_PATH)
            health_status["legacy_data_sources"] = {
                "return_distribution_path_exists": return_dist_path.exists(),
                "trade_history_path_exists": Path(
                    self.config.TRADE_HISTORY_PATH
                ).exists(),
                "equity_paths_exist": [
                    Path(p).exists() for p in self.config.EQUITY_DATA_PATHS
                ],
            }

            # If coordinator is disabled, legacy data sources are primary
            if not self.use_coordinator:
                health_status["data_sources"] = health_status["legacy_data_sources"]

        except Exception as e:
            health_status["status"] = "degraded"
            health_status["error"] = str(e)

        return health_status

    def _extract_raw_analysis_data(
        self,
        current_position_data: dict[str, Any] | None,
        use_trade_history: bool,
        strategy_analysis: StrategyDistributionAnalysis,
        asset_analysis: AssetDistributionAnalysis,
    ) -> dict[str, Any] | None:
        """Extract raw analysis data for backtesting parameter generation"""
        try:
            raw_data = {
                "returns": [],
                "durations": [],
                "data_source": (
                    "trade_history" if use_trade_history else "equity_curves"
                ),
            }

            if use_trade_history and current_position_data:
                # Extract from trade history
                if isinstance(current_position_data, list):
                    for trade in current_position_data:
                        # Extract return data
                        if "Return_Pct" in trade and trade["Return_Pct"] is not None:
                            with contextlib.suppress(ValueError, TypeError):
                                raw_data["returns"].append(float(trade["Return_Pct"]))

                        # Extract duration data (in days)
                        if (
                            "Duration_Days" in trade
                            and trade["Duration_Days"] is not None
                        ):
                            with contextlib.suppress(ValueError, TypeError):
                                raw_data["durations"].append(
                                    int(trade["Duration_Days"])
                                )

                        # Alternative duration calculation from dates
                        elif "Entry_Date" in trade and "Exit_Date" in trade:
                            try:
                                from datetime import datetime

                                entry_date = datetime.strptime(
                                    str(trade["Entry_Date"]), "%Y-%m-%d"
                                )
                                exit_date = datetime.strptime(
                                    str(trade["Exit_Date"]), "%Y-%m-%d"
                                )
                                duration = (exit_date - entry_date).days
                                if duration > 0:
                                    raw_data["durations"].append(duration)
                            except (ValueError, TypeError):
                                pass

                self.logger.info(
                    f"Extracted {len(raw_data['returns'])} returns and {len(raw_data['durations'])} durations from trade history"
                )

            else:
                # Extract from statistical analysis (equity curves)
                # Use strategy analysis statistics for returns estimation
                if strategy_analysis and strategy_analysis.statistics:
                    stats = strategy_analysis.statistics

                    # Generate synthetic returns based on statistical properties
                    # This is an approximation for backtesting parameter generation
                    import numpy as np

                    np.random.seed(42)  # For reproducibility

                    # Generate returns based on mean, std, and distribution shape
                    sample_size = min(stats.count, 1000)  # Cap at 1000 for performance

                    if stats.mean and stats.std and sample_size > 0:
                        # Constrain statistical parameters to realistic daily trading ranges
                        # Daily returns typically don't exceed ±50% except in extreme cases
                        constrained_mean = max(
                            -0.10, min(0.10, stats.mean)
                        )  # ±10% daily mean
                        constrained_std = max(
                            0.005, min(0.08, stats.std)
                        )  # 0.5% to 8% daily volatility

                        # Generate normal distribution with constrained parameters
                        base_returns = np.random.normal(
                            constrained_mean, constrained_std, sample_size
                        )

                        # Apply skewness adjustment if available, but keep it modest
                        if hasattr(stats, "skewness") and stats.skewness:
                            # Much smaller skewness adjustment to keep returns realistic
                            skew_adjustment = (
                                np.clip(stats.skewness, -2.0, 2.0)
                                * constrained_std
                                * 0.05
                            )
                            base_returns = base_returns + skew_adjustment

                        # Final clipping to ensure no extreme outliers
                        base_returns = np.clip(
                            base_returns, -0.25, 0.50
                        )  # ±25% to +50% daily range

                        raw_data["returns"] = base_returns.tolist()

                    # Generate realistic strategy-specific durations
                    if asset_analysis and asset_analysis.statistics:
                        # Create strategy-specific duration profiles based on volatility and returns
                        asset_vol = max(
                            0.005, min(0.08, asset_analysis.statistics.std)
                        )  # Constrain volatility
                        strategy_return = (
                            max(-0.10, min(0.10, strategy_analysis.statistics.mean))
                            if strategy_analysis.statistics.mean
                            else 0.02
                        )

                        # Strategy-specific duration calculation
                        # High volatility = shorter durations, high returns = potentially longer durations
                        volatility_factor = (
                            asset_vol / 0.02
                        )  # Normalize around 2% daily vol
                        return_factor = max(
                            0.5, min(2.0, 1.0 + strategy_return * 5)
                        )  # Return influence

                        # Base duration: 15-45 days scaled by factors
                        base_duration = int(30 / volatility_factor * return_factor)
                        base_duration = max(
                            5, min(90, base_duration)
                        )  # Realistic range

                        # Create realistic duration distribution with strategy variation
                        # Use different distribution shapes for different strategies
                        np.random.seed(
                            hash(strategy_analysis.statistics.mean + asset_vol)
                            % 2**32
                        )  # Strategy-specific seed

                        # Generate mixed distribution: some short-term, some medium-term, few long-term
                        short_term = np.random.gamma(
                            2, base_duration * 0.3, sample_size // 3
                        )  # 1/3 short positions
                        medium_term = np.random.gamma(
                            3, base_duration * 0.6, sample_size // 2
                        )  # 1/2 medium positions
                        long_term = np.random.gamma(
                            4,
                            base_duration * 1.2,
                            sample_size - len(short_term) - len(medium_term),
                        )  # Remainder long

                        # Combine and add strategy-specific variation
                        all_durations = np.concatenate(
                            [short_term, medium_term, long_term]
                        )

                        # Add some noise for realism
                        noise = np.random.normal(
                            0, base_duration * 0.1, len(all_durations)
                        )
                        all_durations = all_durations + noise

                        # Clip to realistic bounds and convert to integers
                        durations = np.clip(all_durations, 1, 180).astype(
                            int
                        )  # 1 day to 6 months max

                        # Shuffle to randomize order
                        np.random.shuffle(durations)
                        raw_data["durations"] = durations.tolist()

                self.logger.info(
                    f"Estimated {len(raw_data['returns'])} returns and {len(raw_data['durations'])} durations from statistical analysis"
                )

            # Only return data if we have meaningful content
            if len(raw_data["returns"]) > 0 or len(raw_data["durations"]) > 0:
                return raw_data
            return None

        except Exception as e:
            self.logger.error(f"Failed to extract raw analysis data: {e}")
            return None

    def _extract_asset_analysis_from_coordinated_data(
        self, strategy_data, ticker: str
    ) -> AssetDistributionAnalysis:
        """Extract asset distribution analysis from coordinated strategy data"""
        try:
            # Check if we have return distribution data in the coordinated data
            raw_data = strategy_data.raw_analysis_data or {}

            # Try to extract asset-level distribution data
            asset_analysis = raw_data.get("asset_analysis", {})
            if not asset_analysis:
                # Fallback to loading directly from file
                raise ValueError("No asset analysis data in coordinated data")

            # Extract statistical metrics
            stats = asset_analysis.get("statistics", {})
            statistical_metrics = StatisticalMetrics(
                mean=float(stats.get("mean", 0.0)),
                median=float(stats.get("median", 0.0)),
                std=float(stats.get("std", 0.0)),
                min=float(stats.get("min", 0.0)),
                max=float(stats.get("max", 0.0)),
                skewness=float(stats.get("skewness", 0.0)),
                kurtosis=float(stats.get("kurtosis", 0.0)),
                count=int(stats.get("count", 0)),
            )

            # Extract percentile metrics
            percentiles_data = asset_analysis.get("percentiles", {})
            percentiles = PercentileMetrics(
                p5=float(percentiles_data.get("5", 0.0)),
                p10=float(percentiles_data.get("10", 0.0)),
                p25=float(percentiles_data.get("25", 0.0)),
                p50=float(percentiles_data.get("50", 0.0)),
                p75=float(percentiles_data.get("75", 0.0)),
                p90=float(percentiles_data.get("90", 0.0)),
                p95=float(percentiles_data.get("95", 0.0)),
                p99=float(percentiles_data.get("99", 0.0)),
            )

            # Extract VaR metrics
            var_data = asset_analysis.get("var_metrics", {})
            var_metrics = VaRMetrics(
                var_95=float(var_data.get("var_95", 0.0)),
                var_99=float(var_data.get("var_99", 0.0)),
                expected_shortfall_95=float(var_data.get("expected_shortfall_95", 0.0)),
                expected_shortfall_99=float(var_data.get("expected_shortfall_99", 0.0)),
            )

            # Extract additional data
            current_return = asset_analysis.get("current_return")
            current_percentile = asset_analysis.get("current_percentile")
            regime_score = asset_analysis.get("regime_score", 0.0)
            volatility_regime = asset_analysis.get("volatility_regime", "medium")

            # Create asset distribution analysis
            return AssetDistributionAnalysis(
                ticker=ticker,
                timeframe="D",
                data_source=DataSource.RETURN_DISTRIBUTION,
                statistics=statistical_metrics,
                percentiles=percentiles,
                var_metrics=var_metrics,
                current_return=current_return,
                current_percentile=current_percentile,
                regime_score=regime_score,
                volatility_regime=volatility_regime,
                last_updated=datetime.now(),
                sample_period_start=datetime.now().date(),
                sample_period_end=datetime.now().date(),
            )

        except Exception as e:
            self.logger.error(
                f"Failed to extract asset analysis from coordinated data: {e}"
            )
            # Re-raise to trigger fallback to direct file loading
            raise

    def _extract_strategy_analysis_from_coordinated_data(
        self, strategy_data, use_trade_history: bool
    ) -> StrategyDistributionAnalysis:
        """Extract strategy distribution analysis from coordinated strategy data"""
        try:
            # Extract core statistical metrics from coordinated data
            stats = StatisticalMetrics(
                mean=float(strategy_data.performance.current_return),
                median=float(strategy_data.performance.current_return),  # Approximation
                std=0.02,  # Default volatility estimate
                min=(
                    float(strategy_data.performance.mae)
                    if strategy_data.performance.mae
                    else -0.1
                ),
                max=(
                    float(strategy_data.performance.mfe)
                    if strategy_data.performance.mfe
                    else 0.1
                ),
                skewness=0.0,  # Default
                kurtosis=0.0,  # Default
                count=(
                    int(strategy_data.statistics.sample_size)
                    if strategy_data.statistics.sample_size
                    else 100
                ),
            )

            # Create percentile metrics from available data
            percentiles = PercentileMetrics(
                p5=(
                    float(strategy_data.performance.mae)
                    if strategy_data.performance.mae
                    else -0.05
                ),
                p10=(
                    float(strategy_data.performance.mae) * 0.8
                    if strategy_data.performance.mae
                    else -0.04
                ),
                p25=(
                    float(strategy_data.performance.mae) * 0.5
                    if strategy_data.performance.mae
                    else -0.025
                ),
                p50=0.0,  # Median
                p75=(
                    float(strategy_data.performance.mfe) * 0.5
                    if strategy_data.performance.mfe
                    else 0.025
                ),
                p90=(
                    float(strategy_data.performance.mfe) * 0.8
                    if strategy_data.performance.mfe
                    else 0.04
                ),
                p95=(
                    float(strategy_data.performance.mfe)
                    if strategy_data.performance.mfe
                    else 0.05
                ),
                p99=(
                    float(strategy_data.performance.mfe) * 1.2
                    if strategy_data.performance.mfe
                    else 0.06
                ),
            )

            # Create VaR metrics
            var_metrics = VaRMetrics(
                var_95=percentiles.p5,
                var_99=percentiles.p5 * 1.5,
                expected_shortfall_95=percentiles.p5 * 1.2,
                expected_shortfall_99=percentiles.p5 * 1.8,
            )

            # Extract additional strategy metrics
            win_rate = None  # Not available from coordinated data
            profit_factor = None
            sharpe_ratio = None
            max_drawdown = (
                -abs(float(strategy_data.performance.mae))
                if strategy_data.performance.mae
                else None
            )

            # Confidence assessment
            confidence_level = (
                ConfidenceLevel.HIGH
                if strategy_data.statistics.sample_size > 1000
                else ConfidenceLevel.MEDIUM
            )
            confidence_score = (
                float(strategy_data.statistics.sample_size_confidence)
                if strategy_data.statistics.sample_size_confidence
                else 0.7
            )

            # Bootstrap results (not available from coordinated data)
            bootstrap_results = None

            return StrategyDistributionAnalysis(
                strategy_name=strategy_data.strategy_name,
                ticker=strategy_data.ticker,
                timeframe=strategy_data.timeframe or "D",
                data_sources_used=[
                    (
                        DataSource.TRADE_HISTORY
                        if use_trade_history
                        else DataSource.EQUITY_CURVES
                    )
                ],
                combined_confidence=confidence_score,
                data_source=(
                    DataSource.TRADE_HISTORY
                    if use_trade_history
                    else DataSource.EQUITY_CURVES
                ),
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=self._safe_max_drawdown(max_drawdown),
                mfe_statistics=None,
                mae_statistics=None,
                duration_statistics=None,
                bootstrap_results=bootstrap_results,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to extract strategy analysis from coordinated data: {e}"
            )
            # Re-raise to trigger fallback to legacy analysis methods
            raise

    async def _analyze_trade_history_performance_raw(
        self, strategy_name: str, ticker: str
    ) -> TradeHistoryAnalysis:
        """Analyze strategy performance using trade history data returning raw TradeHistoryAnalysis"""
        try:
            # Use trade history analyzer
            trade_data = await self.trade_history_analyzer.analyze_strategy_trades(
                strategy_name, ticker
            )

            # Calculate additional trade-specific metrics
            mfe_values = trade_data.get("mfe_values", [])
            mae_values = trade_data.get("mae_values", [])
            durations = trade_data.get("durations", [])

            # MFE statistics
            mfe_statistics = self._calculate_statistical_metrics(
                pd.Series(mfe_values) if mfe_values else pd.Series([0])
            )

            # MAE statistics
            mae_statistics = self._calculate_statistical_metrics(
                pd.Series(mae_values) if mae_values else pd.Series([0])
            )

            # Duration statistics
            duration_statistics = self._calculate_statistical_metrics(
                pd.Series(durations) if durations else pd.Series([0])
            )

            # Trade quality metrics
            total_trades = trade_data.get("total_trades", 0)
            winning_trades = trade_data.get("winning_trades", 0)
            losing_trades = total_trades - winning_trades

            # Exit efficiency calculations
            average_exit_efficiency = 0.7  # Default estimate
            mfe_capture_ratio = 0.6  # Default estimate

            if mfe_values and trade_data.get("returns"):
                returns = trade_data["returns"]
                if len(returns) == len(mfe_values):
                    # Calculate actual capture ratio
                    positive_returns = [r for r in returns if r > 0]
                    positive_mfe = [
                        mfe_values[i] for i, r in enumerate(returns) if r > 0
                    ]
                    if positive_returns and positive_mfe:
                        mfe_capture_ratio = sum(positive_returns) / sum(positive_mfe)
                        mfe_capture_ratio = min(1.0, max(0.0, mfe_capture_ratio))

            # Confidence assessment
            confidence_level = self.config.get_confidence_level(total_trades)
            confidence_score = self.config.get_confidence_threshold(total_trades)

            return TradeHistoryAnalysis(
                statistics=trade_data["return_statistics"],
                percentiles=trade_data["return_percentiles"],
                var_metrics=trade_data["var_metrics"],
                mfe_statistics=mfe_statistics,
                mae_statistics=mae_statistics,
                duration_statistics=duration_statistics,
                win_rate=trade_data.get("win_rate", 0.0),
                profit_factor=trade_data.get("profit_factor", 1.0),
                average_exit_efficiency=average_exit_efficiency,
                mfe_capture_ratio=mfe_capture_ratio,
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to analyze trade history for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _analyze_equity_curve_performance_raw(
        self, strategy_name: str, ticker: str
    ) -> EquityAnalysis:
        """Analyze strategy performance using equity curve data returning raw EquityAnalysis"""
        try:
            # Search for equity data files
            equity_file = None
            for equity_path in self.config.EQUITY_DATA_PATHS:
                # Try the correct naming pattern: {strategy_name}.csv
                potential_file = Path(equity_path) / f"{strategy_name}.csv"
                if potential_file.exists():
                    equity_file = potential_file
                    break

                # Fallback to old naming pattern for compatibility
                potential_file_old = (
                    Path(equity_path) / f"{strategy_name}_{ticker}_equity.csv"
                )
                if potential_file_old.exists():
                    equity_file = potential_file_old
                    break

            if not equity_file:
                raise FileNotFoundError(
                    f"Equity data not found for {strategy_name} on {ticker}"
                )

            # Load and process equity data
            if self.enable_memory_optimization:
                df = self.memory_optimizer.read_csv_optimized(str(equity_file))
            else:
                df = pd.read_csv(equity_file)

            # Calculate returns from equity curve
            if "equity_change_pct" in df.columns:
                returns = df["equity_change_pct"].dropna()
            elif "equity" in df.columns:
                returns = df["equity"].pct_change().dropna()
            else:
                raise ValueError("No suitable equity column found in data")

            # Calculate statistics
            stats = self._calculate_statistical_metrics(returns)
            percentiles = self._calculate_percentile_metrics(returns)
            var_metrics = self._calculate_var_metrics(returns)

            # Performance metrics
            sharpe_ratio = (
                returns.mean() / returns.std() * np.sqrt(252)
                if returns.std() > 0
                else 0.0
            )

            max_drawdown = self._calculate_max_drawdown(
                df.get("equity", returns.cumsum())
            )

            # Recovery factor (total return / max drawdown)
            total_return = returns.sum()
            recovery_factor = 0.0
            if max_drawdown != 0 and np.isfinite(max_drawdown):
                rf_value = abs(total_return / max_drawdown)
                if np.isfinite(rf_value):
                    recovery_factor = rf_value

            # Calmar ratio (annualized return / max drawdown)
            annualized_return = returns.mean() * 252
            calmar_ratio = 0.0
            if max_drawdown != 0 and np.isfinite(max_drawdown):
                cr_value = abs(annualized_return / max_drawdown)
                if np.isfinite(cr_value):
                    calmar_ratio = cr_value

            # Volatility metrics
            volatility = returns.std() * np.sqrt(252)  # Annualized volatility
            downside_returns = returns[returns < 0]
            downside_deviation = (
                downside_returns.std() * np.sqrt(252)
                if len(downside_returns) > 0
                else 0.0
            )

            # Confidence assessment
            confidence_level = self.config.get_confidence_level(len(returns))
            confidence_score = self.config.get_confidence_threshold(len(returns))

            return EquityAnalysis(
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=self._safe_max_drawdown(max_drawdown),
                recovery_factor=recovery_factor,
                calmar_ratio=calmar_ratio,
                volatility=volatility,
                downside_deviation=downside_deviation,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to analyze equity curve for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _combine_strategy_analyses(
        self,
        strategy_name: str,
        ticker: str,
        trade_history_analysis: TradeHistoryAnalysis | None,
        equity_analysis: EquityAnalysis | None,
    ) -> StrategyDistributionAnalysis:
        """Combine trade history and equity curve analyses into unified StrategyDistributionAnalysis"""
        try:
            # Determine data sources used
            data_sources_used = []
            if trade_history_analysis:
                data_sources_used.append(DataSource.TRADE_HISTORY)
            if equity_analysis:
                data_sources_used.append(DataSource.EQUITY_CURVES)

            # Select primary source for combined metrics (prefer trade history)
            primary_analysis = (
                trade_history_analysis if trade_history_analysis else equity_analysis
            )

            if not primary_analysis:
                raise ValueError("At least one analysis must be provided")

            # Calculate convergence between sources if both are available
            dual_source_convergence = None
            if trade_history_analysis and equity_analysis:
                dual_source_convergence = await self._calculate_dual_source_convergence(
                    trade_history_analysis, equity_analysis
                )

            # Combined confidence assessment
            analysis_agreement_score = None
            combined_confidence = primary_analysis.confidence_score

            if dual_source_convergence:
                analysis_agreement_score = dual_source_convergence.convergence_score
                # Weight confidence by convergence strength
                combined_confidence = (
                    primary_analysis.confidence_score * 0.7
                    + dual_source_convergence.convergence_score * 0.3
                )

            # Source agreement summary for reporting
            if trade_history_analysis and equity_analysis:
                pass

            # Extract combined metrics (prioritize trade history, fallback to equity)
            win_rate = (
                trade_history_analysis.win_rate if trade_history_analysis else None
            )
            profit_factor = (
                trade_history_analysis.profit_factor if trade_history_analysis else None
            )
            sharpe_ratio = equity_analysis.sharpe_ratio if equity_analysis else None

            # Handle max_drawdown with NaN validation
            max_drawdown = None
            if equity_analysis and equity_analysis.max_drawdown is not None:
                if not (
                    np.isnan(equity_analysis.max_drawdown)
                    or np.isinf(equity_analysis.max_drawdown)
                ):
                    max_drawdown = equity_analysis.max_drawdown
                else:
                    max_drawdown = 0.0  # Fallback for NaN/inf values

            # Legacy fields for backward compatibility
            mfe_statistics = (
                trade_history_analysis.mfe_statistics
                if trade_history_analysis
                else None
            )
            mae_statistics = (
                trade_history_analysis.mae_statistics
                if trade_history_analysis
                else None
            )
            duration_statistics = (
                trade_history_analysis.duration_statistics
                if trade_history_analysis
                else None
            )

            return StrategyDistributionAnalysis(
                strategy_name=strategy_name,
                ticker=ticker,
                timeframe="D",  # Default timeframe
                data_sources_used=data_sources_used,
                trade_history_analysis=trade_history_analysis,
                equity_analysis=equity_analysis,
                dual_source_convergence=dual_source_convergence,
                statistics=primary_analysis.statistics,
                percentiles=primary_analysis.percentiles,
                var_metrics=primary_analysis.var_metrics,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=self._safe_max_drawdown(max_drawdown),
                mfe_statistics=mfe_statistics,
                mae_statistics=mae_statistics,
                duration_statistics=duration_statistics,
                bootstrap_results=None,  # Can be added later if needed
                confidence_level=primary_analysis.confidence_level,
                confidence_score=primary_analysis.confidence_score,
                analysis_agreement_score=analysis_agreement_score,
                combined_confidence=combined_confidence,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to combine strategy analyses for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _calculate_dual_source_convergence(
        self,
        trade_history_analysis: TradeHistoryAnalysis,
        equity_analysis: EquityAnalysis,
    ) -> DualSourceConvergence:
        """Calculate convergence metrics between trade history and equity curve analyses"""
        try:
            # Compare return characteristics
            th_mean = trade_history_analysis.statistics.mean
            eq_mean = equity_analysis.statistics.mean

            th_std = trade_history_analysis.statistics.std
            eq_std = equity_analysis.statistics.std

            # Calculate correlation proxy (normalized difference in means and stds)
            mean_agreement = 1.0 - min(
                1.0, abs(th_mean - eq_mean) / max(abs(th_mean), abs(eq_mean), 0.01)
            )
            std_agreement = 1.0 - min(
                1.0, abs(th_std - eq_std) / max(th_std, eq_std, 0.01)
            )

            return_correlation = (mean_agreement + std_agreement) / 2.0

            # Performance agreement (compare win rates vs positive returns)
            th_win_rate = trade_history_analysis.win_rate
            eq_positive_rate = (
                1.0  # Placeholder - would need actual equity return distribution
            )
            performance_agreement = 1.0 - abs(th_win_rate - eq_positive_rate)

            # Risk agreement (compare VaR metrics)
            th_var95 = trade_history_analysis.var_metrics.var_95
            eq_var95 = equity_analysis.var_metrics.var_95
            risk_agreement = 1.0 - min(
                1.0, abs(th_var95 - eq_var95) / max(abs(th_var95), abs(eq_var95), 0.01)
            )

            # Overall convergence score
            convergence_score = (
                return_correlation + performance_agreement + risk_agreement
            ) / 3.0

            # Convergence strength classification
            if convergence_score >= 0.8:
                convergence_strength = "strong"
            elif convergence_score >= 0.6:
                convergence_strength = "moderate"
            else:
                convergence_strength = "weak"

            # Divergence detection
            has_significant_divergence = convergence_score < 0.5
            divergence_explanation = None
            if has_significant_divergence:
                divergence_explanation = f"Low convergence score ({convergence_score:.2f}) indicates significant differences between trade history and equity curve analysis"

            return DualSourceConvergence(
                return_correlation=return_correlation,
                performance_agreement=performance_agreement,
                risk_agreement=risk_agreement,
                convergence_score=convergence_score,
                convergence_strength=convergence_strength,
                has_significant_divergence=has_significant_divergence,
                divergence_explanation=divergence_explanation,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate dual source convergence: {e}")
            # Return default convergence result
            return DualSourceConvergence(
                convergence_score=0.5,
                convergence_strength="moderate",
                has_significant_divergence=False,
            )

    def _generate_source_agreement_summary(
        self, strategy_analysis: StrategyDistributionAnalysis
    ) -> str:
        """Generate summary of agreement/divergence between data sources"""
        if not strategy_analysis.dual_source_convergence:
            # Single source analysis
            if DataSource.TRADE_HISTORY in strategy_analysis.data_sources_used:
                return "Single source analysis using trade history data"
            if DataSource.EQUITY_CURVES in strategy_analysis.data_sources_used:
                return "Single source analysis using equity curve data"
            return "Single source analysis"

        # Dual source analysis
        convergence = strategy_analysis.dual_source_convergence
        strength = convergence.convergence_strength
        score = convergence.convergence_score

        if convergence.has_significant_divergence:
            return f"Dual-source analysis with {strength} convergence ({score:.2f}). Significant divergence detected between trade history and equity curve data."
        return f"Dual-source analysis with {strength} convergence ({score:.2f}). Good agreement between trade history and equity curve data."

    def _generate_data_quality_assessment(
        self, strategy_analysis: StrategyDistributionAnalysis
    ) -> dict[str, str]:
        """Generate quality assessment for each data source"""
        assessment = {}

        if strategy_analysis.trade_history_analysis:
            total_trades = strategy_analysis.trade_history_analysis.total_trades
            confidence = strategy_analysis.trade_history_analysis.confidence_level.value
            assessment[
                "trade_history"
            ] = f"{confidence} confidence with {total_trades} trades"

        if strategy_analysis.equity_analysis:
            confidence = strategy_analysis.equity_analysis.confidence_level.value
            sharpe = strategy_analysis.equity_analysis.sharpe_ratio
            assessment[
                "equity_curves"
            ] = f"{confidence} confidence, Sharpe ratio: {sharpe:.2f}"

        if not assessment:
            assessment["unknown"] = "Data quality assessment unavailable"

        return assessment

    def _calculate_asset_layer_contribution(
        self,
        asset_analysis: AssetDistributionAnalysis,
        asset_divergence: DivergenceMetrics,
    ) -> float:
        """Calculate asset layer contribution to exit signal"""
        # Base contribution from asset divergence strength
        divergence_strength = asset_divergence.rarity_score

        # Adjust for volatility regime
        regime_adjustment = {"low": 0.8, "medium": 1.0, "high": 1.2}.get(
            asset_analysis.volatility_regime, 1.0
        )

        # Adjust for sample size quality
        sample_quality = min(
            1.0, asset_analysis.statistics.count / self.config.PREFERRED_SAMPLE_SIZE
        )

        contribution = divergence_strength * regime_adjustment * sample_quality
        return min(1.0, max(0.0, contribution))

    def _calculate_trade_history_contribution(
        self, trade_history_analysis: TradeHistoryAnalysis
    ) -> float:
        """Calculate trade history contribution to exit signal"""
        # Base contribution from win rate deviation from 50%
        win_rate_deviation = abs(trade_history_analysis.win_rate - 0.5) * 2.0

        # Adjust for trade count quality
        trade_count_quality = min(1.0, trade_history_analysis.total_trades / 30.0)

        # Adjust for MFE capture efficiency
        mfe_efficiency = trade_history_analysis.mfe_capture_ratio

        # Adjust for confidence level
        confidence_multiplier = trade_history_analysis.confidence_score

        contribution = (
            win_rate_deviation
            * trade_count_quality
            * mfe_efficiency
            * confidence_multiplier
        )
        return min(1.0, max(0.0, contribution))

    def _calculate_equity_curve_contribution(
        self, equity_analysis: EquityAnalysis
    ) -> float:
        """Calculate equity curve contribution to exit signal"""
        # Base contribution from Sharpe ratio strength
        sharpe_strength = min(1.0, abs(equity_analysis.sharpe_ratio) / 2.0)

        # Adjust for drawdown severity (higher drawdown = stronger signal)
        drawdown_severity = min(1.0, abs(equity_analysis.max_drawdown) / 0.2)

        # Adjust for volatility
        volatility_factor = min(1.0, equity_analysis.volatility / 0.3)

        # Adjust for confidence level
        confidence_multiplier = equity_analysis.confidence_score

        contribution = (
            (sharpe_strength + drawdown_severity + volatility_factor)
            / 3.0
            * confidence_multiplier
        )
        return min(1.0, max(0.0, contribution))

    def _calculate_data_source_confidence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> dict[str, float]:
        """Calculate confidence scores for each data source"""
        confidence_scores = {}

        # Asset data confidence
        asset_sample_ratio = min(
            1.0, asset_analysis.statistics.count / self.config.PREFERRED_SAMPLE_SIZE
        )
        confidence_scores["asset"] = (
            asset_sample_ratio * 0.9
        )  # Asset data is generally reliable

        # Strategy data confidence
        if strategy_analysis.trade_history_analysis:
            trade_confidence = strategy_analysis.trade_history_analysis.confidence_score
            confidence_scores["trade_history"] = trade_confidence

        if strategy_analysis.equity_analysis:
            equity_confidence = strategy_analysis.equity_analysis.confidence_score
            confidence_scores["equity_curves"] = equity_confidence

        return confidence_scores

    def _calculate_combined_source_confidence(
        self,
        data_source_confidence: dict[str, float],
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate combined confidence from all data sources"""
        if not data_source_confidence:
            return 0.5  # Default

        # Weight sources by availability and quality
        total_confidence = 0.0
        total_weight = 0.0

        # Asset layer (always present)
        asset_confidence = data_source_confidence.get("asset", 0.5)
        total_confidence += asset_confidence * 0.3
        total_weight += 0.3

        # Trade history (if available)
        if "trade_history" in data_source_confidence:
            trade_confidence = data_source_confidence["trade_history"]
            total_confidence += trade_confidence * 0.4
            total_weight += 0.4

        # Equity curves (if available)
        if "equity_curves" in data_source_confidence:
            equity_confidence = data_source_confidence["equity_curves"]
            total_confidence += equity_confidence * 0.3
            total_weight += 0.3

        # Bonus for dual-source convergence
        if (
            strategy_analysis.dual_source_convergence
            and strategy_analysis.dual_source_convergence.convergence_score > 0.7
        ):
            convergence_bonus = (
                strategy_analysis.dual_source_convergence.convergence_score * 0.1
            )
            total_confidence += convergence_bonus

        combined_confidence = total_confidence / max(total_weight, 0.3)
        return min(1.0, max(0.1, combined_confidence))

    def _calculate_source_reliability_score(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        dual_layer_convergence: DualLayerConvergence,
    ) -> float:
        """Calculate overall source reliability assessment"""
        reliability_factors = []

        # Base reliability from convergence
        base_reliability = dual_layer_convergence.weighted_convergence_score
        reliability_factors.append(base_reliability)

        # Sample size reliability
        if strategy_analysis.trade_history_analysis:
            trade_sample_reliability = min(
                1.0, strategy_analysis.trade_history_analysis.total_trades / 50.0
            )
            reliability_factors.append(trade_sample_reliability)

        if strategy_analysis.equity_analysis:
            equity_sample_reliability = (
                strategy_analysis.equity_analysis.confidence_score
            )
            reliability_factors.append(equity_sample_reliability)

        # Convergence consistency reliability
        if strategy_analysis.dual_source_convergence:
            consistency_reliability = 1.0 - (
                1.0
                if strategy_analysis.dual_source_convergence.has_significant_divergence
                else 0.0
            )
            reliability_factors.append(consistency_reliability)

        # Calculate weighted average
        overall_reliability = (
            sum(reliability_factors) / len(reliability_factors)
            if reliability_factors
            else 0.5
        )
        return min(1.0, max(0.1, overall_reliability))

    def _calculate_enhanced_sample_size_confidence(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        combined_source_confidence: float,
    ) -> float:
        """Calculate enhanced sample size confidence with multi-source weighting"""
        base_confidence = strategy_analysis.confidence_score

        # Boost confidence if multiple high-quality sources agree
        if (
            strategy_analysis.trade_history_analysis
            and strategy_analysis.equity_analysis
            and strategy_analysis.dual_source_convergence
            and strategy_analysis.dual_source_convergence.convergence_score > 0.8
        ):
            multi_source_boost = 0.15  # 15% boost for strong dual-source agreement
            enhanced_confidence = base_confidence + multi_source_boost
        else:
            enhanced_confidence = base_confidence

        # Weight by combined source confidence
        final_confidence = enhanced_confidence * combined_source_confidence
        return min(1.0, max(0.1, final_confidence))

    def _determine_enhanced_signal_type(
        self,
        dual_layer_convergence: DualLayerConvergence,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
        primary_strength: float,
        strategy_analysis: StrategyDistributionAnalysis,
        component_scores: dict[str, Any] | None = None,
    ) -> SignalType:
        """Determine signal type with enhanced multi-source analysis"""
        # Base signal determination
        base_signal = self._determine_signal_type(
            dual_layer_convergence,
            asset_divergence,
            strategy_divergence,
            primary_strength,
        )

        # COMPONENT SCORE OVERRIDE: Check for extreme component scores and override signal if necessary
        component_override_signal = self._check_component_score_override(
            component_scores, base_signal
        )
        if component_override_signal is not None:
            self.logger.info(
                f"Component score override: changed {base_signal.value} to {component_override_signal.value}"
            )
            base_signal = component_override_signal

        # Enhanced logic for dual-source analysis - Complete Entry/Exit System
        if (
            strategy_analysis.trade_history_analysis
            and strategy_analysis.equity_analysis
            and strategy_analysis.dual_source_convergence
        ):
            convergence_score = (
                strategy_analysis.dual_source_convergence.convergence_score
            )

            # If sources strongly agree and both indicate extreme conditions
            if convergence_score > 0.8:
                trade_percentile = (
                    strategy_divergence.percentile_rank
                )  # Represents combined strategy

                # Entry signal enhancement with strong convergence
                if trade_percentile <= 10:  # Bottom 10% with strong convergence
                    return SignalType.STRONG_BUY
                if trade_percentile <= 20:  # Bottom 20% with strong convergence
                    return SignalType.BUY
                # Exit signal enhancement (existing logic)
                if trade_percentile > 95:
                    return SignalType.EXIT_IMMEDIATELY
                if trade_percentile > 90:
                    return SignalType.STRONG_SELL
                if trade_percentile > 80:
                    return SignalType.SELL

            # Balanced convergence (0.5-0.8) - require base signal validation
            elif 0.5 <= convergence_score <= 0.8:
                # Entry signals require at least 0.7 convergence (validated in base signal)
                # Exit signals can proceed with moderate convergence
                if base_signal in [SignalType.STRONG_BUY, SignalType.BUY]:
                    # Entry signals already validated convergence >= 0.7 in base signal
                    return base_signal
                if base_signal in [
                    SignalType.SELL,
                    SignalType.STRONG_SELL,
                    SignalType.EXIT_IMMEDIATELY,
                ]:
                    # Exit signals can proceed with moderate convergence
                    return base_signal

            # If sources disagree significantly, be more conservative
            elif convergence_score < 0.5:
                # Downgrade all aggressive signals when convergence is poor
                if base_signal in [SignalType.STRONG_BUY, SignalType.BUY]:
                    return SignalType.HOLD  # Entry signals require good convergence
                if base_signal in [
                    SignalType.EXIT_IMMEDIATELY,
                    SignalType.STRONG_SELL,
                ]:
                    return SignalType.SELL  # Downgrade aggressive exit signals
                if base_signal == SignalType.SELL:
                    return SignalType.HOLD  # Downgrade to hold

        return base_signal

    def _calculate_enhanced_base_confidence(
        self,
        primary_strength: float,
        secondary_strength: float,
        tertiary_strength: float,
        asset_layer_contribution: float,
        trade_history_contribution: float | None,
        equity_curve_contribution: float | None,
    ) -> float:
        """Calculate enhanced base confidence with multi-source contributions"""
        # Traditional layer-based confidence
        layer_confidence = (
            primary_strength + secondary_strength + tertiary_strength
        ) / 3.0

        # Multi-source contribution confidence
        source_contributions = [asset_layer_contribution]
        if trade_history_contribution is not None:
            source_contributions.append(trade_history_contribution)
        if equity_curve_contribution is not None:
            source_contributions.append(equity_curve_contribution)

        source_confidence = sum(source_contributions) / len(source_contributions)

        # Weighted combination with bonus for multiple sources
        if len(source_contributions) > 1:
            # Multi-source bonus
            multi_source_bonus = (len(source_contributions) - 1) * 0.05
            enhanced_confidence = (
                layer_confidence * 0.6 + source_confidence * 0.4 + multi_source_bonus
            ) * 100
        else:
            enhanced_confidence = (
                layer_confidence * 0.7 + source_confidence * 0.3
            ) * 100

        return min(100.0, max(10.0, enhanced_confidence))

    def _estimate_enhanced_expected_upside(
        self,
        signal_type: SignalType,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float | None:
        """Estimate expected upside with enhanced multi-source insights"""
        base_upside = self._estimate_expected_upside(
            signal_type, asset_divergence, strategy_divergence
        )

        # Enhance with dual-source insights
        if (
            strategy_analysis.trade_history_analysis
            and strategy_analysis.equity_analysis
            and strategy_analysis.dual_source_convergence
        ):
            # Use average MFE from trade history as upside estimate
            if hasattr(strategy_analysis.trade_history_analysis, "mfe_statistics"):
                avg_mfe = strategy_analysis.trade_history_analysis.mfe_statistics.mean
                if avg_mfe > 0:
                    trade_upside = avg_mfe * 0.7  # Conservative estimate

                    # Blend with base estimate if available
                    if base_upside is not None:
                        enhanced_upside = (base_upside + trade_upside) / 2.0
                    else:
                        enhanced_upside = trade_upside

                    return max(0.0, enhanced_upside)

        return base_upside

    def _generate_enhanced_risk_warning(
        self,
        signal_type: SignalType,
        strategy_analysis: StrategyDistributionAnalysis,
        dual_layer_convergence: DualLayerConvergence,
        source_divergence_warning: str | None,
    ) -> str | None:
        """Generate enhanced risk warning with multi-source considerations"""
        base_warning = self._generate_risk_warning(
            signal_type, strategy_analysis, dual_layer_convergence
        )

        warnings = []
        if base_warning:
            warnings.append(base_warning)

        # Add source divergence warning
        if source_divergence_warning:
            warnings.append(source_divergence_warning)

        # Add low convergence warning
        if dual_layer_convergence.weighted_convergence_score < 0.5:
            warnings.append(
                f"Low convergence across analysis layers (score: {dual_layer_convergence.weighted_convergence_score:.2f}). "
                "Signal reliability may be reduced."
            )

        # Add sample size warnings for dual-source analysis
        if (
            strategy_analysis.trade_history_analysis
            and strategy_analysis.trade_history_analysis.total_trades < 20
        ):
            warnings.append(
                f"Limited trade history ({strategy_analysis.trade_history_analysis.total_trades} trades). Consider additional validation."
            )

        return " ".join(warnings) if warnings else None

    def _check_component_score_override(
        self,
        component_scores: dict[str, Any] | None,
        base_signal: SignalType,
    ) -> SignalType | None:
        """
        Check component scores for extreme values and override signal if necessary.

        Complete Entry/Exit System: Handles both extreme negative scores (sell signals)
        and extreme positive scores (buy signals) with dual-layer convergence validation.
        """
        try:
            # Check if component scores are provided
            if component_scores is None or not isinstance(component_scores, dict):
                return None

            # Extract key component scores
            momentum_score = component_scores.get("momentum_score", 0)
            risk_score = component_scores.get("risk_score", 0)
            trend_score = component_scores.get("trend_score", 0)
            overall_score = component_scores.get("overall_score", 0)
            mean_reversion_score = component_scores.get("mean_reversion_score", 0)

            # Check dual-layer convergence requirement for entry signals
            dual_layer_convergence = component_scores.get("dual_layer_convergence", 0)

            # Define extreme thresholds for both directions
            # Positive thresholds for entry signals
            EXTREME_POSITIVE_THRESHOLD = +80  # Very positive scores
            SEVERE_POSITIVE_THRESHOLD = +95  # Extremely positive scores
            EXTREME_OVERALL_POSITIVE = +15  # Very positive overall scores

            # Negative thresholds for exit signals (existing)
            EXTREME_NEGATIVE_THRESHOLD = -80  # Very negative scores
            SEVERE_NEGATIVE_THRESHOLD = (
                -95
            )  # Extremely negative scores (like -96 momentum)
            EXTREME_OVERALL_NEGATIVE = -15  # Very negative overall scores

            # ENTRY SIGNAL OVERRIDES - Only if dual-layer convergence >= 0.7
            if dual_layer_convergence >= 0.7:
                # Check for extremely positive momentum (strong buy signal)
                if momentum_score >= SEVERE_POSITIVE_THRESHOLD:
                    self.logger.info(
                        f"Extreme positive momentum detected: {momentum_score} with convergence {dual_layer_convergence}. Overriding to STRONG_BUY"
                    )
                    return SignalType.STRONG_BUY

                # Check for very positive risk score (exceptional entry opportunity)
                if risk_score >= EXTREME_POSITIVE_THRESHOLD and overall_score > 0:
                    self.logger.info(
                        f"Positive risk score ({risk_score}) + positive overall ({overall_score}) with convergence {dual_layer_convergence}. Overriding to STRONG_BUY"
                    )
                    return SignalType.STRONG_BUY

                # Check for extremely positive overall score
                if overall_score >= EXTREME_OVERALL_POSITIVE:
                    self.logger.info(
                        f"Extreme positive overall score detected: {overall_score} with convergence {dual_layer_convergence}. Overriding to BUY"
                    )
                    return SignalType.BUY

                # Check for combination of multiple positive indicators
                positive_indicators = 0
                if momentum_score >= 50:
                    positive_indicators += 1
                if risk_score >= 30:
                    positive_indicators += 1
                if trend_score >= 30:
                    positive_indicators += 1
                if mean_reversion_score >= 30:
                    positive_indicators += 1
                if overall_score >= 10:
                    positive_indicators += 1

                # Multiple positive indicators should trigger BUY
                if positive_indicators >= 3:
                    self.logger.info(
                        f"Multiple positive indicators detected ({positive_indicators}) with convergence {dual_layer_convergence}. Overriding to BUY"
                    )
                    return SignalType.BUY

            # EXIT SIGNAL OVERRIDES (existing logic)
            # Check for extremely negative momentum (like the -96 case)
            if momentum_score <= SEVERE_NEGATIVE_THRESHOLD:
                self.logger.info(
                    f"Extreme negative momentum detected: {momentum_score}. Overriding to STRONG_SELL"
                )
                return SignalType.STRONG_SELL

            # Check for very negative momentum combined with negative overall
            if momentum_score <= EXTREME_NEGATIVE_THRESHOLD and overall_score < 0:
                self.logger.info(
                    f"Negative momentum ({momentum_score}) + negative overall ({overall_score}). Overriding to SELL"
                )
                return SignalType.SELL

            # Check for extremely negative overall score
            if overall_score <= EXTREME_OVERALL_NEGATIVE:
                self.logger.info(
                    f"Extreme negative overall score detected: {overall_score}. Overriding to SELL"
                )
                return SignalType.SELL

            # Check for combination of multiple negative indicators
            negative_indicators = 0
            if momentum_score <= -50:
                negative_indicators += 1
            if risk_score <= -30:
                negative_indicators += 1
            if mean_reversion_score <= -30:
                negative_indicators += 1
            if overall_score <= -10:
                negative_indicators += 1

            # Multiple severe negative indicators should trigger SELL
            if negative_indicators >= 3:
                self.logger.info(
                    f"Multiple negative indicators detected ({negative_indicators}). Overriding to SELL"
                )
                return SignalType.SELL

            # Don't override if component scores don't indicate extreme conditions
            return None

        except Exception as e:
            self.logger.error(f"Error in component score override check: {e}")
            return None

    def validate_signal_generation_for_extreme_scores(self) -> dict[str, Any]:
        """
        Validation method to test signal generation with extreme component scores.

        Complete Entry/Exit System: Tests both extreme negative scores (sell signals)
        and extreme positive scores (buy signals) with dual-layer convergence validation.
        Returns a report of test cases and their expected vs actual signals.
        """
        test_cases = [
            # EXIT SIGNAL TEST CASES (existing)
            {
                "name": "Extreme Negative Momentum (like MA_SMA_78_82)",
                "component_scores": {
                    "momentum_score": -96,
                    "risk_score": 3,
                    "trend_score": -1,
                    "overall_score": -17.7,
                    "mean_reversion_score": 1,
                    "volume_score": 5,
                    "dual_layer_convergence": 0.8,
                },
                "expected_signal": "STRONG_SELL",
            },
            {
                "name": "Multiple Negative Indicators",
                "component_scores": {
                    "momentum_score": -60,
                    "risk_score": -35,
                    "trend_score": -5,
                    "overall_score": -12,
                    "mean_reversion_score": -40,
                    "volume_score": 10,
                    "dual_layer_convergence": 0.6,
                },
                "expected_signal": "SELL",
            },
            {
                "name": "Extreme Negative Overall Score",
                "component_scores": {
                    "momentum_score": -30,
                    "risk_score": 10,
                    "trend_score": 5,
                    "overall_score": -20,
                    "mean_reversion_score": 0,
                    "volume_score": 15,
                    "dual_layer_convergence": 0.5,
                },
                "expected_signal": "SELL",
            },
            # ENTRY SIGNAL TEST CASES (new)
            {
                "name": "Extreme Positive Momentum with Strong Convergence",
                "component_scores": {
                    "momentum_score": 96,
                    "risk_score": 15,
                    "trend_score": 20,
                    "overall_score": 18.5,
                    "mean_reversion_score": 10,
                    "volume_score": 25,
                    "dual_layer_convergence": 0.85,
                },
                "expected_signal": "STRONG_BUY",
            },
            {
                "name": "High Risk Score with Positive Overall and Strong Convergence",
                "component_scores": {
                    "momentum_score": 40,
                    "risk_score": 85,
                    "trend_score": 15,
                    "overall_score": 12,
                    "mean_reversion_score": 20,
                    "volume_score": 30,
                    "dual_layer_convergence": 0.8,
                },
                "expected_signal": "STRONG_BUY",
            },
            {
                "name": "Multiple Positive Indicators with Good Convergence",
                "component_scores": {
                    "momentum_score": 60,
                    "risk_score": 35,
                    "trend_score": 40,
                    "overall_score": 15,
                    "mean_reversion_score": 35,
                    "volume_score": 25,
                    "dual_layer_convergence": 0.75,
                },
                "expected_signal": "BUY",
            },
            {
                "name": "Extreme Positive Overall Score with Adequate Convergence",
                "component_scores": {
                    "momentum_score": 20,
                    "risk_score": 10,
                    "trend_score": 25,
                    "overall_score": 22,
                    "mean_reversion_score": 15,
                    "volume_score": 20,
                    "dual_layer_convergence": 0.7,
                },
                "expected_signal": "BUY",
            },
            {
                "name": "Positive Scores but Insufficient Convergence (should remain HOLD)",
                "component_scores": {
                    "momentum_score": 70,
                    "risk_score": 40,
                    "trend_score": 30,
                    "overall_score": 15,
                    "mean_reversion_score": 25,
                    "volume_score": 35,
                    "dual_layer_convergence": 0.6,  # Below 0.7 threshold
                },
                "expected_signal": "HOLD",
            },
            {
                "name": "Normal Scores (should remain HOLD)",
                "component_scores": {
                    "momentum_score": -20,
                    "risk_score": 5,
                    "trend_score": 2,
                    "overall_score": -3,
                    "mean_reversion_score": 0,
                    "volume_score": 10,
                    "dual_layer_convergence": 0.5,
                },
                "expected_signal": "HOLD",
            },
        ]

        results = []

        for test_case in test_cases:
            # Create mock strategy analysis with component scores
            from ..models.statistical_analysis_models import (
                ConfidenceLevel,
                DataSource,
                PercentileMetrics,
                StatisticalMetrics,
                StrategyDistributionAnalysis,
                VaRMetrics,
            )

            StrategyDistributionAnalysis(
                strategy_name=f"TEST_{test_case['name'].replace(' ', '_')}",
                ticker="TEST",
                timeframe="D",
                data_sources_used=[DataSource.TRADE_HISTORY],
                statistics=StatisticalMetrics(
                    mean=0.0,
                    median=0.0,
                    std=1.0,
                    min_value=-1.0,
                    max_value=1.0,
                    skewness=0.0,
                    kurtosis=0.0,
                    count=100,
                ),
                percentiles=PercentileMetrics(
                    p5=-2.0,
                    p10=-1.5,
                    p25=-0.5,
                    p50=0.0,
                    p75=0.5,
                    p90=1.5,
                    p95=2.0,
                    p99=3.0,
                ),
                var_metrics=VaRMetrics(
                    var_95=-2.0,
                    var_99=-3.0,
                    expected_shortfall_95=-2.5,
                    expected_shortfall_99=-3.5,
                ),
                confidence_level=ConfidenceLevel.HIGH,
                confidence_score=0.8,
                combined_confidence=0.8,
                raw_analysis_data={"component_scores": test_case["component_scores"]},
            )

            # Test the component score override logic
            override_signal = self._check_component_score_override(
                test_case["component_scores"], SignalType.HOLD
            )

            actual_signal = override_signal.value if override_signal else "HOLD"

            test_result = {
                "test_case": test_case["name"],
                "component_scores": test_case["component_scores"],
                "expected_signal": test_case["expected_signal"],
                "actual_signal": actual_signal,
                "passed": actual_signal == test_case["expected_signal"],
            }

            results.append(test_result)

            self.logger.info(
                f"Signal validation test: {test_case['name']} - "
                f"Expected: {test_case['expected_signal']}, Got: {actual_signal}, "
                f"{'PASS' if test_result['passed'] else 'FAIL'}"
            )

        # Generate summary report
        passed_tests = sum(1 for r in results if r["passed"])
        total_tests = len(results)

        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
            "test_results": results,
        }

        self.logger.info(
            f"Signal generation validation complete: {passed_tests}/{total_tests} tests passed "
            f"({summary['success_rate']:.1%} success rate)"
        )

        return summary

    def update_exit_signal_with_component_scores(
        self, result: "StatisticalAnalysisResult", component_scores: dict[str, Any]
    ) -> "StatisticalAnalysisResult":
        """
        Update the exit signal in a StatisticalAnalysisResult with component score override logic.

        This is called after component scores are calculated to apply component-based signal overrides.
        """
        try:
            # Get the current exit signal
            current_signal = result.exit_signal.signal_type

            # Check for component score override
            override_signal = self._check_component_score_override(
                component_scores, current_signal
            )

            if override_signal is not None:
                self.logger.info(
                    f"Component score override for {result.strategy_name}: "
                    f"changed {current_signal.value} to {override_signal.value}"
                )

                # Create updated exit signal with the override
                updated_exit_signal = ProbabilisticExitSignal(
                    signal_type=override_signal,
                    confidence=result.exit_signal.confidence,
                    primary_signal_strength=result.exit_signal.primary_signal_strength,
                    secondary_signal_strength=result.exit_signal.secondary_signal_strength,
                    tertiary_signal_strength=result.exit_signal.tertiary_signal_strength,
                    asset_layer_contribution=result.exit_signal.asset_layer_contribution,
                    trade_history_contribution=result.exit_signal.trade_history_contribution,
                    equity_curve_contribution=result.exit_signal.equity_curve_contribution,
                    dual_layer_score=result.exit_signal.dual_layer_score,
                    triple_layer_score=result.exit_signal.triple_layer_score,
                    timeframe_score=result.exit_signal.timeframe_score,
                    risk_adjusted_score=result.exit_signal.risk_adjusted_score,
                    intra_strategy_consistency=result.exit_signal.intra_strategy_consistency,
                    source_reliability_score=result.exit_signal.source_reliability_score,
                    sample_size_confidence=result.exit_signal.sample_size_confidence,
                    statistical_validity=result.exit_signal.statistical_validity,
                    data_source_confidence=result.exit_signal.data_source_confidence,
                    combined_source_confidence=result.exit_signal.combined_source_confidence,
                    expected_upside=result.exit_signal.expected_upside,
                    expected_timeline=result.exit_signal.expected_timeline,
                    risk_warning=result.exit_signal.risk_warning
                    or "Signal overridden based on extreme component scores",
                    source_divergence_warning=result.exit_signal.source_divergence_warning,
                )

                # Update the result with the new exit signal
                result.exit_signal = updated_exit_signal

                # Update recommendation summary
                result.recommendation_summary = self._generate_recommendation_summary(
                    updated_exit_signal,
                    result.dual_layer_convergence,
                    result.overall_confidence,
                )

            return result

        except Exception as e:
            self.logger.error(f"Error updating exit signal with component scores: {e}")
            return result
