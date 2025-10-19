-- ============================================================================
-- Sweep Run Analysis Views
-- ============================================================================
-- Views for comparing and analyzing different sweep runs
-- ============================================================================

-- ============================================================================
-- v_sweep_run_summary
-- ============================================================================
-- Purpose: Comprehensive overview of each sweep run
-- ============================================================================
CREATE OR REPLACE VIEW v_sweep_run_summary AS
WITH sweep_basics AS (
    SELECT 
        sr.sweep_run_id,
        MIN(sr.created_at) as run_date,
        COUNT(*) as result_count,
        COUNT(DISTINCT sr.ticker_id) as ticker_count,
        COUNT(DISTINCT st.strategy_type) as strategy_count
    FROM strategy_sweep_results sr
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    GROUP BY sr.sweep_run_id
),
sweep_performance AS (
    SELECT 
        sr.sweep_run_id,
        AVG(sr.score) as avg_score,
        STDDEV(sr.score) as stddev_score,
        MIN(sr.score) as min_score,
        MAX(sr.score) as max_score,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sr.score) as median_score,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY sr.score) as q1_score,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY sr.score) as q3_score,
        AVG(sr.sharpe_ratio) as avg_sharpe,
        AVG(sr.total_return_pct) as avg_return,
        AVG(sr.win_rate_pct) as avg_win_rate,
        AVG(sr.max_drawdown_pct) as avg_drawdown
    FROM strategy_sweep_results sr
    GROUP BY sr.sweep_run_id
),
best_in_sweep AS (
    SELECT DISTINCT ON (sr.sweep_run_id)
        sr.sweep_run_id,
        t.ticker as best_ticker,
        st.strategy_type as best_strategy,
        sr.fast_period as best_fast,
        sr.slow_period as best_slow,
        sr.score as best_score
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    ORDER BY sr.sweep_run_id, sr.score DESC
)
SELECT 
    sb.sweep_run_id,
    sb.run_date,
    sb.result_count,
    sb.ticker_count,
    sb.strategy_count,
    sp.avg_score,
    sp.stddev_score,
    sp.min_score,
    sp.max_score,
    sp.median_score,
    sp.q1_score,
    sp.q3_score,
    sp.avg_sharpe,
    sp.avg_return,
    sp.avg_win_rate,
    sp.avg_drawdown,
    bis.best_ticker,
    bis.best_strategy,
    bis.best_fast,
    bis.best_slow,
    bis.best_score
FROM sweep_basics sb
JOIN sweep_performance sp ON sb.sweep_run_id = sp.sweep_run_id
JOIN best_in_sweep bis ON sb.sweep_run_id = bis.sweep_run_id
ORDER BY sb.run_date DESC;

COMMENT ON VIEW v_sweep_run_summary IS 
'Comprehensive summary statistics for each sweep run including best performer and distribution metrics.';

-- ============================================================================
-- v_sweep_comparison
-- ============================================================================
-- Purpose: Compare performance across sweep runs with trends
-- ============================================================================
CREATE OR REPLACE VIEW v_sweep_comparison AS
WITH sweep_metrics AS (
    SELECT 
        sr.sweep_run_id,
        sr.ticker_id,
        t.ticker,
        sr.strategy_type_id,
        st.strategy_type,
        MIN(sr.created_at) as run_date,
        MAX(sr.score) as best_score,
        AVG(sr.score) as avg_score,
        MAX(sr.sharpe_ratio) as best_sharpe,
        MAX(sr.total_return_pct) as best_return,
        COUNT(*) as result_count
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    GROUP BY sr.sweep_run_id, sr.ticker_id, t.ticker, sr.strategy_type_id, st.strategy_type
),
sweep_with_prev AS (
    SELECT 
        *,
        LAG(best_score) OVER (
            PARTITION BY ticker_id, strategy_type_id 
            ORDER BY run_date
        ) as prev_best_score,
        LAG(run_date) OVER (
            PARTITION BY ticker_id, strategy_type_id 
            ORDER BY run_date
        ) as prev_run_date,
        ROW_NUMBER() OVER (
            PARTITION BY ticker_id, strategy_type_id 
            ORDER BY run_date DESC
        ) as recency_rank
    FROM sweep_metrics
)
SELECT 
    sweep_run_id,
    run_date,
    ticker,
    strategy_type,
    best_score,
    avg_score,
    best_sharpe,
    best_return,
    result_count,
    prev_best_score,
    prev_run_date,
    CASE 
        WHEN prev_best_score IS NOT NULL 
        THEN best_score - prev_best_score
        ELSE NULL
    END as score_change,
    CASE 
        WHEN prev_best_score IS NOT NULL AND prev_best_score > 0
        THEN ((best_score - prev_best_score) / prev_best_score) * 100
        ELSE NULL
    END as score_change_pct,
    CASE 
        WHEN prev_run_date IS NOT NULL
        THEN run_date - prev_run_date
        ELSE NULL
    END as days_since_prev_sweep,
    recency_rank
FROM sweep_with_prev
ORDER BY run_date DESC, best_score DESC;

COMMENT ON VIEW v_sweep_comparison IS 
'Compare sweep runs over time showing score changes and trends per ticker/strategy combination.';

-- ============================================================================
-- v_parameter_evolution
-- ============================================================================
-- Purpose: Track how optimal parameters change across sweep runs
-- ============================================================================
CREATE OR REPLACE VIEW v_parameter_evolution AS
WITH best_params_per_sweep AS (
    SELECT DISTINCT ON (sr.sweep_run_id, sr.ticker_id, sr.strategy_type_id)
        sr.sweep_run_id,
        MIN(sr.created_at) OVER (PARTITION BY sr.sweep_run_id) as run_date,
        t.ticker,
        st.strategy_type,
        sr.fast_period,
        sr.slow_period,
        sr.signal_period,
        sr.score,
        sr.sharpe_ratio
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    ORDER BY sr.sweep_run_id, sr.ticker_id, sr.strategy_type_id, sr.score DESC
)
SELECT 
    sweep_run_id,
    run_date,
    ticker,
    strategy_type,
    fast_period,
    slow_period,
    signal_period,
    score,
    sharpe_ratio,
    LAG(fast_period) OVER (
        PARTITION BY ticker, strategy_type 
        ORDER BY run_date
    ) as prev_fast_period,
    LAG(slow_period) OVER (
        PARTITION BY ticker, strategy_type 
        ORDER BY run_date
    ) as prev_slow_period,
    LAG(score) OVER (
        PARTITION BY ticker, strategy_type 
        ORDER BY run_date
    ) as prev_score,
    ROW_NUMBER() OVER (
        PARTITION BY ticker, strategy_type 
        ORDER BY run_date
    ) as sweep_number
FROM best_params_per_sweep
ORDER BY ticker, strategy_type, run_date DESC;

COMMENT ON VIEW v_parameter_evolution IS 
'Track how optimal parameter values change across successive sweep runs for each ticker/strategy.';

-- ============================================================================
-- v_sweep_coverage
-- ============================================================================
-- Purpose: Analyze parameter space coverage in each sweep
-- ============================================================================
CREATE OR REPLACE VIEW v_sweep_coverage AS
SELECT 
    sr.sweep_run_id,
    MIN(sr.created_at) as run_date,
    COUNT(DISTINCT sr.ticker_id) as tickers_tested,
    COUNT(DISTINCT st.strategy_type) as strategies_tested,
    MIN(sr.fast_period) as min_fast,
    MAX(sr.fast_period) as max_fast,
    MIN(sr.slow_period) as min_slow,
    MAX(sr.slow_period) as max_slow,
    COUNT(DISTINCT (sr.fast_period, sr.slow_period)) as unique_param_combinations,
    COUNT(*) as total_tests,
    ROUND(
        COUNT(*) / NULLIF(COUNT(DISTINCT (sr.fast_period, sr.slow_period)), 0)::numeric, 
        2
    ) as avg_tests_per_combination
FROM strategy_sweep_results sr
JOIN strategy_types st ON sr.strategy_type_id = st.id
GROUP BY sr.sweep_run_id
ORDER BY run_date DESC;

COMMENT ON VIEW v_sweep_coverage IS 
'Analyze parameter space coverage and test distribution for each sweep run.';

