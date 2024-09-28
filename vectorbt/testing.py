import vectorbt as vbt
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go

# Constants for order quantities
EMA_ENTRY_QUANTITY = 10
MACD_ENTRY_QUANTITY = 4

# # Download historical data for a specific stock (you can replace 'AAPL' with any ticker)
ticker = 'BTC-USD'
data = yf.download(ticker, start='2010-01-01', end='2024-09-28', progress=False)

# Strategy 1: EMA 8/21 Cross Strategy
# Use vectorbt's MA indicator with exponential weighting (ewm=True) for EMA
ema_fast = vbt.MA.run(data['Close'], window=11, ewm=True).ma
ema_slow = vbt.MA.run(data['Close'], window=17, ewm=True).ma

# Entry and Exit Conditions for EMA Strategy
entries_ema = ema_fast > ema_slow
exits_ema = ema_fast < ema_slow

# Strategy 2: MACD 12/26/9 vs MACD 12/24/13 Cross Strategy
# MACD 12, 26, 9 (Standard MACD)
macd = vbt.MACD.run(data['Close'], fast_window=14, slow_window=23, signal_window=13)
entries_macd = macd.macd_crossed_above(macd.signal)
exits_macd = macd.macd_crossed_below(macd.signal)

# Create a size array based on the entry quantities for each strategy
# For long-only strategies, we only specify the position sizes for entries (no negative sizes for exits)
size = pd.Series(0, index=data.index)
size = size.where(~entries_ema, EMA_ENTRY_QUANTITY)  # Apply EMA entry quantity
size = size.where(~entries_macd, MACD_ENTRY_QUANTITY)  # Apply MACD 12/26/9 entry quantity

# Portfolio simulation with proper size handling for entries and exits (no negative sizes)
portfolio = vbt.Portfolio.from_signals(
    close=data['Close'],
    # entries=entries_ema | entries_macd,  # Combined entry signals
    # exits=exits_ema | exits_macd,          # Combined exit signals
    entries=entries_macd,  # Combined entry signals
    exits=exits_macd,          # Combined exit signals
    size=size,            # Use the size array for entries only
    direction='longonly',  # Only take long positions
    fees=0.005
)

# Plotting the portfolio
# portfolio.plot(subplots=[
#     ('orders', {'plot_type': 'markers'}),
#     ('trades', {'plot_type': 'markers'})
# ], plot_type='candlestick', title='Combined EMA and MACD Crossover Strategy with Individual Quantities').show()

# Plotting the portfolio
# portfolio.plot().show()

# Analyze and plot the results
# print(portfolio.stats())
# print(portfolio.orders.records_readable)
# portfolio.plot(
#     marker_settings={
#         'buy': {'marker': 'triangle-up', 'color': 'green', 'size': 10},
#         'sell': {'marker': 'triangle-down', 'color': 'red', 'size': 10}
#     },
#     # subplots=[
#     #     'orders',    # Show buy and sell orders as a subplot
#     #     'cash'
#     # ]      
#     ).show()
# print(portfolio.available_subplots())

# fig = go.Figure()

# # Add equity curve (portfolio value)
# fig.add_trace(go.Scatter(x=portfolio.value().index, 
#                          y=portfolio.value().values,
#                          mode='lines', 
#                          name='Equity Curve'))

# # Show the plot
# fig.show()

print(portfolio.plots())

# portfolio.plot(
#     subplots=[
#         'equity',
#         'trades',
#         'drawdowns'
#     ],
#     layout=dict(
#         title='Portfolio Performance',
#         xaxis_title='Time',
#         yaxis_title='Equity Value',
#         height=800,
#         width=1000
#     )
# )

print(portfolio.subplots)

portfolio.plot(
    subplots=[
        'value',
        'drawdowns',
        'cum_returns',
        'assets',
        'orders',
        'trades',
        'trade_pnl',
        'asset_flow',
        'cash_flow',
        'asset_value',
        'cash',
        'underwater',
        'gross_exposure',
        'net_exposure',
    ],  # Replace with valid subplots
    # layout_kwargs=dict(
    #     title='Portfolio Performance',
    #     xaxis_title='Time',
    #     yaxis_title='Value',
    #     height=800,
    #     width=1000
    # ),
    show_titles=True
).show()