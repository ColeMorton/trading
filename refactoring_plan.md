# Refactoring Plan: CSV Directory Path Change

## Overview

This refactoring plan outlines the steps needed to change the directory from which CSV files are imported from `/csv/portfolios` to `/csv/strategies`. The plan focuses on three main files:

1. `app/ma_cross/1_scanner.py`
2. `app/strategies/update_portfolios.py`
3. `app/concurrency/review.py`

All export paths will remain unchanged, continuing to use `/csv/portfolios` and its subdirectories.

## Affected Components

### 1. Files with Direct Import Path References

- `app/ma_cross/1_scanner.py` - Line 112: `f'./csv/portfolios/{config["PORTFOLIO"]}'`
- `app/concurrency/review.py` - Line 160: `csv_path = Path(f"csv/portfolios/{portfolio_name}.csv")`
- `app/ma_cross/tools/scanner_processing.py` - Line 141: `portfolio_path = os.path.join("./csv/portfolios", config["PORTFOLIO"])`

### 2. Indirect Import References via Portfolio Loading Functions

- `app/strategies/update_portfolios.py` - Uses `load_portfolio` function which internally resolves paths

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

### 3. Ensure Export Paths Remain Unchanged

All export functions should continue to use `/csv/portfolios` and its subdirectories. No changes are needed for export paths.

## Implementation Approach

1. **Sequential Updates**: Modify files in a specific order to minimize potential issues:
   - First, update the path resolution functions in `app/tools/portfolio/paths.py` to look in `/csv/strategies` for CSV files
   - Then update direct path references in the three main files

2. **Verification**: After each file is modified, verify that:
   - Files are correctly read from `/csv/strategies`
   - Files are still written to `/csv/portfolios` and its subdirectories

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

5. **Step 5: Verify `app/strategies/update_portfolios.py`**
   - This file uses the `load_portfolio` function which should now look in `/csv/strategies`

6. **Step 6: Final Verification**
   - Verify that all three files correctly read from `/csv/strategies`
   - Verify that all export operations still write to `/csv/portfolios` and its subdirectories

## Potential Risks and Considerations

1. **Missing Files**: If CSV files are not moved from `/csv/portfolios` to `/csv/strategies`, applications will fail with "file not found" errors.

2. **Inconsistent File Locations**: Having files read from one location but written to another could lead to confusion and potential issues if files need to be read immediately after being written.

3. **Export Path Preservation**: Special care must be taken to ensure that all export paths remain unchanged, as modifying them could break downstream processes.

## Conclusion

This refactoring plan provides a comprehensive approach to changing the CSV file import directory from `/csv/portfolios` to `/csv/strategies` while maintaining the existing export paths. By following these steps, we can ensure that files are read from the new location while preserving the existing export behavior.