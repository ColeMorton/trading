"""
Benchmark Comparison Service

Standardized service for creating and comparing portfolio performance
against various benchmark strategies.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt

from app.tools.get_data import get_data


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark creation."""

    symbol: str
    strategy_type: str = "buy_and_hold"
    rebalance_frequency: str = "none"  # none, daily, weekly, monthly
    allocation_method: str = "equal_weight"  # equal_weight, market_cap, custom
    custom_weights: Optional[Dict[str, float]] = None


@dataclass
class ComparisonMetrics:
    """Metrics comparing portfolio to benchmark performance."""

    excess_return: float
    tracking_error: float
    information_ratio: float
    beta: float
    alpha: float
    correlation: float
    max_drawdown_diff: float
    sharpe_ratio_diff: float
    win_rate_vs_benchmark: float


class BenchmarkComparisonService:
    """
    Service for creating benchmarks and comparing portfolio performance.

    Supports multiple benchmark types:
    - Buy and hold (single asset or portfolio)
    - Equal weighted portfolios
    - Market cap weighted portfolios
    - Custom weighted portfolios
    - Rebalanced portfolios
    """

    def __init__(self, logger=None):
        """Initialize benchmark comparison service."""
        self.logger = logger

    def create_benchmark_portfolio(
        self,
        benchmark_config: BenchmarkConfig,
        start_date: str,
        end_date: str,
        init_cash: float = 10000.0,
        fees: float = 0.001,
        symbols: Optional[List[str]] = None,
    ) -> "vbt.Portfolio":
        """
        Create benchmark portfolio based on configuration.

        Args:
            benchmark_config: Benchmark configuration
            start_date: Start date for analysis
            end_date: End date for analysis
            init_cash: Initial cash amount
            fees: Trading fees
            symbols: List of symbols for multi-asset benchmarks

        Returns:
            VectorBT Portfolio object representing the benchmark
        """
        # Define fallback benchmarks in order of preference
        fallback_symbols = ["SPY", "QQQ", "VTI", "VTSMX"]
        original_symbol = benchmark_config.symbol

        try:
            if benchmark_config.strategy_type == "buy_and_hold":
                try:
                    return self._create_buy_and_hold_benchmark(
                        benchmark_config.symbol, start_date, end_date, init_cash, fees
                    )
                except ValueError as e:
                    # Try fallback symbols if original symbol fails
                    if (
                        benchmark_config.symbol
                        and benchmark_config.symbol not in fallback_symbols
                    ):
                        self._log(
                            f"Primary benchmark '{benchmark_config.symbol}' failed, trying fallbacks",
                            "warning",
                        )

                        for fallback_symbol in fallback_symbols:
                            try:
                                self._log(
                                    f"Attempting fallback benchmark: {fallback_symbol}",
                                    "info",
                                )
                                return self._create_buy_and_hold_benchmark(
                                    fallback_symbol,
                                    start_date,
                                    end_date,
                                    init_cash,
                                    fees,
                                )
                            except ValueError:
                                continue

                        # If all fallbacks fail, provide helpful error message
                        self._log(
                            f"All benchmark symbols failed. Tried: {original_symbol}, {', '.join(fallback_symbols)}",
                            "error",
                        )
                        raise ValueError(
                            f"Could not create benchmark. Primary symbol '{original_symbol}' and fallback symbols "
                            f"({', '.join(fallback_symbols)}) all failed. Check your date range and network connectivity."
                        ) from e
                    else:
                        raise

            elif benchmark_config.strategy_type == "equal_weighted_portfolio":
                if not symbols:
                    raise ValueError(
                        "Symbols required for equal weighted portfolio benchmark"
                    )

                try:
                    return self._create_equal_weighted_benchmark(
                        symbols, start_date, end_date, init_cash, fees, benchmark_config
                    )
                except Exception as e:
                    # For multi-asset benchmarks, try with subset of working symbols
                    self._log(
                        f"Equal weighted benchmark failed, attempting with valid symbols only",
                        "warning",
                    )

                    valid_symbols = []
                    for symbol in symbols:
                        try:
                            # Test if we can get data for this symbol
                            config = {"start_date": start_date, "end_date": end_date}
                            test_data = get_data(symbol, config, self._log)
                            if test_data.height > 0:
                                valid_symbols.append(symbol)
                        except:
                            self._log(
                                f"Excluding invalid symbol '{symbol}' from benchmark",
                                "debug",
                            )
                            continue

                    if len(valid_symbols) >= 1:
                        self._log(
                            f"Creating benchmark with {len(valid_symbols)} valid symbols: {valid_symbols}",
                            "info",
                        )
                        return self._create_equal_weighted_benchmark(
                            valid_symbols,
                            start_date,
                            end_date,
                            init_cash,
                            fees,
                            benchmark_config,
                        )
                    else:
                        raise ValueError(
                            "No valid symbols available for equal weighted benchmark"
                        ) from e

            elif benchmark_config.strategy_type == "custom_weighted_portfolio":
                if not symbols or not benchmark_config.custom_weights:
                    raise ValueError(
                        "Symbols and custom weights required for custom weighted benchmark"
                    )
                return self._create_custom_weighted_benchmark(
                    symbols, start_date, end_date, init_cash, fees, benchmark_config
                )

            else:
                raise ValueError(
                    f"Unsupported benchmark strategy type: {benchmark_config.strategy_type}"
                )

        except ValueError:
            # Re-raise validation errors with original message
            raise
        except Exception as e:
            self._log(
                f"Unexpected error creating benchmark portfolio: {str(e)}", "error"
            )
            self._log(
                "Suggestion: Check network connectivity, date ranges, and symbol validity",
                "info",
            )
            raise ValueError("Benchmark creation failed due to unexpected error") from e

    def compare_portfolios(
        self, portfolio: "vbt.Portfolio", benchmark_portfolio: "vbt.Portfolio"
    ) -> ComparisonMetrics:
        """
        Compare portfolio performance against benchmark.

        Args:
            portfolio: Strategy portfolio to analyze
            benchmark_portfolio: Benchmark portfolio for comparison

        Returns:
            ComparisonMetrics with detailed comparison
        """
        try:
            # Get returns series
            portfolio_returns = portfolio.returns()
            benchmark_returns = benchmark_portfolio.returns()

            # Align returns (ensure same dates)
            common_index = portfolio_returns.index.intersection(benchmark_returns.index)
            portfolio_returns = portfolio_returns.loc[common_index]
            benchmark_returns = benchmark_returns.loc[common_index]

            # Convert to numpy arrays for calculations
            port_ret = portfolio_returns.values
            bench_ret = benchmark_returns.values

            # Calculate comparison metrics
            excess_return = np.mean(port_ret - bench_ret) * 252  # Annualized

            # Tracking error (standard deviation of excess returns)
            tracking_error = np.std(port_ret - bench_ret) * np.sqrt(252)

            # Information ratio
            information_ratio = (
                excess_return / tracking_error if tracking_error != 0 else 0
            )

            # Beta and Alpha (CAPM)
            beta = self._calculate_beta(port_ret, bench_ret)
            alpha = self._calculate_alpha(port_ret, bench_ret, beta)

            # Correlation
            correlation = (
                np.corrcoef(port_ret, bench_ret)[0, 1] if len(port_ret) > 1 else 0
            )

            # Drawdown comparison
            portfolio_dd = (
                portfolio.drawdowns.max_drawdown.iloc[0]
                if hasattr(portfolio.drawdowns, "max_drawdown")
                else 0
            )
            benchmark_dd = (
                benchmark_portfolio.drawdowns.max_drawdown.iloc[0]
                if hasattr(benchmark_portfolio.drawdowns, "max_drawdown")
                else 0
            )
            max_drawdown_diff = portfolio_dd - benchmark_dd

            # Sharpe ratio comparison
            portfolio_sharpe = self._calculate_sharpe_ratio(port_ret)
            benchmark_sharpe = self._calculate_sharpe_ratio(bench_ret)
            sharpe_ratio_diff = portfolio_sharpe - benchmark_sharpe

            # Win rate vs benchmark (percentage of periods where portfolio outperformed)
            win_rate_vs_benchmark = np.mean(port_ret > bench_ret) * 100

            return ComparisonMetrics(
                excess_return=excess_return,
                tracking_error=tracking_error,
                information_ratio=information_ratio,
                beta=beta,
                alpha=alpha,
                correlation=correlation,
                max_drawdown_diff=max_drawdown_diff,
                sharpe_ratio_diff=sharpe_ratio_diff,
                win_rate_vs_benchmark=win_rate_vs_benchmark,
            )

        except Exception as e:
            self._log(f"Error comparing portfolios: {str(e)}", "error")
            raise

    def create_multi_asset_benchmark(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        init_cash: float = 10000.0,
        fees: float = 0.001,
        allocation_method: str = "equal_weight",
    ) -> Tuple["vbt.Portfolio", pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create benchmark from multiple assets with specified allocation.

        Args:
            symbols: List of symbols for benchmark
            start_date: Start date
            end_date: End date
            init_cash: Initial cash
            fees: Trading fees
            allocation_method: Allocation method (equal_weight, etc.)

        Returns:
            Tuple of (benchmark_portfolio, close_prices, entries, sizes)
        """
        try:
            self._log(f"Creating multi-asset benchmark with {len(symbols)} symbols")

            # Download data for all symbols
            data_dict = {}
            for symbol in symbols:
                config = {"start_date": start_date, "end_date": end_date}
                df = get_data(symbol, config, self._log)
                data_dict[symbol] = df

            # Find common dates
            common_dates = None
            for df in data_dict.values():
                dates = df.get_column("Date").to_list()
                if common_dates is None:
                    common_dates = set(dates)
                else:
                    common_dates = common_dates.intersection(set(dates))

            common_dates = sorted(list(common_dates))
            self._log(f"Found {len(common_dates)} common trading days")

            # Create aligned price DataFrame
            price_df = pl.DataFrame(
                {"Date": pl.Series(common_dates).cast(pl.Datetime("ns"))}
            )

            for symbol in symbols:
                close_prices = data_dict[symbol].select(["Date", "Close"])
                price_df = price_df.join(
                    close_prices.rename({"Close": symbol}), on="Date", how="left"
                )

            # Convert to pandas for VectorBT
            close_pd = price_df.to_pandas().set_index("Date")

            # Ensure numeric types
            for col in close_pd.columns:
                close_pd[col] = pd.to_numeric(close_pd[col], errors="coerce")

            # Create entries (buy and hold - enter on first day)
            entries_pd = pd.DataFrame(index=close_pd.index, columns=close_pd.columns)
            entries_pd.iloc[0] = True  # Enter on first day
            entries_pd.iloc[1:] = False  # No more entries
            entries_pd = entries_pd.astype(bool)

            # Create position sizes based on allocation method
            if allocation_method == "equal_weight":
                weight = 1.0 / len(symbols)
                sizes_pd = pd.DataFrame(
                    weight, index=close_pd.index, columns=close_pd.columns
                )
            else:
                raise ValueError(f"Unsupported allocation method: {allocation_method}")

            # Create benchmark portfolio
            benchmark_portfolio = vbt.Portfolio.from_signals(
                close=close_pd,
                entries=entries_pd,
                size=sizes_pd,
                init_cash=init_cash,
                fees=fees,
                freq="1D",
                group_by=True,
                cash_sharing=True,
            )

            return benchmark_portfolio, close_pd, entries_pd, sizes_pd

        except Exception as e:
            self._log(f"Error creating multi-asset benchmark: {str(e)}", "error")
            raise

    def _create_buy_and_hold_benchmark(
        self, symbol: str, start_date: str, end_date: str, init_cash: float, fees: float
    ) -> "vbt.Portfolio":
        """Create simple buy and hold benchmark for single asset."""
        try:
            # Get data with specific error handling
            config = {"start_date": start_date, "end_date": end_date}

            try:
                data = get_data(symbol, config, self._log)
            except Exception as e:
                self._log(
                    f"Failed to fetch data for benchmark symbol '{symbol}': {str(e)}",
                    "error",
                )
                self._log(
                    f"Suggestion: Verify symbol '{symbol}' is valid and data is available for date range {start_date} to {end_date}",
                    "info",
                )
                raise ValueError(
                    f"Benchmark data unavailable for symbol '{symbol}'"
                ) from e

            # Validate data quality
            if data.height == 0:
                raise ValueError(
                    f"No data available for benchmark symbol '{symbol}' in the specified date range"
                )

            if "Close" not in data.columns:
                raise ValueError(
                    f"Price data for '{symbol}' missing required 'Close' column"
                )

            # Convert to pandas with validation
            try:
                data_pd = data.to_pandas().set_index("Date")
                close_prices = data_pd["Close"]

                # Check for valid prices
                if close_prices.isna().all():
                    raise ValueError(f"All price data for '{symbol}' is invalid (NaN)")

                if (close_prices <= 0).any():
                    self._log(
                        f"Warning: Found non-positive prices for '{symbol}', may affect benchmark accuracy",
                        "warning",
                    )

            except Exception as e:
                self._log(
                    f"Failed to process price data for '{symbol}': {str(e)}", "error"
                )
                raise ValueError(
                    f"Invalid price data format for benchmark symbol '{symbol}'"
                ) from e

            # Create entries (buy on first day only)
            entries = pd.Series(False, index=close_prices.index)
            entries.iloc[0] = True

            # Full position size
            sizes = pd.Series(1.0, index=close_prices.index)

            # Create portfolio with error handling
            try:
                portfolio = vbt.Portfolio.from_signals(
                    close=close_prices,
                    entries=entries,
                    size=sizes,
                    init_cash=init_cash,
                    fees=fees,
                    freq="1D",
                )

                # Validate portfolio creation
                if portfolio.total_return() is None or np.isnan(
                    portfolio.total_return()
                ):
                    self._log(
                        f"Warning: Benchmark portfolio for '{symbol}' has invalid return",
                        "warning",
                    )

            except Exception as e:
                self._log(
                    f"Failed to create VectorBT portfolio for '{symbol}': {str(e)}",
                    "error",
                )
                raise ValueError(
                    f"Benchmark portfolio creation failed for '{symbol}'"
                ) from e

            self._log(
                f"Successfully created buy-and-hold benchmark for '{symbol}'", "debug"
            )
            return portfolio

        except ValueError:
            # Re-raise validation errors with original message
            raise
        except Exception as e:
            self._log(
                f"Unexpected error creating buy and hold benchmark for '{symbol}': {str(e)}",
                "error",
            )
            raise ValueError(
                f"Benchmark creation failed due to unexpected error"
            ) from e

    def _create_equal_weighted_benchmark(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        init_cash: float,
        fees: float,
        benchmark_config: BenchmarkConfig,
    ) -> "vbt.Portfolio":
        """Create equal weighted portfolio benchmark."""
        portfolio, _, _, _ = self.create_multi_asset_benchmark(
            symbols, start_date, end_date, init_cash, fees, "equal_weight"
        )
        return portfolio

    def _create_custom_weighted_benchmark(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        init_cash: float,
        fees: float,
        benchmark_config: BenchmarkConfig,
    ) -> "vbt.Portfolio":
        """Create custom weighted portfolio benchmark."""
        # Implementation for custom weights would go here
        # For now, fall back to equal weight
        return self._create_equal_weighted_benchmark(
            symbols, start_date, end_date, init_cash, fees, benchmark_config
        )

    def _calculate_beta(
        self, portfolio_returns: np.ndarray, benchmark_returns: np.ndarray
    ) -> float:
        """Calculate portfolio beta relative to benchmark."""
        try:
            if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
                return 1.0

            covariance = np.cov(portfolio_returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)

            if benchmark_variance == 0:
                return 1.0

            return covariance / benchmark_variance

        except Exception:
            return 1.0

    def _calculate_alpha(
        self, portfolio_returns: np.ndarray, benchmark_returns: np.ndarray, beta: float
    ) -> float:
        """Calculate portfolio alpha (excess return after adjusting for beta)."""
        try:
            portfolio_mean = np.mean(portfolio_returns) * 252  # Annualized
            benchmark_mean = np.mean(benchmark_returns) * 252  # Annualized

            # Alpha = Portfolio Return - (Risk-free rate + Beta * (Benchmark Return - Risk-free rate))
            # Assuming risk-free rate = 0 for simplicity
            alpha = portfolio_mean - (beta * benchmark_mean)

            return alpha

        except Exception:
            return 0.0

    def _calculate_sharpe_ratio(
        self, returns: np.ndarray, risk_free_rate: float = 0.0
    ) -> float:
        """Calculate Sharpe ratio for returns series."""
        try:
            if len(returns) < 2:
                return 0.0

            mean_return = np.mean(returns) * 252  # Annualized
            std_return = np.std(returns) * np.sqrt(252)  # Annualized

            if std_return == 0:
                return 0.0

            return (mean_return - risk_free_rate) / std_return

        except Exception:
            return 0.0

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
