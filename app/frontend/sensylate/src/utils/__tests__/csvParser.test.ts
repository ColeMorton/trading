import {
  parseStrategyCSV,
  strategyRowToCSV,
  migrateCSVToEnhanced,
} from '../csvParser';
import { StrategyRow } from '../../types';

describe('CSV Parser', () => {
  // Sample legacy CSV content (based on actual trades.csv structure)
  const legacyCSVContent = `Ticker,Strategy Type,Short Window,Long Window,Signal Window,Signal Entry,Signal Exit,Total Open Trades,Total Trades,Score,Win Rate [%],Profit Factor,Expectancy per Trade,Sortino Ratio,Beats BNH [%],Avg Trade Duration,Allocation [%],Stop Loss [%]
NFLX,SMA,82,83,0,false,false,1,109,1.74,58.33,3.92,11.40,1.62,-0.53,36 days,2.78,
AMAT,SMA,64,77,0,false,false,1,101,1.70,60.0,2.66,12.44,1.20,0.24,66 days,,
TSLA,SMA,4,39,0,false,false,1,74,1.43,42.47,5.15,12.54,1.96,-0.18,28 days,20.0,`;

  // Sample enhanced CSV content with manual entry fields
  const enhancedCSVContent = `Ticker,Strategy Type,Short Window,Long Window,Signal Window,Signal Entry,Signal Exit,Total Trades,Win Rate [%],Profit Factor,Expectancy per Trade,Sortino Ratio,Allocation [%],Stop Loss [%],Manual Position Size,Manual Entry Date,Current Status,Stop Status
NFLX,SMA,82,83,0,false,false,109,58.33,3.92,11.40,1.62,2.78,,5000,2024-01-15,Active,Risk
AMAT,SMA,64,77,0,false,false,101,60.0,2.66,12.44,1.20,,,7500,2024-01-10,Active,Protected
TSLA,SMA,4,39,0,false,false,74,42.47,5.15,12.54,1.96,20.0,,3000,2024-01-20,Closed,Risk`;

  describe('parseStrategyCSV', () => {
    it('should parse legacy CSV format correctly', () => {
      const result = parseStrategyCSV(legacyCSVContent);

      expect(result.data).toHaveLength(3);
      expect(result.hasEnhancedColumns).toBe(false);
      expect(result.warnings).toHaveLength(0);

      const nflxRow = result.data[0];
      expect(nflxRow.ticker).toBe('NFLX');
      expect(nflxRow.strategyType).toBe('SMA');
      expect(nflxRow.shortWindow).toBe(82);
      expect(nflxRow.longWindow).toBe(83);
      expect(nflxRow.signalEntry).toBe(false);
      expect(nflxRow.winRate).toBe(58.33);
      expect(nflxRow.allocation).toBe(2.78);

      // Enhanced fields should be undefined for legacy format
      expect(nflxRow.manualPositionSize).toBeUndefined();
      expect(nflxRow.manualEntryDate).toBeUndefined();
      expect(nflxRow.currentStatus).toBeUndefined();
    });

    it('should parse enhanced CSV format correctly', () => {
      const result = parseStrategyCSV(enhancedCSVContent);

      expect(result.data).toHaveLength(3);
      expect(result.hasEnhancedColumns).toBe(true);
      expect(result.warnings).toHaveLength(0);

      const nflxRow = result.data[0];
      expect(nflxRow.ticker).toBe('NFLX');
      expect(nflxRow.manualPositionSize).toBe(5000);
      expect(nflxRow.manualEntryDate).toBe('2024-01-15');
      expect(nflxRow.currentStatus).toBe('Active');
      expect(nflxRow.stopStatus).toBe('Risk');

      const amatRow = result.data[1];
      expect(amatRow.manualPositionSize).toBe(7500);
      expect(amatRow.stopStatus).toBe('Protected');

      const tslaRow = result.data[2];
      expect(tslaRow.currentStatus).toBe('Closed');
    });

    it('should handle missing optional columns gracefully', () => {
      const csvWithMissingColumns = `Ticker,Strategy Type,Short Window,Long Window
AAPL,SMA,20,50
MSFT,EMA,12,26`;

      const result = parseStrategyCSV(csvWithMissingColumns);

      expect(result.data).toHaveLength(2);
      expect(result.warnings).toHaveLength(0);

      const aaplRow = result.data[0];
      expect(aaplRow.ticker).toBe('AAPL');
      expect(aaplRow.strategyType).toBe('SMA');
      expect(aaplRow.shortWindow).toBe(20);
      expect(aaplRow.longWindow).toBe(50);
      // Optional fields should have default values
      expect(aaplRow.totalTrades).toBe(0);
      expect(aaplRow.winRate).toBe(0);
    });

    it('should handle quoted values with commas', () => {
      const csvWithQuotes = `Ticker,Strategy Type,Notes
AAPL,SMA,"This is a note, with commas"
MSFT,EMA,Simple note`;

      const result = parseStrategyCSV(csvWithQuotes);

      expect(result.data).toHaveLength(2);
      expect(result.data[0].notes).toBe('This is a note, with commas');
      expect(result.data[1].notes).toBe('Simple note');
    });

    it('should validate date formats', () => {
      const csvWithInvalidDate = `Ticker,Strategy Type,Manual Entry Date
AAPL,SMA,2024-01-15
MSFT,EMA,invalid-date
GOOGL,SMA,2024-12-31`;

      const result = parseStrategyCSV(csvWithInvalidDate);

      expect(result.data).toHaveLength(3);
      expect(result.data[0].manualEntryDate).toBe('2024-01-15');
      expect(result.data[1].manualEntryDate).toBeUndefined(); // Invalid date ignored
      expect(result.data[2].manualEntryDate).toBe('2024-12-31');
    });
  });

  describe('strategyRowToCSV', () => {
    it('should convert strategy rows back to CSV format', () => {
      const rows: StrategyRow[] = [
        {
          ticker: 'AAPL',
          strategyType: 'SMA',
          shortWindow: 20,
          longWindow: 50,
          signalEntry: true,
          signalExit: false,
          totalTrades: 100,
          winRate: 65.5,
          profitFactor: 1.8,
          expectancyPerTrade: 15.2,
          sortinoRatio: 1.4,
          allocation: 10.0,
          manualPositionSize: 5000,
          manualEntryDate: '2024-01-15',
          currentStatus: 'Active',
          stopStatus: 'Risk',
        },
      ];

      const csvResult = strategyRowToCSV(rows, true);
      const lines = csvResult.split('\n');

      expect(lines).toHaveLength(2); // Header + 1 data row
      expect(lines[0]).toContain('Manual Position Size');
      expect(lines[1]).toContain('AAPL');
      expect(lines[1]).toContain('5000');
      expect(lines[1]).toContain('Active');
    });

    it('should exclude enhanced columns when requested', () => {
      const rows: StrategyRow[] = [
        {
          ticker: 'AAPL',
          strategyType: 'SMA',
          shortWindow: 20,
          longWindow: 50,
          signalEntry: true,
          signalExit: false,
          totalTrades: 100,
          winRate: 65.5,
          profitFactor: 1.8,
          expectancyPerTrade: 15.2,
          sortinoRatio: 1.4,
        },
      ];

      const csvResult = strategyRowToCSV(rows, false);
      const lines = csvResult.split('\n');

      expect(lines[0]).not.toContain('Manual Position Size');
      expect(lines[0]).not.toContain('Current Status');
    });

    it('should handle empty arrays', () => {
      const result = strategyRowToCSV([]);
      expect(result).toBe('');
    });

    it('should escape commas and quotes properly', () => {
      const rows: StrategyRow[] = [
        {
          ticker: 'TEST',
          strategyType: 'SMA',
          shortWindow: 20,
          longWindow: 50,
          signalEntry: false,
          signalExit: false,
          totalTrades: 0,
          winRate: 0,
          profitFactor: 0,
          expectancyPerTrade: 0,
          sortinoRatio: 0,
          notes: 'This note has, commas and "quotes"',
        },
      ];

      const csvResult = strategyRowToCSV(rows, true);
      expect(csvResult).toContain('"This note has, commas and ""quotes"""');
    });
  });

  describe('migrateCSVToEnhanced', () => {
    it('should add enhanced columns to legacy CSV', () => {
      const migratedCSV = migrateCSVToEnhanced(legacyCSVContent);
      const result = parseStrategyCSV(migratedCSV);

      expect(result.hasEnhancedColumns).toBe(true);
      expect(result.data).toHaveLength(3);

      // Original data should be preserved
      const nflxRow = result.data[0];
      expect(nflxRow.ticker).toBe('NFLX');
      expect(nflxRow.winRate).toBe(58.33);

      // Enhanced columns should be present but empty
      expect(migratedCSV).toContain('Manual Position Size');
      expect(migratedCSV).toContain('Current Status');
    });

    it('should not modify already enhanced CSV', () => {
      const migratedCSV = migrateCSVToEnhanced(enhancedCSVContent);
      expect(migratedCSV).toBe(enhancedCSVContent);
    });
  });

  describe('Edge cases', () => {
    it('should handle empty CSV content', () => {
      expect(() => parseStrategyCSV('')).toThrow('CSV content is empty');
    });

    it('should handle CSV with only headers', () => {
      const headerOnlyCSV = 'Ticker,Strategy Type,Short Window,Long Window';
      const result = parseStrategyCSV(headerOnlyCSV);

      expect(result.data).toHaveLength(0);
      expect(result.headers).toHaveLength(4);
      expect(result.warnings).toHaveLength(0);
    });

    it('should handle malformed lines gracefully', () => {
      const malformedCSV = `Ticker,Strategy Type,Short Window,Long Window
AAPL,SMA,20,50
MALFORMED LINE WITH WRONG COLUMN COUNT
MSFT,EMA,12,26`;

      const result = parseStrategyCSV(malformedCSV);

      expect(result.data).toHaveLength(2); // Only valid rows
      expect(result.warnings).toHaveLength(1);
      expect(result.warnings[0]).toContain('Failed to parse line 2');
    });

    it('should handle different boolean representations', () => {
      const booleanCSV = `Ticker,Strategy Type,Signal Entry,Signal Exit
AAPL,SMA,true,false
MSFT,EMA,1,0
GOOGL,SMA,TRUE,FALSE`;

      const result = parseStrategyCSV(booleanCSV);

      expect(result.data[0].signalEntry).toBe(true);
      expect(result.data[0].signalExit).toBe(false);
      expect(result.data[1].signalEntry).toBe(true);
      expect(result.data[1].signalExit).toBe(false);
      expect(result.data[2].signalEntry).toBe(true);
      expect(result.data[2].signalExit).toBe(false);
    });
  });
});
