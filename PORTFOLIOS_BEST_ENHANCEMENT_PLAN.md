# Portfolios Best Export Enhancement Implementation Plan

## Overview
This plan outlines the implementation of enhanced export functionality for portfolios_best CSV files, adding deduplication and metric type concatenation with proper sorting.

## Current State Analysis

### Current Export Flow
1. **PortfolioOrchestrator** (`app/tools/orchestration/portfolio_orchestrator.py`)
   - Calls `export_best_portfolios` after filtering portfolios
   - Sorts by `config['SORT_BY']` (default: 'Total Return [%]')

2. **export_best_portfolios** (`app/tools/portfolio/collection.py`)
   - Sorts portfolios using `sort_portfolios` function
   - Calls `export_portfolios` with `export_type="portfolios_best"`

3. **export_portfolios** (`app/tools/strategy/export_portfolios.py`)
   - Converts portfolios to Polars DataFrame
   - Handles column transformations and formatting
   - Calls `export_csv` to write the file

4. **export_csv** (`app/tools/export_csv.py`)
   - Creates directories and writes CSV file
   - Handles filename generation with timestamp

### Current Limitations
- No deduplication based on unique strategy configuration
- No handling of multiple Metric Type values
- Sorts by Total Return [%] instead of Score
- No metric type concatenation or sorting

## Required Changes

### 1. Add Score Column Support
- Ensure Score column is included in portfolio data
- Modify sorting to use Score instead of Total Return [%]

### 2. Implement Deduplication Logic
- Create unique ID from: Ticker + Strategy Type + Short Window + Long Window
- Group by unique ID and aggregate data
- Keep highest score entry for each unique configuration

### 3. Implement Metric Type Concatenation
- Collect all Metric Type values for each unique configuration
- Sort by priority: Most → Mean → Median → Least
- Concatenate with comma separation

## Implementation Details

### Phase 1: Update Portfolio Data Structure
**File: `app/tools/portfolio/collection.py`**

```python
def deduplicate_and_aggregate_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log: Optional[Callable] = None
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """
    Deduplicate portfolios based on unique strategy configuration and 
    aggregate metric types.
    
    Args:
        portfolios: Portfolio data
        log: Logging function
        
    Returns:
        Deduplicated portfolios with aggregated metric types
    """
    # Implementation details in Phase 2
```

### Phase 2: Implement Deduplication Function
**File: `app/tools/portfolio/collection.py`**

```python
def deduplicate_and_aggregate_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log: Optional[Callable] = None
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Deduplicate portfolios and aggregate metric types."""
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios
    
    # Create unique ID
    df = df.with_columns(
        (pl.col("Ticker").cast(pl.Utf8) + "_" + 
         pl.col("Strategy Type").cast(pl.Utf8) + "_" + 
         pl.col("Short Window").cast(pl.Utf8) + "_" + 
         pl.col("Long Window").cast(pl.Utf8)).alias("unique_id")
    )
    
    # Sort by Score descending
    df = df.sort("Score", descending=True)
    
    # Define metric type sorting function
    def sort_metric_types(metrics_list: List[str]) -> str:
        def get_priority(metric: str) -> int:
            if metric.strip().startswith('Most'):
                return 1
            elif metric.strip().startswith('Mean'):
                return 2
            elif metric.strip().startswith('Median'):
                return 3
            elif metric.strip().startswith('Least'):
                return 4
            else:
                return 5
        
        sorted_metrics = sorted(metrics_list, key=lambda x: (get_priority(x), x))
        return ', '.join(sorted_metrics)
    
    # Group by unique_id and aggregate
    agg_exprs = []
    for col in df.columns:
        if col == "Metric Type":
            # Aggregate and sort metric types
            agg_exprs.append(
                pl.col(col).list().map_elements(sort_metric_types).alias(col)
            )
        elif col != "unique_id":
            # Keep first value (highest score) for other columns
            agg_exprs.append(pl.col(col).first().alias(col))
    
    df_grouped = df.group_by("unique_id").agg(agg_exprs)
    
    # Drop the temporary unique_id column
    df_grouped = df_grouped.drop("unique_id")
    
    # Sort by Score again to ensure proper order
    df_grouped = df_grouped.sort("Score", descending=True)
    
    if log:
        log(f"Deduplicated portfolios from {len(df)} to {len(df_grouped)} rows", "info")
    
    return df_grouped.to_dicts() if input_is_list else df_grouped
```

### Phase 3: Update export_best_portfolios Function
**File: `app/tools/portfolio/collection.py`**

```python
def export_best_portfolios(
    portfolios: List[Dict[str, Any]],
    config: Config,
    log: callable
) -> bool:
    """Export the best portfolios to a CSV file with deduplication."""
    if not portfolios:
        log("No portfolios to export", "warning")
        return False
        
    try:
        # Ensure Score column exists
        if portfolios and "Score" not in portfolios[0]:
            log("Warning: Score column not found, using Total Return [%] as fallback", "warning")
            for p in portfolios:
                p["Score"] = p.get("Total Return [%]", 0)
        
        # Sort by Score instead of Total Return [%]
        original_sort_by = config.get('SORT_BY', 'Total Return [%]')
        config['SORT_BY'] = 'Score'
        
        # Sort portfolios
        sorted_portfolios = sort_portfolios(portfolios, config)
        
        # Apply deduplication and metric type aggregation
        deduplicated_portfolios = deduplicate_and_aggregate_portfolios(
            sorted_portfolios, log
        )
        
        # Restore original sort configuration
        config['SORT_BY'] = original_sort_by
        
        # Import and call export function
        from app.tools.strategy.export_portfolios import export_portfolios
        
        export_portfolios(
            portfolios=deduplicated_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log
        )
        
        log(f"Exported {len(deduplicated_portfolios)} unique portfolios sorted by Score")
        return True
        
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False
```

### Phase 4: Update MA Cross Strategy to Include Score
**File: `app/strategies/ma_cross/1_get_portfolios.py`**

Ensure that the Score column is calculated and included in portfolio results. This may require:
1. Adding Score calculation to the strategy processing
2. Ensuring Score is passed through the entire pipeline

### Phase 5: Testing and Validation
1. Create unit tests for deduplication function
2. Create integration tests for full export flow
3. Test with sample data containing duplicates
4. Validate metric type sorting

## Testing Strategy

### Unit Tests
**File: `tests/test_portfolio_deduplication.py`**

```python
def test_deduplicate_portfolios():
    """Test portfolio deduplication logic."""
    # Test data with duplicates
    portfolios = [
        {"Ticker": "BTC", "Strategy Type": "SMA", "Short Window": 5, 
         "Long Window": 20, "Score": 1.5, "Metric Type": "Most Profit"},
        {"Ticker": "BTC", "Strategy Type": "SMA", "Short Window": 5, 
         "Long Window": 20, "Score": 1.2, "Metric Type": "Least Loss"},
    ]
    
    result = deduplicate_and_aggregate_portfolios(portfolios)
    
    assert len(result) == 1
    assert result[0]["Score"] == 1.5
    assert "Most Profit, Least Loss" in result[0]["Metric Type"]

def test_metric_type_sorting():
    """Test metric type sorting logic."""
    metrics = ["Least Win Rate", "Most Profit", "Mean Return", "Median Sharpe"]
    sorted_metrics = sort_metric_types(metrics)
    
    expected = "Most Profit, Mean Return, Median Sharpe, Least Win Rate"
    assert sorted_metrics == expected
```

### Integration Tests
1. Test full export flow with duplicate data
2. Verify CSV output format
3. Test backward compatibility

## Rollout Plan

1. **Phase 1**: Implement deduplication function (1 day)
2. **Phase 2**: Update export_best_portfolios (1 day)
3. **Phase 3**: Add Score column support (1-2 days)
4. **Phase 4**: Testing and validation (1 day)
5. **Phase 5**: Documentation and deployment (1 day)

## Backward Compatibility

- Existing exports without Score column will fall back to Total Return [%]
- Existing single Metric Type values will be preserved
- No changes to file naming or directory structure

## Future Enhancements

1. Make deduplication configurable (enable/disable)
2. Allow custom unique ID components
3. Support different aggregation strategies for metrics
4. Add export format versioning for future changes

## Implementation Priority

1. **High Priority**: Core deduplication and aggregation logic
2. **Medium Priority**: Score column support
3. **Low Priority**: Configuration options and future enhancements