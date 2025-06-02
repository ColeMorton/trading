-- Performance indexes for trading database

-- Portfolio indexes
CREATE INDEX IF NOT EXISTS idx_portfolio_ticker_id ON "Portfolio"(ticker_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_strategy_id ON "Portfolio"(strategy_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_type ON "Portfolio"(type);
CREATE INDEX IF NOT EXISTS idx_portfolio_created_at ON "Portfolio"(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_portfolio_name ON "Portfolio"(name);

-- Strategy indexes
CREATE INDEX IF NOT EXISTS idx_strategy_type ON "Strategy"(strategy_type);
CREATE INDEX IF NOT EXISTS idx_strategy_created_at ON "Strategy"(created_at DESC);

-- Ticker indexes
CREATE INDEX IF NOT EXISTS idx_ticker_symbol ON "Ticker"(symbol);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ticker_symbol_unique ON "Ticker"(symbol);
CREATE INDEX IF NOT EXISTS idx_ticker_asset_class ON "Ticker"(asset_class);

-- Price data indexes (composite for time-series queries)
CREATE INDEX IF NOT EXISTS idx_price_data_ticker_date ON "PriceData"(ticker_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_price_data_date ON "PriceData"(date DESC);

-- Signal indexes
CREATE INDEX IF NOT EXISTS idx_signal_portfolio_id ON "Signal"(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_signal_date ON "Signal"(date DESC);
CREATE INDEX IF NOT EXISTS idx_signal_type ON "Signal"(signal_type);
CREATE INDEX IF NOT EXISTS idx_signal_portfolio_date ON "Signal"(portfolio_id, date DESC);

-- Backtest result indexes
CREATE INDEX IF NOT EXISTS idx_backtest_portfolio_id ON "BacktestResult"(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_backtest_created_at ON "BacktestResult"(created_at DESC);

-- Portfolio metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_portfolio_id ON "PortfolioMetrics"(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON "PortfolioMetrics"(date DESC);

-- Analysis execution indexes
CREATE INDEX IF NOT EXISTS idx_execution_status ON "AnalysisExecution"(status);
CREATE INDEX IF NOT EXISTS idx_execution_created_at ON "AnalysisExecution"(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_execution_user_status ON "AnalysisExecution"(user_id, status);

-- Configuration indexes
CREATE INDEX IF NOT EXISTS idx_config_type ON "Configuration"(config_type);
CREATE INDEX IF NOT EXISTS idx_config_name ON "Configuration"(name);

-- Full text search indexes (if using PostgreSQL full text search)
CREATE INDEX IF NOT EXISTS idx_ticker_search ON "Ticker" USING gin(to_tsvector('english', name || ' ' || symbol));
CREATE INDEX IF NOT EXISTS idx_portfolio_search ON "Portfolio" USING gin(to_tsvector('english', name));

-- Analyze tables for query optimization
ANALYZE "Portfolio";
ANALYZE "Strategy";
ANALYZE "Ticker";
ANALYZE "PriceData";
ANALYZE "Signal";
ANALYZE "BacktestResult";
ANALYZE "PortfolioMetrics";
ANALYZE "AnalysisExecution";
ANALYZE "Configuration";