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