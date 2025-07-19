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

import polars as pl
import vectorbt as vbt

from app.portfolio_review.tools.portfolio_analysis import (
    calculate_risk_metrics,
    check_open_positions,
    create_benchmark_data,
    create_price_dataframe,
    find_common_dates,
    prepare_data,
)
from app.strategies.ma_cross.tools.generate_signals import generate_signals
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_data import get_data
from app.tools.stats_converter import convert_stats
from app.utils import backtest_strategy


@dataclass
class StrategyConfig:
    """Configuration for a single strategy."""

    ticker: str
    short_window: int
    long_window: int
    strategy_type: str = "SMA"
    direction: str = "long"
    stop_loss: Optional[float] = None
    position_size: float = 1.0
    use_sma: bool = True
    use_hourly: bool = False
    rsi_window: Optional[int] = None
    rsi_threshold: Optional[int] = None
    signal_window: int = 9  # For MACD


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
                    strategy_config.short_window,
                    strategy_config.long_window,
                    strategy_config.signal_window,
                    data_config,
                    self._log,
                )
            else:
                # Default to MA strategy
                data = calculate_ma_and_signals(
                    data,
                    strategy_config.short_window,
                    strategy_config.long_window,
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

            # Create benchmark portfolio if specified
            benchmark_portfolio = None
            if self.config.benchmark_symbol:
                benchmark_portfolio = self._create_benchmark_portfolio(
                    strategy_config, data
                )

            return PortfolioResults(
                portfolio=portfolio,
                benchmark_portfolio=benchmark_portfolio,
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                equity_curve_path=equity_curve_path,
                plot_paths=self.plot_paths.copy(),
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

            # Create price DataFrame
            price_df_pd = create_price_dataframe(
                common_dates, data_dict, config_dict, self._log
            )
            if price_df_pd.empty:
                raise ValueError("Failed to create price DataFrame")

            # Generate trading signals
            self._log("Generating trading signals")
            signal_config = {
                "strategies": {
                    f"{strategy.ticker}_Strategy": {
                        "symbol": strategy.ticker,
                        "short_window": strategy.short_window,
                        "long_window": strategy.long_window,
                        "position_size": strategy.position_size,
                        "use_sma": strategy.use_sma,
                        "strategy_type": strategy.strategy_type,
                        "signal_window": strategy.signal_window,
                        # Only include stop_loss if it's not None
                        **(
                            {"stop_loss": strategy.stop_loss}
                            if strategy.stop_loss is not None
                            else {}
                        ),
                    }
                    for strategy in self.config.strategies
                },
                "USE_SMA": any(strategy.use_sma for strategy in self.config.strategies),
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

            # Create size DataFrame
            sizes_pd = price_df_pd.copy()
            for strategy in self.config.strategies:
                strategy_name = f"{strategy.ticker}_Strategy"
                if strategy_name in sizes_pd.columns:
                    sizes_pd[strategy_name] = strategy.position_size

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

            return PortfolioResults(
                portfolio=portfolio,
                benchmark_portfolio=benchmark_portfolio,
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                plot_paths=self.plot_paths.copy(),
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
            "SHORT_WINDOW": strategy_config.short_window,
            "LONG_WINDOW": strategy_config.long_window,
            "STRATEGY_TYPE": strategy_config.strategy_type,
            "USE_SMA": strategy_config.use_sma,
            "USE_HOURLY": strategy_config.use_hourly,
            "STOP_LOSS": strategy_config.stop_loss,
            "DIRECTION": strategy_config.direction,
            "SIGNAL_WINDOW": strategy_config.signal_window,
            "RSI_WINDOW": strategy_config.rsi_window,
            "RSI_THRESHOLD": strategy_config.rsi_threshold,
        }

    def _create_benchmark_portfolio(
        self, strategy_config: StrategyConfig, data: pl.DataFrame
    ) -> Optional["vbt.Portfolio"]:
        """Create benchmark portfolio for comparison."""
        if not self.config.benchmark_symbol:
            return None

        try:
            # Get benchmark data
            benchmark_config = {
                "start_date": self.config.start_date,
                "end_date": self.config.end_date,
                "USE_HOURLY": strategy_config.use_hourly,
            }
            benchmark_data = get_data(
                self.config.benchmark_symbol, benchmark_config, self._log
            )

            # Create simple buy-and-hold strategy for benchmark
            benchmark_data = benchmark_data.with_columns(
                [
                    pl.lit(True).alias("Position"),  # Always in position
                    pl.lit(1.0).alias("Size"),  # Full position
                ]
            )

            # Run benchmark backtest
            benchmark_portfolio_config = {
                **benchmark_config,
                "TICKER": self.config.benchmark_symbol,
                "STRATEGY_TYPE": "BuyAndHold",
            }

            benchmark_portfolio = backtest_strategy(
                benchmark_data, benchmark_portfolio_config, self._log
            )

            return benchmark_portfolio

        except Exception as e:
            self._log(f"Error creating benchmark portfolio: {str(e)}", "warning")
            return None

    def _convert_to_legacy_config(self) -> Dict[str, Any]:
        """Convert modern config to legacy format for existing functions."""
        return {
            "strategies": {
                f"{strategy.ticker}_Strategy": {
                    "symbol": strategy.ticker,
                    "short_window": strategy.short_window,
                    "long_window": strategy.long_window,
                    "stop_loss": strategy.stop_loss,
                    "position_size": strategy.position_size,
                    "use_sma": strategy.use_sma,
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
            csv_path = f"data/outputs/portfolio_review/{strategy_type_dir}/equity_curve/{strategy_config.ticker}.csv"

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
                    strategy_config.short_window,
                    strategy_config.long_window,
                    strategy_config.signal_window,
                    data_config,
                    self._log,
                )
            else:
                data = calculate_ma_and_signals(
                    data,
                    strategy_config.short_window,
                    strategy_config.long_window,
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

            return PortfolioResults(
                portfolio=combined_portfolio,
                benchmark_portfolio=None,  # Simplified - no benchmark for parallel processing
                statistics=converted_stats,
                risk_metrics=risk_metrics,
                open_positions=open_positions,
                plot_paths=self.plot_paths.copy(),
            )

        except Exception as e:
            self._log(f"Error in parallel multi-strategy review: {str(e)}", "error")
            # Fall back to sequential processing
            self._log("Falling back to sequential processing")
            return self.run_multi_strategy_review()

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
