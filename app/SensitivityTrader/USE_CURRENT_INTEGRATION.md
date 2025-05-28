# USE_CURRENT Parameter Integration

This document explains how the `USE_CURRENT` checkbox in SensitivityTrader is connected to the MA Cross API.

## Overview

The `USE_CURRENT` parameter controls whether the MA Cross analysis should use the most recent market data or potentially use cached/historical data. This parameter flows from the SensitivityTrader UI to the MA Cross API and ultimately to the `1_get_portfolios.py` script.

## Integration Flow

1. **UI Layer** (`templates/index.html`)
   - Checkbox with id `use-current-checkbox` (line 88)
   - Default state: checked (true)
   ```html
   <input class="form-check-input" type="checkbox" id="use-current-checkbox" checked>
   <label class="form-check-label" for="use-current-checkbox">Use Current</label>
   ```

2. **JavaScript Layer** (`static/js/app.js`)
   - Reads checkbox value in `buildConfigFromForm()` (line 230)
   - Includes in API request in `buildMACrossRequest()` (line 265)
   ```javascript
   USE_CURRENT: document.getElementById('use-current-checkbox').checked,
   ```

3. **API Model Layer** (`app/api/models/ma_cross.py`)
   - Defined as a field in `MACrossRequest` (lines 168-172)
   - Passed to strategy config in `to_strategy_config()` (line 247)
   ```python
   use_current: bool = Field(
       True,
       description="Whether to use current market data",
       alias="USE_CURRENT"
   )
   ```

4. **MA Cross Module** (`app/ma_cross/1_get_portfolios.py`)
   - Used in the CONFIG dictionary (line 95)
   - Controls data refresh behavior

## Testing

Run the test script to verify the integration:
```bash
# Start the API server
python -m app.api.run

# Run the test
python app/SensitivityTrader/test_use_current.py
```

## Manual Testing

1. Start both servers:
   ```bash
   # Terminal 1: API server
   python -m app.api.run
   
   # Terminal 2: SensitivityTrader
   python app/SensitivityTrader/main.py
   ```

2. Open browser to http://127.0.0.1:5000

3. Open browser developer console (F12)

4. Toggle the "Use Current" checkbox and run analysis

5. Check the network tab to verify the `USE_CURRENT` parameter is sent correctly:
   - When checked: `"USE_CURRENT": true`
   - When unchecked: `"USE_CURRENT": false`

## Implementation Details

### What USE_CURRENT Controls

In `1_get_portfolios.py`, the `USE_CURRENT` parameter typically affects:
- Whether to download fresh market data
- Whether to use cached price data
- How recent the data cutoff should be

The exact behavior depends on the implementation in the MA Cross module.

### Default Behavior

- UI default: checked (true)
- API default: true
- Script default: true

This ensures that by default, the system uses the most current market data available.

## Troubleshooting

### Parameter Not Being Sent
Check browser console for the request payload. The `USE_CURRENT` field should be present.

### Parameter Not Affecting Behavior
Verify that `1_get_portfolios.py` is actually using the `USE_CURRENT` parameter in its logic.

### Checkbox State Not Persisting
The checkbox state is not saved between page refreshes. This is by design to ensure users are aware of their data freshness choice.