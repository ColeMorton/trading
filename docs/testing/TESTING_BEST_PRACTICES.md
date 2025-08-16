# Testing Best Practices and Patterns

## Overview

This document provides comprehensive testing best practices and proven patterns for the trading system, covering common scenarios, advanced techniques, and specific guidance for financial applications.

## Fundamental Testing Principles

### 1. Test Behavior, Not Implementation

#### ❌ Bad: Testing Internal Implementation

```python
def test_internal_method_called():
    """Bad: Testing implementation details."""
    service = PortfolioService()

    with patch.object(service, '_calculate_internal_score') as mock_internal:
        service.calculate_portfolio_score(portfolio_data)

        # This test breaks when internal implementation changes
        mock_internal.assert_called_once_with(portfolio_data)
```

#### ✅ Good: Testing Observable Behavior

```python
def test_portfolio_score_calculation():
    """Good: Testing observable behavior and outcomes."""
    service = PortfolioService()
    portfolio_data = create_test_portfolio(
        returns=[0.10, 0.15, -0.05],
        win_rate=0.65
    )

    score = service.calculate_portfolio_score(portfolio_data)

    # Test the observable outcome
    assert 0.0 <= score <= 1.0
    assert score > 0.5  # Should be positive for profitable portfolio
```

### 2. Make Tests Independent and Isolated

#### ❌ Bad: Tests Depend on Each Other

```python
class TestPortfolioAnalysis:
    portfolio = None  # Shared state

    def test_create_portfolio(self):
        """Bad: Creates shared state."""
        self.portfolio = create_portfolio()
        assert self.portfolio is not None

    def test_analyze_portfolio(self):
        """Bad: Depends on previous test."""
        # This test fails if test_create_portfolio doesn't run first
        analysis = analyze_portfolio(self.portfolio)
        assert analysis.score > 0
```

#### ✅ Good: Independent Tests with Fresh State

```python
class TestPortfolioAnalysis:

    def test_create_portfolio(self):
        """Good: Self-contained test."""
        portfolio = create_portfolio()
        assert portfolio is not None
        assert len(portfolio.trades) > 0

    def test_analyze_portfolio(self):
        """Good: Creates its own test data."""
        portfolio = create_test_portfolio(
            trades=create_sample_trades(count=10)
        )

        analysis = analyze_portfolio(portfolio)
        assert analysis.score > 0
```

### 3. Use Descriptive Test Names

#### ❌ Bad: Vague Test Names

```python
def test_strategy():
    pass

def test_calculation():
    pass

def test_error():
    pass
```

#### ✅ Good: Descriptive Test Names

```python
def test_ma_crossover_strategy_generates_buy_signal_when_fast_crosses_above_slow():
    pass

def test_sharpe_ratio_calculation_handles_zero_standard_deviation_gracefully():
    pass

def test_portfolio_validation_raises_error_for_negative_position_sizes():
    pass
```

## Testing Patterns for Financial Applications

### 1. Financial Calculation Testing

#### Precision and Rounding

```python
def test_portfolio_value_calculation_precision():
    """Test financial calculations with appropriate precision."""
    portfolio = Portfolio([
        Position("AAPL", quantity=100, price=150.12),
        Position("MSFT", quantity=50, price=300.45)
    ])

    total_value = portfolio.calculate_total_value()

    # Use appropriate precision for financial calculations
    expected_value = 100 * 150.12 + 50 * 300.45  # 30034.50
    assert abs(total_value - expected_value) < 0.01

def test_percentage_calculations_handle_edge_cases():
    """Test percentage calculations with edge cases."""
    # Test division by zero
    returns = calculate_percentage_returns([100, 0, 50])
    assert math.isnan(returns[1]) or math.isinf(returns[1])

    # Test very small numbers
    tiny_returns = calculate_percentage_returns([0.0001, 0.0002])
    assert not math.isnan(tiny_returns[0])
    assert abs(tiny_returns[0] - 1.0) < 0.001
```

#### Risk Metrics Testing

```python
def test_value_at_risk_statistical_properties():
    """Test VaR calculation follows statistical properties."""
    returns = np.random.normal(0.001, 0.02, 1000)  # Normal distribution

    var_95 = calculate_var(returns, confidence=0.95)
    var_99 = calculate_var(returns, confidence=0.99)

    # 99% VaR should be more extreme than 95% VaR
    assert var_99 < var_95

    # VaR should be negative for loss measurement
    assert var_95 < 0
    assert var_99 < 0

    # Approximately 5% of returns should exceed 95% VaR
    exceeding_count = sum(1 for r in returns if r < var_95)
    expected_exceeding = len(returns) * 0.05

    # Allow some statistical variation
    assert abs(exceeding_count - expected_exceeding) < expected_exceeding * 0.3
```

### 2. Time Series Data Testing

#### Market Data Validation

```python
def test_market_data_integrity():
    """Test market data follows financial market rules."""
    market_data = load_market_data("AAPL", "2023-01-01", "2023-12-31")

    for _, row in market_data.iterrows():
        # OHLC relationships
        assert row['Low'] <= row['High'], "Low must be <= High"
        assert row['Low'] <= row['Open'] <= row['High'], "Open must be between Low and High"
        assert row['Low'] <= row['Close'] <= row['High'], "Close must be between Low and High"

        # Volume should be non-negative
        assert row['Volume'] >= 0, "Volume cannot be negative"

        # Prices should be positive
        assert row['Open'] > 0, "Prices must be positive"
        assert row['High'] > 0
        assert row['Low'] > 0
        assert row['Close'] > 0

def test_returns_calculation_mathematical_properties():
    """Test returns calculation mathematical properties."""
    prices = [100, 105, 102, 110, 95]
    returns = calculate_returns(prices)

    # Number of returns should be one less than prices
    assert len(returns) == len(prices) - 1

    # Verify calculation accuracy
    expected_returns = [
        (105 - 100) / 100,  # 0.05
        (102 - 105) / 105,  # ~-0.0286
        (110 - 102) / 102,  # ~0.0784
        (95 - 110) / 110    # ~-0.1364
    ]

    for actual, expected in zip(returns, expected_returns):
        assert abs(actual - expected) < 0.0001
```

### 3. Strategy Testing Patterns

#### Signal Generation Testing

```python
def test_moving_average_crossover_signals():
    """Test MA crossover signal generation with known data."""
    # Create test data with known crossover points
    prices = [100, 101, 102, 104, 106, 105, 103, 102, 101, 103, 105, 107]

    strategy = MovingAverageCrossoverStrategy(fast_window=3, slow_window=5)
    signals = strategy.generate_signals(prices)

    # Verify signal timing and accuracy
    buy_signals = [i for i, s in enumerate(signals) if s == 'BUY']
    sell_signals = [i for i, s in enumerate(signals) if s == 'SELL']

    # Should have signals at expected crossover points
    assert len(buy_signals) > 0, "Should generate at least one buy signal"
    assert len(sell_signals) > 0, "Should generate at least one sell signal"

    # Signals should alternate (no consecutive buy/sell)
    previous_signal = None
    for signal in signals:
        if signal in ['BUY', 'SELL']:
            assert signal != previous_signal, "Signals should alternate"
            previous_signal = signal

def test_strategy_parameter_validation():
    """Test strategy parameter validation."""
    # Test invalid parameters
    with pytest.raises(ValueError, match="Fast window must be positive"):
        MovingAverageCrossoverStrategy(fast_window=0, slow_window=20)

    with pytest.raises(ValueError, match="Fast window must be less than slow window"):
        MovingAverageCrossoverStrategy(fast_window=20, slow_window=10)

    with pytest.raises(ValueError, match="Windows must be integers"):
        MovingAverageCrossoverStrategy(fast_window=5.5, slow_window=20)
```

#### Backtesting Validation

```python
def test_backtest_trade_accounting():
    """Test backtest trade accounting accuracy."""
    strategy = SimpleStrategy()
    market_data = create_test_market_data()

    backtest_result = strategy.backtest(market_data, initial_capital=10000)

    # Verify trade accounting
    total_trades = len(backtest_result.trades)
    winning_trades = sum(1 for trade in backtest_result.trades if trade.pnl > 0)
    losing_trades = sum(1 for trade in backtest_result.trades if trade.pnl < 0)

    assert winning_trades + losing_trades <= total_trades

    # Verify P&L calculation
    calculated_pnl = sum(trade.pnl for trade in backtest_result.trades)
    final_capital = backtest_result.final_capital
    initial_capital = backtest_result.initial_capital

    assert abs((final_capital - initial_capital) - calculated_pnl) < 0.01

    # Verify win rate calculation
    expected_win_rate = winning_trades / total_trades if total_trades > 0 else 0
    assert abs(backtest_result.win_rate - expected_win_rate) < 0.001
```

## Advanced Testing Patterns

### 1. Property-Based Testing

#### Using Hypothesis for Financial Properties

```python
from hypothesis import given, strategies as st, assume

@given(
    prices=st.lists(
        st.floats(min_value=1.0, max_value=1000.0),
        min_size=2,
        max_size=100
    )
)
def test_returns_calculation_properties(prices):
    """Property-based test for returns calculation."""
    assume(all(p > 0 for p in prices))  # Ensure positive prices

    returns = calculate_returns(prices)

    # Property: Number of returns = number of prices - 1
    assert len(returns) == len(prices) - 1

    # Property: Returns should be bounded for reasonable price changes
    for ret in returns:
        assert -1 <= ret <= 10  # Max 1000% gain, 100% loss

@given(
    returns=st.lists(
        st.floats(min_value=-0.5, max_value=0.5),
        min_size=10,
        max_size=1000
    ),
    confidence=st.floats(min_value=0.8, max_value=0.99)
)
def test_var_calculation_properties(returns, confidence):
    """Property-based test for VaR calculation."""
    var = calculate_var(returns, confidence)

    # Property: VaR should be a percentile of the distribution
    percentile_rank = sum(1 for r in returns if r <= var) / len(returns)
    expected_rank = 1 - confidence

    # Allow some tolerance for discrete distributions
    assert abs(percentile_rank - expected_rank) < 0.1
```

### 2. Parameterized Testing

#### Testing Multiple Scenarios Efficiently

```python
@pytest.mark.parametrize("fast_window,slow_window,expected_signals", [
    (5, 10, {"min_signals": 1, "max_signals": 10}),
    (10, 20, {"min_signals": 1, "max_signals": 5}),
    (20, 50, {"min_signals": 0, "max_signals": 3}),
])
def test_ma_strategy_signal_frequency(fast_window, slow_window, expected_signals):
    """Test signal frequency for different MA parameters."""
    strategy = MovingAverageCrossoverStrategy(fast_window, slow_window)
    test_data = create_trending_market_data(periods=100)

    signals = strategy.generate_signals(test_data)
    signal_count = sum(1 for s in signals if s in ['BUY', 'SELL'])

    assert expected_signals["min_signals"] <= signal_count <= expected_signals["max_signals"]

@pytest.mark.parametrize("ticker,expected_properties", [
    ("AAPL", {"min_price": 50, "max_price": 300, "min_volume": 1000000}),
    ("BTC-USD", {"min_price": 1000, "max_price": 100000, "min_volume": 100}),
    ("TSLA", {"min_price": 20, "max_price": 500, "min_volume": 5000000}),
])
def test_ticker_data_properties(ticker, expected_properties):
    """Test data properties for different tickers."""
    data = fetch_market_data(ticker, "2023-01-01", "2023-12-31")

    assert data['Close'].min() >= expected_properties["min_price"]
    assert data['Close'].max() <= expected_properties["max_price"]
    assert data['Volume'].min() >= expected_properties["min_volume"]
```

### 3. Mock and Stub Patterns

#### Creating Realistic Financial Mocks

```python
class MockMarketDataProvider:
    """Mock market data provider with realistic behavior."""

    def __init__(self, seed=42):
        self.seed = seed
        np.random.seed(seed)

    def get_historical_data(self, ticker, start_date, end_date):
        """Generate realistic historical data."""
        date_range = pd.date_range(start_date, end_date, freq='D')

        # Generate realistic price series with trend and volatility
        returns = np.random.normal(0.0005, 0.02, len(date_range))
        prices = [100]  # Starting price

        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))

        return pd.DataFrame({
            'Date': date_range,
            'Open': prices,
            'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'Close': prices,
            'Volume': np.random.randint(1000000, 10000000, len(date_range))
        })

@pytest.fixture
def mock_data_provider():
    """Fixture providing mocked data provider."""
    return MockMarketDataProvider(seed=42)

def test_strategy_with_mock_data(mock_data_provider):
    """Test strategy using mocked data provider."""
    with patch('app.data.get_market_data', side_effect=mock_data_provider.get_historical_data):
        strategy = MovingAverageCrossoverStrategy(5, 20)
        result = strategy.backtest("AAPL", "2023-01-01", "2023-12-31")

        assert result.total_return is not None
        assert result.total_trades >= 0
        assert 0 <= result.win_rate <= 1
```

## Testing Anti-Patterns and Common Mistakes

### 1. Avoid Testing Random Behavior

#### ❌ Bad: Non-Deterministic Tests

```python
def test_random_strategy():
    """Bad: Non-deterministic test that can randomly fail."""
    strategy = RandomStrategy()

    # This can randomly fail
    result = strategy.generate_signal()
    assert result in ['BUY', 'SELL']  # What if it returns 'HOLD'?

    # This is unpredictable
    profit = strategy.calculate_expected_profit()
    assert profit > 0  # Random strategy might lose money
```

#### ✅ Good: Deterministic Tests with Controlled Randomness

```python
def test_random_strategy_with_seed():
    """Good: Deterministic test with controlled randomness."""
    strategy = RandomStrategy(seed=42)  # Fixed seed for reproducibility

    # With fixed seed, behavior is predictable
    result = strategy.generate_signal()
    assert result == 'BUY'  # Known result with seed=42

    # Test the distribution over many iterations
    signals = [strategy.generate_signal() for _ in range(1000)]
    buy_ratio = signals.count('BUY') / len(signals)

    # Should be approximately 50% with some tolerance
    assert 0.4 <= buy_ratio <= 0.6
```

### 2. Avoid Overly Complex Test Setup

#### ❌ Bad: Complex, Hard-to-Understand Setup

```python
def test_portfolio_optimization():
    """Bad: Overly complex setup that obscures the test intent."""
    # 50 lines of complex setup
    historical_data = {}
    for ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']:
        data = fetch_complex_data(ticker)
        processed_data = apply_complex_transformations(data)
        normalized_data = normalize_with_complex_algorithm(processed_data)
        historical_data[ticker] = normalized_data

    correlation_matrix = calculate_complex_correlations(historical_data)
    risk_models = build_complex_risk_models(correlation_matrix)
    constraints = create_complex_constraints()

    optimizer = PortfolioOptimizer(risk_models, constraints)

    # The actual test is lost in the complexity
    result = optimizer.optimize(historical_data)
    assert result is not None
```

#### ✅ Good: Simple, Focused Setup

```python
def test_portfolio_optimization():
    """Good: Simple setup with clear test intent."""
    # Simple, clear test data
    portfolio_data = create_test_portfolio([
        {'ticker': 'AAPL', 'expected_return': 0.10, 'volatility': 0.20},
        {'ticker': 'MSFT', 'expected_return': 0.08, 'volatility': 0.15},
        {'ticker': 'GOOGL', 'expected_return': 0.12, 'volatility': 0.25}
    ])

    optimizer = PortfolioOptimizer()

    # Clear test intent
    optimized_weights = optimizer.optimize(portfolio_data, target_return=0.10)

    # Clear assertions
    assert sum(optimized_weights.values()) == pytest.approx(1.0, abs=0.001)
    assert all(weight >= 0 for weight in optimized_weights.values())
    assert optimized_weights['AAPL'] > 0  # Should include AAPL
```

### 3. Avoid Testing Too Many Things at Once

#### ❌ Bad: Testing Multiple Concerns in One Test

```python
def test_complete_trading_system():
    """Bad: Testing too many things at once."""
    # This test does too much
    data = fetch_market_data("AAPL")
    strategy = MovingAverageCrossoverStrategy(5, 20)
    portfolio = Portfolio(initial_capital=10000)
    risk_manager = RiskManager(max_position_size=0.1)
    order_manager = OrderManager()

    # Testing data fetching, strategy logic, portfolio management,
    # risk management, and order execution all in one test
    for price in data:
        signal = strategy.generate_signal(price)
        if signal == 'BUY':
            position_size = risk_manager.calculate_position_size(portfolio)
            order = order_manager.create_buy_order(position_size)
            portfolio.execute_order(order)

    # Hard to determine what failed if this test breaks
    assert portfolio.total_value > 10000
    assert portfolio.total_trades > 0
    assert portfolio.win_rate > 0.5
```

#### ✅ Good: Focused, Single-Responsibility Tests

```python
def test_moving_average_signal_generation():
    """Good: Focused test for signal generation only."""
    strategy = MovingAverageCrossoverStrategy(fast_window=5, slow_window=20)
    prices = create_test_price_series_with_crossover()

    signals = strategy.generate_signals(prices)

    # Test only signal generation logic
    assert signals[15] == 'BUY'  # Known crossover point
    assert signals[25] == 'SELL'  # Known crossover point

def test_risk_manager_position_sizing():
    """Good: Focused test for position sizing only."""
    risk_manager = RiskManager(max_position_size=0.1)
    portfolio = create_test_portfolio(total_value=10000)

    position_size = risk_manager.calculate_position_size(portfolio, "AAPL")

    # Test only position sizing logic
    assert position_size <= 1000  # 10% of portfolio
    assert position_size > 0

def test_portfolio_order_execution():
    """Good: Focused test for order execution only."""
    portfolio = Portfolio(initial_capital=10000)
    order = BuyOrder("AAPL", quantity=10, price=150)

    portfolio.execute_order(order)

    # Test only order execution logic
    assert portfolio.get_position("AAPL").quantity == 10
    assert portfolio.cash == 8500  # 10000 - (10 * 150)
```

## Performance Testing Best Practices

### 1. Benchmark Critical Operations

```python
def test_portfolio_calculation_performance():
    """Test portfolio calculation performance with large dataset."""
    large_portfolio = create_large_test_portfolio(1000_positions)

    start_time = time.time()
    total_value = large_portfolio.calculate_total_value()
    execution_time = time.time() - start_time

    assert total_value > 0
    assert execution_time < 1.0, f"Calculation too slow: {execution_time:.3f}s"

@pytest.mark.benchmark
def test_strategy_signal_generation_benchmark(benchmark):
    """Benchmark strategy signal generation."""
    strategy = MovingAverageCrossoverStrategy(20, 50)
    market_data = create_large_market_dataset(10000_points)

    # Benchmark the signal generation
    result = benchmark(strategy.generate_signals, market_data)

    assert len(result) == len(market_data)
```

### 2. Memory Usage Testing

```python
def test_memory_efficient_data_processing():
    """Test memory efficiency of data processing."""
    import psutil
    import gc

    # Baseline memory
    gc.collect()
    baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024

    # Process large dataset
    large_dataset = create_large_dataset(1_000_000_rows)
    processed_data = process_financial_data(large_dataset)

    # Check memory usage
    current_memory = psutil.Process().memory_info().rss / 1024 / 1024
    memory_growth = current_memory - baseline_memory

    assert len(processed_data) > 0
    assert memory_growth < 500, f"Excessive memory usage: {memory_growth}MB"

    # Cleanup
    del large_dataset, processed_data
    gc.collect()
```

## Testing Documentation and Maintenance

### 1. Test Documentation Standards

```python
def test_complex_financial_calculation():
    """
    Test complex financial calculation with multiple scenarios.

    This test verifies the calculation of risk-adjusted returns using
    the Sharpe ratio formula: (Return - Risk-free rate) / Standard deviation

    Test scenarios:
    1. Normal case with positive returns and volatility
    2. Edge case with zero volatility (handle division by zero)
    3. Edge case with negative returns

    Expected behavior:
    - Should return finite values for normal inputs
    - Should handle zero volatility gracefully (return NaN or infinity)
    - Should work correctly with negative returns
    """
    # Normal case
    returns = [0.05, 0.03, 0.08, -0.02, 0.06]
    risk_free_rate = 0.02

    sharpe = calculate_sharpe_ratio(returns, risk_free_rate)
    assert isinstance(sharpe, float)
    assert not math.isnan(sharpe)

    # Zero volatility case
    constant_returns = [0.05, 0.05, 0.05, 0.05, 0.05]
    sharpe_zero_vol = calculate_sharpe_ratio(constant_returns, risk_free_rate)
    assert math.isinf(sharpe_zero_vol) or math.isnan(sharpe_zero_vol)

    # Negative returns case
    negative_returns = [-0.02, -0.01, -0.03, -0.01, -0.02]
    sharpe_negative = calculate_sharpe_ratio(negative_returns, risk_free_rate)
    assert sharpe_negative < 0
```

### 2. Test Maintenance Guidelines

```python
# Good: Keep tests up-to-date with business logic changes
def test_updated_commission_calculation():
    """Test updated commission structure (updated 2024-01-15)."""
    # Updated to reflect new commission structure
    order = Order("AAPL", quantity=100, price=150)

    commission = calculate_commission(order)

    # New commission structure: $0.005 per share, min $1.00
    expected_commission = max(100 * 0.005, 1.00)
    assert commission == expected_commission

# Good: Version test data when business rules change
@pytest.fixture
def commission_rates_v2():
    """Commission rates effective from 2024-01-15."""
    return {
        'per_share': 0.005,
        'minimum': 1.00,
        'maximum': 50.00,
        'options_multiplier': 0.65
    }
```

This comprehensive guide provides proven patterns and practices for maintaining high-quality, maintainable tests in financial trading systems.
