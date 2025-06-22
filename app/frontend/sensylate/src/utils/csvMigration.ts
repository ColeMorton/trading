/**
 * CSV Migration Utilities for Position Sizing Data Entry
 *
 * This module provides utilities to migrate existing strategy CSV files
 * to the enhanced format with manual entry fields while maintaining
 * backward compatibility.
 */

import { parseStrategyCSV, strategyRowToCSV } from './csvParser';
import { StrategyRow } from '../types';

export interface MigrationOptions {
  backupOriginal?: boolean;
  preserveData?: boolean;
  addDefaultValues?: boolean;
}

export interface MigrationResult {
  success: boolean;
  originalRowCount: number;
  migratedRowCount: number;
  enhancedColumnsAdded: string[];
  warnings: string[];
  backupPath?: string;
}

/**
 * Enhanced columns that will be added during migration
 */
export const ENHANCED_COLUMNS = [
  'Manual Position Size',
  'Manual Entry Date',
  'Current Status',
  'Stop Status',
  'Notes',
];

/**
 * Default values for enhanced columns during migration
 */
export const DEFAULT_VALUES = {
  manualPositionSize: undefined,
  manualEntryDate: undefined,
  currentStatus: 'Pending' as const,
  stopStatus: 'Risk' as const,
  notes: undefined,
};

/**
 * Migrate a strategy CSV to enhanced format with manual entry fields
 */
export async function migrateStrategyCSV(
  csvContent: string,
  options: MigrationOptions = {}
): Promise<MigrationResult> {
  const { preserveData = true, addDefaultValues = false } = options;

  const result: MigrationResult = {
    success: false,
    originalRowCount: 0,
    migratedRowCount: 0,
    enhancedColumnsAdded: [],
    warnings: [],
  };

  try {
    // Parse original CSV
    const parseResult = parseStrategyCSV(csvContent);
    result.originalRowCount = parseResult.data.length;
    result.warnings = [...parseResult.warnings];

    // Check if already enhanced
    if (parseResult.hasEnhancedColumns) {
      result.warnings.push('CSV already contains enhanced columns');
      result.success = true;
      result.migratedRowCount = result.originalRowCount;
      return result;
    }

    // Enhance each row with default values if requested
    const enhancedRows: StrategyRow[] = parseResult.data.map((row) => {
      const enhanced = { ...row };

      if (addDefaultValues) {
        enhanced.currentStatus = DEFAULT_VALUES.currentStatus;
        enhanced.stopStatus = DEFAULT_VALUES.stopStatus;
      }

      return enhanced;
    });

    // Generate enhanced CSV
    const enhancedCSV = strategyRowToCSV(enhancedRows, true);

    result.success = true;
    result.migratedRowCount = enhancedRows.length;
    result.enhancedColumnsAdded = ENHANCED_COLUMNS;

    return result;
  } catch (error) {
    result.warnings.push(
      `Migration failed: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`
    );
    return result;
  }
}

/**
 * Validate that a CSV can be safely migrated
 */
export function validateCSVForMigration(csvContent: string): {
  canMigrate: boolean;
  issues: string[];
  recommendations: string[];
} {
  const issues: string[] = [];
  const recommendations: string[] = [];

  try {
    const parseResult = parseStrategyCSV(csvContent);

    // Check for required columns
    const requiredFields = ['ticker', 'strategyType'];
    const sampleRow = parseResult.data[0];

    if (!sampleRow) {
      issues.push('CSV contains no data rows');
      return { canMigrate: false, issues, recommendations };
    }

    for (const field of requiredFields) {
      if (!sampleRow[field as keyof StrategyRow]) {
        issues.push(`Missing required field: ${field}`);
      }
    }

    // Check data quality
    const rowsWithTicker = parseResult.data.filter(
      (row) => row.ticker && row.ticker.trim() !== ''
    );
    if (rowsWithTicker.length !== parseResult.data.length) {
      const missingTickers = parseResult.data.length - rowsWithTicker.length;
      issues.push(`${missingTickers} rows missing ticker symbols`);
      recommendations.push(
        'Clean up rows with missing ticker symbols before migration'
      );
    }

    // Check for duplicate tickers
    const tickers = parseResult.data.map((row) => row.ticker).filter(Boolean);
    const uniqueTickers = new Set(tickers);
    if (tickers.length !== uniqueTickers.size) {
      recommendations.push('Consider consolidating duplicate ticker entries');
    }

    // Check if already enhanced
    if (parseResult.hasEnhancedColumns) {
      recommendations.push(
        'CSV already contains enhanced columns - migration not needed'
      );
    }

    return {
      canMigrate: issues.length === 0,
      issues,
      recommendations,
    };
  } catch (error) {
    issues.push(
      `CSV validation failed: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`
    );
    return { canMigrate: false, issues, recommendations };
  }
}

/**
 * Generate migration summary report
 */
export function generateMigrationReport(
  portfolioType: 'Risk_On' | 'Investment' | 'Protected',
  beforeCSV: string,
  afterCSV: string
): string {
  const beforeResult = parseStrategyCSV(beforeCSV);
  const afterResult = parseStrategyCSV(afterCSV);

  const report = [
    `# ${portfolioType} Portfolio Migration Report`,
    `Generated: ${new Date().toISOString()}`,
    '',
    '## Summary',
    `- Portfolio Type: ${portfolioType}`,
    `- Original Rows: ${beforeResult.data.length}`,
    `- Migrated Rows: ${afterResult.data.length}`,
    `- Enhanced Columns Added: ${
      afterResult.hasEnhancedColumns ? 'Yes' : 'No'
    }`,
    '',
    '## Enhanced Columns',
    ...ENHANCED_COLUMNS.map((col) => `- ${col}`),
    '',
    '## Validation Results',
    ...(beforeResult.warnings.length > 0
      ? ['### Warnings:', ...beforeResult.warnings.map((w) => `- ${w}`)]
      : ['✓ No validation warnings']),
    '',
    '## Next Steps',
    '1. Review migrated CSV for accuracy',
    '2. Begin manual data entry for active positions',
    '3. Update Kelly Criterion values from trading journal',
    '4. Configure portfolio transitions (Risk → Protected)',
    '',
    '## Migration Notes',
    '- All original data preserved',
    '- Enhanced columns initialized as empty/default values',
    '- Backward compatibility maintained',
    '- Ready for Position Sizing dashboard integration',
  ];

  return report.join('\n');
}

/**
 * Batch migrate all three portfolio CSV files
 */
export async function migrateBatchPortfolios(portfolios: {
  trades: string;
  portfolio: string;
  protected: string;
}): Promise<Record<string, MigrationResult>> {
  const results: Record<string, MigrationResult> = {};

  for (const [portfolioType, csvContent] of Object.entries(portfolios)) {
    try {
      results[portfolioType] = await migrateStrategyCSV(csvContent, {
        preserveData: true,
        addDefaultValues: true,
      });
    } catch (error) {
      results[portfolioType] = {
        success: false,
        originalRowCount: 0,
        migratedRowCount: 0,
        enhancedColumnsAdded: [],
        warnings: [
          `Batch migration failed: ${
            error instanceof Error ? error.message : 'Unknown error'
          }`,
        ],
      };
    }
  }

  return results;
}

export default {
  migrateStrategyCSV,
  validateCSVForMigration,
  generateMigrationReport,
  migrateBatchPortfolios,
  ENHANCED_COLUMNS,
  DEFAULT_VALUES,
};
