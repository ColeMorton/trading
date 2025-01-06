"""
Multiple Strategy Portfolio Review Module

This module performs portfolio analysis for multiple trading strategies,
comparing their performance against a benchmark portfolio.
"""

from typing import List
import vectorbt as vbt
from config import config
from app.tools.setup_logging import setup_logging
from app.portfolio_review.tools.portfolio_analysis import (
    prepare_data,
    find_common_dates,
    create_price_dataframe,
    create_benchmark_data,
    calculate_risk_metrics,
    check_open_positions
)
from app.portfolio_review.tools.visualization import (
    create_portfolio_plots,
    print_portfolio_stats,
    print_open_positions
)
from app.ma_cross.tools.generate_signals import generate_signals
from app.tools.stats_converter import convert_stats

def run_portfolio_analysis():
    """Run portfolio analysis for multiple strategies."""
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name='portfolio_review',
        log_file='review_multiple.log'
    )
    
    try:
        # Get unique symbols from strategies
        symbols: List[str] = list(set(strategy['symbol'] for strategy in config['strategies'].values()))
        log(f"Processing symbols: {symbols}")

        # Download and prepare data
        data_dict, pandas_data_dict = prepare_data(symbols, config, log)
        
        # Find common date range
        common_dates = find_common_dates(data_dict, log)
        
        # Create price DataFrame
        price_df_pd = create_price_dataframe(common_dates, data_dict, config, log)
        
        # Generate signals using the generate_signals utility
        log("Generating trading signals")
        entries_pd, exits_pd = generate_signals(pandas_data_dict, {
            'strategies': config['strategies'],
            'USE_SMA': config.get('USE_SMA', False),
            'USE_RSI': config.get('USE_RSI', False),
            'RSI_THRESHOLD': config.get('RSI_THRESHOLD', 70),
            'SHORT': config.get('SHORT', False),
            'init_cash': config.get('init_cash', 10000),
            'fees': config.get('fees', 0.001)
        }, log)

        # Create size DataFrame (position sizes for each strategy)
        sizes_pd = price_df_pd.copy()
        sizes_pd[:] = 1.0  # Set all position sizes to 1.0
        
        # Run the portfolio simulation
        log("Running portfolio simulation")
        portfolio = vbt.Portfolio.from_signals(
            close=price_df_pd,
            entries=entries_pd.astype(bool),
            exits=exits_pd.astype(bool),
            size=sizes_pd,
            init_cash=config['init_cash'],
            fees=config['fees'],
            freq='1D',
            group_by=True,
            cash_sharing=True
        )

        # Create benchmark portfolio data
        benchmark_close_pd, benchmark_entries_pd, benchmark_sizes_pd = create_benchmark_data(
            common_dates, data_dict, symbols, log
        )

        # Create benchmark portfolio
        log("Creating benchmark portfolio")
        benchmark_portfolio = vbt.Portfolio.from_signals(
            close=benchmark_close_pd,
            entries=benchmark_entries_pd,
            size=benchmark_sizes_pd,
            init_cash=config['init_cash'],
            fees=config['fees'],
            freq='1D',
            group_by=True,
            cash_sharing=True
        )

        # Calculate and display portfolio statistics
        stats = portfolio.stats()
        converted_stats = convert_stats(stats, log, config)
        
        # Calculate risk metrics
        risk_metrics = calculate_risk_metrics(portfolio.returns().values)
        
        # Print statistics and risk metrics
        print_portfolio_stats(converted_stats, risk_metrics, log)
        
        # Create and display plots
        create_portfolio_plots(portfolio, benchmark_portfolio, log)
        
        # Check and display open positions
        open_positions = check_open_positions(portfolio, price_df_pd, log)
        print_open_positions(open_positions)

    except Exception as e:
        log(f"Error in portfolio review: {str(e)}", "error")
        raise
    finally:
        log_close()

if __name__ == "__main__":
    run_portfolio_analysis()
