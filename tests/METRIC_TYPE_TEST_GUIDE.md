# Metric Type Test Suite Documentation

This document provides comprehensive documentation for the metric_type functionality test suite, covering the entire flow from backend data processing through API serialization to frontend display.

## Overview

The metric_type feature allows portfolio analysis results to include classification information about which metric criteria each portfolio represents (e.g., "Most Sharpe Ratio", "Most Total Return [%]", etc.). This test suite ensures the feature works correctly across all layers of the application.

## Test Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Coverage Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Backend Tests          API Layer          Frontend Tests   │
│  ┌─────────────┐       ┌─────────┐        ┌──────────────┐  │
│  │ Pydantic    │──────▶│ FastAPI │◀──────│ API Service  │  │
│  │ Models      │       │ Router  │       │ (TypeScript) │  │
│  └─────────────┘       └─────────┘       └──────────────┘  │
│  ┌─────────────┐                         ┌──────────────┐  │
│  │ Service     │                         │ React Hooks  │  │
│  │ Layer       │                         │ (useParam..) │  │
│  └─────────────┘                         └──────────────┘  │
│                                          ┌──────────────┐  │
│                    E2E Tests             │ Components   │  │
│                  ┌─────────────┐         │ (ResultsTable│  │
│                  │ Integration │         │ .tsx)        │  │
│                  │ Flow Tests  │         └──────────────┘  │
│                  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Test Files Structure

```
tests/
├── api/
│   ├── test_metric_type_models.py     # Pydantic model tests
│   ├── test_metric_type_service.py    # Service layer tests
│   └── test_metric_type_router.py     # FastAPI router tests
├── e2e/
│   └── test_metric_type_integration.py # End-to-end tests
├── run_metric_type_tests.py           # Test runner script
└── METRIC_TYPE_TEST_GUIDE.md          # This documentation

app/frontend/sensylate/src/
├── services/__tests__/
│   └── maCrossApi.test.ts             # API service tests
├── hooks/__tests__/
│   └── useParameterTesting.test.ts    # Hook tests
└── components/__tests__/
    └── ResultsTable.test.tsx          # Component tests
```

## Backend Tests

### 1. Pydantic Model Tests (`test_metric_type_models.py`)

**Purpose**: Verify that the `PortfolioMetrics` model correctly handles the `metric_type` field.

**Key Test Cases**:

- ✅ `metric_type` field exists and is properly typed
- ✅ Default value handling (empty string)
- ✅ `None` value conversion to empty string
- ✅ `model_dump()` includes `metric_type` field
- ✅ `exclude_none=False` preserves empty `metric_type`
- ✅ Complex metric type values (comma-separated, special characters)
- ✅ Round-trip serialization/deserialization

**Example Test**:

```python
def test_metric_type_field_exists(self):
    portfolio = PortfolioMetrics(
        ticker="TEST",
        strategy_type="SMA",
        # ... other fields ...
        metric_type="Most Total Return [%]"
    )

    assert hasattr(portfolio, 'metric_type')
    assert portfolio.metric_type == "Most Total Return [%]"
```

### 2. Service Layer Tests (`test_metric_type_service.py`)

**Purpose**: Verify that the MA Cross service correctly extracts and preserves `metric_type` from portfolio dictionaries.

**Key Test Cases**:

- ✅ `PortfolioMetrics` creation with `metric_type` from dict
- ✅ Missing `metric_type` handling in portfolio dict
- ✅ Full analysis flow preserves `metric_type`
- ✅ Multiple portfolios with different `metric_type` values
- ✅ Deduplication logic preserves `metric_type`

**Example Test**:

```python
def test_portfolio_metrics_creation_with_metric_type(self, sample_portfolio_dict_with_metric_type):
    portfolio_dict = sample_portfolio_dict_with_metric_type

    metrics = PortfolioMetrics(
        ticker=portfolio_dict.get("Ticker", ""),
        # ... other field mappings ...
        metric_type=portfolio_dict.get("Metric Type")
    )

    assert metrics.metric_type == "Most Sharpe Ratio, Most Total Return [%]"
```

### 3. API Router Tests (`test_metric_type_router.py`)

**Purpose**: Verify that FastAPI router endpoints correctly serialize and return `metric_type` in responses.

**Key Test Cases**:

- ✅ Synchronous analysis includes `metric_type` in response
- ✅ Asynchronous status endpoint includes `metric_type` in results
- ✅ `response_model_exclude_none=False` preserves empty `metric_type`
- ✅ Multiple portfolios with different `metric_type` values
- ✅ Serialization consistency across different paths

**Example Test**:

```python
@patch('app.api.routers.ma_cross.get_ma_cross_service')
def test_analyze_sync_includes_metric_type(self, mock_get_service, client, sample_portfolio_metrics_with_metric_type):
    # Mock service and response...
    response = client.post("/api/ma-cross/analyze", json={
        "ticker": "BTC-USD",
        "windows": 10,
        "async_execution": False
    })

    assert response.status_code == 200
    data = response.json()
    portfolio = data["portfolios"][0]
    assert "metric_type" in portfolio
    assert portfolio["metric_type"] == "Most Sharpe Ratio, Most Total Return [%]"
```

## Frontend Tests

### 4. API Service Tests (`maCrossApi.test.ts`)

**Purpose**: Verify that the frontend API service correctly handles `metric_type` in requests and responses.

**Key Test Cases**:

- ✅ `PortfolioMetrics` interface includes `metric_type` field
- ✅ `portfolioToResult` transformation preserves `metric_type`
- ✅ `getStatus` API call preserves `metric_type`
- ✅ Cache functionality works with `metric_type`
- ✅ Complex and undefined `metric_type` values

**Example Test**:

```typescript
it('should preserve metric_type when transforming portfolio to result', () => {
  const portfolio: PortfolioMetrics = {
    ticker: 'BTC-USD',
    strategy_type: 'EMA',
    // ... other fields ...
    metric_type: 'Most Omega Ratio, Most Sharpe Ratio',
  };

  const results = maCrossApi.responseToResults(mockSyncResponse);
  expect(results[0].metric_type).toBe('Most Omega Ratio, Most Sharpe Ratio');
});
```

### 5. Hook Tests (`useParameterTesting.test.ts`)

**Purpose**: Verify that the `useParameterTesting` hook correctly maps `metric_type` in both async and sync result processing paths.

**Key Test Cases**:

- ✅ Synchronous analysis preserves `metric_type` via `responseToResults`
- ✅ Asynchronous `status.results` path includes `metric_type`
- ✅ Asynchronous `status.result` path includes `metric_type`
- ✅ Multiple portfolios with different `metric_type` values
- ✅ Undefined/empty `metric_type` handling

**Example Test**:

```typescript
it('should handle async response with metric_type in status.results path', async () => {
  const mockStatusResponse: ExecutionStatusResponse = {
    execution_id: 'test-exec-123',
    status: 'completed',
    results: [
      {
        ticker: 'BTC-USD',
        // ... other fields ...
        metric_type: 'Most Omega Ratio, Most Sharpe Ratio',
      },
    ],
  };

  // ... setup and execution ...

  expect(result.current.results[0].metric_type).toBe(
    'Most Omega Ratio, Most Sharpe Ratio'
  );
});
```

### 6. Component Tests (`ResultsTable.test.tsx`)

**Purpose**: Verify that the `ResultsTable` component correctly displays `metric_type` in expandable row details.

**Key Test Cases**:

- ✅ Expandable row functionality with `metric_type`
- ✅ `metric_type` displayed as badges when expanded
- ✅ Single and multiple comma-separated metric types
- ✅ Empty/undefined `metric_type` graceful handling
- ✅ CSS classes and styling for badges
- ✅ Multiple rows with different `metric_type` values

**Example Test**:

```typescript
it('should expand row and show metric_type as badges when clicked', () => {
  render(<ResultsTable results={[sampleResultWithMetricType]} />);

  const expandButton = screen.getByTitle('Expand details');
  fireEvent.click(expandButton);

  expect(screen.getByText('Metric Type:')).toBeInTheDocument();
  expect(screen.getByText('Most Sharpe Ratio')).toBeInTheDocument();
  expect(screen.getByText('Most Total Return [%]')).toBeInTheDocument();

  const badges = screen.getAllByClassName('badge bg-primary text-white');
  expect(badges).toHaveLength(2);
});
```

## End-to-End Tests

### 7. Integration Tests (`test_metric_type_integration.py`)

**Purpose**: Verify the complete `metric_type` flow from backend processing through API responses to frontend consumption.

**Key Test Cases**:

- ✅ Synchronous analysis complete flow
- ✅ Asynchronous analysis complete flow
- ✅ Consistency across different endpoints
- ✅ Different ticker and strategy configurations
- ✅ Serialization format consistency
- ✅ Error scenario handling
- ✅ Performance impact assessment

**Example Test**:

```python
def test_sync_analysis_metric_type_flow(self, client):
    response = client.post("/api/ma-cross/analyze", json={
        "ticker": "BTC-USD",
        "windows": 10,
        "strategy_types": ["EMA"],
        "async_execution": False,
        "refresh": True
    })

    assert response.status_code == 200
    data = response.json()
    portfolios = data.get("portfolios", [])

    portfolios_with_metric_type = [
        p for p in portfolios
        if "metric_type" in p and p["metric_type"]
    ]

    assert len(portfolios_with_metric_type) > 0
```

## Running the Tests

### Quick Start

```bash
# Run all tests
python tests/run_metric_type_tests.py

# Run with verbose output
python tests/run_metric_type_tests.py --verbose

# Run only backend tests
python tests/run_metric_type_tests.py --backend-only

# Run only frontend tests
python tests/run_metric_type_tests.py --frontend-only

# Run only end-to-end tests
python tests/run_metric_type_tests.py --e2e-only

# Run with coverage reporting
python tests/run_metric_type_tests.py --coverage
```

### Prerequisites

**Backend Tests**:

- Python 3.8+
- pytest
- All backend dependencies installed (`pip install -r requirements.txt`)

**Frontend Tests**:

- Node.js 16+
- npm or yarn
- Jest testing framework
- Frontend dependencies installed (`npm install`)

**End-to-End Tests**:

- API server running (`python -m app.api.run`)
- Both backend and frontend dependencies

### Individual Test Execution

```bash
# Backend tests
python -m pytest tests/api/test_metric_type_models.py -v
python -m pytest tests/api/test_metric_type_service.py -v
python -m pytest tests/api/test_metric_type_router.py -v

# Frontend tests (from frontend directory)
cd app/frontend/sensylate
npm test -- src/services/__tests__/maCrossApi.test.ts --watchAll=false
npm test -- src/hooks/__tests__/useParameterTesting.test.ts --watchAll=false
npm test -- src/components/__tests__/ResultsTable.test.tsx --watchAll=false

# End-to-end tests
python -m pytest tests/e2e/test_metric_type_integration.py -v
```

## Test Data and Scenarios

### Metric Type Format Examples

The tests cover various `metric_type` format scenarios:

```
Single metric:
"Most Sharpe Ratio"

Multiple metrics:
"Most Sharpe Ratio, Most Total Return [%]"

Complex metrics:
"Most Omega Ratio, Most Sharpe Ratio, Most Sortino Ratio, Most Total Return [%], Median Total Trades"

Special characters:
"Most Total Return [%]"
"Mean Avg Winning Trade [%]"

Edge cases:
""                    # Empty string
null/undefined        # Missing data
"   "                 # Whitespace only
"Valid, , , Valid"    # Empty comma values
```

### Test Portfolio Data

The tests use realistic portfolio data with:

- Various tickers (BTC-USD, ETH-USD, AAPL, etc.)
- Different strategy types (EMA, SMA)
- Realistic financial metrics
- Different window combinations
- Multiple timeframes

## Coverage Areas

The test suite provides comprehensive coverage for:

✅ **Data Modeling**: Pydantic model field definition and serialization
✅ **Data Extraction**: Service layer portfolio dictionary processing
✅ **API Serialization**: FastAPI response formatting and JSON serialization
✅ **Frontend Interfaces**: TypeScript interface definitions
✅ **Data Transformation**: Frontend API service data mapping
✅ **State Management**: React hook result processing
✅ **UI Rendering**: Component display logic and user interaction
✅ **End-to-End Flow**: Complete data flow from backend to UI
✅ **Error Handling**: Edge cases and error scenarios
✅ **Performance**: Impact on analysis and response times

## Troubleshooting

### Common Issues

**Backend Tests Failing**:

- Ensure all Python dependencies are installed
- Check that test data matches expected portfolio dictionary format
- Verify Pydantic model field definitions

**Frontend Tests Failing**:

- Ensure Node.js dependencies are installed (`npm install`)
- Check TypeScript compilation errors
- Verify mock data matches interface definitions

**E2E Tests Failing**:

- Ensure API server is running on port 8000
- Check that test data can be processed by actual backend
- Verify network connectivity and timeouts

### Debug Commands

```bash
# Run with maximum verbosity
python tests/run_metric_type_tests.py --verbose

# Run specific test with debugging
python -m pytest tests/api/test_metric_type_models.py::TestPortfolioMetricsMetricType::test_metric_type_field_exists -v -s

# Check coverage gaps
python tests/run_metric_type_tests.py --coverage

# Frontend test debugging
cd app/frontend/sensylate
npm test -- --verbose --no-coverage
```

## Maintenance

### Adding New Tests

When adding new `metric_type` related functionality:

1. **Backend Changes**: Add tests to appropriate backend test file
2. **API Changes**: Update router tests and integration tests
3. **Frontend Changes**: Add tests to corresponding frontend test file
4. **UI Changes**: Update component tests
5. **Data Flow Changes**: Update end-to-end tests

### Test Data Updates

When portfolio data structure changes:

1. Update sample data in all test files
2. Verify interface definitions match
3. Update mock data generation
4. Run full test suite to verify compatibility

### Performance Monitoring

The test suite includes performance checks:

- Backend analysis execution time
- API response time
- Frontend rendering performance
- Memory usage during large dataset processing

Regular monitoring ensures `metric_type` feature doesn't impact system performance.

## Conclusion

This comprehensive test suite ensures the `metric_type` functionality works reliably across the entire application stack. The tests cover data modeling, processing, serialization, transformation, display, and user interaction, providing confidence that portfolio metric classifications are accurately preserved and displayed throughout the system.

For questions or issues with the test suite, refer to the individual test files for detailed examples and assertions.
