import polars as pl
import json
import numpy as np
from typing import List
import random

TICKER = 'BTC-USD'
BASE_INITIAL_PORTFOLIO_VALUE = 10000

def calculate_cumulative_return(returns: List[float]) -> float:
    """Calculate the cumulative return of a sequence of trades."""
    return np.prod(1 + np.array(returns)) - 1

def calculate_max_drawdown(returns: List[float]) -> float:
    """Calculate the maximum drawdown of a sequence of trades."""
    cumulative = np.cumprod(1 + np.array(returns))
    peak = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - peak) / peak
    return np.min(drawdown)

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.02) -> float:
    """Calculate the Sharpe ratio of a sequence of trades."""
    excess_returns = np.array(returns) - risk_free_rate / 252  # Assuming 252 trading days in a year
    return np.sqrt(252) * np.mean(excess_returns) / np.std(excess_returns)

def calculate_final_portfolio_value(returns: List[float], initial_value: float) -> float:
    """Calculate the final portfolio value given a sequence of returns."""
    return initial_value * np.prod(1 + np.array(returns))

def calculate_performance_metrics(sequence: pl.DataFrame, initial_value: float) -> dict:
    """Calculate performance metrics for a single sequence."""
    returns = sequence['Return (%)'].to_list()
    cumulative_return = calculate_cumulative_return(returns)
    max_drawdown = calculate_max_drawdown(returns)
    sharpe_ratio = calculate_sharpe_ratio(returns)
    final_portfolio_value = calculate_final_portfolio_value(returns, initial_value)
    
    return {
        'cumulative_return': cumulative_return,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'final_portfolio_value': final_portfolio_value,
        'initial_portfolio_value': initial_value
    }

# Read the JSON file
with open(f'json/monte_carlo/{TICKER}_ema_cross_permutations.json', 'r') as file:
    data = json.load(file)

# Get the original trade data
original_trades = data['permutations'][0]

# Print a sample of the original trade data
print("Sample of original trade data:")
for key, value in original_trades.items():
    print(f"{key}: {value[:5]}")

print("\nSample of 'Return (%)' values:")
print(original_trades['Return (%)'][:10])

# Number of Monte Carlo simulations
num_simulations = 1000

# Process all permutations
results = []
for i in range(num_simulations):
    # Create a new random permutation of trades with added randomness
    shuffled_trades = {k: random.sample(v, len(v)) for k, v in original_trades.items()}
    
    # Add some random variation to the returns
    shuffled_trades['Return (%)'] = [r + random.gauss(0, 0.001) for r in shuffled_trades['Return (%)']]
    
    sequence = pl.DataFrame(shuffled_trades)
    
    # Randomize the initial portfolio value
    initial_value = BASE_INITIAL_PORTFOLIO_VALUE * (1 + random.gauss(0, 0.05))
    
    metrics = calculate_performance_metrics(sequence, initial_value)
    metrics['sequence_id'] = i
    results.append(metrics)
    
    # Print detailed information for the first few simulations
    if i < 5:
        print(f"\nSimulation {i}:")
        print(f"Initial portfolio value: {initial_value:.2f}")
        print(f"First few returns: {sequence['Return (%)'][:5].to_list()}")
        print(f"Cumulative return: {metrics['cumulative_return']}")
        print(f"Max drawdown: {metrics['max_drawdown']}")
        print(f"Sharpe ratio: {metrics['sharpe_ratio']}")
        print(f"Final portfolio value: {metrics['final_portfolio_value']}")

# Convert results to a DataFrame
results_df = pl.DataFrame(results)

# Calculate summary statistics
summary_stats = {
    'mean_cumulative_return': results_df['cumulative_return'].mean(),
    'median_cumulative_return': results_df['cumulative_return'].median(),
    'std_cumulative_return': results_df['cumulative_return'].std(),
    'mean_max_drawdown': results_df['max_drawdown'].mean(),
    'median_max_drawdown': results_df['max_drawdown'].median(),
    'mean_sharpe_ratio': results_df['sharpe_ratio'].mean(),
    'median_sharpe_ratio': results_df['sharpe_ratio'].median(),
    'mean_final_portfolio_value': results_df['final_portfolio_value'].mean(),
    'std_final_portfolio_value': results_df['final_portfolio_value'].std(),
    'worst_case_portfolio_value': results_df['final_portfolio_value'].min(),
    'var_5_percent': np.percentile(results_df['final_portfolio_value'].to_numpy(), 5)
}

# Add summary statistics to the results DataFrame
for key, value in summary_stats.items():
    results_df = results_df.with_columns(pl.lit(value).alias(key))

# Save results to a CSV file
results_df.write_csv(f'csv/{TICKER}_monte_carlo_performance.csv')

print(f"\nProcessed {num_simulations} permutations. Results saved to 'csv/{TICKER}_monte_carlo_performance.csv'.")
print("\nSummary Statistics:")
for key, value in summary_stats.items():
    print(f"{key}: {value}")

# Print the first few rows of the results DataFrame
print("\nSample of results DataFrame:")
print(results_df.head())
