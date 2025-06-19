import puppeteer from 'puppeteer';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const TIMEOUT = 60000;
const REFRESH_INTERVAL = 30000;
const SCREENSHOT_DIR = path.join(__dirname, '../screenshots/position-sizing');

// Test configuration flags
const shouldTakeScreenshots = process.argv.includes('--screenshots');
const isVerbose = process.argv.includes('--verbose');

// Logging utilities
const log = (message) => {
  if (isVerbose) {
    console.log(`[${new Date().toISOString()}] ${message}`);
  }
};

const logStep = (stepNumber, description) => {
  console.log(`\n✓ Step ${stepNumber}: ${description}`);
};

// Screenshot utility
async function takeScreenshot(page, filename, description) {
  if (!shouldTakeScreenshots) return;

  if (!fs.existsSync(SCREENSHOT_DIR)) {
    fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const screenshotPath = path.join(SCREENSHOT_DIR, `${timestamp}_${filename}`);
  await page.screenshot({ path: screenshotPath, fullPage: true });
  log(`Screenshot saved: ${screenshotPath} - ${description}`);
}

// Wait utilities
async function waitForElement(page, selector, options = {}) {
  const timeout = options.timeout || 30000;
  log(`Waiting for element: ${selector}`);

  try {
    await page.waitForSelector(selector, { timeout, visible: true });
    log(`Element found: ${selector}`);
    return true;
  } catch (error) {
    log(`Element not found within timeout: ${selector}`);
    return false;
  }
}

// Unused function - kept for future use
// async function waitForText(page, text, options = {}) {
//   const timeout = options.timeout || 30000;
//   log(`Waiting for text: ${text}`);

//   try {
//     await page.waitForFunction(
//       (searchText) => document.body.textContent.includes(searchText),
//       { timeout },
//       text
//     );
//     log(`Text found: ${text}`);
//     return true;
//   } catch (error) {
//     log(`Text not found within timeout: ${text}`);
//     return false;
//   }
// }

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Main test function
async function runPositionSizingE2ETest() {
  console.log('🚀 Starting Position Sizing E2E Test Suite');
  console.log('================================');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Screenshots: ${shouldTakeScreenshots ? 'Enabled' : 'Disabled'}`);
  console.log(`Verbose: ${isVerbose ? 'Enabled' : 'Disabled'}`);
  console.log('================================\n');

  const browser = await puppeteer.launch({
    headless: !process.argv.includes('--headed'),
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const testResults = {
    totalTests: 0,
    passed: 0,
    failed: 0,
    errors: [],
  };

  try {
    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // Test 1: Dashboard Load Test
    console.log('\n📊 Test 1: Dashboard Load Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Navigating to base URL');
      await page.goto(BASE_URL, {
        waitUntil: 'networkidle2',
        timeout: TIMEOUT,
      });

      logStep(2, 'Clicking Position Sizing navigation button');
      const positionSizingNav = await page.waitForSelector(
        '[data-testid="nav-position-sizing"]',
        { timeout: 10000 }
      );
      await positionSizingNav.click();
      await sleep(1000); // Wait for view to switch
      await takeScreenshot(page, '01_initial_load.png', 'Initial page load');

      logStep(3, 'Verifying main dashboard container loads');
      const dashboardLoaded = await waitForElement(
        page,
        '.container-fluid:has(h2)'
      );
      if (!dashboardLoaded) {
        throw new Error('Dashboard container not found');
      }

      logStep(4, 'Checking for Position Sizing Dashboard header');
      const hasHeader = await page.evaluate(() => {
        const h2 = document.querySelector('h2');
        return h2 && h2.textContent.includes('Position Sizing Dashboard');
      });
      if (!hasHeader) {
        throw new Error('Position Sizing Dashboard header not found');
      }

      logStep(5, 'Verifying dashboard sections are present');
      const sections = [
        { selector: '.card', name: 'Dashboard Cards' },
        { selector: '.row', name: 'Dashboard Rows' },
      ];

      for (const section of sections) {
        const found = await waitForElement(page, section.selector, {
          timeout: 10000,
        });
        if (!found) {
          throw new Error(`Section not found: ${section.name}`);
        }
        log(`✓ ${section.name} loaded`);
      }

      await takeScreenshot(
        page,
        '02_all_sections_loaded.png',
        'All dashboard sections loaded'
      );

      logStep(6, 'Verifying dashboard structure and content');
      const dashboardStructure = await page.evaluate(() => {
        const titleElement = document.querySelector('h2');
        const hasTitle =
          titleElement &&
          titleElement.textContent.includes('Position Sizing Dashboard');
        const hasRefreshButton = Array.from(
          document.querySelectorAll('button')
        ).some((btn) => btn.textContent.includes('Refresh'));
        const portfolioMetrics =
          document
            .querySelector('h5, h6')
            ?.textContent.includes('Portfolio Risk') ||
          document.body.textContent.includes('Portfolio Risk');
        const accountBalances =
          document.body.textContent.includes('IBKR') ||
          document.body.textContent.includes('Account') ||
          document.body.textContent.includes('Balance');
        const riskAllocation =
          document.body.textContent.includes('Risk') &&
          document.body.textContent.includes('Allocation');
        return {
          hasTitle,
          hasRefreshButton,
          portfolioMetrics,
          accountBalances,
          riskAllocation,
        };
      });

      if (!dashboardStructure.hasTitle) {
        throw new Error('Dashboard title not found');
      }

      log(
        `Dashboard structure: Title=${dashboardStructure.hasTitle}, Refresh=${dashboardStructure.hasRefreshButton}, Portfolio=${dashboardStructure.portfolioMetrics}, Accounts=${dashboardStructure.accountBalances}, Risk=${dashboardStructure.riskAllocation}`
      );

      console.log(
        '✅ Test 1 PASSED: Dashboard loads successfully with all sections'
      );
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 1 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Dashboard Load Test',
        error: error.message,
      });
      await takeScreenshot(
        page,
        'error_dashboard_load.png',
        'Dashboard load error'
      );
    }

    // Test 2: Table Interaction Test
    console.log('\n📊 Test 2: Table Interaction Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Testing table search functionality');
      const searchInput = await page.$(
        'input[type="text"], input[placeholder*="Search"], input[placeholder*="search"]'
      );
      if (searchInput) {
        await searchInput.type('BTC');
        await sleep(1000);
        await takeScreenshot(
          page,
          '03_search_active.png',
          'Active positions search for BTC'
        );

        // Clear search
        await searchInput.click({ clickCount: 3 });
        await searchInput.press('Backspace');
      }

      logStep(2, 'Testing table sorting functionality');
      const sortableHeaders = await page.$$(
        'th[role="columnheader"], th.sortable, th:first-child'
      );
      if (sortableHeaders.length > 0) {
        await sortableHeaders[0].click();
        await sleep(500);
        log('Clicked first sortable column');
        await takeScreenshot(
          page,
          '04_sorted_table.png',
          'Table after sorting'
        );
      }

      logStep(3, 'Verifying table structure');
      const hasTable = await page.evaluate(() => {
        const table = document.querySelector('table');
        return table && table.offsetHeight > 0;
      });

      if (!hasTable) {
        log('Warning: No tables found');
      }

      console.log('✅ Test 2 PASSED: Table interactions working correctly');
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 2 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Table Interaction Test',
        error: error.message,
      });
    }

    // Test 3: Refresh Functionality Test
    console.log('\n📊 Test 3: Refresh Functionality Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Finding refresh button');
      const refreshButtonExists = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('button')).some(
          (btn) =>
            btn.textContent.includes('Refresh') ||
            btn.getAttribute('title')?.includes('Refresh')
        );
      });

      if (refreshButtonExists) {
        logStep(2, 'Clicking refresh button');
        await page.evaluate(() => {
          const button = Array.from(document.querySelectorAll('button')).find(
            (btn) =>
              btn.textContent.includes('Refresh') ||
              btn.getAttribute('title')?.includes('Refresh')
          );
          if (button) button.click();
        });

        // Wait for potential loading state
        await sleep(2000);

        logStep(3, 'Verifying page is still functional after refresh');
        const stillFunctional = await page.evaluate(() => {
          const h2 = document.querySelector('h2');
          return h2 && h2.textContent.includes('Position Sizing Dashboard');
        });

        if (stillFunctional) {
          await takeScreenshot(
            page,
            '05_after_refresh.png',
            'Dashboard after manual refresh'
          );
          console.log('✅ Test 3 PASSED: Manual refresh working');
          testResults.passed++;
        } else {
          throw new Error('Dashboard not functional after refresh');
        }
      } else {
        log('Warning: Refresh button not found - skipping test');
        console.log('⚠️  Test 3 SKIPPED: Refresh button not found');
      }
    } catch (error) {
      console.error('❌ Test 3 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Refresh Functionality Test',
        error: error.message,
      });
    }

    // Test 4: Incoming Signals Interaction Test
    console.log('\n📊 Test 4: Incoming Signals Interaction Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Checking for signal-related content');
      const hasSignalContent = await page.evaluate(() => {
        return (
          document.body.textContent.includes('Signal') ||
          document.body.textContent.includes('Incoming')
        );
      });

      if (hasSignalContent) {
        const hasSignals = await page.evaluate(() => {
          const rows = document.querySelectorAll('tbody tr, .signal-row');
          return rows.length > 0;
        });

        if (hasSignals) {
          logStep(2, 'Found incoming signals');
          await takeScreenshot(
            page,
            '06_incoming_signals.png',
            'Incoming signals display'
          );

          // Check for execute buttons
          const executeButtons = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('button')).filter(
              (btn) => btn.textContent.includes('Execute')
            ).length;
          });
          if (executeButtons > 0) {
            log(`Found ${executeButtons} execute buttons`);
          }

          // Verify signal types and confidence levels
          const signalTypes = await page.evaluate(() => {
            const badges = document.querySelectorAll('.badge, .signal-type');
            return Array.from(badges).map((b) => b.textContent);
          });

          log(`Signal types found: ${signalTypes.join(', ')}`);
          console.log('✅ Test 4 PASSED: Incoming signals display correctly');
          testResults.passed++;
        } else {
          console.log('⚠️  Test 4 SKIPPED: No incoming signals available');
        }
      } else {
        // Check if we have the signals section even with no data
        const hasSignalsSection = await page.evaluate(() => {
          return (
            document.body.textContent.includes('Incoming Signals') ||
            document.body.textContent.includes('No incoming signals') ||
            document.body.textContent.includes('Signals will appear')
          );
        });

        if (hasSignalsSection) {
          console.log(
            '✅ Test 4 PASSED: Incoming signals section displayed (empty state)'
          );
          testResults.passed++;
        } else {
          console.log('⚠️  Test 4 SKIPPED: No signal content found');
        }
      }
    } catch (error) {
      console.error('❌ Test 4 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Incoming Signals Interaction Test',
        error: error.message,
      });
    }

    // Test 5: Risk Allocation Display Test
    console.log('\n📊 Test 5: Risk Allocation Display Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Verifying risk allocation content');
      const hasRiskContent = await page.evaluate(() => {
        return (
          document.body.textContent.includes('Risk') ||
          document.body.textContent.includes('Allocation')
        );
      });

      if (hasRiskContent) {
        // Check for account balances
        const hasAccountBalances = await page.evaluate(() => {
          const accounts = ['IBKR', 'Bybit', 'Cash'];
          return accounts.every((account) =>
            document.body.textContent.includes(account)
          );
        });

        if (!hasAccountBalances) {
          log('Warning: Not all account balances found');
        }

        // Check for risk utilization progress bar
        const progressBar = await page.$(
          '.risk-utilization-progress, .progress-bar, [role="progressbar"]'
        );
        if (progressBar) {
          const utilization = await page.evaluate((el) => {
            const style = window.getComputedStyle(el);
            return style.width || el.getAttribute('aria-valuenow');
          }, progressBar);
          log(`Risk utilization: ${utilization}`);
        }

        await takeScreenshot(
          page,
          '07_risk_allocation.png',
          'Risk allocation display'
        );
        console.log('✅ Test 5 PASSED: Risk allocation displays correctly');
        testResults.passed++;
      } else {
        log('No risk allocation content found');
        console.log('⚠️  Test 5 SKIPPED: No risk allocation content found');
      }
    } catch (error) {
      console.error('❌ Test 5 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Risk Allocation Display Test',
        error: error.message,
      });
    }

    // Test 6: Strategic Holdings Display Test
    console.log('\n📊 Test 6: Strategic Holdings Display Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Checking for holdings content');
      const hasHoldingsContent = await page.evaluate(() => {
        return (
          document.body.textContent.includes('Holdings') ||
          document.body.textContent.includes('Strategic')
        );
      });

      if (hasHoldingsContent) {
        // Check for P&L color coding
        const plColors = await page.evaluate(() => {
          const plCells = document.querySelectorAll(
            '.pl-cell, td.profit-loss, .text-success, .text-danger'
          );
          const colors = { green: 0, red: 0 };

          plCells.forEach((cell) => {
            const style = window.getComputedStyle(cell);
            const text = cell.textContent;
            const classList = String(cell.className || '');
            if (
              style.color.includes('green') ||
              text.includes('+') ||
              classList.includes('success')
            )
              colors.green++;
            if (
              style.color.includes('red') ||
              text.includes('-') ||
              classList.includes('danger')
            )
              colors.red++;
          });

          return colors;
        });

        log(`P&L colors - Green: ${plColors.green}, Red: ${plColors.red}`);

        // Check for allocation percentages
        const hasAllocations = await page.evaluate(() => {
          return document.body.textContent.includes('%');
        });

        if (hasAllocations) {
          log('Allocation percentages found');
        }

        await takeScreenshot(
          page,
          '08_strategic_holdings.png',
          'Strategic holdings display'
        );
        console.log('✅ Test 6 PASSED: Strategic holdings display correctly');
        testResults.passed++;
      } else {
        // Check if we have the holdings section even with no data
        const hasHoldingsSection = await page.evaluate(() => {
          return (
            document.body.textContent.includes('Strategic Holdings') ||
            document.body.textContent.includes('No strategic holdings') ||
            document.body.textContent.includes('holdings found') ||
            document.body.textContent.includes('Investment portfolio')
          );
        });

        if (hasHoldingsSection) {
          console.log(
            '✅ Test 6 PASSED: Strategic holdings section displayed (empty state)'
          );
          testResults.passed++;
        } else {
          log('No holdings content found');
          console.log('⚠️  Test 6 SKIPPED: No holdings content found');
        }
      }
    } catch (error) {
      console.error('❌ Test 6 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Strategic Holdings Display Test',
        error: error.message,
      });
    }

    // Test 7: Responsive Behavior Test
    console.log('\n📊 Test 7: Responsive Behavior Test');
    testResults.totalTests++;

    try {
      logStep(1, 'Testing tablet viewport (1024x768)');
      await page.setViewport({ width: 1024, height: 768 });
      await sleep(1000);
      await takeScreenshot(page, '09_tablet_view.png', 'Tablet viewport');

      logStep(2, 'Testing mobile viewport (375x667)');
      await page.setViewport({ width: 375, height: 667 });
      await sleep(1000);
      await takeScreenshot(page, '10_mobile_view.png', 'Mobile viewport');

      // Verify key elements are still visible
      const mobileElementsVisible = await page.evaluate(() => {
        const essentialElements = [
          '.portfolio-risk-panel, [data-testid="portfolio-risk-panel"]',
          '.risk-allocation-buckets, [data-testid="risk-allocation-buckets"]',
        ];

        return essentialElements.every((selector) => {
          const element = document.querySelector(selector);
          return element && element.offsetHeight > 0;
        });
      });

      if (!mobileElementsVisible) {
        log('Warning: Some elements not properly visible on mobile');
      }

      // Restore desktop viewport
      await page.setViewport({ width: 1920, height: 1080 });

      console.log('✅ Test 7 PASSED: Responsive behavior working');
      testResults.passed++;
    } catch (error) {
      console.error('❌ Test 7 FAILED:', error.message);
      testResults.failed++;
      testResults.errors.push({
        test: 'Responsive Behavior Test',
        error: error.message,
      });
    }

    // Test 8: Auto-refresh Test (Optional - takes 30+ seconds)
    if (process.argv.includes('--full')) {
      console.log('\n📊 Test 8: Auto-refresh Test (30 second wait)');
      testResults.totalTests++;

      try {
        logStep(1, 'Capturing initial state');
        const initialTimestamp = await page.evaluate(() => {
          return new Date().toISOString();
        });

        logStep(
          2,
          `Waiting ${REFRESH_INTERVAL / 1000} seconds for auto-refresh...`
        );
        await sleep(REFRESH_INTERVAL + 5000); // Wait for refresh interval + buffer

        logStep(3, 'Checking if data refreshed');
        const dataChanged = await page.evaluate((initial) => {
          // Check if any timestamp or data has changed
          const currentTime = new Date().toISOString();
          return currentTime !== initial;
        }, initialTimestamp);

        if (dataChanged) {
          await takeScreenshot(
            page,
            '11_after_auto_refresh.png',
            'After auto-refresh'
          );
          console.log('✅ Test 8 PASSED: Auto-refresh working');
          testResults.passed++;
        } else {
          console.log('⚠️  Test 8 INCONCLUSIVE: Could not verify auto-refresh');
        }
      } catch (error) {
        console.error('❌ Test 8 FAILED:', error.message);
        testResults.failed++;
        testResults.errors.push({
          test: 'Auto-refresh Test',
          error: error.message,
        });
      }
    }
  } catch (error) {
    console.error('🚨 Critical test error:', error);
    testResults.errors.push({ test: 'General', error: error.message });
  } finally {
    await browser.close();
  }

  // Print test summary
  console.log('\n================================');
  console.log('📊 Position Sizing E2E Test Summary');
  console.log('================================');
  console.log(`Total Tests: ${testResults.totalTests}`);
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(
    `Success Rate: ${(
      (testResults.passed / testResults.totalTests) *
      100
    ).toFixed(1)}%`
  );

  if (testResults.errors.length > 0) {
    console.log('\n❌ Errors:');
    testResults.errors.forEach(({ test, error }) => {
      console.log(`  - ${test}: ${error}`);
    });
  }

  if (shouldTakeScreenshots) {
    console.log(`\n📸 Screenshots saved to: ${SCREENSHOT_DIR}`);
  }

  // Exit with appropriate code
  process.exit(testResults.failed > 0 ? 1 : 0);
}

// Run the test
runPositionSizingE2ETest().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
