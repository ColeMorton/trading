export interface CSVFile {
  path: string;
  name: string;
}

export interface CSVData {
  data: Record<string, any>[];
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
  STRATEGY_TYPES: ('SMA' | 'EMA')[];
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
  metric_type?: string;
  [key: string]: any;
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
