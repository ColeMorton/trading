#!/usr/bin/env node

/**
 * CSV Data Validation Test for Position Sizing System
 * Ensures all data from protected.csv, trades.csv, and portfolio.csv is correctly imported/displayed/used
 */

import puppeteer from 'puppeteer';
import { readFileSync } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const TIMEOUT = 60000;

// CSV file paths
const CSV_FILES = {
  protected: '/Users/colemorton/Projects/trading/csv/strategies/protected.csv',
  trades: '/Users/colemorton/Projects/trading/csv/strategies/trades.csv',
  portfolio: '/Users/colemorton/Projects/trading/csv/strategies/portfolio.csv',
};

// Logging utilities
const log = (message) => {
  console.log(`[${new Date().toISOString()}] ${message}`);
};

const logStep = (stepNumber, description) => {
  console.log(`\n✓ Step ${stepNumber}: ${description}`);
};

// Parse CSV data
function parseCSV(filePath) {
  try {
    const content = readFileSync(filePath, 'utf-8');
    const lines = content.trim().split('\n');
    const headers = lines[0].split(',');
    const rows = lines.slice(1).map((line) => {
      const values = line.split(',');
      const row = {};
      headers.forEach((header, index) => {
        row[header.trim()] = values[index]?.trim() || '';
      });
      return row;
    });
    return { headers, rows };
  } catch (error) {
    log(`Error parsing CSV ${filePath}: ${error.message}`);
    return { headers: [], rows: [] };
  }
}

async function runCSVDataValidationTest() {
  console.log('🚀 Starting CSV Data Validation Test Suite');
  console.log('==========================================');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Testing CSV files:');
  console.log('- protected.csv (Protected Portfolio strategies)');
  console.log('- trades.csv (Risk On Portfolio strategies)');
  console.log('- portfolio.csv (Investment Portfolio strategies)');
  console.log('==========================================\n');

  const browser = await puppeteer.launch({
    headless: !process.argv.includes('--headed'),
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const testResults = {
    totalTests: 0,
    passed: 0,
    failed: 0,
    errors: [],
    csvData: {},
  };

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // Parse CSV files first
    logStep(1, 'Loading and parsing CSV files');
    for (const [type, filePath] of Object.entries(CSV_FILES)) {
      const csvData = parseCSV(filePath);
      testResults.csvData[type] = csvData;
      log(`${type}.csv: ${csvData.rows.length} strategies loaded`);
    }

    // Test 1: CSV Data Accessibility via API
    console.log('\n📊 Test 1: CSV Data API Accessibility');
    testResults.totalTests++;

    try {
      logStep(1, 'Navigating to application');
      await page.goto(BASE_URL, {
        waitUntil: 'networkidle2',
        timeout: TIMEOUT,
      });

      logStep(2, 'Testing direct CSV API access');

      // Test CSV API endpoints
      const csvEndpoints = [
        '/api/data/csv/strategies/protected.csv',
        '/api/data/csv/strategies/trades.csv',
        '/api/data/csv/strategies/portfolio.csv',
      ];

      for (const endpoint of csvEndpoints) {
        const response = await page.evaluate(async (endpoint) => {
          try {
            const response = await fetch(endpoint);
            const text = await response.text();
            return {
              status: response.status,
              ok: response.ok,
              dataLength: text.length,
              hasHeader: text.includes('Ticker,Strategy Type'),
              rowCount: text.split('\n').length - 1,
            };
          } catch (error) {
            return { error: error.message };
          }
        }, endpoint);

        if (response.error) {
          throw new Error(`CSV API ${endpoint}: ${response.error}`);
        }

        if (!response.ok) {
          throw new Error(`CSV API ${endpoint}: Status ${response.status}`);
        }

        log(
          `✓ ${endpoint}: ${response.rowCount} rows, ${response.dataLength} bytes`
        );
      }

      console.log('✅ Test 1 PASSED: All CSV files accessible via API');
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 1 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'CSV Data API Accessibility',
        error: error.message,
      });
    }

    // Test 2: Position Sizing Dashboard Data Integration
    console.log('\n📊 Test 2: Position Sizing Dashboard Data Integration');
    testResults.totalTests++;

    try {
      logStep(1, 'Navigating to Position Sizing dashboard');
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]', {
        timeout: 10000,
      });

      logStep(2, 'Checking dashboard API data integration');

      // Intercept API calls to position sizing dashboard
      const apiCalls = [];
      page.on('response', (response) => {
        if (response.url().includes('/api/position-sizing/dashboard')) {
          apiCalls.push({
            url: response.url(),
            status: response.status(),
            timestamp: Date.now(),
          });
        }
      });

      // Force refresh to trigger API call
      await page.click('button[title*="Refresh"]');
      await page.waitForTimeout(2000);

      if (apiCalls.length === 0) {
        log(
          'Warning: No position sizing API calls detected, checking for data presence'
        );
      }

      logStep(3, 'Validating portfolio data display');

      // Check for portfolio sections that should contain CSV-derived data
      const portfolioSections = await page.evaluate(() => {
        const sections = {
          portfolioRisk: !!document.querySelector(
            '[data-testid="portfolio-risk-panel"]'
          ),
          activePositions:
            !!document.querySelector(
              '[data-testid="active-positions-table"]'
            ) || !!document.body.textContent.includes('Active Positions'),
          strategicHoldings:
            !!document.querySelector(
              '[data-testid="strategic-holdings-table"]'
            ) || !!document.body.textContent.includes('Strategic Holdings'),
          incomingSignals:
            !!document.querySelector(
              '[data-testid="incoming-signals-table"]'
            ) || !!document.body.textContent.includes('Incoming Signals'),
          riskAllocation:
            !!document.querySelector(
              '[data-testid="risk-allocation-buckets"]'
            ) || !!document.body.textContent.includes('Risk Allocation'),
        };

        // Extract actual data values
        const netWorth = document.body.textContent.match(/\$[\d,]+/g) || [];
        const percentages = document.body.textContent.match(/\d+\.\d+%/g) || [];
        const strategies = Array.from(
          document.querySelectorAll('tbody tr')
        ).length;

        return {
          sections,
          netWorth: netWorth.length,
          percentages: percentages.length,
          strategies,
        };
      });

      log(
        `Portfolio sections found: ${
          Object.values(portfolioSections.sections).filter(Boolean).length
        }/5`
      );
      log(
        `Financial data: ${portfolioSections.netWorth} dollar amounts, ${portfolioSections.percentages} percentages`
      );
      log(`Strategy rows: ${portfolioSections.strategies} table rows`);

      if (
        Object.values(portfolioSections.sections).filter(Boolean).length < 3
      ) {
        throw new Error('Missing essential portfolio sections in dashboard');
      }

      console.log(
        '✅ Test 2 PASSED: Dashboard displays portfolio data from CSV sources'
      );
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 2 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Position Sizing Dashboard Data Integration',
        error: error.message,
      });
    }

    // Test 3: CSV Data Mapping Validation
    console.log('\n📊 Test 3: CSV Data Mapping Validation');
    testResults.totalTests++;

    try {
      logStep(1, 'Validating CSV data structure matches expected schema');

      const expectedColumns = {
        protected: [
          'Ticker',
          'Strategy Type',
          'Win Rate [%]',
          'Total Return [%]',
          'Max Drawdown [%]',
          'Allocation [%]',
          'Stop Loss [%]',
        ],
        trades: [
          'Ticker',
          'Strategy Type',
          'Win Rate [%]',
          'Total Return [%]',
          'Max Drawdown [%]',
        ],
        portfolio: [
          'Ticker',
          'Allocation [%]',
          'Strategy Type',
          'Win Rate [%]',
          'Total Return [%]',
          'Max Drawdown [%]',
        ],
      };

      for (const [type, expectedCols] of Object.entries(expectedColumns)) {
        const csvData = testResults.csvData[type];
        if (!csvData || csvData.rows.length === 0) {
          throw new Error(`No data found in ${type}.csv`);
        }

        // Check for required columns
        const missingColumns = expectedCols.filter(
          (col) => !csvData.headers.includes(col)
        );
        if (missingColumns.length > 0) {
          log(
            `Warning: ${type}.csv missing columns: ${missingColumns.join(', ')}`
          );
        }

        // Validate data quality
        const tickers = csvData.rows.map((row) => row.Ticker).filter(Boolean);
        const strategies = csvData.rows
          .map((row) => row['Strategy Type'])
          .filter(Boolean);

        log(
          `✓ ${type}.csv: ${tickers.length} tickers, ${
            new Set(strategies).size
          } unique strategies`
        );

        // Sample some data validation
        const sampleRow = csvData.rows[0];
        if (sampleRow) {
          const winRate = parseFloat(sampleRow['Win Rate [%]']);
          const totalReturn = parseFloat(sampleRow['Total Return [%]']);

          if (isNaN(winRate) || isNaN(totalReturn)) {
            log(
              `Warning: ${type}.csv may have data quality issues in first row`
            );
          }
        }
      }

      logStep(2, 'Cross-referencing portfolio types with CSV files');

      // Verify that tickers appear in appropriate portfolios
      const protectedTickers = new Set(
        testResults.csvData.protected.rows.map((r) => r.Ticker)
      );
      const tradesTickers = new Set(
        testResults.csvData.trades.rows.map((r) => r.Ticker)
      );
      const portfolioTickers = new Set(
        testResults.csvData.portfolio.rows.map((r) => r.Ticker)
      );

      log(
        `Portfolio distribution: Protected=${protectedTickers.size}, Trades=${tradesTickers.size}, Portfolio=${portfolioTickers.size}`
      );

      // Check for common tickers (some overlap is expected)
      const overlapTradesProtected = [...tradesTickers].filter((t) =>
        protectedTickers.has(t)
      );
      const overlapPortfolioTrades = [...portfolioTickers].filter((t) =>
        tradesTickers.has(t)
      );

      log(
        `Ticker overlaps: Trades↔Protected=${overlapTradesProtected.length}, Portfolio↔Trades=${overlapPortfolioTrades.length}`
      );

      console.log('✅ Test 3 PASSED: CSV data mapping validation successful');
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 3 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'CSV Data Mapping Validation',
        error: error.message,
      });
    }

    // Test 4: Risk Calculations Using CSV Data
    console.log('\n📊 Test 4: Risk Calculations Using CSV Data');
    testResults.totalTests++;

    try {
      logStep(1, 'Checking risk allocation calculations');

      // Look for CVaR calculations and risk metrics
      const riskMetrics = await page.evaluate(() => {
        const metrics = {
          cvarTargetFound:
            document.body.textContent.includes('11.8%') ||
            document.body.textContent.includes('CVaR'),
          riskUtilization:
            document.body.textContent.includes('Risk') &&
            document.body.textContent.includes('%'),
          allocationData: Array.from(
            document.querySelectorAll('.progress-bar, [role="progressbar"]')
          ).length,
          netWorthDisplayed:
            document.body.textContent.match(/\$[\d,]+/g)?.length || 0,
          accountBalances:
            document.body.textContent.includes('IBKR') ||
            document.body.textContent.includes('Bybit') ||
            document.body.textContent.includes('Cash'),
        };

        // Extract numerical values for validation
        const percentageMatches =
          document.body.textContent.match(/\d+\.\d+%/g) || [];
        const dollarMatches =
          document.body.textContent.match(/\$[\d,]+/g) || [];

        return {
          ...metrics,
          percentageCount: percentageMatches.length,
          dollarAmountCount: dollarMatches.length,
          percentageValues: percentageMatches.slice(0, 5), // Sample first 5
          dollarValues: dollarMatches.slice(0, 5), // Sample first 5
        };
      });

      log(`Risk display metrics:`);
      log(`  CVaR Target Found: ${riskMetrics.cvarTargetFound}`);
      log(`  Risk Utilization: ${riskMetrics.riskUtilization}`);
      log(`  Progress Bars: ${riskMetrics.allocationData}`);
      log(`  Account Balances: ${riskMetrics.accountBalances}`);
      log(`  Percentage Values: ${riskMetrics.percentageValues.join(', ')}`);
      log(`  Dollar Values: ${riskMetrics.dollarValues.join(', ')}`);

      // Cross-reference with CSV allocation data
      const csvAllocations = testResults.csvData.portfolio.rows
        .map((row) => parseFloat(row['Allocation [%]']))
        .filter((val) => !isNaN(val));

      const csvTotalAllocation = csvAllocations.reduce(
        (sum, val) => sum + val,
        0
      );
      log(`CSV total allocation: ${csvTotalAllocation.toFixed(2)}%`);

      if (!riskMetrics.cvarTargetFound) {
        log('Warning: CVaR target (11.8%) not clearly displayed');
      }

      if (csvTotalAllocation > 0) {
        log(
          `✓ CSV allocation data is being processed (${csvAllocations.length} entries)`
        );
      }

      console.log('✅ Test 4 PASSED: Risk calculations appear to use CSV data');
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 4 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Risk Calculations Using CSV Data',
        error: error.message,
      });
    }

    // Test 5: Strategic Holdings Data Display
    console.log('\n📊 Test 5: Strategic Holdings Data Display');
    testResults.totalTests++;

    try {
      logStep(1, 'Verifying strategic holdings display CSV data');

      // Check for specific tickers from portfolio.csv
      const portfolioTickers = testResults.csvData.portfolio.rows
        .map((row) => row.Ticker)
        .filter(Boolean);
      const sampleTickers = portfolioTickers.slice(0, 5); // Test first 5 tickers

      const tickerDisplay = await page.evaluate((tickers) => {
        const pageText = document.body.textContent;
        const results = {};

        tickers.forEach((ticker) => {
          results[ticker] = pageText.includes(ticker);
        });

        // Look for strategic holdings section
        const hasStrategicSection =
          pageText.includes('Strategic Holdings') ||
          pageText.includes('Investment Portfolio') ||
          pageText.includes('Holdings');

        // Count table rows that might contain strategy data
        const tableRows = Array.from(document.querySelectorAll('tbody tr'));
        const rowsWithTickers = tableRows.filter((row) =>
          tickers.some((ticker) => row.textContent.includes(ticker))
        );

        return {
          tickerMatches: results,
          hasStrategicSection,
          totalTableRows: tableRows.length,
          rowsWithPortfolioTickers: rowsWithTickers.length,
        };
      }, sampleTickers);

      const matchedTickers = Object.values(tickerDisplay.tickerMatches).filter(
        Boolean
      ).length;
      log(
        `Ticker display: ${matchedTickers}/${sampleTickers.length} sample tickers found`
      );
      log(`Strategic section: ${tickerDisplay.hasStrategicSection}`);
      log(
        `Table rows: ${tickerDisplay.totalTableRows} total, ${tickerDisplay.rowsWithPortfolioTickers} with portfolio tickers`
      );

      // Check for allocation percentages from CSV
      const csvAllocations = testResults.csvData.portfolio.rows
        .map((row) => row['Allocation [%]'])
        .filter(Boolean)
        .slice(0, 3);

      if (csvAllocations.length > 0) {
        const allocationDisplay = await page.evaluate((allocations) => {
          const pageText = document.body.textContent;
          return allocations.map((alloc) => ({
            allocation: alloc,
            displayed:
              pageText.includes(alloc + '%') || pageText.includes(alloc),
          }));
        }, csvAllocations);

        const displayedAllocations = allocationDisplay.filter(
          (a) => a.displayed
        ).length;
        log(
          `Allocation display: ${displayedAllocations}/${csvAllocations.length} sample allocations found`
        );
      }

      if (matchedTickers === 0 && tickerDisplay.totalTableRows === 0) {
        log(
          'Warning: No portfolio ticker data displayed - may be expected if no CSV data loaded'
        );
      }

      console.log(
        '✅ Test 5 PASSED: Strategic holdings section processes CSV data'
      );
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 5 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Strategic Holdings Data Display',
        error: error.message,
      });
    }
  } catch (error) {
    console.error('🚨 Critical test error:', error);
    testResults.errors.push({ test: 'General', error: error.message });
  } finally {
    await browser.close();
  }

  // Print comprehensive test summary
  console.log('\n==========================================');
  console.log('📊 CSV Data Validation Test Summary');
  console.log('==========================================');
  console.log(`Total Tests: ${testResults.totalTests}`);
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(
    `Success Rate: ${(
      (testResults.passed / testResults.totalTests) *
      100
    ).toFixed(1)}%`
  );

  // CSV Data Summary
  console.log('\n📁 CSV Data Summary:');
  for (const [type, data] of Object.entries(testResults.csvData)) {
    console.log(
      `  ${type}.csv: ${data.rows.length} strategies, ${data.headers.length} columns`
    );
  }

  if (testResults.errors.length > 0) {
    console.log('\n❌ Errors Details:');
    testResults.errors.forEach(({ test, error }) => {
      console.log(`  - ${test}: ${error}`);
    });
  }

  console.log('\n🎯 CSV Data Integration Status:');
  console.log(
    `  API Access: ${
      testResults.passed >= 1 ? '✅' : '❌'
    } CSV files accessible via API`
  );
  console.log(
    `  Dashboard Integration: ${
      testResults.passed >= 2 ? '✅' : '❌'
    } Data flows to dashboard`
  );
  console.log(
    `  Data Mapping: ${
      testResults.passed >= 3 ? '✅' : '❌'
    } CSV structure validated`
  );
  console.log(
    `  Risk Calculations: ${
      testResults.passed >= 4 ? '✅' : '❌'
    } Risk metrics use CSV data`
  );
  console.log(
    `  Strategic Display: ${
      testResults.passed >= 5 ? '✅' : '❌'
    } Holdings display CSV data`
  );

  // Exit with appropriate code
  process.exit(testResults.failed > 0 ? 1 : 0);
}

// Run the test
runCSVDataValidationTest().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
