-- ============================================================================
-- Parameter Heatmap Data
-- ============================================================================
-- Description: Generate data for creating heatmaps of fast/slow period
--              combinations showing average performance
-- 
-- Parameters:
--   :ticker - (Optional) Filter by ticker
--   :strategy_type - (Optional) Filter by strategy type
--
-- Output: Grid data showing average score for each parameter combination
-- ============================================================================

SELECT 
    sr.fast_period,
    sr.slow_period,
    COUNT(*) as test_count,
    AVG(sr.score) as avg_score,
    STDDEV(sr.score) as stddev_score,
    MIN(sr.score) as min_score,
    MAX(sr.score) as max_score,
    AVG(sr.sharpe_ratio) as avg_sharpe,
    AVG(sr.total_return_pct) as avg_return,
    AVG(sr.win_rate_pct) as avg_win_rate,
    COUNT(DISTINCT sr.ticker_id) as ticker_count
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
-- WHERE t.ticker = :ticker  -- Optional filter
-- WHERE st.strategy_type = :strategy_type  -- Optional filter
GROUP BY sr.fast_period, sr.slow_period
HAVING COUNT(*) >= 2  -- At least 2 tests for relevance
ORDER BY sr.fast_period, sr.slow_period;

-- Use this data to create visualizations like:
-- - Heatmap with fast_period on X-axis, slow_period on Y-axis, color by avg_score
-- - Contour plot showing optimal parameter regions

