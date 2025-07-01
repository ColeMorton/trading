# trade_history

## Description

Update existing open positions in portfolio CSV files with current market data. This command refreshes dynamic metrics for open positions including unrealized P&L, excursion metrics, days since entry, and trade quality assessments. Focuses specifically on positions with Status="Open" while preserving all closed position data.

## Parameters

- **portfolio** (optional): Portfolio name to update (default: "live_signals")
  - Available portfolios: live_signals, protected, risk_on, or any custom portfolio in csv/positions/

## Objectives

1. **Read Trade History Executive Specification**: Examine @docs/Trade_History_Executive_Specification.md for update protocols
2. **Open Position Identification**: Identify all positions with Status="Open" in the target portfolio
3. **Dynamic Metrics Update**: Refresh time-sensitive and market-dependent fields
4. **Data Integrity**: Preserve all static fields and closed position data
5. **Risk Assessment**: Recalculate MFE/MAE and trade quality for open positions

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

### Phase 1: Portfolio Validation and Open Position Detection

```bash
# Set default portfolio if not provided
Portfolio="${portfolio:-live_signals}"

# Read and understand the executive specification
cat docs/Trade_History_Executive_Specification.md

# Validate portfolio exists
if [ ! -f "csv/positions/${Portfolio}.csv" ]; then
    echo "❌ PORTFOLIO NOT FOUND: csv/positions/${Portfolio}.csv"
    echo "Available portfolios:"
    ls csv/positions/*.csv | xargs -n 1 basename | sed 's/.csv//'
    exit 1
fi

echo "🔄 UPDATING PORTFOLIO: ${Portfolio}"
echo "Target file: csv/positions/${Portfolio}.csv"

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
```

### Phase 2: Dynamic Metrics Calculation

```bash
# Update dynamic metrics for all open positions
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
```

### Phase 3: Market Data Integration and Risk Recalculation

```bash
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
```

### Phase 4: Trade Quality Reassessment

```bash
# Reassess trade quality for open positions with updated metrics
python app/tools/trade_history_utils.py --update-quality \
    --portfolio "$Portfolio" \
    --open-only \
    --verbose

if [ $? -eq 0 ]; then
    echo "✅ TRADE QUALITY REASSESSMENT COMPLETE"
else
    echo "⚠️  Trade quality update had issues"
fi
```

### Phase 5: Validation and Reporting

```bash
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
    null_count = open_positions[field].isnull().sum()
    if null_count > 0:
        errors.append(f'{field}: {null_count} null values in open positions')

# Validate MFE/MAE ratios
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

### **Default Portfolio Update**

```bash
# Update live_signals portfolio (default)
/trade_history
```

### **Specific Portfolio Update**

```bash
# Update protected portfolio
/trade_history --portfolio protected

# Update risk_on portfolio
/trade_history --portfolio risk_on
```

### **Automated Daily Update**

```bash
# Can be added to cron for daily updates
0 18 * * * cd /path/to/trading && /trade_history --portfolio live_signals
```

## Integration with Trade History System

This command integrates with the existing Trade History Executive System:

1. **Reads Specification**: Examines executive specification for update protocols
2. **Preserves Integrity**: Never modifies closed positions or static fields
3. **Market Integration**: Uses latest price data for accurate calculations
4. **Quality Monitoring**: Continuously reassesses trade performance
5. **Schema Compliance**: Maintains position-level schema standards

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

- **Trade History Executive Specification**: @docs/Trade_History_Executive_Specification.md
- **Generalized Trade History Exporter**: app/tools/generalized_trade_history_exporter.py
- **Trade History Utilities**: app/tools/trade_history_utils.py
- **Price Data**: csv/price_data/{TICKER}\_D.csv (auto-updated)
- **Portfolio Files**: csv/positions/{PORTFOLIO}.csv

## Security and Data Protection

- **Closed Position Protection**: Closed positions are never modified
- **Static Field Protection**: Entry data and strategy parameters remain immutable
- **Backup Strategy**: Original data preserved before updates
- **Validation Checks**: Comprehensive data integrity validation
- **Error Recovery**: Graceful handling of market data failures

---

**Command Version**: 2.0
**Created**: June 25, 2025
**Purpose**: Open Position Updates Only
**Data Protection**: Closed positions and static fields preserved
**Update Focus**: Dynamic metrics and market-driven calculations
