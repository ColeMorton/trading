-- ============================================================================
-- Metric Analysis Views
-- ============================================================================
-- Views for analyzing metric types and their distributions
-- ============================================================================

-- ============================================================================
-- v_strategies_by_metric_type
-- ============================================================================
-- Purpose: Show strategies grouped by their metric type classifications
-- ============================================================================
CREATE OR REPLACE VIEW v_strategies_by_metric_type AS
SELECT
    mt.id as metric_type_id,
    mt.name as metric_type_name,
    mt.category as metric_category,
    t.ticker,
    st.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.score,
    sr.sharpe_ratio,
    sr.total_return_pct,
    sr.win_rate_pct,
    sr.sweep_run_id,
    sr.created_at as result_date,
    COUNT(*) OVER (PARTITION BY mt.id) as strategies_with_this_metric
FROM metric_types mt
JOIN strategy_sweep_result_metrics srm ON mt.id = srm.metric_type_id
JOIN strategy_sweep_results sr ON srm.sweep_result_id = sr.id
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
ORDER BY mt.category, mt.name, sr.score DESC;

COMMENT ON VIEW v_strategies_by_metric_type IS
'Strategies grouped by their assigned metric type classifications (e.g., "Most Sharpe Ratio").';

-- ============================================================================
-- v_metric_type_summary
-- ============================================================================
-- Purpose: Summary statistics for each metric type
-- ============================================================================
CREATE OR REPLACE VIEW v_metric_type_summary AS
SELECT
    mt.id,
    mt.name,
    mt.category,
    mt.description,
    COUNT(DISTINCT srm.sweep_result_id) as assigned_strategy_count,
    COUNT(DISTINCT sr.ticker_id) as ticker_count,
    COUNT(DISTINCT sr.sweep_run_id) as sweep_run_count,
    AVG(sr.score) as avg_score_of_strategies,
    MAX(sr.score) as max_score_of_strategies,
    MIN(sr.created_at) as first_assignment,
    MAX(sr.created_at) as latest_assignment
FROM metric_types mt
LEFT JOIN strategy_sweep_result_metrics srm ON mt.id = srm.metric_type_id
LEFT JOIN strategy_sweep_results sr ON srm.sweep_result_id = sr.id
GROUP BY mt.id, mt.name, mt.category, mt.description
ORDER BY assigned_strategy_count DESC NULLS LAST, mt.category, mt.name;

COMMENT ON VIEW v_metric_type_summary IS
'Summary statistics showing how many strategies have been assigned each metric type classification.';

-- ============================================================================
-- v_metric_leaders_by_category
-- ============================================================================
-- Purpose: Top strategy for each metric type
-- ============================================================================
CREATE OR REPLACE VIEW v_metric_leaders_by_category AS
WITH ranked_by_metric AS (
    SELECT
        mt.id as metric_type_id,
        mt.name as metric_type_name,
        mt.category,
        t.ticker,
        st.strategy_type,
        sr.fast_period,
        sr.slow_period,
        sr.score,
        sr.sharpe_ratio,
        sr.total_return_pct,
        sr.sweep_run_id,
        ROW_NUMBER() OVER (
            PARTITION BY mt.id
            ORDER BY sr.score DESC
        ) as rank_in_metric
    FROM metric_types mt
    JOIN strategy_sweep_result_metrics srm ON mt.id = srm.metric_type_id
    JOIN strategy_sweep_results sr ON srm.sweep_result_id = sr.id
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
)
SELECT
    metric_type_id,
    metric_type_name,
    category,
    ticker,
    strategy_type,
    fast_period,
    slow_period,
    score,
    sharpe_ratio,
    total_return_pct,
    sweep_run_id
FROM ranked_by_metric
WHERE rank_in_metric = 1
ORDER BY category, score DESC;

COMMENT ON VIEW v_metric_leaders_by_category IS
'The single best performing strategy for each metric type classification.';
