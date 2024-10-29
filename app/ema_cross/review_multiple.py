from typing import List, Dict, TypedDict, NotRequired

class StrategyConfig(TypedDict):
    symbol: str
    short_window: int
    long_window: int
    stop_loss: float
    position_size: float
    use_sma: bool

class Config(TypedDict):
    strategies: Dict[str, StrategyConfig]
    start_date: str
    end_date: str
    init_cash: float
    fees: float

import vectorbt as vbt
import yfinance as yf
import polars as pl
import pandas as pd
import numpy as np

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
            'stop_loss': 12.5,
            'position_size': 1,
            'use_sma': True
        },
        'SOL_Strategy_2': {
            'symbol': 'SOL-USD',
            'short_window': 27,
            'long_window': 30,
            'stop_loss': 8.8,
            'position_size': 1,
            'use_sma': True
        }
    },
    'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    'end_date': '2024-10-28',
    'init_cash': 10000,
    'fees': 0.001
}

# Get unique symbols from strategies
symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))

# Download historical data for all symbols
data_dict: Dict[str, pd.DataFrame] = {}
for symbol in symbols:
    # Download with yfinance (returns pandas DataFrame)
    pd_df = yf.download(symbol, start=config['start_date'], end=config['end_date'])
    # Ensure index is datetime
    pd_df.index = pd.to_datetime(pd_df.index)
    data_dict[symbol] = pd_df

# Find common date range
common_dates = None
for df in data_dict.values():
    if common_dates is None:
        common_dates = set(df.index)
    else:
        common_dates = common_dates.intersection(set(df.index))
common_dates = sorted(list(common_dates))

# Reindex all dataframes to common dates
for symbol in data_dict:
    data_dict[symbol] = data_dict[symbol].reindex(index=common_dates)

# Create price DataFrame for each strategy
price_df = pd.DataFrame(index=common_dates)
for strategy_name, strategy in config['strategies'].items():
    price_df[strategy_name] = data_dict[strategy['symbol']]['Close']

# Generate signals for each strategy using vectorbt
entries = pd.DataFrame(False, index=common_dates, columns=price_df.columns)
exits = pd.DataFrame(False, index=common_dates, columns=price_df.columns)

for strategy_name, strategy in config['strategies'].items():
    # Calculate moving averages using vectorbt
    if strategy['use_sma']:
        fast_ma = vbt.MA.run(price_df[strategy_name], window=strategy['short_window'], short_name='fast')
        slow_ma = vbt.MA.run(price_df[strategy_name], window=strategy['long_window'], short_name='slow')
    else:
        fast_ma = vbt.MA.run(price_df[strategy_name], window=strategy['short_window'], short_name='fast', ewm=True)
        slow_ma = vbt.MA.run(price_df[strategy_name], window=strategy['long_window'], short_name='slow', ewm=True)
    
    # Generate crossover signals
    entries[strategy_name] = fast_ma.ma_crossed_above(slow_ma)
    
    # Calculate stop-loss exits
    price_series = price_df[strategy_name]
    returns = price_series.pct_change()
    
    # Initialize arrays for tracking position and entry price
    position = np.zeros(len(price_series))
    entry_price = np.zeros(len(price_series))
    stop_loss_exits = np.zeros(len(price_series), dtype=bool)
    
    # Track positions and check for stop-loss
    for i in range(1, len(price_series)):
        if entries.iloc[i, entries.columns.get_loc(strategy_name)]:
            position[i] = 1
            entry_price[i] = price_series.iloc[i]
        elif i > 0:
            position[i] = position[i-1]
            entry_price[i] = entry_price[i-1] if position[i] == 1 else 0
            
        if position[i] == 1 and entry_price[i] > 0:
            # Calculate drawdown from entry
            current_drawdown = (price_series.iloc[i] - entry_price[i]) / entry_price[i] * 100
            if current_drawdown <= -strategy['stop_loss']:
                stop_loss_exits[i] = True
                position[i] = 0
                entry_price[i] = 0
    
    # Combine MA crossover exits with stop-loss exits
    ma_cross_exits = fast_ma.ma_crossed_below(slow_ma)
    exits[strategy_name] = ma_cross_exits | pd.Series(stop_loss_exits, index=price_series.index)

# Create size DataFrame (position sizes for each strategy)
sizes = pd.DataFrame(1.0, index=common_dates, columns=price_df.columns)

# Run the portfolio simulation
portfolio = vbt.Portfolio.from_signals(
    close=price_df,
    entries=entries,
    exits=exits,
    size=sizes,
    init_cash=config['init_cash'],
    fees=config['fees'],
    freq='1D',
    group_by=True,
    cash_sharing=True
)

# Prepare benchmark data
benchmark_close = pd.DataFrame(index=common_dates)
for symbol in symbols:
    benchmark_close[symbol] = data_dict[symbol]['Close']

# Create benchmark entries (always True after first row)
benchmark_entries = pd.DataFrame(False, index=common_dates, columns=symbols)
benchmark_entries.iloc[1:] = True

# Create benchmark position sizes (50/50 split)
benchmark_sizes = pd.DataFrame(0.5, index=common_dates, columns=symbols)

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

# Create comparison plots
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

# Check which strategies have open positions at the end
print("\nStrategies with Open Positions:")
print("===================")
positions = portfolio.positions.values[-1]  # Get positions at the last timestamp
for strategy_name, position in zip(price_df.columns, positions):
    if position != 0:
        print(f"{strategy_name}: {position:.2f} units")
