# Technical Implementation Guide: Concurrency Analysis Module

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Data Structures and Types](#data-structures-and-types)
3. [Core Algorithms](#core-algorithms)
4. [Configuration System](#configuration-system)
5. [Error Handling Framework](#error-handling-framework)
6. [Portfolio Processing Pipeline](#portfolio-processing-pipeline)
7. [Strategy Processing](#strategy-processing)
8. [Analysis Engine](#analysis-engine)
9. [Optimization Engine](#optimization-engine)
10. [Visualization System](#visualization-system)
11. [Report Generation](#report-generation)
12. [Performance Optimizations](#performance-optimizations)
13. [Integration Points](#integration-points)
14. [Testing Framework](#testing-framework)

## Architecture Overview

### Design Patterns

The concurrency module implements several design patterns:

1. **Strategy Pattern**: Different allocation strategies (Equal, Performance, Risk-Adjusted)
2. **Factory Pattern**: Strategy creation based on configuration type
3. **Observer Pattern**: Progress tracking during optimization
4. **Context Manager Pattern**: Resource management and error handling
5. **Registry Pattern**: Error tracking and analytics
6. **Adapter Pattern**: Format adaptation between CSV and JSON portfolios

### Module Dependencies

```python
# Core Dependencies
polars as pl           # High-performance dataframes
numpy as np           # Numerical computations
plotly.graph_objects  # Interactive visualizations
typing               # Type annotations

# Internal Dependencies
app.tools.*          # Shared trading utilities
app.concurrency.tools.*  # Module-specific tools
```

### File Organization

```
app/concurrency/
├── Configuration Layer
│   ├── config.py            # Type definitions
│   ├── config_defaults.py   # Default values
│   └── config/             # Additional configs
├── Core Engine
│   ├── review.py           # Main entry point
│   └── tools/
│       ├── runner.py       # Orchestration
│       ├── analysis.py     # Core algorithms
│       └── permutation.py  # Optimization
├── Processing Layer
│   └── tools/
│       ├── strategy_processor.py
│       ├── portfolio_loader.py
│       └── data_alignment.py
├── Metrics Layer
│   └── tools/
│       ├── efficiency.py
│       ├── risk_metrics.py
│       ├── signal_quality.py
│       └── position_metrics.py
├── Output Layer
│   └── tools/
│       ├── visualization.py
│       └── report/
└── Infrastructure
    └── error_handling/
```

## Data Structures and Types

### Core Types

```python
# Configuration Types
class ConcurrencyConfig(TypedDict):
    PORTFOLIO: str
    BASE_DIR: str
    REFRESH: bool
    VISUALIZATION: bool
    OPTIMIZE: bool
    ALLOCATION_MODE: str
    REPORT_INCLUDES: Dict[str, bool]

# Strategy Configuration
class StrategyConfig(TypedDict):
    ticker: str
    strategy_type: str
    fast_period: int
    slow_period: int
    signal_period: int
    allocation: float
    stop_loss: Optional[float]

# Analysis Results
class ConcurrencyStats(TypedDict):
    portfolio_metrics: Dict[str, Any]
    ticker_metrics: Optional[Dict[str, Any]]
    strategies: Optional[List[Dict[str, Any]]]
    config: Dict[str, Any]
```

### Internal Data Structures

```python
# Position Arrays (for correlation analysis)
position_arrays: Dict[str, np.ndarray]  # strategy_id -> position array

# Correlation Matrix
correlation_matrix: np.ndarray  # NxN matrix of correlations

# Activity Periods
activity_periods: Dict[str, Dict[str, int]]  # {
#     "active": count,
#     "inactive": count,
#     "exclusive": count,
#     "concurrent": count
# }

# Risk Contributions
risk_contributions: Dict[str, float]  # strategy_id -> risk weight

# Allocation Weights
allocations: Dict[str, float]  # strategy_id -> allocation percentage
```

## Core Algorithms

### 1. Correlation Calculation

```python
def calculate_correlations(position_arrays: Dict[str, np.ndarray]) -> np.ndarray:
    """
    Calculate pairwise correlations between strategy positions.

    Algorithm:
    1. Convert position arrays to matrix form
    2. Use numpy's corrcoef for efficient correlation calculation
    3. Handle NaN values from strategies with no position changes
    """
    strategies = list(position_arrays.keys())
    n_strategies = len(strategies)

    # Create position matrix
    position_matrix = np.array([position_arrays[strategy] for strategy in strategies])

    # Calculate correlation matrix
    correlation_matrix = np.corrcoef(position_matrix)

    # Handle NaN values (strategies with constant positions)
    correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0)

    return correlation_matrix
```

### 2. Independence Factor Calculation

```python
def calculate_independence_factor(
    exclusive_ratio: float,
    concurrent_ratio: float,
    inactive_ratio: float
) -> float:
    """
    Calculate independence factor using sophisticated formula.

    Algorithm:
    1. Calculate active ratio: 1 - inactive_ratio
    2. Calculate exclusive portion of active periods
    3. Apply transformation to prevent extreme values
    4. Ensure minimum independence value
    """
    active_ratio = 1 - inactive_ratio

    if active_ratio == 0:
        return 0.1  # Minimum independence for inactive strategies

    # Proportion of active periods that are exclusive
    exclusive_proportion = exclusive_ratio / active_ratio

    # Transform to prevent extreme values
    independence = max(0.1, exclusive_proportion)

    # Apply adjustment to make metric less sensitive to low values
    adjusted_independence = 0.2 + 0.8 * independence

    return adjusted_independence
```

### 3. Efficiency Score Calculation

```python
def calculate_strategy_efficiency(
    strategy_id: str,
    correlation_matrix: np.ndarray,
    activity_data: Dict[str, Dict[str, int]],
    strategy_index: int,
    strategies: List[str]
) -> float:
    """
    Calculate efficiency score for a single strategy.

    Components:
    1. Diversification = 1 - average_correlation_with_others
    2. Independence = adjusted_independence_factor
    3. Activity = 1 - inactive_ratio

    Formula: efficiency = diversification × independence × activity
    """
    # Calculate diversification
    other_correlations = [
        abs(correlation_matrix[strategy_index, j])
        for j in range(len(strategies))
        if j != strategy_index
    ]
    average_correlation = np.mean(other_correlations) if other_correlations else 0
    diversification = 1 - average_correlation

    # Calculate independence
    periods = activity_data[strategy_id]
    total_periods = sum(periods.values())

    exclusive_ratio = periods['exclusive'] / total_periods if total_periods > 0 else 0
    concurrent_ratio = periods['concurrent'] / total_periods if total_periods > 0 else 0
    inactive_ratio = periods['inactive'] / total_periods if total_periods > 0 else 1

    independence = calculate_independence_factor(
        exclusive_ratio, concurrent_ratio, inactive_ratio
    )

    # Calculate activity
    activity = 1 - inactive_ratio

    # Combine components
    efficiency = diversification * independence * activity

    return efficiency
```

### 4. Risk-Adjusted Efficiency

```python
def calculate_weighted_efficiency(
    base_efficiency: float,
    expectancy: float,
    allocation: float,
    risk_contribution: float
) -> float:
    """
    Calculate risk-adjusted efficiency incorporating performance.

    Formula: weighted_eff = base_efficiency × expectancy × allocation × risk_factor
    Where risk_factor = 1 - risk_contribution
    """
    risk_factor = 1 - risk_contribution
    weighted_efficiency = base_efficiency * expectancy * allocation * risk_factor

    return weighted_efficiency
```

### 5. Portfolio-Level Metrics

```python
def calculate_portfolio_efficiency(
    strategy_efficiencies: Dict[str, float],
    allocations: Dict[str, float],
    expectancies: Dict[str, float],
    risk_contributions: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate portfolio-level efficiency metrics.

    Returns:
    - total_weighted_efficiency: Sum of all weighted efficiencies
    - average_efficiency: Allocation-weighted average efficiency
    - efficiency_score: Final portfolio efficiency score
    """
    total_weighted_efficiency = 0
    total_allocation = 0

    for strategy_id in strategy_efficiencies:
        base_efficiency = strategy_efficiencies[strategy_id]
        allocation = allocations[strategy_id]
        expectancy = expectancies[strategy_id]
        risk_contribution = risk_contributions[strategy_id]

        weighted_eff = calculate_weighted_efficiency(
            base_efficiency, expectancy, allocation, risk_contribution
        )

        total_weighted_efficiency += weighted_eff
        total_allocation += allocation

    # Calculate metrics
    average_efficiency = total_weighted_efficiency / total_allocation if total_allocation > 0 else 0

    return {
        'total_weighted_efficiency': total_weighted_efficiency,
        'average_efficiency': average_efficiency,
        'efficiency_score': total_weighted_efficiency  # Primary metric
    }
```

## Configuration System

### Configuration Flow

```python
def load_and_validate_config(config_overrides: Dict = None) -> ConcurrencyConfig:
    """
    Configuration loading pipeline:
    1. Load environment variables
    2. Apply default values
    3. Apply user overrides
    4. Validate configuration
    5. Normalize paths and values
    """
    # Step 1: Environment variables
    env_config = load_environment_config()

    # Step 2: Default values
    config = {**DEFAULT_CONFIG, **env_config}

    # Step 3: User overrides
    if config_overrides:
        config.update(config_overrides)

    # Step 4: Validation
    validate_config(config)

    # Step 5: Normalization
    config = normalize_config(config)

    return config

def validate_config(config: Dict) -> None:
    """
    Validate configuration values:
    - Required fields present
    - Valid enum values
    - Path accessibility
    - Numeric ranges
    """
    required_fields = ['PORTFOLIO', 'BASE_DIR']
    for field in required_fields:
        if field not in config:
            raise ValidationError(f"Required field {field} missing")

    # Validate allocation mode
    valid_allocation_modes = [
        'EQUAL', 'SIGNAL_COUNT', 'PERFORMANCE',
        'RISK_ADJUSTED', 'INVERSE_VOLATILITY', 'CUSTOM'
    ]
    if config.get('ALLOCATION_MODE') not in valid_allocation_modes:
        raise ValidationError(f"Invalid allocation mode: {config.get('ALLOCATION_MODE')}")

    # Validate paths
    portfolio_path = get_portfolio_path(config['PORTFOLIO'])
    if not portfolio_path.exists():
        raise ValidationError(f"Portfolio file not found: {portfolio_path}")
```

### Schema Detection

```python
def detect_portfolio_schema(portfolio_data: Union[pd.DataFrame, Dict]) -> str:
    """
    Detect portfolio schema type:
    - base: Basic strategy parameters
    - extended: Includes allocation and stop_loss
    - json: JSON format with nested structure
    """
    if isinstance(portfolio_data, dict):
        return 'json'

    # Check for extended schema columns
    extended_columns = ['allocation', 'stop_loss', 'expectancy']
    has_extended = any(col in portfolio_data.columns for col in extended_columns)

    return 'extended' if has_extended else 'base'
```

## Error Handling Framework

### Exception Hierarchy

```python
class ConcurrencyError(TradingSystemError):
    """Base exception for concurrency analysis errors."""
    pass

class StrategyProcessingError(ConcurrencyError):
    """Error during strategy processing."""
    pass

class PermutationAnalysisError(ConcurrencyError):
    """Error during permutation analysis."""
    pass

class ValidationError(ConcurrencyError):
    """Configuration or data validation error."""
    pass
```

### Error Handling Decorators

```python
def handle_concurrency_errors(
    error_mapping: Dict[Type[Exception], Type[ConcurrencyError]] = None,
    re_raise: bool = True,
    recovery_function: Callable = None
):
    """
    Decorator for standardized error handling.

    Features:
    - Automatic context extraction
    - Error type mapping
    - Optional recovery functions
    - Logging integration
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Extract context
                context = extract_context(func, args, kwargs)

                # Map error type
                if error_mapping and type(e) in error_mapping:
                    mapped_error = error_mapping[type(e)](str(e))
                    mapped_error.context = context
                    error_to_handle = mapped_error
                else:
                    error_to_handle = e

                # Log error
                logger.error(f"Error in {func.__name__}: {error_to_handle}")

                # Attempt recovery
                if recovery_function:
                    try:
                        return recovery_function(error_to_handle, context)
                    except Exception as recovery_error:
                        logger.error(f"Recovery failed: {recovery_error}")

                # Re-raise if configured
                if re_raise:
                    raise error_to_handle

                return None

        return wrapper
    return decorator
```

### Context Managers

```python
class concurrency_error_context:
    """
    Context manager for error handling with automatic cleanup.
    """
    def __init__(self, operation: str, cleanup_function: Callable = None):
        self.operation = operation
        self.cleanup_function = cleanup_function
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is None:
            logger.info(f"Completed {self.operation} in {duration:.2f}s")
        else:
            logger.error(f"Failed {self.operation} after {duration:.2f}s: {exc_val}")

            # Register error
            ErrorRegistry.instance().register_error(
                error_type=exc_type.__name__,
                operation=self.operation,
                message=str(exc_val)
            )

            # Cleanup if provided
            if self.cleanup_function:
                try:
                    self.cleanup_function()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")

        return False  # Don't suppress exceptions
```

## Portfolio Processing Pipeline

### Data Loading

```python
def load_portfolio(portfolio_name: str, config: ConcurrencyConfig) -> Tuple[List[StrategyConfig], str]:
    """
    Portfolio loading pipeline:
    1. Detect file format (CSV or JSON)
    2. Load and parse data
    3. Detect schema type
    4. Normalize to standard format
    5. Validate strategy configurations
    """
    portfolio_path = get_portfolio_path(portfolio_name)

    # Detect format
    if portfolio_path.suffix.lower() == '.csv':
        raw_data = pd.read_csv(portfolio_path)
        schema = detect_portfolio_schema(raw_data)
        strategies = parse_csv_portfolio(raw_data, schema, config)
    else:
        with open(portfolio_path, 'r') as f:
            raw_data = json.load(f)
        schema = 'json'
        strategies = parse_json_portfolio(raw_data, config)

    # Validate strategies
    for strategy in strategies:
        validate_strategy_config(strategy)

    return strategies, schema

def parse_csv_portfolio(data: pd.DataFrame, schema: str, config: ConcurrencyConfig) -> List[StrategyConfig]:
    """
    Parse CSV portfolio data into strategy configurations.

    Handles:
    - Base schema: ticker, strategy_type, fast_period, slow_period
    - Extended schema: + allocation, stop_loss, expectancy
    """
    strategies = []

    for _, row in data.iterrows():
        strategy = StrategyConfig(
            ticker=row['ticker'],
            strategy_type=row.get('strategy_type', 'SMA'),
            fast_period=int(row['fast_period']),
            slow_period=int(row['slow_period']),
            signal_period=int(row.get('signal_period', 0))
        )

        # Extended schema fields
        if schema == 'extended':
            strategy['allocation'] = float(row.get('allocation', 10.0))
            strategy['stop_loss'] = row.get('stop_loss') if pd.notna(row.get('stop_loss')) else None
            if strategy['stop_loss'] is not None:
                strategy['stop_loss'] = float(strategy['stop_loss'])
        else:
            # Calculate allocation based on mode
            strategy['allocation'] = calculate_default_allocation(strategy, config)

        strategies.append(strategy)

    return strategies
```

### Data Alignment

```python
def align_strategy_data(strategy_dataframes: Dict[str, pl.DataFrame]) -> Dict[str, pl.DataFrame]:
    """
    Align multiple strategy dataframes to common time index.

    Algorithm:
    1. Find common date range across all strategies
    2. Resample to common frequency
    3. Forward-fill missing positions
    4. Ensure consistent column names
    """
    if not strategy_dataframes:
        return {}

    # Find common date range
    start_dates = []
    end_dates = []

    for df in strategy_dataframes.values():
        start_dates.append(df['date'].min())
        end_dates.append(df['date'].max())

    common_start = max(start_dates)
    common_end = min(end_dates)

    # Align each dataframe
    aligned_dfs = {}

    for strategy_id, df in strategy_dataframes.items():
        # Filter to common date range
        aligned_df = df.filter(
            (pl.col('date') >= common_start) &
            (pl.col('date') <= common_end)
        )

        # Ensure required columns exist
        required_columns = ['date', 'position', 'close']
        for col in required_columns:
            if col not in aligned_df.columns:
                if col == 'position':
                    aligned_df = aligned_df.with_columns(pl.lit(0).alias('position'))
                elif col == 'close':
                    aligned_df = aligned_df.with_columns(pl.lit(0.0).alias('close'))

        # Sort by date
        aligned_df = aligned_df.sort('date')

        aligned_dfs[strategy_id] = aligned_df

    return aligned_dfs
```

## Strategy Processing

### Strategy Factory

```python
class StrategyFactory:
    """Factory for creating strategy processors based on type."""

    @staticmethod
    def create_processor(strategy_config: StrategyConfig) -> 'BaseStrategyProcessor':
        """Create appropriate processor based on strategy type."""
        strategy_type = strategy_config['strategy_type'].upper()

        if strategy_type in ['SMA', 'EMA']:
            return MAStrategyProcessor(strategy_config)
        elif strategy_type == 'MACD':
            return MACDStrategyProcessor(strategy_config)
        elif strategy_type == 'ATR':
            return ATRStrategyProcessor(strategy_config)
        else:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

class BaseStrategyProcessor:
    """Base class for strategy processors."""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self.strategy_id = generate_strategy_id(config)

    def process(self, refresh: bool = False) -> pl.DataFrame:
        """Main processing pipeline."""
        # 1. Get market data
        data = self.get_market_data(refresh)

        # 2. Calculate indicators
        data = self.calculate_indicators(data)

        # 3. Generate signals
        data = self.generate_signals(data)

        # 4. Apply stop losses if configured
        if self.config.get('stop_loss'):
            data = self.apply_stop_loss(data)

        # 5. Calculate expectancy
        expectancy = self.calculate_expectancy(data)

        return data

    @abstractmethod
    def calculate_indicators(self, data: pl.DataFrame) -> pl.DataFrame:
        """Calculate strategy-specific indicators."""
        pass

    @abstractmethod
    def generate_signals(self, data: pl.DataFrame) -> pl.DataFrame:
        """Generate buy/sell signals."""
        pass
```

### MA Strategy Implementation

```python
class MAStrategyProcessor(BaseStrategyProcessor):
    """Moving Average strategy processor."""

    def calculate_indicators(self, data: pl.DataFrame) -> pl.DataFrame:
        """Calculate moving averages."""
        fast_period = self.config['fast_period']
        slow_period = self.config['slow_period']
        ma_type = self.config['strategy_type']

        if ma_type == 'SMA':
            data = data.with_columns([
                pl.col('close').rolling_mean(fast_period).alias('short_ma'),
                pl.col('close').rolling_mean(slow_period).alias('long_ma')
            ])
        elif ma_type == 'EMA':
            data = data.with_columns([
                pl.col('close').ewm_mean(span=fast_period).alias('short_ma'),
                pl.col('close').ewm_mean(span=slow_period).alias('long_ma')
            ])

        return data

    def generate_signals(self, data: pl.DataFrame) -> pl.DataFrame:
        """Generate crossover signals."""
        data = data.with_columns([
            # Signal when short MA crosses above long MA
            ((pl.col('short_ma') > pl.col('long_ma')) &
             (pl.col('short_ma').shift(1) <= pl.col('long_ma').shift(1))).alias('buy_signal'),

            # Signal when short MA crosses below long MA
            ((pl.col('short_ma') < pl.col('long_ma')) &
             (pl.col('short_ma').shift(1) >= pl.col('long_ma').shift(1))).alias('sell_signal')
        ])

        # Generate position column
        data = data.with_columns(
            pl.when(pl.col('buy_signal')).then(1)
            .when(pl.col('sell_signal')).then(0)
            .otherwise(None)
            .forward_fill()
            .fill_null(0)
            .alias('position')
        )

        return data
```

### Synthetic Ticker Processing

```python
def process_synthetic_ticker(ticker: str) -> Dict[str, Any]:
    """
    Process synthetic tickers (e.g., STRK_MSTR).

    Algorithm:
    1. Parse ticker components
    2. Get data for each component
    3. Calculate relative performance
    4. Generate synthetic price series
    """
    if '_' not in ticker:
        return None

    components = ticker.split('_')
    if len(components) != 2:
        return None

    ticker1, ticker2 = components

    # Get data for both components
    data1 = get_data(ticker1)
    data2 = get_data(ticker2)

    # Align dates
    common_dates = set(data1['date']) & set(data2['date'])

    data1_aligned = data1.filter(pl.col('date').is_in(list(common_dates)))
    data2_aligned = data2.filter(pl.col('date').is_in(list(common_dates)))

    # Calculate ratio
    synthetic_data = data1_aligned.join(
        data2_aligned.select(['date', pl.col('close').alias('close2')]),
        on='date'
    ).with_columns(
        (pl.col('close') / pl.col('close2')).alias('synthetic_close')
    ).select(['date', pl.col('synthetic_close').alias('close')])

    return {
        'data': synthetic_data,
        'components': [ticker1, ticker2],
        'type': 'ratio'
    }
```

## Analysis Engine

### Position Analysis

```python
def analyze_positions(aligned_data: Dict[str, pl.DataFrame]) -> Dict[str, Any]:
    """
    Analyze position data for concurrency metrics.

    Returns:
    - position_arrays: Position vectors for correlation
    - activity_periods: Activity statistics per strategy
    - concurrent_periods: Global concurrency data
    """
    strategies = list(aligned_data.keys())

    # Extract position arrays
    position_arrays = {}
    for strategy_id, df in aligned_data.items():
        position_arrays[strategy_id] = df['position'].to_numpy()

    # Calculate activity periods
    activity_periods = {}
    for strategy_id, positions in position_arrays.items():
        active_mask = positions != 0
        activity_periods[strategy_id] = {
            'active': int(np.sum(active_mask)),
            'inactive': int(np.sum(~active_mask)),
            'total': len(positions)
        }

    # Calculate concurrent periods
    concurrent_periods = calculate_concurrent_periods(position_arrays)

    # Add exclusive periods to activity data
    for strategy_id in strategies:
        exclusive_count = 0
        concurrent_count = 0

        positions = position_arrays[strategy_id]
        for i, pos in enumerate(positions):
            if pos != 0:  # Strategy is active
                # Check if any other strategy is active
                other_active = any(
                    position_arrays[other_id][i] != 0
                    for other_id in strategies
                    if other_id != strategy_id
                )

                if other_active:
                    concurrent_count += 1
                else:
                    exclusive_count += 1

        activity_periods[strategy_id]['exclusive'] = exclusive_count
        activity_periods[strategy_id]['concurrent'] = concurrent_count

    return {
        'position_arrays': position_arrays,
        'activity_periods': activity_periods,
        'concurrent_periods': concurrent_periods
    }

def calculate_concurrent_periods(position_arrays: Dict[str, np.ndarray]) -> Dict[str, int]:
    """Calculate global concurrency statistics."""
    if not position_arrays:
        return {'concurrent': 0, 'total': 0}

    # Get array length
    array_length = len(next(iter(position_arrays.values())))

    concurrent_count = 0

    for i in range(array_length):
        # Count active strategies at this time point
        active_count = sum(
            1 for positions in position_arrays.values()
            if positions[i] != 0
        )

        if active_count > 1:
            concurrent_count += 1

    return {
        'concurrent': concurrent_count,
        'total': array_length,
        'ratio': concurrent_count / array_length if array_length > 0 else 0
    }
```

### Risk Metrics Calculation

```python
def calculate_risk_metrics(
    aligned_data: Dict[str, pl.DataFrame],
    allocations: Dict[str, float],
    config: ConcurrencyConfig
) -> Dict[str, Any]:
    """
    Calculate comprehensive risk metrics.

    Metrics calculated:
    - Value at Risk (VaR) at 95% and 99%
    - Conditional Value at Risk (CVaR)
    - Risk contributions per strategy
    - Portfolio volatility
    """
    # Calculate returns for each strategy
    strategy_returns = {}
    for strategy_id, df in aligned_data.items():
        if 'position' in df.columns and 'close' in df.columns:
            returns = calculate_strategy_returns(df)
            strategy_returns[strategy_id] = returns

    # Portfolio returns
    portfolio_returns = calculate_portfolio_returns(strategy_returns, allocations)

    # VaR calculations
    var_95 = np.percentile(portfolio_returns, 5)
    var_99 = np.percentile(portfolio_returns, 1)

    # CVaR calculations
    cvar_95 = np.mean(portfolio_returns[portfolio_returns <= var_95])
    cvar_99 = np.mean(portfolio_returns[portfolio_returns <= var_99])

    # Risk contributions
    risk_contributions = calculate_risk_contributions(
        strategy_returns, allocations, portfolio_returns
    )

    # Portfolio volatility
    portfolio_volatility = np.std(portfolio_returns)

    return {
        'var_95': var_95,
        'var_99': var_99,
        'cvar_95': cvar_95,
        'cvar_99': cvar_99,
        'risk_contributions': risk_contributions,
        'portfolio_volatility': portfolio_volatility,
        'portfolio_returns': portfolio_returns
    }

def calculate_risk_contributions(
    strategy_returns: Dict[str, np.ndarray],
    allocations: Dict[str, float],
    portfolio_returns: np.ndarray
) -> Dict[str, float]:
    """Calculate marginal risk contributions using covariance method."""
    strategies = list(strategy_returns.keys())
    n_strategies = len(strategies)

    if n_strategies <= 1:
        return {strategies[0]: 1.0} if strategies else {}

    # Create return matrix
    return_matrix = np.array([strategy_returns[strategy] for strategy in strategies])

    # Calculate covariance matrix
    cov_matrix = np.cov(return_matrix)

    # Allocation vector
    allocation_vector = np.array([allocations[strategy] for strategy in strategies])

    # Portfolio variance
    portfolio_variance = np.dot(allocation_vector, np.dot(cov_matrix, allocation_vector))

    # Marginal contributions
    marginal_contributions = np.dot(cov_matrix, allocation_vector)

    # Risk contributions
    risk_contributions_array = allocation_vector * marginal_contributions / portfolio_variance

    # Return as dictionary
    return {
        strategies[i]: float(risk_contributions_array[i])
        for i in range(n_strategies)
    }
```

## Optimization Engine

### Permutation Generation

```python
def generate_permutations(
    strategies: List[str],
    min_strategies: int = 3,
    max_permutations: Optional[int] = None
) -> Iterator[List[str]]:
    """
    Generate strategy permutations for optimization.

    Algorithm:
    1. Generate all combinations of size min_strategies to n
    2. Limit total permutations if max_permutations specified
    3. Yield permutations in order of increasing size
    """
    n_strategies = len(strategies)

    if n_strategies < min_strategies:
        return

    total_generated = 0

    for size in range(min_strategies, n_strategies + 1):
        for combination in itertools.combinations(strategies, size):
            if max_permutations and total_generated >= max_permutations:
                return

            yield list(combination)
            total_generated += 1

def optimize_strategy_selection(
    strategies: List[StrategyConfig],
    config: ConcurrencyConfig,
    progress_callback: Callable[[int, int], None] = None
) -> Dict[str, Any]:
    """
    Find optimal strategy subset using permutation analysis.

    Algorithm:
    1. Generate all valid permutations
    2. For each permutation:
       - Run concurrency analysis with equal allocations
       - Calculate efficiency score
    3. Track best permutation
    4. Return optimization results
    """
    strategy_ids = [generate_strategy_id(s) for s in strategies]
    min_strategies = config.get('OPTIMIZE_MIN_STRATEGIES', 3)
    max_permutations = config.get('OPTIMIZE_MAX_PERMUTATIONS')

    best_efficiency = -float('inf')
    best_permutation = None
    best_results = None

    permutations = list(generate_permutations(
        strategy_ids, min_strategies, max_permutations
    ))

    total_permutations = len(permutations)

    for i, permutation in enumerate(permutations):
        # Create subset of strategies
        subset_strategies = [
            s for s in strategies
            if generate_strategy_id(s) in permutation
        ]

        # Run analysis with equal allocations
        subset_config = {**config, 'ALLOCATION_MODE': 'EQUAL'}

        try:
            results = run_concurrency_analysis(subset_strategies, subset_config)
            efficiency = results['portfolio_metrics']['efficiency']['score']

            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_permutation = permutation
                best_results = results

        except Exception as e:
            logger.warning(f"Failed to analyze permutation {permutation}: {e}")
            continue

        # Progress callback
        if progress_callback:
            progress_callback(i + 1, total_permutations)

    return {
        'best_permutation': best_permutation,
        'best_efficiency': best_efficiency,
        'best_results': best_results,
        'total_analyzed': total_permutations
    }
```

### Progress Tracking

```python
class ProgressTracker:
    """Track progress of long-running operations."""

    def __init__(self, total_items: int, operation_name: str = "Processing"):
        self.total_items = total_items
        self.operation_name = operation_name
        self.completed_items = 0
        self.start_time = time.time()
        self.last_update = self.start_time

    def update(self, completed: int):
        """Update progress and estimate remaining time."""
        self.completed_items = completed
        current_time = time.time()

        # Calculate progress
        progress_percent = (completed / self.total_items) * 100

        # Estimate remaining time
        elapsed = current_time - self.start_time
        if completed > 0:
            avg_time_per_item = elapsed / completed
            remaining_items = self.total_items - completed
            estimated_remaining = avg_time_per_item * remaining_items
        else:
            estimated_remaining = 0

        # Log progress (throttled)
        if current_time - self.last_update >= 5.0:  # Every 5 seconds
            logger.info(
                f"{self.operation_name}: {completed}/{self.total_items} "
                f"({progress_percent:.1f}%) - "
                f"ETA: {estimated_remaining:.0f}s"
            )
            self.last_update = current_time

    def complete(self):
        """Mark operation as complete."""
        total_time = time.time() - self.start_time
        logger.info(
            f"{self.operation_name} completed: {self.total_items} items "
            f"in {total_time:.1f}s"
        )
```

## Visualization System

### Chart Generation

```python
def create_strategy_chart(
    aligned_data: Dict[str, pl.DataFrame],
    stats: Dict[str, Any],
    config: ConcurrencyConfig
) -> go.Figure:
    """
    Create comprehensive strategy visualization.

    Chart components:
    1. Price lines for each strategy
    2. Position indicators (long/short)
    3. ATR trailing stops (if applicable)
    4. Concurrency heatmap
    5. Statistics annotation
    """
    strategies = list(aligned_data.keys())
    n_strategies = len(strategies)

    # Create subplots: one per strategy + concurrency heatmap
    fig = make_subplots(
        rows=n_strategies + 1,
        cols=1,
        shared_xaxis=True,
        subplot_titles=strategies + ["Strategy Concurrency"],
        vertical_spacing=0.02
    )

    # Color scheme
    colors = get_color_scheme(n_strategies)

    # Plot each strategy
    for i, (strategy_id, df) in enumerate(aligned_data.items()):
        color = colors[i]

        # Price line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                name=f"{strategy_id} Price",
                line=dict(color=color, width=1),
                hovertemplate=f"{strategy_id}<br>Price: %{{y:.2f}}<br>Date: %{{x}}<extra></extra>"
            ),
            row=i+1, col=1
        )

        # Position indicators
        long_positions = df.filter(pl.col('position') == 1)
        short_positions = df.filter(pl.col('position') == -1)

        if not long_positions.is_empty():
            fig.add_trace(
                go.Scatter(
                    x=long_positions['date'],
                    y=long_positions['close'],
                    mode='markers',
                    name=f"{strategy_id} Long",
                    marker=dict(color='green', size=4, symbol='triangle-up'),
                    hovertemplate="Long Position<br>Price: %{y:.2f}<br>Date: %{x}<extra></extra>"
                ),
                row=i+1, col=1
            )

        if not short_positions.is_empty():
            fig.add_trace(
                go.Scatter(
                    x=short_positions['date'],
                    y=short_positions['close'],
                    mode='markers',
                    name=f"{strategy_id} Short",
                    marker=dict(color='red', size=4, symbol='triangle-down'),
                    hovertemplate="Short Position<br>Price: %{y:.2f}<br>Date: %{x}<extra></extra>"
                ),
                row=i+1, col=1
            )

        # ATR trailing stops (if available)
        if 'atr_stop' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['date'],
                    y=df['atr_stop'],
                    mode='lines',
                    name=f"{strategy_id} ATR Stop",
                    line=dict(color='red', width=1, dash='dot'),
                    hovertemplate="ATR Stop: %{y:.2f}<br>Date: %{x}<extra></extra>"
                ),
                row=i+1, col=1
            )

    # Concurrency heatmap
    concurrency_data = calculate_concurrency_heatmap(aligned_data)

    fig.add_trace(
        go.Heatmap(
            z=[concurrency_data['values']],
            x=concurrency_data['dates'],
            colorscale='Viridis',
            name="Active Strategies",
            hovertemplate="Active Strategies: %{z}<br>Date: %{x}<extra></extra>"
        ),
        row=n_strategies + 1, col=1
    )

    # Add statistics annotation
    stats_text = format_statistics_text(stats)
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=10, family="monospace"),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )

    # Update layout
    fig.update_layout(
        height=200 * (n_strategies + 1),
        title="Strategy Concurrency Analysis",
        showlegend=True
    )

    return fig

def calculate_concurrency_heatmap(aligned_data: Dict[str, pl.DataFrame]) -> Dict[str, Any]:
    """Calculate concurrency heatmap data."""
    if not aligned_data:
        return {'dates': [], 'values': []}

    # Get common dates
    first_df = next(iter(aligned_data.values()))
    dates = first_df['date'].to_list()

    # Count active strategies per date
    concurrency_values = []

    for i in range(len(dates)):
        active_count = sum(
            1 for df in aligned_data.values()
            if i < len(df) and df[i, 'position'] != 0
        )
        concurrency_values.append(active_count)

    return {
        'dates': dates,
        'values': concurrency_values
    }
```

## Report Generation

### JSON Report Structure

```python
def generate_concurrency_report(
    stats: Dict[str, Any],
    config: ConcurrencyConfig
) -> Dict[str, Any]:
    """
    Generate comprehensive JSON report.

    Report structure:
    {
        "portfolio_metrics": {
            "concurrency": {...},
            "efficiency": {...},
            "risk": {...},
            "signals": {...}
        },
        "ticker_metrics": {...},  # Optional
        "strategies": [...],      # Optional
        "config": {...}
    }
    """
    report = {
        "portfolio_metrics": generate_portfolio_metrics(stats),
        "config": sanitize_config_for_report(config),
        "generated_at": datetime.now().isoformat(),
        "version": "1.0"
    }

    # Optional sections based on configuration
    report_includes = config.get('REPORT_INCLUDES', {})

    if report_includes.get('TICKER_METRICS', True):
        report['ticker_metrics'] = generate_ticker_metrics(stats)

    if report_includes.get('STRATEGIES', True):
        report['strategies'] = generate_strategy_details(stats)

    if report_includes.get('STRATEGY_RELATIONSHIPS', True):
        report['strategy_relationships'] = generate_relationship_metrics(stats)

    return report

def generate_portfolio_metrics(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Generate portfolio-level metrics section."""
    return {
        "concurrency": {
            "concurrent_periods": {
                "value": stats['concurrent_periods']['concurrent'],
                "description": "Number of periods with multiple active strategies"
            },
            "concurrent_ratio": {
                "value": stats['concurrent_periods']['ratio'],
                "description": "Proportion of periods with concurrent trading"
            },
            "total_periods": {
                "value": stats['concurrent_periods']['total'],
                "description": "Total number of time periods analyzed"
            }
        },
        "efficiency": {
            "score": {
                "value": stats['portfolio_efficiency']['efficiency_score'],
                "description": "Overall portfolio efficiency score"
            },
            "weighted_efficiency": {
                "value": stats['portfolio_efficiency']['total_weighted_efficiency'],
                "description": "Risk-adjusted efficiency weighted by allocations"
            },
            "expectancy": {
                "value": stats['portfolio_expectancy'],
                "description": "Portfolio-wide expected return per trade"
            }
        },
        "risk": {
            "var_95": {
                "value": stats['risk_metrics']['var_95'],
                "description": "Value at Risk at 95% confidence level"
            },
            "var_99": {
                "value": stats['risk_metrics']['var_99'],
                "description": "Value at Risk at 99% confidence level"
            },
            "cvar_95": {
                "value": stats['risk_metrics']['cvar_95'],
                "description": "Conditional Value at Risk at 95% confidence"
            },
            "portfolio_volatility": {
                "value": stats['risk_metrics']['portfolio_volatility'],
                "description": "Portfolio return volatility"
            }
        },
        "signals": generate_signal_metrics(stats)
    }
```

### Custom JSON Encoder

```python
class ConcurrencyJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for concurrency analysis results."""

    def default(self, obj):
        """Handle special types in JSON serialization."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        else:
            return super().default(obj)
```

## Performance Optimizations

### Data Processing Optimizations

```python
# Use Polars for high-performance dataframe operations
def optimize_dataframe_operations():
    """
    Polars optimizations:
    1. Lazy evaluation for complex queries
    2. Vectorized operations for calculations
    3. Efficient memory usage
    4. Parallel processing where applicable
    """

    # Example: Lazy evaluation for signal generation
    lazy_df = pl.scan_csv("price_data.csv")

    result = (
        lazy_df
        .with_columns([
            pl.col('close').rolling_mean(10).alias('short_ma'),
            pl.col('close').rolling_mean(20).alias('long_ma')
        ])
        .with_columns([
            (pl.col('short_ma') > pl.col('long_ma')).alias('signal')
        ])
        .filter(pl.col('signal') == True)
        .collect()
    )

# Vectorized correlation calculations
def vectorized_correlations(position_matrix: np.ndarray) -> np.ndarray:
    """Use numpy's optimized correlation function."""
    return np.corrcoef(position_matrix)

# Efficient permutation generation
def memory_efficient_permutations(strategies: List[str], batch_size: int = 1000):
    """Generate permutations in batches to manage memory."""
    for i in range(0, len(strategies), batch_size):
        batch = strategies[i:i + batch_size]
        yield from itertools.combinations(batch, min(len(batch), 3))
```

### Caching Strategy

```python
class AnalysisCache:
    """Cache expensive calculations for reuse."""

    def __init__(self):
        self._cache = {}
        self._timestamps = {}

    def get_cached_result(self, key: str, max_age: int = 3600) -> Optional[Any]:
        """Get cached result if still valid."""
        if key not in self._cache:
            return None

        timestamp = self._timestamps.get(key, 0)
        if time.time() - timestamp > max_age:
            # Cache expired
            del self._cache[key]
            del self._timestamps[key]
            return None

        return self._cache[key]

    def cache_result(self, key: str, result: Any):
        """Cache a result with timestamp."""
        self._cache[key] = result
        self._timestamps[key] = time.time()

    def generate_cache_key(self, strategy_config: StrategyConfig, data_hash: str) -> str:
        """Generate cache key from strategy configuration and data."""
        config_str = json.dumps(strategy_config, sort_keys=True)
        return hashlib.md5(f"{config_str}_{data_hash}".encode()).hexdigest()

# Global cache instance
analysis_cache = AnalysisCache()
```

## Integration Points

### FastAPI Integration

```python
from fastapi import APIRouter, HTTPException
from app.concurrency.review import run_concurrency_review

router = APIRouter(prefix="/concurrency", tags=["concurrency"])

@router.post("/analyze")
async def analyze_portfolio(
    portfolio_name: str,
    config: Optional[Dict[str, Any]] = None
):
    """Run concurrency analysis via API."""
    try:
        results = run_concurrency_review(portfolio_name, config or {})
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolios")
async def list_portfolios():
    """List available portfolios for analysis."""
    portfolio_dir = Path("json/concurrency")
    portfolios = [
        f.stem for f in portfolio_dir.glob("*.json")
        if not f.name.startswith(".")
    ]
    return {"portfolios": portfolios}
```

### Command Line Interface

```python
def main():
    """Command line interface for concurrency analysis."""
    parser = argparse.ArgumentParser(description="Strategy Concurrency Analysis")

    parser.add_argument("portfolio", help="Portfolio name to analyze")
    parser.add_argument("--optimize", action="store_true", help="Run optimization")
    parser.add_argument("--visualize", action="store_true", help="Generate charts")
    parser.add_argument("--refresh", action="store_true", help="Refresh data")
    parser.add_argument("--config", help="Configuration file path")

    args = parser.parse_args()

    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)

    # Apply command line overrides
    if args.optimize:
        config['OPTIMIZE'] = True
    if args.visualize:
        config['VISUALIZATION'] = True
    if args.refresh:
        config['REFRESH'] = True

    # Run analysis
    try:
        results = run_concurrency_review(args.portfolio, config)
        logger.info("Analysis completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## Testing Framework

### Unit Tests Structure

```python
class TestConcurrencyAnalysis(unittest.TestCase):
    """Test suite for concurrency analysis."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_strategies = [
            create_ma_strategy("BTC-USD", "SMA", 10, 20, 30),
            create_ma_strategy("ETH-USD", "EMA", 12, 26, 35),
        ]
        self.test_config = {
            "PORTFOLIO": "test_portfolio.json",
            "BASE_DIR": "./test_logs",
            "REFRESH": False,
            "VISUALIZATION": False
        }

    def test_correlation_calculation(self):
        """Test correlation matrix calculation."""
        position_arrays = {
            "strategy1": np.array([1, 0, 1, 0, 1]),
            "strategy2": np.array([0, 1, 0, 1, 0])
        }

        correlation_matrix = calculate_correlations(position_arrays)

        # Should be perfectly negatively correlated
        self.assertAlmostEqual(correlation_matrix[0, 1], -1.0, places=5)

    def test_efficiency_calculation(self):
        """Test efficiency score calculation."""
        # Test data with known expected results
        diversification = 0.8
        independence = 0.6
        activity = 0.7

        expected_efficiency = diversification * independence * activity

        calculated_efficiency = calculate_strategy_efficiency(
            "test_strategy",
            correlation_matrix=np.array([[1.0, 0.2], [0.2, 1.0]]),
            activity_data={
                "test_strategy": {
                    "active": 70,
                    "inactive": 30,
                    "exclusive": 40,
                    "concurrent": 30
                }
            },
            strategy_index=0,
            strategies=["test_strategy", "other_strategy"]
        )

        self.assertAlmostEqual(calculated_efficiency, expected_efficiency, places=3)

    def test_permutation_optimization(self):
        """Test permutation optimization logic."""
        strategies = ["A", "B", "C", "D"]
        permutations = list(generate_permutations(strategies, min_strategies=3))

        # Should generate C(4,3) + C(4,4) = 4 + 1 = 5 permutations
        self.assertEqual(len(permutations), 5)

        # All permutations should have at least 3 strategies
        for perm in permutations:
            self.assertGreaterEqual(len(perm), 3)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete analysis pipeline."""

    def test_end_to_end_analysis(self):
        """Test complete analysis pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test portfolio
            test_portfolio = create_test_portfolio()
            portfolio_path = Path(temp_dir) / "test_portfolio.json"

            with open(portfolio_path, 'w') as f:
                json.dump(test_portfolio, f)

            # Run analysis
            config = {
                "PORTFOLIO": str(portfolio_path),
                "BASE_DIR": temp_dir,
                "REFRESH": False,
                "VISUALIZATION": False
            }

            results = run_concurrency_review("test_portfolio", config)

            # Verify results structure
            self.assertIn("portfolio_metrics", results)
            self.assertIn("efficiency", results["portfolio_metrics"])
            self.assertIn("risk", results["portfolio_metrics"])
```

### Performance Tests

```python
class TestPerformance(unittest.TestCase):
    """Performance benchmarks for concurrency analysis."""

    def test_large_portfolio_performance(self):
        """Test performance with large portfolio."""
        # Create portfolio with 50 strategies
        large_portfolio = create_large_test_portfolio(50)

        start_time = time.time()
        results = run_concurrency_analysis(large_portfolio, test_config)
        end_time = time.time()

        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 300)  # 5 minutes max

        # Results should be valid
        self.assertIsNotNone(results)
        self.assertIn("portfolio_metrics", results)

    def test_optimization_scalability(self):
        """Test optimization performance scaling."""
        for n_strategies in [5, 10, 15]:
            strategies = create_test_strategies(n_strategies)

            start_time = time.time()
            optimization_results = optimize_strategy_selection(
                strategies,
                {"OPTIMIZE_MAX_PERMUTATIONS": 1000}
            )
            end_time = time.time()

            logger.info(f"Optimization with {n_strategies} strategies: {end_time - start_time:.2f}s")

            self.assertIsNotNone(optimization_results)
```

This technical documentation provides a comprehensive overview of the concurrency module's implementation, covering all major components, algorithms, and technical details necessary for understanding, maintaining, and extending the system.
