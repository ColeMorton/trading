-- ============================================================================
-- Top N Strategies by Any Metric
-- ============================================================================
-- Description: Get top N strategies ordered by any performance metric
-- 
-- Parameters:
--   :metric_column - The column to order by (e.g., 'score', 'sharpe_ratio', 'total_return_pct')
--   :ticker - (Optional) Filter by ticker, use NULL or remove WHERE clause for all tickers
--   :limit - Number of results to return
--
-- Usage:
--   Uncomment and modify the ORDER BY clause based on desired metric
-- ============================================================================

SELECT 
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.sweep_run_id,
    sr.created_at as run_date,
    sr.fast_period,
    sr.slow_period,
    sr.signal_period,
    sr.score,
    sr.sharpe_ratio,
    sr.sortino_ratio,
    sr.calmar_ratio,
    sr.total_return_pct,
    sr.win_rate_pct,
    sr.profit_factor,
    sr.max_drawdown_pct,
    sr.expectancy_per_trade,
    sr.total_trades
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
-- WHERE t.ticker = :ticker  -- Optional: filter by ticker
ORDER BY sr.score DESC  -- Change column name here for different metrics
LIMIT 10;  -- Change limit as needed

-- Example variations:
-- ORDER BY sr.sharpe_ratio DESC        -- Best risk-adjusted returns
-- ORDER BY sr.total_return_pct DESC    -- Highest returns
-- ORDER BY sr.win_rate_pct DESC        -- Highest win rate
-- ORDER BY sr.profit_factor DESC       -- Best profit factor
-- ORDER BY sr.max_drawdown_pct ASC     -- Smallest drawdown

