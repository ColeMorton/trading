# Statistical Performance Divergence System - Simplified Interface

## Overview

The Statistical Performance Divergence System (SPDS) provides advanced statistical analysis for trading portfolios with a dramatically simplified interface. Instead of complex configuration, you only need **two parameters**:

1. **PORTFOLIO** - Portfolio filename (e.g., "risk_on.csv")
2. **USE_TRADE_HISTORY** - Data source: trade history (True) or equity curves (False)

## Quick Start

```python
from app.tools.portfolio_analyzer import analyze_portfolio

# Analyze portfolio with trade history - ONE LINE!
results, summary = await analyze_portfolio("risk_on.csv", use_trade_history=True)

print(f"Immediate exits: {summary['immediate_exits']}")
print(f"Strong sells: {summary['strong_sells']}")
```

## File Structure

The system automatically locates files based on the portfolio name:

```
./csv/strategies/risk_on.csv     # Portfolio definition
./csv/positions/risk_on.csv      # Trade history (same filename)
./json/return_distribution/      # Asset return data (auto-loaded)
```

## Usage Examples

### Basic Portfolio Analysis

```python
from app.tools.portfolio_analyzer import PortfolioStatisticalAnalyzer

# Method 1: Full analyzer interface
analyzer = PortfolioStatisticalAnalyzer("risk_on.csv", use_trade_history=True)
results = await analyzer.analyze()
summary = analyzer.get_summary_report(results)

# Method 2: Quick one-liner
results, summary = await analyze_portfolio("risk_on.csv", use_trade_history=True)
```

### Portfolio CSV Format

Your portfolio CSV should be in `./csv/strategies/` with columns:

```csv
strategy_name,ticker,allocation,risk_level
AAPL_SMA_20_50,AAPL,0.15,medium
TSLA_EMA_12_26,TSLA,0.12,high
NVDA_SMA_15_35,NVDA,0.10,high
```

### Trade History CSV Format

If using trade history (`use_trade_history=True`), place in `./csv/positions/` with same filename:

```csv
strategy_name,ticker,entry_date,exit_date,return,mfe,mae,duration_days
AAPL_SMA_20_50,AAPL,2024-01-15,2024-02-28,0.187,0.234,0.057,44
TSLA_EMA_12_26,TSLA,2024-02-01,2024-03-15,0.143,0.189,0.034,43
```

## Data Source Options

### Trade History Mode (`use_trade_history=True`)

- **Primary**: Individual trade data from `./csv/positions/{portfolio}`
- **Fallback**: Equity curve data if trade history unavailable
- **Benefits**: Individual trade-level statistical precision, MFE/MAE analysis

### Equity Curve Mode (`use_trade_history=False`)

- **Primary**: Strategy equity curves from existing equity data directories
- **Benefits**: Works with any equity curve data, no trade history required

## Results and Signals

### Exit Signals

- **EXIT_IMMEDIATELY** - Statistical exhaustion detected (95th+ percentile)
- **STRONG_SELL** - High statistical divergence (90-95th percentile)
- **SELL** - Moderate divergence (80-90th percentile)
- **HOLD** - Below statistical thresholds

### Summary Report

```python
summary = {
    'portfolio': 'risk_on.csv',
    'total_strategies': 12,
    'immediate_exits': 3,
    'strong_sells': 2,
    'holds': 7,
    'confidence_rate': 0.83  # 83% high confidence
}
```

## Advanced Usage

### Configuration Options

```python
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig

# Simple configuration
config = StatisticalAnalysisConfig.create("risk_on.csv", use_trade_history=True)

# Access file paths
portfolio_path = config.get_portfolio_file_path()      # ./csv/strategies/risk_on.csv
trade_history_path = config.get_trade_history_file_path()  # ./csv/positions/risk_on.csv
```

### Individual Strategy Analysis

```python
# Get detailed results for specific strategies
for strategy_name, result in results.items():
    if hasattr(result, 'exit_signals') and result.exit_signals:
        signal = result.exit_signals.primary_signal
        confidence = result.exit_signals.confidence
        print(f"{strategy_name}: {signal} (confidence: {confidence:.1%})")
```

### Batch Portfolio Analysis

```python
# Analyze multiple portfolios
portfolios = ["risk_on.csv", "conservative.csv", "momentum.csv"]

for portfolio in portfolios:
    results, summary = await analyze_portfolio(portfolio, use_trade_history=True)
    print(f"{portfolio}: {summary['immediate_exits']} immediate exits")
```

## Interface Comparison

### Before (Complex)

```python
# OLD: 20+ parameters, complex configuration
config = SPDSConfig(
    USE_TRADE_HISTORY=True,
    TRADE_HISTORY_PATH="./csv/positions/",
    PERCENTILE_THRESHOLD=95,
    DUAL_LAYER_THRESHOLD=0.85,
    RARITY_THRESHOLD=0.05,
    MULTI_TIMEFRAME_AGREEMENT=3,
    SAMPLE_SIZE_MINIMUM=15,
    # ... 15+ more parameters
)
service = StatisticalAnalysisService(config=config)
# Then manually loop through strategies...
```

### After (Simple)

```python
# NEW: 2 parameters, automatic everything
results, summary = await analyze_portfolio("risk_on.csv", use_trade_history=True)
```

## Error Handling

The system gracefully handles missing files:

```python
try:
    analyzer = PortfolioStatisticalAnalyzer("portfolio.csv", use_trade_history=True)
    results = await analyzer.analyze()
except FileNotFoundError as e:
    print(f"Required file not found: {e}")
except Exception as e:
    print(f"Analysis failed: {e}")
```

### Fallback Behavior

- If trade history file missing → falls back to equity curves (if `FALLBACK_TO_EQUITY=True`)
- If individual strategy fails → continues with other strategies
- If insufficient data → returns lower confidence results

## Performance Features

### Automatic Optimizations

- **Memory Optimization**: Enabled by default for large portfolios
- **Caching**: Statistical results cached for faster subsequent runs
- **Parallel Processing**: Multiple strategies analyzed concurrently

### Sample Size Management

- **High Confidence**: 30+ trades/observations (95% confidence intervals)
- **Medium Confidence**: 15-29 trades/observations (90% confidence intervals)
- **Low Confidence**: 5-14 trades/observations (80% confidence intervals)
- **Bootstrap Validation**: Enhanced accuracy for small samples

## Statistical Features

### Dual-Layer Analysis

- **Layer 1**: Asset-level return distributions (market context)
- **Layer 2**: Strategy-level performance distributions
- **Convergence**: Alignment between both layers for high-confidence signals

### Risk Management

- **VaR Integration**: Value-at-Risk calculations across timeframes
- **Percentile-Based Thresholds**: Statistical rarity detection
- **Multi-Timeframe Validation**: Cross-timeframe signal confirmation

## Demo Script

Run the demo to see the simplified interface in action:

```bash
python app/tools/demo_simplified_interface.py
```

This creates sample files and demonstrates all features.

## Migration from Complex Interface

If you have existing code using the complex interface:

### Old Code

```python
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService
from app.tools.config.statistical_analysis_config import SPDSConfig

config = SPDSConfig(USE_TRADE_HISTORY=True, PERCENTILE_THRESHOLD=95, ...)
service = StatisticalAnalysisService(config=config)

for strategy in strategies:
    result = await service.analyze_position(strategy.name, strategy.ticker)
```

### New Code

```python
from app.tools.portfolio_analyzer import analyze_portfolio

# Put strategies in CSV file, then:
results, summary = await analyze_portfolio("my_strategies.csv", use_trade_history=True)
```

## Technical Notes

### Portfolio CSV Requirements

- Must be in `./csv/strategies/` directory
- Must have `.csv` extension
- Should include `strategy_name` and `ticker` columns
- Additional columns (allocation, risk_level, etc.) are preserved as metadata

### Trade History CSV Requirements

- Must be in `./csv/positions/` directory
- Must have same filename as portfolio CSV
- Should include: `strategy_name`, `ticker`, `return`, `mfe`, `mae`, `duration_days`
- Optional: `entry_date`, `exit_date`, `trade_quality`

### Automatic Fallbacks

1. Trade history missing → equity curves
2. Return distribution missing → basic analysis
3. Individual strategy failure → continue with others
4. Small sample size → bootstrap validation

This simplified interface reduces the complexity from 20+ configuration parameters down to just 2, while maintaining all the advanced statistical analysis capabilities.
