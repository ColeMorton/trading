# Scanner List Update Implementation Plan

## Overview
Update the scanner list by processing individual portfolio results and compiling them into a comprehensive scanner list CSV.

## Requirements
1. Import scanner list CSV containing strategy parameters
2. Create dataframe of strategies (one row per strategy)
3. Process portfolio CSVs for each ticker/strategy combination
4. Export compiled results to scanner list CSV

## Implementation Steps

### 1. Configuration and Setup
- Define TypedDict for configuration
- Set up logging using app/tools/setup_logging.py
- Define constants for file paths and column names

### 2. Data Loading
- Load scanner list CSV using Polars
- Validate required columns exist
- Split rows with multiple strategies into separate entries
- Create strategy dataframe with 'Use SMA' boolean

### 3. Portfolio Processing
- For each strategy:
  - Construct portfolio CSV path based on ticker and MA type
  - Load portfolio CSV
  - Filter for matching Short/Long window combination
  - Validate required columns exist
  - Add strategy metadata (Use SMA, windows)

### 4. Results Compilation
- Combine all portfolio results
- Ensure all required columns present
- Sort by specified criteria (Expectancy Adjusted)
- Export to CSV in scanner list format

### 5. Error Handling
- Validate input files exist
- Handle missing or invalid data
- Log errors and warnings
- Clean up resources

## Type Definitions

```python
class ScannerConfig(TypedDict):
    """Scanner configuration type definition.
    
    Required Fields:
        SCANNER_LIST (str): Input scanner list filename
        BASE_DIR (str): Base directory for file operations
    
    Optional Fields:
        REFRESH (NotRequired[bool]): Whether to refresh existing results
        SORT_BY (NotRequired[str]): Field to sort results by
    """
    SCANNER_LIST: str
    BASE_DIR: str
    REFRESH: NotRequired[bool]
    SORT_BY: NotRequired[str]
```

## File Structure
```
csv/
  ma_cross/
    scanner_list/
      DAILY_test.csv         # Input scanner list
    portfolios/
      {TICKER}_D_EMA.csv    # Portfolio results for EMA
      {TICKER}_D_SMA.csv    # Portfolio results for SMA
```

## Output Format
CSV file with columns:
- Ticker
- Use SMA
- Short Window
- Long Window
- Total Trades
- Win Rate [%]
- Profit Factor
- Trades Per Day
- Expectancy
- Expectancy Adjusted
- [Additional metrics...]

## Error Cases to Handle
1. Missing input scanner list
2. Invalid portfolio CSV paths
3. Missing required columns
4. Data type validation failures
5. File permission issues

## Logging
- Setup logging with module name
- Log start/end of processing
- Log errors with context
- Log statistics and results

## Testing Strategy
1. Verify input file handling
2. Test strategy splitting logic
3. Validate portfolio processing
4. Check output format compliance
5. Verify error handling
6. Test with various input combinations

Would you like me to proceed with implementing this plan in Code mode?