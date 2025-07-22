#!/usr/bin/env python3
"""
Strategy Data Coordinator Service

Central data coordination service that eliminates duplicate data loading logic
across the trading system and ensures data consistency between all services.

This service provides:
- Unified data access layer for all strategy data
- Coordinated data refresh cycles
- Central validation and constraint checking
- Data versioning and lineage tracking
- Single source of truth for strategy information

Replaces 60+ scattered data loading implementations with centralized coordination.
"""

import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd
import polars as pl

from app.core.interfaces import LoggingInterface

# Import unified data models and interfaces
from app.tools.models.unified_strategy_models import (
    BacktestingParameters,
    DataSourceType,
    PerformanceMetrics,
    SignalInformation,
    StatisticalMetrics,
    UnifiedStrategyData,
    migrate_legacy_strategy_data,
)

# Type alias for compatibility during migration
StrategyData = UnifiedStrategyData

logger = logging.getLogger(__name__)


@dataclass
class DataSourceMetadata:
    """Metadata for tracking data sources and freshness"""

    source_type: str  # 'json', 'positions', 'csv', 'live'
    file_path: str
    last_modified: datetime
    last_accessed: datetime
    data_version: str
    checksum: str = ""


@dataclass
class DataSnapshot:
    """Immutable data snapshot for consistent multi-service operations"""

    snapshot_id: str
    created_at: datetime
    strategy_data: Dict[str, StrategyData] = field(default_factory=dict)
    metadata: Dict[str, DataSourceMetadata] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataCoordinationConfig:
    """Configuration for data coordination behavior"""

    enable_validation: bool = True
    enable_auto_refresh: bool = True
    max_data_age_minutes: int = 30
    enable_memory_optimization: bool = True
    concurrent_loading: bool = True
    max_workers: int = 4
    cache_ttl_minutes: int = 15


class StrategyDataCoordinatorError(Exception):
    """Exception raised by StrategyDataCoordinator."""

    pass


class StrategyDataCoordinator:
    """
    Central coordinator for all strategy data loading, validation, and consistency.

    This service eliminates the 60+ duplicate data loading implementations across
    the codebase by providing a single, coordinated access point for all strategy data.

    Key Features:
    - Unified data loading from all sources (JSON, CSV, positions, live)
    - Mathematical constraint validation at data level
    - Coordinated refresh cycles preventing temporal inconsistencies
    - Data versioning and snapshot management
    - Memory optimization integration
    - Comprehensive error handling and monitoring
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        logger: Optional[LoggingInterface] = None,
        config: Optional[DataCoordinationConfig] = None,
    ):
        """
        Initialize the strategy data coordinator.

        Args:
            base_path: Base path for data files (defaults to current working directory)
            logger: Logger interface for consistent logging
            config: Configuration for coordination behavior
        """
        self.base_path = base_path or Path.cwd()
        self.logger = logger
        self.config = config or DataCoordinationConfig()

        # Data storage and caching
        self._data_cache: Dict[str, StrategyData] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        self._data_snapshots: Dict[str, DataSnapshot] = {}
        self._source_metadata: Dict[str, DataSourceMetadata] = {}

        # Coordination state
        self._refresh_lock = threading.RLock()
        self._snapshot_lock = threading.RLock()
        self._active_snapshots: Set[str] = set()

        # Warning cache to prevent repeated messages
        self._warning_cache: Set[str] = set()

        # File paths
        self.exports_path = self.base_path / "data" / "outputs" / "spds"
        self.statistical_csv = (
            self.exports_path / "statistical_analysis" / "live_signals.csv"
        )
        self.statistical_json = (
            self.exports_path / "statistical_analysis" / "live_signals.json"
        )
        self.backtesting_json = (
            self.exports_path / "backtesting_parameters" / "live_signals.json"
        )
        self.backtesting_csv = (
            self.exports_path / "backtesting_parameters" / "live_signals.csv"
        )
        self.positions_csv = (
            self.base_path / "data" / "raw" / "positions" / "live_signals.csv"
        )

        # Initialize memory optimization if enabled
        if self.config.enable_memory_optimization:
            self._init_memory_optimization()

        # Validate required files exist
        self._validate_data_sources()

        logger.info(
            "StrategyDataCoordinator initialized with central coordination enabled"
        ) if logger else None

    def _init_memory_optimization(self):
        """Initialize memory optimization components if available"""
        try:
            from app.tools.processing import configure_memory_optimizer

            self.memory_optimizer = configure_memory_optimizer(
                enable_pooling=True, enable_monitoring=True, memory_threshold_mb=1000.0
            )
            logger.info(
                "Memory optimization enabled in StrategyDataCoordinator"
            ) if self.logger else None
        except ImportError:
            self.memory_optimizer = None
            logger.warning("Memory optimization not available") if self.logger else None

    def _validate_data_sources(self):
        """Validate that required data sources exist and are accessible"""
        required_files = [
            self.statistical_csv,
            self.statistical_json,
            self.positions_csv,
        ]

        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            logger.warning(
                f"Missing data source files: {missing_files}"
            ) if self.logger else None

        # Check file permissions
        for file_path in [f for f in required_files if f.exists()]:
            if not file_path.is_file() or not file_path.stat().st_size > 0:
                logger.warning(
                    f"Data source file empty or invalid: {file_path}"
                ) if self.logger else None

    def get_strategy_data(
        self,
        strategy_identifier: str,
        force_refresh: bool = False,
        snapshot_id: Optional[str] = None,
    ) -> Optional[StrategyData]:
        """
        Get comprehensive strategy data by identifier with central coordination.

        This is the primary interface that replaces all scattered data loading logic.

        Args:
            strategy_identifier: Strategy name or Position_UUID
            force_refresh: Force fresh data loading bypassing cache
            snapshot_id: Use specific data snapshot for consistency

        Returns:
            StrategyData object with all coordinated data or None if not found
        """
        try:
            # Use snapshot data if specified
            if snapshot_id and snapshot_id in self._data_snapshots:
                snapshot = self._data_snapshots[snapshot_id]
                return snapshot.strategy_data.get(strategy_identifier)

            # Check cache first (unless forcing refresh)
            if not force_refresh and self._is_cache_valid(strategy_identifier):
                cached_data = self._data_cache.get(strategy_identifier)
                if cached_data:
                    logger.debug(
                        f"Returning cached data for {strategy_identifier}"
                    ) if self.logger else None
                    return cached_data

            # Load fresh data with coordination
            with self._refresh_lock:
                strategy_data = self._load_coordinated_strategy_data(
                    strategy_identifier
                )

                if strategy_data:
                    # Update cache
                    self._data_cache[strategy_identifier] = strategy_data
                    self._cache_timestamps[strategy_identifier] = datetime.now()

                    logger.info(
                        f"Successfully loaded coordinated data for {strategy_identifier}"
                    ) if self.logger else None
                    return strategy_data
                else:
                    # Enhanced error reporting with suggestions
                    self._log_strategy_not_found_with_suggestions(strategy_identifier)
                    return None

        except Exception as e:
            logger.error(
                f"Error loading strategy data for {strategy_identifier}: {e}"
            ) if self.logger else None
            raise StrategyDataCoordinatorError(f"Failed to load strategy data: {e}")

    def _load_coordinated_strategy_data(
        self, strategy_identifier: str
    ) -> Optional[StrategyData]:
        """
        Load strategy data with full coordination across all sources.

        This method implements the central data loading logic that eliminates
        duplication across the codebase.
        """
        try:
            # Step 1: Find strategy in statistical CSV (primary index)
            strategy_row = self._find_strategy_in_csv(strategy_identifier)
            if not strategy_row:
                return None

            # Get strategy_name from row (may be constructed if CSV doesn't have strategy_name column)
            strategy_name = strategy_row.get("strategy_name")
            if not strategy_name:
                # Construct strategy_name if not present (backup safety check)
                ticker = strategy_row.get("ticker", "UNKNOWN")
                strategy_type = strategy_row.get("strategy_type", "UNKNOWN")
                short_window = strategy_row.get("short_window", 0)
                long_window = strategy_row.get("long_window", 0)
                strategy_name = (
                    f"{ticker}_{strategy_type}_{int(short_window)}_{int(long_window)}"
                )
                strategy_row[
                    "strategy_name"
                ] = strategy_name  # Add to row for consistency

            # Step 2: Create unified strategy data object with structured components
            strategy_data = UnifiedStrategyData(
                strategy_name=strategy_name,
                ticker=strategy_row["ticker"],
                timeframe=strategy_row.get("timeframe", "D"),
                position_uuid=self._generate_position_uuid(strategy_row),
                generation_timestamp=datetime.now().isoformat(),
                performance=PerformanceMetrics(),
                statistics=StatisticalMetrics(),
                backtesting=BacktestingParameters(),
                signal=SignalInformation(),
            )

            # Add initial data lineage
            strategy_data.add_data_lineage(
                source_type=DataSourceType.COORDINATOR,
                metadata={"initial_load": True, "coordinator_version": "2.0"},
            )

            # Step 3: Coordinate data loading from all sources
            loading_tasks = []

            if self.config.concurrent_loading:
                # Load from multiple sources concurrently
                with ThreadPoolExecutor(
                    max_workers=self.config.max_workers
                ) as executor:
                    # Submit all loading tasks
                    tasks = {
                        executor.submit(
                            self._populate_from_statistical_csv,
                            strategy_data,
                            strategy_row,
                        ): "statistical_csv",
                        executor.submit(
                            self._populate_from_statistical_json,
                            strategy_data,
                            strategy_name,
                        ): "statistical_json",
                        executor.submit(
                            self._populate_from_backtesting_data,
                            strategy_data,
                            strategy_name,
                        ): "backtesting",
                        executor.submit(
                            self._populate_from_positions_data,
                            strategy_data,
                            strategy_name,
                        ): "positions",
                        executor.submit(
                            self._populate_from_asset_distribution,
                            strategy_data,
                            strategy_data.ticker,
                        ): "asset_distribution",
                    }

                    # Wait for completion and handle results
                    for future in as_completed(tasks):
                        source_name = tasks[future]
                        try:
                            result = future.result(
                                timeout=10
                            )  # 10 second timeout per source
                            logger.debug(
                                f"Successfully loaded data from {source_name} for {strategy_name}"
                            ) if self.logger else None
                        except Exception as e:
                            logger.warning(
                                f"Failed to load data from {source_name} for {strategy_name}: {e}"
                            ) if self.logger else None
            else:
                # Sequential loading (fallback)
                self._populate_from_statistical_csv(strategy_data, strategy_row)
                self._populate_from_statistical_json(strategy_data, strategy_name)
                self._populate_from_backtesting_data(strategy_data, strategy_name)
                self._populate_from_positions_data(strategy_data, strategy_name)
                self._populate_from_asset_distribution(
                    strategy_data, strategy_data.ticker
                )

            # Step 4: Perform central validation
            if self.config.enable_validation:
                validation_result = self._validate_strategy_data(
                    strategy_data, strategy_name
                )
                if validation_result["critical_violations"]:
                    logger.error(
                        f"Critical validation failures for {strategy_name}: {validation_result['critical_violations']}"
                    ) if self.logger else None
                    # Still return data but with warnings

            # Step 5: Apply memory optimization if enabled
            if self.memory_optimizer:
                try:
                    # Optimize any dataframes in raw_analysis_data
                    if strategy_data.raw_analysis_data and isinstance(
                        strategy_data.raw_analysis_data, dict
                    ):
                        for key, value in strategy_data.raw_analysis_data.items():
                            if hasattr(value, "memory_usage"):  # Likely a DataFrame
                                strategy_data.raw_analysis_data[
                                    key
                                ] = self.memory_optimizer.optimize_dataframe(value)
                except Exception as e:
                    logger.warning(
                        f"Memory optimization failed for {strategy_name}: {e}"
                    ) if self.logger else None

            return strategy_data

        except Exception as e:
            logger.error(
                f"Error in coordinated data loading for {strategy_identifier}: {e}"
            ) if self.logger else None
            return None

    def _populate_from_statistical_csv(
        self, strategy_data: UnifiedStrategyData, strategy_row: Dict[str, Any]
    ):
        """Populate strategy data from statistical CSV using structured format"""
        try:
            # Update statistical metrics
            strategy_data.statistics.sample_size = int(
                strategy_row.get("sample_size", 0)
            )
            strategy_data.statistics.sample_size_confidence = float(
                strategy_row.get("sample_size_confidence", 0.0)
            )
            strategy_data.statistics.dual_layer_convergence_score = float(
                strategy_row.get("dual_layer_convergence_score", 0.0)
            )
            strategy_data.statistics.asset_layer_percentile = float(
                strategy_row.get("asset_layer_percentile", 0.0)
            )
            strategy_data.statistics.strategy_layer_percentile = float(
                strategy_row.get("strategy_layer_percentile", 0.0)
            )
            strategy_data.statistics.statistical_significance = strategy_row.get(
                "statistical_significance", "LOW"
            )
            strategy_data.statistics.p_value = float(strategy_row.get("p_value", 0.1))
            strategy_data.statistics.z_score_divergence = float(
                strategy_row.get("z_score_divergence", 0.0)
            )
            strategy_data.statistics.iqr_divergence = float(
                strategy_row.get("iqr_divergence", 0.0)
            )
            strategy_data.statistics.rarity_score = float(
                strategy_row.get("rarity_score", 0.0)
            )

            # Update signal information
            strategy_data.signal.exit_signal = strategy_row.get(
                "exit_signal", "UNKNOWN"
            )
            strategy_data.signal.signal_confidence = float(
                strategy_row.get("signal_confidence", 0.0)
            )
            strategy_data.signal.exit_recommendation = strategy_row.get(
                "exit_recommendation", ""
            )
            strategy_data.signal.target_exit_timeframe = strategy_row.get(
                "target_exit_timeframe", ""
            )

            # Update performance metrics with NaN handling
            strategy_data.performance.current_return = self._safe_float_conversion(
                strategy_row.get("current_return", 0.0), default=0.0
            )
            strategy_data.performance.mfe = self._safe_float_conversion(
                strategy_row.get("mfe", 0.0), default=0.0
            )
            strategy_data.performance.mae = self._safe_float_conversion(
                strategy_row.get("mae", 0.0), default=0.0
            )
            strategy_data.performance.unrealized_pnl = self._safe_float_conversion(
                strategy_row.get("unrealized_pnl", 0.0), default=0.0
            )

            # Add data lineage
            strategy_data.add_data_lineage(
                source_type=DataSourceType.STATISTICAL_CSV,
                file_path=str(self.statistical_csv),
                metadata={"row_data_loaded": True},
            )

        except (ValueError, TypeError) as e:
            logger.warning(
                f"Error parsing statistical CSV data: {e}"
            ) if self.logger else None

    def _populate_from_statistical_json(
        self, strategy_data: UnifiedStrategyData, strategy_name: str
    ):
        """Populate strategy data from statistical JSON using structured format"""
        try:
            if not self.statistical_json.exists():
                return

            with open(self.statistical_json, "r") as f:
                json_data = json.load(f)

            # Find matching strategy in JSON
            strategy_result = None
            for result in json_data.get("results", []):
                if result.get("strategy_name") == strategy_name:
                    strategy_result = result
                    break

            if not strategy_result:
                return

            # Extract performance metrics from JSON (often more accurate than CSV)
            performance_metrics = strategy_result.get("performance_metrics", {})
            if performance_metrics:
                # JSON is authoritative for current_return
                if (
                    "current_return" in performance_metrics
                    and performance_metrics["current_return"] is not None
                ):
                    strategy_data.performance.current_return = (
                        self._safe_float_conversion(
                            performance_metrics["current_return"], default=0.0
                        )
                    )

                # Use JSON MFE/MAE if they have valid values (not zero)
                if "mfe" in performance_metrics and performance_metrics["mfe"] not in (
                    None,
                    0.0,
                ):
                    strategy_data.performance.mfe = self._safe_float_conversion(
                        performance_metrics["mfe"], default=0.0
                    )

                if "mae" in performance_metrics and performance_metrics["mae"] not in (
                    None,
                    0.0,
                ):
                    strategy_data.performance.mae = self._safe_float_conversion(
                        performance_metrics["mae"], default=0.0
                    )

                if (
                    "unrealized_pnl" in performance_metrics
                    and performance_metrics["unrealized_pnl"] is not None
                ):
                    strategy_data.performance.unrealized_pnl = float(
                        performance_metrics["unrealized_pnl"]
                    )

            # Store raw JSON data for advanced analysis
            strategy_data.raw_analysis_data = strategy_result

            # Add data lineage
            strategy_data.add_data_lineage(
                source_type=DataSourceType.STATISTICAL_JSON,
                file_path=str(self.statistical_json),
                metadata={
                    "json_metrics_loaded": True,
                    "has_performance_metrics": bool(performance_metrics),
                },
            )

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning(
                f"Error loading statistical JSON for {strategy_name}: {e}"
            ) if self.logger else None

    def _populate_from_backtesting_data(
        self, strategy_data: UnifiedStrategyData, strategy_name: str
    ):
        """Populate backtesting parameters using structured format"""
        try:
            # Try JSON first, then CSV
            for file_path in [self.backtesting_json, self.backtesting_csv]:
                if not file_path.exists():
                    continue

                if file_path.suffix == ".json":
                    self._load_backtesting_from_json(
                        strategy_data, strategy_name, file_path
                    )
                else:
                    self._load_backtesting_from_csv(
                        strategy_data, strategy_name, file_path
                    )

                # Break if we successfully loaded parameters
                if (
                    strategy_data.backtesting.take_profit_pct > 0
                    or strategy_data.backtesting.stop_loss_pct > 0
                ):
                    break

            # Add data lineage
            strategy_data.add_data_lineage(
                source_type=DataSourceType.BACKTESTING_JSON
                if self.backtesting_json.exists()
                else DataSourceType.BACKTESTING_CSV,
                file_path=str(
                    self.backtesting_json
                    if self.backtesting_json.exists()
                    else self.backtesting_csv
                ),
                metadata={"backtesting_params_loaded": True},
            )

        except Exception as e:
            logger.warning(
                f"Error loading backtesting parameters for {strategy_name}: {e}"
            ) if self.logger else None

    def _load_backtesting_from_json(
        self, strategy_data: UnifiedStrategyData, strategy_name: str, file_path: Path
    ):
        """Load backtesting parameters from JSON file using structured format"""
        try:
            with open(file_path, "r") as f:
                json_data = json.load(f)

            # Find matching strategy
            for result in json_data.get("results", []):
                if result.get("strategy_name") == strategy_name:
                    params = result.get("parameters", {})

                    strategy_data.backtesting.take_profit_pct = float(
                        params.get("take_profit_pct", 0.0)
                    )
                    strategy_data.backtesting.stop_loss_pct = float(
                        params.get("stop_loss_pct", 0.0)
                    )
                    strategy_data.backtesting.trailing_stop_pct = float(
                        params.get("trailing_stop_pct", 0.0)
                    )
                    strategy_data.backtesting.max_holding_days = int(
                        params.get("max_holding_days", 0)
                    )
                    strategy_data.backtesting.min_holding_days = int(
                        params.get("min_holding_days", 0)
                    )
                    strategy_data.backtesting.momentum_exit_threshold = float(
                        params.get("momentum_exit_threshold", 0.0)
                    )
                    strategy_data.backtesting.trend_exit_threshold = float(
                        params.get("trend_exit_threshold", 0.0)
                    )
                    strategy_data.backtesting.confidence_level = float(
                        params.get("confidence_level", 0.0)
                    )
                    break

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(
                f"Error parsing backtesting JSON: {e}"
            ) if self.logger else None

    def _load_backtesting_from_csv(
        self, strategy_data: UnifiedStrategyData, strategy_name: str, file_path: Path
    ):
        """Load backtesting parameters from CSV file using structured format"""
        try:
            df = pd.read_csv(file_path)
            matches = pd.DataFrame()  # Initialize empty matches

            # Handle CSV files with explicit strategy_name column (new format)
            if "strategy_name" in df.columns:
                matches = df[df["strategy_name"] == strategy_name]

            # Handle CSV files without strategy_name column (legacy format)
            elif all(
                col in df.columns
                for col in ["ticker", "strategy_type", "short_window", "long_window"]
            ):
                # Show warning only once per file
                warning_key = f"backtesting_csv_no_strategy_name_{file_path}"
                if warning_key not in self._warning_cache:
                    logger.info(
                        f"CSV file {file_path} missing 'strategy_name' column, constructing from components"
                    ) if self.logger else None
                    self._warning_cache.add(warning_key)

                # Parse strategy_name components from input
                if "_" in strategy_name:
                    parts = strategy_name.split("_")
                    if len(parts) >= 3:
                        strategy_type = parts[0]  # e.g., "SMA"
                        short_window = parts[1]  # e.g., "78"
                        long_window = parts[2]  # e.g., "82"

                        # Extract ticker from strategy_data
                        ticker = (
                            strategy_data.ticker
                            if hasattr(strategy_data, "ticker")
                            else None
                        )

                        if ticker:
                            # Find matching row using component matching
                            matches = df[
                                (df["ticker"] == ticker)
                                & (df["strategy_type"] == strategy_type)
                                & (df["short_window"].astype(str) == short_window)
                                & (df["long_window"].astype(str) == long_window)
                            ]
            else:
                # Unknown CSV format
                warning_key = f"backtesting_csv_unknown_format_{file_path}"
                if warning_key not in self._warning_cache:
                    logger.warning(
                        f"CSV file {file_path} has unrecognized format for backtesting parameters"
                    ) if self.logger else None
                    self._warning_cache.add(warning_key)
                return

            # Process matched row if found
            if not matches.empty:
                row = matches.iloc[0]

                strategy_data.backtesting.take_profit_pct = float(
                    row.get("take_profit_pct", 0.0)
                )
                strategy_data.backtesting.stop_loss_pct = float(
                    row.get("stop_loss_pct", 0.0)
                )
                strategy_data.backtesting.trailing_stop_pct = float(
                    row.get("trailing_stop_pct", 0.0)
                )
                strategy_data.backtesting.max_holding_days = int(
                    row.get("max_holding_days", 0)
                )
                strategy_data.backtesting.min_holding_days = int(
                    row.get("min_holding_days", 0)
                )
                strategy_data.backtesting.momentum_exit_threshold = float(
                    row.get("momentum_exit_threshold", 0.0)
                )
                strategy_data.backtesting.trend_exit_threshold = float(
                    row.get("trend_exit_threshold", 0.0)
                )
                strategy_data.backtesting.confidence_level = float(
                    row.get("confidence_level", 0.0)
                )

        except (pd.errors.EmptyDataError, ValueError, KeyError) as e:
            logger.warning(
                f"Error parsing backtesting CSV {file_path}: {e}"
            ) if self.logger else None
        except Exception as e:
            logger.warning(
                f"Unexpected error reading backtesting CSV {file_path}: {e}"
            ) if self.logger else None

    def _populate_from_positions_data(
        self, strategy_data: UnifiedStrategyData, strategy_name: str
    ):
        """Populate data from positions file with enhanced validation using structured format"""
        try:
            if not self.positions_csv.exists():
                return

            df = pd.read_csv(self.positions_csv)

            # Find matching position using flexible pattern matching
            position = self._find_matching_position(df, strategy_name)
            if position is None:
                return

            # Load MFE and MAE with validation
            self._load_mfe_mae_from_position(strategy_data, position, strategy_name)

            # Load additional position data
            if "Status" in position and position["Status"] in ["Open", "OPEN"]:
                # Position is active, validate data freshness
                entry_date = position.get("Entry_Date", position.get("entry_date", ""))
                if entry_date:
                    try:
                        entry_dt = pd.to_datetime(entry_date)
                        position_age = (datetime.now() - entry_dt).days

                        if position_age > 90:  # Position older than 90 days
                            logger.warning(
                                f"Position {strategy_name} is {position_age} days old - data may be stale"
                            ) if self.logger else None
                        elif position_age < 0:  # Future date (error)
                            logger.error(
                                f"Position {strategy_name} has invalid entry date: {entry_date}"
                            ) if self.logger else None
                            return
                    except (ValueError, TypeError):
                        logger.warning(
                            f"Invalid entry date for {strategy_name}: {entry_date}"
                        ) if self.logger else None

        except Exception as e:
            logger.warning(
                f"Error loading positions data for {strategy_name}: {e}"
            ) if self.logger else None

    def _find_matching_position(
        self, df: pd.DataFrame, strategy_name: str
    ) -> Optional[pd.Series]:
        """Find matching position using multiple patterns"""
        patterns = [
            strategy_name,  # Exact match
            strategy_name.replace("_", " "),  # Replace underscores with spaces
            strategy_name.split("_")[0],  # Just ticker
        ]

        # Try different column names for position identification
        id_columns = ["Position_UUID", "strategy_name", "ticker", "Strategy"]

        for column in id_columns:
            if column not in df.columns:
                continue

            for pattern in patterns:
                matches = df[df[column].str.contains(pattern, case=False, na=False)]
                if not matches.empty:
                    return matches.iloc[0]

        return None

    def _load_mfe_mae_from_position(
        self,
        strategy_data: UnifiedStrategyData,
        position: pd.Series,
        strategy_name: str,
    ):
        """Load MFE and MAE from position data with validation using structured format"""
        try:
            # Try different column name variations
            mfe_columns = ["Max_Favourable_Excursion", "MFE", "max_favorable_excursion"]
            mae_columns = ["Max_Adverse_Excursion", "MAE", "max_adverse_excursion"]

            for col in mfe_columns:
                if col in position and pd.notna(position[col]):
                    new_mfe = self._safe_float_conversion(position[col], default=0.0)

                    # Validate MFE - log warning but continue processing
                    if strategy_data.performance.current_return > 0 and new_mfe < 0:
                        logger.info(
                            f"Using historical negative MFE ({new_mfe:.4f}) for currently profitable position {strategy_name}"
                        ) if self.logger else None

                    # Use positions MFE if JSON had zero or if positions value seems more reasonable
                    if strategy_data.performance.mfe == 0.0 or abs(new_mfe) > abs(
                        strategy_data.performance.mfe
                    ):
                        old_mfe = strategy_data.performance.mfe
                        strategy_data.performance.mfe = new_mfe
                        logger.info(
                            f"Using MFE from positions file: {new_mfe:.4f} (was {old_mfe:.4f})"
                        ) if self.logger else None
                    break

            for col in mae_columns:
                if col in position and pd.notna(position[col]):
                    new_mae = self._safe_float_conversion(position[col], default=0.0)

                    # Use positions MAE if JSON had zero or if positions value seems more reasonable
                    if strategy_data.performance.mae == 0.0 or abs(new_mae) > abs(
                        strategy_data.performance.mae
                    ):
                        old_mae = strategy_data.performance.mae
                        strategy_data.performance.mae = new_mae
                        logger.info(
                            f"Using MAE from positions file: {new_mae:.4f} (was {old_mae:.4f})"
                        ) if self.logger else None
                    break

            # Add data lineage for positions data
            strategy_data.add_data_lineage(
                source_type=DataSourceType.POSITIONS_CSV,
                file_path=str(self.positions_csv),
                metadata={"mfe_mae_loaded": True},
            )

        except (ValueError, TypeError) as e:
            logger.warning(
                f"Error parsing MFE/MAE from positions for {strategy_name}: {e}"
            ) if self.logger else None

    def _populate_from_asset_distribution(
        self, strategy_data: UnifiedStrategyData, ticker: str
    ):
        """Populate asset distribution analysis data from return distribution files"""
        try:
            # Construct path to asset distribution file
            distribution_file = (
                Path("data/raw/reports/return_distribution") / f"{ticker}.json"
            )

            if not distribution_file.exists():
                logger.warning(
                    f"Asset distribution file not found for {ticker}: {distribution_file}"
                ) if self.logger else None
                return

            # Load asset distribution data
            with open(distribution_file, "r") as f:
                asset_data = json.load(f)

            # Extract timeframe analysis (assuming 'D' for daily)
            timeframe_data = asset_data.get("timeframe_analysis", {}).get("D", {})
            if not timeframe_data:
                logger.warning(
                    f"No daily timeframe data found for {ticker}"
                ) if self.logger else None
                return

            # Extract statistical metrics
            descriptive_stats = timeframe_data.get("descriptive_statistics", {})
            percentiles = timeframe_data.get("percentiles", {})
            var_metrics = timeframe_data.get("var_metrics", {})

            # Create asset analysis structure for raw_analysis_data
            asset_analysis = {
                "statistics": {
                    "mean": descriptive_stats.get("mean", 0.0),
                    "median": descriptive_stats.get("median", 0.0),
                    "std": descriptive_stats.get("std_dev", 0.0),
                    "min": descriptive_stats.get("min", 0.0),
                    "max": descriptive_stats.get("max", 0.0),
                    "skewness": descriptive_stats.get("skewness", 0.0),
                    "kurtosis": descriptive_stats.get("kurtosis", 0.0),
                    "count": timeframe_data.get("returns_count", 0),
                },
                "percentiles": percentiles,
                "var_metrics": var_metrics,
                "current_return": timeframe_data.get("current_return", 0.0),
                "current_percentile": timeframe_data.get("current_percentile", 0.0),
                "regime_score": timeframe_data.get("regime_score", 0.0),
                "volatility_regime": timeframe_data.get("volatility_regime", "medium"),
            }

            # Initialize raw_analysis_data if not exists
            if not strategy_data.raw_analysis_data:
                strategy_data.raw_analysis_data = {}

            # Add asset analysis to raw_analysis_data
            strategy_data.raw_analysis_data["asset_analysis"] = asset_analysis

            # Add data lineage
            strategy_data.add_data_lineage(
                source_type=DataSourceType.ASSET_DISTRIBUTION,
                file_path=str(distribution_file),
                metadata={"asset_analysis_loaded": True, "ticker": ticker},
            )

            logger.info(
                f"Successfully loaded asset distribution data for {ticker}"
            ) if self.logger else None

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.warning(
                f"Error loading asset distribution for {ticker}: {e}"
            ) if self.logger else None

    def _validate_strategy_data(
        self, strategy_data: UnifiedStrategyData, strategy_name: str
    ) -> Dict[str, Any]:
        """
        Central validation logic for mathematical constraints and data quality using unified data models.

        This consolidates validation logic that was scattered across multiple services
        and uses the built-in validation from UnifiedStrategyData.
        """
        validation_result = {
            "strategy_name": strategy_name,
            "timestamp": datetime.now().isoformat(),
            "constraints_passed": 0,
            "constraints_failed": 0,
            "critical_violations": [],
            "warnings": [],
            "data_quality_score": 0.0,
        }

        try:
            # Use the built-in validation from UnifiedStrategyData
            unified_validation_results = strategy_data.validate(auto_fix=False)

            # Convert UnifiedStrategyData validation results to legacy format
            for result in unified_validation_results:
                if result.severity.value in ["CRITICAL", "ERROR"]:
                    validation_result["constraints_failed"] += 1
                    validation_result["critical_violations"].append(result.message)
                elif result.severity.value == "WARNING":
                    validation_result["warnings"].append(result.message)
                else:  # INFO
                    validation_result["constraints_passed"] += 1

            # Calculate total constraints (based on unified model validation)
            total_constraints = (
                len(unified_validation_results) if unified_validation_results else 6
            )

            # Additional legacy constraint checks for backward compatibility
            legacy_passed = 0
            legacy_total = 6

            # Constraint 1: Basic data validity
            performance_attrs = ["current_return", "mfe", "mae"]
            if all(
                isinstance(getattr(strategy_data.performance, attr), (int, float))
                and pd.notna(getattr(strategy_data.performance, attr))
                for attr in performance_attrs
            ):
                legacy_passed += 1
            else:
                validation_result["critical_violations"].append(
                    "Invalid or missing performance metrics"
                )

            # Constraint 2: MFE cannot be negative if current return is positive
            if strategy_data.performance.current_return > 0:
                if strategy_data.performance.mfe >= 0:
                    legacy_passed += 1
                else:
                    validation_result["critical_violations"].append(
                        f"Negative MFE ({strategy_data.performance.mfe:.4f}) with positive return ({strategy_data.performance.current_return:.4f})"
                    )
            else:
                legacy_passed += 1

            # Constraint 3: Current return should not exceed MFE (mathematical impossibility)
            if strategy_data.performance.mfe > 0:
                if (
                    strategy_data.performance.current_return
                    <= strategy_data.performance.mfe
                ):
                    legacy_passed += 1
                else:
                    excess_pct = (
                        (
                            strategy_data.performance.current_return
                            - strategy_data.performance.mfe
                        )
                        / strategy_data.performance.mfe
                    ) * 100
                    validation_result["critical_violations"].append(
                        f"Current return ({strategy_data.performance.current_return:.4f}) exceeds MFE ({strategy_data.performance.mfe:.4f}) by {excess_pct:.1f}%"
                    )
            else:
                legacy_passed += 1

            # Constraint 4: MAE validation for negative returns
            if (
                strategy_data.performance.mae < 0
                and strategy_data.performance.current_return
                < strategy_data.performance.mae
            ):
                validation_result["critical_violations"].append(
                    f"Current return ({strategy_data.performance.current_return:.4f}) worse than MAE ({strategy_data.performance.mae:.4f})"
                )
            else:
                legacy_passed += 1

            # Constraint 5: Sample size validation
            if strategy_data.statistics.sample_size > 0:
                legacy_passed += 1
            else:
                validation_result["warnings"].append("Missing or zero sample size")

            # Constraint 6: Statistical significance consistency
            if (
                (
                    strategy_data.statistics.statistical_significance == "HIGH"
                    and strategy_data.statistics.p_value <= 0.05
                )
                or (
                    strategy_data.statistics.statistical_significance == "MEDIUM"
                    and 0.05 < strategy_data.statistics.p_value <= 0.1
                )
                or (
                    strategy_data.statistics.statistical_significance == "LOW"
                    and strategy_data.statistics.p_value > 0.1
                )
            ):
                legacy_passed += 1
            else:
                validation_result["warnings"].append(
                    f"Statistical significance ({strategy_data.statistics.statistical_significance}) inconsistent with p-value ({strategy_data.statistics.p_value})"
                )

            # Combine results (use unified validation score if available, otherwise legacy)
            if unified_validation_results:
                validation_result[
                    "data_quality_score"
                ] = strategy_data.get_data_quality_score()
                validation_result["constraints_passed"] = sum(
                    1
                    for r in unified_validation_results
                    if r.severity.value not in ["CRITICAL", "ERROR"]
                )
                validation_result["constraints_failed"] = sum(
                    1
                    for r in unified_validation_results
                    if r.severity.value in ["CRITICAL", "ERROR"]
                )
            else:
                validation_result["data_quality_score"] = legacy_passed / legacy_total
                validation_result["constraints_passed"] = legacy_passed
                validation_result["constraints_failed"] = legacy_total - legacy_passed

            return validation_result

        except Exception as e:
            validation_result["critical_violations"].append(
                f"Validation error: {str(e)}"
            )
            return validation_result

    def _find_strategy_in_csv(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Find strategy in statistical CSV by name or UUID, with enhanced name resolution"""
        try:
            if not self.statistical_csv.exists():
                return None

            df = pd.read_csv(self.statistical_csv)

            # Enhanced strategy name resolution
            # First, try to parse the identifier to extract components
            parsed_components = self._parse_strategy_identifier(identifier)

            # If the CSV has a strategy_name column, use enhanced matching logic
            if "strategy_name" in df.columns:
                # Try exact match first
                matches = df[df["strategy_name"] == identifier]
                if not matches.empty:
                    return matches.iloc[0].to_dict()

                # Try Position_UUID format parsing (e.g., TSLA_SMA_4_39_0_2025-06-11)
                if parsed_components:
                    ticker = parsed_components.get("ticker")
                    strategy_type = parsed_components.get("strategy_type")
                    short_window = parsed_components.get("short_window")
                    long_window = parsed_components.get("long_window")

                    if ticker and strategy_type and short_window and long_window:
                        # Look for matching strategy by components
                        expected_strategy_name = (
                            f"{strategy_type}_{short_window}_{long_window}"
                        )

                        # Match by strategy_name and ticker
                        matches = df[
                            (df["strategy_name"] == expected_strategy_name)
                            & (df["ticker"] == ticker)
                        ]
                        if not matches.empty:
                            logger.info(
                                f"Found strategy using component matching: {expected_strategy_name} for ticker {ticker}"
                            ) if self.logger else None
                            return matches.iloc[0].to_dict()

                        # Try partial matching with different patterns
                        for pattern in [
                            f"{strategy_type}_{short_window}_{long_window}",
                            f"{short_window}_{long_window}",
                            f"{strategy_type}_{short_window}",
                            f"{strategy_type}_{long_window}",
                        ]:
                            matches = df[
                                (
                                    df["strategy_name"].str.contains(
                                        pattern, case=False, na=False
                                    )
                                )
                                & (df["ticker"] == ticker)
                            ]
                            if not matches.empty:
                                logger.info(
                                    f"Found strategy using pattern matching: {pattern} for ticker {ticker}"
                                ) if self.logger else None
                                return matches.iloc[0].to_dict()

                        # Try ticker-only matching as fallback
                        matches = df[df["ticker"] == ticker]
                        if not matches.empty:
                            logger.info(
                                f"Found strategy using ticker-only matching: {ticker}"
                            ) if self.logger else None
                            return matches.iloc[0].to_dict()

                # Traditional matching strategies
                for column in ["strategy_name", "ticker"]:
                    if column in df.columns:
                        # Partial match (case insensitive)
                        matches = df[
                            df[column].str.contains(identifier, case=False, na=False)
                        ]
                        if not matches.empty:
                            return matches.iloc[0].to_dict()
            else:
                # Handle CSV files without strategy_name column
                # Generate strategy_name from available columns: ticker, strategy_type, short_window, long_window
                return self._find_strategy_by_constructed_name(df, identifier)

            return None

        except Exception as e:
            logger.error(f"Error finding strategy in CSV: {e}") if self.logger else None
            return None

    def _parse_strategy_identifier(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        Parse strategy identifier to extract components.

        Supports formats like:
        - TSLA_SMA_4_39_0_2025-06-11 (Position_UUID format)
        - AAPL_EMA_12_26_2025-07-10 (Position_UUID format)
        - SMA_20_50 (strategy_name format)
        """
        try:
            if not identifier or not isinstance(identifier, str):
                return None

            parts = identifier.split("_")

            # Handle Position_UUID format: TICKER_STRATEGY_SHORT_LONG_SIGNAL_DATE
            if len(parts) >= 4:
                ticker = parts[0]
                strategy_type = parts[1]

                # Try to extract numeric parameters
                try:
                    short_window = int(parts[2])
                    long_window = int(parts[3])

                    # Extract signal window and date if present
                    signal_window = None
                    entry_date = None

                    if len(parts) >= 5:
                        try:
                            signal_window = int(parts[4])
                        except ValueError:
                            pass

                    if len(parts) >= 6:
                        # Handle date format (might have hyphens)
                        date_part = "_".join(parts[5:])
                        # Look for date patterns like 2025-06-11
                        import re

                        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", date_part)
                        if date_match:
                            entry_date = date_match.group(1)

                    return {
                        "ticker": ticker,
                        "strategy_type": strategy_type,
                        "short_window": short_window,
                        "long_window": long_window,
                        "signal_window": signal_window,
                        "entry_date": entry_date,
                        "format": "position_uuid",
                    }
                except (ValueError, IndexError):
                    pass

            # Handle strategy_name format: SMA_20_50
            if len(parts) >= 3:
                strategy_type = parts[0]
                try:
                    short_window = int(parts[1])
                    long_window = int(parts[2])

                    return {
                        "strategy_type": strategy_type,
                        "short_window": short_window,
                        "long_window": long_window,
                        "format": "strategy_name",
                    }
                except (ValueError, IndexError):
                    pass

            # Handle simple ticker format
            if len(parts) == 1 and identifier.isalpha():
                return {"ticker": identifier, "format": "ticker_only"}

            return None

        except Exception as e:
            logger.warning(
                f"Error parsing strategy identifier '{identifier}': {e}"
            ) if self.logger else None
            return None

    def _find_strategy_by_constructed_name(
        self, df: pd.DataFrame, identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Find strategy in CSV by constructing strategy names from ticker, strategy_type, and window parameters"""
        try:
            # Required columns for constructing strategy name
            required_cols = ["ticker", "strategy_type", "short_window", "long_window"]

            # Check if we have the required columns
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logger.warning(
                    f"Cannot construct strategy names, missing columns: {missing_cols}"
                ) if self.logger else None
                return None

            # Add constructed strategy_name column to dataframe for searching
            df_with_strategy_name = df.copy()
            df_with_strategy_name["strategy_name"] = df_with_strategy_name.apply(
                lambda row: f"{row['ticker']}_{row['strategy_type']}_{int(row['short_window'])}_{int(row['long_window'])}",
                axis=1,
            )

            # Try to find the strategy using the constructed name
            # Exact match
            matches = df_with_strategy_name[
                df_with_strategy_name["strategy_name"] == identifier
            ]
            if not matches.empty:
                result = matches.iloc[0].to_dict()
                logger.info(
                    f"Found strategy using constructed name: {result['strategy_name']}"
                ) if self.logger else None
                return result

            # Partial match (case insensitive)
            matches = df_with_strategy_name[
                df_with_strategy_name["strategy_name"].str.contains(
                    identifier, case=False, na=False
                )
            ]
            if not matches.empty:
                result = matches.iloc[0].to_dict()
                logger.info(
                    f"Found strategy using partial constructed name match: {result['strategy_name']}"
                ) if self.logger else None
                return result

            # Try matching by ticker only as fallback
            matches = df_with_strategy_name[
                df_with_strategy_name["ticker"].str.contains(
                    identifier, case=False, na=False
                )
            ]
            if not matches.empty:
                result = matches.iloc[0].to_dict()
                logger.info(
                    f"Found strategy using ticker fallback: {result['strategy_name']}"
                ) if self.logger else None
                return result

            return None

        except Exception as e:
            logger.error(
                f"Error constructing strategy name for search: {e}"
            ) if self.logger else None
            return None

    def _generate_position_uuid(self, strategy_row: Dict[str, Any]) -> str:
        """Generate Position_UUID from strategy data"""
        try:
            strategy_name = strategy_row.get("strategy_name", "Unknown")
            ticker = strategy_row.get("ticker", "Unknown")
            timeframe = strategy_row.get("timeframe", "D")

            # Use current date for UUID generation
            current_date = datetime.now().strftime("%Y-%m-%d")
            return f"{strategy_name}_0_{current_date}"

        except Exception as e:
            logger.warning(
                f"Error generating position UUID: {e}"
            ) if self.logger else None
            return f"Unknown_0_{datetime.now().strftime('%Y-%m-%d')}"

    def _is_cache_valid(self, strategy_identifier: str) -> bool:
        """Check if cached data is still valid based on TTL"""
        if strategy_identifier not in self._cache_timestamps:
            return False

        cache_age = datetime.now() - self._cache_timestamps[strategy_identifier]
        return cache_age.total_seconds() < (self.config.cache_ttl_minutes * 60)

    def create_data_snapshot(self, strategy_identifiers: List[str]) -> str:
        """
        Create an immutable data snapshot for consistent multi-service operations.

        This ensures all services working on the same analysis use identical data.
        """
        try:
            with self._snapshot_lock:
                snapshot_id = f"snapshot_{int(time.time())}_{len(self._data_snapshots)}"

                snapshot_data = {}
                metadata = {}

                # Load all requested strategies into snapshot
                for identifier in strategy_identifiers:
                    strategy_data = self.get_strategy_data(
                        identifier, force_refresh=False
                    )
                    if strategy_data:
                        snapshot_data[identifier] = strategy_data

                        # Add metadata
                        metadata[identifier] = DataSourceMetadata(
                            source_type="coordinated",
                            file_path=str(self.statistical_csv),
                            last_modified=datetime.now(),
                            last_accessed=datetime.now(),
                            data_version="1.0",
                        )

                # Create snapshot
                snapshot = DataSnapshot(
                    snapshot_id=snapshot_id,
                    created_at=datetime.now(),
                    strategy_data=snapshot_data,
                    metadata=metadata,
                )

                self._data_snapshots[snapshot_id] = snapshot
                self._active_snapshots.add(snapshot_id)

                logger.info(
                    f"Created data snapshot {snapshot_id} with {len(snapshot_data)} strategies"
                ) if self.logger else None
                return snapshot_id

        except Exception as e:
            logger.error(f"Error creating data snapshot: {e}") if self.logger else None
            raise StrategyDataCoordinatorError(f"Failed to create data snapshot: {e}")

    def release_data_snapshot(self, snapshot_id: str):
        """Release a data snapshot to free memory"""
        try:
            with self._snapshot_lock:
                if snapshot_id in self._data_snapshots:
                    del self._data_snapshots[snapshot_id]
                    self._active_snapshots.discard(snapshot_id)
                    logger.info(
                        f"Released data snapshot {snapshot_id}"
                    ) if self.logger else None

        except Exception as e:
            logger.warning(
                f"Error releasing snapshot {snapshot_id}: {e}"
            ) if self.logger else None

    def refresh_all_data(self) -> Dict[str, Any]:
        """
        Refresh all cached data and return coordination report.

        This provides coordinated refresh across all data sources.
        """
        try:
            with self._refresh_lock:
                start_time = datetime.now()

                # Clear caches
                self._data_cache.clear()
                self._cache_timestamps.clear()

                # Get list of all strategies from statistical CSV
                if not self.statistical_csv.exists():
                    return {"error": "Statistical CSV not found"}

                df = pd.read_csv(self.statistical_csv)
                strategy_names = df["strategy_name"].unique().tolist()

                # Refresh data for all strategies
                refreshed = 0
                errors = []

                for strategy_name in strategy_names:
                    try:
                        strategy_data = self.get_strategy_data(
                            strategy_name, force_refresh=True
                        )
                        if strategy_data:
                            refreshed += 1
                    except Exception as e:
                        errors.append(f"{strategy_name}: {str(e)}")

                refresh_time = (datetime.now() - start_time).total_seconds()

                report = {
                    "timestamp": datetime.now().isoformat(),
                    "total_strategies": len(strategy_names),
                    "successfully_refreshed": refreshed,
                    "errors": errors,
                    "refresh_time_seconds": refresh_time,
                    "cache_hit_rate": 0.0,  # All fresh data
                    "active_snapshots": len(self._active_snapshots),
                }

                logger.info(
                    f"Refreshed {refreshed}/{len(strategy_names)} strategies in {refresh_time:.2f}s"
                ) if self.logger else None
                return report

        except Exception as e:
            logger.error(f"Error in refresh_all_data: {e}") if self.logger else None
            return {"error": str(e)}

    def get_coordination_status(self) -> Dict[str, Any]:
        """Get current status of the data coordination system"""
        try:
            return {
                "timestamp": datetime.now().isoformat(),
                "cached_strategies": len(self._data_cache),
                "active_snapshots": len(self._active_snapshots),
                "config": {
                    "validation_enabled": self.config.enable_validation,
                    "auto_refresh_enabled": self.config.enable_auto_refresh,
                    "max_data_age_minutes": self.config.max_data_age_minutes,
                    "memory_optimization_enabled": self.config.enable_memory_optimization,
                    "concurrent_loading": self.config.concurrent_loading,
                },
                "data_sources": {
                    "statistical_csv": self.statistical_csv.exists(),
                    "statistical_json": self.statistical_json.exists(),
                    "backtesting_json": self.backtesting_json.exists(),
                    "positions_csv": self.positions_csv.exists(),
                },
                "memory_optimizer_available": self.memory_optimizer is not None,
            }
        except Exception as e:
            return {"error": str(e)}

    def _log_strategy_not_found_with_suggestions(
        self, strategy_identifier: str
    ) -> None:
        """
        Log detailed error message with suggestions when strategy is not found.
        """
        try:
            # Use INFO level instead of WARNING since system has robust fallback mechanisms
            logger.info(
                f"Primary strategy data not found for {strategy_identifier} - checking fallback sources"
            ) if self.logger else None

            # Parse the identifier to provide specific suggestions
            parsed_components = self._parse_strategy_identifier(strategy_identifier)

            if parsed_components:
                if parsed_components.get("format") == "position_uuid":
                    # Position UUID format - suggest checking ticker and strategy availability
                    ticker = parsed_components.get("ticker")
                    strategy_type = parsed_components.get("strategy_type")
                    short_window = parsed_components.get("short_window")
                    long_window = parsed_components.get("long_window")

                    logger.info(
                        f"Parsed Position_UUID format: ticker={ticker}, strategy_type={strategy_type}, "
                        f"short_window={short_window}, long_window={long_window}"
                    ) if self.logger else None

                    # Check if ticker exists in CSV
                    if ticker and self.statistical_csv.exists():
                        try:
                            df = pd.read_csv(self.statistical_csv)
                            if "ticker" in df.columns:
                                ticker_strategies = df[df["ticker"] == ticker]
                                if ticker_strategies.empty:
                                    logger.info(
                                        f"No strategies found for ticker {ticker} in statistical analysis data - using fallback analysis"
                                    ) if self.logger else None
                                else:
                                    # Show available strategies for this ticker
                                    available_strategies = ticker_strategies[
                                        "strategy_name"
                                    ].tolist()
                                    logger.info(
                                        f"Available strategies for {ticker}: {', '.join(available_strategies)}"
                                    ) if self.logger else None

                                    # Suggest closest match
                                    expected_strategy = (
                                        f"{strategy_type}_{short_window}_{long_window}"
                                    )
                                    closest_match = self._find_closest_strategy_match(
                                        expected_strategy, available_strategies
                                    )
                                    if closest_match:
                                        logger.info(
                                            f"Closest match for {ticker}: {closest_match}"
                                        ) if self.logger else None
                        except Exception as e:
                            logger.warning(
                                f"Error checking ticker availability: {e}"
                            ) if self.logger else None

                elif parsed_components.get("format") == "strategy_name":
                    # Strategy name format - suggest checking available strategies
                    strategy_type = parsed_components.get("strategy_type")
                    short_window = parsed_components.get("short_window")
                    long_window = parsed_components.get("long_window")

                    logger.info(
                        f"Parsed strategy_name format: strategy_type={strategy_type}, "
                        f"short_window={short_window}, long_window={long_window}"
                    ) if self.logger else None

                    # Show available strategies
                    self._show_available_strategies(limit=10)

            else:
                logger.info(
                    f"Could not parse strategy identifier: {strategy_identifier}"
                ) if self.logger else None
                self._show_available_strategies(limit=10)

        except Exception as e:
            logger.error(
                f"Error in strategy not found reporting: {e}"
            ) if self.logger else None

    def _find_closest_strategy_match(
        self, target_strategy: str, available_strategies: List[str]
    ) -> Optional[str]:
        """
        Find the closest matching strategy name using simple similarity.
        """
        try:
            if not available_strategies:
                return None

            # Simple similarity based on common characters
            best_match = None
            best_score = 0

            for strategy in available_strategies:
                # Count common characters
                common_chars = sum(
                    1 for a, b in zip(target_strategy, strategy) if a == b
                )
                score = common_chars / max(len(target_strategy), len(strategy))

                if score > best_score:
                    best_score = score
                    best_match = strategy

            # Only return if similarity is reasonably high
            if best_score > 0.5:
                return best_match

            return None

        except Exception as e:
            logger.warning(
                f"Error finding closest strategy match: {e}"
            ) if self.logger else None
            return None

    def _show_available_strategies(self, limit: int = 10) -> None:
        """
        Show available strategies for troubleshooting.
        """
        try:
            if not self.statistical_csv.exists():
                logger.warning(
                    "Statistical CSV file not found"
                ) if self.logger else None
                return

            df = pd.read_csv(self.statistical_csv)

            if "strategy_name" in df.columns:
                available_strategies = df["strategy_name"].unique()[:limit]
                logger.info(
                    f"Available strategies: {', '.join(available_strategies)}"
                ) if self.logger else None

                if len(df) > limit:
                    logger.info(
                        f"... and {len(df) - limit} more strategies"
                    ) if self.logger else None
            else:
                logger.info(
                    "No strategy_name column found in statistical CSV"
                ) if self.logger else None

        except Exception as e:
            logger.warning(
                f"Error showing available strategies: {e}"
            ) if self.logger else None

    def diagnose_strategy_data_issue(self, strategy_identifier: str) -> Dict[str, Any]:
        """
        Comprehensive diagnostic tool for strategy data issues.

        Returns detailed analysis and suggestions for resolving strategy data problems.
        """
        try:
            diagnosis = {
                "strategy_identifier": strategy_identifier,
                "timestamp": datetime.now().isoformat(),
                "status": "unknown",
                "found_in_sources": {},
                "parsing_results": {},
                "suggestions": [],
                "available_alternatives": [],
                "data_integrity_issues": [],
            }

            # Step 1: Parse the identifier
            parsed_components = self._parse_strategy_identifier(strategy_identifier)
            if parsed_components:
                diagnosis["parsing_results"] = parsed_components
                diagnosis["status"] = "parsed_successfully"
            else:
                diagnosis["status"] = "parsing_failed"
                diagnosis["suggestions"].append(
                    "Strategy identifier format not recognized"
                )
                return diagnosis

            # Step 2: Check availability in different data sources
            diagnosis["found_in_sources"] = self._check_strategy_in_all_sources(
                strategy_identifier, parsed_components
            )

            # Step 3: Generate specific suggestions based on findings
            diagnosis["suggestions"] = self._generate_diagnostic_suggestions(
                parsed_components, diagnosis["found_in_sources"]
            )

            # Step 4: Find alternative strategies
            diagnosis["available_alternatives"] = self._find_alternative_strategies(
                parsed_components
            )

            # Step 5: Check data integrity
            diagnosis["data_integrity_issues"] = self._check_data_integrity_issues()

            # Step 6: Overall assessment
            if any(diagnosis["found_in_sources"].values()):
                diagnosis["status"] = "partially_found"
            else:
                diagnosis["status"] = "not_found"

            return diagnosis

        except Exception as e:
            return {
                "strategy_identifier": strategy_identifier,
                "status": "diagnostic_error",
                "error": str(e),
                "suggestions": ["Unable to complete diagnostic - check system logs"],
            }

    def _check_strategy_in_all_sources(
        self, strategy_identifier: str, parsed_components: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Check if strategy exists in all data sources.
        """
        sources = {
            "statistical_csv": False,
            "statistical_json": False,
            "backtesting_json": False,
            "backtesting_csv": False,
            "positions_csv": False,
        }

        try:
            # Check statistical CSV
            if self.statistical_csv.exists():
                strategy_row = self._find_strategy_in_csv(strategy_identifier)
                sources["statistical_csv"] = strategy_row is not None

            # Check positions CSV
            if self.positions_csv.exists():
                df = pd.read_csv(self.positions_csv)
                if "Position_UUID" in df.columns:
                    sources["positions_csv"] = (
                        strategy_identifier in df["Position_UUID"].values
                    )

            # Check statistical JSON
            if self.statistical_json.exists():
                with open(self.statistical_json, "r") as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    sources["statistical_json"] = any(
                        result.get("strategy_name") == strategy_identifier
                        for result in results
                    )

            # Check backtesting JSON
            if self.backtesting_json.exists():
                with open(self.backtesting_json, "r") as f:
                    data = json.load(f)
                    results = data.get("results", [])
                    sources["backtesting_json"] = any(
                        result.get("strategy_name") == strategy_identifier
                        for result in results
                    )

            # Check backtesting CSV
            if self.backtesting_csv.exists():
                df = pd.read_csv(self.backtesting_csv)
                if "strategy_name" in df.columns:
                    sources["backtesting_csv"] = (
                        strategy_identifier in df["strategy_name"].values
                    )

        except Exception as e:
            logger.warning(f"Error checking sources: {e}") if self.logger else None

        return sources

    def _generate_diagnostic_suggestions(
        self, parsed_components: Dict[str, Any], sources: Dict[str, bool]
    ) -> List[str]:
        """
        Generate specific suggestions based on diagnostic results.
        """
        suggestions = []

        # Check if position exists but strategy data doesn't
        if sources.get("positions_csv") and not sources.get("statistical_csv"):
            suggestions.append(
                "Position exists but no statistical analysis data found - run SPDS analysis for this strategy"
            )

        # Check if it's a ticker issue
        if parsed_components.get("format") == "position_uuid":
            ticker = parsed_components.get("ticker")
            if ticker and not sources.get("statistical_csv"):
                suggestions.append(
                    f"No statistical data found for ticker {ticker} - check if ticker is included in analysis"
                )

        # Check for partial data
        if sources.get("statistical_csv") and not sources.get("statistical_json"):
            suggestions.append(
                "Strategy found in CSV but not JSON - check statistical analysis export process"
            )

        # Check if no data found anywhere
        if not any(sources.values()):
            suggestions.append(
                "Strategy not found in any data source - check strategy name format and availability"
            )

            if parsed_components.get("format") == "position_uuid":
                ticker = parsed_components.get("ticker")
                strategy_type = parsed_components.get("strategy_type")
                short_window = parsed_components.get("short_window")
                long_window = parsed_components.get("long_window")

                suggestions.append(
                    f"Try searching for: {strategy_type}_{short_window}_{long_window} with ticker {ticker}"
                )

        return suggestions

    def _find_alternative_strategies(
        self, parsed_components: Dict[str, Any]
    ) -> List[str]:
        """
        Find alternative strategies that might be what the user is looking for.
        """
        alternatives = []

        try:
            if not self.statistical_csv.exists():
                return alternatives

            df = pd.read_csv(self.statistical_csv)

            if parsed_components.get("format") == "position_uuid":
                ticker = parsed_components.get("ticker")
                strategy_type = parsed_components.get("strategy_type")

                # Find strategies for same ticker
                if ticker and "ticker" in df.columns:
                    ticker_strategies = df[df["ticker"] == ticker]
                    if not ticker_strategies.empty:
                        alternatives.extend(
                            ticker_strategies["strategy_name"].tolist()[:5]
                        )

                # Find strategies of same type
                if strategy_type and "strategy_name" in df.columns:
                    type_strategies = df[
                        df["strategy_name"].str.contains(
                            strategy_type, case=False, na=False
                        )
                    ]
                    if not type_strategies.empty:
                        alternatives.extend(
                            type_strategies["strategy_name"].tolist()[:5]
                        )

        except Exception as e:
            logger.warning(f"Error finding alternatives: {e}") if self.logger else None

        return list(set(alternatives))  # Remove duplicates

    def _safe_float_conversion(self, value: Any, default: float = 0.0) -> float:
        """
        Safely convert a value to float, handling NaN, None, and invalid values.

        Args:
            value: Value to convert to float
            default: Default value to return if conversion fails

        Returns:
            Valid float value, never NaN or inf
        """
        try:
            if value is None:
                return default

            float_val = float(value)

            # Check for NaN or infinite values
            if np.isnan(float_val) or np.isinf(float_val):
                return default

            return float_val
        except (ValueError, TypeError, OverflowError):
            return default

    def _check_data_integrity_issues(self) -> List[str]:
        """
        Check for common data integrity issues.
        """
        issues = []

        try:
            # Check if required files exist
            required_files = [
                ("statistical_csv", self.statistical_csv),
                ("statistical_json", self.statistical_json),
                ("positions_csv", self.positions_csv),
            ]

            for name, file_path in required_files:
                if not file_path.exists():
                    issues.append(f"Missing required file: {file_path}")
                elif file_path.stat().st_size == 0:
                    issues.append(f"Empty file: {file_path}")

            # Check CSV column integrity
            if self.statistical_csv.exists():
                df = pd.read_csv(self.statistical_csv)
                required_columns = ["strategy_name", "ticker", "timeframe"]
                missing_columns = [
                    col for col in required_columns if col not in df.columns
                ]
                if missing_columns:
                    issues.append(
                        f"Missing columns in statistical CSV: {missing_columns}"
                    )

        except Exception as e:
            issues.append(f"Error checking data integrity: {e}")

        return issues
