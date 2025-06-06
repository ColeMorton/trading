/**
 * Test suite for MACD strategy support in MA Cross API service.
 *
 * Tests the frontend API service MACD parameter handling and request formatting.
 */

import { maCrossApi, MACrossRequest } from '../maCrossApi';
import { AnalysisConfiguration } from '../../types';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('maCrossApi MACD strategy support', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();

    // Clear caches
    maCrossApi.clearCache();
  });

  describe('MACD parameter inclusion in requests', () => {
    it('should include MACD parameters when MACD strategy is selected', async () => {
      const config: AnalysisConfiguration = {
        TICKER: 'BTC-USD',
        WINDOWS: 10,
        DIRECTION: 'Long',
        STRATEGY_TYPES: ['MACD'],
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        REFRESH: false,
        MINIMUMS: {
          WIN_RATE: 50,
          TRADES: 10,
          EXPECTANCY_PER_TRADE: 0.1,
          PROFIT_FACTOR: 1.2,
          SORTINO_RATIO: 0.5,
        },
        SORT_BY: 'Score',
        SORT_ASC: false,
        USE_GBM: false,
        async_execution: false,
        // MACD-specific parameters
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 15,
        LONG_WINDOW_START: 12,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 2,
      };

      const mockResponse = {
        data: {
          status: 'success',
          request_id: 'test-123',
          timestamp: '2025-01-01T00:00:00Z',
          ticker: 'BTC-USD',
          strategy_types: ['MACD'],
          portfolios: [],
          total_portfolios_analyzed: 0,
          total_portfolios_filtered: 0,
          execution_time: 10.0,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      await maCrossApi.analyze(config);

      // Verify the API was called with correct MACD parameters
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/ma-cross/analyze',
        expect.objectContaining({
          ticker: 'BTC-USD',
          strategy_types: ['MACD'],
          short_window_start: 6,
          short_window_end: 15,
          long_window_start: 12,
          long_window_end: 35,
          signal_window_start: 5,
          signal_window_end: 12,
          step: 2,
        }),
        { timeout: 30000 }
      );
    });

    it('should not include MACD parameters when MACD strategy is not selected', async () => {
      const config: AnalysisConfiguration = {
        TICKER: 'ETH-USD',
        WINDOWS: 10,
        DIRECTION: 'Long',
        STRATEGY_TYPES: ['SMA', 'EMA'], // No MACD
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        REFRESH: false,
        MINIMUMS: {
          WIN_RATE: 50,
          TRADES: 10,
          EXPECTANCY_PER_TRADE: 0.1,
          PROFIT_FACTOR: 1.2,
          SORTINO_RATIO: 0.5,
        },
        SORT_BY: 'Score',
        SORT_ASC: false,
        USE_GBM: false,
        async_execution: false,
        // MACD parameters present but should be ignored
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 15,
        LONG_WINDOW_START: 12,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 2,
      };

      const mockResponse = {
        data: {
          status: 'success',
          request_id: 'test-123',
          timestamp: '2025-01-01T00:00:00Z',
          ticker: 'ETH-USD',
          strategy_types: ['SMA', 'EMA'],
          portfolios: [],
          total_portfolios_analyzed: 0,
          total_portfolios_filtered: 0,
          execution_time: 10.0,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      await maCrossApi.analyze(config);

      // Verify the API was called without MACD parameters
      const actualCall = mockedAxios.post.mock.calls[0][1] as MACrossRequest;
      expect(actualCall.strategy_types).toEqual(['SMA', 'EMA']);
      expect(actualCall.short_window_start).toBeUndefined();
      expect(actualCall.short_window_end).toBeUndefined();
      expect(actualCall.long_window_start).toBeUndefined();
      expect(actualCall.long_window_end).toBeUndefined();
      expect(actualCall.signal_window_start).toBeUndefined();
      expect(actualCall.signal_window_end).toBeUndefined();
      expect(actualCall.step).toBeUndefined();
    });

    it('should include MACD parameters with mixed strategy types', async () => {
      const config: AnalysisConfiguration = {
        TICKER: 'AAPL',
        WINDOWS: 10,
        DIRECTION: 'Long',
        STRATEGY_TYPES: ['SMA', 'EMA', 'MACD'], // Mixed strategies
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        REFRESH: false,
        MINIMUMS: {
          WIN_RATE: 60,
          TRADES: 20,
          EXPECTANCY_PER_TRADE: 0.2,
          PROFIT_FACTOR: 1.5,
          SORTINO_RATIO: 0.8,
        },
        SORT_BY: 'Profit Factor',
        SORT_ASC: false,
        USE_GBM: false,
        async_execution: false,
        // MACD-specific parameters
        SHORT_WINDOW_START: 8,
        SHORT_WINDOW_END: 18,
        LONG_WINDOW_START: 15,
        LONG_WINDOW_END: 40,
        SIGNAL_WINDOW_START: 7,
        SIGNAL_WINDOW_END: 15,
        STEP: 3,
      };

      const mockResponse = {
        data: {
          status: 'success',
          request_id: 'test-123',
          timestamp: '2025-01-01T00:00:00Z',
          ticker: 'AAPL',
          strategy_types: ['SMA', 'EMA', 'MACD'],
          portfolios: [],
          total_portfolios_analyzed: 0,
          total_portfolios_filtered: 0,
          execution_time: 10.0,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      await maCrossApi.analyze(config);

      // Verify the API was called with all strategy types and MACD parameters
      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/ma-cross/analyze',
        expect.objectContaining({
          ticker: 'AAPL',
          strategy_types: ['SMA', 'EMA', 'MACD'],
          short_window_start: 8,
          short_window_end: 18,
          long_window_start: 15,
          long_window_end: 40,
          signal_window_start: 7,
          signal_window_end: 15,
          step: 3,
        }),
        { timeout: 30000 }
      );
    });
  });

  describe('MACD cache key generation', () => {
    it('should generate different cache keys for different MACD parameters', async () => {
      const baseConfig: Omit<
        AnalysisConfiguration,
        'SHORT_WINDOW_START' | 'SHORT_WINDOW_END'
      > = {
        TICKER: 'BTC-USD',
        WINDOWS: 10,
        DIRECTION: 'Long',
        STRATEGY_TYPES: ['MACD'],
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        REFRESH: false,
        MINIMUMS: {
          WIN_RATE: 50,
          TRADES: 10,
          EXPECTANCY_PER_TRADE: 0.1,
          PROFIT_FACTOR: 1.2,
          SORTINO_RATIO: 0.5,
        },
        SORT_BY: 'Score',
        SORT_ASC: false,
        USE_GBM: false,
        async_execution: false,
        LONG_WINDOW_START: 12,
        LONG_WINDOW_END: 35,
        SIGNAL_WINDOW_START: 5,
        SIGNAL_WINDOW_END: 12,
        STEP: 1,
      };

      const config1: AnalysisConfiguration = {
        ...baseConfig,
        SHORT_WINDOW_START: 6,
        SHORT_WINDOW_END: 15,
      };

      const config2: AnalysisConfiguration = {
        ...baseConfig,
        SHORT_WINDOW_START: 8,
        SHORT_WINDOW_END: 18,
      };

      const mockResponse1 = {
        data: {
          status: 'success',
          request_id: 'test-123',
          timestamp: '2025-01-01T00:00:00Z',
          ticker: 'BTC-USD',
          strategy_types: ['MACD'],
          portfolios: [
            {
              ticker: 'BTC-USD',
              strategy_type: 'MACD',
              short_window: 6,
              long_window: 12,
              signal_window: 5,
              direction: 'Long',
              timeframe: 'D',
              total_return: 150.0,
              annual_return: 25.0,
              sharpe_ratio: 1.2,
              sortino_ratio: 1.5,
              max_drawdown: 20.0,
              total_trades: 50,
              winning_trades: 30,
              losing_trades: 20,
              win_rate: 0.6,
              profit_factor: 2.0,
              expectancy: 500.0,
              expectancy_per_trade: 500.0,
              score: 1.0,
              beats_bnh: 10.0,
              has_open_trade: false,
              has_signal_entry: true,
            },
          ],
          total_portfolios_analyzed: 1,
          total_portfolios_filtered: 1,
          execution_time: 10.0,
        },
      };

      const mockResponse2 = {
        data: {
          status: 'success',
          request_id: 'test-124',
          timestamp: '2025-01-01T00:01:00Z',
          ticker: 'BTC-USD',
          strategy_types: ['MACD'],
          portfolios: [
            {
              ticker: 'BTC-USD',
              strategy_type: 'MACD',
              short_window: 8,
              long_window: 15,
              signal_window: 7,
              direction: 'Long',
              timeframe: 'D',
              total_return: 175.0,
              annual_return: 30.0,
              sharpe_ratio: 1.4,
              sortino_ratio: 1.8,
              max_drawdown: 18.0,
              total_trades: 45,
              winning_trades: 28,
              losing_trades: 17,
              win_rate: 0.62,
              profit_factor: 2.2,
              expectancy: 550.0,
              expectancy_per_trade: 550.0,
              score: 1.1,
              beats_bnh: 12.0,
              has_open_trade: false,
              has_signal_entry: true,
            },
          ],
          total_portfolios_analyzed: 1,
          total_portfolios_filtered: 1,
          execution_time: 12.0,
        },
      };

      mockedAxios.post.mockResolvedValueOnce(mockResponse1);
      mockedAxios.post.mockResolvedValueOnce(mockResponse2);

      // First call
      const result1 = await maCrossApi.analyze(config1);

      // Second call with different MACD parameters
      const result2 = await maCrossApi.analyze(config2);

      // Should make two separate API calls (different cache keys)
      expect(mockedAxios.post).toHaveBeenCalledTimes(2);

      // Verify different results
      if ('portfolios' in result1 && 'portfolios' in result2) {
        expect(result1.portfolios[0].short_window).toBe(6);
        expect(result2.portfolios[0].short_window).toBe(8);
      }
    });

    it('should use cache for identical MACD configurations', async () => {
      const config: AnalysisConfiguration = {
        TICKER: 'ETH-USD',
        WINDOWS: 10,
        DIRECTION: 'Long',
        STRATEGY_TYPES: ['MACD'],
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        REFRESH: false,
        MINIMUMS: {
          WIN_RATE: 55,
          TRADES: 15,
          EXPECTANCY_PER_TRADE: 0.15,
          PROFIT_FACTOR: 1.3,
          SORTINO_RATIO: 0.6,
        },
        SORT_BY: 'Win Rate [%]',
        SORT_ASC: false,
        USE_GBM: false,
        async_execution: false,
        SHORT_WINDOW_START: 10,
        SHORT_WINDOW_END: 20,
        LONG_WINDOW_START: 20,
        LONG_WINDOW_END: 50,
        SIGNAL_WINDOW_START: 8,
        SIGNAL_WINDOW_END: 16,
        STEP: 2,
      };

      const mockResponse = {
        data: {
          status: 'success',
          request_id: 'test-125',
          timestamp: '2025-01-01T00:02:00Z',
          ticker: 'ETH-USD',
          strategy_types: ['MACD'],
          portfolios: [],
          total_portfolios_analyzed: 0,
          total_portfolios_filtered: 0,
          execution_time: 8.0,
        },
      };

      mockedAxios.post.mockResolvedValue(mockResponse);

      // First call
      await maCrossApi.analyze(config);

      // Second call with identical configuration
      await maCrossApi.analyze(config);

      // Should only make one API call (second uses cache)
      expect(mockedAxios.post).toHaveBeenCalledTimes(1);
    });
  });

  describe('MACD signal window handling', () => {
    it('should preserve signal_window for MACD results', () => {
      const portfolios = [
        {
          ticker: 'BTC-USD',
          strategy_type: 'MACD',
          short_window: 12,
          long_window: 26,
          signal_window: 9, // MACD signal window
          direction: 'Long',
          timeframe: 'D',
          total_return: 200.0,
          annual_return: 35.0,
          sharpe_ratio: 1.6,
          sortino_ratio: 2.0,
          max_drawdown: 15.0,
          total_trades: 60,
          winning_trades: 38,
          losing_trades: 22,
          win_rate: 0.63,
          profit_factor: 2.4,
          expectancy: 700.0,
          expectancy_per_trade: 700.0,
          score: 1.4,
          beats_bnh: 18.0,
          has_open_trade: false,
          has_signal_entry: true,
        },
      ];

      const mockSyncResponse = {
        status: 'success' as const,
        request_id: 'test-126',
        timestamp: '2025-01-01T00:03:00Z',
        ticker: 'BTC-USD',
        strategy_types: ['MACD'],
        portfolios,
        total_portfolios_analyzed: 1,
        total_portfolios_filtered: 1,
        execution_time: 15.0,
      };

      const results = maCrossApi.responseToResults(mockSyncResponse);

      expect(results).toHaveLength(1);
      expect(results[0].strategy_type).toBe('MACD');
      expect(results[0].signal_window).toBe(9);
      expect(results[0].short_window).toBe(12);
      expect(results[0].long_window).toBe(26);
    });
  });
});
