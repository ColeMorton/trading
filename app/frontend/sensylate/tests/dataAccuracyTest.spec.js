import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Data Accuracy Test for Sensylate Parameter Testing
 *
 * Tests the specific issues reported:
 * 1. Expectancy (per trade) returns 782.34 where it should be 7.06
 * 2. Avg Trade Duration = N/A where it should be 67 days 05:16:29.010989010
 * 3. Metric Type (concatenated) was missing
 * 4. No CSV file was exported to @csv/portfolios_best/
 *
 * Reference: USLM,SMA,55,80 in @csv/portfolios_filtered/20250605/USLM_D_SMA.csv
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:5173';
const API_BASE_URL = 'http://localhost:8000';
const TIMEOUT = 120000; // 2 minutes for API calls
const SCREENSHOT_DIR = path.join(__dirname, '../screenshots');

// Expected values from reference data USLM,SMA,55,80
const EXPECTED_VALUES = {
  ticker: 'USLM',
  strategy_type: 'SMA',
  short_window: 55,
  long_window: 80,
  expectancy_per_trade: 7.057303121782205, // Should show as 7.06
  avg_trade_duration: '67 days 05:16:29.010989010',
  metric_type: 'Most Expectancy', // One of the metric types for this config
};

const TAKE_SCREENSHOTS = process.argv.includes('--screenshots');
const VERBOSE =
  process.argv.includes('--verbose') || process.argv.includes('--debug');

console.log(`🔬 Sensylate Data Accuracy Test`);
console.log(`📷 Screenshots: ${TAKE_SCREENSHOTS ? 'ENABLED' : 'DISABLED'}`);
console.log(`🔊 Verbose: ${VERBOSE ? 'ENABLED' : 'DISABLED'}`);
console.log(`🎯 Frontend URL: ${BASE_URL}`);
console.log(`🎯 API URL: ${API_BASE_URL}`);

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function log(message) {
  if (VERBOSE) {
    console.log(`   ${message}`);
  }
}

async function takeScreenshot(page, filename, description) {
  if (!TAKE_SCREENSHOTS) return null;

  try {
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const screenshotPath = path.join(
      SCREENSHOT_DIR,
      `data_accuracy_${timestamp}_${filename}.png`
    );

    await page.screenshot({
      path: screenshotPath,
      fullPage: true,
      captureBeyondViewport: true,
    });

    console.log(`📸 Screenshot: ${filename} - ${description}`);
    return screenshotPath;
  } catch (error) {
    console.log(`❌ Screenshot failed for ${filename}: ${error.message}`);
    return null;
  }
}

async function waitForElement(page, selector, options = {}) {
  const timeout = options.timeout || TIMEOUT;
  try {
    await page.waitForSelector(selector, { timeout, ...options });
    return true;
  } catch (error) {
    console.log(`⚠️ Element not found: ${selector} (timeout: ${timeout}ms)`);
    return false;
  }
}

async function testDirectAPICall() {
  console.log('\n🔍 Test 1: Direct API Call');
  console.log('============================');

  const testResults = {
    apiCallSuccess: false,
    correctDataValues: false,
    expectancyCorrect: false,
    avgTradeDurationCorrect: false,
    metricTypePresent: false,
  };

  try {
    // Make direct API call to test backend
    const apiUrl = `${API_BASE_URL}/api/ma-cross/analyze`;
    const requestBody = {
      ticker: EXPECTED_VALUES.ticker,
      windows: 89, // Max window to ensure 55,80 combination is tested
      strategy_types: [EXPECTED_VALUES.strategy_type],
      direction: 'Long',
      use_current: false, // Important: don't filter by current signals
      refresh: true, // Force fresh analysis
    };

    console.log('🔄 Making direct API call...');
    console.log('📤 Request:', JSON.stringify(requestBody, null, 2));

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(
        `API call failed: ${response.status} ${response.statusText}`
      );
    }

    const data = await response.json();
    testResults.apiCallSuccess = true;
    console.log('✅ API call successful');

    log(`📊 Response status: ${data.status}`);
    log(`📊 Total portfolios: ${data.portfolios?.length || 0}`);

    if (data.portfolios && data.portfolios.length > 0) {
      // Find the specific USLM,SMA,55,80 combination
      const targetPortfolio = data.portfolios.find(
        (p) =>
          p.ticker === EXPECTED_VALUES.ticker &&
          p.strategy_type === EXPECTED_VALUES.strategy_type &&
          p.short_window === EXPECTED_VALUES.short_window &&
          p.long_window === EXPECTED_VALUES.long_window
      );

      if (targetPortfolio) {
        console.log('🎯 Found target portfolio USLM,SMA,55,80');
        log('📋 Portfolio data:');
        log(JSON.stringify(targetPortfolio, null, 2));

        // Test expectancy_per_trade value
        const expectancyValue =
          targetPortfolio.expectancy_per_trade || targetPortfolio.expectancy;
        console.log(
          `💰 Expectancy per trade: ${expectancyValue} (expected: ${EXPECTED_VALUES.expectancy_per_trade})`
        );

        if (
          Math.abs(expectancyValue - EXPECTED_VALUES.expectancy_per_trade) <
          0.01
        ) {
          testResults.expectancyCorrect = true;
          console.log('✅ Expectancy per trade value is correct');
        } else {
          console.log('❌ Expectancy per trade value is INCORRECT');
          console.log(`   Expected: ${EXPECTED_VALUES.expectancy_per_trade}`);
          console.log(`   Got: ${expectancyValue}`);
        }

        // Test avg_trade_duration
        const avgTradeDuration = targetPortfolio.avg_trade_duration;
        console.log(
          `⏱️ Avg Trade Duration: "${avgTradeDuration}" (expected: "${EXPECTED_VALUES.avg_trade_duration}")`
        );

        if (avgTradeDuration === EXPECTED_VALUES.avg_trade_duration) {
          testResults.avgTradeDurationCorrect = true;
          console.log('✅ Avg Trade Duration is correct');
        } else {
          console.log('❌ Avg Trade Duration is INCORRECT');
          console.log(`   Expected: "${EXPECTED_VALUES.avg_trade_duration}"`);
          console.log(`   Got: "${avgTradeDuration}"`);
        }

        // Test metric_type presence
        const metricType = targetPortfolio.metric_type;
        console.log(`🏷️ Metric Type: "${metricType}"`);

        if (metricType && metricType.trim() !== '') {
          testResults.metricTypePresent = true;
          console.log('✅ Metric Type is present');
        } else {
          console.log('❌ Metric Type is MISSING');
        }

        testResults.correctDataValues =
          testResults.expectancyCorrect &&
          testResults.avgTradeDurationCorrect &&
          testResults.metricTypePresent;
      } else {
        console.log('❌ Target portfolio USLM,SMA,55,80 not found in results');
        log('Available portfolios:');
        data.portfolios.slice(0, 5).forEach((p) => {
          log(
            `  - ${p.ticker},${p.strategy_type},${p.short_window},${p.long_window}`
          );
        });
      }
    } else {
      console.log('❌ No portfolios returned from API');
    }
  } catch (error) {
    console.error('❌ Direct API test failed:', error.message);
    log('Error details:', error.stack);
  }

  return testResults;
}

async function testFrontendDisplay() {
  console.log('\n🖥️ Test 2: Frontend Display');
  console.log('==============================');

  const browser = await puppeteer.launch({
    headless: process.env.CI === 'true',
    defaultViewport: { width: 1280, height: 720 },
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const testResults = {
    navigationSuccess: false,
    analysisExecution: false,
    resultsDisplayed: false,
    expectancyDisplayCorrect: false,
    avgTradeDurationDisplayCorrect: false,
    metricTypeDisplayed: false,
    csvExportAvailable: false,
  };

  let page;
  try {
    page = await browser.newPage();

    // Enable console logging
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('🔴 Page Error:', msg.text());
      }
      if (VERBOSE && msg.type() === 'log') {
        log('Page Log: ' + msg.text());
      }
    });

    // Navigate to Parameter Testing
    console.log('🌐 Navigating to Sensylate...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });

    await takeScreenshot(page, '01_initial_load', 'Initial page load');

    // Click Parameter Testing button
    const parameterTestingClicked = await page.evaluate(() => {
      const button = Array.from(document.querySelectorAll('button')).find((b) =>
        b.textContent?.includes('Parameter Testing')
      );
      if (button) {
        button.click();
        return true;
      }
      return false;
    });

    if (!parameterTestingClicked) {
      throw new Error('Parameter Testing button not found');
    }

    await sleep(1000);
    testResults.navigationSuccess = true;
    console.log('✅ Navigated to Parameter Testing');

    await takeScreenshot(
      page,
      '02_parameter_testing',
      'Parameter Testing view'
    );

    // Configure analysis for USLM
    console.log('⚙️ Configuring analysis for USLM...');

    // Set ticker
    const tickerInput = await page.$('#ticker-input');
    if (tickerInput) {
      await tickerInput.click({ clickCount: 3 });
      await tickerInput.type(EXPECTED_VALUES.ticker);
      log('Set ticker to USLM');
    }

    // Set windows to include our target combination
    const windowsInput = await page.$('#windows-input');
    if (windowsInput) {
      await windowsInput.click({ clickCount: 3 });
      await windowsInput.type('89'); // Ensure 55,80 combination is tested
      log('Set windows to 89');
    }

    // Ensure SMA is selected
    const smaCheckbox = await page.$('#sma-checkbox');
    if (smaCheckbox) {
      const isChecked = await page.$eval('#sma-checkbox', (el) => el.checked);
      if (!isChecked) {
        await smaCheckbox.click();
      }
      log('Ensured SMA is selected');
    }

    // Uncheck USE_CURRENT to get all results
    const useCurrentCheckbox = await page.$('#use-current-checkbox');
    if (useCurrentCheckbox) {
      const isChecked = await page.$eval(
        '#use-current-checkbox',
        (el) => el.checked
      );
      if (isChecked) {
        await useCurrentCheckbox.click();
        log('Unchecked USE_CURRENT');
      }
    }

    // Check REFRESH to get fresh data
    const refreshCheckbox = await page.$('#refresh-checkbox');
    if (refreshCheckbox) {
      const isChecked = await page.$eval(
        '#refresh-checkbox',
        (el) => el.checked
      );
      if (!isChecked) {
        await refreshCheckbox.click();
        log('Checked REFRESH');
      }
    }

    await takeScreenshot(page, '03_configured', 'Analysis configured');

    // Run analysis
    console.log('🚀 Running analysis...');
    const runButton = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const runBtn = buttons.find((btn) =>
        btn.textContent?.includes('Run Analysis')
      );
      if (runBtn && !runBtn.disabled) {
        runBtn.click();
        return true;
      }
      return false;
    });

    if (!runButton) {
      throw new Error('Run Analysis button not found or disabled');
    }

    testResults.analysisExecution = true;
    console.log('✅ Analysis started');

    // Wait for results with extended timeout
    console.log('⏳ Waiting for results...');
    let resultsFound = false;
    let attempts = 0;
    const maxAttempts = 30; // 2 minutes total

    while (!resultsFound && attempts < maxAttempts) {
      await sleep(4000); // Check every 4 seconds
      attempts++;

      const hasResults = await page.evaluate(() => {
        // Look for results table
        const table = document.querySelector('table, .react-table');
        if (table) {
          const rows = table.querySelectorAll('tbody tr');
          return rows.length > 0;
        }
        return false;
      });

      if (hasResults) {
        resultsFound = true;
        break;
      }

      log(`Attempt ${attempts}/${maxAttempts} - No results yet...`);

      // Take occasional screenshots during wait
      if (attempts % 5 === 0) {
        await takeScreenshot(
          page,
          `04_waiting_${attempts}`,
          `Waiting for results - attempt ${attempts}`
        );
      }
    }

    if (!resultsFound) {
      throw new Error(
        `No results found after ${maxAttempts} attempts (${
          maxAttempts * 4
        } seconds)`
      );
    }

    testResults.resultsDisplayed = true;
    console.log('✅ Results displayed');

    await takeScreenshot(page, '05_results_displayed', 'Results are displayed');

    // Find and verify the USLM,SMA,55,80 row
    console.log('🔍 Looking for USLM,SMA,55,80 row...');

    const targetRowData = await page.evaluate((expected) => {
      const table = document.querySelector('table, .react-table');
      if (!table) return null;

      const rows = Array.from(table.querySelectorAll('tbody tr'));

      for (const row of rows) {
        const cells = Array.from(row.querySelectorAll('td'));
        if (cells.length === 0) continue;

        const cellTexts = cells.map((cell) => cell.textContent?.trim() || '');

        // Check if this row matches our target (USLM, SMA, 55, 80)
        const ticker = cellTexts[1]; // Assuming ticker is in column 1
        const strategy = cellTexts[2]; // Assuming strategy is in column 2
        const shortWindow = cellTexts[3]; // Assuming short window is in column 3
        const longWindow = cellTexts[4]; // Assuming long window is in column 4

        if (
          ticker === expected.ticker &&
          strategy === expected.strategy_type &&
          shortWindow === expected.short_window.toString() &&
          longWindow === expected.long_window.toString()
        ) {
          return {
            found: true,
            ticker,
            strategy,
            shortWindow,
            longWindow,
            expectancy: cellTexts[10], // Assuming expectancy is in column 10
            avgTradeDuration: cellTexts[11], // Assuming avg trade duration is in column 11
            rowTexts: cellTexts,
          };
        }
      }

      return { found: false, availableRows: rows.length };
    }, EXPECTED_VALUES);

    if (targetRowData?.found) {
      console.log('🎯 Found target row USLM,SMA,55,80');
      log('Row data:', targetRowData);

      // Check expectancy value
      const displayedExpectancy = parseFloat(targetRowData.expectancy);
      const expectedDisplayValue =
        Math.round(EXPECTED_VALUES.expectancy_per_trade * 100) / 100; // 7.06

      console.log(
        `💰 Displayed Expectancy: ${targetRowData.expectancy} (expected: ${expectedDisplayValue})`
      );

      if (Math.abs(displayedExpectancy - expectedDisplayValue) < 0.01) {
        testResults.expectancyDisplayCorrect = true;
        console.log('✅ Expectancy display is correct');
      } else {
        console.log('❌ Expectancy display is INCORRECT');
        console.log(`   Expected: ${expectedDisplayValue}`);
        console.log(`   Got: ${displayedExpectancy}`);
      }

      // Check avg trade duration
      console.log(
        `⏱️ Displayed Avg Trade Duration: "${targetRowData.avgTradeDuration}"`
      );

      if (
        targetRowData.avgTradeDuration === EXPECTED_VALUES.avg_trade_duration
      ) {
        testResults.avgTradeDurationDisplayCorrect = true;
        console.log('✅ Avg Trade Duration display is correct');
      } else if (targetRowData.avgTradeDuration === 'N/A') {
        console.log('❌ Avg Trade Duration shows N/A (should show duration)');
      } else {
        console.log('❌ Avg Trade Duration display is INCORRECT');
        console.log(`   Expected: "${EXPECTED_VALUES.avg_trade_duration}"`);
        console.log(`   Got: "${targetRowData.avgTradeDuration}"`);
      }

      // Test metric type by expanding the row
      console.log('🔍 Testing Metric Type display...');

      // Find and click the expand button for this row
      const metricTypeDisplayed = await page.evaluate(() => {
        const table = document.querySelector('table, .react-table');
        if (!table) return false;

        const rows = Array.from(table.querySelectorAll('tbody tr'));

        for (const row of rows) {
          const expandButton = row.querySelector(
            'button[title*="Expand"], button[title*="expand"]'
          );
          if (expandButton) {
            expandButton.click();

            // Wait a moment for expansion
            setTimeout(() => {
              // Look for metric type in expanded content
              const expandedRow = row.nextElementSibling;
              if (
                expandedRow &&
                expandedRow.classList.contains('expanded-row')
              ) {
                const metricTypeElement = expandedRow.querySelector(
                  '[class*="metric"], dt:contains("Metric Type")'
                );
                return metricTypeElement !== null;
              }
            }, 500);

            return true; // Found expand button
          }
        }
        return false;
      });

      await sleep(1000); // Wait for expansion

      if (metricTypeDisplayed) {
        testResults.metricTypeDisplayed = true;
        console.log('✅ Metric Type can be displayed');
      } else {
        console.log('❌ Metric Type expansion not working');
      }

      await takeScreenshot(
        page,
        '06_target_row_found',
        'Target row USLM,SMA,55,80 found'
      );
    } else {
      console.log('❌ Target row USLM,SMA,55,80 not found');
      log(`Available rows: ${targetRowData?.availableRows || 'unknown'}`);
    }

    // Test CSV export functionality
    console.log('📄 Testing CSV export...');

    const exportButtonExists = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const exportBtn = buttons.find(
        (btn) =>
          btn.textContent?.includes('Save to Server') ||
          btn.textContent?.includes('Export') ||
          btn.textContent?.includes('CSV')
      );
      return exportBtn !== null;
    });

    if (exportButtonExists) {
      testResults.csvExportAvailable = true;
      console.log('✅ CSV export button found');
    } else {
      console.log('❌ CSV export button not found');
    }

    await takeScreenshot(page, '07_final_state', 'Final test state');
  } catch (error) {
    console.error('❌ Frontend test failed:', error.message);
    log('Error details:', error.stack);

    if (page) {
      await takeScreenshot(page, '99_error', `Error: ${error.message}`);
    }
  } finally {
    if (page) {
      await page.close();
    }
    await browser.close();
  }

  return testResults;
}

async function testCSVExportFunctionality() {
  console.log('\n📁 Test 3: CSV Export Functionality');
  console.log('====================================');

  const testResults = {
    exportEndpointAvailable: false,
    portfoliosBestDirExists: false,
    exportExecuted: false,
  };

  try {
    // Check if portfolios_best directory exists
    const portfoliosBestPath = path.join(
      __dirname,
      '../../../csv/portfolios_best'
    );
    if (fs.existsSync(portfoliosBestPath)) {
      testResults.portfoliosBestDirExists = true;
      console.log('✅ portfolios_best directory exists');

      const files = fs.readdirSync(portfoliosBestPath);
      log(`Found ${files.length} files in portfolios_best`);
    } else {
      console.log('❌ portfolios_best directory does not exist');
    }

    // Test the export API endpoint directly
    const exportUrl = `${API_BASE_URL}/api/ma-cross/export`;
    const testData = {
      results: [
        {
          ticker: 'TEST',
          strategy_type: 'SMA',
          short_window: 5,
          long_window: 20,
          expectancy_per_trade: 1.5,
          avg_trade_duration: '30 days',
          metric_type: 'Test Metric',
        },
      ],
    };

    console.log('🔄 Testing export endpoint...');

    const response = await fetch(exportUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testData),
    });

    if (response.ok) {
      const result = await response.json();
      testResults.exportEndpointAvailable = true;
      testResults.exportExecuted = true;
      console.log('✅ Export endpoint working');
      console.log(`📄 Exported to: ${result.filename}`);
    } else {
      console.log(`❌ Export endpoint failed: ${response.status}`);
    }
  } catch (error) {
    console.error('❌ CSV export test failed:', error.message);
  }

  return testResults;
}

async function runDataAccuracyTests() {
  console.log('🚀 Starting Data Accuracy Test Suite');
  console.log('=====================================');
  console.log(`📅 Test run: ${new Date().toISOString()}`);
  console.log(`🎯 Testing USLM,SMA,55,80 configuration`);
  console.log(
    `💰 Expected expectancy: ${EXPECTED_VALUES.expectancy_per_trade} (display: 7.06)`
  );
  console.log(`⏱️ Expected duration: ${EXPECTED_VALUES.avg_trade_duration}`);
  console.log(
    `🏷️ Expected metric type: Present (e.g., "${EXPECTED_VALUES.metric_type}")`
  );

  const allResults = {
    apiTest: {},
    frontendTest: {},
    exportTest: {},
    summary: { passed: 0, failed: 0, total: 0 },
  };

  try {
    // Test 1: Direct API call
    allResults.apiTest = await testDirectAPICall();

    // Test 2: Frontend display
    allResults.frontendTest = await testFrontendDisplay();

    // Test 3: CSV export
    allResults.exportTest = await testCSVExportFunctionality();

    // Calculate summary
    const allTestValues = [
      ...Object.values(allResults.apiTest),
      ...Object.values(allResults.frontendTest),
      ...Object.values(allResults.exportTest),
    ];

    allResults.summary.total = allTestValues.length;
    allResults.summary.passed = allTestValues.filter(
      (result) => result === true
    ).length;
    allResults.summary.failed =
      allResults.summary.total - allResults.summary.passed;

    console.log('\n📊 TEST RESULTS SUMMARY');
    console.log('========================');
    console.log(`✅ Passed: ${allResults.summary.passed}`);
    console.log(`❌ Failed: ${allResults.summary.failed}`);
    console.log(`📝 Total:  ${allResults.summary.total}`);
    console.log(
      `📈 Success Rate: ${(
        (allResults.summary.passed / allResults.summary.total) *
        100
      ).toFixed(1)}%`
    );

    console.log('\n📋 Detailed Results:');
    console.log('API Tests:', allResults.apiTest);
    console.log('Frontend Tests:', allResults.frontendTest);
    console.log('Export Tests:', allResults.exportTest);

    // Specific issue analysis
    console.log('\n🔍 ISSUE ANALYSIS:');
    console.log('==================');

    if (!allResults.apiTest.expectancyCorrect) {
      console.log('❌ ISSUE 1: Backend returns wrong expectancy value');
    } else if (!allResults.frontendTest.expectancyDisplayCorrect) {
      console.log(
        '❌ ISSUE 1: Frontend displays wrong expectancy value (backend correct)'
      );
    } else {
      console.log('✅ Issue 1: Expectancy value is correct');
    }

    if (!allResults.apiTest.avgTradeDurationCorrect) {
      console.log('❌ ISSUE 2: Backend returns wrong avg trade duration');
    } else if (!allResults.frontendTest.avgTradeDurationDisplayCorrect) {
      console.log(
        '❌ ISSUE 2: Frontend displays wrong avg trade duration (backend correct)'
      );
    } else {
      console.log('✅ Issue 2: Avg Trade Duration is correct');
    }

    if (!allResults.apiTest.metricTypePresent) {
      console.log('❌ ISSUE 3: Backend missing metric type data');
    } else if (!allResults.frontendTest.metricTypeDisplayed) {
      console.log(
        '❌ ISSUE 3: Frontend cannot display metric type (backend has data)'
      );
    } else {
      console.log('✅ Issue 3: Metric Type is working');
    }

    if (!allResults.exportTest.exportExecuted) {
      console.log('❌ ISSUE 4: CSV export functionality not working');
    } else {
      console.log('✅ Issue 4: CSV export is working');
    }

    const criticalIssues = allResults.summary.failed;
    if (criticalIssues === 0) {
      console.log('\n🎉 ALL ISSUES RESOLVED! Data accuracy is correct.');
      process.exit(0);
    } else {
      console.log(
        `\n⚠️  ${criticalIssues} ISSUE(S) FOUND. See analysis above.`
      );
      process.exit(1);
    }
  } catch (error) {
    console.error('💥 Test suite failed with error:', error.message);
    console.error('Stack trace:', error.stack);
    process.exit(1);
  }
}

// Run the test suite if this file is executed directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  console.log('🧪 Data Accuracy Test Suite');
  console.log('============================');
  console.log('This test will:');
  console.log('1. Test backend API for correct data values');
  console.log('2. Test frontend display of the data');
  console.log('3. Test CSV export functionality');
  console.log('4. Identify exactly where the issues are occurring');
  console.log('\nStarting tests in 3 seconds...');

  setTimeout(() => {
    runDataAccuracyTests();
  }, 3000);
}

export {
  testDirectAPICall,
  testFrontendDisplay,
  testCSVExportFunctionality,
  runDataAccuracyTests,
};
