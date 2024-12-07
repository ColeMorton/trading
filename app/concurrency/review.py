"""
Concurrency Analysis Module for Trading Strategies.

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure. Supports analysis of strategies with different
timeframes by resampling hourly data to daily when needed.
"""

from typing import List
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.concurrency.tools.types import StrategyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.visualization import plot_concurrency

def run(strategies: List[StrategyConfig]) -> bool:
    """Run concurrency analysis across multiple strategies.

    Performs a comprehensive analysis of concurrent positions across all
    provided trading strategies simultaneously, including data preparation,
    analysis, and visualization. Handles different timeframes by resampling
    hourly data to daily when needed.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to analyze

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If analysis fails at any stage
    """
    log, log_close, _, _ = setup_logging(
        module_name='concurrency',
        log_file='concurrency_analysis.log'
    )
    
    try:
        if len(strategies) < 2:
            raise ValueError("At least two strategies are required for concurrency analysis")
            
        log(f"Starting unified concurrency analysis across {len(strategies)} strategies")
        for i, config in enumerate(strategies, 1):
            log(f"Strategy {i} - {config['TICKER']}: {'Hourly' if config.get('USE_HOURLY', False) else 'Daily'}")
        
        # Get and prepare data for all strategies
        strategy_data = []
        for config in strategies:
            data = get_data(config["TICKER"], config)
            data = calculate_ma_and_signals(
                data, 
                config['SHORT_WINDOW'], 
                config['LONG_WINDOW'], 
                config
            )
            strategy_data.append(data)
        
        # Analyze concurrency across all strategies simultaneously
        stats, aligned_data = analyze_concurrency(
            strategy_data,
            strategies
        )
        
        log(f"Overall concurrency statistics:")
        log(f"Total concurrent periods: {stats['total_concurrent_periods']}")
        log(f"Average concurrent strategies: {stats['avg_concurrent_strategies']:.2f}")
        log(f"Max concurrent strategies: {stats['max_concurrent_strategies']}")
        
        # Create and display unified visualization
        fig = plot_concurrency(
            aligned_data,
            stats,
            strategies
        )
        fig.show()
        
        log("Unified concurrency analysis completed successfully")
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    # Example configurations
    strategy_1: StrategyConfig = {
        "TICKER": "BTC-USD",
        "SHORT_WINDOW": 27,
        "LONG_WINDOW": 29,
        "BASE_DIR": ".",
        "USE_SMA": True,
        "REFRESH": True,
        "USE_RSI": True,
        "RSI_PERIOD": 14,
        "RSI_THRESHOLD": 50,
        "STOP_LOSS": 0.0911
    }

    strategy_2: StrategyConfig = {
        "TICKER": "BTC-USD",
        "SHORT_WINDOW": 65,
        "LONG_WINDOW": 74,
        "BASE_DIR": ".",
        "USE_SMA": True,
        "USE_HOURLY": True,
        "REFRESH": True,
        "USE_RSI": True,
        "RSI_PERIOD": 29,
        "RSI_THRESHOLD": 30,
        "STOP_LOSS": 0.0565
    }

    strategy_3: StrategyConfig = {
        "TICKER": "SOL-USD",
        "SHORT_WINDOW": 14,
        "LONG_WINDOW": 32,
        "BASE_DIR": ".",
        "USE_SMA": True,
        "REFRESH": True,
        "USE_RSI": True,
        "RSI_PERIOD": 26,
        "RSI_THRESHOLD": 43,
        "STOP_LOSS": 0.125
    }

    try:
        # Run unified analysis across all strategies
        result = run([strategy_1, strategy_2, strategy_3])
        if result:
            print("Unified concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
