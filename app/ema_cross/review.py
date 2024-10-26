from app.tools.get_config import get_config
from app.utils import get_data, calculate_ma_and_signals, backtest_strategy
import polars as pl
import pandas as pd

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'BTC-USD',
    "USE_SYNTHETIC": True,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 55
}

config = get_config(CONFIG)

data = get_data(config)

data = calculate_ma_and_signals(data, config["SHORT_WINDOW"], config["LONG_WINDOW"], config)

portfolio = backtest_strategy(data, CONFIG)

print(portfolio.stats())

# Extract value series and convert to DataFrame
value_series = portfolio.value()
print(portfolio.value())
initial_value = value_series[0]
equity_curve = pl.DataFrame({
    'Date': value_series.index,
    'Close': value_series.values / initial_value
})

# Export to CSV
equity_curve.write_csv('csv/ma_cross/equity_curve/BTC.csv')

# fig = portfolio.plot(subplots=[
#     'value',
#     'drawdowns',
#     'cum_returns',
#     'assets',
#     'orders',
#     'trades',
#     'trade_pnl',
#     'asset_flow',
#     'cash_flow',
#     'asset_value',
#     'cash',
#     'underwater',
#     'gross_exposure',
#     'net_exposure',
# ],
# show_titles=True)

# fig.update_layout(
#     width=1600,
#     height=10000,
#     autosize=True
# )

# fig.show()
