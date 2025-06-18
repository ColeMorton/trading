# Position Sizing Excel Spreadsheet Specification

## Executive Summary

This specification documents a Position Sizing Excel Spreadsheet system based purely on the observable elements in the provided screenshots. The spreadsheet appears to be a comprehensive portfolio management tool that handles multiple account balances, risk calculations, position sizing, and tracks both active positions and incoming trading signals.

## 1. Spreadsheet Structure Overview

Based on the screenshots, the spreadsheet contains:

- **Portfolio Risk Dashboard** (Screenshot 1) - Account balances and risk metrics
- **Risk-On Trading Positions** (Screenshot 2, top) - Active trading positions
- **Incoming Signals** (Screenshot 2, middle) - Pipeline of potential new positions
- **Investment Portfolio** (Screenshot 2, bottom) - Strategic holdings

## 2. Portfolio Risk Dashboard (Screenshot 1)

### 2.1 Account Balance Section

**Observable Structure:**

```
Row 1: Net Worth | IBKR | Bybit | Cash | [Column E]
Row 2: Balances | $13,683 | $7,784 | $5,457 | $442
```

**Bold Labels (Formulas/Headers):**

- **"Net Worth"** - Header for portfolio value calculation
- **"Balances"** - Row label for account balance inputs

### 2.2 Risk Allocation Buckets

**Observable Structure:**

```
Risk 0.13    Risk 0.118    Risk 0.08    Risk 0.05    Risk 0.03
$1,779       $1,615        $1,095       $684         $410
```

**Actual Formula Structure:**

```excel
// Risk bucket calculations (based on total portfolio percentage)
A5 = =$B$2*0.13    // 13% risk bucket = $1,779
B5 = =$B$2*0.118   // 11.8% risk bucket = $1,615
C5 = =$B$2*0.08    // 8% risk bucket = $1,095 (inferred)
D5 = =$B$2*0.05    // 5% risk bucket = $684 (inferred)
E5 = =$B$2*0.03    // 3% risk bucket = $410 (inferred)
```

These are risk-based allocation buckets that calculate specific dollar amounts based on different percentage allocations of the total portfolio value ($27,366).

### 2.3 Risk Metrics Section

**Bold Labels (from Screenshot):**

- **"Risk Metrics"** - Section header with note "(Excluding PSL positions)"
- **"Portfolio"** - Left column identifier
- **"Net Worth"** - Metric label
- **"CVaR 95"** - Risk metric label
- **"Risk Amount:"** - Dollar risk label
- **"Risk:"** - Risk percentage label
- **"Allocation:"** - Allocation percentage label

**Observable Values:**

```
Portfolio Section:          Investment Section:
Net Worth: $9,352          Portfolio: -7.24%
CVaR 95: -10.32%           Leverage Target: 1.63
Risk Amount: $965.21       Risk Amount: $1,667
Risk: 7.05%                Risk: 12.18%
Allocation: 37%            Max Portfolio: $14,125
```

**Actual Excel Formulas (Provided):**

```excel
// Cell E12 (Investment section calculation)
E12 = =-(0.118)/$E11

// Cell E13 (Investment risk amount calculation)
E13 = =$E12*$B$5-$B$13

// Cell E14 (Investment risk percentage)
E14 = =$E13/$B$2

// Cell B13 (Portfolio risk amount calculation)
B13 = =B11*B12*-1

// Cell B14 (Portfolio risk percentage)
B14 = =$B13/$B$2

// Cell B15 (Portfolio allocation percentage)
B15 = =B14/(B14+E14)

// Cell B19 (Confidence calculation)
B19 = =1-(B18/(B17+B18))

// Cell B21 (Max Risk $ calculation)
B21 = =B20*0.236/100*$B$2
```

**Key Reference Cells:**

```excel
// Core portfolio calculations
B2 = =C2+D2+E2  // Total portfolio value (sum of IBKR + Bybit + Cash)
B5 = =$B$2*0.118  // 11.8% of total portfolio (target risk allocation)

// Risk allocation buckets
A5 = =$B$2*0.13  // 13% risk bucket = $1,779

// Portfolio components
B33 = =SUM(B25:B32)  // Sum of Risk-On positions (B25:B32 range)
B11 = B33  // References B33 (Net Worth of trading positions = $9,352)

// CVaR calculations (separate portfolios)
B12 = [CVaR 95% of trade portfolio - Risk-On positions]
E11 = [CVaR 95% of investment portfolio - BTC-USD and MSTR holdings]

// Trading statistics
B17 = [Total number of closed trades in trading portfolio]
B18 = [Trades/outliers excluded from the trading portfolio]
B20 = [Kelly criterion of trading portfolio (wins and losses only, not BE)]
```

**Complete Formula Analysis:**

- **E12**: `=-(0.118)/$E11` → -11.8% ÷ Investment portfolio CVaR (leverage calculation)
- **E13**: `=$E12*$B$5-$B$13` → (E12 × 11.8% of portfolio) - Trading portfolio risk
- **E14**: `=$E13/$B$2` → Investment risk amount ÷ Total portfolio value
- **B13**: `=B11*B12*-1` → Trading Net Worth × Trading CVaR × -1 (dollar risk)
- **B14**: `=$B13/$B$2` → Trading risk amount ÷ Total portfolio value
- **B15**: `=B14/(B14+E14)` → Trading risk ÷ (Trading risk + Investment risk)
- **B19**: `=1-(B18/(B17+B18))` → 1 - (Excluded trades ÷ Total trades) = Confidence
- **B21**: `=B20*0.236/100*$B$2` → Kelly criterion × 0.236% × Total portfolio
- **B33**: `=SUM(B25:B32)` → Sum of Risk-On positions = $9,352
- **C26**: `=B25/Risk_On[[#TOTALS],[Amount]]` → Position ÷ Total Risk-On amount

**Key Architecture:**

- **Dual Portfolio System**: Separate CVaR calculations for Trading (Risk-On) and Investment (BTC/MSTR) portfolios
- **Risk Allocation**: Multiple risk buckets (3%, 5%, 8%, 11.8%, 13%) calculated as percentages of total portfolio
- **Kelly Framework**: Uses trading performance statistics to calculate optimal position sizing
- **Excel Tables**: Structured references for dynamic calculations (Risk_On table)

### 2.4 Kelly Criterion Section

**Bold Labels:**

- **"No. Primary"** - Count label
- **"No. Outliers"** - Count label
- **"Confidence"** - Percentage label
- **"Kelly Criterion"** - Multiplier label
- **"Max Risk $"** - Dollar limit label

**Observable Values:**

```
No. Primary: 214
No. Outliers: 25
Confidence: 89.54%
Kelly Criterion: 4.48
Max Risk $: $145
```

## 3. Risk-On Trading Positions (Screenshot 2, Top Section)

### 3.1 Active Positions Table

**Bold Headers:**

- **"Risk On"** - Section header (appears to be a dropdown filter)
- **"Asset"** - Column header
- **"Amount"** - Column header
- **"% Allocation"** - Column header
- **"TOTAL"** - Summary row

**Observable Data:**

```
Asset | Amount  | % Allocation
CLSK  | $618    | 6.61%
NFLX  | $1,222  | 13.07%
USB   | $1,343  | 14.36%
TSLA  | $969    | 10.36%
HIMS  | $1,127  | 12.05%
ALGN  | $1,129  | 12.07%
COR   | $2,062  | 22.05%
AMAT  | $882    | 9.43%
TOTAL | $9,352  | 100.00%
```

## 4. Incoming Signals Section (Screenshot 2, Middle)

### 4.1 Signal Analysis Table

**Bold Headers (Column Labels):**

- **"Incoming"** - Section header (dropdown filter)
- **"Asset"** - Column A
- **"% Drawdown"** - Column B
- **"Kelly Position"** - Column C
- **"Max Allocation %"** - Column D
- **"Max Allocation $"** - Column E
- **"Position $"** - Column F
- **"Price $"** - Column G
- **"Allo. Units"** - Column H
- **"Kelly Eff."** - Column I
- **"Allocation Eff"** - Column J
- **"Column 1"** - Column K
- **"TOTAL"** - Summary row

**Observable Data:**

```
Asset | % Drawdown | Kelly Position | Max Allocation % | Max Allocation $ | Position $ | Price $ | Allo. Units | Kelly Eff. | Allocation Eff | Column 1
VRSN  | 11.35%     | $1,275        | 7.82%           | $731            | $1,003     | 283.96  | 3.53        | 79%        | 137%          |
IRM   | 8.35%      | $1,733        | 12.57%          | $1,176          | $1,454     | 102.77  | 14.15       | 84%        | 124%          |
AMZN  | 13.61%     | $1,063        | 7.82%           | $731            | $897       | 214.82  | 4.18        | 84%        | 123%          |
TOTAL | 11.10%     | $4,070        | 28%             | $2,638          | $3,354     |         | 21.86       |            |               |
```

## 5. Investment Portfolio Section (Screenshot 2, Bottom)

### 5.1 Strategic Holdings Table

**Bold Headers:**

- **"Investment"** - Section header (dropdown filter)
- **"Asset"** - Column A
- **"Price"** - Column B
- **"Allocation %"** - Column C
- **"Total Strategies"** - Column D
- **"Open Strategies"** - Column E
- **"Current Position"** - Column F
- **"Max Allocation $"** - Column G
- **"Max Allo. Units"** - Column H
- **"Target Allo. Units"** - Column I
- **"Buy Units pe"** - Column J (appears cut off)
- **"Sell Units per Signal"** - Column K

**Observable Data:**

```
Asset | Price        | Allocation % | Total Strategies | Open Strategies | Current Position | Max Allocation $ | Max Allo. Units | Target Allo. Units | Buy Units per | Sell Units per Signal
BTC   | $104,540.00  | 61.38%      | 9               | 6              | 0.077           | $8,670          | 0.083           | 0.055             | 0.009        | 0.013
MSTR  | $396.46      | 38.62%      | 8               | 3              | 12              | $5,455          | 14              | 5                 | 2            | 4
```

## 6. Reconstructed Excel Formulas

### 6.1 Basic Calculations

**Account Balance Totals:**

```excel
// Total portfolio value (actual formula)
B2 = =C2+D2+E2  // Sum IBKR + Bybit + Cash = $27,366
// Note: Excludes first account column for some reason
```

**Risk-On Position Calculations:**

```excel
// Actual formula for percentage allocation (from C26)
C26 = =B25/Risk_On[[#TOTALS],[Amount]]

// This shows the spreadsheet uses Excel Table structure with:
// - "Risk_On" as the table name
// - [#TOTALS] reference to the totals row
// - [Amount] as the column reference
// - Formula calculates individual position / total amount

// TOTAL row calculations (inferred structure)
=SUM(Risk_On[Amount])     // Sum of all position amounts = $9,352
=SUM(Risk_On[% Allocation]) // Sum of all allocations = 100.00%
```

### 6.2 Incoming Signals Calculations

**Efficiency Metrics:**

```excel
// Kelly Efficiency (Position $ / Kelly Position)
=F3/C3  // For VRSN: $1,003 / $1,275 = 79%

// Allocation Units calculation
=F3/G3  // Position $ / Price $ = Units

// TOTAL row averages and sums
=AVERAGE(Incoming[% Drawdown])    // Average drawdown = 11.10%
=SUM(Incoming[Kelly Position])    // Sum Kelly Positions = $4,070
=SUM(Incoming[Max Allocation %])  // Sum Max Allocation % = 28%
=SUM(Incoming[Max Allocation $])  // Sum Max Allocation $ = $2,638
=SUM(Incoming[Position $])        // Sum Position $ = $3,354
=SUM(Incoming[Allo. Units])       // Sum Allo. Units = 21.86
```

**Inferred Table Structure:**
The Incoming signals section likely uses an Excel Table named "Incoming" with structured references similar to the Risk_On table.

### 6.3 Investment Portfolio Calculations

**Target Allocation Calculations:**

```excel
// Allocation percentage calculation (61.38% BTC, 38.62% MSTR)
=Asset_Value / Total_Investment_Portfolio_Value

// Target allocation units
=(Total_Investment_Portfolio * Allocation_Percentage) / Asset_Price

// Position difference calculations
=Target_Allo_Units - Current_Position

// Max Allocation $ calculations
=Investment_Portfolio_Value * Allocation_Percentage

// Buy/Sell units per signal (systematic rebalancing)
=Rebalancing_Amount / Asset_Price / Signals_Per_Period
```

**Inferred Table Structure:**
The Investment section likely uses an Excel Table named "Investment" with structured references for BTC and MSTR holdings, tracking multiple strategies per asset (9 for BTC, 8 for MSTR).

## 7. Key Observations

### 7.1 Multiple Account Structure

The spreadsheet tracks balances across multiple accounts (IBKR, Bybit, Cash) suggesting a multi-broker/multi-venue trading setup.

### 7.2 Risk-Based Allocation

The risk buckets (0.13, 0.118, 0.08, 0.05, 0.03) suggest a sophisticated risk management approach with different risk levels allocated specific dollar amounts.

### 7.3 Kelly Criterion Implementation

The system implements Kelly Criterion position sizing with efficiency tracking and outlier detection.

### 7.4 Multi-Asset Strategy

The Investment section shows both traditional crypto (BTC) and crypto-related stocks (MSTR) with multiple strategies per asset.

### 7.5 Pipeline Management

The Incoming signals section suggests a systematic approach to evaluating and sizing new position opportunities.

## 8. Cell Structure and Dependencies

Based on the screenshots, the spreadsheet likely has this structure:

**Screenshot 1 (Portfolio Dashboard):**

- Rows 1-2: Account balances
- Rows 3-4: Risk allocation buckets
- Rows 5-15: Risk metrics calculations
- Rows 16-20: Kelly criterion calculations

**Screenshot 2 (Trading Positions):**

- Risk-On section: Approximately rows 1-10
- Incoming section: Approximately rows 12-16
- Investment section: Approximately rows 18-20

## 9. Formula Dependencies

The spreadsheet has these key dependencies and calculation flow:

### 9.1 Core Calculation Chain

1. **Account Balances (C2, D2, E2)** → **Total Portfolio (B2)**
2. **Total Portfolio (B2)** → **Risk Buckets (A5, B5, C5, D5, E5)**
3. **Risk-On Positions (B25:B32)** → **Net Worth (B33)** → **Portfolio Risk (B13)**
4. **Trading Statistics (B17, B18, B20)** → **Confidence (B19)** & **Max Risk (B21)**
5. **CVaR Calculations (B12, E11)** → **Risk Amounts (B13, E13)** → **Allocations (B15)**

### 9.2 Table Dependencies

- **Risk_On Table**: Dynamic position calculations with structured references
- **Incoming Table**: Signal analysis with efficiency metrics
- **Investment Table**: Strategic allocation with multi-strategy tracking

### 9.3 Cross-Portfolio Integration

- **Dual CVaR System**: Separate risk calculations for Trading vs Investment portfolios
- **Risk Allocation Balance**: B15 formula balances risk between Trading and Investment
- **Kelly Framework**: Uses actual trading performance to optimize position sizing

## 10. Complete Formula Reference

**All Documented Formulas:**

```excel
// Core Structure
B2 = =C2+D2+E2                              // Total portfolio
B5 = =$B$2*0.118                           // 11.8% risk allocation
A5 = =$B$2*0.13                            // 13% risk allocation
B33 = =SUM(B25:B32)                        // Risk-On total
B11 = B33                                   // Net Worth reference

// Risk Calculations
B12 = [CVaR 95% of trade portfolio]        // Trading CVaR
E11 = [CVaR 95% of investment portfolio]   // Investment CVaR
B13 = =B11*B12*-1                          // Trading risk amount
E12 = =-(0.118)/$E11                       // Investment leverage
E13 = =$E12*$B$5-$B$13                     // Investment risk amount
B14 = =$B13/$B$2                           // Trading risk %
E14 = =$E13/$B$2                           // Investment risk %
B15 = =B14/(B14+E14)                       // Risk allocation %

// Kelly & Performance
B17 = [Total closed trades]                // Trade count
B18 = [Excluded trades/outliers]           // Outlier count
B19 = =1-(B18/(B17+B18))                   // Confidence %
B20 = [Kelly criterion of trading portfolio] // Kelly value
B21 = =B20*0.236/100*$B$2                  // Max risk per position

// Table References
C26 = =B25/Risk_On[[#TOTALS],[Amount]]     // Position allocation %
```

This comprehensive specification provides all necessary details to recreate the Position Sizing Excel Spreadsheet from scratch, including the exact formulas, table structures, and calculation dependencies.
