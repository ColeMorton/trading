-- ============================================================================
-- Optimal Parameters by Ticker
-- ============================================================================
-- Description: Find optimal fast/slow parameters for each ticker using
--              multiple criteria (score, sharpe, consistency)
-- ============================================================================

WITH ticker_param_stats AS (
    SELECT 
        sr.ticker_id,
        t.ticker,
        sr.fast_period,
        sr.slow_period,
        COUNT(*) as test_count,
        AVG(sr.score) as avg_score,
        STDDEV(sr.score) as stddev_score,
        AVG(sr.sharpe_ratio) as avg_sharpe,
        AVG(sr.total_return_pct) as avg_return,
        AVG(sr.win_rate_pct) as avg_win_rate,
        AVG(sr.max_drawdown_pct) as avg_drawdown,
        -- Consistency metric (lower is better)
        CASE 
            WHEN AVG(sr.score) > 0 
            THEN STDDEV(sr.score) / AVG(sr.score)
            ELSE NULL
        END as coefficient_of_variation
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    GROUP BY sr.ticker_id, t.ticker, sr.fast_period, sr.slow_period
    HAVING COUNT(*) >= 2  -- At least 2 tests
),
ranked_params AS (
    SELECT 
        *,
        ROW_NUMBER() OVER (
            PARTITION BY ticker_id 
            ORDER BY avg_score DESC
        ) as rank_by_score,
        ROW_NUMBER() OVER (
            PARTITION BY ticker_id 
            ORDER BY avg_sharpe DESC NULLS LAST
        ) as rank_by_sharpe,
        ROW_NUMBER() OVER (
            PARTITION BY ticker_id 
            ORDER BY coefficient_of_variation ASC NULLS LAST
        ) as rank_by_consistency
    FROM ticker_param_stats
)
SELECT 
    ticker,
    fast_period,
    slow_period,
    test_count,
    avg_score,
    avg_sharpe,
    avg_return,
    avg_win_rate,
    avg_drawdown,
    coefficient_of_variation,
    rank_by_score,
    rank_by_sharpe,
    rank_by_consistency,
    -- Composite rank (lower is better)
    (rank_by_score + rank_by_sharpe + rank_by_consistency) as composite_rank
FROM ranked_params
WHERE rank_by_score <= 5  -- Top 5 by score
ORDER BY ticker, composite_rank;

