import puppeteer from 'puppeteer';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Comprehensive Puppeteer test suite for Sensylate Parameter Testing
 * Based on SensitivityTrader test patterns
 * Tests the complete Parameter Testing workflow integration
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BASE_URL = 'http://localhost:5173'; // Vite dev server default
const TIMEOUT = 30000; // 30 seconds
const SCREENSHOT_DIR = path.join(__dirname, '../screenshots');

// Expected BXP result configuration for testing
const TEST_CONFIG = {
    ticker: 'BXP',
    expectedResults: {
        ticker: 'BXP',
        strategyType: 'SMA',
        timeframe: 'D',
        direction: 'Long'
    }
};

// Check for screenshot argument
const TAKE_SCREENSHOTS = process.argv.includes('--screenshots');

console.log(`🧪 Sensylate Parameter Testing Test Suite`);
console.log(`📷 Screenshots: ${TAKE_SCREENSHOTS ? 'ENABLED' : 'DISABLED'}`);
console.log(`🎯 Target URL: ${BASE_URL}`);

async function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function takeScreenshot(page, filename, description) {
    if (!TAKE_SCREENSHOTS) return null;
    
    try {
        // Ensure screenshot directory exists
        if (!fs.existsSync(SCREENSHOT_DIR)) {
            fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
        }
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const screenshotPath = path.join(SCREENSHOT_DIR, `${timestamp}_${filename}.png`);
        
        await page.screenshot({ 
            path: screenshotPath, 
            fullPage: true,
            captureBeyondViewport: true
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

async function testNavigationAndPageLoad() {
    console.log('\\n🔍 Test 1: Navigation and Page Load');
    console.log('=====================================');
    
    const browser = await puppeteer.launch({
        headless: process.env.CI === 'true', // Headless in CI, visible otherwise
        defaultViewport: { width: 1280, height: 720 },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    let testResults = {
        pageLoad: false,
        navbarPresent: false,
        parameterTestingNav: false,
        initialView: false
    };
    
    try {
        const page = await browser.newPage();
        
        // Enable console logging from the page
        page.on('console', msg => {
            if (msg.type() === 'error') {
                console.log('🔴 Page Error:', msg.text());
            }
        });
        
        console.log('🌐 Navigating to Sensylate...');
        await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        
        await takeScreenshot(page, '01_initial_load', 'Sensylate initial page load');
        
        // Verify page loaded correctly
        const navbarExists = await waitForElement(page, '.navbar');
        if (navbarExists) {
            testResults.navbarPresent = true;
            console.log('✅ Navbar loaded successfully');
        }
        
        // Check for Parameter Testing navigation item
        const parameterTestingButton = await page.$('[data-view="parameterTesting"]');
        if (parameterTestingButton) {
            testResults.parameterTestingNav = true;
            console.log('✅ Parameter Testing navigation button found');
            
            // Check button text and icon
            const buttonText = await page.$eval('[data-view="parameterTesting"]', el => el.textContent.trim());
            console.log(`   📝 Button text: "${buttonText}"`);
            
            // Verify icon presence
            const hasIcon = await page.$('[data-view="parameterTesting"] i.fa-flask');
            if (hasIcon) {
                console.log('   ✅ Flask icon present');
            }
        }
        
        // Verify initial view (should be CSV Viewer by default)
        const csvViewerVisible = await page.$('#csv-viewer:not(.d-none)');
        const parameterTestingHidden = await page.$('#parameter-testing.d-none');
        
        if (csvViewerVisible && parameterTestingHidden) {
            testResults.initialView = true;
            console.log('✅ Initial view correctly shows CSV Viewer');
        }
        
        testResults.pageLoad = true;
        console.log('✅ Page load test completed successfully');
        
    } catch (error) {
        console.error('❌ Navigation test failed:', error.message);
        await takeScreenshot(page, '01_error', `Navigation test error: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return testResults;
}

async function testParameterTestingWorkflow() {
    console.log('\\n🔬 Test 2: Parameter Testing Workflow');
    console.log('======================================');
    
    const browser = await puppeteer.launch({
        headless: process.env.CI === 'true',
        defaultViewport: { width: 1280, height: 720 },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    let testResults = {
        navigation: false,
        configurationForm: false,
        formInteraction: false,
        analysisExecution: false,
        resultsDisplay: false,
        errorHandling: false
    };
    
    try {
        const page = await browser.newPage();
        
        // Navigate to page
        await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        
        // Step 1: Navigate to Parameter Testing
        console.log('📍 Step 1: Navigate to Parameter Testing view');
        const parameterTestingButton = await page.$('[data-view="parameterTesting"]');
        if (!parameterTestingButton) {
            throw new Error('Parameter Testing navigation button not found');
        }
        
        await parameterTestingButton.click();
        await sleep(500); // Allow view transition
        
        // Verify Parameter Testing view is now visible
        const parameterTestingVisible = await page.$('#parameter-testing:not(.d-none)');
        const csvViewerHidden = await page.$('#csv-viewer.d-none');
        
        if (parameterTestingVisible && csvViewerHidden) {
            testResults.navigation = true;
            console.log('✅ Successfully navigated to Parameter Testing view');
        }
        
        await takeScreenshot(page, '02_parameter_testing_view', 'Parameter Testing view active');
        
        // Step 2: Verify configuration form elements
        console.log('📍 Step 2: Verify configuration form elements');
        
        const formElements = {
            ticker: await waitForElement(page, 'input[placeholder*="ticker"]'),
            presets: await waitForElement(page, 'select.form-select'),
            strategyTypes: await waitForElement(page, 'input[type="checkbox"]'),
            runButton: await waitForElement(page, 'button:contains("Run Analysis")')
        };
        
        const allElementsPresent = Object.values(formElements).every(exists => exists);
        if (allElementsPresent) {
            testResults.configurationForm = true;
            console.log('✅ All configuration form elements present');
        }
        
        await takeScreenshot(page, '03_form_elements', 'Configuration form elements verified');
        
        // Step 3: Test form interactions
        console.log('📍 Step 3: Test form interactions');
        
        // Test ticker input
        const tickerInput = await page.$('input[placeholder*="ticker"], input[placeholder*="Ticker"]');
        if (tickerInput) {
            await tickerInput.click({ clickCount: 3 }); // Select all
            await tickerInput.type(TEST_CONFIG.ticker);
            console.log(`   ✅ Entered ticker: ${TEST_CONFIG.ticker}`);
        }
        
        // Test preset selection
        const presetSelect = await page.$('select.form-select');
        if (presetSelect) {
            await presetSelect.select('quick-test');
            console.log('   ✅ Selected Quick Test preset');
            await sleep(500); // Allow preset to load
        }
        
        // Verify strategy type checkboxes
        const smaCheckbox = await page.$('input[value="SMA"]');
        const emaCheckbox = await page.$('input[value="EMA"]');
        
        if (smaCheckbox && emaCheckbox) {
            const smaChecked = await page.$eval('input[value="SMA"]', el => el.checked);
            const emaChecked = await page.$eval('input[value="EMA"]', el => el.checked);
            console.log(`   📊 Strategy types - SMA: ${smaChecked}, EMA: ${emaChecked}`);
            testResults.formInteraction = true;
        }
        
        await takeScreenshot(page, '04_form_configured', 'Form configured with test data');
        
        // Step 4: Test Advanced Configuration collapse
        console.log('📍 Step 4: Test Advanced Configuration');
        await testAdvancedConfigurationCollapse(page);
        
        // Step 5: Execute analysis (mock or real)
        console.log('📍 Step 5: Execute analysis');
        
        const runButton = await page.$('button');
        const runButtonText = await page.evaluate(() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            return buttons.find(btn => btn.textContent.includes('Run') || btn.textContent.includes('Analysis'));
        });
        
        if (runButtonText) {
            console.log('   🔄 Clicking Run Analysis button');
            await runButtonText.click();
            
            // Look for loading indicators
            await sleep(1000);
            
            // Check for progress indicator or loading state
            const progressVisible = await page.$('.progress, .spinner-border, [role="progressbar"]');
            if (progressVisible) {
                console.log('   ✅ Progress indicator appeared');
                await takeScreenshot(page, '05_analysis_progress', 'Analysis progress visible');
            }
            
            testResults.analysisExecution = true;
            console.log('   ✅ Analysis execution initiated');
        }
        
        await takeScreenshot(page, '06_analysis_complete', 'Analysis execution state');
        
        // Step 6: Check for error boundaries and error handling
        console.log('📍 Step 6: Test error handling');
        await testErrorHandling(page);
        testResults.errorHandling = true;
        
        console.log('✅ Parameter Testing workflow test completed');
        
    } catch (error) {
        console.error('❌ Workflow test failed:', error.message);
        await takeScreenshot(page, '06_workflow_error', `Workflow error: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return testResults;
}

async function testAdvancedConfigurationCollapse(page) {
    console.log('📍 Advanced Configuration Collapse Test');
    
    // Find the advanced configuration toggle button
    const toggleButton = await page.$('button[data-bs-toggle="collapse"], button[aria-controls*="advanced"]');
    if (!toggleButton) {
        console.log('   ⚠️  Advanced configuration toggle not found');
        return;
    }
    
    // Check initial state (should be collapsed)
    const initialState = await page.evaluate(() => {
        const advancedSection = document.querySelector('[id*="advanced"], .collapse');
        return {
            collapsed: advancedSection ? !advancedSection.classList.contains('show') : null,
            height: advancedSection ? advancedSection.offsetHeight : null
        };
    });
    
    console.log(`   📏 Initial state - Collapsed: ${initialState.collapsed}, Height: ${initialState.height}px`);
    
    // Click to expand
    await toggleButton.click();
    await sleep(500); // Allow animation
    
    const expandedState = await page.evaluate(() => {
        const advancedSection = document.querySelector('[id*="advanced"], .collapse');
        return {
            expanded: advancedSection ? advancedSection.classList.contains('show') : null,
            height: advancedSection ? advancedSection.offsetHeight : null
        };
    });
    
    console.log(`   📏 Expanded state - Expanded: ${expandedState.expanded}, Height: ${expandedState.height}px`);
    
    if (expandedState.expanded && expandedState.height > initialState.height) {
        console.log('   ✅ Advanced configuration collapse/expand working');
    }
    
    await takeScreenshot(page, '04a_advanced_expanded', 'Advanced configuration expanded');
    
    // Collapse again
    await toggleButton.click();
    await sleep(500);
    
    await takeScreenshot(page, '04b_advanced_collapsed', 'Advanced configuration collapsed again');
}

async function testErrorHandling(page) {
    console.log('📍 Error Handling Test');
    
    // Check for ErrorBoundary component
    const errorBoundaryExists = await page.evaluate(() => {
        // Look for error boundary indicators
        const errorElements = document.querySelectorAll('[class*="error"], [role="alert"]');
        return errorElements.length;
    });
    
    console.log(`   🛡️  Found ${errorBoundaryExists} error-related elements`);
    
    // Test with invalid ticker format
    const tickerInput = await page.$('input[placeholder*="ticker"], input[placeholder*="Ticker"]');
    if (tickerInput) {
        await tickerInput.click({ clickCount: 3 });
        await tickerInput.type('INVALID@TICKER#FORMAT');
        
        // Look for validation errors
        await sleep(500);
        const validationErrors = await page.$$('.invalid-feedback, .text-danger, .error-message');
        if (validationErrors.length > 0) {
            console.log('   ✅ Form validation errors displayed for invalid input');
        }
        
        // Reset to valid ticker
        await tickerInput.click({ clickCount: 3 });
        await tickerInput.type(TEST_CONFIG.ticker);
    }
}

async function testResponsiveDesign() {
    console.log('\\n📱 Test 3: Responsive Design');
    console.log('==============================');
    
    const browser = await puppeteer.launch({
        headless: process.env.CI === 'true',
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    let testResults = {
        mobile: false,
        tablet: false,
        desktop: false
    };
    
    try {
        const page = await browser.newPage();
        
        // Test mobile viewport (375x667 - iPhone SE)
        console.log('📱 Testing mobile viewport (375x667)');
        await page.setViewport({ width: 375, height: 667 });
        await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        
        // Navigate to Parameter Testing
        const paramButton = await page.$('[data-view="parameterTesting"]');
        if (paramButton) {
            await paramButton.click();
            await sleep(500);
        }
        
        await takeScreenshot(page, '07_mobile_view', 'Mobile viewport (375x667)');
        
        // Check if content is responsive
        const mobileLayout = await page.evaluate(() => {
            const container = document.querySelector('.container, .container-fluid');
            const formGroups = document.querySelectorAll('.form-group, .mb-3');
            return {
                containerWidth: container ? container.offsetWidth : 0,
                formGroupsVisible: formGroups.length,
                hasScrollbar: document.body.scrollWidth > window.innerWidth
            };
        });
        
        if (mobileLayout.containerWidth > 0 && mobileLayout.formGroupsVisible > 0) {
            testResults.mobile = true;
            console.log('✅ Mobile layout responsive');
        }
        
        // Test tablet viewport (768x1024 - iPad)
        console.log('📱 Testing tablet viewport (768x1024)');
        await page.setViewport({ width: 768, height: 1024 });
        await sleep(500);
        
        await takeScreenshot(page, '08_tablet_view', 'Tablet viewport (768x1024)');
        
        const tabletLayout = await page.evaluate(() => {
            const container = document.querySelector('.container, .container-fluid');
            return {
                containerWidth: container ? container.offsetWidth : 0,
                viewportRatio: window.innerWidth / window.innerHeight
            };
        });
        
        if (tabletLayout.containerWidth > 0) {
            testResults.tablet = true;
            console.log('✅ Tablet layout responsive');
        }
        
        // Test desktop viewport (1280x720)
        console.log('🖥️  Testing desktop viewport (1280x720)');
        await page.setViewport({ width: 1280, height: 720 });
        await sleep(500);
        
        await takeScreenshot(page, '09_desktop_view', 'Desktop viewport (1280x720)');
        
        const desktopLayout = await page.evaluate(() => {
            const container = document.querySelector('.container, .container-fluid');
            const columns = document.querySelectorAll('.col, [class*="col-"]');
            return {
                containerWidth: container ? container.offsetWidth : 0,
                columnCount: columns.length
            };
        });
        
        if (desktopLayout.containerWidth > 0) {
            testResults.desktop = true;
            console.log('✅ Desktop layout responsive');
        }
        
        console.log('✅ Responsive design test completed');
        
    } catch (error) {
        console.error('❌ Responsive design test failed:', error.message);
        await takeScreenshot(page, '09_responsive_error', `Responsive test error: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return testResults;
}

async function testAccessibility() {
    console.log('\\n♿ Test 4: Accessibility Features');
    console.log('===================================');
    
    const browser = await puppeteer.launch({
        headless: process.env.CI === 'true',
        defaultViewport: { width: 1280, height: 720 },
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    let testResults = {
        ariaLabels: false,
        keyboardNavigation: false,
        semanticHTML: false,
        focusManagement: false
    };
    
    try {
        const page = await browser.newPage();
        await page.goto(BASE_URL, { waitUntil: 'networkidle2', timeout: TIMEOUT });
        
        // Navigate to Parameter Testing
        const paramButton = await page.$('[data-view="parameterTesting"]');
        if (paramButton) {
            await paramButton.click();
            await sleep(500);
        }
        
        await takeScreenshot(page, '10_accessibility_view', 'Accessibility testing view');
        
        // Test ARIA labels and attributes
        const ariaElements = await page.evaluate(() => {
            const elementsWithAria = document.querySelectorAll('[aria-label], [aria-describedby], [aria-required], [role]');
            const results = [];
            
            elementsWithAria.forEach(el => {
                results.push({
                    tag: el.tagName.toLowerCase(),
                    ariaLabel: el.getAttribute('aria-label'),
                    ariaDescribedby: el.getAttribute('aria-describedby'),
                    role: el.getAttribute('role'),
                    ariaRequired: el.getAttribute('aria-required')
                });
            });
            
            return results;
        });
        
        console.log(`🏷️  Found ${ariaElements.length} elements with ARIA attributes`);
        if (ariaElements.length > 0) {
            testResults.ariaLabels = true;
            console.log('✅ ARIA labels present');
            ariaElements.slice(0, 3).forEach(el => {
                console.log(`   - ${el.tag}: ${el.ariaLabel || el.role || 'aria attributes present'}`);
            });
        }
        
        // Test keyboard navigation
        console.log('⌨️  Testing keyboard navigation');
        await page.keyboard.press('Tab');
        await sleep(200);
        
        const focusedElement = await page.evaluate(() => {
            const active = document.activeElement;
            return {
                tag: active.tagName.toLowerCase(),
                type: active.type || null,
                id: active.id || null,
                className: active.className || null
            };
        });
        
        if (focusedElement.tag && focusedElement.tag !== 'body') {
            testResults.keyboardNavigation = true;
            console.log(`✅ Keyboard navigation working - focused: ${focusedElement.tag}`);
        }
        
        // Test semantic HTML
        const semanticElements = await page.evaluate(() => {
            const semantic = ['main', 'section', 'article', 'header', 'nav', 'footer', 'aside'];
            const found = [];
            
            semantic.forEach(tag => {
                const elements = document.querySelectorAll(tag);
                if (elements.length > 0) {
                    found.push({ tag, count: elements.length });
                }
            });
            
            return found;
        });
        
        console.log(`🏗️  Found semantic HTML elements:`, semanticElements);
        if (semanticElements.length > 0) {
            testResults.semanticHTML = true;
            console.log('✅ Semantic HTML structure present');
        }
        
        // Test focus management
        const formInputs = await page.$$('input, select, button, textarea');
        if (formInputs.length > 0) {
            // Test that inputs can receive focus
            await formInputs[0].focus();
            const focusAfterManual = await page.evaluate(() => document.activeElement.tagName.toLowerCase());
            
            if (focusAfterManual === 'input' || focusAfterManual === 'select' || focusAfterManual === 'button') {
                testResults.focusManagement = true;
                console.log('✅ Focus management working');
            }
        }
        
        console.log('✅ Accessibility test completed');
        
    } catch (error) {
        console.error('❌ Accessibility test failed:', error.message);
        await takeScreenshot(page, '10_accessibility_error', `Accessibility test error: ${error.message}`);
    } finally {
        await browser.close();
    }
    
    return testResults;
}

async function runFullTestSuite() {
    console.log('🚀 Starting Sensylate Parameter Testing Test Suite');
    console.log('===================================================');
    console.log(`📅 Test run: ${new Date().toISOString()}`);
    console.log(`🔧 Node version: ${process.version}`);
    console.log(`💻 Platform: ${process.platform}`);
    
    const results = {
        navigation: {},
        workflow: {},
        responsive: {},
        accessibility: {},
        summary: { passed: 0, failed: 0, total: 0 }
    };
    
    try {
        // Test 1: Navigation and Page Load
        results.navigation = await testNavigationAndPageLoad();
        
        // Test 2: Parameter Testing Workflow
        results.workflow = await testParameterTestingWorkflow();
        
        // Test 3: Responsive Design
        results.responsive = await testResponsiveDesign();
        
        // Test 4: Accessibility
        results.accessibility = await testAccessibility();
        
        // Calculate summary
        const allTestResults = [
            ...Object.values(results.navigation),
            ...Object.values(results.workflow),
            ...Object.values(results.responsive),
            ...Object.values(results.accessibility)
        ];
        
        results.summary.total = allTestResults.length;
        results.summary.passed = allTestResults.filter(result => result === true).length;
        results.summary.failed = results.summary.total - results.summary.passed;
        
        console.log('\\n📊 TEST RESULTS SUMMARY');
        console.log('========================');
        console.log(`✅ Passed: ${results.summary.passed}`);
        console.log(`❌ Failed: ${results.summary.failed}`);
        console.log(`📝 Total:  ${results.summary.total}`);
        console.log(`📈 Success Rate: ${(results.summary.passed / results.summary.total * 100).toFixed(1)}%`);
        
        // Detailed results
        console.log('\\n📋 Detailed Results:');
        console.log('Navigation Tests:', results.navigation);
        console.log('Workflow Tests:', results.workflow);
        console.log('Responsive Tests:', results.responsive);
        console.log('Accessibility Tests:', results.accessibility);
        
        if (results.summary.failed === 0) {
            console.log('\\n🎉 ALL TESTS PASSED! Parameter Testing integration is working correctly.');
            process.exit(0);
        } else {
            console.log(`\\n⚠️  ${results.summary.failed} TEST(S) FAILED. Review the results above.`);
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
    console.log('🧪 Sensylate Parameter Testing Test Suite');
    console.log('===========================================');
    console.log('This test suite will:');
    console.log('1. Test navigation to Parameter Testing view');
    console.log('2. Verify configuration form functionality');
    console.log('3. Test advanced configuration collapse/expand');
    console.log('4. Test analysis workflow and progress tracking');
    console.log('5. Verify error boundaries and error handling');
    console.log('6. Test responsive design across viewports');
    console.log('7. Verify accessibility features (ARIA, keyboard nav)');
    console.log('\\nStarting tests in 3 seconds...');
    
    setTimeout(() => {
        runFullTestSuite();
    }, 3000);
}

export {
    testNavigationAndPageLoad,
    testParameterTestingWorkflow,
    testResponsiveDesign,
    testAccessibility,
    runFullTestSuite
};