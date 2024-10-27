from typing import List
import vectorbt as vbt
import yfinance as yf
import polars as pl
import pandas as pd
from app.ema_cross.tools.generate_signals import generate_signals, Config

# Configuration for the strategy
config: Config = {
    'strategies': {
        'BTC_Strategy_1': {
            'symbol': 'BTC-USD',
            'short_window': 2,
            'long_window': 25,
            'stop_loss': None,
            'position_size': 0.5,
            'use_sma': True
        },
        'BTC_Strategy_2': {
            'symbol': 'BTC-USD',
            'short_window': 27,
            'long_window': 29,
            'stop_loss': None,
            'position_size': 0.5,
            'use_sma': True
        }
    },
    'start_date': '2020-01-01',
    'end_date': '2024-10-25',
    'init_cash': 1000,
    'fees': 0.001
}

# Get unique symbols from strategies
symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))

# Download historical data and convert to polars
data: pd.DataFrame = yf.download(symbols[0], start=config['start_date'], end=config['end_date'])
data_pl: pl.DataFrame = pl.from_pandas(data)
close_data: pl.Series = data_pl.select("Close").to_series()
close_data.index = data.index

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
print("\nPortfolio Statistics:")
print("===================")
print(portfolio.stats())

# Create visualization
fig = portfolio.plot(subplots=[
    'value',
    'drawdowns',
    'cum_returns',
    'cash_flow',
    'asset_value',
    'cash',
    'underwater',
    'gross_exposure',
    'net_exposure',
],
show_titles=True)

fig.update_layout(
    width=1200,
    height=10000,
    autosize=True
)

fig.show()
