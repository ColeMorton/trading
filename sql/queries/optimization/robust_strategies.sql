-- ============================================================================
-- Robust Strategies Across Tickers
-- ============================================================================
-- Description: Find parameter combinations that perform consistently well
--              across multiple tickers (robust/universal strategies)
-- ============================================================================

WITH param_performance AS (
    SELECT
        sr.fast_period,
        sr.slow_period,
        st.strategy_type,
        COUNT(DISTINCT sr.ticker_id) as ticker_count,
        AVG(sr.score) as avg_score,
        STDDEV(sr.score) as stddev_score,
        MIN(sr.score) as min_score,
        MAX(sr.score) as max_score,
        AVG(sr.sharpe_ratio) as avg_sharpe,
        AVG(sr.win_rate_pct) as avg_win_rate,
        -- Coefficient of variation (consistency across tickers)
        CASE
            WHEN AVG(sr.score) > 0
            THEN STDDEV(sr.score) / AVG(sr.score)
            ELSE NULL
        END as cv,
        -- Percentage of tickers where this combo scores above median
        SUM(CASE WHEN sr.score > (
            SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY score)
            FROM strategy_sweep_results sr2
            WHERE sr2.ticker_id = sr.ticker_id
        ) THEN 1 ELSE 0 END)::numeric / COUNT(*) * 100 as pct_above_median
    FROM strategy_sweep_results sr
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    GROUP BY sr.fast_period, sr.slow_period, st.strategy_type
    HAVING COUNT(DISTINCT sr.ticker_id) >= 3  -- Tested on at least 3 tickers
)
SELECT
    fast_period,
    slow_period,
    strategy_type,
    ticker_count,
    avg_score,
    stddev_score,
    min_score,
    max_score,
    avg_sharpe,
    avg_win_rate,
    cv as consistency_coefficient,
    pct_above_median,
    -- Robustness score (high avg, low variation, works across tickers)
    avg_score / (1 + COALESCE(cv, 1)) * (pct_above_median / 100) as robustness_score
FROM param_performance
WHERE cv IS NOT NULL
ORDER BY robustness_score DESC
LIMIT 20;
