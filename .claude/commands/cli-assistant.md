# Unified Trading CLI Assistant

Comprehensive expert assistant for the production-ready Unified Trading CLI system. Provides authoritative guidance on all CLI operations, configuration management, command execution, troubleshooting, and system architecture with complete knowledge of the current implementation.

## Purpose

Expert assistant for the **Unified Trading CLI** (v2.0.0) - an enterprise-grade command-line interface built with Typer for trading strategy analysis, portfolio management, and system operations. The CLI provides unified access to all trading tools with type-safe configuration management and rich terminal output.

## Parameters

- `task`: CLI operation type (required)

  - `execute` - Command execution guidance and syntax help
  - `configure` - Configuration and profile management
  - `troubleshoot` - System diagnostics and issue resolution
  - `architecture` - System architecture and integration guidance
  - `commands` - Detailed command reference and examples
  - `profiles` - Profile system management and inheritance
  - `validation` - Configuration validation and schema guidance
  - `health` - System health checks and dependency validation
  - `performance` - Performance optimization and memory management

- `command`: Specific CLI command (optional: "strategy", "portfolio", "spds", "trade-history", "config", "tools", "concurrency")
- `operation`: Subcommand operation (optional: "run", "analyze", "export", "validate", etc.)
- `profile`: Configuration profile name (optional, e.g., "ma_cross_crypto")
- `format`: Output format preference (optional: "table", "json", "verbose")

## CLI System Architecture

### **Core Framework**

- **Framework**: Typer with Rich for enhanced terminal output
- **Version**: 2.0.0
- **Configuration**: YAML-based with Pydantic validation
- **Type Safety**: Comprehensive Pydantic models throughout
- **Error Handling**: Graceful degradation with meaningful messages
- **Terminal Enhancement**: Rich library for beautiful tables, progress bars, and colors

### **Entry Points**

**Primary Entry Point:**

```bash
./trading-cli [command] [subcommand] [options]
```

**Alternative Entry Points:**

```bash
# Module execution
./trading-cli

# Programmatic access
from app.cli.main import cli_main
```

### **Command Structure**

The CLI provides **7 main command groups** with comprehensive subcommands:

#### **1. strategy** - Strategy Analysis and Execution

**Available subcommands:**

- `run` - Execute strategy analysis with profile or custom parameters
- `sweep` - Parameter sweep analysis for optimization
- `analyze` - Single strategy detailed analysis

```bash
# Profile-based execution
./trading-cli strategy run --profile ma_cross_crypto

# Custom parameter execution
./trading-cli strategy run --ticker BTC-USD,ETH-USD --strategy-type SMA --fast-period 20 --slow-period 50

# Parameter sweep analysis
./trading-cli strategy sweep --ticker AAPL --fast-range 5,10 --slow-range 20,50 --min-trades 100

# Single strategy analysis
./trading-cli strategy analyze --ticker BTC-USD --strategy-type SMA --fast-period 9 --slow-period 21

# Advanced filtering
./trading-cli strategy run --profile ma_cross_crypto --min-win-rate 0.6 --min-profit-factor 1.5 --min-sortino 1.0
```

#### **2. portfolio** - Portfolio Processing and Aggregation

**Available subcommands:**

- `update` - Update and aggregate portfolio results
- `process` - Process portfolio files with validation
- `aggregate` - Aggregate multiple portfolios with advanced metrics

```bash
# Portfolio update with validation
./trading-cli portfolio update --validate --export-format json

# Process specific portfolio with schema validation
./trading-cli portfolio process portfolio.csv --schema-version extended --validate

# Advanced aggregation with breadth metrics
./trading-cli portfolio aggregate --by-ticker --calculate-breadth --export-format csv

# Batch processing with correlation analysis
./trading-cli portfolio aggregate --correlation-analysis --risk-metrics
```

#### **3. spds** - Enhanced Statistical Performance Divergence System (v2.0)

**Available subcommands:**

- `analyze` - Portfolio statistical analysis with auto data source detection
- `export` - Export backtesting parameters and analysis results
- `demo` - Create demo files and run example analysis
- `health` - System health check and data source validation
- `configure` - Interactive configuration management
- `list-portfolios` - List available portfolios for analysis
- `interactive` - Interactive guided analysis mode

```bash
# Auto-detection with dual-source analysis
./trading-cli spds analyze risk_on.csv --data-source auto

# Explicit dual-source analysis with enhanced confidence
./trading-cli spds analyze risk_on.csv --data-source both --confidence-boost

# Single-source analysis
./trading-cli spds analyze risk_on.csv --data-source trade-history
./trading-cli spds analyze risk_on.csv --data-source equity-curves

# Enhanced exports with multi-source details
./trading-cli spds export risk_on.csv --format all --multi-source-details --save-results

# Interactive mode with guided analysis
./trading-cli spds interactive --auto-detect-sources

# System health and source validation
./trading-cli spds health --convergence-analysis
./trading-cli spds list-sources --all-portfolios
```

#### **4. trade-history** - Trade History Analysis and Position Management

**Available subcommands:**

- `close` - Close positions and generate comprehensive sell signal reports
- `update` - Update positions with current market data
- `list` - List available strategies for analysis
- `health` - System health check
- `validate` - Data validation

```bash
# Close position with portfolio update
./trading-cli trade-history close \
  --strategy NFLX_SMA_82_83_2025-06-16 \
  --portfolio risk_on \
  --price 1273.99

# Close with comprehensive analysis and verbose output
./trading-cli trade-history close \
  --strategy AAPL_SMA_20_50_2025-01-01 \
  --portfolio live_signals \
  --price 150.00 \
  --verbose \
  --market-condition bearish

# Update positions with market data and risk assessment
./trading-cli trade-history update --portfolio live_signals \
  --refresh-prices --recalculate --update-risk --dry-run

# List available strategies with filtering
./trading-cli trade-history list --portfolio risk_on --active-only

# Generate report-only analysis
./trading-cli trade-history close MA_SMA_78_82 \
  --current-price 245.50 --output reports/exit_analysis.md --format markdown
```

#### **5. config** - Configuration and Profile Management

**Available subcommands:**

- `list` - List all available configuration profiles
- `show` - Show configuration details for specific profile
- `create-defaults` - Create default configuration profiles
- `set-default` - Set the default configuration profile
- `edit` - Edit a configuration profile
- `validate` - Validate configuration profiles

```bash
# Profile management
./trading-cli config list
./trading-cli config show ma_cross_crypto --format json
./trading-cli config create-defaults
./trading-cli config set-default ma_cross_crypto

# Configuration validation
./trading-cli config validate
./trading-cli config validate ma_cross_crypto --detailed

# Profile editing
./trading-cli config edit ma_cross_crypto
```

#### **6. tools** - Utility Tools and System Management

**Available subcommands:**

- `schema` - Schema detection, validation, and conversion
- `health` - Comprehensive system health diagnostics
- `validate` - Data validation utilities

```bash
# System health and diagnostics
./trading-cli tools health
./trading-cli tools health --verbose --check-dependencies

# Schema management
./trading-cli tools schema --detect-version --convert
./trading-cli tools schema --validate-all --report

# Data validation
./trading-cli tools validate --batch --format json
./trading-cli tools validate --file portfolio.csv --comprehensive
```

#### **7. concurrency** - Concurrency Analysis and Trade History

**Available subcommands:**

- `analyze` - Concurrency analysis with trade history export
- `review` - Portfolio interaction analysis with visualization

```bash
# Concurrency analysis with trade export
./trading-cli concurrency analyze --export-trades

# Portfolio interaction analysis
./trading-cli concurrency review --visualization --allocation-analysis
```

### **Root Commands**

**System-level operations:**

```bash
./trading-cli version           # Show version information
./trading-cli status            # System status and configuration
./trading-cli init              # Initialize CLI with default profiles
```

### **Global Options (Available for ALL commands)**

```bash
--verbose, -v              # Enable verbose output with detailed logging
--profiles-dir PATH        # Custom profiles directory (default: app/cli/profiles)
--dry-run                  # Preview operations without execution
--output-format FORMAT     # Output format (table, json, verbose)
--no-color                 # Disable colored output
--config-file PATH         # Custom configuration file
--log-level LEVEL          # Set logging level (DEBUG, INFO, WARNING, ERROR)
```

## Advanced Configuration System

### **Profile-Based Configuration**

**Profile Structure with Enhanced Metadata:**

```yaml
metadata:
  name: profile_name
  description: 'Comprehensive profile description'
  created_at: '2025-07-11T10:30:00.000000'
  updated_at: '2025-07-11T10:30:00.000000'
  version: '1.0'
  tags: [production, crypto, optimized]
  author: 'system'

inherits_from: parent_profile # Optional inheritance with validation
config_type: strategy # Determines validation model (strategy, portfolio, spds, trade_history, concurrency, tools)

config: # Type-safe configuration data with comprehensive validation
  # Strategy Configuration
  ticker: [BTC-USD, ETH-USD, AAPL, MSFT]
  strategy_types: [SMA, EMA]
  timeframe: '1d'

  # Performance Filters
  minimums:
    win_rate: 0.5
    trades: 44
    profit_factor: 1.2
    expectancy: 0.05
    sortino_ratio: 1.0
    beats_buy_and_hold: true

  # Advanced Features
  memory_optimization:
    enable_pooling: true
    enable_monitoring: true
    memory_threshold_mb: 1000.0
    streaming_threshold_mb: 5.0

  # Output Configuration
  export_formats: [csv, json]
  verbose_output: false
  rich_formatting: true
```

### **Configuration Management Features**

**Profile Inheritance with Validation:**

- Recursive profile loading with circular reference detection
- Deep merging of configuration dictionaries with conflict resolution
- Automatic backup management with timestamped versions
- Cache optimization for performance with TTL support
- Comprehensive validation at each inheritance level

**Multi-Source Configuration Loading:**

```bash
# Profile-based configuration
./trading-cli strategy run --profile ma_cross_crypto

# Runtime parameter overrides
./trading-cli strategy run --profile ma_cross_crypto --ticker BTC-USD --verbose --min-trades 100

# Custom configuration file
./trading-cli strategy run --config-file custom_strategy.yaml

# Environment variable overrides
CLI_PROFILE=ma_cross_crypto ./trading-cli strategy run
```

### **Available Profiles**

**Default Profiles:**

- `default_strategy` - Base strategy configuration with conservative settings
- `default_portfolio` - Portfolio processing defaults with validation
- `default_concurrency` - Concurrency analysis settings
- `ma_cross_crypto` - Cryptocurrency MA Cross analysis (production-ready)
- `current` - Production analysis matching existing legacy scripts

**Strategy-Specific Profiles:**

- `strategies/current.yaml` - Current production configuration
- `strategies/ma_cross_crypto.yaml` - Crypto-focused MA Cross
- `strategies/ma_cross_dev.yaml` - Development and testing configuration

**Profile Locations:**

```
./app/cli/profiles/
├── config.yaml                    # Main profile configuration registry
├── default_strategy.yaml          # Base strategy defaults
├── default_portfolio.yaml         # Portfolio processing defaults
├── default_concurrency.yaml       # Concurrency analysis defaults
├── ma_cross_crypto.yaml          # Crypto-focused configuration
└── strategies/                    # Strategy-specific profiles
    ├── current.yaml               # Production configuration
    ├── ma_cross_crypto.yaml       # Crypto MA Cross optimized
    └── ma_cross_dev.yaml          # Development configuration
```

## Type-Safe Data Models

### **Comprehensive Model Hierarchy**

**Base Configuration:**

```python
class BaseConfig(BaseModel):
    """Foundation class with common fields and validation"""
    verbose: bool = False
    dry_run: bool = False
    output_dir: Optional[Path] = None
    memory_optimization: Optional[MemoryConfig] = None
    rich_formatting: bool = True
    log_level: LogLevel = LogLevel.INFO
```

**Domain-Specific Models:**

- `StrategyConfig` - Strategy execution parameters with advanced filtering
- `PortfolioConfig` - Portfolio processing settings with schema validation
- `SPDSConfig` - Enhanced statistical analysis with dual-source support
- `TradeHistoryConfig` - Trade history operations with position management
- `ConcurrencyConfig` - Concurrency analysis settings
- `ToolsConfig` - Utility tools configuration

### **Enhanced Validation Features**

**Type Safety with Business Logic:**

```python
class StrategyType(str, Enum):
    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"

class Direction(str, Enum):
    LONG = "Long"
    SHORT = "Short"

class OutputFormat(str, Enum):
    TABLE = "table"
    JSON = "json"
    VERBOSE = "verbose"
    CSV = "csv"
```

**Advanced Business Logic Validation:**

```python
@validator("slow_period")
def validate_periods(cls, v, values):
    if "fast_period" in values and v <= values["fast_period"]:
        raise ValueError("Slow period must be greater than fast period")
    return v

@validator("minimums")
def validate_minimums(cls, v):
    if v.win_rate < 0 or v.win_rate > 1:
        raise ValueError("Win rate must be between 0 and 1")
    return v
```

## Rich Terminal Features

### **Enhanced Display Capabilities**

**Rich Table Output:**

- Color-coded performance metrics (green for positive, red for negative)
- Sortable columns with automatic type detection
- Progress bars for long-running operations
- Status indicators and icons for quick visual feedback

**Interactive Features:**

- Real-time progress tracking with ETA
- Interactive prompts for configuration
- Colored error messages with resolution hints
- Formatted help text with syntax highlighting

**Example Rich Output:**

```bash
# Strategy analysis with rich formatting
./trading-cli strategy run --profile ma_cross_crypto --verbose

┌──────────────────────────────────────────────────────────────────┐
│                     Strategy Analysis Results                    │
├──────────────────────────────────────────────────────────────────┤
│ Ticker: BTC-USD | Strategy: SMA_20_50 | Period: 2020-2025       │
│ ✅ Win Rate: 65.2% | 🎯 Profit Factor: 2.34 | 📈 Total Return: 156.7% │
│ 📊 Trades: 87 | 💰 Expectancy: 2.45% | 🛡️ Sortino: 1.82       │
└──────────────────────────────────────────────────────────────────┘
```

## Comprehensive Usage Examples

### **Strategy Analysis (Advanced)**

```bash
# Quick strategy analysis with default profile
./trading-cli strategy run

# Multi-ticker analysis with custom filtering
./trading-cli strategy run \
  --ticker BTC-USD,ETH-USD,AAPL,MSFT \
  --strategy-type SMA,EMA \
  --min-win-rate 0.6 \
  --min-profit-factor 1.5 \
  --min-trades 50 \
  --verbose

# Parameter sweep with optimization
./trading-cli strategy sweep \
  --profile ma_cross_crypto \
  --fast-range 5,15 \
  --slow-range 20,60 \
  --min-trades 100 \
  --export-format json \
  --memory-optimization

# Single strategy deep analysis
./trading-cli strategy analyze \
  --ticker BTC-USD \
  --strategy-type SMA \
  --fast-period 9 \
  --slow-period 21 \
  --output-format verbose \
  --include-signals
```

### **Portfolio Management (Enterprise)**

```bash
# Portfolio update with comprehensive validation
./trading-cli portfolio update --validate --export-format json --verbose

# Process portfolio with schema upgrade
./trading-cli portfolio process portfolio.csv \
  --schema-version extended \
  --validate \
  --convert-format \
  --backup

# Advanced aggregation with risk metrics
./trading-cli portfolio aggregate \
  --by-ticker \
  --by-strategy \
  --calculate-breadth \
  --correlation-analysis \
  --risk-metrics \
  --export-format csv,json

# Batch processing with optimization
./trading-cli portfolio aggregate \
  --input-dir csv/portfolios/ \
  --output-dir csv/aggregated/ \
  --memory-optimization \
  --parallel-processing
```

### **Enhanced SPDS Analysis (v2.0) - Dual-Source**

#### **Auto-Detection Mode**

```bash
# Intelligent dual-source analysis
./trading-cli spds analyze risk_on.csv --data-source auto

# Enhanced analysis with confidence boosting
./trading-cli spds analyze risk_on.csv \
  --data-source auto \
  --confidence-boost \
  --convergence-threshold 0.8 \
  --verbose

# Production analysis with conservative settings
./trading-cli spds analyze risk_on.csv \
  --data-source auto \
  --conservative-on-divergence \
  --min-trade-count 30 \
  --multi-source-details
```

#### **Explicit Dual-Source Analysis**

```bash
# Force dual-source analysis (requires both data sources)
./trading-cli spds analyze risk_on.csv --data-source both

# Triple-layer convergence analysis
./trading-cli spds analyze risk_on.csv \
  --data-source both \
  --asset-weight 0.3 \
  --trade-weight 0.4 \
  --equity-weight 0.3 \
  --convergence-validation

# Development testing with permissive settings
./trading-cli spds analyze test_portfolio.csv \
  --data-source both \
  --convergence-threshold 0.6 \
  --min-trade-count 10 \
  --aggressive-on-convergence
```

#### **System Health and Diagnostics**

```bash
# Comprehensive SPDS health check
./trading-cli spds health --convergence-analysis --verbose

# Data source availability check
./trading-cli spds list-sources risk_on.csv --detailed

# Source convergence validation
./trading-cli spds validate-convergence risk_on.csv --matrix

# Export with comprehensive diagnostics
./trading-cli spds export risk_on.csv \
  --format all \
  --source-details \
  --convergence-matrix \
  --debug-output
```

### **Trade History Operations (Enterprise)**

#### **Position Management**

```bash
# Close position with portfolio update
./trading-cli trade-history close \
  --strategy NFLX_SMA_82_83_2025-06-16 \
  --portfolio risk_on \
  --price 1273.99 \
  --verbose

# Advanced position closing with market analysis
./trading-cli trade-history close \
  --strategy AAPL_SMA_20_50_2025-01-01 \
  --portfolio live_signals \
  --price 150.00 \
  --market-condition bearish \
  --risk-assessment \
  --spds-analysis \
  --output reports/AAPL_exit_analysis.md

# Batch position updates with optimization
./trading-cli trade-history update \
  --portfolio live_signals \
  --refresh-prices \
  --recalculate \
  --update-risk \
  --parallel-processing \
  --dry-run
```

#### **Analysis and Reporting**

```bash
# Generate comprehensive sell signal report
./trading-cli trade-history close MA_SMA_78_82 \
  --current-price 245.50 \
  --market-condition bearish \
  --output reports/exit_analysis.md \
  --format markdown \
  --include-charts

# JSON export for programmatic use
./trading-cli trade-history close QCOM_SMA_49_66 \
  --format json \
  --include-raw-data \
  --risk-metrics \
  --output data/QCOM_analysis.json

# Interactive analysis with guidance
./trading-cli trade-history close \
  --strategy TSLA_EMA_12_26_2025-02-15 \
  --interactive \
  --guided-analysis \
  --recommendations
```

### **Configuration Management (Advanced)**

```bash
# Profile management with validation
./trading-cli config list --detailed --with-inheritance
./trading-cli config show ma_cross_crypto --format json --validate

# Profile creation and editing
./trading-cli config create-defaults --overwrite --backup
./trading-cli config edit ma_cross_crypto --interactive

# Advanced validation with business logic
./trading-cli config validate --all-profiles --strict --report
./trading-cli config validate ma_cross_crypto --detailed --fix-issues

# Profile inheritance and composition
./trading-cli config show ma_cross_crypto --resolve-inheritance --format yaml
```

### **System Tools (Comprehensive)**

```bash
# System health with comprehensive checks
./trading-cli tools health --verbose --check-dependencies --performance-test

# Schema management with migration
./trading-cli tools schema --detect-version --convert --backup --validate

# Data validation with detailed reporting
./trading-cli tools validate \
  --batch \
  --format json \
  --comprehensive \
  --output reports/validation_report.json

# Performance diagnostics
./trading-cli tools health --memory-analysis --import-timing --dependency-check
```

## Advanced Features

### **Memory Optimization and Performance**

**Automatic Memory Management:**

- Object pooling for DataFrame operations with configurable pool sizes
- Real-time memory monitoring with configurable thresholds and alerts
- Streaming processing for large datasets (>5MB automatic streaming)
- Intelligent garbage collection optimization with adaptive triggers
- Memory-mapped file access for large CSV files

**Performance Configuration:**

```yaml
# In profile configuration
config:
  memory_optimization:
    enable_pooling: true # Enable object pooling
    pool_size: 100 # Pool size for DataFrame objects
    enable_monitoring: true # Real-time memory monitoring
    memory_threshold_mb: 1000.0 # GC trigger threshold
    streaming_threshold_mb: 5.0 # Automatic streaming threshold
    gc_optimization: true # Intelligent GC management

  performance:
    parallel_processing: true # Enable parallel operations
    batch_size: 1000 # Batch processing size
    cache_results: true # Enable result caching
    progress_tracking: true # Show progress bars
```

**Performance Commands:**

```bash
# Enable memory optimization for large operations
./trading-cli strategy run --profile ma_cross_crypto --memory-optimization

# Performance monitoring mode
./trading-cli strategy sweep --ticker AAPL --memory-monitoring --performance-tracking

# Streaming mode for large datasets
./trading-cli portfolio process large_portfolio.csv --streaming --chunk-size 10000
```

### **Rich Terminal Output Enhancement**

**Advanced Display Features:**

- **Colored Tables**: Performance metrics with green/red coloring
- **Progress Bars**: Real-time progress with ETA for long operations
- **Status Indicators**: Icons and symbols for quick visual feedback
- **Interactive Prompts**: User-friendly configuration and confirmation
- **Formatted Help**: Syntax-highlighted help text with examples

**Terminal Customization:**

```bash
# Disable colors for scripting
./trading-cli strategy run --no-color --output-format json

# Verbose mode with detailed formatting
./trading-cli strategy run --verbose --rich-formatting

# Compact output for CI/CD
./trading-cli strategy run --output-format table --compact
```

### **Error Handling and Validation**

**Comprehensive Error Management:**

- **Pre-flight Validation**: Configuration and dependency checks before execution
- **Runtime Error Recovery**: Graceful handling with fallback mechanisms
- **Detailed Error Messages**: Clear descriptions with resolution guidance
- **Verbose Error Modes**: Stack traces and debugging information
- **Error Reporting**: Structured error logs with context

**Validation Features:**

```bash
# Pre-flight validation
./trading-cli strategy run --dry-run --validate-config --check-dependencies

# Comprehensive validation with detailed reporting
./trading-cli config validate --all-profiles --business-logic --report

# Runtime validation with error recovery
./trading-cli strategy run --validate-runtime --graceful-errors
```

## Enhanced SPDS System (v2.0) - Dual-Source Analysis

### **Revolutionary Multi-Source Analysis**

The Statistical Performance Divergence System supports simultaneous analysis of BOTH trade history AND equity curve data, providing unprecedented analytical depth and reliability.

#### **Key Innovations**

**1. Auto-Detection & Intelligent Source Selection**

- Automatically detects available data sources
- Uses optimal combination based on data quality
- Graceful fallback to single-source when needed
- Complete backward compatibility maintained

**2. Triple-Layer Convergence Analysis**

- **Asset Layer**: Distribution-based analysis of underlying returns
- **Trade History Layer**: Execution-reality analysis from actual trades
- **Equity Curve Layer**: Portfolio performance analysis
- **Convergence Scoring**: Cross-validation between all three layers

**3. Enhanced Exit Signal Generation**

- Multi-source confidence weighting
- Source-specific signal contributions
- Intelligent signal adjustment based on source agreement
- Conservative mode when sources diverge, aggressive when they agree

#### **Data Source Options**

**Auto-Detection Mode:**

```bash
# System automatically detects and uses best available sources
./trading-cli spds analyze portfolio.csv --data-source auto
```

**Explicit Dual-Source:**

```bash
# Force dual-source analysis (requires both data sources)
./trading-cli spds analyze portfolio.csv --data-source both
```

**Single-Source Modes:**

```bash
# Trade history only
./trading-cli spds analyze portfolio.csv --data-source trade-history

# Equity curves only
./trading-cli spds analyze portfolio.csv --data-source equity-curves
```

#### **Enhanced Configuration Parameters**

**13 New Dual-Source Configuration Options:**

**Convergence Thresholds:**

```yaml
DUAL_SOURCE_CONVERGENCE_THRESHOLD: 0.7 # Minimum convergence for dual-source reliability
TRIPLE_LAYER_CONVERGENCE_THRESHOLD: 0.75 # Asset + Trade History + Equity threshold
SOURCE_AGREEMENT_THRESHOLD: 0.8 # Strong agreement classification
SOURCE_DIVERGENCE_THRESHOLD: 0.5 # Significant divergence warning
```

**Source Weighting Strategy:**

```yaml
ASSET_LAYER_WEIGHT: 0.3 # Asset distribution weight (30%)
TRADE_HISTORY_WEIGHT: 0.4 # Trade history weight (40%)
EQUITY_CURVE_WEIGHT: 0.3 # Equity curve weight (30%)
```

**Quality & Reliability Thresholds:**

```yaml
MIN_TRADE_COUNT_FOR_RELIABILITY: 20 # Minimum trades for statistical significance
MIN_EQUITY_PERIODS_FOR_RELIABILITY: 50 # Minimum periods for equity analysis
MULTI_SOURCE_CONFIDENCE_BOOST: 0.15 # 15% confidence boost for source agreement
```

**Behavioral Controls:**

```yaml
DUAL_SOURCE_SIGNAL_ADJUSTMENT: true # Enable intelligent signal modification
CONSERVATIVE_MODE_ON_DIVERGENCE: true # Downgrade signals when sources disagree
AGGRESSIVE_MODE_ON_CONVERGENCE: true # Upgrade signals when sources agree strongly
```

#### **Enhanced Reporting Features**

**Multi-Source Analysis Overview:**

- Dual-source analysis coverage percentage
- Source agreement distribution (Strong/Moderate/Weak)
- Convergence score statistics

**Individual Strategy Details:**

- Source-specific metrics (trade history vs equity analysis)
- Convergence strength classification
- Signal contribution breakdown by source
- Enhanced risk warnings for source divergence

**Source Quality Assessment:**

- Data availability matrix
- Source reliability scoring
- Convergence validation results
- Quality-based confidence adjustments

#### **Advanced Usage Examples**

**Production Analysis with Custom Thresholds:**

```bash
./trading-cli spds analyze risk_on.csv \
  --data-source auto \
  --convergence-threshold 0.8 \
  --conservative-on-divergence \
  --min-trade-count 30
```

**Development Testing with Permissive Settings:**

```bash
./trading-cli spds analyze test_portfolio.csv \
  --data-source both \
  --convergence-threshold 0.6 \
  --min-trade-count 10 \
  --aggressive-on-convergence
```

**Source Diagnostics and Validation:**

```bash
# Check data source availability
./trading-cli spds list-sources portfolio.csv

# Validate source convergence
./trading-cli spds validate-convergence portfolio.csv

# Export detailed source analysis
./trading-cli spds export portfolio.csv --source-details --convergence-matrix
```

#### **Data Requirements for Dual-Source Analysis**

**Required File Structure:**

```
csv/
├── strategies/          # Portfolio files
│   └── risk_on.csv
├── trade_history/       # Trade history data (same filename)
│   └── risk_on.csv
└── ma_cross/equity_data/ # Strategy-specific equity curves
    ├── SMA_20_50.csv
    └── SMA_78_82.csv
```

**Minimum Requirements:**

- **Full Dual-Source**: All three file types present
- **Partial Dual-Source**: Portfolio + either trade history OR equity data
- **Single-Source**: Portfolio + one additional source
- **Fallback Mode**: Portfolio file only (basic analysis)

## Comprehensive Error Handling and Troubleshooting

### **Error Types and Resolution**

#### **1. Configuration Errors**

**Profile Not Found:**

```bash
ERROR: Profile 'invalid_profile' not found in profiles directory

Resolution:
./trading-cli config list
./trading-cli config create-defaults
```

**Invalid Configuration:**

```bash
ERROR: Slow period (10) must be greater than fast period (20)

Resolution:
./trading-cli config show profile_name --format json
./trading-cli config validate profile_name --detailed
```

**Inheritance Errors:**

```bash
ERROR: Circular inheritance detected in profile chain

Resolution:
./trading-cli config validate --all-profiles --check-inheritance
./trading-cli config show profile_name --resolve-inheritance
```

#### **2. Runtime Errors**

**Missing Dependencies:**

```bash
ERROR: Required data file not found: csv/positions/risk_on.csv

Resolution:
./trading-cli tools health --check-dependencies
./trading-cli tools validate --batch --comprehensive
```

**Memory Issues:**

```bash
WARNING: Memory usage exceeds threshold (1000MB)

Resolution:
./trading-cli strategy run --memory-optimization --streaming
./trading-cli strategy run --chunk-size 1000 --gc-optimization
```

**Data Validation Errors:**

```bash
ERROR: Portfolio schema validation failed: missing required columns

Resolution:
./trading-cli tools schema --detect-version --convert
./trading-cli portfolio process --schema-version extended --validate
```

#### **3. Performance Issues**

**Slow Execution:**

```bash
# Diagnosis
./trading-cli tools health --performance-test --memory-analysis

# Resolution
./trading-cli strategy run --memory-optimization --parallel-processing
./trading-cli strategy run --batch-size 500 --cache-results
```

**Large Dataset Issues:**

```bash
# Diagnosis
du -h csv/ && ./trading-cli tools health --memory-analysis

# Resolution
./trading-cli portfolio process --streaming --chunk-size 5000
./trading-cli strategy run --memory-threshold-mb 500 --gc-optimization
```

#### **4. SPDS Dual-Source Issues**

**Source Detection Problems:**

```bash
# Diagnosis
./trading-cli spds list-sources portfolio.csv --detailed
./trading-cli spds health --convergence-analysis

# Resolution
./trading-cli spds analyze portfolio.csv --data-source trade-history
./trading-cli spds analyze portfolio.csv --debug-sources --verbose
```

**Convergence Issues:**

```bash
# Diagnosis
./trading-cli spds export portfolio.csv --convergence-matrix --source-details

# Resolution
./trading-cli spds analyze portfolio.csv --conservative-on-divergence
./trading-cli spds analyze portfolio.csv --convergence-threshold 0.6
```

### **Comprehensive Health Checks**

**System Health Commands:**

```bash
# Complete system health check
./trading-cli tools health --verbose --check-dependencies --performance-test

# Individual subsystem health
./trading-cli spds health --convergence-analysis
./trading-cli trade-history health --data-validation
./trading-cli config validate --all-profiles --business-logic

# Performance diagnostics
./trading-cli tools health --memory-analysis --import-timing --dependency-check
```

**Data Validation Commands:**

```bash
# Comprehensive data validation
./trading-cli tools validate --batch --comprehensive --report

# Portfolio-specific validation
./trading-cli portfolio process --validate --schema-check --fix-issues

# SPDS data validation
./trading-cli spds health --data-quality --source-validation
```

## Best Practices and Performance Optimization

### **Configuration Management Best Practices**

1. **Use Profile Inheritance**: Create base profiles and extend for specific use cases
2. **Version Control Profiles**: Keep profiles in version control for team consistency
3. **Validate Frequently**: Always validate profiles after changes
4. **Document Profiles**: Add meaningful descriptions and tags to profiles
5. **Use Runtime Overrides**: Override specific parameters without modifying profiles

### **Performance Optimization Guidelines**

1. **Enable Memory Optimization**: Use `--memory-optimization` for large datasets
2. **Use Streaming**: Enable streaming for files >5MB with `--streaming`
3. **Batch Processing**: Use appropriate `--batch-size` for operations
4. **Parallel Processing**: Enable `--parallel-processing` for multi-core systems
5. **Monitor Resources**: Use `--memory-monitoring` to track resource usage

### **Error Prevention Strategies**

1. **Pre-flight Validation**: Always use `--dry-run` for complex operations
2. **Health Checks**: Run regular health checks with `./trading-cli tools health`
3. **Configuration Validation**: Validate profiles with `./trading-cli config validate`
4. **Data Validation**: Use `./trading-cli tools validate` before processing
5. **Verbose Logging**: Use `--verbose` for troubleshooting and debugging

### **CLI Usage Best Practices**

1. **Profile-Based Configuration**: Always use profiles instead of inline parameters
2. **Consistent Interface**: Use CLI commands for all trading operations
3. **Rich Output**: Leverage Rich formatting for better user experience
4. **Error Handling**: Enable graceful error handling with appropriate flags
5. **Performance Monitoring**: Monitor performance and optimize based on usage patterns

## Integration and Architecture

### **System Architecture Overview**

**Modular CLI Design:**

- **Command Modules**: Each command group in separate module with consistent interface
- **Configuration System**: YAML-based profile management with Pydantic validation
- **Service Integration**: Integration with strategy engines, portfolio services, and analysis systems
- **Performance Layer**: Memory optimization, streaming, and parallel processing

**Service Integration Patterns:**

- **Strategy Execution Engine**: Type-safe strategy validation and execution
- **Portfolio Processing Service**: Comprehensive portfolio data processing and conversion
- **Statistical Analysis System**: SPDS with dual-source analysis capabilities
- **Trade History Service**: Position management and analysis reporting

### **Performance Architecture**

**Memory Management:**

- **Object Pooling**: Reusable DataFrame pools with configurable sizes
- **Memory Monitoring**: Real-time usage tracking with automatic GC triggers
- **Streaming Processing**: Automatic streaming for large files with configurable thresholds
- **Garbage Collection**: Intelligent GC management with performance optimization

**Parallel Processing:**

- **Adaptive ThreadPools**: Dynamic sizing based on workload and system resources
- **Batch Operations**: Optimized batch processing with configurable sizes
- **Progress Tracking**: Real-time progress monitoring with ETA calculations

## Integration with External Systems

### **API Server Integration**

```bash
# CLI alongside API server
./trading-cli config show api-config &  # Check API configuration
./trading-cli strategy run  # Execute CLI operations independently
```

### **External Tool Integration**

```bash
# JSON output for external analysis
./trading-cli portfolio aggregate --export-format json | jq '.performance.total_return'

# Pipeline integration
./trading-cli spds analyze risk_on.csv --output-format json | \
  python external_analysis_tool.py --input-format json

# CSV export for spreadsheet analysis
./trading-cli strategy run --profile ma_cross_crypto --export-format csv
```

### **CI/CD Integration**

```bash
# Automated testing with health checks
./trading-cli tools health --check-dependencies --performance-test --exit-code

# Batch processing with error handling
./trading-cli portfolio update --validate --export-format json --graceful-errors

# Performance regression testing
./trading-cli tools health --memory-analysis --performance-benchmark
```

## Future Enhancements and Extensibility

### **Planned Features**

1. **Enhanced Profile Templates**: Automated profile generation based on usage patterns
2. **Advanced Monitoring Dashboard**: Real-time performance metrics and system status
3. **Extended Integration**: Additional external tool integrations and API endpoints
4. **Workflow Automation**: Scheduled execution and complex workflow orchestration
5. **Machine Learning Integration**: AI-powered configuration optimization and recommendations

### **Extension Points**

1. **Custom Command Plugins**: Framework for adding domain-specific commands and functionality
2. **Configuration Providers**: Support for additional configuration sources (databases, APIs)
3. **Output Formatters**: Custom output format implementations and rendering engines
4. **Analysis Modules**: Pluggable analysis modules for specialized trading strategies
5. **Data Sources**: Support for additional data sources and market data providers

## Quick Reference Guide

### **Essential Commands**

```bash
# System initialization and health
./trading-cli init                                    # Initialize CLI system
./trading-cli tools health                           # Comprehensive health check
./trading-cli status                                 # System status

# Configuration management
./trading-cli config list                           # List all profiles
./trading-cli config validate                       # Validate all configurations

# Strategy analysis
./trading-cli strategy run --profile ma_cross_crypto # Run strategy analysis
./trading-cli strategy sweep --fast-range 5,15      # Parameter optimization

# Portfolio operations
./trading-cli portfolio update --validate           # Update and aggregate portfolios

# SPDS analysis with dual-source (v2.0)
./trading-cli spds analyze risk_on.csv --data-source auto  # Auto-detection analysis

# Trade history - Position management
./trading-cli trade-history close --strategy STRATEGY --portfolio PORTFOLIO --price PRICE

# System diagnostics
./trading-cli tools health --verbose --check-dependencies
./trading-cli spds health --convergence-analysis
```

### **Emergency Commands**

```bash
# System recovery and reset
./trading-cli init                                   # Reset to defaults
./trading-cli config create-defaults                # Recreate default profiles
./trading-cli tools health --verbose                # Comprehensive diagnostics
./trading-cli config validate --fix-issues          # Fix configuration issues
```

### **Performance Commands**

```bash
# Memory optimization for large operations
./trading-cli strategy run --memory-optimization --streaming
./trading-cli portfolio process --streaming --chunk-size 5000
./trading-cli tools health --memory-analysis --performance-test
```

## Notes

- **System Status**: Production-ready enterprise-grade CLI with comprehensive testing and validation
- **SPDS Enhancement**: v2.0 with revolutionary dual-source analysis and triple-layer convergence
- **Type Safety**: Complete Pydantic validation with business logic enforcement
- **Performance**: Optimized for large-scale operations with memory efficiency and parallel processing
- **Rich Terminal**: Beautiful formatted output with progress tracking and interactive features
- **Error Handling**: Comprehensive error management with graceful degradation and recovery
- **Future-Proof**: Actively maintained with planned enhancements and extensibility framework
- **Enterprise Ready**: Battle-tested with comprehensive documentation and support systems
