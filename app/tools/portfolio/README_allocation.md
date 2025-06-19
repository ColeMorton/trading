# Allocation Utility Module

This module provides utility functions for working with allocation percentages in portfolio data. It handles validation, normalization, and calculation of position sizes based on allocations.

## Overview

The allocation utility module is designed to handle various allocation scenarios in portfolio management:

1. **Empty Allocations**: When the Allocation [%] column exists but no values are provided
2. **Partial Allocations**: When some rows have allocation values and others don't
3. **Invalid Allocations**: When allocation values are invalid or out of range
4. **Unbalanced Allocations**: When allocation values don't sum to 100%

## Key Functions

### `validate_allocations(portfolio_data, log=None)`

Validates allocation values in portfolio data, ensuring they are valid numbers between 0 and 100.

```python
from app.tools.portfolio import validate_allocations

# Validate allocation values
validated_data = validate_allocations(portfolio_data, log_function)
```

### `normalize_allocations(portfolio_data, log=None)`

Normalizes allocation values in portfolio data, ensuring all rows have an allocation field with proper formatting.

```python
from app.tools.portfolio import normalize_allocations

# Normalize allocation values
normalized_data = normalize_allocations(portfolio_data, log_function)
```

### `distribute_missing_allocations(portfolio_data, log=None)`

Distributes equal allocations to rows with missing allocation values.

```python
from app.tools.portfolio import distribute_missing_allocations

# Distribute missing allocations
distributed_data = distribute_missing_allocations(portfolio_data, log_function)
```

### `ensure_allocation_sum_100_percent(portfolio_data, log=None)`

Ensures the sum of all allocations equals 100%.

```python
from app.tools.portfolio import ensure_allocation_sum_100_percent

# Ensure allocations sum to 100%
adjusted_data = ensure_allocation_sum_100_percent(portfolio_data, log_function)
```

### `calculate_position_sizes(portfolio_data, account_value, log=None)`

Calculates position sizes based on allocations and account value.

```python
from app.tools.portfolio import calculate_position_sizes

# Calculate position sizes
account_value = 100000.0
position_data = calculate_position_sizes(portfolio_data, account_value, log_function)
```

### `get_allocation_summary(portfolio_data, log=None)`

Gets a summary of allocation statistics for the portfolio.

```python
from app.tools.portfolio import get_allocation_summary

# Get allocation summary
summary = get_allocation_summary(portfolio_data, log_function)
```

## Special Cases Handling

The module handles these specific cases:

1. **Case 1**: When Allocation [%] column exists (Extended Schema) yet no Allocation values exist in any row

   - The column is maintained with empty values

2. **Case 2**: When Allocation [%] column does not exist (Base Schema)

   - The system adds the column with empty fields

3. **Case 3**: When Allocation [%] column exists (Extended Schema) and some rows contain Allocation values while some do not

   - The empty Allocation [%] values are assigned equal values
   - The sum of all Allocations equals 100%

4. **Case 4**: When all rows have allocation values but they don't sum to 100%
   - The values are scaled proportionally to ensure they sum to 100%

## Usage Example

```python
from app.tools.portfolio import (
    validate_allocations,
    normalize_allocations,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    calculate_position_sizes,
    get_allocation_summary
)

# Sample portfolio data
portfolio_data = [
    {"Ticker": "AAPL", "Allocation [%]": 30, "Strategy Type": "SMA"},
    {"Ticker": "MSFT", "Allocation [%]": None, "Strategy Type": "SMA"},
    {"Ticker": "GOOG", "Allocation [%]": 40, "Strategy Type": "SMA"}
]

# Process the data
validated_data = validate_allocations(portfolio_data)
normalized_data = normalize_allocations(validated_data)
distributed_data = distribute_missing_allocations(normalized_data)
adjusted_data = ensure_allocation_sum_100_percent(distributed_data)

# Calculate position sizes
account_value = 100000.0
position_data = calculate_position_sizes(adjusted_data, account_value)

# Get allocation summary
summary = get_allocation_summary(position_data)
```

## Integration with Schema Detection

The allocation utility module works seamlessly with the schema detection module to handle different CSV schema versions:

```python
from app.tools.portfolio import (
    detect_schema_version,
    normalize_portfolio_data,
    ensure_allocation_sum_100_percent,
    calculate_position_sizes
)

# Detect schema version
schema_version = detect_schema_version(csv_data)

# Normalize data based on schema version
normalized_data = normalize_portfolio_data(csv_data, schema_version)

# Ensure allocations sum to 100%
adjusted_data = ensure_allocation_sum_100_percent(normalized_data)

# Calculate position sizes
account_value = 100000.0
position_data = calculate_position_sizes(adjusted_data, account_value)
```
