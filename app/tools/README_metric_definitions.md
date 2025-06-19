# Signal and Trade Metrics Definitions

This document provides comprehensive definitions, formulas, and interpretation guidelines for all metrics used in signal and trade analysis.

## Table of Contents

1. [Return Metrics](#return-metrics)
2. [Signal Frequency Metrics](#signal-frequency-metrics)
3. [Signal Quality Metrics](#signal-quality-metrics)
4. [Horizon Metrics](#horizon-metrics)
5. [Portfolio Metrics](#portfolio-metrics)
6. [Composite Scores](#composite-scores)
7. [Normalization Methods](#normalization-methods)

## Return Metrics

### Average Return (`avg_return`)

**Definition**: The mean return across all active positions.

**Formula**:

```
avg_return = (1/n) * Σ(r_i)
```

where `r_i` is the return for position `i`, and `n` is the total number of positions.

**Interpretation**:

- Positive values indicate profitable positions on average
- Higher values indicate better performance
- Should be considered alongside volatility metrics

**Typical Range**: -0.05 to 0.05 (or -5% to 5%)

### Median Return (`median_return`)

**Definition**: The middle value of returns when arranged in order.

**Formula**: The value separating the higher half from the lower half of returns.

**Interpretation**:

- Less affected by outliers than average return
- Provides insight into the typical return
- Difference from average return indicates skew in the distribution

**Typical Range**: -0.03 to 0.03 (or -3% to 3%)

### Return Standard Deviation (`std_return`)

**Definition**: The standard deviation of returns, measuring volatility.

**Formula**:

```
std_return = sqrt((1/n) * Σ((r_i - avg_return)²))
```

**Interpretation**:

- Lower values indicate more consistent returns
- Higher values indicate higher volatility
- Should be considered alongside average return

**Typical Range**: 0.01 to 0.10 (or 1% to 10%)

### Win Rate (`win_rate`)

**Definition**: The proportion of positions that result in positive returns.

**Formula**:

```
win_rate = (number of positions with positive returns) / (total number of positions)
```

**Interpretation**:

- Values above 0.5 (50%) indicate more winning positions than losing positions
- Should be considered alongside average win and average loss
- High win rates with small average wins can still be profitable

**Typical Range**: 0.3 to 0.7 (or 30% to 70%)

### Average Win (`avg_win`)

**Definition**: The mean return across all winning positions.

**Formula**:

```
avg_win = (1/w) * Σ(r_i) for all r_i > 0
```

where `w` is the number of winning positions.

**Interpretation**:

- Higher values indicate larger profits on winning positions
- Should be considered alongside win rate
- Contributes to overall expectancy

**Typical Range**: 0.01 to 0.10 (or 1% to 10%)

### Average Loss (`avg_loss`)

**Definition**: The mean return across all losing positions (reported as a negative value).

**Formula**:

```
avg_loss = (1/l) * Σ(r_i) for all r_i < 0
```

where `l` is the number of losing positions.

**Interpretation**:

- Values closer to zero indicate smaller losses
- Should be considered alongside win rate
- Contributes to overall expectancy

**Typical Range**: -0.05 to -0.01 (or -5% to -1%)

### Risk-Reward Ratio (`risk_reward_ratio`)

**Definition**: The ratio of average win to the absolute value of average loss.

**Formula**:

```
risk_reward_ratio = avg_win / |avg_loss|
```

**Interpretation**:

- Values above 1.0 indicate larger average wins than losses
- Higher values are generally better
- Should be considered alongside win rate

**Typical Range**: 0.5 to 3.0

### Profit Factor (`profit_factor`)

**Definition**: The ratio of gross profits to gross losses.

**Formula**:

```
profit_factor = Σ(positive returns) / |Σ(negative returns)|
```

**Interpretation**:

- Values above 1.0 indicate overall profitability
- Higher values indicate more robust profitability
- More comprehensive than risk-reward ratio as it accounts for frequency

**Typical Range**: 0.8 to 2.5

### Expectancy Per Trade (`expectancy_per_trade`)

**Definition**: The expected return per trade, accounting for win rate, average win, and average loss.

**Formula**:

```
expectancy_per_trade = (win_rate * avg_win) - ((1 - win_rate) * |avg_loss|)
```

**Interpretation**:

- Positive values indicate a profitable system
- Higher values indicate better performance
- Combines frequency and magnitude of wins and losses

**Typical Range**: -0.02 to 0.05 (or -2% to 5%)

### Annualized Return (`annualized_return`)

**Definition**: The average return scaled to an annual basis.

**Formula**:

```
annualized_return = avg_return * annualization_factor
```

where `annualization_factor` is typically 252 for daily data.

**Interpretation**:

- Allows comparison across different timeframes
- Higher values indicate better performance
- Should be considered alongside annualized volatility

**Typical Range**: -0.5 to 1.0 (or -50% to 100%)

### Annualized Volatility (`annualized_volatility`)

**Definition**: The standard deviation of returns scaled to an annual basis.

**Formula**:

```
annualized_volatility = std_return * sqrt(annualization_factor)
```

**Interpretation**:

- Lower values indicate more consistent returns
- Higher values indicate higher risk
- Should be considered alongside annualized return

**Typical Range**: 0.1 to 0.5 (or 10% to 50%)

### Sharpe Ratio (`sharpe_ratio`)

**Definition**: The risk-adjusted return, measuring excess return per unit of risk.

**Formula**:

```
sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility
```

Note: We typically assume a risk-free rate of 0 for simplicity.

**Interpretation**:

- Values above 1.0 are generally considered acceptable
- Values above 2.0 are considered very good
- Higher values indicate better risk-adjusted performance

**Typical Range**: 0 to 3.0

### Maximum Drawdown (`max_drawdown`)

**Definition**: The maximum observed loss from a peak to a trough.

**Formula**:

```
max_drawdown = max(peak_value - trough_value) / peak_value
```

**Interpretation**:

- Lower values indicate less severe drawdowns
- Important for risk management
- Should be considered alongside return metrics

**Typical Range**: 0.05 to 0.5 (or 5% to 50%)

### Sortino Ratio (`sortino_ratio`)

**Definition**: A variation of the Sharpe ratio that only considers downside volatility.

**Formula**:

```
sortino_ratio = (annualized_return - risk_free_rate) / (downside_deviation * sqrt(annualization_factor))
```

where `downside_deviation` is the standard deviation of negative returns.

**Interpretation**:

- Higher values indicate better risk-adjusted performance
- More relevant than Sharpe ratio for asymmetric return distributions
- Values above 2.0 are generally considered good

**Typical Range**: 0 to 4.0

### Calmar Ratio (`calmar_ratio`)

**Definition**: The ratio of annualized return to maximum drawdown.

**Formula**:

```
calmar_ratio = annualized_return / max_drawdown
```

**Interpretation**:

- Higher values indicate better return per unit of drawdown risk
- Values above 1.0 are generally considered good
- Important for evaluating long-term performance

**Typical Range**: 0 to 5.0

### Value at Risk (`value_at_risk_95`)

**Definition**: The maximum loss expected with 95% confidence over a specified time period.

**Formula**:

```
var_95 = 5th percentile of returns
```

**Interpretation**:

- Lower absolute values indicate lower risk
- Important for risk management
- Represents the worst-case scenario with 95% confidence

**Typical Range**: -0.05 to -0.01 (or -5% to -1%)

## Signal Frequency Metrics

### Mean Signals Per Month (`mean_signals_per_month`)

**Definition**: The average number of signals generated per month.

**Formula**:

```
mean_signals_per_month = (total number of signals) / (number of months)
```

**Interpretation**:

- Higher values indicate more frequent trading
- Should be considered alongside signal quality metrics
- Optimal value depends on the strategy type

**Typical Range**: 1 to 30

### Median Signals Per Month (`median_signals_per_month`)

**Definition**: The median number of signals generated per month.

**Formula**: The middle value of monthly signal counts when arranged in order.

**Interpretation**:

- Less affected by outlier months than mean
- Provides insight into typical signal frequency
- Difference from mean indicates skew in distribution

**Typical Range**: 1 to 25

### Signal Volatility (`signal_volatility`)

**Definition**: The standard deviation of monthly signal counts.

**Formula**:

```
signal_volatility = sqrt((1/m) * Σ((s_i - mean_signals_per_month)²))
```

where `s_i` is the number of signals in month `i`, and `m` is the number of months.

**Interpretation**:

- Lower values indicate more consistent signal generation
- Higher values indicate irregular signal patterns
- Should be considered relative to mean signals

**Typical Range**: 0.5 to 15

### Signal Consistency (`signal_consistency`)

**Definition**: A measure of how consistently signals are generated over time.

**Formula**:

```
signal_consistency = 1.0 - min(1.0, signal_volatility / mean_signals_per_month)
```

**Interpretation**:

- Values closer to 1.0 indicate more consistent signal generation
- Values closer to 0.0 indicate highly irregular signal patterns
- Important for evaluating strategy reliability

**Typical Range**: 0.3 to 0.9

### Signal Density (`signal_density`)

**Definition**: The proportion of trading days that generate signals.

**Formula**:

```
signal_density = (total number of signals) / (total number of trading days)
```

**Interpretation**:

- Higher values indicate more active signal generation
- Lower values indicate more selective signal generation
- Optimal value depends on the strategy type

**Typical Range**: 0.01 to 0.3 (or 1% to 30%)

## Signal Quality Metrics

### Signal Quality Score (`signal_quality_score`)

**Definition**: A composite score measuring overall signal quality.

**Formula**:

```
signal_quality_score = 10.0 * (
    0.4 * win_rate +
    0.3 * (min(profit_factor, 5.0) / 5.0) +
    0.2 * (avg_return / max(|avg_loss|, 0.001)) +
    0.1 * (1.0 if avg_return > 0 else 0.0)
)
```

**Rationale for Weights**:

- Win rate (40%): Primary indicator of signal accuracy
- Profit factor (30%): Measures overall profitability
- Risk-reward (20%): Measures quality of individual signals
- Positive return (10%): Basic profitability check

**Interpretation**:

- Scale of 0 to 10
- Values above 7.0 indicate high-quality signals
- Values below 3.0 indicate poor-quality signals
- Should be used alongside individual metrics for detailed analysis

**Typical Range**: 2.0 to 8.0

## Horizon Metrics

### Horizon Average Return (`horizon_metrics[horizon]["avg_return"]`)

**Definition**: The average return over a specific time horizon after a signal.

**Formula**:

```
horizon_avg_return = (1/n) * Σ(r_i,h)
```

where `r_i,h` is the cumulative return for position `i` over horizon `h`.

**Interpretation**:

- Positive values indicate profitable signals over the horizon
- Helps identify optimal holding periods
- Should be compared across different horizons

**Typical Range**: -0.05 to 0.10 (or -5% to 10%)

### Horizon Win Rate (`horizon_metrics[horizon]["win_rate"]`)

**Definition**: The proportion of positions that result in positive returns over a specific time horizon.

**Formula**:

```
horizon_win_rate = (number of positions with positive returns over horizon) / (total number of positions)
```

**Interpretation**:

- Values above 0.5 (50%) indicate more winning positions than losing positions
- Helps identify optimal holding periods
- Should be compared across different horizons

**Typical Range**: 0.3 to 0.7 (or 30% to 70%)

### Horizon Sharpe Ratio (`horizon_metrics[horizon]["sharpe"]`)

**Definition**: The risk-adjusted return over a specific time horizon.

**Formula**:

```
horizon_sharpe = horizon_avg_return / std(horizon_returns)
```

**Interpretation**:

- Higher values indicate better risk-adjusted performance
- Helps identify optimal holding periods
- Should be compared across different horizons

**Typical Range**: 0 to 2.0

## Portfolio Metrics

### Portfolio Mean Signals Per Month (`portfolio_mean_signals_per_month`)

**Definition**: The average number of signals generated per month across all strategies in the portfolio.

**Formula**:

```
portfolio_mean_signals_per_month = (1/s) * Σ(mean_signals_per_month_i)
```

where `s` is the number of strategies.

**Interpretation**:

- Higher values indicate more frequent trading
- Important for capacity and execution planning
- Should be considered alongside signal quality metrics

**Typical Range**: 5 to 100

### Portfolio Signal Volatility (`portfolio_signal_volatility`)

**Definition**: The standard deviation of monthly signal counts across all strategies.

**Formula**:

```
portfolio_signal_volatility = sqrt((1/s) * Σ((signal_volatility_i)²))
```

**Interpretation**:

- Lower values indicate more consistent signal generation
- Higher values indicate irregular signal patterns
- Important for risk management

**Typical Range**: 2 to 30

## Composite Scores

### Combined Score Calculation

**Definition**: The methodology for calculating composite scores from individual metrics.

**General Formula**:

```
composite_score = Σ(weight_i * normalized_metric_i)
```

**Normalization Method**:

- Min-max scaling to [0, 1] range
- Z-score normalization for comparative metrics
- Robust scaling for metrics with outliers

**Weighting Rationale**:

- Higher weights for more reliable and predictive metrics
- Lower weights for more volatile or context-dependent metrics
- Weights adjusted based on empirical performance

**Interpretation**:

- Higher values indicate better overall performance
- Should be used alongside individual metrics for detailed analysis
- Useful for ranking and comparing strategies

## Normalization Methods

### Min-Max Scaling

**Definition**: Scales values to a specified range, typically [0, 1].

**Formula**:

```
normalized_value = (value - min_value) / (max_value - min_value) * (target_max - target_min) + target_min
```

**Use Cases**:

- Metrics with well-defined bounds
- Metrics used in weighted sums
- Metrics with different units or scales

### Z-Score Normalization

**Definition**: Scales values based on mean and standard deviation.

**Formula**:

```
normalized_value = (value - mean) / standard_deviation
```

**Use Cases**:

- Metrics for comparison across different datasets
- Metrics with approximately normal distributions
- Detecting outliers

### Robust Scaling

**Definition**: Scales values based on median and interquartile range.

**Formula**:

```
normalized_value = (value - median) / IQR
```

**Use Cases**:

- Metrics with outliers
- Metrics with skewed distributions
- Metrics requiring robust statistical comparison
