# trade_history_add_live_signal

## Description

Add a new position to the Live Signals portfolio with comprehensive signal verification and risk management. This command reads the Trade History Executive Specification on each execution and strictly follows its guidelines for position creation, signal validation, and data integrity.

## Parameters

- **Strategy_Type** (required): Strategy type (SMA, EMA, MACD, RSI, BOLLINGER, STOCHASTIC)
- **Short_Window** (required): Short window period for the strategy (positive integer)
- **Long_Window** (required): Long window period for the strategy (positive integer, must be > Short_Window)
- **Signal_Window** (optional): Signal window period (default: 0)
- **Entry_Timestamp** (required): Entry date in YYYY-MM-DD format
- **Ticker** (optional): Ticker symbol (auto-detected from recent strategies if not provided)

## Objectives

1. **Read Trade History Executive Specification**: Examine @docs/Trade_History_Executive_Specification.md on each execution
2. **Signal Verification**: Verify that the entry signal actually occurred on the specified date using crossover analysis
3. **Position Creation**: Add verified position to @csv/positions/live_signals.csv with complete schema compliance
4. **Data Integrity**: Ensure no duplicate UUIDs and maintain position-level schema standards
5. **Risk Management**: Calculate MFE/MAE metrics and trade quality assessment

## Implementation Process

### Phase 1: Specification Review and Validation

```bash
# Read and understand the executive specification
cat docs/Trade_History_Executive_Specification.md

# Validate input parameters
echo "Validating Strategy_Type: $Strategy_Type"
echo "Validating Short_Window: $Short_Window"
echo "Validating Long_Window: $Long_Window"
echo "Validating Entry_Timestamp: $Entry_Timestamp"
```

### Phase 2: Ticker Detection and Signal Verification

```bash
# Auto-detect ticker if not provided (from recent strategy activity)
if [ -z "$Ticker" ]; then
    Ticker=$(python -c "
from app.strategies.update_portfolios import get_recent_ticker
print(get_recent_ticker())
")
    echo "Auto-detected ticker: $Ticker"
fi

# Verify entry signal occurred on specified date
python app/tools/generalized_trade_history_exporter.py --verify-signal \
    --ticker "$Ticker" \
    --strategy "$Strategy_Type" \
    --short-window "$Short_Window" \
    --long-window "$Long_Window" \
    --entry-date "$Entry_Timestamp"

if [ $? -ne 0 ]; then
    echo "❌ SIGNAL VERIFICATION FAILED"
    echo "No valid crossover signal found on $Entry_Timestamp for $Ticker $Strategy_Type $Short_Window/$Long_Window"
    exit 1
fi

echo "✅ SIGNAL VERIFIED: Valid crossover detected on $Entry_Timestamp"
```

### Phase 3: Position Creation with Full Schema Compliance

```bash
# Add position to live_signals portfolio with automatic signal verification
python app/tools/generalized_trade_history_exporter.py --add-position \
    --ticker "$Ticker" \
    --strategy "$Strategy_Type" \
    --short-window "$Short_Window" \
    --long-window "$Long_Window" \
    --signal-window "${Signal_Window:-0}" \
    --entry-date "$Entry_Timestamp" \
    --portfolio "live_signals" \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ POSITION ADDED SUCCESSFULLY"

    # Generate position UUID for reference
    Position_UUID="${Ticker}_${Strategy_Type}_${Short_Window}_${Long_Window}_${Signal_Window:-0}_${Entry_Timestamp}"
    echo "Position UUID: $Position_UUID"

    # Display portfolio summary
    python app/tools/trade_history_utils.py --summary --portfolio live_signals
else
    echo "❌ POSITION CREATION FAILED"
    exit 1
fi
```

### Phase 4: Validation and Verification

```bash
# Verify position was added correctly
echo "Verifying position in live_signals.csv..."
grep "$Position_UUID" csv/positions/live_signals.csv

if [ $? -eq 0 ]; then
    echo "✅ POSITION VERIFICATION COMPLETE"
    echo "Position successfully added to Live Signals portfolio"
else
    echo "❌ POSITION VERIFICATION FAILED"
    exit 1
fi

# Check for duplicates
python app/tools/trade_history_utils.py --find-duplicates --portfolio live_signals

# Update trade quality if needed
python app/tools/trade_history_utils.py --update-quality --portfolio live_signals
```

## Signal Verification Details

The command performs comprehensive signal verification using the `verify_entry_signal()` function from the Trade History Executive Specification:

### Crossover Detection Logic

- **Bullish Crossover** (Long Entry): `(current_short > current_long) AND (prev_short <= prev_long)`
- **Bearish Crossover** (Short Entry): `(current_short < current_long) AND (prev_short >= prev_long)`

### Verification Output Example

```
✓ VERIFIED: Bullish crossover on 2025-06-24 - SMA49 ($147.96) crossed above SMA66 ($147.78)

Signal Details:
  Close Price: $155.71
  SMA49: $147.96 (prev: $147.63)
  SMA66: $147.78 (prev: $147.82)
  MA Spread: $0.18 (prev: $-0.19)
  Signal Type: Bullish Crossover (Long Entry)
```

## Error Handling

### Signal Verification Failures

```bash
# Example failure output
✗ NO SIGNAL: SMA49 ($147.63) was below SMA66 ($147.82) on 2025-06-23 with no crossover
```

### Invalid Parameter Handling

- **Invalid Strategy Type**: Returns list of supported strategies
- **Invalid Date Format**: Provides correct YYYY-MM-DD format example
- **Missing Price Data**: Indicates missing ticker price data file
- **Duplicate Position**: Warns about existing UUID in portfolio

## Position Schema Compliance

The command ensures full compliance with the position-level schema defined in the Trade History Executive Specification:

### Core Fields

```csv
Position_UUID,Ticker,Strategy_Type,Short_Window,Long_Window,Signal_Window,
Entry_Timestamp,Exit_Timestamp,Avg_Entry_Price,Avg_Exit_Price,Position_Size,
Direction,PnL,Return,Duration_Days,Trade_Type,Status
```

### Risk Metrics

```csv
Max_Favourable_Excursion,Max_Adverse_Excursion,MFE_MAE_Ratio,Exit_Efficiency,
Exit_Efficiency_Fixed,Trade_Quality,Days_Since_Entry,Current_Unrealized_PnL,Current_Excursion_Status
```

## Usage Examples

### Basic Usage

```bash
claude trade_history_add_live_signal \
    --Strategy_Type SMA \
    --Short_Window 49 \
    --Long_Window 66 \
    --Entry_Timestamp 2025-06-24
```

### With Specific Ticker

```bash
claude trade_history_add_live_signal \
    --Strategy_Type EMA \
    --Short_Window 12 \
    --Long_Window 26 \
    --Signal_Window 9 \
    --Entry_Timestamp 2025-06-25 \
    --Ticker AAPL
```

### Advanced Strategy

```bash
claude trade_history_add_live_signal \
    --Strategy_Type MACD \
    --Short_Window 12 \
    --Long_Window 26 \
    --Signal_Window 9 \
    --Entry_Timestamp 2025-06-20 \
    --Ticker BTC-USD
```

## Integration with Trade History System

This command integrates seamlessly with the Trade History Executive System:

1. **Reads Specification**: Examines the executive specification on each execution
2. **Signal Verification**: Uses the `verify_entry_signal()` engine for validation
3. **Position Creation**: Leverages `add_position_to_portfolio()` with verification
4. **Risk Calculation**: Automatically calculates MFE/MAE using price data integration
5. **Quality Assessment**: Applies trade quality classification algorithms
6. **Schema Compliance**: Ensures position-level schema adherence

## Output and Reporting

### Success Output

```
✅ SIGNAL VERIFIED: Valid crossover detected on 2025-06-24
✅ POSITION ADDED SUCCESSFULLY
Position UUID: QCOM_SMA_49_66_0_2025-06-24
✅ POSITION VERIFICATION COMPLETE
Position successfully added to Live Signals portfolio

LIVE_SIGNALS PORTFOLIO SUMMARY
==============================
Total positions: 36
Open positions: 17
Closed positions: 19
```

### Failure Output

```
❌ SIGNAL VERIFICATION FAILED
No valid crossover signal found on 2025-06-23 for QCOM SMA 49/66
Command failed with exit code 1
```

## Dependencies

- **Trade History Executive Specification**: @docs/Trade_History_Executive_Specification.md
- **Generalized Trade History Exporter**: app/tools/generalized_trade_history_exporter.py
- **Trade History Utilities**: app/tools/trade_history_utils.py
- **Price Data**: csv/price_data/{TICKER}\_D.csv
- **Live Signals Portfolio**: csv/positions/live_signals.csv

## Security and Validation

- **Input Validation**: All parameters validated against specification requirements
- **Signal Verification**: Mandatory crossover signal validation prevents false entries
- **UUID Uniqueness**: Prevents duplicate position creation
- **Schema Compliance**: Ensures data integrity across all position fields
- **Error Recovery**: Comprehensive error handling with clear failure messages

---

**Command Version**: 1.0
**Created**: June 26, 2025
**Specification Compliance**: Trade History Executive Specification v3.1
**Signal Verification**: Enabled by default with crossover detection
**Risk Management**: Full MFE/MAE calculation and trade quality assessment
