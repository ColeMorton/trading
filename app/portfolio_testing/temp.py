import numpy as np
import pandas as pd
import yfinance as yf
import warnings
import matplotlib.pyplot as plt
import riskfolio as rp

warnings.filterwarnings("ignore")
pd.options.display.float_format = '{:.4%}'.format

# Date range
start_date = '2020-05-02'
end_date = '2024-11-03'

# start_date = '2020-01-01'
# end_date = '2021-01-01'

# start_date = '2020-01-01'
# end_date = '2024-10-24'

# start_date = '2023-10-24'
# end_date = '2024-10-24'

# start_date = '2021-01-01'
# end_date = '2022-01-01'

# Tickers of assets
# assets = ['BTC-USD', 'SOL-USD', 'SPY', 'QQQ', 'MSTR', 'WULF']
assets = ['BTC-USD', 'MSTR']
# assets = ['BTC-USD', 'SOL-USD']
# assets = ['BTC-USD', 'SOL-USD', 'MSTR']
assets.sort()

# Downloading data
data = yf.download(assets, start = start_date, end = end_date)
data = data.loc[:,('Adj Close', slice(None))]
data.columns = assets

Y = data[assets].pct_change().dropna()

# Building the portfolio object
port = rp.Portfolio(returns=Y)

# Calculating optimal portfolio

# Select method and estimate input parameters:

method_mu='hist' # Method to estimate expected returns based on historical data.
method_cov='hist' # Method to estimate covariance matrix based on historical data.

port.assets_stats(method_mu=method_mu, method_cov=method_cov)

# Risk Measures available:
#
# 'MV': Standard Deviation.
# 'MAD': Mean Absolute Deviation.
# 'MSV': Semi Standard Deviation.
# 'FLPM': First Lower Partial Moment (Omega Ratio).
# 'SLPM': Second Lower Partial Moment (Sortino Ratio).
# 'CVaR': Conditional Value at Risk.
# 'EVaR': Entropic Value at Risk.
# 'WR': Worst Realization (Minimax)
# 'MDD': Maximum Drawdown of uncompounded cumulative returns (Calmar Ratio).
# 'ADD': Average Drawdown of uncompounded cumulative returns.
# 'CDaR': Conditional Drawdown at Risk of uncompounded cumulative returns.
# 'EDaR': Entropic Drawdown at Risk of uncompounded cumulative returns.
# 'UCI': Ulcer Index of uncompounded cumulative returns.

rms = ['MV', 'MAD', 'MSV', 'FLPM', 'SLPM', 'CVaR',
       'EVaR', 'WR', 'MDD', 'ADD', 'CDaR', 'UCI', 'EDaR']

# Estimate optimal portfolio:

model='Classic' # Could be Classic (historical), BL (Black Litterman) or FM (Factor Model)
rm = 'CVaR' # Risk measure used, this time will be variance
obj = 'Sharpe' # Objective function, could be MinRisk, MaxRet, Utility or Sharpe
hist = True # Use historical scenarios for risk measures that depend on scenarios
rf = 0 # Risk free rate
l = 0 # Risk aversion factor, only useful when obj is 'Utility'

w = port.optimization(model=model, rm=rm, obj=obj, rf=rf, l=l, hist=hist)

ax = rp.plot_pie(w=w, title='Sortino Mean Variance', others=0.05, nrow=25, cmap = "tab20",
                 height=6, width=10, ax=None)

# points = 50 # Number of points of the frontier

# frontier = port.efficient_frontier(model=model, rm=rm, points=points, rf=rf, hist=hist)

# label = 'Max Risk Adjusted Return Portfolio' # Title of point
# mu = port.mu # Expected returns
# cov = port.cov # Covariance matrix
# returns = port.returns # Returns of the assets

# ax = rp.plot_frontier(w_frontier=frontier, mu=mu, cov=cov, returns=returns, rm=rm,
#                       rf=rf, alpha=0.05, cmap='viridis', w=w, label=label,
#                       marker='*', s=16, c='r', height=6, width=10, ax=None)

plt.show()