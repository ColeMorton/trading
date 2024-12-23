# Changes Log

## 2024-03-19

### Enhanced Portfolio Analysis and Export
- **Files Modified**:
  1. `app/ema_cross/tools/sensitivity_analysis.py`:
     - Added required portfolio statistics during analysis
     - Added 'Ticker' from config to identify portfolio source
     - Added 'Use SMA' flag from config to indicate strategy type
     - Ensures all required columns are available for reordering
     - Fixes portfolio processing errors by providing complete statistics

  2. `app/ema_cross/1_get_portfolios.py`:
     - Fixed best portfolios collection and export
     - Added missing best portfolio append operation
     - Ensures best portfolios are properly collected for export
     - Enables successful export to portfolios_best directory

  3. `app/ema_cross/tools/portfolio_selection.py`:
     - Modified get_best_portfolio function to remove "Metric Type" column
     - Updated all three portfolio return points to clean data
     - Ensures clean data structure in best portfolio exports
     - Maintains data consistency across the export pipeline

## 2024-03-20

### Dynamic Moving Average Column Naming
- **Files Modified**:
  1. `app/ema_cross/tools/portfolio_selection.py`:
     - Renamed "Short Window" to "SMA_FAST" or "EMA_FAST" based on "Use SMA" flag
     - Renamed "Long Window" to "SMA_SLOW" or "EMA_SLOW" based on "Use SMA" flag
     - Updated column references throughout get_best_portfolio function
     - Added "Use SMA" to required columns check
     - Modified log messages to reflect dynamic column names
     - Ensures consistent naming convention across SMA and EMA strategies

## 2024-03-21

### Consolidated Portfolio Export Files
- **Files Modified**:
  1. `app/ema_cross/tools/export_portfolios.py`:
     - Modified export behavior for portfolios_best type
     - Disabled MA suffix in filename when exporting portfolios_best
     - Added handling for combined SMA and EMA portfolios in single D.csv file
     - Implemented automatic column creation for SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW
     - Added conditional logic to populate appropriate columns based on strategy type
     - Set null values for non-applicable columns (EMA columns for SMA portfolios and vice versa)
     - Defined specific column ordering with EMA_FAST and EMA_SLOW at indexes 4 and 5
     - Ensures consistent data structure and column ordering across different strategy types

  2. `app/ema_cross/1_get_portfolios.py`:
     - Added new run_both_strategies function to handle combined strategy execution
     - Implemented accumulation of best portfolios from both EMA and SMA runs
     - Added separate logging for combined strategy execution
     - Modified main execution to use combined strategy function
     - Ensures both EMA and SMA portfolios are included in final export