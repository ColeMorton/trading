"""
Runner Module for Concurrency Analysis.

This module contains the main execution logic for running concurrency analysis
across multiple trading strategies.
"""

from typing import List, Callable
import json
from pathlib import Path
from app.tools.setup_logging import setup_logging
from app.concurrency.tools.types import StrategyConfig, ConcurrencyConfig
from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.visualization import plot_concurrency
from app.concurrency.tools.report import generate_json_report
from app.concurrency.tools.portfolio_loader import load_portfolio
from app.concurrency.tools.strategy_processor import process_strategies

def get_portfolio_path(config: ConcurrencyConfig) -> Path:
    """Get the full path to the portfolio file.

    Args:
        config (ConcurrencyConfig): Configuration dictionary containing PORTFOLIO path

    Returns:
        Path: Full path to the portfolio file (.json or .csv)
    """
    return Path(__file__).parent.parent / 'portfolios' / config["PORTFOLIO"]


def run_analysis(
    strategies: List[StrategyConfig], 
    log: Callable[[str, str], None],
    config: ConcurrencyConfig
) -> bool:
    """Run concurrency analysis across multiple strategies.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to analyze
        log: Callable for logging messages
        config: Configuration dictionary

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If analysis fails at any stage
    """
    try:
        # Process strategies and get data
        log("Processing strategy data", "info")
        strategy_data, updated_strategies = process_strategies(strategies, log)
        
        # Analyze concurrency
        log("Running concurrency analysis", "info")
        stats, aligned_data = analyze_concurrency(
            strategy_data,
            updated_strategies,
            log
        )
        
        # Log statistics
        log("Logging analysis statistics", "info")
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
        
        # Create visualization
        log("Creating visualization", "info")
        fig = plot_concurrency(
            aligned_data,
            stats,
            updated_strategies,
            log
        )
        fig.show()
        log("Visualization displayed", "info")

        # Generate and save JSON report
        log("Generating JSON report", "info")
        report = generate_json_report(updated_strategies, stats, log)
        
        # Ensure the json/concurrency directory exists
        json_dir = Path("json/concurrency")
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the portfolio filename without extension
        portfolio_filename = Path(config["PORTFOLIO"]).stem
        report_filename = f"{portfolio_filename}.json"
        
        # Save the report
        report_path = json_dir / report_filename
        log(f"Saving JSON report to {report_path}", "info")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4)
        
        log(f"JSON report saved to {report_path}", "info")
        log("Unified concurrency analysis completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        raise

def main(config: ConcurrencyConfig) -> bool:
    """Main entry point for concurrency analysis.

    Args:
        config (ConcurrencyConfig): Configuration dictionary containing PORTFOLIO path
            (supports both .json and .csv files)

    Returns:
        bool: True if analysis successful
    """
    try:
        log, log_close, _, _ = setup_logging(
            module_name='concurrency',
            log_file='concurrency_analysis.log'
        )

        log("Starting concurrency analysis", "info")
        
        # Load portfolio from JSON or CSV
        log("Loading portfolio configuration", "info")
        portfolio_path = get_portfolio_path(config)
        strategies = load_portfolio(portfolio_path, log, config)
        
        # Run analysis
        log("Running analysis", "info")
        result = run_analysis(strategies, log, config)
        
        log("Analysis completed", "info")
        log_close()
        return result
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
