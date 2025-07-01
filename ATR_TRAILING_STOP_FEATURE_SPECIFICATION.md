# ATR Trailing Stop Exit Parameter Sensitivity Analysis Feature Specification

## 1. Feature Overview

### 1.1 Purpose

Implement ATR (Average True Range) Trailing Stop exit parameter sensitivity analysis for the MA Cross strategy suite, enabling optimization of exit signals while using fixed, proven MA Cross entry configurations.

### 1.2 Scope

- **Entry Strategy**: Fixed MA Cross configuration (SMA 51/69 from config)
- **Exit Strategy**: ATR Trailing Stop with parameter sensitivity analysis
- **Analysis Type**: Parameter sweep across ATR Length and Multiplier combinations
- **Integration**: Seamless integration with existing MA Cross strategy framework

### 1.3 Business Value

- Optimize exit timing for existing profitable MA Cross strategies
- Provide comprehensive parameter sensitivity analysis for ATR-based exits
- Maintain proven entry signals while improving exit performance
- Enable data-driven ATR parameter selection

## 2. Technical Requirements

### 2.1 Parameter Configuration

**Fixed MA Entry Parameters** (from `3_get_atr_stop_portfolios.py` config):

```python
FIXED_MA_CONFIG = {
    "TICKER": "AMZN",
    "SHORT_WINDOW": 51,
    "LONG_WINDOW": 69,
    "USE_SMA": True,
    "DIRECTION": "Long",
    "USE_HOURLY": False
}
```

**Variable ATR Exit Parameters**:

```python
ATR_PARAMETER_RANGES = {
    "ATR_STOP_LENGTH": list(range(2, 22)),           # 2 to 21 (20 values)
    "ATR_STOP_MULTIPLIER": [round(1.5 + i * 0.2, 1) for i in range(43)]  # 1.5 to 10.0 in 0.2 steps (43 values)
}
# Total combinations: 860 (20 × 43)
```

### 2.2 Schema Extensions

**New CSV Schema Fields** (added to Extended Portfolio Schema):

```python
SCHEMA_EXTENSIONS = [
    ColumnDefinition(
        "ATR Stop Length",
        ColumnDataType.INTEGER,
        nullable=True,
        description="ATR period length for trailing stop calculation"
    ),
    ColumnDefinition(
        "ATR Stop Multiplier",
        ColumnDataType.FLOAT,
        nullable=True,
        description="ATR multiplier for trailing stop distance"
    )
]
```

### 2.3 File Organization

**File Naming Convention**:

```
{TICKER}_D_{STRATEGY_TYPE}_{SHORT_WINDOW}_{LONG_WINDOW}_ATR.csv
```

**Examples**:

```
AMZN_D_SMA_51_69_ATR.csv
META_D_SMA_51_69_ATR.csv
```

**Directory Structure**:

```
/csv/portfolios/               # Raw parameter sweep results
  └── AMZN_D_SMA_51_69_ATR.csv

/csv/portfolios_filtered/      # Filtered by performance criteria
  └── AMZN_D_SMA_51_69_ATR.csv

/csv/portfolios_best/          # Top performing combinations
  └── AMZN_D_SMA_51_69_ATR.csv
```

## 3. Implementation Design

### 3.1 Core Architecture

**Primary Implementation File**: `app/strategies/ma_cross/3_get_atr_stop_portfolios.py`

**Supporting Modules**:

- `app/strategies/ma_cross/tools/atr_signal_processing.py` - Hybrid signal generation
- `app/strategies/ma_cross/tools/atr_parameter_analysis.py` - Parameter sensitivity analysis

### 3.2 Signal Generation Logic

**Hybrid Signal Strategy**:

```python
def generate_hybrid_ma_atr_signals(data, ma_config, atr_length, atr_multiplier, log):
    """
    Generate hybrid signals combining MA Cross entries with ATR Trailing Stop exits.

    Signal Logic:
    1. Entry: MA Cross (short MA crosses above long MA for long positions)
    2. Exit: ATR Trailing Stop OR opposite MA Cross (whichever occurs first)
    3. Position Management: Enter on MA cross, exit on ATR stop breach
    """
    # 1. Generate MA cross signals for entries
    data = calculate_ma_and_signals(
        data, ma_config["SHORT_WINDOW"], ma_config["LONG_WINDOW"],
        ma_config, log, "SMA" if ma_config["USE_SMA"] else "EMA"
    )

    # 2. Calculate ATR and apply trailing stop logic
    data["ATR"] = calculate_atr(data, atr_length)
    data = apply_atr_trailing_stop_exits(data, atr_length, atr_multiplier, log)

    # 3. Combine entry and exit signals
    data = combine_ma_entry_atr_exit_signals(data, ma_config, log)

    return data
```

### 3.3 Code Reuse Strategy

**Reusable Components from `app/atr/atr.py`**:

```python
# Direct imports for reuse
from app.atr.atr import (
    calculate_atr,                    # ATR calculation
    calculate_atr_trailing_stop,      # Trailing stop logic
    generate_signals as atr_generate_signals  # Reference implementation
)
```

**Abstracted Functions**:

```python
def create_atr_ma_analyzer(ma_config):
    """Factory function to create ATR analyzer with fixed MA config."""
    return ATRMAAnalyzer(
        short_window=ma_config["SHORT_WINDOW"],
        long_window=ma_config["LONG_WINDOW"],
        strategy_type="SMA" if ma_config["USE_SMA"] else "EMA"
    )
```

### 3.4 Parameter Sweep Implementation

**Main Analysis Function**:

```python
def execute_atr_parameter_sensitivity(config, log):
    """
    Execute comprehensive ATR parameter sensitivity analysis.

    Process:
    1. Load price data for ticker
    2. Generate 860 parameter combinations
    3. Test each ATR parameter combination with fixed MA entry
    4. Calculate portfolio metrics for each combination
    5. Export results with proper schema compliance
    """

    # Fixed MA configuration
    ma_config = extract_ma_config(config)

    # Get price data
    data = get_data(config["TICKER"], config, log)

    # Parameter combinations
    atr_lengths = ATR_PARAMETER_RANGES["ATR_STOP_LENGTH"]
    atr_multipliers = ATR_PARAMETER_RANGES["ATR_STOP_MULTIPLIER"]

    portfolios = []

    # Single loop over ATR parameters (no nested MA loops)
    for atr_length in atr_lengths:
        for atr_multiplier in atr_multipliers:

            # Generate hybrid signals
            test_data = generate_hybrid_ma_atr_signals(
                data.copy(), ma_config, atr_length, atr_multiplier, log
            )

            # Backtest strategy
            portfolio = backtest_strategy(test_data, config, log)

            if portfolio:
                # Convert to portfolio metrics
                stats = convert_stats(portfolio.stats(), log, config)

                # Add parameter identification
                stats.update({
                    "TICKER": config["TICKER"],
                    "Strategy Type": "SMA" if ma_config["USE_SMA"] else "EMA",
                    "Short Window": ma_config["SHORT_WINDOW"],
                    "Long Window": ma_config["LONG_WINDOW"],
                    "ATR Stop Length": atr_length,
                    "ATR Stop Multiplier": atr_multiplier
                })

                portfolios.append(stats)

    return portfolios
```

## 4. Integration Points

### 4.1 Strategy Execution Integration

**Extend `app/strategies/ma_cross/tools/strategy_execution.py`**:

```python
def execute_atr_strategy(ticker, config, log):
    """Execute ATR sensitivity analysis strategy."""
    return execute_atr_parameter_sensitivity(config, log)
```

### 4.2 Export Integration

**Filename Generation**:

```python
def generate_atr_filename(config):
    """Generate filename for ATR analysis results."""
    ticker = config["TICKER"]
    timeframe = "H" if config.get("USE_HOURLY") else "D"
    strategy = "SMA" if config.get("USE_SMA") else "EMA"
    short_window = config["SHORT_WINDOW"]
    long_window = config["LONG_WINDOW"]

    return f"{ticker}_{timeframe}_{strategy}_{short_window}_{long_window}_ATR.csv"
```

### 4.3 Portfolio Processing Integration

**Filter Integration**:

```python
# ATR portfolios use same filtering criteria as standard MA Cross
FILTERING_CRITERIA = {
    "WIN_RATE": 0.5,
    "TRADES": 44,
    "EXPECTANCY_PER_TRADE": 0.5,
    "PROFIT_FACTOR": 1.236,
    "SORTINO_RATIO": 0.5
}
```

## 5. Performance Metrics

### 5.1 Enhanced Metrics

**Standard Portfolio Metrics** (58 base columns) plus:

- ATR Stop Length
- ATR Stop Multiplier
- Entry Signal Accuracy (from MA Cross)
- Exit Signal Effectiveness (from ATR Trailing Stop)
- Combined Strategy Performance

### 5.2 Analysis Outputs

**Parameter Sensitivity Heatmaps**:

- ATR Length vs ATR Multiplier performance matrices
- Optimal parameter identification
- Performance degradation analysis

**Comparative Analysis**:

- Pure MA Cross vs MA Cross + ATR Trailing Stop
- Parameter stability analysis
- Risk-adjusted return improvements

## 6. Configuration Management

### 6.1 Config Structure

**Complete Configuration Example**:

```python
ATR_ANALYSIS_CONFIG = {
    # Fixed MA Entry Configuration
    "TICKER": "AMZN",
    "SHORT_WINDOW": 51,
    "LONG_WINDOW": 69,
    "USE_SMA": True,

    # Standard Configuration
    "BASE_DIR": ".",
    "REFRESH": True,
    "USE_HOURLY": False,
    "DIRECTION": "Long",

    # Filtering Criteria
    "MINIMUMS": {
        "WIN_RATE": 0.5,
        "TRADES": 44,
        "EXPECTANCY_PER_TRADE": 0.5,
        "PROFIT_FACTOR": 1.236,
        "SORTINO_RATIO": 0.5
    }
}
```

### 6.2 Runtime Configuration

**Parameter Range Overrides**:

```python
# Allow runtime parameter range customization
if "ATR_LENGTH_RANGE" in config:
    atr_lengths = config["ATR_LENGTH_RANGE"]
if "ATR_MULTIPLIER_RANGE" in config:
    atr_multipliers = config["ATR_MULTIPLIER_RANGE"]
```

## 7. Testing and Validation

### 7.1 Unit Tests

**Test Coverage**:

- ATR calculation accuracy
- Hybrid signal generation logic
- Parameter combination generation
- Schema compliance validation
- File naming convention adherence

### 7.2 Integration Tests

**End-to-End Validation**:

- Complete parameter sweep execution
- CSV export validation
- Portfolio filtering integration
- Performance metric calculation

### 7.3 Performance Tests

**Scalability Validation**:

- 860 parameter combination processing time
- Memory usage with large datasets
- Export performance optimization

## 8. Success Criteria

### 8.1 Functional Requirements

✅ **Parameter Analysis**:

- 860 ATR parameter combinations tested per ticker
- Fixed MA configuration (SMA 51/69) for entries
- ATR Trailing Stop for exits

✅ **Export Compliance**:

- CSV files exported to portfolios/, portfolios_filtered/, portfolios_best/
- Filename pattern: `{TICKER}_D_SMA_51_69_ATR.csv`
- Schema includes "ATR Stop Length" and "ATR Stop Multiplier" fields

✅ **Integration Compliance**:

- Uses existing MA Cross configuration system
- Maintains compatibility with portfolio processing pipeline
- Leverages established filtering and export utilities

### 8.2 Performance Requirements

✅ **Efficiency**:

- Under 1000 total parameter combinations
- Memory-efficient processing using existing optimization frameworks
- Reasonable execution time for parameter sweep

### 8.3 Quality Requirements

✅ **Code Quality**:

- DRY principle: Reuse existing ATR implementation
- SOLID principles: Clean separation of concerns
- KISS principle: Simple, focused implementation
- YAGNI principle: No unnecessary features

## 9. Implementation Timeline

### Phase 1: Core Implementation (Priority: High)

1. Implement `3_get_atr_stop_portfolios.py` main function
2. Create ATR signal processing module
3. Extend schema with ATR fields

### Phase 2: Integration (Priority: High)

1. Integrate with existing strategy execution pipeline
2. Implement filename generation and export logic
3. Add configuration validation

### Phase 3: Analysis Tools (Priority: Medium)

1. Create parameter sensitivity analysis tools
2. Implement performance comparison utilities
3. Add heatmap generation capabilities

This specification provides a complete roadmap for implementing ATR Trailing Stop exit parameter sensitivity analysis while maintaining full compatibility with the existing MA Cross strategy framework.
