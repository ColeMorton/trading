-- ============================================================================
-- Risk/Reward Scatter Plot Data
-- ============================================================================
-- Description: Generate data for risk vs reward scatter plots
--
-- Output: Data points for plotting risk (max drawdown) vs reward (return)
-- ============================================================================

SELECT
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.fast_period,
    sr.slow_period,
    sr.max_drawdown_pct as risk_metric,  -- X-axis (lower is better)
    sr.total_return_pct as reward_metric,  -- Y-axis (higher is better)
    sr.sharpe_ratio,  -- Size or color
    sr.score,  -- Alternative color/size
    sr.win_rate_pct,
    CONCAT(sr.fast_period, '/', sr.slow_period) as param_label
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.max_drawdown_pct IS NOT NULL
  AND sr.total_return_pct IS NOT NULL
ORDER BY sr.score DESC;

-- Visualization suggestions:
-- - X-axis: max_drawdown_pct (or use negative for left-to-right better performance)
-- - Y-axis: total_return_pct
-- - Point size: sharpe_ratio
-- - Point color: ticker or score
-- - Identify efficient frontier (high return, low drawdown)
