"""
Memory-Optimized Runner for Concurrency Analysis.

This module provides a memory-optimized version of the concurrency analysis
runner that integrates with the system's memory optimization framework.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl

from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.permutation import find_optimal_permutation
from app.concurrency.tools.report import generate_json_report
from app.concurrency.tools.strategy_id import generate_strategy_id
from app.concurrency.tools.strategy_processor import process_strategies
from app.concurrency.tools.types import ConcurrencyConfig
from app.tools.portfolio import StrategyConfig, load_portfolio
from app.tools.processing.data_converter import DataConverter

# Import memory optimization framework
from app.tools.processing.memory_optimizer import configure_memory_optimizer
from app.tools.processing.mmap_accessor import MMapCSVReader, get_mmap_accessor
from app.tools.processing.streaming_processor import StreamingProcessor


class MemoryOptimizedConcurrencyRunner:
    """Memory-optimized concurrency analysis runner.

    This class provides memory-efficient execution of concurrency analysis
    by leveraging the system's memory optimization framework.
    """

    def __init__(
        self,
        enable_memory_optimization: bool = True,
        memory_threshold_mb: float = 1000.0,
        streaming_threshold_mb: float = 5.0,
        enable_pooling: bool = True,
        enable_monitoring: bool = True,
    ):
        """Initialize memory-optimized runner.

        Args:
            enable_memory_optimization: Enable memory optimization features
            memory_threshold_mb: Memory threshold for GC triggers
            streaming_threshold_mb: File size threshold for streaming
            enable_pooling: Enable DataFrame object pooling
            enable_monitoring: Enable memory monitoring
        """
        self.enable_optimization = enable_memory_optimization

        if enable_memory_optimization:
            # Configure memory optimizer
            self.memory_optimizer = configure_memory_optimizer(
                enable_pooling=enable_pooling,
                enable_monitoring=enable_monitoring,
                memory_threshold_mb=memory_threshold_mb,
            )

            # Initialize streaming processor
            self.streaming_processor = StreamingProcessor(
                streaming_threshold_mb=streaming_threshold_mb, chunk_size_rows=10000,
            )

            # Initialize data converter with caching
            self.data_converter = DataConverter(enable_cache=True)

            # Initialize memory-mapped accessor
            self.mmap_accessor = get_mmap_accessor()
        else:
            self.memory_optimizer = None
            self.streaming_processor = None
            self.data_converter = None
            self.mmap_accessor = None

    def run_analysis(
        self,
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run memory-optimized concurrency analysis.

        Args:
            config: Concurrency analysis configuration
            progress_callback: Optional progress callback

        Returns:
            Analysis results dictionary
        """
        try:
            # Load portfolio with memory optimization
            portfolio_strategies = self._load_portfolio_optimized(config)

            # Process strategies with memory optimization
            processed_data = self._process_strategies_optimized(
                portfolio_strategies, config, progress_callback,
            )

            # Run concurrency analysis with memory optimization
            analysis_results = self._analyze_concurrency_optimized(
                processed_data, config,
            )

            # Generate reports with memory optimization
            report = self._generate_report_optimized(analysis_results, config)

            # Run optimization if enabled
            if config.get("OPTIMIZE", False):
                optimization_results = self._run_optimization_optimized(
                    portfolio_strategies, config, progress_callback,
                )
                report["optimization_results"] = optimization_results

            return report

        except Exception as e:
            msg = f"Memory-optimized concurrency analysis failed: {e!s}"
            raise RuntimeError(msg)

    def _load_portfolio_optimized(
        self, config: ConcurrencyConfig,
    ) -> list[StrategyConfig]:
        """Load portfolio with memory optimization."""
        portfolio_path = self._get_portfolio_path(config)

        if not self.enable_optimization:
            return load_portfolio(str(portfolio_path))

        # Use streaming for large files
        file_size_mb = portfolio_path.stat().st_size / (1024 * 1024)

        if file_size_mb > self.streaming_processor.streaming_threshold_mb:
            # Use streaming processor for large files
            if portfolio_path.suffix.lower() == ".csv":
                df = self.streaming_processor.read_csv(str(portfolio_path))
            else:
                # For JSON files, fall back to regular loading
                df = load_portfolio(str(portfolio_path))
        # Use memory-mapped reading for efficient access
        elif portfolio_path.suffix.lower() == ".csv":
            with MMapCSVReader(str(portfolio_path)) as reader:
                # Read all rows with memory mapping
                df = reader.read_rows(0, reader.get_row_count())
        else:
            df = load_portfolio(str(portfolio_path))

        return df

    def _process_strategies_optimized(
        self,
        strategies: list[StrategyConfig],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Process strategies with memory optimization."""
        if not self.enable_optimization:
            return process_strategies(strategies, config)

        processed_data = {}
        total_strategies = len(strategies)

        for i, strategy in enumerate(strategies):
            # Update progress
            if progress_callback:
                progress_callback(i, total_strategies)

            # Process strategy with memory optimization
            strategy_data = self._process_single_strategy_optimized(strategy, config)

            if strategy_data is not None:
                strategy_id = generate_strategy_id(strategy)

                # Optimize DataFrame memory usage
                if self.memory_optimizer:
                    strategy_data = self.memory_optimizer.optimize_dataframe(
                        strategy_data,
                    )

                processed_data[strategy_id] = strategy_data

            # Trigger garbage collection if memory threshold exceeded
            if self.memory_optimizer and self.memory_optimizer.should_trigger_gc():
                self.memory_optimizer.trigger_gc()

        if progress_callback:
            progress_callback(total_strategies, total_strategies)

        return processed_data

    def _process_single_strategy_optimized(
        self, strategy: StrategyConfig, config: ConcurrencyConfig,
    ) -> pl.DataFrame | None:
        """Process a single strategy with memory optimization."""
        try:
            # Use DataFrame pooling if available
            if self.memory_optimizer and self.memory_optimizer.df_pool:
                with self.memory_optimizer.df_pool.polars() as pooled_df:
                    # Process strategy using pooled DataFrame
                    result = self._execute_strategy_processing(
                        strategy, config, pooled_df,
                    )

                    # Convert to optimized DataFrame
                    if result is not None:
                        return self.memory_optimizer.optimize_dataframe(result)
            else:
                # Fall back to regular processing
                return self._execute_strategy_processing(strategy, config)

        except Exception as e:
            # Log error but continue processing
            print(
                f"Error processing strategy {strategy.get('ticker', 'Unknown')}: {e!s}",
            )
            return None

    def _execute_strategy_processing(
        self,
        strategy: StrategyConfig,
        config: ConcurrencyConfig,
        pooled_df: pl.DataFrame | None = None,
    ) -> pl.DataFrame | None:
        """Execute strategy processing logic."""
        # This would integrate with the existing strategy processing logic
        # from app.concurrency.tools.strategy_processor

        # For now, return a placeholder that would be replaced with
        # the actual strategy processing implementation
        from app.concurrency.tools.strategy_processor import process_single_strategy

        try:
            return process_single_strategy(strategy, config)
        except Exception:
            return None

    def _analyze_concurrency_optimized(
        self, processed_data: dict[str, pl.DataFrame], config: ConcurrencyConfig,
    ) -> dict[str, Any]:
        """Run concurrency analysis with memory optimization."""
        if not self.enable_optimization:
            return analyze_concurrency(processed_data, config)

        # Use memory-efficient data structures
        optimized_data = {}

        for strategy_id, df in processed_data.items():
            # Convert to optimized format if needed
            if self.data_converter:
                optimized_df = self.data_converter.optimize_for_analysis(df)
                optimized_data[strategy_id] = optimized_df
            else:
                optimized_data[strategy_id] = df

        # Run analysis with optimized data
        results = analyze_concurrency(optimized_data, config)

        # Clean up temporary data structures
        if self.memory_optimizer:
            self.memory_optimizer.trigger_gc()

        return results

    def _generate_report_optimized(
        self, analysis_results: dict[str, Any], config: ConcurrencyConfig,
    ) -> dict[str, Any]:
        """Generate report with memory optimization."""
        if not self.enable_optimization:
            return generate_json_report(analysis_results, config)

        # Use memory-efficient JSON serialization
        report = generate_json_report(analysis_results, config)

        # Optimize large data structures in report
        if self.memory_optimizer:
            report = self._optimize_report_memory(report)

        return report

    def _run_optimization_optimized(
        self,
        strategies: list[StrategyConfig],
        config: ConcurrencyConfig,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> dict[str, Any]:
        """Run permutation optimization with memory efficiency."""
        if not self.enable_optimization:
            return find_optimal_permutation(strategies, config)

        # Use memory-efficient permutation analysis
        from app.tools.processing.parameter_sweep import (
            memory_efficient_parameter_sweep,
        )

        def optimization_function(params):
            # Run concurrency analysis for parameter subset
            subset_strategies = params["strategies"]
            subset_config = {**config, "ALLOCATION_MODE": "EQUAL"}

            try:
                # Run analysis with memory optimization
                subset_data = self._process_strategies_optimized(
                    subset_strategies, subset_config,
                )
                results = self._analyze_concurrency_optimized(
                    subset_data, subset_config,
                )

                return pl.DataFrame(
                    {
                        "efficiency_score": [
                            results.get("portfolio_efficiency", {}).get(
                                "efficiency_score", 0,
                            ),
                        ],
                        "strategies": [len(subset_strategies)],
                        "strategy_ids": [
                            ",".join(generate_strategy_id(s) for s in subset_strategies),
                        ],
                    },
                )
            except Exception:
                return pl.DataFrame(
                    {
                        "efficiency_score": [0],
                        "strategies": [len(subset_strategies)],
                        "strategy_ids": ["error"],
                    },
                )

        # Generate parameter grid for optimization
        min_strategies = config.get("OPTIMIZE_MIN_STRATEGIES", 3)
        max_permutations = config.get("OPTIMIZE_MAX_PERMUTATIONS", 1000)

        parameter_grid = self._generate_optimization_parameters(
            strategies, min_strategies, max_permutations,
        )

        # Run memory-efficient optimization
        results = memory_efficient_parameter_sweep(
            strategy_fn=optimization_function,
            parameter_grid=parameter_grid,
            strategy_name="concurrency_optimization",
            output_dir="./optimization_results/",
            max_memory_mb=(
                self.memory_optimizer.memory_threshold_mb
                if self.memory_optimizer
                else 1000.0
            ),
            chunk_size=50,
        )

        # Process optimization results
        return self._process_optimization_results(results, strategies)

    def _optimize_report_memory(self, report: dict[str, Any]) -> dict[str, Any]:
        """Optimize report memory usage."""
        # Remove large unnecessary data structures
        optimized_report = {}

        for key, value in report.items():
            if isinstance(value, np.ndarray) and value.size > 1000:
                # Convert large arrays to summaries
                optimized_report[key] = {
                    "shape": value.shape,
                    "dtype": str(value.dtype),
                    "mean": float(np.mean(value)),
                    "std": float(np.std(value)),
                    "min": float(np.min(value)),
                    "max": float(np.max(value)),
                }
            elif isinstance(value, dict):
                optimized_report[key] = self._optimize_report_memory(value)
            else:
                optimized_report[key] = value

        return optimized_report

    def _generate_optimization_parameters(
        self,
        strategies: list[StrategyConfig],
        min_strategies: int,
        max_permutations: int,
    ) -> dict[str, list]:
        """Generate parameter grid for optimization."""
        from itertools import combinations

        strategy_combinations = []

        # Generate all combinations from min_strategies to len(strategies)
        for size in range(min_strategies, len(strategies) + 1):
            for combo in combinations(strategies, size):
                strategy_combinations.append(list(combo))
                if len(strategy_combinations) >= max_permutations:
                    break
            if len(strategy_combinations) >= max_permutations:
                break

        return {"strategies": strategy_combinations}

    def _process_optimization_results(
        self, results: pl.DataFrame, original_strategies: list[StrategyConfig],
    ) -> dict[str, Any]:
        """Process optimization results into final format."""
        # Find best result
        best_idx = results["efficiency_score"].arg_max()
        best_score = results["efficiency_score"][best_idx]
        best_strategy_ids = results["strategy_ids"][best_idx].split(",")

        return {
            "best_efficiency": float(best_score),
            "best_permutation": best_strategy_ids,
            "total_analyzed": len(results),
            "improvement_percentage": 0.0,  # Would calculate based on baseline
        }

    def _get_portfolio_path(self, config: ConcurrencyConfig) -> Path:
        """Get portfolio file path."""
        portfolio_file = config["PORTFOLIO"]
        if "/" in portfolio_file or "\\" in portfolio_file:
            return Path(portfolio_file)

        # Search in common locations
        base_dir = Path(config.get("BASE_DIR", "."))
        possible_paths = [
            base_dir / portfolio_file,
            Path("data/raw/reports/concurrency") / portfolio_file,
            Path("data/raw/strategies") / portfolio_file,
            Path(portfolio_file),
        ]

        for path in possible_paths:
            if path.exists():
                return path

        msg = f"Portfolio file not found: {portfolio_file}"
        raise FileNotFoundError(msg)


# Legacy compatibility function
def run_memory_optimized_analysis(
    config: ConcurrencyConfig,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    """Run memory-optimized concurrency analysis.

    This function provides backward compatibility with the existing
    concurrency analysis interface while using memory optimization.
    """
    runner = MemoryOptimizedConcurrencyRunner(enable_memory_optimization=True)
    return runner.run_analysis(config, progress_callback)
