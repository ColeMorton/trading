import { StrategyRow } from '../types';

/**
 * Enhanced CSV parser for strategy files with backward compatibility
 * Handles both legacy CSV format and new enhanced format with manual entry fields
 */

export interface CSVParseOptions {
  hasHeader?: boolean;
  delimiter?: string;
  allowMissingColumns?: boolean;
}

export interface CSVParseResult {
  data: StrategyRow[];
  headers: string[];
  hasEnhancedColumns: boolean;
  warnings: string[];
}

// Standard column mappings for strategy CSV files
const STANDARD_COLUMNS = {
  // Core strategy columns
  ticker: ['Ticker', 'ticker', 'symbol', 'Symbol'],
  strategyType: ['Strategy Type', 'strategy_type', 'type'],
  shortWindow: ['Short Window', 'short_window'],
  longWindow: ['Long Window', 'long_window'],
  signalWindow: ['Signal Window', 'signal_window'],
  signalEntry: ['Signal Entry', 'signal_entry'],
  signalExit: ['Signal Exit', 'signal_exit'],
  totalTrades: ['Total Trades', 'total_trades'],
  winRate: ['Win Rate [%]', 'win_rate', 'Win Rate'],
  profitFactor: ['Profit Factor', 'profit_factor'],
  expectancyPerTrade: ['Expectancy per Trade', 'expectancy_per_trade'],
  sortinoRatio: ['Sortino Ratio', 'sortino_ratio'],
  allocation: ['Allocation [%]', 'allocation', 'Allocation'],
  stopLoss: ['Stop Loss [%]', 'stop_loss', 'Stop Loss'],

  // Enhanced manual entry columns
  manualPositionSize: [
    'Manual Position Size',
    'manual_position_size',
    'Position Size',
  ],
  manualEntryDate: ['Manual Entry Date', 'manual_entry_date', 'Entry Date'],
  currentStatus: ['Current Status', 'current_status', 'Status'],
  stopStatus: ['Stop Status', 'stop_status'],
  notes: ['Notes', 'notes', 'Comments'],
};

/**
 * Parse CSV string into StrategyRow objects with enhanced field support
 */
export function parseStrategyCSV(
  csvContent: string,
  options: CSVParseOptions = {}
): CSVParseResult {
  const {
    hasHeader = true,
    delimiter = ',',
    allowMissingColumns = true,
  } = options;

  const lines = csvContent.trim().split('\n');
  const warnings: string[] = [];

  if (lines.length === 0) {
    throw new Error('CSV content is empty');
  }

  // Parse headers
  const headers = hasHeader ? parseCSVLine(lines[0], delimiter) : [];
  const dataLines = hasHeader ? lines.slice(1) : lines;

  // Create column index mapping
  const columnMapping = createColumnMapping(headers);

  // Check for enhanced columns
  const hasEnhancedColumns = hasEnhancedColumnsPresent(headers);

  if (hasEnhancedColumns) {
    console.log('✓ Enhanced CSV format detected with manual entry columns');
  } else {
    console.log(
      'ℹ Legacy CSV format detected - enhanced columns will be optional'
    );
  }

  // Parse data rows
  const data: StrategyRow[] = [];

  for (let i = 0; i < dataLines.length; i++) {
    const line = dataLines[i].trim();
    if (!line) continue;

    try {
      const values = parseCSVLine(line, delimiter);
      const row = parseStrategyRow(values, columnMapping, allowMissingColumns);

      if (row) {
        data.push(row);
      }
    } catch (error) {
      const warning = `Warning: Failed to parse line ${i + 1}: ${
        error instanceof Error ? error.message : 'Unknown error'
      }`;
      warnings.push(warning);
      console.warn(warning);
    }
  }

  return {
    data,
    headers,
    hasEnhancedColumns,
    warnings,
  };
}

/**
 * Parse individual CSV line handling quoted values and commas
 */
function parseCSVLine(line: string, delimiter: string): string[] {
  const values: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === delimiter && !inQuotes) {
      values.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }

  values.push(current.trim());
  return values;
}

/**
 * Create mapping of column names to array indices
 */
function createColumnMapping(headers: string[]): Record<string, number> {
  const mapping: Record<string, number> = {};

  for (const [fieldName, possibleNames] of Object.entries(STANDARD_COLUMNS)) {
    for (const possibleName of possibleNames) {
      const index = headers.findIndex(
        (h) => h.toLowerCase().trim() === possibleName.toLowerCase().trim()
      );

      if (index !== -1) {
        mapping[fieldName] = index;
        break;
      }
    }
  }

  return mapping;
}

/**
 * Check if CSV contains enhanced manual entry columns
 */
function hasEnhancedColumnsPresent(headers: string[]): boolean {
  const enhancedFields = [
    'manualPositionSize',
    'manualEntryDate',
    'currentStatus',
    'stopStatus',
  ];

  return enhancedFields.some((field) => {
    const possibleNames =
      STANDARD_COLUMNS[field as keyof typeof STANDARD_COLUMNS];
    return possibleNames.some((name) =>
      headers.some((h) => h.toLowerCase().includes(name.toLowerCase()))
    );
  });
}

/**
 * Parse individual strategy row from CSV values
 */
function parseStrategyRow(
  values: string[],
  columnMapping: Record<string, number>,
  allowMissing: boolean
): StrategyRow | null {
  const getValue = (fieldName: string): string | undefined => {
    const index = columnMapping[fieldName];
    return index !== undefined ? values[index] : undefined;
  };

  const getNumberValue = (fieldName: string): number | undefined => {
    const value = getValue(fieldName);
    if (!value || value === '') return undefined;
    const num = parseFloat(value);
    return isNaN(num) ? undefined : num;
  };

  const getBooleanValue = (fieldName: string): boolean => {
    const value = getValue(fieldName);
    if (!value) return false;
    return value.toLowerCase() === 'true' || value === '1';
  };

  const getDateValue = (fieldName: string): string | undefined => {
    const value = getValue(fieldName);
    if (!value || value === '') return undefined;

    // Validate date format
    const date = new Date(value);
    return isNaN(date.getTime()) ? undefined : value;
  };

  // Required fields check
  const ticker = getValue('ticker');
  const strategyType = getValue('strategyType');

  if (!ticker || !strategyType) {
    if (!allowMissing) {
      throw new Error(
        `Missing required fields: ticker=${ticker}, strategyType=${strategyType}`
      );
    }
    return null;
  }

  const row: StrategyRow = {
    // Core required fields
    ticker,
    strategyType,
    shortWindow: getNumberValue('shortWindow') || 0,
    longWindow: getNumberValue('longWindow') || 0,
    signalEntry: getBooleanValue('signalEntry'),
    signalExit: getBooleanValue('signalExit'),
    totalTrades: getNumberValue('totalTrades') || 0,
    winRate: getNumberValue('winRate') || 0,
    profitFactor: getNumberValue('profitFactor') || 0,
    expectancyPerTrade: getNumberValue('expectancyPerTrade') || 0,
    sortinoRatio: getNumberValue('sortinoRatio') || 0,

    // Optional core fields
    signalWindow: getNumberValue('signalWindow'),
    allocation: getNumberValue('allocation'),
    stopLoss: getNumberValue('stopLoss'),

    // Enhanced manual entry fields (optional)
    manualPositionSize: getNumberValue('manualPositionSize'),
    manualEntryDate: getDateValue('manualEntryDate'),
    currentStatus: getValue('currentStatus') as
      | 'Active'
      | 'Closed'
      | 'Pending'
      | undefined,
    stopStatus: getValue('stopStatus') as 'Risk' | 'Protected' | undefined,
    notes: getValue('notes'),
  };

  return row;
}

/**
 * Convert StrategyRow back to CSV format
 */
export function strategyRowToCSV(
  rows: StrategyRow[],
  includeEnhancedColumns = true
): string {
  if (rows.length === 0) return '';

  // Define column order
  const baseColumns = [
    'ticker',
    'strategyType',
    'shortWindow',
    'longWindow',
    'signalWindow',
    'signalEntry',
    'signalExit',
    'totalTrades',
    'winRate',
    'profitFactor',
    'expectancyPerTrade',
    'sortinoRatio',
    'allocation',
    'stopLoss',
  ];

  const enhancedColumns = [
    'manualPositionSize',
    'manualEntryDate',
    'currentStatus',
    'stopStatus',
    'notes',
  ];

  const columns = includeEnhancedColumns
    ? [...baseColumns, ...enhancedColumns]
    : baseColumns;

  // Create header mapping for display
  const headerMapping: Record<string, string> = {
    ticker: 'Ticker',
    strategyType: 'Strategy Type',
    shortWindow: 'Short Window',
    longWindow: 'Long Window',
    signalWindow: 'Signal Window',
    signalEntry: 'Signal Entry',
    signalExit: 'Signal Exit',
    totalTrades: 'Total Trades',
    winRate: 'Win Rate [%]',
    profitFactor: 'Profit Factor',
    expectancyPerTrade: 'Expectancy per Trade',
    sortinoRatio: 'Sortino Ratio',
    allocation: 'Allocation [%]',
    stopLoss: 'Stop Loss [%]',
    manualPositionSize: 'Manual Position Size',
    manualEntryDate: 'Manual Entry Date',
    currentStatus: 'Current Status',
    stopStatus: 'Stop Status',
    notes: 'Notes',
  };

  // Generate header
  const headers = columns.map((col) => headerMapping[col] || col);
  const lines = [headers.join(',')];

  // Generate data rows
  for (const row of rows) {
    const values = columns.map((col) => {
      const value = row[col as keyof StrategyRow];

      if (value === undefined || value === null) return '';

      // Handle different data types
      if (typeof value === 'boolean') return value ? 'true' : 'false';
      if (typeof value === 'number') return value.toString();
      if (typeof value === 'string') {
        // Escape commas and quotes
        if (value.includes(',') || value.includes('"')) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }

      return String(value);
    });

    lines.push(values.join(','));
  }

  return lines.join('\n');
}

/**
 * Migration utility to add enhanced columns to existing CSV
 */
export function migrateCSVToEnhanced(csvContent: string): string {
  const parseResult = parseStrategyCSV(csvContent);

  if (parseResult.hasEnhancedColumns) {
    console.log('CSV already has enhanced columns');
    return csvContent;
  }

  console.log('Migrating CSV to enhanced format...');
  return strategyRowToCSV(parseResult.data, true);
}

export default {
  parseStrategyCSV,
  strategyRowToCSV,
  migrateCSVToEnhanced,
};
