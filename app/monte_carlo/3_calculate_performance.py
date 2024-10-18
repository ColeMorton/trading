import polars as pl
import json
import numpy as np
from typing import List
import random
from app.monte_carlo.utils import get_data, calculate_performance_metrics

TICKER = 'BTC-USD'
BASE_INITIAL_PORTFOLIO_VALUE = 10000

# Read the JSON file
data = get_data(TICKER)

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
