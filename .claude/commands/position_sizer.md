# Position Sizer

Kelly Criterion-optimized position sizing workflow for incoming trading strategies with comprehensive risk management.

## Purpose

Executes the complete Position Sizing Executive Specification workflow to calculate optimal position sizes for strategies in `./csv/strategies/incoming.csv`. Implements Kelly Criterion mathematics with risk adjustments, custom stop-loss integration, and CVaR portfolio constraints to determine precise share quantities and dollar allocations for new positions.

## Parameters

- `incoming_csv`: Path to incoming strategies CSV (default: `./csv/strategies/incoming.csv`)
- `current_csv`: Path to current portfolio CSV (default: `./csv/strategies/risk_on.csv`)
- `kelly_params`: Path to Kelly parameters JSON (default: `./data/kelly/kelly_parameters.json`)
- `accounts`: Path to account balances JSON (default: `./data/accounts/manual_balances.json`)
- `cvar_target`: Portfolio CVaR target (default: `0.118` = 11.8%)
- `max_position_risk`: Maximum risk per position (default: `0.15` = 15%)
- `correlation_adjustment`: Position correlation factor (default: `0.8` = 20% correlation)
- `output_format`: Report format (`console` | `file` | `both`) (default: `both`)
- `export_json`: Export results to JSON (default: `true`, saves to `./data/positions/incoming.json`)
- `implementation_mode`: Execution mode (`analysis` | `entry_plan` | `full_execution`) (default: `analysis`)

## Process

### **Phase 1: System Parameter Loading & Validation**

1. **Load Kelly Parameters**: Extract kelly_criterion from JSON file (currently 4.48%)
2. **Calculate Total Capital**: Sum account balances from all accounts (IBKR + Bybit + Cash)
3. **Validate Data Sources**: Confirm incoming strategies CSV exists and contains required fields
4. **Initialize Kelly Framework**: Setup Kelly-optimized position sizer with loaded parameters

### **Phase 2: Strategy Analysis & Kelly Calculation**

1. **Extract Strategy Metrics**: Load win rates, profit factors, stop-loss levels, and performance data
2. **Calculate Theoretical Kelly**: Apply pure Kelly formula: `K = (bp - q) / b` for each strategy
3. **Apply Risk Adjustments**: Scale based on Sortino ratio, Calmar ratio, volatility, and drawdown
4. **Integrate Stop-Loss Reality**: Adjust position sizes for actual risk per trade (custom stop-loss %)
5. **Validate Mathematical Edges**: Confirm positive Kelly calculations indicating quantifiable edges

### **Phase 3: Portfolio-Level Risk Management**

1. **Calculate CVaR Contributions**: Determine individual strategy risk contributions to portfolio
2. **Apply Correlation Adjustments**: Account for position interdependencies (default 20% correlation)
3. **Enforce Portfolio Constraints**: Scale allocations if total risk exceeds 11.8% CVaR target
4. **Validate Risk Budget**: Ensure remaining CVaR capacity for future opportunities
5. **Generate Risk Warnings**: Alert if any position exceeds maximum risk thresholds

### **Phase 4: Position Execution Calculations**

1. **Retrieve Current Prices**: Fetch real-time market prices for accurate share calculations
2. **Calculate Share Quantities**: Determine integer share positions from dollar allocations
3. **Compute Risk Per Trade**: Calculate maximum risk per position based on stop-loss levels
4. **Project Expected Returns**: Estimate return expectations based on historical performance
5. **Validate Position Sizes**: Ensure positions meet minimum/maximum size requirements

### **Phase 5: Implementation Planning & Reporting**

1. **Generate Priority Ranking**: Order positions by allocation size and risk-adjusted characteristics
2. **Create Entry Sequence**: Develop phase-based implementation plan with validation periods
3. **Produce Comprehensive Report**: Generate Kelly analysis, risk assessment, and execution plan
4. **Export JSON Results**: Save structured position data to `./data/positions/incoming.json`
5. **Save Additional Reports**: Output findings to specified format (console/file/both)
6. **Validate Success Criteria**: Confirm all specifications met per Position_Sizing_Executive_Specification.md

## Implementation Modes

### **Analysis Mode** (default)

- Calculates optimal position sizes
- Generates comprehensive reports
- No actual position entry
- Full risk analysis and validation

### **Entry Plan Mode**

- Creates detailed execution sequence
- Specifies exact entry timing
- Includes risk monitoring protocols
- Prepares for live implementation

### **Full Execution Mode**

- ⚠️ **LIVE TRADING MODE** - Requires explicit confirmation
- Executes actual position entries
- Implements stop-loss orders
- Real-time risk monitoring

## Expected Outputs

### **JSON Export** (`./data/positions/incoming.json`)

```json
{
  "timestamp": "2025-06-25T10:30:00.000Z",
  "total_capital": 14194.36,
  "kelly_criterion": 0.0448,
  "cvar_target": 0.118,
  "cvar_utilization": 0.077,
  "positions": [
    {
      "ticker": "XRAY",
      "strategy_type": "SMA",
      "theoretical_kelly": 0.439,
      "risk_adjusted_kelly": 0.15,
      "stop_loss_adjusted_kelly": 0.125,
      "final_allocation": 0.125,
      "position_shares": 113,
      "dollar_amount": 1767.0,
      "stop_loss_percentage": 0.12,
      "max_risk_per_trade": 212.04,
      "expected_return": 7.145,
      "risk_contribution": 0.002,
      "priority": 2
    },
    {
      "ticker": "QCOM",
      "strategy_type": "SMA",
      "theoretical_kelly": 0.426,
      "risk_adjusted_kelly": 0.15,
      "stop_loss_adjusted_kelly": 0.143,
      "final_allocation": 0.143,
      "position_shares": 13,
      "dollar_amount": 2024.0,
      "stop_loss_percentage": 0.105,
      "max_risk_per_trade": 212.52,
      "expected_return": 24.389,
      "risk_contribution": 0.012,
      "priority": 1
    }
  ],
  "portfolio_summary": {
    "total_allocation": 0.268,
    "total_amount": 3791.0,
    "total_risk": 0.009,
    "remaining_capacity": 0.109,
    "average_kelly": 0.134
  }
}
```

### **Kelly Optimization Report**

```
================================================================================
KELLY-OPTIMIZED POSITION SIZING REPORT
================================================================================
Total Capital: $14,194.36
Global Kelly Base: 4.5%
CVaR Target: 11.8%

KELLY CRITERION ANALYSIS
--------------------------------------------------
Ticker   Theor%   Risk%    Stop%    Final%   Shares   Amount
--------------------------------------------------
[Strategy results with theoretical, risk-adjusted, and final allocations]

RISK ANALYSIS
------------------------------
Total Portfolio Risk: X.X%
CVaR Target Utilization: XX.X%
Remaining Capacity: XX.X%
```

### **Implementation Plan**

- Priority-ordered position entry sequence
- Risk monitoring protocols
- Validation checkpoints
- Stop-loss placement instructions

### **Risk Assessment**

- Individual position risk contributions
- Portfolio-level CVaR utilization
- Correlation impact analysis
- Maximum risk per trade calculations

## Usage

```bash
# Basic analysis of incoming strategies
/position_sizer

# Custom CSV files with detailed reporting
/position_sizer incoming_csv:./custom/strategies.csv output_format:both

# Risk-conservative analysis with lower CVaR target
/position_sizer cvar_target:0.10 max_position_risk:0.12

# Generate entry plan for implementation
/position_sizer implementation_mode:entry_plan output_format:file

# Full analysis with custom correlation assumptions
/position_sizer correlation_adjustment:0.7 cvar_target:0.118

# Export to JSON only (skip console output)
/position_sizer output_format:file export_json:true
```

## Success Validation

### **Mathematical Validation**

- [ ] Kelly calculations follow `K = (bp - q) / b` formula exactly
- [ ] Risk adjustments applied based on Sortino, Calmar, volatility factors
- [ ] Stop-loss integration reflects actual risk per trade
- [ ] Portfolio CVaR calculations include correlation adjustments

### **Data Integration Validation**

- [ ] Kelly criterion loaded from `./data/kelly/kelly_parameters.json`
- [ ] Total capital calculated from `./data/accounts/manual_balances.json`
- [ ] Strategy metrics extracted from incoming CSV with all required fields
- [ ] Current portfolio data integrated for correlation analysis

### **Risk Management Validation**

- [ ] CVaR target utilization calculated and enforced
- [ ] Individual position risk limits respected (default 15%)
- [ ] Maximum risk per trade computed using custom stop-loss levels
- [ ] Portfolio constraints applied if risk exceeds targets

### **Output Validation**

- [ ] Kelly-optimized allocations generated for all viable strategies
- [ ] Share quantities calculated as integers for practical execution
- [ ] Dollar amounts computed based on current market prices
- [ ] Implementation sequence prioritized by allocation size and risk metrics
- [ ] JSON export saved to `./data/positions/incoming.json` with complete position data

### **Specification Compliance**

- [ ] All requirements from Position_Sizing_Executive_Specification.md implemented
- [ ] Universal framework applicable to any strategy/ticker combination
- [ ] Mathematical rigor maintained throughout calculation process
- [ ] Institutional-grade risk management standards met

## Error Handling

### **Data Errors**

- Missing CSV files → Graceful error with file path guidance
- Invalid JSON parameters → Fallback to documented defaults
- Missing strategy fields → Clear field requirement messaging
- Price data unavailable → Fallback pricing with warnings

### **Calculation Errors**

- Negative Kelly values → Strategy exclusion with rationale
- CVaR target exceeded → Automatic scaling with notification
- Zero win rates → Mathematical edge validation failure
- Invalid stop-loss levels → Default stop-loss application

### **Risk Errors**

- Excessive position concentration → Position size scaling
- Portfolio risk exceeded → Allocation reduction recommendations
- Correlation assumptions invalid → Conservative fallback adjustments
- Capital constraints → Available capital allocation optimization

## Notes

- **Universal Application**: Framework works with any strategy CSV containing required fields (Ticker, Win Rate, Profit Factor, Stop Loss %)
- **Real-Time Data**: Always uses current Kelly parameters and account balances from JSON files
- **Mathematical Foundation**: Every allocation decision quantitatively justified via Kelly Criterion
- **Risk Priority**: CVaR targeting ensures institutional-grade risk management
- **Scalable Framework**: Methodology extends to unlimited strategy combinations
- **Implementation Ready**: Generates actionable position sizing with exact share quantities

## Integration Points

- **Data Sources**: `./csv/strategies/incoming.csv`, `./data/kelly/kelly_parameters.json`, `./data/accounts/manual_balances.json`
- **JSON Export**: Structured position data exported to `./data/positions/incoming.json` for system integration
- **Risk Framework**: Integrates with existing CVaR targeting and portfolio risk management
- **Execution Engine**: Compatible with position sizing algorithms in `./app/position_sizing/`
- **Reporting System**: Outputs compatible with executive specification requirements
- **Validation Framework**: Ensures compliance with Position_Sizing_Executive_Specification.md
