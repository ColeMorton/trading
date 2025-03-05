# Signal Value Metrics Integration Guide

This guide provides step-by-step instructions for integrating the signal value metrics into the existing concurrency analysis system.

## Overview

The signal value metrics provide additional insights into the quality and value of trading signals. These metrics go beyond basic quality metrics to provide deeper insights into signal performance, risk characteristics, and overall value.

## Step 1: Test the Signal Value Metrics

Before integrating the metrics into the main system, you can test them using the provided test script:

```bash
python -m app.concurrency.test_signal_value
```

This will generate sample data, calculate signal value metrics, and save them to a JSON file at `json/concurrency/signal_value_example.json`.

## Step 2: Modify the Analysis Module

To integrate the signal value metrics into the main analysis workflow, you'll need to modify the `app/concurrency/tools/analysis.py` file:

1. Add the import statements at the top of the file:

```python
from app.concurrency.tools.signal_value import (
    calculate_signal_value_metrics,
    integrate_signal_value_metrics
)
```

2. Modify the `compile_statistics` function to include signal value metrics:

```python
def compile_statistics(
    aligned_data: List[pl.DataFrame],
    position_metrics: Tuple[dict, float, int, int, int, int, float],
    risk_metrics: dict,
    efficiency_metrics: Tuple[float, float, float, float, float],
    signal_metrics: dict,
    signal_quality_metrics: dict,
    signal_value_metrics: dict,  # Add this parameter
    strategy_expectancies: List[float],
    strategy_efficiencies: List[Tuple[float, float, float, float]],
    log: Callable[[str, str], None]
) -> ConcurrencyStats:
    # ...existing code...
    
    stats = {
        # ...existing stats...
        "signal_metrics": signal_metrics,
        "signal_quality_metrics": signal_quality_metrics,
        "signal_value_metrics": signal_value_metrics,  # Add this line
        "start_date": str(aligned_data[0]["Date"].min()),
        "end_date": str(aligned_data[0]["Date"].max())
    }
    
    # ...rest of the function...
```

3. Add signal value metrics calculation to the `analyze_concurrency` function:

```python
def analyze_concurrency(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig],
    log: Callable[[str, str], None]
) -> Tuple[ConcurrencyStats, List[pl.DataFrame]]:
    # ...existing code...
    
    # After calculating signal quality metrics
    
    # Create signals and returns dataframes for signal value calculation
    signals_df_list = []
    returns_df_list = []
    for df in aligned_data:
        # Calculate returns from Close prices
        returns_df = df.select(["Date", "Close"]).with_columns(
            pl.col("Close").pct_change().alias("return")
        )
        
        # Create signals dataframe
        signals_df = df.select(["Date", "Position"]).with_columns(
            pl.col("Position").diff().alias("signal")
        )
        
        signals_df_list.append(signals_df)
        returns_df_list.append(returns_df)
    
    # Calculate signal value metrics
    log("Calculating signal value metrics", "info")
    signal_value_metrics = integrate_signal_value_metrics(
        signals_df_list=signals_df_list,
        returns_df_list=returns_df_list,
        risk_metrics=risk_metrics,
        log=log
    )
    
    # ...existing code...
    
    # Compile all statistics
    stats = compile_statistics(
        aligned_data,
        position_metrics,
        risk_metrics,
        efficiency_metrics,
        signal_metrics,
        signal_quality_metrics,
        signal_value_metrics,  # Add this parameter
        strategy_expectancies,
        strategy_efficiencies,
        log
    )
    
    # ...rest of the function...
    
    # In the exception handler, add signal value metrics to the default stats
    stats = {
        # ...existing default metrics...
        "signal_metrics": signal_metrics,
        "signal_quality_metrics": {},
        "signal_value_metrics": {},  # Add this line
        "start_date": "",
        "end_date": ""
    }
```

## Step 3: Update the Report Module

To include the signal value metrics in the JSON output, modify the `app/concurrency/tools/report.py` file:

1. Add a function to get metric descriptions:

```python
def get_signal_value_metric_description(metric_name: str) -> str:
    """Get description for a signal value metric.
    
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
```

2. Modify the `generate_strategy_data` function to include signal value metrics:

```python
def generate_strategy_data(
    strategy: StrategyConfig,
    stats: ConcurrencyStats,
    strategy_id: str,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    # ...existing code...
    
    # Add signal value metrics
    if "signal_value_metrics" in stats and strategy_id in stats["signal_value_metrics"]:
        strategy_data["signal_value"] = {}
        for metric_name, value in stats["signal_value_metrics"][strategy_id].items():
            strategy_data["signal_value"][metric_name] = {
                "value": value,
                "description": get_signal_value_metric_description(metric_name)
            }
    
    # ...rest of the function...
```

3. Modify the `generate_portfolio_metrics` function to include aggregate signal value metrics:

```python
def generate_portfolio_metrics(
    stats: ConcurrencyStats,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    # ...existing code...
    
    # Add aggregate signal value metrics
    if "signal_value_metrics" in stats and "aggregate" in stats["signal_value_metrics"]:
        portfolio_metrics["signal_value"] = {}
        for metric_name, value in stats["signal_value_metrics"]["aggregate"].items():
            portfolio_metrics["signal_value"][metric_name] = {
                "value": value,
                "description": get_signal_value_metric_description(metric_name)
            }
    
    # ...rest of the function...
```

## Step 4: Update the Types Module

To ensure type safety, update the `app/concurrency/tools/types.py` file to include signal value metrics in the `ConcurrencyStats` type:

```python
ConcurrencyStats = Dict[str, Any]  # Complex nested structure
# Or if you have a TypedDict:
class ConcurrencyStats(TypedDict):
    # ...existing fields...
    signal_metrics: Dict[str, Any]
    signal_quality_metrics: Dict[str, Dict[str, Any]]
    signal_value_metrics: Dict[str, Dict[str, Any]]  # Add this line
    # ...other fields...
```

## Step 5: Test the Integration

After making these changes, you can test the integration by running the concurrency analysis:

```bash
python -m app.concurrency.review
```

This will generate a JSON report that includes the new signal value metrics.

## Example Output

The signal value metrics will be added to the JSON output in the following format:

```json
{
    "strategies": [
        {
            "id": "strategy_1",
            "parameters": { ... },
            "performance": { ... },
            "risk_metrics": { ... },
            "efficiency": { ... },
            "signals": { ... },
            "signal_value": {
                "signal_risk_adjusted_value": {
                    "value": 0.85,
                    "description": "Value of each signal adjusted for risk"
                },
                "signal_contribution_ratio": {
                    "value": 0.0032,
                    "description": "How much each signal contributes to overall strategy performance"
                },
                // Additional metrics...
            },
            "allocation_score": 0.4,
            "allocation": 61.54
        },
        // Additional strategies...
    ],
    "portfolio_metrics": {
        // Other metrics...
        "signal_value": {
            "signal_risk_adjusted_value": {
                "value": 0.72,
                "description": "Portfolio-wide value of signals adjusted for risk"
            },
            // Additional aggregate metrics...
        }
    }
}
```

## Conclusion

By following these steps, you can integrate the signal value metrics into the existing concurrency analysis system. These metrics provide valuable insights into signal performance, risk characteristics, and overall value, helping traders make more informed decisions.

For more information on the signal value metrics, refer to the `signal_value_metrics_report.md` file.