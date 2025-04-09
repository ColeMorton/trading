# Refactoring Plan: CSV Directory Path Change

## Overview

This refactoring plan outlines the steps needed to change the directory from which CSV files are imported from `/csv/portfolios` to `/csv/strategies`. The plan focuses on three main files:

1. `app/ma_cross/1_scanner.py`
2. `app/strategies/update_portfolios.py`
3. `app/concurrency/review.py`

Additionally, `app/strategies/update_portfolios.py` should export to the same location it imports from (`/csv/strategies`), while the other files should continue to export to `/csv/portfolios` and its subdirectories.

## Affected Components

### 1. Files with Direct Import Path References

- `app/ma_cross/1_scanner.py` - Line 112: `f'./csv/portfolios/{config["PORTFOLIO"]}'`
- `app/concurrency/review.py` - Line 160: `csv_path = Path(f"csv/portfolios/{portfolio_name}.csv")`
- `app/ma_cross/tools/scanner_processing.py` - Line 141: `portfolio_path = os.path.join("./csv/portfolios", config["PORTFOLIO"])`

### 2. Indirect Import References via Portfolio Loading Functions

- `app/strategies/update_portfolios.py` - Uses `load_portfolio` function which internally resolves paths

### 3. Export Path in `app/strategies/update_portfolios.py`

- The `export_summary_results` function in `app/strategies/tools/summary_processing.py` (line 190) needs to be modified to export to `/csv/strategies` instead of `/csv/portfolios`

## Detailed Refactoring Steps

### 1. Update Direct Import Path References

#### 1.1. `app/ma_cross/1_scanner.py`

```diff
- scanner_df = pl.read_csv(
-     f'./csv/portfolios/{config["PORTFOLIO"]}',
-     infer_schema_length=10000,
+ scanner_df = pl.read_csv(
+     f'./csv/strategies/{config["PORTFOLIO"]}',
+     infer_schema_length=10000,
```

#### 1.2. `app/concurrency/review.py`

```diff
- csv_path = Path(f"csv/portfolios/{portfolio_name}.csv")
+ csv_path = Path(f"csv/strategies/{portfolio_name}.csv")
```

#### 1.3. `app/ma_cross/tools/scanner_processing.py`

```diff
- portfolio_path = os.path.join("./csv/portfolios", config["PORTFOLIO"])
+ portfolio_path = os.path.join("./csv/strategies", config["PORTFOLIO"])
```

### 2. Update Portfolio Loading Functions for Imports

#### 2.1. Modify `app/tools/portfolio/paths.py`

We need to update the path resolution function to look in `/csv/strategies` for CSV files:

```diff
def resolve_portfolio_path(
    portfolio_name: str,
    base_dir: Optional[str] = None,
    file_type: Optional[str] = None
) -> Path:
    """
    Resolve the path to a portfolio file.

    Args:
        portfolio_name: Name of the portfolio file (with or without extension)
        base_dir: Base directory (defaults to current working directory)
        file_type: Force specific file type ('csv' or 'json')

    Returns:
        Path: Resolved path to the portfolio file

    Raises:
        FileNotFoundError: If portfolio file cannot be found
    """
    # Use provided base_dir or default to current directory
    base = Path(base_dir) if base_dir else Path('.')
    
    # If file_type is specified, force that extension
    if file_type:
        if file_type.lower() not in ['csv', 'json']:
            raise ValueError(f"Unsupported file type: {file_type}. Must be 'csv' or 'json'")
        
        # Ensure portfolio_name has the correct extension
        name = portfolio_name
        if '.' in name:
            name = name.split('.')[0]
        
-       portfolio_path = base / "csv" / "portfolios" / f"{name}.{file_type.lower()}"
+       # For CSV files, check strategies directory
+       if file_type.lower() == 'csv':
+           portfolio_path = base / "csv" / "strategies" / f"{name}.{file_type.lower()}"
+       else:
+           # For JSON files, use the original path
+           portfolio_path = base / "json" / "portfolios" / f"{name}.json"
        if portfolio_path.exists():
            return portfolio_path
```

Similar changes are needed for the other path resolution sections in this file:

```diff
    # Try to find the file with any supported extension
    # First check if the name already has an extension
    if '.' in portfolio_name:
        name, ext = portfolio_name.split('.', 1)
        if ext.lower() in ['csv', 'json']:
            # Check CSV directory first
            if ext.lower() == 'csv':
-               portfolio_path = base / "csv" / "portfolios" / portfolio_name
+               portfolio_path = base / "csv" / "strategies" / portfolio_name
                if portfolio_path.exists():
                    return portfolio_path
```

And:

```diff
    else:
        # Try CSV first
-       portfolio_path = base / "csv" / "portfolios" / f"{portfolio_name}.csv"
+       portfolio_path = base / "csv" / "strategies" / f"{portfolio_name}.csv"
        if portfolio_path.exists():
            return portfolio_path
```

### 3. Update Export Path in `app/strategies/tools/summary_processing.py`

After examining the `export_summary_results` function, we need to modify it to export to `/csv/strategies` instead of `/csv/portfolios`. The function currently uses the `export_portfolios` function with `feature_dir=""` which defaults to exporting to `/csv/portfolios`.

```diff
def export_summary_results(portfolios: List[Dict], portfolio_name: str, log: Callable[[str, str], None], config: Optional[Dict] = None) -> bool:
    """
    Export portfolio summary results to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio statistics
        portfolio_name (str): Name of the portfolio file
        log (Callable): Logging function
        config (Optional[Dict]): Configuration dictionary including USE_HOURLY setting

    Returns:
        bool: True if export successful, False otherwise
    """
    if portfolios:
        # Reorder columns for each portfolio
        reordered_portfolios = [reorder_columns(p) for p in portfolios]
        
        # Use provided config or get default if none provided
        export_config = config if config is not None else get_config({})
        export_config["TICKER"] = None
        
        # Remove duplicates based on Ticker, Use SMA, Short Window, Long Window
        try:
            # Convert to Polars DataFrame for deduplication
            df = pl.DataFrame(reordered_portfolios)
            
            # Check for duplicate entries
            duplicate_count = len(df) - df.unique(subset=["Ticker", "Strategy Type", "Short Window", "Long Window"]).height
            
            if duplicate_count > 0:
                log(f"Found {duplicate_count} duplicate entries. Removing duplicates...", "warning")
                
                # Keep only unique combinations of the specified columns
                df = df.unique(subset=["Ticker", "Strategy Type", "Short Window", "Long Window"], keep="first")
                log(f"After deduplication: {len(df)} unique strategy combinations")
                
                # Convert back to list of dictionaries
                reordered_portfolios = df.to_dicts()
        except Exception as e:
            log(f"Error during deduplication: {str(e)}", "warning")
        
        # Sort portfolios if SORT_BY is specified in config
        if export_config.get("SORT_BY"):
            try:
                # Convert to Polars DataFrame for sorting
                df = pl.DataFrame(reordered_portfolios)
                
                # Apply sorting
                sort_by = export_config["SORT_BY"]
                sort_asc = export_config.get("SORT_ASC", False)
                
                if sort_by in df.columns:
                    # Sort the DataFrame
                    df = df.sort(sort_by, descending=not sort_asc)
                    log(f"Sorted results by {sort_by} ({'ascending' if sort_asc else 'descending'})")
                    
                    # Convert back to list of dictionaries
                    reordered_portfolios = df.to_dicts()
                    
                    # Ensure the sort order is preserved by setting it in the export_config
                    # This will be used by export_portfolios to maintain the order
                    export_config["_SORTED_PORTFOLIOS"] = reordered_portfolios
                else:
                    log(f"Warning: Sort column '{sort_by}' not found in results", "warning")
            except Exception as e:
                log(f"Error during sorting: {str(e)}", "warning")
        
        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios
        
        # Pass the export_config which may contain _SORTED_PORTFOLIOS if sorting was applied
-       _, success = export_portfolios(reordered_portfolios, export_config, 'portfolios', portfolio_name, log, feature_dir="")
+       # Change feature_dir to "strategies" to export to /csv/strategies instead of /csv/portfolios
+       _, success = export_portfolios(reordered_portfolios, export_config, 'portfolios', portfolio_name, log, feature_dir="strategies")
        if not success:
            log("Failed to export portfolios", "error")
            return False
        
        log("Portfolio summary exported successfully")
        return True
    else:
        log("No portfolios were processed", "warning")
        return False
```

### 4. Ensure Other Export Paths Remain Unchanged

All other export functions should continue to use `/csv/portfolios` and its subdirectories. No changes are needed for these export paths.

## Implementation Approach

1. **Sequential Updates**: Modify files in a specific order to minimize potential issues:
   - First, update the path resolution functions in `app/tools/portfolio/paths.py` to look in `/csv/strategies` for CSV files
   - Then update direct path references in the three main files
   - Finally, update the export path in `app/strategies/tools/summary_processing.py` to use `/csv/strategies`

2. **Verification**: After each file is modified, verify that:
   - All three files correctly read from `/csv/strategies`
   - `app/strategies/update_portfolios.py` exports to `/csv/strategies`
   - Other files still export to `/csv/portfolios` and its subdirectories

3. **No Backward Compatibility**: As specified in the requirements, we will not implement backward compatibility measures.

## Step-by-Step Implementation Plan

1. **Step 1: Update `app/tools/portfolio/paths.py`**
   - Modify the `resolve_portfolio_path` function to look in `/csv/strategies` for CSV files

2. **Step 2: Update `app/ma_cross/1_scanner.py`**
   - Change the direct path reference from `/csv/portfolios` to `/csv/strategies`

3. **Step 3: Update `app/concurrency/review.py`**
   - Change the direct path reference from `/csv/portfolios` to `/csv/strategies`

4. **Step 4: Update `app/ma_cross/tools/scanner_processing.py`**
   - Change the direct path reference from `/csv/portfolios` to `/csv/strategies`

5. **Step 5: Update `app/strategies/tools/summary_processing.py`**
   - Change the `feature_dir` parameter in the `export_portfolios` function call from `""` to `"strategies"`

6. **Step 6: Verify `app/strategies/update_portfolios.py`**
   - Ensure that it correctly reads files from `/csv/strategies`
   - Ensure that it correctly exports to `/csv/strategies`

7. **Step 7: Final Verification**
   - Verify that all three files correctly read from `/csv/strategies`
   - Verify that `app/strategies/update_portfolios.py` exports to `/csv/strategies`
   - Verify that other files still export to `/csv/portfolios` and its subdirectories

## Potential Risks and Considerations

1. **Missing Files**: If CSV files are not moved from `/csv/portfolios` to `/csv/strategies`, applications will fail with "file not found" errors.

2. **Inconsistent File Locations**: Having files read from one location but written to another (except for `app/strategies/update_portfolios.py`) could lead to confusion.

3. **Export Path Modification**: Special care must be taken to ensure that only `app/strategies/update_portfolios.py` exports to `/csv/strategies`, while all other export paths remain unchanged.

4. **File Overwriting**: If the same filename is used in both `/csv/portfolios` and `/csv/strategies`, there's a risk of confusion about which file is being used.

## Conclusion

This refactoring plan provides a comprehensive approach to changing the CSV file import directory from `/csv/portfolios` to `/csv/strategies` for all three files, while ensuring that only `app/strategies/update_portfolios.py` exports to the same location it imports from. By following these steps, we can ensure that the changes are implemented correctly and consistently.