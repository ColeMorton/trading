-- ============================================================================
-- Find Best Result for Specific Sweep Run and Ticker
-- ============================================================================
-- Description: Get the best performing strategy for a specific ticker in a
--              specific sweep run. This is the most common operational query.
--
-- Parameters:
--   :sweep_run_id - UUID of the sweep run
--   :ticker - Ticker symbol (e.g., 'AAPL')
--
-- Usage:
--   Replace :sweep_run_id and :ticker with actual values
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
    sr.max_drawdown_duration,
    sr.total_trades,
    sr.total_closed_trades,
    sr.trades_per_month,
    sr.avg_trade_duration
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.sweep_run_id = :sweep_run_id
  AND t.ticker = :ticker
ORDER BY sr.score DESC
LIMIT 1;

-- Example usage:
-- WHERE sr.sweep_run_id = 'fbecc235-07c9-4ae3-b5df-9df1017b2b1d'
--   AND t.ticker = 'AAPL'
