# Remaining Test Failures Analysis - QA Engineering Report

**Date:** October 28, 2025
**Analyst:** DevOps/QA Engineer
**Status:** 4 Failures Identified and Analyzed

---

## Executive Summary

After fixing the SSE proxy tests, **4 tests remain failing** in the API test suite (down from original 5, as we fixed `test_get_user_info_without_auth` with the logout changes).

**Test Suite Status:**

- Total: 113 tests
- Passing: 109 ✅
- Failing: 4 ❌
- Success Rate: 96.5%

---

## Failing Tests Analysis

### ❌ Failure 1 & 2: JobService Constructor Issues

**Tests:**

1. `tests/api/test_job_webhook_integration.py::TestJobWebhookIntegration::test_job_stores_webhook_url`
2. `tests/api/test_job_webhook_integration.py::TestJobWebhookIntegration::test_job_stores_webhook_headers`

**Error:**

```python
TypeError: JobService() takes no arguments
```

**Root Cause:**

The tests try to instantiate `JobService` as a class with constructor arguments:

```python
# tests/api/test_job_webhook_integration.py:34
job_service = JobService(mock_db_manager, mock_redis_manager)  # ❌ Wrong
```

But `JobService` is actually implemented with **static methods only**:

```python
# app/api/services/job_service.py:16
class JobService:
    """Service for managing job records."""

    @staticmethod
    async def create_job(
        db: AsyncSession,          # First parameter is db session
        api_key_id: str,
        command_group: str,
        command_name: str,
        parameters: dict,
        webhook_url: str | None = None,
        webhook_headers: dict | None = None,
    ) -> Job:
```

**Analysis:**

This is a **test design mismatch**. The tests were written expecting `JobService` to be an instance-based service with dependency injection, but it's actually a utility class with static methods.

**Impact:**

- Tests fail to instantiate the service
- Cannot verify webhook storage functionality
- Test coverage gap for webhook integration

**Test Code (Current):**

```python
# Line 34
job_service = JobService(mock_db_manager, mock_redis_manager)

job = await job_service.create_job(
    command_group="strategy",
    command_name="run",
    parameters={"ticker": "AAPL"},
    webhook_url="https://example.com/webhook",
)
```

**Should Be:**

```python
# Static method call, pass db session directly
job = await JobService.create_job(
    db=mock_session,  # Pass session directly
    api_key_id="test-key-id",
    command_group="strategy",
    command_name="run",
    parameters={"ticker": "AAPL"},
    webhook_url="https://example.com/webhook",
)
```

---

### ❌ Failure 3: SeasonalityRunRequest Schema Mismatch

**Test:**
`tests/api/test_webhook_parameters.py::TestWebhookParameters::test_seasonality_run_accepts_webhook_url`

**Error:**

```python
AttributeError: 'SeasonalityRunRequest' object has no attribute 'analysis_type'
```

**Root Cause:**

The test tries to use a field that doesn't exist in the schema:

```python
# tests/api/test_webhook_parameters.py:64
request = SeasonalityRunRequest(
    ticker="ETH-USD",
    analysis_type="monthly",  # ❌ Field doesn't exist
    webhook_url="https://example.com/seasonality-webhook",
)

# Line 69
assert request.analysis_type == "monthly"  # ❌ Attribute doesn't exist
```

But the actual `SeasonalityRunRequest` schema has different fields:

```python
# app/api/models/schemas.py:763
class SeasonalityRunRequest(SQLModel):
    """Request model for seasonality run command."""

    tickers: list[str] | None = Field(None, description="Tickers to analyze")  # ✅ List, not single ticker
    min_years: float = Field(default=3.0, ...)
    time_period: int = Field(default=1, ...)  # Time period, not analysis_type
    confidence_level: float = Field(default=0.95, ...)
    output_format: str = Field(default="csv", ...)
    detrend: bool = Field(default=True, ...)
    min_sample_size: int = Field(default=10, ...)
    webhook_url: str | None = Field(None, ...)
    webhook_headers: dict[str, str] | None = Field(None, ...)
    # ❌ NO 'analysis_type' field
    # ❌ NO 'ticker' field (uses 'tickers' plural)
```

**Analysis:**

This is a **test outdated with schema evolution**. The test was written with an old version of the schema that had:

- `ticker` (singular) → Now `tickers` (plural list)
- `analysis_type` → Now uses `time_period` instead

**Impact:**

- Test cannot instantiate schema (Pydantic validation fails)
- Cannot verify webhook URL acceptance for seasonality
- Test coverage gap for seasonality webhook params

**Current Test Code:**

```python
request = SeasonalityRunRequest(
    ticker="ETH-USD",              # ❌ Wrong field name
    analysis_type="monthly",        # ❌ Field doesn't exist
    webhook_url="https://example.com/seasonality-webhook",
)
assert request.analysis_type == "monthly"  # ❌ Wrong field
```

**Should Be:**

```python
request = SeasonalityRunRequest(
    tickers=["ETH-USD"],           # ✅ Correct field (plural, list)
    time_period=30,                # ✅ Use time_period instead of analysis_type
    webhook_url="https://example.com/seasonality-webhook",
)
assert request.tickers == ["ETH-USD"]
assert request.time_period == 30
```

---

### ❌ Failure 4: ConcurrencyAnalyzeRequest Schema Mismatch

**Test:**
`tests/api/test_webhook_parameters.py::TestWebhookParameters::test_concurrency_analyze_accepts_webhook_url`

**Error:**

```python
AttributeError: 'ConcurrencyAnalyzeRequest' object has no attribute 'method'
```

**Root Cause:**

Similar to the seasonality issue, the test uses a non-existent field:

```python
# tests/api/test_webhook_parameters.py:75
request = ConcurrencyAnalyzeRequest(
    portfolio="data/raw/strategies/portfolio.csv",
    method="pearson",  # ❌ Field doesn't exist
    webhook_url="https://example.com/concurrency-webhook",
)

# Line 80
assert request.method == "pearson"  # ❌ Attribute doesn't exist
```

But the actual `ConcurrencyAnalyzeRequest` schema doesn't have a `method` field:

```python
# app/api/models/schemas.py:484
class ConcurrencyAnalyzeRequest(SQLModel):
    """Request model for concurrency analyze command."""

    portfolio: str = Field(..., description="Portfolio filename (JSON or CSV)")
    profile: str | None = Field(None, ...)
    refresh: bool = Field(default=True, ...)
    initial_value: float | None = Field(None, ...)
    target_var: float | None = Field(None, ...)
    visualization: bool = Field(default=True, ...)
    export_trade_history: bool = Field(default=True, ...)
    memory_optimization: bool = Field(default=False, ...)
    webhook_url: str | None = Field(None, ...)
    webhook_headers: dict[str, str] | None = Field(None, ...)
    # ❌ NO 'method' field
```

**Analysis:**

This is another **test outdated with schema evolution**. The concurrency analyze command doesn't have a user-selectable correlation method parameter in the API schema (it may be handled internally or via the profile).

**Impact:**

- Test cannot instantiate schema
- Cannot verify webhook URL acceptance for concurrency
- Test coverage gap for concurrency webhook params

**Current Test Code:**

```python
request = ConcurrencyAnalyzeRequest(
    portfolio="data/raw/strategies/portfolio.csv",
    method="pearson",  # ❌ Field doesn't exist
    webhook_url="https://example.com/concurrency-webhook",
)
assert request.method == "pearson"  # ❌ Wrong field
```

**Should Be:**

```python
request = ConcurrencyAnalyzeRequest(
    portfolio="data/raw/strategies/portfolio.csv",
    # Remove method parameter - not part of schema
    webhook_url="https://example.com/concurrency-webhook",
)
assert request.portfolio == "data/raw/strategies/portfolio.csv"
assert request.webhook_url == "https://example.com/concurrency-webhook"
```

---

## Summary of Issues

| Test                                           | Error Type     | Root Cause              | Severity |
| ---------------------------------------------- | -------------- | ----------------------- | -------- |
| `test_job_stores_webhook_url`                  | TypeError      | JobService API mismatch | HIGH     |
| `test_job_stores_webhook_headers`              | TypeError      | JobService API mismatch | HIGH     |
| `test_seasonality_run_accepts_webhook_url`     | AttributeError | Outdated schema fields  | MEDIUM   |
| `test_concurrency_analyze_accepts_webhook_url` | AttributeError | Outdated schema fields  | MEDIUM   |

---

## Recommended Fixes

### Fix 1: Update JobService Tests (2 tests)

**File:** `tests/api/test_job_webhook_integration.py`

**Change Pattern:**

```python
# ❌ Before
job_service = JobService(mock_db_manager, mock_redis_manager)
job = await job_service.create_job(...)

# ✅ After
job = await JobService.create_job(
    db=mock_session,
    api_key_id="test-api-key-id",
    ...
)
```

**Implementation:**

1. Remove service instantiation
2. Call static methods directly
3. Pass mock db session as first parameter
4. Add required `api_key_id` parameter

### Fix 2: Update Seasonality Schema Test (1 test)

**File:** `tests/api/test_webhook_parameters.py`

**Change:**

```python
# ❌ Before
request = SeasonalityRunRequest(
    ticker="ETH-USD",
    analysis_type="monthly",
    webhook_url="...",
)
assert request.analysis_type == "monthly"

# ✅ After
request = SeasonalityRunRequest(
    tickers=["ETH-USD"],  # Changed to plural list
    time_period=30,        # Changed from analysis_type
    webhook_url="...",
)
assert request.tickers == ["ETH-USD"]
assert request.webhook_url == "..."  # Test the important part
```

### Fix 3: Update Concurrency Schema Test (1 test)

**File:** `tests/api/test_webhook_parameters.py`

**Change:**

```python
# ❌ Before
request = ConcurrencyAnalyzeRequest(
    portfolio="...",
    method="pearson",
    webhook_url="...",
)
assert request.method == "pearson"

# ✅ After
request = ConcurrencyAnalyzeRequest(
    portfolio="...",
    # Remove method parameter
    webhook_url="...",
)
assert request.portfolio == "..."
assert request.webhook_url == "..."  # Test the important part
```

---

## Testing Priority

### P0 - Critical (JobService tests)

These tests validate core webhook integration functionality:

- Webhook URL storage in database
- Webhook headers serialization
- Job creation flow

**Impact if not fixed:** Cannot verify webhook integration works correctly

### P1 - High (Schema validation tests)

These tests validate API request schemas accept webhook parameters:

- Webhook URL acceptance
- Parameter validation

**Impact if not fixed:** Cannot verify webhook parameters accepted across all endpoints

---

## Estimated Effort

| Fix                     | Complexity | Time       | Risk    |
| ----------------------- | ---------- | ---------- | ------- |
| JobService tests        | Medium     | 15 min     | Low     |
| Seasonality schema test | Low        | 5 min      | Low     |
| Concurrency schema test | Low        | 5 min      | Low     |
| **Total**               |            | **25 min** | **Low** |

---

## Implementation Steps

### Step 1: Fix JobService Tests

1. Read current `JobService` implementation to understand static method signatures
2. Update test to call static methods with correct parameters
3. Add required `api_key_id` parameter to test
4. Verify webhook URL and headers are properly tested

### Step 2: Fix Schema Tests

1. Update field names to match current schemas
2. Remove non-existent fields
3. Add assertions for fields that actually exist
4. Verify webhook_url acceptance (the main goal of these tests)

### Step 3: Run All Tests

```bash
poetry run pytest tests/api/ -v
```

Expected: **113/113 PASSED** ✅

---

## Risk Assessment

**Low Risk** - These are isolated test fixes that:

- Don't modify production code
- Only update test expectations to match current implementation
- Improve test coverage accuracy

**Benefits:**

- ✅ Complete test suite passing
- ✅ Accurate webhook integration validation
- ✅ Up-to-date schema validation
- ✅ Better confidence in production code

---

## Root Cause Categories

### 1. **API Evolution** (3 failures)

- Schema fields changed during development
- Tests not updated to match schema evolution
- Common in agile development with rapid iteration

### 2. **Design Pattern Mismatch** (2 failures)

- Tests assumed instance-based service pattern
- Actual implementation uses static utility pattern
- Tests need to match actual architecture

---

## Prevention Strategies

### For Future Development:

1. **Schema Version Tracking**

   - Document schema changes in migration notes
   - Update related tests when schemas change
   - Use schema validation in CI/CD

2. **API Contract Testing**

   - Validate request/response schemas against OpenAPI spec
   - Auto-generate tests from OpenAPI definitions
   - Catch schema drift early

3. **Test Maintenance**

   - Regular test audits for outdated assumptions
   - Link tests to schema definitions
   - Run full suite on schema changes

4. **Static Analysis**
   - Use type checkers to catch attribute access errors
   - Validate Pydantic models in tests
   - CI checks for schema compatibility

---

## Detailed Fix Specifications

### Fix 1: test_job_stores_webhook_url

**Location:** `tests/api/test_job_webhook_integration.py` line 21-52

**Current Code:**

```python
async def test_job_stores_webhook_url(self):
    # Mock database manager
    mock_db_manager = Mock()
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_db_manager.get_async_session.return_value = mock_session

    # Mock Redis manager
    mock_redis_manager = Mock()
    mock_redis_manager.enqueue_job = AsyncMock(return_value="task-id-123")

    job_service = JobService(mock_db_manager, mock_redis_manager)  # ❌ TypeError

    # Create job with webhook URL
    with patch("app.api.services.job_service.Job") as MockJob:
        mock_job = Mock(spec=Job)
        mock_job.id = "test-job-123"
        mock_job.status = JobStatus.PENDING
        mock_job.webhook_url = "https://example.com/webhook"
        MockJob.return_value = mock_job

        job = await job_service.create_job(
            command_group="strategy",
            command_name="run",
            parameters={"ticker": "AAPL"},
            webhook_url="https://example.com/webhook",
        )

        # Verify webhook URL was set
        assert job.webhook_url == "https://example.com/webhook"
```

**Fixed Code:**

```python
async def test_job_stores_webhook_url(self):
    # Mock database session
    mock_session = AsyncMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_session.add = Mock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Create job with webhook URL using static method
    with patch("app.api.services.job_service.Job") as MockJob:
        mock_job = Mock(spec=Job)
        mock_job.id = "test-job-123"
        mock_job.status = JobStatus.PENDING
        mock_job.webhook_url = "https://example.com/webhook"
        MockJob.return_value = mock_job

        # ✅ Call static method directly
        job = await JobService.create_job(
            db=mock_session,
            api_key_id="test-api-key-id",
            command_group="strategy",
            command_name="run",
            parameters={"ticker": "AAPL"},
            webhook_url="https://example.com/webhook",
        )

        # Verify webhook URL was set
        assert job.webhook_url == "https://example.com/webhook"
```

**Changes:**

1. Remove `JobService` instantiation
2. Call `JobService.create_job()` as static method
3. Pass `db=mock_session` directly
4. Add required `api_key_id` parameter
5. Simplify mock setup (no need for db_manager/redis_manager)

---

### Fix 2: test_job_stores_webhook_headers

**Location:** `tests/api/test_job_webhook_integration.py` line 54-94

**Same pattern as Fix 1:**

- Remove service instantiation
- Call static method
- Pass session directly
- Add api_key_id

---

### Fix 3: test_seasonality_run_accepts_webhook_url

**Location:** `tests/api/test_webhook_parameters.py` line 60-69

**Current Code:**

```python
def test_seasonality_run_accepts_webhook_url(self):
    """Test that SeasonalityRunRequest accepts optional webhook_url."""
    request = SeasonalityRunRequest(
        ticker="ETH-USD",                    # ❌ Wrong field name
        analysis_type="monthly",             # ❌ Field doesn't exist
        webhook_url="https://example.com/seasonality-webhook",
    )

    assert request.webhook_url == "https://example.com/seasonality-webhook"
    assert request.analysis_type == "monthly"  # ❌ Field doesn't exist
```

**Fixed Code:**

```python
def test_seasonality_run_accepts_webhook_url(self):
    """Test that SeasonalityRunRequest accepts optional webhook_url."""
    request = SeasonalityRunRequest(
        tickers=["ETH-USD"],                 # ✅ Correct field (plural list)
        time_period=30,                      # ✅ Valid field (30 days = monthly)
        webhook_url="https://example.com/seasonality-webhook",
    )

    assert request.webhook_url == "https://example.com/seasonality-webhook"
    assert request.tickers == ["ETH-USD"]
    assert request.time_period == 30
```

**Changes:**

1. Change `ticker` → `tickers` (list)
2. Change `analysis_type` → `time_period` (int)
3. Update assertions to match actual schema fields

---

### Fix 4: test_concurrency_analyze_accepts_webhook_url

**Location:** `tests/api/test_webhook_parameters.py` line 71-80

**Current Code:**

```python
def test_concurrency_analyze_accepts_webhook_url(self):
    """Test that ConcurrencyAnalyzeRequest accepts optional webhook_url."""
    request = ConcurrencyAnalyzeRequest(
        portfolio="data/raw/strategies/portfolio.csv",
        method="pearson",  # ❌ Field doesn't exist
        webhook_url="https://example.com/concurrency-webhook",
    )

    assert request.webhook_url == "https://example.com/concurrency-webhook"
    assert request.method == "pearson"  # ❌ Field doesn't exist
```

**Fixed Code:**

```python
def test_concurrency_analyze_accepts_webhook_url(self):
    """Test that ConcurrencyAnalyzeRequest accepts optional webhook_url."""
    request = ConcurrencyAnalyzeRequest(
        portfolio="data/raw/strategies/portfolio.csv",
        # Remove method parameter - handled via profile or internally
        webhook_url="https://example.com/concurrency-webhook",
    )

    assert request.webhook_url == "https://example.com/concurrency-webhook"
    assert request.portfolio == "data/raw/strategies/portfolio.csv"
    # Test other valid fields if needed
    assert request.refresh is True  # Default value
```

**Changes:**

1. Remove `method` parameter (doesn't exist in schema)
2. Update assertions to test actual schema fields
3. Verify webhook_url is the main focus

---

## Validation Plan

After implementing fixes, run tests in sequence:

```bash
# Test 1: Fix JobService tests
poetry run pytest tests/api/test_job_webhook_integration.py -v

# Test 2: Fix schema tests
poetry run pytest tests/api/test_webhook_parameters.py -v

# Test 3: Run full API suite
poetry run pytest tests/api/ -v

# Expected: All tests passing
```

---

## QA Recommendations

### Immediate Actions:

1. ✅ Fix all 4 failing tests (25 minutes)
2. ✅ Run complete test suite (5 minutes)
3. ✅ Document schema changes (already done in this report)

### Follow-up Actions:

1. **Create Schema Change Checklist**

   - Update related tests when schemas change
   - Document breaking changes
   - Version API schemas

2. **Improve Test Robustness**

   - Use schema introspection instead of hardcoding field names
   - Generate tests from OpenAPI spec
   - Add schema validation layer

3. **CI/CD Enhancements**
   - Add schema validation step
   - Run test suite on every schema change
   - Alert on test failures

---

## Conclusion

All 4 failures are **test maintenance issues** rather than production bugs:

- ✅ Production code is correct
- ❌ Tests are outdated
- ✅ Fixes are straightforward
- ✅ Low risk of breaking changes

**Recommended Approach:** Fix all 4 tests in a single batch to achieve 100% test pass rate.

**Expected Outcome:** 113/113 tests passing ✅

---

**Analysis Complete**
**Status:** Ready for implementation
**Estimated Time:** 25 minutes
**Risk Level:** LOW
