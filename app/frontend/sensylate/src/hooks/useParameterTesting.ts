import { useState, useCallback, useRef, useEffect } from 'react';
import { AnalysisConfiguration, AnalysisResult } from '../types';
import { maCrossApi } from '../services/serviceFactory';
import {
  MACrossSyncResponse,
  MACrossAsyncResponse,
} from '../services/maCrossApi';

export interface UseParameterTestingReturn {
  analyze: (config: AnalysisConfiguration) => Promise<void>;
  results: AnalysisResult[];
  isAnalyzing: boolean;
  progress: number;
  error: string | null;
  executionId: string | null;
  clearResults: () => void;
  cancelAnalysis: () => void;
}

// Streamlined state interface
interface AnalysisState {
  status: 'idle' | 'analyzing' | 'completed' | 'error';
  results: AnalysisResult[];
  progress: number;
  error: string | null;
  executionId: string | null;
}

const POLLING_INTERVAL = 1000; // 1 second
const MAX_POLLING_ATTEMPTS = 600; // 10 minutes max

export const useParameterTesting = (): UseParameterTestingReturn => {
  // Unified state management
  const [state, setState] = useState<AnalysisState>({
    status: 'idle',
    results: [],
    progress: 0,
    error: null,
    executionId: null,
  });

  // Refs for polling management
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const pollingAttemptsRef = useRef(0);
  const isCancelledRef = useRef(false);

  // Derived state for backward compatibility
  const isAnalyzing = state.status === 'analyzing';
  const { results, progress, error, executionId } = state;

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Simplified polling for async execution status
  const pollStatus = useCallback(async (execId: string) => {
    try {
      const status = await maCrossApi.getStatus(execId);

      // Check if cancelled
      if (isCancelledRef.current) {
        setState((prev) => ({ ...prev, status: 'idle', progress: 0 }));
        return;
      }

      // Update progress
      const progressValue =
        typeof status.progress === 'number' ? status.progress : 0;

      setState((prev) => ({ ...prev, progress: progressValue }));

      // Handle different status states
      switch (status.status) {
        case 'completed': {
          // Analysis completed successfully
          let analysisResults: AnalysisResult[] = [];

          if (status.results) {
            // Convert API results to AnalysisResult format
            analysisResults = status.results.map((portfolio) => ({
              ticker: portfolio.ticker,
              strategy_type: portfolio.strategy_type,
              short_window: portfolio.short_window,
              long_window: portfolio.long_window,
              signal_window: portfolio.signal_window || 0,
              direction: portfolio.direction,
              timeframe: portfolio.timeframe,
              total_trades: portfolio.total_trades,
              win_rate: portfolio.win_rate,
              profit_factor: portfolio.profit_factor,
              expectancy_per_trade:
                portfolio.expectancy_per_trade || portfolio.expectancy || 0,
              sortino_ratio: portfolio.sortino_ratio,
              max_drawdown: portfolio.max_drawdown,
              total_return: portfolio.total_return,
              annual_return: portfolio.annual_return,
              sharpe_ratio: portfolio.sharpe_ratio,
              winning_trades: portfolio.winning_trades,
              losing_trades: portfolio.losing_trades,
              score: portfolio.score,
              beats_bnh: portfolio.beats_bnh,
              has_open_trade: portfolio.has_open_trade,
              has_signal_entry: portfolio.has_signal_entry,
              metric_type: portfolio.metric_type,
            }));
          } else if (status.result) {
            // Legacy API format: full response object
            analysisResults = maCrossApi.responseToResults(status.result);
          }

          setState({
            status: 'completed',
            results: analysisResults,
            progress: 100,
            error: null,
            executionId: execId,
          });

          // Clear polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          break;
        }

        case 'failed':
          setState({
            status: 'error',
            results: [],
            progress: 0,
            error: status.error || 'Analysis failed',
            executionId: execId,
          });

          // Clear polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          break;

        case 'running':
        case 'pending':
          // Still processing - continue polling
          pollingAttemptsRef.current++;

          // Check max attempts
          if (pollingAttemptsRef.current >= MAX_POLLING_ATTEMPTS) {
            setState({
              status: 'error',
              results: [],
              progress: 0,
              error: 'Analysis timeout - exceeded maximum wait time',
              executionId: execId,
            });

            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
          break;
      }
    } catch (err) {
      console.error('Error polling status:', err);
      pollingAttemptsRef.current++;

      if (pollingAttemptsRef.current >= MAX_POLLING_ATTEMPTS) {
        setState({
          status: 'error',
          results: [],
          progress: 0,
          error: 'Failed to get analysis status',
          executionId: execId,
        });

        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }
    }
  }, []);

  // Streamlined analysis function
  const analyze = useCallback(
    async (config: AnalysisConfiguration) => {
      try {
        // Reset state and setup for new analysis
        setState({
          status: 'analyzing',
          results: [],
          progress: 0,
          error: null,
          executionId: null,
        });

        isCancelledRef.current = false;
        pollingAttemptsRef.current = 0;

        // Clear any existing polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }

        // Make API call
        const response = await maCrossApi.analyze(config);

        // Handle synchronous response
        if ('portfolios' in response) {
          const syncResponse = response as MACrossSyncResponse;

          if (syncResponse.status === 'success') {
            const analysisResults = maCrossApi.responseToResults(syncResponse);
            setState({
              status: 'completed',
              results: analysisResults,
              progress: 100,
              error: null,
              executionId: null,
            });
          } else {
            throw new Error(syncResponse.error || 'Analysis failed');
          }
        } else {
          // Handle asynchronous response
          const asyncResponse = response as MACrossAsyncResponse;

          setState((prev) => ({
            ...prev,
            executionId: asyncResponse.execution_id,
          }));

          // Start polling for status
          pollingIntervalRef.current = setInterval(() => {
            pollStatus(asyncResponse.execution_id);
          }, POLLING_INTERVAL);

          // Do initial poll immediately
          pollStatus(asyncResponse.execution_id);
        }
      } catch (err) {
        console.error('Analysis error:', err);
        setState({
          status: 'error',
          results: [],
          progress: 0,
          error: err instanceof Error ? err.message : 'Analysis failed',
          executionId: null,
        });
      }
    },
    [pollStatus]
  );

  // Clear results
  const clearResults = useCallback(() => {
    setState({
      status: 'idle',
      results: [],
      progress: 0,
      error: null,
      executionId: null,
    });
  }, []);

  // Cancel ongoing analysis
  const cancelAnalysis = useCallback(() => {
    isCancelledRef.current = true;

    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }

    setState({
      status: 'idle',
      results: [],
      progress: 0,
      error: null,
      executionId: null,
    });
  }, []);

  return {
    analyze,
    results,
    isAnalyzing,
    progress,
    error,
    executionId,
    clearResults,
    cancelAnalysis,
  };
};
