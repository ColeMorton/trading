# Stop Loss Simulator Module

## Overview

The Stop Loss Simulator module provides functionality for simulating the effects of stop losses on signal returns and adjusting signal quality metrics accordingly. This module addresses the critical issue of ensuring consistent stop loss application across all metrics and providing comparative analysis between raw and stop-loss-adjusted metrics.

## Key Features

- **Stop Loss Simulation**: Apply stop losses to returns based on signals
- **Adjusted Metrics Calculation**: Calculate metrics adjusted for stop loss effects
- **Comparative Analysis**: Compare raw vs. stop-loss-adjusted metrics
- **Stop Loss Optimization**: Find the optimal stop loss level based on specified metrics
- **Signal Quality Integration**: Apply stop loss effects to signal quality metrics

## Usage

### Basic Usage

```python
from app.tools.stop_loss_simulator import (
    apply_stop_loss_to_returns,
    calculate_stop_loss_adjusted_metrics,
    compare_stop_loss_levels,
    find_optimal_stop_loss,
    apply_stop_loss_to_signal_quality_metrics
)

# Apply stop loss to returns
adjusted_returns, triggers = apply_stop_loss_to_returns(returns, signals, 0.05, log)

# Calculate stop loss adjusted metrics
metrics = calculate_stop_loss_adjusted_metrics(returns, signals, 0.05, log)

# Compare different stop loss levels
results = compare_stop_loss_levels(returns, signals, [0.03, 0.05, 0.10], log)

# Find optimal stop loss
optimal = find_optimal_stop_loss(returns, signals, (0.01, 0.20), 0.01, "adjusted_avg_return", log)

# Apply stop loss to signal quality metrics
adjusted_metrics = apply_stop_loss_to_signal_quality_metrics(metrics, returns, signals, 0.05, log)
```

### Integration with Signal Quality Metrics

The module integrates with the signal quality metrics calculation by providing an optional `stop_loss` parameter:

```python
from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics

# Calculate signal quality metrics with stop loss
metrics = calculate_signal_quality_metrics(
    signals_df, returns_df, strategy_id, log, stop_loss=0.05
)
```

### Stop Loss Simulation

The core functionality is the stop loss simulation, which applies stop losses to returns based on signals:

```python
adjusted_returns, triggers = apply_stop_loss_to_returns(returns, signals, 0.05, log)
```

This function simulates the effect of a stop loss by:

1. Tracking cumulative returns for each position
2. Triggering a stop loss when cumulative returns fall below the stop loss threshold
3. Adjusting returns at the trigger point to reflect the stop loss

### Adjusted Metrics Calculation

The module calculates a comprehensive set of metrics adjusted for stop loss effects:

```python
metrics = calculate_stop_loss_adjusted_metrics(returns, signals, 0.05, log)
```

This function calculates:

- Raw metrics (without stop loss)
- Adjusted metrics (with stop loss)
- Impact metrics (difference between raw and adjusted)
- Stop loss statistics (count, rate)

### Comparative Analysis

The module provides functionality for comparing different stop loss levels:

```python
results = compare_stop_loss_levels(returns, signals, [0.03, 0.05, 0.10], log)
```

This function calculates metrics for each stop loss level, allowing for easy comparison of the effects of different stop loss levels.

### Stop Loss Optimization

The module can find the optimal stop loss level based on a specified metric:

```python
optimal = find_optimal_stop_loss(
    returns, signals, (0.01, 0.20), 0.01, "adjusted_avg_return", log
)
```

This function tests a range of stop loss levels and selects the one that optimizes the specified metric.

## Implementation Details

### Stop Loss Simulation Algorithm

The stop loss simulation algorithm works as follows:

1. Create a position array from signals
2. Track cumulative returns for each position
3. Check if stop loss is triggered at each time step
4. Adjust returns at trigger points
5. Return adjusted returns and trigger points

### Metrics Calculation

The module calculates a comprehensive set of metrics:

- **Raw Metrics**: Metrics calculated without stop loss
- **Adjusted Metrics**: Metrics calculated with stop loss
- **Impact Metrics**: Difference between raw and adjusted metrics
- **Stop Loss Statistics**: Count and rate of stop loss triggers

### Signal Quality Integration

The module integrates with the signal quality metrics calculation by:

1. Calculating raw signal quality metrics
2. Applying stop loss to returns
3. Recalculating metrics with adjusted returns
4. Adding stop loss specific metrics
5. Adding raw vs. adjusted comparison

## Benefits

1. **Risk Management**: Better understanding of stop loss effects on strategy performance
2. **Realistic Metrics**: More accurate representation of real-world trading conditions
3. **Optimization**: Ability to find the optimal stop loss level for a strategy
4. **Consistency**: Ensures consistent stop loss application across all metrics
5. **Transparency**: Clear comparison between raw and stop-loss-adjusted metrics
