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
  KellyInput,
  RiskAllocation,
  StrategyRow,
} from '../types';

// API response wrapper interface
interface ApiResponse<T> {
  status: 'success' | 'error' | 'warning';
  data: T;
  message?: string;
  timestamp: string;
}

// Enhanced caching for dashboard data with TTL
const cache = {
  dashboard: null as PositionSizingDashboard | null,
  kellyInput: null as KellyInput | null,
  lastFetch: 0,
  kellyLastFetch: 0,
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

      const response = await axios.get<ApiResponse<any>>(
        '/api/position-sizing/dashboard'
      );

      if (response.data.status !== 'success') {
        throw new Error(
          response.data.message || 'Failed to fetch dashboard data'
        );
      }

      // Transform backend response to frontend expected format
      const backendData = response.data.data;
      const dashboard: PositionSizingDashboard = {
        portfolioRisk: {
          netWorth: backendData.net_worth || 0,
          cvarTrading: backendData.portfolio_risk_metrics?.trading_cvar || 0,
          cvarInvestment:
            backendData.portfolio_risk_metrics?.investment_cvar || 0,
          riskAmount: backendData.portfolio_risk_metrics?.risk_amount || 0,
          kellyMetrics: {
            numPrimary: backendData.portfolio_risk_metrics?.num_primary || 0,
            numOutliers: backendData.portfolio_risk_metrics?.num_outliers || 0,
            kellyCriterion:
              backendData.portfolio_risk_metrics?.kelly_criterion || 0,
            confidenceMetrics:
              backendData.portfolio_risk_metrics?.confidence_metrics || {},
          },
          totalStrategies:
            backendData.portfolio_risk_metrics?.total_strategies || 0,
        },
        activePositions: backendData.active_positions || [],
        incomingSignals: backendData.incoming_signals || [],
        strategicHoldings: backendData.strategic_holdings || [],
        accountBalances: {
          ibkr: backendData.account_balances?.ibkr || 0,
          bybit: backendData.account_balances?.bybit || 0,
          cash: backendData.account_balances?.cash || 0,
          total: backendData.net_worth || 0,
          accountBreakdown: backendData.account_balances || {},
        },
        riskAllocation: {
          targetCVaR: 0.118, // Fixed 11.8% target
          currentCVaR: backendData.portfolio_risk_metrics?.current_cvar || 0,
          utilization:
            (backendData.portfolio_risk_metrics?.current_cvar || 0) / 0.118,
          availableRisk:
            0.118 - (backendData.portfolio_risk_metrics?.current_cvar || 0),
          riskAmount:
            (backendData.net_worth || 0) *
            (backendData.portfolio_risk_metrics?.current_cvar || 0),
        },
        kellyInput: cache.kellyInput, // Include cached Kelly input
        lastUpdated: backendData.last_updated || new Date().toISOString(),
      };

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
    cache.kellyInput = null;
    cache.lastFetch = 0;
    cache.kellyLastFetch = 0;
  },

  // ===== ENHANCED API METHODS FOR MANUAL DATA ENTRY =====

  /**
   * Get current Kelly Criterion input data
   */
  getKellyInput: async (): Promise<KellyInput | null> => {
    try {
      // Check cache first
      const now = Date.now();
      if (cache.kellyInput && now - cache.kellyLastFetch < cache.TTL) {
        return cache.kellyInput;
      }

      const response = await axios.get<ApiResponse<KellyInput>>(
        '/api/position-sizing/kelly'
      );

      if (response.data.status !== 'success') {
        throw new Error(response.data.message || 'Failed to fetch Kelly input');
      }

      // Update cache
      cache.kellyInput = response.data.data;
      cache.kellyLastFetch = now;

      return response.data.data;
    } catch (error) {
      // If error, return cached data or null
      if (cache.kellyInput) {
        console.warn('Using cached Kelly input due to error:', error);
        return cache.kellyInput;
      }
      return null;
    }
  },

  /**
   * Update Kelly Criterion value (from trading journal)
   */
  updateKellyInput: async (
    kellyInput: Omit<KellyInput, 'lastUpdated'>
  ): Promise<KellyInput> => {
    const payload = {
      ...kellyInput,
      lastUpdated: new Date().toISOString(),
    };

    const response = await axios.post<ApiResponse<KellyInput>>(
      '/api/position-sizing/kelly',
      payload
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to update Kelly input');
    }

    // Clear related caches
    cache.kellyInput = response.data.data;
    cache.kellyLastFetch = Date.now();
    cache.dashboard = null; // Force dashboard refresh

    return response.data.data;
  },

  /**
   * Update individual position with enhanced fields
   */
  updatePositionEnhanced: async (
    symbol: string,
    updates: PositionUpdateRequest
  ): Promise<TradingPosition> => {
    const response = await axios.put<ApiResponse<TradingPosition>>(
      `/api/position-sizing/positions/${symbol.toUpperCase()}/enhanced`,
      updates
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to update position');
    }

    // Clear dashboard cache to reflect changes
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Transition position between portfolios (Risk → Protected)
   */
  transitionPosition: async (
    symbol: string,
    transition: 'Risk_to_Protected' | 'Protected_to_Investment'
  ): Promise<{
    success: boolean;
    fromPortfolio: string;
    toPortfolio: string;
    position: TradingPosition;
  }> => {
    const response = await axios.post<
      ApiResponse<{
        success: boolean;
        fromPortfolio: string;
        toPortfolio: string;
        position: TradingPosition;
      }>
    >(`/api/position-sizing/positions/${symbol.toUpperCase()}/transition`, {
      transition,
    });

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to transition position');
    }

    // Clear dashboard cache to reflect portfolio changes
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Add new position with manual entry data
   */
  addPositionEnhanced: async (
    position: PositionEntryRequest & {
      manualPositionSize?: number;
      manualEntryDate?: string;
      currentStatus?: 'Active' | 'Closed' | 'Pending';
      stopStatus?: 'Risk' | 'Protected';
      notes?: string;
    }
  ): Promise<TradingPosition> => {
    const response = await axios.post<ApiResponse<TradingPosition>>(
      '/api/position-sizing/positions/enhanced',
      position
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Failed to add position');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Bulk update positions from CSV data
   */
  bulkUpdatePositions: async (
    portfolioType: 'Risk_On' | 'Investment' | 'Protected',
    strategies: StrategyRow[]
  ): Promise<{
    success: boolean;
    updated: number;
    errors: Array<{ symbol: string; error: string }>;
  }> => {
    const response = await axios.post<
      ApiResponse<{
        success: boolean;
        updated: number;
        errors: Array<{ symbol: string; error: string }>;
      }>
    >(`/api/position-sizing/portfolios/${portfolioType}/bulk-update`, {
      strategies,
    });

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Bulk update failed');
    }

    // Clear dashboard cache
    cache.dashboard = null;

    return response.data.data;
  },

  /**
   * Export enhanced CSV for a portfolio
   */
  exportEnhancedCSV: async (
    portfolioType: 'Risk_On' | 'Investment' | 'Protected'
  ): Promise<{
    csvContent: string;
    filename: string;
    rowCount: number;
  }> => {
    const response = await axios.get<
      ApiResponse<{
        csvContent: string;
        filename: string;
        rowCount: number;
      }>
    >(`/api/position-sizing/portfolios/${portfolioType}/export-enhanced`);

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'CSV export failed');
    }

    return response.data.data;
  },

  /**
   * Import enhanced CSV data
   */
  importEnhancedCSV: async (
    portfolioType: 'Risk_On' | 'Investment' | 'Protected',
    csvContent: string,
    options: {
      validateOnly?: boolean;
      backupOriginal?: boolean;
    } = {}
  ): Promise<{
    success: boolean;
    imported: number;
    warnings: string[];
    backupPath?: string;
  }> => {
    const response = await axios.post<
      ApiResponse<{
        success: boolean;
        imported: number;
        warnings: string[];
        backupPath?: string;
      }>
    >(`/api/position-sizing/portfolios/${portfolioType}/import-enhanced`, {
      csvContent,
      options,
    });

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'CSV import failed');
    }

    // Clear dashboard cache after successful import
    if (!options.validateOnly) {
      cache.dashboard = null;
    }

    return response.data.data;
  },

  /**
   * Get current risk allocation with real-time calculations
   */
  getRiskAllocation: async (): Promise<RiskAllocation> => {
    const response = await axios.get<ApiResponse<RiskAllocation>>(
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
   * Validate position data before updates
   */
  validatePosition: async (
    symbol: string,
    positionData: Partial<TradingPosition>
  ): Promise<{
    valid: boolean;
    warnings: string[];
    suggestions: string[];
  }> => {
    const response = await axios.post<
      ApiResponse<{
        valid: boolean;
        warnings: string[];
        suggestions: string[];
      }>
    >(
      `/api/position-sizing/positions/${symbol.toUpperCase()}/validate`,
      positionData
    );

    if (response.data.status !== 'success') {
      throw new Error(response.data.message || 'Position validation failed');
    }

    return response.data.data;
  },
};
