# Position Sizing Manual Data Entry - User Manual

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Kelly Criterion Management](#kelly-criterion-management)
4. [Position Entry and Management](#position-entry-and-management)
5. [Portfolio Transitions](#portfolio-transitions)
6. [Risk Allocation Monitoring](#risk-allocation-monitoring)
7. [Advanced Analytics](#advanced-analytics)
8. [CSV Data Management](#csv-data-management)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

## Overview

The Position Sizing Manual Data Entry system enhances your existing trading workflow by adding manual data entry capabilities while maintaining full backward compatibility with your CSV-based strategy analysis.

### Key Features

- **Manual Position Size Entry**: Specify exact position sizes in USD
- **Entry Date Tracking**: Record when positions were opened
- **Kelly Criterion Management**: Input values from your trading journal
- **Portfolio Lifecycle**: Track positions from Risk On → Protected → Investment
- **Real-time Risk Monitoring**: Monitor against 11.8% CVaR target
- **Advanced Analytics**: Scenario analysis and performance visualization

### Portfolio Types

- **Risk On Portfolio (trades.csv)**: New daily trend-following positions with stop losses
- **Protected Portfolio (protected.csv)**: Positions where stop loss has moved to entry price
- **Investment Portfolio (portfolio.csv)**: Long-term strategic holdings

## Getting Started

### Accessing the System

1. Open the Sensylate application
2. Click on "Position Sizing" in the navigation menu
3. The dashboard will load with your current portfolio data

### Dashboard Overview

The main dashboard provides:

- **Portfolio Risk Panel**: Overall risk metrics and Kelly Criterion
- **Risk Allocation Buckets**: Current risk utilization vs 11.8% target
- **Active Positions Table**: All current positions with inline editing
- **Incoming Signals**: New trading opportunities
- **Strategic Holdings**: Long-term investment positions

## Kelly Criterion Management

### Purpose

The Kelly Criterion determines optimal position sizing based on your trading edge and win rate. This value comes from your external trading journal analysis.

### Updating Kelly Criterion

1. Locate the "Kelly Criterion" section on the dashboard
2. Enter your Kelly value (0.0 to 1.0) from your trading journal
3. Select the source:
   - **Trading Journal**: Value calculated from historical performance
   - **Manual**: Manually estimated value
   - **Calculated**: System-calculated value
4. Add notes about the calculation or timeframe
5. Click "Save Changes"

### Best Practices

- Update Kelly values quarterly or after significant strategy changes
- Document the analysis period in the notes field
- Use conservative estimates when uncertain
- Typical values range from 0.10 to 0.25 for most strategies

## Position Entry and Management

### Adding New Positions

#### Method 1: Position Entry Modal

1. Click the "Add Position" button
2. Fill in the position details:
   - **Symbol**: Stock ticker or crypto pair (e.g., AAPL, BTC-USD)
   - **Position Size**: USD amount invested
   - **Entry Date**: When the position was opened
   - **Status**: Active, Closed, or Pending
   - **Stop Status**: Risk or Protected
   - **Portfolio**: Risk On, Protected, or Investment
   - **Notes**: Optional notes about the trade
3. Click "Add Position"

#### Method 2: CSV Upload

1. Export your current portfolio CSV
2. Add manual entry columns:
   - Manual Position Size
   - Manual Entry Date
   - Current Status
   - Stop Status
   - Notes
3. Import the updated CSV

### Editing Existing Positions

1. In the Active Positions table, hover over any field
2. Click the edit icon that appears
3. Modify the value inline
4. Press Enter or click the checkmark to save
5. Press Escape or click X to cancel

### Position Status Management

- **Active**: Position is currently open
- **Closed**: Position has been closed
- **Pending**: Position order placed but not filled

### Stop Status Tracking

- **Risk**: Position still at original stop loss level
- **Protected**: Stop loss moved to entry price (breakeven)

## Portfolio Transitions

### Understanding the Lifecycle

Positions naturally progress through three portfolios:

1. **Risk On → Protected**: When stop loss moves to entry price
2. **Protected → Investment**: When position becomes long-term holding

### Executing Transitions

#### Risk On to Protected

1. Identify positions in Risk On portfolio with "Risk" stop status
2. When your stop loss moves to entry price:
   - Click the "Protect" button next to the position
   - Review the confirmation dialog
   - Confirm the transition
3. Position moves to Protected portfolio with "Protected" status

#### Protected to Investment

1. For positions you want to hold long-term:
   - Click the "Invest" button in Protected portfolio
   - Confirm the transition to Investment portfolio
2. Position becomes a strategic holding

### Important Notes

- Transitions update your CSV files automatically
- Transitions cannot be easily reversed
- Only positions with correct status can be transitioned

## Risk Allocation Monitoring

### Understanding the 11.8% Target

The system uses a fixed 11.8% CVaR (Conditional Value at Risk) target, which represents the maximum portfolio risk allocation.

### Risk Utilization Display

- **Current CVaR**: Your actual portfolio risk level
- **Utilization**: Percentage of the 11.8% target being used
- **Available Risk**: Remaining risk capacity
- **Risk Amount**: Dollar amount at risk

### Risk Level Indicators

- 🟢 **Conservative (<70%)**: Room for additional positions
- 🟡 **Moderate (70-90%)**: Careful position sizing required
- 🔴 **High (>90%)**: Consider reducing positions

### Real-time Alerts

The system monitors risk levels and provides alerts when:

- Risk utilization exceeds 80% (Warning)
- Risk utilization exceeds 100% (Critical)
- Risk utilization exceeds 120% (Excessive)

### Alert Configuration

1. Click the settings icon in Risk Monitoring section
2. Adjust alert thresholds:
   - Warning Level (default: 80%)
   - Critical Level (default: 100%)
   - Excessive Level (default: 120%)
3. Save settings

## Advanced Analytics

### Risk Trend Analysis

View historical risk allocation trends:

1. Select "Trend" chart view
2. Choose time range: 1D, 7D, 30D, 90D
3. Analyze CVaR changes over time
4. Identify risk patterns and trends

### Portfolio Composition Analysis

Understand portfolio breakdown:

1. Select "Composition" view
2. Choose analysis type:
   - By Portfolio (Risk On, Protected, Investment)
   - By Position Size (Large, Medium, Small)
   - By Status (Active, Closed, Pending)
3. Review pie chart and bar chart visualizations

### Scenario Analysis

Test portfolio resilience:

1. Access the Scenario Analyzer
2. Choose scenario type:
   - **Mild Stress**: 10% market decline
   - **Moderate Correction**: 20% market decline
   - **Severe Crisis**: 40% market decline
   - **Custom**: Set your own parameters
3. Click "Run Scenario Analysis"
4. Review results:
   - Projected portfolio loss
   - Updated CVaR estimates
   - Worst-case position impacts
   - Risk management recommendations

### Custom Scenario Parameters

- **Market Stress Level**: Expected market decline (0-60%)
- **Correlation Increase**: How much correlations increase during stress (0-100%)
- **Volatility Multiplier**: Volatility increase factor (1-5x)
- **Liquidity Impact**: Additional spread/slippage (0-20%)

## CSV Data Management

### Enhanced CSV Format

The system adds optional columns to your existing CSV files:

- **Manual Position Size**: USD position size
- **Manual Entry Date**: Position entry date (YYYY-MM-DD)
- **Current Status**: Active/Closed/Pending
- **Stop Status**: Risk/Protected
- **Notes**: Additional information

### Backward Compatibility

- Existing CSV files work without modification
- Enhanced columns are added automatically when needed
- Legacy systems continue to function normally

### Export/Import Process

1. **Export**: Download enhanced CSV with all manual data
2. **Edit**: Modify in Excel or text editor
3. **Import**: Upload updated CSV to sync changes
4. **Validate**: System validates data integrity

### File Locations

- **trades.csv**: Risk On Portfolio positions
- **protected.csv**: Protected Portfolio positions
- **portfolio.csv**: Investment Portfolio positions

## Troubleshooting

### Common Issues

#### Kelly Criterion Won't Save

- Ensure value is between 0.0 and 1.0
- Check internet connection
- Try refreshing the page and re-entering

#### Position Entry Validation Errors

- **Symbol**: Must contain only letters, numbers, and hyphens
- **Position Size**: Must be positive number
- **Entry Date**: Cannot be in the future
- **Required Fields**: Symbol and position size are mandatory

#### Chart Loading Issues

- Refresh the browser page
- Check if data is available for the selected time range
- Try switching chart types (pie chart vs bar chart)

#### CSV Import Failures

- Verify CSV format is correct
- Check for special characters in data
- Ensure file size is under 10MB
- Validate date formats (YYYY-MM-DD)

### Performance Issues

If the system feels slow:

1. Close other browser tabs
2. Clear browser cache
3. Check internet connection speed
4. Try using Chrome or Firefox

### Data Sync Issues

If data doesn't appear correctly:

1. Click the "Refresh" button on the dashboard
2. Check if CSV files are properly formatted
3. Verify backend API is responding
4. Contact support if issues persist

## FAQ

### General Questions

**Q: Will this system replace my existing CSV workflow?**
A: No, it enhances your existing workflow. All CSV files remain compatible and functional.

**Q: Can I still use the system if I don't enter manual data?**
A: Yes, the system works with your existing strategy data. Manual entry is optional.

**Q: How often should I update the Kelly Criterion?**
A: Quarterly or after significant changes to your trading strategy performance.

### Technical Questions

**Q: What happens if I lose internet connection?**
A: The system will use cached data and allow you to continue working. Changes will sync when connection is restored.

**Q: Can I export all my data?**
A: Yes, you can export enhanced CSV files containing all your manual entries and strategy data.

**Q: Is my trading data secure?**
A: Yes, all data is encrypted in transit and stored securely. The system follows financial industry security standards.

### Risk Management Questions

**Q: What does the 11.8% CVaR target mean?**
A: It's the maximum portfolio risk level, representing the expected loss in the worst 5% of scenarios.

**Q: Should I always fill my risk allocation to 11.8%?**
A: Not necessarily. Use 70-90% utilization for normal operations, keeping some capacity for opportunities.

**Q: What happens if I exceed the risk target?**
A: The system will alert you and recommend reducing position sizes or closing some positions.

### Portfolio Questions

**Q: When should I transition positions from Risk On to Protected?**
A: When your stop loss moves to entry price (breakeven), protecting your capital.

**Q: Can I move positions directly from Risk On to Investment?**
A: No, positions must go through Protected status first, following the proper risk management lifecycle.

**Q: What's the difference between the three portfolios?**
A: Risk On (new positions with risk), Protected (breakeven positions), Investment (long-term holds).

## Support

For additional help:

- Check the troubleshooting section above
- Review system alerts and error messages
- Contact your system administrator
- Refer to the technical documentation for developers

---

_This manual covers the Position Sizing Manual Data Entry system. For technical implementation details, see the developer documentation._
