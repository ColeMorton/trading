-- ============================================================================
-- Core Operational Views - PRIORITY VIEWS
-- ============================================================================
-- These views provide quick access to best backtest results per sweep run,
-- which is the most common operational query pattern.
-- ============================================================================

-- ============================================================================
-- v_best_by_sweep_and_ticker
-- ============================================================================
-- Purpose: Find the best result for each ticker within each sweep run
-- This is the PRIMARY view for answering: "What's the best strategy for 
-- ticker X in sweep run Y?"
-- ============================================================================
CREATE OR REPLACE VIEW v_best_by_sweep_and_ticker AS
WITH ranked_results AS (
    SELECT 
        sr.id,
        sr.sweep_run_id,
        sr.created_at as run_date,
        t.ticker,
        st.strategy_type,
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
        sr.total_trades,
        sr.total_closed_trades,
        sr.expectancy_per_trade,
        sr.trades_per_month,
        ROW_NUMBER() OVER (
            PARTITION BY sr.sweep_run_id, sr.ticker_id 
            ORDER BY sr.score DESC
        ) as rank_in_ticker
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
)
SELECT 
    sweep_run_id,
    run_date,
    ticker,
    strategy_type,
    id as best_result_id,
    fast_period,
    slow_period,
    signal_period,
    score,
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    total_return_pct,
    win_rate_pct,
    profit_factor,
    max_drawdown_pct,
    total_trades,
    total_closed_trades,
    expectancy_per_trade,
    trades_per_month
FROM ranked_results
WHERE rank_in_ticker = 1
ORDER BY sweep_run_id DESC, score DESC;

COMMENT ON VIEW v_best_by_sweep_and_ticker IS 
'Best performing strategy result for each ticker within each sweep run. Use this to quickly find optimal parameters for a specific ticker in a specific sweep.';

-- ============================================================================
-- v_best_results_per_sweep
-- ============================================================================
-- Purpose: Overall best result for each sweep run plus summary stats
-- Answers: "What's THE best result from sweep run X?"
-- ============================================================================
CREATE OR REPLACE VIEW v_best_results_per_sweep AS
WITH sweep_stats AS (
    SELECT 
        sr.sweep_run_id,
        MIN(sr.created_at) as run_date,
        COUNT(*) as result_count,
        COUNT(DISTINCT sr.ticker_id) as ticker_count,
        AVG(sr.score) as avg_score,
        MAX(sr.score) as max_score,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY sr.score) as median_score
    FROM strategy_sweep_results sr
    GROUP BY sr.sweep_run_id
),
best_overall AS (
    SELECT DISTINCT ON (sr.sweep_run_id)
        sr.sweep_run_id,
        sr.id as overall_best_id,
        t.ticker as overall_best_ticker,
        st.strategy_type as overall_best_strategy,
        sr.score as overall_best_score,
        sr.fast_period as overall_best_fast,
        sr.slow_period as overall_best_slow,
        sr.signal_period as overall_best_signal,
        sr.sharpe_ratio as overall_best_sharpe,
        sr.total_return_pct as overall_best_return
    FROM strategy_sweep_results sr
    JOIN tickers t ON sr.ticker_id = t.id
    JOIN strategy_types st ON sr.strategy_type_id = st.id
    ORDER BY sr.sweep_run_id, sr.score DESC
)
SELECT 
    ss.sweep_run_id,
    ss.run_date,
    ss.result_count,
    ss.ticker_count,
    ss.avg_score,
    ss.max_score,
    ss.median_score,
    bo.overall_best_id,
    bo.overall_best_ticker,
    bo.overall_best_strategy,
    bo.overall_best_score,
    bo.overall_best_fast,
    bo.overall_best_slow,
    bo.overall_best_signal,
    bo.overall_best_sharpe,
    bo.overall_best_return
FROM sweep_stats ss
JOIN best_overall bo ON ss.sweep_run_id = bo.sweep_run_id
ORDER BY ss.run_date DESC;

COMMENT ON VIEW v_best_results_per_sweep IS 
'Summary of each sweep run with the single best overall result and aggregate statistics. Use this for quick sweep run overview.';

-- ============================================================================
-- v_latest_best_results
-- ============================================================================
-- Purpose: Best results from the most recent sweep run
-- Quick access to most actionable/recent data
-- ============================================================================
CREATE OR REPLACE VIEW v_latest_best_results AS
WITH latest_sweep AS (
    SELECT MAX(created_at) as latest_date
    FROM strategy_sweep_results
),
latest_sweep_id AS (
    SELECT DISTINCT sweep_run_id
    FROM strategy_sweep_results sr
    CROSS JOIN latest_sweep ls
    WHERE sr.created_at = ls.latest_date
)
SELECT 
    sr.id,
    sr.sweep_run_id,
    sr.created_at as run_date,
    t.ticker,
    st.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.signal_period,
    sr.score,
    sr.sharpe_ratio,
    sr.sortino_ratio,
    sr.calmar_ratio,
    sr.omega_ratio,
    sr.total_return_pct,
    sr.annualized_return,
    sr.win_rate_pct,
    sr.profit_factor,
    sr.expectancy_per_trade,
    sr.max_drawdown_pct,
    sr.max_drawdown_duration,
    sr.total_trades,
    sr.total_closed_trades,
    sr.trades_per_month,
    sr.avg_trade_duration,
    sr.best_trade_pct,
    sr.worst_trade_pct,
    sr.avg_winning_trade_pct,
    sr.avg_losing_trade_pct,
    ROW_NUMBER() OVER (
        PARTITION BY sr.ticker_id 
        ORDER BY sr.score DESC
    ) as rank_for_ticker
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.sweep_run_id IN (SELECT sweep_run_id FROM latest_sweep_id)
ORDER BY sr.score DESC;

COMMENT ON VIEW v_latest_best_results IS 
'All results from the most recent sweep run with ranking. Use rank_for_ticker=1 to get best per ticker.';

-- ============================================================================
-- v_top_10_overall
-- ============================================================================
-- Purpose: Top 10 best results across ALL sweep runs
-- Quick reference for absolute best performers
-- ============================================================================
CREATE OR REPLACE VIEW v_top_10_overall AS
SELECT 
    sr.id,
    sr.sweep_run_id,
    sr.created_at as run_date,
    t.ticker,
    st.strategy_type,
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
    ROW_NUMBER() OVER (ORDER BY sr.score DESC) as overall_rank
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
ORDER BY sr.score DESC
LIMIT 10;

COMMENT ON VIEW v_top_10_overall IS 
'Top 10 best performing strategy results across all sweep runs and tickers.';

