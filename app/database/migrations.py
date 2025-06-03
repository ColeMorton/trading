"""
Database Migration Scripts

This module contains scripts to migrate existing CSV/JSON data to PostgreSQL.
"""

import asyncio
import json
import logging
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from app.database.config import get_database_settings
from prisma import Prisma

logger = logging.getLogger(__name__)


class DataMigrator:
    """Handles migration of CSV and JSON data to PostgreSQL."""

    def __init__(self, prisma: Prisma):
        self.prisma = prisma
        self.settings = get_database_settings()
        self.project_root = Path(__file__).parent.parent.parent

    async def migrate_all(self):
        """Run all migration steps."""
        logger.info("Starting full data migration...")

        # Step 1: Create core strategies
        await self.create_core_strategies()

        # Step 2: Migrate tickers from price data
        await self.migrate_tickers()

        # Step 3: Migrate price data
        await self.migrate_price_data()

        # Step 4: Migrate portfolio configurations
        await self.migrate_portfolio_configurations()

        # Step 5: Migrate backtest results
        await self.migrate_backtest_results()

        # Step 6: Create portfolios and metrics
        await self.create_portfolios()

        logger.info("Data migration completed successfully")

    async def create_core_strategies(self):
        """Create core strategy types."""
        strategies = [
            {
                "name": "EMA_Cross",
                "type": "MA_CROSS",
                "description": "Exponential Moving Average Crossover",
            },
            {
                "name": "SMA_Cross",
                "type": "MA_CROSS",
                "description": "Simple Moving Average Crossover",
            },
            {"name": "MACD", "type": "MACD", "description": "MACD Signal Strategy"},
            {
                "name": "Mean_Reversion",
                "type": "MEAN_REVERSION",
                "description": "Mean Reversion Strategy",
            },
            {"name": "RSI", "type": "RSI", "description": "RSI Momentum Strategy"},
            {"name": "ATR", "type": "ATR", "description": "ATR Volatility Strategy"},
            {"name": "Range", "type": "RANGE", "description": "Range Trading Strategy"},
        ]

        for strategy_data in strategies:
            try:
                await self.prisma.strategy.upsert(
                    where={"name": strategy_data["name"]},
                    data={
                        "create": strategy_data,
                        "update": {"description": strategy_data["description"]},
                    },
                )
                logger.info(f"Created/updated strategy: {strategy_data['name']}")
            except Exception as e:
                logger.error(f"Failed to create strategy {strategy_data['name']}: {e}")

    async def migrate_tickers(self):
        """Extract and migrate ticker information from price data files."""
        price_data_dir = self.project_root / "csv" / "price_data"

        if not price_data_dir.exists():
            logger.warning(f"Price data directory not found: {price_data_dir}")
            return

        tickers_created = 0

        for csv_file in price_data_dir.glob("*.csv"):
            # Extract ticker symbol from filename (e.g., "BTC-USD_D.csv" -> "BTC-USD")
            filename = csv_file.stem
            if "_" in filename:
                symbol = filename.rsplit("_", 1)[0]
            else:
                symbol = filename

            # Determine asset class
            asset_class = self._determine_asset_class(symbol)

            try:
                await self.prisma.ticker.upsert(
                    where={"symbol": symbol},
                    data={
                        "create": {
                            "symbol": symbol,
                            "name": symbol,  # Can be updated later with proper names
                            "assetClass": asset_class,
                        },
                        "update": {"assetClass": asset_class},
                    },
                )
                tickers_created += 1

                if tickers_created % 50 == 0:
                    logger.info(f"Processed {tickers_created} tickers...")

            except Exception as e:
                logger.error(f"Failed to create ticker {symbol}: {e}")

        logger.info(f"Migrated {tickers_created} tickers")

    def _determine_asset_class(self, symbol: str) -> str:
        """Determine asset class based on symbol patterns."""
        if "-USD" in symbol:
            return "CRYPTO"
        elif symbol in [
            "SPY",
            "QQQ",
            "IWM",
            "DIA",
            "XLF",
            "XLE",
            "XLU",
            "XLI",
            "XLV",
            "XLY",
            "XLP",
            "XLB",
            "XLK",
            "XLRE",
        ]:
            return "ETF"
        elif "=F" in symbol:
            return "COMMODITY"
        else:
            return "STOCK"

    async def migrate_price_data(self, batch_size: int = 1000):
        """Migrate price data from CSV files."""
        price_data_dir = self.project_root / "csv" / "price_data"

        if not price_data_dir.exists():
            logger.warning(f"Price data directory not found: {price_data_dir}")
            return

        total_records = 0

        for csv_file in price_data_dir.glob("*.csv"):
            filename = csv_file.stem
            if "_" in filename:
                symbol = filename.rsplit("_", 1)[0]
            else:
                symbol = filename

            try:
                # Get ticker ID
                ticker = await self.prisma.ticker.find_unique(where={"symbol": symbol})
                if not ticker:
                    logger.warning(f"Ticker not found for symbol: {symbol}")
                    continue

                # Read and process CSV data
                df = pd.read_csv(csv_file)
                df.columns = df.columns.str.lower()

                # Convert date column
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                elif df.index.name == "Date" or "Date" in df.columns:
                    if df.index.name == "Date":
                        df = df.reset_index()
                    df["date"] = pd.to_datetime(df["Date"])

                # Prepare records for insertion
                records = []
                for _, row in df.iterrows():
                    record = {
                        "tickerId": ticker.id,
                        "date": row["date"].to_pydatetime(),
                        "open": Decimal(str(row["open"])),
                        "high": Decimal(str(row["high"])),
                        "low": Decimal(str(row["low"])),
                        "close": Decimal(str(row["close"])),
                        "volume": (
                            Decimal(str(row["volume"]))
                            if "volume" in row and pd.notna(row["volume"])
                            else None
                        ),
                    }
                    records.append(record)

                # Insert in batches
                for i in range(0, len(records), batch_size):
                    batch = records[i : i + batch_size]
                    try:
                        await self.prisma.pricedata.create_many(
                            data=batch, skip_duplicates=True
                        )
                    except Exception as e:
                        logger.error(f"Failed to insert batch for {symbol}: {e}")

                total_records += len(records)
                logger.info(f"Migrated {len(records)} price records for {symbol}")

            except Exception as e:
                logger.error(f"Failed to process price data for {csv_file}: {e}")

        logger.info(f"Migrated {total_records} total price records")

    async def migrate_portfolio_configurations(self):
        """Migrate portfolio configurations from JSON files."""
        json_dir = self.project_root / "json" / "portfolios"

        if not json_dir.exists():
            logger.warning(f"Portfolio JSON directory not found: {json_dir}")
            return

        configs_created = 0

        for json_file in json_dir.glob("*.json"):
            try:
                with open(json_file, "r") as f:
                    portfolio_data = json.load(f)

                if isinstance(portfolio_data, list):
                    configs = portfolio_data
                elif (
                    isinstance(portfolio_data, dict) and "strategies" in portfolio_data
                ):
                    configs = portfolio_data["strategies"]
                else:
                    configs = [portfolio_data]

                for config in configs:
                    await self._create_strategy_configuration(config)
                    configs_created += 1

                logger.info(
                    f"Processed {len(configs)} configurations from {json_file.name}"
                )

            except Exception as e:
                logger.error(f"Failed to process {json_file}: {e}")

        logger.info(f"Migrated {configs_created} strategy configurations")

    async def _create_strategy_configuration(self, config: Dict[str, Any]):
        """Create a strategy configuration from JSON data."""
        try:
            # Extract configuration details
            symbol = config.get("ticker", config.get("symbol", ""))
            strategy_type = config.get("type", config.get("strategy", ""))
            timeframe = config.get("timeframe", "1d")

            # Get or create ticker
            ticker = await self.prisma.ticker.find_unique(where={"symbol": symbol})
            if not ticker:
                # Create ticker if it doesn't exist
                ticker = await self.prisma.ticker.create(
                    data={
                        "symbol": symbol,
                        "name": symbol,
                        "assetClass": self._determine_asset_class(symbol),
                    }
                )

            # Get strategy
            strategy_name = self._map_strategy_type(strategy_type)
            strategy = await self.prisma.strategy.find_unique(
                where={"name": strategy_name}
            )
            if not strategy:
                logger.warning(f"Strategy not found: {strategy_name}")
                return

            # Map timeframe
            timeframe_mapped = self._map_timeframe(timeframe)

            # Create configuration
            config_data = {
                "strategyId": strategy.id,
                "tickerId": ticker.id,
                "timeframe": timeframe_mapped,
                "shortWindow": config.get("short", config.get("short_window")),
                "longWindow": config.get("long", config.get("long_window")),
                "signalWindow": config.get("signal", config.get("signal_window")),
                "stopLossPct": (
                    Decimal(str(config["stop_loss"]))
                    if config.get("stop_loss")
                    else None
                ),
                "rsiPeriod": config.get("rsi_period"),
                "rsiThreshold": (
                    Decimal(str(config["rsi_threshold"]))
                    if config.get("rsi_threshold")
                    else None
                ),
                "signalEntry": config.get("signal_entry"),
                "signalExit": config.get("signal_exit"),
                "direction": config.get("direction", "LONG"),
                "allocationPct": (
                    Decimal(str(config["allocation"]))
                    if config.get("allocation")
                    else None
                ),
                "parameters": config.get("parameters", {}),
            }

            await self.prisma.strategyconfiguration.create(data=config_data)

        except Exception as e:
            logger.error(f"Failed to create strategy configuration: {e}")

    def _map_strategy_type(self, strategy_type: str) -> str:
        """Map strategy type to standardized name."""
        mapping = {
            "ema": "EMA_Cross",
            "sma": "SMA_Cross",
            "macd": "MACD",
            "mean_reversion": "Mean_Reversion",
            "rsi": "RSI",
            "atr": "ATR",
            "range": "Range",
        }
        return mapping.get(strategy_type.lower(), "EMA_Cross")

    def _map_timeframe(self, timeframe: str) -> str:
        """Map timeframe to enum value."""
        mapping = {
            "1m": "ONE_MINUTE",
            "5m": "FIVE_MINUTES",
            "15m": "FIFTEEN_MINUTES",
            "30m": "THIRTY_MINUTES",
            "1h": "ONE_HOUR",
            "2h": "TWO_HOURS",
            "4h": "FOUR_HOURS",
            "6h": "SIX_HOURS",
            "8h": "EIGHT_HOURS",
            "12h": "TWELVE_HOURS",
            "1d": "ONE_DAY",
            "d": "ONE_DAY",
            "D": "ONE_DAY",
            "3d": "THREE_DAYS",
            "1w": "ONE_WEEK",
            "1M": "ONE_MONTH",
        }
        return mapping.get(timeframe, "ONE_DAY")

    async def migrate_backtest_results(self):
        """Migrate backtest results from portfolio CSV files."""
        portfolios_dir = self.project_root / "csv" / "portfolios"

        if not portfolios_dir.exists():
            logger.warning(f"Portfolios directory not found: {portfolios_dir}")
            return

        results_created = 0

        for csv_file in portfolios_dir.glob("*.csv"):
            try:
                df = pd.read_csv(csv_file)

                for _, row in df.iterrows():
                    await self._create_backtest_result(row, csv_file.stem)
                    results_created += 1

                logger.info(
                    f"Processed {len(df)} backtest results from {csv_file.name}"
                )

            except Exception as e:
                logger.error(f"Failed to process backtest results from {csv_file}: {e}")

        logger.info(f"Migrated {results_created} backtest results")

    async def _create_backtest_result(self, row: pd.Series, filename: str):
        """Create a backtest result from CSV row data."""
        try:
            # Extract ticker and strategy info from filename or row
            symbol = row.get(
                "Ticker", filename.split("_")[0] if "_" in filename else filename
            )

            # Find strategy configuration
            # This is a simplified lookup - in practice, you'd need more sophisticated matching
            ticker = await self.prisma.ticker.find_unique(where={"symbol": symbol})
            if not ticker:
                return

            # Create a basic backtest result (you'll need to map all the columns properly)
            result_data = {
                "strategyConfigId": "placeholder",  # You'll need to implement proper lookup
                "runDate": datetime.now(),
                "startDate": pd.to_datetime(
                    row.get("Start", "2023-01-01")
                ).to_pydatetime(),
                "endDate": pd.to_datetime(row.get("End", "2024-01-01")).to_pydatetime(),
                "totalReturnPct": Decimal(str(row.get("Total Return [%]", 0))),
                "sharpeRatio": (
                    Decimal(str(row.get("Sharpe Ratio", 0)))
                    if pd.notna(row.get("Sharpe Ratio"))
                    else None
                ),
                "maxDrawdownPct": (
                    Decimal(str(row.get("Max Drawdown [%]", 0)))
                    if pd.notna(row.get("Max Drawdown [%]"))
                    else None
                ),
                "totalTrades": int(row.get("# Trades", 0)),
                "winRatePct": (
                    Decimal(str(row.get("Win Rate [%]", 0)))
                    if pd.notna(row.get("Win Rate [%]"))
                    else None
                ),
                # Add more field mappings as needed
            }

            # Note: This is a placeholder - you'll need to implement proper strategy config lookup
            logger.info(f"Would create backtest result for {symbol} (placeholder)")

        except Exception as e:
            logger.error(f"Failed to create backtest result: {e}")

    async def create_portfolios(self):
        """Create portfolio records from existing data."""
        # Create standard portfolios
        portfolio_types = [
            {
                "name": "Best Performers",
                "type": "BEST",
                "description": "Top performing strategies",
            },
            {
                "name": "Filtered Strategies",
                "type": "FILTERED",
                "description": "Filtered strategy selection",
            },
            {
                "name": "All Strategies",
                "type": "STANDARD",
                "description": "Complete strategy universe",
            },
        ]

        for portfolio_data in portfolio_types:
            try:
                await self.prisma.portfolio.upsert(
                    where={"name": portfolio_data["name"]},
                    data={
                        "create": portfolio_data,
                        "update": {"description": portfolio_data["description"]},
                    },
                )
                logger.info(f"Created/updated portfolio: {portfolio_data['name']}")
            except Exception as e:
                logger.error(
                    f"Failed to create portfolio {portfolio_data['name']}: {e}"
                )


async def run_migration():
    """Run the complete data migration."""
    prisma = Prisma()

    try:
        await prisma.connect()
        logger.info("Connected to database for migration")

        migrator = DataMigrator(prisma)
        await migrator.migrate_all()

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await prisma.disconnect()
        logger.info("Disconnected from database")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_migration())
