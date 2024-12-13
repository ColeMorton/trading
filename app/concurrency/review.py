"""
Concurrency Analysis Module for Trading Strategies.

This module analyzes the concurrent exposure between multiple trading strategies.
It identifies periods of overlapping positions and calculates key statistics
about the concurrent exposure. Supports analysis of strategies with different
timeframes by resampling hourly data to daily when needed.
"""

from typing import List, Dict, Any
import json
from pathlib import Path
from app.tools.setup_logging import setup_logging
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.concurrency.tools.types import StrategyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.visualization import plot_concurrency
from app.tools.backtest_strategy import backtest_strategy
from app.tools.file_utils import convert_stats
from app.concurrency.portfolios.current_daily import portfolio
import polars as pl

def generate_json_report(
    strategies: List[StrategyConfig], 
    stats: Dict[str, Any], 
    log: callable
) -> Dict[str, Any]:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (callable): Logging function

    Returns:
        Dict[str, Any]: Complete report in dictionary format
    """
    report = {
        "strategies": [],
        "metrics": {
            "concurrency": {
                "total_concurrent_periods": stats['total_concurrent_periods'],
                "concurrency_ratio": stats['concurrency_ratio'],
                "exclusive_ratio": stats['exclusive_ratio'],
                "inactive_ratio": stats['inactive_ratio'],
                "avg_concurrent_strategies": stats['avg_concurrent_strategies'],
                "max_concurrent_strategies": stats['max_concurrent_strategies']
            },
            "efficiency": {
                "efficiency_score": stats['efficiency_score'],
                "total_expectancy": stats['total_expectancy'],
                "diversification_multiplier": stats['diversification_multiplier'],
                "independence_multiplier": stats['independence_multiplier'],
                "activity_multiplier": stats['activity_multiplier']
            },
            "risk": {
                "risk_concentration_index": stats['risk_concentration_index'],
                **stats['risk_metrics']
            }
        }
    }

    # Add strategy details
    for strategy in strategies:
        strategy_info = {
            "ticker": strategy["TICKER"],
            "timeframe": "Hourly" if strategy.get("USE_HOURLY", False) else "Daily",
            "expectancy_per_day": strategy.get("EXPECTANCY_PER_DAY", 0),
        }
        
        # Add strategy-specific parameters
        if "SIGNAL_PERIOD" in strategy:
            strategy_info.update({
                "type": "MACD",
                "short_window": strategy["SHORT_WINDOW"],
                "long_window": strategy["LONG_WINDOW"],
                "signal_period": strategy["SIGNAL_PERIOD"]
            })
        else:
            # Determine if it's EMA or SMA Cross
            ma_type = "EMA Cross" if strategy.get("USE_EMA", True) else "SMA Cross"
            strategy_info.update({
                "type": ma_type,
                "short_window": strategy["SHORT_WINDOW"],
                "long_window": strategy["LONG_WINDOW"]
            })
        
        report["strategies"].append(strategy_info)

    return report
    
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
            data = get_data(config["TICKER"], config, log)
            
            # Check if this is a MACD strategy by looking for SIGNAL_PERIOD
            if 'SIGNAL_PERIOD' in config:
                log(f"Processing MACD strategy with periods: {config['SHORT_WINDOW']}/{config['LONG_WINDOW']}/{config['SIGNAL_PERIOD']}")
                data = calculate_macd(
                    data,
                    short_window=config['SHORT_WINDOW'],
                    long_window=config['LONG_WINDOW'],
                    signal_window=config['SIGNAL_PERIOD']
                )
                data = calculate_macd_signals(data, config.get('SHORT', False))
                # Add Position column (shifted Signal) for MACD strategies
                data = data.with_columns([
                    pl.col("Signal").shift(1).fill_null(0).alias("Position")
                ])
            else:
                log(f"Processing MA cross strategy with windows: {config['SHORT_WINDOW']}/{config['LONG_WINDOW']}")
                data = calculate_ma_and_signals(
                    data, 
                    config['SHORT_WINDOW'], 
                    config['LONG_WINDOW'], 
                    config,
                    log
                )
            
            # Add expectancy per day to the strategy config
            portfolio = backtest_strategy(data, config, log)
            stats = convert_stats(portfolio.stats(), config)
            config['EXPECTANCY_PER_DAY'] = stats['Expectancy per Day']
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
        
        # Save the report
        report_path = json_dir / "concurrency_report.json"
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

if __name__ == "__main__":
    try:
        # Run unified analysis across all strategies
        result = run(portfolio)
        if result:
            print("Unified concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
