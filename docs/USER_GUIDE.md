# Trading CLI User Guide

A comprehensive guide to using the unified trading strategy analysis CLI system.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation & Setup](#installation--setup)
3. [Core Concepts](#core-concepts)
4. [Configuration Management](#configuration-management)
5. [Strategy Analysis](#strategy-analysis)
6. [Portfolio Management](#portfolio-management)
7. [Statistical Performance Divergence System](#statistical-performance-divergence-system)
8. [Trade History Analysis](#trade-history-analysis)
9. [Concurrency Analysis](#concurrency-analysis)
10. [Advanced Usage](#advanced-usage)
11. [Troubleshooting](#troubleshooting)
12. [Command Reference](#command-reference)

## Quick Start

### 1. Initialize the System

```bash
# Initialize with default profiles
./trading-cli init

# Check system status
./trading-cli status
```

### 2. Run Your First Strategy Analysis

```bash
# Preview with dry run
./trading-cli strategy run --ticker AAPL --strategy SMA --dry-run

# Execute analysis
./trading-cli strategy run --ticker AAPL --ticker MSFT --strategy SMA --strategy EMA
```

### 3. Update Portfolio Results

```bash
# Update using default portfolio
./trading-cli portfolio update --profile default_portfolio

# Update specific portfolio with equity export
./trading-cli portfolio update --portfolio risk_on.csv --export-equity
```

### 4. Explore Available Commands

```bash
# Show all commands
./trading-cli --help

# Get help for specific command
./trading-cli strategy --help
./trading-cli config --help
```

## Installation & Setup

### Prerequisites

- Python 3.8+ with required packages:
  - `typer` - CLI framework
  - `rich` - Rich terminal output
  - `pydantic` - Type validation
  - `pyyaml` - YAML configuration

### Setup

1. **Make CLI executable**:

   ```bash
   chmod +x trading-cli
   ```

2. **Initialize system** (creates `~/.trading/profiles/`):

   ```bash
   ./trading-cli init
   ```

3. **Verify installation**:
   ```bash
   ./trading-cli status
   ```

### Optional: System-wide Installation

Add to your shell profile (`.bashrc`, `.zshrc`):

```bash
export PATH="/path/to/trading:$PATH"
alias tcli="trading-cli"
```

## Core Concepts

### Configuration Profiles

**Profiles** are YAML-based configuration files that define settings for different use cases:

- **Strategy Profiles**: Settings for MA Cross/MACD analysis
- **Portfolio Profiles**: Settings for portfolio processing
- **Concurrency Profiles**: Settings for concurrency analysis

### Profile Inheritance

Profiles can inherit from other profiles, enabling configuration reuse:

```yaml
metadata:
  name: 'my_crypto_strategy'
  description: 'Custom crypto strategy'
inherits_from: 'default_strategy'
config:
  ticker: ['BTC-USD', 'ETH-USD']
  windows: 55
```

### Type Safety

All configurations use **Pydantic models** for automatic validation:

- Invalid values are caught before execution
- Clear error messages guide corrections
- IDE support with type hints

## Configuration Management

### Listing Profiles

```bash
# List all available profiles
./trading-cli config list

# Show profile details
./trading-cli config show default_strategy

# Show resolved configuration (with inheritance)
./trading-cli config show my_profile --resolved
```

### Creating & Managing Profiles

```bash
# Create default profiles
./trading-cli config create-defaults

# Set default profile
./trading-cli config set-default ma_cross_crypto

# Validate profiles
./trading-cli config validate
./trading-cli config validate specific_profile
```

### Profile Structure

Profiles are stored in `~/.trading/profiles/` as YAML files:

```yaml
metadata:
  name: 'custom_strategy'
  description: 'Custom MA Cross strategy'
  created_at: '2025-01-15T10:30:00'
  tags: ['ma_cross', 'crypto']

inherits_from: 'default_strategy' # Optional inheritance

config_type: 'ma_cross'

config:
  ticker: ['BTC-USD', 'ETH-USD']
  strategy_types: ['SMA', 'EMA']
  windows: 89
  fast_period_range: [5, 50]
  slow_period_range: [20, 200]
  minimums:
    win_rate: 0.55
    trades: 50
    profit_factor: 1.5
```

### Default Profiles Created by `init`

#### `default_strategy`

- **Type**: `strategy`
- **Purpose**: Basic strategy analysis
- **Tickers**: AAPL, MSFT, GOOGL
- **Strategies**: SMA, EMA

#### `default_portfolio`

- **Type**: `portfolio`
- **Purpose**: Portfolio processing
- **Portfolio**: DAILY.csv
- **Features**: Basic portfolio updates

#### `default_concurrency`

- **Type**: `concurrency`
- **Purpose**: Concurrency analysis
- **Features**: Trade history export, full reporting

#### `ma_cross_crypto`

- **Type**: `ma_cross`
- **Purpose**: Cryptocurrency MA Cross analysis
- **Tickers**: BTC-USD, ETH-USD
- **Features**: Parameter sweep ready

## Strategy Analysis

### Basic Strategy Execution

```bash
# Run with default profile
./trading-cli strategy run --profile default_strategy

# Run with custom parameters
./trading-cli strategy run \
  --ticker AAPL --ticker MSFT --ticker GOOGL \
  --strategy SMA --strategy EMA \
  --windows 89 \
  --min-trades 20 \
  --min-win-rate 0.55

# Preview configuration
./trading-cli strategy run --ticker AAPL --dry-run
```

### Parameter Sweeps

```bash
# Parameter sweep for MA Cross strategies
./trading-cli strategy sweep \
  --ticker AAPL \
  --fast-min 5 --fast-max 50 \
  --slow-min 20 --slow-max 200 \
  --max-results 50

# Preview sweep parameters
./trading-cli strategy sweep --profile ma_cross_crypto --dry-run
```

### Detailed Analysis

```bash
# Analyze specific strategy configuration
./trading-cli strategy analyze AAPL \
  --strategy SMA \
  --fast 20 \
  --slow 50 \
  --show-trades
```

### Strategy Configuration Options

#### Core Parameters

- `ticker`: Single ticker or list (e.g., `AAPL` or `["AAPL", "MSFT"]`)
- `strategy_types`: Strategy types (`SMA`, `EMA`, `MACD`)
- `windows`: Look-back window for analysis
- `direction`: Trading direction (`Long` or `Short`)

#### Filtering (Minimums)

- `win_rate`: Minimum win rate (0.0 to 1.0)
- `trades`: Minimum number of trades
- `expectancy_per_trade`: Minimum expectancy per trade
- `profit_factor`: Minimum profit factor
- `sortino_ratio`: Minimum Sortino ratio

#### MA Cross Specific

- `fast_period`: Fast moving average period
- `slow_period`: Slow moving average period
- `fast_period_range`: Range for parameter sweep
- `slow_period_range`: Range for parameter sweep

## Portfolio Management

### Basic Portfolio Operations

```bash
# Update portfolio with default settings
./trading-cli portfolio update --profile default_portfolio

# Update specific portfolio
./trading-cli portfolio update --portfolio DAILY.csv

# Update with equity data export
./trading-cli portfolio update \
  --portfolio risk_on.csv \
  --export-equity \
  --refresh

# Preview configuration
./trading-cli portfolio update --portfolio test.csv --dry-run
```

### Advanced Portfolio Processing

```bash
# Process multiple portfolios
./trading-cli portfolio process \
  --input-dir ./csv/portfolios \
  --output-dir ./processed \
  --format json \
  --validate

# Aggregate portfolio results
./trading-cli portfolio aggregate \
  --by-ticker \
  --by-strategy \
  --breadth \
  --output aggregated_results.csv
```

### Portfolio Configuration Options

#### Basic Settings

- `portfolio`: Portfolio filename (with or without extension)
- `refresh`: Whether to refresh cached data
- `direction`: Trading direction
- `sort_by`: Field to sort results by
- `use_extended_schema`: Use extended schema with allocation/stop loss

#### Equity Data Export

- `export`: Enable equity data export
- `metric`: Metric to use (`mean`, `median`, `max`, `min`)
- `force_fresh_analysis`: Force regeneration of all equity files

#### Allocation & Stop Loss

- `handle_allocations`: Process allocation data
- `handle_stop_loss`: Process stop loss data
- `account_value`: Account value for position size calculation

## Statistical Performance Divergence System

The Statistical Performance Divergence System (SPDS) provides comprehensive portfolio analysis using advanced statistical methods to generate exit signals and assess portfolio performance.

### Basic SPDS Analysis

```bash
# Quick portfolio analysis with equity curves
./trading-cli spds analyze risk_on.csv

# Analysis with trade history data
./trading-cli spds analyze live_signals.csv --trade-history

# Analysis with backtesting parameter export
./trading-cli spds analyze risk_on.csv --export-backtesting --save-results results.json
```

### Advanced SPDS Features

```bash
# Custom threshold configuration
./trading-cli spds analyze portfolio.csv --percentile-threshold 90 --confidence-level high

# Export analysis results in multiple formats
./trading-cli spds export risk_on.csv --format all --output-dir ./reports/

# System health check
./trading-cli spds health

# Interactive configuration
./trading-cli spds configure
```

### SPDS Configuration Options

#### Analysis Parameters

- `percentile-threshold`: Exit signal percentile threshold (default: 95)
- `dual-layer-threshold`: Convergence threshold (default: 0.85)
- `sample-size-min`: Minimum sample size for analysis (default: 15)
- `confidence-level`: Analysis confidence level (low, medium, high)

#### Data Sources

- `--trade-history`: Use comprehensive trade history data
- `--no-trade-history`: Use equity curves only (faster analysis)

#### Output Options

- `--output-format`: Choose between table, json, or summary output
- `--export-backtesting`: Generate deterministic backtesting parameters
- `--save-results`: Save detailed results to JSON file

## Trade History Analysis

Trade History Analysis provides comprehensive tools for managing live trading positions, generating sell signals, and maintaining trade records.

### Basic Trade History Operations

```bash
# Generate sell signal report for a strategy
./trading-cli trade-history close MA_SMA_78_82

# Add new live signal position
./trading-cli trade-history add AAPL --strategy-type SMA --short-window 20 --long-window 50

# Update existing positions with current market data
./trading-cli trade-history update --portfolio live_signals

# List all available strategies
./trading-cli trade-history list
```

### Advanced Trade History Features

```bash
# Generate detailed sell report with market context
./trading-cli trade-history close CRWD_EMA_5_21 \
  --current-price 245.50 \
  --market-condition bearish \
  --output reports/CRWD_exit_analysis.md

# Add position with custom parameters
./trading-cli trade-history add BTC-USD \
  --strategy-type EMA \
  --short-window 12 \
  --long-window 26 \
  --timeframe D \
  --entry-price 45000.00

# Comprehensive system validation
./trading-cli trade-history validate --show-details
```

### Trade History Configuration Options

#### Position Management

- `strategy-type`: Strategy type (SMA, EMA, MACD)
- `short-window` / `long-window`: Period windows for moving averages
- `timeframe`: Trading timeframe (D, H, 4H, 1H)
- `entry-price`: Manual entry price override
- `quantity`: Position quantity

#### Report Generation

- `--format`: Output format (markdown, json, html)
- `--include-raw-data`: Include statistical appendices
- `--current-price`: Current market price for enhanced analysis
- `--market-condition`: Market condition context (bullish, bearish, sideways, volatile)

#### Data Management

- `--refresh-prices`: Update current market prices
- `--recalculate`: Recalculate MFE/MAE metrics
- `--update-risk`: Refresh risk assessment scores

## Concurrency Analysis

> **Note**: Concurrency commands are currently in development. Use the existing `app/concurrency/review.py` module for full functionality.

### Basic Concurrency Analysis

```bash
# Run concurrency analysis (coming soon)
./trading-cli concurrency analyze --profile default_concurrency

# Export trade history (coming soon)
./trading-cli concurrency export --portfolio portfolio.csv

# Review portfolio interactions (coming soon)
./trading-cli concurrency review --portfolio portfolio.csv
```

### Current Workaround

Until concurrency commands are implemented, use:

```bash
python app/concurrency/review.py
```

## Advanced Usage

### Custom Configuration Override

You can override any configuration parameter from the command line:

```bash
# Override multiple parameters
./trading-cli strategy run \
  --profile default_strategy \
  --ticker BTC-USD \
  --windows 55 \
  --min-trades 30
```

### Environment Variables

Set custom profiles directory:

```bash
export TRADING_PROFILES_DIR="/custom/path/profiles"
./trading-cli status
```

### Verbose Output

Enable verbose logging for debugging:

```bash
./trading-cli --verbose strategy run --ticker AAPL
```

### Batch Operations

Process multiple configurations:

```bash
# Create a script for batch operations
#!/bin/bash
for ticker in AAPL MSFT GOOGL; do
  ./trading-cli strategy run --ticker $ticker --min-trades 20
done
```

### Integration with Existing Modules

The CLI integrates seamlessly with existing modules:

```bash
# CLI approach
./trading-cli portfolio update --portfolio DAILY.csv

# Direct module approach (still works)
python app/strategies/update_portfolios.py
```

## Troubleshooting

### Common Issues

#### 1. Profile Not Found

```
Error: Profile 'my_profile' not found
```

**Solution**: Check available profiles with `./trading-cli config list`

#### 2. Invalid Configuration

```
ValidationError: Invalid win_rate value
```

**Solution**: Use `./trading-cli config validate profile_name` to check configuration

#### 3. Missing Dependencies

```
ImportError: No module named 'typer'
```

**Solution**: Install required packages:

```bash
pip install typer rich pydantic pyyaml
```

#### 4. Permission Denied

```
Permission denied: trading-cli
```

**Solution**: Make script executable:

```bash
chmod +x trading-cli
```

### Debug Mode

Enable verbose output for detailed error information:

```bash
./trading-cli --verbose command-that-fails
```

### Configuration Validation

Validate all profiles to catch issues:

```bash
./trading-cli config validate
```

### Reset Configuration

Remove profiles directory to start fresh:

```bash
rm -rf ~/.trading/profiles
./trading-cli init
```

## Command Reference

### Global Options

- `--verbose, -v`: Enable verbose output
- `--profiles-dir PATH`: Custom profiles directory
- `--help`: Show help message

### Main Commands

#### `version`

Show version information.

#### `status`

Show system status and configuration.

#### `init`

Initialize the trading CLI with default profiles.

#### `spds`

Statistical Performance Divergence System - Portfolio Analysis.

#### `trade-history`

Trade History Analysis and Position Management.

### Strategy Commands (`strategy`)

#### `run`

Execute strategy analysis with specified parameters.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--ticker, -t TEXT`: Ticker symbols (multiple allowed)
- `--strategy, -s TEXT`: Strategy types (multiple allowed)
- `--windows, -w INT`: Look-back window
- `--min-trades INT`: Minimum trades filter
- `--min-win-rate FLOAT`: Minimum win rate filter
- `--dry-run`: Preview without executing
- `--verbose, -v`: Verbose output

**Examples:**

```bash
./trading-cli strategy run --profile ma_cross_crypto
./trading-cli strategy run --ticker AAPL --ticker MSFT --strategy SMA --strategy EMA
./trading-cli strategy run --ticker BTC-USD --windows 55 --dry-run
```

#### `sweep`

Perform parameter sweep analysis for MA Cross strategies.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--ticker, -t TEXT`: Single ticker for sweep
- `--fast-min INT`: Minimum fast period
- `--fast-max INT`: Maximum fast period
- `--slow-min INT`: Minimum slow period
- `--slow-max INT`: Maximum slow period
- `--max-results INT`: Maximum results to display
- `--dry-run`: Preview without executing

**Examples:**

```bash
./trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50
./trading-cli strategy sweep --profile ma_cross_crypto --max-results 20
```

#### `analyze`

Analyze a single strategy configuration in detail.

**Arguments:**

- `TICKER`: Ticker symbol to analyze

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--strategy, -s TEXT`: Strategy type (SMA, EMA, MACD)
- `--fast INT`: Fast period parameter
- `--slow INT`: Slow period parameter
- `--show-trades`: Show individual trade details

**Examples:**

```bash
./trading-cli strategy analyze AAPL --strategy SMA --fast 20 --slow 50
./trading-cli strategy analyze BTC-USD --strategy EMA --show-trades
```

### Portfolio Commands (`portfolio`)

#### `update`

Update portfolio results and aggregation.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--portfolio, -f TEXT`: Portfolio filename
- `--refresh/--no-refresh`: Whether to refresh cached data
- `--export-equity`: Export equity data
- `--dry-run`: Preview without executing
- `--verbose, -v`: Verbose output

**Examples:**

```bash
./trading-cli portfolio update --profile default_portfolio
./trading-cli portfolio update --portfolio DAILY.csv --export-equity
./trading-cli portfolio update --portfolio risk_on.csv --dry-run
```

#### `process`

Process individual portfolio files with comprehensive validation.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--input-dir PATH`: Input directory
- `--output-dir PATH`: Output directory
- `--format TEXT`: Output format (csv, json)
- `--validate/--no-validate`: Validate schemas
- `--dry-run`: Preview without executing

**Examples:**

```bash
./trading-cli portfolio process --input-dir ./csv/portfolios --output-dir ./processed
./trading-cli portfolio process --profile portfolio_processing --format json
```

#### `aggregate`

Aggregate multiple portfolio results with comprehensive metrics.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--by-ticker/--no-by-ticker`: Aggregate by ticker
- `--by-strategy/--no-by-strategy`: Aggregate by strategy
- `--breadth/--no-breadth`: Calculate breadth metrics
- `--output, -o TEXT`: Output filename

**Examples:**

```bash
./trading-cli portfolio aggregate --by-ticker --output results.csv
./trading-cli portfolio aggregate --profile portfolio_processing --no-breadth
```

### Configuration Commands (`config`)

#### `list`

List all available configuration profiles.

#### `show`

Show configuration details for a specific profile.

**Arguments:**

- `PROFILE_NAME`: Profile name to display

**Options:**

- `--resolved`: Show resolved configuration with inheritance

**Examples:**

```bash
./trading-cli config show default_strategy
./trading-cli config show my_profile --resolved
```

#### `create-defaults`

Create default configuration profiles.

#### `set-default`

Set the default configuration profile.

**Arguments:**

- `PROFILE_NAME`: Profile name to set as default

#### `validate`

Validate configuration profiles.

**Arguments:**

- `PROFILE_NAME` (optional): Specific profile to validate

**Examples:**

```bash
./trading-cli config validate              # Validate all profiles
./trading-cli config validate my_profile   # Validate specific profile
```

### Statistical Performance Divergence System Commands (`spds`)

#### `analyze`

Analyze portfolio using Statistical Performance Divergence System.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--trade-history/--no-trade-history`: Use trade history data vs equity curves
- `--output-format TEXT`: Output format (json, table, summary)
- `--save-results TEXT`: Save results to file (JSON format)
- `--export-backtesting/--no-export-backtesting`: Export deterministic backtesting parameters
- `--percentile-threshold INTEGER`: Percentile threshold for exit signals (default: 95)
- `--dual-layer-threshold FLOAT`: Dual layer convergence threshold (default: 0.85)
- `--sample-size-min INTEGER`: Minimum sample size for analysis (default: 15)
- `--confidence-level TEXT`: Confidence level (low, medium, high)
- `--verbose, -v`: Enable verbose output
- `--quiet, -q`: Quiet mode (errors only)

**Examples:**

```bash
./trading-cli spds analyze risk_on.csv --trade-history
./trading-cli spds analyze conservative.csv --no-trade-history
./trading-cli spds analyze risk_on.csv --export-backtesting --save-results results.json
```

#### `export`

Export backtesting parameters and analysis results.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--trade-history/--no-trade-history`: Use trade history data vs equity curves
- `--format TEXT`: Export format (all, json, csv, markdown)
- `--output-dir TEXT`: Output directory for exports
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
./trading-cli spds export risk_on.csv --format all
./trading-cli spds export conservative.csv --format json --output-dir ./exports/
```

#### `demo`

Create demo files and run example analysis.

#### `health`

Run SPDS system health check.

#### `configure`

Interactive SPDS configuration management.

#### `list-portfolios`

List available portfolios for analysis.

#### `interactive`

Interactive SPDS analysis mode.

### Trade History Commands (`trade-history`)

#### `close`

Generate comprehensive sell signal reports from SPDS data.

**Options:**

- `--profile, -p TEXT`: Configuration profile name
- `--output, -o TEXT`: Output file path (default: stdout)
- `--format, -f TEXT`: Output format (markdown, json, html)
- `--include-raw-data/--no-raw-data`: Include raw statistical data in appendices
- `--current-price FLOAT`: Current market price for enhanced analysis
- `--market-condition TEXT`: Market condition (bullish, bearish, sideways, volatile)
- `--base-path TEXT`: Base path to trading system directory
- `--verbose, -v`: Enable verbose logging

**Examples:**

```bash
./trading-cli trade-history close MA_SMA_78_82
./trading-cli trade-history close CRWD_EMA_5_21 --output reports/CRWD_analysis.md
./trading-cli trade-history close QCOM_SMA_49_66 --format json --include-raw-data
```

#### `add`

Add new live signal position with verification.

**Options:**

- `--strategy-type, -s TEXT`: Strategy type (SMA, EMA, MACD) [required]
- `--short-window INTEGER`: Short period window [required]
- `--long-window INTEGER`: Long period window [required]
- `--profile, -p TEXT`: Configuration profile name
- `--timeframe, -t TEXT`: Timeframe (D, H, 4H, 1H)
- `--entry-price FLOAT`: Manual entry price override
- `--quantity FLOAT`: Position quantity
- `--signal-date TEXT`: Signal date (YYYY-MM-DD format)
- `--dry-run`: Preview the addition without executing
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
./trading-cli trade-history add AAPL --strategy-type SMA --short-window 20 --long-window 50
./trading-cli trade-history add BTC-USD --strategy-type EMA --short-window 12 --long-window 26 --timeframe D
```

#### `update`

Update existing positions with current market data.

**Options:**

- `--portfolio, -f TEXT`: Portfolio name to update (default: live_signals)
- `--profile, -p TEXT`: Configuration profile name
- `--refresh-prices/--no-refresh-prices`: Refresh current market prices
- `--recalculate/--no-recalculate`: Recalculate MFE/MAE metrics
- `--update-risk/--no-update-risk`: Update risk assessment scores
- `--dry-run`: Preview updates without executing
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
./trading-cli trade-history update --portfolio live_signals
./trading-cli trade-history update --refresh-prices --recalculate
```

#### `list`

List all available strategies for analysis.

**Options:**

- `--show-signals/--no-signals`: Show exit signals in listing
- `--filter-signal TEXT`: Filter by signal type (SELL, HOLD, BUY)
- `--sort-by TEXT`: Sort by (confidence, ticker, signal, strategy)
- `--limit, -n INTEGER`: Limit number of results
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
./trading-cli trade-history list
./trading-cli trade-history list --filter-signal SELL --limit 10
./trading-cli trade-history list --sort-by ticker --no-signals
```

#### `validate`

Validate trade history data integrity and system health.

**Options:**

- `--check-integrity/--no-check-integrity`: Check data integrity across sources
- `--check-files/--no-check-files`: Check required file existence
- `--check-strategies/--no-check-strategies`: Validate strategy data quality
- `--show-details`: Show detailed validation results
- `--verbose, -v`: Enable verbose output

**Examples:**

```bash
./trading-cli trade-history validate
./trading-cli trade-history validate --show-details
./trading-cli trade-history validate --no-check-strategies
```

#### `health`

Perform comprehensive trade history system health check.

### Concurrency Commands (`concurrency`)

> **Note**: Currently in development. Commands show placeholder functionality.

#### `analyze`

Run concurrency analysis.

#### `export`

Export trade history data.

#### `review`

Review portfolio interactions.

### Tools Commands (`tools`)

> **Note**: Currently in development. Commands show placeholder functionality.

#### `schema`

Schema detection and conversion tools.

#### `validate`

Data validation utilities.

#### `health`

System health check.

---

## Getting Help

- **Command help**: Add `--help` to any command
- **System status**: `./trading-cli status`
- **Profile validation**: `./trading-cli config validate`
- **Verbose output**: Add `--verbose` for detailed information

## Next Steps

1. **Explore Examples**: Try the provided examples with your data
2. **Create Custom Profiles**: Build profiles for your specific use cases
3. **Integrate Workflows**: Incorporate CLI commands into your analysis workflows
4. **Extend Functionality**: Use the modular design to add custom features

The Trading CLI provides a powerful, type-safe interface for all your trading analysis needs. Start with the basic commands and gradually explore the advanced features as your requirements grow!
