import axios from 'axios';
import { AnalysisConfiguration, AnalysisResult } from '../types';

// API request interfaces matching backend models
export interface MACrossRequest {
  ticker: string | string[];
  windows?: number;
  direction?: 'Long' | 'Short';
  strategy_types?: ('SMA' | 'EMA')[];
  use_hourly?: boolean;
  use_years?: boolean;
  years?: number;
  use_synthetic?: boolean;
  ticker_1?: string;
  ticker_2?: string;
  refresh?: boolean;
  minimums?: {
    trades?: number;
    win_rate?: number;
    expectancy_per_trade?: number;
    profit_factor?: number;
    score?: number;
    sortino_ratio?: number;
    beats_bnh?: number;
  };
  sort_by?: string;
  sort_asc?: boolean;
  use_gbm?: boolean;
  use_current?: boolean;
  use_scanner?: boolean;
  async_execution?: boolean;
}

// Portfolio metrics returned by the API
export interface PortfolioMetrics {
  ticker: string;
  strategy_type: string;
  short_window: number;
  long_window: number;
  signal_window?: number;
  direction: string;
  timeframe: string;
  total_return: number;
  annual_return: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  max_drawdown: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  profit_factor: number;
  expectancy: number;
  expectancy_per_trade?: number;
  score: number;
  beats_bnh: number;
  has_open_trade: boolean;
  has_signal_entry: boolean;
  metric_type?: string; // Metric type classification
  [key: string]: any; // Allow additional metrics
}

// Synchronous API response
export interface MACrossSyncResponse {
  status: 'success' | 'error';
  request_id: string;
  timestamp: string;
  ticker: string | string[];
  strategy_types: string[];
  portfolios: PortfolioMetrics[];
  portfolio_exports?: {
    [key: string]: string; // CSV file paths
  };
  total_portfolios_analyzed: number;
  total_portfolios_filtered: number;
  execution_time: number;
  error?: string;
  error_details?: any;
}

// Asynchronous API response
export interface MACrossAsyncResponse {
  status: 'accepted';
  execution_id: string;
  message: string;
  status_url: string;
  stream_url: string;
  timestamp: string;
  estimated_time?: number;
}

// Status polling response
export interface ExecutionStatusResponse {
  execution_id?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number | string;
  message?: string;
  result?: MACrossSyncResponse;
  results?: PortfolioMetrics[]; // Direct results array for completed executions
  error?: string;
  error_details?: any;
  timestamp?: string;
  started_at?: string;
  completed_at?: string;
  execution_time?: number;
  estimated_time_remaining?: number;
}

// Simple in-memory cache for results
const resultsCache = new Map<string, MACrossSyncResponse>();

// IndexedDB storage for offline support
const DB_NAME = 'sensylate-ma-cross';
const DB_VERSION = 1;
const STORE_NAME = 'analysis-results';

// Initialize IndexedDB
const initDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const store = db.createObjectStore(STORE_NAME, { keyPath: 'cacheKey' });
        store.createIndex('timestamp', 'timestamp', { unique: false });
      }
    };
  });
};

// Save results to IndexedDB
const saveToIndexedDB = async (
  cacheKey: string,
  response: MACrossSyncResponse
) => {
  try {
    const db = await initDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    await store.put({
      cacheKey,
      response,
      timestamp: Date.now(),
    });

    // Clean up old entries (keep last 50)
    const allKeysRequest = store.getAllKeys();
    const allKeys = await new Promise<IDBValidKey[]>((resolve) => {
      allKeysRequest.onsuccess = () => resolve(allKeysRequest.result);
    });

    if (allKeys.length > 50) {
      const keysToDelete = allKeys.slice(0, allKeys.length - 50);
      for (const key of keysToDelete) {
        await store.delete(key);
      }
    }
  } catch (error) {
    console.error('Failed to save to IndexedDB:', error);
  }
};

// Load results from IndexedDB
const loadFromIndexedDB = async (
  cacheKey: string
): Promise<MACrossSyncResponse | null> => {
  try {
    const db = await initDB();
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);

    const request = store.get(cacheKey);
    const result = await new Promise<any>((resolve) => {
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => resolve(null);
    });

    if (result && result.timestamp) {
      // Check if cache is not too old (24 hours)
      const age = Date.now() - result.timestamp;
      if (age < 24 * 60 * 60 * 1000) {
        return result.response;
      }
    }
  } catch (error) {
    console.error('Failed to load from IndexedDB:', error);
  }

  return null;
};

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1 second

// Helper to generate cache key from configuration
const getCacheKey = (config: AnalysisConfiguration): string => {
  const ticker = Array.isArray(config.TICKER)
    ? config.TICKER.join(',')
    : config.TICKER;
  return `${ticker}-${config.WINDOWS}-${
    config.DIRECTION
  }-${config.STRATEGY_TYPES.join(',')}-${config.USE_HOURLY}`;
};

// Helper function to wait
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Retry logic wrapper
async function withRetry<T>(
  fn: () => Promise<T>,
  retries = MAX_RETRIES,
  delay = RETRY_DELAY
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0) {
      // Only retry on network errors or 5xx server errors
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        if (!status || status >= 500 || error.code === 'ECONNABORTED') {
          console.log(`Retrying after ${delay}ms... (${retries} retries left)`);
          await wait(delay);
          return withRetry(fn, retries - 1, delay * 2); // Exponential backoff
        }
      }
    }
    throw error;
  }
}

// Convert frontend configuration to API request format
const configToRequest = (config: AnalysisConfiguration): MACrossRequest => {
  const request: MACrossRequest = {
    ticker: config.TICKER,
    windows: config.WINDOWS,
    direction: config.DIRECTION,
    strategy_types: config.STRATEGY_TYPES,
    use_hourly: config.USE_HOURLY,
    use_years: config.USE_YEARS,
    years: config.YEARS,
    use_synthetic: config.USE_SYNTHETIC,
    refresh: config.REFRESH,
    sort_by: config.SORT_BY,
    sort_asc: config.SORT_ASC,
    use_gbm: config.USE_GBM,
    use_current: config.USE_CURRENT,
    use_scanner: config.USE_SCANNER,
    async_execution: config.async_execution,
  };

  // Only include minimums if they have values
  if (config.MINIMUMS) {
    const minimums: any = {};

    // Convert win_rate from percentage to decimal (44 -> 0.44)
    if (
      config.MINIMUMS.WIN_RATE !== undefined &&
      config.MINIMUMS.WIN_RATE !== null
    ) {
      minimums.win_rate = config.MINIMUMS.WIN_RATE / 100;
    }

    if (
      config.MINIMUMS.TRADES !== undefined &&
      config.MINIMUMS.TRADES !== null
    ) {
      minimums.trades = config.MINIMUMS.TRADES;
    }

    if (
      config.MINIMUMS.EXPECTANCY_PER_TRADE !== undefined &&
      config.MINIMUMS.EXPECTANCY_PER_TRADE !== null
    ) {
      minimums.expectancy_per_trade = config.MINIMUMS.EXPECTANCY_PER_TRADE;
    }

    if (
      config.MINIMUMS.PROFIT_FACTOR !== undefined &&
      config.MINIMUMS.PROFIT_FACTOR !== null
    ) {
      minimums.profit_factor = config.MINIMUMS.PROFIT_FACTOR;
    }

    if (
      config.MINIMUMS.SORTINO_RATIO !== undefined &&
      config.MINIMUMS.SORTINO_RATIO !== null
    ) {
      minimums.sortino_ratio = config.MINIMUMS.SORTINO_RATIO;
    }

    // Only add minimums if there's at least one value
    if (Object.keys(minimums).length > 0) {
      request.minimums = minimums;
    }
  }

  return request;
};

// Convert API portfolio metrics to frontend result format
const portfolioToResult = (portfolio: PortfolioMetrics): AnalysisResult => {
  return {
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
      portfolio.expectancy_per_trade || portfolio.expectancy,
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
  };
};

// Configuration presets interfaces
export interface ConfigPreset {
  name: string;
  config: Partial<AnalysisConfiguration>;
}

export interface ConfigPresetsResponse {
  status: string;
  presets: ConfigPreset[];
  timestamp: string;
}

export const maCrossApi = {
  // Get configuration presets
  getConfigPresets: async (): Promise<ConfigPreset[]> => {
    try {
      const response = await withRetry(() =>
        axios.get<ConfigPresetsResponse>('/api/ma-cross/config-presets', {
          timeout: 10000, // 10 second timeout
        })
      );

      return response.data.presets;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorResponse = error.response?.data;
        let errorMessage = 'Failed to load configuration presets';

        if (errorResponse?.detail) {
          errorMessage = errorResponse.detail;
        } else if (errorResponse?.error) {
          errorMessage = errorResponse.error;
        } else if (error.message) {
          errorMessage = error.message;
        }

        throw new Error(errorMessage);
      }
      throw error;
    }
  },

  // Main analysis function
  analyze: async (
    config: AnalysisConfiguration
  ): Promise<MACrossSyncResponse | MACrossAsyncResponse> => {
    try {
      const cacheKey = getCacheKey(config);

      // Check cache first if not refreshing
      if (!config.REFRESH) {
        // Check in-memory cache first
        const cached = resultsCache.get(cacheKey);
        if (cached) {
          console.log('Returning in-memory cached results for', cacheKey);
          return cached;
        }

        // Check IndexedDB for offline support
        const offlineCached = await loadFromIndexedDB(cacheKey);
        if (offlineCached) {
          console.log('Returning offline cached results for', cacheKey);
          // Also update in-memory cache
          resultsCache.set(cacheKey, offlineCached);
          return offlineCached;
        }
      }

      // Convert configuration to API request format
      const request = configToRequest(config);

      // Make API call with retry logic
      const response = await withRetry(() =>
        axios.post<MACrossSyncResponse | MACrossAsyncResponse>(
          '/api/ma-cross/analyze',
          request,
          {
            timeout: 30000, // 30 second timeout
          }
        )
      );

      // Handle synchronous response
      if (response.data.status === 'success') {
        const syncResponse = response.data as MACrossSyncResponse;
        // Cache the results
        resultsCache.set(cacheKey, syncResponse);
        // Also save to IndexedDB for offline support
        await saveToIndexedDB(cacheKey, syncResponse);
        return syncResponse;
      }

      // Return async response for polling
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorResponse = error.response?.data;
        let errorMessage = 'MA Cross analysis failed';

        if (errorResponse?.detail) {
          errorMessage = errorResponse.detail;
        } else if (errorResponse?.error) {
          errorMessage = errorResponse.error;
        } else if (error.message) {
          errorMessage = error.message;
        }

        throw new Error(errorMessage);
      }
      throw error;
    }
  },

  // Poll for async execution status
  getStatus: async (executionId: string): Promise<ExecutionStatusResponse> => {
    try {
      const response = await withRetry(() =>
        axios.get<ExecutionStatusResponse>(
          `/api/ma-cross/status/${executionId}`,
          {
            timeout: 10000, // 10 second timeout for status checks
          }
        )
      );

      // Debug: Log what we receive from the API
      if (
        response.data.status === 'completed' &&
        response.data.results &&
        response.data.results.length > 0
      ) {
        const firstResult = response.data.results[0];
        console.log(
          '🔍 API Response Debug - First result keys:',
          Object.keys(firstResult)
        );
        console.log(
          '🔍 API Response Debug - metric_type present:',
          'metric_type' in firstResult
        );
        console.log(
          '🔍 API Response Debug - metric_type value:',
          firstResult.metric_type
        );
        console.log(
          '🔍 API Response Debug - Raw first result:',
          JSON.stringify(firstResult, null, 2)
        );
      }

      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const errorResponse = error.response?.data;
        let errorMessage = 'Failed to get execution status';

        if (errorResponse?.detail) {
          errorMessage = errorResponse.detail;
        } else if (errorResponse?.error) {
          errorMessage = errorResponse.error;
        } else if (error.message) {
          errorMessage = error.message;
        }

        throw new Error(errorMessage);
      }
      throw error;
    }
  },

  // Helper to convert sync response to results array
  responseToResults: (response: MACrossSyncResponse): AnalysisResult[] => {
    return response.portfolios.map(portfolioToResult);
  },

  // Clear the cache (useful when changing configurations)
  clearCache: async () => {
    resultsCache.clear();

    // Also clear IndexedDB cache
    try {
      const db = await initDB();
      const transaction = db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      await store.clear();
      console.log('🧹 All caches cleared (in-memory + IndexedDB)');
    } catch (error) {
      console.error('Failed to clear IndexedDB cache:', error);
    }
  },
};
