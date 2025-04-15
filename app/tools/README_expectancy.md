# Expectancy Calculation Module

## Overview

The Expectancy Calculation Module provides standardized functions for calculating expectancy metrics across both signals and trades. This ensures consistency throughout the system and eliminates duplication of calculation logic.

## Key Features

- Unified expectancy calculation formula
- Support for calculating expectancy directly from returns
- Stop loss adjustment capabilities
- Conversion between per-trade and per-month expectancy
- Comprehensive expectancy metrics calculation

## Usage

### Basic Expectancy Calculation

```python
from app.tools.expectancy import calculate_expectancy

# Calculate expectancy
win_rate = 0.6  # 60% win rate
avg_win = 0.05  # 5% average win
avg_loss = 0.03  # 3% average loss
expectancy = calculate_expectancy(win_rate, avg_win, avg_loss)
```

### Calculating Expectancy from Returns

```python
from app.tools.expectancy import calculate_expectancy_from_returns

# Calculate expectancy from a series of returns
returns = [0.05, -0.03, 0.04, -0.02, 0.06]
expectancy, components = calculate_expectancy_from_returns(returns)

# Access components
win_rate = components["win_rate"]
avg_win = components["avg_win"]
avg_loss = components["avg_loss"]
```

### Applying Stop Loss

```python
from app.tools.expectancy import calculate_expectancy_with_stop_loss

# Calculate expectancy with stop loss
returns = [0.05, -0.08, 0.04, -0.06, 0.07]
stop_loss = 0.05  # 5% stop loss
direction = "Long"  # or "Short"
expectancy, components = calculate_expectancy_with_stop_loss(returns, stop_loss, direction)
```

### Comprehensive Metrics

```python
from app.tools.expectancy import calculate_expectancy_metrics

# Calculate all expectancy metrics
returns = [0.05, -0.03, 0.04, -0.02, 0.06]
config = {
    "STOP_LOSS": 0.05,
    "DIRECTION": "Long",
    "TRADES_PER_MONTH": 20
}
metrics = calculate_expectancy_metrics(returns, config)

# Access metrics
expectancy = metrics["Expectancy"]
expectancy_per_trade = metrics["Expectancy per Trade"]
expectancy_per_month = metrics["Expectancy per Month"]
```

## Integration with Existing Systems

The module is designed to integrate seamlessly with both signal quality metrics and trade performance metrics:

### Signal Quality Integration

```python
from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics

# The signal quality module now uses the standardized expectancy calculation
signal_metrics = calculate_signal_quality_metrics(signals_df, returns_df, strategy_id, log)
expectancy = signal_metrics["expectancy_per_signal"]
```

### Trade Performance Integration

```python
from app.tools.backtest_strategy import backtest_strategy

# The backtest strategy module now uses the standardized expectancy calculation
portfolio = backtest_strategy(data, config, log)
stats = portfolio.stats()
expectancy = stats["Expectancy per Trade"]
```

## Benefits

- **Consistency**: Same calculation method used throughout the system
- **Maintainability**: Single source of truth for expectancy calculations
- **Extensibility**: Easy to add new expectancy-related metrics
- **Transparency**: Clear documentation of calculation methodology
- **Reliability**: Comprehensive test coverage ensures correctness

## Implementation Details

The module follows the Single Responsibility Principle (SRP) by focusing solely on expectancy calculations. It adheres to the Don't Repeat Yourself (DRY) principle by providing reusable components that eliminate code duplication across the system.