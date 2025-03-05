"""Test script for signal quality metrics in concurrency analysis.

This script demonstrates the new signal quality metrics functionality
by running a concurrency analysis on a sample portfolio and displaying
the results.
"""

import sys
import json
from pathlib import Path
import logging

from app.concurrency.review import run_analysis
from app.concurrency.config import ConcurrencyConfig
from app.tools.setup_logging import setup_logging

# Configure logging
log, log_close, _, _ = setup_logging(
    module_name="test_signal_quality",
    log_file="test_signal_quality.log",
    level=logging.INFO
)

def main():
    """Run a test of the signal quality metrics functionality."""
    try:
        # Define test configuration
        test_config: ConcurrencyConfig = {
            "PORTFOLIO": "json/concurrency/macd_test.json",  # Use the example portfolio
            "BASE_DIR": '.',  # Default to project root directory
            "REFRESH": True,
            "SL_CANDLE_CLOSE": True,
            "VISUALIZATION": False,  # Disable visualization for this test
            "RATIO_BASED_ALLOCATION": True,
            "CSV_USE_HOURLY": False
        }
        
        log("Starting signal quality metrics test", "info")
        
        # Run the analysis
        success = run_analysis(test_config)
        
        if not success:
            log("Analysis failed", "error")
            return False
        
        # Load the generated JSON file to display signal quality metrics
        output_path = Path("json/concurrency/macd_test_analysis.json")
        if not output_path.exists():
            log(f"Output file not found: {output_path}", "error")
            return False
        
        with open(output_path, "r") as f:
            results = json.load(f)
        
        # Display signal quality metrics for each strategy
        log("Signal Quality Metrics by Strategy:", "info")
        for strategy in results.get("strategies", []):
            strategy_id = strategy.get("id", "unknown")
            log(f"\nStrategy: {strategy_id}", "info")
            
            if "signal_quality_metrics" in strategy:
                metrics = strategy["signal_quality_metrics"]
                log(f"  Signal Count: {metrics.get('signal_count', 0)}", "info")
                log(f"  Win Rate: {metrics.get('win_rate', 0):.2f}", "info")
                log(f"  Profit Factor: {metrics.get('profit_factor', 0):.2f}", "info")
                log(f"  Risk-Reward Ratio: {metrics.get('risk_reward_ratio', 0):.2f}", "info")
                log(f"  Expectancy Per Signal: {metrics.get('expectancy_per_signal', 0):.4f}", "info")
                log(f"  Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}", "info")
                log(f"  Sortino Ratio: {metrics.get('sortino_ratio', 0):.2f}", "info")
                log(f"  Signal Efficiency: {metrics.get('signal_efficiency', 0):.2f}", "info")
                log(f"  Signal Quality Score: {metrics.get('signal_quality_score', 0):.2f}", "info")
                
                if "best_horizon" in metrics:
                    log(f"  Best Horizon: {metrics['best_horizon']} periods", "info")
            else:
                log("  No signal quality metrics available", "warning")
        
        # Display aggregate signal quality metrics
        log("\nAggregate Signal Quality Metrics:", "info")
        if "portfolio_metrics" in results and "signal_quality" in results["portfolio_metrics"]:
            agg_metrics = results["portfolio_metrics"]["signal_quality"]
            for key, metric in agg_metrics.items():
                if isinstance(metric, dict) and "value" in metric:
                    log(f"  {key}: {metric['value']}", "info")
        else:
            log("  No aggregate signal quality metrics available", "warning")
        
        log("\nSignal quality metrics test completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Error in signal quality metrics test: {str(e)}", "error")
        return False
    finally:
        log_close()

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)