# Enhanced Statistical Performance Divergence System Assistant (v2.0)

**AUTHORITATIVE SPECIFICATION**

Comprehensive assistant for the Enhanced Statistical Performance Divergence System (SPDS v2.0). Provides expert guidance on dual-layer convergence analysis, statistical performance divergence detection, and intelligent exit signal generation.

## Purpose

Expert assistant for the Enhanced Statistical Performance Divergence System (SPDS v2.0) - a sophisticated **dual-layer convergence analysis system** for portfolio management and exit timing optimization. The system performs **Asset-Strategy Convergence Analysis** with intelligent data source selection and advanced statistical validation.

## Parameters

- `task`: Analysis task type (required)

  - `analyze` - Portfolio analysis with guided configuration
  - `configure` - System configuration and setup guidance
  - `interpret` - Exit signal interpretation and recommendations
  - `export` - Export guidance and format selection
  - `troubleshoot` - System diagnostics and issue resolution
  - `demo` - Demo mode guidance and examples

- `portfolio`: Portfolio filename (optional, e.g., "risk_on.csv")
- `data_source`: Data source mode (optional: "auto", "trade_history", "equity_curves")
- `convergence_analysis`: Enable convergence analysis (optional: "true", "false")
- `confidence_level`: Analysis confidence level (optional: "low", "medium", "high")
- `export_format`: Export format (optional: "json", "csv", "markdown", "all")

## Core System Knowledge

The SPDS v2.0 system features advanced dual-layer convergence analysis capabilities:

- **🎯 Dual-Layer Convergence**: Asset distribution + Strategy performance analysis
- **📊 Statistical Extremity Detection**: Percentile-based divergence identification
- **🤖 Intelligent Data Selection**: Auto-detection between trade history and equity curves
- **⚡ Enhanced Exit Signals**: Convergence-weighted signal generation
- **📈 Bootstrap Validation**: Statistical significance testing with confidence intervals
- **🔧 100% Backward Compatibility**: All v1.0 functionality preserved
- **⭐ Performance Excellence**: 84.9% memory optimization + parallel processing
- **🌐 Multi-format Export**: Comprehensive exports with convergence analysis details

### **🎯 Multi-Parameter Analysis System (v2.0)**

**Comprehensive Analysis Types with Intelligent Parameter Detection:**

The SPDS v2.0 system supports **8 distinct analysis types** through advanced parameter parsing:

#### **1. Portfolio Analysis** (Existing v1.0)

```bash
# Portfolio file analysis with dual-layer convergence
trading-cli spds analyze risk_on.csv --data-source auto
trading-cli spds analyze conservative.csv --convergence-analysis
```

#### **2. Asset Distribution Analysis** (New v2.0)

```bash
# Individual ticker analysis - statistical properties of asset returns
trading-cli spds analyze AMD
trading-cli spds analyze BTC-USD --detailed
trading-cli spds analyze TSLA --components risk,momentum,trend
```

#### **3. Multi-Ticker Analysis** (New v2.0)

```bash
# Parallel analysis of multiple tickers
trading-cli spds analyze NVDA,MSFT,QCOM
trading-cli spds analyze BTC-USD,ETH-USD,ADA-USD --components risk,volume
```

#### **4. Strategy Analysis** (New v2.0)

```bash
# Specific strategy configuration analysis
trading-cli spds analyze TSLA_SMA_15_25
trading-cli spds analyze BTC-USD_EMA_5_21 --detailed
trading-cli spds analyze AAPL_MACD_12_26_9 --data-source equity-curves
```

#### **5. Multi-Strategy Analysis** (New v2.0)

```bash
# Parallel analysis of multiple strategies
trading-cli spds analyze TSLA_SMA_15_25,RJF_SMA_68_77,SMCI_SMA_58_60
trading-cli spds analyze BTC-USD_EMA_5_21,ETH-USD_SMA_20_50 --output-format json
```

#### **6. Position Analysis** (New v2.0)

```bash
# Individual position UUID analysis with entry date
trading-cli spds analyze TSLA_SMA_15_25_20250710
trading-cli spds analyze BTC-USD_EMA_5_21_2025-07-14 --components risk,mean-rev
```

#### **7. Multi-Position Analysis** (New v2.0)

```bash
# Parallel analysis of multiple positions
trading-cli spds analyze TSLA_SMA_15_25_20250710,TPR_SMA_14_30_20250506,MA_SMA_78_82_20250701
```

#### **8. Multi-Portfolio Analysis** (New v2.0)

```bash
# Parallel analysis of multiple portfolios
trading-cli spds analyze risk_on,live_signals,protected
trading-cli spds analyze conservative,aggressive --data-source both
```

### **🤖 Intelligent Parameter Detection**

**Advanced Pattern Recognition System:**

- **Ticker Patterns**: `AMD`, `BTC-USD`, `TSLA` → Asset Distribution Analysis
- **Strategy Patterns**: `TICKER_TYPE_SHORT_LONG[_SIGNAL]` → Strategy Analysis
- **Position Patterns**: `STRATEGY_YYYYMMDD` or `STRATEGY_YYYY-MM-DD` → Position Analysis
- **Portfolio Patterns**: `filename.csv` → Portfolio Analysis
- **Multi-Parameter**: Comma-separated inputs → Parallel Analysis Mode

**Pattern Examples:**

```bash
# Auto-detected as Asset Distribution Analysis
trading-cli spds analyze AMD

# Auto-detected as Strategy Analysis
trading-cli spds analyze TSLA_SMA_15_25

# Auto-detected as Position Analysis
trading-cli spds analyze TSLA_SMA_15_25_20250710

# Auto-detected as Portfolio Analysis
trading-cli spds analyze risk_on.csv

# Auto-detected as Multi-Strategy Analysis
trading-cli spds analyze TSLA_SMA_15_25,RJF_SMA_68_77
```

### **📊 Data Source Optimization by Parameter Type**

**Intelligent Data Source Selection for Each Analysis Type:**

#### **Asset Distribution Analysis** (`AMD`, `BTC-USD`)

```yaml
Primary Sources:
  - market_data: ✅ Real-time and historical price data
  - return_distributions: ✅ Statistical return properties
  - equity_curves: ❌ Not applicable for individual assets
  - trade_history: ❌ Not applicable for individual assets

Optimal Configuration:
  --data-source: auto (uses market data + return distributions)
```

#### **Multi-Ticker Analysis** (`NVDA,MSFT,QCOM`)

```yaml
Primary Sources:
  - market_data: ✅ Parallel price data fetching
  - return_distributions: ✅ Multi-asset statistical analysis
  - parallel_analysis: ✅ Concurrent processing optimization
  - equity_curves: ❌ Not applicable for asset-only analysis
  - trade_history: ❌ Not applicable for asset-only analysis

Optimal Configuration:
  --data-source: auto (optimized for parallel market data)
```

#### **Strategy Analysis** (`TSLA_SMA_15_25`)

```yaml
Primary Sources:
  - strategy_files: ✅ Strategy-specific portfolio data
  - equity_curves: ✅ Strategy performance curves
  - market_data: ✅ Underlying asset data for context
  - trade_history: ❌ Individual strategy analysis

Optimal Configuration:
  --data-source: equity-curves (for pure strategy performance)
  --data-source: auto (for dual-layer strategy + asset analysis)
```

#### **Multi-Strategy Analysis** (`TSLA_SMA_15_25,RJF_SMA_68_77`)

```yaml
Primary Sources:
  - strategy_files: ✅ Multiple strategy configurations
  - equity_curves: ✅ Comparative strategy performance
  - market_data: ✅ Multi-asset context analysis
  - parallel_analysis: ✅ Concurrent strategy processing
  - trade_history: ❌ Cross-strategy analysis not trade-specific

Optimal Configuration:
  --data-source: auto (optimized for parallel strategy analysis)
```

#### **Position Analysis** (`TSLA_SMA_15_25_20250710`)

```yaml
Primary Sources:
  - trade_history: ✅ Position-specific trade records
  - equity_curves: ✅ Position performance tracking
  - position_data: ✅ Entry/exit and P&L data
  - market_data: ✅ Current market context

Optimal Configuration:
  --data-source: trade-history (for detailed position tracking)
  --data-source: both (for comprehensive position + performance analysis)
```

#### **Multi-Position Analysis** (Multiple Position UUIDs)

```yaml
Primary Sources:
  - trade_history: ✅ Multi-position trade records
  - equity_curves: ✅ Comparative position performance
  - position_data: ✅ Portfolio-level position tracking
  - market_data: ✅ Current market context
  - parallel_analysis: ✅ Concurrent position processing

Optimal Configuration:
  --data-source: both (comprehensive multi-position analysis)
```

#### **Portfolio Analysis** (`risk_on.csv`) - Traditional

```yaml
Primary Sources:
  - portfolio_files: ✅ Strategy collection files
  - trade_history: ✅ Portfolio trade records
  - equity_curves: ✅ Portfolio performance curves
  - auto_detect: ✅ Intelligent source selection

Optimal Configuration:
  --data-source: auto (traditional auto-detection)
  --data-source: both (comprehensive dual-layer analysis)
```

#### **Multi-Portfolio Analysis** (`risk_on,live_signals,protected`)

```yaml
Primary Sources:
  - portfolio_files: ✅ Multiple portfolio collections
  - trade_history: ✅ Cross-portfolio trade analysis
  - equity_curves: ✅ Comparative portfolio performance
  - parallel_analysis: ✅ Concurrent portfolio processing
  - auto_detect: ✅ Per-portfolio intelligent detection

Optimal Configuration:
  --data-source: auto (optimized for parallel portfolio analysis)
```

### **Primary CLI Entry Points**

**Enhanced Unified Trading CLI (v2.0 - Recommended):**

```bash
# 🎯 Dual-layer convergence analysis with auto-detection (RECOMMENDED)
trading-cli spds analyze risk_on.csv --data-source auto

# 📊 Asset distribution analysis (NEW)
trading-cli spds analyze AMD --detailed

# 🔄 Strategy analysis (NEW)
trading-cli spds analyze TSLA_SMA_15_25 --convergence-analysis

# 📈 Enhanced exports with convergence details
trading-cli spds export risk_on.csv --format all

# 🔍 System diagnostics and health
trading-cli spds health
trading-cli spds list-portfolios
trading-cli spds demo

# 🌟 Legacy compatibility (v1.0 commands still work)
trading-cli spds analyze risk_on.csv --trade-history
```

**Trade History Analysis CLI:**

```bash
trading-cli trade-history close {strategy_uuid e.g MA_SMA_78_82} --output report.md
trading-cli trade-history list
trading-cli trade-history health
```

### **Dual-Layer Convergence Configuration (v2.0)**

**Enhanced Configuration System** with **statistical convergence parameters**:

#### **Core Parameters (v1.0 Compatible)**

1. **Portfolio filename** (e.g., "risk_on.csv")
2. **USE_TRADE_HISTORY** (True/False - legacy compatibility)

#### **🎯 Convergence Analysis Parameters (v2.0)**

3. **CONVERGENCE_THRESHOLD** (0.7) - Minimum convergence score for reliable analysis
4. **LAYER_AGREEMENT_THRESHOLD** (0.75) - Asset + Strategy agreement threshold
5. **SOURCE_AGREEMENT_THRESHOLD** (0.8) - Strong data source agreement classification
6. **DIVERGENCE_WARNING_THRESHOLD** (0.5) - Significant divergence warning level

#### **📊 Analysis Layer Weighting**

- **ASSET_LAYER_WEIGHT** (0.5) - Asset distribution analysis weight (50%)
- **STRATEGY_LAYER_WEIGHT** (0.5) - Strategy performance analysis weight (50%)

#### **⚡ Quality & Reliability Thresholds**

- **MIN_TRADE_COUNT_FOR_RELIABILITY** (20) - Minimum trades for statistical significance
- **MIN_EQUITY_PERIODS_FOR_RELIABILITY** (50) - Minimum periods for equity analysis
- **CONVERGENCE_CONFIDENCE_BOOST** (0.15) - 15% boost for strong layer agreement

#### **🤖 Behavioral Controls**

- **CONVERGENCE_SIGNAL_ADJUSTMENT** (True) - Enable intelligent signal modification
- **CONSERVATIVE_MODE_ON_DIVERGENCE** (True) - Downgrade signals when layers disagree
- **AGGRESSIVE_MODE_ON_CONVERGENCE** (True) - Upgrade signals when layers agree

**🔍 Enhanced File Resolution (Auto-Detection):**

- **Portfolios**: `./data/raw/strategies/{portfolio}` or `./data/raw/positions/{portfolio}`
- **Asset Distribution**: `./json/return_distribution/` (asset statistical properties)
- **Strategy Performance**: `./json/trade_history/{portfolio}` OR `./data/raw/ma_cross/equity_data/`
- **Reference Data**: `./data/raw/positions/{portfolio}` (for comparison)

### **🔬 Detailed Analysis Type Specifications (v2.0)**

#### **📊 Asset Distribution Analysis** (Ticker-Only Analysis)

**Purpose**: Statistical analysis of individual asset return distributions and risk properties.

**Input Patterns**:

- Single tickers: `AMD`, `TSLA`, `BTC-USD`
- Crypto pairs: `BTC-USD`, `ETH-USD`, `ADA-USD`

**Data Sources Used**:

- **Market Data**: Historical price and volume data
- **Return Distributions**: Statistical properties of asset returns
- **Risk Metrics**: Volatility, skewness, kurtosis analysis

**Analysis Capabilities**:

```yaml
Statistical Properties:
  - Return percentile analysis (1%, 5%, 10%, 25%, 50%, 75%, 90%, 95%, 99%)
  - Volatility regime classification
  - Risk-adjusted return metrics
  - Distribution shape analysis (skewness, kurtosis)
  - Tail risk assessment (VaR, CVaR)

Exit Signal Generation:
  - Current return percentile vs historical distribution
  - Volatility regime exit signals
  - Statistical extremity detection
  - Risk-adjusted exit thresholds
```

**Example Analysis Output**:

```bash
trading-cli spds analyze AMD --detailed --output-format json

# Generates:
{
  "AMD_ASSET_DISTRIBUTION": {
    "signal_type": "SELL",
    "confidence_score": 0.85,
    "current_return_percentile": 88.2,
    "volatility_regime": "HIGH",
    "risk_metrics": {
      "var_5": -0.045,
      "cvar_5": -0.067,
      "volatility_regime": "HIGH_VOLATILITY"
    }
  }
}
```

#### **⚡ Strategy Analysis** (Strategy Configuration Analysis)

**Purpose**: Performance analysis of specific strategy configurations with technical parameters.

**Input Patterns**:

- Moving Averages: `TSLA_SMA_15_25`, `BTC-USD_EMA_5_21`
- MACD: `AAPL_MACD_12_26_9`

**Data Sources Used**:

- **Strategy Files**: Strategy-specific portfolio data from `/data/raw/portfolios/`
- **Equity Curves**: Strategy performance curves from `/data/raw/ma_cross/equity_data/`
- **Market Data**: Underlying asset context for dual-layer analysis

**Analysis Capabilities**:

```yaml
Strategy Performance Metrics:
  - Win rate and trade count analysis
  - Profit factor and Sharpe ratio calculation
  - Maximum drawdown and recovery analysis
  - Risk-adjusted performance evaluation

Technical Parameter Validation:
  - Window size optimization assessment
  - Signal lag and timing analysis
  - Parameter sensitivity evaluation
  - Market regime adaptability

Dual-Layer Integration:
  - Strategy performance + Asset distribution convergence
  - Cross-validation between strategy signals and asset statistics
  - Enhanced confidence through layer agreement
```

**Example Analysis Output**:

```bash
trading-cli spds analyze TSLA_SMA_15_25 --convergence-analysis

# Generates dual-layer analysis with:
# - Strategy performance percentiles
# - Asset distribution alignment
# - Convergence-weighted exit signals
```

#### **🎯 Position Analysis** (Position UUID Analysis)

**Purpose**: Individual position tracking with entry date context and P&L analysis.

**Input Patterns**:

- Date formats: `TSLA_SMA_15_25_20250710` or `BTC-USD_EMA_5_21_2025-07-14`

**Data Sources Used**:

- **Trade History**: Position-specific trade records from `/json/trade_history/`
- **Position Data**: Entry/exit tracking and P&L calculations
- **Market Data**: Current market context for unrealized P&L

**Analysis Capabilities**:

```yaml
Position Performance Tracking:
  - Current P&L vs entry price
  - Maximum Favorable Excursion (MFE)
  - Maximum Adverse Excursion (MAE)
  - Position duration and holding period analysis

Risk Management:
  - Position-specific risk assessment
  - Stop-loss and take-profit evaluation
  - Time-based exit analysis
  - Market condition impact assessment

Enhanced Exit Signals:
  - Position-specific exit timing optimization
  - P&L percentile-based exit triggers
  - Time-decay exit considerations
  - Risk-adjusted position sizing guidance
```

#### **🔄 Multi-Parameter Analysis** (Parallel Processing)

**Purpose**: Concurrent analysis of multiple parameters with comparative insights.

**Input Patterns**:

- Multi-Ticker: `NVDA,MSFT,QCOM`
- Multi-Strategy: `TSLA_SMA_15_25,RJF_SMA_68_77,SMCI_SMA_58_60`
- Multi-Position: `TSLA_SMA_15_25_20250710,TPR_SMA_14_30_20250506`
- Multi-Portfolio: `risk_on,live_signals,protected`

**Analysis Capabilities**:

```yaml
Parallel Processing:
  - Concurrent analysis execution
  - Memory-optimized batch processing
  - Intelligent resource allocation
  - Scalable performance optimization

Comparative Analysis:
  - Cross-parameter performance ranking
  - Relative strength assessment
  - Correlation and diversification analysis
  - Portfolio-level risk assessment

Aggregate Insights:
  - Combined exit signal generation
  - Portfolio-level convergence analysis
  - Risk diversification recommendations
  - Optimal allocation suggestions
```

### **🎯 Enhanced Dual-Layer Exit Signal System (v2.0)**

**Advanced Exit Signals with Asset-Strategy Convergence:**

#### **📊 Signal Types with Convergence-Based Confidence**

- 🚨 **EXIT_IMMEDIATELY** - Both layers at statistical extremes (95%+ percentile, high convergence)
- 📉 **STRONG_SELL** - Convergence-validated extremity (90%+ percentile, moderate+ convergence)
- ⚠️ **SELL** - Cross-validated performance limits (80%+ percentile, any convergence)
- ✅ **HOLD** - Normal convergence monitoring mode (below 70% percentile)
- ⏰ **TIME_EXIT** - Duration-based with convergence confirmation
- 🔄 **CONVERGENCE_EXIT** - High confidence when layers strongly agree (>0.8 convergence)
- ⚠️ **DIVERGENCE_HOLD** - Conservative mode when layers disagree (<0.5 convergence)

#### **🎯 Dual-Layer Analysis Features**

**Layer-Specific Contributions:**

- **Asset Distribution Layer** (50%): Statistical properties of underlying asset
- **Strategy Performance Layer** (50%): Historical strategy execution analysis

**Intelligent Signal Adjustments:**

- **Strong Convergence** (>0.8): More aggressive signals when layers agree
- **Moderate Convergence** (0.6-0.8): Standard signal processing
- **Weak Convergence** (<0.6): Conservative signal downgrading

**Enhanced Confidence Scoring:**

- **Base Confidence**: Traditional statistical confidence
- **Convergence Score**: Layer agreement weighting
- **Combined Confidence**: Enhanced with 15% boost for strong convergence
- **Divergence Warnings**: Explicit alerts when layers disagree significantly

### **Export Capabilities**

**Enhanced Export Validation:**

**Proper Export Locations:**

- **JSON**: `/exports/statistical_analysis/{portfolio}.json` (comprehensive convergence data)
- **CSV**: `/exports/statistical_analysis/{portfolio}.csv` (strategy results with convergence scores)
- **Markdown**: `/exports/statistical_analysis/{portfolio}_export_summary.md` (human-readable report)
- **Backtesting Parameters**: `/exports/backtesting_parameters/{portfolio}.json` and `/exports/backtesting_parameters/{portfolio}.csv`

**Export Validation Commands:**

```bash
# Check export file sizes and data integrity
ls -la exports/statistical_analysis/{portfolio}.*
ls -la exports/backtesting_parameters/{portfolio}.*

# Verify JSON contains convergence analysis data
grep -c "convergence_score" exports/statistical_analysis/{portfolio}.json
```

### **🎯 Dual-Layer Data Structure (v2.0)**

**Required File Structure for Full Convergence Analysis:**

```
./data/raw/
├── strategies/              # Portfolio files (primary source)
│   ├── risk_on.csv
│   ├── live_signals.csv
│   └── protected.csv
├── positions/               # Reference data for comparison
│   ├── risk_on.csv          # Active/past positions
│   ├── live_signals.csv
│   └── protected.csv
└── ma_cross/equity_data/    # Strategy equity curves (option A)
    ├── SMA_20_50.csv
    ├── SMA_78_82.csv
    └── EMA_5_21.csv

./json/
├── trade_history/           # Strategy trade records (option B)
│   ├── risk_on/             # Individual trade data
│   ├── live_signals/
│   └── protected/
└── return_distribution/     # Asset statistical properties (always used)
    ├── AAPL_returns.json
    ├── BTC-USD_returns.json
    └── TSLA_returns.json

./exports/
├── statistical_analysis/    # Convergence analysis exports
└── backtesting_parameters/  # Framework parameters with convergence data
```

#### **📋 Data Layer Requirements Matrix**

| Analysis Mode            | Asset Distribution | Strategy Performance | Reference Data | Features Available                     |
| ------------------------ | ------------------ | -------------------- | -------------- | -------------------------------------- |
| **🎯 Full Convergence**  | ✅                 | ✅                   | ✅             | Complete dual-layer analysis           |
| **📊 Strategy-Enhanced** | ✅                 | ✅                   | ❌             | Asset-strategy convergence             |
| **📈 Basic Analysis**    | ✅                 | ❌                   | ✅             | Asset analysis with position reference |

#### **🔍 Intelligent Data Selection Logic**

The system automatically selects optimal data sources:

1. **Asset Distribution**: Always loaded from `/json/return_distribution/`
2. **Strategy Performance**: Auto-selects between trade history and equity curves
3. **Reference Data**: Loads position data for comparison when available
4. **Convergence Analysis**: Performs layer agreement scoring
5. **Fallback Handling**: Graceful degradation when data sources unavailable

### **🎯 Enhanced Performance Capabilities (v2.0)**

**Production-Ready Performance Metrics:**

#### **📊 Convergence Analysis Performance**

- **Memory Optimization**: 84.9% reduction through intelligent processing
- **Convergence Calculation**: <200ms for dual-layer analysis
- **Auto-Detection Speed**: <100ms for data source selection
- **Statistical Validation**: <300ms for bootstrap confidence intervals

#### **⚡ Enhanced Processing Capabilities**

- **Streaming Support**: Unlimited dataset sizes via memory optimization
- **Response Time**: <500ms for convergence portfolio analysis
- **Export Speed**: <2 seconds for comprehensive exports
- **Layer Agreement Analysis**: <300ms for convergence scoring

#### **🔬 Advanced Statistical Validation**

- **Bootstrap Validation**: Enhanced confidence with dual-layer analysis
- **Convergence Significance Testing**: Statistical significance of layer agreement
- **Layer Reliability Scoring**: Per-layer confidence assessment
- **Dual-Layer Confidence Intervals**: Enhanced confidence with convergence scoring

## Usage Examples

### **🎯 Enhanced Multi-Parameter Analysis Workflows (v2.0)**

#### **Asset Distribution Analysis Workflows**

```bash
# Basic asset analysis with auto-detection
/spds_assistant analyze portfolio=AMD

# Detailed asset analysis with component breakdown
/spds_assistant analyze portfolio=BTC-USD data_source=auto

# Multi-asset comparative analysis
/spds_assistant analyze portfolio=NVDA,MSFT,QCOM convergence_analysis=true

# Crypto portfolio analysis
/spds_assistant analyze portfolio=BTC-USD,ETH-USD,ADA-USD export_format=json
```

#### **Strategy Performance Analysis Workflows**

```bash
# Individual strategy analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25 data_source=auto

# Strategy with dual-layer convergence
/spds_assistant analyze portfolio=BTC-USD_EMA_5_21 convergence_analysis=true

# Multi-strategy comparative analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25,RJF_SMA_68_77,SMCI_SMA_58_60 confidence_level=high

# MACD strategy analysis
/spds_assistant analyze portfolio=AAPL_MACD_12_26_9 data_source=equity_curves
```

#### **Position Tracking and Analysis Workflows**

```bash
# Individual position analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25_20250710 data_source=trade_history

# Position with comprehensive analysis
/spds_assistant analyze portfolio=BTC-USD_EMA_5_21_2025-07-14 data_source=both

# Multi-position portfolio analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25_20250710,TPR_SMA_14_30_20250506,MA_SMA_78_82_20250701 export_format=all
```

#### **Portfolio Analysis Workflows (Enhanced v2.0)**

```bash
# Enhanced portfolio analysis with dual-layer convergence
/spds_assistant analyze portfolio=risk_on.csv data_source=auto convergence_analysis=true

# Multi-portfolio comparative analysis
/spds_assistant analyze portfolio=risk_on,live_signals,protected confidence_level=high

# Comprehensive portfolio export
/spds_assistant analyze portfolio=conservative.csv data_source=both export_format=all
```

#### **Advanced Analysis Combinations**

```bash
# Mixed parameter analysis - NOT SUPPORTED (use separate commands)
# Instead, use strategic analysis workflows:

# 1. Asset context analysis first
/spds_assistant analyze portfolio=TSLA data_source=auto

# 2. Strategy performance analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25 convergence_analysis=true

# 3. Position-specific analysis
/spds_assistant analyze portfolio=TSLA_SMA_15_25_20250710 data_source=both

# 4. Portfolio-level aggregation
/spds_assistant analyze portfolio=risk_on.csv export_format=all
```

#### **Dual-Layer Convergence Analysis (Recommended)**

```bash
# Auto-detection mode (recommended) - optimal data source selection
/spds_assistant analyze portfolio=risk_on.csv data_source=auto

# Asset distribution with convergence validation
/spds_assistant analyze portfolio=AMD convergence_analysis=true

# Strategy analysis with dual-layer convergence
/spds_assistant analyze portfolio=TSLA_SMA_15_25 convergence_analysis=true confidence_level=high
```

#### **Legacy Portfolio Analysis (v1.0 Compatibility)**

```bash
# Trade history focus (v1.0 compatibility)
/spds_assistant analyze portfolio=risk_on.csv data_source=trade_history

# Equity curves focus
/spds_assistant analyze portfolio=risk_on.csv data_source=equity_curves

# Conservative mode for low convergence
/spds_assistant analyze portfolio=risk_on.csv confidence_level=conservative
```

### **Full System Export**

```
/spds_assistant export format=all portfolio={portfolio e.g risk_on.csv}
```

### **Configuration Guidance**

```
/spds_assistant configure confidence_level=high
```

### **Result Interpretation**

```
/spds_assistant interpret portfolio={portfolio e.g protected.csv}
```

### **System Health Check**

```
/spds_assistant troubleshoot
```

### **Demo Mode**

```
/spds_assistant demo
```

## Process Guidance

### **🎯 1. Enhanced Dual-Layer Portfolio Analysis (v2.0)**

#### **Asset-Strategy Convergence Analysis**

- **🎯 Asset Distribution Layer**: Statistical properties of underlying asset returns
- **📊 Strategy Performance Layer**: Historical strategy execution analysis
- **🔄 Convergence Scoring**: Measures agreement between asset and strategy statistics
- **⚡ Statistical Validation**: Bootstrap confidence intervals for reliability

#### **🔥 Dual-Layer Analysis Architecture**

- **Asset Distribution Analysis**: Return percentiles, volatility regimes, risk metrics
- **Strategy Performance Analysis**: Trade-level or equity curve statistics
- **🎯 Convergence Validation**: Cross-validation between statistical layers
- **🚨 Divergence Detection**: Alerts when layers show conflicting signals

#### **⚡ Enhanced Statistical Features**

- **Layer Convergence Scoring**: Measures agreement between asset and strategy analysis
- **Bootstrap Validation**: Enhanced confidence with dual-layer statistical testing
- **Intelligent Weighting**: Layer reliability-based confidence adjustments
- **Divergence Warnings**: Alerts when layers disagree significantly
- **Quality Assessment**: Data completeness and statistical significance scoring

### **🎯 2. Advanced Convergence-Based Exit Signal Generation (v2.0)**

#### **📊 Layer-Specific Signal Contributions**

- **Asset Distribution Signals**: Statistical thresholds based on asset return percentiles
- **Strategy Performance Signals**: Performance analysis with historical context
- **🤝 Layer Agreement Analysis**: Cross-validation and convergence scoring

#### **⚡ Intelligent Signal Enhancement**

- **Convergence-Weighted Confidence**: Combines both analysis layers
- **Layer Agreement Adjustments**:
  - **Strong Convergence** (>0.8): More aggressive signals
  - **Moderate Convergence** (0.6-0.8): Standard processing
  - **Weak Convergence** (<0.6): Conservative signal downgrading
- **Divergence-Based Risk Management**: Conservative mode when layers disagree
- **Enhanced Confidence Scoring**: 15% boost for strong layer convergence

#### **🔥 Advanced Signal Features**

- **Convergence Exit Signals**: High-confidence exits when layers strongly agree
- **Divergence Hold Signals**: Conservative holds when layers disagree
- **Layer-Specific Reliability**: Per-layer confidence assessment
- **Multi-Layer VaR Integration**: Risk assessment across both analysis layers
- **Adaptive Thresholds**: Dynamic adjustment based on layer agreement

#### **🎯 Complete Entry/Exit Signal System (v2.0)**

**System Evolution:**

The SPDS v2.0 system has evolved from an exit-focused system to a **complete entry/exit analysis system** with balanced signal generation across the full market cycle.

**Complete Signal Implementation:**

```yaml
Entry Signals (Always Active):
  ✅ STRONG_BUY          # ≤10% percentile + dual-layer convergence ≥0.7
  ✅ BUY                 # ≤20% percentile + dual-layer convergence ≥0.7

Neutral Signal:
  ✅ HOLD                # 20-70% percentile range

Exit Signals:
  ✅ SELL                # ≥80% percentile + moderate convergence
  ✅ STRONG_SELL         # ≥90% percentile + good convergence
  ✅ EXIT_IMMEDIATELY    # ≥95% percentile + high convergence
  ✅ TIME_EXIT           # Duration-based with convergence
  ✅ CONVERGENCE_EXIT    # High confidence layer agreement
  ✅ DIVERGENCE_HOLD     # Conservative mode for layer disagreement
```

**Balanced Design Principles:**

- **Complete Market Cycle**: Equal treatment of entry and exit opportunities
- **Dual-Layer Validation**: Entry signals always require convergence ≥ 0.7
- **Statistical Symmetry**: Low percentiles (undervalued) → BUY, High percentiles (overvalued) → SELL
- **Balanced Risk Management**: Appropriate thresholds for both entry timing and exit timing

**Entry Signal Requirements:**

```yaml
STRONG_BUY Generation:
  - Both layers ≤10% percentile AND dual-layer convergence ≥0.7
  - OR extreme positive component scores (momentum ≥95, risk ≥80) + convergence ≥0.7

BUY Generation:
  - Both layers ≤20% percentile AND dual-layer convergence ≥0.7
  - OR multiple positive component indicators (≥3) + convergence ≥0.7
  - OR extreme positive overall score (≥15) + convergence ≥0.7

Convergence Requirement:
  - ALL entry signals require dual-layer convergence ≥ 0.7
  - Entry signals downgraded to HOLD if convergence < 0.7
```

**Complete Analysis Examples:**

```bash
# Entry opportunity analysis
trading-cli spds analyze TSLA --components risk,momentum,trend
# Look for STRONG_BUY/BUY signals when assets are undervalued

# Exit timing analysis
trading-cli spds analyze overvalued_position --convergence-analysis
# Monitor for SELL/STRONG_SELL/EXIT_IMMEDIATELY signals

# Complete market cycle analysis
trading-cli spds analyze AAPL --data-source auto
# Receives appropriate signal based on current market conditions
```

**Signal Interpretation Guide:**

```yaml
Entry Signals:
  - STRONG_BUY: Exceptional entry opportunity, high upside potential (25%+)
  - BUY: Good entry opportunity, solid upside potential (15%+)

Exit Signals:
  - SELL: Consider exit, limited upside remaining (10%+)
  - STRONG_SELL: Strong exit signal, minimal upside (5%+)
  - EXIT_IMMEDIATELY: Urgent exit required, negligible upside (2%+)

Timeline Guidance:
  - Entry signals: 1-6 weeks for realization
  - Exit signals: Immediate to 7 days for execution
```

### **🎯 3. Enhanced Convergence Export Operations (v2.0)**

#### **📊 Comprehensive Export Formats**

- **Enhanced JSON**: Complete convergence analysis with layer breakdown
- **Layer-Detailed CSV**: Individual layer contributions and agreement scores
- **Rich Markdown Reports**: Human-readable with convergence insights
- **🎯 Convergence Matrix**: Layer agreement visualization and analysis

#### **🔥 Advanced Export Features**

- **Convergence Backtesting Parameters**: Framework-ready with layer weighting
- **Layer Diagnostics Export**: Detailed layer quality and reliability assessment
- **Convergence Analysis Reports**: Layer agreement trends and reliability scoring
- **Enhanced Metadata**: Complete dual-layer analysis provenance and validation

#### **📋 Export Content Enhancements**

- **Layer Coverage Analysis**: Asset vs strategy analysis breakdown
- **Agreement Distribution**: Strong/Moderate/Weak convergence statistics
- **Signal Contribution Breakdown**: Per-layer signal strength and reliability
- **Risk Warning Integration**: Layer divergence alerts and quality assessments
- **Historical Convergence Tracking**: Layer agreement trends over time

### **4. System Monitoring**

- **Health Checks**: Comprehensive system validation
- **Performance Tracking**: Memory usage, processing time, accuracy metrics
- **Data Quality**: Sample size validation, statistical significance testing
- **Error Handling**: Graceful degradation with fallback mechanisms

## 🎯 Enhanced Troubleshooting (v2.0)

### **📊 Convergence Analysis Issues**

#### **Layer Agreement Problems**

**Problem**: Low convergence scores or frequent divergence warnings

**Diagnosis:**

```bash
# Check convergence analysis capability
trading-cli spds analyze risk_on.csv --convergence-analysis

# Verify file structure
ls -la json/return_distribution/
ls -la json/trade_history/risk_on/
ls -la data/raw/ma_cross/equity_data/

# Test layer agreement analysis
trading-cli spds health --convergence-analysis
```

**Resolution:**

```bash
# Use conservative mode for low convergence
trading-cli spds analyze risk_on.csv --conservative-on-divergence

# Increase quality thresholds
trading-cli spds analyze risk_on.csv --min-trade-count 30

# Generate comprehensive diagnostics
trading-cli spds export risk_on.csv --convergence-analysis --debug
```

#### **Data Source Selection Issues**

**Problem**: Auto-detection not finding optimal data sources

**Diagnosis:**

```bash
# Check data source availability
trading-cli spds list-portfolios

# Verify data source paths
ls -la json/return_distribution/{asset}_returns.json
ls -la json/trade_history/{portfolio}/
ls -la data/raw/ma_cross/equity_data/

# Test auto-detection process
trading-cli spds analyze risk_on.csv --data-source auto --debug
```

**Resolution:**

```bash
# Force specific data source if auto-detection fails
trading-cli spds analyze risk_on.csv --data-source trade-history

# Adjust convergence thresholds for development
trading-cli spds analyze risk_on.csv --convergence-threshold 0.6

# Debug data source detection process
trading-cli spds analyze risk_on.csv --data-source auto --debug-sources
```

### **Export Validation**

**Problem**: SPDS CLI generates incomplete export files

**Immediate Fix**:

```bash
# 1. Verify export integrity
ls -la exports/statistical_analysis/{portfolio}.*
# Files should be >1KB with convergence data

# 2. Check for convergence analysis in exports
grep -c "convergence_score" exports/statistical_analysis/{portfolio}.json
# Should return number > 0

# 3. Validate CSV contains convergence data
head -1 exports/statistical_analysis/{portfolio}.csv | grep -c "convergence"
# Should return number > 0 if convergence analysis performed
```

### **System Health Commands**

```bash
# ALWAYS run these in order:

# 1. Verify system health
trading-cli spds health

# 2. Check available portfolios
trading-cli spds list-portfolios

# 3. Run convergence analysis with export validation
trading-cli spds analyze {portfolio} --data-source auto --output-format all

# 4. CRITICAL: Verify exports contain convergence data
ls -la exports/statistical_analysis/{portfolio}.*
grep -c "convergence_score" exports/statistical_analysis/{portfolio}.json

# 5. Trade history system validation
trading-cli trade-history health

# 6. ENHANCED: Convergence-specific validation
trading-cli spds validate-config --convergence-analysis
trading-cli spds health --convergence-analysis
```

## Best Practices

### **🎯 Enhanced Dual-Layer Analysis Workflow (v2.0)**

#### **📊 Comprehensive Analysis Process**

1. **🔍 System Health & Data Detection**

   - Run comprehensive health check
   - Check data source availability for target portfolio
   - Validate file structure for convergence analysis

2. **📊 Layer Analysis & Optimization**

   - Use auto-detection mode for optimal data source selection
   - Verify layer convergence capabilities
   - Review data quality and statistical significance

3. **🎯 Convergence Analysis Execution**

   - Execute dual-layer analysis with convergence validation
   - Monitor layer agreement and divergence warnings
   - Validate convergence-weighted confidence scoring

4. **📋 Enhanced Export & Validation**

   - **CRITICAL**: Verify all export files contain convergence analysis data
   - Validate layer-specific analysis results
   - Confirm convergence metadata completeness

5. **🎯 Layer Agreement Interpretation**

   - Review convergence scores and layer classifications
   - Analyze divergence warnings and reliability assessments
   - Validate signal confidence enhancements from convergence analysis

6. **⚡ Advanced Quality Assurance**
   - Cross-validate results across both analysis layers
   - Confirm statistical significance with enhanced confidence scoring
   - Document layer-specific insights and recommendations

### **🎯 Enhanced Convergence-Based Exit Signal Interpretation (v2.0)**

#### **📊 Convergence-Enhanced Signal Prioritization**

1. **🚨 EXIT_IMMEDIATELY with Strong Convergence** (>0.8) - **Highest Priority**

   - Both layers agree on statistical extremes
   - Enhanced confidence from layer agreement
   - Immediate action strongly recommended

2. **📉 STRONG_SELL with Layer Validation** - **High Priority**

   - Cross-validated extremity signal
   - Asset and strategy analysis alignment
   - Consider market timing for execution

3. **🔄 CONVERGENCE_EXIT Signals** - **New High-Confidence Category**

   - Layers strongly agree despite lower individual percentiles
   - Convergence validation provides enhanced reliability
   - Consider as upgraded exit signal

4. **⚠️ DIVERGENCE_HOLD Warnings** - **Exercise Caution**
   - Layers disagree significantly (<0.5 convergence)
   - Conservative approach recommended
   - Investigate layer divergence causes

#### **🔥 Convergence Assessment Guidelines**

- **Convergence Score**: >0.8 (Strong), 0.6-0.8 (Moderate), <0.6 (Weak)
- **Combined Confidence**: Enhanced with 15% boost for strong convergence
- **Layer-Specific Reliability**: Per-layer confidence validation
- **Divergence Risk Assessment**: Impact of layer disagreement on signal reliability

#### **📊 Advanced Interpretation Guidelines**

- **Strong Layer Convergence**: Increase position sizing and conviction
- **Moderate Layer Convergence**: Standard signal processing and execution
- **Weak Layer Convergence**: Reduce position sizing, seek additional confirmation
- **Significant Divergence**: Investigate data quality, consider market regime changes

### **Export and Integration**

1. **JSON format** for programmatic consumption and API integration
2. **Markdown reports** for human review and documentation
3. **Backtesting parameters** for strategy development and validation
4. **Timestamp tracking** for historical analysis and audit trails

## Integration Points

**Production-ready integrations:**

- **API Server**: RESTful endpoints for programmatic access
- **Strategy Execution**: Seamless integration with existing strategy workflows
- **Portfolio Management**: Automated aggregation and filtering capabilities
- **Trade History**: Real-time position tracking and analysis
- **Backtesting Frameworks**: Direct parameter export for VectorBT, Backtrader, Zipline

## 🎯 Enhanced System Notes (v2.0)

- **📊 System Status**: Production-ready dual-layer convergence analysis with advanced capabilities
- **🎯 v2.0 Innovation**: Asset-Strategy convergence analysis with intelligent data selection
- **⚡ Performance**: Optimized for large-scale analysis with 84.9% memory efficiency
- **🔬 Enhanced Reliability**: Bootstrap validation and convergence significance testing
- **🤖 Auto-Detection**: Intelligent data source selection and optimal utilization
- **📊 Layer Convergence**: Advanced layer agreement analysis and divergence warnings
- **🔧 100% Backward Compatibility**: All v1.0 functionality preserved while adding advanced features
- **🎛️ Advanced Configuration**: Convergence parameters for fine-tuned control
- **📈 Scalability**: Streaming processing supports unlimited dataset sizes
- **📚 Enhanced Documentation**: Convergence reports with layer insights and reliability assessment

## System Verification

**Quick Verification Commands:**

```bash
# COMPREHENSIVE system health check (RECOMMENDED)
python -m app.tools.spds_health_check

# Fix common issues automatically
python -m app.tools.spds_health_check --fix

# Verify SPDS CLI health
trading-cli spds health

# Test dual-layer convergence analysis with export validation
trading-cli spds analyze live_signals.csv --data-source auto --output-format all

# Test convergence analysis capability
trading-cli spds analyze live_signals.csv --convergence-analysis

# Legacy compatibility test
trading-cli spds analyze live_signals.csv --trade-history --output-format all

# CRITICAL: Always validate exports after analysis
ls -la exports/statistical_analysis/live_signals.*
ls -la exports/backtesting_parameters/live_signals.*

# Check available portfolios
trading-cli spds list-portfolios

# Verify trade history system
trading-cli trade-history health
```

**🎯 Enhanced Expected Results (v2.0):**

- **✅ SPDS v2.0 Health**: HEALTHY with dual-layer convergence capabilities
- **📊 Data Detection**: Auto-detection working for available portfolios
- **🎯 Convergence Analysis**: Layer agreement scoring operational
- **🔧 CRITICAL CHECK**: Export files must contain convergence analysis data
- **🎯 ENHANCED VALIDATION**: Exports must include layer agreement data and convergence scores
- **📈 Trade History**: Enhanced with convergence integration capabilities

**🔬 Enhanced Export Validation Checklist:**

```bash
# Files should exist and have substantial size
ls -la exports/statistical_analysis/live_signals.*
ls -la exports/backtesting_parameters/live_signals.*

# JSON should contain strategy results AND convergence data
grep -c "strategy_name" exports/statistical_analysis/live_signals.json
# Should return number > 0

grep -c "convergence_score" exports/statistical_analysis/live_signals.json
# Should return number > 0 for convergence analysis

grep -c "layer_agreement" exports/statistical_analysis/live_signals.json
# Should return number > 0 for dual-layer analysis

# CSV should have data rows with convergence details
wc -l exports/statistical_analysis/live_signals.csv
# Should return number > 1

# Verify convergence-specific fields exist
head -1 exports/statistical_analysis/live_signals.csv | grep -c "convergence"
# Should return number > 0 if convergence analysis was performed

# Check for convergence analysis metadata
python -c "
import json
with open('exports/statistical_analysis/live_signals.json', 'r') as f:
    data = json.load(f)
    if 'convergence_analysis' in str(data):
        print('✅ Convergence analysis detected')
    else:
        print('ℹ️  Basic analysis (normal if convergence not requested)')
"
```

**📊 Convergence Validation Commands:**

```bash
# Verify convergence analysis capability
trading-cli spds analyze live_signals.csv --convergence-analysis

# Test convergence configuration
trading-cli spds validate-config --convergence-analysis

# Verify enhanced export content
python -c "
import json
import os
if os.path.exists('exports/statistical_analysis/live_signals.json'):
    with open('exports/statistical_analysis/live_signals.json', 'r') as f:
        data = json.load(f)
        results = data.get('statistical_analysis_results', [])
        if results:
            sample = results[0]
            print(f'✅ Export contains {len(results)} strategies')
            if 'convergence_score' in sample:
                print('✅ Convergence analysis data present')
            if 'layer_agreement' in sample:
                print('✅ Layer agreement analysis present')
            if 'dual_layer_convergence_score' in sample:
                print(f'✅ Dual-layer convergence: {sample.get(\"dual_layer_convergence_score\", \"N/A\")}')
        else:
            print('❌ Export contains no strategy results')
else:
    print('❌ Export file not found')
"
```
