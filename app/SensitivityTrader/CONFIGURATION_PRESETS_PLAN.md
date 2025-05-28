# Configuration Presets Implementation Plan

## Executive Summary

<summary>
  <objective>Add configuration preset functionality to SensitivityTrader UI, allowing users to easily switch between predefined analysis configurations</objective>
  <approach>Mirror the existing ticker list implementation pattern, loading presets from JSON and updating form fields dynamically</approach>
  <expected-outcome>Users can select from predefined configuration presets via dropdown, automatically populating all analysis parameters</expected-outcome>
</summary>

## Architecture Overview

### Current State Analysis
- Configuration parameters are manually entered via form inputs
- Default configuration is hardcoded in `app.py`
- No ability to switch between different configuration sets
- Ticker lists already implement a similar preset pattern

### Target State Design
- Configuration presets loaded from `/json/configuration/ma_cross.json`
- Dropdown selector for preset configurations
- Automatic form population when preset is selected
- Ability to modify preset values after selection
- Consistent UI/UX with existing ticker list functionality

### Gap Analysis
- Need backend endpoint to serve configuration presets
- Need frontend dropdown and selection handler
- Need form population logic for all configuration fields
- Need to maintain current manual input capability

## Phase Breakdown

<phase number="1">
  <objective>Add backend support for configuration presets</objective>
  <scope>Create API endpoint to serve configuration presets from JSON file</scope>
  <dependencies>Existing FastAPI setup, ma_cross.json file</dependencies>
  <implementation>
    <step>Add route handler in app.py to load and serve configuration presets</step>
    <step>Implement error handling for missing/invalid JSON file</step>
    <step>Test endpoint returns correct preset data</step>
  </implementation>
  <deliverables>Working /api/config-presets endpoint returning JSON presets</deliverables>
  <risks>JSON file format changes could break parsing</risks>
</phase>

<phase number="2">
  <objective>Add configuration preset dropdown to UI</objective>
  <scope>Modify index.html to include preset selector in configuration section</scope>
  <dependencies>Phase 1 completion, existing UI structure</dependencies>
  <implementation>
    <step>Add dropdown HTML similar to ticker list selector</step>
    <step>Position appropriately in configuration form section</step>
    <step>Add loading state and error handling</step>
  </implementation>
  <deliverables>Visible preset dropdown in UI with proper styling</deliverables>
  <risks>UI layout disruption, style inconsistencies</risks>
</phase>

<phase number="3">
  <objective>Implement preset loading and form population</objective>
  <scope>JavaScript logic to fetch presets and update form fields</scope>
  <dependencies>Phase 2 completion, existing form structure</dependencies>
  <implementation>
    <step>Add preset fetching logic in app.js</step>
    <step>Implement preset selection handler</step>
    <step>Map preset values to corresponding form fields</step>
    <step>Handle checkbox states for boolean values</step>
  </implementation>
  <deliverables>Functional preset selection with automatic form population</deliverables>
  <risks>Field mapping mismatches, data type conversion issues</risks>
</phase>

<phase number="4">
  <objective>Testing and refinement</objective>
  <scope>Comprehensive testing of preset functionality</scope>
  <dependencies>Phases 1-3 completion</dependencies>
  <implementation>
    <step>Test all presets load correctly</step>
    <step>Verify form values populate accurately</step>
    <step>Test switching between presets</step>
    <step>Ensure manual overrides work after preset selection</step>
  </implementation>
  <deliverables>Fully tested configuration preset feature</deliverables>
  <risks>Edge cases with specific field combinations</risks>
</phase>

## Implementation Details

### Backend Endpoint Structure
```python
@app.get("/api/config-presets")
async def get_config_presets():
    """Return available configuration presets"""
    # Load from /json/configuration/ma_cross.json
    # Return as list of {name, config} objects
```

### Frontend Integration Pattern
```javascript
// Similar to existing ticker list implementation
async function loadConfigPresets() {
    const response = await fetch('/api/config-presets');
    const presets = await response.json();
    populatePresetDropdown(presets);
}

function applyPreset(presetName) {
    const preset = presets[presetName];
    // Map preset values to form fields
    document.getElementById('windows').value = preset.WINDOWS;
    // ... map other fields
}
```

### Form Field Mapping
- WINDOWS → #windows
- USE_SCANNER → #use_scanner (checkbox)
- STRATEGY_TYPES → #strategy_types (multi-select)
- DIRECTION → #direction
- USE_HOURLY → #use_hourly (checkbox)
- USE_YEARS → #use_years (checkbox)
- YEARS → #years
- USE_SYNTHETIC → #use_synthetic (checkbox)
- USE_CURRENT → #use_current (checkbox)
- SORT_BY → #sort_by
- SORT_ASC → #sort_asc (checkbox)
- USE_GBM → #use_gbm (checkbox)

## Phase 1: Implementation Summary
**Status**: ✅ Complete

### What Was Accomplished
- Added `/api/config-presets` endpoint in `app.py` to serve configuration presets
- Endpoint loads presets from `/json/configuration/ma_cross.json`
- Implements proper error handling for missing files and JSON parsing errors
- Returns presets in list format suitable for frontend consumption

### Files Modified/Created
- `app/SensitivityTrader/app.py`: Added get_config_presets() route handler
- `app/SensitivityTrader/test_config_presets.py`: Created test script for endpoint verification

### Testing Results
- Endpoint correctly returns presets from JSON file
- Error handling works for missing files
- Response format matches expected structure

### Known Issues
- None identified

### Next Steps
- Phase 2: Add UI dropdown (completed)
- Phase 3: Implement JavaScript logic (completed)

## Phase 2: Implementation Summary
**Status**: ✅ Complete

### What Was Accomplished
- Added configuration preset dropdown to index.html
- Positioned below ticker list dropdown for consistency
- Styled to match existing UI elements

### Files Modified
- `templates/index.html`: Added config-preset-select dropdown element

### Testing Results
- Dropdown renders correctly in UI
- Maintains consistent styling with other form elements

### Known Issues
- None identified

### Next Steps
- Phase 3: JavaScript implementation (completed)

## Phase 3: Implementation Summary
**Status**: ✅ Complete

### What Was Accomplished
- Implemented loadConfigPresets() function to fetch presets from API
- Added populateConfigPresetDropdown() to populate dropdown options
- Created handleConfigPresetSelection() to apply preset values to all form fields
- Integrated with existing form structure and field IDs
- Added proper error handling and user notifications
- Stores presets globally in window.configPresets for easy access

### Files Modified
- `static/js/app.js`: Added three new functions and initialization call

### Key Features Implemented
- Automatic preset loading on page load
- Dynamic dropdown population
- Complete field mapping for all configuration options:
  - Basic config: WINDOWS, STRATEGY_TYPES, DIRECTION, REFRESH, USE_CURRENT
  - Advanced config: USE_HOURLY, USE_YEARS, YEARS, USE_SYNTHETIC, TICKER_2, USE_SCANNER, USE_GBM
  - Minimums: WIN_RATE, TRADES, EXPECTANCY_PER_TRADE, PROFIT_FACTOR, SORTINO_RATIO
  - Sorting: SORT_BY, SORT_ASC
- Toast notifications for user feedback
- Graceful error handling with fallback to manual configuration

### Testing Results
- Presets load successfully from server
- All form fields update correctly when preset is selected
- Manual override works after preset selection
- Error handling works when API is unavailable

### Known Issues
- None identified

### Next Steps
- Phase 4: Comprehensive testing

## Success Criteria
- Users can select from available configuration presets
- All form fields update correctly when preset is selected
- Manual overrides work after preset selection
- UI remains consistent with existing design
- No disruption to current functionality

## Risk Mitigation
- Maintain backward compatibility with manual input
- Provide clear error messages for missing presets
- Include "Custom" option to indicate manual configuration
- Test thoroughly with existing workflows

## Timeline Estimate
- Phase 1: Backend implementation (2-3 hours)
- Phase 2: UI integration (1-2 hours)
- Phase 3: JavaScript logic (2-3 hours)
- Phase 4: Testing and refinement (1-2 hours)

Total: 6-10 hours of implementation time