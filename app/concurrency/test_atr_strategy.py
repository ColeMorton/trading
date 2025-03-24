"""Test script for ATR Trailing Stop strategy in concurrency analysis.

This script demonstrates the ATR Trailing Stop strategy functionality
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
    module_name="test_atr_strategy",
    log_file="test_atr_strategy.log",
    level=logging.INFO
)

def main():
    """Run a test of the ATR Trailing Stop strategy functionality."""
    try:
        # Define test configuration
        test_config: ConcurrencyConfig = {
            "PORTFOLIO": "atr_test_portfolio.json",  # Use the ATR test portfolio
            "BASE_DIR": '.',  # Default to project root directory
            "REFRESH": True,
            "SL_CANDLE_CLOSE": True,
            "VISUALIZATION": False,  # Disable visualization for this test
            "RATIO_BASED_ALLOCATION": True,
            "CSV_USE_HOURLY": False
        }
        
        log("Starting ATR Trailing Stop strategy test", "info")
        
        # Run the analysis
        success = run_analysis(test_config)
        
        if not success:
            log("Analysis failed", "error")
            return False
        
        # Load the generated JSON file to display strategy metrics
        output_path = Path("json/concurrency/atr_test_portfolio_analysis.json")
        if not output_path.exists():
            log(f"Output file not found: {output_path}", "error")
            return False
        
        with open(output_path, "r") as f:
            results = json.load(f)
        
        # Display strategy metrics for each strategy
        log("Strategy Metrics:", "info")
        for strategy in results.get("strategies", []):
            strategy_id = strategy.get("id", "unknown")
            strategy_type = strategy.get("parameters", {}).get("type", {}).get("value", "unknown")
            
            log(f"\nStrategy: {strategy_id} (Type: {strategy_type})", "info")
            
            # Display allocation and metrics
            log(f"  Allocation: {strategy.get('allocation', 0):.2f}", "info")
            log(f"  Allocation Score: {strategy.get('allocation_score', 0):.2f}", "info")
            
            # Display risk metrics
            if "risk_metrics" in strategy:
                risk = strategy["risk_metrics"]
                log("  Risk Metrics:", "info")
                for key, metric in risk.items():
                    if isinstance(metric, dict) and "value" in metric:
                        log(f"    {key}: {metric['value']}", "info")
            
            # Display signal quality metrics if available
            if "signal_quality_metrics" in strategy:
                metrics = strategy["signal_quality_metrics"]
                log("  Signal Quality Metrics:", "info")
                log(f"    Signal Count: {metrics.get('signal_count', 0)}", "info")
                log(f"    Win Rate: {metrics.get('win_rate', 0):.2f}", "info")
                log(f"    Profit Factor: {metrics.get('profit_factor', 0):.2f}", "info")
                log(f"    Risk-Reward Ratio: {metrics.get('risk_reward_ratio', 0):.2f}", "info")
                log(f"    Expectancy Per Signal: {metrics.get('expectancy_per_signal', 0):.4f}", "info")
                log(f"    Signal Quality Score: {metrics.get('signal_quality_score', 0):.2f}", "info")
        
        # Display portfolio metrics
        log("\nPortfolio Metrics:", "info")
        if "portfolio_metrics" in results:
            portfolio = results["portfolio_metrics"]
            
            # Display concurrency metrics
            if "concurrency" in portfolio:
                concurrency = portfolio["concurrency"]
                log("  Concurrency Metrics:", "info")
                for key, metric in concurrency.items():
                    if isinstance(metric, dict) and "value" in metric:
                        log(f"    {key}: {metric['value']}", "info")
            
            # Display efficiency metrics
            if "efficiency" in portfolio:
                efficiency = portfolio["efficiency"]
                log("  Efficiency Metrics:", "info")
                for key, metric in efficiency.items():
                    if isinstance(metric, dict) and "value" in metric:
                        log(f"    {key}: {metric['value']}", "info")
        
        log("\nATR Trailing Stop strategy test completed successfully", "info")
        return True
        
    except Exception as e:
        log(f"Error in ATR strategy test: {str(e)}", "error")
        return False
    finally:
        log_close()

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)