import pandas as pd
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.macd.tools.backtest_strategy import backtest_strategy
from app.macd.tools.calculate_expectancy import calculate_expectancy

def parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows, short):
    """Perform parameter sensitivity analysis."""
    results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    expectancy_results = pd.DataFrame(index=pd.MultiIndex.from_product([short_windows, long_windows]), columns=signal_windows)
    for short in short_windows:
        for long in long_windows:
            if short < long:
                for signal in signal_windows:
                    data = calculate_macd(data, short_window=short, long_window=long, signal_window=signal)
                    data = calculate_macd_signals(data, short)
                    portfolio = backtest_strategy(data, short)
                    results.loc[(short, long), signal] = portfolio.total_return()
                    expectancy_results.loc[(short, long), signal] = calculate_expectancy(portfolio)
    return results, expectancy_results
