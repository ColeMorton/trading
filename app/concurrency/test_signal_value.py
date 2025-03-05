"""
Test script for signal value metrics.

This script demonstrates how to use the signal_value.py module to calculate
signal value metrics for a sample strategy.
"""

import polars as pl
import numpy as np
from pathlib import Path
import json
from typing import Dict, Any, Callable

from app.tools.setup_logging import setup_logging
from app.concurrency.tools.signal_value import (
    calculate_signal_value_metrics,
    calculate_aggregate_signal_value
)

def create_sample_data() -> tuple:
    """Create sample data for testing signal value metrics.
    
    Returns:
        tuple: (signals_df, returns_df, risk_metrics)
    """
    # Create date range
    dates = pl.date_range(
        start=pl.date(2023, 1, 1),
        end=pl.date(2023, 12, 31),
        interval="1d"
    )
    
    # Create sample position data (1 for long, 0 for no position)
    np.random.seed(42)  # For reproducibility
    positions = np.zeros(len(dates))
    
    # Create some random entry/exit points
    for i in range(10, len(dates), 20):
        if i + 10 < len(dates):
            positions[i:i+10] = 1
    
    # Create signals from position changes
    signals = np.diff(positions, prepend=0)
    
    # Create sample returns data
    returns = np.random.normal(0.001, 0.02, len(dates))
    
    # Make returns slightly positive when in position
    returns[positions == 1] = returns[positions == 1] + 0.005
    
    # Create signals dataframe
    signals_df = pl.DataFrame({
        "Date": dates,
        "Position": positions,
        "signal": signals
    })
    
    # Create returns dataframe
    returns_df = pl.DataFrame({
        "Date": dates,
        "return": returns
    })
    
    # Create sample risk metrics
    risk_metrics = {
        "strategy_1_var_95": -0.05,
        "strategy_1_cvar_95": -0.07,
        "strategy_1_risk_contrib": 0.5,
        "strategy_1_alpha": 0.0002
    }
    
    return signals_df, returns_df, risk_metrics

def print_metrics(metrics: Dict[str, Any]) -> None:
    """Print metrics in a formatted way.
    
    Args:
        metrics (Dict[str, Any]): Metrics dictionary
    """
    print("\nSignal Value Metrics:")
    print("=" * 50)
    
    for name, value in metrics.items():
        print(f"{name.replace('_', ' ').title()}: {value:.4f}")

def save_metrics_to_json(metrics: Dict[str, Any], filepath: str) -> None:
    """Save metrics to a JSON file.
    
    Args:
        metrics (Dict[str, Any]): Metrics dictionary
        filepath (str): Path to save the JSON file
    """
    # Create formatted metrics with descriptions
    formatted_metrics = {}
    
    for name, value in metrics.items():
        formatted_metrics[name] = {
            "value": value,
            "description": get_metric_description(name)
        }
    
    # Create output directory if it doesn't exist
    output_dir = Path(filepath).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to JSON
    with open(filepath, 'w') as f:
        json.dump(formatted_metrics, f, indent=4)
    
    print(f"\nMetrics saved to {filepath}")

def get_metric_description(metric_name: str) -> str:
    """Get description for a metric.
    
    Args:
        metric_name (str): Metric name
        
    Returns:
        str: Metric description
    """
    descriptions = {
        "signal_risk_adjusted_value": "Value of each signal adjusted for risk",
        "signal_contribution_ratio": "How much each signal contributes to overall strategy performance",
        "signal_efficiency_ratio": "How efficiently signals capture available market movements",
        "signal_risk_contribution": "How much each signal contributes to portfolio risk",
        "signal_tail_risk_exposure": "Exposure to tail risk events per signal",
        "signal_consistency_score": "Consistency of signal performance over time",
        "signal_information_ratio": "Excess return per unit of risk",
        "signal_market_impact": "Estimate of market impact cost per signal",
        "signal_opportunity_score": "Composite score of signal value (0-10 scale)",
        "signal_expected_value": "Expected monetary value of each signal"
    }
    
    return descriptions.get(metric_name, "No description available")

def main() -> None:
    """Main function to test signal value metrics."""
    # Setup logging
    log, log_close, _, _ = setup_logging(
        module_name="test_signal_value",
        log_file="test_signal_value.log"
    )
    
    try:
        log("Creating sample data", "info")
        signals_df, returns_df, risk_metrics = create_sample_data()
        
        log("Calculating signal value metrics", "info")
        metrics = calculate_signal_value_metrics(
            signals_df=signals_df,
            returns_df=returns_df,
            risk_metrics=risk_metrics,
            strategy_id="strategy_1",
            log=log
        )
        
        if metrics:
            print_metrics(metrics)
            
            # Save metrics to JSON
            save_metrics_to_json(
                metrics=metrics,
                filepath="json/concurrency/signal_value_example.json"
            )
            
            log("Signal value metrics calculated successfully", "info")
        else:
            log("No metrics calculated", "warning")
        
        # Test aggregate metrics
        log("Testing aggregate metrics calculation", "info")
        
        # Create a second strategy with different metrics
        np.random.seed(43)  # Different seed
        signals_df2, returns_df2, risk_metrics2 = create_sample_data()
        
        metrics2 = calculate_signal_value_metrics(
            signals_df=signals_df2,
            returns_df=returns_df2,
            risk_metrics=risk_metrics,
            strategy_id="strategy_2",
            log=log
        )
        
        # Calculate aggregate metrics
        strategy_metrics = {
            "strategy_1": {**metrics, "signal_count": 36},
            "strategy_2": {**metrics2, "signal_count": 42}
        }
        
        aggregate_metrics = calculate_aggregate_signal_value(
            strategy_metrics=strategy_metrics,
            log=log
        )
        
        if aggregate_metrics:
            print("\nAggregate Signal Value Metrics:")
            print("=" * 50)
            for name, value in aggregate_metrics.items():
                print(f"{name.replace('_', ' ').title()}: {value:.4f}")
            
            log("Aggregate metrics calculated successfully", "info")
        else:
            log("No aggregate metrics calculated", "warning")
        
        log("Test completed successfully", "info")
        
    except Exception as e:
        log(f"Error: {str(e)}", "error")
    finally:
        log_close()

if __name__ == "__main__":
    main()