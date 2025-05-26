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
- [x] Created Pydantic models for MA Cross API endpoint
- [x] Implemented request model (`MACrossRequest`) based on `StrategyConfig`
- [x] Implemented response models (`MACrossResponse`, `MACrossAsyncResponse`)
- [x] Added portfolio metrics model (`PortfolioMetrics`)
- [x] Implemented type conversion utilities
- [x] Added comprehensive validation logic

**Files Created/Modified:**
- `/app/api/models/ma_cross.py` - New file containing all MA Cross API models

**Key Features Implemented:**
- Full compatibility with `StrategyConfig` TypedDict
- Enum-based validation for direction and strategy types
- Nested model for minimum criteria with proper aliasing
- Conversion methods to transform between API models and internal formats
- Comprehensive field validation including synthetic pair logic
- Support for both single ticker and multiple ticker analysis
- Extended schema support (allocation and stop loss percentages)

**Testing Results:**
- Unit tests: To be implemented
- Integration tests: To be implemented

**Known Issues:**
- None

**Next Steps:**
- Proceed to Phase 2: Service Layer Implementation

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