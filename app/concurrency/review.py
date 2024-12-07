"""
Concurrency Analysis Module for Trading Strategies.

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure. Supports analysis of strategies with different
timeframes by resampling hourly data to daily when needed.
"""

from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.concurrency.tools.types import StrategyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.visualization import plot_concurrency

def run(config_1: StrategyConfig, config_2: StrategyConfig) -> bool:
    """Run concurrency analysis between two strategies.

    Performs a comprehensive analysis of concurrent positions between two
    trading strategies, including data preparation, analysis, and visualization.
    Handles different timeframes by resampling hourly data to daily when needed.

    Args:
        config_1 (StrategyConfig): Configuration for first strategy
        config_2 (StrategyConfig): Configuration for second strategy

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
        log(f"Starting concurrency analysis for {config_1['TICKER']} vs {config_2['TICKER']}")
        log(f"Strategy 1 timeframe: {'Hourly' if config_1.get('USE_HOURLY', False) else 'Daily'}")
        log(f"Strategy 2 timeframe: {'Hourly' if config_2.get('USE_HOURLY', False) else 'Daily'}")
        
        # Get and prepare data for both strategies
        data_1 = get_data(config_1["TICKER"], config_1)
        data_2 = get_data(config_2["TICKER"], config_2)
        
        # Calculate MAs and signals for both strategies
        data_1 = calculate_ma_and_signals(
            data_1, 
            config_1['SHORT_WINDOW'], 
            config_1['LONG_WINDOW'], 
            config_1
        )
        
        data_2 = calculate_ma_and_signals(
            data_2, 
            config_2['SHORT_WINDOW'], 
            config_2['LONG_WINDOW'], 
            config_2
        )
        
        # Analyze concurrency with timeframe handling
        stats, data_1_aligned, data_2_aligned = analyze_concurrency(
            data_1, 
            data_2,
            config_1,
            config_2
        )
        log(f"Concurrency analysis completed. Concurrent ratio: {stats['concurrency_ratio']:.2%}")
        
        # Create and display visualization
        fig = plot_concurrency(data_1_aligned, data_2_aligned, stats, config_1, config_2)
        fig.show()
        log("Visualization displayed successfully")
        
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
        result = run(strategy_1, strategy_2)
        if result:
            print("Concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
