# Quick Start Guide

Get up and running with the trading system in 5 minutes.

## Prerequisites

- Python 3.8+
- Poetry (recommended) or pip
- Git

## Installation

### Option 1: Using Poetry (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd trading

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Option 2: Using pip

```bash
# Clone the repository
git clone <repository-url>
cd trading

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## First Steps

### 1. Initialize the System

```bash
# Initialize with default configuration
trading-cli init

# Verify installation
trading-cli --help
```

### 2. Run Your First Strategy Analysis

```bash
# Quick analysis with default parameters
trading-cli strategy run --ticker AAPL --strategy SMA

# Preview with dry run
trading-cli strategy run --ticker AAPL --strategy SMA --dry-run
```

### 3. Check Results

```bash
# View generated portfolio files
ls csv/portfolios/

# View the latest results
trading-cli portfolio list --recent
```

## Basic Commands

### Strategy Analysis

```bash
# Single ticker analysis
trading-cli strategy run --ticker AAPL --strategy SMA

# Multiple tickers
trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA,EMA

# Using configuration profile
trading-cli strategy run --profile ma_cross_crypto
```

### Portfolio Management

```bash
# Update portfolio results
trading-cli portfolio update --validate

# Export portfolio data
trading-cli portfolio export --format json --portfolio risk_on.csv
```

### Statistical Analysis

```bash
# Analyze portfolio performance
trading-cli spds analyze risk_on.csv

# Interactive analysis mode
trading-cli spds interactive
```

## Understanding the Output

### Strategy Analysis Results

```
csv/portfolios/          # Individual strategy portfolios
csv/portfolios_best/     # Best performing portfolios
csv/portfolios_filtered/ # Filtered portfolios by criteria
```

### Statistical Analysis Results

```
exports/statistical_analysis/     # Statistical analysis exports
exports/backtesting_parameters/   # Backtesting parameter exports
```

## Common Use Cases

### 1. Daily Strategy Analysis

```bash
# Morning routine: analyze key stocks
trading-cli strategy run --ticker AAPL,MSFT,GOOGL,AMZN --strategy SMA,EMA

# Update portfolios
trading-cli portfolio update --validate --export-format json
```

### 2. Portfolio Performance Review

```bash
# Analyze current positions
trading-cli spds analyze live_signals.csv

# Generate comprehensive report
trading-cli trade-history update --portfolio live_signals --refresh-prices
```

### 3. Strategy Optimization

```bash
# Parameter sweep analysis
trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50

# Validate results
trading-cli portfolio validate --portfolio sweep_results.csv
```

## Configuration

### Using Profiles

Create custom configuration profiles in `app/cli/profiles/`:

```yaml
# my_strategy.yaml
metadata:
  name: my_strategy
  description: Custom strategy configuration

config_type: strategy
config:
  ticker: [AAPL, MSFT, GOOGL]
  strategy_types: [SMA, EMA]
  windows: 50
  minimums:
    win_rate: 0.6
    trades: 50
```

Use the profile:

```bash
trading-cli strategy run --profile my_strategy
```

### Environment Variables

```bash
# Set default configuration
export TRADING_CONFIG_PATH=/path/to/config
export TRADING_LOG_LEVEL=INFO

# Override specific settings
export TRADING_MIN_TRADES=100
export TRADING_WIN_RATE=0.65
```

## Getting Help

### Command Help

```bash
# General help
trading-cli --help

# Command-specific help
trading-cli strategy --help
trading-cli portfolio --help
trading-cli spds --help
```

### System Health Check

```bash
# Check system status
trading-cli tools health

# Validate configuration
trading-cli config validate
```

## Next Steps

1. **Read the [User Guide](../USER_GUIDE.md)** for comprehensive documentation
2. **Explore [Configuration Management](../features/CONFIGURATION.md)** for advanced configuration
3. **Check [Strategy Analysis](../features/STRATEGY_ANALYSIS.md)** for detailed strategy documentation
4. **Review [Performance Optimization](../performance/PERFORMANCE_OPTIMIZATION_GUIDE.md)** for scaling tips

## Troubleshooting

### Common Issues

**Command not found**:

```bash
# Make sure you're in the right directory and virtual environment
pwd
which python
```

**Permission denied**:

```bash
# Check file permissions
ls -la app/cli/
```

**Configuration errors**:

```bash
# Validate configuration
trading-cli config validate

# Reset to defaults
trading-cli config reset
```

### Getting Support

1. Check the [troubleshooting guide](../troubleshooting/COMMON_ISSUES.md)
2. Review the [error message reference](../troubleshooting/ERROR_MESSAGES.md)
3. Use the system health check: `trading-cli tools health`

---

_You're now ready to start using the trading system! Continue with the [User Guide](../USER_GUIDE.md) for more detailed information._
