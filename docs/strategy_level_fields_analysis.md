# Strategy-Level Fields Analysis

## Overview

This document analyzes fields that pertain to the strategy as a whole (multiple positions) vs. individual position-level data for the trade_history CSV schema design.

## Strategy-Level Fields (Multiple Positions)

These fields should be considered for a separate strategy_performance table/file:

### Performance Aggregates

- `Total_Return` - Cumulative return across all positions
- `Total_Trades` - Count of all trades in strategy
- `Win_Rate` - Overall success rate across all positions
- `Sharpe_Ratio` - Risk-adjusted return metric for entire strategy
- `Max_Drawdown` - Worst portfolio-level decline
- `Profit_Factor` - Ratio of gross profits to gross losses

### Trade Analytics (Strategy-Wide)

- `Avg_Trade_Duration` - Average holding period across all positions
- `Avg_Winner` - Average return of winning trades
- `Avg_Loser` - Average return of losing trades
- `Best_Trade` - Single best performing trade return
- `Worst_Trade` - Single worst performing trade return

### Trade Distribution Counts

- `Big_Winner_Count` - Count of trades classified as "Big Winner"
- `Big_Loser_Count` - Count of trades classified as "Big Loser"
- `Winner_Count` - Count of profitable trades
- `Loser_Count` - Count of losing trades
- `Breakeven_Count` - Count of neutral trades

### Rolling Metrics (Strategy-Wide)

- `Rolling_Win_Rate` - Recent performance window win rate
- `Rolling_Avg_Return` - Recent performance window average return

### Metadata

- `Export_Timestamp` - When the strategy analysis was exported

## Position-Level Fields (Individual Trades)

These fields are appropriate for the trade_history CSV:

### Position Identification

- `Position_UUID` - Unique identifier: `{Ticker}_{Strategy_Type}_{Short_Window}_{Long_Window}_{Signal_Window}_{Last_Position_Open_Date}`
- `Ticker` - Asset symbol
- `Strategy_Type` - SMA/EMA/MACD
- `Short_Window` - Strategy parameter
- `Long_Window` - Strategy parameter
- `Signal_Window` - Strategy parameter (0 for SMA/EMA)

### Position Execution

- `Entry_Timestamp` - Position open date/time
- `Exit_Timestamp` - Position close date/time (null if open)
- `Avg_Entry_Price` - Average price of entry orders
- `Avg_Exit_Price` - Average price of exit orders
- `Position_Size` - Number of shares/units
- `Direction` - Long/Short

### Position Performance

- `PnL` - Profit/Loss in currency units
- `Return` - Percentage return on position
- `Duration_Days` - Holding period in days
- `Trade_Type` - Classification: Big Winner, Winner, Breakeven, Loser, Big Loser
- `Status` - Open/Closed

### Risk Metrics (Position-Specific)

- `Max_Favourable_Excursion` - Best unrealized profit during position
- `Max_Adverse_Excursion` - Worst unrealized loss during position
- `MFE_MAE_Ratio` - Efficiency metric for individual position
- `Exit_Efficiency` - (Final PnL / MFE) for closed positions

### Current Position Data (Open Positions Only)

- `Days_Since_Entry` - Days position has been held
- `Current_Unrealized_PnL` - Current unrealized profit/loss
- `Current_Excursion_Status` - Current vs entry price analysis

## Recommendations

### Trade History CSV Schema

Focus on individual position data with unique identifiers, enabling position-level analysis and risk management.

### Future Strategy Performance Table

Create separate schema for strategy-level aggregates, enabling strategy comparison and selection.

### Data Relationship

- One strategy can have many positions (1:N relationship)
- Strategy UUID: `{Ticker}_{Strategy_Type}_{Short_Window}_{Long_Window}_{Signal_Window}`
- Position UUID: `{Strategy_UUID}_{Entry_Date}`

This separation enables both position-level risk management and strategy-level performance evaluation while maintaining data integrity and avoiding redundancy.
