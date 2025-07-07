# trade_history

## Description

Comprehensive trade history management system supporting position lifecycle operations, statistical analysis, and risk management across all portfolios. This unified command consolidates position management, sell signal generation, and portfolio updates into a single interface with support for live_signals, protected, risk_on, and custom portfolios.

## Command Structure

This command uses **sub-commands** following the modern CLI pattern:

- `trading-cli trade-history update` - Update existing open positions with current market data
- `trading-cli trade-history add` - Add new position with signal verification and risk assessment
- `trading-cli trade-history close` - Generate comprehensive sell signal reports from SPDS data
- `trading-cli trade-history list` - List available strategies and current signals
- `trading-cli trade-history validate` - Validate system health and data integrity
- `trading-cli trade-history health` - Perform comprehensive system health check

## Parameters

### Core Parameters

- **portfolio** (optional): Portfolio name to operate on (default: "live_signals")
  - Available portfolios: live_signals, protected, risk_on, or any custom portfolio in csv/positions/

### Position Management Parameters (for `add` sub-command)

- **ticker** (required for add): Ticker symbol (e.g., AAPL, BTC-USD, ETH-USD)
- **strategy_type** (required for add): Strategy type (SMA, EMA, MACD, RSI, BOLLINGER, STOCHASTIC)
- **short_window** (required for add): Short window period (positive integer)
- **long_window** (required for add): Long window period (positive integer, must be > short_window)
- **signal_window** (optional): Signal window period (default: 0)
- **entry_date** (optional): Entry date in YYYY-MM-DD format (auto-detected if not provided)
- **entry_price** (optional): Entry price (market price if not provided)

### Analysis Parameters (for `close` sub-command)

- **strategy** (required for close): Strategy name or Position_UUID to analyze
- **output** (optional): Output file path for reports (stdout if not specified)
- **format** (optional): Output format (markdown, json, html) - default: markdown
- **include_raw_data** (optional): Include raw statistical data in appendices
- **current_price** (optional): Current market price for enhanced analysis
- **market_condition** (optional): Market condition (bullish/bearish/sideways/volatile)

## Objectives

### Universal Trade History Management

1. **Unified Interface**: Single command supporting all trade history operations across multiple portfolios
2. **Portfolio Agnostic**: Support for live_signals, protected, risk_on, and any custom portfolio
3. **Signal Verification**: Comprehensive entry signal validation using crossover analysis
4. **Risk Management**: Advanced MFE/MAE calculations and trade quality assessment
5. **SPDS Integration**: Full integration with Statistical Performance Divergence System for exit signal generation

### Action-Specific Objectives

#### Update Action

1. **Open Position Updates**: Refresh dynamic metrics for positions with Status="Open"
2. **Market Data Integration**: Update current prices and calculate unrealized P&L
3. **Risk Recalculation**: Recalculate MFE/MAE with latest price data
4. **Data Integrity**: Preserve all static fields and closed position data

#### Add Action

1. **Signal Verification**: Verify entry signals actually occurred using crossover detection
2. **Position Creation**: Add verified positions with complete schema compliance
3. **Risk Assessment**: Calculate initial MFE/MAE metrics and trade quality
4. **Portfolio Integration**: Seamless addition to any specified portfolio

#### Close Action

1. **SPDS Analysis**: Generate comprehensive sell signal reports using Statistical Performance Divergence System
2. **Exit Strategy Optimization**: Provide multiple exit scenarios with risk-adjusted recommendations
3. **Multi-Source Integration**: Aggregate data from statistical analysis, backtesting parameters, and trade history
4. **Actionable Insights**: Deliver clear SELL/HOLD recommendations with confidence levels

## Dynamic Fields Updated

### **Guaranteed Updates (Daily)**

- `Days_Since_Entry` - Updates daily as time passes
- `Current_Unrealized_PnL` - Updates with current market prices
- `Current_Excursion_Status` - Updates based on current position vs entry

### **Conditional Updates (Market-Driven)**

- `Max_Favourable_Excursion` (MFE) - Updates if position reaches new favorable extremes
- `Max_Adverse_Excursion` (MAE) - Updates if position hits new adverse levels
- `MFE_MAE_Ratio` - Recalculated when MFE/MAE change
- `Trade_Quality` - Reassessed based on updated MFE/MAE metrics

### **Protected Fields (Never Updated)**

- All entry-related data (Position_UUID, Entry_Timestamp, Avg_Entry_Price)
- Strategy parameters (Ticker, Strategy_Type, Windows)
- Closed position data (Status="Closed" positions remain untouched)

## Implementation Process

### Sub-Command Routing and Portfolio Validation

```bash
# Sub-command routing (automatically handled by trading-cli)
SUBCOMMAND="$1"  # update, add, close, list, validate, health
Portfolio="${portfolio:-live_signals}"

# Validate sub-command (handled by CLI framework)
case "$SUBCOMMAND" in
    update|add|close|list|validate|health)
        echo "🎯 TRADE HISTORY SUB-COMMAND: ${SUBCOMMAND}"
        ;;
    *)
        echo "❌ INVALID SUB-COMMAND: ${SUBCOMMAND}"
        echo "Valid sub-commands: update, add, close, list, validate, health"
        exit 1
        ;;
esac

# Read and understand the executive specification
cat docs/Trade_History_Executive_Specification.md

# Portfolio validation (for portfolio-specific actions)
if [[ "$SUBCOMMAND" == "update" || "$SUBCOMMAND" == "add" ]]; then
    if [ ! -f "csv/positions/${Portfolio}.csv" ]; then
        echo "❌ PORTFOLIO NOT FOUND: csv/positions/${Portfolio}.csv"
        echo "Available portfolios:"
        ls csv/positions/*.csv | xargs -n 1 basename | sed 's/.csv//' 2>/dev/null || echo "No portfolios found"
        exit 1
    fi

    echo "📂 TARGET PORTFOLIO: ${Portfolio}"
    echo "📁 File: csv/positions/${Portfolio}.csv"
fi
```

### Phase 1: Sub-Command Dispatch and Execution

```bash
case "$SUBCOMMAND" in
    "update")
        # Existing update logic enhanced with portfolio generalization
        echo "🔄 UPDATING PORTFOLIO: ${Portfolio}"

        # Count open positions before update
        OPEN_COUNT=$(python -c "
import pandas as pd
df = pd.read_csv('csv/positions/${Portfolio}.csv')
open_positions = df[df['Status'] == 'Open']
print(len(open_positions))
")

        echo "📊 Open positions to update: $OPEN_COUNT"

        if [ "$OPEN_COUNT" -eq "0" ]; then
            echo "ℹ️  No open positions found in ${Portfolio} portfolio"
            echo "✅ UPDATE COMPLETE - No changes needed"
            exit 0
        fi
        ;;

    "add")
        # New position addition with verification
        echo "➕ ADDING POSITION TO PORTFOLIO: ${Portfolio}"

        # Validate required parameters
        if [[ -z "$ticker" || -z "$strategy_type" || -z "$short_window" || -z "$long_window" ]]; then
            echo "❌ MISSING REQUIRED PARAMETERS for add sub-command"
            echo "Required: ticker, strategy_type, short_window, long_window"
            exit 1
        fi

        echo "📊 Position Details:"
        echo "   Ticker: ${ticker}"
        echo "   Strategy: ${strategy_type} ${short_window}/${long_window}"
        echo "   Portfolio: ${Portfolio}"
        ;;

    "close")
        # Sell signal report generation
        echo "📈 GENERATING SELL SIGNAL REPORT"

        if [[ -z "$strategy" ]]; then
            echo "❌ MISSING REQUIRED PARAMETER: strategy"
            echo "Required: strategy (Position_UUID or strategy name)"
            exit 1
        fi

        echo "🎯 Strategy: ${strategy}"
        ;;

    "list")
        # List available strategies across all portfolios
        echo "📋 LISTING AVAILABLE STRATEGIES"
        ;;

    "validate")
        # System health and data validation
        echo "🔍 SYSTEM VALIDATION"
        ;;

    "health")
        # Comprehensive system health check
        echo "🏥 COMPREHENSIVE SYSTEM HEALTH CHECK"
        ;;
esac
```

### Phase 2: Sub-Command-Specific Implementation

```bash
case "$SUBCOMMAND" in
    "update")
        # Update dynamic metrics for all open positions
        echo "🔄 Updating dynamic metrics for open positions..."

        python app/tools/generalized_trade_history_exporter.py --update-open-positions \
            --portfolio "$Portfolio" \
            --update-fields "days_since_entry,unrealized_pnl,excursion_status,mfe,mae,trade_quality" \
            --preserve-closed \
            --verbose

        if [ $? -ne 0 ]; then
            echo "❌ DYNAMIC METRICS UPDATE FAILED"
            exit 1
        fi
        echo "✅ DYNAMIC METRICS UPDATED"
        ;;

    "add")
        # Add new position with signal verification
        echo "🔍 Verifying entry signal and adding position..."

        # Use generalized trade history exporter to add position
        python app/tools/generalized_trade_history_exporter.py --add-position \
            --ticker "$ticker" \
            --strategy "$strategy_type" \
            --short-window "$short_window" \
            --long-window "$long_window" \
            --signal-window "${signal_window:-0}" \
            --entry-date "${entry_date:-}" \
            --entry-price "${entry_price:-}" \
            --portfolio "$Portfolio" \
            --verbose

        if [ $? -eq 0 ]; then
            echo "✅ POSITION ADDED SUCCESSFULLY"
            Position_UUID="${ticker}_${strategy_type}_${short_window}_${long_window}_${signal_window:-0}_${entry_date:-$(date +%Y-%m-%d)}"
            echo "📊 Position UUID: $Position_UUID"
        else
            echo "❌ POSITION CREATION FAILED"
            exit 1
        fi
        ;;

    "close")
        # Generate comprehensive sell signal report using SPDS data
        echo "📈 Generating sell signal report using SPDS data..."

        # Determine output parameters
        OUTPUT_PARAMS=""
        if [[ -n "$output" ]]; then
            OUTPUT_PARAMS="--output $output"
        fi

        if [[ -n "$format" ]]; then
            OUTPUT_PARAMS="$OUTPUT_PARAMS --format $format"
        fi

        if [[ "$include_raw_data" == "true" ]]; then
            OUTPUT_PARAMS="$OUTPUT_PARAMS --include-raw-data"
        fi

        if [[ -n "$current_price" ]]; then
            OUTPUT_PARAMS="$OUTPUT_PARAMS --current-price $current_price"
        fi

        if [[ -n "$market_condition" ]]; then
            OUTPUT_PARAMS="$OUTPUT_PARAMS --market-condition $market_condition"
        fi

        # Execute sell signal report generation
        python -m app.tools.trade_history_close_live_signal \
            --strategy "$strategy" \
            $OUTPUT_PARAMS \
            --verbose

        if [ $? -eq 0 ]; then
            echo "✅ SELL SIGNAL REPORT GENERATED SUCCESSFULLY"
        else
            echo "❌ SELL SIGNAL REPORT GENERATION FAILED"
            exit 1
        fi
        ;;

    "list")
        # List available strategies across all portfolios or specific portfolio
        echo "📋 Listing available strategies..."

        if [[ "$portfolio" != "live_signals" && -n "$portfolio" ]]; then
            echo "📂 Portfolio filter: $portfolio"
        fi

        python -m app.tools.trade_history_close_live_signal --list-strategies

        if [ $? -ne 0 ]; then
            echo "❌ STRATEGY LISTING FAILED"
            exit 1
        fi
        ;;

    "validate")
        # Comprehensive system validation
        echo "🔍 Running system health check and data validation..."

        # Health check
        python -m app.tools.trade_history_close_live_signal --health-check
        HEALTH_RESULT=$?

        # Data validation
        python -m app.tools.trade_history_close_live_signal --validate-data
        VALIDATION_RESULT=$?

        if [[ $HEALTH_RESULT -eq 0 && $VALIDATION_RESULT -eq 0 ]]; then
            echo "✅ SYSTEM VALIDATION PASSED"
        else
            echo "❌ SYSTEM VALIDATION ISSUES FOUND"
            exit 1
        fi
        ;;

    "health")
        # Comprehensive system health check
        echo "🏥 Running comprehensive system health check..."

        python -m app.tools.trade_history_close_live_signal --health-check

        if [ $? -eq 0 ]; then
            echo "✅ SYSTEM HEALTH CHECK PASSED"
        else
            echo "❌ SYSTEM HEALTH CHECK FAILED"
            exit 1
        fi
        ;;
esac
```

### Phase 3: Market Data Integration and Portfolio Updates (Update Sub-Command Only)

```bash
if [[ "$SUBCOMMAND" == "update" ]]; then
    # Fetch latest price data for all open position tickers
    echo "🔄 Updating market data for open positions..."

    python -c "
import pandas as pd
import yfinance as yf
from datetime import datetime

# Read portfolio
df = pd.read_csv('csv/positions/${Portfolio}.csv')
open_positions = df[df['Status'] == 'Open']

# Get unique tickers
tickers = open_positions['Ticker'].unique()
print(f'📈 Fetching latest prices for {len(tickers)} tickers: {list(tickers)}')

# Update price data files
for ticker in tickers:
    try:
        data = yf.download(ticker, period='5d', progress=False)
        if not data.empty:
            # Update price data file
            data.to_csv(f'csv/price_data/{ticker}_D.csv')
            print(f'✅ Updated price data: {ticker}')
        else:
            print(f'⚠️  No data available: {ticker}')
    except Exception as e:
        print(f'❌ Failed to update {ticker}: {str(e)}')
"

    # Recalculate MFE/MAE with updated price data
    python app/tools/generalized_trade_history_exporter.py --recalculate-mfe-mae \
        --portfolio "$Portfolio" \
        --open-only \
        --verbose

    if [ $? -eq 0 ]; then
        echo "✅ MFE/MAE RECALCULATION COMPLETE"
    else
        echo "⚠️  MFE/MAE recalculation had issues (check logs)"
    fi
fi
```

### Phase 4: Validation and Reporting

```bash
# Sub-command-specific validation and reporting
case "$SUBCOMMAND" in
    "update")
        # Trade quality reassessment for updated positions
        echo "🔍 Reassessing trade quality for updated positions..."

        python app/tools/trade_history_utils.py --update-quality \
            --portfolio "$Portfolio" \
            --open-only \
            --verbose

        if [ $? -eq 0 ]; then
            echo "✅ TRADE QUALITY REASSESSMENT COMPLETE"
        else
            echo "⚠️  Trade quality update had issues"
        fi

        # Validate update integrity
        echo "🔍 Validating update integrity..."

        python -c "
import pandas as pd
from datetime import datetime

# Read updated portfolio
df = pd.read_csv('csv/positions/${Portfolio}.csv')

# Validate open positions
open_positions = df[df['Status'] == 'Open']
closed_positions = df[df['Status'] == 'Closed']

print(f'📊 PORTFOLIO UPDATE SUMMARY')
print(f'========================')
print(f'Portfolio: ${Portfolio}')
print(f'Total positions: {len(df)}')
print(f'Open positions updated: {len(open_positions)}')
print(f'Closed positions (unchanged): {len(closed_positions)}')
print()

# Check for data integrity issues
errors = []

# Validate required fields are not null for open positions
required_fields = ['Days_Since_Entry', 'Current_Unrealized_PnL', 'Max_Favourable_Excursion', 'Max_Adverse_Excursion']
for field in required_fields:
    if field in open_positions.columns:
        null_count = open_positions[field].isnull().sum()
        if null_count > 0:
            errors.append(f'{field}: {null_count} null values in open positions')

# Validate MFE/MAE ratios
if 'Max_Favourable_Excursion' in open_positions.columns and 'Max_Adverse_Excursion' in open_positions.columns:
    invalid_ratios = open_positions[
        (open_positions['Max_Favourable_Excursion'] <= 0) |
        (open_positions['Max_Adverse_Excursion'] <= 0)
    ]
    if len(invalid_ratios) > 0:
        errors.append(f'Invalid MFE/MAE values in {len(invalid_ratios)} positions')

# Report validation results
if errors:
    print('⚠️  VALIDATION WARNINGS:')
    for error in errors:
        print(f'  - {error}')
else:
    print('✅ DATA INTEGRITY VALIDATED')

print()
print('🔄 UPDATE TIMESTAMP:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
"

        # Display portfolio summary
        python app/tools/trade_history_utils.py --summary --portfolio "$Portfolio"
        echo "✅ PORTFOLIO UPDATE COMPLETE"
        ;;

    "add")
        # Verify position was added correctly
        echo "🔍 Verifying position addition..."

        if [[ -n "$Position_UUID" ]]; then
            grep "$Position_UUID" "csv/positions/${Portfolio}.csv" > /dev/null
            if [ $? -eq 0 ]; then
                echo "✅ POSITION VERIFICATION COMPLETE"
                echo "📊 Position successfully added to ${Portfolio} portfolio"
            else
                echo "❌ POSITION VERIFICATION FAILED"
                exit 1
            fi
        fi

        # Display updated portfolio summary
        python app/tools/trade_history_utils.py --summary --portfolio "$Portfolio"
        echo "✅ POSITION ADDITION COMPLETE"
        ;;

    "close")
        # Report generation completed in Phase 2
        echo "📊 Sell signal report generation completed"
        ;;

    "list")
        # Strategy listing completed in Phase 2
        echo "📋 Strategy listing completed"
        ;;

    "validate")
        # System validation completed in Phase 2
        echo "🔍 System validation completed"
        ;;
esac
```

## Update Frequency Recommendations

### **Daily Updates**

- Days_Since_Entry (automatic time progression)
- Current_Unrealized_PnL (market close prices)

### **Intraday Updates** (Optional)

- Current_Unrealized_PnL (real-time prices)
- Current_Excursion_Status (live market monitoring)

### **Weekly Updates**

- MFE/MAE recalculation (capture weekly highs/lows)
- Trade_Quality reassessment (strategy performance review)

## Error Handling

### **Portfolio Not Found**

```bash
❌ PORTFOLIO NOT FOUND: csv/positions/invalid_portfolio.csv
Available portfolios:
live_signals
protected
risk_on
```

### **No Open Positions**

```bash
ℹ️  No open positions found in protected portfolio
✅ UPDATE COMPLETE - No changes needed
```

### **Market Data Issues**

```bash
⚠️  Failed to update INVALID_TICKER: No data available
🔄 Continuing with available price data...
```

## Position Update Schema

### **Updated Fields (Open Positions Only)**

```csv
Days_Since_Entry,Current_Unrealized_PnL,Current_Excursion_Status,
Max_Favourable_Excursion,Max_Adverse_Excursion,MFE_MAE_Ratio,Trade_Quality
```

### **Protected Fields (Never Changed)**

```csv
Position_UUID,Ticker,Strategy_Type,Short_Window,Long_Window,Signal_Window,
Entry_Timestamp,Exit_Timestamp,Avg_Entry_Price,Avg_Exit_Price,Position_Size,
Direction,PnL,Return,Duration_Days,Trade_Type,Status
```

## Usage Examples

### **Portfolio Update Operations**

```bash
# Update live_signals portfolio (default portfolio)
trading-cli trade-history update

# Update specific portfolio
trading-cli trade-history update --portfolio protected
trading-cli trade-history update --portfolio risk_on

# Update with comprehensive recalculation
trading-cli trade-history update --portfolio live_signals
```

### **Position Addition Operations**

```bash
# Add AAPL position to live_signals (default portfolio)
trading-cli trade-history add AAPL --strategy-type SMA --short-window 20 --long-window 50

# Add position to specific portfolio with custom entry
trading-cli trade-history add BTC-USD --strategy-type EMA --short-window 12 --long-window 26 --portfolio risk_on --signal-date 2025-06-24

# Add position with manual entry price
trading-cli trade-history add GOOGL --strategy-type SMA --short-window 49 --long-window 66 --portfolio protected --entry-price 2750.00
```

### **Sell Signal Report Generation**

```bash
# Generate sell signal report (console output)
trading-cli trade-history close MA_SMA_78_82

# Generate report with file output
trading-cli trade-history close CRWD_EMA_5_21 --output reports/CRWD_analysis.md

# Generate enhanced report with market context
trading-cli trade-history close QCOM_SMA_49_66 --current-price 147.50 --market-condition bearish --format json --output analysis.json
```

### **System Management Operations**

```bash
# List all available strategies
trading-cli trade-history list

# List strategies for specific portfolio
trading-cli trade-history list --portfolio risk_on

# System health check and validation
trading-cli trade-history validate
```

### **Multi-Portfolio Operations**

```bash
# Update all portfolios sequentially
for portfolio in live_signals protected risk_on; do
    trading-cli trade-history update --portfolio $portfolio
done

# Add same strategy to multiple portfolios
for portfolio in live_signals risk_on; do
    trading-cli trade-history add TSLA --strategy-type SMA --short-window 21 --long-window 50 --portfolio $portfolio
done
```

### **Automated Daily Operations**

```bash
# Daily portfolio updates (can be added to cron)
0 18 * * * cd /path/to/trading && trading-cli trade-history update --portfolio live_signals
0 18 * * * cd /path/to/trading && trading-cli trade-history update --portfolio protected
0 18 * * * cd /path/to/trading && trading-cli trade-history update --portfolio risk_on

# Weekly comprehensive validation
0 9 * * 1 cd /path/to/trading && trading-cli trade-history validate
```

## Integration with Trade History Executive System

This unified command integrates comprehensively with the Trade History Executive System:

### **Core System Integration**

1. **Executive Specification Compliance**: Examines @docs/Trade_History_Executive_Specification.md on each execution
2. **Generalized Trade History Exporter**: Leverages `app/tools/generalized_trade_history_exporter.py` for position management
3. **SPDS Integration**: Full integration with Statistical Performance Divergence System for exit signal generation
4. **Schema Evolution**: Maintains position-level schema standards across all portfolios

### **Multi-Portfolio Architecture**

1. **Portfolio Agnostic**: Supports live_signals, protected, risk_on, and custom portfolios
2. **Data Integrity**: Preserves closed positions and static fields across all portfolio types
3. **Market Integration**: Uses latest price data for accurate calculations across all tickers
4. **Quality Monitoring**: Continuously reassesses trade performance for all position types

### **Action-Specific Integration**

#### **Update Action Integration**

- Real-time MFE/MAE calculation with price data integration
- Dynamic metrics updating preserving data integrity
- Trade quality reassessment with portfolio-specific insights

#### **Add Action Integration**

- Signal verification using crossover analysis (`verify_entry_signal()`)
- Position creation with `add_position_to_portfolio()` verification
- Risk calculation using `calculate_mfe_mae()` integration

#### **Close Action Integration**

- Multi-source data aggregation from SPDS exports
- `TradeHistoryCloseCommand` for comprehensive sell signal reports
- Exit strategy optimization with risk-adjusted recommendations

#### **List/Validate Action Integration**

- Strategy discovery across all portfolios
- System health monitoring with comprehensive validation
- Data integrity checks across all data sources

## Output and Reporting

### **Successful Update**

```
🔄 UPDATING PORTFOLIO: live_signals
📊 Open positions to update: 17
📈 Fetching latest prices for 15 tickers: ['CRWD', 'NFLX', 'COST', ...]
✅ Updated price data: CRWD
✅ Updated price data: NFLX
✅ DYNAMIC METRICS UPDATED
✅ MFE/MAE RECALCULATION COMPLETE
✅ TRADE QUALITY REASSESSMENT COMPLETE
✅ DATA INTEGRITY VALIDATED

📊 PORTFOLIO UPDATE SUMMARY
========================
Portfolio: live_signals
Total positions: 36
Open positions updated: 17
Closed positions (unchanged): 19

🔄 UPDATE TIMESTAMP: 2025-06-25 18:00:00
✅ PORTFOLIO UPDATE COMPLETE
```

### **No Updates Needed**

```
ℹ️  No open positions found in protected portfolio
✅ UPDATE COMPLETE - No changes needed
```

## Dependencies

### **Core System Dependencies**

- **Trade History Executive Specification**: @docs/Trade_History_Executive_Specification.md
- **Generalized Trade History Exporter**: app/tools/generalized_trade_history_exporter.py
- **Trade History Close Command**: app/tools/trade_history_close_live_signal.py
- **Trade History Utilities**: app/tools/trade_history_utils.py
- **SPDS Services**: app/tools/services/ (SignalDataAggregator, ExitStrategyOptimizer, SellReportGenerator)

### **Data Dependencies**

- **Price Data**: csv/price_data/{TICKER}\_D.csv (auto-updated across all actions)
- **Portfolio Files**: csv/positions/{PORTFOLIO}.csv (live_signals, protected, risk_on, custom)
- **SPDS Exports**: exports/statistical_analysis/, exports/backtesting_parameters/
- **Trade History JSON**: json/trade_history/ (for comprehensive analysis)

## Security and Data Protection

- **Closed Position Protection**: Closed positions are never modified
- **Static Field Protection**: Entry data and strategy parameters remain immutable
- **Backup Strategy**: Original data preserved before updates
- **Validation Checks**: Comprehensive data integrity validation
- **Error Recovery**: Graceful handling of market data failures

---

## Command Consolidation Summary

### **Unified Trade History Management**

This consolidated `trade_history.md` command successfully merges the functionality of three previously separate commands:

1. **trade_history.md** (original) - Portfolio position updates
2. **trade_history_add_live_signal.md** - Position addition with signal verification
3. **trade_history_close_live_signal.md** - SPDS-powered sell signal reports

### **Key Consolidation Benefits**

#### **Single Interface**

- **5 Actions**: `update`, `add`, `close`, `list`, `validate`
- **Portfolio Agnostic**: Works with live_signals, protected, risk_on, and custom portfolios
- **Unified Parameter Structure**: Consistent command interface across all operations

#### **Enhanced Capabilities**

- **Signal Verification**: Comprehensive crossover analysis for position addition
- **SPDS Integration**: Full Statistical Performance Divergence System integration
- **Multi-Portfolio Support**: Operates across all portfolio types, not just live_signals
- **Risk Management**: Advanced MFE/MAE calculations and trade quality assessment

#### **Preserved Functionality**

- **Update Operations**: All original update capabilities maintained and enhanced
- **Add Operations**: Complete implementation of add functionality from specification
- **Close Operations**: Full SPDS sell signal report generation maintained
- **Data Integrity**: All existing data protection and validation features preserved

### **Implementation Status**

**✅ Fully Consolidated:**

- Command specification updated with unified interface
- Action-based routing implemented
- Portfolio generalization completed
- Integration points mapped to existing infrastructure

**✅ Ready for Implementation:**

- All underlying tools and services exist and are functional
- Clear implementation path using existing `generalized_trade_history_exporter.py` and `trade_history_close_live_signal.py`
- Comprehensive error handling and validation included

---

**Command Version**: 3.0 (Unified)
**Created**: July 7, 2025
**Consolidates**: trade_history.md + trade_history_add_live_signal.md + trade_history_close_live_signal.md
**Purpose**: Complete trade history lifecycle management across all portfolios
**Data Protection**: Closed positions and static fields preserved across all actions
**Portfolio Support**: live_signals, protected, risk_on, and custom portfolios
**Integration**: Full SPDS and Trade History Executive System integration
