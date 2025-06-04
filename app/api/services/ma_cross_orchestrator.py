"""
MA Cross Orchestrator

Coordinates the decomposed services for MA Cross analysis.
This orchestrator manages the workflow between parameter testing, filtering, and export services.
"""

import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.api.models.ma_cross import MACrossRequest, MACrossResponse, PortfolioMetrics
from app.api.services.parameter_testing_service import ParameterTestingService
from app.api.services.portfolio_filter_service import PortfolioFilterService
from app.api.services.results_export_service import ResultsExportService
from app.core.interfaces import (
    CacheInterface,
    ConfigurationInterface,
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
    StrategyExecutorInterface,
)


class MACrossOrchestrator:
    """
    Orchestrates MA Cross analysis using decomposed services.

    This class coordinates the workflow between:
    - ParameterTestingService: Executes parameter sweeps
    - PortfolioFilterService: Applies filtering criteria
    - ResultsExportService: Handles result transformation and export
    """

    def __init__(
        self,
        logger: LoggingInterface,
        progress_tracker: ProgressTrackerInterface,
        strategy_executor: StrategyExecutorInterface,
        strategy_analyzer: StrategyAnalyzerInterface,
        cache: CacheInterface,
        monitoring: MonitoringInterface,
        configuration: ConfigurationInterface,
    ):
        """
        Initialize the orchestrator with all required dependencies.

        Args:
            logger: Logging interface
            progress_tracker: Progress tracking interface
            strategy_executor: Strategy execution interface
            strategy_analyzer: Strategy analysis interface
            cache: Cache interface
            monitoring: Monitoring interface
            configuration: Configuration interface
        """
        self.logger = logger
        self.cache = cache
        self.monitoring = monitoring
        self.configuration = configuration

        # Initialize decomposed services
        self.parameter_service = ParameterTestingService(
            logger, progress_tracker, strategy_executor
        )
        self.filter_service = PortfolioFilterService(logger)
        self.export_service = ResultsExportService(logger)

    async def analyze_portfolio(
        self,
        request: MACrossRequest,
    ) -> MACrossResponse:
        """
        Execute complete MA Cross analysis workflow.

        Args:
            request: MACrossRequest with analysis parameters

        Returns:
            MACrossResponse with analysis results
        """
        start_time = time.time()
        request_id = str(uuid.uuid4())

        try:
            # Step 1: Check cache
            cache_key = self._generate_cache_key(request)
            if not request.refresh:
                cached_result = await self.cache.get(cache_key)
                if cached_result:
                    self.logger.log("Returning cached results", "info")
                    return cached_result

            # Step 2: Validate parameters
            tickers = (
                request.ticker if isinstance(request.ticker, list) else [request.ticker]
            )
            is_valid, error_msg = self.parameter_service.validate_parameters(
                tickers,
                request.windows,
                request.strategy_types,
            )

            if not is_valid:
                raise ValueError(f"Invalid parameters: {error_msg}")

            # Step 3: Create configuration
            config = self._create_config_from_request(request)

            # Step 4: Execute parameter sweep
            self.logger.log("Starting parameter sweep execution", "info")
            portfolios, sweep_time = self.parameter_service.execute_parameter_sweep(
                config,
                request.strategy_types,
            )

            total_analyzed = len(portfolios)

            # Step 5: Apply filters
            filter_criteria = self._create_filter_criteria(request)
            filtered_portfolios = self.filter_service.filter_portfolios(
                portfolios,
                filter_criteria,
            )

            # Step 6: Get best portfolios by metric
            sort_metric = self._map_sort_field(request.sort_by)
            best_portfolios = self.filter_service.get_best_portfolios_by_metric(
                filtered_portfolios,
                sort_metric,
                top_n=100,  # Limit results
                ascending=request.sort_asc,
            )

            # Step 7: Convert to PortfolioMetrics
            portfolio_metrics = self.export_service.convert_to_portfolio_metrics(
                best_portfolios
            )

            # Step 8: Export results (optional)
            export_paths = {}
            if len(best_portfolios) > 0:
                base_path = config.get("BASE_DIR", "/Users/colemorton/Projects/trading")
                csv_path = self.export_service.export_to_csv(
                    best_portfolios, base_path, f"ma_cross_{request_id[:8]}"
                )
                if csv_path:
                    export_paths["csv"] = csv_path

            # Step 9: Create response
            execution_time = time.time() - start_time
            response_data = self.export_service.format_for_api_response(
                portfolio_metrics,
                {
                    "request_id": request_id,
                    "ticker": tickers,
                    "strategy_types": request.strategy_types,
                    "total_analyzed": total_analyzed,
                },
                execution_time,
                export_paths,
            )

            # Create response object
            response = MACrossResponse(**response_data)

            # Step 10: Cache results
            await self.cache.set(cache_key, response, ttl=3600)  # 1 hour TTL

            # Step 11: Record metrics
            self.monitoring.record_metric(
                "ma_cross_analysis_duration",
                execution_time,
                {"status": "success", "portfolios": len(portfolio_metrics)},
            )

            return response

        except Exception as e:
            self.logger.log(f"Error in MA Cross analysis: {str(e)}", "error")
            self.monitoring.record_metric(
                "ma_cross_analysis_error", 1, {"error": str(e)}
            )
            raise

    def _generate_cache_key(self, request: MACrossRequest) -> str:
        """Generate a cache key from request parameters."""
        ticker_str = (
            request.ticker
            if isinstance(request.ticker, str)
            else ",".join(sorted(request.ticker))
        )
        strategy_str = ",".join(sorted(request.strategy_types))

        # Include key parameters in cache key
        key_parts = [
            f"ma_cross:v2",
            f"t:{ticker_str}",
            f"w:{request.windows}",
            f"s:{strategy_str}",
            f"d:{request.direction}",
            f"h:{request.use_hourly}",
        ]

        # Add minimum filters if present
        if request.minimums:
            min_parts = []
            if request.minimums.win_rate is not None:
                min_parts.append(f"wr:{request.minimums.win_rate}")
            if request.minimums.trades is not None:
                min_parts.append(f"tr:{request.minimums.trades}")
            if min_parts:
                key_parts.append(f"min:{'-'.join(min_parts)}")

        return ":".join(key_parts)

    def _create_config_from_request(self, request: MACrossRequest) -> Dict[str, Any]:
        """Create configuration dictionary from request."""
        config = {
            "TICKER": request.ticker,
            "WINDOWS": request.windows,
            "DIRECTION": request.direction,
            "STRATEGY_TYPES": request.strategy_types,
            "USE_HOURLY": request.use_hourly,
            "USE_YEARS": request.use_years,
            "YEARS": request.years if request.use_years else None,
            "USE_SYNTHETIC": request.use_synthetic,
            "SORT_BY": request.sort_by,
            "SORT_ASC": request.sort_asc,
            "USE_GBM": request.use_gbm,
            "USE_CURRENT": request.use_current,
            "USE_SCANNER": request.use_scanner,
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

        # Add synthetic ticker config if needed
        if request.use_synthetic and request.ticker_1 and request.ticker_2:
            config["TICKER_1"] = request.ticker_1
            config["TICKER_2"] = request.ticker_2

        return config

    def _create_filter_criteria(self, request: MACrossRequest) -> Dict[str, Any]:
        """Create filter criteria from request."""
        criteria = {
            "minimums": {},
        }

        if request.minimums:
            # Map request minimums to filter criteria
            if request.minimums.win_rate is not None:
                criteria["minimums"]["win_rate"] = request.minimums.win_rate
            if request.minimums.trades is not None:
                criteria["minimums"]["trades"] = request.minimums.trades
            if request.minimums.expectancy_per_trade is not None:
                criteria["minimums"][
                    "expectancy_per_trade"
                ] = request.minimums.expectancy_per_trade
            if request.minimums.profit_factor is not None:
                criteria["minimums"]["profit_factor"] = request.minimums.profit_factor
            if request.minimums.sortino_ratio is not None:
                criteria["minimums"]["sortino_ratio"] = request.minimums.sortino_ratio
            if request.minimums.score is not None:
                criteria["minimums"]["score"] = request.minimums.score
            if request.minimums.beats_bnh is not None:
                criteria["minimums"]["beats_bnh"] = request.minimums.beats_bnh

        return criteria

    def _map_sort_field(self, sort_by: str) -> str:
        """Map API sort field to portfolio column name."""
        mapping = {
            "total_return": "Total Return [%]",
            "annual_return": "Ann. Return [%]",
            "sharpe_ratio": "Sharpe Ratio",
            "sortino_ratio": "Sortino Ratio",
            "win_rate": "Win Rate [%]",
            "profit_factor": "Profit Factor",
            "expectancy": "Expectancy",
            "score": "Score",
            "total_trades": "Total Trades",
            "max_drawdown": "Max Drawdown [%]",
        }

        return mapping.get(sort_by, sort_by)

    def get_execution_estimate(
        self,
        request: MACrossRequest,
    ) -> Dict[str, Any]:
        """
        Get execution time estimate for the analysis.

        Args:
            request: MACrossRequest with analysis parameters

        Returns:
            Dictionary with execution estimate
        """
        tickers = (
            request.ticker if isinstance(request.ticker, list) else [request.ticker]
        )

        estimated_time = self.parameter_service.estimate_execution_time(
            len(tickers),
            request.windows,
            len(request.strategy_types),
        )

        return {
            "estimated_seconds": round(estimated_time, 1),
            "estimated_minutes": round(estimated_time / 60, 1),
            "factors": {
                "ticker_count": len(tickers),
                "window_size": request.windows,
                "strategy_count": len(request.strategy_types),
                "uses_concurrent": len(tickers) > 2,
            },
        }
