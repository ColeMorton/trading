"""
Portfolio Review Service

Unified service for portfolio review operations, supporting both single
and multi-strategy analysis with benchmark comparison.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
import polars as pl
import vectorbt as vbt

from app.portfolio_review.tools.portfolio_analysis import (
    calculate_risk_metrics,
    check_open_positions,
    create_benchmark_data,
    create_pricesframe,
    find_common_dates,
    prepare_data,
)
from app.strategies.ma_cross.tools.generate_signals import generate_signals
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_data import get_data
from app.tools.portfolio.strategy_types import derive_use_sma
from app.tools.stats_converter import convert_stats
from app.utils import backtest_strategy

from .portfolio_data_export_service import (
    ExportConfig,
    ExportResults,
    PortfolioDataExportService,
)


@dataclass
class StrategyConfig:
    """Configuration for a single strategy."""

    ticker: str
    fast_period: int
    slow_period: int
    strategy_type: str = "SMA"
    direction: str = "long"
    stop_loss: Optional[float] = None
    position_size: float = 1.0
    use_sma: bool = True
    use_hourly: bool = False
    rsi_window: Optional[int] = None
    rsi_threshold: Optional[int] = None
    signal_period: int = 9  # For MACD


@dataclass
class PortfolioReviewConfig:
    """Configuration for portfolio review operations."""

    strategies: List[StrategyConfig]
    start_date: str = "2020-01-01"
    end_date: str = "2024-12-31"
    init_cash: float = 10000.0
    fees: float = 0.001
    benchmark_symbol: Optional[str] = None
    enable_plotting: bool = True
    export_equity_curve: bool = True
    calculate_risk_metrics: bool = True
    enable_memory_optimization: bool = False
    memory_threshold_mb: float = 500.0
    enable_parallel_processing: bool = False
    max_workers: Optional[int] = None
    export_raw_data: bool = False
    raw_data_export_config: Optional[ExportConfig] = None


@dataclass
class PortfolioResults:
    """Results from portfolio review analysis."""

    portfolio: "vbt.Portfolio"
    benchmark_portfolio: Optional["vbt.Portfolio"]
    statistics: Dict[str, Any]
    risk_metrics: Dict[str, float]
    open_positions: List[Tuple[str, float]]
    equity_curve_path: Optional[str] = None
    plot_paths: List[str] = None
    raw_data_export_results: Optional[ExportResults] = None


class PortfolioReviewService:
    """
    Unified service for portfolio review operations.

    Supports both single and multi-strategy analysis with benchmark comparison,
    risk metrics calculation, and comprehensive reporting.
    """

    def __init__(self, config: PortfolioReviewConfig, logger=None):
        """Initialize portfolio review service."""
        self.config = config
        self.logger = logger
        self.plot_paths = []

        # Initialize memory optimization if enabled
        self.memory_optimizer = None
        if config.enable_memory_optimization:
            try:
                from app.tools.processing.memory_optimizer import (
                    configure_memory_optimizer,
                )

                self.memory_optimizer = configure_memory_optimizer(
                    enable_pooling=True,
                    enable_monitoring=True,
                    memory_threshold_mb=config.memory_threshold_mb,
                )
                self._log("Memory optimization enabled")
            except ImportError:
                self._log("Memory optimization requested but not available", "warning")

        # Initialize data export service if enabled
        self.data_export_service = None
        if config.export_raw_data:
            export_config = config.raw_data_export_config or ExportConfig()
            self.data_export_service = PortfolioDataExportService(export_config, logger)
            self._log("Raw data export enabled")

    def run_single_strategy_review(
        self, strategy_config: StrategyConfig
    ) -> PortfolioResults:
        """
        Run portfolio review for a single strategy.

        Args:
            strategy_config: Configuration for the strategy

        Returns:
            PortfolioResults with analysis results
        """
        try:
            self._log(f"Starting single strategy review for {strategy_config.ticker}")

            # Get market data
            data_config = {
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "USE_HOURLY": strategy_config.use_hourly,
            }
            data = get_data(strategy_config.ticker, data_config, self._log)

            # Calculate signals based on strategy type
            if strategy_config.strategy_type == "MACD":
                data = calculate_macd_and_signals(
                    data,
                    strategy_config.fast_period,
                    strategy_config.slow_period,
                    strategy_config.signal_period,
                    data_config,
                    self._log,
                )
            else:
                # Default to MA strategy
                data = calculate_ma_and_signals(
                    data,
                    strategy_config.fast_period,
                    strategy_config.slow_period,
                    data_config,
                    self._log,
                )

            # Create portfolio configuration for backtesting
            portfolio_config = self._create_portfolio_config(strategy_config)

            # Run backtest
            portfolio = backtest_strategy(data, portfolio_config, self._log)

            # Calculate statistics and risk metrics
            stats = portfolio.stats()
            converted_stats = convert_stats(
                stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
                self._log,
                data_config,
                None,
            )

            # Calculate risk metrics if enabled
            risk_metrics = {}
            if self.config.calculate_risk_metrics:
                try:
                    from app.contexts.portfolio.services.risk_metrics_calculator import (
                        RiskMetricsCalculator,
                    )

                    risk_calculator = RiskMetricsCalculator()
                    returns = portfolio.returns()
                    portfolio_value = portfolio.value()
                    risk_metrics = risk_calculator.calculate_comprehensive_risk_metrics(
                        returns, portfolio_value
                    )
                except Exception as e:
                    self._log(
                        f"Error calculating comprehensive risk metrics: {str(e)}",
                        "warning",
                    )
                    # Fall back to basic risk metrics
                    returns = portfolio.returns()
                    returns_array = (
                        returns.to_numpy()
                        if hasattr(returns, "to_numpy")
                        else returns.values
                    )
                    risk_metrics = calculate_risk_metrics(returns_array)

            # Check open positions
            # Create a simple price dataframe for open positions check
            value_series = portfolio.value()
            price_df = (
                pl.DataFrame(
                    {
                        "Date": value_series.index,
                        strategy_config.ticker: value_series.values,
                    }
                )
                .to_pandas()
                .set_index("Date")
            )

            open_positions = check_open_positions(portfolio, price_df, self._log)

            # Export equity curve if enabled
            equity_curve_path = None
            if self.config.export_equity_curve:
                equity_curve_path = self._export_equity_curve(
                    portfolio, strategy_config
                )

            # Create benchmark portfolio (always enabled for buy-and-hold comparison)
            benchmark_portfolio = self._create_benchmark_portfolio(
                strategy_config, data
            )

            # Export raw data if enabled
            export_results = None
            if self.data_export_service:
                portfolio_name = f"{strategy_config.ticker}_{strategy_config.strategy_type}_{strategy_config.fast_period}_{strategy_config.slow_period}"
                export_results = self.data_export_service.export_portfolio_data(
                    portfolio, portfolio_name, benchmark_portfolio
                )
                if export_results.success:
                    self._log(
                        f"Exported raw data for {portfolio_name}: {export_results.total_files} files"
                    )
                else:
                    self._log(
                        f"Failed to export raw data: {export_results.error_message}",
                        "warning",
                    )

            return PortfolioResults(
                portfolio=portfolio,
                benchmark_portfolio=benchmark_portfolio,
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                equity_curve_path=equity_curve_path,
                plot_paths=self.plot_paths.copy(),
                raw_data_export_results=export_results,
            )

        except Exception as e:
            self._log(f"Error in single strategy review: {str(e)}", "error")
            raise

    def run_multi_strategy_review(self) -> PortfolioResults:
        """
        Run portfolio review for multiple strategies with benchmark comparison.

        Returns:
            PortfolioResults with comprehensive analysis
        """
        try:
            self._log("Starting multi-strategy portfolio review")

            # Validate configuration
            if not self.config.strategies:
                raise ValueError("No strategies defined in config")

            # Get unique symbols from strategies
            symbols = list(set(strategy.ticker for strategy in self.config.strategies))
            self._log(f"Processing symbols: {symbols}")

            # Convert strategy configs to the format expected by existing functions
            config_dict = self._convert_to_legacy_config()

            # Download and prepare data
            data_dict, pandas_data_dict = prepare_data(symbols, config_dict, self._log)

            # Find common date range
            common_dates = find_common_dates(data_dict, self._log)
            if not common_dates:
                raise ValueError("No common dates found across symbols")

            # Apply Benchmark-Aligned Start Date: start when strategies are ready to signal
            aligned_start_date = self._calculate_strategy_ready_date(
                common_dates, self.config.strategies
            )
            if aligned_start_date:
                common_dates = [
                    date for date in common_dates if date >= aligned_start_date
                ]
                self._log(
                    f"Benchmark-Aligned Start Date: {aligned_start_date}, reduced to {len(common_dates)} periods"
                )

                # Filter pandas_data_dict to match aligned date range
                aligned_pandas_data_dict = {}
                for symbol, df in pandas_data_dict.items():
                    # Filter DataFrame to only include dates from aligned start date onwards
                    aligned_df = df[df.index >= aligned_start_date].copy()
                    aligned_pandas_data_dict[symbol] = aligned_df
                    self._log(
                        f"Filtered {symbol} data: {len(df)} -> {len(aligned_df)} periods"
                    )
                pandas_data_dict = aligned_pandas_data_dict

            # Create price DataFrame
            price_df_pd = create_pricesframe(
                common_dates, data_dict, config_dict, self._log
            )
            if price_df_pd.empty:
                raise ValueError("Failed to create price DataFrame")

            # Generate trading signals
            self._log("Generating trading signals")
            self._log(f"Processing {len(self.config.strategies)} strategies:")
            for i, strategy in enumerate(self.config.strategies, 1):
                strategy_name = f"{strategy.ticker}_{strategy.fast_period}_{strategy.slow_period}_Strategy"
                self._log(
                    f"  {i}. {strategy_name} - Windows: {strategy.fast_period}/{strategy.slow_period}"
                )

            signal_config = {
                "strategies": {
                    f"{strategy.ticker}_{strategy.fast_period}_{strategy.slow_period}_Strategy": {
                        "symbol": strategy.ticker,
                        "fast_period": strategy.fast_period,
                        "slow_period": strategy.slow_period,
                        "position_size": strategy.position_size,
                        "use_sma": derive_use_sma(
                            strategy.strategy_type.value
                            if hasattr(strategy.strategy_type, "value")
                            else strategy.strategy_type
                        ),
                        "strategy_type": strategy.strategy_type,
                        "signal_period": strategy.signal_period,
                        # Only include stop_loss if it's not None
                        **(
                            {"stop_loss": strategy.stop_loss}
                            if strategy.stop_loss is not None
                            else {}
                        ),
                    }
                    for strategy in self.config.strategies
                },
                "USE_SMA": any(
                    derive_use_sma(
                        strategy.strategy_type.value
                        if hasattr(strategy.strategy_type, "value")
                        else strategy.strategy_type
                    )
                    for strategy in self.config.strategies
                ),
                "USE_RSI": any(
                    strategy.rsi_window is not None
                    for strategy in self.config.strategies
                ),
                "RSI_THRESHOLD": 70,  # Default
                "SHORT": False,
                "init_cash": self.config.init_cash,
                "fees": self.config.fees,
            }

            entries_pd, exits_pd = generate_signals(
                pandas_data_dict, signal_config, self._log
            )
            if entries_pd.empty or exits_pd.empty:
                raise ValueError("Failed to generate trading signals")

            # Log which strategies have signals
            self._log(f"Generated signals for strategies: {list(entries_pd.columns)}")
            for col in entries_pd.columns:
                entry_count = entries_pd[col].sum()
                exit_count = exits_pd[col].sum()
                self._log(f"  {col}: {entry_count} entries, {exit_count} exits")

            # Create dynamic size DataFrame using Strategy-First Allocation Method
            sizes_pd = self._create_dynamic_allocation(
                price_df_pd, entries_pd, exits_pd, self.config.strategies
            )

            # Run the portfolio simulation
            self._log("Running portfolio simulation")
            portfolio = vbt.Portfolio.from_signals(
                close=price_df_pd,
                entries=entries_pd.astype(bool),
                exits=exits_pd.astype(bool),
                size=sizes_pd,
                init_cash=self.config.init_cash,
                fees=self.config.fees,
                freq="1D",
                group_by=True,
                cash_sharing=True,
            )

            # Create benchmark portfolio
            benchmark_portfolio = None
            if self.config.benchmark_symbol or len(symbols) > 1:
                (
                    benchmark_close_pd,
                    benchmark_entries_pd,
                    benchmark_sizes_pd,
                ) = create_benchmark_data(common_dates, data_dict, symbols, self._log)

                benchmark_portfolio = vbt.Portfolio.from_signals(
                    close=benchmark_close_pd,
                    entries=benchmark_entries_pd,
                    size=benchmark_sizes_pd,
                    init_cash=self.config.init_cash,
                    fees=self.config.fees,
                    freq="1D",
                    group_by=True,
                    cash_sharing=True,
                )

            # Calculate statistics and risk metrics
            stats = portfolio.stats()
            converted_stats = convert_stats(
                stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
                self._log,
                {"USE_HOURLY": False, "TICKER": "Portfolio"},
                None,
            )

            # Calculate risk metrics
            risk_metrics = {}
            if self.config.calculate_risk_metrics:
                try:
                    from app.contexts.portfolio.services.risk_metrics_calculator import (
                        RiskMetricsCalculator,
                    )

                    risk_calculator = RiskMetricsCalculator()
                    returns = portfolio.returns()
                    portfolio_value = portfolio.value()
                    risk_metrics = risk_calculator.calculate_comprehensive_risk_metrics(
                        returns, portfolio_value
                    )
                except Exception as e:
                    self._log(
                        f"Error calculating comprehensive risk metrics: {str(e)}",
                        "warning",
                    )
                    # Fall back to basic risk metrics
                    returns = portfolio.returns()
                    returns_array = (
                        returns.to_numpy()
                        if hasattr(returns, "to_numpy")
                        else returns.values
                    )
                    risk_metrics = calculate_risk_metrics(returns_array)

            # Check open positions
            open_positions = check_open_positions(portfolio, price_df_pd, self._log)

            # Export raw data if enabled
            export_results = None
            if self.data_export_service:
                portfolio_name = "multi_strategy_portfolio"
                export_results = self.data_export_service.export_portfolio_data(
                    portfolio, portfolio_name, benchmark_portfolio
                )
                if export_results.success:
                    self._log(
                        f"Exported raw data for {portfolio_name}: {export_results.total_files} files"
                    )
                else:
                    self._log(
                        f"Failed to export raw data: {export_results.error_message}",
                        "warning",
                    )

            return PortfolioResults(
                portfolio=portfolio,
                benchmark_portfolio=benchmark_portfolio,
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                plot_paths=self.plot_paths.copy(),
                raw_data_export_results=export_results,
            )

        except Exception as e:
            self._log(f"Error in multi-strategy review: {str(e)}", "error")
            raise

    def _create_portfolio_config(
        self, strategy_config: StrategyConfig
    ) -> Dict[str, Any]:
        """Create portfolio configuration for backtesting."""
        return {
            "TICKER": strategy_config.ticker,
            "FAST_PERIOD": strategy_config.fast_period,
            "SLOW_PERIOD": strategy_config.slow_period,
            "STRATEGY_TYPE": strategy_config.strategy_type,
            "USE_SMA": derive_use_sma(
                strategy_config.strategy_type.value
                if hasattr(strategy_config.strategy_type, "value")
                else strategy_config.strategy_type
            ),
            "USE_HOURLY": strategy_config.use_hourly,
            "STOP_LOSS": strategy_config.stop_loss,
            "DIRECTION": strategy_config.direction,
            "SIGNAL_PERIOD": strategy_config.signal_period,
            "RSI_WINDOW": strategy_config.rsi_window,
            "RSI_THRESHOLD": strategy_config.rsi_threshold,
        }

    def _create_benchmark_portfolio(
        self, strategy_config: StrategyConfig, data: pl.DataFrame
    ) -> Optional["vbt.Portfolio"]:
        """Create benchmark portfolio for comparison."""
        try:
            # Use explicit benchmark symbol if specified, otherwise use strategy ticker for buy-and-hold
            benchmark_symbol = self.config.benchmark_symbol or strategy_config.ticker

            # For single strategies, create buy-and-hold benchmark using the same data
            if benchmark_symbol == strategy_config.ticker:
                # Use the existing data to avoid redundant API calls
                benchmark_data = data.clone()
            else:
                # Get external benchmark data
                benchmark_config = {
                    "start_date": self.config.start_date,
                    "end_date": self.config.end_date,
                    "USE_HOURLY": strategy_config.use_hourly,
                }
                benchmark_data = get_data(benchmark_symbol, benchmark_config, self._log)

            # Create simple buy-and-hold strategy for benchmark
            benchmark_data = benchmark_data.with_columns(
                [
                    pl.lit(True).alias("Position"),  # Always in position
                    pl.lit(1.0).alias("Size"),  # Full position
                ]
            )

            # Run benchmark backtest
            benchmark_portfolio_config = {
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "USE_HOURLY": strategy_config.use_hourly,
                "TICKER": benchmark_symbol,
                "STRATEGY_TYPE": "BuyAndHold",
            }

            benchmark_portfolio = backtest_strategy(
                benchmark_data, benchmark_portfolio_config, self._log
            )

            self._log(f"Created benchmark portfolio for {benchmark_symbol}")
            return benchmark_portfolio

        except Exception as e:
            self._log(f"Error creating benchmark portfolio: {str(e)}", "warning")
            return None

    def _convert_to_legacy_config(self) -> Dict[str, Any]:
        """Convert modern config to legacy format for existing functions."""
        return {
            "strategies": {
                f"{strategy.ticker}_{strategy.fast_period}_{strategy.slow_period}_Strategy": {
                    "symbol": strategy.ticker,
                    "fast_period": strategy.fast_period,
                    "slow_period": strategy.slow_period,
                    "stop_loss": strategy.stop_loss,
                    "position_size": strategy.position_size,
                    "use_sma": derive_use_sma(
                        strategy.strategy_type.value
                        if hasattr(strategy.strategy_type, "value")
                        else strategy.strategy_type
                    ),
                }
                for strategy in self.config.strategies
            },
            "start_date": self.config.start_date,
            "end_date": self.config.end_date,
            "init_cash": self.config.init_cash,
            "fees": self.config.fees,
        }

    def _export_equity_curve(
        self, portfolio: "vbt.Portfolio", strategy_config: StrategyConfig
    ) -> str:
        """Export equity curve to CSV."""
        try:
            # Extract value series and convert to DataFrame
            value_series = portfolio.value()
            initial_value = value_series[0]
            equity_curve = pl.DataFrame(
                {
                    "Date": value_series.index,
                    "Close": value_series.values / initial_value,
                }
            )

            # Determine output path
            strategy_type_dir = (
                "macd" if strategy_config.strategy_type == "MACD" else "ma_cross"
            )
            csv_path = f"data/outputs/portfolio/{strategy_type_dir}/equity_curve/{strategy_config.ticker}.csv"

            # Ensure directory exists
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)

            # Export
            equity_curve.write_csv(csv_path)
            self._log(f"Exported equity curve to {csv_path}")

            return csv_path

        except Exception as e:
            self._log(f"Error exporting equity curve: {str(e)}", "warning")
            return None

    def _optimize_dataframe(self, df):
        """Optimize dataframe memory usage if memory optimization is enabled."""
        if self.memory_optimizer:
            try:
                return self.memory_optimizer.optimize_dataframe(df)
            except Exception as e:
                self._log(f"Error optimizing dataframe: {str(e)}", "warning")
        return df

    def _process_strategy_parallel(
        self, strategy_config: StrategyConfig
    ) -> Dict[str, Any]:
        """Process a single strategy for parallel execution."""
        try:
            self._log(f"Processing strategy {strategy_config.ticker} in parallel")

            # Get market data
            data_config = {
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "USE_HOURLY": strategy_config.use_hourly,
            }
            data = get_data(strategy_config.ticker, data_config, self._log)

            # Optimize data if memory optimization is enabled
            if self.config.enable_memory_optimization:
                data = self._optimize_dataframe(data)

            # Calculate signals
            if strategy_config.strategy_type == "MACD":
                data = calculate_macd_and_signals(
                    data,
                    strategy_config.fast_period,
                    strategy_config.slow_period,
                    strategy_config.signal_period,
                    data_config,
                    self._log,
                )
            else:
                data = calculate_ma_and_signals(
                    data,
                    strategy_config.fast_period,
                    strategy_config.slow_period,
                    data_config,
                    self._log,
                )

            # Create portfolio configuration
            portfolio_config = self._create_portfolio_config(strategy_config)

            # Run backtest
            portfolio = backtest_strategy(data, portfolio_config, self._log)

            return {
                "strategy_config": strategy_config,
                "portfolio": portfolio,
                "data": data,
                "success": True,
            }

        except Exception as e:
            self._log(
                f"Error processing strategy {strategy_config.ticker}: {str(e)}", "error"
            )
            return {
                "strategy_config": strategy_config,
                "portfolio": None,
                "data": None,
                "success": False,
                "error": str(e),
            }

    def run_multi_strategy_review_parallel(self) -> PortfolioResults:
        """
        Run portfolio review for multiple strategies using parallel processing.

        Returns:
            PortfolioResults with comprehensive analysis
        """
        try:
            self._log("Starting parallel multi-strategy portfolio review")

            if not self.config.enable_parallel_processing:
                return self.run_multi_strategy_review()

            # Validate configuration
            if not self.config.strategies:
                raise ValueError("No strategies defined in config")

            # Process strategies in parallel
            strategy_results = []
            max_workers = self.config.max_workers or min(len(self.config.strategies), 4)

            self._log(
                f"Processing {len(self.config.strategies)} strategies with {max_workers} workers"
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all strategy processing tasks
                future_to_strategy = {
                    executor.submit(self._process_strategy_parallel, strategy): strategy
                    for strategy in self.config.strategies
                }

                # Collect results as they complete
                for future in as_completed(future_to_strategy):
                    strategy = future_to_strategy[future]
                    try:
                        result = future.result()
                        strategy_results.append(result)

                        if result["success"]:
                            self._log(f"✓ Completed {strategy.ticker}")
                        else:
                            self._log(
                                f"✗ Failed {strategy.ticker}: {result.get('error', 'Unknown error')}"
                            )

                    except Exception as e:
                        self._log(
                            f"✗ Exception processing {strategy.ticker}: {str(e)}",
                            "error",
                        )
                        strategy_results.append(
                            {
                                "strategy_config": strategy,
                                "portfolio": None,
                                "data": None,
                                "success": False,
                                "error": str(e),
                            }
                        )

            # Filter successful results
            successful_results = [r for r in strategy_results if r["success"]]
            if not successful_results:
                raise ValueError("No strategies processed successfully")

            self._log(
                f"Successfully processed {len(successful_results)}/{len(strategy_results)} strategies"
            )

            # Combine portfolios (simplified approach - using first successful portfolio as base)
            # In a more sophisticated implementation, you would properly combine the portfolios
            primary_result = successful_results[0]
            combined_portfolio = primary_result["portfolio"]

            # Calculate combined statistics
            stats = combined_portfolio.stats()
            converted_stats = convert_stats(
                stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
                self._log,
                {"USE_HOURLY": False, "TICKER": "Parallel Portfolio"},
                None,
            )

            # Calculate risk metrics
            risk_metrics = {}
            if self.config.calculate_risk_metrics:
                returns = combined_portfolio.returns()
                returns_array = (
                    returns.to_numpy()
                    if hasattr(returns, "to_numpy")
                    else returns.values
                )
                risk_metrics = calculate_risk_metrics(returns_array)

            # Create a simple price dataframe for open positions check
            value_series = combined_portfolio.value()
            price_df = (
                pl.DataFrame(
                    {"Date": value_series.index, "Portfolio": value_series.values}
                )
                .to_pandas()
                .set_index("Date")
            )

            open_positions = check_open_positions(
                combined_portfolio, price_df, self._log
            )

            # Export raw data if enabled
            export_results = None
            if self.data_export_service:
                portfolio_name = "parallel_portfolio"
                export_results = self.data_export_service.export_portfolio_data(
                    combined_portfolio, portfolio_name, None
                )
                if export_results.success:
                    self._log(
                        f"Exported raw data for {portfolio_name}: {export_results.total_files} files"
                    )
                else:
                    self._log(
                        f"Failed to export raw data: {export_results.error_message}",
                        "warning",
                    )

            return PortfolioResults(
                portfolio=combined_portfolio,
                benchmark_portfolio=None,  # Simplified - no benchmark for parallel processing
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                plot_paths=self.plot_paths.copy(),
                raw_data_export_results=export_results,
            )

        except Exception as e:
            self._log(f"Error in parallel multi-strategy review: {str(e)}", "error")
            # Fall back to sequential processing
            self._log("Falling back to sequential processing")
            return self.run_multi_strategy_review()

    def _create_dynamic_allocation(
        self,
        price_df_pd: pd.DataFrame,
        entries_pd: pd.DataFrame,
        exits_pd: pd.DataFrame,
        strategies: List[StrategyConfig],
    ) -> pd.DataFrame:
        """
        Create dynamic allocation using Strategy-First Allocation Method.

        Rules:
        - When one strategy signals and other is inactive: 100% to active strategy
        - When both strategies signal: 50/50 split
        - When no strategies signal: hold cash (0% allocation)

        Args:
            price_df_pd: Price data DataFrame
            entries_pd: Entry signals DataFrame
            exits_pd: Exit signals DataFrame
            strategies: List of strategy configurations

        Returns:
            Dynamic size allocation DataFrame
        """
        # Initialize sizes DataFrame with zeros
        sizes_pd = price_df_pd.copy()

        # Clear all columns and initialize with zeros
        for col in sizes_pd.columns:
            sizes_pd[col] = 0.0

        # Get strategy names
        strategy_names = []
        for strategy in strategies:
            strategy_name = f"{strategy.ticker}_{strategy.fast_period}_{strategy.slow_period}_Strategy"
            strategy_names.append(strategy_name)
            sizes_pd[strategy_name] = 0.0

        # Create position tracking for each strategy
        positions = {}
        for strategy_name in strategy_names:
            positions[strategy_name] = False

        self._log(
            f"Implementing Strategy-First Allocation for strategies: {strategy_names}"
        )

        # Process each date to determine dynamic allocation
        allocation_changes = 0
        for date in sizes_pd.index:
            if date not in entries_pd.index or date not in exits_pd.index:
                continue

            # Update positions based on entry/exit signals
            for strategy_name in strategy_names:
                if (
                    strategy_name in entries_pd.columns
                    and entries_pd.loc[date, strategy_name]
                ):
                    positions[strategy_name] = True
                if (
                    strategy_name in exits_pd.columns
                    and exits_pd.loc[date, strategy_name]
                ):
                    positions[strategy_name] = False

            # Count active strategies
            active_strategies = sum(1 for pos in positions.values() if pos)

            # Apply Strategy-First Allocation Method
            if active_strategies == 0:
                # No strategies active: hold cash (0% allocation)
                for strategy_name in strategy_names:
                    sizes_pd.loc[date, strategy_name] = 0.0

            elif active_strategies == 1:
                # One strategy active: 100% allocation to active strategy
                allocation_changes += 1
                for strategy_name in strategy_names:
                    if positions[strategy_name]:
                        sizes_pd.loc[date, strategy_name] = 1.0  # 100% allocation
                    else:
                        sizes_pd.loc[date, strategy_name] = 0.0

            else:
                # Multiple strategies active: equal split
                allocation_per_strategy = 1.0 / active_strategies
                for strategy_name in strategy_names:
                    if positions[strategy_name]:
                        sizes_pd.loc[date, strategy_name] = allocation_per_strategy
                    else:
                        sizes_pd.loc[date, strategy_name] = 0.0

        self._log(
            f"Strategy-First Allocation complete. {allocation_changes} periods with 100% single-strategy allocation"
        )

        # Log allocation summary
        for strategy_name in strategy_names:
            max_alloc = sizes_pd[strategy_name].max()
            mean_alloc = sizes_pd[strategy_name].mean()
            nonzero_periods = (sizes_pd[strategy_name] > 0).sum()
            total_periods = len(sizes_pd)
            self._log(
                f"  {strategy_name}: max={max_alloc:.1%}, mean={mean_alloc:.1%}, active={nonzero_periods}/{total_periods} periods"
            )

        return sizes_pd

    def _calculate_strategy_ready_date(
        self, common_dates: List, strategies: List[StrategyConfig]
    ) -> Optional[any]:
        """
        Calculate the date when strategies are ready to start signaling.

        For SMA strategies, we need enough periods to calculate the longest moving average.

        Args:
            common_dates: List of available dates
            strategies: List of strategy configurations

        Returns:
            Date when all strategies can start signaling, or None if no adjustment needed
        """
        if not strategies or not common_dates:
            return None

        # Find the maximum window size across all strategies
        max_window = 0
        for strategy in strategies:
            # For SMA strategies, we need the longer window
            if strategy.strategy_type.upper() in ["SMA", "EMA"]:
                max_window = max(max_window, strategy.slow_period)
            elif strategy.strategy_type.upper() == "MACD":
                # For MACD, we typically need the slow period + signal line
                max_window = max(
                    max_window, strategy.slow_period + (strategy.signal_period or 9)
                )

        if max_window <= 1:
            return None  # No adjustment needed

        # Calculate the ready date (skip the required periods for MA calculation)
        if len(common_dates) > max_window:
            ready_date = common_dates[
                max_window - 1
            ]  # -1 because we start counting from 0
            self._log(
                f"Strategy ready calculation: max_window={max_window}, ready_date={ready_date}"
            )
            return ready_date
        else:
            self._log(
                f"Warning: Not enough data periods ({len(common_dates)}) for max_window={max_window}"
            )
            return None

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
