# Command Reference

Complete reference for all CLI commands in the trading system.

**⚠️ Important: This trading system uses CLI-first architecture. All functionality should be accessed through these CLI commands. Direct script execution is deprecated and will be removed in future versions.**

## Global Options

All commands support these global options:

```bash
--help              Show help message and exit
--verbose           Enable verbose output
--config PATH       Path to configuration file
--log-level LEVEL   Set logging level (DEBUG, INFO, WARNING, ERROR)
--dry-run          Preview actions without executing
```

## Strategy Analysis Commands

### `strategy run`

Execute strategy analysis on specified tickers.

```bash
python -m app.cli strategy run [OPTIONS]
```

**Options:**

- `--ticker TEXT`: Comma-separated list of tickers (required)
- `--strategy TEXT`: Strategy types (SMA, EMA, MACD, RSI)
- `--profile TEXT`: Configuration profile name
- `--min-trades INTEGER`: Minimum number of trades required
- `--min-win-rate FLOAT`: Minimum win rate required
- `--start-date TEXT`: Start date for analysis (YYYY-MM-DD)
- `--end-date TEXT`: End date for analysis (YYYY-MM-DD)
- `--data-period TEXT`: Data period (1Y, 2Y, 5Y, 10Y)
- `--export-format TEXT`: Export format (csv, json)
- `--parallel`: Enable parallel processing
- `--optimize-memory`: Enable memory optimization

**Examples:**

```bash
# Basic analysis
python -m app.cli strategy run --ticker AAPL --strategy SMA

# Multiple tickers and strategies
python -m app.cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA,EMA

# Using profile
python -m app.cli strategy run --profile ma_cross_crypto

# Custom parameters
python -m app.cli strategy run --ticker AAPL --strategy SMA --min-trades 50 --min-win-rate 0.6
```

### `strategy sweep`

Perform parameter sweep analysis.

```bash
python -m app.cli strategy sweep [OPTIONS]
```

**Options:**

- `--ticker TEXT`: Ticker symbol (required)
- `--strategy TEXT`: Strategy type (default: SMA)
- `--fast-min INTEGER`: Minimum fast period
- `--fast-max INTEGER`: Maximum fast period
- `--slow-min INTEGER`: Minimum slow period
- `--slow-max INTEGER`: Maximum slow period
- `--step INTEGER`: Step size for parameter sweep
- `--optimize`: Optimize parameters

**Examples:**

```bash
# Basic parameter sweep
python -m app.cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50

# Comprehensive sweep with optimization
python -m app.cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200 --optimize
```

### `strategy validate`

Validate strategy results against criteria.

```bash
python -m app.cli strategy validate [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio file to validate
- `--criteria TEXT`: Validation criteria file
- `--strict`: Enable strict validation

**Examples:**

```bash
# Validate portfolio
python -m app.cli strategy validate --portfolio AAPL_D_SMA.csv

# Strict validation
python -m app.cli strategy validate --portfolio AAPL_D_SMA.csv --strict
```

## Portfolio Management Commands

### `portfolio update`

Update portfolio aggregations and calculations.

```bash
python -m app.cli portfolio update [OPTIONS]
```

**Options:**

- `--profile TEXT`: Portfolio profile name
- `--portfolio TEXT`: Specific portfolio file
- `--validate`: Validate results
- `--export-format TEXT`: Export format (csv, json)
- `--export-equity`: Export equity curves
- `--parallel`: Enable parallel processing

**Examples:**

```bash
# Update with validation
python -m app.cli portfolio update --validate

# Update specific portfolio
python -m app.cli portfolio update --portfolio risk_on.csv --export-format json

# Update with equity export
python -m app.cli portfolio update --export-equity --parallel
```

### `portfolio list`

List available portfolios.

```bash
python -m app.cli portfolio list [OPTIONS]
```

**Options:**

- `--recent`: Show only recent portfolios
- `--filter TEXT`: Filter by name pattern
- `--format TEXT`: Output format (table, json)

**Examples:**

```bash
# List all portfolios
python -m app.cli portfolio list

# List recent portfolios
python -m app.cli portfolio list --recent

# Filter portfolios
python -m app.cli portfolio list --filter "risk_*"
```

### `portfolio export`

Export portfolio data in various formats.

```bash
python -m app.cli portfolio export [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio file to export
- `--format TEXT`: Export format (csv, json, excel)
- `--output TEXT`: Output file path
- `--include-metadata`: Include metadata in export

**Examples:**

```bash
# Export to JSON
python -m app.cli portfolio export --portfolio risk_on.csv --format json

# Export with metadata
python -m app.cli portfolio export --portfolio risk_on.csv --format json --include-metadata
```

### `portfolio optimize`

Optimize portfolio allocation and parameters.

```bash
python -m app.cli portfolio optimize [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio file to optimize
- `--method TEXT`: Optimization method (sharpe, return, risk)
- `--constraints TEXT`: Optimization constraints file
- `--output TEXT`: Output file path

**Examples:**

```bash
# Optimize for Sharpe ratio
python -m app.cli portfolio optimize --portfolio risk_on.csv --method sharpe

# Optimize with constraints
python -m app.cli portfolio optimize --portfolio risk_on.csv --method sharpe --constraints constraints.yaml
```

## Statistical Analysis Commands

### `spds analyze`

Perform Statistical Performance Divergence System analysis.

```bash
python -m app.cli spds analyze [OPTIONS] PORTFOLIO
```

**Options:**

- `--data-source TEXT`: Data source (auto, trade-history, equity-curves, both)
- `--output-format TEXT`: Output format (markdown, json)
- `--confidence-level FLOAT`: Confidence level (0.0-1.0)
- `--save-results TEXT`: Save results to file

**Examples:**

```bash
# Basic analysis
python -m app.cli spds analyze risk_on.csv

# Specify data source
python -m app.cli spds analyze risk_on.csv --data-source trade-history

# Save results
python -m app.cli spds analyze risk_on.csv --save-results analysis_results.json
```

### `spds interactive`

Launch interactive SPDS analysis mode.

```bash
python -m app.cli spds interactive [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Initial portfolio to load
- `--auto-refresh`: Enable auto-refresh

**Examples:**

```bash
# Launch interactive mode
python -m app.cli spds interactive

# Start with specific portfolio
python -m app.cli spds interactive --portfolio risk_on.csv
```

### `spds health`

Check SPDS system health and configuration.

```bash
python -m app.cli spds health [OPTIONS]
```

**Options:**

- `--detailed`: Show detailed health information
- `--fix`: Attempt to fix issues automatically

**Examples:**

```bash
# Basic health check
python -m app.cli spds health

# Detailed health check
python -m app.cli spds health --detailed

# Health check with auto-fix
python -m app.cli spds health --fix
```

### `spds list-portfolios`

List available portfolios for SPDS analysis.

```bash
python -m app.cli spds list-portfolios [OPTIONS]
```

**Options:**

- `--filter TEXT`: Filter by name pattern
- `--format TEXT`: Output format (table, json)

**Examples:**

```bash
# List all portfolios
python -m app.cli spds list-portfolios

# Filter portfolios
python -m app.cli spds list-portfolios --filter "*signals*"
```

### `spds demo`

Create demo portfolios and run example analysis.

```bash
python -m app.cli spds demo [OPTIONS]
```

**Options:**

- `--cleanup`: Clean up demo files after completion
- `--example TEXT`: Specific example to run

**Examples:**

```bash
# Run demo
python -m app.cli spds demo

# Run with cleanup
python -m app.cli spds demo --cleanup
```

## Trade History Commands

### `trade-history update`

Update trade history with current market data.

```bash
python -m app.cli trade-history update [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio to update
- `--refresh-prices`: Refresh current prices
- `--recalculate`: Recalculate all metrics
- `--update-risk`: Update risk metrics

**Examples:**

```bash
# Update live signals
python -m app.cli trade-history update --portfolio live_signals

# Full update with price refresh
python -m app.cli trade-history update --portfolio live_signals --refresh-prices --recalculate
```

### `trade-history close`

Close position and generate exit analysis.

```bash
python -m app.cli trade-history close [OPTIONS] STRATEGY
```

**Options:**

- `--portfolio TEXT`: Portfolio name
- `--price FLOAT`: Current price for exit
- `--market-condition TEXT`: Market condition (bullish, bearish, neutral)
- `--format TEXT`: Output format (markdown, json)
- `--output TEXT`: Output file path

**Examples:**

```bash
# Close position
python -m app.cli trade-history close MA_SMA_78_82

# Close with specific price
python -m app.cli trade-history close MA_SMA_78_82 --price 150.25 --portfolio risk_on

# Generate JSON report
python -m app.cli trade-history close MA_SMA_78_82 --format json --output exit_analysis.json
```

### `trade-history list`

List available strategies for trade history analysis.

```bash
python -m app.cli trade-history list [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio to list
- `--active-only`: Show only active positions
- `--format TEXT`: Output format (table, json)

**Examples:**

```bash
# List all strategies
python -m app.cli trade-history list

# List active positions only
python -m app.cli trade-history list --active-only

# List for specific portfolio
python -m app.cli trade-history list --portfolio risk_on
```

### `trade-history health`

Check trade history system health.

```bash
python -m app.cli trade-history health [OPTIONS]
```

**Options:**

- `--detailed`: Show detailed health information
- `--fix`: Attempt to fix issues automatically

**Examples:**

```bash
# Basic health check
python -m app.cli trade-history health

# Detailed health check with auto-fix
python -m app.cli trade-history health --detailed --fix
```

### `trade-history validate`

Validate trade history data integrity.

```bash
python -m app.cli trade-history validate [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio to validate
- `--strict`: Enable strict validation
- `--fix`: Attempt to fix issues automatically

**Examples:**

```bash
# Validate trade history
python -m app.cli trade-history validate

# Strict validation with auto-fix
python -m app.cli trade-history validate --strict --fix
```

## Concurrency Analysis Commands

### `concurrency analyze`

Analyze concurrency and overlapping trades.

```bash
python -m app.cli concurrency analyze [OPTIONS]
```

**Options:**

- `--portfolio TEXT`: Portfolio to analyze
- `--export-trades`: Export trade history
- `--detailed`: Show detailed analysis

**Examples:**

```bash
# Basic concurrency analysis
python -m app.cli concurrency analyze

# Export trade history
python -m app.cli concurrency analyze --export-trades

# Detailed analysis
python -m app.cli concurrency analyze --detailed
```

## Configuration Commands

### `config list`

List available configuration profiles.

```bash
python -m app.cli config list [OPTIONS]
```

**Options:**

- `--type TEXT`: Configuration type (strategy, portfolio, spds)
- `--format TEXT`: Output format (table, json)

**Examples:**

```bash
# List all profiles
python -m app.cli config list

# List strategy profiles
python -m app.cli config list --type strategy
```

### `config validate`

Validate configuration files.

```bash
python -m app.cli config validate [OPTIONS]
```

**Options:**

- `--profile TEXT`: Specific profile to validate
- `--strict`: Enable strict validation

**Examples:**

```bash
# Validate all configurations
python -m app.cli config validate

# Validate specific profile
python -m app.cli config validate --profile ma_cross_crypto
```

### `config reset`

Reset configuration to defaults.

```bash
python -m app.cli config reset [OPTIONS]
```

**Options:**

- `--profile TEXT`: Specific profile to reset
- `--confirm`: Skip confirmation prompt

**Examples:**

```bash
# Reset all configurations
python -m app.cli config reset

# Reset specific profile
python -m app.cli config reset --profile ma_cross_crypto --confirm
```

## Utility Commands

### `tools health`

Check overall system health.

```bash
python -m app.cli tools health [OPTIONS]
```

**Options:**

- `--detailed`: Show detailed health information
- `--fix`: Attempt to fix issues automatically

**Examples:**

```bash
# Basic health check
python -m app.cli tools health

# Detailed health check with auto-fix
python -m app.cli tools health --detailed --fix
```

### `init`

Initialize the trading system.

```bash
python -m app.cli init [OPTIONS]
```

**Options:**

- `--force`: Force initialization even if already initialized
- `--profile TEXT`: Initialize with specific profile

**Examples:**

```bash
# Basic initialization
python -m app.cli init

# Force re-initialization
python -m app.cli init --force
```

## Exit Codes

The CLI uses standard exit codes:

- `0`: Success
- `1`: General error
- `2`: Invalid command or arguments
- `3`: Configuration error
- `4`: Data error
- `5`: Validation error

## Environment Variables

The CLI respects these environment variables:

- `TRADING_CONFIG_PATH`: Path to configuration directory
- `TRADING_LOG_LEVEL`: Default logging level
- `TRADING_DATA_PATH`: Path to data directory
- `TRADING_EXPORT_PATH`: Path to export directory

## Configuration Files

### Profile Structure

```yaml
metadata:
  name: profile_name
  description: Profile description
  version: 1.0

config_type: strategy # or portfolio, spds
config:
  # Profile-specific configuration
```

### Global Configuration

```yaml
# config/global.yaml
logging:
  level: INFO
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

paths:
  data: './data'
  exports: './exports'
  csv: './csv'

defaults:
  min_trades: 44
  min_win_rate: 0.5
  data_period: '2Y'
```

---

_For more detailed information about specific commands, use the `--help` option with any command._
