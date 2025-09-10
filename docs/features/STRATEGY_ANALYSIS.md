# Strategy Analysis

## Overview

The strategy analysis system provides comprehensive tools for analyzing trading strategies with statistical rigor and performance optimization.

## Supported Strategies

### 1. Moving Average Strategies

- **Simple Moving Average (SMA)**: Traditional moving average crossover
- **Exponential Moving Average (EMA)**: Weighted recent price emphasis
- **Dual Moving Average Cross**: Fast/slow moving average crossover signals

### 2. Momentum Strategies

- **MACD**: Moving Average Convergence Divergence
- **RSI**: Relative Strength Index
- **Momentum Oscillator**: Custom momentum indicators

### 3. Volatility Strategies

- **Bollinger Bands**: Volatility-based entry/exit signals
- **ATR-based**: Average True Range position sizing
- **Volatility Breakout**: Volatility expansion strategies

## Command Interface

### Basic Usage

```bash
# Single strategy analysis
trading-cli strategy run --ticker AAPL --strategy SMA

# Multiple strategies
trading-cli strategy run --ticker AAPL --strategy SMA,EMA,MACD

# Multiple tickers
trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA
```

### Advanced Options

```bash
# Custom parameters
trading-cli strategy run --ticker AAPL --strategy SMA --fast-window 20 --slow-window 50

# Minimum requirements
trading-cli strategy run --ticker AAPL --strategy SMA --min-trades 100 --min-win-rate 0.6

# Time constraints
trading-cli strategy run --ticker AAPL --strategy SMA --start-date 2023-01-01 --end-date 2023-12-31
```

### Parameter Sweeps

```bash
# Comprehensive parameter sweep
trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200

# Optimized sweep with constraints
trading-cli strategy sweep --ticker AAPL --fast-min 10 --fast-max 30 --slow-min 40 --slow-max 100 --min-trades 50
```

## Configuration Profiles

### Creating Custom Profiles

```yaml
# app/cli/profiles/my_ma_cross.yaml
metadata:
  name: my_ma_cross
  description: Custom MA cross strategy

config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL, AMZN]
  strategy_types: [SMA, EMA]
  windows: 100
  minimums:
    win_rate: 0.55
    trades: 75
    sharpe_ratio: 0.5
  data_period: 2Y
```

### Using Profiles

```bash
# Run with profile
trading-cli strategy run --profile my_ma_cross

# Override profile settings
trading-cli strategy run --profile my_ma_cross --ticker TSLA --min-trades 50
```

## Performance Metrics

### Core Metrics

- **Total Return**: Overall strategy performance
- **Win Rate**: Percentage of winning trades
- **Sharpe Ratio**: Risk-adjusted return
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Profit Factor**: Ratio of gross profits to gross losses

### Advanced Metrics

- **Sortino Ratio**: Downside deviation-adjusted return
- **Calmar Ratio**: Annual return to max drawdown ratio
- **Information Ratio**: Excess return per unit of tracking error
- **Tail Ratio**: Ratio of 95th percentile to 5th percentile returns

### Risk Metrics

- **Value at Risk (VaR)**: Maximum expected loss at confidence level
- **Conditional VaR**: Expected loss beyond VaR threshold
- **Beta**: Sensitivity to market movements
- **Alpha**: Excess return above market

## Strategy Validation

### Minimum Requirements

```python
# Default validation criteria
MINIMUM_TRADES = 44
MINIMUM_WIN_RATE = 0.5
MINIMUM_SHARPE_RATIO = 0.0
MINIMUM_PROFIT_FACTOR = 1.0
```

### Statistical Significance

- **Sample Size**: Minimum number of trades for statistical validity
- **Confidence Intervals**: 95% confidence intervals for all metrics
- **Hypothesis Testing**: Statistical significance of outperformance

### Robustness Tests

- **Walk-Forward Analysis**: Out-of-sample validation
- **Monte Carlo Simulation**: Randomized performance testing
- **Stability Analysis**: Performance consistency across periods

## Output Formats

### CSV Exports

```
data/raw/portfolios/TICKER_TIMEFRAME_STRATEGY.csv
```

**Example**: `data/raw/portfolios/AAPL_D_SMA.csv`

### JSON Exports (Optional)

```bash
# Export with JSON format
trading-cli strategy run --ticker AAPL --strategy SMA --export-format json
```

### Portfolio Aggregation

```
data/raw/portfolios_filtered/    # Filtered by criteria
data/raw/portfolios_best/        # Best performing strategies
```

## Integration with Other Systems

### Statistical Analysis

```bash
# Analyze strategy results
trading-cli spds analyze AAPL_D_SMA.csv
```

### Portfolio Management

```bash
# Update portfolio with new results
trading-cli portfolio update --validate --export-format json
```

### Trade History

```bash
# Export trade history
trading-cli trade-history update --portfolio live_signals
```

## Data Sources

### Market Data

- **Yahoo Finance**: Primary data source via yfinance
- **Custom Data**: CSV import capability
- **Real-time Data**: Live price updates (optional)

### Synthetic Instruments

- **Pair Trading**: STRK_MSTR synthetic pairs
- **Spread Trading**: Custom spread calculations
- **Ratio Trading**: Ratio-based synthetic instruments

## Performance Optimization

### Memory Management

```bash
# Enable memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory

# Streaming for large datasets
trading-cli strategy run --ticker AAPL --strategy SMA --stream-data
```

### Parallel Processing

```bash
# Parallel execution
trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA --parallel

# Batch processing
trading-cli strategy run --batch-size 10 --ticker-file tickers.txt
```

## Debugging and Validation

### Dry Run Mode

```bash
# Preview without execution
trading-cli strategy run --ticker AAPL --strategy SMA --dry-run
```

### Verbose Output

```bash
# Detailed logging
trading-cli strategy run --ticker AAPL --strategy SMA --verbose
```

### Validation Checks

```bash
# Validate strategy results
trading-cli strategy validate --portfolio AAPL_D_SMA.csv

# Health check
trading-cli tools health
```

## Advanced Features

### Custom Indicators

```python
# Implement custom indicators
class CustomIndicator:
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        # Custom calculation logic
        return custom_values
```

### Strategy Composition

```bash
# Combine multiple strategies
trading-cli strategy run --ticker AAPL --strategy SMA,EMA --combine-signals
```

### Risk Management

```bash
# Apply risk management rules
trading-cli strategy run --ticker AAPL --strategy SMA --stop-loss 0.05 --take-profit 0.15
```

## Best Practices

### 1. Data Quality

- Verify data completeness before analysis
- Check for missing values and outliers
- Validate data ranges and consistency

### 2. Strategy Selection

- Start with simple strategies before complex ones
- Validate assumptions with statistical tests
- Consider transaction costs and slippage

### 3. Performance Evaluation

- Use multiple metrics for comprehensive evaluation
- Apply statistical significance tests
- Consider risk-adjusted returns

### 4. Overfitting Prevention

- Use out-of-sample validation
- Apply walk-forward analysis
- Limit parameter optimization

## Common Patterns

### 1. Daily Analysis Routine

```bash
# Morning strategy update
trading-cli strategy run --profile daily_analysis
trading-cli portfolio update --validate
trading-cli spds analyze live_signals.csv
```

### 2. Strategy Development

```bash
# Parameter optimization
trading-cli strategy sweep --ticker AAPL --strategy SMA
trading-cli strategy validate --portfolio sweep_results.csv
trading-cli portfolio optimize --portfolio validated_strategies.csv
```

### 3. Performance Monitoring

```bash
# Regular performance review
trading-cli trade-history update --portfolio live_signals
trading-cli portfolio health --portfolio live_signals.csv
```

## Troubleshooting

### Common Issues

**Insufficient Data**:

```bash
# Check data availability
trading-cli data check --ticker AAPL --start-date 2023-01-01

# Extend data period
trading-cli strategy run --ticker AAPL --strategy SMA --data-period 5Y
```

**Poor Performance**:

```bash
# Analyze strategy weaknesses
trading-cli strategy review --portfolio AAPL_D_SMA.csv --detailed

# Optimize parameters
trading-cli strategy sweep --ticker AAPL --strategy SMA --optimize
```

**Memory Issues**:

```bash
# Enable memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory --stream-data
```

---

_For more detailed information, see the [User Guide](../USER_GUIDE.md) and [API Reference](../reference/API_REFERENCE.md)._
