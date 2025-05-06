import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt

# Set date range and assets
# start_date = '2020-06-02'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2023-10-24'
# end_date = '2024-11-02'

start_date = '2020-09-01'
end_date = '2025-05-05'

# ASSETS = ['BTC-USD', 'SPY']

# ASSETS = ['BTC-USD', 'SOL-USD', 'MSTR']

# ASSETS = ['BTC-USD', 'QQQ']

# ASSETS = ['CRWD', 'MCO', 'INTU', 'COST', 'TSLA', 'GOOGL', 'EQT']

ASSETS = ['TRX-USD', 'PENDLE-USD', 'AVAX-USD', 'RUNE-USD', 'SOL-USD']

# ASSETS = ['BTC-USD', 'MSTR', 'SOL-USD']

# ASSETS = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD', 'MSTR']

# ASSETS = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD']

# ASSETS = ['BTC-USD', 'SOL-USD', 'MSTR']

# ASSETS = ['SPY', 'QQQ']

# ASSETS = ['BTC-USD', 'MSTR']

# Download the data
# data = yf.download(ASSETS, start=start_date, end=end_date)['Close']
data = yf.download(ASSETS, period="max")['Close']
print(f'Start Date: {start_date} End Date: {end_date}')

# Calculate daily returns
returns = data.pct_change().dropna()

def portfolio_performance(weights, mean_returns, cov_matrix):
    returns = np.dot(weights, mean_returns)
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return returns, std

def downside_deviation(returns, target=0):
    downside_diff = np.minimum(0, returns - target)
    return np.sqrt((downside_diff ** 2).mean())

def negative_sortino_ratio(weights, mean_returns, returns, target=0, risk_free_rate=0):
    p_return, _ = portfolio_performance(weights, mean_returns, cov_matrix)
    dd = downside_deviation(np.dot(returns, weights), target)
    return -(p_return - risk_free_rate) / dd

def negative_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate=0):
    p_return, p_std = portfolio_performance(weights, mean_returns, cov_matrix)
    return -(p_return - risk_free_rate) / p_std

def max_drawdown(returns):
    # Convert the NumPy array to a Pandas Series to use cummax()
    cumulative_returns = pd.Series((1 + returns).cumprod())
    peak = cumulative_returns.cummax()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def calmar_ratio(weights, mean_returns, returns):
    p_return, _ = portfolio_performance(weights, mean_returns, cov_matrix)
    portfolio_returns = np.dot(returns, weights)
    mdd = max_drawdown(portfolio_returns)
    return p_return / abs(mdd)

# Calculate mean returns and covariance matrix
mean_returns = returns.mean()
cov_matrix = returns.cov()

# Number of assets
num_assets = len(mean_returns)

# Initial guess (equal weights)
init_guess = num_assets * [1. / num_assets]

# Constraints (weights must sum to 1)
constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

# Bounds (weights must be between 0 and 1)
bounds = tuple((0, 1) for asset in range(num_assets))

# Perform optimization for Sortino Ratio
result_sortino = minimize(negative_sortino_ratio, init_guess, args=(mean_returns, returns), 
                          method='SLSQP', bounds=bounds, constraints=constraints)

# Get the optimal weights for Sortino Ratio
optimal_weights_sortino = result_sortino.x
optimal_return_sortino, optimal_std_sortino = portfolio_performance(optimal_weights_sortino, mean_returns, cov_matrix)
optimal_sortino = -(result_sortino.fun)  # Since we minimized the negative sortino ratio

print(f"Optimal Sortino Weights: {optimal_weights_sortino}")
print(f"Optimal Sortino Portfolio Return: {optimal_return_sortino}")
print(f"Optimal Sortino Portfolio Volatility: {optimal_std_sortino}")
print(f"Optimal Sortino Ratio: {optimal_sortino}")

# Perform optimization for Sharpe Ratio
result_sharpe = minimize(negative_sharpe_ratio, init_guess, args=(mean_returns, cov_matrix), 
                         method='SLSQP', bounds=bounds, constraints=constraints)

# Get the optimal weights for Sharpe Ratio
optimal_weights_sharpe = result_sharpe.x
optimal_return_sharpe, optimal_std_sharpe = portfolio_performance(optimal_weights_sharpe, mean_returns, cov_matrix)
optimal_sharpe = -(result_sharpe.fun)  # Since we minimized the negative sharpe ratio

print(f"\nOptimal Sharpe Weights: {optimal_weights_sharpe}")
print(f"Optimal Sharpe Portfolio Return: {optimal_return_sharpe}")
print(f"Optimal Sharpe Portfolio Volatility: {optimal_std_sharpe}")
print(f"Optimal Sharpe Ratio: {optimal_sharpe}")

# Calculate Sharpe and Calmar ratios for optimal weights
optimal_calmar_sortino = calmar_ratio(optimal_weights_sortino, mean_returns, returns)
optimal_calmar_sharpe = calmar_ratio(optimal_weights_sharpe, mean_returns, returns)

print(f"Optimal Sortino Calmar Ratio: {optimal_calmar_sortino}")
print(f"Optimal Sharpe Calmar Ratio: {optimal_calmar_sharpe}")

# Plot efficient frontier
def plot_efficient_frontier(mean_returns, cov_matrix, returns, num_portfolios=10000, risk_free_rate=0):
    results = np.zeros((4, num_portfolios))  # Adding Sharpe ratio to results array
    weights_record = []

    for i in range(num_portfolios):
        weights = np.random.random(len(mean_returns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_return, portfolio_std = portfolio_performance(weights, mean_returns, cov_matrix)
        dd = downside_deviation(np.dot(returns, weights))
        results[0, i] = portfolio_return
        results[1, i] = portfolio_std
        results[2, i] = (portfolio_return - risk_free_rate) / dd  # Sortino ratio
        results[3, i] = (portfolio_return - risk_free_rate) / portfolio_std  # Sharpe ratio

    max_sortino_idx = np.argmax(results[2])
    max_sharpe_idx = np.argmax(results[3])

    sdp_sortino, rp_sortino = results[1, max_sortino_idx], results[0, max_sortino_idx]
    sdp_sharpe, rp_sharpe = results[1, max_sharpe_idx], results[0, max_sharpe_idx]

    max_sortino_allocation = pd.DataFrame(weights_record[max_sortino_idx], index=mean_returns.index, columns=['allocation'])
    max_sortino_allocation.allocation = [round(i*100, 2) for i in max_sortino_allocation.allocation]

    plt.figure(figsize=(10, 7))
    plt.scatter(results[1, :], results[0, :], c=results[2, :], cmap='YlGnBu', marker='o')
    plt.scatter(sdp_sortino, rp_sortino, marker='*', color='r', s=200, label='Maximum Sortino ratio')
    plt.scatter(sdp_sharpe, rp_sharpe, marker='*', color='b', s=200, label='Maximum Sharpe ratio')
    plt.title('Efficient Frontier with Sharpe and Sortino Ratios')
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Expected Returns')
    plt.colorbar(label='Sortino ratio')
    plt.legend(labelspacing=0.8)

    return max_sortino_allocation

max_sortino_allocation = plot_efficient_frontier(mean_returns, cov_matrix, returns)

print("\nMaximum Sortino Ratio Portfolio Allocation\n")
print(max_sortino_allocation)
plt.show()
