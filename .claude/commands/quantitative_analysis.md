# Comprehensive Quantitative Analysis

This command performs advanced quantitative analysis on trading strategy data, providing professional-grade insights and recommendations for portfolio optimization.

## Features

- **Strategy Performance Analysis**: Risk-adjusted metrics, efficiency scores, rankings
- **Portfolio Optimization**: Correlation analysis, diversification metrics, enhancement analysis
- **Risk Assessment**: VaR calculations, Monte Carlo simulation, drawdown analysis
- **Professional Reporting**: Executive summary, detailed analysis, actionable recommendations
- **Data Export**: JSON metrics export for further analysis

## Usage

### Basic Analysis

```bash
python quantitative_analysis.py
```

### Advanced Options

```bash
# Export correlation charts and performance visualizations
python quantitative_analysis.py --export-charts

# Run Monte Carlo simulation with custom number of simulations
python quantitative_analysis.py --monte-carlo-sims 50000

# Export only JSON format
python quantitative_analysis.py --output-format json

# Verbose logging
python quantitative_analysis.py --verbose
```

## Data Sources

The analysis leverages multiple data sources:

1. **trades.csv**: 13 strategies (existing portfolio)
2. **incoming.csv**: 24 strategies (potential new positions)
3. **Trade History JSON**: Enhancement data from concurrency analysis with additional metrics

## Output Files

All output files are saved to the `/reports/` directory:

- **Comprehensive Report** (`quantitative_analysis_report_YYYYMMDD_HHMMSS.txt`): Professional analysis report
- **Strategy Metrics** (`strategy_metrics_YYYYMMDD_HHMMSS.json`): Detailed metrics in JSON format
- **Charts** (optional): Correlation matrices and performance visualizations

## Report Sections

### Executive Summary

- Key findings and high-level metrics
- Portfolio comparison overview
- Enhancement impact analysis

### Existing Portfolio Analysis

- 13 strategies with comprehensive metrics
- Top performers and risk contributors
- Portfolio-level risk assessment

### Incoming Strategies Analysis

- 24 potential new strategies
- Performance comparison with existing portfolio
- Integration recommendations

### Portfolio Enhancement Analysis

- Expected return improvement/degradation
- Risk-adjusted return changes
- Diversification impact
- Specific enhancement recommendations

### Monte Carlo Simulation

- 1-year portfolio projections
- Confidence intervals
- Probability distributions
- Risk scenario analysis

### Actionable Recommendations

- Specific trading guidance
- Risk management suggestions
- Diversification recommendations
- Position sizing adjustments

## Key Metrics Analyzed

- **Returns**: Total return, annualized return, risk-adjusted returns
- **Risk**: Sharpe ratio, Sortino ratio, Calmar ratio, maximum drawdown
- **Statistical**: VaR (95%, 99%), skewness, kurtosis, correlation
- **Performance**: Win rate, profit factor, expectancy per trade
- **Portfolio**: Diversification ratio, correlation matrix, enhancement impact

## Integration with Existing Framework

This analysis tool integrates seamlessly with the existing concurrency analysis framework:

- Uses the same data sources and directory structure
- Leverages existing logging and error handling
- Compatible with existing portfolio management tools
- Extends the analysis capabilities without disrupting current workflows

## Professional Output

The generated reports provide institutional-quality analysis suitable for:

- Investment committee presentations
- Risk management reviews
- Portfolio optimization decisions
- Strategy selection and allocation
- Performance attribution analysis
