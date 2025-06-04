#!/usr/bin/env node

/**
 * Simple test runner for the End-to-End Workflow Test
 *
 * Usage:
 *   node tests/runEndToEndTest.js
 *   node tests/runEndToEndTest.js --screenshots
 *   node tests/runEndToEndTest.js --verbose --screenshots
 */

import { runEndToEndWorkflow } from './endToEndWorkflow.spec.js';

async function main() {
  console.log('🔬 Sensylate End-to-End Workflow Test Runner');
  console.log('==============================================');

  const args = process.argv.slice(2);
  const hasScreenshots = args.includes('--screenshots');
  const hasVerbose = args.includes('--verbose') || args.includes('--debug');

  console.log(`📷 Screenshots: ${hasScreenshots ? 'ENABLED' : 'DISABLED'}`);
  console.log(`🔊 Verbose mode: ${hasVerbose ? 'ENABLED' : 'DISABLED'}`);
  console.log('');

  try {
    const result = await runEndToEndWorkflow();

    if (result.success) {
      console.log('\n🎉 End-to-End Workflow Test PASSED!');
      console.log('All workflow steps completed successfully.');

      if (result.strategyInFocus) {
        console.log('\n📊 Strategy in Focus:');
        console.log(JSON.stringify(result.strategyInFocus, null, 2));
      }

      process.exit(0);
    } else {
      console.log('\n❌ End-to-End Workflow Test FAILED!');

      if (result.error) {
        console.log(`Error: ${result.error}`);
      }

      if (result.results) {
        const failed = Object.entries(result.results)
          .filter(([step, passed]) => !passed)
          .map(([step]) => step);

        if (failed.length > 0) {
          console.log(`Failed steps: ${failed.join(', ')}`);
        }
      }

      process.exit(1);
    }
  } catch (error) {
    console.error('💥 Test runner failed:', error.message);
    process.exit(1);
  }
}

main();
