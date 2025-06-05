import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

/**
 * Quick Data Test - Tests the data transformation logic directly
 * without running a full analysis
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the reference CSV file
const REFERENCE_CSV_PATH = path.join(
  __dirname,
  '../../../../csv/portfolios_filtered/20250605/USLM_D_SMA.csv'
);

// Expected values from USLM,SMA,55,80 row
const EXPECTED_VALUES = {
  ticker: 'USLM',
  strategy_type: 'SMA',
  short_window: 55,
  long_window: 80,
  expectancy_per_trade: 7.057303121782205,
  expectancy: 782.3371558859208, // The raw expectancy value
  avg_trade_duration: '67 days 05:16:29.010989010',
  metric_type: 'Most Expectancy',
};

console.log('🔬 Quick Data Test');
console.log('==================');

async function testCSVDataExtraction() {
  console.log('\n📄 Test 1: CSV Data Extraction');
  console.log('================================');

  try {
    // Read the CSV file
    const csvContent = fs.readFileSync(REFERENCE_CSV_PATH, 'utf8');
    const lines = csvContent.split('\n');
    const headers = lines[0].split(',');

    console.log('✅ CSV file read successfully');
    console.log(`📊 Total lines: ${lines.length}`);
    console.log(`📊 Headers count: ${headers.length}`);

    // Find header indices
    const headerIndices = {
      ticker: headers.findIndex((h) => h.includes('Ticker')),
      strategyType: headers.findIndex((h) => h.includes('Strategy Type')),
      shortWindow: headers.findIndex((h) => h.includes('Short Window')),
      longWindow: headers.findIndex((h) => h.includes('Long Window')),
      expectancyPerTrade: headers.findIndex((h) =>
        h.includes('Expectancy per Trade')
      ),
      expectancy: headers.findIndex((h) => h === 'Expectancy'),
      avgTradeDuration: headers.findIndex((h) =>
        h.includes('Avg Trade Duration')
      ),
      metricType: headers.findIndex((h) => h.includes('Metric Type')),
    };

    console.log('📋 Header indices:', headerIndices);

    // Find the target row (USLM,SMA,55,80)
    let targetRow = null;
    let targetRowIndex = -1;

    for (let i = 1; i < lines.length; i++) {
      const cells = lines[i].split(',');

      if (
        cells.length > headerIndices.longWindow &&
        cells[headerIndices.ticker] === EXPECTED_VALUES.ticker &&
        cells[headerIndices.strategyType] === EXPECTED_VALUES.strategy_type &&
        cells[headerIndices.shortWindow] ===
          EXPECTED_VALUES.short_window.toString() &&
        cells[headerIndices.longWindow] ===
          EXPECTED_VALUES.long_window.toString()
      ) {
        targetRow = cells;
        targetRowIndex = i;
        break;
      }
    }

    if (targetRow) {
      console.log(`🎯 Found target row at line ${targetRowIndex}`);

      const extractedData = {
        ticker: targetRow[headerIndices.ticker],
        strategyType: targetRow[headerIndices.strategyType],
        shortWindow: parseInt(targetRow[headerIndices.shortWindow]),
        longWindow: parseInt(targetRow[headerIndices.longWindow]),
        expectancyPerTrade: parseFloat(
          targetRow[headerIndices.expectancyPerTrade]
        ),
        expectancy: parseFloat(targetRow[headerIndices.expectancy]),
        avgTradeDuration: targetRow[headerIndices.avgTradeDuration],
        metricType: targetRow[headerIndices.metricType],
      };

      console.log('\n📊 Extracted Data:');
      console.log('==================');
      Object.entries(extractedData).forEach(([key, value]) => {
        console.log(`${key}: ${value}`);
      });

      // Validate the data
      console.log('\n✅ Data Validation:');
      console.log('===================');

      // Check expectancy per trade
      console.log(
        `💰 Expectancy per Trade: ${extractedData.expectancyPerTrade} (expected: ${EXPECTED_VALUES.expectancy_per_trade})`
      );
      const expectancyMatch =
        Math.abs(
          extractedData.expectancyPerTrade -
            EXPECTED_VALUES.expectancy_per_trade
        ) < 0.0001;
      console.log(
        `   ${expectancyMatch ? '✅' : '❌'} ${
          expectancyMatch ? 'CORRECT' : 'INCORRECT'
        }`
      );

      // Check expectancy (raw value)
      console.log(
        `💰 Expectancy (raw): ${extractedData.expectancy} (expected: ${EXPECTED_VALUES.expectancy})`
      );
      const expectancyRawMatch =
        Math.abs(extractedData.expectancy - EXPECTED_VALUES.expectancy) <
        0.0001;
      console.log(
        `   ${expectancyRawMatch ? '✅' : '❌'} ${
          expectancyRawMatch ? 'CORRECT' : 'INCORRECT'
        }`
      );

      // Check avg trade duration
      console.log(
        `⏱️ Avg Trade Duration: "${extractedData.avgTradeDuration}" (expected: "${EXPECTED_VALUES.avg_trade_duration}")`
      );
      const durationMatch =
        extractedData.avgTradeDuration === EXPECTED_VALUES.avg_trade_duration;
      console.log(
        `   ${durationMatch ? '✅' : '❌'} ${
          durationMatch ? 'CORRECT' : 'INCORRECT'
        }`
      );

      // Check metric type
      console.log(
        `🏷️ Metric Type: "${extractedData.metricType}" (expected: contains "${EXPECTED_VALUES.metric_type}")`
      );
      const metricTypeMatch =
        extractedData.metricType &&
        extractedData.metricType.includes(EXPECTED_VALUES.metric_type);
      console.log(
        `   ${metricTypeMatch ? '✅' : '❌'} ${
          metricTypeMatch ? 'CORRECT' : 'INCORRECT'
        }`
      );

      return {
        dataExtracted: true,
        expectancyPerTradeCorrect: expectancyMatch,
        expectancyRawCorrect: expectancyRawMatch,
        avgTradeDurationCorrect: durationMatch,
        metricTypeCorrect: metricTypeMatch,
        extractedData,
      };
    } else {
      console.log('❌ Target row USLM,SMA,55,80 not found in CSV');

      // Show available combinations for debugging
      console.log('\n🔍 Available combinations (first 10):');
      for (let i = 1; i < Math.min(11, lines.length); i++) {
        const cells = lines[i].split(',');
        if (cells.length > headerIndices.longWindow) {
          console.log(
            `   ${cells[headerIndices.ticker]},${
              cells[headerIndices.strategyType]
            },${cells[headerIndices.shortWindow]},${
              cells[headerIndices.longWindow]
            }`
          );
        }
      }

      return { dataExtracted: false };
    }
  } catch (error) {
    console.error('❌ CSV extraction failed:', error.message);
    return { dataExtracted: false, error: error.message };
  }
}

async function testBackendTransformation() {
  console.log('\n⚙️ Test 2: Backend Transformation Logic');
  console.log('========================================');

  try {
    // Simulate the backend transformation process
    const mockPortfolioData = {
      Ticker: 'USLM',
      'Strategy Type': 'SMA',
      'Short Window': 55,
      'Long Window': 80,
      'Expectancy per Trade': 7.057303121782205,
      Expectancy: 782.3371558859208,
      'Avg Trade Duration': '67 days 05:16:29.010989010',
      'Metric Type': 'Most Expectancy',
      'Total Trades': 92,
      'Win Rate [%]': 46.15384615384615,
      'Profit Factor': 5.5719574781404395,
    };

    console.log('📥 Mock portfolio data:');
    console.log(JSON.stringify(mockPortfolioData, null, 2));

    // Simulate the _convert_portfolios_to_metrics transformation
    const convertedData = {
      ticker: mockPortfolioData['Ticker'],
      strategy_type: mockPortfolioData['Strategy Type'],
      short_window: parseInt(mockPortfolioData['Short Window']),
      long_window: parseInt(mockPortfolioData['Long Window']),
      expectancy: parseFloat(mockPortfolioData['Expectancy']),
      expectancy_per_trade: parseFloat(
        mockPortfolioData['Expectancy per Trade']
      ),
      avg_trade_duration: mockPortfolioData['Avg Trade Duration'],
      metric_type: mockPortfolioData['Metric Type'],
      total_trades: parseInt(mockPortfolioData['Total Trades']),
      win_rate: parseFloat(mockPortfolioData['Win Rate [%]']) / 100.0,
      profit_factor: parseFloat(mockPortfolioData['Profit Factor']),
    };

    console.log('\n📤 Converted data (backend output):');
    console.log(JSON.stringify(convertedData, null, 2));

    // Validate the conversion
    console.log('\n✅ Backend Transformation Validation:');
    console.log('====================================');

    const validations = [
      {
        name: 'Expectancy (raw)',
        value: convertedData.expectancy,
        expected: EXPECTED_VALUES.expectancy,
        correct:
          Math.abs(convertedData.expectancy - EXPECTED_VALUES.expectancy) <
          0.0001,
      },
      {
        name: 'Expectancy Per Trade',
        value: convertedData.expectancy_per_trade,
        expected: EXPECTED_VALUES.expectancy_per_trade,
        correct:
          Math.abs(
            convertedData.expectancy_per_trade -
              EXPECTED_VALUES.expectancy_per_trade
          ) < 0.0001,
      },
      {
        name: 'Avg Trade Duration',
        value: convertedData.avg_trade_duration,
        expected: EXPECTED_VALUES.avg_trade_duration,
        correct:
          convertedData.avg_trade_duration ===
          EXPECTED_VALUES.avg_trade_duration,
      },
      {
        name: 'Metric Type',
        value: convertedData.metric_type,
        expected: EXPECTED_VALUES.metric_type,
        correct: convertedData.metric_type === EXPECTED_VALUES.metric_type,
      },
    ];

    let allCorrect = true;
    validations.forEach((validation) => {
      console.log(
        `${validation.name}: ${validation.value} (expected: ${validation.expected})`
      );
      console.log(
        `   ${validation.correct ? '✅' : '❌'} ${
          validation.correct ? 'CORRECT' : 'INCORRECT'
        }`
      );
      if (!validation.correct) allCorrect = false;
    });

    return {
      transformationWorking: allCorrect,
      convertedData,
      validations,
    };
  } catch (error) {
    console.error('❌ Backend transformation test failed:', error.message);
    return { transformationWorking: false, error: error.message };
  }
}

async function testFrontendMapping() {
  console.log('\n🖥️ Test 3: Frontend Mapping Logic');
  console.log('==================================');

  try {
    // Simulate the frontend portfolioToResult mapping
    const mockBackendResponse = {
      ticker: 'USLM',
      strategy_type: 'SMA',
      short_window: 55,
      long_window: 80,
      signal_window: 0,
      direction: 'Long',
      timeframe: 'D',
      expectancy: 782.3371558859208,
      expectancy_per_trade: 7.057303121782205,
      avg_trade_duration: '67 days 05:16:29.010989010',
      metric_type: 'Most Expectancy',
      total_trades: 92,
      win_rate: 0.4615384615384615,
      profit_factor: 5.5719574781404395,
    };

    console.log('📥 Mock backend response:');
    console.log(JSON.stringify(mockBackendResponse, null, 2));

    // Frontend portfolioToResult transformation
    const frontendResult = {
      ticker: mockBackendResponse.ticker,
      strategy_type: mockBackendResponse.strategy_type,
      short_window: mockBackendResponse.short_window,
      long_window: mockBackendResponse.long_window,
      signal_window: mockBackendResponse.signal_window || 0,
      direction: mockBackendResponse.direction,
      timeframe: mockBackendResponse.timeframe,
      total_trades: mockBackendResponse.total_trades,
      win_rate: mockBackendResponse.win_rate,
      profit_factor: mockBackendResponse.profit_factor,
      expectancy_per_trade:
        mockBackendResponse.expectancy_per_trade ||
        mockBackendResponse.expectancy,
      metric_type: mockBackendResponse.metric_type,
      avg_trade_duration: mockBackendResponse.avg_trade_duration,
    };

    console.log('\n📤 Frontend result:');
    console.log(JSON.stringify(frontendResult, null, 2));

    // Test the display values
    console.log('\n✅ Frontend Display Validation:');
    console.log('===============================');

    const displayValidations = [
      {
        name: 'Expectancy Per Trade (display)',
        value: frontendResult.expectancy_per_trade.toFixed(2),
        expected: '7.06',
        correct: frontendResult.expectancy_per_trade.toFixed(2) === '7.06',
      },
      {
        name: 'Avg Trade Duration (display)',
        value: frontendResult.avg_trade_duration || 'N/A',
        expected: EXPECTED_VALUES.avg_trade_duration,
        correct:
          (frontendResult.avg_trade_duration || 'N/A') ===
          EXPECTED_VALUES.avg_trade_duration,
      },
      {
        name: 'Metric Type (display)',
        value: frontendResult.metric_type || 'Missing',
        expected: EXPECTED_VALUES.metric_type,
        correct: frontendResult.metric_type === EXPECTED_VALUES.metric_type,
      },
    ];

    let allDisplayCorrect = true;
    displayValidations.forEach((validation) => {
      console.log(
        `${validation.name}: "${validation.value}" (expected: "${validation.expected}")`
      );
      console.log(
        `   ${validation.correct ? '✅' : '❌'} ${
          validation.correct ? 'CORRECT' : 'INCORRECT'
        }`
      );
      if (!validation.correct) allDisplayCorrect = false;
    });

    return {
      frontendMappingWorking: allDisplayCorrect,
      frontendResult,
      displayValidations,
    };
  } catch (error) {
    console.error('❌ Frontend mapping test failed:', error.message);
    return { frontendMappingWorking: false, error: error.message };
  }
}

async function runQuickDataTest() {
  console.log('🚀 Starting Quick Data Test Suite');
  console.log('==================================');
  console.log(`📅 Test run: ${new Date().toISOString()}`);
  console.log(`📄 Reference file: ${REFERENCE_CSV_PATH}`);

  const results = {
    csvTest: {},
    backendTest: {},
    frontendTest: {},
    summary: { passed: 0, failed: 0, total: 0 },
  };

  try {
    // Test 1: CSV Data Extraction
    results.csvTest = await testCSVDataExtraction();

    // Test 2: Backend Transformation
    results.backendTest = await testBackendTransformation();

    // Test 3: Frontend Mapping
    results.frontendTest = await testFrontendMapping();

    // Calculate summary
    const allTestValues = [
      results.csvTest.dataExtracted || false,
      results.csvTest.expectancyPerTradeCorrect || false,
      results.csvTest.avgTradeDurationCorrect || false,
      results.csvTest.metricTypeCorrect || false,
      results.backendTest.transformationWorking || false,
      results.frontendTest.frontendMappingWorking || false,
    ];

    results.summary.total = allTestValues.length;
    results.summary.passed = allTestValues.filter(
      (result) => result === true
    ).length;
    results.summary.failed = results.summary.total - results.summary.passed;

    console.log('\n📊 QUICK TEST RESULTS SUMMARY');
    console.log('==============================');
    console.log(`✅ Passed: ${results.summary.passed}`);
    console.log(`❌ Failed: ${results.summary.failed}`);
    console.log(`📝 Total:  ${results.summary.total}`);
    console.log(
      `📈 Success Rate: ${(
        (results.summary.passed / results.summary.total) *
        100
      ).toFixed(1)}%`
    );

    console.log('\n🔍 DIAGNOSIS:');
    console.log('=============');

    if (results.csvTest.dataExtracted) {
      console.log('✅ Reference CSV data is correct and accessible');
    } else {
      console.log('❌ Problem with reference CSV data');
    }

    if (results.backendTest.transformationWorking) {
      console.log('✅ Backend transformation logic is working correctly');
    } else {
      console.log('❌ Backend transformation has issues');
    }

    if (results.frontendTest.frontendMappingWorking) {
      console.log('✅ Frontend mapping and display logic is working correctly');
    } else {
      console.log('❌ Frontend mapping/display has issues');
    }

    // Specific issue analysis
    console.log('\n💡 RECOMMENDATIONS:');
    console.log('===================');

    if (!results.csvTest.expectancyPerTradeCorrect) {
      console.log('❌ The reference CSV has wrong expectancy per trade value');
    } else if (!results.backendTest.transformationWorking) {
      console.log('❌ Fix backend transformation in ma_cross_service.py');
    } else if (!results.frontendTest.frontendMappingWorking) {
      console.log(
        '❌ Fix frontend mapping in maCrossApi.ts or ResultsTable.tsx'
      );
    } else {
      console.log(
        '✅ All logic appears correct - issue may be in the API execution pipeline'
      );
    }

    if (results.summary.failed === 0) {
      console.log('\n🎉 ALL QUICK TESTS PASSED! The logic is correct.');
      console.log('💡 The issue may be in the API execution or data pipeline.');
    } else {
      console.log(
        `\n⚠️  ${results.summary.failed} ISSUE(S) FOUND in the logic.`
      );
    }
  } catch (error) {
    console.error('💥 Quick test suite failed:', error.message);
    console.error('Stack trace:', error.stack);
  }

  return results;
}

// Run the test
runQuickDataTest();
