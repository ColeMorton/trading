from typing import List, Dict
import vectorbt as vbt
import yfinance as yf
import polars as pl
import numpy as np
from config import config

# Get unique symbols from strategies
symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))

# Download historical data for all symbols
data_dict: Dict[str, pl.DataFrame] = {}
for symbol in symbols:
    # Download with yfinance and convert directly to polars
    pd_df = yf.download(symbol, start=config['start_date'], end=config['end_date'])
    pl_df = pl.from_pandas(pd_df.reset_index())
    pl_df = pl_df.with_columns(pl.col('Date').cast(pl.Datetime).alias('Date'))
    data_dict[symbol] = pl_df

# Find common date range using polars operations
common_dates = None
for df in data_dict.values():
    dates = df.get_column('Date').to_list()
    if common_dates is None:
        common_dates = set(dates)
    else:
        common_dates = common_dates.intersection(set(dates))
common_dates = sorted(list(common_dates))

# Reindex all dataframes to common dates
for symbol in data_dict:
    data_dict[symbol] = data_dict[symbol].filter(pl.col('Date').is_in(common_dates))

# Create price DataFrame for vectorbt (convert to pandas as required by vectorbt)
price_df = pl.DataFrame({'Date': common_dates})
for strategy_name, strategy in config['strategies'].items():
    close_prices = data_dict[strategy['symbol']].select(['Date', 'Close'])
    price_df = price_df.join(
        close_prices.rename({'Close': strategy_name}),
        on='Date',
        how='left'
    )
# Convert to pandas for vectorbt with Date as index
price_df_pd = price_df.to_pandas().set_index('Date')

# Generate signals for each strategy using vectorbt
entries = pl.DataFrame({'Date': common_dates})
exits = pl.DataFrame({'Date': common_dates})

for strategy_name, strategy in config['strategies'].items():
    # Calculate moving averages using vectorbt
    if strategy['use_sma']:
        fast_ma = vbt.MA.run(price_df_pd[strategy_name], window=strategy['short_window'], short_name='fast')
        slow_ma = vbt.MA.run(price_df_pd[strategy_name], window=strategy['long_window'], short_name='slow')
    else:
        fast_ma = vbt.MA.run(price_df_pd[strategy_name], window=strategy['short_window'], short_name='fast', ewm=True)
        slow_ma = vbt.MA.run(price_df_pd[strategy_name], window=strategy['long_window'], short_name='slow', ewm=True)
    
    # Generate crossover signals
    entries = entries.with_columns(
        pl.Series(name=strategy_name, values=fast_ma.ma_crossed_above(slow_ma).values)
    )
    
    # Calculate stop-loss exits
    price_series = price_df_pd[strategy_name]
    returns = price_series.pct_change()
    
    # Initialize arrays for tracking position and entry price
    position = np.zeros(len(price_series))
    entry_price = np.zeros(len(price_series))
    stop_loss_exits = np.zeros(len(price_series), dtype=bool)
    
    # Track positions and check for stop-loss
    for i in range(1, len(price_series)):
        if entries[strategy_name][i]:
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
    exits = exits.with_columns(
        pl.Series(name=strategy_name, values=ma_cross_exits.values | stop_loss_exits)
    )

# Convert signals to pandas for vectorbt
entries_pd = entries.to_pandas().set_index('Date')
exits_pd = exits.to_pandas().set_index('Date')

# Create size DataFrame (position sizes for each strategy)
sizes = pl.DataFrame({'Date': common_dates})
for strategy_name in price_df_pd.columns:
    sizes = sizes.with_columns(pl.lit(1.0).alias(strategy_name))
sizes_pd = sizes.to_pandas().set_index('Date')

# Run the portfolio simulation
portfolio = vbt.Portfolio.from_signals(
    close=price_df_pd,
    entries=entries_pd,
    exits=exits_pd,
    size=sizes_pd,
    init_cash=config['init_cash'],
    fees=config['fees'],
    freq='1D',
    group_by=True,
    cash_sharing=True
)

# Prepare benchmark data
benchmark_close = pl.DataFrame({'Date': common_dates})
for symbol in symbols:
    close_prices = data_dict[symbol].select(['Date', 'Close'])
    benchmark_close = benchmark_close.join(
        close_prices.rename({'Close': symbol}),
        on='Date',
        how='left'
    )
benchmark_close_pd = benchmark_close.to_pandas().set_index('Date')

# Create benchmark entries (always True after first row)
benchmark_entries = pl.DataFrame({'Date': common_dates})
for symbol in symbols:
    benchmark_entries = benchmark_entries.with_columns(
        pl.Series(name=symbol, values=[False] + [True] * (len(common_dates) - 1))
    )
benchmark_entries_pd = benchmark_entries.to_pandas().set_index('Date')

# Create benchmark position sizes (50/50 split)
benchmark_sizes = pl.DataFrame({'Date': common_dates})
for symbol in symbols:
    benchmark_sizes = benchmark_sizes.with_columns(pl.lit(0.5).alias(symbol))
benchmark_sizes_pd = benchmark_sizes.to_pandas().set_index('Date')

# Create benchmark portfolio
benchmark_portfolio = vbt.Portfolio.from_signals(
    close=benchmark_close_pd,
    entries=benchmark_entries_pd,
    size=benchmark_sizes_pd,
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
for strategy_name, position in zip(price_df_pd.columns, positions):
    if position != 0:
        print(f"{strategy_name}: {position:.2f} units")
