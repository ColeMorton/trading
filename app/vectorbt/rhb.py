import vectorbt as vbt
import pandas as pd
import numpy as np
from itertools import product
import matplotlib.pyplot as plt
import seaborn as sns

# Fetch BTC-USD daily data
btc_data = vbt.YFData.download("BTC-USD", start="2015-01-01")

# Extract OHLC data
ohlc = btc_data.get()

# Calculate daily range
ohlc['range'] = ohlc['High'] - ohlc['Low']

def generate_entries_exits(close, high, range_val, x, y):
    # Generate entry signals: where close > (previous high + x * range)
    entries = close > high.shift(1) + x * range_val
    # Generate exit signals: close should not be greater than shifted high + x * shifted range
    exits = ~(close > high.shift(y) + x * range_val.shift(y))
    return entries, exits

# Define parameter ranges
x_range = range(3, 55)
y_range = range(1, 55)

# Generate all parameter combinations
params = list(product(x_range, y_range))

# Function to process a single parameter combination
def process_single_param(x, y):
    # Generate entry and exit signals for the given x and y
    entries, exits = generate_entries_exits(ohlc['Close'], ohlc['High'], ohlc['range'], x, y)
    
    # Create portfolio based on the signals
    portfolio = vbt.Portfolio.from_signals(
        ohlc['Close'],
        entries,
        exits
    )
    
    return {
        'Total Return': portfolio.total_return(),
        'Sharpe Ratio': portfolio.sharpe_ratio(),
        'Max Drawdown': portfolio.max_drawdown()
    }

# Function to process a batch of parameters
def process_batch(batch_params):
    results = []

    for x, y in batch_params:
        metrics = process_single_param(x, y)
        results.append({
            'x': x,
            'y': y,
            'Total Return': metrics['Total Return'],
            'Sharpe Ratio': metrics['Sharpe Ratio'],
            'Max Drawdown': metrics['Max Drawdown']
        })

    return pd.DataFrame(results).set_index(['x', 'y'])

# Process parameters in batches
batch_size = 100
results_list = []

for i in range(0, len(params), batch_size):
    batch_params = params[i:i + batch_size]
    batch_results = process_batch(batch_params)
    results_list.append(batch_results)
    print(f"Processed batch {i // batch_size + 1} of {len(params) // batch_size + 1}")

# Combine all results
results_df = pd.concat(results_list)

# Find best parameters for each metric
best_return = results_df['Total Return'].idxmax()
best_sharpe = results_df['Sharpe Ratio'].idxmax()
best_drawdown = results_df['Max Drawdown'].idxmin()

print("\nBest parameters:")
print(f"Total Return: x={best_return[0]}, y={best_return[1]}")
print(f"Sharpe Ratio: x={best_sharpe[0]}, y={best_sharpe[1]}")
print(f"Max Drawdown: x={best_drawdown[0]}, y={best_drawdown[1]}")

# Create heatmaps
def create_heatmap(data, title):
    pivot_data = data.unstack(level='y')
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(pivot_data, ax=ax, cmap='viridis')
    ax.set_title(title)
    ax.set_xlabel('Y')
    ax.set_ylabel('X')
    plt.show()

create_heatmap(results_df['Total Return'], "Total Return Heatmap")
create_heatmap(results_df['Sharpe Ratio'], "Sharpe Ratio Heatmap")
create_heatmap(results_df['Max Drawdown'], "Max Drawdown Heatmap")
