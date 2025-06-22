# Position Sizing System Specification

## Single Source of Truth

**Document Version**: 1.0
**Last Updated**: 2025-06-22
**Status**: Production Implementation

---

## Executive Summary

This specification documents the Position Sizing System that replaces Excel-based portfolio management with an automated, real-time solution. The system implements a **11.8% CVaR target** for risk management with comprehensive manual data entry capabilities.

**Key Principle**: Target risk of 11.8% CVaR (95% confidence).

---

## 1. Core Architecture

### 1.1 Risk Management Framework

**Single Risk Target**: 11.8% CVaR Target

- **Target CVaR**: 11.8% (fixed)
- **Current CVaR**: Real-time calculation from trading portfolio
- **Risk Utilization**: Current CVaR ÷ Target CVaR
- **Available Risk**: Target CVaR - Current CVaR
- **Maximum Risk Amount**: Net Worth × 11.8%

### 1.2 Portfolio Structure

**Dual Portfolio System**:

- **Risk-On Trading Portfolio**: Active trading positions with CVaR monitoring
- **Investment Portfolio**: Strategic holdings (BTC, MSTR) with separate CVaR calculation

**Account Integration**:

- **IBKR**: Interactive Brokers trading account
- **Bybit**: Crypto exchange account
- **Cash**: Liquid reserves
- **Net Worth**: Sum of all account balances

---

## 2. Data Sources and Calculations

### 2.1 CVaR Calculations

**Trading CVaR**:

- Source: `json/concurrency/trades.json: portfolio_metrics.risk.combined_risk.cvar_95`
- Cross-reference: `csv/strategies/trades.csv` for validation
- Current Value: -7.05% (displayed as 7.05%)

**Investment CVaR**:

- Source: `json/concurrency/portfolio.json: portfolio_metrics.risk.combined_risk.cvar_95`
- Cross-reference: `csv/strategies/portfolio.csv` for validation

### 2.2 Kelly Criterion Parameters

**Manual Input Sources**:

- **Kelly Criterion**: 4.48% (from trading journal)
- **Primary Trades**: 214 (manual count)
- **Outlier Trades**: 25 (manual count)
- **Confidence**: 89.54% calculated (Primary ÷ Total)

**Kelly Amount Formula**:

```
Kelly Amount = Kelly Criterion × Kelly Fraction × Net Worth
Where: Kelly Fraction = 23.6% (0.236)
Example: 0.0448 × 0.236 × $13,579 = $143.57
```

### 2.3 Account Balances

**Manual Entry System**:

- **IBKR**: $7,803 (manual update from broker)
- **Bybit**: $5,333 (manual update from exchange)
- **Cash**: $443 (manual tracking)
- **Total Net Worth**: $13,579 (calculated sum)

---

## 3. Risk Allocation Specification

### 3.1 Risk Target (11.8% CVaR Target)

```
Target CVaR: 11.8%
Current CVaR: 7.05% (from trading data)
Risk Utilization: 7.05% ÷ 11.8% = 59.7% Used
Available Risk: 11.8% - 7.05% = 4.75% Available
Maximum Risk Amount: $13,579 × 11.8% = $1,602
```

### 3.2 Risk Monitoring Display

**Dashboard Elements**:

- **Target CVaR**: Fixed 11.8% indicator
- **Current CVaR**: Real-time value from trading portfolio
- **Risk Utilization Progress Bar**: Visual percentage used vs available
- **Risk Amount**: Dollar value of maximum risk allocation
- **Color Coding**: Green (<70%), Yellow (70-90%), Red (>90%)

---

## 4. Manual Data Entry Components

### 4.1 Account Balance Management

**Data Entry Requirements**:

- Manual input for IBKR, Bybit, Cash balances
- Real-time net worth calculation
- Last updated timestamps
- Balance validation (non-negative values)

### 4.2 Kelly Criterion Input

**Required Fields**:

- Kelly Criterion value (0.0448 = 4.48%)
- Number of primary trades (214)
- Number of outlier trades (25)
- Source tracking (Trading Journal)
- Update timestamps

### 4.3 Position Management

**Position Entry**:

- Symbol identification
- Position value (from broker fills)
- Entry date (manual)
- Current status (Active/Closed/Pending)
- Portfolio type (Risk_On/Investment/Protected)
- Stop-loss distance (manual)

---

## 5. Technical Implementation

### 5.1 Backend Services

**Core Components**:

- `PositionSizingOrchestrator`: Main coordination service
- `CVaRCalculator`: Risk metric calculations
- `KellyCriterionSizer`: Kelly calculations with manual inputs
- `ManualAccountBalanceService`: Account balance management
- `RiskAllocationCalculator`: Target 11.8% calculations

### 5.2 API Endpoints

**Dashboard Data**:

- `GET /api/position-sizing/dashboard`: Complete dashboard data
- `GET /api/position-sizing/risk/allocation`: Risk allocation status

**Manual Entry**:

- `POST /api/position-sizing/accounts/balance`: Update account balances
- `POST /api/position-sizing/kelly`: Update Kelly parameters
- `POST /api/position-sizing/positions`: Add/update positions

### 5.3 Frontend Components

**Dashboard Structure**:

- `PositionSizingDashboard`: Main dashboard page
- `PortfolioRiskPanel`: Risk metrics display
- `RiskAllocation`: 11.8% target visualization
- `ActivePositionsTable`: Current positions
- `IncomingSignalsTable`: Pending signals
- `StrategicHoldingsTable`: Investment portfolio

---

## 6. Data Storage

### 6.1 Configuration Files

**Account Balances**: `/data/accounts/manual_balances.json`

```json
{
  "balances": [
    { "account_type": "IBKR", "balance": 7803.0 },
    { "account_type": "Bybit", "balance": 5333 },
    { "account_type": "Cash", "balance": 443 }
  ]
}
```

**Kelly Parameters**: `/data/kelly/kelly_parameters.json`

```json
{
  "num_primary": 214,
  "num_outliers": 25,
  "kelly_criterion": 0.0448
}
```

### 6.2 CSV Integration

**Enhanced Format Support**:

- Backward compatible with existing CSV files
- Optional columns for manual entry data
- Automatic format detection and migration
- Validation and error handling

---

## 7. Business Rules

### 7.1 Risk Management Rules

**Risk Target Enforcement**:

- Maximum risk allocation: 11.8% of net worth
- Real-time monitoring against target
- Automatic alerts when approaching limits

### 7.2 Portfolio Lifecycle

**Position Flow**:

1. **Risk-On**: Active trading positions
2. **Protected**: Positions moved to protection (optional transition)
3. **Investment**: Long-term strategic holdings

### 7.3 Validation Rules

**Data Integrity**:

- Account balances must be non-negative
- Kelly Criterion must be between 0-100%
- Position values must be positive
- CVaR calculations must use valid data sources

---

## 8. User Interface Requirements

### 8.1 Dashboard Layout

**Main Sections**:

1. **Portfolio Risk Metrics**: Net worth, CVaR, risk amount
2. **Account Balances**: IBKR, Bybit, Cash breakdown
3. **Risk Allocation**: Single 11.8% target with utilization
4. **Active Positions**: Current trading positions
5. **Incoming Signals**: Pending position opportunities
6. **Strategic Holdings**: Investment portfolio

### 8.2 Manual Entry Forms

**Required Capabilities**:

- Account balance input with validation
- Kelly parameter management
- Position entry and editing
- Real-time validation feedback
- Error handling and user guidance

---

## 9. Performance Requirements

### 9.1 Response Times

**Target Performance**:

- Dashboard load: <3 seconds
- User interactions: <500ms
- Risk calculations: <1 second
- Chart rendering: <2 seconds

### 9.2 Data Refresh

**Update Frequencies**:

- Risk allocation: Real-time (30-second refresh)
- CVaR calculations: On-demand
- Account balances: Manual update only
- Position data: Real-time during trading hours

---

## 10. Migration from Excel

### 10.1 Excel System Legacy

**Previous Implementation**:

- Manual calculations and updates
- Static data with daily updates

### 10.2 New System Benefits

**Improvements**:

- Single, focused 11.8% CVaR target
- Real-time risk monitoring
- Automated calculations
- Manual data entry capabilities
- Web-based accessibility
- Type-safe implementation

---

## 11. Success Metrics

### 11.1 Technical KPIs

**Performance Standards**:

- System uptime: >99.9%
- Response times: <500ms average
- Data accuracy: 100% vs Excel validation
- Error rate: <0.1%

### 11.2 Business KPIs

**Operational Efficiency**:

- 40% reduction in manual Excel maintenance
- Real-time risk awareness vs daily updates
- Improved decision-making speed
- Enhanced portfolio oversight

---

## Conclusion

This specification defines the Position Sizing System as implemented with a **11.8% CVaR target**. The system replaces Excel-based workflows with automated, real-time risk management while providing comprehensive manual data entry capabilities.

**Key Success Factors**:

- Target risk CVaR 95%
- Real-time monitoring and alerts
- Manual control with automated calculations
- Backward-compatible CSV integration
- Production-ready implementation

---

_This document serves as the single source of truth for the Position Sizing System. All implementation, testing, and operational decisions should reference this specification._
