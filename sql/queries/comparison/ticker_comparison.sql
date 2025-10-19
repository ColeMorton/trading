-- ============================================================================
-- Ticker Comparison
-- ============================================================================
-- Description: Compare performance across all tickers side-by-side
-- Output: Summary statistics for each ticker
-- ============================================================================

SELECT 
    t.ticker,
    COUNT(*) as total_tests,
    COUNT(DISTINCT sr.sweep_run_id) as sweep_runs,
    AVG(sr.score) as avg_score,
    MAX(sr.score) as best_score,
    AVG(sr.sharpe_ratio) as avg_sharpe,
    MAX(sr.sharpe_ratio) as best_sharpe,
    AVG(sr.total_return_pct) as avg_return,
    MAX(sr.total_return_pct) as best_return,
    AVG(sr.win_rate_pct) as avg_win_rate,
    AVG(sr.max_drawdown_pct) as avg_drawdown,
    AVG(sr.total_trades) as avg_trades,
    -- Best parameter combination
    (SELECT CONCAT(fast_period, '/', slow_period)
     FROM strategy_sweep_results sr2
     WHERE sr2.ticker_id = sr.ticker_id
     ORDER BY sr2.score DESC
     LIMIT 1) as best_params
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
GROUP BY t.ticker, sr.ticker_id
ORDER BY avg_score DESC;

