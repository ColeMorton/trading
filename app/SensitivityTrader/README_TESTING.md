# SensitivityTrader Testing Guide

## Puppeteer E2E Testing

This directory contains end-to-end tests for the SensitivityTrader application using Puppeteer.

### BXP Analysis Test

The `test_bxp_puppeteer.js` test verifies the complete MA Cross analysis workflow for BXP ticker.

#### Test Coverage

The test performs the following verification steps:

1. **Navigation & Setup**
   - Loads SensitivityTrader at `http://localhost:5000`
   - Verifies page loads correctly

2. **Configuration**
   - Sets ticker input to "BXP"
   - Ensures "Use Current Price" is enabled (default)
   - Maintains other default settings

3. **Analysis Execution**
   - Clicks "Run Analysis" button
   - Verifies loading spinner appears and disappears
   - Waits for analysis completion

4. **Result Verification**
   - Checks that results table appears with data
   - Verifies first result matches expected: **BXP SMA 34/43/0**
   - Validates all result fields (ticker, strategy type, windows)

5. **CSV Export Verification**
   - Confirms CSV files are exported to:
     - `/csv/portfolios/20250529/BXP_D_SMA.csv`
     - `/csv/portfolios_filtered/20250529/BXP_D_SMA.csv`
     - `/csv/portfolios_best/20250529/BXP_*_D.csv` (dynamic timestamp)

#### Prerequisites

1. **Install Dependencies**
   ```bash
   cd app/SensitivityTrader
   npm install
   ```

2. **Start API Server**
   ```bash
   # From project root
   python -m app.api.run
   ```

3. **Start SensitivityTrader**
   ```bash
   # From project root
   python app/SensitivityTrader/main.py
   ```

   The application should be running on `http://localhost:5000`

#### Running the Test

```bash
# Run the BXP analysis test
npm run test:bxp

# Or run directly
node test_bxp_puppeteer.js
```

#### Expected Output

The test will provide detailed console output showing:
- ✅ Successful steps
- ❌ Failed steps  
- ⚠️ Warnings or partial matches
- 📊 Analysis results data
- 📁 CSV file verification status
- 📸 Screenshot capture notifications

#### Screenshots

The test automatically captures timestamped screenshots at key points:

1. **01_page_loaded** - Initial SensitivityTrader page load
2. **02_configuration_complete** - BXP ticker configured with Use Current enabled
3. **03_analysis_started** - Analysis button clicked, processing started
4. **04_loading_spinner** - Loading spinner visible during analysis
5. **05_results_table** - Results table displayed after analysis completion
6. **06_bxp_result_found** - BXP SMA 34/43/0 result successfully identified
7. **07_test_complete** - Final test state with all results
8. **99_error_state** - Captured on any test failure (if possible)

Screenshots are saved to: `app/SensitivityTrader/screenshots/`
Filename format: `[timestamp]_[step]_[description].png`

#### Test Configuration

**Expected Result:**
- Ticker: BXP
- Strategy: SMA
- Short Window: 34
- Long Window: 43
- Signal Window: 0

**Browser Settings:**
- Runs in non-headless mode for debugging (set `headless: true` for CI)
- 1280x720 viewport
- 30-second timeout for operations

#### Troubleshooting

**Common Issues:**

1. **Connection Refused**
   - Ensure SensitivityTrader is running on port 5000
   - Check that API server is running on port 8000

2. **Expected Result Mismatch**
   - BXP signals may change with market data
   - Test will continue CSV verification even if result differs
   - Check current signals in `/csv/ma_cross/current_signals/`

3. **CSV Files Not Found**
   - Ensure proper file permissions
   - Check that analysis completed successfully
   - Verify date-based subdirectories exist

4. **Puppeteer Browser Issues**
   - Install Chrome/Chromium if not available
   - Run with `--no-sandbox` flags if in container

#### File Cleanup

The test automatically cleans up previous BXP CSV files before running to ensure fresh results.

## Development Notes

- Test uses live market data (no mocking)
- Expected result (SMA 34/43/0) is based on current market conditions for BXP
- CSV export verification ensures the complete MA Cross pipeline works end-to-end
- Test provides comprehensive logging for debugging issues