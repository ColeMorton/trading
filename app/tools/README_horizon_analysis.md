# Horizon Analysis Methodology

## Overview

The Horizon Analysis module provides a framework for evaluating signal performance across different time horizons without introducing forward-looking bias. This is crucial for accurate strategy evaluation and optimization.

## Key Features

- **Bias-Free Evaluation**: Ensures that signals are evaluated using only data that would have been available at the time of the signal
- **Position-Based Analysis**: Evaluates positions (which are derived from signals) rather than signals directly
- **Multiple Horizons**: Analyzes performance across different time horizons (1, 3, 5, 10 days)
- **Statistical Significance**: Considers sample size when selecting the optimal horizon
- **Comprehensive Metrics**: Calculates win rate, average return, and risk-adjusted returns for each horizon

## Implementation Details

### Signal to Position Conversion

The first step in horizon analysis is converting signals to positions:

```python
# A position at time t is determined by the signal at time t-1
positions = np.zeros_like(signals)
for i in range(1, len(signals)):
    if signals[i-1] != 0:
        positions[i] = signals[i-1]
```

This ensures that positions are only established after signals are generated, avoiding look-ahead bias.

### Horizon Return Calculation

For each position, returns are calculated over the specified horizon:

```python
# For each position, calculate the return over the specified horizon
for i in range(len(positions) - horizon):
    if positions[i] != 0:  # If there's an active position
        # Calculate return over the horizon
        if positions[i] > 0:  # Long position
            horizon_return = np.sum(returns[i:i+horizon])
        else:  # Short position
            horizon_return = -np.sum(returns[i:i+horizon])
        
        horizon_returns.append(horizon_return)
```

For long positions, positive returns are favorable. For short positions, negative returns are favorable (hence the negation).

### Best Horizon Selection

The best horizon is selected based on multiple criteria:

```python
# Calculate a combined score that considers multiple factors
sample_size_factor = min(1.0, sample_size / 100)  # Cap at 100 samples
combined_score = (0.6 * sharpe) + (0.3 * win_rate) + (0.1 * sample_size_factor)
```

This approach balances:
- Risk-adjusted returns (Sharpe ratio)
- Consistency (win rate)
- Statistical significance (sample size)

## Usage

### Basic Horizon Analysis

```python
from app.concurrency.tools.signal_quality import _calculate_horizon_metrics, _find_best_horizon

# Calculate horizon metrics
horizon_metrics = _calculate_horizon_metrics(signals, returns)

# Find the best horizon
best_horizon = _find_best_horizon(horizon_metrics)

# Access metrics for a specific horizon
horizon_3_metrics = horizon_metrics.get("3", {})
win_rate = horizon_3_metrics.get("win_rate", 0)
```

### Integration with Signal Quality Metrics

The horizon analysis is automatically included in the signal quality metrics:

```python
from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics

# Calculate signal quality metrics
metrics = calculate_signal_quality_metrics(signals_df, returns_df, strategy_id, log)

# Access horizon metrics
horizon_metrics = metrics.get("horizon_metrics", {})
best_horizon = metrics.get("best_horizon")
```

## Benefits

1. **Accurate Evaluation**: Eliminates forward-looking bias for more realistic performance assessment
2. **Optimal Holding Period**: Identifies the most effective time horizon for each strategy
3. **Strategy Comparison**: Provides a standardized framework for comparing strategies across different time horizons
4. **Risk Management**: Helps understand how strategy performance varies over different holding periods

## Implementation Notes

- The horizon analysis is implemented in `app/concurrency/tools/signal_quality.py`
- Unit tests are available in `app/tools/tests/test_horizon_analysis.py`
- The methodology follows best practices for out-of-sample testing