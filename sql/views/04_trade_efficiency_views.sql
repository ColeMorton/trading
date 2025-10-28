-- ============================================================================
-- Trade Efficiency and Win Rate Views
-- ============================================================================
-- Views for analyzing trading frequency, efficiency, and win rates
-- ============================================================================

-- ============================================================================
-- v_trade_efficiency_analysis
-- ============================================================================
-- Purpose: Analyze trade frequency vs performance
-- ============================================================================
CREATE OR REPLACE VIEW v_trade_efficiency_analysis AS
SELECT
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.sweep_run_id,
    sr.fast_period,
    sr.slow_period,
    sr.total_trades,
    sr.total_closed_trades,
    sr.trades_per_month,
    sr.trades_per_day,
    sr.avg_trade_duration,
    sr.win_rate_pct,
    sr.profit_factor,
    sr.expectancy_per_trade,
    sr.expectancy_per_month,
    sr.score,
    sr.sharpe_ratio,
    -- Efficiency score: performance per trade
    CASE
        WHEN sr.total_trades > 0
        THEN sr.score / sr.total_trades
        ELSE NULL
    END as score_per_trade,
    -- Monthly efficiency: performance per trading month
    CASE
        WHEN sr.trades_per_month > 0
        THEN sr.score / sr.trades_per_month
        ELSE NULL
    END as score_per_trading_month,
    -- Risk-adjusted efficiency
    CASE
        WHEN sr.total_trades > 0 AND sr.sharpe_ratio IS NOT NULL
        THEN sr.sharpe_ratio / sr.total_trades
        ELSE NULL
    END as sharpe_per_trade,
    -- Trade frequency category
    CASE
        WHEN sr.trades_per_month >= 20 THEN 'Very High Frequency'
        WHEN sr.trades_per_month >= 10 THEN 'High Frequency'
        WHEN sr.trades_per_month >= 5 THEN 'Medium Frequency'
        WHEN sr.trades_per_month >= 2 THEN 'Low Frequency'
        ELSE 'Very Low Frequency'
    END as frequency_category
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.total_trades IS NOT NULL
ORDER BY sr.score DESC;

COMMENT ON VIEW v_trade_efficiency_analysis IS
'Analyze trading efficiency metrics including trades per month, score per trade, and frequency categorization.';

-- ============================================================================
-- v_win_rate_analysis
-- ============================================================================
-- Purpose: Detailed win rate analysis with categorization
-- ============================================================================
CREATE OR REPLACE VIEW v_win_rate_analysis AS
SELECT
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.sweep_run_id,
    sr.fast_period,
    sr.slow_period,
    sr.win_rate_pct,
    sr.total_trades,
    sr.total_closed_trades,
    sr.profit_factor,
    sr.expectancy_per_trade,
    sr.avg_winning_trade_pct,
    sr.avg_losing_trade_pct,
    sr.best_trade_pct,
    sr.worst_trade_pct,
    sr.avg_winning_trade_duration,
    sr.avg_losing_trade_duration,
    sr.score,
    -- Win/Loss ratio
    CASE
        WHEN sr.avg_losing_trade_pct IS NOT NULL AND sr.avg_losing_trade_pct != 0
        THEN sr.avg_winning_trade_pct / ABS(sr.avg_losing_trade_pct)
        ELSE NULL
    END as win_loss_ratio,
    -- Win rate category
    CASE
        WHEN sr.win_rate_pct >= 70 THEN 'Excellent (>=70%)'
        WHEN sr.win_rate_pct >= 60 THEN 'Very Good (60-70%)'
        WHEN sr.win_rate_pct >= 50 THEN 'Good (50-60%)'
        WHEN sr.win_rate_pct >= 40 THEN 'Fair (40-50%)'
        ELSE 'Needs Improvement (<40%)'
    END as win_rate_category,
    -- Trade quality score (combines win rate and profit factor)
    CASE
        WHEN sr.profit_factor IS NOT NULL
        THEN (sr.win_rate_pct / 100.0) * sr.profit_factor
        ELSE NULL
    END as trade_quality_score
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.win_rate_pct IS NOT NULL
ORDER BY sr.score DESC;

COMMENT ON VIEW v_win_rate_analysis IS
'Detailed win rate analysis with categorization, win/loss ratios, and trade quality metrics.';

-- ============================================================================
-- v_trade_duration_analysis
-- ============================================================================
-- Purpose: Analyze holding periods and their relationship to performance
-- ============================================================================
CREATE OR REPLACE VIEW v_trade_duration_analysis AS
SELECT
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.sweep_run_id,
    sr.fast_period,
    sr.slow_period,
    sr.avg_trade_duration,
    sr.avg_winning_trade_duration,
    sr.avg_losing_trade_duration,
    sr.max_drawdown_duration,
    sr.win_rate_pct,
    sr.profit_factor,
    sr.total_trades,
    sr.score,
    sr.sharpe_ratio,
    -- Extract numeric values from duration strings if possible
    -- Note: This assumes duration format like "5 days" or "2 days 3:30:00"
    CASE
        WHEN sr.avg_trade_duration ~ '^\d+ day'
        THEN CAST(SPLIT_PART(sr.avg_trade_duration, ' ', 1) AS INTEGER)
        ELSE NULL
    END as avg_trade_days,
    -- Duration efficiency: score per day held
    CASE
        WHEN sr.avg_trade_duration ~ '^\d+ day'
        THEN sr.score / NULLIF(CAST(SPLIT_PART(sr.avg_trade_duration, ' ', 1) AS INTEGER), 0)
        ELSE NULL
    END as score_per_holding_day
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.avg_trade_duration IS NOT NULL
ORDER BY sr.score DESC;

COMMENT ON VIEW v_trade_duration_analysis IS
'Analyze trade holding periods and their relationship to performance metrics.';

-- ============================================================================
-- v_expectancy_analysis
-- ============================================================================
-- Purpose: Deep dive into expectancy metrics
-- ============================================================================
CREATE OR REPLACE VIEW v_expectancy_analysis AS
SELECT
    sr.id,
    t.ticker,
    st.strategy_type,
    sr.sweep_run_id,
    sr.fast_period,
    sr.slow_period,
    sr.expectancy,
    sr.expectancy_per_trade,
    sr.expectancy_per_month,
    sr.profit_factor,
    sr.win_rate_pct,
    sr.total_trades,
    sr.trades_per_month,
    sr.score,
    sr.total_return_pct,
    -- Annualized expectancy estimate
    CASE
        WHEN sr.expectancy_per_month IS NOT NULL
        THEN sr.expectancy_per_month * 12
        ELSE NULL
    END as annualized_expectancy,
    -- Expectancy quality (expectancy relative to volatility)
    CASE
        WHEN sr.expectancy_per_trade IS NOT NULL AND sr.profit_factor IS NOT NULL
        THEN sr.expectancy_per_trade * sr.profit_factor
        ELSE NULL
    END as expectancy_quality,
    -- Categorize expectancy
    CASE
        WHEN sr.expectancy_per_trade >= 5 THEN 'Excellent (>=5)'
        WHEN sr.expectancy_per_trade >= 2 THEN 'Very Good (2-5)'
        WHEN sr.expectancy_per_trade >= 1 THEN 'Good (1-2)'
        WHEN sr.expectancy_per_trade >= 0.5 THEN 'Fair (0.5-1)'
        WHEN sr.expectancy_per_trade > 0 THEN 'Marginal (>0)'
        ELSE 'Negative (<=0)'
    END as expectancy_category
FROM strategy_sweep_results sr
JOIN tickers t ON sr.ticker_id = t.id
JOIN strategy_types st ON sr.strategy_type_id = st.id
WHERE sr.expectancy_per_trade IS NOT NULL
ORDER BY sr.expectancy_per_trade DESC;

COMMENT ON VIEW v_expectancy_analysis IS
'Deep analysis of expectancy metrics including per-trade, per-month, and annualized expectations.';
