#!/usr/bin/env node

import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configuration
const SCREENSHOT_DIR = path.join(__dirname, '../screenshots/position-sizing');

// Parse command line arguments
const args = process.argv.slice(2);
const shouldTakeScreenshots = args.includes('--screenshots');
const isVerbose = args.includes('--verbose');
const isHeaded = args.includes('--headed');
const isFull = args.includes('--full');

console.log('🚀 Position Sizing E2E Test Runner');
console.log('==================================');
console.log('Usage: npm run test:position-sizing [options]');
console.log('Options:');
console.log('  --screenshots   Take screenshots during test');
console.log('  --verbose       Show detailed logging');
console.log('  --headed        Run tests in headed mode (visible browser)');
console.log('  --full          Run all tests including long-running ones');
console.log('==================================\n');

// Clean up old screenshots if taking new ones
if (shouldTakeScreenshots && fs.existsSync(SCREENSHOT_DIR)) {
  console.log('🧹 Cleaning up old screenshots...');
  const files = fs.readdirSync(SCREENSHOT_DIR);
  files.forEach((file) => {
    if (file.endsWith('.png')) {
      fs.unlinkSync(path.join(SCREENSHOT_DIR, file));
    }
  });
  console.log(
    `✓ Removed ${
      files.filter((f) => f.endsWith('.png')).length
    } old screenshots\n`
  );
}

// Ensure screenshot directory exists
if (shouldTakeScreenshots && !fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  console.log('✓ Created screenshot directory\n');
}

// Build command arguments
const testArgs = ['tests/positionSizing.spec.js'];
if (shouldTakeScreenshots) testArgs.push('--screenshots');
if (isVerbose) testArgs.push('--verbose');
if (isHeaded) testArgs.push('--headed');
if (isFull) testArgs.push('--full');

// Run the test
console.log('🧪 Running Position Sizing E2E tests...\n');
const testProcess = spawn('node', testArgs, {
  cwd: path.join(__dirname, '..'),
  stdio: 'inherit',
});

testProcess.on('close', (code) => {
  if (code === 0) {
    console.log('\n✅ All Position Sizing E2E tests passed!');

    if (shouldTakeScreenshots) {
      console.log(`\n📸 Screenshots available at: ${SCREENSHOT_DIR}`);

      // List screenshots
      try {
        const screenshots = fs
          .readdirSync(SCREENSHOT_DIR)
          .filter((f) => f.endsWith('.png'))
          .sort();

        if (screenshots.length > 0) {
          console.log('\nScreenshots captured:');
          screenshots.forEach((file, index) => {
            const match = file.match(/_(\d+)_(.+)\.png$/);
            if (match) {
              console.log(`  ${index + 1}. ${match[2].replace(/_/g, ' ')}`);
            }
          });
        }
      } catch (error) {
        // Ignore errors when listing screenshots
      }
    }
  } else {
    console.log(`\n❌ Position Sizing E2E tests failed with exit code ${code}`);
  }

  process.exit(code);
});

testProcess.on('error', (error) => {
  console.error('Failed to start test process:', error);
  process.exit(1);
});
