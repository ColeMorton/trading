import numpy as np
import vectorbt as vbt

# Change the frequency to 1 hour
FREQ = "1D"
# FREQ = '1H'

# Add constant to determine whether to use SMA or EMA
USE_SMA = False  # Set to True to use SMAs, False to use EMAs

symbols = ["BTC-USD", "WLD-USD", "SOL-USD"]
price = vbt.YFData.download(symbols, missing_index="drop").get("Close")

print(price)

windows = np.arange(2, 101)
# Use SMA if USE_SMA is True, otherwise use EMA
if USE_SMA:
    fast_ma, slow_ma = vbt.MA.run_combs(
        price, window=windows, r=2, short_names=["fast", "slow"]
    )
else:
    fast_ma, slow_ma = vbt.MA.run_combs(
        price, window=windows, r=2, short_names=["fast", "slow"], ewm=True
    )
entries = fast_ma.ma_crossed_above(slow_ma)
exits = fast_ma.ma_crossed_below(slow_ma)

pf_kwargs = dict(size=np.inf, fees=0.001, freq=FREQ)
pf = vbt.Portfolio.from_signals(price, entries, exits, **pf_kwargs)

fig = pf.total_return().vbt.heatmap(
    x_level="fast_window",
    y_level="slow_window",
    slider_level="symbol",
    symmetric=True,
    trace_kwargs=dict(colorbar=dict(title="Total return", tickformat="%")),
)
fig.show()

# price.vbt.plot().show_svg()

# print(pf[(11, 17, 'BTC-USD')].stats())
# pf[(11, 17, 'BTC-USD')].plot().show()

# print(pf[(11, 17, 'BTC-USD')])
# print(pf[(27, 28, 'BTC-USD')].stats())
# pf[(27, 28, 'BTC-USD')].plot().show()
