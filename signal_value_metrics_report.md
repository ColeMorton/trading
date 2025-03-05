# Signal Value Metrics Report

## Overview

This report outlines additional metrics that can be integrated into the concurrency analysis system to better quantify the value of trading signals. These metrics go beyond basic quality metrics to provide deeper insights into signal performance, risk characteristics, and overall value.

## Implemented Signal Value Metrics

The `signal_value.py` module implements the following metrics:

### 1. Signal Risk-Adjusted Value (SRAV)
- **Description**: Measures the value of each signal adjusted for risk
- **Calculation**: Average signal return divided by Value at Risk (95%)
- **Interpretation**: Higher values indicate signals that generate better returns relative to their risk
- **Use case**: Identify signals that provide the best risk-adjusted performance

### 2. Signal Contribution Ratio (SCR)
- **Description**: Measures how much each signal contributes to overall strategy performance
- **Calculation**: Total return divided by signal count
- **Interpretation**: Higher values indicate more impactful signals
- **Use case**: Identify which signals are most valuable to the strategy

### 3. Signal Efficiency Ratio (SER)
- **Description**: Measures how efficiently signals capture available market movements
- **Calculation**: (Win Rate × Average Win) ÷ ((1 - Win Rate) × |Average Loss|)
- **Interpretation**: Higher values indicate more efficient signals
- **Use case**: Evaluate signal efficiency in capturing market movements

### 4. Signal Risk Contribution (SRC)
- **Description**: Measures how much each signal contributes to portfolio risk
- **Calculation**: Strategy risk contribution divided by signal count
- **Interpretation**: Lower values indicate signals with less risk impact
- **Use case**: Identify signals that add minimal risk to the portfolio

### 5. Signal Tail Risk Exposure (STRE)
- **Description**: Measures exposure to tail risk events per signal
- **Calculation**: Conditional Value at Risk (95%) divided by signal count
- **Interpretation**: Lower values indicate signals with less tail risk
- **Use case**: Evaluate signal vulnerability to extreme market events

### 6. Signal Consistency Score (SCS)
- **Description**: Measures consistency of signal performance over time
- **Calculation**: 1 ÷ (1 + Standard deviation of rolling returns)
- **Interpretation**: Higher values indicate more consistent signals
- **Use case**: Identify signals with stable performance characteristics

### 7. Signal Information Ratio (SIR)
- **Description**: Measures excess return per unit of risk
- **Calculation**: Average return divided by return volatility
- **Interpretation**: Higher values indicate better risk-adjusted returns
- **Use case**: Compare signal quality across different market conditions

### 8. Signal Market Impact (SMI)
- **Description**: Estimate of market impact cost per signal
- **Calculation**: Simplified model based on average absolute return
- **Interpretation**: Lower values indicate signals with less market impact
- **Use case**: Estimate transaction costs associated with signals

### 9. Signal Opportunity Score (SOS)
- **Description**: Composite score of signal value considering multiple factors
- **Calculation**: Weighted combination of multiple metrics
- **Interpretation**: Higher values (0-10 scale) indicate more valuable signals
- **Use case**: Overall ranking of signal quality

### 10. Signal Expected Value (SEV)
- **Description**: Expected monetary value of each signal
- **Calculation**: (Win Rate × Average Win) - ((1 - Win Rate) × |Average Loss|)
- **Interpretation**: Higher values indicate more profitable signals
- **Use case**: Direct measure of signal profitability

## Integration with Existing System

To integrate these metrics into the existing concurrency analysis system, the following steps would be required:

1. **Import the signal_value module** in analysis.py:
   ```python
   from app.concurrency.tools.signal_value import (
       calculate_signal_value_metrics,
       integrate_signal_value_metrics
   )
   ```

2. **Modify the compile_statistics function** to include signal value metrics:
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
   ```

3. **Add signal value metrics to the stats dictionary**:
   ```python
   stats = {
       # Existing metrics...
       "signal_metrics": signal_metrics,
       "signal_quality_metrics": signal_quality_metrics,
       "signal_value_metrics": signal_value_metrics,  # Add this line
       "start_date": str(aligned_data[0]["Date"].min()),
       "end_date": str(aligned_data[0]["Date"].max())
   }
   ```

4. **Calculate signal value metrics** in the analyze_concurrency function:
   ```python
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
   ```

5. **Pass signal value metrics to compile_statistics**:
   ```python
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
   ```

6. **Add signal value metrics to the default stats** in case of error:
   ```python
   stats = {
       # Existing default metrics...
       "signal_metrics": signal_metrics,
       "signal_quality_metrics": {},
       "signal_value_metrics": {},  # Add this line
       "start_date": "",
       "end_date": ""
   }
   ```

7. **Update the report.py file** to include signal value metrics in the JSON output:
   ```python
   # Add signal value metrics to strategy data
   if "signal_value_metrics" in stats and strategy_id in stats["signal_value_metrics"]:
       strategy_data["signal_value"] = {}
       for metric_name, value in stats["signal_value_metrics"][strategy_id].items():
           strategy_data["signal_value"][metric_name] = {
               "value": value,
               "description": get_metric_description(metric_name)
           }
   ```

## Example JSON Output

The signal value metrics would be added to the JSON output in the following format:

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
                "signal_efficiency_ratio": {
                    "value": 2.75,
                    "description": "How efficiently signals capture available market movements"
                },
                "signal_risk_contribution": {
                    "value": 0.0029,
                    "description": "How much each signal contributes to portfolio risk"
                },
                "signal_tail_risk_exposure": {
                    "value": 0.00043,
                    "description": "Exposure to tail risk events per signal"
                },
                "signal_consistency_score": {
                    "value": 0.78,
                    "description": "Consistency of signal performance over time"
                },
                "signal_information_ratio": {
                    "value": 0.65,
                    "description": "Excess return per unit of risk"
                },
                "signal_market_impact": {
                    "value": 0.00015,
                    "description": "Estimate of market impact cost per signal"
                },
                "signal_opportunity_score": {
                    "value": 7.2,
                    "description": "Composite score of signal value (0-10 scale)"
                },
                "signal_expected_value": {
                    "value": 0.0025,
                    "description": "Expected monetary value of each signal"
                }
            },
            "allocation_score": 0.4,
            "allocation": 61.54
        },
        // Additional strategies...
    ],
    "ticker_metrics": { ... },
    "portfolio_metrics": {
        "concurrency": { ... },
        "efficiency": { ... },
        "risk": { ... },
        "signals": { ... },
        "signal_value": {
            "signal_risk_adjusted_value": {
                "value": 0.72,
                "description": "Portfolio-wide value of signals adjusted for risk"
            },
            "signal_contribution_ratio": {
                "value": 0.0028,
                "description": "Average contribution of signals to portfolio performance"
            },
            // Additional aggregate metrics...
        }
    }
}
```

## Benefits of Signal Value Metrics

1. **Deeper Signal Analysis**: These metrics provide a more comprehensive understanding of signal quality and value.

2. **Risk-Adjusted Evaluation**: Metrics like SRAV and SRC help evaluate signals in the context of their risk contribution.

3. **Efficiency Assessment**: Metrics like SER and SIR help identify which signals are most efficient at capturing market opportunities.

4. **Consistency Measurement**: The SCS metric helps identify signals with stable performance characteristics.

5. **Composite Scoring**: The Signal Opportunity Score provides an overall ranking of signal quality.

6. **Expected Value**: The SEV metric provides a direct measure of signal profitability.

## Conclusion

The signal value metrics implemented in the `signal_value.py` module provide a comprehensive framework for quantifying the value of trading signals. By integrating these metrics into the existing concurrency analysis system, traders can gain deeper insights into signal performance, risk characteristics, and overall value.

These metrics can help traders make more informed decisions about which signals to prioritize, which strategies to allocate more capital to, and how to optimize their overall trading approach.