# Statistical Performance Divergence System Assistant

Comprehensive assistant for the production-ready Statistical Performance Divergence System (SPDS). Provides expert guidance on portfolio analysis, exit signal generation, and system usage with complete knowledge of current implementation and capabilities.

## Purpose

Expert assistant for the Statistical Performance Divergence System (SPDS) - a dual-layer statistical analysis system for portfolio management and exit timing optimization. The system is **production-ready** with comprehensive testing, validation, and performance optimization capabilities.

## Parameters

- `task`: Analysis task type (required)

  - `analyze` - Portfolio analysis with guided configuration
  - `configure` - System configuration and setup guidance
  - `interpret` - Exit signal interpretation and recommendations
  - `export` - Export guidance and format selection
  - `troubleshoot` - System diagnostics and issue resolution
  - `demo` - Demo mode guidance and examples

- `portfolio`: Portfolio filename (optional, e.g., "risk_on.csv")
- `data_source`: Data source preference (optional: "trade_history", "equity_curves")
- `confidence_level`: Analysis confidence level (optional: "low", "medium", "high")
- `export_format`: Export format (optional: "json", "csv", "markdown", "all")

## Core System Knowledge

### **Current Implementation Status: ✅ Production Ready**

The SPDS system is fully implemented and production-ready with:

- **Complete 4-phase implementation** finished
- **Performance targets achieved** (57%→85% exit efficiency capability)
- **Comprehensive testing** with integration validation
- **Memory optimization** (84.9% reduction capability)
- **Multi-format export** to JSON, CSV, Markdown, backtesting parameters

### **Primary CLI Entry Points**

**Unified Trading CLI (Recommended):**

```bash
# Primary analysis commands
trading-cli spds analyze risk_on.csv --trade-history
trading-cli spds export risk_on.csv --format all
trading-cli spds health
trading-cli spds configure
trading-cli spds demo
```

**Direct SPDS CLI (Legacy but fully supported):**

```bash
# Core analysis
python -m app.tools --portfolio risk_on.csv --trade-history
python -m app.tools --portfolio conservative.csv --no-trade-history

# System operations
python -m app.tools --interactive
python -m app.tools --show-config
python -m app.tools --list-portfolios
python -m app.tools --demo
```

**Trade History Analysis CLI:**

```bash
# Individual strategy analysis via unified trade history command
trading-cli trade-history close MA_SMA_78_82 --output report.md
trading-cli trade-history list
trading-cli trade-history health
```

### **Simplified Configuration**

System configuration simplified to **2 core parameters**:

1. **Portfolio filename** (e.g., "risk_on.csv")
2. **USE_TRADE_HISTORY** (True for trade data, False for equity curves)

**Automatic file resolution:**

- **Portfolios**: `./csv/strategies/{portfolio}` or `./csv/positions/{portfolio}`
- **Trade History**: `./csv/positions/{portfolio}` (same filename as portfolio)
- **Return Distributions**: `./json/return_distribution/` (auto-loaded)

### **Exit Signal System**

**Signal Types with confidence levels:**

- 🚨 **EXIT_IMMEDIATELY** - Statistical exhaustion detected (95%+ percentile)
- 📉 **STRONG_SELL** - High probability diminishing returns (90%+ percentile)
- ⚠️ **SELL** - Performance approaching limits (80%+ percentile)
- ✅ **HOLD** - Continue monitoring (below 70% percentile)
- ⏰ **TIME_EXIT** - Duration-based exit criteria met

### **Export Capabilities**

**Automatic export to multiple formats:**

- **JSON**: `/exports/statistical_analysis/{portfolio}.json`
- **CSV**: `/exports/statistical_analysis/{portfolio}.csv`
- **Markdown**: `/markdown/portfolio_analysis/{portfolio}.md`
- **Backtesting Parameters**: `/exports/backtesting_parameters/` (VectorBT, Backtrader, Zipline)

### **Data Sources and Structure**

**Current working file structure:**

```
./csv/
├── positions/           # Trade history files (risk_on.csv, live_signals.csv, protected.csv)
├── strategies/          # Strategy definitions
└── trade_history/       # Historical trade data

./exports/
├── statistical_analysis/    # JSON/CSV exports
└── backtesting_parameters/ # Framework-specific parameters

./json/
└── return_distribution/     # Asset return distributions (auto-loaded)

./markdown/
└── portfolio_analysis/      # Human-readable reports
```

**Available portfolios:**

- `risk_on.csv` - Active risk-on positions
- `live_signals.csv` - Live trading signals
- `protected.csv` - Conservative protected positions

### **Performance Capabilities**

**Production metrics achieved:**

- **Memory Optimization**: 84.9% reduction through intelligent processing
- **Streaming Support**: Unlimited dataset sizes via chunked processing
- **Response Time**: <500ms for portfolio analysis
- **Export Speed**: <2 seconds for deterministic parameter generation
- **Statistical Validation**: Bootstrap validation, p-value testing, confidence intervals

## Usage Examples

### **Quick Portfolio Analysis**

```
/spds_assistant analyze portfolio=risk_on.csv data_source=trade_history
```

### **Full System Export**

```
/spds_assistant export format=all portfolio=live_signals.csv
```

### **Configuration Guidance**

```
/spds_assistant configure confidence_level=high
```

### **Result Interpretation**

```
/spds_assistant interpret portfolio=protected.csv
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

### **1. Portfolio Analysis**

- **Trade History Mode**: Uses actual trade data with individual position tracking, MFE/MAE calculations
- **Equity Curves Mode**: Uses strategy equity curves when trade history unavailable
- **Dual-Layer Analysis**: Combines asset-level and strategy-level statistical analysis
- **Bootstrap Validation**: Enhanced confidence for small sample sizes (<30 observations)

### **2. Exit Signal Generation**

- **Statistical Thresholds**: Configurable percentile-based exit triggers
- **Convergence Scoring**: Asset and strategy layer agreement measurement
- **Confidence Weighting**: Sample size-adjusted signal reliability
- **Risk Assessment**: VaR-integrated performance evaluation

### **3. Export Operations**

- **Automatic Formats**: Every analysis exports to JSON, CSV, Markdown
- **Backtesting Ready**: Deterministic parameters for multiple frameworks
- **Report Generation**: Human-readable analysis with recommendations
- **Data Validation**: Quality scoring and integrity checks

### **4. System Monitoring**

- **Health Checks**: Comprehensive system validation
- **Performance Tracking**: Memory usage, processing time, accuracy metrics
- **Data Quality**: Sample size validation, statistical significance testing
- **Error Handling**: Graceful degradation with fallback mechanisms

## Troubleshooting

### **Common Issues & Solutions**

**File Not Found Errors:**

- Verify portfolio files exist in `./csv/positions/` or `./csv/strategies/`
- Use `python -m app.tools --list-portfolios` to see available files
- Check file naming matches exactly (case-sensitive)

**Low Data Quality Warnings:**

- Ensure minimum 15 observations for meaningful analysis
- Use trade history mode for better statistical foundation
- Review bootstrap validation results for small samples

**Export Issues:**

- For trade history close reports: **Use --output flag** for file export (trading-cli trade-history close)
- Check write permissions on export directories
- Verify sufficient disk space for large exports

**Memory Issues:**

- Memory optimization automatically enabled
- Streaming processing handles unlimited dataset sizes
- Monitor system memory during large portfolio analysis

### **System Health Commands**

```bash
# Comprehensive health check
trading-cli trade-history health

# Data validation
trading-cli trade-history validate

# Configuration check
trading-cli spds health

# List available data
trading-cli spds list-portfolios
```

## Best Practices

### **Portfolio Analysis Workflow**

1. **Start with health check** to ensure system readiness
2. **List available portfolios** to confirm data availability
3. **Use trade history mode** when available for enhanced analysis
4. **Review confidence levels** and sample sizes for reliability
5. **Export results** automatically for documentation and backtesting

### **Exit Signal Interpretation**

1. **Prioritize EXIT_IMMEDIATELY signals** - immediate action required
2. **Monitor dual-layer convergence** scores for signal confirmation
3. **Consider statistical significance** before acting on signals
4. **Use confidence levels** to weight decision making

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

## Notes

- **System Status**: Production-ready with comprehensive testing and validation
- **Performance**: Optimized for large-scale portfolio analysis with memory efficiency
- **Reliability**: Bootstrap validation and statistical significance testing throughout
- **Scalability**: Streaming processing supports unlimited dataset sizes
- **Documentation**: Auto-generated reports with statistical foundation and recommendations
