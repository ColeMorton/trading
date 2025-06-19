# Trading Strategy Concurrency Analysis Module

## Overview

The Concurrency Analysis Module is a sophisticated trading system component designed to analyze how multiple trading strategies work together in a portfolio. It addresses the critical question: **"Which combination of strategies works best together while minimizing risk concentration and maximizing efficiency?"**

This module provides comprehensive analysis of strategy interactions, risk concentration, and portfolio efficiency through advanced metrics and optimization algorithms.

## Key Features

### 1. Multi-Strategy Support

- **MA Cross Strategies**: SMA and EMA with customizable parameters
- **MACD Strategies**: Traditional MACD with signal line
- **ATR Strategies**: ATR-based trailing stop strategies
- **Synthetic Tickers**: Support for pair trading (e.g., STRK_MSTR)
- **Position Types**: Both long and short positions

### 2. Concurrency Analysis

- **Correlation Analysis**: Measures statistical relationships between strategies
- **Independence Metrics**: Evaluates how independently strategies operate
- **Activity Tracking**: Monitors strategy activity levels
- **Risk Concentration**: Identifies periods of concentrated exposure

### 3. Efficiency Scoring

The module uses a sophisticated efficiency scoring system:

```
Base Efficiency = Diversification × Independence × Activity
Risk-Adjusted Efficiency = Base Efficiency × Expectancy × Risk Factor
```

### 4. Optimization Engine

- **Permutation Analysis**: Systematically evaluates all strategy combinations
- **Optimal Subset Selection**: Finds the best combination of strategies
- **Progress Tracking**: Real-time progress updates for large analyses
- **Configurable Constraints**: Minimum strategies per combination

### 5. Risk Management

- **VaR and CVaR**: Value at Risk calculations at 95% and 99% confidence
- **Risk Contributions**: Individual strategy risk contributions
- **Stop Loss Integration**: Adjusts metrics for stop loss strategies
- **Allocation Management**: Position sizing and capital allocation

### 6. Advanced Metrics

- **Signal Quality Score**: 0-10 scale evaluation of signal effectiveness
- **Horizon Analysis**: Performance across 1, 3, 5, 10-day horizons
- **Win Rate & Profit Factor**: Traditional performance metrics
- **Sharpe, Sortino, Calmar Ratios**: Risk-adjusted returns

## Quick Start

### Basic Usage

```python
from app.concurrency.review import run_concurrency_review

# Run analysis on a portfolio
run_concurrency_review("crypto_d_20250508")
```

### Command Line Usage

```bash
# Basic analysis
python app/concurrency/review.py crypto_d_20250508

# With optimization
python app/concurrency/review.py crypto_d_20250508 --optimize

# Custom configuration
python app/concurrency/review.py crypto_d_20250508 --refresh --visualize
```

### Configuration Options

```python
config = {
    "PORTFOLIO": "portfolio_name.json",  # or .csv
    "BASE_DIR": "./logs",
    "REFRESH": True,                     # Refresh market data
    "VISUALIZATION": True,               # Generate charts
    "OPTIMIZE": True,                    # Run permutation analysis
    "OPTIMIZE_MIN_STRATEGIES": 3,        # Min strategies per subset
    "ALLOCATION_MODE": "SIGNAL_COUNT",   # Allocation strategy
    "REPORT_INCLUDES": {
        "TICKER_METRICS": True,
        "STRATEGIES": True,
        "STRATEGY_RELATIONSHIPS": True
    }
}
```

## Architecture

```
app/concurrency/
├── review.py              # Main entry point
├── config.py             # Configuration types and validation
├── config_defaults.py    # Default settings
├── strategy_efficiency_guide.md  # Comprehensive documentation
├── error_handling/       # Robust error management system
│   ├── exceptions.py     # Custom exception hierarchy
│   ├── decorators.py     # Error handling decorators
│   ├── context_managers.py
│   ├── recovery.py       # Recovery strategies
│   └── registry.py       # Error tracking and analytics
└── tools/
    ├── analysis.py       # Core analysis algorithms
    ├── permutation.py    # Optimization engine
    ├── runner.py         # Execution orchestration
    ├── strategy_processor.py  # Strategy execution
    ├── signal_quality.py # Advanced signal metrics
    ├── risk_metrics.py   # Risk calculations
    ├── efficiency.py     # Efficiency calculations
    ├── visualization.py  # Interactive charts
    └── report/          # Report generation
        ├── generator.py
        ├── metrics.py
        └── strategy.py
```

## Core Concepts

### 1. Strategy Efficiency

Strategy efficiency measures how effectively multiple strategies work together:

- **Diversification**: How different strategies are from each other (1 - correlation)
- **Independence**: How independently strategies operate
- **Activity**: How often strategies are in positions vs. idle

### 2. Correlation Analysis

Correlation measures the statistical relationship between strategy positions:

- **1**: Perfect positive correlation (strategies move identically)
- **0**: No correlation (strategies move independently)
- **-1**: Perfect negative correlation (strategies move oppositely)

### 3. Risk-Adjusted Performance

The module combines structural efficiency with performance metrics:

- **Expectancy**: Expected return per trade
- **Risk Factor**: Inverse of risk contribution
- **Allocation**: Position sizing weight

### 4. Strategy Identification

Strategies are uniquely identified using a standardized format:

```
{ticker}_{type}_{short}_{long}_{signal}
```

Examples:

- `BTC-USD_SMA_80_85_0`: Bitcoin SMA strategy
- `AAPL_EMA_19_21_0`: Apple EMA strategy
- `MSTR_MACD_12_26_9`: MicroStrategy MACD strategy

## Allocation Strategies

The module supports multiple allocation strategies:

1. **Equal**: Simple equal weighting
2. **Signal Count**: Weight by number of signals (default)
3. **Performance**: Weight by historical performance
4. **Risk-Adjusted**: Combines Sharpe, win rate, and drawdown
5. **Inverse Volatility**: Higher allocation to lower volatility
6. **Custom**: User-defined allocations from CSV

## Output Formats

### 1. JSON Reports

Comprehensive analysis results in structured JSON format:

```json
{
    "portfolio_metrics": {
        "concurrency": {...},
        "efficiency": {...},
        "risk": {...},
        "signals": {...}
    },
    "ticker_metrics": {...},
    "strategies": [...]
}
```

### 2. Visualizations

Interactive Plotly charts showing:

- Price movements with position indicators
- Strategy-specific overlays (e.g., ATR stops)
- Concurrency heatmap
- Performance statistics

### 3. Optimization Reports

Comparison between full portfolio and optimal subset:

- Efficiency improvement percentage
- Strategy selection rationale
- Detailed metrics comparison

## Performance Considerations

1. **Data Processing**: Uses Polars for high-performance operations
2. **Vectorized Calculations**: Efficient position and correlation metrics
3. **Caching**: Expensive computations are cached
4. **Progress Tracking**: Time estimates for long-running analyses

## Error Handling

The module includes a comprehensive error handling system:

- Custom exception hierarchy
- Automatic retry with backoff
- Context-aware error messages
- Error analytics and reporting

## Integration Points

1. **Data Sources**

   - CSV portfolios from MA cross analysis
   - JSON strategy configurations
   - Price data via yfinance

2. **Downstream Usage**

   - Portfolio optimization decisions
   - Risk management insights
   - Strategy selection criteria

3. **API Integration**
   - Can be called programmatically
   - Command-line interface
   - FastAPI endpoint compatibility

## Best Practices

1. **Portfolio Construction**

   - Include diverse strategy types (trend, mean-reversion)
   - Mix different timeframes
   - Target correlations below 0.7

2. **Optimization**

   - Start with smaller strategy sets for faster analysis
   - Use `OPTIMIZE_MAX_PERMUTATIONS` for large portfolios
   - Review both full and optimal results

3. **Risk Management**
   - Monitor risk concentration metrics
   - Set appropriate stop losses
   - Balance allocations across strategies

## Examples

### Example 1: Basic Analysis

```python
from app.concurrency.review import run_concurrency_review

# Analyze a crypto portfolio
results = run_concurrency_review("crypto_d_20250508")
print(f"Portfolio efficiency: {results['portfolio_metrics']['efficiency']['score']}")
```

### Example 2: Custom Configuration

```python
config = {
    "PORTFOLIO": "btc_strategies.csv",
    "ALLOCATION_MODE": "RISK_ADJUSTED",
    "OPTIMIZE": True,
    "VISUALIZATION": True
}

results = run_concurrency_review("btc_strategies", config)
```

### Example 3: Command Line with Options

```bash
# Full analysis with optimization and visualization
python app/concurrency/review.py my_portfolio --optimize --visualize --refresh

# Quick analysis without data refresh
python app/concurrency/review.py my_portfolio --no-refresh
```

## Troubleshooting

### Common Issues

1. **No data found**: Ensure portfolio file exists in correct location
2. **Low efficiency scores**: Check for high correlations between strategies
3. **Memory issues**: Reduce `OPTIMIZE_MAX_PERMUTATIONS` for large portfolios

### Debug Mode

Enable detailed logging:

```python
config = {"DEBUG": True}
```

## Further Reading

- See `strategy_efficiency_guide.md` for in-depth concept explanations
- Review example portfolios in `/json/concurrency/`
- Check test files in `/tests/concurrency/` for usage patterns

## Contributing

When contributing to this module:

1. Maintain type safety with TypedDict and Pydantic
2. Add appropriate error handling
3. Update tests for new features
4. Document configuration options

## License

This module is part of the trading system and follows the project's licensing terms.
