/**
 * Test suite for metric_type handling in useParameterTesting hook.
 *
 * Tests the hook to ensure metric_type is properly preserved
 * through both async and sync result processing paths.
 */

import { renderHook, act } from '@testing-library/react';
import { useParameterTesting } from '../useParameterTesting';
import { maCrossApi } from '../services/serviceFactory';
import {
  MACrossSyncResponse,
  MACrossAsyncResponse,
  ExecutionStatusResponse,
} from '../services/maCrossApi';

// Mock the maCrossApi
jest.mock('../services/serviceFactory', () => ({
  maCrossApi: {
    analyze: jest.fn(),
    getStatus: jest.fn(),
    responseToResults: jest.fn(),
  },
}));

const mockMaCrossApi = maCrossApi as jest.Mocked<typeof maCrossApi>;

describe('useParameterTesting metric_type handling', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  const sampleConfig = {
    TICKER: 'BTC-USD',
    WINDOWS: 10,
    DIRECTION: 'Long' as const,
    STRATEGY_TYPES: ['EMA' as const],
    USE_HOURLY: false,
    USE_YEARS: false,
    YEARS: 15,
    USE_SYNTHETIC: false,
    REFRESH: true,
    SORT_BY: 'Score',
    SORT_ASC: false,
    USE_GBM: false,
    USE_CURRENT: true,
    USE_SCANNER: false,
    async_execution: false,
  };

  describe('synchronous analysis with metric_type', () => {
    it('should handle sync response with metric_type using responseToResults', async () => {
      const mockSyncResponse: MACrossSyncResponse = {
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
      };

      const mockAnalysisResults = [
        {
          ticker: 'BTC-USD',
          strategy_type: 'EMA',
          short_window: 5,
          long_window: 10,
          signal_window: 0,
          direction: 'Long',
          timeframe: 'D',
          total_trades: 50,
          win_rate: 0.6,
          profit_factor: 2.0,
          expectancy_per_trade: 500.0,
          sortino_ratio: 1.5,
          max_drawdown: 20.0,
          total_return: 150.0,
          annual_return: 25.0,
          sharpe_ratio: 1.2,
          winning_trades: 30,
          losing_trades: 20,
          score: 1.0,
          beats_bnh: 10.0,
          has_open_trade: false,
          has_signal_entry: true,
          metric_type: 'Most Sharpe Ratio, Most Total Return [%]',
        },
      ];

      mockMaCrossApi.analyze.mockResolvedValue(mockSyncResponse);
      mockMaCrossApi.responseToResults.mockReturnValue(mockAnalysisResults);

      const { result } = renderHook(() => useParameterTesting());

      await act(async () => {
        await result.current.analyze(sampleConfig);
      });

      expect(result.current.results).toHaveLength(1);
      expect(result.current.results[0].metric_type).toBe(
        'Most Sharpe Ratio, Most Total Return [%]'
      );
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.error).toBe(null);
      expect(result.current.progress).toBe(100);

      // Verify responseToResults was called correctly
      expect(mockMaCrossApi.responseToResults).toHaveBeenCalledWith(
        mockSyncResponse
      );
    });
  });

  describe('asynchronous analysis with metric_type', () => {
    it('should handle async response with metric_type in status.results path', async () => {
      const mockAsyncResponse: MACrossAsyncResponse = {
        status: 'accepted',
        execution_id: 'test-exec-123',
        message: 'Analysis started',
        status_url: '/api/ma-cross/status/test-exec-123',
        stream_url: '/api/ma-cross/stream/test-exec-123',
        timestamp: '2025-01-01T00:00:00Z',
      };

      const mockStatusResponse: ExecutionStatusResponse = {
        execution_id: 'test-exec-123',
        status: 'completed',
        progress: 100,
        message: 'Analysis completed',
        results: [
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
            metric_type: 'Most Omega Ratio, Most Sharpe Ratio',
          },
        ],
        timestamp: '2025-01-01T00:01:00Z',
        started_at: '2025-01-01T00:00:00Z',
        completed_at: '2025-01-01T00:01:00Z',
        execution_time: 60.0,
      };

      mockMaCrossApi.analyze.mockResolvedValue(mockAsyncResponse);
      mockMaCrossApi.getStatus.mockResolvedValue(mockStatusResponse);

      const { result } = renderHook(() => useParameterTesting());

      // Start analysis
      await act(async () => {
        await result.current.analyze({
          ...sampleConfig,
          async_execution: true,
        });
      });

      expect(result.current.executionId).toBe('test-exec-123');
      expect(result.current.isAnalyzing).toBe(true);

      // Simulate polling completion
      await act(async () => {
        jest.advanceTimersByTime(1000); // Advance by polling interval
      });

      expect(result.current.results).toHaveLength(1);
      expect(result.current.results[0].metric_type).toBe(
        'Most Omega Ratio, Most Sharpe Ratio'
      );
      expect(result.current.results[0].ticker).toBe('BTC-USD');
      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.progress).toBe(100);
    });

    it('should handle async response with metric_type in status.result path', async () => {
      const mockAsyncResponse: MACrossAsyncResponse = {
        status: 'accepted',
        execution_id: 'test-exec-456',
        message: 'Analysis started',
        status_url: '/api/ma-cross/status/test-exec-456',
        stream_url: '/api/ma-cross/stream/test-exec-456',
        timestamp: '2025-01-01T00:00:00Z',
      };

      const mockSyncResult: MACrossSyncResponse = {
        status: 'success',
        request_id: 'test-456',
        timestamp: '2025-01-01T00:01:00Z',
        ticker: 'ETH-USD',
        strategy_types: ['SMA'],
        portfolios: [
          {
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
            metric_type: 'Most Total Return [%]',
          },
        ],
        total_portfolios_analyzed: 1,
        total_portfolios_filtered: 1,
        execution_time: 60.0,
      };

      const mockStatusResponse: ExecutionStatusResponse = {
        execution_id: 'test-exec-456',
        status: 'completed',
        progress: 100,
        message: 'Analysis completed',
        result: mockSyncResult, // Legacy format
        timestamp: '2025-01-01T00:01:00Z',
        started_at: '2025-01-01T00:00:00Z',
        completed_at: '2025-01-01T00:01:00Z',
        execution_time: 60.0,
      };

      const mockAnalysisResults = [
        {
          ticker: 'ETH-USD',
          strategy_type: 'SMA',
          short_window: 12,
          long_window: 26,
          signal_window: 0,
          direction: 'Long',
          timeframe: 'D',
          total_trades: 30,
          win_rate: 0.7,
          profit_factor: 1.8,
          expectancy_per_trade: 300.0,
          sortino_ratio: 1.2,
          max_drawdown: 15.0,
          total_return: 100.0,
          annual_return: 20.0,
          sharpe_ratio: 1.0,
          winning_trades: 21,
          losing_trades: 9,
          score: 0.9,
          beats_bnh: 5.0,
          has_open_trade: true,
          has_signal_entry: false,
          metric_type: 'Most Total Return [%]',
        },
      ];

      mockMaCrossApi.analyze.mockResolvedValue(mockAsyncResponse);
      mockMaCrossApi.getStatus.mockResolvedValue(mockStatusResponse);
      mockMaCrossApi.responseToResults.mockReturnValue(mockAnalysisResults);

      const { result } = renderHook(() => useParameterTesting());

      // Start analysis
      await act(async () => {
        await result.current.analyze({
          ...sampleConfig,
          ticker: 'ETH-USD',
          strategy_types: ['SMA'],
          async_execution: true,
        });
      });

      expect(result.current.executionId).toBe('test-exec-456');
      expect(result.current.isAnalyzing).toBe(true);

      // Simulate polling completion
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.results).toHaveLength(1);
      expect(result.current.results[0].metric_type).toBe(
        'Most Total Return [%]'
      );
      expect(result.current.results[0].ticker).toBe('ETH-USD');
      expect(result.current.isAnalyzing).toBe(false);

      // Verify responseToResults was called for legacy format
      expect(mockMaCrossApi.responseToResults).toHaveBeenCalledWith(
        mockSyncResult
      );
    });

    it('should handle multiple portfolios with different metric_types in async results', async () => {
      const mockAsyncResponse: MACrossAsyncResponse = {
        status: 'accepted',
        execution_id: 'test-exec-789',
        message: 'Analysis started',
        status_url: '/api/ma-cross/status/test-exec-789',
        stream_url: '/api/ma-cross/stream/test-exec-789',
        timestamp: '2025-01-01T00:00:00Z',
      };

      const mockStatusResponse: ExecutionStatusResponse = {
        execution_id: 'test-exec-789',
        status: 'completed',
        progress: 100,
        message: 'Analysis completed',
        results: [
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
            metric_type: 'Most Sharpe Ratio',
          },
          {
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
            metric_type: 'Most Total Return [%]',
          },
        ],
        timestamp: '2025-01-01T00:02:00Z',
        started_at: '2025-01-01T00:00:00Z',
        completed_at: '2025-01-01T00:02:00Z',
        execution_time: 120.0,
      };

      mockMaCrossApi.analyze.mockResolvedValue(mockAsyncResponse);
      mockMaCrossApi.getStatus.mockResolvedValue(mockStatusResponse);

      const { result } = renderHook(() => useParameterTesting());

      // Start analysis
      await act(async () => {
        await result.current.analyze({
          ...sampleConfig,
          ticker: ['BTC-USD', 'ETH-USD'],
          strategy_types: ['EMA', 'SMA'],
          async_execution: true,
        });
      });

      // Simulate polling completion
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.results).toHaveLength(2);

      // Verify first portfolio
      expect(result.current.results[0].ticker).toBe('BTC-USD');
      expect(result.current.results[0].metric_type).toBe('Most Sharpe Ratio');

      // Verify second portfolio
      expect(result.current.results[1].ticker).toBe('ETH-USD');
      expect(result.current.results[1].metric_type).toBe(
        'Most Total Return [%]'
      );
    });

    it('should handle undefined/empty metric_type in async results', async () => {
      const mockAsyncResponse: MACrossAsyncResponse = {
        status: 'accepted',
        execution_id: 'test-exec-empty',
        message: 'Analysis started',
        status_url: '/api/ma-cross/status/test-exec-empty',
        stream_url: '/api/ma-cross/stream/test-exec-empty',
        timestamp: '2025-01-01T00:00:00Z',
      };

      const mockStatusResponse: ExecutionStatusResponse = {
        execution_id: 'test-exec-empty',
        status: 'completed',
        progress: 100,
        message: 'Analysis completed',
        results: [
          {
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
            // metric_type is undefined
          },
        ],
        timestamp: '2025-01-01T00:01:30Z',
        started_at: '2025-01-01T00:00:00Z',
        completed_at: '2025-01-01T00:01:30Z',
        execution_time: 90.0,
      };

      mockMaCrossApi.analyze.mockResolvedValue(mockAsyncResponse);
      mockMaCrossApi.getStatus.mockResolvedValue(mockStatusResponse);

      const { result } = renderHook(() => useParameterTesting());

      // Start analysis
      await act(async () => {
        await result.current.analyze({
          ...sampleConfig,
          ticker: 'AAPL',
          async_execution: true,
        });
      });

      // Simulate polling completion
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.results).toHaveLength(1);
      expect(result.current.results[0].ticker).toBe('AAPL');
      expect(result.current.results[0].metric_type).toBeUndefined();
    });
  });

  describe('error scenarios with metric_type', () => {
    it('should handle failed analysis gracefully', async () => {
      const mockAsyncResponse: MACrossAsyncResponse = {
        status: 'accepted',
        execution_id: 'test-exec-fail',
        message: 'Analysis started',
        status_url: '/api/ma-cross/status/test-exec-fail',
        stream_url: '/api/ma-cross/stream/test-exec-fail',
        timestamp: '2025-01-01T00:00:00Z',
      };

      const mockFailedStatusResponse: ExecutionStatusResponse = {
        execution_id: 'test-exec-fail',
        status: 'failed',
        progress: 0,
        message: 'Analysis failed',
        error: 'Internal server error',
        timestamp: '2025-01-01T00:00:30Z',
        started_at: '2025-01-01T00:00:00Z',
      };

      mockMaCrossApi.analyze.mockResolvedValue(mockAsyncResponse);
      mockMaCrossApi.getStatus.mockResolvedValue(mockFailedStatusResponse);

      const { result } = renderHook(() => useParameterTesting());

      // Start analysis
      await act(async () => {
        await result.current.analyze({
          ...sampleConfig,
          async_execution: true,
        });
      });

      // Simulate polling failure
      await act(async () => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.error).toBe('Internal server error');
      expect(result.current.results).toHaveLength(0);
    });
  });

  describe('utility functions', () => {
    it('should clear results properly', () => {
      const { result } = renderHook(() => useParameterTesting());

      act(() => {
        result.current.clearResults();
      });

      expect(result.current.results).toHaveLength(0);
      expect(result.current.error).toBe(null);
      expect(result.current.progress).toBe(0);
      expect(result.current.executionId).toBe(null);
    });

    it('should cancel analysis properly', () => {
      const { result } = renderHook(() => useParameterTesting());

      act(() => {
        result.current.cancelAnalysis();
      });

      expect(result.current.isAnalyzing).toBe(false);
      expect(result.current.progress).toBe(0);
      expect(result.current.executionId).toBe(null);
    });
  });
});
