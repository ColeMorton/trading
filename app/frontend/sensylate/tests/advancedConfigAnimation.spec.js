/* eslint-env node */
import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const __dirname = path.dirname(__filename);

/**
 * Puppeteer test for Advanced Configuration collapse functionality in Sensylate
 * Tests Bootstrap collapse animation and UI interactions
 */

const BASE_URL = 'http://localhost:5173'; // Vite dev server default port
const TIMEOUT = 10000; // 10 seconds
const SCREENSHOT_DIR =
  '/Users/colemorton/Projects/trading/app/sensylate/screenshots';

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function cleanupOldScreenshots() {
  try {
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      return; // No screenshots directory exists
    }

    const files = fs.readdirSync(SCREENSHOT_DIR);
    const screenshotFiles = files.filter(
      (file) =>
        file.endsWith('.png') &&
        /\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}/.test(file) // Match timestamp pattern
    );

    if (screenshotFiles.length > 0) {
      console.log(
        `🧹 Cleaning up ${screenshotFiles.length} old advanced config test screenshots...`
      );

      for (const file of screenshotFiles) {
        const filePath = path.join(SCREENSHOT_DIR, file);
        fs.unlinkSync(filePath);
      }

      console.log('✅ Old advanced config test screenshots cleaned up');
    }
  } catch (error) {
    console.log(`⚠️ Failed to cleanup old screenshots: ${error.message}`);
  }
}

async function takeScreenshot(page, filename, description) {
  try {
    // Ensure screenshot directory exists
    if (!fs.existsSync(SCREENSHOT_DIR)) {
      fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const screenshotPath = path.join(
      SCREENSHOT_DIR,
      `${timestamp}_${filename}.png`
    );

    await page.screenshot({
      path: screenshotPath,
      fullPage: true,
      captureBeyondViewport: true,
    });

    console.log(`📸 Screenshot: ${filename} - ${description}`);
  } catch (error) {
    console.error(`❌ Screenshot failed for ${filename}:`, error.message);
  }
}

async function testAdvancedConfigCollapse() {
  console.log('🚀 Starting Sensylate Advanced Configuration collapse test...');

  // Clean up old screenshots before starting new test run
  await cleanupOldScreenshots();

  const browser = await puppeteer.launch({
    headless: false, // Set to true for CI/automated testing
    devtools: false,
    slowMo: 100, // Slow down for better observation
  });

  let page;

  try {
    page = await browser.newPage();

    // Set viewport for consistent testing
    await page.setViewport({ width: 1200, height: 800 });

    console.log('📱 Navigating to Sensylate application...');
    await page.goto(BASE_URL, { waitUntil: 'networkidle0', timeout: TIMEOUT });

    // Navigate to parameter testing view
    console.log('🔄 Switching to Parameter Testing view...');
    await page.waitForSelector('[data-testid="nav-parameter-testing"]', {
      timeout: TIMEOUT,
    });
    await page.click('[data-testid="nav-parameter-testing"]');

    await takeScreenshot(
      page,
      '01_parameter_testing_loaded',
      'Parameter testing view loaded'
    );

    // Wait for the Advanced Configuration button to be available
    console.log('🔍 Waiting for Advanced Configuration button...');
    await page.waitForSelector(
      'button[data-bs-target="#advanced-configuration"]',
      { timeout: TIMEOUT }
    );

    // Get initial state of the collapsible element
    const advancedConfigCollapsed = await page.$eval(
      '#advanced-configuration',
      (el) => !el.classList.contains('show')
    );

    if (!advancedConfigCollapsed) {
      throw new Error('Advanced Configuration should be collapsed initially');
    }
    console.log('✅ Advanced Configuration is initially collapsed');

    // Get the button element for testing
    const toggleButton = await page.$(
      'button[data-bs-target="#advanced-configuration"]'
    );
    if (!toggleButton) {
      throw new Error('Advanced Configuration toggle button not found');
    }

    const initialButtonText = await page.$eval(
      'button[data-bs-target="#advanced-configuration"]',
      (el) => el.textContent.trim()
    );

    console.log(`📝 Initial button text: "${initialButtonText}"`);

    // Test aria-expanded attribute
    const initialAriaExpanded = await page.$eval(
      'button[data-bs-target="#advanced-configuration"]',
      (el) => el.getAttribute('aria-expanded')
    );

    if (initialAriaExpanded !== 'false') {
      throw new Error(
        `Expected aria-expanded="false", got "${initialAriaExpanded}"`
      );
    }
    console.log('✅ Initial aria-expanded is "false"');

    // Measure the initial height of the collapsible element
    const initialHeight = await page.$eval(
      '#advanced-configuration',
      (el) => el.offsetHeight
    );
    console.log(`📏 Initial height: ${initialHeight}px`);

    if (initialHeight !== 0) {
      throw new Error(
        `Expected initial height to be 0, got ${initialHeight}px`
      );
    }

    await takeScreenshot(
      page,
      '02_before_expand',
      'Before expanding advanced config'
    );

    // Click to expand the Advanced Configuration
    console.log('🖱️  Clicking Advanced Configuration button to expand...');
    await toggleButton.click();

    // Wait for animation to start
    await sleep(50);
    await takeScreenshot(page, '03_animation_start', 'Animation starting');

    // Wait for the collapse animation to complete (Bootstrap default is ~350ms)
    await sleep(400);

    // Verify the element is now expanded
    const expandedConfigVisible = await page.$eval(
      '#advanced-configuration',
      (el) => el.classList.contains('show')
    );

    if (!expandedConfigVisible) {
      throw new Error('Advanced Configuration should be expanded after click');
    }
    console.log('✅ Advanced Configuration is now expanded');

    // Verify aria-expanded changed to true
    const expandedAriaExpanded = await page.$eval(
      'button[data-bs-target="#advanced-configuration"]',
      (el) => el.getAttribute('aria-expanded')
    );

    if (expandedAriaExpanded !== 'true') {
      throw new Error(
        `Expected aria-expanded="true", got "${expandedAriaExpanded}"`
      );
    }
    console.log('✅ aria-expanded is now "true"');

    // Check if chevron icon changed (should be pointing up when expanded)
    const iconElement = await page.$(
      'button[data-bs-target="#advanced-configuration"] svg'
    );
    if (iconElement) {
      // Check if the icon exists (the actual icon type depends on the Icon component implementation)
      console.log('✅ Chevron icon element found');

      // Alternative: Check the button's aria-expanded attribute which we already verified
      // The icon should change based on isAdvancedExpanded state
      if (expandedAriaExpanded === 'true') {
        console.log(
          '✅ Icon should be showing up arrow (based on aria-expanded state)'
        );
      }
    } else {
      console.warn(
        '⚠️  Could not find icon element - may be using a different icon implementation'
      );
    }

    // Measure the expanded height
    const expandedHeight = await page.$eval(
      '#advanced-configuration',
      (el) => el.offsetHeight
    );
    console.log(`📏 Expanded height: ${expandedHeight}px`);

    if (expandedHeight <= initialHeight) {
      throw new Error(
        `Expected expanded height to be greater than initial height`
      );
    }

    await takeScreenshot(page, '04_expanded', 'Fully expanded advanced config');

    // Verify that advanced configuration fields are visible and accessible
    const visibleFields = await page.$$eval(
      '#advanced-configuration input, #advanced-configuration select',
      (elements) =>
        elements.map((el) => ({
          id: el.id,
          type: el.type || el.tagName.toLowerCase(),
          visible: el.offsetWidth > 0 && el.offsetHeight > 0,
        }))
    );

    console.log('📋 Visible fields in advanced config:', visibleFields);

    const hiddenFields = visibleFields.filter((field) => !field.visible);
    if (hiddenFields.length > 0) {
      console.warn('⚠️  Some fields are not visible:', hiddenFields);
    }

    // Test collapsing again
    console.log('🖱️  Clicking Advanced Configuration button to collapse...');
    await toggleButton.click();

    // Wait for animation to start
    await sleep(50);
    await takeScreenshot(
      page,
      '05_collapse_start',
      'Collapse animation starting'
    );

    // Wait for the collapse animation to complete
    await sleep(400);

    // Verify the element is collapsed again
    const collapsedConfigHidden = await page.$eval(
      '#advanced-configuration',
      (el) => !el.classList.contains('show')
    );

    if (!collapsedConfigHidden) {
      throw new Error(
        'Advanced Configuration should be collapsed after second click'
      );
    }
    console.log('✅ Advanced Configuration is collapsed again');

    // Verify aria-expanded changed back to false
    const collapsedAriaExpanded = await page.$eval(
      'button[data-bs-target="#advanced-configuration"]',
      (el) => el.getAttribute('aria-expanded')
    );

    if (collapsedAriaExpanded !== 'false') {
      throw new Error(
        `Expected aria-expanded="false", got "${collapsedAriaExpanded}"`
      );
    }
    console.log('✅ aria-expanded is back to "false"');

    // Check if chevron icon changed back (should be pointing down when collapsed)
    const finalIconElement = await page.$(
      'button[data-bs-target="#advanced-configuration"] svg'
    );
    if (finalIconElement) {
      console.log('✅ Chevron icon element found');

      // The icon should change based on isAdvancedExpanded state
      if (collapsedAriaExpanded === 'false') {
        console.log(
          '✅ Icon should be showing down arrow (based on aria-expanded state)'
        );
      }
    } else {
      console.warn(
        '⚠️  Could not find icon element - may be using a different icon implementation'
      );
    }

    // Verify height is back to 0
    const finalHeight = await page.$eval(
      '#advanced-configuration',
      (el) => el.offsetHeight
    );
    console.log(`📏 Final height: ${finalHeight}px`);

    if (finalHeight !== 0) {
      throw new Error(`Expected final height to be 0, got ${finalHeight}px`);
    }

    await takeScreenshot(page, '06_collapsed_final', 'Final collapsed state');

    // Test animation timing by measuring transition duration
    console.log('⏱️  Testing animation timing...');

    // Expand again to test timing
    const startTime = Date.now();
    await toggleButton.click();

    // Wait for the 'show' class to be added (should happen quickly)
    await page.waitForFunction(
      () => {
        const element = document.querySelector('#advanced-configuration');
        return element && element.classList.contains('show');
      },
      { timeout: 1000 }
    );

    const animationTime = Date.now() - startTime;
    console.log(`⏱️  Animation completed in ${animationTime}ms`);

    // Bootstrap's default transition is around 350ms, allow some variance
    if (animationTime < 100 || animationTime > 1000) {
      console.warn(
        `⚠️  Animation time ${animationTime}ms seems outside expected range (100-1000ms)`
      );
    } else {
      console.log('✅ Animation timing is within expected range');
    }

    await takeScreenshot(
      page,
      '07_timing_test_complete',
      'Animation timing test complete'
    );

    console.log(
      '✅ All Sensylate Advanced Configuration collapse tests passed!'
    );
  } catch (error) {
    console.error('❌ Test failed:', error.message);
    try {
      if (typeof page !== 'undefined' && page) {
        await takeScreenshot(page, '99_error', 'Error state');
      }
    } catch (screenshotError) {
      console.error(
        'Failed to take error screenshot:',
        screenshotError.message
      );
    }
    throw error;
  } finally {
    await browser.close();
  }
}

// Run the test
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  testAdvancedConfigCollapse()
    .then(() => {
      console.log(
        '🎉 Sensylate Advanced Configuration collapse test completed successfully!'
      );
      process.exit(0);
    })
    .catch((error) => {
      console.error('💥 Test suite failed:', error);
      process.exit(1);
    });
}

export { testAdvancedConfigCollapse };
