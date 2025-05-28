# SensitivityTrader Field Connections Documentation

This document describes how all configuration fields flow from the SensitivityTrader UI through the MA Cross API to the backend analysis module.

## Field Flow Overview

```
SensitivityTrader UI (HTML/JS) → MA Cross API (FastAPI) → MA Cross Module (Python)
```

## Complete Field Mapping

### 1. TICKER
- **UI Element**: `<input id="tickers-input">` 
- **JS Variable**: `config.TICKER` (converted from comma-separated string to array)
- **API Model**: `ticker: Union[str, List[str]]`
- **Backend**: `CONFIG["TICKER"]`
- **Description**: Trading symbol(s) to analyze

### 2. WINDOWS
- **UI Element**: `<input id="windows-input" type="number" value="89">`
- **JS Variable**: `config.WINDOWS`
- **API Model**: `windows: int = Field(89, ge=2, le=200)`
- **Backend**: `CONFIG["WINDOWS"]`
- **Description**: Maximum window size for parameter analysis

### 3. DIRECTION
- **UI Element**: `<select id="direction-select">`
- **JS Variable**: `config.DIRECTION`
- **API Model**: `direction: DirectionEnum`
- **Backend**: `CONFIG["DIRECTION"]`
- **Description**: Trading direction (Long/Short)

### 4. USE_SMA / Strategy Types
- **UI Element**: `<input id="sma-checkbox" type="checkbox">`
- **JS Variable**: `config.STRATEGY_TYPES` (array including "SMA" if checked)
- **API Model**: `strategy_types: List[StrategyTypeEnum]`
- **Backend**: `CONFIG["STRATEGY_TYPES"]`
- **Description**: Whether to include SMA strategy

### 5. USE_HOURLY
- **UI Element**: `<input id="use-hourly-checkbox" type="checkbox">`
- **JS Variable**: `config.USE_HOURLY`
- **API Model**: `use_hourly: bool = Field(False)`
- **Backend**: `CONFIG["USE_HOURLY"]`
- **Description**: Use hourly data instead of daily

### 6. USE_YEARS
- **UI Element**: `<input id="use-years-checkbox" type="checkbox">`
- **JS Variable**: `config.USE_YEARS`
- **API Model**: `use_years: bool = Field(False)`
- **Backend**: `CONFIG["USE_YEARS"]`
- **Description**: Whether to limit data by years

### 7. YEARS
- **UI Element**: `<input id="years-input" type="number" value="15">`
- **JS Variable**: `config.YEARS`
- **API Model**: `years: float = Field(15, gt=0, le=50)`
- **Backend**: `CONFIG["YEARS"]`
- **Description**: Number of years of data to use

### 8. USE_SYNTHETIC
- **UI Element**: `<input id="use-synthetic-checkbox" type="checkbox">`
- **JS Variable**: `config.USE_SYNTHETIC`
- **API Model**: `use_synthetic: bool = Field(False)`
- **Backend**: `CONFIG["USE_SYNTHETIC"]`
- **Description**: Enable synthetic pair trading

### 9. TICKER_2
- **UI Element**: `<input id="ticker2-input" placeholder="e.g., MSTR">`
- **JS Variable**: `config.TICKER_2` (only added if USE_SYNTHETIC is true)
- **API Model**: `ticker_2: Optional[str]`
- **Backend**: `CONFIG["TICKER_2"]`
- **Description**: Second ticker for synthetic pair

### 10. USE_SCANNER
- **UI Element**: `<input id="use-scanner-checkbox" type="checkbox">`
- **JS Variable**: `config.USE_SCANNER`
- **API Model**: `use_scanner: bool = Field(False)`
- **Backend**: `CONFIG["USE_SCANNER"]`
- **Description**: Enable scanner mode

### 11. REFRESH
- **UI Element**: `<input id="refresh-checkbox" type="checkbox" checked>`
- **JS Variable**: `config.REFRESH` (hardcoded to true in buildConfigFromForm)
- **API Model**: `refresh: bool = Field(True)`
- **Backend**: `CONFIG["REFRESH"]`
- **Description**: Whether to refresh cached data

### 12. USE_CURRENT
- **UI Element**: `<input id="use-current-checkbox" type="checkbox" checked>`
- **JS Variable**: `config.USE_CURRENT`
- **API Model**: `use_current: bool = Field(True)`
- **Backend**: `CONFIG["USE_CURRENT"]`
- **Description**: Use current market data

### 13. MINIMUMS
- **UI Elements**: Multiple inputs for minimum criteria
  - `<input id="min-win-rate-input" value="0.44">`
  - `<input id="min-trades-input" value="54">`
  - `<input id="min-expectancy-input" value="1">`
  - `<input id="min-profit-factor-input" value="1">`
  - `<input id="min-sortino-input" value="0.4">`
- **JS Variable**: `config.MINIMUMS` (object with all criteria)
- **API Model**: `minimums: Optional[MinimumCriteria]`
- **Backend**: `CONFIG["MINIMUMS"]`
- **Description**: Minimum criteria for portfolio filtering

### 14. SORT_BY
- **UI Element**: `<select id="sort-by-select">`
- **JS Variable**: `config.SORT_BY`
- **API Model**: `sort_by: str = Field("Score")`
- **Backend**: `CONFIG["SORT_BY"]`
- **Description**: Field to sort results by

### 15. SORT_ASC
- **UI Element**: `<input id="sort-asc-checkbox" type="checkbox">`
- **JS Variable**: `config.SORT_ASC`
- **API Model**: `sort_asc: bool = Field(False)`
- **Backend**: `CONFIG["SORT_ASC"]`
- **Description**: Sort in ascending order

### 16. USE_GBM (Additional field)
- **UI Element**: `<input id="use-gbm-checkbox" type="checkbox">`
- **JS Variable**: `config.USE_GBM`
- **API Model**: `use_gbm: bool = Field(False)`
- **Backend**: `CONFIG["USE_GBM"]`
- **Description**: Use Geometric Brownian Motion simulation

## JavaScript Implementation Details

### Form to Config Conversion (buildConfigFromForm)
```javascript
const config = {
    WINDOWS: parseInt(document.getElementById('windows-input').value),
    REFRESH: true,
    STRATEGY_TYPES: strategyTypes,
    DIRECTION: document.getElementById('direction-select').value,
    USE_HOURLY: document.getElementById('use-hourly-checkbox').checked,
    USE_YEARS: document.getElementById('use-years-checkbox').checked,
    YEARS: parseInt(document.getElementById('years-input').value),
    USE_SYNTHETIC: document.getElementById('use-synthetic-checkbox').checked,
    USE_CURRENT: document.getElementById('use-current-checkbox').checked,
    USE_SCANNER: document.getElementById('use-scanner-checkbox').checked,
    MINIMUMS: { /* ... */ },
    SORT_BY: document.getElementById('sort-by-select').value,
    SORT_ASC: document.getElementById('sort-asc-checkbox').checked,
    USE_GBM: document.getElementById('use-gbm-checkbox').checked
};

// Conditional addition of TICKER_2
if (config.USE_SYNTHETIC) {
    const ticker2Value = document.getElementById('ticker2-input').value.trim();
    if (ticker2Value) {
        config.TICKER_2 = ticker2Value;
    }
}
```

### Config to API Request (buildMACrossRequest)
```javascript
const request = {
    TICKER: tickerArray.length === 1 ? tickerArray[0] : tickerArray,
    WINDOWS: config.WINDOWS,
    DIRECTION: config.DIRECTION,
    STRATEGY_TYPES: config.STRATEGY_TYPES,
    USE_HOURLY: config.USE_HOURLY,
    USE_YEARS: config.USE_YEARS,
    YEARS: config.YEARS,
    USE_SYNTHETIC: config.USE_SYNTHETIC,
    USE_CURRENT: config.USE_CURRENT,
    USE_SCANNER: config.USE_SCANNER,
    REFRESH: config.REFRESH,
    MINIMUMS: config.MINIMUMS,
    SORT_BY: config.SORT_BY,
    SORT_ASC: config.SORT_ASC,
    USE_GBM: config.USE_GBM,
    async_execution: false
};

// Add TICKER_2 if present
if (config.TICKER_2) {
    request.TICKER_2 = config.TICKER_2;
}
```

## Testing

To test all field connections:

```bash
# 1. Start the API server
python -m app.api.run

# 2. Run the test script
python app/SensitivityTrader/test_all_fields.py
```

## Troubleshooting

### Common Issues

1. **Field not passing through**: Check that the field is:
   - Read from the correct HTML element ID
   - Added to the config object in JavaScript
   - Included in the API request
   - Defined in the API model
   - Passed to the backend in `to_strategy_config()`

2. **Type mismatch**: Ensure proper type conversion:
   - Use `parseInt()` for numbers in JavaScript
   - Use `parseFloat()` for decimals
   - Check `.checked` for checkboxes
   - Use `.value` for text inputs and selects

3. **Conditional fields**: Some fields like `TICKER_2` are only added when certain conditions are met (e.g., when `USE_SYNTHETIC` is true)

4. **Default values**: Check that default values are consistent across:
   - HTML element attributes
   - JavaScript `defaultConfig` object
   - Python `DEFAULT_CONFIG` in app.py
   - API model field defaults