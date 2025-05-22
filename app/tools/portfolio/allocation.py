"""Allocation utility module for portfolio management.

This module provides utility functions for working with allocation percentages
in portfolio data. It handles validation, normalization, and calculation of
position sizes based on allocations.

The module implements the following special cases:
1. When Allocation [%] column exists but no values: maintain the column with empty values
2. When Allocation [%] column doesn't exist: add it with empty fields
3. When some rows have Allocation [%] values and others don't: assign equal values to empty ones
   so the sum equals 100%
"""

from typing import List, Dict, Any, Optional, Callable, Union, TypeVar, cast
import logging
from decimal import Decimal, ROUND_HALF_UP

# Type variable for generic portfolio data
T = TypeVar('T', Dict[str, Any], Dict[str, Union[str, float, int, None]])

def get_allocation_field_name(row: Dict[str, Any]) -> str:
    """Get the allocation field name from a row.
    
    Handles different variations of the allocation field name.
    
    Args:
        row: Dictionary representing a row in portfolio data
        
    Returns:
        str: The allocation field name
    """
    # Check for different variations of the allocation field name
    for field in ['Allocation [%]', 'Allocation']:
        if field in row:
            return field
    
    # Default field name if not found
    return 'Allocation [%]'

def validate_allocations(
    portfolio_data: List[T], 
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """Validate allocation values in portfolio data.
    
    Checks that allocation values are valid numbers between 0 and 100.
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function
        
    Returns:
        List of dictionaries with validated allocation values
    """
    if not portfolio_data:
        return []
    
    validated_data = []
    
    for row in portfolio_data:
        validated_row = dict(row)
        allocation_field = get_allocation_field_name(row)
        
        # Validate allocation value if present
        if allocation_field in row and row[allocation_field] not in (None, "", "None"):
            try:
                # Convert to float and validate range
                allocation_value = float(row[allocation_field])
                if allocation_value < 0 or allocation_value > 100:
                    if log:
                        log(f"Invalid allocation value {allocation_value} for {row.get('Ticker', 'Unknown')}: "
                            f"must be between 0 and 100. Setting to None.", "warning")
                    validated_row[allocation_field] = None
                else:
                    validated_row[allocation_field] = allocation_value
            except (ValueError, TypeError):
                if log:
                    log(f"Invalid allocation value {row[allocation_field]} for {row.get('Ticker', 'Unknown')}: "
                        f"must be a number. Setting to None.", "warning")
                validated_row[allocation_field] = None
        
        validated_data.append(validated_row)
    
    return validated_data

def normalize_allocations(
    portfolio_data: List[T],
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """Normalize allocation values in portfolio data.
    
    Ensures all rows have an allocation field with proper formatting.
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function
        
    Returns:
        List of dictionaries with normalized allocation values
    """
    if not portfolio_data:
        return []
    
    normalized_data = []
    standard_allocation_field = 'Allocation [%]'
    
    for row in portfolio_data:
        normalized_row = dict(row)
        
        # Find the allocation field if it exists with any variation
        allocation_field = None
        allocation_value = None
        
        for field in ['Allocation [%]', 'Allocation']:
            if field in row:
                allocation_field = field
                allocation_value = row[field]
                break
        
        # Normalize the field name to the standard format
        if allocation_field and allocation_field != standard_allocation_field:
            normalized_row[standard_allocation_field] = allocation_value
            del normalized_row[allocation_field]
        elif standard_allocation_field not in normalized_row:
            normalized_row[standard_allocation_field] = None
        
        normalized_data.append(normalized_row)
    
    return normalized_data

def distribute_missing_allocations(
    portfolio_data: List[T],
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """Distribute equal allocations to rows with missing allocation values.
    
    Handles the case where some rows have allocation values and others don't.
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function
        
    Returns:
        List of dictionaries with distributed allocation values
    """
    if not portfolio_data:
        return []
    
    # Create a copy of the data to avoid modifying the original
    distributed_data = [dict(row) for row in portfolio_data]
    allocation_field = 'Allocation [%]'
    
    # Count rows with and without allocations
    rows_with_allocations = 0
    rows_without_allocations = 0
    existing_allocation_sum = 0.0
    
    for row in distributed_data:
        if allocation_field not in row:
            row[allocation_field] = None
            rows_without_allocations += 1
            continue
            
        value = row[allocation_field]
        if value is not None and value != "" and value != "None":
            try:
                allocation_value = float(value)
                row[allocation_field] = allocation_value  # Ensure it's a float
                existing_allocation_sum += allocation_value
                rows_with_allocations += 1
            except (ValueError, TypeError):
                row[allocation_field] = None
                rows_without_allocations += 1
        else:
            row[allocation_field] = None
            rows_without_allocations += 1
    
    # If no rows have allocations, maintain empty values
    if rows_with_allocations == 0:
        if log:
            log("No allocation values found. Maintaining empty allocation column.", "info")
        return distributed_data
    
    # If some rows have allocations and others don't, distribute the remaining allocation
    if rows_without_allocations > 0:
        remaining_allocation = 100.0 - existing_allocation_sum
        
        if remaining_allocation > 0:
            equal_allocation = remaining_allocation / rows_without_allocations
            
            for row in distributed_data:
                if row[allocation_field] is None:
                    row[allocation_field] = equal_allocation
            
            if log:
                log(f"Distributed equal allocations of {equal_allocation:.2f}% "
                    f"to {rows_without_allocations} rows without allocations", "info")
    
    return distributed_data

def ensure_allocation_sum_100_percent(
    portfolio_data: List[T],
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """Ensure the sum of all allocations equals 100%.
    
    This function handles the following cases:
    1. When no rows have allocation values: maintain the column with empty values
    2. When all rows have allocation values but sum != 100%: scale to 100%
    3. When some rows have allocation values and others don't:
       distribute remaining allocation equally among rows without values
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function
        
    Returns:
        List of dictionaries with normalized allocations
    """
    if not portfolio_data:
        return []
    
    # Create a copy of the data to avoid modifying the original
    normalized_data = [dict(row) for row in portfolio_data]
    allocation_field = 'Allocation [%]'
    
    # Count rows with and without allocations
    rows_with_allocations = 0
    rows_without_allocations = 0
    
    for row in normalized_data:
        if allocation_field not in row:
            row[allocation_field] = None
            rows_without_allocations += 1
            continue
            
        allocation_value = row[allocation_field]
        if allocation_value is not None and allocation_value != "" and allocation_value != "None":
            # Try to convert to float to ensure it's a valid number
            try:
                float_value = float(allocation_value)
                if not isinstance(row[allocation_field], float):
                    row[allocation_field] = float_value
                rows_with_allocations += 1
            except (ValueError, TypeError):
                row[allocation_field] = None
                rows_without_allocations += 1
        else:
            row[allocation_field] = None
            rows_without_allocations += 1
    
    # Case 1: If no rows have allocations, maintain the column with empty values
    if rows_with_allocations == 0:
        if log:
            log("No allocation values found. Maintaining empty allocation column.", "info")
        return normalized_data
    
    # Calculate the sum of existing allocations
    allocation_sum = 0.0
    for row in normalized_data:
        value = row[allocation_field]
        if value is not None and value != "" and value != "None":
            try:
                allocation_sum += float(value)
            except (ValueError, TypeError):
                # Skip invalid values
                if log:
                    log(f"Skipping invalid allocation value: {value}", "warning")
    
    # Case 3: When some rows have allocation values and others don't
    if rows_with_allocations > 0 and rows_without_allocations > 0:
        if log:
            log(f"Found {rows_with_allocations} rows with allocations and "
                f"{rows_without_allocations} rows without allocations", "info")
        
        # Calculate the remaining allocation to distribute
        remaining_allocation = 100.0 - allocation_sum
        
        if remaining_allocation > 0:
            # Calculate equal allocation for rows without allocation
            equal_allocation = remaining_allocation / rows_without_allocations
            
            # Distribute equal allocations
            for row in normalized_data:
                if row[allocation_field] is None:
                    row[allocation_field] = equal_allocation
            
            if log:
                log(f"Distributed equal allocations of {equal_allocation:.2f}% "
                    f"to {rows_without_allocations} rows without allocations", "info")
            
            # Update allocation sum after distribution
            allocation_sum = 100.0
    
    # Case 2: When all rows have allocation values but sum != 100%
    if abs(allocation_sum - 100.0) > 0.01:  # Allow for small floating-point errors
        if log:
            log(f"Allocation sum is {allocation_sum:.2f}%, adjusting to 100%", "info")
        
        # Scale factor to adjust allocations
        scale_factor = 100.0 / allocation_sum if allocation_sum > 0 else 0
        
        # Adjust allocations
        for row in normalized_data:
            value = row[allocation_field]
            if value is not None and value != "" and value != "None":
                try:
                    row[allocation_field] = float(value) * scale_factor
                except (ValueError, TypeError):
                    # Skip invalid values
                    if log:
                        log(f"Skipping invalid allocation value during scaling: {value}", "warning")
                    row[allocation_field] = None
    
    return normalized_data

def calculate_position_sizes(
    portfolio_data: List[T],
    account_value: float,
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> List[Dict[str, Any]]:
    """Calculate position sizes based on allocations and account value.
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        account_value: Total account value to allocate
        log: Optional logging function
        
    Returns:
        List of dictionaries with position sizes added
    """
    if not portfolio_data or account_value <= 0:
        return portfolio_data
    
    # First ensure allocations are valid and sum to 100%
    normalized_data = ensure_allocation_sum_100_percent(portfolio_data, log)
    allocation_field = 'Allocation [%]'
    
    # Add position size to each row
    for row in normalized_data:
        allocation = row.get(allocation_field)
        if allocation is not None and allocation != "" and allocation != "None":
            try:
                allocation_decimal = float(allocation) / 100.0  # Convert percentage to decimal
                position_size = account_value * allocation_decimal
                
                # Round to 2 decimal places for currency values
                position_size_decimal = Decimal(str(position_size)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                row['Position Size'] = float(position_size_decimal)
            except (ValueError, TypeError):
                if log:
                    log(f"Could not calculate position size for {row.get('Ticker', 'Unknown')}: "
                        f"invalid allocation value {allocation}", "warning")
                row['Position Size'] = 0.0
        else:
            row['Position Size'] = 0.0
    
    return normalized_data

def get_allocation_summary(
    portfolio_data: List[T],
    log: Optional[Callable[[str, Optional[str]], None]] = None
) -> Dict[str, Any]:
    """Get a summary of allocation statistics for the portfolio.
    
    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function
        
    Returns:
        Dictionary with allocation summary statistics
    """
    if not portfolio_data:
        return {
            "total_allocation": 0.0,
            "allocated_rows": 0,
            "unallocated_rows": 0,
            "total_rows": 0,
            "has_complete_allocation": False
        }
    
    allocation_field = 'Allocation [%]'
    allocated_rows = 0
    unallocated_rows = 0
    total_allocation = 0.0
    
    for row in portfolio_data:
        if allocation_field in row and row[allocation_field] not in (None, "", "None"):
            try:
                allocation = float(row[allocation_field])
                total_allocation += allocation
                allocated_rows += 1
            except (ValueError, TypeError):
                unallocated_rows += 1
        else:
            unallocated_rows += 1
    
    total_rows = allocated_rows + unallocated_rows
    has_complete_allocation = abs(total_allocation - 100.0) < 0.01 and unallocated_rows == 0
    
    return {
        "total_allocation": total_allocation,
        "allocated_rows": allocated_rows,
        "unallocated_rows": unallocated_rows,
        "total_rows": total_rows,
        "has_complete_allocation": has_complete_allocation
    }