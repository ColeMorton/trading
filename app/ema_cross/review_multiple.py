from typing import List, Dict
import vectorbt as vbt
import yfinance as yf
import polars as pl
import pandas as pd
import numpy as np
from app.ema_cross.tools.generate_signals import generate_signals, Config

# Configuration for the strategy
config: Config = {
    'strategies': {
        'BTC_Strategy_1': {
            'symbol': 'BTC-USD',
            'short_window': 2,
            'long_window': 25,
            'stop_loss': 5.43,
            'position_size': 1,
            'use_sma': True
        },
        'BTC_Strategy_2': {
            'symbol': 'BTC-USD',
            'short_window': 27,
            'long_window': 29,
            'stop_loss': 9.11,
            'position_size': 1,
            'use_sma': True
        },
        'SOL_Strategy_1': {
            'symbol': 'SOL-USD',
            'short_window': 14,
            'long_window': 32,
            'stop_loss': None,
            'position_size': 1,
            'use_sma': True
        },
        'SOL_Strategy_2': {
            'symbol': 'SOL-USD',
            'short_window': 27,
            'long_window': 30,
            'stop_loss': None,
            'position_size': 1,
            'use_sma': True
        }
    },
    # 'start_date': '2020-04-10',  # Updated to SOL-USD's start date
    'start_date': '2014-10-27',  # Updated to SOL-USD's start date
    'end_date': '2024-10-27',
    'init_cash': 10000,
    'fees': 0.001
}

# Get unique symbols from strategies
symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))

# Download historical data for all symbols
data_dict: Dict[str, pd.DataFrame] = {}
for symbol in symbols:
    data_dict[symbol] = yf.download(symbol, start=config['start_date'], end=config['end_date'])

# Prepare benchmark data
benchmark_close = pd.DataFrame()
for symbol in symbols:
    benchmark_close[symbol] = data_dict[symbol]['Close']

# Create benchmark entries (always True after first row)
benchmark_entries = pd.DataFrame(index=benchmark_close.index)
for symbol in symbols:
    entries = np.full(len(benchmark_close), True)
    entries[0] = False  # First entry is False to allow for position sizing
    benchmark_entries[symbol] = entries

# Create benchmark position sizes (50/50 split)
benchmark_sizes = pd.DataFrame(index=benchmark_close.index)
for symbol in symbols:
    benchmark_sizes[symbol] = 0.5

# Create benchmark portfolio
benchmark_portfolio = vbt.Portfolio.from_signals(
    close=benchmark_close,
    entries=benchmark_entries,
    size=benchmark_sizes,
    init_cash=config['init_cash'],
    fees=config['fees'],
    freq='1D',
    group_by=True,
    cash_sharing=True
)

# Convert strategy data to polars and prepare for signals
data_pl: pl.DataFrame = pl.from_pandas(data_dict[symbols[0]])
close_data: pl.Series = data_pl.select("Close").to_series()
close_data.index = data_dict[symbols[0]].index

# Create position sizing DataFrame with strategy names as columns
size_pl: pl.DataFrame = pl.DataFrame({"Date": close_data.index})
for strategy_name, strategy in config['strategies'].items():
    size_pl = size_pl.with_columns(pl.Series(name=strategy_name, values=[strategy['position_size']] * len(close_data)))
size_pd: pd.DataFrame = size_pl.to_pandas().set_index("Date")

# Generate signals using the utility function
entries, exits = generate_signals(close_data, config)

# Prepare price data for portfolio
price_pl: pl.DataFrame = pl.DataFrame({"Date": close_data.index})
for strategy_name in config['strategies'].keys():
    price_pl = price_pl.with_columns(pl.Series(name=strategy_name, values=close_data))
price_pd: pd.DataFrame = price_pl.to_pandas().set_index("Date")

# Run the portfolio simulation
portfolio: vbt.Portfolio = vbt.Portfolio.from_signals(
    price_pd,  # Use prepared price data
    entries,
    exits,
    size=size_pd,
    init_cash=config['init_cash'],
    fees=config['fees'],
    freq='1D',
    group_by=True,
    cash_sharing=True
)

# Print portfolio statistics
print("\nStrategy Portfolio Statistics:")
print("===================")
print(portfolio.stats())

# Calculate and print VaR and CVaR at 99%
returns = portfolio.returns().values
# Calculate VaR 99%
var_99 = np.percentile(returns, 1)  # 1st percentile for 99% VaR
# Calculate CVaR 99%
cvar_99 = returns[returns <= var_99].mean()

print("\nRisk Metrics:")
print("===================")
print(f"VaR 99%: {var_99:.2%}")
print(f"CVaR 99%: {cvar_99:.2%}")

print("\nBenchmark Portfolio Statistics (50/50 BTC-USD/SOL-USD):")
print("===================")
print(benchmark_portfolio.stats())

# Create comparison plots
# portfolio.plot_value().show()  # Plot strategy portfolio value
benchmark_portfolio.plot_value().show()  # Plot benchmark portfolio value

# Plot additional metrics for strategy portfolio
portfolio.plot([
    'value',
    'cum_returns',
    'drawdowns',
    'underwater',
    'net_exposure',
],
show_titles=True).show()
