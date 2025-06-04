const puppeteer = require('puppeteer');

const APP_URL = 'http://localhost:5001';
const TIMEOUT = 30000;

async function runTests() {
  let browser;
  let passed = 0;
  let failed = 0;

  try {
    console.log('🚀 Starting Puppeteer tests...\n');

    browser = await puppeteer.launch({
      headless: 'new',
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });

    const page = await browser.newPage();

    // Set viewport
    await page.setViewport({ width: 1280, height: 800 });

    // Test 1: Page loads successfully
    console.log('Test 1: Page loads successfully');
    try {
      await page.goto(APP_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
      const title = await page.title();
      assert(
        title === 'Stock Price History',
        `Expected title "Stock Price History", got "${title}"`
      );
      console.log('✅ Page loaded successfully\n');
      passed++;
    } catch (error) {
      console.log('❌ Failed to load page:', error.message, '\n');
      failed++;
    }

    // Test 2: UI elements are present
    console.log('Test 2: UI elements are present');
    try {
      await page.waitForSelector('h1', { timeout: 5000 });
      const heading = await page.$eval('h1', (el) => el.textContent);
      assert(
        heading === 'Stock Price History',
        `Expected heading "Stock Price History", got "${heading}"`
      );

      await page.waitForSelector('#tickerInput', { timeout: 5000 });
      const inputExists = (await page.$('#tickerInput')) !== null;
      assert(inputExists, 'Ticker input not found');

      await page.waitForSelector('#goButton', { timeout: 5000 });
      const buttonExists = (await page.$('#goButton')) !== null;
      assert(buttonExists, 'Go button not found');

      console.log('✅ All UI elements present\n');
      passed++;
    } catch (error) {
      console.log('❌ UI elements test failed:', error.message, '\n');
      failed++;
    }

    // Test 3: Default ticker value
    console.log('Test 3: Default ticker value');
    try {
      const defaultValue = await page.$eval('#tickerInput', (el) => el.value);
      assert(
        defaultValue === 'BTC-USD',
        `Expected default value "BTC-USD", got "${defaultValue}"`
      );
      console.log('✅ Default ticker value is correct\n');
      passed++;
    } catch (error) {
      console.log('❌ Default value test failed:', error.message, '\n');
      failed++;
    }

    // Test 4: Fetch BTC-USD data
    console.log('Test 4: Fetch BTC-USD data');
    try {
      // Click the Go button
      await page.click('#goButton');

      // Wait for either chart to appear or error message
      await Promise.race([
        page.waitForSelector('.chart-container.visible', { timeout: 15000 }),
        page.waitForSelector('.error.visible', { timeout: 15000 }),
      ]);

      const errorVisible = await page.$('.error.visible');
      if (errorVisible) {
        const errorText = await page.$eval(
          '.error.visible',
          (el) => el.textContent
        );
        throw new Error(`API returned error: ${errorText}`);
      }

      // Check if chart is visible
      const chartVisible = await page.$('.chart-container.visible');
      assert(chartVisible, 'Chart container not visible after fetching data');

      // Check if canvas element exists
      const canvasExists = (await page.$('#priceChart')) !== null;
      assert(canvasExists, 'Chart canvas not found');

      console.log('✅ BTC-USD data fetched and displayed successfully\n');
      passed++;
    } catch (error) {
      console.log('❌ BTC-USD fetch test failed:', error.message, '\n');
      failed++;
    }

    // Test 5: Change ticker and fetch stock data
    console.log('Test 5: Change ticker and fetch stock data (AAPL)');
    try {
      // Clear input and type new ticker
      await page.click('#tickerInput', { clickCount: 3 });
      await page.type('#tickerInput', 'AAPL');

      // Click Go button
      await page.click('#goButton');

      // Wait for loading to disappear
      await page.waitForFunction(
        () => !document.querySelector('.loading.visible'),
        { timeout: 15000 }
      );

      // Check for errors
      const errorVisible = await page.$('.error.visible');
      if (errorVisible) {
        const errorText = await page.$eval(
          '.error.visible',
          (el) => el.textContent
        );
        throw new Error(`API returned error: ${errorText}`);
      }

      // Verify ticker label updated
      await page.waitForSelector('.ticker-label.visible', { timeout: 5000 });
      const tickerLabel = await page.$eval(
        '.ticker-label.visible',
        (el) => el.textContent
      );
      assert(
        tickerLabel === 'AAPL',
        `Expected ticker label "AAPL", got "${tickerLabel}"`
      );

      console.log('✅ AAPL data fetched and displayed successfully\n');
      passed++;
    } catch (error) {
      console.log('❌ AAPL fetch test failed:', error.message, '\n');
      failed++;
    }

    // Test 6: Invalid ticker handling
    console.log('Test 6: Invalid ticker handling');
    try {
      // Clear input and type invalid ticker
      await page.click('#tickerInput', { clickCount: 3 });
      await page.type('#tickerInput', 'INVALID123');

      // Click Go button
      await page.click('#goButton');

      // Wait for error message
      await page.waitForSelector('.error.visible', { timeout: 10000 });
      const errorText = await page.$eval(
        '.error.visible',
        (el) => el.textContent
      );
      assert(errorText.length > 0, 'Error message is empty');

      console.log('✅ Invalid ticker handled correctly with error message\n');
      passed++;
    } catch (error) {
      console.log('❌ Invalid ticker test failed:', error.message, '\n');
      failed++;
    }

    // Test 7: Enter key functionality
    console.log('Test 7: Enter key functionality');
    try {
      // Clear input and type ticker
      await page.click('#tickerInput', { clickCount: 3 });
      await page.type('#tickerInput', 'MSFT');

      // Press Enter
      await page.keyboard.press('Enter');

      // Wait for loading to complete
      await page.waitForFunction(
        () => !document.querySelector('.loading.visible'),
        { timeout: 15000 }
      );

      // Check if data loaded
      const chartVisible = await page.$('.chart-container.visible');
      assert(chartVisible, 'Chart not displayed after pressing Enter');

      console.log('✅ Enter key functionality works correctly\n');
      passed++;
    } catch (error) {
      console.log('❌ Enter key test failed:', error.message, '\n');
      failed++;
    }

    // Test 8: Button disabled during loading
    console.log('Test 8: Button disabled during loading');
    try {
      // Clear input
      await page.click('#tickerInput', { clickCount: 3 });
      await page.type('#tickerInput', 'GOOGL');

      // Click button and immediately check if disabled
      await page.click('#goButton');

      const isDisabled = await page.$eval(
        '#goButton',
        (button) => button.disabled
      );
      assert(isDisabled, 'Button should be disabled during loading');

      // Wait for loading to complete
      await page.waitForFunction(
        () => !document.querySelector('#goButton').disabled,
        { timeout: 15000 }
      );

      console.log('✅ Button disable/enable behavior works correctly\n');
      passed++;
    } catch (error) {
      console.log('❌ Button disable test failed:', error.message, '\n');
      failed++;
    }
  } catch (error) {
    console.error('Test suite error:', error);
    failed++;
  } finally {
    if (browser) {
      await browser.close();
    }

    // Print summary
    console.log('\n' + '='.repeat(50));
    console.log('TEST SUMMARY');
    console.log('='.repeat(50));
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📊 Total: ${passed + failed}`);
    console.log('='.repeat(50));

    // Exit with appropriate code
    process.exit(failed > 0 ? 1 : 0);
  }
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message || 'Assertion failed');
  }
}

// Run tests
runTests().catch(console.error);
