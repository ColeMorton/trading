-- ============================================================================
-- Performance Analysis Views
-- ============================================================================
-- Views for analyzing strategy performance across different dimensions
-- ============================================================================

-- ============================================================================
-- v_top_performers_by_ticker
-- ============================================================================
-- Purpose: Top N performing strategies for each ticker across all sweeps
-- ============================================================================
CREATE OR REPLACE VIEW v_top_performers_by_ticker AS
WITH ranked_by_ticker AS (
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
        sr.total_return_pct,
        sr.win_rate_pct,
        sr.profit_factor,
        sr.max_drawdown_pct,
        sr.total_trades,
        ROW_NUMBER() OVER (
            PARTITION BY sr.ticker_id
            ORDER BY sr.score DESC
        ) as rank_for_ticker,
        PERCENT_RANK() OVER (
            PARTITION BY sr.ticker_id
            ORDER BY sr.score
        ) as percentile
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
)
SELECT *
FROM ranked_by_ticker
WHERE rank_for_ticker <= 20  -- Top 20 per ticker
ORDER BY ticker, rank_for_ticker;

COMMENT ON VIEW v_top_performers_by_ticker IS
'Top 20 performing strategies for each ticker across all sweep runs.';

-- ============================================================================
-- v_risk_adjusted_rankings
-- ============================================================================
-- Purpose: Rank strategies by composite risk-adjusted performance
-- ============================================================================
CREATE OR REPLACE VIEW v_risk_adjusted_rankings AS
WITH normalized_metrics AS (
    SELECT
        sr.id,
        t.ticker,
        st.strategy_type,
        sr.sweep_run_id,
        sr.fast_period,
        sr.slow_period,
        sr.score,
        sr.sharpe_ratio,
        sr.sortino_ratio,
        sr.calmar_ratio,
        sr.omega_ratio,
        sr.max_drawdown_pct,
        sr.total_return_pct,
        sr.win_rate_pct,
        -- Normalize metrics to 0-1 scale for composite ranking
        PERCENT_RANK() OVER (ORDER BY sr.sharpe_ratio) as sharpe_rank,
        PERCENT_RANK() OVER (ORDER BY sr.sortino_ratio) as sortino_rank,
        PERCENT_RANK() OVER (ORDER BY sr.calmar_ratio) as calmar_rank,
        PERCENT_RANK() OVER (ORDER BY -sr.max_drawdown_pct) as drawdown_rank,
        PERCENT_RANK() OVER (ORDER BY sr.score) as score_rank
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    WHERE sr.sharpe_ratio IS NOT NULL
      AND sr.sortino_ratio IS NOT NULL
)
SELECT
    id,
    ticker,
    strategy_type,
    sweep_run_id,
    fast_period,
    slow_period,
    score,
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    max_drawdown_pct,
    total_return_pct,
    win_rate_pct,
    -- Composite rank (weighted average of all risk metrics)
    (sharpe_rank * 0.3 +
     sortino_rank * 0.25 +
     calmar_rank * 0.2 +
     drawdown_rank * 0.15 +
     score_rank * 0.1) as composite_risk_score,
    ROW_NUMBER() OVER (
        ORDER BY (sharpe_rank * 0.3 + sortino_rank * 0.25 +
                  calmar_rank * 0.2 + drawdown_rank * 0.15 +
                  score_rank * 0.1) DESC
    ) as composite_rank
FROM normalized_metrics
ORDER BY composite_risk_score DESC;

COMMENT ON VIEW v_risk_adjusted_rankings IS
'Strategies ranked by composite risk-adjusted performance (Sharpe, Sortino, Calmar, Drawdown, Score).';

-- ============================================================================
-- v_parameter_performance_summary
-- ============================================================================
-- Purpose: Aggregate performance statistics by parameter combinations
-- ============================================================================
CREATE OR REPLACE VIEW v_parameter_performance_summary AS
SELECT
    sr.fast_period,
    sr.slow_period,
    st.strategy_type,
    COUNT(*) as result_count,
    COUNT(DISTINCT sr.ticker_id) as ticker_count,
    COUNT(DISTINCT sr.sweep_run_id) as sweep_count,
    AVG(sr.score) as avg_score,
    STDDEV(sr.score) as stddev_score,
    MIN(sr.score) as min_score,
    MAX(sr.score) as max_score,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sr.score) as median_score,
    AVG(sr.sharpe_ratio) as avg_sharpe_ratio,
    AVG(sr.total_return_pct) as avg_total_return_pct,
    AVG(sr.win_rate_pct) as avg_win_rate_pct,
    AVG(sr.max_drawdown_pct) as avg_max_drawdown_pct,
    AVG(sr.total_trades) as avg_total_trades,
    AVG(sr.profit_factor) as avg_profit_factor
FROM strategy_sweep_results sr
JOIN strategy_types st ON sr.strategy_type_id = st.id
GROUP BY sr.fast_period, sr.slow_period, st.strategy_type
HAVING COUNT(*) >= 3  -- At least 3 results for statistical relevance
ORDER BY avg_score DESC;

COMMENT ON VIEW v_parameter_performance_summary IS
'Aggregated performance statistics for each parameter combination across all tickers and sweeps.';

-- ============================================================================
-- v_consistency_analysis
-- ============================================================================
-- Purpose: Identify strategies with consistent performance across tickers
-- ============================================================================
CREATE OR REPLACE VIEW v_consistency_analysis AS
WITH param_stats AS (
    SELECT
        sr.fast_period,
        sr.slow_period,
        st.strategy_type,
        COUNT(DISTINCT sr.ticker_id) as ticker_count,
        AVG(sr.score) as avg_score,
        STDDEV(sr.score) as stddev_score,
        MIN(sr.score) as min_score,
        MAX(sr.score) as max_score,
        -- Coefficient of variation (lower = more consistent)
        CASE
            WHEN AVG(sr.score) > 0 THEN STDDEV(sr.score) / AVG(sr.score)
            ELSE NULL
        END as coefficient_of_variation
    FROM strategy_sweep_results sr
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    GROUP BY sr.fast_period, sr.slow_period, st.strategy_type
    HAVING COUNT(DISTINCT sr.ticker_id) >= 3
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
    coefficient_of_variation,
    -- Consistency score (high avg, low variation)
    CASE
        WHEN coefficient_of_variation IS NOT NULL
        THEN avg_score / (1 + coefficient_of_variation)
        ELSE avg_score
    END as consistency_score,
    ROW_NUMBER() OVER (
        ORDER BY
            CASE
                WHEN coefficient_of_variation IS NOT NULL
                THEN avg_score / (1 + coefficient_of_variation)
                ELSE avg_score
            END DESC
    ) as consistency_rank
FROM param_stats
ORDER BY consistency_score DESC;

COMMENT ON VIEW v_consistency_analysis IS
'Strategies ranked by performance consistency across multiple tickers. Low coefficient of variation indicates consistent performance.';
