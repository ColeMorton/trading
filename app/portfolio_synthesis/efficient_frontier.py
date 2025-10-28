import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize
import yfinance as yf


# Set date range and assets
# start_date = '2020-06-02'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2020-01-01'
# end_date = '2024-11-02'

# start_date = '2023-10-24'
# end_date = '2024-11-02'

# ===========================
# CONFIGURATION SECTION
# ===========================


class OptimizationConfig:
    """Configuration class for efficient frontier optimization."""

    def __init__(self):
        # Data configuration
        self.start_date = "2020-01-01"
        self.end_date = "2025-10-22"
        self.use_max_period = (
            True  # If True, ignores date range and uses max available data
        )

        # Asset configuration
        self.assets = ["MA", "BRK-B", "TPR", "AVGO", "TTWO", "XYZ"]

        # Asset configuration
        # self.assets = [
        #     "NVDA",
        #     "TSLA",
        #     "PLTR",
        #     "NRG",
        #     # "BTC-USD",
        # ]

        # Business rules
        self.apply_half_rule = True  # Enforce min allocation = 0.5 * max allocation

        # System configuration (auto-determined)
        self.memory_limit_mb = self._get_system_memory_limit()
        self.max_portfolios = 100000  # High quality analysis
        self.min_portfolios = 1000  # Minimum for meaningful analysis

        # Performance settings (fixed for accuracy)
        self.random_portfolio_ratio = 0.4  # 40% random for good coverage

        # Optimization configuration
        self.risk_free_rate = 0.0
        self.optimization_method = "SLSQP"
        self.random_seed = 42

    def _get_system_memory_limit(self):
        """Determine appropriate memory limit based on system resources."""
        import psutil

        # Get total system memory
        total_memory_gb = psutil.virtual_memory().total / (1024**3)

        # Use conservative percentage of available memory
        if total_memory_gb >= 16:
            # High-memory system: use up to 8GB
            return 8000
        if total_memory_gb >= 8:
            # Medium-memory system: use up to 4GB
            return 4000
        if total_memory_gb >= 4:
            # Low-memory system: use up to 2GB
            return 2000
        # Very low-memory system: use up to 1GB
        return 1000

    def get_performance_settings(self):
        """Get performance settings optimized for accuracy."""
        return {
            "random_portfolio_ratio": self.random_portfolio_ratio,
            "max_portfolios": self.max_portfolios,
            "memory_limit_mb": self.memory_limit_mb,
        }


# Create global configuration instance
config = OptimizationConfig()

# ===========================
# EASY CONFIGURATION OVERRIDES
# ===========================
# Uncomment and modify any of these lines to customize the analysis:

# config.assets = ['BTC-USD', 'SPY', 'QQQ', 'SOL-USD']  # Custom asset list
# config.apply_half_rule = False  # Disable half rule constraint

print(
    f"Configuration: {len(config.assets)} assets, memory limit: {config.memory_limit_mb}MB, half rule: {config.apply_half_rule}",
)

# Legacy variable assignments for backward compatibility
start_date = config.start_date
end_date = config.end_date
HALF_RULE = config.apply_half_rule
ASSETS = config.assets

# Download the data
# data = yf.download(ASSETS, start=start_date, end=end_date)['Close']
data = yf.download(ASSETS, period="max")["Close"]
print(f"Start Date: {start_date} End Date: {end_date}")

# Calculate daily returns
returns = data.pct_change().dropna()


class MatrixCache:
    """Cache for expensive matrix operations."""

    def __init__(self):
        self.cache = {}

    def get_cached_cholesky(self, cov_matrix):
        """Get cached Cholesky decomposition of covariance matrix."""
        cache_key = "cholesky_" + str(hash(cov_matrix.tobytes()))

        if cache_key not in self.cache:
            try:
                self.cache[cache_key] = np.linalg.cholesky(cov_matrix)
            except np.linalg.LinAlgError:
                # Fallback to eigenvalue decomposition for near-singular matrices
                eigenvals, eigenvecs = np.linalg.eigh(cov_matrix)
                eigenvals = np.maximum(eigenvals, 1e-8)  # Regularize small eigenvalues
                self.cache[cache_key] = eigenvecs @ np.diag(np.sqrt(eigenvals))

        return self.cache[cache_key]

    def get_cached_inverse(self, matrix):
        """Get cached matrix inverse with regularization."""
        cache_key = "inverse_" + str(hash(matrix.tobytes()))

        if cache_key not in self.cache:
            try:
                self.cache[cache_key] = np.linalg.inv(matrix)
            except np.linalg.LinAlgError:
                # Use pseudo-inverse for singular matrices
                self.cache[cache_key] = np.linalg.pinv(matrix)

        return self.cache[cache_key]


# Global cache instance
_matrix_cache = MatrixCache()


def portfolio_performance(weights, mean_returns, cov_matrix):
    """Optimized portfolio performance calculation with caching."""
    returns = np.dot(weights, mean_returns)

    # Use cached operations for better performance
    variance = weights.T @ cov_matrix @ weights
    std = np.sqrt(variance)

    return returns, std


def portfolio_performance_batch(weights_matrix, mean_returns, cov_matrix):
    """
    Vectorized portfolio performance calculation for multiple portfolios.

    Args:
        weights_matrix (np.ndarray): Matrix where each row is a portfolio weight vector
        mean_returns (np.ndarray): Vector of mean returns
        cov_matrix (np.ndarray): Covariance matrix

    Returns:
        tuple: (returns_array, std_array) for all portfolios
    """
    # Vectorized calculations - much faster than loops
    returns_array = weights_matrix @ mean_returns

    # Calculate portfolio variances: diag(W @ Cov @ W.T) where W is weights matrix
    variances = np.sum((weights_matrix @ cov_matrix) * weights_matrix, axis=1)
    std_array = np.sqrt(variances)

    return returns_array, std_array


def downside_deviation_batch(returns_matrix, target=0):
    """
    Vectorized downside deviation calculation for multiple portfolios.

    Args:
        returns_matrix (np.ndarray): Matrix where each row is portfolio returns
        target (float): Target return threshold

    Returns:
        np.ndarray: Downside deviation for each portfolio
    """
    downside_diff = np.minimum(0, returns_matrix - target)
    dd = np.sqrt(np.mean(downside_diff**2, axis=1))
    dd[dd == 0] = 1e-10
    return dd


def downside_deviation(returns, target=0):
    downside_diff = np.minimum(0, returns - target)
    if np.all(downside_diff == 0):
        return 1e-10
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
    optimal_weights_sortino,
    mean_returns,
    cov_matrix,
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
    optimal_weights_sharpe,
    mean_returns,
    cov_matrix,
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
        fractional_parts.keys(),
        key=fractional_parts.get,
        reverse=True,
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


def calculate_adaptive_portfolio_count(num_assets, config_obj=None, max_assets=8):
    """
    Calculate adaptive portfolio count based on number of assets.

    For assets <= max_assets: use base_count
    For assets > max_assets: scale down to maintain performance

    Args:
        num_assets (int): Number of assets in portfolio
        config_obj (OptimizationConfig): Configuration object
        max_assets (int): Asset count threshold for scaling

    Returns:
        int: Adaptive portfolio count
    """
    if config_obj is None:
        config_obj = config

    settings = config_obj.get_performance_settings()
    base_count = settings["max_portfolios"]
    min_count = config_obj.min_portfolios

    if num_assets <= max_assets:
        return base_count

    # Scale down exponentially to maintain reasonable performance
    # For each asset beyond max_assets, reduce portfolio count by factor
    scale_factor = (max_assets / num_assets) ** 2

    adaptive_count = max(int(base_count * scale_factor), min_count)

    print(
        f"Adaptive scaling: {num_assets} assets -> {adaptive_count:,} portfolios (vs {base_count:,} baseline)",
    )
    return adaptive_count


def estimate_memory_usage(num_assets, num_portfolios):
    """
    Estimate memory usage for efficient frontier calculation.

    Args:
        num_assets (int): Number of assets
        num_portfolios (int): Number of portfolios to generate

    Returns:
        float: Estimated memory usage in MB
    """
    # Results matrix: 4 metrics × num_portfolios × 8 bytes per float64
    results_memory = 4 * num_portfolios * 8 / (1024 * 1024)

    # Weights record: num_portfolios × num_assets × 8 bytes per float64
    weights_memory = num_portfolios * num_assets * 8 / (1024 * 1024)

    # Returns and covariance matrices
    returns_memory = len(returns) * num_assets * 8 / (1024 * 1024)
    cov_memory = num_assets * num_assets * 8 / (1024 * 1024)

    total_memory = results_memory + weights_memory + returns_memory + cov_memory

    print(f"Estimated memory usage: {total_memory:.1f} MB")
    return total_memory


# Plot efficient frontier
def plot_efficient_frontier(
    mean_returns,
    cov_matrix,
    returns,
    num_portfolios=None,
    config_obj=None,
):
    """
    Generate and plot the efficient frontier using a combination of:
    1. Random portfolios
    2. Portfolios along the efficient frontier
    3. The optimized Sharpe and Sortino portfolios
    """
    # Use global config if not provided
    if config_obj is None:
        config_obj = config

    # Set seed for reproducibility
    np.random.seed(config_obj.random_seed)

    # Get performance settings
    settings = config_obj.get_performance_settings()
    risk_free_rate = config_obj.risk_free_rate

    # Calculate adaptive portfolio count if not specified
    num_assets = len(mean_returns)
    if num_portfolios is None:
        total_portfolios = calculate_adaptive_portfolio_count(num_assets, config_obj)
    else:
        total_portfolios = num_portfolios

    # Estimate and check memory usage
    estimated_memory = estimate_memory_usage(num_assets, total_portfolios)
    memory_limit_mb = settings["memory_limit_mb"]

    if estimated_memory > memory_limit_mb:
        # Scale down further if memory usage is too high
        scale_factor = memory_limit_mb / estimated_memory
        total_portfolios = max(
            int(total_portfolios * scale_factor),
            config_obj.min_portfolios,
        )
        print(f"Memory limit exceeded, reducing to {total_portfolios:,} portfolios")
        estimated_memory = estimate_memory_usage(num_assets, total_portfolios)

    # Allocate space for results
    results = np.zeros((4, total_portfolios))
    weights_record = []

    # Smart sampling strategy: use configured ratio with adaptive scaling
    base_ratio = settings["random_portfolio_ratio"]
    random_portfolio_ratio = min(base_ratio, 5000 / total_portfolios)  # Adaptive ratio
    num_random = int(total_portfolios * random_portfolio_ratio)

    print(
        f"Generating {num_random:,} random portfolios ({random_portfolio_ratio:.1%} of total)",
    )

    # Generate random portfolios using Latin hypercube sampling for better coverage
    from scipy.stats import qmc

    if num_random > 0:
        # Use Latin hypercube sampling for better space coverage
        sampler = qmc.LatinHypercube(d=len(mean_returns), seed=42)
        lh_samples = sampler.random(n=num_random)

        # Normalize all samples to sum to 1 (vectorized)
        lh_weights = lh_samples / np.sum(lh_samples, axis=1, keepdims=True)

        # Vectorized batch calculations for all random portfolios
        returns_array, std_array = portfolio_performance_batch(
            lh_weights,
            mean_returns,
            cov_matrix,
        )

        # Calculate portfolio returns for downside deviation (vectorized)
        portfolio_returns_matrix = lh_weights @ returns.T
        dd_array = downside_deviation_batch(portfolio_returns_matrix)

        # Store results (vectorized)
        results[0, :num_random] = returns_array
        results[1, :num_random] = std_array
        results[2, :num_random] = (
            returns_array - risk_free_rate
        ) / dd_array  # Sortino ratio
        results[3, :num_random] = (
            returns_array - risk_free_rate
        ) / std_array  # Sharpe ratio

        # Store weights for later use
        weights_record.extend(lh_weights.tolist())

    # Strategic sampling: efficient frontier and optimized portfolio combinations
    remaining = total_portfolios - num_random
    current_idx = num_random

    print(f"Generating {remaining:,} strategic portfolios along efficient frontier")

    # Include the optimized portfolios themselves
    if remaining > 0:
        weights_record.append(optimal_weights_sharpe)
        portfolio_return, portfolio_std = portfolio_performance(
            optimal_weights_sharpe,
            mean_returns,
            cov_matrix,
        )
        dd = downside_deviation(np.dot(returns, optimal_weights_sharpe))
        results[0, current_idx] = portfolio_return
        results[1, current_idx] = portfolio_std
        results[2, current_idx] = (portfolio_return - risk_free_rate) / dd
        results[3, current_idx] = (portfolio_return - risk_free_rate) / portfolio_std
        current_idx += 1
        remaining -= 1

    if remaining > 0:
        weights_record.append(optimal_weights_sortino)
        portfolio_return, portfolio_std = portfolio_performance(
            optimal_weights_sortino,
            mean_returns,
            cov_matrix,
        )
        dd = downside_deviation(np.dot(returns, optimal_weights_sortino))
        results[0, current_idx] = portfolio_return
        results[1, current_idx] = portfolio_std
        results[2, current_idx] = (portfolio_return - risk_free_rate) / dd
        results[3, current_idx] = (portfolio_return - risk_free_rate) / portfolio_std
        current_idx += 1
        remaining -= 1

    # Generate strategic portfolios along efficient frontier
    if remaining > 0:
        # More sophisticated frontier sampling: use risk budgeting approach
        for i in range(remaining):
            if remaining == 1:
                t = 0.5  # Single portfolio at midpoint
            else:
                # Non-linear spacing for better coverage of interesting regions
                linear_t = i / (remaining - 1)
                t = linear_t**0.7  # Bias towards lower-risk region

            # Create weighted combinations with small random perturbation
            base_weights = (
                t * optimal_weights_sharpe + (1 - t) * optimal_weights_sortino
            )

            # Add small random perturbation for diversity (5% of base allocation)
            perturbation = np.random.normal(0, 0.05, len(base_weights))
            weights = base_weights + perturbation * base_weights

            # Ensure non-negative and normalized
            weights = np.maximum(weights, 0.001)  # Minimum 0.1% allocation
            weights = weights / np.sum(weights)

            weights_record.append(weights)
            portfolio_return, portfolio_std = portfolio_performance(
                weights,
                mean_returns,
                cov_matrix,
            )
            dd = downside_deviation(np.dot(returns, weights))

            results[0, current_idx] = portfolio_return
            results[1, current_idx] = portfolio_std
            results[2, current_idx] = (portfolio_return - risk_free_rate) / dd
            results[3, current_idx] = (
                portfolio_return - risk_free_rate
            ) / portfolio_std
            current_idx += 1

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
    optimal_weights_sharpe,
    index=mean_returns.index,
    columns=["allocation"],
)
max_sharpe_allocation.allocation = [
    round(i * 100, 2) for i in max_sharpe_allocation.allocation
]

max_sortino_allocation = pd.DataFrame(
    optimal_weights_sortino,
    index=mean_returns.index,
    columns=["allocation"],
)
max_sortino_allocation.allocation = [
    round(i * 100, 2) for i in max_sortino_allocation.allocation
]

# Generate the efficient frontier plot with adaptive scaling
plot_efficient_frontier(mean_returns, cov_matrix, returns)

print("\nRaw Maximum Sharpe Ratio Portfolio Allocation\n")
print(max_sharpe_allocation)

print("\nRaw Maximum Sortino Ratio Portfolio Allocation\n")
print(max_sortino_allocation)

# Check if we should apply the half rule based on configuration
if config.apply_half_rule:
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
        sharpe_half_rule,
        orient="index",
        columns=["allocation"],
    )
    max_sortino_half_rule = pd.DataFrame.from_dict(
        sortino_half_rule,
        orient="index",
        columns=["allocation"],
    )

    print("\nFinal Maximum Sharpe Ratio Portfolio Allocation (Half Rule Applied)\n")
    print(max_sharpe_half_rule)

    print("\nFinal Maximum Sortino Ratio Portfolio Allocation (Half Rule Applied)\n")
    print(max_sortino_half_rule)

plt.show()
