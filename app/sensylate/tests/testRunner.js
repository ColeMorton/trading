import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';
import fs from 'fs';

/**
 * Master Test Runner for Sensylate Parameter Testing
 * Orchestrates all Puppeteer test suites with comprehensive reporting
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const TEST_SUITES = [
    {
        name: 'Parameter Testing Workflow',
        file: 'parameterTesting.spec.js',
        description: 'Complete Parameter Testing feature workflow',
        critical: true
    }
];

const COLORS = {
    reset: '\\x1b[0m',
    bright: '\\x1b[1m',
    red: '\\x1b[31m',
    green: '\\x1b[32m',
    yellow: '\\x1b[33m',
    blue: '\\x1b[34m',
    magenta: '\\x1b[35m',
    cyan: '\\x1b[36m'
};

function colorize(text, color) {
    return `${COLORS[color]}${text}${COLORS.reset}`;
}

function formatDuration(ms) {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
}

async function runTestSuite(suite, options = {}) {
    console.log(`\\n${colorize('🧪 Running:', 'cyan')} ${colorize(suite.name, 'bright')}`);
    console.log(`   ${suite.description}`);
    
    const startTime = Date.now();
    const testFile = path.join(__dirname, suite.file);
    
    // Check if test file exists
    if (!fs.existsSync(testFile)) {
        console.log(`   ${colorize('❌ Test file not found:', 'red')} ${suite.file}`);
        return {
            suite: suite.name,
            success: false,
            error: 'Test file not found',
            duration: 0
        };
    }
    
    return new Promise((resolve) => {
        const args = ['node', testFile];
        
        // Add screenshot flag if enabled
        if (options.screenshots) {
            args.push('--screenshots');
        }
        
        // Add debug flag if enabled
        if (options.debug) {
            args.push('--debug');
        }
        
        const child = spawn('node', [testFile, ...(options.screenshots ? ['--screenshots'] : [])], {
            stdio: 'pipe',
            cwd: __dirname,
            env: { ...process.env, CI: options.ci ? 'true' : 'false' }
        });
        
        let stdout = '';
        let stderr = '';
        
        child.stdout.on('data', (data) => {
            const output = data.toString();
            stdout += output;
            if (options.verbose) {
                process.stdout.write(`   ${output}`);
            }
        });
        
        child.stderr.on('data', (data) => {
            const output = data.toString();
            stderr += output;
            if (options.verbose) {
                process.stderr.write(`   ${colorize(output, 'red')}`);
            }
        });
        
        child.on('close', (code) => {
            const duration = Date.now() - startTime;
            const success = code === 0;
            
            console.log(`   ${success ? colorize('✅ PASSED', 'green') : colorize('❌ FAILED', 'red')} in ${formatDuration(duration)}`);
            
            if (!success && !options.verbose) {
                console.log(`   ${colorize('Error output:', 'red')}`);
                console.log(`   ${stderr || stdout.split('\\n').slice(-5).join('\\n')}`);
            }
            
            resolve({
                suite: suite.name,
                success,
                code,
                duration,
                stdout: options.saveOutput ? stdout : null,
                stderr: options.saveOutput ? stderr : null,
                critical: suite.critical
            });
        });
        
        child.on('error', (error) => {
            const duration = Date.now() - startTime;
            console.log(`   ${colorize('❌ ERROR', 'red')}: ${error.message}`);
            
            resolve({
                suite: suite.name,
                success: false,
                error: error.message,
                duration,
                critical: suite.critical
            });
        });
    });
}

async function checkPrerequisites() {
    console.log(`${colorize('🔍 Checking Prerequisites', 'blue')}`);
    console.log('========================');
    
    const checks = {
        nodeVersion: process.version,
        testServer: false,
        screenshotDir: false,
        downloadDir: false
    };
    
    // Check Node.js version
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.slice(1).split('.')[0]);
    if (majorVersion >= 16) {
        console.log(`✅ Node.js version: ${nodeVersion}`);
    } else {
        console.log(`⚠️  Node.js version: ${nodeVersion} (recommend >=16)`);
    }
    
    // Create necessary directories
    const screenshotDir = path.join(__dirname, '../screenshots');
    const downloadDir = path.join(__dirname, '../downloads');
    
    try {
        if (!fs.existsSync(screenshotDir)) {
            fs.mkdirSync(screenshotDir, { recursive: true });
        }
        checks.screenshotDir = true;
        console.log(`✅ Screenshot directory: ${screenshotDir}`);
    } catch (error) {
        console.log(`❌ Screenshot directory creation failed: ${error.message}`);
    }
    
    try {
        if (!fs.existsSync(downloadDir)) {
            fs.mkdirSync(downloadDir, { recursive: true });
        }
        checks.downloadDir = true;
        console.log(`✅ Download directory: ${downloadDir}`);
    } catch (error) {
        console.log(`❌ Download directory creation failed: ${error.message}`);
    }
    
    // Basic server connectivity check (optional)
    console.log(`📡 Target server: http://localhost:5173`);
    console.log(`   ${colorize('Note:', 'yellow')} Ensure Vite dev server is running with 'npm run dev'`);
    
    return checks;
}

function generateReport(results, options = {}) {
    const totalTests = results.length;
    const passedTests = results.filter(r => r.success).length;
    const failedTests = totalTests - passedTests;
    const criticalFailures = results.filter(r => !r.success && r.critical).length;
    const totalDuration = results.reduce((sum, r) => sum + r.duration, 0);
    
    console.log(`\\n${colorize('📊 TEST RESULTS SUMMARY', 'magenta')}`);
    console.log('========================');
    console.log(`📅 Test run: ${new Date().toISOString()}`);
    console.log(`⏱️  Total duration: ${formatDuration(totalDuration)}`);
    console.log(`📝 Test suites: ${totalTests}`);
    console.log(`${colorize('✅ Passed:', 'green')} ${passedTests}`);
    console.log(`${colorize('❌ Failed:', 'red')} ${failedTests}`);
    console.log(`📈 Success rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
    
    if (criticalFailures > 0) {
        console.log(`${colorize('🚨 Critical failures:', 'red')} ${criticalFailures}`);
    }
    
    console.log('\\n📋 Detailed Results:');
    results.forEach((result, index) => {
        const status = result.success ? colorize('✅ PASS', 'green') : colorize('❌ FAIL', 'red');
        const critical = result.critical ? colorize(' (CRITICAL)', 'red') : '';
        const duration = formatDuration(result.duration);
        
        console.log(`${index + 1}. ${status} ${result.suite}${critical} (${duration})`);
        
        if (!result.success && result.error) {
            console.log(`   ${colorize('Error:', 'red')} ${result.error}`);
        }
    });
    
    // Save detailed report if requested
    if (options.saveReport) {
        const reportPath = path.join(__dirname, '../test-report.json');
        const reportData = {
            timestamp: new Date().toISOString(),
            summary: {
                total: totalTests,
                passed: passedTests,
                failed: failedTests,
                criticalFailures,
                duration: totalDuration,
                successRate: (passedTests / totalTests) * 100
            },
            results,
            environment: {
                nodeVersion: process.version,
                platform: process.platform,
                target: 'http://localhost:5173'
            }
        };
        
        try {
            fs.writeFileSync(reportPath, JSON.stringify(reportData, null, 2));
            console.log(`\\n📄 Detailed report saved: ${reportPath}`);
        } catch (error) {
            console.log(`\\n❌ Failed to save report: ${error.message}`);
        }
    }
    
    // Determine overall result
    const overallSuccess = criticalFailures === 0 && passedTests >= (totalTests * 0.7);
    
    if (overallSuccess) {
        console.log(`\\n${colorize('🎉 OVERALL RESULT: PASSED', 'green')}`);
        console.log('Sensylate Parameter Testing implementation is working correctly!');
        return { success: true, results };
    } else {
        console.log(`\\n${colorize('💥 OVERALL RESULT: FAILED', 'red')}`);
        if (criticalFailures > 0) {
            console.log('Critical test failures detected. Core functionality may be broken.');
        } else {
            console.log('Some tests failed but core functionality appears to be working.');
        }
        return { success: false, results };
    }
}

async function runAllTests(options = {}) {
    console.log(`${colorize('🚀 Sensylate Parameter Testing Test Suite', 'bright')}`);
    console.log('=============================================');
    console.log(`${colorize('Phase 6:', 'cyan')} Puppeteer Testing Implementation`);
    console.log(`📅 Started: ${new Date().toLocaleString()}`);
    
    if (options.screenshots) {
        console.log(`📷 Screenshots: ${colorize('ENABLED', 'green')}`);
    }
    
    if (options.ci) {
        console.log(`🤖 CI Mode: ${colorize('ENABLED', 'blue')} (headless browser)`);
    }
    
    // Check prerequisites
    const prerequisites = await checkPrerequisites();
    
    if (!prerequisites.screenshotDir || !prerequisites.downloadDir) {
        console.log(`\\n${colorize('❌ Prerequisites check failed', 'red')}`);
        return { success: false, error: 'Prerequisites not met' };
    }
    
    console.log(`\\n${colorize('🧪 Running Test Suites', 'blue')}`);
    console.log('======================');
    
    const results = [];
    
    // Run each test suite
    for (const suite of TEST_SUITES) {
        try {
            const result = await runTestSuite(suite, options);
            results.push(result);
            
            // Add delay between test suites to prevent resource conflicts
            if (results.length < TEST_SUITES.length) {
                await new Promise(resolve => setTimeout(resolve, 2000));
            }
        } catch (error) {
            console.log(`   ${colorize('❌ Suite execution failed:', 'red')} ${error.message}`);
            results.push({
                suite: suite.name,
                success: false,
                error: error.message,
                duration: 0,
                critical: suite.critical
            });
        }
    }
    
    // Generate and display report
    return generateReport(results, options);
}

// Parse command line arguments
function parseArgs() {
    const args = process.argv.slice(2);
    const options = {
        screenshots: args.includes('--screenshots'),
        verbose: args.includes('--verbose') || args.includes('-v'),
        ci: args.includes('--ci') || process.env.CI === 'true',
        debug: args.includes('--debug'),
        saveOutput: args.includes('--save-output'),
        saveReport: args.includes('--save-report') || args.includes('--ci'),
        help: args.includes('--help') || args.includes('-h')
    };
    
    return options;
}

function showHelp() {
    console.log(`${colorize('Sensylate Parameter Testing Test Runner', 'bright')}`);
    console.log('Usage: node testRunner.js [options]\\n');
    console.log('Options:');
    console.log('  --screenshots    Enable screenshot capture during tests');
    console.log('  --verbose, -v    Show detailed test output');
    console.log('  --ci             Run in CI mode (headless, save report)');
    console.log('  --debug          Enable debug mode');
    console.log('  --save-output    Save test output to results');
    console.log('  --save-report    Save detailed JSON report');
    console.log('  --help, -h       Show this help message\\n');
    console.log('Examples:');
    console.log('  node testRunner.js                    # Run all tests');
    console.log('  node testRunner.js --screenshots      # Run with screenshots');
    console.log('  node testRunner.js --verbose --ci     # CI mode with verbose output');
}

// Main execution
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    const options = parseArgs();
    
    if (options.help) {
        showHelp();
        process.exit(0);
    }
    
    console.log(`${colorize('🎯 Starting Parameter Testing Validation', 'cyan')}`);
    console.log('This will validate the complete Parameter Testing migration from SensitivityTrader to Sensylate.\\n');
    
    if (!options.ci) {
        console.log(`${colorize('💡 Tip:', 'yellow')} Use --screenshots to capture test screenshots`);
        console.log(`${colorize('🚀 Make sure:', 'yellow')} Vite dev server is running (npm run dev)`);
        console.log('\\nStarting tests in 3 seconds...');
        
        setTimeout(async () => {
            const result = await runAllTests(options);
            process.exit(result.success ? 0 : 1);
        }, 3000);
    } else {
        // Run immediately in CI mode
        runAllTests(options).then(result => {
            process.exit(result.success ? 0 : 1);
        }).catch(error => {
            console.error(`${colorize('💥 Test runner failed:', 'red')} ${error.message}`);
            process.exit(1);
        });
    }
}

export { runAllTests, runTestSuite, TEST_SUITES };