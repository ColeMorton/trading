# Sensylate Parameter Testing Test Suite

Comprehensive Puppeteer-based testing for the Parameter Testing feature migration from SensitivityTrader to Sensylate.

## Overview

This test suite validates the complete Parameter Testing workflow implemented in **Phase 6** of the migration plan. It includes:

- ✅ Full workflow testing (navigation, configuration, analysis execution)
- ✅ BXP-specific analysis validation (matching SensitivityTrader patterns)  
- ✅ CSV export and validation functionality
- ✅ Advanced configuration collapse/expand testing
- ✅ Responsive design validation
- ✅ Accessibility compliance testing
- ✅ Error boundary and error handling validation

## Test Structure

```
tests/
├── README.md                    # This file
├── testRunner.js                # Master test orchestrator
├── parameterTesting.spec.js     # Main workflow tests
├── bxpAnalysis.spec.js          # BXP-specific analysis tests
├── csvValidation.spec.js        # CSV export/import tests
├── screenshots/                 # Generated screenshots (--screenshots)
└── downloads/                   # Test download directory
```

## Prerequisites

1. **Node.js 16+** - Required for ES modules and Puppeteer
2. **Vite dev server running** - Tests target `http://localhost:5173`
3. **Backend API available** - MA Cross endpoints should be accessible

## Installation

```bash
# Install Puppeteer (if not already installed)
npm install

# Install Puppeteer browsers
npx puppeteer browsers install
```

## Running Tests

### Quick Start
```bash
# Run all test suites
npm run test:e2e

# Run complete end-to-end workflow test
npm run test:e2e-workflow

# Run with screenshots enabled
npm run test:screenshots

# Run end-to-end workflow with screenshots and verbose output
npm run test:e2e-verbose

# Run in CI mode (headless, with report)
npm run test:ci
```

### Individual Test Suites
```bash
# Run specific test suites
npm run test:e2e-workflow  # Complete end-to-end workflow test
npm run test:workflow      # Main Parameter Testing workflow
npm run test:bxp          # BXP analysis validation  
npm run test:csv          # CSV functionality tests

# Run with verbose output
npm run test:verbose
npm run test:e2e-verbose  # End-to-end workflow with verbose output

# Screenshot management
npm run test:cleanup-screenshots         # Clean up old test screenshots
npm run test:cleanup-screenshots-verbose # Clean up with detailed logging
```

### Advanced Options
```bash
# Run test runner directly with options
node tests/testRunner.js --help
node tests/testRunner.js --screenshots --verbose
node tests/testRunner.js --ci --save-report
```

## Test Suites

### 1. End-to-End Workflow (`endToEndWorkflow.spec.js`)
**Critical Test Suite** - Tests complete user workflow

- ✅ **CSV Viewer Setup**: Load Daily.csv and update data
- ✅ **Table Interaction**: Sort by Signal Entry = True
- ✅ **Strategy Selection**: Identify strategy with lowest Long Window and Signal Entry = True
- ✅ **Navigation**: Switch to Parameter Testing view
- ✅ **Configuration**: Set up analysis with strategy details (ticker, windows, strategy type)
- ✅ **Options**: Enable Use Current Price and Refresh Data
- ✅ **Analysis Execution**: Run analysis and wait for completion
- ✅ **Results Validation**: Ensure returned results match strategy in focus

### 2. Parameter Testing Workflow (`parameterTesting.spec.js`)
**Critical Test Suite** - Tests core functionality

- ✅ **Navigation**: CSV Viewer ↔ Parameter Testing view switching
- ✅ **Form Configuration**: Ticker input, presets, strategy selection
- ✅ **Advanced Config**: Collapse/expand functionality
- ✅ **Analysis Execution**: Run button, progress tracking
- ✅ **Error Handling**: Form validation, error boundaries
- ✅ **Responsive Design**: Mobile, tablet, desktop viewports
- ✅ **Accessibility**: ARIA labels, keyboard navigation

### 3. BXP Analysis (`bxpAnalysis.spec.js`)
**Critical Test Suite** - Validates specific analysis case

- ✅ **Configuration**: BXP ticker setup with optimal settings
- ✅ **Analysis Execution**: Real analysis run with progress tracking
- ✅ **Result Validation**: Expected BXP SMA strategy results
- ✅ **API Integration**: MA Cross endpoint communication
- ✅ **Progress Tracking**: Loading states and completion detection

### 4. CSV Validation (`csvValidation.spec.js`)
**Non-Critical Test Suite** - Tests data export functionality

- ✅ **Export Functionality**: CSV download trigger and completion
- ✅ **File Structure**: Column validation and data integrity
- ✅ **CSV Viewer Integration**: File selection and data display
- ✅ **View Navigation**: Seamless switching between views

## Test Configuration

### Screenshot Capture
Screenshots are captured at key workflow points when `--screenshots` flag is used:

```
01_page_loaded.png          # Initial application load
02_parameter_testing.png    # Parameter Testing view
03_analysis_configured.png  # Form configuration complete
04_analysis_started.png     # Analysis execution initiated
05_analysis_complete.png    # Analysis results displayed
06_results_validation.png   # Result validation complete
07_final_state.png         # Final test state
```

#### Automatic Screenshot Cleanup
- **Old screenshots are automatically cleaned up** when new tests run with `--screenshots` flag
- Each test suite cleans up its own screenshot type (e.g., e2e tests clean up `e2e_*` files)
- Manual cleanup available with `npm run test:cleanup-screenshots`
- Prevents screenshot directories from accumulating too many files

### Environment Variables
- `CI=true` - Enables headless mode for automated testing
- `NODE_ENV=test` - Test environment configuration

## Test Results

### Success Criteria
- **Critical tests**: Must pass for overall success
- **Non-critical tests**: Allowed to fail without blocking success
- **Minimum success rate**: 70% for non-critical features

### Report Generation
Test reports are generated in JSON format:

```json
{
  "timestamp": "2024-12-30T...",
  "summary": {
    "total": 8,
    "passed": 7,
    "failed": 1,
    "criticalFailures": 0,
    "duration": 45000,
    "successRate": 87.5
  },
  "results": [...],
  "environment": {
    "nodeVersion": "v18.x.x",
    "platform": "darwin",
    "target": "http://localhost:5173"
  }
}
```

## Debugging

### Verbose Mode
```bash
npm run test:verbose
```
Shows detailed test output and browser interactions.

### Screenshots
```bash
npm run test:screenshots
```
Captures screenshots at each major step for visual debugging.

### Individual Test Files
```bash
# Run single test file with full output
node tests/parameterTesting.spec.js --screenshots --debug
```

## Browser Configuration

Tests use Puppeteer with the following settings:
- **Viewport**: 1280x720 (desktop), 768x1024 (tablet), 375x667 (mobile)
- **Timeout**: 30 seconds for most operations, 45 seconds for analysis
- **Headless**: Configurable via CI flag
- **Screenshots**: Full page capture with beyond-viewport content

## Integration with SensitivityTrader

These tests validate feature parity with the original SensitivityTrader implementation:

1. **BXP Analysis Pattern**: Matches SensitivityTrader's BXP test case
2. **UI Interactions**: Bootstrap collapse behavior matching original
3. **Form Validation**: Similar validation patterns and error messaging
4. **Progress Tracking**: Equivalent loading states and progress indicators

## Troubleshooting

### Common Issues

**"Navigation button not found"**
- Ensure Vite dev server is running on port 5173
- Check that Sensylate application loads correctly

**"Analysis timeout"** 
- Verify backend API is running and accessible
- Check MA Cross endpoints are responding
- Increase timeout in test configuration if needed

**"Screenshot directory creation failed"**
- Ensure write permissions in test directory
- Run tests with appropriate user permissions

**"Puppeteer browser not found"**
```bash
npx puppeteer browsers install
```

### Performance Tips

1. **Run tests sequentially** - Avoid parallel execution to prevent resource conflicts
2. **Use headless mode in CI** - Faster execution without GUI overhead
3. **Limit screenshot capture** - Only enable for debugging sessions
4. **Close unused applications** - Free up system resources during testing

## Development Workflow

When modifying Parameter Testing functionality:

1. **Run affected test suite**:
   ```bash
   npm run test:workflow  # For UI changes
   npm run test:bxp      # For analysis logic changes
   npm run test:csv      # For export functionality changes
   ```

2. **Update screenshots** if UI changes significantly:
   ```bash
   npm run test:screenshots
   ```

3. **Run full suite** before committing:
   ```bash
   npm run test:e2e
   ```

## Future Enhancements

Potential test suite improvements:

- **Performance testing** - Load time and analysis speed benchmarks
- **Cross-browser testing** - Firefox, Safari compatibility
- **API mocking** - Tests without backend dependency
- **Visual regression** - Screenshot comparison testing
- **Stress testing** - Multiple concurrent analyses

---

**Phase 6 Status**: ✅ **COMPLETED**  
All Puppeteer testing infrastructure and test suites have been implemented successfully.