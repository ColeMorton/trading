import { gql } from '@apollo/client';
import * as Apollo from '@apollo/client';
export type Maybe<T> = T | null;
export type InputMaybe<T> = Maybe<T>;
export type Exact<T extends { [key: string]: unknown }> = { [K in keyof T]: T[K] };
export type MakeOptional<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]?: Maybe<T[SubKey]> };
export type MakeMaybe<T, K extends keyof T> = Omit<T, K> & { [SubKey in K]: Maybe<T[SubKey]> };
export type MakeEmpty<T extends { [key: string]: unknown }, K extends keyof T> = { [_ in K]?: never };
export type Incremental<T> = T | { [P in keyof T]?: P extends ' $fragmentName' | '__typename' ? T[P] : never };
const defaultOptions = {} as const;
/** All built-in and custom scalars, mapped to their actual values */
export type Scalars = {
  ID: { input: string; output: string; }
  String: { input: string; output: string; }
  Boolean: { input: boolean; output: boolean; }
  Int: { input: number; output: number; }
  Float: { input: number; output: number; }
  DateTime: { input: string; output: string; }
  JSON: { input: Record<string, any>; output: Record<string, any>; }
};

export type AnalysisResult = {
  __typename?: 'AnalysisResult';
  hasOpenTrade: Scalars['Boolean']['output'];
  hasSignalEntry: Scalars['Boolean']['output'];
  longWindow: Scalars['Int']['output'];
  performance: PerformanceMetrics;
  shortWindow: Scalars['Int']['output'];
  strategyType: Scalars['String']['output'];
  ticker: Scalars['String']['output'];
};

export type AnalysisStatus = {
  __typename?: 'AnalysisStatus';
  completedAt?: Maybe<Scalars['DateTime']['output']>;
  error?: Maybe<Scalars['String']['output']>;
  executionId: Scalars['ID']['output'];
  executionTime?: Maybe<Scalars['Float']['output']>;
  progress: Scalars['String']['output'];
  results?: Maybe<Array<AnalysisResult>>;
  startedAt: Scalars['DateTime']['output'];
  status: Scalars['String']['output'];
};

export enum AssetClass {
  Bond = 'BOND',
  Commodity = 'COMMODITY',
  Crypto = 'CRYPTO',
  Etf = 'ETF',
  Forex = 'FOREX',
  Index = 'INDEX',
  Stock = 'STOCK'
}

export type AsyncAnalysisResponse = {
  __typename?: 'AsyncAnalysisResponse';
  estimatedTime?: Maybe<Scalars['Float']['output']>;
  executionId: Scalars['ID']['output'];
  message: Scalars['String']['output'];
  status: Scalars['String']['output'];
  statusUrl: Scalars['String']['output'];
  streamUrl: Scalars['String']['output'];
  timestamp: Scalars['DateTime']['output'];
};

export type BacktestResult = {
  __typename?: 'BacktestResult';
  alpha?: Maybe<Scalars['Float']['output']>;
  annualReturnPct?: Maybe<Scalars['Float']['output']>;
  avgLosingTrade?: Maybe<Scalars['Float']['output']>;
  avgTradeDuration?: Maybe<Scalars['Float']['output']>;
  avgWinningTrade?: Maybe<Scalars['Float']['output']>;
  benchmarkReturnPct?: Maybe<Scalars['Float']['output']>;
  beta?: Maybe<Scalars['Float']['output']>;
  calmarRatio?: Maybe<Scalars['Float']['output']>;
  conditionalValueAtRisk?: Maybe<Scalars['Float']['output']>;
  createdAt: Scalars['DateTime']['output'];
  endDate: Scalars['DateTime']['output'];
  expectancyPerTrade?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  informationRatio?: Maybe<Scalars['Float']['output']>;
  losingTrades?: Maybe<Scalars['Int']['output']>;
  maxDrawdownPct?: Maybe<Scalars['Float']['output']>;
  openTrades?: Maybe<Scalars['Int']['output']>;
  outperformancePct?: Maybe<Scalars['Float']['output']>;
  profitFactor?: Maybe<Scalars['Float']['output']>;
  rawMetrics?: Maybe<Scalars['JSON']['output']>;
  runDate: Scalars['DateTime']['output'];
  score?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  startDate: Scalars['DateTime']['output'];
  strategyConfigId: Scalars['String']['output'];
  totalReturnPct: Scalars['Float']['output'];
  totalTrades: Scalars['Int']['output'];
  trackingError?: Maybe<Scalars['Float']['output']>;
  tradesPerDay?: Maybe<Scalars['Float']['output']>;
  tradesPerMonth?: Maybe<Scalars['Float']['output']>;
  valueAtRisk95?: Maybe<Scalars['Float']['output']>;
  winRatePct?: Maybe<Scalars['Float']['output']>;
  winningTrades?: Maybe<Scalars['Int']['output']>;
};

export enum DirectionType {
  Both = 'BOTH',
  Long = 'LONG',
  Short = 'SHORT'
}

export type MaCrossAnalysisInput = {
  asyncExecution?: Scalars['Boolean']['input'];
  direction?: DirectionType;
  minCriteria?: InputMaybe<PerformanceCriteria>;
  refresh?: Scalars['Boolean']['input'];
  sortAsc?: Scalars['Boolean']['input'];
  sortBy?: Scalars['String']['input'];
  strategyTypes?: Array<StrategyType>;
  ticker1?: InputMaybe<Scalars['String']['input']>;
  ticker2?: InputMaybe<Scalars['String']['input']>;
  tickers: Array<Scalars['String']['input']>;
  useCurrent?: Scalars['Boolean']['input'];
  useGbm?: Scalars['Boolean']['input'];
  useHourly?: Scalars['Boolean']['input'];
  useScanner?: Scalars['Boolean']['input'];
  useSynthetic?: Scalars['Boolean']['input'];
  useYears?: Scalars['Boolean']['input'];
  windows?: Scalars['Int']['input'];
  years?: Scalars['Float']['input'];
};

export type MaCrossAnalysisResponse = {
  __typename?: 'MACrossAnalysisResponse';
  error?: Maybe<Scalars['String']['output']>;
  executionTime: Scalars['Float']['output'];
  portfolios?: Maybe<Array<AnalysisResult>>;
  requestId: Scalars['String']['output'];
  status: Scalars['String']['output'];
  strategyTypes: Array<Scalars['String']['output']>;
  tickers: Array<Scalars['String']['output']>;
  timestamp: Scalars['DateTime']['output'];
  totalPortfoliosAnalyzed: Scalars['Int']['output'];
  totalPortfoliosFiltered: Scalars['Int']['output'];
};

export type MaCrossAnalysisResponseAsyncAnalysisResponse = AsyncAnalysisResponse | MaCrossAnalysisResponse;

export type MetricsFilter = {
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  maxDrawdown?: InputMaybe<Scalars['Float']['input']>;
  minReturn?: InputMaybe<Scalars['Float']['input']>;
  minSharpe?: InputMaybe<Scalars['Float']['input']>;
  minTrades?: InputMaybe<Scalars['Int']['input']>;
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
};

export type Mutation = {
  __typename?: 'Mutation';
  addStrategyToPortfolio: Scalars['Boolean']['output'];
  cancelAnalysis: Scalars['Boolean']['output'];
  createPortfolio: Portfolio;
  createStrategy: Strategy;
  createStrategyConfiguration: StrategyConfiguration;
  deletePortfolio: Scalars['Boolean']['output'];
  deleteStrategy: Scalars['Boolean']['output'];
  deleteStrategyConfiguration: Scalars['Boolean']['output'];
  executeMaCrossAnalysis: MaCrossAnalysisResponseAsyncAnalysisResponse;
  getAnalysisStatus?: Maybe<AnalysisStatus>;
  removeStrategyFromPortfolio: Scalars['Boolean']['output'];
  updatePortfolio?: Maybe<Portfolio>;
  updateStrategy?: Maybe<Strategy>;
  updateStrategyConfiguration?: Maybe<StrategyConfiguration>;
};


export type MutationAddStrategyToPortfolioArgs = {
  allocationPct: Scalars['Float']['input'];
  portfolioId: Scalars['ID']['input'];
  position?: InputMaybe<Scalars['Int']['input']>;
  strategyConfigId: Scalars['ID']['input'];
};


export type MutationCancelAnalysisArgs = {
  executionId: Scalars['ID']['input'];
};


export type MutationCreatePortfolioArgs = {
  input: PortfolioInput;
};


export type MutationCreateStrategyArgs = {
  input: StrategyInput;
};


export type MutationCreateStrategyConfigurationArgs = {
  input: StrategyConfigurationInput;
};


export type MutationDeletePortfolioArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteStrategyArgs = {
  id: Scalars['ID']['input'];
};


export type MutationDeleteStrategyConfigurationArgs = {
  id: Scalars['ID']['input'];
};


export type MutationExecuteMaCrossAnalysisArgs = {
  input: MaCrossAnalysisInput;
};


export type MutationGetAnalysisStatusArgs = {
  executionId: Scalars['ID']['input'];
};


export type MutationRemoveStrategyFromPortfolioArgs = {
  portfolioId: Scalars['ID']['input'];
  strategyConfigId: Scalars['ID']['input'];
};


export type MutationUpdatePortfolioArgs = {
  id: Scalars['ID']['input'];
  input: PortfolioInput;
};


export type MutationUpdateStrategyArgs = {
  id: Scalars['ID']['input'];
  input: StrategyInput;
};


export type MutationUpdateStrategyConfigurationArgs = {
  id: Scalars['ID']['input'];
  input: StrategyConfigurationInput;
};

export type PerformanceCriteria = {
  beatsBnh?: InputMaybe<Scalars['Float']['input']>;
  expectancyPerTrade?: InputMaybe<Scalars['Float']['input']>;
  profitFactor?: InputMaybe<Scalars['Float']['input']>;
  score?: InputMaybe<Scalars['Float']['input']>;
  sortinoRatio?: InputMaybe<Scalars['Float']['input']>;
  trades?: InputMaybe<Scalars['Int']['input']>;
  winRate?: InputMaybe<Scalars['Float']['input']>;
};

export type PerformanceMetrics = {
  __typename?: 'PerformanceMetrics';
  annualReturn?: Maybe<Scalars['Float']['output']>;
  calmarRatio?: Maybe<Scalars['Float']['output']>;
  expectancy?: Maybe<Scalars['Float']['output']>;
  maxDrawdown?: Maybe<Scalars['Float']['output']>;
  profitFactor?: Maybe<Scalars['Float']['output']>;
  score?: Maybe<Scalars['Float']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  totalReturn: Scalars['Float']['output'];
  totalTrades: Scalars['Int']['output'];
  winRate?: Maybe<Scalars['Float']['output']>;
};

export type Portfolio = {
  __typename?: 'Portfolio';
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  parameters?: Maybe<Scalars['JSON']['output']>;
  type: PortfolioType;
  updatedAt: Scalars['DateTime']['output'];
};

export type PortfolioFilter = {
  createdAfter?: InputMaybe<Scalars['DateTime']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  nameContains?: InputMaybe<Scalars['String']['input']>;
  type?: InputMaybe<PortfolioType>;
};

export type PortfolioInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  parameters?: InputMaybe<Scalars['JSON']['input']>;
  type?: PortfolioType;
};

export type PortfolioMetrics = {
  __typename?: 'PortfolioMetrics';
  avgConcurrentStrategies?: Maybe<Scalars['Float']['output']>;
  concurrencyRatio?: Maybe<Scalars['Float']['output']>;
  correlationMatrix?: Maybe<Scalars['JSON']['output']>;
  createdAt: Scalars['DateTime']['output'];
  diversificationRatio?: Maybe<Scalars['Float']['output']>;
  efficiencyScore?: Maybe<Scalars['Float']['output']>;
  id: Scalars['ID']['output'];
  maxConcurrentStrategies?: Maybe<Scalars['Int']['output']>;
  maxDrawdownPct?: Maybe<Scalars['Float']['output']>;
  metricDate: Scalars['DateTime']['output'];
  performanceAttribution?: Maybe<Scalars['JSON']['output']>;
  portfolioId: Scalars['String']['output'];
  portfolioVar?: Maybe<Scalars['Float']['output']>;
  riskContribution?: Maybe<Scalars['JSON']['output']>;
  sharpeRatio?: Maybe<Scalars['Float']['output']>;
  sortinoRatio?: Maybe<Scalars['Float']['output']>;
  strategyWeights?: Maybe<Scalars['JSON']['output']>;
  totalReturnPct: Scalars['Float']['output'];
};

export enum PortfolioType {
  Best = 'BEST',
  Filtered = 'FILTERED',
  Standard = 'STANDARD'
}

export type PriceBar = {
  __typename?: 'PriceBar';
  close: Scalars['Float']['output'];
  date: Scalars['DateTime']['output'];
  high: Scalars['Float']['output'];
  low: Scalars['Float']['output'];
  open: Scalars['Float']['output'];
  volume?: Maybe<Scalars['Float']['output']>;
};

export type PriceDataFilter = {
  endDate?: InputMaybe<Scalars['DateTime']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  startDate?: InputMaybe<Scalars['DateTime']['input']>;
  symbol?: InputMaybe<Scalars['String']['input']>;
};

export type Query = {
  __typename?: 'Query';
  availableTimeframes: Array<TimeframeType>;
  backtestResults: Array<BacktestResult>;
  portfolio?: Maybe<Portfolio>;
  portfolioMetrics: Array<PortfolioMetrics>;
  portfolios: Array<Portfolio>;
  priceData: Array<PriceBar>;
  signals: Array<Signal>;
  strategies: Array<Strategy>;
  strategy?: Maybe<Strategy>;
  strategyConfigurations: Array<StrategyConfiguration>;
  ticker?: Maybe<Ticker>;
  tickers: Array<Ticker>;
};


export type QueryBacktestResultsArgs = {
  filter?: InputMaybe<MetricsFilter>;
  strategyConfigId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryPortfolioArgs = {
  id: Scalars['ID']['input'];
};


export type QueryPortfolioMetricsArgs = {
  filter?: InputMaybe<MetricsFilter>;
  portfolioId: Scalars['ID']['input'];
};


export type QueryPortfoliosArgs = {
  filter?: InputMaybe<PortfolioFilter>;
};


export type QueryPriceDataArgs = {
  filter?: InputMaybe<PriceDataFilter>;
  symbol: Scalars['String']['input'];
};


export type QuerySignalsArgs = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  strategyConfigId?: InputMaybe<Scalars['ID']['input']>;
};


export type QueryStrategiesArgs = {
  filter?: InputMaybe<StrategyFilter>;
};


export type QueryStrategyArgs = {
  id: Scalars['ID']['input'];
};


export type QueryStrategyConfigurationsArgs = {
  filter?: InputMaybe<StrategyFilter>;
  strategyId?: InputMaybe<Scalars['ID']['input']>;
  tickerSymbol?: InputMaybe<Scalars['String']['input']>;
};


export type QueryTickerArgs = {
  symbol: Scalars['String']['input'];
};


export type QueryTickersArgs = {
  assetClass?: InputMaybe<Scalars['String']['input']>;
  limit?: InputMaybe<Scalars['Int']['input']>;
  symbolContains?: InputMaybe<Scalars['String']['input']>;
};

export type Signal = {
  __typename?: 'Signal';
  confidence?: Maybe<Scalars['Float']['output']>;
  createdAt: Scalars['DateTime']['output'];
  id: Scalars['ID']['output'];
  metadata?: Maybe<Scalars['JSON']['output']>;
  price: Scalars['Float']['output'];
  quantity?: Maybe<Scalars['Float']['output']>;
  signalDate: Scalars['DateTime']['output'];
  signalType: SignalType;
  strategyConfigId: Scalars['String']['output'];
};

export enum SignalType {
  Buy = 'BUY',
  Hold = 'HOLD',
  Sell = 'SELL'
}

export type Strategy = {
  __typename?: 'Strategy';
  createdAt: Scalars['DateTime']['output'];
  description?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name: Scalars['String']['output'];
  type: StrategyType;
  updatedAt: Scalars['DateTime']['output'];
};

export type StrategyConfiguration = {
  __typename?: 'StrategyConfiguration';
  allocationPct?: Maybe<Scalars['Float']['output']>;
  createdAt: Scalars['DateTime']['output'];
  direction: DirectionType;
  id: Scalars['ID']['output'];
  longWindow?: Maybe<Scalars['Int']['output']>;
  parameters?: Maybe<Scalars['JSON']['output']>;
  rsiPeriod?: Maybe<Scalars['Int']['output']>;
  rsiThreshold?: Maybe<Scalars['Float']['output']>;
  shortWindow?: Maybe<Scalars['Int']['output']>;
  signalEntry?: Maybe<Scalars['String']['output']>;
  signalExit?: Maybe<Scalars['String']['output']>;
  signalWindow?: Maybe<Scalars['Int']['output']>;
  stopLossPct?: Maybe<Scalars['Float']['output']>;
  strategyId: Scalars['String']['output'];
  tickerId: Scalars['String']['output'];
  timeframe: TimeframeType;
  updatedAt: Scalars['DateTime']['output'];
};

export type StrategyConfigurationInput = {
  allocationPct?: InputMaybe<Scalars['Float']['input']>;
  direction?: DirectionType;
  longWindow?: InputMaybe<Scalars['Int']['input']>;
  parameters?: InputMaybe<Scalars['JSON']['input']>;
  rsiPeriod?: InputMaybe<Scalars['Int']['input']>;
  rsiThreshold?: InputMaybe<Scalars['Float']['input']>;
  shortWindow?: InputMaybe<Scalars['Int']['input']>;
  signalEntry?: InputMaybe<Scalars['String']['input']>;
  signalExit?: InputMaybe<Scalars['String']['input']>;
  signalWindow?: InputMaybe<Scalars['Int']['input']>;
  stopLossPct?: InputMaybe<Scalars['Float']['input']>;
  strategyId: Scalars['String']['input'];
  tickerId: Scalars['String']['input'];
  timeframe: TimeframeType;
};

export type StrategyFilter = {
  limit?: InputMaybe<Scalars['Int']['input']>;
  tickerSymbol?: InputMaybe<Scalars['String']['input']>;
  timeframe?: InputMaybe<TimeframeType>;
  type?: InputMaybe<StrategyType>;
};

export type StrategyInput = {
  description?: InputMaybe<Scalars['String']['input']>;
  name: Scalars['String']['input'];
  type: StrategyType;
};

export enum StrategyType {
  Atr = 'ATR',
  BollingerBands = 'BOLLINGER_BANDS',
  Custom = 'CUSTOM',
  Macd = 'MACD',
  MaCross = 'MA_CROSS',
  MeanReversion = 'MEAN_REVERSION',
  Range = 'RANGE',
  Rsi = 'RSI'
}

export type Ticker = {
  __typename?: 'Ticker';
  assetClass: AssetClass;
  createdAt: Scalars['DateTime']['output'];
  exchange?: Maybe<Scalars['String']['output']>;
  id: Scalars['ID']['output'];
  name?: Maybe<Scalars['String']['output']>;
  sector?: Maybe<Scalars['String']['output']>;
  symbol: Scalars['String']['output'];
  updatedAt: Scalars['DateTime']['output'];
};

export enum TimeframeType {
  EightHours = 'EIGHT_HOURS',
  FifteenMinutes = 'FIFTEEN_MINUTES',
  FiveMinutes = 'FIVE_MINUTES',
  FourHours = 'FOUR_HOURS',
  OneDay = 'ONE_DAY',
  OneHour = 'ONE_HOUR',
  OneMinute = 'ONE_MINUTE',
  OneMonth = 'ONE_MONTH',
  OneWeek = 'ONE_WEEK',
  SixHours = 'SIX_HOURS',
  ThirtyMinutes = 'THIRTY_MINUTES',
  ThreeDays = 'THREE_DAYS',
  TwelveHours = 'TWELVE_HOURS',
  TwoHours = 'TWO_HOURS'
}

export type ExecuteMaCrossAnalysisMutationVariables = Exact<{
  input: MaCrossAnalysisInput;
}>;


export type ExecuteMaCrossAnalysisMutation = { __typename?: 'Mutation', executeMaCrossAnalysis: { __typename?: 'AsyncAnalysisResponse', status: string, executionId: string, message: string, statusUrl: string, streamUrl: string, timestamp: string, estimatedTime?: number | null } | { __typename?: 'MACrossAnalysisResponse', status: string, requestId: string, timestamp: string, tickers: Array<string>, strategyTypes: Array<string>, totalPortfoliosAnalyzed: number, totalPortfoliosFiltered: number, executionTime: number, portfolios?: Array<{ __typename?: 'AnalysisResult', ticker: string, strategyType: string, shortWindow: number, longWindow: number, hasOpenTrade: boolean, hasSignalEntry: boolean, performance: { __typename?: 'PerformanceMetrics', totalReturn: number, sharpeRatio?: number | null, maxDrawdown?: number | null, winRate?: number | null, profitFactor?: number | null, expectancy?: number | null } }> | null } };

export type CreatePortfolioMutationVariables = Exact<{
  input: PortfolioInput;
}>;


export type CreatePortfolioMutation = { __typename?: 'Mutation', createPortfolio: { __typename?: 'Portfolio', id: string, name: string, type: PortfolioType, description?: string | null, parameters?: Record<string, any> | null, createdAt: string } };

export type UpdatePortfolioMutationVariables = Exact<{
  id: Scalars['ID']['input'];
  input: PortfolioInput;
}>;


export type UpdatePortfolioMutation = { __typename?: 'Mutation', updatePortfolio?: { __typename?: 'Portfolio', id: string, name: string, type: PortfolioType, description?: string | null, parameters?: Record<string, any> | null, updatedAt: string } | null };

export type DeletePortfolioMutationVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type DeletePortfolioMutation = { __typename?: 'Mutation', deletePortfolio: boolean };

export type GetFileListQueryVariables = Exact<{
  limit?: InputMaybe<Scalars['Int']['input']>;
}>;


export type GetFileListQuery = { __typename?: 'Query', tickers: Array<{ __typename?: 'Ticker', id: string, symbol: string, name?: string | null, assetClass: AssetClass, exchange?: string | null }>, strategies: Array<{ __typename?: 'Strategy', id: string, name: string, type: StrategyType, description?: string | null, createdAt: string, updatedAt: string }> };

export type GetPortfoliosQueryVariables = Exact<{
  filter?: InputMaybe<PortfolioFilter>;
}>;


export type GetPortfoliosQuery = { __typename?: 'Query', portfolios: Array<{ __typename?: 'Portfolio', id: string, name: string, type: PortfolioType, description?: string | null, parameters?: Record<string, any> | null, createdAt: string, updatedAt: string }> };

export type GetPortfolioByIdQueryVariables = Exact<{
  id: Scalars['ID']['input'];
}>;


export type GetPortfolioByIdQuery = { __typename?: 'Query', portfolio?: { __typename?: 'Portfolio', id: string, name: string, type: PortfolioType, description?: string | null, parameters?: Record<string, any> | null, createdAt: string, updatedAt: string } | null };

export type GetPriceDataQueryVariables = Exact<{
  symbol: Scalars['String']['input'];
  filter?: InputMaybe<PriceDataFilter>;
}>;


export type GetPriceDataQuery = { __typename?: 'Query', priceData: Array<{ __typename?: 'PriceBar', date: string, open: number, high: number, low: number, close: number, volume?: number | null }> };


export const ExecuteMaCrossAnalysisDocument = /*#__PURE__*/ gql`
    mutation ExecuteMACrossAnalysis($input: MACrossAnalysisInput!) {
  executeMaCrossAnalysis(input: $input) {
    ... on MACrossAnalysisResponse {
      status
      requestId
      timestamp
      tickers
      strategyTypes
      totalPortfoliosAnalyzed
      totalPortfoliosFiltered
      executionTime
      portfolios {
        ticker
        strategyType
        shortWindow
        longWindow
        performance {
          totalReturn
          sharpeRatio
          maxDrawdown
          winRate
          profitFactor
          expectancy
        }
        hasOpenTrade
        hasSignalEntry
      }
    }
    ... on AsyncAnalysisResponse {
      status
      executionId
      message
      statusUrl
      streamUrl
      timestamp
      estimatedTime
    }
  }
}
    `;
export type ExecuteMaCrossAnalysisMutationFn = Apollo.MutationFunction<ExecuteMaCrossAnalysisMutation, ExecuteMaCrossAnalysisMutationVariables>;

/**
 * __useExecuteMaCrossAnalysisMutation__
 *
 * To run a mutation, you first call `useExecuteMaCrossAnalysisMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useExecuteMaCrossAnalysisMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [executeMaCrossAnalysisMutation, { data, loading, error }] = useExecuteMaCrossAnalysisMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useExecuteMaCrossAnalysisMutation(baseOptions?: Apollo.MutationHookOptions<ExecuteMaCrossAnalysisMutation, ExecuteMaCrossAnalysisMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<ExecuteMaCrossAnalysisMutation, ExecuteMaCrossAnalysisMutationVariables>(ExecuteMaCrossAnalysisDocument, options);
      }
export type ExecuteMaCrossAnalysisMutationHookResult = ReturnType<typeof useExecuteMaCrossAnalysisMutation>;
export type ExecuteMaCrossAnalysisMutationResult = Apollo.MutationResult<ExecuteMaCrossAnalysisMutation>;
export type ExecuteMaCrossAnalysisMutationOptions = Apollo.BaseMutationOptions<ExecuteMaCrossAnalysisMutation, ExecuteMaCrossAnalysisMutationVariables>;
export const CreatePortfolioDocument = /*#__PURE__*/ gql`
    mutation CreatePortfolio($input: PortfolioInput!) {
  createPortfolio(input: $input) {
    id
    name
    type
    description
    parameters
    createdAt
  }
}
    `;
export type CreatePortfolioMutationFn = Apollo.MutationFunction<CreatePortfolioMutation, CreatePortfolioMutationVariables>;

/**
 * __useCreatePortfolioMutation__
 *
 * To run a mutation, you first call `useCreatePortfolioMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useCreatePortfolioMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [createPortfolioMutation, { data, loading, error }] = useCreatePortfolioMutation({
 *   variables: {
 *      input: // value for 'input'
 *   },
 * });
 */
export function useCreatePortfolioMutation(baseOptions?: Apollo.MutationHookOptions<CreatePortfolioMutation, CreatePortfolioMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<CreatePortfolioMutation, CreatePortfolioMutationVariables>(CreatePortfolioDocument, options);
      }
export type CreatePortfolioMutationHookResult = ReturnType<typeof useCreatePortfolioMutation>;
export type CreatePortfolioMutationResult = Apollo.MutationResult<CreatePortfolioMutation>;
export type CreatePortfolioMutationOptions = Apollo.BaseMutationOptions<CreatePortfolioMutation, CreatePortfolioMutationVariables>;
export const UpdatePortfolioDocument = /*#__PURE__*/ gql`
    mutation UpdatePortfolio($id: ID!, $input: PortfolioInput!) {
  updatePortfolio(id: $id, input: $input) {
    id
    name
    type
    description
    parameters
    updatedAt
  }
}
    `;
export type UpdatePortfolioMutationFn = Apollo.MutationFunction<UpdatePortfolioMutation, UpdatePortfolioMutationVariables>;

/**
 * __useUpdatePortfolioMutation__
 *
 * To run a mutation, you first call `useUpdatePortfolioMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useUpdatePortfolioMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [updatePortfolioMutation, { data, loading, error }] = useUpdatePortfolioMutation({
 *   variables: {
 *      id: // value for 'id'
 *      input: // value for 'input'
 *   },
 * });
 */
export function useUpdatePortfolioMutation(baseOptions?: Apollo.MutationHookOptions<UpdatePortfolioMutation, UpdatePortfolioMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<UpdatePortfolioMutation, UpdatePortfolioMutationVariables>(UpdatePortfolioDocument, options);
      }
export type UpdatePortfolioMutationHookResult = ReturnType<typeof useUpdatePortfolioMutation>;
export type UpdatePortfolioMutationResult = Apollo.MutationResult<UpdatePortfolioMutation>;
export type UpdatePortfolioMutationOptions = Apollo.BaseMutationOptions<UpdatePortfolioMutation, UpdatePortfolioMutationVariables>;
export const DeletePortfolioDocument = /*#__PURE__*/ gql`
    mutation DeletePortfolio($id: ID!) {
  deletePortfolio(id: $id)
}
    `;
export type DeletePortfolioMutationFn = Apollo.MutationFunction<DeletePortfolioMutation, DeletePortfolioMutationVariables>;

/**
 * __useDeletePortfolioMutation__
 *
 * To run a mutation, you first call `useDeletePortfolioMutation` within a React component and pass it any options that fit your needs.
 * When your component renders, `useDeletePortfolioMutation` returns a tuple that includes:
 * - A mutate function that you can call at any time to execute the mutation
 * - An object with fields that represent the current status of the mutation's execution
 *
 * @param baseOptions options that will be passed into the mutation, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options-2;
 *
 * @example
 * const [deletePortfolioMutation, { data, loading, error }] = useDeletePortfolioMutation({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useDeletePortfolioMutation(baseOptions?: Apollo.MutationHookOptions<DeletePortfolioMutation, DeletePortfolioMutationVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useMutation<DeletePortfolioMutation, DeletePortfolioMutationVariables>(DeletePortfolioDocument, options);
      }
export type DeletePortfolioMutationHookResult = ReturnType<typeof useDeletePortfolioMutation>;
export type DeletePortfolioMutationResult = Apollo.MutationResult<DeletePortfolioMutation>;
export type DeletePortfolioMutationOptions = Apollo.BaseMutationOptions<DeletePortfolioMutation, DeletePortfolioMutationVariables>;
export const GetFileListDocument = /*#__PURE__*/ gql`
    query GetFileList($limit: Int) {
  tickers(limit: $limit) {
    id
    symbol
    name
    assetClass
    exchange
  }
  strategies {
    id
    name
    type
    description
    createdAt
    updatedAt
  }
}
    `;

/**
 * __useGetFileListQuery__
 *
 * To run a query within a React component, call `useGetFileListQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetFileListQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetFileListQuery({
 *   variables: {
 *      limit: // value for 'limit'
 *   },
 * });
 */
export function useGetFileListQuery(baseOptions?: Apollo.QueryHookOptions<GetFileListQuery, GetFileListQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetFileListQuery, GetFileListQueryVariables>(GetFileListDocument, options);
      }
export function useGetFileListLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetFileListQuery, GetFileListQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetFileListQuery, GetFileListQueryVariables>(GetFileListDocument, options);
        }
export function useGetFileListSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetFileListQuery, GetFileListQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetFileListQuery, GetFileListQueryVariables>(GetFileListDocument, options);
        }
export type GetFileListQueryHookResult = ReturnType<typeof useGetFileListQuery>;
export type GetFileListLazyQueryHookResult = ReturnType<typeof useGetFileListLazyQuery>;
export type GetFileListSuspenseQueryHookResult = ReturnType<typeof useGetFileListSuspenseQuery>;
export type GetFileListQueryResult = Apollo.QueryResult<GetFileListQuery, GetFileListQueryVariables>;
export function refetchGetFileListQuery(variables?: GetFileListQueryVariables) {
      return { query: GetFileListDocument, variables: variables }
    }
export const GetPortfoliosDocument = /*#__PURE__*/ gql`
    query GetPortfolios($filter: PortfolioFilter) {
  portfolios(filter: $filter) {
    id
    name
    type
    description
    parameters
    createdAt
    updatedAt
  }
}
    `;

/**
 * __useGetPortfoliosQuery__
 *
 * To run a query within a React component, call `useGetPortfoliosQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPortfoliosQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPortfoliosQuery({
 *   variables: {
 *      filter: // value for 'filter'
 *   },
 * });
 */
export function useGetPortfoliosQuery(baseOptions?: Apollo.QueryHookOptions<GetPortfoliosQuery, GetPortfoliosQueryVariables>) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPortfoliosQuery, GetPortfoliosQueryVariables>(GetPortfoliosDocument, options);
      }
export function useGetPortfoliosLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPortfoliosQuery, GetPortfoliosQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPortfoliosQuery, GetPortfoliosQueryVariables>(GetPortfoliosDocument, options);
        }
export function useGetPortfoliosSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPortfoliosQuery, GetPortfoliosQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPortfoliosQuery, GetPortfoliosQueryVariables>(GetPortfoliosDocument, options);
        }
export type GetPortfoliosQueryHookResult = ReturnType<typeof useGetPortfoliosQuery>;
export type GetPortfoliosLazyQueryHookResult = ReturnType<typeof useGetPortfoliosLazyQuery>;
export type GetPortfoliosSuspenseQueryHookResult = ReturnType<typeof useGetPortfoliosSuspenseQuery>;
export type GetPortfoliosQueryResult = Apollo.QueryResult<GetPortfoliosQuery, GetPortfoliosQueryVariables>;
export function refetchGetPortfoliosQuery(variables?: GetPortfoliosQueryVariables) {
      return { query: GetPortfoliosDocument, variables: variables }
    }
export const GetPortfolioByIdDocument = /*#__PURE__*/ gql`
    query GetPortfolioById($id: ID!) {
  portfolio(id: $id) {
    id
    name
    type
    description
    parameters
    createdAt
    updatedAt
  }
}
    `;

/**
 * __useGetPortfolioByIdQuery__
 *
 * To run a query within a React component, call `useGetPortfolioByIdQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPortfolioByIdQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPortfolioByIdQuery({
 *   variables: {
 *      id: // value for 'id'
 *   },
 * });
 */
export function useGetPortfolioByIdQuery(baseOptions: Apollo.QueryHookOptions<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables> & ({ variables: GetPortfolioByIdQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>(GetPortfolioByIdDocument, options);
      }
export function useGetPortfolioByIdLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>(GetPortfolioByIdDocument, options);
        }
export function useGetPortfolioByIdSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>(GetPortfolioByIdDocument, options);
        }
export type GetPortfolioByIdQueryHookResult = ReturnType<typeof useGetPortfolioByIdQuery>;
export type GetPortfolioByIdLazyQueryHookResult = ReturnType<typeof useGetPortfolioByIdLazyQuery>;
export type GetPortfolioByIdSuspenseQueryHookResult = ReturnType<typeof useGetPortfolioByIdSuspenseQuery>;
export type GetPortfolioByIdQueryResult = Apollo.QueryResult<GetPortfolioByIdQuery, GetPortfolioByIdQueryVariables>;
export function refetchGetPortfolioByIdQuery(variables: GetPortfolioByIdQueryVariables) {
      return { query: GetPortfolioByIdDocument, variables: variables }
    }
export const GetPriceDataDocument = /*#__PURE__*/ gql`
    query GetPriceData($symbol: String!, $filter: PriceDataFilter) {
  priceData(symbol: $symbol, filter: $filter) {
    date
    open
    high
    low
    close
    volume
  }
}
    `;

/**
 * __useGetPriceDataQuery__
 *
 * To run a query within a React component, call `useGetPriceDataQuery` and pass it any options that fit your needs.
 * When your component renders, `useGetPriceDataQuery` returns an object from Apollo Client that contains loading, error, and data properties
 * you can use to render your UI.
 *
 * @param baseOptions options that will be passed into the query, supported options are listed on: https://www.apollographql.com/docs/react/api/react-hooks/#options;
 *
 * @example
 * const { data, loading, error } = useGetPriceDataQuery({
 *   variables: {
 *      symbol: // value for 'symbol'
 *      filter: // value for 'filter'
 *   },
 * });
 */
export function useGetPriceDataQuery(baseOptions: Apollo.QueryHookOptions<GetPriceDataQuery, GetPriceDataQueryVariables> & ({ variables: GetPriceDataQueryVariables; skip?: boolean; } | { skip: boolean; }) ) {
        const options = {...defaultOptions, ...baseOptions}
        return Apollo.useQuery<GetPriceDataQuery, GetPriceDataQueryVariables>(GetPriceDataDocument, options);
      }
export function useGetPriceDataLazyQuery(baseOptions?: Apollo.LazyQueryHookOptions<GetPriceDataQuery, GetPriceDataQueryVariables>) {
          const options = {...defaultOptions, ...baseOptions}
          return Apollo.useLazyQuery<GetPriceDataQuery, GetPriceDataQueryVariables>(GetPriceDataDocument, options);
        }
export function useGetPriceDataSuspenseQuery(baseOptions?: Apollo.SkipToken | Apollo.SuspenseQueryHookOptions<GetPriceDataQuery, GetPriceDataQueryVariables>) {
          const options = baseOptions === Apollo.skipToken ? baseOptions : {...defaultOptions, ...baseOptions}
          return Apollo.useSuspenseQuery<GetPriceDataQuery, GetPriceDataQueryVariables>(GetPriceDataDocument, options);
        }
export type GetPriceDataQueryHookResult = ReturnType<typeof useGetPriceDataQuery>;
export type GetPriceDataLazyQueryHookResult = ReturnType<typeof useGetPriceDataLazyQuery>;
export type GetPriceDataSuspenseQueryHookResult = ReturnType<typeof useGetPriceDataSuspenseQuery>;
export type GetPriceDataQueryResult = Apollo.QueryResult<GetPriceDataQuery, GetPriceDataQueryVariables>;
export function refetchGetPriceDataQuery(variables: GetPriceDataQueryVariables) {
      return { query: GetPriceDataDocument, variables: variables }
    }