-- ============================================================================
-- Executive Summary Report
-- ============================================================================
-- Description: High-level summary for decision makers showing key metrics,
--              best performers, and overall statistics
-- ============================================================================

-- Overall Statistics
SELECT 'Overall Statistics' as section, NULL as detail_label, NULL as detail_value
UNION ALL
SELECT '', 'Total Sweep Runs', COUNT(DISTINCT sweep_run_id)::text
FROM strategy_sweep_results
UNION ALL
SELECT '', 'Total Tests Performed', COUNT(*)::text
FROM strategy_sweep_results
UNION ALL
SELECT '', 'Unique Tickers Tested', COUNT(DISTINCT ticker_id)::text
FROM strategy_sweep_results
UNION ALL
SELECT '', 'Strategy Types', COUNT(DISTINCT strategy_type_id)::text
FROM strategy_sweep_results
UNION ALL
SELECT '', 'Date Range', 
    CONCAT(
        TO_CHAR(MIN(created_at), 'YYYY-MM-DD'), 
        ' to ', 
        TO_CHAR(MAX(created_at), 'YYYY-MM-DD')
    )
FROM strategy_sweep_results

UNION ALL SELECT '', '', '' -- Spacer

-- Best Overall Performer
UNION ALL
SELECT 'Best Overall Performer', NULL, NULL
UNION ALL
SELECT '', 'Ticker', t.ticker
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
ORDER BY sr.score DESC LIMIT 1
UNION ALL
SELECT '', 'Score', ROUND(score::numeric, 2)::text
FROM strategy_sweep_results
ORDER BY score DESC LIMIT 1
UNION ALL
SELECT '', 'Parameters', CONCAT(fast_period, '/', slow_period)
FROM strategy_sweep_results
ORDER BY score DESC LIMIT 1
UNION ALL
SELECT '', 'Sharpe Ratio', ROUND(sharpe_ratio::numeric, 2)::text
FROM strategy_sweep_results
ORDER BY score DESC LIMIT 1
UNION ALL
SELECT '', 'Total Return %', ROUND(total_return_pct::numeric, 2)::text
FROM strategy_sweep_results
ORDER BY score DESC LIMIT 1

UNION ALL SELECT '', '', '' -- Spacer

-- Performance Averages
UNION ALL
SELECT 'Average Performance Metrics', NULL, NULL
UNION ALL
SELECT '', 'Avg Score', ROUND(AVG(score)::numeric, 2)::text
FROM strategy_sweep_results
UNION ALL
SELECT '', 'Avg Sharpe Ratio', ROUND(AVG(sharpe_ratio)::numeric, 2)::text
FROM strategy_sweep_results WHERE sharpe_ratio IS NOT NULL
UNION ALL
SELECT '', 'Avg Win Rate %', ROUND(AVG(win_rate_pct)::numeric, 2)::text
FROM strategy_sweep_results WHERE win_rate_pct IS NOT NULL
UNION ALL
SELECT '', 'Avg Return %', ROUND(AVG(total_return_pct)::numeric, 2)::text
FROM strategy_sweep_results WHERE total_return_pct IS NOT NULL
UNION ALL
SELECT '', 'Avg Max Drawdown %', ROUND(AVG(max_drawdown_pct)::numeric, 2)::text
FROM strategy_sweep_results WHERE max_drawdown_pct IS NOT NULL;

-- Top 5 Performers by Ticker
SELECT 
    'Top Performers' as category,
    t.ticker,
    sr.score,
    CONCAT(sr.fast_period, '/', sr.slow_period) as parameters,
    sr.sharpe_ratio,
    sr.total_return_pct,
    sr.win_rate_pct
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
ORDER BY sr.score DESC
LIMIT 5;

