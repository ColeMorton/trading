"""
Portfolio Visualization Module

This module handles the creation and display of portfolio analysis plots.
"""

import vectorbt as vbt


def create_portfolio_plots(
    portfolio: vbt.Portfolio, benchmark_portfolio: vbt.Portfolio, log
):
    """
    Create and display portfolio analysis plots.

    Args:
        portfolio: Strategy portfolio
        benchmark_portfolio: Benchmark portfolio for comparison
        log: Logging function
    """
    # Create comparison plots
    log("Creating portfolio plots")

    # Plot benchmark portfolio value
    benchmark_portfolio.plot_value().show()

    # Plot additional metrics for strategy portfolio
    portfolio.plot(
        [
            "value",
            "cum_returns",
            "drawdowns",
            "underwater",
            "net_exposure",
        ],
        show_titles=True,
    ).show()


def print_portfolio_stats(stats: dict, risk_metrics: dict, log):
    """
    Print portfolio statistics and risk metrics.

    Args:
        stats: Dictionary of portfolio statistics
        risk_metrics: Dictionary of risk metrics (VaR, CVaR)
        log: Logging function
    """
    print("\nStrategy Portfolio Statistics:")
    print("===================")
    for key, value in stats.items():
        print(f"{key}: {value}")
        log(f"{key}: {value}")

    print("\nRisk Metrics:")
    print("===================")
    for metric, value in risk_metrics.items():
        print(f"{metric}: {value:.2%}")
        log(f"{metric}: {value:.2%}")


def print_open_positions(open_positions: list):
    """
    Print currently open positions.

    Args:
        open_positions: List of tuples containing (strategy_name, position_size)
    """
    if open_positions:
        print("\nStrategies with Open Positions:")
        print("===================")
        for strategy_name, position in open_positions:
            print(f"{strategy_name}: {position:.2f} units")
