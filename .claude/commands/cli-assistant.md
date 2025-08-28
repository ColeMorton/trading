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

- `command`: Specific CLI command (optional: "strategy", "portfolio", "spds", "trade-history", "config", "tools", "concurrency", "positions")
- `operation`: Subcommand operation (optional: "run", "analyze", "export", "validate", "optimize", "monte-carlo", "review", "health", "demo", etc.)
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

The CLI provides **8 main command groups** with comprehensive subcommands:

#### **1. strategy** - Strategy Analysis and Execution

**Available subcommands:**

- `run` - Execute strategy analysis with profile or custom parameters
- `sweep` - Parameter sweep analysis for optimization
- `analyze` - Single strategy detailed analysis

```bash
# Profile-based execution
./trading-cli strategy run --profile ma_cross_crypto

# Custom parameter execution
./trading-cli strategy run --strategy-type SMA --fast-period 8 --slow-period 21 --ticker BTC-USD,ETH-USD

# Parameter sweep analysis
./trading-cli strategy sweep --ticker AAPL --fast-range 5,89 --slow-range 8,89 --min-trades 50

# Single strategy analysis
./trading-cli strategy analyze --ticker BTC-USD --strategy-type SMA --fast-period 9 --slow-period 21

# Advanced filtering
./trading-cli strategy run --profile ma_cross_crypto --min-win-rate 0.6 --min-profit-factor 1.5 --min-sortino 1.0
```

#### **2. portfolio** - Portfolio Processing, Aggregation, and Analysis

**Available subcommands:**

- `update` - Update and aggregate portfolio results
- `process` - Process portfolio files with validation
- `aggregate` - Aggregate multiple portfolios with advanced metrics
- `review` - Comprehensive portfolio analysis with benchmarking and visualization (Advanced)

```bash
# Portfolio update with validation
./trading-cli portfolio update --validate --export-format json

# Process specific portfolio with schema validation
./trading-cli portfolio process portfolio.csv --schema-version extended --validate

# Advanced aggregation with breadth metrics
./trading-cli portfolio aggregate --by-ticker --calculate-breadth --export-format csv

# Batch processing with correlation analysis
./trading-cli portfolio aggregate --correlation-analysis --risk-metrics

# Comprehensive portfolio review analysis (NEW)
./trading-cli portfolio review --profile portfolio_review_multi_crypto

# CSV-based strategy loading with raw_strategies
./trading-cli portfolio review --profile portfolio_review_multi_crypto --benchmark SPY

# Single strategy analysis with custom parameters
./trading-cli portfolio review --ticker BTC-USD --benchmark QQQ --save-plots --export-stats

# Raw data export for external analysis
./trading-cli portfolio review --profile portfolio_review_multi_crypto \
  --export-raw-data \
  --raw-data-formats csv,json,parquet \
  --raw-data-types portfolio_value,returns,trades,positions \
  --include-vectorbt
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

#### **7. concurrency** - Advanced Concurrency Analysis and Strategy Optimization

**Available subcommands:**

- `analyze` - Comprehensive concurrency analysis with trade history export
- `export` - Export trade history data from portfolio analysis
- `review` - Portfolio interaction analysis with visualization
- `optimize` - Find optimal strategy combinations using permutation analysis
- `monte-carlo` - Run Monte Carlo simulations for risk analysis and forecasting
- `health` - Check concurrency analysis system health and validate configurations
- `demo` - Run demo analysis with sample portfolio data

```bash
# Basic concurrency analysis with default profile
./trading-cli concurrency analyze portfolio.csv

# Advanced analysis with profile and comprehensive options
./trading-cli concurrency analyze risk_on.csv \
  --profile risk_on_concurrency \
  --export-trade-history \
  --visualization \
  --memory-optimization \
  --initial-value 25000 \
  --target-var 0.08

# Export trade history with custom settings
./trading-cli concurrency export portfolio.csv \
  --output-dir ./exports \
  --format json \
  --include-analytics

# Portfolio review with detailed analysis
./trading-cli concurrency review portfolio.csv \
  --focus allocation \
  --output-format json \
  --save-report analysis.json

# Strategy optimization with parallel processing
./trading-cli concurrency optimize portfolio.csv \
  --min-strategies 3 \
  --max-permutations 5000 \
  --allocation RISK_ADJUSTED \
  --parallel \
  --output results.json \
  --visualize

# Monte Carlo risk analysis with confidence intervals
./trading-cli concurrency monte-carlo portfolio.csv \
  --simulations 25000 \
  --confidence 90,95,99 \
  --horizon 252 \
  --save-simulations \
  --output-file monte_carlo_results.json \
  --visualize

# System health check and diagnostics
./trading-cli concurrency health \
  --check-dependencies \
  --check-data \
  --check-config \
  --fix

# Demo analysis with sample data
./trading-cli concurrency demo \
  --strategies 10 \
  --output ./demo_results \
  --analyze
```

#### **8. positions** - Position Equity Management and Validation

**Available subcommands:**

- `equity` - Generate equity curves from position-level data
- `validate-equity` - Validate mathematical consistency between position P&L and equity curves
- `validate` - Validate position data integrity and completeness
- `list` - List available portfolios for analysis
- `info` - Show detailed portfolio information and statistics

```bash
# Generate equity data for specific portfolio
./trading-cli positions equity --portfolio protected

# Generate equity data for multiple portfolios
./trading-cli positions equity --portfolio live_signals,risk_on,protected

# Generate with custom metric type and output directory
./trading-cli positions equity --portfolio protected --metric-type mean --output-dir ./custom_equity/

# Validate mathematical consistency of equity curves
./trading-cli positions validate-equity --portfolio protected

# Validate all portfolios with detailed reporting
./trading-cli positions validate-equity --output-format json

# Validate all portfolios with comprehensive error analysis
./trading-cli positions validate-equity --verbose --detailed-errors

# List available portfolios with status information
./trading-cli positions list --with-stats --format table

# Show detailed portfolio information
./trading-cli positions info --portfolio protected --verbose --include-metrics

# Batch validation with custom thresholds
./trading-cli positions validate-equity --all-portfolios --error-threshold 5.0 --warning-threshold 10.0
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
├── ma_cross_crypto.yaml          # Crypto-focused configuration
├── strategies/                    # Strategy-specific profiles
│   ├── current.yaml               # Production configuration
│   ├── ma_cross_crypto.yaml       # Crypto MA Cross optimized
│   └── ma_cross_dev.yaml          # Development configuration
└── concurrency/                   # Concurrency analysis profiles (optimized structure)
    ├── base/                      # Base templates (75% duplication reduction)
    │   ├── concurrency_base.yaml  # Core settings shared by all profiles
    │   ├── conservative_base.yaml # Risk-averse configurations
    │   ├── aggressive_base.yaml   # High-return configurations
    │   └── optimized_base.yaml    # Performance-optimized settings
    ├── portfolio_specific/        # Production-ready profiles
    │   ├── risk_on.yaml          # Aggressive strategies (inherits aggressive_base)
    │   ├── protected.yaml        # Conservative strategies (inherits conservative_base)
    │   └── live_signals.yaml     # Live trading (inherits optimized_base)
    ├── default.yaml              # Default concurrency configuration
    ├── enhanced.yaml             # Full-featured demonstration profile
    └── templates/                # Documentation and reference
        └── complete_reference.yaml # Comprehensive options reference
```

**Concurrency Profile Optimization:**

The concurrency profiles use an advanced inheritance hierarchy that eliminates 75% of configuration duplication:

- **Base Templates** (`/base/`): Contain 90% of common configuration, not used directly
- **Portfolio-Specific** (`/portfolio_specific/`): Minimal 15-20 line profiles for production use
- **Inheritance Chain**: `concurrency_base` → `{conservative|aggressive|optimized}_base` → `{portfolio}_specific`

**Profile Selection Guide for Concurrency:**

| Profile                    | Use Case              | Risk Level | Memory Usage | Key Features                        |
| -------------------------- | --------------------- | ---------- | ------------ | ----------------------------------- |
| `default_concurrency`      | General analysis      | Medium     | Low          | Basic features, standard settings   |
| `risk_on_concurrency`      | Aggressive strategies | High       | Medium       | Monte Carlo, higher risk limits     |
| `protected_concurrency`    | Conservative trading  | Low        | Low          | VaR calculation, strict limits      |
| `live_signals_concurrency` | Production trading    | Medium     | High         | Real-time optimization, hourly data |
| `enhanced_concurrency`     | Full demonstration    | Low        | High         | All features enabled                |

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

# Comprehensive portfolio review analysis
./trading-cli portfolio review --profile portfolio_review_multi_crypto --verbose

# CSV-based multi-strategy analysis with benchmarking
./trading-cli portfolio review --profile portfolio_review_multi_crypto \
  --benchmark SPY \
  --save-plots \
  --export-stats \
  --output-format detailed

# Single strategy comprehensive analysis
./trading-cli portfolio review \
  --ticker BTC-USD \
  --benchmark QQQ \
  --save-plots \
  --export-raw-data \
  --raw-data-formats csv,json \
  --raw-data-types all

# Advanced raw data export with VectorBT objects
./trading-cli portfolio review --profile portfolio_review_multi_crypto \
  --export-raw-data \
  --include-vectorbt \
  --raw-data-output-dir ./advanced_analysis \
  --raw-data-types portfolio_value,returns,trades,orders,positions,statistics

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
  --input-dir data/raw/portfolios/ \
  --output-dir data/raw/aggregated/ \
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

### **Position Equity Management (Enterprise)**

#### **Equity Generation and Mathematical Validation**

```bash
# Generate equity curves for single portfolio
./trading-cli positions equity --portfolio protected --verbose

# Batch equity generation for multiple portfolios
./trading-cli positions equity \
  --portfolio live_signals,risk_on,protected \
  --metric-type mean \
  --output-dir ./equity_analysis/ \
  --parallel-processing

# Advanced equity generation with custom parameters
./trading-cli positions equity \
  --portfolio protected \
  --metric-type best \
  --init-cash 50000 \
  --memory-optimization \
  --verbose

# Mathematical consistency validation for specific portfolio
./trading-cli positions validate-equity \
  --portfolio protected \
  --output-format json \
  --detailed-analysis \
  --error-threshold 5.0

# Comprehensive validation of all portfolios
./trading-cli positions validate-equity \
  --all-portfolios \
  --warning-threshold 10.0 \
  --critical-threshold 15.0 \
  --generate-report

# Advanced validation with custom tolerance levels
./trading-cli positions validate-equity \
  --portfolio risk_on \
  --size-adjustment-enabled \
  --absolute-difference-threshold 100.0 \
  --business-logic-validation
```

#### **Portfolio Information and Diagnostics**

```bash
# List all available portfolios with statistics
./trading-cli positions list \
  --with-stats \
  --include-validation-status \
  --format table \
  --sort-by error-percentage

# Detailed portfolio information and metrics
./trading-cli positions info \
  --portfolio protected \
  --verbose \
  --include-metrics \
  --include-position-breakdown \
  --output-format json

# Portfolio health check with validation
./trading-cli positions validate \
  --portfolio protected \
  --comprehensive \
  --check-data-integrity \
  --validate-timestamps \
  --check-price-data

# Batch portfolio analysis
./trading-cli positions info \
  --all-portfolios \
  --summary-only \
  --export-format csv \
  --output ./portfolio_summary.csv
```

#### **Integration with SPDS and Performance Analysis**

```bash
# Position equity validation integrated with SPDS analysis
./trading-cli positions validate-equity --portfolio risk_on && \
./trading-cli spds analyze risk_on.csv --data-source equity-curves

# Performance monitoring for equity generation
./trading-cli positions equity \
  --portfolio live_signals \
  --memory-monitoring \
  --performance-tracking \
  --streaming

# Mathematical consistency validation with error analysis
./trading-cli positions validate-equity \
  --portfolio protected \
  --verbose \
  --debug-calculations \
  --export-detailed-report ./validation_report.json
```

### **Concurrency Analysis (Advanced Workflows)**

```bash
# Basic concurrency analysis workflow
./trading-cli concurrency analyze risk_on.csv \
  --profile risk_on_concurrency \
  --export-trade-history \
  --visualization

# Complete optimization workflow with Monte Carlo
./trading-cli concurrency optimize portfolio.csv \
  --min-strategies 3 \
  --max-permutations 10000 \
  --parallel && \
./trading-cli concurrency monte-carlo portfolio.csv \
  --simulations 50000 \
  --confidence 90,95,99 \
  --visualize

# Production analysis with custom parameters
./trading-cli concurrency analyze live_signals.csv \
  --profile live_signals_concurrency \
  --hourly \
  --initial-value 50000 \
  --target-var 0.05 \
  --max-risk-strategy 75 \
  --memory-optimization

# Comprehensive review and export workflow
./trading-cli concurrency review portfolio.csv \
  --focus all \
  --save-report review.json && \
./trading-cli concurrency export portfolio.csv \
  --output-dir ./trade_history \
  --format csv \
  --include-analytics

# Integration with position validation
./trading-cli positions validate-equity --portfolio risk_on && \
./trading-cli concurrency analyze risk_on.csv \
  --profile risk_on_concurrency \
  --export-trade-history

# Demo workflow for testing
./trading-cli concurrency demo \
  --strategies 15 \
  --output ./demo_concurrency \
  --analyze && \
./trading-cli concurrency optimize ./demo_concurrency/demo_portfolio.json \
  --min-strategies 5 \
  --visualize
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
data/raw/
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

**Portfolio Review Configuration Errors:**

```bash
ERROR: Raw strategies CSV file does not exist: data/raw/strategies/invalid.csv

# Diagnosis
./trading-cli config show portfolio_review_multi_crypto --format json
ls data/raw/strategies/

# Resolution
./trading-cli portfolio review --profile portfolio_review_multi_crypto --raw-strategies TSLA
./trading-cli config validate portfolio_review_multi_crypto --detailed
```

```bash
ERROR: Either 'strategies' must be provided or 'raw_strategies' must reference a valid CSV file

# Diagnosis
./trading-cli config show portfolio_review_profile --resolve-inheritance

# Resolution
./trading-cli config edit portfolio_review_profile  # Add strategies or raw_strategies
./trading-cli portfolio review --ticker BTC-USD  # Use CLI override
```

#### **2. Runtime Errors**

**Missing Dependencies:**

```bash
ERROR: Required data file not found: data/raw/positions/risk_on.csv

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
du -h data/raw/ && ./trading-cli tools health --memory-analysis

# Resolution
./trading-cli portfolio process --streaming --chunk-size 5000
./trading-cli strategy run --memory-threshold-mb 500 --gc-optimization
```

**Portfolio Review Analysis Errors:**

```bash
ERROR: Could not create benchmark. Primary symbol 'SPY' and fallback symbols (QQQ, VTI, VTSMX) all failed

# Diagnosis
./trading-cli portfolio review --ticker BTC-USD --dry-run --verbose
./trading-cli tools health --check-dependencies --check-network

# Resolution
./trading-cli portfolio review --ticker BTC-USD --benchmark QQQ  # Try different benchmark
./trading-cli portfolio review --profile portfolio_review_multi_crypto  # Use equal_weighted_portfolio
```

```bash
ERROR: No strategies defined in config

# Diagnosis
./trading-cli config show portfolio_review_profile --resolve-inheritance --verbose

# Resolution
./trading-cli portfolio review --ticker BTC-USD  # Add ticker via CLI
./trading-cli config edit portfolio_review_profile  # Add strategies to profile
./trading-cli portfolio review --raw-strategies crypto  # Use CSV loading
```

```bash
ERROR: Failed to create VectorBT portfolio - insufficient data

# Diagnosis
./trading-cli portfolio review --ticker INVALID_TICKER --dry-run --verbose
./trading-cli tools health --check-data-sources

# Resolution
./trading-cli portfolio review --ticker BTC-USD --start-date 2023-01-01  # Adjust date range
./trading-cli portfolio review --profile portfolio_review_multi_crypto --verbose  # Use working profile
```

#### **4. Position Equity Management Issues**

**Mathematical Consistency Validation Errors:**

```bash
ERROR: Position P&L ($606.16) vs Equity Change ($529.13) - 12.77% error exceeds threshold

# Diagnosis
./trading-cli positions validate-equity --portfolio protected --verbose --debug-calculations
./trading-cli positions info --portfolio protected --include-metrics --detailed

# Resolution
./trading-cli positions equity --portfolio protected --memory-optimization --precision-mode
./trading-cli positions validate-equity --portfolio protected --size-adjustment-enabled --tolerance 15.0
```

**Missing Position Data:**

```bash
ERROR: Position file not found: data/raw/positions/protected.csv

# Diagnosis
./trading-cli positions list --check-files --verbose
./trading-cli tools health --check-position-data

# Resolution
./trading-cli strategy run --export-positions
./trading-cli tools validate --position-files --comprehensive
```

**Equity Generation Failures:**

```bash
ERROR: Failed to generate equity curve - insufficient price data

# Diagnosis
./trading-cli positions validate --portfolio protected --check-price-data --verbose
./trading-cli tools health --check-data-dependencies

# Resolution
./trading-cli positions equity --portfolio protected --memory-optimization --streaming
./trading-cli tools health --fix-data-issues --backup
```

**Cash Flow Analysis Warnings:**

```bash
WARNING: Insufficient cash for position entry - chronological execution issue

# Diagnosis
./trading-cli positions info --portfolio protected --cash-flow-analysis --verbose
./trading-cli positions validate --portfolio protected --check-timestamps

# Resolution
./trading-cli positions equity --portfolio protected --baseline-calculation --precision-buffer
./trading-cli positions validate-equity --portfolio protected --absolute-difference-threshold 200.0
```

#### **5. Concurrency Analysis Issues**

**Profile Loading Errors:**

```bash
ERROR: Profile 'risk_on_concurrency' not found

# Diagnosis
./trading-cli config list | grep concurrency
./trading-cli concurrency health --check-config

# Resolution
./trading-cli concurrency analyze risk_on.csv --profile concurrency/portfolio_specific/risk_on
./trading-cli config validate risk_on_concurrency --detailed
```

**Memory Optimization Issues:**

```bash
WARNING: Large portfolio exceeds memory threshold

# Diagnosis
./trading-cli concurrency health --verbose
./trading-cli tools health --memory-analysis

# Resolution
./trading-cli concurrency analyze large_portfolio.csv \
  --profile enhanced_concurrency \
  --memory-optimization \
  --memory-threshold 2000 \
  --streaming
```

**Optimization Convergence Problems:**

```bash
ERROR: Optimization failed to converge after 1000 iterations

# Diagnosis
./trading-cli concurrency optimize portfolio.csv --verbose --dry-run

# Resolution
./trading-cli concurrency optimize portfolio.csv \
  --min-strategies 5 \
  --max-permutations 500 \
  --convergence-threshold 0.005 \
  --convergence-window 25
```

**Monte Carlo Simulation Errors:**

```bash
ERROR: Insufficient data for Monte Carlo analysis

# Diagnosis
./trading-cli concurrency monte-carlo portfolio.csv --verbose
./trading-cli concurrency review portfolio.csv --focus metrics

# Resolution
./trading-cli concurrency monte-carlo portfolio.csv \
  --simulations 5000 \
  --confidence 95 \
  --horizon 126 \
  --bootstrap
```

#### **6. SPDS Dual-Source Issues**

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
./trading-cli positions validate-equity --all-portfolios --health-check
./trading-cli concurrency health --check-dependencies --check-data --check-config
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

# Position equity validation
./trading-cli positions validate --all-portfolios --comprehensive --report
./trading-cli positions validate-equity --batch-validation --error-analysis

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

#### **Raw Strategies CSV Loading (Portfolio Review Innovation)**

The portfolio review system supports loading strategy configurations from CSV files in `data/raw/strategies/`, enabling dynamic strategy management and automated analysis workflows.

**File Structure:**

```
data/raw/strategies/
├── TSLA.csv         # Tesla-focused strategies
├── crypto.csv       # Cryptocurrency strategies
├── RKLB.csv         # Rocket Lab strategies
├── protected.csv    # Conservative strategies
└── risk_on.csv      # Aggressive strategies
```

**Configuration Usage:**

```yaml
# In profile configuration (e.g., portfolio_review_multi_crypto.yaml)
metadata:
  name: portfolio_review_multi_crypto
  description: 'Multi-strategy analysis with CSV-based strategy loading'

config:
  raw_strategies: TSLA # Loads from data/raw/strategies/TSLA.csv
  # This completely overrides any explicit strategies list

  # Other configuration remains the same
  init_cash: 10000.0
  fees: 0.001
  benchmark:
    benchmark_type: equal_weighted_portfolio
```

**CLI Usage Examples:**

```bash
# Profile-based CSV strategy loading
./trading-cli portfolio review --profile portfolio_review_multi_crypto

# Override CSV file at runtime (loads from protected.csv instead)
./trading-cli portfolio review --profile portfolio_review_multi_crypto --raw-strategies protected

# Single strategy with CSV loading
./trading-cli portfolio review --raw-strategies crypto --benchmark SPY --verbose
```

**CSV File Format:**

The CSV files should contain strategy configurations with columns:

- `TICKER` - Asset symbol (required)
- `FAST_PERIOD` - Fast moving average period (default: 20)
- `SLOW_PERIOD` - Slow moving average period (default: 50)
- `STRATEGY_TYPE` - SMA, EMA, or MACD (default: SMA)
- `DIRECTION` - long or short (default: long)
- `POSITION_SIZE` - Position size multiplier (default: 1.0)
- `STOP_LOSS` - Stop loss percentage (optional)
- `USE_HOURLY` - Use hourly data (default: false)
- `RSI_WINDOW` - RSI window for filtering (optional)
- `RSI_THRESHOLD` - RSI threshold (optional)
- `SIGNAL_PERIOD` - MACD signal period (default: 9)

**Dynamic Output Organization:**

When using `raw_strategies`, all outputs are automatically organized into subdirectories:

```
# With raw_strategies: TSLA
data/outputs/portfolio/multi_crypto/TSLA/
├── benchmark_comparison.html
├── benchmark_comparison.png
├── portfolio_value.html
├── drawdowns.html
└── risk_metrics.html

# Raw data exports also organized
data/raw/portfolio_exports/TSLA/
├── portfolio_data.csv
├── trades_data.json
└── statistics.json
```

**Advanced Features:**

- **Automatic Validation**: CSV files are validated for required columns and data types
- **Error Recovery**: Graceful handling of missing or malformed CSV files
- **Strategy Mapping**: Automatic conversion from CSV format to internal strategy configuration
- **Profile Integration**: Full compatibility with profile inheritance and runtime overrides
- **Benchmark Integration**: Equal-weighted portfolio benchmarks automatically created for multi-symbol strategies

**Benefits:**

- **Dynamic Strategy Management**: Update strategies without modifying code or profiles
- **Workflow Automation**: Supports automated analysis pipelines and batch processing
- **Organization**: Clear separation of strategy sets with organized output directories
- **Flexibility**: Mix CSV-based and profile-based configurations as needed
- **Version Control**: Strategy CSV files can be version controlled independently

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
./trading-cli portfolio review --profile portfolio_review_multi_crypto  # Comprehensive portfolio analysis

# SPDS analysis with dual-source (v2.0)
./trading-cli spds analyze risk_on.csv --data-source auto  # Auto-detection analysis

# Trade history - Position management
./trading-cli trade-history close --strategy STRATEGY --portfolio PORTFOLIO --price PRICE

# Concurrency analysis and optimization
./trading-cli concurrency analyze portfolio.csv --profile risk_on_concurrency  # Strategy interaction analysis
./trading-cli concurrency optimize portfolio.csv --min-strategies 3 --parallel # Optimization
./trading-cli concurrency monte-carlo portfolio.csv --simulations 25000        # Risk analysis

# Position equity management
./trading-cli positions equity --portfolio protected          # Generate equity curves
./trading-cli positions validate-equity --portfolio protected # Validate mathematical consistency
./trading-cli positions list                                  # List available portfolios

# System diagnostics
./trading-cli tools health --verbose --check-dependencies
./trading-cli spds health --convergence-analysis
./trading-cli concurrency health --check-dependencies --check-data
./trading-cli positions validate-equity --all-portfolios     # Position validation health check
```

### **Emergency Commands**

```bash
# System recovery and reset
./trading-cli init                                   # Reset to defaults
./trading-cli config create-defaults                # Recreate default profiles
./trading-cli tools health --verbose                # Comprehensive diagnostics
./trading-cli config validate --fix-issues          # Fix configuration issues

# Position data recovery
./trading-cli positions validate --all-portfolios --fix-issues  # Fix position data issues
./trading-cli positions equity --all-portfolios --regenerate    # Regenerate equity curves

# Concurrency system recovery
./trading-cli concurrency health --check-dependencies --fix     # Fix concurrency issues
./trading-cli config validate risk_on_concurrency --fix-issues  # Fix profile issues
```

### **Performance Commands**

```bash
# Memory optimization for large operations
./trading-cli strategy run --memory-optimization --streaming
./trading-cli portfolio process --streaming --chunk-size 5000
./trading-cli portfolio review --profile portfolio_review_multi_crypto --export-raw-data --memory-optimization
./trading-cli positions equity --memory-optimization --parallel-processing
./trading-cli concurrency analyze --memory-optimization --streaming --memory-threshold 2000
./trading-cli concurrency optimize --parallel --max-workers 8
./trading-cli tools health --memory-analysis --performance-test
```

## Notes

- **System Status**: Production-ready enterprise-grade CLI with comprehensive testing and validation
- **Portfolio Review Enhancement**: Comprehensive multi-strategy analysis with CSV-based strategy loading, dynamic output organization, and advanced benchmarking
- **Raw Strategies Innovation**: Dynamic strategy loading from CSV files with automatic subdirectory organization and profile integration
- **SPDS Enhancement**: v2.0 with revolutionary dual-source analysis and triple-layer convergence
- **Position Equity Management**: Mathematical consistency validation with precision fee calculations and cash flow analysis
- **Concurrency Analysis**: Advanced strategy interaction analysis with optimization, Monte Carlo risk analysis, and optimized profile inheritance (75% duplication reduction)
- **Service Architecture**: Integrated portfolio review, visualization, benchmark comparison, and data export services
- **Type Safety**: Complete Pydantic validation with business logic enforcement
- **Performance**: Optimized for large-scale operations with memory efficiency and parallel processing
- **Rich Terminal**: Beautiful formatted output with progress tracking and interactive features
- **Error Handling**: Comprehensive error management with graceful degradation and recovery
- **Future-Proof**: Actively maintained with planned enhancements and extensibility framework
- **Enterprise Ready**: Battle-tested with comprehensive documentation and support systems
