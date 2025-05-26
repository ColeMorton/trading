# MA Cross API Endpoint Implementation Plan

## Overview
This plan outlines the creation of a new API endpoint in `/app/api/` that accepts a `StrategyConfig` object and integrates with the MA Cross portfolio analysis functionality in `/app/ma_cross/1_get_portfolios.py`.

## Architecture Principles
- **Modularity**: Each phase is independent and can be deployed without breaking existing functionality
- **Backward Compatibility**: All changes maintain backward compatibility
- **Separation of Concerns**: Clear separation between API layer, business logic, and data processing
- **Type Safety**: Leverage TypedDict definitions from `app.tools.strategy.types`

## Phase 1: API Models and Request/Response Types
**Goal**: Create type-safe request and response models for the MA Cross endpoint

### Tasks:
1. Create new Pydantic models in `/app/api/models/ma_cross.py`:
   - `MACrossRequest` model based on `StrategyConfig`
   - `MACrossResponse` model for portfolio results
   - `PortfolioResult` model for individual portfolio data

2. Extend existing models if needed:
   - Update `/app/api/models/request.py` with base classes if applicable
   - Update `/app/api/models/response.py` with standard response wrappers

### Deliverables:
- New model definitions with proper validation
- Type conversion utilities between Pydantic models and TypedDict
- Unit tests for model validation

### No Breaking Changes:
- New files only, no modifications to existing code
- Models are self-contained

---

## Phase 2: Service Layer Implementation
**Goal**: Create a service layer that bridges the API and the MA Cross functionality

### Tasks:
1. Create `/app/api/services/ma_cross_service.py`:
   - `MACrossService` class with methods for:
     - Converting API models to internal config format
     - Executing MA Cross analysis
     - Processing and formatting results
   - Error handling and logging integration

2. Create utility functions for:
   - Config validation and normalization
   - Result transformation and filtering
   - Async/sync execution handling

### Deliverables:
- Complete service implementation
- Integration tests with mock data
- Error handling scenarios

### No Breaking Changes:
- New service layer doesn't modify existing code
- Uses existing functions from `1_get_portfolios.py` without modification

---

## Phase 3: API Router Implementation
**Goal**: Create the API endpoint that handles HTTP requests

### Tasks:
1. Create `/app/api/routers/ma_cross.py`:
   - POST endpoint `/api/ma-cross/analyze`
   - Request validation using Pydantic models
   - Response formatting and error handling
   - API documentation with OpenAPI schema

2. Register router in `/app/api/main.py`:
   - Add import for ma_cross router
   - Include router with appropriate prefix

### Deliverables:
- Fully functional API endpoint
- OpenAPI documentation
- Integration with existing middleware

### No Breaking Changes:
- New router added alongside existing ones
- Main.py modification is additive only

---

## Phase 4: Refactor MA Cross Module for API Compatibility
**Goal**: Make `1_get_portfolios.py` more API-friendly without breaking CLI functionality

### Tasks:
1. Extract core logic into reusable functions:
   - Create `analyze_portfolios(config: StrategyConfig) -> List[Dict]`
   - Separate CLI-specific code from business logic
   - Improve error handling for API context

2. Add configuration options for API mode:
   - Disable file I/O when running from API
   - Return results instead of exporting to files
   - Make logging configurable

### Deliverables:
- Refactored module with clean separation
- Maintained CLI functionality
- New API-friendly entry points

### No Breaking Changes:
- Existing `run()` and `run_strategies()` functions remain unchanged
- New functions added alongside existing ones
- CLI behavior identical to current implementation

---

## Phase 5: Enhanced Features and Optimization
**Goal**: Add advanced features for the API endpoint

### Tasks:
1. Implement caching layer:
   - Cache frequently requested analyses
   - Configurable TTL for results
   - Cache invalidation strategies

2. Add batch processing support:
   - Accept multiple configurations in one request
   - Parallel execution for better performance
   - Progress tracking for long-running analyses

3. Implement result streaming:
   - Server-sent events for real-time updates
   - WebSocket support for interactive sessions
   - Partial result delivery

### Deliverables:
- Caching infrastructure
- Batch processing endpoints
- Real-time communication options

### No Breaking Changes:
- New features are optional
- Existing endpoint behavior unchanged
- Backward compatible API versions

---

## Phase 6: Testing and Documentation
**Goal**: Comprehensive testing and documentation

### Tasks:
1. Create test suites:
   - Unit tests for all new components
   - Integration tests for API endpoints
   - End-to-end tests for complete workflows
   - Performance benchmarks

2. Documentation:
   - API endpoint documentation
   - Usage examples and tutorials
   - Architecture diagrams
   - Migration guide for existing users

3. Monitoring and observability:
   - Add metrics collection
   - Implement request tracing
   - Create dashboards for API usage

### Deliverables:
- Complete test coverage
- Professional documentation
- Monitoring infrastructure

### No Breaking Changes:
- Tests don't affect production code
- Documentation is supplementary
- Monitoring is opt-in

---

## Implementation Summary

### Phase 1 Summary - Completed
**Completed Tasks:**
- [x] Created Pydantic models for MA Cross API endpoint in `/app/api/models/ma_cross.py`
- [x] Implemented `MACrossRequest` model with full StrategyConfig compatibility
- [x] Implemented response models (`MACrossResponse`, `MACrossAsyncResponse`)
- [x] Added `PortfolioMetrics` model with comprehensive trade and performance metrics
- [x] Created `MinimumCriteria` model for portfolio filtering
- [x] Implemented type conversion utilities with `to_strategy_config()` method
- [x] Added comprehensive validation logic for all fields

**Files Created/Modified:**
- `/app/api/models/ma_cross.py` - New file containing all MA Cross API models (329 lines)

**Key Features Implemented:**
- Full compatibility with `StrategyConfig` TypedDict from `app/ma_cross/config_types.py`
- Enum-based validation for direction (Long/Short) and strategy types (SMA/EMA)
- Nested model for minimum criteria with proper UPPERCASE aliasing
- Field aliasing to match existing configuration format (e.g., `ticker` → `TICKER`)
- Comprehensive validation including:
  - Ticker format validation (1-10 characters)
  - Synthetic pair configuration validation
  - Window size limits (2-200)
  - Percentage field bounds (win_rate: 0-1)
- Support for both single ticker and multiple ticker analysis
- Extended schema support:
  - Portfolio allocation percentage
  - Stop loss percentage
  - Position size calculation
  - Trade status indicators
- Asynchronous execution response model with SSE endpoints
- Breadth metrics support for market analysis

**Model Structure:**
1. **Enums:**
   - `DirectionEnum`: Long/Short trading directions
   - `StrategyTypeEnum`: SMA/EMA strategy types

2. **Request Models:**
   - `MACrossRequest`: Main request model with 16 fields
   - `MinimumCriteria`: Nested model with 7 filtering criteria

3. **Response Models:**
   - `PortfolioMetrics`: 24 fields for comprehensive portfolio analysis
   - `MACrossResponse`: Synchronous response with results and metadata
   - `MACrossAsyncResponse`: Asynchronous execution response

**Validation Features:**
- Custom validators for ticker format and list validation
- Synthetic pair configuration validation (requires TICKER_1 and TICKER_2)
- Prevents synthetic pairs with multiple tickers
- Field bounds validation (years: 0-50, windows: 2-200)
- Enum value validation for direction and strategy types

**Testing Results:**
- Unit tests: To be implemented
- Integration tests: To be implemented
- Manual validation: Models successfully instantiate and validate test data

**Known Issues:**
- None identified

**Next Steps:**
- Proceed to Phase 2: Service Layer Implementation
- Create unit tests for model validation
- Document API usage examples

---

### Phase 2 Implementation Summary (Completed)

**Date Completed:** January 27, 2025

**Overview:**
Successfully implemented the MA Cross service layer (`/app/api/services/ma_cross_service.py`) with both synchronous and asynchronous execution methods. The service integrates with the existing MA Cross scanner functionality and provides a clean API interface.

**Files Created/Modified:**
1. **Created `/app/api/services/ma_cross_service.py`** (313 lines)
   - Main service implementation with MACrossService class
   - Complete error handling and logging infrastructure
   - Thread pool executor for async operations

2. **Modified `/app/api/services/__init__.py`**
   - Added exports for MACrossService and MACrossServiceError
   - Maintained consistency with existing service exports

**Key Implementation Details:**

1. **MACrossService Class:**
   - Synchronous method: `analyze_portfolio(request: MACrossRequest) -> MACrossResponse`
   - Asynchronous method: `analyze_portfolio_async(request: MACrossRequest) -> MACrossAsyncResponse`
   - Status tracking: `get_task_status(execution_id: str) -> Dict[str, Any]`
   - Cleanup utility: `cleanup_old_tasks(max_age_hours: int) -> int`

2. **Integration Points:**
   - Uses existing `app.ma_cross.tools.scanner_processing` functions
   - Leverages `app.tools.setup_logging` for consistent logging
   - Maintains compatibility with existing configuration structure
   - Integrates with global `task_status` dictionary for async tracking

3. **Error Handling:**
   - Custom `MACrossServiceError` exception class
   - Comprehensive try-catch blocks with detailed logging
   - Traceback capture for debugging
   - Graceful error propagation to API responses

4. **Async Execution Pattern:**
   - ThreadPoolExecutor with 4 workers
   - UUID-based execution tracking
   - Real-time status updates in task_status dictionary
   - Progress messages for client feedback

5. **Logging Infrastructure:**
   - Separate log files for sync/async operations
   - Timestamped log files in `ma_cross` subdirectory
   - Structured logging with levels (info, error)
   - Automatic log cleanup on completion

**Technical Decisions:**
1. Used ThreadPoolExecutor instead of ProcessPoolExecutor for better shared memory access
2. Maintained existing scanner logic rather than refactoring to minimize risk
3. Added sys.path manipulation to ensure module imports work correctly
4. Implemented placeholder metrics (trades, win_rate, etc.) for initial MVP

**Known Limitations:**
1. Portfolio metrics are currently placeholders (zeros) - will be populated when integrated with full backtest
2. Single/portfolio ticker handling could be refactored for clarity
3. Task cleanup is manual - could add automatic cleanup on a schedule

**Testing Considerations:**
- Service methods are designed for easy unit testing
- Async operations can be tested with execution ID tracking
- Error cases are explicitly handled and logged

**Next Steps:**
- Proceed to Phase 3: API Endpoint Implementation
- Create comprehensive unit tests for service layer
- Consider adding service-level caching for repeated requests
- Implement full backtest integration for complete metrics

---

## Risk Mitigation

1. **Configuration Compatibility**:
   - Maintain backward compatibility with existing config format
   - Provide migration utilities if needed

2. **Performance Considerations**:
   - Implement request timeouts
   - Add rate limiting for resource protection
   - Use async processing where beneficial

3. **Error Handling**:
   - Consistent error response format
   - Detailed logging for debugging
   - Graceful degradation for partial failures

## Success Criteria

- API endpoint successfully processes StrategyConfig requests
- Response times under 30 seconds for typical requests
- No impact on existing CLI functionality
- Complete test coverage (>90%)
- Clear documentation for all features