import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt

TICKER = 'BTC-USD'
ANNUAL_TRADING_DAYS = 365
# ANNUAL_TRADING_DAYS = 252

ema_fast = 11
ema_slow = 30

# Load the simulations
df = pd.read_csv(f'csv/geometric_brownian_motion/{TICKER}_gbm_extracted_simulations.csv', index_col='timestamp', parse_dates=True)

print(f"Loaded DataFrame shape: {df.shape}")

# Perform backtesting for each simulation
results = {}
for column in df.columns:
    price = df[column]
    
    print(f"\nProcessing simulation: {column}")
    print(f"Price range: {price.min():.2f} to {price.max():.2f}")
    print(f"Price series shape: {price.shape}")
    
    # Calculate EMAs
    ema_fast_series = vbt.MA.run(price, window=ema_fast, ewm=True).ma
    ema_slow_series = vbt.MA.run(price, window=ema_slow, ewm=True).ma
    
    # Generate entry and exit signals
    entries = (ema_fast_series > ema_slow_series) & (ema_fast_series.shift(1) <= ema_slow_series.shift(1))
    exits = (ema_fast_series < ema_slow_series) & (ema_fast_series.shift(1) >= ema_slow_series.shift(1))
    
    print(f"Number of entry signals: {entries.sum()}")
    print(f"Number of exit signals: {exits.sum()}")
    
    # Run portfolio simulation
    portfolio = vbt.Portfolio.from_signals(
        price,
        entries,
        exits,
        init_cash=10000,
        fees=0.001,
        freq='D'  # Set the frequency to daily
    ) 
    results[column] = portfolio
    
    print(f"Total return: {portfolio.total_return():.2%}")
    print(f"Sharpe ratio: {portfolio.sharpe_ratio():.2f}")
    print(f"Sortino ratio: {portfolio.sortino_ratio():.2f}")
    print(f"Calmar ratio: {portfolio.calmar_ratio():.2f}")
    print(f"Max drawdown: {portfolio.max_drawdown():.2%}")

print(f"\nNumber of simulations processed: {len(results)}")

if len(results) == 0:
    print("Error: No simulations were processed. Check the input data.")
else:
    # Combine results
    combined_results = pd.DataFrame({
        'Total Return (%)': [results[col].total_return() * 100 for col in df.columns],
        'Sharpe Ratio': [results[col].sharpe_ratio() for col in df.columns],
        'Sortino Ratio': [results[col].sortino_ratio() for col in df.columns],
        'Calmar Ratio': [results[col].calmar_ratio() for col in df.columns],
        'Max Drawdown (%)': [results[col].max_drawdown() * 100 for col in df.columns]
    })

    # Handle infinite values in ratios
    for ratio in ['Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio']:
        combined_results[ratio] = combined_results[ratio].replace([np.inf, -np.inf], np.nan)

    # Calculate median values
    median_values = combined_results.median()

    # Add median row to combined_results
    combined_results.loc['Median'] = median_values

    # Visualize results
    fig, axes = plt.subplots(3, 2, figsize=(15, 20))
    fig.suptitle('Backtest Results for Different Simulations', fontsize=16)

    # Total Return
    axes[0, 0].bar(range(len(combined_results) - 1), combined_results['Total Return (%)'][:-1])
    axes[0, 0].set_title('Total Return (%)')
    axes[0, 0].set_xticks(range(len(combined_results) - 1))
    axes[0, 0].set_xticklabels(combined_results.index[:-1], rotation=45)

    # Sharpe Ratio
    axes[0, 1].bar(range(len(combined_results) - 1), combined_results['Sharpe Ratio'][:-1])
    axes[0, 1].set_title('Sharpe Ratio')
    axes[0, 1].set_xticks(range(len(combined_results) - 1))
    axes[0, 1].set_xticklabels(combined_results.index[:-1], rotation=45)

    # Sortino Ratio
    axes[1, 0].bar(range(len(combined_results) - 1), combined_results['Sortino Ratio'][:-1])
    axes[1, 0].set_title('Sortino Ratio')
    axes[1, 0].set_xticks(range(len(combined_results) - 1))
    axes[1, 0].set_xticklabels(combined_results.index[:-1], rotation=45)

    # Calmar Ratio
    axes[1, 1].bar(range(len(combined_results) - 1), combined_results['Calmar Ratio'][:-1])
    axes[1, 1].set_title('Calmar Ratio')
    axes[1, 1].set_xticks(range(len(combined_results) - 1))
    axes[1, 1].set_xticklabels(combined_results.index[:-1], rotation=45)

    # Max Drawdown
    axes[2, 0].bar(range(len(combined_results) - 1), combined_results['Max Drawdown (%)'][:-1])
    axes[2, 0].set_title('Max Drawdown (%)')
    axes[2, 0].set_xticks(range(len(combined_results) - 1))
    axes[2, 0].set_xticklabels(combined_results.index[:-1], rotation=45)

    # Remove the last subplot
    fig.delaxes(axes[2, 1])

    plt.tight_layout()
    plt.savefig(f'images/geometric_brownian_motion/{TICKER}_backtest_results.png')
    print("\nBacktest results visualization saved to images/geometric_brownian_motion/backtest_results.png")

    # Print combined results with formatted numbers
    print("\nCombined Backtest Results:")
    pd.set_option('display.float_format', '{:.2f}'.format)
    print(combined_results)

    # Plot equity curves
    try:
        plt.figure(figsize=(15, 10))
        for column in df.columns:
            equity_curve = (1 + results[column].returns()).cumprod()
            plt.plot(equity_curve.index, equity_curve.values, label=column)
            print(f"Equity curve for {column}: min={equity_curve.min():.2f}, max={equity_curve.max():.2f}")
        plt.title('Equity Curves for Different Simulations')
        plt.xlabel('Date')
        plt.ylabel('Portfolio Value (Normalized)')
        plt.legend()
        plt.tight_layout()
        plt.savefig(f'images/geometric_brownian_motion/{TICKER}_gbm_equity_curves.png')
        print("Equity curves visualization saved to images/geometric_brownian_motion/equity_curves.png")
    except Exception as e:
        print(f"Error while plotting equity curves: {str(e)}")

print("Script execution completed.")
