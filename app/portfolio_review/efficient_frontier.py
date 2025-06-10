import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from scipy.optimize import minimize

# Set date range and assets
# start_date = '2020-06-02'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2023-10-24'
# end_date = '2024-11-02'

start_date = "2020-06-02"
end_date = "2025-06-02"

HALF_RULE = True

# ASSETS = ['BTC-USD', 'SPY']

# ASSETS = ['BTC-USD', 'MSTR']

# ASSETS = ['QQQ', 'MSTR']

# ASSETS = ['PENDLE-USD', 'SUI20947-USD']

ASSETS = ["CMG", "ETH-USD", "NVDA", "AIZ", "COIN", "USB", "NBIX", "PLTR"]

# ASSETS = ['TRX-USD', 'FET-USD', 'AVAX-USD', 'SOL-USD']

# ASSETS = ['BTC-USD', 'MSTR', 'SOL-USD']

# ASSETS = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD', 'MSTR']

# ASSETS = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD']

# ASSETS = ["PLTR", "COIN"]

# ASSETS = ['SPY', 'QQQ']

# ASSETS = ['BTC-USD', 'MSTR']

# Download the data
# data = yf.download(ASSETS, start=start_date, end=end_date)['Close']
data = yf.download(ASSETS, period="max")["Close"]
print(f"Start Date: {start_date} End Date: {end_date}")

# Calculate daily returns
returns = data.pct_change().dropna()


def portfolio_performance(weights, mean_returns, cov_matrix):
    returns = np.dot(weights, mean_returns)
    std = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
    return returns, std


def downside_deviation(returns, target=0):
    downside_diff = np.minimum(0, returns - target)
    return np.sqrt((downside_diff**2).mean())


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
init_guess = num_assets * [1.0 / num_assets]

# Add a small random perturbation for Sharpe optimization to ensure
# different starting point
np.random.seed(42)  # Set seed for reproducibility
sharpe_perturbation = np.random.normal(0, 0.01, num_assets)
init_guess_sharpe = np.clip(init_guess + sharpe_perturbation, 0, 1)
# Normalize to ensure sum is 1
init_guess_sharpe = init_guess_sharpe / np.sum(init_guess_sharpe)

# Constraints (weights must sum to 1)
constraints = {"type": "eq", "fun": lambda x: np.sum(x) - 1}

# Bounds (weights must be between 0 and 1)
bounds = tuple((0, 1) for asset in range(num_assets))

# Perform optimization for Sortino Ratio
result_sortino = minimize(
    negative_sortino_ratio,
    init_guess,
    args=(mean_returns, returns),
    method="SLSQP",
    bounds=bounds,
    constraints=constraints,
)

# Get the optimal weights for Sortino Ratio
optimal_weights_sortino = result_sortino.x
optimal_return_sortino, optimal_std_sortino = portfolio_performance(
    optimal_weights_sortino, mean_returns, cov_matrix
)
optimal_sortino = -(result_sortino.fun)  # Since we minimized the negative sortino ratio

print(f"Optimal Sortino Weights: {optimal_weights_sortino}")
print(f"Optimal Sortino Portfolio Return: {optimal_return_sortino}")
print(f"Optimal Sortino Portfolio Volatility: {optimal_std_sortino}")
print(f"Optimal Sortino Ratio: {optimal_sortino}")

# Perform optimization for Sharpe Ratio
result_sharpe = minimize(
    negative_sharpe_ratio,
    init_guess_sharpe,
    args=(mean_returns, cov_matrix),
    method="SLSQP",
    bounds=bounds,
    constraints=constraints,
)

# Get the optimal weights for Sharpe Ratio
optimal_weights_sharpe = result_sharpe.x
optimal_return_sharpe, optimal_std_sharpe = portfolio_performance(
    optimal_weights_sharpe, mean_returns, cov_matrix
)
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


def enforce_half_rule_and_normalize(allocations):
    """
    Enforce the rule that the lowest value must be exactly half the highest value
    while preserving the relative ratios between allocations.
    Then normalize to 100%.
    """
    # Find min and max values
    min_ticker = min(allocations, key=allocations.get)
    max_ticker = max(allocations, key=allocations.get)
    min_value = allocations[min_ticker]
    max_value = allocations[max_ticker]

    print(f"Original min: {min_ticker} = {min_value}")
    print(f"Original max: {max_ticker} = {max_value}")
    print(f"Current ratio of min/max: {min_value/max_value}")

    # To preserve ratios between allocations, we add a constant 'c' where:
    # (min_value + c) / (max_value + c) = 0.5
    # Solving: c = max_value - 2*min_value

    c = max_value - 2 * min_value

    # Apply transformation to all values
    adjusted = {ticker: value + c for ticker, value in allocations.items()}

    # Verify the ratio
    new_min = min(adjusted.values())
    new_max = max(adjusted.values())
    new_ratio = new_min / new_max

    print(f"Adjusted by adding constant: {c}")
    print(f"After adjustment, min/max ratio: {new_ratio}")

    # Normalize to sum to 100%
    total = sum(adjusted.values())
    normalized = {ticker: (value / total) * 100 for ticker, value in adjusted.items()}

    # Round to 2 decimal places but ensure sum equals 100%
    # First round down for all to avoid overshooting
    rounded = {ticker: int(value * 100) / 100 for ticker, value in normalized.items()}
    leftover = 100 - sum(rounded.values())

    # Distribute the leftover across tickers in order of fractional parts
    fractional_parts = {
        ticker: value - rounded[ticker] for ticker, value in normalized.items()
    }
    ordered_tickers = sorted(
        fractional_parts.keys(), key=fractional_parts.get, reverse=True
    )

    leftover_pennies = round(leftover * 100)
    for i in range(leftover_pennies):
        ticker = ordered_tickers[i % len(ordered_tickers)]
        rounded[ticker] += 0.01

    # Ensure final sum is exactly 100
    final_sum = sum(rounded.values())
    if abs(final_sum - 100.0) > 0.001:
        diff = 100.0 - final_sum
        # Add to the largest allocation to minimize impact
        max_ticker = max(rounded, key=rounded.get)
        rounded[max_ticker] = round(rounded[max_ticker] + diff, 2)

    return rounded


# Plot efficient frontier
def plot_efficient_frontier(
    mean_returns, cov_matrix, returns, num_portfolios=50000, risk_free_rate=0
):
    """
    Generate and plot the efficient frontier using a combination of:
    1. Random portfolios
    2. Portfolios along the efficient frontier
    3. The optimized Sharpe and Sortino portfolios
    """
    # Set seed for reproducibility
    np.random.seed(101)

    # Total number of portfolios to generate
    total_portfolios = num_portfolios

    # Allocate space for results
    results = np.zeros((4, total_portfolios))
    weights_record = []

    # Generate random portfolios for the first part
    for i in range(int(total_portfolios * 0.7)):  # 70% random portfolios
        weights = np.random.random(len(mean_returns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_return, portfolio_std = portfolio_performance(
            weights, mean_returns, cov_matrix
        )
        dd = downside_deviation(np.dot(returns, weights))
        results[0, i] = portfolio_return
        results[1, i] = portfolio_std
        results[2, i] = (portfolio_return - risk_free_rate) / dd  # Sortino ratio
        results[3, i] = (
            portfolio_return - risk_free_rate
        ) / portfolio_std  # Sharpe ratio

    # Generate portfolios that are combinations of the optimized portfolios
    # This ensures we include points along the efficient frontier
    remaining = total_portfolios - int(total_portfolios * 0.7)

    # Include the optimized portfolios themselves
    weights_record.append(optimal_weights_sharpe)
    portfolio_return, portfolio_std = portfolio_performance(
        optimal_weights_sharpe, mean_returns, cov_matrix
    )
    dd = downside_deviation(np.dot(returns, optimal_weights_sharpe))
    idx = int(total_portfolios * 0.7)
    results[0, idx] = portfolio_return
    results[1, idx] = portfolio_std
    results[2, idx] = (portfolio_return - risk_free_rate) / dd
    results[3, idx] = (portfolio_return - risk_free_rate) / portfolio_std

    weights_record.append(optimal_weights_sortino)
    portfolio_return, portfolio_std = portfolio_performance(
        optimal_weights_sortino, mean_returns, cov_matrix
    )
    dd = downside_deviation(np.dot(returns, optimal_weights_sortino))
    idx = int(total_portfolios * 0.7) + 1
    results[0, idx] = portfolio_return
    results[1, idx] = portfolio_std
    results[2, idx] = (portfolio_return - risk_free_rate) / dd
    results[3, idx] = (portfolio_return - risk_free_rate) / portfolio_std

    # Generate portfolios along the efficient frontier by taking weighted combinations
    # of the Sharpe and Sortino optimal portfolios
    for i in range(remaining - 2):
        # Create weighted combinations
        t = (i + 1) / (remaining - 1)  # Weight parameter from 0 to 1
        weights = t * optimal_weights_sharpe + (1 - t) * optimal_weights_sortino
        weights /= np.sum(weights)  # Ensure weights sum to 1

        weights_record.append(weights)
        portfolio_return, portfolio_std = portfolio_performance(
            weights, mean_returns, cov_matrix
        )
        dd = downside_deviation(np.dot(returns, weights))

        idx = int(total_portfolios * 0.7) + 2 + i
        results[0, idx] = portfolio_return
        results[1, idx] = portfolio_std
        results[2, idx] = (portfolio_return - risk_free_rate) / dd
        results[3, idx] = (portfolio_return - risk_free_rate) / portfolio_std

    # Find the maximum Sharpe and Sortino portfolios from our generated set
    max_sortino_idx = np.argmax(results[2])
    max_sharpe_idx = np.argmax(results[3])

    sdp_sortino, rp_sortino = results[1, max_sortino_idx], results[0, max_sortino_idx]
    sdp_sharpe, rp_sharpe = results[1, max_sharpe_idx], results[0, max_sharpe_idx]

    # Create the plot
    plt.figure(figsize=(10, 7))

    # Plot all portfolios
    plt.scatter(
        results[1, :],
        results[0, :],
        c=results[2, :],
        cmap="YlGnBu",
        marker="o",
        alpha=0.5,
    )

    # Plot the maximum Sharpe and Sortino portfolios from our generated set
    plt.scatter(
        sdp_sortino,
        rp_sortino,
        marker="*",
        color="r",
        s=200,
        label="Maximum Sortino ratio",
    )
    plt.scatter(
        sdp_sharpe,
        rp_sharpe,
        marker="*",
        color="b",
        s=200,
        label="Maximum Sharpe ratio",
    )

    # Plot the optimized portfolios from the minimize function
    opt_sortino_std, opt_sortino_ret = optimal_std_sortino, optimal_return_sortino
    opt_sharpe_std, opt_sharpe_ret = optimal_std_sharpe, optimal_return_sharpe

    plt.scatter(
        opt_sortino_std,
        opt_sortino_ret,
        marker="D",
        color="darkred",
        s=200,
        label="Optimized Sortino",
    )
    plt.scatter(
        opt_sharpe_std,
        opt_sharpe_ret,
        marker="D",
        color="darkblue",
        s=200,
        label="Optimized Sharpe",
    )

    # Draw a line connecting the optimized portfolios to show the efficient frontier
    frontier_x = [opt_sharpe_std, opt_sortino_std]
    frontier_y = [opt_sharpe_ret, opt_sortino_ret]
    plt.plot(frontier_x, frontier_y, "k--", linewidth=2, label="Efficient Frontier")

    plt.title("Efficient Frontier with Sharpe and Sortino Ratios")
    plt.xlabel("Volatility (Std. Deviation)")
    plt.ylabel("Expected Returns")
    plt.colorbar(label="Sortino ratio")
    plt.legend(labelspacing=0.8)


# Create allocations directly from the optimization results
max_sharpe_allocation = pd.DataFrame(
    optimal_weights_sharpe, index=mean_returns.index, columns=["allocation"]
)
max_sharpe_allocation.allocation = [
    round(i * 100, 2) for i in max_sharpe_allocation.allocation
]

max_sortino_allocation = pd.DataFrame(
    optimal_weights_sortino, index=mean_returns.index, columns=["allocation"]
)
max_sortino_allocation.allocation = [
    round(i * 100, 2) for i in max_sortino_allocation.allocation
]

# Generate the efficient frontier plot
plot_efficient_frontier(mean_returns, cov_matrix, returns)

print("\nRaw Maximum Sharpe Ratio Portfolio Allocation\n")
print(max_sharpe_allocation)

print("\nRaw Maximum Sortino Ratio Portfolio Allocation\n")
print(max_sortino_allocation)

# Check if we should apply the half rule based on the HALF_RULE flag
if HALF_RULE:
    # Apply the half rule and normalize to both allocation types
    print("\nApplying half rule and normalizing allocations...")
    # Convert DataFrame to dictionary for the enforce_half_rule_and_normalize function
    sharpe_dict = max_sharpe_allocation["allocation"].to_dict()
    sortino_dict = max_sortino_allocation["allocation"].to_dict()

    # Apply the half rule and normalize
    sharpe_half_rule = enforce_half_rule_and_normalize(sharpe_dict)
    sortino_half_rule = enforce_half_rule_and_normalize(sortino_dict)

    # Convert back to DataFrame for display
    max_sharpe_half_rule = pd.DataFrame.from_dict(
        sharpe_half_rule, orient="index", columns=["allocation"]
    )
    max_sortino_half_rule = pd.DataFrame.from_dict(
        sortino_half_rule, orient="index", columns=["allocation"]
    )

    print("\nFinal Maximum Sharpe Ratio Portfolio Allocation (Half Rule Applied)\n")
    print(max_sharpe_half_rule)

    print("\nFinal Maximum Sortino Ratio Portfolio Allocation (Half Rule Applied)\n")
    print(max_sortino_half_rule)

plt.show()
