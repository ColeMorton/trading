# Position Sizer

Calculates optimal position sizes for trading strategies using Kelly Criterion and other position sizing methods.

## Purpose

Analyzes trading strategies from `incoming.csv` and calculates optimal position sizes based on their performance metrics (win rate, profit factor, expectancy, drawdown, etc.). Exports position sizing analysis to `data/positions/` directory for implementation.

## Parameters

### **Input Parameters**

- `incoming_csv`: Path to strategy candidates CSV (default: `./data/raw/strategies/incoming.csv`)
- `total_capital`: Total capital available for allocation (default: auto-detect from account balances)
- `min_trades`: Minimum number of trades required (default: `20`)

### **Kelly Criterion Parameters**

- `kelly_multiplier`: Kelly fraction multiplier for conservative sizing (default: `0.25`)
- `max_kelly`: Maximum Kelly percentage per strategy (default: `0.20`)
- `min_win_rate`: Minimum win rate for inclusion (default: `0.50`)

### **Risk Management Parameters**

- `max_drawdown_threshold`: Maximum acceptable drawdown (default: `0.30`)
- `max_single_allocation`: Maximum allocation per strategy (default: `0.15`)
- `correlation_threshold`: Maximum strategy correlation (default: `0.70`)

### **Output Parameters**

- `output_format`: Report format (`console` | `file` | `both`) (default: `both`)
- `export_json`: Export to JSON (default: `true`)
- `output_directory`: Output directory (default: `./data/positions/`)

## Process

### **Step 1: Strategy Analysis**

1. Load strategies from `incoming.csv`
2. Analyze performance metrics (win rate, profit factor, expectancy, drawdown)
3. Filter strategies based on minimum criteria (trades, win rate, drawdown)

### **Step 2: Kelly Calculation**

1. Calculate Kelly Criterion for each strategy: `f = (bp - q) / b`
   - b = odds received (average win / average loss)
   - p = probability of winning (win rate)
   - q = probability of losing (1 - win rate)
2. Apply Kelly multiplier for conservative sizing
3. Cap individual positions at maximum allocation limits

### **Step 3: Risk Management**

1. Apply maximum drawdown filters
2. Check correlation between strategies
3. Ensure total allocation doesn't exceed available capital
4. Apply portfolio-level risk limits

### **Step 4: Position Sizing & Export**

1. Calculate dollar amounts and share quantities
2. Rank strategies by risk-adjusted returns
3. Generate position sizing report
4. Export results to JSON in `data/positions/`

## Implementation Modes

### **Analysis Mode** (default)

- Calculate optimal position sizes based on strategy performance
- Generate detailed position sizing report
- Export results to JSON without executing trades

### **Conservative Mode**

- Apply stricter risk management criteria
- Lower Kelly multiplier for more conservative sizing
- Higher minimum win rate requirements

### **Aggressive Mode**

- Higher Kelly multiplier for larger position sizes
- Relaxed filtering criteria
- Higher maximum allocation limits

## Expected Outputs

### **JSON Export** (`./data/positions/position_sizing_analysis.json`)

```json
{
  "timestamp": "2025-06-25T10:30:00.000Z",
  "total_capital": 14194.36,
  "kelly_multiplier": 0.25,
  "positions": [
    {
      "ticker": "XRAY",
      "strategy_type": "SMA",
      "win_rate": 0.578,
      "profit_factor": 1.77,
      "avg_win": 21.66,
      "avg_loss": -7.14,
      "kelly_fraction": 0.439,
      "adjusted_kelly": 0.11,
      "allocation_percent": 0.11,
      "dollar_amount": 1561.38,
      "max_drawdown": 0.374,
      "total_trades": 65,
      "rank": 1
    },
    {
      "ticker": "QCOM",
      "strategy_type": "SMA",
      "win_rate": 0.556,
      "profit_factor": 1.47,
      "avg_win": 53.45,
      "avg_loss": -10.67,
      "kelly_fraction": 0.426,
      "adjusted_kelly": 0.107,
      "allocation_percent": 0.107,
      "dollar_amount": 1518.8,
      "max_drawdown": 0.641,
      "total_trades": 82,
      "rank": 2
    }
  ],
  "portfolio_summary": {
    "total_strategies": 7,
    "qualified_strategies": 2,
    "total_allocation": 0.217,
    "cash_remaining": 0.783,
    "avg_win_rate": 0.567,
    "portfolio_kelly": 0.217
  }
}
```

### **Position Sizing Report**

```
================================================================================
POSITION SIZING ANALYSIS
================================================================================
Total Capital: $14,194.36
Kelly Multiplier: 0.25 (Conservative)
Analysis Date: 2025-06-25

STRATEGY ANALYSIS
--------------------------------------------------
Total Strategies Analyzed: 7
Qualified Strategies: 2
Filtered Out: 5 (insufficient win rate or excessive drawdown)

POSITION SIZING RESULTS
--------------------------------------------------
Ticker   Win%   P.Factor   Kelly%   Adj.Kelly   Allocation   Amount
--------------------------------------------------
XRAY     57.8%    1.77     43.9%     11.0%      $1,561    STRONG
QCOM     55.6%    1.47     42.6%     10.7%      $1,519    MODERATE
HUBB     56.3%    2.73      X         X           $0     HIGH DRAWDOWN
LH       55.4%    1.54      X         X           $0     HIGH DRAWDOWN
VRSN     51.9%    1.42      X         X           $0     LOW WIN RATE
SCHW     53.7%    1.29      X         X           $0     HIGH DRAWDOWN
SIRI     50.9%    1.33      X         X           $0     LOW WIN RATE

PORTFOLIO SUMMARY
------------------------------
Total Allocation: 21.7%          Cash Reserve: 78.3%
Portfolio Kelly: 21.7%           Strategies: 2 of 7
Average Win Rate: 56.7%          Conservative Approach: ENABLED
```

### **Implementation Plan**

1. **XRAY (Rank 1)**: Allocate $1,561 (11.0% Kelly-adjusted)

   - Strong 57.8% win rate with 1.77 profit factor
   - Manageable 37.4% max drawdown

2. **QCOM (Rank 2)**: Allocate $1,519 (10.7% Kelly-adjusted)

   - Good 55.6% win rate with 1.47 profit factor
   - Higher 64.1% max drawdown requires monitoring

3. **Cash Reserve**: $11,114 (78.3%)
   - Conservative approach due to high drawdowns in other strategies
   - Available for additional qualified strategies

## Usage

```bash
# Basic position sizing analysis
/position_sizer

# Conservative position sizing
/position_sizer kelly_multiplier:0.20 max_single_allocation:0.10

# Aggressive position sizing
/position_sizer kelly_multiplier:0.50 min_win_rate:0.45

# Custom input file
/position_sizer incoming_csv:./data/raw/strategies/custom_strategies.csv

# Strict risk management
/position_sizer max_drawdown_threshold:0.20 min_win_rate:0.60

# Export to specific directory
/position_sizer output_directory:./results/positions/ export_json:true
```

## Success Validation

### **Input Processing**

- [ ] Successfully loads strategies from `incoming.csv`
- [ ] Parses all performance metrics (win rate, profit factor, drawdown, etc.)
- [ ] Applies minimum criteria filters (trades, win rate, drawdown)

### **Kelly Calculation**

- [ ] Correctly calculates Kelly Criterion: `f = (bp - q) / b`
- [ ] Applies Kelly multiplier for conservative sizing
- [ ] Caps positions at maximum allocation limits

### **Risk Management**

- [ ] Filters strategies exceeding maximum drawdown threshold
- [ ] Ensures total allocation doesn't exceed available capital
- [ ] Applies individual position size limits

### **Output Generation**

- [ ] Generates position sizing report with rankings
- [ ] Exports JSON to `data/positions/` directory
- [ ] Provides clear implementation recommendations

## Error Handling

### **Data Errors**

- Missing CSV file → Use default path `./data/raw/strategies/incoming.csv`
- Invalid performance data → Skip strategy with warning
- Insufficient trade count → Exclude from analysis
- Missing required columns → Report error and exit

### **Calculation Errors**

- Negative Kelly values → Set allocation to 0%
- Division by zero → Skip strategy calculation
- Invalid win/loss ratios → Use alternative sizing method
- Extremely high Kelly → Cap at maximum allocation

### **Output Errors**

- Directory doesn't exist → Create `data/positions/` directory
- Permission errors → Report file access issues
- JSON export failure → Continue with console output only

## Notes

- **Conservative Approach**: Uses Kelly multiplier to reduce position sizes for safety
- **Risk-Based Filtering**: Excludes strategies with excessive drawdowns or low win rates
- **Mathematical Foundation**: Kelly Criterion provides optimal position sizing framework
- **Export Integration**: Results saved to `data/positions/` for implementation tracking

## Integration Points

- **Strategy Input**: `./data/raw/strategies/incoming.csv` (strategy performance data)
- **Position Output**: `./data/positions/` (JSON exports for implementation)
- **Account Data**: Auto-detects available capital for allocation
- **Risk Management**: Integrates with portfolio risk limits and constraints
