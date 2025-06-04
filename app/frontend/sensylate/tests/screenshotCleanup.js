/**
 * Screenshot Cleanup Utility
 *
 * Provides functions to clean up old Puppeteer screenshots across test suites.
 * This helps prevent screenshot directories from accumulating too many files.
 */

import fs from 'fs';
import path from 'path';

/**
 * Clean up old screenshots in a directory
 * @param {string} screenshotDir - Directory containing screenshots
 * @param {object} options - Cleanup options
 * @param {string} options.prefix - File prefix to match (e.g., 'e2e_')
 * @param {boolean} options.verbose - Whether to log detailed information
 * @param {number} options.maxAge - Maximum age in hours (optional)
 */
export async function cleanupScreenshots(screenshotDir, options = {}) {
  const { prefix = '', verbose = false, maxAge = null } = options;

  try {
    if (!fs.existsSync(screenshotDir)) {
      if (verbose)
        console.log(
          '📁 Screenshots directory does not exist, skipping cleanup'
        );
      return { cleaned: 0, kept: 0 };
    }

    const files = fs.readdirSync(screenshotDir);
    let screenshotFiles = files.filter((file) => {
      if (!file.endsWith('.png')) return false;
      if (prefix && !file.startsWith(prefix)) return false;
      // Match timestamp pattern in filename
      return /\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}/.test(file);
    });

    // If maxAge is specified, filter by file age
    if (maxAge !== null) {
      const maxAgeMs = maxAge * 60 * 60 * 1000; // Convert hours to milliseconds
      const now = Date.now();

      screenshotFiles = screenshotFiles.filter((file) => {
        const filePath = path.join(screenshotDir, file);
        const stats = fs.statSync(filePath);
        const fileAge = now - stats.mtime.getTime();
        return fileAge > maxAgeMs;
      });
    }

    if (screenshotFiles.length === 0) {
      if (verbose) console.log('🧹 No old screenshots to clean up');
      return {
        cleaned: 0,
        kept: files.filter((f) => f.endsWith('.png')).length,
      };
    }

    console.log(
      `🧹 Cleaning up ${screenshotFiles.length} old screenshots${
        prefix ? ` (${prefix}*)` : ''
      }...`
    );

    let cleaned = 0;
    for (const file of screenshotFiles) {
      try {
        const filePath = path.join(screenshotDir, file);
        fs.unlinkSync(filePath);
        cleaned++;
        if (verbose) console.log(`   🗑️  Deleted: ${file}`);
      } catch (error) {
        console.log(`   ⚠️  Failed to delete ${file}: ${error.message}`);
      }
    }

    const remaining = files.filter((f) => f.endsWith('.png')).length - cleaned;
    console.log(
      `✅ Screenshot cleanup complete: ${cleaned} deleted, ${remaining} kept`
    );

    return { cleaned, kept: remaining };
  } catch (error) {
    console.log(`⚠️ Failed to cleanup screenshots: ${error.message}`);
    return { cleaned: 0, kept: 0, error: error.message };
  }
}

/**
 * Clean up end-to-end test screenshots
 * @param {string} screenshotDir - Directory containing screenshots
 * @param {boolean} verbose - Whether to log detailed information
 */
export async function cleanupE2EScreenshots(screenshotDir, verbose = false) {
  return cleanupScreenshots(screenshotDir, { prefix: 'e2e_', verbose });
}

/**
 * Clean up parameter testing screenshots
 * @param {string} screenshotDir - Directory containing screenshots
 * @param {boolean} verbose - Whether to log detailed information
 */
export async function cleanupParameterTestingScreenshots(
  screenshotDir,
  verbose = false
) {
  return cleanupScreenshots(screenshotDir, { prefix: '', verbose });
}

/**
 * Clean up screenshots older than specified age
 * @param {string} screenshotDir - Directory containing screenshots
 * @param {number} maxAgeHours - Maximum age in hours
 * @param {boolean} verbose - Whether to log detailed information
 */
export async function cleanupOldScreenshots(
  screenshotDir,
  maxAgeHours = 24,
  verbose = false
) {
  return cleanupScreenshots(screenshotDir, { maxAge: maxAgeHours, verbose });
}

// If running directly, clean up both Sensylate and SensitivityTrader screenshots
if (process.argv[1] === new URL(import.meta.url).pathname) {
  const verbose = process.argv.includes('--verbose');
  const dryRun = process.argv.includes('--dry-run');

  console.log('🧹 Screenshot Cleanup Utility');
  console.log('==============================');

  if (dryRun) {
    console.log('🔍 DRY RUN MODE - No files will be deleted');
  }

  const sensylateDir = path.join(process.cwd(), 'screenshots');
  const sensitivityTraderDir = path.join(
    process.cwd(),
    '../SensitivityTrader/screenshots'
  );

  async function runCleanup() {
    console.log('\n📱 Cleaning Sensylate screenshots...');
    const sensylateResult = await cleanupScreenshots(sensylateDir, { verbose });

    console.log('\n🔬 Cleaning SensitivityTrader screenshots...');
    const sensitivityResult = await cleanupScreenshots(sensitivityTraderDir, {
      verbose,
    });

    const totalCleaned = sensylateResult.cleaned + sensitivityResult.cleaned;
    const totalKept = sensylateResult.kept + sensitivityResult.kept;

    console.log(`\n📊 Total Summary:`);
    console.log(`   🗑️  Cleaned: ${totalCleaned} screenshots`);
    console.log(`   📁 Kept: ${totalKept} screenshots`);
    console.log('✅ Cleanup complete!');
  }

  if (!dryRun) {
    runCleanup().catch(console.error);
  }
}

export default {
  cleanupScreenshots,
  cleanupE2EScreenshots,
  cleanupParameterTestingScreenshots,
  cleanupOldScreenshots,
};
