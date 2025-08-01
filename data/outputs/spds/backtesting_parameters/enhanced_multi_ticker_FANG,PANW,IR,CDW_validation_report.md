# Backtesting Parameter Validation Report

## Generation Summary

- **Generation Date:** 2025-07-25T15:35:03.131763
- **Total Strategies:** 4
- **Confidence Level:** 0.9
- **SPDS Version:** 1.0.0

## Parameter Validity Assessment

| Validity Level | Count | Percentage |
| -------------- | ----- | ---------- |
| HIGH           | 4     | 100.0%     |
| MEDIUM         | 0     | 0.0%       |
| LOW            | 0     | 0.0%       |

## Statistical Summary

- **Average Sample Size:** 344.0
- **Average Confidence:** 90.0%

## Framework Compatibility

✅ **VectorBT**: Compatible with parameter dictionary format
✅ **Backtrader**: Strategy class templates generated
✅ **Zipline**: Algorithm templates generated
✅ **Generic CSV/JSON**: Exported for custom frameworks

## Recommendations

### High Validity Parameters (4 strategies)

These parameters are derived from robust statistical analysis with sample sizes ≥30 and high confidence levels. Recommended for production backtesting.

### Medium Validity Parameters (0 strategies)

These parameters have moderate statistical support. Use with additional validation and consider paper trading before live deployment.

### Low Validity Parameters (0 strategies)

These parameters have limited statistical support. Not recommended for production use without significant additional validation.

## Usage Guidelines

1. **Parameter Interpretation:**

   - Take Profit %: Percentile-based profit target
   - Stop Loss %: Risk management threshold
   - Max Holding Days: Time-based exit criteria
   - Trailing Stop %: Volatility-adjusted trailing stop

2. **Implementation Notes:**

   - Parameters are derived from historical statistical analysis
   - Consider market regime changes when applying parameters
   - Monitor parameter performance and adjust as needed

3. **Validation Recommendations:**
   - Backtest parameters on out-of-sample data
   - Compare performance against baseline strategies
   - Monitor parameter stability over time

## Export Details

- **VectorBT File:** Python dictionary format for direct import
- **Backtrader File:** Complete strategy class templates
- **Zipline File:** Algorithm template with exit logic
- **CSV File:** Tabular format for batch processing
- **JSON File:** Structured format with metadata
