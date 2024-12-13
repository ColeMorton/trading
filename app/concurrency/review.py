"""
Concurrency Analysis Module for Trading Strategies.

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure. Supports analysis of strategies with different
timeframes by resampling hourly data to daily when needed.
"""

from typing import List, Callable
import json
from pathlib import Path
import polars as pl
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.concurrency.tools.types import StrategyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.visualization import plot_concurrency
from app.concurrency.tools.report import generate_json_report
from app.concurrency.tools.portfolio_loader import load_portfolio_from_csv
from app.tools.backtest_strategy import backtest_strategy
from app.tools.file_utils import convert_stats

def run(strategies: List[StrategyConfig], log: Callable[[str, str], None], config: dict) -> bool:
    """Run concurrency analysis across multiple strategies.

    Performs a comprehensive analysis of concurrent positions across all
    provided trading strategies simultaneously, including data preparation,
    analysis, and visualization. Handles different timeframes by resampling
    hourly data to daily when needed.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to analyze
        log: Callable for logging messages
        config: Configuration dictionary containing BASE_DIR and REFRESH settings

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If analysis fails at any stage
    """

    try:
        if len(strategies) < 2:
            raise ValueError("At least two strategies are required for concurrency analysis")
            
        log(f"Starting unified concurrency analysis across {len(strategies)} strategies")
        for i, strategy_config in enumerate(strategies, 1):
            log(f"Strategy {i} - {strategy_config['TICKER']}: {'Hourly' if strategy_config.get('USE_HOURLY', False) else 'Daily'}")
        
        # Get and prepare data for all strategies
        strategy_data = []
        for strategy_config in strategies:
            data = get_data(strategy_config["TICKER"], strategy_config, log)
            
            # Check if this is a MACD strategy by looking for SIGNAL_PERIOD
            if 'SIGNAL_PERIOD' in strategy_config:
                log(f"Processing MACD strategy with periods: {strategy_config['SHORT_WINDOW']}/{strategy_config['LONG_WINDOW']}/{strategy_config['SIGNAL_PERIOD']}")
                data = calculate_macd(
                    data,
                    short_window=strategy_config['SHORT_WINDOW'],
                    long_window=strategy_config['LONG_WINDOW'],
                    signal_window=strategy_config['SIGNAL_PERIOD']
                )
                data = calculate_macd_signals(data, strategy_config.get('SHORT', False))
                # Add Position column (shifted Signal) for MACD strategies
                data = data.with_columns([
                    pl.col("Signal").shift(1).fill_null(0).alias("Position")
                ])
            else:
                log(f"Processing MA cross strategy with windows: {strategy_config['SHORT_WINDOW']}/{strategy_config['LONG_WINDOW']}")
                data = calculate_ma_and_signals(
                    data, 
                    strategy_config['SHORT_WINDOW'], 
                    strategy_config['LONG_WINDOW'], 
                    strategy_config,
                    log
                )
            
            # Add expectancy per day to the strategy config
            portfolio = backtest_strategy(data, strategy_config, log)
            stats = convert_stats(portfolio.stats(), strategy_config)
            strategy_config['EXPECTANCY_PER_DAY'] = stats['Expectancy per Day']
            strategy_data.append(data)
        
        # Analyze concurrency across all strategies simultaneously
        stats, aligned_data = analyze_concurrency(
            strategy_data,
            strategies,
            log
        )
        
        log(f"Overall concurrency statistics:")
        log(f"Total concurrent periods: {stats['total_concurrent_periods']}")
        log(f"Concurrency Ratio: {stats['concurrency_ratio']:.2f}")
        log(f"Exclusive Ratio: {stats['exclusive_ratio']:.2f}")
        log(f"Inactive Ratio: {stats['inactive_ratio']:.2f}")
        log(f"Average concurrent strategies: {stats['avg_concurrent_strategies']:.2f}")
        log(f"Max concurrent strategies: {stats['max_concurrent_strategies']}")
        log(f"Risk Concentration Index: {stats['risk_concentration_index']}")
        log(f"Efficiency Score: {stats['efficiency_score']:.2f}")
        
        # Log risk metrics
        log(f"\nRisk Metrics:")
        for key, value in stats['risk_metrics'].items():
            if isinstance(value, float):
                log(f"{key}: {value:.4f}")
            else:
                log(f"{key}: {value}")
        
        # Create and display unified visualization
        fig = plot_concurrency(
            aligned_data,
            stats,
            strategies
        )
        fig.show()

        # Generate and save JSON report
        report = generate_json_report(strategies, stats, log)
        
        # Ensure the json/concurrency directory exists
        json_dir = Path("json/concurrency")
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the portfolio filename without extension
        portfolio_filename = Path(config["PORTFOLIO"]).stem
        report_filename = f"{portfolio_filename}.json"
        
        # Save the report
        report_path = json_dir / report_filename
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        log(f"JSON report saved to {report_path}")
        
        log("Unified concurrency analysis completed successfully")
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

# Default Configuration
config = {
    "PORTFOLIO": "current.csv",
    "BASE_DIR": ".",
    "REFRESH": True
}

if __name__ == "__main__":
    try:
        log, log_close, _, _ = setup_logging(
            module_name='concurrency',
            log_file='concurrency_analysis.log'
        )

        # Run unified analysis across all strategies
        portfolio_path = Path(__file__).parent / 'portfolios' / config["PORTFOLIO"]
        
        # Load portfolio from CSV
        strategies = load_portfolio_from_csv(portfolio_path, log, config)
        
        # Run unified analysis
        result = run(strategies, log, config)
        if result:
            print("Unified concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
