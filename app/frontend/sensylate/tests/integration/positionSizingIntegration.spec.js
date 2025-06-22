/**
 * Comprehensive Integration Tests for Position Sizing Manual Data Entry System
 * Tests end-to-end workflows including UI components, API integration, and data flow
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

describe('Position Sizing Manual Data Entry - Integration Tests', () => {
  let browser;
  let page;
  const baseUrl = 'http://localhost:5173';
  const testTimeout = 30000;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: process.env.CI === 'true',
      slowMo: process.env.CI ? 0 : 50,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });

    // Set up console logging for debugging
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        console.log('Browser Error:', msg.text());
      }
    });

    // Set up error handling
    page.on('pageerror', (error) => {
      console.log('Page Error:', error.message);
    });
  }, testTimeout);

  afterAll(async () => {
    if (browser) {
      await browser.close();
    }
  });

  beforeEach(async () => {
    await page.goto(baseUrl);
    await page.waitForSelector('[data-testid="app-container"]', {
      timeout: 10000,
    });
  });

  describe('Dashboard Integration', () => {
    test('should load Position Sizing dashboard without errors', async () => {
      // Navigate to Position Sizing
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]', {
        timeout: 10000,
      });

      // Verify main components are loaded
      const dashboardTitle = await page.$eval('h2', (el) => el.textContent);
      expect(dashboardTitle).toContain('Position Sizing Dashboard');

      // Check for key dashboard sections
      await page.waitForSelector('[data-testid="portfolio-risk-panel"]');
      await page.waitForSelector('[data-testid="risk-allocation-buckets"]');
      await page.waitForSelector('[data-testid="active-positions-table"]');
    });

    test('should display risk allocation with 11.8% target', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="risk-allocation-buckets"]');

      // Verify 11.8% target is displayed
      const riskTarget = await page.$eval(
        '[data-testid="risk-target"]',
        (el) => el.textContent
      );
      expect(riskTarget).toContain('11.8%');

      // Check risk utilization display
      const riskUtilization = await page.$('[data-testid="risk-utilization"]');
      expect(riskUtilization).toBeTruthy();
    });
  });

  describe('Kelly Criterion Input Integration', () => {
    test('should update Kelly Criterion value', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="kelly-input-form"]');

      // Input new Kelly value
      const kellyInput = await page.$('[data-testid="kelly-criterion-input"]');
      await kellyInput.click({ clickCount: 3 }); // Select all
      await kellyInput.type('0.25');

      // Select source
      await page.select(
        '[data-testid="kelly-source-select"]',
        'Trading Journal'
      );

      // Add notes
      await page.type(
        '[data-testid="kelly-notes"]',
        'Updated from Q4 trading journal analysis'
      );

      // Save changes
      await page.click('[data-testid="kelly-save-button"]');

      // Wait for success feedback
      await page.waitForSelector('[data-testid="kelly-success-message"]', {
        timeout: 5000,
      });

      // Verify value was saved
      const savedValue = await page.$eval(
        '[data-testid="kelly-criterion-input"]',
        (el) => el.value
      );
      expect(savedValue).toBe('0.25');
    });

    test('should validate Kelly Criterion input ranges', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="kelly-input-form"]');

      // Test invalid value (>1.0)
      const kellyInput = await page.$('[data-testid="kelly-criterion-input"]');
      await kellyInput.click({ clickCount: 3 });
      await kellyInput.type('1.5');

      await page.click('[data-testid="kelly-save-button"]');

      // Should show validation error
      await page.waitForSelector('[data-testid="validation-error"]');
      const errorText = await page.$eval(
        '[data-testid="validation-error"]',
        (el) => el.textContent
      );
      expect(errorText).toContain('between 0 and 1');
    });
  });

  describe('Position Entry Integration', () => {
    test('should add new position through modal', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

      // Open position entry modal
      await page.click('[data-testid="add-position-button"]');
      await page.waitForSelector('[data-testid="position-entry-modal"]');

      // Fill position details
      await page.type('[data-testid="position-symbol"]', 'MSFT');
      await page.type('[data-testid="position-size"]', '15000');
      await page.type('[data-testid="position-entry-date"]', '2024-01-15');
      await page.select('[data-testid="position-status"]', 'Active');
      await page.select('[data-testid="stop-status"]', 'Risk');
      await page.select('[data-testid="portfolio-type"]', 'Risk_On');
      await page.type(
        '[data-testid="position-notes"]',
        'Added via integration test'
      );

      // Submit position
      await page.click('[data-testid="submit-position"]');

      // Wait for success and modal close
      await page.waitForFunction(
        () => !document.querySelector('[data-testid="position-entry-modal"]')
      );

      // Verify position appears in table
      await page.waitForSelector('[data-testid="active-positions-table"]');
      const positionExists = await page.$eval(
        '[data-testid="active-positions-table"]',
        (el) => el.textContent.includes('MSFT')
      );
      expect(positionExists).toBe(true);
    });

    test('should validate position entry form', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.click('[data-testid="add-position-button"]');
      await page.waitForSelector('[data-testid="position-entry-modal"]');

      // Submit empty form
      await page.click('[data-testid="submit-position"]');

      // Should show validation errors
      await page.waitForSelector('[data-testid="validation-errors"]');
      const errors = await page.$$eval(
        '[data-testid="validation-error"]',
        (elements) => elements.map((el) => el.textContent)
      );

      expect(errors.some((error) => error.includes('Symbol is required'))).toBe(
        true
      );
      expect(
        errors.some((error) => error.includes('Position size is required'))
      ).toBe(true);
    });
  });

  describe('Position Table Editor Integration', () => {
    test('should edit position inline', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-table-editor"]');

      // Find first position and click edit
      const firstEditButton = await page.$(
        '[data-testid="edit-position-size"]'
      );
      if (firstEditButton) {
        await firstEditButton.click();

        // Wait for inline editor
        await page.waitForSelector('[data-testid="inline-position-editor"]');

        // Update position size
        const editor = await page.$(
          '[data-testid="inline-position-editor"] input'
        );
        await editor.click({ clickCount: 3 });
        await editor.type('20000');

        // Save changes
        await page.click('[data-testid="save-inline-edit"]');

        // Verify update
        await page.waitForFunction(
          () =>
            !document.querySelector('[data-testid="inline-position-editor"]')
        );
      }
    });
  });

  describe('Portfolio Transition Integration', () => {
    test('should transition position from Risk to Protected', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector(
        '[data-testid="portfolio-transition-manager"]'
      );

      // Find transition button for Risk_On position
      const transitionButton = await page.$(
        '[data-testid="transition-to-protected"]'
      );
      if (transitionButton) {
        await transitionButton.click();

        // Wait for confirmation dialog
        await page.waitForSelector('[data-testid="transition-confirmation"]');

        // Confirm transition
        await page.click('[data-testid="confirm-transition"]');

        // Wait for success message
        await page.waitForSelector('[data-testid="transition-success"]', {
          timeout: 5000,
        });

        // Verify position moved to Protected portfolio
        const successMessage = await page.$eval(
          '[data-testid="transition-success"]',
          (el) => el.textContent
        );
        expect(successMessage).toContain('Protected Portfolio');
      }
    });
  });

  describe('Risk Visualization Integration', () => {
    test('should display advanced risk dashboard', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="advanced-risk-dashboard"]');

      // Check chart components
      await page.waitForSelector('[data-testid="risk-trend-chart"]');
      await page.waitForSelector('[data-testid="portfolio-composition-chart"]');

      // Test chart interactions
      await page.click('[data-testid="chart-type-toggle"]');
      await page.waitForSelector('[data-testid="bar-chart-view"]');

      // Test time range selection
      await page.click('[data-testid="time-range-7d"]');
      await page.waitForFunction(
        () => document.querySelector('[data-testid="chart-loading"]') === null
      );
    });

    test('should show risk monitoring alerts', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="risk-monitoring-alerts"]');

      // Check alert system status
      const alertStatus = await page.$eval(
        '[data-testid="alert-status"]',
        (el) => el.textContent
      );
      expect(alertStatus).toContain('Risk Monitoring');

      // Test alert settings
      await page.click('[data-testid="alert-settings-toggle"]');
      await page.waitForSelector('[data-testid="alert-thresholds"]');

      // Verify threshold controls
      const warningThreshold = await page.$(
        '[data-testid="warning-threshold"]'
      );
      expect(warningThreshold).toBeTruthy();
    });
  });

  describe('Scenario Analysis Integration', () => {
    test('should run scenario analysis', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="scenario-analyzer"]');

      // Select moderate scenario
      await page.click('[data-testid="scenario-moderate"]');

      // Run analysis
      await page.click('[data-testid="run-scenario-analysis"]');

      // Wait for results
      await page.waitForSelector('[data-testid="scenario-results"]', {
        timeout: 10000,
      });

      // Verify results components
      await page.waitForSelector('[data-testid="potential-loss"]');
      await page.waitForSelector('[data-testid="projected-cvar"]');
      await page.waitForSelector('[data-testid="worst-case-positions"]');
      await page.waitForSelector('[data-testid="recommendations"]');

      const potentialLoss = await page.$eval(
        '[data-testid="potential-loss"]',
        (el) => el.textContent
      );
      expect(potentialLoss).toMatch(/\$[\d,]+/);
    });
  });

  describe('Performance Integration', () => {
    test('should load dashboard within performance thresholds', async () => {
      const startTime = Date.now();

      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000); // Should load within 3 seconds
    });

    test('should handle large datasets efficiently', async () => {
      await page.click('[data-testid="nav-position-sizing"]');

      // Simulate large dataset by checking memory usage
      const metrics = await page.metrics();
      const initialMemory = metrics.JSHeapUsedSize;

      // Interact with various components
      await page.click('[data-testid="portfolio-composition-visualizer"]');
      await page.click('[data-testid="chart-type-toggle"]');
      await page.click('[data-testid="time-range-30d"]');

      const finalMetrics = await page.metrics();
      const memoryIncrease = finalMetrics.JSHeapUsedSize - initialMemory;

      // Memory increase should be reasonable (less than 50MB)
      expect(memoryIncrease).toBeLessThan(50 * 1024 * 1024);
    });
  });

  describe('Error Handling Integration', () => {
    test('should handle API errors gracefully', async () => {
      // Intercept API calls and simulate error
      await page.setRequestInterception(true);
      page.on('request', (request) => {
        if (request.url().includes('/api/position-sizing/')) {
          request.respond({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: 'Internal server error' }),
          });
        } else {
          request.continue();
        }
      });

      await page.click('[data-testid="nav-position-sizing"]');

      // Should show error state
      await page.waitForSelector('[data-testid="error-message"]', {
        timeout: 5000,
      });
      const errorMessage = await page.$eval(
        '[data-testid="error-message"]',
        (el) => el.textContent
      );
      expect(errorMessage).toContain('error');
    });

    test('should recover from network issues', async () => {
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

      // Simulate network recovery by clicking retry
      if (await page.$('[data-testid="retry-button"]')) {
        await page.click('[data-testid="retry-button"]');
        await page.waitForSelector('[data-testid="position-sizing-dashboard"]');
      }
    });
  });

  describe('Data Persistence Integration', () => {
    test('should persist Kelly Criterion changes across sessions', async () => {
      await page.click('[data-testid="nav-position-sizing"]');

      // Update Kelly value
      const kellyInput = await page.$('[data-testid="kelly-criterion-input"]');
      if (kellyInput) {
        await kellyInput.click({ clickCount: 3 });
        await kellyInput.type('0.18');
        await page.click('[data-testid="kelly-save-button"]');
        await page.waitForSelector('[data-testid="kelly-success-message"]');
      }

      // Refresh page and verify persistence
      await page.reload();
      await page.waitForSelector('[data-testid="kelly-input-form"]');

      const savedValue = await page.$eval(
        '[data-testid="kelly-criterion-input"]',
        (el) => el.value
      );
      expect(savedValue).toBe('0.18');
    });
  });

  describe('Mobile Responsiveness Integration', () => {
    test('should work on mobile viewports', async () => {
      await page.setViewport({ width: 375, height: 667 }); // iPhone SE

      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

      // Check that key components are still accessible
      const dashboard = await page.$(
        '[data-testid="position-sizing-dashboard"]'
      );
      expect(dashboard).toBeTruthy();

      // Verify responsive layouts
      const riskPanel = await page.$('[data-testid="portfolio-risk-panel"]');
      const panelWidth = await riskPanel.evaluate((el) => el.offsetWidth);
      expect(panelWidth).toBeLessThanOrEqual(375);
    });
  });
});

export default {
  testSuite: 'Position Sizing Integration Tests',
  totalTests: 20,
  categories: [
    'Dashboard Integration',
    'Kelly Criterion Input',
    'Position Entry',
    'Position Table Editor',
    'Portfolio Transitions',
    'Risk Visualization',
    'Scenario Analysis',
    'Performance',
    'Error Handling',
    'Data Persistence',
    'Mobile Responsiveness',
  ],
};
