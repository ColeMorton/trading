# Signal Metrics Module

## Overview

The Signal Metrics module provides a standardized framework for calculating signal metrics, combining frequency, distribution, and quality metrics in a consistent manner. This module addresses the critical issue of inconsistent signal metrics calculation across different parts of the system.

## Key Features

- **Unified Framework**: Combines functionality from multiple existing modules
- **Consistent Methodology**: Ensures metrics are calculated the same way everywhere
- **Comprehensive Metrics**: Includes frequency, distribution, and quality metrics
- **Backward Compatibility**: Provides legacy functions for seamless integration
- **Extensible Design**: Easy to add new metrics or modify existing ones

## Usage

### Basic Usage

```python
from app.tools.signal_metrics import SignalMetrics

# Create a SignalMetrics instance
metrics = SignalMetrics(log)

# Calculate frequency metrics
frequency_metrics = metrics.calculate_frequency_metrics(data, signal_column="Signal", date_column="Date")

# Calculate quality metrics
quality_metrics = metrics.calculate_quality_metrics(signals_df, returns_df, "strategy_id")

# Calculate portfolio metrics
portfolio_metrics = metrics.calculate_portfolio_metrics(data_list, strategy_ids)
```

### Frequency Metrics

Frequency metrics analyze how often signals occur and their distribution over time:

```python
frequency_metrics = metrics.calculate_frequency_metrics(data)

# Access metrics
mean_signals = frequency_metrics["mean_signals_per_month"]
signal_volatility = frequency_metrics["signal_volatility"]
total_signals = frequency_metrics["total_signals"]
signal_consistency = frequency_metrics["signal_consistency"]
```

### Quality Metrics

Quality metrics evaluate the effectiveness and reliability of signals:

```python
quality_metrics = metrics.calculate_quality_metrics(signals_df, returns_df, "strategy_id")

# Access metrics
win_rate = quality_metrics["win_rate"]
profit_factor = quality_metrics["profit_factor"]
expectancy = quality_metrics["expectancy_per_signal"]
quality_score = quality_metrics["signal_quality_score"]
```

### Horizon Analysis

Horizon analysis evaluates signal performance across different time horizons:

```python
# Horizon metrics are included in quality metrics
horizon_metrics = quality_metrics["horizon_metrics"]
best_horizon = quality_metrics["best_horizon"]

# Access metrics for a specific horizon
horizon_3_metrics = horizon_metrics.get("3", {})
win_rate_h3 = horizon_3_metrics.get("win_rate", 0)
```

### Portfolio Metrics

Portfolio metrics analyze signals across multiple strategies:

```python
portfolio_metrics = metrics.calculate_portfolio_metrics(data_list, strategy_ids)

# Access strategy-specific metrics
strategy1_signals = portfolio_metrics["strategy_1_total_signals"]

# Access portfolio-level metrics
portfolio_signals = portfolio_metrics["portfolio_total_signals"]
```

### Legacy Functions

For backward compatibility, the module provides legacy functions:

```python
from app.tools.signal_metrics import calculate_signal_metrics, calculate_signal_quality_metrics

# Calculate signal metrics (legacy)
metrics = calculate_signal_metrics(aligned_data, log)

# Calculate signal quality metrics (legacy)
quality_metrics = calculate_signal_quality_metrics(signals_df, returns_df, "strategy_id", log)
```

## Key Metrics

### Frequency Metrics

- **mean_signals_per_month**: Average number of signals per month
- **signal_volatility**: Standard deviation of monthly signal counts
- **signal_consistency**: Consistency of signal frequency (1 - normalized volatility)
- **signal_density**: Signals per trading day

### Quality Metrics

- **win_rate**: Percentage of signals that result in positive returns
- **profit_factor**: Sum of positive returns divided by sum of negative returns
- **expectancy_per_signal**: Expected return per signal
- **risk_reward_ratio**: Average win divided by average loss
- **signal_quality_score**: Overall quality score (0-10 scale)

### Horizon Metrics

- **avg_return**: Average return over the horizon
- **win_rate**: Percentage of positive returns over the horizon
- **sharpe**: Risk-adjusted return over the horizon
- **sample_size**: Number of samples for statistical significance

## Implementation Details

The module is implemented as a class-based design with the following components:

- **SignalMetrics**: Main class for calculating all metrics
- **calculate_frequency_metrics**: Method for calculating frequency metrics
- **calculate_quality_metrics**: Method for calculating quality metrics
- **calculate_portfolio_metrics**: Method for calculating portfolio-level metrics
- **_calculate_horizon_metrics**: Helper method for horizon analysis
- **_find_best_horizon**: Helper method for selecting the best horizon

## Benefits

1. **Consistency**: Same calculation methodology used throughout the system
2. **Maintainability**: Single source of truth for signal metrics calculations
3. **Extensibility**: Easy to add new metrics or modify existing ones
4. **Transparency**: Clear documentation of calculation methodology
5. **Reliability**: Comprehensive test coverage ensures correctness