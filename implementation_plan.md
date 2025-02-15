# Implementation Plan: CSV Import Support for Concurrency Analysis

## Overview
Extend the concurrency analysis module to support importing strategy configurations from CSV files while maintaining backward compatibility with JSON files.

## Current Implementation Analysis
- The module currently supports JSON files through `load_portfolio_from_json` in portfolio_loader.py
- Strategy configurations are defined by `StrategyConfig` TypedDict in types.py
- The JSON loader handles defaults and type conversions for various fields

## Required Changes

### 1. Portfolio Loader Module
Create a new function `load_portfolio_from_csv` with similar structure to the JSON loader:
```python
def load_portfolio_from_csv(csv_path: Path, log: Callable[[str, str], None], config: Dict) -> List[StrategyConfig]
```

#### CSV to JSON Field Mapping
- Ticker → ticker
- Use SMA → type ("SMA" if True else "EMA")
- Short Window → short_window
- Long Window → long_window
- Default Values:
  - timeframe: "Daily"
  - direction: "Long"
  - USE_RSI: False
  - USE_HOURLY: False (based on timeframe)

### 2. File Type Detection
Modify the portfolio loader to:
- Detect file type based on extension
- Route to appropriate loader function
- Add validation for supported file types

### 3. Error Handling
- Add CSV-specific validation
- Handle missing required columns
- Validate data types in CSV columns
- Provide clear error messages for CSV format issues

### 4. Documentation Updates
- Update docstrings to reflect CSV support
- Add CSV format specifications
- Document default values for optional fields

## Implementation Steps

1. **File Type Detection**
   - Add file extension check in portfolio_loader.py
   - Create routing logic to appropriate loader function

2. **CSV Loader Implementation**
   - Implement CSV file reading using Polars
   - Add column validation
   - Map CSV fields to StrategyConfig format
   - Handle type conversions and defaults

3. **Testing**
   - Test with example CSV file (BTC_D.csv)
   - Verify field mappings and defaults
   - Ensure backward compatibility with JSON files

4. **Documentation**
   - Update module docstrings
   - Add CSV format requirements
   - Document field mappings and defaults

## Migration Notes
- Existing JSON files will continue to work without changes
- CSV files must follow the specified column format
- Default values will be applied consistently across both formats

## Next Steps
1. Switch to Code mode to implement the changes
2. Test with the provided BTC_D.csv file
3. Verify backward compatibility with existing JSON files