export interface CSVFile {
  path: string;
  name: string;
}

export interface CSVData {
  data: Record<string, unknown>[];
  columns: string[];
}

export interface UpdateStatus {
  status: 'accepted' | 'running' | 'completed' | 'failed';
  execution_id?: string;
  progress?: number;
  error?: string;
  message?: string;
}

// Parameter Testing interfaces
export interface AnalysisConfiguration {
  TICKER: string | string[];
  WINDOWS: number;
  DIRECTION: 'Long' | 'Short';
  STRATEGY_TYPES: ('SMA' | 'EMA' | 'MACD')[];
  USE_HOURLY: boolean;
  USE_YEARS: boolean;
  YEARS: number;
  USE_SYNTHETIC: boolean;
  USE_CURRENT: boolean;
  USE_SCANNER: boolean;
  REFRESH: boolean;
  MINIMUMS: {
    WIN_RATE: number;
    TRADES: number;
    EXPECTANCY_PER_TRADE: number;
    PROFIT_FACTOR: number;
    SORTINO_RATIO: number;
  };
  SORT_BY: string;
  SORT_ASC: boolean;
  USE_GBM: boolean;
  async_execution: boolean;
  // MACD-specific parameters
  SHORT_WINDOW_START?: number;
  SHORT_WINDOW_END?: number;
  LONG_WINDOW_START?: number;
  LONG_WINDOW_END?: number;
  SIGNAL_WINDOW_START?: number;
  SIGNAL_WINDOW_END?: number;
  STEP?: number;
}

export interface AnalysisResult {
  ticker: string;
  strategy_type: string;
  short_window: number;
  long_window: number;
  signal_window: number;
  direction: string;
  timeframe: string;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  expectancy_per_trade: number;
  sortino_ratio: number;
  max_drawdown: number;
  total_return: number;
  score?: number;
  avg_trade_duration?: string;
  beats_bnh?: number;
  metric_type?: string;
  [key: string]: unknown;
}

export interface MACrossResponse {
  status: 'completed' | 'error' | 'running';
  results?: AnalysisResult[];
  execution_id?: string;
  progress?: number;
  error?: string;
  message?: string;
}

export interface ExecutionStatus {
  status: 'running' | 'completed' | 'error';
  progress: number;
  message?: string;
  error?: string;
  results?: AnalysisResult[];
}

export interface ParameterTestingState {
  configuration: AnalysisConfiguration;
  results: AnalysisResult[];
  isAnalyzing: boolean;
  error: string | null;
  progress: number;
  executionId: string | null;
}

// Position Sizing interfaces
export interface PortfolioRiskMetrics {
  netWorth: number;
  cvarTrading: number;
  cvarInvestment: number;
  riskAmount: number;
  kellyMetrics: KellyMetrics;
  totalStrategies: number;
}

export interface KellyMetrics {
  kellyCriterion: number;
  numPrimary: number;
  numOutliers: number;
  confidenceMetrics?: Record<string, number>;
}

export interface AccountBalances {
  ibkr: number;
  bybit: number;
  cash: number;
  total: number;
  accountBreakdown: Record<string, number>;
  lastUpdated: string;
}

export interface TradingPosition {
  symbol: string;
  positionValue: number;
  currentPosition: number;
  maxDrawdown?: number;
  riskAmount?: number;
  accountType: string;
  entryDate?: string;
  stopLossPrice?: number;
  // Enhanced fields for manual entry
  manualPositionSize?: number;
  manualEntryDate?: string;
  currentStatus?: 'Active' | 'Closed' | 'Pending';
  stopStatus?: 'Risk' | 'Protected';
  portfolioType?: 'Risk_On' | 'Investment' | 'Protected';
}

export interface SignalAnalysis {
  symbol: string;
  signalType: 'entry' | 'exit';
  price: number;
  confidence: 'primary' | 'outlier';
  recommendedSize: number;
  positionValue: number;
  riskAmount: number;
  timestamp: string;
}

export interface InvestmentHolding {
  symbol: string;
  shares: number;
  averagePrice: number;
  currentValue: number;
  unrealizedPnl: number;
  allocationPercentage: number;
}

export interface RiskBucket {
  riskLevel: number;
  allocationAmount: number;
  percentage: number;
  status: 'active' | 'future';
}

export interface PositionSizingDashboard {
  portfolioRisk: PortfolioRiskMetrics;
  activePositions: TradingPosition[];
  incomingSignals: SignalAnalysis[];
  strategicHoldings: InvestmentHolding[];
  accountBalances: AccountBalances;
  riskAllocation: RiskAllocation; // Updated from riskAllocationBuckets
  kellyInput?: KellyInput; // Manual Kelly Criterion data
  lastUpdated: string;
}

export interface PositionSizingRequest {
  symbol: string;
  signalType: 'entry' | 'exit';
  portfolioType: 'Risk_On' | 'Investment';
  entryPrice?: number;
  stopLossDistance?: number;
  confidenceLevel?: 'primary' | 'outlier';
}

export interface PositionSizingResponse {
  symbol: string;
  recommendedPositionSize: number;
  positionValue: number;
  riskAmount: number;
  kellyPercentage: number;
  allocationPercentage: number;
  stopLossPrice?: number;
  confidenceMetrics: Record<string, number>;
  riskBucketAllocation: number;
  accountAllocation: Record<string, number>;
  calculationTimestamp: string;
}

export interface PositionEntryRequest {
  symbol: string;
  positionValue: number;
  stopLossDistance?: number;
  entryPrice?: number;
  portfolioType: 'Risk_On' | 'Investment';
}

export interface PositionUpdateRequest {
  positionValue?: number;
  stopLossDistance?: number;
  currentPosition?: number;
  entryPrice?: number;
  shares?: number;
  currentValue?: number;
}

export interface AccountBalanceUpdate {
  account_type: 'IBKR' | 'Bybit' | 'Cash';
  balance: number;
}

export interface KellyParametersUpdate {
  numPrimary: number;
  numOutliers: number;
  kellyCriterion: number;
}

// Enhanced interfaces for manual data entry
export interface KellyInput {
  kellyCriterion: number;
  numPrimary: number;
  numOutliers: number;
  lastUpdated: Date;
  source: 'Trading Journal' | 'Manual' | 'Calculated';
  notes?: string;
}

export interface StrategyRow {
  // Core strategy data from CSV
  ticker: string;
  strategyType: string;
  shortWindow: number;
  longWindow: number;
  signalWindow?: number;
  signalEntry: boolean;
  signalExit: boolean;
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  expectancyPerTrade: number;
  sortinoRatio: number;
  allocation?: number;
  stopLoss?: number;

  // Enhanced manual entry fields
  manualPositionSize?: number;
  manualEntryDate?: string;
  currentStatus?: 'Active' | 'Closed' | 'Pending';
  stopStatus?: 'Risk' | 'Protected';
  notes?: string;
}

export type PortfolioType = 'Risk_On' | 'Protected' | 'Investment';

export interface RiskAllocation {
  targetCVaR: 0.118; // Fixed 11.8% target
  currentCVaR: number;
  utilization: number; // currentCVaR / targetCVaR
  availableRisk: number; // 0.118 - currentCVaR
  riskAmount: number; // Net worth × current CVaR
}

export interface PositionUpdateRequest {
  positionValue?: number;
  stopLossDistance?: number;
  currentPosition?: number;
  entryPrice?: number;
  shares?: number;
  currentValue?: number;
  // Enhanced manual entry fields
  manualPositionSize?: number;
  manualEntryDate?: string;
  currentStatus?: 'Active' | 'Closed' | 'Pending';
  stopStatus?: 'Risk' | 'Protected';
  portfolioTransition?: 'Risk_to_Protected' | 'Protected_to_Investment';
}

export interface ExcelValidationRequest {
  netWorth?: number;
  tradingCvar?: number;
  investmentCvar?: number;
  riskAmount?: number;
  totalStrategies?: number;
}

export interface ValidationResult {
  validated: boolean;
  discrepancies: Array<{
    field: string;
    expected: number;
    actual: number;
    difference: number;
  }>;
  validations: Array<{
    field: string;
    status: 'passed';
    value: number;
  }>;
}

export interface RiskAllocationSummary {
  netWorth: number;
  riskAllocationLimit: number;
  currentRiskExposure: number;
  riskUtilizationPercentage: number;
  availableRiskCapacity: number;
  riskBuckets: RiskBucket[];
  positionCount: number;
}

export interface PositionAnalysis {
  symbol: string;
  positionTracking: {
    positionValue: number;
    currentPosition: number;
    accountType?: string;
    entryDate?: string;
  };
  riskMetrics: {
    stopLossDistance?: number;
    maxRiskAmount?: number;
    stopLossPrice?: number;
    riskPercentage?: number;
  };
  portfolioAllocation: {
    riskOn: {
      shares: number;
      value: number;
      allocation: number;
    };
    investment: {
      shares: number;
      value: number;
      allocation: number;
    };
  };
  totalExposure: {
    totalValue: number;
    percentageOfPortfolio: number;
  };
}
