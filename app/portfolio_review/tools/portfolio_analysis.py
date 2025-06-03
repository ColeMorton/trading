"""
Portfolio Analysis Module

This module provides core functionality for analyzing portfolios including:
- Data preparation and alignment
- Signal generation
- Portfolio simulation
- Performance metrics calculation
"""

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt

from app.tools.get_data import get_data


def prepare_data(
    symbols: List[str], config: Dict, log
) -> Tuple[Dict[str, pl.DataFrame], Dict[str, pd.DataFrame]]:
    """
    Download and prepare data for all symbols.

    Args:
        symbols: List of trading symbols
        config: Configuration dictionary
        log: Logging function

    Returns:
        Tuple containing polars and pandas DataFrames dictionaries
    """
    data_dict: Dict[str, pl.DataFrame] = {}
    pandas_data_dict: Dict[str, pd.DataFrame] = {}

    for symbol in symbols:
        log(f"Downloading data for {symbol}")
        df = get_data(
            symbol,
            {"start_date": config["start_date"], "end_date": config["end_date"]},
            log,
        ).with_columns(pl.col("Date").cast(pl.Datetime("ns")).alias("Date"))
        data_dict[symbol] = df

        # Create pandas version for generate_signals
        pandas_df = df.to_pandas()
        pandas_df.set_index("Date", inplace=True)
        pandas_data_dict[symbol] = pandas_df

    return data_dict, pandas_data_dict


def find_common_dates(data_dict: Dict[str, pl.DataFrame], log) -> List:
    """Find common date range across all symbols."""
    common_dates = None
    for df in data_dict.values():
        dates = df.get_column("Date").to_list()
        if common_dates is None:
            common_dates = set(dates)
        else:
            common_dates = common_dates.intersection(set(dates))
    common_dates = sorted(list(common_dates))
    log(f"Date range: {common_dates[0]} to {common_dates[-1]}")
    return common_dates


def create_price_dataframe(
    common_dates: List, data_dict: Dict[str, pl.DataFrame], config: Dict, log
) -> pd.DataFrame:
    """Create aligned price DataFrame for all strategies."""
    price_df = pl.DataFrame({"Date": pl.Series(common_dates).cast(pl.Datetime("ns"))})

    for strategy_name, strategy in config["strategies"].items():
        close_prices = data_dict[strategy["symbol"]].select(["Date", "Close"])
        price_df = price_df.join(
            close_prices.rename({"Close": strategy_name}), on="Date", how="left"
        )

    # Convert to pandas for vectorbt
    price_df_pd = price_df.to_pandas().set_index("Date")

    # Ensure numeric type for all price columns
    for col in price_df_pd.columns:
        price_df_pd[col] = pd.to_numeric(price_df_pd[col], errors="coerce")

    return price_df_pd


def create_benchmark_data(
    common_dates: List, data_dict: Dict[str, pl.DataFrame], symbols: List[str], log
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create benchmark portfolio data."""
    benchmark_close = pl.DataFrame(
        {"Date": pl.Series(common_dates).cast(pl.Datetime("ns"))}
    )

    for symbol in symbols:
        close_prices = data_dict[symbol].select(["Date", "Close"])
        benchmark_close = benchmark_close.join(
            close_prices.rename({"Close": symbol}), on="Date", how="left"
        )
    benchmark_close_pd = benchmark_close.to_pandas().set_index("Date")

    # Ensure numeric type for benchmark prices
    for col in benchmark_close_pd.columns:
        benchmark_close_pd[col] = pd.to_numeric(
            benchmark_close_pd[col], errors="coerce"
        )

    # Create benchmark entries (always True after first row)
    benchmark_entries = pl.DataFrame(
        {"Date": pl.Series(common_dates).cast(pl.Datetime("ns"))}
    )
    for symbol in symbols:
        benchmark_entries = benchmark_entries.with_columns(
            pl.Series(name=symbol, values=[False] + [True] * (len(common_dates) - 1))
        )
    benchmark_entries_pd = benchmark_entries.to_pandas().set_index("Date")
    benchmark_entries_pd = benchmark_entries_pd.astype(bool)

    # Create benchmark position sizes (equal weight split)
    weight = 1.0 / len(symbols)
    benchmark_sizes = pl.DataFrame(
        {"Date": pl.Series(common_dates).cast(pl.Datetime("ns"))}
    )
    for symbol in symbols:
        benchmark_sizes = benchmark_sizes.with_columns(pl.lit(weight).alias(symbol))
    benchmark_sizes_pd = benchmark_sizes.to_pandas().set_index("Date")
    benchmark_sizes_pd = benchmark_sizes_pd.astype(float)

    return benchmark_close_pd, benchmark_entries_pd, benchmark_sizes_pd


def calculate_risk_metrics(returns: np.ndarray) -> Dict[str, float]:
    """Calculate VaR and CVaR risk metrics."""
    var_99 = np.percentile(returns, 1)  # 1st percentile for 99% VaR
    cvar_99 = returns[returns <= var_99].mean()
    var_95 = np.percentile(returns, 5)  # 5th percentile for 95% VaR
    cvar_95 = returns[returns <= var_95].mean()

    return {
        "VaR 95%": var_95,
        "CVaR 95%": cvar_95,
        "VaR 99%": var_99,
        "CVaR 99%": cvar_99,
    }


def check_open_positions(
    portfolio: vbt.Portfolio, price_df_pd: pd.DataFrame, log
) -> List[Tuple[str, float]]:
    """Check which strategies have open positions at the end."""
    positions = portfolio.positions.values[-1]
    open_positions = []
    for strategy_name, position in zip(price_df_pd.columns, positions):
        if position != 0:
            open_positions.append((strategy_name, position))
            log(f"{strategy_name}: {position:.2f} units")
    return open_positions
