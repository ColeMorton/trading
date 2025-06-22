#!/usr/bin/env node

/**
 * Performance Testing Script for Position Sizing System
 * Runs automated performance tests and generates reports
 */

import puppeteer from 'puppeteer';
import { writeFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

class PerformanceTester {
  constructor(options = {}) {
    this.baseUrl = options.baseUrl || 'http://localhost:5173';
    this.iterations = options.iterations || 5;
    this.outputDir = options.outputDir || join(__dirname, '../reports');
    this.results = [];
  }

  async runTests() {
    console.log('🚀 Starting Position Sizing Performance Tests');
    console.log(`Base URL: ${this.baseUrl}`);
    console.log(`Iterations: ${this.iterations}`);

    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-dev-shm-usage'],
    });

    try {
      await this.testDashboardLoad(browser);
      await this.testKellyInputPerformance(browser);
      await this.testPositionEntryPerformance(browser);
      await this.testChartRenderingPerformance(browser);
      await this.testScenarioAnalysisPerformance(browser);
      await this.testMemoryUsage(browser);

      this.generateReport();
    } finally {
      await browser.close();
    }
  }

  async testDashboardLoad(browser) {
    console.log('📊 Testing Dashboard Load Performance');

    const results = [];

    for (let i = 0; i < this.iterations; i++) {
      const page = await browser.newPage();

      // Enable performance monitoring
      await page.evaluateOnNewDocument(() => {
        window.performanceMarks = [];
        const originalMark = performance.mark;
        performance.mark = function (name) {
          window.performanceMarks.push({ name, time: Date.now() });
          return originalMark.call(this, name);
        };
      });

      const startTime = Date.now();

      await page.goto(this.baseUrl);
      await page.waitForSelector('[data-testid="app-container"]');

      // Navigate to Position Sizing
      await page.click('[data-testid="nav-position-sizing"]');
      const loadStart = Date.now();

      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');
      await page.waitForSelector('[data-testid="portfolio-risk-panel"]');
      await page.waitForSelector('[data-testid="risk-allocation-buckets"]');

      const loadTime = Date.now() - loadStart;
      const totalTime = Date.now() - startTime;

      // Get performance metrics from page
      const metrics = await page.evaluate(() => {
        const perfEntries = performance.getEntriesByType('navigation')[0];
        return {
          domContentLoaded:
            perfEntries.domContentLoadedEventEnd - perfEntries.navigationStart,
          loadComplete: perfEntries.loadEventEnd - perfEntries.navigationStart,
          firstPaint:
            performance
              .getEntriesByType('paint')
              .find((entry) => entry.name === 'first-paint')?.startTime || 0,
          firstContentfulPaint:
            performance
              .getEntriesByType('paint')
              .find((entry) => entry.name === 'first-contentful-paint')
              ?.startTime || 0,
        };
      });

      results.push({
        iteration: i + 1,
        dashboardLoadTime: loadTime,
        totalTime,
        ...metrics,
      });

      await page.close();
      console.log(`  Iteration ${i + 1}: ${loadTime}ms dashboard load`);
    }

    this.results.push({
      testName: 'Dashboard Load Performance',
      results,
      averageLoadTime:
        results.reduce((sum, r) => sum + r.dashboardLoadTime, 0) /
        results.length,
      minLoadTime: Math.min(...results.map((r) => r.dashboardLoadTime)),
      maxLoadTime: Math.max(...results.map((r) => r.dashboardLoadTime)),
    });
  }

  async testKellyInputPerformance(browser) {
    console.log('📈 Testing Kelly Input Performance');

    const results = [];

    for (let i = 0; i < this.iterations; i++) {
      const page = await browser.newPage();
      await page.goto(this.baseUrl);
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="kelly-input-form"]');

      const startTime = Date.now();

      // Fill Kelly form
      await page.type('[data-testid="kelly-criterion-input"]', '0.25');
      await page.select(
        '[data-testid="kelly-source-select"]',
        'Trading Journal'
      );
      await page.type(
        '[data-testid="kelly-notes"]',
        'Performance test iteration ' + (i + 1)
      );

      // Submit and wait for response
      await page.click('[data-testid="kelly-save-button"]');
      await page.waitForSelector('[data-testid="kelly-success-message"]', {
        timeout: 5000,
      });

      const responseTime = Date.now() - startTime;

      results.push({
        iteration: i + 1,
        responseTime,
      });

      await page.close();
      console.log(`  Iteration ${i + 1}: ${responseTime}ms Kelly update`);
    }

    this.results.push({
      testName: 'Kelly Input Performance',
      results,
      averageResponseTime:
        results.reduce((sum, r) => sum + r.responseTime, 0) / results.length,
    });
  }

  async testPositionEntryPerformance(browser) {
    console.log('💼 Testing Position Entry Performance');

    const results = [];

    for (let i = 0; i < this.iterations; i++) {
      const page = await browser.newPage();
      await page.goto(this.baseUrl);
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

      const startTime = Date.now();

      // Open position entry modal
      await page.click('[data-testid="add-position-button"]');
      await page.waitForSelector('[data-testid="position-entry-modal"]');

      const modalOpenTime = Date.now() - startTime;

      // Fill form
      const formFillStart = Date.now();
      await page.type('[data-testid="position-symbol"]', `TEST${i}`);
      await page.type('[data-testid="position-size"]', '10000');
      await page.type('[data-testid="position-entry-date"]', '2024-01-15');
      await page.select('[data-testid="position-status"]', 'Active');

      const formFillTime = Date.now() - formFillStart;

      // Submit form
      const submitStart = Date.now();
      await page.click('[data-testid="submit-position"]');
      await page.waitForFunction(
        () => !document.querySelector('[data-testid="position-entry-modal"]')
      );

      const submitTime = Date.now() - submitStart;
      const totalTime = Date.now() - startTime;

      results.push({
        iteration: i + 1,
        modalOpenTime,
        formFillTime,
        submitTime,
        totalTime,
      });

      await page.close();
      console.log(
        `  Iteration ${
          i + 1
        }: ${totalTime}ms total (${modalOpenTime}ms modal, ${submitTime}ms submit)`
      );
    }

    this.results.push({
      testName: 'Position Entry Performance',
      results,
      averageTotalTime:
        results.reduce((sum, r) => sum + r.totalTime, 0) / results.length,
      averageSubmitTime:
        results.reduce((sum, r) => sum + r.submitTime, 0) / results.length,
    });
  }

  async testChartRenderingPerformance(browser) {
    console.log('📊 Testing Chart Rendering Performance');

    const results = [];

    for (let i = 0; i < this.iterations; i++) {
      const page = await browser.newPage();
      await page.goto(this.baseUrl);
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="advanced-risk-dashboard"]');

      // Test trend chart rendering
      const trendChartStart = Date.now();
      await page.click('[data-testid="chart-trend-tab"]');
      await page.waitForSelector('[data-testid="risk-trend-chart"]');
      const trendChartTime = Date.now() - trendChartStart;

      // Test composition chart rendering
      const compositionChartStart = Date.now();
      await page.click('[data-testid="chart-composition-tab"]');
      await page.waitForSelector('[data-testid="portfolio-composition-chart"]');
      const compositionChartTime = Date.now() - compositionChartStart;

      // Test chart interactions
      const interactionStart = Date.now();
      await page.click('[data-testid="chart-type-toggle"]');
      await page.waitForTimeout(100); // Wait for animation
      const interactionTime = Date.now() - interactionStart;

      results.push({
        iteration: i + 1,
        trendChartTime,
        compositionChartTime,
        interactionTime,
      });

      await page.close();
      console.log(
        `  Iteration ${
          i + 1
        }: Trend ${trendChartTime}ms, Composition ${compositionChartTime}ms`
      );
    }

    this.results.push({
      testName: 'Chart Rendering Performance',
      results,
      averageTrendChartTime:
        results.reduce((sum, r) => sum + r.trendChartTime, 0) / results.length,
      averageCompositionChartTime:
        results.reduce((sum, r) => sum + r.compositionChartTime, 0) /
        results.length,
    });
  }

  async testScenarioAnalysisPerformance(browser) {
    console.log('🎯 Testing Scenario Analysis Performance');

    const results = [];

    for (let i = 0; i < this.iterations; i++) {
      const page = await browser.newPage();
      await page.goto(this.baseUrl);
      await page.click('[data-testid="nav-position-sizing"]');
      await page.waitForSelector('[data-testid="scenario-analyzer"]');

      const startTime = Date.now();

      // Select scenario and run analysis
      await page.click('[data-testid="scenario-moderate"]');
      await page.click('[data-testid="run-scenario-analysis"]');

      // Wait for results
      await page.waitForSelector('[data-testid="scenario-results"]', {
        timeout: 15000,
      });
      await page.waitForSelector('[data-testid="worst-case-positions"]');

      const analysisTime = Date.now() - startTime;

      results.push({
        iteration: i + 1,
        analysisTime,
      });

      await page.close();
      console.log(`  Iteration ${i + 1}: ${analysisTime}ms scenario analysis`);
    }

    this.results.push({
      testName: 'Scenario Analysis Performance',
      results,
      averageAnalysisTime:
        results.reduce((sum, r) => sum + r.analysisTime, 0) / results.length,
    });
  }

  async testMemoryUsage(browser) {
    console.log('🧠 Testing Memory Usage');

    const page = await browser.newPage();
    await page.goto(this.baseUrl);

    // Get initial memory
    const initialMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        const memory = performance.memory;
        return {
          usedHeapSize: memory.usedJSHeapSize,
          totalHeapSize: memory.totalJSHeapSize,
          heapSizeLimit: memory.jsHeapSizeLimit,
        };
      }
      return null;
    });

    // Navigate and interact with the app
    await page.click('[data-testid="nav-position-sizing"]');
    await page.waitForSelector('[data-testid="position-sizing-dashboard"]');

    // Perform memory-intensive operations
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="chart-type-toggle"]');
      await page.waitForTimeout(100);
      await page.click('[data-testid="time-range-30d"]');
      await page.waitForTimeout(100);
    }

    // Get final memory
    const finalMemory = await page.evaluate(() => {
      if ('memory' in performance) {
        const memory = performance.memory;
        return {
          usedHeapSize: memory.usedJSHeapSize,
          totalHeapSize: memory.totalJSHeapSize,
          heapSizeLimit: memory.jsHeapSizeLimit,
        };
      }
      return null;
    });

    await page.close();

    if (initialMemory && finalMemory) {
      const memoryIncrease =
        finalMemory.usedHeapSize - initialMemory.usedHeapSize;

      this.results.push({
        testName: 'Memory Usage',
        initialMemory: initialMemory.usedHeapSize / 1024 / 1024, // MB
        finalMemory: finalMemory.usedHeapSize / 1024 / 1024, // MB
        memoryIncrease: memoryIncrease / 1024 / 1024, // MB
        memoryIncreasePercentage:
          (memoryIncrease / initialMemory.usedHeapSize) * 100,
      });

      console.log(
        `  Memory increase: ${(memoryIncrease / 1024 / 1024).toFixed(2)}MB`
      );
    }
  }

  generateReport() {
    console.log('\n📋 Generating Performance Report');

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const reportData = {
      timestamp: new Date().toISOString(),
      testConfiguration: {
        baseUrl: this.baseUrl,
        iterations: this.iterations,
        browser: 'Chrome (Puppeteer)',
      },
      results: this.results,
      summary: this.generateSummary(),
    };

    // Generate JSON report
    const jsonReport = JSON.stringify(reportData, null, 2);
    const jsonPath = join(
      this.outputDir,
      `performance-report-${timestamp}.json`
    );
    writeFileSync(jsonPath, jsonReport);

    // Generate markdown report
    const markdownReport = this.generateMarkdownReport(reportData);
    const mdPath = join(this.outputDir, `performance-report-${timestamp}.md`);
    writeFileSync(markdownReport, mdPath);

    console.log(`\n✅ Performance test completed!`);
    console.log(`📄 JSON Report: ${jsonPath}`);
    console.log(`📄 Markdown Report: ${mdPath}`);
    console.log(`\n${this.generateConsoleSummary()}`);
  }

  generateSummary() {
    const summary = {};

    this.results.forEach((result) => {
      if (result.averageLoadTime !== undefined) {
        summary.dashboardLoad = {
          average: result.averageLoadTime,
          min: result.minLoadTime,
          max: result.maxLoadTime,
          threshold: 3000,
          status: result.averageLoadTime < 3000 ? 'PASS' : 'FAIL',
        };
      }

      if (result.averageResponseTime !== undefined) {
        summary.kellyInput = {
          average: result.averageResponseTime,
          threshold: 1000,
          status: result.averageResponseTime < 1000 ? 'PASS' : 'FAIL',
        };
      }

      if (result.averageSubmitTime !== undefined) {
        summary.positionEntry = {
          average: result.averageSubmitTime,
          threshold: 2000,
          status: result.averageSubmitTime < 2000 ? 'PASS' : 'FAIL',
        };
      }

      if (result.memoryIncrease !== undefined) {
        summary.memoryUsage = {
          increase: result.memoryIncrease,
          threshold: 50,
          status: result.memoryIncrease < 50 ? 'PASS' : 'FAIL',
        };
      }
    });

    return summary;
  }

  generateConsoleSummary() {
    const summary = this.generateSummary();

    return `
📊 PERFORMANCE SUMMARY:
${Object.entries(summary)
  .map(
    ([test, data]) =>
      `${data.status === 'PASS' ? '✅' : '❌'} ${test}: ${
        data.average
          ? `${data.average.toFixed(0)}ms avg`
          : data.increase
            ? `${data.increase.toFixed(1)}MB increase`
            : 'N/A'
      } (threshold: ${data.threshold}${data.average ? 'ms' : 'MB'})`
  )
  .join('\n')}

${
  Object.values(summary).every((s) => s.status === 'PASS')
    ? '🎉 All performance tests PASSED!'
    : '⚠️  Some performance tests FAILED - review detailed report'
}
    `.trim();
  }

  generateMarkdownReport(data) {
    return `# Position Sizing Performance Test Report

Generated: ${data.timestamp}

## Test Configuration
- **Base URL**: ${data.testConfiguration.baseUrl}
- **Iterations**: ${data.testConfiguration.iterations}
- **Browser**: ${data.testConfiguration.browser}

## Summary
${Object.entries(data.summary)
  .map(
    ([test, result]) =>
      `- **${test}**: ${result.status} (${
        result.average
          ? result.average.toFixed(0) + 'ms'
          : result.increase.toFixed(1) + 'MB'
      })`
  )
  .join('\n')}

## Detailed Results

${data.results
  .map(
    (result) => `### ${result.testName}
${JSON.stringify(result, null, 2)}
`
  )
  .join('\n')}

## Performance Thresholds
- Dashboard Load: < 3000ms
- Kelly Input Response: < 1000ms
- Position Entry Submit: < 2000ms
- Memory Increase: < 50MB

---
*Generated by Position Sizing Performance Test Suite*`;
  }
}

// CLI execution
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const tester = new PerformanceTester({
    baseUrl: process.argv[2] || 'http://localhost:5173',
    iterations: parseInt(process.argv[3]) || 5,
  });

  tester.runTests().catch(console.error);
}

export default PerformanceTester;
