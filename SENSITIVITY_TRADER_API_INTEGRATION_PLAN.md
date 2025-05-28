# SensitivityTrader API Integration Plan

## Executive Summary

<summary>
  <objective>Integrate SensitivityTrader UI to use the existing /api/ma-cross/analyze endpoint for parameter sensitivity analysis</objective>
  <approach>Modify SensitivityTrader's frontend JavaScript to call the MA Cross API directly, handle async execution, and display results including portfolios_best</approach>
  <expected-outcome>SensitivityTrader UI successfully sends parameters to MA Cross API, retrieves analysis results, and displays them in the existing Results table with access to portfolios_best CSV files</expected-outcome>
</summary>

## Architecture Overview

### Current State Analysis
- **SensitivityTrader**: Flask-based web app with its own analysis endpoint
- **API**: FastAPI server with fully functional MA Cross endpoint at `/api/ma-cross/analyze`
- **MA Cross**: Core analysis engine accessible via API that generates portfolio CSV files
- **Gap**: SensitivityTrader UI doesn't use the API endpoint

### Target State Design
- SensitivityTrader UI calls `/api/ma-cross/analyze` directly
- Handles both synchronous and asynchronous execution responses
- Retrieves and displays portfolios_best CSV files when available
- Maintains existing UI functionality while using API backend

### Gap Analysis
What needs to change:
1. Update JavaScript to call MA Cross API instead of Flask endpoint
2. Handle API response format and transform data for display
3. Implement polling for async execution status
4. Add functionality to retrieve and display portfolios_best CSV files
5. Ensure proper CORS configuration

## Phase Breakdown

<phase number="1">
  <objective>Update SensitivityTrader JavaScript to Call MA Cross API</objective>
  <scope>Modify app.js to send requests to /api/ma-cross/analyze with proper formatting</scope>
  <dependencies>None - client-side changes only</dependencies>
  <implementation>
    <step>Update runAnalysis() to call MA Cross API endpoint</step>
    <step>Transform form data to match MACrossRequest model format</step>
    <step>Handle both sync (200) and async (202) response codes</step>
    <step>Fix element IDs to match actual HTML form structure</step>
  </implementation>
  <deliverables>Frontend successfully sends requests to MA Cross API</deliverables>
  <risks>CORS configuration may need adjustment</risks>
</phase>

<phase number="2">
  <objective>Implement Async Execution Handling</objective>
  <scope>Add polling mechanism for asynchronous analysis status</scope>
  <dependencies>Phase 1 completion</dependencies>
  <implementation>
    <step>Create pollForResults() function to check /api/ma-cross/status/{id}</step>
    <step>Display progress updates from status endpoint</step>
    <step>Handle completion and failure states</step>
    <step>Show appropriate notifications during execution</step>
  </implementation>
  <deliverables>UI properly handles long-running analyses</deliverables>
  <risks>Timeout handling for very long analyses</risks>
</phase>

<phase number="3">
  <objective>Transform and Display MA Cross Results</objective>
  <scope>Process API response and populate existing Results table</scope>
  <dependencies>Phase 2 completion</dependencies>
  <implementation>
    <step>Create processMACrossResults() to transform API response</step>
    <step>Map portfolio metrics to existing table columns</step>
    <step>Store portfolio_exports information for CSV access</step>
    <step>Update populateResultsTable() to handle new data format</step>
  </implementation>
  <deliverables>Results displayed correctly in existing DataTable</deliverables>
  <risks>Data format differences between Flask and API responses</risks>
</phase>

<phase number="4">
  <objective>Add Portfolios Best CSV Retrieval</objective>
  <scope>Implement functionality to access and display portfolios_best CSV files</scope>
  <dependencies>Phase 3 completion</dependencies>
  <implementation>
    <step>Add exportPortfolioCSV() function to download CSV files</step>
    <step>Create loadPortfoliosBest() to fetch and display best portfolios</step>
    <step>Use /api/data/csv/{path} endpoint for file retrieval</step>
    <step>Add UI buttons for export and load operations</step>
  </implementation>
  <deliverables>Users can access and view portfolios_best results</deliverables>
  <risks>File path resolution between API and UI</risks>
</phase>

<phase number="5">
  <objective>Testing and Refinement</objective>
  <scope>Ensure complete integration works smoothly</scope>
  <dependencies>All previous phases completed</dependencies>
  <implementation>
    <step>Test various ticker combinations and parameters</step>
    <step>Verify async execution for long-running analyses</step>
    <step>Confirm CSV export/import functionality</step>
    <step>Handle edge cases and error scenarios</step>
  </implementation>
  <deliverables>Fully functional integration</deliverables>
  <risks>None - testing phase</risks>
</phase>

## Implementation Tracking

### Phase 1: Implementation Summary
**Status**: ✅ Complete
**Date**: 2024-01-28

### What Was Accomplished
- Modified `runAnalysis()` to call `/api/ma-cross/analyze` endpoint
- Created `buildMACrossRequest()` to format request data properly
- Fixed all form element IDs to match HTML structure
- Added support for both sync and async responses

### Files Modified
- `/app/SensitivityTrader/static/js/app.js`: Updated to use MA Cross API

### Phase 2: Implementation Summary
**Status**: ✅ Complete
**Date**: 2024-01-28

### What Was Accomplished
- Implemented `pollForResults()` function for async status checking
- Added progress notifications during analysis
- Proper error handling for timeouts and failures

### Files Modified
- `/app/SensitivityTrader/static/js/app.js`: Added async polling logic

### Phase 3: Implementation Summary
**Status**: ✅ Complete
**Date**: 2024-01-28

### What Was Accomplished
- Created `processMACrossResults()` to transform API response format
- Mapped portfolio metrics to table columns
- Stored portfolio_exports for CSV access
- Updated table population logic

### Files Modified
- `/app/SensitivityTrader/static/js/app.js`: Added result processing

### Phase 4: Implementation Summary
**Status**: ✅ Complete
**Date**: 2024-01-28

### What Was Accomplished
- Added `exportPortfolioCSV()` for downloading CSV files
- Created `loadPortfoliosBest()` to display best portfolios
- Integrated with `/api/data/csv/` endpoint
- Added UI event handlers for new functionality

### Files Modified
- `/app/SensitivityTrader/static/js/app.js`: Added CSV handling functions

### Known Issues - RESOLVED
- ✅ UI buttons for export/load added to HTML template
- ⚠️ CORS configuration may need adjustment if API and UI run on different ports

### Phase 5: Implementation Summary
**Status**: ✅ Complete
**Date**: 2024-01-28

### What Was Accomplished
- Created test script to verify API integration
- Added comprehensive integration documentation
- Verified complete end-to-end functionality
- Tested various parameter combinations

### Files Created
- `/app/SensitivityTrader/test_integration.py`: Integration test script
- `/app/SensitivityTrader/INTEGRATION_README.md`: User documentation

### Testing Results
- API connectivity confirmed
- Request/response format validation successful
- CSV retrieval functionality working
- UI properly displays results and portfolio exports

### Next Steps
- Deploy to production environment
- Monitor performance with real-world usage
- Consider adding SSE progress streaming for enhanced UX

## Key Principles

- **Simplicity**: Use existing API endpoints without creating new ones
- **Compatibility**: Maintain existing UI functionality
- **Performance**: Leverage API's caching and optimization
- **User Experience**: Provide clear feedback during analysis
- **Reusability**: Use API's portfolio export capabilities

## Best Practices

### DO:
- Use the existing MA Cross API endpoint
- Handle both sync and async execution modes
- Transform data to match UI expectations
- Provide clear user feedback
- Test with various parameter combinations

### DON'T:
- Create duplicate endpoints
- Modify the API backend
- Change core analysis logic
- Skip error handling
- Ignore CORS requirements

## Notes

- This simplified approach leverages the existing MA Cross API without requiring backend changes
- The integration maintains all SensitivityTrader UI features while using the API backend
- Portfolio CSV exports provide additional value through the portfolios_best feature
- Future enhancements can include SSE progress streaming and advanced filtering