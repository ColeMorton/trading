# analyze_portfolio

Comprehensive quantitative analysis of strategy backtest data with professional portfolio assessment

## Purpose

Generates professional quantitative analysis reports from strategy backtest data, leveraging the existing concurrency analysis framework. Provides risk metrics, performance analysis, correlation assessment, and actionable trading recommendations. Includes specialized portfolio enhancement analysis when assessing incoming positions against existing trades.

## Parameters

- `csv_file`: Path to CSV file containing strategy backtest data (required)
  - Must contain columns: Ticker, Strategy Type, Score, Win Rate, Total Return, etc.
  - CSV files are located in `./csv/strategies/` directory
  - Can specify filename only (e.g., `trades.csv`) or full path
- `incoming_csv`: Path to incoming CSV file for portfolio enhancement analysis (optional)
  - Only applicable when base file is `trades.csv`
  - Triggers specialized analysis of adding new positions to existing portfolio
  - Also located in `./csv/strategies/` directory

## Process

1. **File Validation**: Verify CSV file exists and contains required strategy performance columns
2. **JSON Lookup**: Search for corresponding JSON file in `./json/concurrency/` directory (same basename)
3. **Data Loading**: Load strategy data using existing CSV loader infrastructure
4. **Quantitative Analysis**:
   - Performance metrics analysis (scores, win rates, returns)
   - Risk assessment (drawdowns, volatility, VaR)
   - Correlation analysis between strategies
   - Concurrency analysis (if JSON data available)
   - Monte Carlo simulation analysis (if monte_carlo data available in JSON)
   - Signal quality assessment
5. **Portfolio Enhancement** (conditional):
   - If base file is `trades.csv` and `incoming_csv` provided
   - Assess impact of adding incoming positions to existing portfolio
   - Risk contribution analysis
   - Correlation impact evaluation
   - Portfolio optimization recommendations
6. **Report Generation**: Professional analysis report with:
   - Executive summary with key findings
   - Strategy performance ranking and analysis
   - Risk metrics and downside protection assessment
   - Diversification analysis
   - Actionable recommendations for portfolio management

## Usage

```bash
# Basic analysis (CSV files are automatically located in ./csv/strategies/)
/project:analyze_portfolio trades.csv

# Portfolio enhancement analysis
/project:analyze_portfolio trades.csv incoming.csv

# Analysis with full path
/project:analyze_portfolio ./csv/strategies/trades.csv ./csv/strategies/incoming.csv
```

## Output Format

- **Executive Summary**: Key findings and recommendations
- **Performance Analysis**: Strategy rankings, metrics, and efficiency scores
- **Risk Assessment**: VaR, drawdowns, correlation risks
- **Monte Carlo Analysis**: Simulation results, confidence intervals, and robustness metrics
- **Portfolio Insights**: Concurrency analysis, diversification benefits
- **Enhancement Analysis**: (if applicable) Impact assessment of adding new positions
- **Actionable Recommendations**: Specific trading and risk management guidance

## Dependencies

- Existing concurrency analysis framework (`app/concurrency/`)
- Strategy data in standardized CSV format (located in `./csv/strategies/`)
- Optional: Corresponding JSON files for enhanced analysis (located in `./json/concurrency/`)

## Error Handling

- Graceful handling of missing JSON files (analysis continues with available data)
- Validation of CSV format and required columns
- Clear error messages for file path issues
- Fallback analysis when enhanced data unavailable

## File Locations

- **CSV Files**: `./csv/strategies/` - Contains strategy backtest data files
- **JSON Files**: `./json/concurrency/` - Contains enhanced analysis data (optional)
- **Output**: Analysis results are displayed in terminal

## Notes

- Leverages existing quantitative analysis infrastructure
- Provides professional-grade analysis suitable for trading decisions
- Monte Carlo analysis includes bootstrap sampling, confidence intervals, and robustness testing
- Specialized logic for portfolio enhancement when base file is `trades.csv`
- Analysis depth depends on available data (CSV + optional JSON)
- Designed for quantitative traders requiring comprehensive portfolio assessment with statistical validation
- Command automatically searches for CSV files in `./csv/strategies/` if only filename provided
- JSON lookup performed automatically in `./json/concurrency/` based on CSV basename
