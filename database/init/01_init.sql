-- PostgreSQL initialization script
-- This script runs when the database container starts for the first time

-- Create database if it doesn't exist (should already be created by POSTGRES_DB)
-- CREATE DATABASE IF NOT EXISTS trading_db;

-- Use the trading database
\c trading_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create enum types for better type safety
CREATE TYPE timeframe_type AS ENUM ('1m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M');
CREATE TYPE strategy_type AS ENUM ('ma_cross', 'macd', 'mean_reversion', 'rsi', 'atr', 'range', 'bollinger_bands', 'custom');
CREATE TYPE signal_type AS ENUM ('buy', 'sell', 'hold');
CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');
CREATE TYPE position_type AS ENUM ('long', 'short');

-- Grant permissions to trading_user
GRANT ALL PRIVILEGES ON DATABASE trading_db TO trading_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trading_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trading_user;

-- Ensure future objects are also accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO trading_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO trading_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO trading_user;
