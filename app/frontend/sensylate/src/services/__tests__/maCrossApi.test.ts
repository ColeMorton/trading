/**
 * Test suite for metric_type handling in MA Cross API service.
 *
 * Tests the frontend API service to ensure metric_type is properly
 * preserved through API calls and data transformations.
 */

import { maCrossApi, PortfolioMetrics } from '../maCrossApi';
import axios from 'axios';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('maCrossApi metric_type handling', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();

    // Clear caches
    maCrossApi.clearCache();
  });

  describe('PortfolioMetrics interface', () => {
    it('should include metric_type field in interface', () => {
      const portfolio: PortfolioMetrics = {
        ticker: 'BTC-USD',
        strategy_type: 'EMA',
        short_window: 5,
        long_window: 10,
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
        metric_type: 'Most Sharpe Ratio, Most Total Return [%]',
      };

      // TypeScript compilation will fail if metric_type is not in the interface
      expect(portfolio.metric_type).toBe(
        'Most Sharpe Ratio, Most Total Return [%]'
      );
    });

    it('should allow optional metric_type field', () => {
      const portfolio: PortfolioMetrics = {
        ticker: 'ETH-USD',
        strategy_type: 'SMA',
        short_window: 12,
        long_window: 26,
        direction: 'Long',
        timeframe: 'D',
        total_return: 100.0,
        annual_return: 20.0,
        sharpe_ratio: 1.0,
        sortino_ratio: 1.2,
        max_drawdown: 15.0,
        total_trades: 30,
        winning_trades: 21,
        losing_trades: 9,
        win_rate: 0.7,
        profit_factor: 1.8,
        expectancy: 300.0,
        expectancy_per_trade: 300.0,
        score: 0.9,
        beats_bnh: 5.0,
        has_open_trade: true,
        has_signal_entry: false,
        // metric_type is optional
      };

      expect(portfolio.metric_type).toBeUndefined();
    });
  });

  describe('portfolioToResult transformation', () => {
    it('should preserve metric_type when transforming portfolio to result', () => {
      const portfolio: PortfolioMetrics = {
        ticker: 'BTC-USD',
        strategy_type: 'EMA',
        short_window: 5,
        long_window: 10,
        signal_window: 0,
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
        metric_type: 'Most Omega Ratio, Most Sharpe Ratio',
      };

      // Access the internal portfolioToResult function through responseToResults
      const mockSyncResponse = {
        status: 'success' as const,
        request_id: 'test-123',
        timestamp: '2025-01-01T00:00:00Z',
        ticker: 'BTC-USD',
        strategy_types: ['EMA'],
        portfolios: [portfolio],
        total_portfolios_analyzed: 1,
        total_portfolios_filtered: 1,
        execution_time: 10.0,
      };

      const results = maCrossApi.responseToResults(mockSyncResponse);

      expect(results).toHaveLength(1);
      expect(results[0].metric_type).toBe(
        'Most Omega Ratio, Most Sharpe Ratio'
      );
      expect(results[0].ticker).toBe('BTC-USD');
      expect(results[0].strategy_type).toBe('EMA');
    });

    it('should handle undefined metric_type gracefully', () => {
      const portfolio: PortfolioMetrics = {
        ticker: 'ETH-USD',
        strategy_type: 'SMA',
        short_window: 12,
        long_window: 26,
        signal_window: 0,
        direction: 'Long',
        timeframe: 'D',
        total_return: 100.0,
        annual_return: 20.0,
        sharpe_ratio: 1.0,
        sortino_ratio: 1.2,
        max_drawdown: 15.0,
        total_trades: 30,
        winning_trades: 21,
        losing_trades: 9,
        win_rate: 0.7,
        profit_factor: 1.8,
        expectancy: 300.0,
        expectancy_per_trade: 300.0,
        score: 0.9,
        beats_bnh: 5.0,
        has_open_trade: true,
        has_signal_entry: false,
        // metric_type is undefined
      };

      const mockSyncResponse = {
        status: 'success' as const,
        request_id: 'test-123',
        timestamp: '2025-01-01T00:00:00Z',
        ticker: 'ETH-USD',
        strategy_types: ['SMA'],
        portfolios: [portfolio],
        total_portfolios_analyzed: 1,
        total_portfolios_filtered: 1,
        execution_time: 10.0,
      };

      const results = maCrossApi.responseToResults(mockSyncResponse);

      expect(results).toHaveLength(1);
      expect(results[0].metric_type).toBeUndefined();
      expect(results[0].ticker).toBe('ETH-USD');
    });

    it('should preserve complex metric_type values', () => {
      const complexMetricType =
        'Most Omega Ratio, Most Sharpe Ratio, Most Sortino Ratio, Most Total Return [%], Median Total Trades';

      const portfolio: PortfolioMetrics = {
        ticker: 'AAPL',
        strategy_type: 'EMA',
        short_window: 26,
        long_window: 45,
        signal_window: 0,
        direction: 'Long',
        timeframe: 'D',
        total_return: 200.0,
        annual_return: 30.0,
        sharpe_ratio: 1.5,
        sortino_ratio: 1.8,
        max_drawdown: 25.0,
        total_trades: 75,
        winning_trades: 45,
        losing_trades: 30,
        win_rate: 0.6,
        profit_factor: 2.2,
        expectancy: 600.0,
        expectancy_per_trade: 600.0,
        score: 1.3,
        beats_bnh: 15.0,
        has_open_trade: false,
        has_signal_entry: true,
        metric_type: complexMetricType,
      };

      const mockSyncResponse = {
        status: 'success' as const,
        request_id: 'test-123',
        timestamp: '2025-01-01T00:00:00Z',
        ticker: 'AAPL',
        strategy_types: ['EMA'],
        portfolios: [portfolio],
        total_portfolios_analyzed: 1,
        total_portfolios_filtered: 1,
        execution_time: 10.0,
      };

      const results = maCrossApi.responseToResults(mockSyncResponse);

      expect(results).toHaveLength(1);
      expect(results[0].metric_type).toBe(complexMetricType);
    });
  });

  describe('getStatus API call', () => {
    it('should preserve metric_type in status response', async () => {
      const mockStatusResponse = {
        data: {
          execution_id: 'test-exec-123',
          status: 'completed' as const,
          progress: 100,
          message: 'Analysis completed',
          results: [
            {
              ticker: 'BTC-USD',
              strategy_type: 'EMA',
              short_window: 5,
              long_window: 10,
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
              score: 1.0,
              beats_bnh: 10.0,
              has_open_trade: false,
              has_signal_entry: true,
              metric_type: 'Most Sharpe Ratio, Most Total Return [%]',
            },
          ],
          timestamp: '2025-01-01T00:01:00Z',
          started_at: '2025-01-01T00:00:00Z',
          completed_at: '2025-01-01T00:01:00Z',
          execution_time: 60.0,
        },
      };

      mockedAxios.get.mockResolvedValue(mockStatusResponse);

      const result = await maCrossApi.getStatus('test-exec-123');

      expect(result.status).toBe('completed');
      expect(result.results).toHaveLength(1);
      expect(result.results![0].metric_type).toBe(
        'Most Sharpe Ratio, Most Total Return [%]'
      );

      // Verify the API was called correctly
      expect(mockedAxios.get).toHaveBeenCalledWith(
        '/api/ma-cross/status/test-exec-123',
        { timeout: 10000 }
      );
    });

    it('should handle empty metric_type in status response', async () => {
      const mockStatusResponse = {
        data: {
          execution_id: 'test-exec-123',
          status: 'completed' as const,
          progress: 100,
          message: 'Analysis completed',
          results: [
            {
              ticker: 'ETH-USD',
              strategy_type: 'SMA',
              short_window: 12,
              long_window: 26,
              total_return: 100.0,
              annual_return: 20.0,
              sharpe_ratio: 1.0,
              sortino_ratio: 1.2,
              max_drawdown: 15.0,
              total_trades: 30,
              winning_trades: 21,
              losing_trades: 9,
              win_rate: 0.7,
              profit_factor: 1.8,
              expectancy: 300.0,
              score: 0.9,
              beats_bnh: 5.0,
              has_open_trade: true,
              has_signal_entry: false,
              metric_type: '', // Empty string
            },
          ],
          timestamp: '2025-01-01T00:01:00Z',
          started_at: '2025-01-01T00:00:00Z',
          completed_at: '2025-01-01T00:01:00Z',
          execution_time: 60.0,
        },
      };

      mockedAxios.get.mockResolvedValue(mockStatusResponse);

      const result = await maCrossApi.getStatus('test-exec-123');

      expect(result.status).toBe('completed');
      expect(result.results).toHaveLength(1);
      expect(result.results![0].metric_type).toBe('');
    });

    it('should handle multiple portfolios with different metric_types', async () => {
      const mockStatusResponse = {
        data: {
          execution_id: 'test-exec-123',
          status: 'completed' as const,
          progress: 100,
          message: 'Analysis completed',
          results: [
            {
              ticker: 'BTC-USD',
              strategy_type: 'EMA',
              short_window: 5,
              long_window: 10,
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
              score: 1.0,
              beats_bnh: 10.0,
              has_open_trade: false,
              has_signal_entry: true,
              metric_type: 'Most Sharpe Ratio',
            },
            {
              ticker: 'ETH-USD',
              strategy_type: 'SMA',
              short_window: 12,
              long_window: 26,
              total_return: 100.0,
              annual_return: 20.0,
              sharpe_ratio: 1.0,
              sortino_ratio: 1.2,
              max_drawdown: 15.0,
              total_trades: 30,
              winning_trades: 21,
              losing_trades: 9,
              win_rate: 0.7,
              profit_factor: 1.8,
              expectancy: 300.0,
              score: 0.9,
              beats_bnh: 5.0,
              has_open_trade: true,
              has_signal_entry: false,
              metric_type: 'Most Total Return [%]',
            },
          ],
          timestamp: '2025-01-01T00:01:00Z',
          started_at: '2025-01-01T00:00:00Z',
          completed_at: '2025-01-01T00:01:00Z',
          execution_time: 120.0,
        },
      };

      mockedAxios.get.mockResolvedValue(mockStatusResponse);

      const result = await maCrossApi.getStatus('test-exec-123');

      expect(result.status).toBe('completed');
      expect(result.results).toHaveLength(2);

      // Verify first portfolio
      expect(result.results![0].ticker).toBe('BTC-USD');
      expect(result.results![0].metric_type).toBe('Most Sharpe Ratio');

      // Verify second portfolio
      expect(result.results![1].ticker).toBe('ETH-USD');
      expect(result.results![1].metric_type).toBe('Most Total Return [%]');
    });
  });

  describe('cache functionality with metric_type', () => {
    it('should cache and retrieve results with metric_type intact', async () => {
      // Mock a successful sync response
      const mockSyncResponse = {
        data: {
          status: 'success',
          request_id: 'test-123',
          timestamp: '2025-01-01T00:00:00Z',
          ticker: 'BTC-USD',
          strategy_types: ['EMA'],
          portfolios: [
            {
              ticker: 'BTC-USD',
              strategy_type: 'EMA',
              short_window: 5,
              long_window: 10,
              signal_window: 0,
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
              metric_type: 'Most Sharpe Ratio, Most Total Return [%]',
            },
          ],
          total_portfolios_analyzed: 1,
          total_portfolios_filtered: 1,
          execution_time: 10.0,
        },
      };

      mockedAxios.post.mockResolvedValue(mockSyncResponse);

      const config = {
        TICKER: 'BTC-USD',
        WINDOWS: 10,
        DIRECTION: 'Long' as const,
        STRATEGY_TYPES: ['EMA' as const],
        USE_HOURLY: false,
        USE_YEARS: false,
        YEARS: 15,
        USE_SYNTHETIC: false,
        REFRESH: false, // This should enable caching
        SORT_BY: 'Score',
        SORT_ASC: false,
        USE_GBM: false,
        USE_CURRENT: true,
        USE_SCANNER: false,
        async_execution: false,
      };

      // First call - should make API request and cache result
      const firstResult = await maCrossApi.analyze(config);

      expect(mockedAxios.post).toHaveBeenCalledTimes(1);
      expect(firstResult.status).toBe('success');

      if ('portfolios' in firstResult) {
        expect(firstResult.portfolios).toHaveLength(1);
        expect(firstResult.portfolios[0].metric_type).toBe(
          'Most Sharpe Ratio, Most Total Return [%]'
        );
      }

      // Second call with same config - should return cached result
      const secondResult = await maCrossApi.analyze(config);

      // Should not make another API call
      expect(mockedAxios.post).toHaveBeenCalledTimes(1);
      expect(secondResult.status).toBe('success');

      if ('portfolios' in secondResult) {
        expect(secondResult.portfolios).toHaveLength(1);
        expect(secondResult.portfolios[0].metric_type).toBe(
          'Most Sharpe Ratio, Most Total Return [%]'
        );
      }
    });

    it('should clear cache successfully', async () => {
      // Clear cache should not throw
      await expect(maCrossApi.clearCache()).resolves.not.toThrow();
    });
  });
});
