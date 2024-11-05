import pandas as pd
import numpy as np
import logging
import polars as pl
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.macd.tools.backtest_strategy import backtest_strategy
from app.macd.tools.calculate_expectancy import calculate_expectancy

def parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows, config):
    """Perform parameter sensitivity analysis."""
    # Validate input data
    logging.info("\nData Statistics:")
    logging.info(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
    logging.info(f"Number of records: {len(data)}")
    logging.info(f"Price range: {data['Close'].min():.2f} to {data['Close'].max():.2f}")
    
    # Check for sufficient data
    if len(data) < max(long_windows) + max(signal_windows):
        raise ValueError("Not enough data points for the selected window sizes")
    
    # Initialize results dataframes
    results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    expectancy_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    sharpe_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    sortino_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    calmar_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    
    best_return = float('-inf')
    best_params = None
    best_expectancy = float('-inf')
    best_expectancy_params = None
    best_sharpe = float('-inf')
    best_sharpe_params = None
    best_sortino = float('-inf')
    best_sortino_params = None
    best_calmar = float('-inf')
    best_calmar_params = None
    
    total_combinations = len(short_windows) * len(long_windows) * len(signal_windows)
    current_combination = 0
    
    for short in short_windows:
        for long in long_windows:
            if short < long:  # Only test valid combinations where short period is less than long period
                for signal in signal_windows:
                    current_combination += 1
                    logging.info(f"\nTesting combination {current_combination}/{total_combinations}")
                    logging.info(f"Parameters: Short={short}, Long={long}, Signal={signal}")
                    
                    # Create a fresh copy of data for each parameter combination
                    test_data = data.clone()
                    
                    # Calculate MACD and signals
                    test_data = calculate_macd(test_data, short_window=short, long_window=long, signal_window=signal)
                    test_data = calculate_macd_signals(test_data, config["SHORT"])
                    
                    # Count signals
                    signal_counts = test_data.group_by('Signal').agg([
                        pl.count('Signal').alias('count')
                    ]).sort('Signal')
                    logging.info(f"Signal distribution:\n{signal_counts}")
                    
                    # Backtest the strategy
                    portfolio = backtest_strategy(test_data, config["SHORT"])
                    stats = portfolio.stats()
                    
                    total_return = portfolio.total_return()
                    expectancy = calculate_expectancy(portfolio)
                    sharpe = stats['Sharpe Ratio']
                    sortino = stats['Sortino Ratio']
                    calmar = stats['Calmar Ratio']
                    
                    # Log performance metrics
                    logging.info(f"Total Return: {total_return:.2%}")
                    logging.info(f"Expectancy: {expectancy:.4f}")
                    logging.info(f"Sharpe Ratio: {sharpe:.4f}")
                    logging.info(f"Sortino Ratio: {sortino:.4f}")
                    logging.info(f"Calmar Ratio: {calmar:.4f}")
                    
                    # Store results
                    results.loc[(short, long), signal] = total_return
                    expectancy_results.loc[(short, long), signal] = expectancy
                    sharpe_results.loc[(short, long), signal] = sharpe
                    sortino_results.loc[(short, long), signal] = sortino
                    calmar_results.loc[(short, long), signal] = calmar
                    
                    # Update best parameters
                    if total_return > best_return:
                        best_return = total_return
                        best_params = (short, long, signal)
                        logging.info(f"New best return: {best_return:.2%} with parameters: {best_params}")
                    
                    if expectancy > best_expectancy:
                        best_expectancy = expectancy
                        best_expectancy_params = (short, long, signal)
                        logging.info(f"New best expectancy: {best_expectancy:.4f} with parameters: {best_expectancy_params}")
                        
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_sharpe_params = (short, long, signal)
                        logging.info(f"New best Sharpe: {best_sharpe:.4f} with parameters: {best_sharpe_params}")
                        
                    if sortino > best_sortino:
                        best_sortino = sortino
                        best_sortino_params = (short, long, signal)
                        logging.info(f"New best Sortino: {best_sortino:.4f} with parameters: {best_sortino_params}")
                        
                    if calmar > best_calmar:
                        best_calmar = calmar
                        best_calmar_params = (short, long, signal)
                        logging.info(f"New best Calmar: {best_calmar:.4f} with parameters: {best_calmar_params}")
    
    # Log final results
    logging.info("\nOptimization Results:")
    logging.info(f"Best return: {best_return:.2%} with parameters: Short={best_params[0]}, Long={best_params[1]}, Signal={best_params[2]}")
    logging.info(f"Best expectancy: {best_expectancy:.4f} with parameters: Short={best_expectancy_params[0]}, Long={best_expectancy_params[1]}, Signal={best_expectancy_params[2]}")
    logging.info(f"Best Sharpe: {best_sharpe:.4f} with parameters: Short={best_sharpe_params[0]}, Long={best_sharpe_params[1]}, Signal={best_sharpe_params[2]}")
    logging.info(f"Best Sortino: {best_sortino:.4f} with parameters: Short={best_sortino_params[0]}, Long={best_sortino_params[1]}, Signal={best_sortino_params[2]}")
    logging.info(f"Best Calmar: {best_calmar:.4f} with parameters: Short={best_calmar_params[0]}, Long={best_calmar_params[1]}, Signal={best_calmar_params[2]}")
    
    return (results, expectancy_results, sharpe_results, sortino_results, calmar_results,
            best_params, best_expectancy_params, best_sharpe_params, best_sortino_params, best_calmar_params,
            best_return, best_expectancy, best_sharpe, best_sortino, best_calmar)
