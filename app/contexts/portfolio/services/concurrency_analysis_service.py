"""
Concurrency Analysis Service.

This service provides a unified interface for running concurrency analysis
on trading portfolios, following the modular service architecture pattern.
"""

from collections.abc import Callable
import logging
from pathlib import Path
from typing import Any

import polars as pl

from app.concurrency.config import ConcurrencyConfig, validate_config
from app.concurrency.config_defaults import get_default_config
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.permutation import find_optimal_permutation
from app.concurrency.tools.report import generate_json_report
from app.concurrency.tools.runner import save_json_report
from app.concurrency.tools.strategy_processor import process_strategies
from app.concurrency.tools.visualization import plot_concurrency
from app.tools.exceptions import TradingSystemError
from app.tools.portfolio import StrategyConfig, load_portfolio


class ConcurrencyAnalysisEngine:
    """Service for running concurrency analysis on trading portfolios.

    This service encapsulates all the logic for analyzing concurrent exposure
    between trading strategies, calculating efficiency metrics, and generating
    optimization recommendations.
    """

    def __init__(
        self,
        enable_memory_optimization: bool = False,
        enable_visualization: bool = True,
        enable_optimization: bool = False,
        log: Callable[[str, str], None] | None = None,
    ):
        """Initialize the concurrency analysis engine.

        Args:
            enable_memory_optimization: Enable memory optimization features
            enable_visualization: Enable visualization generation
            enable_optimization: Enable permutation optimization
            log: Logging function for progress tracking
        """
        self.enable_memory_optimization = enable_memory_optimization
        self.enable_visualization = enable_visualization
        self.enable_optimization = enable_optimization
        self.log = log or self._default_log

        # Initialize memory optimization if enabled
        if enable_memory_optimization:
            try:
                from app.concurrency.tools.optimized_runner import (
                    MemoryOptimizedConcurrencyRunner,
                )

                self.optimized_runner = MemoryOptimizedConcurrencyRunner(
                    enable_memory_optimization=True
                )
            except ImportError:
                self.log(
                    "Memory optimization unavailable, using standard processing",
                    "warning",
                )
                self.optimized_runner = None
        else:
            self.optimized_runner = None

    def analyze_portfolio(
        self,
        portfolio_path: str | Path,
        config_overrides: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Analyze concurrency for a trading portfolio.

        Args:
            portfolio_path: Path to portfolio file (JSON or CSV)
            config_overrides: Configuration overrides
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing analysis results

        Raises:
            ConfigurationError: If configuration is invalid
            PortfolioLoadError: If portfolio cannot be loaded
            TradingSystemError: For other analysis errors
        """
        try:
            # Build configuration
            config = self._build_config(config_overrides)
            config["PORTFOLIO"] = str(portfolio_path)

            # Validate configuration
            validated_config = validate_config(config)

            self.log(
                f"Starting concurrency analysis for portfolio: {portfolio_path}", "info"
            )

            # Use memory-optimized runner if available
            if self.optimized_runner and config.get("ENABLE_MEMORY_OPTIMIZATION"):
                self.log("Using memory-optimized analysis", "info")
                return self.optimized_runner.run_analysis(
                    validated_config, progress_callback
                )

            # Standard analysis pipeline
            return self._run_standard_analysis(validated_config, progress_callback)

        except Exception as e:
            error_msg = f"Concurrency analysis failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def analyze_strategies(
        self,
        strategies: list[StrategyConfig],
        config_overrides: dict[str, Any] | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Analyze concurrency for a list of strategies.

        Args:
            strategies: List of strategy configurations
            config_overrides: Configuration overrides
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Build configuration
            config = self._build_config(config_overrides)

            self.log(
                f"Starting concurrency analysis for {len(strategies)} strategies",
                "info",
            )

            # Process strategies
            processed_data = self._process_strategies(
                strategies, config, progress_callback
            )

            # Run concurrency analysis
            analysis_results = self._analyze_concurrency(processed_data, config)

            # Generate report
            report = self._generate_report(analysis_results, config)

            # Run optimization if enabled
            if self.enable_optimization or config.get("OPTIMIZE", False):
                optimization_results = self._run_optimization(
                    strategies, config, progress_callback
                )
                report["optimization_results"] = optimization_results

            return report

        except Exception as e:
            error_msg = f"Strategy concurrency analysis failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def calculate_efficiency_metrics(
        self,
        processed_data: dict[str, pl.DataFrame],
        config: ConcurrencyConfig,
    ) -> dict[str, Any]:
        """Calculate efficiency metrics for processed strategy data.

        Args:
            processed_data: Dictionary of processed strategy DataFrames
            config: Concurrency configuration

        Returns:
            Dictionary containing efficiency metrics
        """
        try:
            self.log("Calculating efficiency metrics", "info")

            # Run concurrency analysis to get metrics
            analysis_results = analyze_concurrency(processed_data, config)

            # Extract efficiency metrics
            efficiency_metrics = {
                "portfolio_efficiency": analysis_results.get(
                    "portfolio_efficiency", {}
                ),
                "strategy_efficiencies": analysis_results.get(
                    "strategy_efficiencies", {}
                ),
                "correlation_matrix": analysis_results.get("correlation_matrix", {}),
                "activity_periods": analysis_results.get("activity_periods", {}),
                "concurrent_periods": analysis_results.get("concurrent_periods", {}),
            }

            return efficiency_metrics

        except Exception as e:
            error_msg = f"Efficiency calculation failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def find_optimal_strategy_combination(
        self,
        strategies: list[StrategyConfig],
        min_strategies: int = 3,
        max_permutations: int | None = None,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Find optimal combination of strategies.

        Args:
            strategies: List of strategy configurations
            min_strategies: Minimum strategies per combination
            max_permutations: Maximum permutations to evaluate
            progress_callback: Optional progress callback

        Returns:
            Dictionary containing optimization results
        """
        try:
            self.log(
                f"Finding optimal combination from {len(strategies)} strategies", "info"
            )

            # Build optimization configuration
            config = {
                "OPTIMIZE": True,
                "OPTIMIZE_MIN_STRATEGIES": min_strategies,
                "OPTIMIZE_MAX_PERMUTATIONS": max_permutations,
                "ALLOCATION_MODE": "EQUAL",
            }

            # Run optimization
            optimization_results = find_optimal_permutation(strategies, config)

            self.log("Optimization completed", "info")
            return optimization_results

        except Exception as e:
            error_msg = f"Strategy optimization failed: {e!s}"
            self.log(error_msg, "error")
            raise TradingSystemError(error_msg) from e

    def _run_standard_analysis(
        self,
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run standard concurrency analysis pipeline."""
        # Load portfolio
        portfolio_path = config["PORTFOLIO"]
        strategies = load_portfolio(portfolio_path)

        self.log(f"Loaded {len(strategies)} strategies from portfolio", "info")

        # Process strategies
        processed_data = self._process_strategies(strategies, config, progress_callback)

        # Run concurrency analysis
        analysis_results = self._analyze_concurrency(processed_data, config)

        # Generate report
        report = self._generate_report(analysis_results, config)

        # Run optimization if enabled
        if self.enable_optimization or config.get("OPTIMIZE", False):
            optimization_results = self._run_optimization(
                strategies, config, progress_callback
            )
            report["optimization_results"] = optimization_results

        return report

    def _process_strategies(
        self,
        strategies: list[StrategyConfig],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Process strategies into analyzable data."""
        self.log(f"Processing {len(strategies)} strategies", "info")

        # Use existing strategy processor
        processed_data = process_strategies(strategies, config)

        if progress_callback:
            # Simulate progress updates
            total = len(strategies)
            for i in range(total + 1):
                progress_callback(i, total)

        self.log(f"Successfully processed {len(processed_data)} strategies", "info")
        return processed_data

    def _analyze_concurrency(
        self,
        processed_data: dict[str, pl.DataFrame],
        config: ConcurrencyConfig,
    ) -> dict[str, Any]:
        """Run concurrency analysis on processed data."""
        self.log("Running concurrency analysis", "info")

        # Use existing analysis function
        analysis_results = analyze_concurrency(processed_data, config)

        self.log("Concurrency analysis completed", "info")
        return analysis_results

    def _generate_report(
        self,
        analysis_results: dict[str, Any],
        config: ConcurrencyConfig,
    ) -> dict[str, Any]:
        """Generate analysis report."""
        self.log("Generating analysis report", "info")

        # Generate JSON report
        report = generate_json_report(analysis_results, config)

        # Save report if base directory is specified
        if config.get("BASE_DIR"):
            try:
                report_path = save_json_report(report, config, self.log)
                report["report_path"] = str(report_path)
            except Exception as e:
                self.log(f"Failed to save report: {e!s}", "warning")

        # Generate visualization if enabled
        if self.enable_visualization or config.get("VISUALIZATION", False):
            try:
                viz_path = self._generate_visualization(analysis_results, config)
                if viz_path:
                    report["visualization_path"] = str(viz_path)
            except Exception as e:
                self.log(f"Failed to generate visualization: {e!s}", "warning")

        self.log("Report generation completed", "info")
        return report

    def _generate_visualization(
        self,
        analysis_results: dict[str, Any],
        config: ConcurrencyConfig,
    ) -> Path | None:
        """Generate visualization charts."""
        try:
            # Use existing visualization function
            viz_path = plot_concurrency(analysis_results, config)
            self.log(f"Visualization saved to: {viz_path}", "info")
            return viz_path
        except Exception as e:
            self.log(f"Visualization generation failed: {e!s}", "warning")
            return None

    def _run_optimization(
        self,
        strategies: list[StrategyConfig],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run permutation optimization using the dedicated service."""
        self.log(
            "Running strategy optimization using PermutationOptimizationService", "info"
        )

        try:
            from app.contexts.portfolio.services.permutation_optimization_service import (
                PermutationOptimizationService,
            )

            # Configure optimization service
            enable_parallel = config.get("PARALLEL_PROCESSING", False)
            optimization_service = PermutationOptimizationService(
                enable_parallel_processing=enable_parallel,
                log=self.log,
            )

            # Extract optimization parameters
            min_strategies = config.get("OPTIMIZE_MIN_STRATEGIES", 3)
            max_permutations = config.get("OPTIMIZE_MAX_PERMUTATIONS", None)
            allocation_mode = config.get("ALLOCATION_MODE", "EQUAL")

            # Run optimization
            result = optimization_service.optimize_strategy_selection(
                strategies=strategies,
                min_strategies=min_strategies,
                max_permutations=max_permutations,
                allocation_mode=allocation_mode,
                config_overrides=config,
                progress_callback=progress_callback,
            )

            # Convert result to dictionary format
            optimization_results = {
                "best_permutation": result.best_permutation,
                "best_efficiency": result.best_efficiency,
                "total_analyzed": result.total_analyzed,
                "execution_time": result.execution_time,
                "improvement_percentage": result.improvement_percentage,
            }

            self.log(
                f"Strategy optimization completed in {result.execution_time:.2f}s",
                "info",
            )
            return optimization_results

        except ImportError:
            self.log(
                "PermutationOptimizationService unavailable, using legacy optimization",
                "warning",
            )
            # Fall back to existing optimization
            optimization_results = find_optimal_permutation(strategies, config)
            self.log("Strategy optimization completed", "info")
            return optimization_results

    def _build_config(
        self, config_overrides: dict[str, Any] | None = None
    ) -> ConcurrencyConfig:
        """Build configuration with defaults and overrides."""
        # Start with default configuration
        config = get_default_config()

        # Apply overrides
        if config_overrides:
            config.update(config_overrides)

        # Apply service-specific settings
        if self.enable_visualization:
            config["VISUALIZATION"] = True

        if self.enable_optimization:
            config["OPTIMIZE"] = True

        if self.enable_memory_optimization:
            config["ENABLE_MEMORY_OPTIMIZATION"] = True

        return config

    def _default_log(self, message: str, level: str = "info") -> None:
        """Default logging implementation."""
        logger = logging.getLogger(__name__)
        getattr(logger, level.lower(), logger.info)(message)


# Convenience functions for direct usage
def analyze_portfolio_concurrency(
    portfolio_path: str | Path,
    config_overrides: dict[str, Any] | None = None,
    enable_memory_optimization: bool = False,
    enable_visualization: bool = True,
    enable_optimization: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Analyze concurrency for a portfolio file.

    This is a convenience function that creates and uses a ConcurrencyAnalysisEngine.

    Args:
        portfolio_path: Path to portfolio file
        config_overrides: Configuration overrides
        enable_memory_optimization: Enable memory optimization
        enable_visualization: Enable visualization
        enable_optimization: Enable optimization
        progress_callback: Progress callback

    Returns:
        Analysis results dictionary
    """
    engine = ConcurrencyAnalysisEngine(
        enable_memory_optimization=enable_memory_optimization,
        enable_visualization=enable_visualization,
        enable_optimization=enable_optimization,
    )

    return engine.analyze_portfolio(
        portfolio_path=portfolio_path,
        config_overrides=config_overrides,
        progress_callback=progress_callback,
    )


def analyze_strategies_concurrency(
    strategies: list[StrategyConfig],
    config_overrides: dict[str, Any] | None = None,
    enable_memory_optimization: bool = False,
    enable_visualization: bool = True,
    enable_optimization: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Analyze concurrency for a list of strategies.

    This is a convenience function that creates and uses a ConcurrencyAnalysisEngine.

    Args:
        strategies: List of strategy configurations
        config_overrides: Configuration overrides
        enable_memory_optimization: Enable memory optimization
        enable_visualization: Enable visualization
        enable_optimization: Enable optimization
        progress_callback: Progress callback

    Returns:
        Analysis results dictionary
    """
    engine = ConcurrencyAnalysisEngine(
        enable_memory_optimization=enable_memory_optimization,
        enable_visualization=enable_visualization,
        enable_optimization=enable_optimization,
    )

    return engine.analyze_strategies(
        strategies=strategies,
        config_overrides=config_overrides,
        progress_callback=progress_callback,
    )
