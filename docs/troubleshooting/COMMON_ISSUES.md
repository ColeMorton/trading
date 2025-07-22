# Common Issues and Solutions

This guide covers the most frequently encountered issues and their solutions.

## Installation Issues

### Python Version Compatibility

**Problem**: Error messages about Python version compatibility.

**Solution**:

```bash
# Check Python version
python --version

# Ensure Python 3.8+ is installed
python3 --version

# Initialize and test CLI
trading-cli init
trading-cli --help
```

### Poetry Installation Issues

**Problem**: Poetry not found or installation fails.

**Solution**:

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or use pip
pip install poetry

# Verify installation
poetry --version
```

### Dependency Installation Failures

**Problem**: Package installation fails during `poetry install`.

**Solution**:

```bash
# Update Poetry
poetry self update

# Clear Poetry cache
poetry cache clear pypi --all

# Install with verbose output
poetry install -vvv

# Alternative: Use pip
pip install -r requirements.txt
```

## Configuration Issues

### Configuration File Not Found

**Problem**: `Configuration file not found` error.

**Solution**:

```bash
# Initialize configuration
trading-cli init

# Check configuration directory
ls -la app/cli/profiles/

# Validate configuration
trading-cli config validate
```

### Profile Loading Errors

**Problem**: Profile fails to load or validation errors.

**Solution**:

```bash
# List available profiles
trading-cli config list

# Validate specific profile
trading-cli config validate --profile ma_cross_crypto

# Reset to default profile
trading-cli config reset --profile ma_cross_crypto
```

### Invalid Configuration Values

**Problem**: Configuration validation errors.

**Solution**:

```bash
# Check configuration syntax
trading-cli config validate --strict

# Review configuration file
cat app/cli/profiles/your_profile.yaml

# Use default values
trading-cli strategy run --ticker AAPL --strategy SMA  # Without profile
```

## Data Issues

### Market Data Download Failures

**Problem**: Unable to download market data from Yahoo Finance.

**Solution**:

```bash
# Check internet connection
ping finance.yahoo.com

# Use different date range
trading-cli strategy run --ticker AAPL --strategy SMA --start-date 2023-01-01

# Try different ticker
trading-cli strategy run --ticker MSFT --strategy SMA

# Enable verbose logging
trading-cli strategy run --ticker AAPL --strategy SMA --verbose
```

### Invalid Ticker Symbols

**Problem**: "Ticker not found" or "No data available" errors.

**Solution**:

```bash
# Verify ticker symbol
# Check Yahoo Finance directly: https://finance.yahoo.com/quote/AAPL

# Use valid ticker symbols
trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA

# Check ticker format for crypto
trading-cli strategy run --ticker BTC-USD --strategy SMA
```

### Insufficient Data

**Problem**: "Insufficient data for analysis" errors.

**Solution**:

```bash
# Extend data period
trading-cli strategy run --ticker AAPL --strategy SMA --data-period 5Y

# Reduce minimum trade requirements
trading-cli strategy run --ticker AAPL --strategy SMA --min-trades 10

# Use different strategy parameters
trading-cli strategy run --ticker AAPL --strategy SMA --fast-window 10 --slow-window 30
```

## Strategy Analysis Issues

### No Strategies Meet Criteria

**Problem**: "No strategies meet the specified criteria" message.

**Solution**:

```bash
# Relax criteria
trading-cli strategy run --ticker AAPL --strategy SMA --min-trades 10 --min-win-rate 0.3

# Check with dry run
trading-cli strategy run --ticker AAPL --strategy SMA --dry-run

# Use different time period
trading-cli strategy run --ticker AAPL --strategy SMA --start-date 2020-01-01
```

### Strategy Execution Timeouts

**Problem**: Strategy analysis takes too long or times out.

**Solution**:

```bash
# Enable parallel processing
trading-cli strategy run --ticker AAPL,MSFT --strategy SMA --parallel

# Reduce analysis scope
trading-cli strategy run --ticker AAPL --strategy SMA --data-period 1Y

# Enable memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory
```

### Memory Issues

**Problem**: Out of memory errors during analysis.

**Solution**:

```bash
# Enable memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory

# Process fewer tickers at once
trading-cli strategy run --ticker AAPL --strategy SMA

# Use streaming processing
trading-cli strategy run --ticker AAPL --strategy SMA --stream-data

# Increase system memory or use smaller datasets
```

## Portfolio Issues

### Portfolio Files Not Found

**Problem**: "Portfolio file not found" errors.

**Solution**:

```bash
# Check portfolio directory
ls -la csv/portfolios/

# List available portfolios
trading-cli portfolio list

# Run strategy analysis first
trading-cli strategy run --ticker AAPL --strategy SMA

# Check file permissions
ls -la csv/portfolios/AAPL_D_SMA.csv
```

### Portfolio Validation Failures

**Problem**: Portfolio validation errors.

**Solution**:

```bash
# Check portfolio format
head csv/portfolios/AAPL_D_SMA.csv

# Validate without strict mode
trading-cli portfolio validate --portfolio AAPL_D_SMA.csv

# Regenerate portfolio
trading-cli strategy run --ticker AAPL --strategy SMA
```

### Portfolio Update Issues

**Problem**: Portfolio update fails or produces errors.

**Solution**:

```bash
# Update without validation
trading-cli portfolio update

# Update specific portfolio
trading-cli portfolio update --portfolio risk_on.csv

# Clear and regenerate
rm csv/portfolios_best/*
trading-cli portfolio update --validate
```

## Statistical Analysis Issues

### SPDS Analysis Failures

**Problem**: Statistical analysis fails or produces errors.

**Solution**:

```bash
# Check system health
trading-cli spds health

# Try different data source
trading-cli spds analyze risk_on.csv --data-source equity-curves

# Use demo mode
trading-cli spds demo

# Check portfolio exists
trading-cli spds list-portfolios
```

### Confidence Level Issues

**Problem**: Statistical significance errors.

**Solution**:

```bash
# Lower confidence level
trading-cli spds analyze risk_on.csv --confidence-level 0.8

# Use different analysis method
trading-cli spds analyze risk_on.csv --data-source both

# Check data quality
trading-cli trade-history validate --portfolio risk_on
```

### SPDS Data Source Warnings

**Problem**: Seeing "Strategy data not found" warnings but analysis still completes.

**Explanation**: This is expected behavior! SPDS has a robust multi-layer fallback system:

1. **Primary**: Tries to match Position_UUIDs to trade history files
2. **Fallback**: Uses equity curve analysis when trade history is unavailable
3. **Result**: Analysis completes successfully using the best available data source

**Common Scenarios**:

- **Position_UUID format mismatch**: `CRWD_EMA_5_21_2025-04-14` vs trade history file `CRWD_D_EMA_5_21.json`
- **Missing trade history files**: Strategy positions exist but individual trade data is not available
- **Multi-source analysis**: System successfully uses equity curves as fallback

**Solutions**:

```bash
# Check data source mapping with verbose output
trading-cli spds analyze live_signals.csv --verbose

# Validate specific portfolio data sources
trading-cli spds health

# Force equity curve analysis (recommended for position-based portfolios)
trading-cli spds analyze live_signals.csv --data-source equity-curves

# Use comprehensive analysis when both sources are available
trading-cli spds analyze live_signals.csv --data-source both
```

**Understanding the Messages**:

- ✅ `"Primary strategy data not found - checking fallback sources"` = Normal operation
- ✅ `"Using equity curve analysis (fallback mode enabled)"` = System working correctly
- ✅ `"Export validation passed"` = Analysis completed successfully
- ❌ Only worry if final analysis fails completely

**When to Take Action**:

- **Never**: If analysis completes with results table showing exit signals
- **Sometimes**: If you specifically need trade-level data and only equity analysis is available
- **Always**: If the final analysis fails or produces no results

### Position_UUID to Trade History Mapping Issues

**Problem**: Strategies shown as "Strategy data not found" even though trade history files exist.

**Root Cause**: Naming pattern mismatch between Position_UUIDs and trade history filenames.

**Example Mismatch**:

```
Position UUID: CRWD_EMA_5_21_2025-04-14
Trade History:  CRWD_D_EMA_5_21.json
```

**Solution**:

```bash
# Check current mapping status
trading-cli spds analyze live_signals.csv --verbose

# Validate data source mapping
ls json/trade_history/ | grep CRWD
ls data/raw/positions/ | head -5

# The system now automatically handles these mismatches
# No manual intervention required - fallback analysis will be used
```

**New Enhanced Pattern Matching** (Fixed in latest version):

The system now correctly translates Position_UUIDs to trade history filenames:

- Removes date suffixes (`_2025-04-14`)
- Handles ticker prefixes (`CRWD_EMA_5_21` → `EMA_5_21`)
- Adds timeframe indicators (`EMA_5_21` → `CRWD_D_EMA_5_21.json`)

### SPDS Fallback Analysis Quality

**Problem**: Concerned about analysis quality when using fallback mode.

**Explanation**: SPDS fallback analysis is highly reliable:

- **Equity curve analysis** provides robust statistical metrics
- **Portfolio-level analysis** captures overall strategy performance
- **Bootstrap validation** ensures statistical significance
- **Export validation** confirms data quality before final results

**Quality Indicators**:

```bash
# Check analysis quality metrics
trading-cli spds analyze live_signals.csv --output-format json

# Look for these quality indicators in results:
# - confidence_rate: 1.0 (all strategies analyzed)
# - signal_distribution: Shows signal breakdown
# - export_validation: "passed"
```

**Best Practices**:

1. **Use `--verbose` flag** to understand which data sources are being used
2. **Check export validation** - if it passes, results are reliable
3. **Review confidence levels** - high confidence indicates robust analysis
4. **Compare with trade history** when available for validation

## Performance Issues

### Slow Execution

**Problem**: Commands take too long to execute.

**Solution**:

```bash
# Enable parallel processing
trading-cli strategy run --ticker AAPL,MSFT --strategy SMA --parallel

# Use memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory

# Reduce analysis scope
trading-cli strategy run --ticker AAPL --strategy SMA --data-period 1Y

# Profile performance
trading-cli strategy run --ticker AAPL --strategy SMA --verbose
```

### High Memory Usage

**Problem**: System uses too much memory.

**Solution**:

```bash
# Enable memory optimization
trading-cli strategy run --ticker AAPL --strategy SMA --optimize-memory

# Process fewer tickers
trading-cli strategy run --ticker AAPL --strategy SMA

# Use streaming processing
trading-cli strategy run --ticker AAPL --strategy SMA --stream-data

# Monitor memory usage
trading-cli tools health --detailed
```

## File System Issues

### Permission Denied

**Problem**: Permission denied errors when accessing files.

**Solution**:

```bash
# Check file permissions
ls -la csv/
ls -la exports/

# Fix permissions
chmod -R 755 csv/
chmod -R 755 exports/

# Run with appropriate user
sudo trading-cli strategy run --ticker AAPL --strategy SMA
```

### Disk Space Issues

**Problem**: Not enough disk space for exports.

**Solution**:

```bash
# Check disk space
df -h

# Clean up old files
find csv/ -name "*.csv" -mtime +30 -delete
find exports/ -name "*.json" -mtime +30 -delete

# Use different export directory
export TRADING_EXPORT_PATH=/path/to/larger/disk
```

### File Corruption

**Problem**: Corrupted CSV or JSON files.

**Solution**:

```bash
# Check file integrity
python -c "import pandas as pd; print(pd.read_csv('csv/portfolios/AAPL_D_SMA.csv').head())"

# Regenerate corrupted files
trading-cli strategy run --ticker AAPL --strategy SMA

# Clear cache and regenerate
rm -rf /tmp/trading_cache/
trading-cli strategy run --ticker AAPL --strategy SMA
```

## Network Issues

### Connection Timeouts

**Problem**: Network timeouts when downloading data.

**Solution**:

```bash
# Check internet connection
ping finance.yahoo.com

# Use cached data if available
trading-cli strategy run --ticker AAPL --strategy SMA --use-cache

# Retry with different time period
trading-cli strategy run --ticker AAPL --strategy SMA --start-date 2023-01-01

# Use proxy if needed
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

## Debugging Techniques

### Enable Verbose Logging

```bash
# Global verbose mode
trading-cli --verbose strategy run --ticker AAPL --strategy SMA

# Specific command verbose mode
trading-cli strategy run --ticker AAPL --strategy SMA --verbose

# Set log level
trading-cli --log-level DEBUG strategy run --ticker AAPL --strategy SMA
```

### Use Dry Run Mode

```bash
# Preview without execution
trading-cli strategy run --ticker AAPL --strategy SMA --dry-run

# Check configuration
trading-cli config validate --profile ma_cross_crypto
```

### System Health Checks

```bash
# Overall system health
trading-cli tools health --detailed

# Specific component health
trading-cli spds health --detailed
trading-cli trade-history health --detailed
```

### Manual Validation

```bash
# Check individual components
python -c "import yfinance as yf; print(yf.download('AAPL', period='1y').head())"

# Validate file formats
python -c "import pandas as pd; print(pd.read_csv('csv/portfolios/AAPL_D_SMA.csv').info())"

# Check dependencies
python -c "import app.cli.main; print('CLI module loads successfully')"
```

## Getting Help

### Built-in Help

```bash
# General help
trading-cli --help

# Command-specific help
trading-cli strategy --help
trading-cli portfolio --help
trading-cli spds --help
```

### System Information

```bash
# System health
trading-cli tools health --detailed

# Configuration status
trading-cli config validate

# Version information
trading-cli --version
```

### Log Files

```bash
# Check log files
tail -f logs/trading.log

# Find log files
find . -name "*.log" -type f

# View specific log level
grep ERROR logs/trading.log
```

## Common Error Messages

### "ModuleNotFoundError: No module named 'app'"

**Solution**: Ensure you're running from the correct directory and using the correct Python environment.

### "TypeError: 'NoneType' object is not subscriptable"

**Solution**: Check that all required data is present and valid.

### "FileNotFoundError: [Errno 2] No such file or directory"

**Solution**: Verify file paths and ensure all required files exist.

### "KeyError: 'column_name'"

**Solution**: Check that the expected columns exist in your data files.

### "ValueError: Invalid configuration parameter"

**Solution**: Validate your configuration using `trading-cli config validate`.

---

_If you encounter an issue not covered here, check the [debugging guide](DEBUGGING.md) or review the [command reference](../reference/COMMAND_REFERENCE.md)._
