# Statistical Performance Divergence System - New Architecture

## Overview

The Statistical Performance Divergence System (SPDS) provides advanced statistical analysis for trading portfolios using a streamlined **3-layer architecture**. The system has been completely modernized with scipy/numpy implementations and simplified interfaces.

**New Architecture**: CLI → SPDSAnalysisEngine → Results (replaces old 5-layer system)

## Quick Start

```python
from app.tools.spds_analysis_engine import SPDSAnalysisEngine, AnalysisRequest

# New unified analysis interface
engine = SPDSAnalysisEngine()
request = AnalysisRequest(
    analysis_type="portfolio",
    parameter="risk_on.csv",
    use_trade_history=True
)

results = await engine.analyze(request)
```

## Modern CLI Interface

```bash
# Use the updated CLI for all analysis
python -m app.tools.spds_cli_updated analyze --portfolio risk_on.csv
python -m app.tools.spds_cli_updated analyze --strategy AAPL_SMA_20_50
python -m app.tools.spds_cli_updated health
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
from app.tools.spds_analysis_engine import SPDSAnalysisEngine, AnalysisRequest

# New streamlined interface - all analysis types
engine = SPDSAnalysisEngine()

# Portfolio analysis
portfolio_request = AnalysisRequest(
    analysis_type="portfolio",
    parameter="risk_on.csv",
    use_trade_history=True
)
results = await engine.analyze(portfolio_request)

# Strategy analysis  
strategy_request = AnalysisRequest(
    analysis_type="strategy",
    parameter="AAPL_SMA_20_50"
)
results = await engine.analyze(strategy_request)

# Position analysis
position_request = AnalysisRequest(
    analysis_type="position", 
    parameter="AAPL_SMA_20_50_20250101"
)
results = await engine.analyze(position_request)
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
from app.tools.spds_config import SPDSConfig

# New unified configuration
config = SPDSConfig(
    USE_TRADE_HISTORY=True,
    PORTFOLIO="risk_on.csv",
    PERCENTILE_THRESHOLD=95,
    CONVERGENCE_THRESHOLD=0.85
)

# Configuration presets available
config = SPDSConfig.conservative()  # Conservative analysis settings
config = SPDSConfig.aggressive()   # Aggressive analysis settings
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

## Architecture Evolution

### Before (5-Layer Architecture - Deprecated)

```python
# OLD: Complex 5-layer architecture (REMOVED in Phase 4)
CLI → ConfigLoader → ServiceCoordinator → StatisticalAnalysisService → DivergenceDetector → Results

# Complex service coordination (DEPRECATED)
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService
from app.tools.services.service_coordinator import ServiceCoordinator
service = StatisticalAnalysisService(config=complex_config)
coordinator = ServiceCoordinator(service)
# Manual coordination required...
```

### After (3-Layer Architecture - Current)

```python  
# NEW: Simplified 3-layer architecture (Phase 4 Complete)
CLI → SPDSAnalysisEngine → Results

# Unified analysis engine
from app.tools.spds_analysis_engine import SPDSAnalysisEngine, AnalysisRequest
engine = SPDSAnalysisEngine()
results = await engine.analyze(request)
```

## Statistical Library Improvements

### Custom Implementation (Replaced)

```python
# OLD: 230-line custom percentile estimation (REMOVED in Phase 4B)
def _estimate_percentile_rank(self, value, percentiles):
    # ... 230 lines of complex custom logic ...
    # ... extensive edge case handling ...
    # ... manual interpolation and extrapolation ...
```

### SciPy Implementation (Current)

```python
# NEW: 15-line scipy implementation (Phase 4B Complete)
def _estimate_percentile_rank(self, value, data_array):
    from scipy.stats import percentileofscore
    
    if not isinstance(data_array, np.ndarray) or len(data_array) == 0:
        return 50.0
    
    if not np.isfinite(value):
        return 50.0
    
    try:
        percentile = percentileofscore(data_array, value, kind='rank')
        return max(1.0, min(99.0, percentile))
    except Exception as e:
        self.logger.warning(f"Percentile calculation failed: {e}")
        return 50.0
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
