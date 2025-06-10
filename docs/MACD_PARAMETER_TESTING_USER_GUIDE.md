# MACD Parameter Testing User Guide

## Overview

The MACD (Moving Average Convergence Divergence) strategy has been integrated into the Parameter Sensitivity Testing framework, providing comprehensive analysis capabilities for MACD crossover strategies alongside existing SMA and EMA support.

## What is MACD?

MACD is a trend-following momentum indicator that uses three exponential moving averages:

- **Short EMA**: Fast-moving average (typically 6-15 periods)
- **Long EMA**: Slow-moving average (typically 12-35 periods)
- **Signal EMA**: Signal line smoothing (typically 5-12 periods)

### MACD Calculation

1. **MACD Line** = Short EMA - Long EMA
2. **Signal Line** = EMA of MACD Line (using Signal window)
3. **Entry Signal** = MACD Line crosses above Signal Line
4. **Exit Signal** = MACD Line crosses below Signal Line

## Using MACD in Parameter Testing

### Accessing MACD Strategy

1. **Navigate to Parameter Testing**: Open the Sensylate Parameter Testing interface
2. **Select MACD Strategy**: Check the "MACD (Moving Average Convergence Divergence)" checkbox
3. **Configure Parameters**: MACD parameter section will appear automatically

### MACD Parameter Configuration

When MACD is selected, you'll see a dedicated parameter card with the following controls:

#### Short EMA Window Range

- **Start**: Minimum short window (default: 6)
- **End**: Maximum short window (default: 15)
- **Typical Range**: 6-15 periods
- **Description**: Fast-moving average for trend detection

#### Long EMA Window Range

- **Start**: Minimum long window (default: 12)
- **End**: Maximum long window (default: 35)
- **Typical Range**: 12-35 periods
- **Constraint**: Must be greater than short window end
- **Description**: Slow-moving average for trend confirmation

#### Signal EMA Window Range

- **Start**: Minimum signal window (default: 5)
- **End**: Maximum signal window (default: 12)
- **Typical Range**: 5-12 periods
- **Description**: Signal line smoothing for entry/exit timing

#### Step Size

- **Range**: 1-10
- **Default**: 1
- **Description**: Parameter increment for testing combinations

### Parameter Validation

The system enforces these validation rules:

- Short window end > Short window start
- Long window start > Short window end
- Long window end > Long window start
- Signal window end > Signal window start
- All windows > 0
- Step size between 1-10

Invalid configurations will show error messages and prevent analysis execution.

## MACD Configuration Presets

### Available Presets

#### MACD Standard

- **Use Case**: General-purpose MACD analysis
- **Short Range**: 6-15
- **Long Range**: 12-35
- **Signal Range**: 5-12
- **Step**: 1
- **Timeframe**: 3 years
- **Best For**: Most asset types, balanced approach

#### MACD Quick Test

- **Use Case**: Fast parameter exploration
- **Short Range**: 8-12
- **Long Range**: 20-30
- **Signal Range**: 7-10
- **Step**: 2 (faster execution)
- **Timeframe**: 2 years
- **Best For**: Initial testing, parameter space exploration

#### MACD Comprehensive

- **Use Case**: Thorough parameter analysis
- **Short Range**: 5-20
- **Long Range**: 15-50
- **Signal Range**: 4-15
- **Step**: 1
- **Timeframe**: 5 years
- **Best For**: Final strategy optimization, research

#### MACD Crypto Focus

- **Use Case**: Cryptocurrency-specific parameters
- **Short Range**: 10-18
- **Long Range**: 22-35
- **Signal Range**: 8-14
- **Step**: 2
- **Timeframe**: 2 years, current prices
- **Best For**: Bitcoin, Ethereum, major cryptocurrencies

#### MACD Conservative

- **Use Case**: Risk-averse parameter selection
- **Short Range**: 8-16
- **Long Range**: 25-40
- **Signal Range**: 7-12
- **Step**: 1
- **Timeframe**: 7 years
- **Sort By**: Sortino Ratio (risk-adjusted)
- **Best For**: Conservative portfolios, risk management focus

#### MACD Intraday

- **Use Case**: Hourly/short-term trading
- **Short Range**: 5-10
- **Long Range**: 12-20
- **Signal Range**: 4-8
- **Step**: 1
- **Timeframe**: 1 year, hourly data
- **Best For**: Day trading, short-term strategies

#### Mixed Strategy All

- **Use Case**: Compare MACD with SMA/EMA
- **Strategies**: SMA, EMA, MACD
- **MACD Range**: Moderate (10-16, 20-30, 8-12)
- **Step**: 2
- **Best For**: Strategy comparison, finding optimal approach

## Performance Optimization

### Parameter Combination Limits

MACD testing can generate many parameter combinations:

- **Small**: < 50 combinations (fast execution)
- **Medium**: 50-200 combinations (standard execution)
- **Large**: 200-500 combinations (async recommended)
- **Very Large**: > 500 combinations (async required)

### Automatic Optimizations

The system automatically applies optimizations for large parameter spaces:

1. **Step Size Increase**: Increases step to 2 for very large ranges
2. **Range Reduction**: Limits window ranges to reasonable values
3. **Async Execution**: Automatically enables for large combinations
4. **Memory Management**: Monitors and limits memory usage

### Performance Recommendations

- **Start Small**: Use "MACD Quick Test" for initial exploration
- **Iterate**: Gradually expand ranges based on promising results
- **Use Async**: Enable async execution for comprehensive analysis
- **Monitor Resources**: Watch for performance warnings

## Understanding MACD Results

### Results Table Columns

When viewing MACD results, you'll see these specific columns:

- **Signal Window**: Shows MACD signal window (blank for SMA/EMA)
- **Strategy Type**: Displays "MACD"
- **Short/Long Window**: MACD EMA periods
- **Standard Metrics**: Win rate, profit factor, Sortino ratio, etc.

### MACD-Specific Metrics

MACD strategies include additional context:

- **Signal Quality**: How well signal timing aligns with trends
- **Whipsaw Reduction**: Fewer false signals compared to simple MA crosses
- **Trend Confirmation**: Multiple EMA layers provide trend validation

### Interpreting Results

**Good MACD Parameters:**

- Win Rate > 35% (conservative) to 50% (aggressive)
- Profit Factor > 1.2
- Sortino Ratio > 0.6
- Sufficient trades (> 50 for reliability)
- Reasonable drawdown (< 25%)

**Red Flags:**

- Very high win rate (> 70%) may indicate overfitting
- Too few trades (< 20) reduces statistical significance
- Extreme parameter values may not be robust

## Best Practices

### Parameter Selection Strategy

1. **Start with Standard Preset**: Use "MACD Standard" as baseline
2. **Test Asset-Specific**: Try "MACD Crypto Focus" for crypto
3. **Validate Robustness**: Run "MACD Comprehensive" for final validation
4. **Compare Approaches**: Use "Mixed Strategy All" to compare with MA

### Workflow Recommendations

1. **Initial Exploration**: Quick Test preset (< 5 minutes)
2. **Focused Analysis**: Standard preset on promising assets
3. **Comprehensive Testing**: Full analysis on selected parameters
4. **Out-of-Sample Validation**: Test on different time periods

### Common Pitfalls

❌ **Avoid These Mistakes:**

- Using identical short and long windows
- Setting signal window larger than short window
- Testing too many combinations without focus
- Ignoring parameter validation warnings
- Over-optimizing on limited data

✅ **Best Practices:**

- Ensure logical parameter relationships
- Start with standard ranges and adjust
- Monitor performance warnings
- Validate on multiple time periods
- Consider transaction costs in real trading

## Troubleshooting

### Common Issues

**Issue**: MACD parameters not showing
**Solution**: Ensure MACD checkbox is selected

**Issue**: Validation errors
**Solution**: Check parameter relationships (long > short, etc.)

**Issue**: Analysis taking too long
**Solution**: Reduce parameter ranges or increase step size

**Issue**: No results returned
**Solution**: Check minimum filters, may be too restrictive

**Issue**: Memory warnings
**Solution**: Reduce ticker count or parameter combinations

### Performance Warnings

If you see performance warnings:

- **"Parameter combination count exceeds limit"**: Reduce ranges
- **"Memory usage may exceed limits"**: Limit scope or use async
- **"Async execution required"**: Enable async execution
- **"Consider reducing parameter ranges"**: Use larger step size

### Getting Help

For additional support:

1. Check parameter validation messages
2. Review preset configurations for guidance
3. Start with smaller parameter ranges
4. Monitor system performance recommendations

## Advanced Features

### Custom Parameter Ranges

You can create custom MACD configurations:

- Adjust window ranges based on asset characteristics
- Modify step sizes for performance vs. precision trade-offs
- Set specific minimum filters for your strategy requirements

### Mixed Strategy Analysis

Compare MACD with traditional moving averages:

- Select multiple strategy types (SMA, EMA, MACD)
- Use identical tickers and timeframes
- Compare results side-by-side
- Identify optimal approach for each asset

### Async Execution

For large parameter spaces:

- Enables background processing
- Provides real-time progress updates
- Allows multiple concurrent analyses
- Prevents browser timeouts

---

_This guide covers the complete MACD parameter testing functionality. For technical implementation details, see the MACD Cross Parameter Testing Implementation Plan._
