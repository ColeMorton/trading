import yfinance as yf
import pandas as pd
import numpy as np
from scipy.optimize import minimize
import matplotlib.pyplot as plt
from datetime import datetime

# start_date = '2019-11-01'
# end_date = '2020-02-01'

# start_date = '2019-11-01'
# end_date = '2020-11-01'

# start_date = '2023-09-01'
# end_date = '2023-12-01'

# start_date = '2010-01-01'
# end_date = '2024-09-20'

start_date = '2019-11-20'
end_date = '2024-09-20'

# start_date = '2023-09-20'
# end_date = '2024-09-20'

# start_date = '2024-03-20'
# end_date = '2024-09-20'

# start_date = '2024-05-20'
# end_date = '2024-09-20'

# ASSETS = ['SNX', 'ENPH', 'CHFGBP=X', 'BTC-USD', 'ON']

# ASSETS = ['BTC-USD', 'SPY']

ASSETS = ['QQQ', 'SPY']

# Download the data
data = yf.download(ASSETS, start=start_date, end=end_date)['Adj Close']

print(f'Start Date: {start_date} End Date: {end_date}')

# Display the first few rows of the data
# print(data.head())

# Calculate daily returns
returns = data.pct_change().dropna()

# Display the first few rows of the returns
# print(returns.head())

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

# Perform optimization
result = minimize(negative_sortino_ratio, init_guess, args=(mean_returns, returns), 
                  method='SLSQP', bounds=bounds, constraints=constraints)

# Get the optimal weights
optimal_weights = result.x

print(f"Optimal Weights: {optimal_weights}")

# Portfolio performance
optimal_return, optimal_std = portfolio_performance(optimal_weights, mean_returns, cov_matrix)

# Plot efficient frontier
def plot_efficient_frontier(mean_returns, cov_matrix, returns, num_portfolios=10000, risk_free_rate=0):
    results = np.zeros((3, num_portfolios))
    weights_record = []
    
    for i in range(num_portfolios):
        weights = np.random.random(len(mean_returns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_return, portfolio_std = portfolio_performance(weights, mean_returns, cov_matrix)
        dd = downside_deviation(np.dot(returns, weights))
        results[0, i] = portfolio_return
        results[1, i] = portfolio_std
        results[2, i] = (portfolio_return - risk_free_rate) / dd
    
    max_sortino_idx = np.argmax(results[2])
    sdp, rp = results[1, max_sortino_idx], results[0, max_sortino_idx]
    max_sortino_allocation = pd.DataFrame(weights_record[max_sortino_idx], index=mean_returns.index, columns=['allocation'])
    max_sortino_allocation.allocation = [round(i*100, 2) for i in max_sortino_allocation.allocation]
    
    plt.figure(figsize=(10, 7))
    plt.scatter(results[1, :], results[0, :], c=results[2, :], cmap='YlGnBu', marker='o')
    plt.scatter(sdp, rp, marker='*', color='r', s=200, label='Maximum Sortino ratio')
    plt.title('Efficient Frontier')
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Expected Returns')
    plt.colorbar(label='Sortino ratio')
    plt.legend(labelspacing=0.8)
    
    return max_sortino_allocation

max_sortino_allocation = plot_efficient_frontier(mean_returns, cov_matrix, returns)

print("Maximum Sortino Ratio Portfolio Allocation\n")
print(max_sortino_allocation)
plt.show()
