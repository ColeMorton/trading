-- ============================================================================
-- Find Best Overall Result for Sweep Run
-- ============================================================================
-- Description: Get the single best performing strategy across all tickers
--              in a specific sweep run.
--
-- Parameters:
--   :sweep_run_id - UUID of the sweep run
--
-- Usage:
--   Replace :sweep_run_id with actual value
-- ============================================================================

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
    sr.annualized_return,
    sr.win_rate_pct,
    sr.profit_factor,
    sr.expectancy_per_trade,
    sr.max_drawdown_pct,
    sr.total_trades,
    sr.trades_per_month
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.sweep_run_id = :sweep_run_id
ORDER BY sr.score DESC
LIMIT 1;

-- Example usage:
-- WHERE sr.sweep_run_id = 'fbecc235-07c9-4ae3-b5df-9df1017b2b1d'
