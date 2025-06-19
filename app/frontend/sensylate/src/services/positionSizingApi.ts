import axios from 'axios';
import {
  PositionSizingDashboard,
  PositionSizingRequest,
  PositionSizingResponse,
  PositionEntryRequest,
  PositionUpdateRequest,
  AccountBalanceUpdate,
  KellyParametersUpdate,
  ExcelValidationRequest,
  ValidationResult,
  RiskAllocationSummary,
  PositionAnalysis,
  TradingPosition,
} from '../types';

// API response wrapper interface
interface ApiResponse<T> {
  status: 'success' | 'error' | 'warning';
  data: T;
  message?: string;
  timestamp: string;
}

// Simple caching for dashboard data with TTL
const cache = {
  dashboard: null as PositionSizingDashboard | null,
  lastFetch: 0,
  TTL: 30000, // 30 seconds cache
};

export const positionSizingApi = {
  /**
   * Get complete position sizing dashboard data
   */
  getDashboard: async (): Promise<PositionSizingDashboard> => {
    try {
      // Check cache first
      const now = Date.now();
      if (cache.dashboard && now - cache.lastFetch < cache.TTL) {
        return cache.dashboard;
      }

      const response = await axios.get<ApiResponse<PositionSizingDashboard>>(
        '/api/position-sizing/dashboard'
      );

      if (response.data.status !== 'success') {
        throw new Error(
          response.data.message || 'Failed to fetch dashboard data'
        );
      }

      const dashboard = response.data.data;

      // Update cache
      cache.dashboard = dashboard;
      cache.lastFetch = now;

      return dashboard;
    } catch (error) {
      // If network fails and we have cached data, return it
      if (cache.dashboard) {
        console.warn(
          'Using cached dashboard data due to network error:',
          error
        );
        return cache.dashboard;
      }
      throw error;
    }
  },

  /**
   * Calculate position size for a new signal
   */
  calculatePositionSize: async (
    request: PositionSizingRequest
  ): Promise<PositionSizingResponse> => {
    const response = await axios.post<ApiResponse<PositionSizingResponse>>(
      '/api/position-sizing/calculate',
      request
    );

    if (response.data.status !== 'success') {
      throw new Error(
        response.data.message || 'Position sizing calculation failed'
      );
    }

    return response.data.data;
  },

  /**
   * Get all active positions with optional filtering
   */
  getActivePositions: async (
    portfolioType?: 'Risk_On' | 'Investment'
  ): Promise<{
    positions: TradingPosition[];
    totalCount: number;
    totalValue: number;
    totalRisk: number;
  }> => {
    const params = portfolioType ? { portfolio_type: portfolioType } : {};
    const response = await axios.get<
      ApiResponse<{
        positions: TradingPosition[];
        totalCount: number;
        totalValue: number;
        totalRisk: number;
      }>
    >('/api/position-sizing/positions', { params });

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to fetch positions');
    }

    return response.data.data;
  },

  /**
   * Get detailed analysis for a specific position
   */
  getPositionAnalysis: async (symbol: string): Promise<PositionAnalysis> => {
    const response = await axios.get<ApiResponse<PositionAnalysis>>(
      `/api/position-sizing/positions/${symbol.toUpperCase()}`
    );

    if (response.data.status !== 'success') {
      throw new Error(
        response.data.message || 'Failed to fetch position analysis'
      );
    }

    return response.data.data;
  },

  /**
   * Add a new position entry from manual trade fill
   */
  addPositionEntry: async (request: PositionEntryRequest): Promise<any> => {
    const response = await axios.post<ApiResponse<any>>(
      '/api/position-sizing/positions',
      request
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to add position');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Update position metrics for an existing position
   */
  updatePositionMetrics: async (
    symbol: string,
    updates: PositionUpdateRequest
  ): Promise<any> => {
    const response = await axios.put<ApiResponse<any>>(
      `/api/position-sizing/positions/${symbol.toUpperCase()}`,
      updates
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to update position');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Update account balance
   */
  updateAccountBalance: async (request: AccountBalanceUpdate): Promise<any> => {
    const response = await axios.post<ApiResponse<any>>(
      '/api/position-sizing/accounts/balance',
      request
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to update balance');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Get all account balances
   */
  getAccountBalances: async (): Promise<any> => {
    const response = await axios.get<ApiResponse<any>>(
      '/api/position-sizing/accounts/balances'
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to fetch balances');
    }

    return response.data.data;
  },

  /**
   * Update Kelly criterion parameters
   */
  updateKellyParameters: async (
    request: KellyParametersUpdate
  ): Promise<any> => {
    const response = await axios.post<ApiResponse<any>>(
      '/api/position-sizing/kelly/parameters',
      request
    );

    if (response.data.status !== 'success') {
      throw new Error(
        response.data.message || 'Failed to update Kelly parameters'
      );
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Get risk allocation summary
   */
  getRiskAllocationSummary: async (): Promise<RiskAllocationSummary> => {
    const response = await axios.get<ApiResponse<RiskAllocationSummary>>(
      '/api/position-sizing/risk/allocation'
    );

    if (response.data.status !== 'success') {
      throw new Error(
        response.data.message || 'Failed to fetch risk allocation'
      );
    }

    return response.data.data;
  },

  /**
   * Validate calculations against Excel
   */
  validateExcelCompatibility: async (
    request: ExcelValidationRequest
  ): Promise<ValidationResult> => {
    const response = await axios.post<ApiResponse<ValidationResult>>(
      '/api/position-sizing/validate/excel',
      request
    );

    return response.data.data;
  },

  /**
   * Export position sizing data for Excel migration
   */
  exportPositionSizingData: async (): Promise<{
    exportPath: string;
    exportTimestamp: string;
  }> => {
    const response = await axios.post<
      ApiResponse<{ exportPath: string; exportTimestamp: string }>
    >('/api/position-sizing/export');

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Export failed');
    }

    return response.data.data;
  },

  /**
   * Synchronize with strategy analysis results
   */
  syncWithStrategyResults: async (strategyResults: any): Promise<any> => {
    const response = await axios.post<ApiResponse<any>>(
      '/api/position-sizing/sync/strategy-results',
      strategyResults
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Sync failed');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Check position sizing service health
   */
  checkHealth: async (): Promise<any> => {
    const response = await axios.get<ApiResponse<any>>(
      '/api/position-sizing/health'
    );

    return response.data;
  },

  /**
   * Clear dashboard cache (useful for forced refresh)
   */
  clearCache: (): void => {
    cache.dashboard = null;
    cache.lastFetch = 0;
  },
};
