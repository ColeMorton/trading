# Trading Data Organization Standards

## Directory Structure

```
./data/
├── portfolios/           # Portfolio configurations (YAML files)
├── raw/                  # Data for codebase consumption
│   ├── prices/          # Market price data CSVs
│   ├── strategies/      # Strategy backtest results
│   ├── positions/       # Active portfolio positions & trade history
│   ├── equity/          # Strategy equity curves
│   ├── reports/         # JSON reports & analysis data
│   │   ├── trade_history/
│   │   ├── concurrency/
│   │   ├── return_distribution/
│   │   └── monte_carlo/
│   └── attribution/     # Performance attribution data
└── outputs/              # Generated outputs (not for consumption)
    ├── exports/         # SPDS & feature exports
    ├── images/          # Charts & visualizations
    └── reports/         # Generated documentation & analysis
```

## Naming Conventions

### File Naming Standards

**Portfolio Configurations** (`./data/portfolios/`)

- Format: `{portfolio_name}.yaml`
- Examples: `risk_on.yaml`, `protected.yaml`, `live_signals.yaml`

**Price Data** (`./data/raw/prices/`)

- Format: `{TICKER}_{TIMEFRAME}.csv`
- Examples: `AAPL_D.csv`, `BTC-USD_H.csv`, `SPY_W.csv`

**Strategy Results** (`./data/raw/strategies/`)

- Format: `{TICKER}_{TIMEFRAME}_{STRATEGY_TYPE}.csv`
- Examples: `AAPL_D_SMA.csv`, `BTC-USD_D_MACD.csv`, `NVDA_H_EMA.csv`

**Position Data** (`./data/raw/positions/`)

- Format: `{portfolio_name}.csv`
- Examples: `risk_on.csv`, `protected.csv`, `live_signals.csv`

**Equity Curves** (`./data/raw/equity/`)

- Format: `{TICKER}_{STRATEGY}_{SHORT}_{LONG}.csv`
- Examples: `AAPL_SMA_20_50.csv`, `BTC-USD_EMA_12_26.csv`

**Reports** (`./data/raw/reports/`)

- Trade History: `{TICKER}_{TIMEFRAME}_{STRATEGY}_{SHORT}_{LONG}.json`
- Concurrency: `{portfolio_name}.json`
- Return Distribution: `{TICKER}.json`
- Monte Carlo: `{TICKER}_{analysis_type}.json`

**Attribution Data** (`./data/raw/attribution/`)

- Format: `{TICKER}_{YYYYMMDD}_{HHMMSS}.json`
- Examples: `AAPL_20250719_143022.json`

### Timeframe Codes

- `D` = Daily
- `H` = Hourly
- `W` = Weekly
- `M` = Monthly

### Strategy Type Codes

- `SMA` = Simple Moving Average
- `EMA` = Exponential Moving Average
- `MACD` = MACD Crossover
- `RSI` = RSI Strategy
- `ATR` = ATR-based Strategy

## Data Organization Principles

### Raw Data (`./data/raw/`)

- **Purpose**: Data consumed by the codebase
- **Format**: Primarily CSV and JSON
- **Retention**: Permanent, version controlled
- **Structure**: Organized by data type and purpose

### Outputs (`./data/outputs/`)

- **Purpose**: Generated artifacts, reports, visualizations
- **Format**: Various (PNG, HTML, PDF, CSV, JSON)
- **Retention**: Temporary, not version controlled
- **Structure**: Organized by feature/tool that generates them

### Portfolios (`./data/portfolios/`)

- **Purpose**: Configuration files for portfolio definitions
- **Format**: YAML only
- **Retention**: Permanent, version controlled
- **Structure**: Flat directory with descriptive names

## Migration Guidelines

### Moving Existing Data

1. Preserve original timestamps where possible
2. Maintain file integrity during moves
3. Update all references in codebase
4. Validate functionality after migration

### Adding New Data

1. Follow established naming conventions
2. Place in appropriate directory based on purpose
3. Document any new data types or formats
4. Consider retention and backup policies

## File Management

### Version Control

- Include: `./data/portfolios/`, `./data/raw/`
- Exclude: `./data/outputs/` (add to .gitignore)

### Backup Strategy

- Raw data: Full backup with change tracking
- Outputs: Regenerable, minimal backup needed
- Portfolios: Critical, multiple backup copies

### Cleanup Policies

- Raw data: Retain indefinitely
- Outputs: Clean up files older than 30 days
- Attribution: Archive files older than 90 days

## Access Patterns

### Read Operations

- Price data: High frequency, sequential access
- Strategy results: Batch processing, analytical queries
- Reports: On-demand, random access

### Write Operations

- Price data: Append-only, daily updates
- Strategy results: Bulk writes, analysis completion
- Reports: Event-driven, analysis completion

## Performance Considerations

### Large Files

- Use streaming for files >100MB
- Consider compression for archival data
- Implement pagination for UI access

### Indexing

- Maintain ticker lists for quick lookups
- Create date-based indices for time series
- Use filename conventions for directory scanning

## Data Integrity

### Validation

- Schema validation for all CSV files
- JSON schema validation for reports
- Cross-reference validation between related files

### Monitoring

- File size monitoring for corruption detection
- Timestamp validation for data freshness
- Consistency checks between raw and derived data
