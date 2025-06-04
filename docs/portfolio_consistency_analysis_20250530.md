# Portfolio Consistency Analysis: portfolio_d_20250530

**Analysis Date**: 2025-05-31
**Files Analyzed**:

- `json/concurrency/portfolio_d_20250530.json`
- `csv/strategies/portfolio_d_20250530.csv`

## Executive Summary

✅ **Files are fully consistent** - Both files analyze the same 21 trading strategies with identical parameters. They represent complementary analytical perspectives of the same portfolio: individual strategy performance (CSV) and portfolio-level concurrency analysis (JSON).

## File Format and Purpose

### CSV File (`portfolio_d_20250530.csv`)

- **Purpose**: MA Cross strategy backtesting results
- **Structure**: 21 strategies with complete performance metrics
- **Focus**: Individual strategy performance analysis
- **Key Metrics**: Win rates, profit factors, Sharpe ratios, trade statistics

### JSON File (`portfolio_d_20250530.json`)

- **Purpose**: Concurrency analysis results from the trading system
- **Structure**: Hierarchical JSON with portfolio and strategy-level metrics
- **Focus**: Portfolio-level strategy interactions and efficiency
- **Key Metrics**: Concurrency ratios, efficiency scores, risk concentration

## Consistency Verification

### ✅ Strategy Count

- **CSV**: 21 strategies
- **JSON**: 21 strategies in "strategies" section
- **Status**: ✅ Perfect match

### ✅ Strategy Parameters

**Verification Examples**:

```
CSV Row 2: BTC-USD, SMA, 11, 36, 0
JSON ID:   "BTC-USD_SMA_11_36_0"

CSV Row 3: MSTR, SMA, 16, 82, 0
JSON ID:   "MSTR_SMA_16_82_0"

CSV Row 9: BTC-USD, MACD, 14, 23, 13
JSON ID:   "BTC-USD_MACD_14_23_13"
```

**Status**: ✅ All parameters match perfectly

### ✅ Ticker Distribution

Both files contain identical ticker coverage:

- **MSTR**: 3 strategies each
- **BTC-USD**: 11 strategies each
- **QQQ**: 7 strategies each
- **Total**: 21 strategies each

### ✅ Strategy Types

Both files include the same strategy types:

- **SMA** (Simple Moving Average): 10 strategies
- **EMA** (Exponential Moving Average): 4 strategies
- **MACD** (Moving Average Convergence Divergence): 7 strategies

## Data Structure Comparison

### CSV Structure

```
Ticker | Strategy Type | Short Window | Long Window | Signal Window | Performance Metrics...
MSTR   | SMA          | 52          | 90         | 0            | Score: 1.70, Win Rate: 60.53%
BTC-USD| SMA          | 11          | 36         | 0            | Score: 1.68, Win Rate: 52.83%
QQQ    | SMA          | 69          | 77         | 0            | Score: 1.66, Win Rate: 69.84%
```

### JSON Structure

```json
{
  "portfolio_metrics": {
    "efficiency": { "efficiency_score": 0.134 },
    "concurrency": { "concurrency_ratio": 0.992 }
  },
  "strategies": [
    {
      "id": "BTC-USD_SMA_11_36_0",
      "parameters": {
        "ticker": "BTC-USD",
        "type": "SMA",
        "short_window": 11,
        "long_window": 36
      }
    }
  ]
}
```

## Analysis Perspectives

### CSV Analysis Focus

**Individual Strategy Performance**:

- Trade-level statistics (67 trades avg)
- Win rates (42-70% range)
- Profit factors (1.4-5.7 range)
- Risk metrics (Sharpe, Sortino, Calmar ratios)
- Return analysis vs benchmarks

### JSON Analysis Focus

**Portfolio-Level Interactions**:

- **Concurrency Analysis**: 99.2% concurrent trading periods
- **Efficiency Scoring**: 0.134 overall efficiency
- **Risk Concentration**: High correlation between strategies
- **Diversification Metrics**: 0.77 diversification factor

## Key Metrics Relationship

### Expectancy Comparison

- **CSV Individual Expectancies**: Range from 1.72 to 37.12 per trade
- **JSON Portfolio Expectancy**: 261.74 (allocation-weighted combined)
- **Relationship**: JSON value represents weighted sum of individual CSV expectancies

### Performance Alignment

**Top Performing Strategies (CSV Score)**:

1. MSTR SMA 52/90: Score 1.70
2. BTC-USD SMA 11/36: Score 1.68
3. MSTR SMA 16/82: Score 1.67

**Efficiency Components (JSON)**:

- **Diversification**: 0.77 (good strategy differentiation)
- **Independence**: 0.28 (low - high concurrent trading)
- **Activity**: 0.997 (very high strategy utilization)

## Concurrency Analysis Insights

### High Concurrency Environment

- **99.2%** of periods have multiple strategies active
- **0.56%** exclusive periods (single strategy active)
- **0.26%** inactive periods (no strategies active)
- **Average**: 13.15 strategies active simultaneously
- **Maximum**: 21 strategies active concurrently

### Efficiency Implications

**Low Overall Efficiency (0.134)** driven by:

1. **High Concurrency**: Strategies trade together frequently
2. **Low Independence**: Limited exclusive trading periods
3. **Risk Concentration**: Capital concentrated during concurrent periods

### Risk Metrics

**Portfolio-Level Risk**:

- **VaR 95%**: -4.56%
- **CVaR 95%**: -6.92%
- **VaR 99%**: -8.20%
- **CVaR 99%**: -11.05%
- **Risk Concentration Index**: 0.626

## Conclusions

### ✅ Data Integrity Confirmed

1. **Perfect Parameter Alignment**: All 21 strategies match exactly
2. **Consistent Time Periods**: Both analyze same historical data
3. **Identical Strategy Universe**: Same tickers, types, and configurations

### 📊 Complementary Analysis Value

The two files provide complementary insights:

**CSV Strengths**:

- Individual strategy performance evaluation
- Trade-level statistics and execution metrics
- Benchmark comparison and risk-adjusted returns

**JSON Strengths**:

- Portfolio-level efficiency assessment
- Strategy interaction and correlation analysis
- Risk concentration and diversification metrics

### 🔍 Key Finding: Efficiency Challenge

While individual strategies show good performance in the CSV analysis, the JSON concurrency analysis reveals a portfolio efficiency challenge:

- **High concurrent trading** (99.2%) reduces diversification benefits
- **Low independence** (0.28) indicates strategies trade together
- **Risk concentration** from synchronized positions

### 📈 Optimization Opportunities

The analysis suggests potential portfolio improvements:

1. **Reduce Concurrency**: Add filters to limit simultaneous positions
2. **Increase Independence**: Implement strategy rotation mechanisms
3. **Diversify Timeframes**: Mix daily/hourly strategies for better independence
4. **Add Uncorrelated Strategies**: Include mean-reversion or different asset classes

## Technical Notes

### Strategy ID Format

JSON uses standardized strategy identification:

```
{ticker}_{type}_{short_window}_{long_window}_{signal_window}
```

### Data Sources

- **CSV**: Generated by MA Cross analysis module
- **JSON**: Generated by Concurrency Analysis module
- **Both**: Process identical underlying strategy configurations

### Analysis Period

Both files analyze the same historical period with daily timeframe data, ensuring temporal consistency for meaningful comparison.
