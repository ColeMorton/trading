import { useState, useEffect, useCallback } from 'react';
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
import { positionSizingApi } from '../services/positionSizingApi';

/**
 * Main position sizing dashboard hook
 */
export const usePositionSizingDashboard = (
  autoRefresh = true,
  refreshInterval = 30000
) => {
  const [dashboard, setDashboard] = useState<PositionSizingDashboard | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchDashboard = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) {
        setIsLoading(true);
      }
      setError(null);

      const data = await positionSizingApi.getDashboard();
      setDashboard(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch dashboard'
      );
      console.error('Dashboard fetch error:', err);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  }, []);

  const refresh = useCallback(() => {
    positionSizingApi.clearCache();
    fetchDashboard(true);
  }, [fetchDashboard]);

  // Initial load
  useEffect(() => {
    fetchDashboard(true);
  }, [fetchDashboard]);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchDashboard(false); // Silent refresh
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, fetchDashboard]);

  return {
    dashboard,
    isLoading,
    error,
    lastUpdated,
    refresh,
    fetchDashboard,
  };
};

/**
 * Position sizing calculation hook
 */
export const usePositionSizeCalculation = () => {
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculatePositionSize = useCallback(
    async (
      request: PositionSizingRequest
    ): Promise<PositionSizingResponse | null> => {
      try {
        setIsCalculating(true);
        setError(null);

        const response = await positionSizingApi.calculatePositionSize(request);
        return response;
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Position size calculation failed';
        setError(errorMessage);
        console.error('Position size calculation error:', err);
        return null;
      } finally {
        setIsCalculating(false);
      }
    },
    []
  );

  return {
    calculatePositionSize,
    isCalculating,
    error,
  };
};

/**
 * Active positions management hook
 */
export const useActivePositions = (
  portfolioType?: 'Risk_On' | 'Investment'
) => {
  const [positions, setPositions] = useState<TradingPosition[]>([]);
  const [summary, setSummary] = useState({
    totalCount: 0,
    totalValue: 0,
    totalRisk: 0,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPositions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await positionSizingApi.getActivePositions(portfolioType);
      setPositions(data.positions);
      setSummary({
        totalCount: data.totalCount,
        totalValue: data.totalValue,
        totalRisk: data.totalRisk,
      });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch positions'
      );
      console.error('Positions fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [portfolioType]);

  useEffect(() => {
    fetchPositions();
  }, [fetchPositions]);

  return {
    positions,
    summary,
    isLoading,
    error,
    refetch: fetchPositions,
  };
};

/**
 * Position analysis hook for specific symbols
 */
export const usePositionAnalysis = (symbol?: string) => {
  const [analysis, setAnalysis] = useState<PositionAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async (symbolToFetch: string) => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await positionSizingApi.getPositionAnalysis(symbolToFetch);
      setAnalysis(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch position analysis'
      );
      console.error('Position analysis fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (symbol) {
      fetchAnalysis(symbol);
    }
  }, [symbol, fetchAnalysis]);

  return {
    analysis,
    isLoading,
    error,
    fetchAnalysis,
  };
};

/**
 * Position management hook (add/update positions)
 */
export const usePositionManagement = () => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addPosition = useCallback(
    async (request: PositionEntryRequest): Promise<boolean> => {
      try {
        setIsUpdating(true);
        setError(null);

        await positionSizingApi.addPositionEntry(request);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to add position';
        setError(errorMessage);
        console.error('Add position error:', err);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  const updatePosition = useCallback(
    async (
      symbol: string,
      updates: PositionUpdateRequest
    ): Promise<boolean> => {
      try {
        setIsUpdating(true);
        setError(null);

        await positionSizingApi.updatePositionMetrics(symbol, updates);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to update position';
        setError(errorMessage);
        console.error('Update position error:', err);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  return {
    addPosition,
    updatePosition,
    isUpdating,
    error,
  };
};

/**
 * Account management hook
 */
export const useAccountManagement = () => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateAccountBalance = useCallback(
    async (request: AccountBalanceUpdate): Promise<boolean> => {
      try {
        setIsUpdating(true);
        setError(null);

        await positionSizingApi.updateAccountBalance(request);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Failed to update account balance';
        setError(errorMessage);
        console.error('Update account balance error:', err);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  const updateKellyParameters = useCallback(
    async (request: KellyParametersUpdate): Promise<boolean> => {
      try {
        setIsUpdating(true);
        setError(null);

        await positionSizingApi.updateKellyParameters(request);
        return true;
      } catch (err) {
        const errorMessage =
          err instanceof Error
            ? err.message
            : 'Failed to update Kelly parameters';
        setError(errorMessage);
        console.error('Update Kelly parameters error:', err);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  return {
    updateAccountBalance,
    updateKellyParameters,
    isUpdating,
    error,
  };
};

/**
 * Risk allocation hook
 */
export const useRiskAllocation = () => {
  const [riskSummary, setRiskSummary] = useState<RiskAllocationSummary | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRiskAllocation = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const data = await positionSizingApi.getRiskAllocationSummary();
      setRiskSummary(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to fetch risk allocation'
      );
      console.error('Risk allocation fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRiskAllocation();
  }, [fetchRiskAllocation]);

  return {
    riskSummary,
    isLoading,
    error,
    refetch: fetchRiskAllocation,
  };
};

/**
 * Excel validation hook
 */
export const useExcelValidation = () => {
  const [isValidating, setIsValidating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const validateAgainstExcel = useCallback(
    async (
      request: ExcelValidationRequest
    ): Promise<ValidationResult | null> => {
      try {
        setIsValidating(true);
        setError(null);

        const result =
          await positionSizingApi.validateExcelCompatibility(request);
        return result;
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Excel validation failed';
        setError(errorMessage);
        console.error('Excel validation error:', err);
        return null;
      } finally {
        setIsValidating(false);
      }
    },
    []
  );

  return {
    validateAgainstExcel,
    isValidating,
    error,
  };
};

/**
 * System health monitoring hook
 */
export const usePositionSizingHealth = (checkInterval = 60000) => {
  const [health, setHealth] = useState<any>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      setIsChecking(true);
      setError(null);

      const result = await positionSizingApi.checkHealth();
      setHealth(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Health check failed');
      console.error('Health check error:', err);
    } finally {
      setIsChecking(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, checkInterval);
    return () => clearInterval(interval);
  }, [checkHealth, checkInterval]);

  return {
    health,
    isChecking,
    error,
    checkHealth,
  };
};
