import { getApolloClient } from '../../apollo/client';
import { 
  ExecuteMaCrossAnalysisDocument,
  GetAnalysisStatusDocument,
  MaCrossAnalysisInput,
  TimeframeType,
  StrategyType,
  DirectionType
} from '../../graphql/generated';
import {
  AnalysisConfiguration,
  AnalysisResult,
  MACrossRequest,
  MACrossSyncResponse,
  MACrossAsyncResponse,
  ExecutionStatusResponse,
  PortfolioMetrics,
  ConfigPreset
} from '../maCrossApi';

/**
 * Convert frontend configuration to GraphQL input format
 */
const configToGraphQLInput = (config: AnalysisConfiguration): MaCrossAnalysisInput => {
  // Map strategy types
  const strategyTypes: StrategyType[] = config.STRATEGY_TYPES.map(type => {
    switch (type) {
      case 'SMA': return StrategyType.MaCross;
      case 'EMA': return StrategyType.MaCross;
      default: return StrategyType.MaCross;
    }
  });

  // Map direction
  const direction = config.DIRECTION === 'Long' ? DirectionType.Long : 
                   config.DIRECTION === 'Short' ? DirectionType.Short : 
                   DirectionType.Both;

  // Map timeframe
  const timeframe = config.USE_HOURLY ? TimeframeType.OneHour : TimeframeType.OneDay;

  return {
    ticker: Array.isArray(config.TICKER) ? config.TICKER : [config.TICKER],
    windows: config.WINDOWS,
    direction,
    strategyTypes,
    timeframe,
    useYears: config.USE_YEARS,
    years: config.YEARS,
    useSynthetic: config.USE_SYNTHETIC,
    ticker1: config.ticker_1,
    ticker2: config.ticker_2,
    refresh: config.REFRESH,
    minimums: config.MINIMUMS ? {
      trades: config.MINIMUMS.TRADES,
      winRate: config.MINIMUMS.WIN_RATE ? config.MINIMUMS.WIN_RATE / 100 : undefined,
      expectancyPerTrade: config.MINIMUMS.EXPECTANCY_PER_TRADE,
      profitFactor: config.MINIMUMS.PROFIT_FACTOR,
      sortinoRatio: config.MINIMUMS.SORTINO_RATIO
    } : undefined,
    sortBy: config.SORT_BY,
    sortAsc: config.SORT_ASC,
    useGbm: config.USE_GBM,
    useCurrent: config.USE_CURRENT,
    useScanner: config.USE_SCANNER,
    asyncExecution: config.async_execution
  };
};

/**
 * Convert GraphQL portfolio response to frontend format
 */
const graphQLPortfolioToMetrics = (portfolio: any): PortfolioMetrics => {
  return {
    ticker: portfolio.ticker,
    strategy_type: portfolio.strategyType,
    short_window: portfolio.shortWindow,
    long_window: portfolio.longWindow,
    signal_window: portfolio.signalWindow,
    direction: portfolio.direction,
    timeframe: portfolio.timeframe,
    total_return: portfolio.performance.totalReturn,
    annual_return: portfolio.performance.annualReturn,
    sharpe_ratio: portfolio.performance.sharpeRatio,
    sortino_ratio: portfolio.performance.sortinoRatio,
    max_drawdown: portfolio.performance.maxDrawdown,
    total_trades: portfolio.performance.totalTrades,
    winning_trades: portfolio.performance.winningTrades,
    losing_trades: portfolio.performance.losingTrades,
    win_rate: portfolio.performance.winRate,
    profit_factor: portfolio.performance.profitFactor,
    expectancy: portfolio.performance.expectancy,
    expectancy_per_trade: portfolio.performance.expectancyPerTrade,
    score: portfolio.performance.score,
    beats_bnh: portfolio.performance.beatsBnh,
    has_open_trade: portfolio.hasOpenTrade,
    has_signal_entry: portfolio.hasSignalEntry
  };
};

/**
 * GraphQL MA Cross API adapter
 */
export const graphqlMaCrossApi = {
  /**
   * Get configuration presets
   */
  getConfigPresets: async (): Promise<ConfigPreset[]> => {
    // For now, return hardcoded presets until GraphQL endpoint is available
    return [
      {
        name: 'Default',
        config: {
          WINDOWS: 50,
          DIRECTION: 'Long',
          STRATEGY_TYPES: ['SMA', 'EMA'],
          USE_HOURLY: false,
          USE_YEARS: false,
          YEARS: 2
        }
      },
      {
        name: 'Crypto Daily',
        config: {
          TICKER: ['BTC-USD', 'ETH-USD', 'SOL-USD'],
          WINDOWS: 100,
          DIRECTION: 'Long',
          STRATEGY_TYPES: ['EMA'],
          USE_HOURLY: false
        }
      },
      {
        name: 'Stocks Hourly',
        config: {
          TICKER: ['SPY', 'QQQ'],
          WINDOWS: 50,
          DIRECTION: 'Both',
          STRATEGY_TYPES: ['SMA', 'EMA'],
          USE_HOURLY: true
        }
      }
    ];
  },

  /**
   * Execute MA Cross analysis
   */
  analyze: async (config: AnalysisConfiguration): Promise<MACrossSyncResponse | MACrossAsyncResponse> => {
    try {
      const client = getApolloClient();
      const input = configToGraphQLInput(config);

      // Execute GraphQL mutation
      const { data } = await client.mutate({
        mutation: ExecuteMaCrossAnalysisDocument,
        variables: { input }
      });

      const result = data.executeMaCrossAnalysis;

      // Handle async response
      if ('executionId' in result) {
        return {
          status: 'accepted',
          execution_id: result.executionId,
          message: result.message,
          status_url: result.statusUrl,
          stream_url: result.streamUrl,
          timestamp: result.timestamp,
          estimated_time: result.estimatedTime
        };
      }

      // Handle sync response
      return {
        status: result.status as 'success' | 'error',
        request_id: result.requestId,
        timestamp: result.timestamp,
        ticker: result.ticker,
        strategy_types: result.strategyTypes,
        portfolios: result.portfolios.map(graphQLPortfolioToMetrics),
        portfolio_exports: result.portfolioExports || {},
        total_portfolios_analyzed: result.totalPortfoliosAnalyzed,
        total_portfolios_filtered: result.totalPortfoliosFiltered,
        execution_time: result.executionTime
      };
    } catch (error) {
      console.error('GraphQL error in MA Cross analysis:', error);
      throw error;
    }
  },

  /**
   * Get analysis status for async execution
   */
  getStatus: async (executionId: string): Promise<ExecutionStatusResponse> => {
    try {
      const client = getApolloClient();

      const { data } = await client.query({
        query: GetAnalysisStatusDocument,
        variables: { executionId },
        fetchPolicy: 'network-only' // Always fetch fresh status
      });

      const status = data.analysisStatus;

      // Map GraphQL response to expected format
      const response: ExecutionStatusResponse = {
        execution_id: status.executionId,
        status: status.status as any,
        progress: status.progress,
        message: status.message,
        timestamp: status.timestamp,
        started_at: status.startedAt,
        completed_at: status.completedAt,
        execution_time: status.executionTime,
        estimated_time_remaining: status.estimatedTimeRemaining,
        error: status.error
      };

      // If completed, include results
      if (status.result) {
        response.result = {
          status: status.result.status as 'success' | 'error',
          request_id: status.result.requestId,
          timestamp: status.result.timestamp,
          ticker: status.result.ticker,
          strategy_types: status.result.strategyTypes,
          portfolios: status.result.portfolios.map(graphQLPortfolioToMetrics),
          portfolio_exports: {},
          total_portfolios_analyzed: status.result.totalPortfoliosAnalyzed,
          total_portfolios_filtered: status.result.totalPortfoliosFiltered,
          execution_time: status.result.executionTime
        };
      }

      return response;
    } catch (error) {
      console.error('GraphQL error getting analysis status:', error);
      throw error;
    }
  },

  /**
   * Convert sync response to results array
   */
  responseToResults: (response: MACrossSyncResponse): AnalysisResult[] => {
    return response.portfolios.map(portfolio => ({
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
      expectancy_per_trade: portfolio.expectancy_per_trade || portfolio.expectancy,
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
      has_signal_entry: portfolio.has_signal_entry
    }));
  },

  /**
   * Clear the cache
   */
  clearCache: () => {
    const client = getApolloClient();
    client.cache.reset();
  }
};