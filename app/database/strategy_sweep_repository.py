"""
Strategy Sweep Repository

Repository for persisting strategy sweep results to PostgreSQL database.
"""

import json
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.database.config import DatabaseManager


logger = logging.getLogger(__name__)


class StrategySweepRepository:
    """Repository for strategy sweep results with async batch insert capabilities."""

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize repository with database manager.

        Args:
            db_manager: DatabaseManager instance for connection pooling
        """
        self.db_manager = db_manager

    def _normalize_column_name(self, name: str) -> str:
        """
        Convert CSV column name to database column name.

        Args:
            name: CSV column name (e.g., "Win Rate [%]", "Total Trades")

        Returns:
            Database column name (e.g., "win_rate_pct", "total_trades")
        """
        # Remove percentage indicators and brackets
        name = name.replace(" [%]", "_pct")
        name = name.replace(" [$]", "")
        name = name.replace("[", "").replace("]", "")

        # Convert to lowercase and replace spaces with underscores
        name = name.lower().replace(" ", "_")

        # Handle special cases
        name = name.replace("bnh", "bnh")  # Keep as is
        return name.replace("p&l", "pnl")

    def _convert_value(self, value: Any) -> Any:
        """
        Convert Python value to database-compatible type.

        Args:
            value: Value to convert

        Returns:
            Database-compatible value
        """
        if value is None or value in {"", "N/A"}:
            return None

        # Convert boolean to string
        if isinstance(value, bool):
            return str(value)

        # Convert to Decimal for numeric types to preserve precision
        if isinstance(value, int | float):
            return Decimal(str(value))

        # Keep strings as is
        if isinstance(value, str):
            return value

        # Convert other types to string
        return str(value)

    async def _get_or_create_ticker(self, ticker_symbol: str, connection) -> int:
        """
        Get or create a ticker and return its ID.

        Args:
            ticker_symbol: Ticker symbol string
            connection: Database connection

        Returns:
            Ticker ID

        Raises:
            Exception: If database operation fails
        """
        # Try to get existing ticker
        query = "SELECT id FROM tickers WHERE ticker = $1"
        ticker_id = await connection.fetchval(query, ticker_symbol)

        if ticker_id:
            return ticker_id

        # Create new ticker if it doesn't exist
        insert_query = """
            INSERT INTO tickers (ticker)
            VALUES ($1)
            ON CONFLICT (ticker) DO UPDATE SET ticker = EXCLUDED.ticker
            RETURNING id
        """
        return await connection.fetchval(insert_query, ticker_symbol)

    async def _get_or_create_strategy_type(
        self,
        strategy_type_name: str,
        connection,
    ) -> int:
        """
        Get or create a strategy type and return its ID.

        Args:
            strategy_type_name: Strategy type name string
            connection: Database connection

        Returns:
            Strategy type ID

        Raises:
            Exception: If database operation fails
        """
        # Try to get existing strategy type
        query = "SELECT id FROM strategy_types WHERE strategy_type = $1"
        strategy_type_id = await connection.fetchval(query, strategy_type_name)

        if strategy_type_id:
            return strategy_type_id

        # Create new strategy type if it doesn't exist
        insert_query = """
            INSERT INTO strategy_types (strategy_type)
            VALUES ($1)
            ON CONFLICT (strategy_type) DO UPDATE SET strategy_type = EXCLUDED.strategy_type
            RETURNING id
        """
        return await connection.fetchval(insert_query, strategy_type_name)

    def _prepare_record(
        self,
        result: dict[str, Any],
        sweep_run_id: UUID,
        sweep_config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Prepare a single result record for database insertion.

        Args:
            result: Portfolio result dictionary
            sweep_run_id: UUID grouping this sweep execution
            sweep_config: Sweep configuration dictionary

        Returns:
            Database-ready record dictionary
        """
        record = {
            "sweep_run_id": str(sweep_run_id),
            "sweep_config": json.dumps(sweep_config),
        }

        # Map all CSV columns to database columns
        for csv_col, value in result.items():
            db_col = self._normalize_column_name(csv_col)
            record[db_col] = self._convert_value(value)

        return record

    async def save_sweep_results(
        self,
        sweep_run_id: UUID,
        results: list[dict[str, Any]],
        sweep_config: dict[str, Any],
    ) -> int:
        """
        Save strategy sweep results to database with batch processing.

        Args:
            sweep_run_id: UUID grouping this sweep execution
            results: List of portfolio result dictionaries
            sweep_config: Sweep configuration dictionary

        Returns:
            Number of records inserted

        Raises:
            Exception: If database operation fails
        """
        if not results:
            logger.warning("No results to save")
            return 0

        # Prepare all records
        records = [
            self._prepare_record(result, sweep_run_id, sweep_config)
            for result in results
        ]

        # Build INSERT query dynamically based on first record
        if not records:
            return 0

        # Get column names from first record (excluding None metadata columns)
        sample_record = records[0]
        columns = list(sample_record)

        # Build column list for SQL with proper quoting for reserved keywords
        column_list = ", ".join(f'"{col}"' for col in columns)

        # Build placeholders for SQL (indexed placeholders for asyncpg)
        num_columns = len(columns)

        # Build the INSERT query
        query = f"""
            INSERT INTO strategy_sweep_results ({column_list})
            VALUES ({", ".join(f"${i + 1}" for i in range(num_columns))})
        """

        # Insert in batches for performance
        batch_size = 100
        total_inserted = 0

        try:
            # Get connection from pool
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                # Start transaction
                async with connection.transaction():
                    for i in range(0, len(records), batch_size):
                        batch = records[i : i + batch_size]

                        # Execute batch insert
                        for record in batch:
                            # Convert ticker to ticker_id
                            if "ticker" in record:
                                ticker_symbol = record["ticker"]
                                ticker_id = await self._get_or_create_ticker(
                                    ticker_symbol,
                                    connection,
                                )
                                record["ticker_id"] = ticker_id
                                del record["ticker"]

                                # Update columns list if this is the first record with ticker
                                if "ticker" in columns:
                                    columns = [
                                        col if col != "ticker" else "ticker_id"
                                        for col in columns
                                    ]
                                    column_list = ", ".join(
                                        f'"{col}"' for col in columns
                                    )
                                    query = f"""
                                        INSERT INTO strategy_sweep_results ({column_list})
                                        VALUES ({", ".join(f"${i + 1}" for i in range(len(columns)))})
                                    """

                            # Convert strategy_type to strategy_type_id
                            if "strategy_type" in record:
                                strategy_type_name = record["strategy_type"]
                                if strategy_type_name:
                                    strategy_type_id = (
                                        await self._get_or_create_strategy_type(
                                            strategy_type_name,
                                            connection,
                                        )
                                    )
                                    record["strategy_type_id"] = strategy_type_id
                                    del record["strategy_type"]

                                    # Update columns list if this is the first record with strategy_type
                                    if "strategy_type" in columns:
                                        columns = [
                                            (
                                                col
                                                if col != "strategy_type"
                                                else "strategy_type_id"
                                            )
                                            for col in columns
                                        ]
                                        column_list = ", ".join(
                                            f'"{col}"' for col in columns
                                        )
                                        query = f"""
                                            INSERT INTO strategy_sweep_results ({column_list})
                                            VALUES ({", ".join(f"${i + 1}" for i in range(len(columns)))})
                                        """

                            # Extract values in the same order as columns
                            values = [record.get(col) for col in columns]
                            await connection.execute(query, *values)
                            total_inserted += 1

                        logger.info(
                            f"Inserted batch {i // batch_size + 1}: "
                            f"{len(batch)} records (total: {total_inserted})",
                        )

            logger.info(
                f"Successfully saved {total_inserted} strategy sweep results "
                f"for sweep_run_id={sweep_run_id}",
            )
            return total_inserted

        except Exception as e:
            logger.exception(f"Failed to save strategy sweep results: {e}")
            raise

    async def get_sweep_results(self, sweep_run_id: UUID) -> list[dict[str, Any]]:
        """
        Retrieve all results for a specific sweep run.

        Args:
            sweep_run_id: UUID of the sweep run

        Returns:
            List of result dictionaries

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT sr.*, t.ticker, st.strategy_type
            FROM strategy_sweep_results sr
            JOIN tickers t ON sr.ticker_id = t.id
            JOIN strategy_types st ON sr.strategy_type_id = st.id
            WHERE sr.sweep_run_id = $1
            ORDER BY sr.created_at, t.ticker, st.strategy_type
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, str(sweep_run_id))
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to retrieve sweep results: {e}")
            raise

    async def get_recent_sweeps(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Retrieve most recent sweep runs with summary statistics.

        Args:
            limit: Maximum number of sweep runs to return

        Returns:
            List of sweep summary dictionaries

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT
                sweep_run_id,
                MIN(created_at) as sweep_start,
                COUNT(*) as result_count,
                COUNT(DISTINCT ticker) as ticker_count,
                COUNT(DISTINCT strategy_type) as strategy_count,
                sweep_config
            FROM strategy_sweep_results
            GROUP BY sweep_run_id, sweep_config
            ORDER BY sweep_start DESC
            LIMIT $1
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, limit)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to retrieve recent sweeps: {e}")
            raise

    def _parse_metric_type_string(self, metric_type_str: str | None) -> list[str]:
        """
        Parse comma-separated metric type string into list of metric names.

        Args:
            metric_type_str: Comma-separated string (e.g., "Most Sharpe Ratio, Most Total Return [%]")

        Returns:
            List of trimmed metric type names
        """
        if not metric_type_str or metric_type_str.strip() == "":
            return []

        # Split by comma and trim whitespace
        metric_names = [name.strip() for name in metric_type_str.split(",")]

        # Filter out empty strings
        return [name for name in metric_names if name]

    async def _get_metric_type_ids(
        self,
        metric_names: list[str],
        connection,
    ) -> dict[str, int]:
        """
        Get metric type IDs for given metric names.

        Args:
            metric_names: List of metric type names
            connection: Database connection

        Returns:
            Dictionary mapping metric name to metric type ID
        """
        if not metric_names:
            return {}

        # Query metric_types table to get IDs
        query = """
            SELECT id, name
            FROM metric_types
            WHERE name = ANY($1::text[])
        """

        rows = await connection.fetch(query, metric_names)
        return {row["name"]: row["id"] for row in rows}

    async def _save_metric_type_associations(
        self,
        sweep_result_id: str,
        metric_type_ids: list[int],
        connection,
    ) -> None:
        """
        Save metric type associations for a sweep result.

        Args:
            sweep_result_id: UUID of the sweep result
            metric_type_ids: List of metric type IDs to associate
            connection: Database connection
        """
        if not metric_type_ids:
            return

        # Insert associations using ON CONFLICT to handle duplicates
        query = """
            INSERT INTO strategy_sweep_result_metrics (sweep_result_id, metric_type_id)
            VALUES ($1, $2)
            ON CONFLICT (sweep_result_id, metric_type_id) DO NOTHING
        """

        for metric_type_id in metric_type_ids:
            await connection.execute(query, sweep_result_id, metric_type_id)

    async def save_sweep_results_with_metrics(
        self,
        sweep_run_id: UUID,
        results: list[dict[str, Any]],
        sweep_config: dict[str, Any],
    ) -> int:
        """
        Save strategy sweep results to database with metric type associations.

        This method replaces save_sweep_results() and adds support for
        parsing and storing metric type classifications.

        Args:
            sweep_run_id: UUID grouping this sweep execution
            results: List of portfolio result dictionaries
            sweep_config: Sweep configuration dictionary

        Returns:
            Number of records inserted

        Raises:
            Exception: If database operation fails
        """
        if not results:
            logger.warning("No results to save")
            return 0

        # Prepare all records
        records = [
            self._prepare_record(result, sweep_run_id, sweep_config)
            for result in results
        ]

        if not records:
            return 0

        # Build INSERT query dynamically based on first record
        sample_record = records[0]
        columns = list(sample_record)

        # Build column list for SQL with proper quoting
        column_list = ", ".join(f'"{col}"' for col in columns)

        # Build placeholders for SQL
        num_columns = len(columns)

        # Build the INSERT query
        insert_query = f"""
            INSERT INTO strategy_sweep_results ({column_list})
            VALUES ({", ".join(f"${i + 1}" for i in range(num_columns))})
            RETURNING id
        """

        # Insert in batches for performance
        batch_size = 100
        total_inserted = 0

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                async with connection.transaction():
                    for i in range(0, len(records), batch_size):
                        batch = records[i : i + batch_size]

                        # Process each record in the batch
                        for _record_idx, record in enumerate(batch):
                            # Convert ticker to ticker_id
                            if "ticker" in record:
                                ticker_symbol = record["ticker"]
                                ticker_id = await self._get_or_create_ticker(
                                    ticker_symbol,
                                    connection,
                                )
                                record["ticker_id"] = ticker_id
                                del record["ticker"]

                                # Update columns list if this is the first record with ticker
                                if "ticker" in columns:
                                    columns = [
                                        col if col != "ticker" else "ticker_id"
                                        for col in columns
                                    ]
                                    column_list = ", ".join(
                                        f'"{col}"' for col in columns
                                    )
                                    insert_query = f"""
                                        INSERT INTO strategy_sweep_results ({column_list})
                                        VALUES ({", ".join(f"${i + 1}" for i in range(len(columns)))})
                                        RETURNING id
                                    """

                            # Convert strategy_type to strategy_type_id
                            if "strategy_type" in record:
                                strategy_type_name = record["strategy_type"]
                                if strategy_type_name:
                                    strategy_type_id = (
                                        await self._get_or_create_strategy_type(
                                            strategy_type_name,
                                            connection,
                                        )
                                    )
                                    record["strategy_type_id"] = strategy_type_id
                                    del record["strategy_type"]

                                    # Update columns list if this is the first record with strategy_type
                                    if "strategy_type" in columns:
                                        columns = [
                                            (
                                                col
                                                if col != "strategy_type"
                                                else "strategy_type_id"
                                            )
                                            for col in columns
                                        ]
                                        column_list = ", ".join(
                                            f'"{col}"' for col in columns
                                        )
                                        insert_query = f"""
                                            INSERT INTO strategy_sweep_results ({column_list})
                                            VALUES ({", ".join(f"${i + 1}" for i in range(len(columns)))})
                                            RETURNING id
                                        """

                            # Extract values in the same order as columns
                            values = [record.get(col) for col in columns]

                            # Insert record and get its ID
                            result_id = await connection.fetchval(insert_query, *values)

                            # Parse and save metric type associations
                            metric_type_str = record.get("metric_type")
                            if metric_type_str:
                                metric_names = self._parse_metric_type_string(
                                    metric_type_str,
                                )
                                if metric_names:
                                    # Get metric type IDs
                                    metric_type_map = await self._get_metric_type_ids(
                                        metric_names,
                                        connection,
                                    )
                                    metric_type_ids = list(metric_type_map.values())

                                    # Save associations
                                    await self._save_metric_type_associations(
                                        str(result_id),
                                        metric_type_ids,
                                        connection,
                                    )

                            total_inserted += 1

                        logger.info(
                            f"Inserted batch {i // batch_size + 1}: "
                            f"{len(batch)} records (total: {total_inserted})",
                        )

            logger.info(
                f"Successfully saved {total_inserted} strategy sweep results "
                f"with metric type associations for sweep_run_id={sweep_run_id}",
            )
            return total_inserted

        except Exception as e:
            logger.exception(f"Failed to save strategy sweep results: {e}")
            raise

    async def get_sweep_results_with_metrics(
        self,
        sweep_run_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Retrieve all results for a specific sweep run with metric types.

        Args:
            sweep_run_id: UUID of the sweep run

        Returns:
            List of result dictionaries with metric_types array

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT
                sr.*,
                t.ticker,
                st.strategy_type,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'id', mt.id,
                            'name', mt.name,
                            'category', mt.category
                        )
                        ORDER BY mt.name
                    ) FILTER (WHERE mt.id IS NOT NULL),
                    '[]'::json
                ) as metric_types
            FROM strategy_sweep_results sr
            JOIN tickers t ON sr.ticker_id = t.id
            JOIN strategy_types st ON sr.strategy_type_id = st.id
            LEFT JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
            LEFT JOIN metric_types mt ON srm.metric_type_id = mt.id
            WHERE sr.sweep_run_id = $1
            GROUP BY sr.id, t.ticker, st.strategy_type
            ORDER BY sr.created_at, t.ticker, st.strategy_type
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, str(sweep_run_id))
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to retrieve sweep results with metrics: {e}")
            raise

    async def get_all_metric_types(self) -> list[dict[str, Any]]:
        """
        Retrieve all available metric types.

        Returns:
            List of metric type dictionaries

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT id, name, category, description, created_at
            FROM metric_types
            ORDER BY category, name
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to retrieve metric types: {e}")
            raise

    async def find_results_by_metric_type(
        self,
        metric_type_name: str,
        sweep_run_id: UUID | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Find sweep results that have a specific metric type classification.

        Args:
            metric_type_name: Name of the metric type (e.g., "Most Sharpe Ratio")
            sweep_run_id: Optional filter by specific sweep run
            limit: Maximum number of results to return

        Returns:
            List of sweep result dictionaries

        Raises:
            Exception: If database operation fails
        """
        base_query = """
            SELECT DISTINCT sr.*, mt.name as metric_type_name
            FROM strategy_sweep_results sr
            JOIN strategy_sweep_result_metrics srm ON sr.id = srm.sweep_result_id
            JOIN metric_types mt ON srm.metric_type_id = mt.id
            WHERE mt.name = $1
        """

        if sweep_run_id:
            query = (
                base_query + " AND sr.sweep_run_id = $2 ORDER BY sr.score DESC LIMIT $3"
            )
            params = [metric_type_name, str(sweep_run_id), limit]
        else:
            query = base_query + " ORDER BY sr.created_at DESC, sr.score DESC LIMIT $2"
            params = [metric_type_name, limit]

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, *params)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to find results by metric type: {e}")
            raise

    async def compute_and_save_best_selections(
        self,
        sweep_run_id: UUID,
        algorithm: str = "parameter_consistency",
    ) -> int:
        """
        Compute best portfolio for each ticker+strategy in sweep and save to database.

        Implements the parameter consistency algorithm:
        1. Top 3 all match (100% confidence)
        2. 3 of top 5 match (60-80% confidence)
        3. 5 of top 8 match (62.5% confidence)
        4. Top 2 both match (100% confidence)
        5. Fallback to highest score (0-50% confidence)

        Args:
            sweep_run_id: UUID of the sweep run
            algorithm: Algorithm to use (default: "parameter_consistency")

        Returns:
            Number of best selections created

        Raises:
            Exception: If database operation fails
        """
        from app.cli.services.best_selection_service import BestSelectionService

        logger.info(f"Computing best selections for sweep_run_id={sweep_run_id}")

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            # Get all results for this sweep
            results = await self.get_sweep_results_with_metrics(sweep_run_id)

            if not results:
                logger.warning(f"No results found for sweep_run_id={sweep_run_id}")
                return 0

            # Get unique ticker+strategy combinations
            combinations = set()
            for result in results:
                ticker = result.get("ticker")
                strategy_type = result.get("strategy_type")
                if ticker and strategy_type:
                    combinations.add((ticker, strategy_type))

            logger.info(f"Found {len(combinations)} ticker+strategy combinations")

            # Initialize selection service
            selection_service = BestSelectionService()

            # Compute best for each combination
            best_selections = []
            for ticker, strategy_type in combinations:
                selection = selection_service.find_best_for_ticker_strategy(
                    results,
                    ticker,
                    strategy_type,
                )

                if selection:
                    best_selections.append((ticker, strategy_type, selection))

            # Save all best selections to database
            async with self.db_manager._connection_pool.acquire() as connection:
                async with connection.transaction():
                    for ticker_symbol, strategy_type_name, selection in best_selections:
                        # Get ticker_id and strategy_type_id
                        ticker_id = await self._get_or_create_ticker(
                            ticker_symbol,
                            connection,
                        )
                        strategy_type_id = await self._get_or_create_strategy_type(
                            strategy_type_name,
                            connection,
                        )

                        best_result = selection["best_result"]
                        winning_combo = selection["winning_combination"]

                        # Insert best selection
                        insert_query = """
                            INSERT INTO sweep_best_selections (
                                sweep_run_id, ticker_id, strategy_type_id, best_result_id,
                                selection_algorithm, selection_criteria, confidence_score,
                                alternatives_considered, winning_fast_period,
                                winning_slow_period, winning_signal_period,
                                result_score, result_sharpe_ratio,
                                result_total_return_pct, result_win_rate_pct
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15
                            )
                            ON CONFLICT (sweep_run_id, ticker_id, strategy_type_id)
                            DO UPDATE SET
                                best_result_id = EXCLUDED.best_result_id,
                                selection_algorithm = EXCLUDED.selection_algorithm,
                                selection_criteria = EXCLUDED.selection_criteria,
                                confidence_score = EXCLUDED.confidence_score,
                                alternatives_considered = EXCLUDED.alternatives_considered,
                                winning_fast_period = EXCLUDED.winning_fast_period,
                                winning_slow_period = EXCLUDED.winning_slow_period,
                                winning_signal_period = EXCLUDED.winning_signal_period,
                                result_score = EXCLUDED.result_score,
                                result_sharpe_ratio = EXCLUDED.result_sharpe_ratio,
                                result_total_return_pct = EXCLUDED.result_total_return_pct,
                                result_win_rate_pct = EXCLUDED.result_win_rate_pct
                        """

                        await connection.execute(
                            insert_query,
                            str(sweep_run_id),
                            ticker_id,
                            strategy_type_id,
                            best_result.get("id"),
                            selection["selection_algorithm"],
                            selection["selection_criteria"],
                            selection["confidence_score"],
                            selection["alternatives_considered"],
                            winning_combo[0],  # fast_period
                            winning_combo[1],  # slow_period
                            winning_combo[2],  # signal_period
                            best_result.get("score"),
                            best_result.get("sharpe_ratio"),
                            best_result.get("total_return_pct"),
                            best_result.get("win_rate_pct"),
                        )

            logger.info(
                f"Saved {len(best_selections)} best selections for sweep_run_id={sweep_run_id}",
            )
            return len(best_selections)

        except Exception as e:
            logger.exception(f"Failed to compute and save best selections: {e}")
            raise

    async def get_best_selections(self, sweep_run_id: UUID) -> list[dict[str, Any]]:
        """
        Get all best selections for a sweep run with joined result data.

        Args:
            sweep_run_id: UUID of the sweep run

        Returns:
            List of best selection dictionaries with full result data

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT
                bs.id,
                bs.sweep_run_id,
                t.ticker,
                bs.ticker_id,
                st.strategy_type,
                bs.best_result_id,
                bs.selection_algorithm,
                bs.selection_criteria,
                bs.confidence_score,
                bs.alternatives_considered,
                bs.winning_fast_period,
                bs.winning_slow_period,
                bs.winning_signal_period,
                bs.result_score,
                bs.result_sharpe_ratio,
                bs.result_total_return_pct,
                bs.result_win_rate_pct,
                bs.created_at,
                sr.score as current_score,
                sr.sharpe_ratio as current_sharpe_ratio,
                sr.total_return_pct as current_total_return_pct
            FROM sweep_best_selections bs
            JOIN tickers t ON bs.ticker_id = t.id
            JOIN strategy_types st ON bs.strategy_type_id = st.id
            LEFT JOIN strategy_sweep_results sr ON bs.best_result_id = sr.id
            WHERE bs.sweep_run_id = $1
            ORDER BY bs.confidence_score DESC, bs.result_score DESC
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, str(sweep_run_id))
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to get best selections: {e}")
            raise

    async def get_best_result_for_ticker(
        self,
        sweep_run_id: UUID,
        ticker: str,
        strategy_type: str,
    ) -> dict[str, Any] | None:
        """
        Get the best result for specific ticker and strategy.

        Args:
            sweep_run_id: UUID of the sweep run
            ticker: Ticker symbol
            strategy_type: Strategy type

        Returns:
            Best result dictionary or None if not found

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT
                sr.*,
                t.ticker,
                st.strategy_type,
                bs.selection_criteria,
                bs.confidence_score
            FROM sweep_best_selections bs
            JOIN tickers t ON bs.ticker_id = t.id
            JOIN strategy_types st ON bs.strategy_type_id = st.id
            JOIN strategy_sweep_results sr ON bs.best_result_id = sr.id
            WHERE bs.sweep_run_id = $1
              AND t.ticker = $2
              AND st.strategy_type = $3
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                row = await connection.fetchrow(
                    query,
                    str(sweep_run_id),
                    ticker,
                    strategy_type,
                )
                return dict(row) if row else None

        except Exception as e:
            logger.exception(f"Failed to get best result for ticker: {e}")
            raise

    async def get_sweep_results_with_best_flag(
        self,
        sweep_run_id: UUID,
    ) -> list[dict[str, Any]]:
        """
        Get all sweep results with is_best boolean flag.

        Args:
            sweep_run_id: UUID of the sweep run

        Returns:
            List of result dictionaries with is_best flag

        Raises:
            Exception: If database operation fails
        """
        query = """
            SELECT
                sr.*,
                t.ticker,
                st.strategy_type,
                CASE
                    WHEN bs.best_result_id IS NOT NULL THEN TRUE
                    ELSE FALSE
                END as is_best,
                bs.selection_criteria,
                bs.confidence_score
            FROM strategy_sweep_results sr
            JOIN tickers t ON sr.ticker_id = t.id
            JOIN strategy_types st ON sr.strategy_type_id = st.id
            LEFT JOIN sweep_best_selections bs
                ON sr.id = bs.best_result_id
                AND sr.sweep_run_id = bs.sweep_run_id
            WHERE sr.sweep_run_id = $1
            ORDER BY t.ticker, st.strategy_type, sr.score DESC
        """

        try:
            if not self.db_manager._connection_pool:
                msg = "Database connection pool not initialized"
                raise RuntimeError(msg)

            async with self.db_manager._connection_pool.acquire() as connection:
                rows = await connection.fetch(query, str(sweep_run_id))
                return [dict(row) for row in rows]

        except Exception as e:
            logger.exception(f"Failed to get results with best flag: {e}")
            raise
