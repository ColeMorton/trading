# Comprehensive Portfolio Analysis Report

**Analysis Date:** 2025-01-24
**Portfolios Analyzed:** trades.csv (13 strategies) & incoming.csv (6 strategies)

---

## Executive Summary

### Portfolio Performance Comparison

| Metric            | Trades Portfolio | Incoming Portfolio | Difference |
| ----------------- | ---------------- | ------------------ | ---------- |
| **Total Return**  | 30,783.75%       | 21,514.88%         | +9,268.86% |
| **Sharpe Ratio**  | 0.825            | 0.710              | +0.114     |
| **Sortino Ratio** | 1.310            | 1.090              | +0.220     |
| **Win Rate**      | 51.30%           | 55.78%             | -4.47%     |
| **Max Drawdown**  | 64.41%           | 62.74%             | +1.67%     |

**Key Finding:** Trades portfolio outperforms incoming portfolio in risk-adjusted returns despite lower win rates.

---

## 1. Strategy Performance Rankings

### Trades Portfolio - Top 5 Performers

#### By Score

1. **NFLX (SMA 82/83)** - Score: 1.74
2. **AMAT (SMA 64/77)** - Score: 1.70
3. **AMZN (SMA 51/69)** - Score: 1.55
4. **BLDR (SMA 50/51)** - Score: 1.54
5. **ALGN (SMA 13/39)** - Score: 1.52

#### By Total Return

1. **AMAT (SMA 64/77)** - 222,479.20%
2. **NFLX (SMA 82/83)** - 49,451.63%
3. **AMZN (SMA 51/69)** - 48,576.67%
4. **ALGN (SMA 13/39)** - 37,563.59%
5. **TSLA (SMA 4/39)** - 17,929.52%

#### By Sharpe Ratio

1. **TSLA (SMA 4/39)** - 1.25
2. **HWM (SMA 7/9)** - 1.06
3. **NFLX (SMA 82/83)** - 1.02
4. **ALGN (SMA 13/39)** - 0.96
5. **AMZN (SMA 51/69)** - 0.88

### Incoming Portfolio - Top 5 Performers

#### By Score

1. **AXON (SMA 84/86)** - Score: 1.63
2. **ASML (SMA 71/74)** - Score: 1.61
3. **WELL (SMA 64/76)** - Score: 1.57
4. **RJF (SMA 68/77)** - Score: 1.56
5. **FITB (SMA 20/88)** - Score: 1.29

#### By Total Return

1. **AXON (SMA 84/86)** - 55,786.97%
2. **ASML (SMA 71/74)** - 49,339.80%
3. **RJF (SMA 68/77)** - 8,999.01%
4. **FITB (SMA 20/88)** - 7,827.40%
5. **WELL (SMA 64/76)** - 5,694.46%

---

## 2. Risk-Adjusted Metrics Analysis

### Sharpe Ratio Distribution

- **Trades Portfolio Mean:** 0.825 (StDev: 0.215)
- **Incoming Portfolio Mean:** 0.710 (StDev: 0.148)
- **Statistical Significance:** Not significant (p=0.302)
- **Effect Size:** Medium (Cohen's d=0.532)

### Sortino Ratio Distribution

- **Trades Portfolio Mean:** 1.310 (StDev: 0.348)
- **Incoming Portfolio Mean:** 1.090 (StDev: 0.347)
- **Statistical Significance:** Not significant (p=0.219)
- **Effect Size:** Medium-Large (Cohen's d=0.631)

### Calmar Ratio Distribution

- **Trades Portfolio Mean:** 0.526 (StDev: 0.255)
- **Incoming Portfolio Mean:** 0.360 (StDev: 0.255)
- **Statistical Significance:** Not significant (p=0.241)
- **Effect Size:** Medium-Large (Cohen's d=0.651)

---

## 3. Drawdown Analysis

### Maximum Drawdown Statistics

#### Trades Portfolio

- **Mean:** 64.41%
- **Median:** 63.30%
- **Maximum:** 90.21% (GME)
- **Strategies >50% DD:** 9/13 (69.2%)
- **Strategies >75% DD:** 5/13 (38.5%)

#### Incoming Portfolio

- **Mean:** 62.74%
- **Median:** 61.54%
- **Maximum:** 83.78% (AXON)
- **Strategies >50% DD:** 6/6 (100%)
- **Strategies >75% DD:** 2/6 (33.3%)

### Key Risk Insight

All strategies show substantial drawdowns >50%, indicating high-risk, high-reward profiles typical of trend-following strategies.

---

## 4. Trade Frequency & Expectancy Analysis

### Trade Frequency Metrics

#### Trades Portfolio

- **Average Total Trades:** 100.8
- **Average Trades/Month:** 0.34
- **Trade Duration Range:** 8 days (HWM) to 97 days (USB)

#### Incoming Portfolio

- **Average Total Trades:** 100.7
- **Average Trades/Month:** 0.26
- **Trade Duration Range:** 37 days (AXON) to 95 days (FITB)

### Expectancy Analysis

#### Trades Portfolio

- **Positive Expectancy:** 13/13 strategies (100%)
- **Mean Expectancy/Trade:** 9.63
- **Mean Expectancy/Month:** 2.84

#### Incoming Portfolio

- **Positive Expectancy:** 6/6 strategies (100%)
- **Mean Expectancy/Trade:** 11.96
- **Mean Expectancy/Month:** 3.55

**Key Finding:** All strategies demonstrate positive expectancy, with incoming portfolio showing higher expectancy per trade.

---

## 5. Statistical Significance Testing

### Performance Differences (Trades vs Incoming)

| Metric        | T-Test p-value | Mann-Whitney p-value | Significance    | Effect Size   |
| ------------- | -------------- | -------------------- | --------------- | ------------- |
| Score         | 0.447          | 0.323                | Not Significant | Small (-0.39) |
| Win Rate      | 0.125          | 0.136                | Not Significant | Large (-0.86) |
| Total Return  | 0.725          | 0.416                | Not Significant | Small (0.20)  |
| Sharpe Ratio  | 0.302          | 0.282                | Not Significant | Medium (0.53) |
| Sortino Ratio | 0.219          | 0.179                | Not Significant | Large (0.63)  |

**Key Finding:** No statistically significant differences between portfolios due to small sample sizes, but effect sizes suggest meaningful practical differences.

---

## 6. Strategy Type & Parameter Analysis

### Strategy Distribution

- **All Strategies:** 100% Simple Moving Average (SMA)
- **Signal Usage:** Mixed (some use entry/exit signals, others don't)

### Window Parameter Analysis

#### Short Window Distribution

- **Trades Portfolio:** Range 4-82, Mean: 38.5, Median: 28
- **Incoming Portfolio:** Range 20-84, Mean: 63.5, Median: 68

#### Long Window Distribution

- **Trades Portfolio:** Range 9-88, Mean: 53.5, Median: 51
- **Incoming Portfolio:** Range 74-88, Mean: 80.2, Median: 77

#### Window Spread Analysis

- **Trades Portfolio:** Mean spread: 15.0 days
- **Incoming Portfolio:** Mean spread: 16.7 days

**Key Finding:** Incoming portfolio uses significantly longer moving averages, potentially capturing longer-term trends.

---

## 7. Top & Bottom Performers

### Standout Winners

#### Exceptional Returns (>100,000%)

1. **AMAT (Trades)** - 222,479% return, 1.70 score
2. **AXON (Incoming)** - 55,787% return, 1.63 score
3. **ASML (Incoming)** - 49,340% return, 1.61 score
4. **NFLX (Trades)** - 49,452% return, 1.74 score

#### Best Risk-Adjusted Performance

1. **TSLA (Trades)** - Sharpe: 1.25, Sortino: 1.99
2. **HWM (Trades)** - Sharpe: 1.06, Sortino: 1.60
3. **NFLX (Trades)** - Sharpe: 1.02, Sortino: 1.63

### Concerning Performers

#### High Risk Contributors

1. **GME (Trades)** - 90.2% max drawdown, high volatility
2. **AXON (Incoming)** - 83.8% max drawdown despite strong returns
3. **FITB (Incoming)** - 77.0% max drawdown, lower returns

---

## 8. Portfolio-Level Metrics

### Diversification Analysis

#### Trades Portfolio

- **Unique Tickers:** 13
- **Strategy Types:** 1 (SMA)
- **Sector Concentration:** Technology-heavy

#### Incoming Portfolio

- **Unique Tickers:** 6
- **Strategy Types:** 1 (SMA)
- **Sector Concentration:** More diversified (Finance, Healthcare, Tech)

### Portfolio Risk Contribution

#### Highest Risk Contributors (Trades)

1. **GME** - Extreme volatility, gaming sector
2. **TSLA** - High beta, EV sector volatility
3. **AMAT** - Semiconductor cyclicality

#### Optimal Risk-Return Candidates

- **NFLX:** High return, manageable risk
- **AMZN:** Strong fundamentals, reasonable drawdown
- **AXON:** Exceptional growth, acceptable risk profile

---

## 9. Trading Decision Insights

### Portfolio Optimization Recommendations

#### Immediate Actions

1. **Reduce GME exposure** - 90.2% drawdown risk too high
2. **Increase AXON/ASML allocation** - Strong risk-adjusted performance
3. **Consider NFLX/AMZN core positions** - Consistent performers

#### Parameter Optimization

1. **Test longer MA windows** - Incoming portfolio's approach shows merit
2. **Implement stop-losses** - Only some strategies use them currently
3. **Evaluate signal timing** - Mixed results on entry/exit signals

#### Risk Management

1. **Position sizing based on drawdown** - Limit high-DD strategies to <5%
2. **Correlation analysis** - Avoid concentration in tech sector
3. **Rebalancing frequency** - Consider monthly rebalancing based on performance metrics

### Strategy Selection Criteria

#### Essential Metrics Threshold

- **Minimum Sharpe Ratio:** >0.8
- **Maximum Drawdown:** <70%
- **Minimum Win Rate:** >45%
- **Positive Expectancy:** Required

#### Preferred Characteristics

- **Score >1.5:** Indicates strong overall performance
- **Sortino >1.2:** Good downside risk management
- **Trade frequency:** 0.2-0.5 trades/month for reasonable activity

---

## 10. Risk Assessment Summary

### Overall Portfolio Risk Profile

- **High-Risk, High-Reward:** Both portfolios show aggressive return profiles
- **Trend-Following Nature:** SMA strategies capture major trends but suffer during reversals
- **Drawdown Tolerance Required:** Investors need 70%+ drawdown tolerance
- **Long-Term Horizon:** Strategies require multi-year commitment for best results

### Recommended Portfolio Allocation

#### Conservative Approach (50% allocation)

- NFLX (15%), AMZN (10%), AXON (10%), ASML (10%), RJF (5%)

#### Aggressive Approach (100% allocation)

- AMAT (20%), NFLX (15%), AMZN (15%), AXON (15%), ASML (15%), WELL (10%), ALGN (10%)

#### Risk Budget Allocation

- **Core Holdings (60%):** NFLX, AMZN, AXON, ASML
- **Growth Positions (30%):** AMAT, WELL, ALGN, RJF
- **Speculative (10%):** TSLA, remaining positions

---

## Conclusion

The analysis reveals strong performance from both portfolios, with the trades portfolio showing superior risk-adjusted returns despite lower win rates. The incoming portfolio demonstrates better expectancy metrics and more conservative parameter selection.

**Key strategic recommendations:**

1. Combine best strategies from both portfolios
2. Implement position sizing based on risk contribution
3. Consider longer MA windows for trend capture
4. Maintain strict risk management with drawdown limits

Both portfolios require sophisticated risk management and patient capital due to their high-drawdown, trend-following nature.
