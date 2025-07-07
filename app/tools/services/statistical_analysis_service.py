"""
Statistical Analysis Service

Core service for the Statistical Performance Divergence System (SPDS).
Orchestrates dual-layer statistical analysis, divergence detection, and
probabilistic exit signal generation following existing service patterns.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import polars as pl

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
    PercentileMetrics,
    ProbabilisticExitSignal,
    SignalType,
    StatisticalAnalysisResult,
    StatisticalMetrics,
    StrategyDistributionAnalysis,
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
        config: Optional[SPDSConfig] = None,
        logger: Optional[logging.Logger] = None,
        enable_memory_optimization: bool = True,
        data_coordinator: Optional[StrategyDataCoordinator] = None,
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

        # Service metrics
        self.metrics = {
            "analyses_performed": 0,
            "dual_layer_analyses": 0,
            "trade_history_analyses": 0,
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

    async def analyze_position(
        self,
        strategy_name: str,
        ticker: str,
        current_position_data: Optional[Dict[str, Any]] = None,
        use_trade_history: Optional[bool] = None,
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

            # Create complete result
            result = StatisticalAnalysisResult(
                strategy_name=strategy_name,
                ticker=ticker,
                analysis_timestamp=datetime.now(),
                asset_analysis=asset_analysis,
                strategy_analysis=strategy_analysis,
                asset_divergence=asset_divergence,
                strategy_divergence=strategy_divergence,
                dual_layer_convergence=dual_layer_convergence,
                exit_signal=exit_signal,
                trade_history_metrics=trade_history_metrics,
                overall_confidence=overall_confidence,
                recommendation_summary=recommendation_summary,
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

            with open(distribution_file, "r") as f:
                distribution_data = json.load(f)

            # Handle both old and new JSON structures
            if "timeframe_analysis" in distribution_data:
                # New structure
                timeframe_analysis = distribution_data["timeframe_analysis"]
                timeframe_data = timeframe_analysis.get(
                    "D", timeframe_analysis.get(list(timeframe_analysis.keys())[0])
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
                    "D", distribution_data.get(list(distribution_data.keys())[0])
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
                last_updated=datetime.fromisoformat(last_updated)
                if isinstance(last_updated, str)
                else last_updated,
                sample_period_start=datetime.fromisoformat(period_start).date()
                if isinstance(period_start, str)
                else period_start,
                sample_period_end=datetime.fromisoformat(period_end).date()
                if isinstance(period_end, str)
                else period_end,
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze asset distribution for {ticker}: {e}")
            raise

    async def _analyze_strategy_performance(
        self, strategy_name: str, ticker: str, use_trade_history: bool
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy-level performance distribution (Layer 2) using coordinated data loading"""
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
                        f"Coordinator data not available for {strategy_name}, falling back to legacy analysis"
                    )
                    self.metrics["coordinator_data_loads"] += 1

            # Fallback to legacy analysis methods
            if use_trade_history:
                return await self._analyze_trade_history_performance(
                    strategy_name, ticker
                )
            else:
                return await self._analyze_equity_curve_performance(
                    strategy_name, ticker
                )

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
                data_source=DataSource.TRADE_HISTORY,
                statistics=trade_data["return_statistics"],
                percentiles=trade_data["return_percentiles"],
                var_metrics=trade_data["var_metrics"],
                win_rate=trade_data.get("win_rate"),
                profit_factor=trade_data.get("profit_factor"),
                sharpe_ratio=trade_data.get("sharpe_ratio"),
                max_drawdown=trade_data.get("max_drawdown"),
                mfe_statistics=trade_data.get("mfe_statistics"),
                mae_statistics=trade_data.get("mae_statistics"),
                duration_statistics=trade_data.get("duration_statistics"),
                bootstrap_results=bootstrap_results,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
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
            else:
                raise

    async def _analyze_equity_curve_performance(
        self, strategy_name: str, ticker: str
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy performance using equity curve data"""
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

            # Additional strategy metrics
            win_rate = (returns > 0).mean() if len(returns) > 0 else None
            profit_factor = (
                returns[returns > 0].sum() / abs(returns[returns < 0].sum())
                if len(returns[returns < 0]) > 0
                else None
            )
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
                data_source=DataSource.EQUITY_CURVES,
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                bootstrap_results=bootstrap_results,
                confidence_level=confidence_level,
                confidence_score=confidence_score,
            )

        except Exception as e:
            self.logger.error(
                f"Failed to analyze equity curve for {strategy_name} on {ticker}: {e}"
            )
            raise

    async def _detect_asset_divergence(
        self,
        asset_analysis: AssetDistributionAnalysis,
        current_position_data: Optional[Dict],
    ) -> DivergenceMetrics:
        """Detect divergence in asset-level performance"""
        return await self.divergence_detector.detect_asset_divergence(
            asset_analysis, current_position_data
        )

    async def _detect_strategy_divergence(
        self,
        strategy_analysis: StrategyDistributionAnalysis,
        current_position_data: Optional[Dict],
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

    async def _generate_exit_signal(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
        dual_layer_convergence: DualLayerConvergence,
        asset_divergence: DivergenceMetrics,
        strategy_divergence: DivergenceMetrics,
        current_position_data: Optional[Dict],
    ) -> ProbabilisticExitSignal:
        """Generate probabilistic exit signal with confidence weighting"""
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

            # Calculate component scores
            dual_layer_score = dual_layer_convergence.convergence_score
            timeframe_score = dual_layer_convergence.cross_timeframe_score
            risk_adjusted_score = self._calculate_risk_adjusted_score(
                asset_analysis, strategy_analysis
            )

            # Sample size confidence adjustment
            sample_size_confidence = strategy_analysis.confidence_score

            # Determine signal type based on convergence and thresholds
            signal_type = self._determine_signal_type(
                dual_layer_convergence,
                asset_divergence,
                strategy_divergence,
                primary_strength,
            )

            # Calculate overall confidence
            base_confidence = (
                (primary_strength + secondary_strength + tertiary_strength) / 3 * 100
            )
            adjusted_confidence = base_confidence * sample_size_confidence

            # Generate expected outcomes
            expected_upside = self._estimate_expected_upside(
                signal_type, asset_divergence, strategy_divergence
            )
            expected_timeline = self._estimate_expected_timeline(
                signal_type, strategy_analysis
            )
            risk_warning = self._generate_risk_warning(
                signal_type, strategy_analysis, dual_layer_convergence
            )

            return ProbabilisticExitSignal(
                signal_type=signal_type,
                confidence=min(adjusted_confidence, 100.0),
                primary_signal_strength=primary_strength,
                secondary_signal_strength=secondary_strength,
                tertiary_signal_strength=tertiary_strength,
                dual_layer_score=dual_layer_score,
                timeframe_score=timeframe_score,
                risk_adjusted_score=risk_adjusted_score,
                sample_size_confidence=sample_size_confidence,
                statistical_validity=strategy_analysis.confidence_level,
                expected_upside=expected_upside,
                expected_timeline=expected_timeline,
                risk_warning=risk_warning,
            )

        except Exception as e:
            self.logger.error(f"Failed to generate exit signal: {e}")
            # Return default HOLD signal
            return ProbabilisticExitSignal(
                signal_type=SignalType.HOLD,
                confidence=50.0,
                primary_signal_strength=0.5,
                secondary_signal_strength=0.5,
                tertiary_signal_strength=0.5,
                dual_layer_score=0.5,
                timeframe_score=0.5,
                risk_adjusted_score=0.5,
                sample_size_confidence=0.5,
                statistical_validity=ConfidenceLevel.LOW,
                risk_warning="Analysis failed - using default HOLD signal",
            )

    # Helper methods

    def _calculate_statistical_metrics(
        self, data: Union[pd.Series, np.ndarray, List]
    ) -> StatisticalMetrics:
        """Calculate basic statistical metrics from data"""
        data = np.array(data)
        return StatisticalMetrics(
            mean=float(np.mean(data)),
            median=float(np.median(data)),
            std=float(np.std(data)),
            min=float(np.min(data)),
            max=float(np.max(data)),
            skewness=float(self._calculate_skewness(data)),
            kurtosis=float(self._calculate_kurtosis(data)),
            count=len(data),
        )

    def _calculate_percentile_metrics(
        self, data: Union[pd.Series, np.ndarray, List]
    ) -> PercentileMetrics:
        """Calculate percentile metrics from data"""
        data = np.array(data)
        return PercentileMetrics(
            p5=float(np.percentile(data, 5)),
            p10=float(np.percentile(data, 10)),
            p25=float(np.percentile(data, 25)),
            p50=float(np.percentile(data, 50)),
            p75=float(np.percentile(data, 75)),
            p90=float(np.percentile(data, 90)),
            p95=float(np.percentile(data, 95)),
            p99=float(np.percentile(data, 99)),
        )

    def _calculate_var_metrics(
        self, data: Union[pd.Series, np.ndarray, List]
    ) -> VaRMetrics:
        """Calculate VaR metrics from data"""
        data = np.array(data)
        var_95 = float(np.percentile(data, 5))  # 95% VaR (5th percentile)
        var_99 = float(np.percentile(data, 1))  # 99% VaR (1st percentile)

        # Calculate expected shortfall (CVaR)
        es_95 = (
            float(np.mean(data[data <= var_95])) if np.any(data <= var_95) else var_95
        )
        es_99 = (
            float(np.mean(data[data <= var_99])) if np.any(data <= var_99) else var_99
        )

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
        return (n / ((n - 1) * (n - 2))) * np.sum(((data - mean) / std) ** 3)

    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis of data"""
        n = len(data)
        if n < 4:
            return 0.0
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0.0
        return (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))) * np.sum(
            ((data - mean) / std) ** 4
        ) - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))

    def _calculate_max_drawdown(
        self, equity_series: Union[pd.Series, np.ndarray]
    ) -> float:
        """Calculate maximum drawdown from equity series"""
        try:
            equity = np.array(equity_series)
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

            # Ensure drawdown is negative or zero
            return min(max_dd, 0.0)
        except Exception as e:
            self.logger.warning(f"Error calculating max drawdown: {e}")
            return 0.0

    async def _perform_bootstrap_validation(
        self, data: Union[pd.Series, np.ndarray, List]
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

    def _calculate_regime_score(self, timeframe_data: Dict) -> float:
        """Calculate market regime score based on distribution characteristics"""
        # Simple regime scoring based on skewness and volatility
        skewness = timeframe_data.get("skewness", 0)
        volatility = timeframe_data.get("std", 0)

        # Normalize to [-1, 1] range
        regime_score = np.tanh(skewness * 0.5 - volatility * 0.3)
        return float(regime_score)

    def _calculate_regime_score_new(self, desc_stats: Dict) -> float:
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
        elif volatility > 0.03:
            return "high"
        else:
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
        current_position_data: Optional[Dict],
    ) -> float:
        """Calculate secondary signal strength from multi-timeframe analysis"""
        # Base strength from confidence level
        base_strength = strategy_analysis.confidence_score

        # Adjust based on sample size
        if strategy_analysis.statistics.count >= self.config.OPTIMAL_SAMPLE_SIZE:
            return min(base_strength * 1.1, 1.0)
        elif strategy_analysis.statistics.count >= self.config.PREFERRED_SAMPLE_SIZE:
            return base_strength
        else:
            return base_strength * 0.8

    def _calculate_tertiary_signal_strength(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate tertiary signal strength from risk-adjusted metrics"""
        # Risk adjustment based on VaR and volatility
        asset_var_score = (
            1.0 - abs(asset_analysis.var_metrics.var_95) / 0.1
        )  # Normalize by 10%
        strategy_var_score = 1.0 - abs(strategy_analysis.var_metrics.var_95) / 0.1

        return max(min((asset_var_score + strategy_var_score) / 2, 1.0), 0.0)

    def _calculate_risk_adjusted_score(
        self,
        asset_analysis: AssetDistributionAnalysis,
        strategy_analysis: StrategyDistributionAnalysis,
    ) -> float:
        """Calculate risk-adjusted score combining both layers"""
        # Sharpe ratio-like calculation
        asset_score = asset_analysis.statistics.mean / max(
            asset_analysis.statistics.std, 0.001
        )
        strategy_score = strategy_analysis.statistics.mean / max(
            strategy_analysis.statistics.std, 0.001
        )

        # Normalize to [0, 1]
        combined_score = (asset_score + strategy_score) / 2
        return max(
            min(1 / (1 + np.exp(-combined_score)), 1.0), 0.0
        )  # Sigmoid normalization

    def _determine_signal_type(
        self,
        convergence: DualLayerConvergence,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
        primary_strength: float,
    ) -> SignalType:
        """Determine signal type based on analysis results"""
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
        elif convergence.convergence_score > 0.70 and max(
            asset_div.percentile_rank, strategy_div.percentile_rank
        ) > self.config.get_percentile_threshold("strong_sell"):
            return SignalType.STRONG_SELL

        # Check for sell conditions
        elif convergence.convergence_score > 0.60 and max(
            asset_div.percentile_rank, strategy_div.percentile_rank
        ) > self.config.get_percentile_threshold("sell"):
            return SignalType.SELL

        # Default to hold
        else:
            return SignalType.HOLD

    def _estimate_expected_upside(
        self,
        signal_type: SignalType,
        asset_div: DivergenceMetrics,
        strategy_div: DivergenceMetrics,
    ) -> Optional[float]:
        """Estimate expected additional upside based on signal type"""
        if signal_type == SignalType.EXIT_IMMEDIATELY:
            return 2.0  # Minimal upside expected
        elif signal_type == SignalType.STRONG_SELL:
            return 5.0  # Limited upside
        elif signal_type == SignalType.SELL:
            return 10.0  # Some upside possible
        else:
            return None  # Hold - upside unknown

    def _estimate_expected_timeline(
        self, signal_type: SignalType, strategy_analysis: StrategyDistributionAnalysis
    ) -> Optional[str]:
        """Estimate expected timeline for signal execution"""
        if signal_type == SignalType.EXIT_IMMEDIATELY:
            return "Immediate"
        elif signal_type == SignalType.STRONG_SELL:
            return "1-3 days"
        elif signal_type == SignalType.SELL:
            return "3-7 days"
        else:
            return None

    def _generate_risk_warning(
        self,
        signal_type: SignalType,
        strategy_analysis: StrategyDistributionAnalysis,
        convergence: DualLayerConvergence,
    ) -> Optional[str]:
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
        # Weight different confidence factors
        signal_confidence = exit_signal.confidence
        convergence_confidence = convergence.convergence_score * 100
        sample_size_confidence = strategy_analysis.confidence_score * 100
        data_quality_confidence = (
            90.0 if asset_analysis.statistics.count > 1000 else 70.0
        )

        # Weighted average
        weights = [0.4, 0.3, 0.2, 0.1]  # Signal, convergence, sample size, data quality
        confidences = [
            signal_confidence,
            convergence_confidence,
            sample_size_confidence,
            data_quality_confidence,
        ]

        return sum(w * c for w, c in zip(weights, confidences))

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
        return hashlib.md5(config_str.encode()).hexdigest()[:8]

    def _get_data_sources_used(self, use_trade_history: bool) -> List[DataSource]:
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

    def get_service_metrics(self) -> Dict[str, Any]:
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

    async def health_check(self) -> Dict[str, Any]:
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
        current_position_data: Optional[Dict[str, Any]],
        use_trade_history: bool,
        strategy_analysis: StrategyDistributionAnalysis,
        asset_analysis: AssetDistributionAnalysis,
    ) -> Optional[Dict[str, Any]]:
        """Extract raw analysis data for backtesting parameter generation"""
        try:
            raw_data = {
                "returns": [],
                "durations": [],
                "data_source": "trade_history"
                if use_trade_history
                else "equity_curves",
            }

            if use_trade_history and current_position_data:
                # Extract from trade history
                if isinstance(current_position_data, list):
                    for trade in current_position_data:
                        # Extract return data
                        if "Return_Pct" in trade and trade["Return_Pct"] is not None:
                            try:
                                raw_data["returns"].append(float(trade["Return_Pct"]))
                            except (ValueError, TypeError):
                                pass

                        # Extract duration data (in days)
                        if (
                            "Duration_Days" in trade
                            and trade["Duration_Days"] is not None
                        ):
                            try:
                                raw_data["durations"].append(
                                    int(trade["Duration_Days"])
                                )
                            except (ValueError, TypeError):
                                pass

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
            else:
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
                min=float(strategy_data.performance.mae)
                if strategy_data.performance.mae
                else -0.1,
                max=float(strategy_data.performance.mfe)
                if strategy_data.performance.mfe
                else 0.1,
                skewness=0.0,  # Default
                kurtosis=0.0,  # Default
                count=int(strategy_data.statistics.sample_size)
                if strategy_data.statistics.sample_size
                else 100,
            )

            # Create percentile metrics from available data
            percentiles = PercentileMetrics(
                p5=float(strategy_data.performance.mae)
                if strategy_data.performance.mae
                else -0.05,
                p10=float(strategy_data.performance.mae) * 0.8
                if strategy_data.performance.mae
                else -0.04,
                p25=float(strategy_data.performance.mae) * 0.5
                if strategy_data.performance.mae
                else -0.025,
                p50=0.0,  # Median
                p75=float(strategy_data.performance.mfe) * 0.5
                if strategy_data.performance.mfe
                else 0.025,
                p90=float(strategy_data.performance.mfe) * 0.8
                if strategy_data.performance.mfe
                else 0.04,
                p95=float(strategy_data.performance.mfe)
                if strategy_data.performance.mfe
                else 0.05,
                p99=float(strategy_data.performance.mfe) * 1.2
                if strategy_data.performance.mfe
                else 0.06,
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
                data_source=DataSource.TRADE_HISTORY
                if use_trade_history
                else DataSource.EQUITY_CURVES,
                statistics=stats,
                percentiles=percentiles,
                var_metrics=var_metrics,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
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
