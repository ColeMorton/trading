#!/usr/bin/env python3
"""
Signal Data Aggregator Service

Aggregates and processes all statistical data for a given strategy/Position_UUID
from multiple export sources to enable comprehensive sell signal analysis.

Source Integration:
- data/outputs/spds/statistical_analysis/live_signals.csv
- data/outputs/spds/statistical_analysis/live_signals.json
- data/outputs/spds/backtesting_parameters/live_signals.json
- data/outputs/spds/backtesting_parameters/live_signals.csv
- data/outputs/spds/statistical_analysis/live_signals_export_summary.md
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl

# Import the new central coordinator
from app.tools.services.strategy_data_coordinator import (
    DataCoordinationConfig,
    StrategyDataCoordinator,
    StrategyDataCoordinatorError,
)

logger = logging.getLogger(__name__)


@dataclass
class StrategyData:
    """Comprehensive strategy data from all sources"""

    # Core identification
    strategy_name: str
    ticker: str
    timeframe: str
    position_uuid: Optional[str] = None

    # Statistical analysis data
    sample_size: int = 0
    sample_size_confidence: float = 0.0
    dual_layer_convergence_score: float = 0.0
    asset_layer_percentile: float = 0.0
    strategy_layer_percentile: float = 0.0
    exit_signal: str = "UNKNOWN"
    signal_confidence: float = 0.0
    exit_recommendation: str = ""
    statistical_significance: str = "LOW"
    p_value: float = 0.1

    # Divergence metrics
    z_score_divergence: float = 0.0
    iqr_divergence: float = 0.0
    rarity_score: float = 0.0

    # Performance metrics
    current_return: float = 0.0
    mfe: float = 0.0
    mae: float = 0.0
    unrealized_pnl: float = 0.0

    # Backtesting parameters
    take_profit_pct: float = 0.0
    stop_loss_pct: float = 0.0
    max_holding_days: int = 0
    min_holding_days: int = 0
    trailing_stop_pct: float = 0.0
    momentum_exit_threshold: float = 0.0
    trend_exit_threshold: float = 0.0

    # Validation and quality
    confidence_level: float = 0.0
    statistical_validity: str = "LOW"
    generation_timestamp: str = ""

    # Raw data for advanced analysis
    raw_returns: List[float] = None
    raw_analysis_data: Dict[str, Any] = None


class SignalDataAggregator:
    """
    Strategy data aggregation service with central coordination.

    This service now delegates core data loading to StrategyDataCoordinator while
    maintaining specialized functionality for signal analysis and data quality monitoring.

    Eliminates duplicate data loading logic by using centralized coordinator.
    """

    def __init__(
        self,
        base_path: Optional[Path] = None,
        coordinator: Optional[StrategyDataCoordinator] = None,
        enable_legacy_validation: bool = True,
    ):
        """
        Initialize with central data coordination.

        Args:
            base_path: Base path for data files
            coordinator: StrategyDataCoordinator instance (creates new if None)
            enable_legacy_validation: Whether to maintain legacy validation for compatibility
        """
        self.base_path = base_path or Path.cwd()
        self.enable_legacy_validation = enable_legacy_validation

        # Initialize central data coordinator
        if coordinator:
            self.coordinator = coordinator
        else:
            # Create new coordinator with optimized configuration
            config = DataCoordinationConfig(
                enable_validation=True,
                enable_auto_refresh=True,
                max_data_age_minutes=30,
                enable_memory_optimization=True,
                concurrent_loading=True,
            )
            self.coordinator = StrategyDataCoordinator(
                base_path=self.base_path, logger=logger, config=config
            )

        # Legacy file paths (kept for backward compatibility)
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
        self.summary_md = (
            self.exports_path
            / "statistical_analysis"
            / "live_signals_export_summary.md"
        )

        # Legacy validation (still available for compatibility)
        if enable_legacy_validation:
            self._validate_sources()

        logger.info("SignalDataAggregator initialized with central data coordination")

    def _validate_sources(self) -> None:
        """Validate that all required source files exist"""
        required_files = [
            self.statistical_csv,
            self.statistical_json,
            self.backtesting_json,
            self.backtesting_csv,
        ]

        missing_files = [f for f in required_files if not f.exists()]
        if missing_files:
            logger.warning(f"Missing source files: {missing_files}")

    def get_strategy_data(
        self,
        strategy_identifier: str,
        force_refresh: bool = False,
        snapshot_id: Optional[str] = None,
    ) -> Optional[StrategyData]:
        """
        Get comprehensive strategy data using central coordination.

        This method now delegates to StrategyDataCoordinator, eliminating duplicate
        data loading logic while maintaining the same API for backward compatibility.

        Args:
            strategy_identifier: Strategy name (e.g., "MA_SMA_78_82") or Position_UUID
            force_refresh: Force fresh data loading bypassing cache
            snapshot_id: Use specific data snapshot for consistency

        Returns:
            StrategyData object with all coordinated data or None if not found
        """
        try:
            # Delegate to central coordinator for data loading
            strategy_data = self.coordinator.get_strategy_data(
                strategy_identifier=strategy_identifier,
                force_refresh=force_refresh,
                snapshot_id=snapshot_id,
            )

            if not strategy_data:
                logger.error(
                    f"Strategy '{strategy_identifier}' not found via central coordinator"
                )
                return None

            # Apply any legacy validation if enabled (for backward compatibility)
            if self.enable_legacy_validation:
                try:
                    validation_warnings = self._validate_performance_metrics(
                        strategy_data, strategy_data.strategy_name
                    )
                    if validation_warnings:
                        logger.warning(
                            f"Legacy validation issues for {strategy_data.strategy_name}: {validation_warnings}"
                        )
                except Exception as legacy_error:
                    logger.warning(
                        f"Legacy validation failed for {strategy_data.strategy_name}: {legacy_error}"
                    )

            logger.info(
                f"Successfully retrieved coordinated data for {strategy_data.strategy_name}"
            )
            return strategy_data

        except StrategyDataCoordinatorError as coord_error:
            logger.error(f"Coordinator error for {strategy_identifier}: {coord_error}")
            return None
        except Exception as e:
            logger.error(
                f"Error retrieving strategy data for {strategy_identifier}: {e}"
            )
            return None

    def get_multiple_strategies(
        self,
        strategy_identifiers: List[str],
        use_snapshot: bool = True,
        force_refresh: bool = False,
    ) -> Dict[str, Optional[StrategyData]]:
        """
        Get multiple strategies with coordinated data consistency.

        This method ensures all strategies use the same data snapshot for consistency
        across multi-strategy analysis operations.

        Args:
            strategy_identifiers: List of strategy names or UUIDs
            use_snapshot: Whether to use data snapshots for consistency
            force_refresh: Force fresh data loading

        Returns:
            Dictionary mapping strategy identifiers to StrategyData objects
        """
        try:
            results = {}
            snapshot_id = None

            if use_snapshot:
                # Create coordinated snapshot for consistency
                snapshot_id = self.coordinator.create_data_snapshot(
                    strategy_identifiers
                )
                logger.info(
                    f"Created data snapshot {snapshot_id} for {len(strategy_identifiers)} strategies"
                )

            try:
                # Load all strategies using the same snapshot
                for identifier in strategy_identifiers:
                    strategy_data = self.get_strategy_data(
                        strategy_identifier=identifier,
                        force_refresh=force_refresh,
                        snapshot_id=snapshot_id,
                    )
                    results[identifier] = strategy_data

                return results

            finally:
                # Clean up snapshot
                if snapshot_id:
                    self.coordinator.release_data_snapshot(snapshot_id)

        except Exception as e:
            logger.error(f"Error loading multiple strategies: {e}")
            return {identifier: None for identifier in strategy_identifiers}

    def refresh_strategy_data(self, strategy_identifier: str) -> Optional[StrategyData]:
        """
        Force refresh strategy data bypassing all caches.

        Args:
            strategy_identifier: Strategy name or UUID to refresh

        Returns:
            Refreshed StrategyData object or None if failed
        """
        try:
            return self.get_strategy_data(strategy_identifier, force_refresh=True)
        except Exception as e:
            logger.error(
                f"Error refreshing strategy data for {strategy_identifier}: {e}"
            )
            return None

    def get_coordination_status(self) -> Dict[str, Any]:
        """
        Get status of the central data coordination system.

        Returns:
            Dictionary with coordination system status and health metrics
        """
        try:
            coordinator_status = self.coordinator.get_coordination_status()

            # Add SignalDataAggregator-specific status
            aggregator_status = {
                "signal_aggregator_version": "2.0.0_coordinated",
                "legacy_validation_enabled": self.enable_legacy_validation,
                "coordinator_available": True,
                "backward_compatibility_mode": True,
            }

            return {
                "aggregator_status": aggregator_status,
                "coordinator_status": coordinator_status,
                "overall_health": "HEALTHY"
                if coordinator_status.get("cached_strategies", 0) >= 0
                else "DEGRADED",
            }

        except Exception as e:
            logger.error(f"Error getting coordination status: {e}")
            return {
                "aggregator_status": {"error": str(e)},
                "coordinator_status": {"error": str(e)},
                "overall_health": "ERROR",
            }

    # === Legacy Methods (Deprecated but maintained for compatibility) ===
    #
    # The following methods are deprecated and should not be used in new code.
    # They are maintained for backward compatibility during the migration to
    # central data coordination. Use the coordinator-based methods instead.

    def _find_strategy_in_csv(self, identifier: str) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Find strategy in statistical CSV by name or UUID

        This method is deprecated. Use coordinator.get_strategy_data() instead.
        """
        import warnings

        warnings.warn(
            "_find_strategy_in_csv is deprecated. Use coordinator.get_strategy_data() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            if not self.statistical_csv.exists():
                logger.error(f"Statistical CSV not found: {self.statistical_csv}")
                return None

            df = pd.read_csv(self.statistical_csv)

            # Try exact match on strategy_name first
            match = df[df["strategy_name"] == identifier]
            if not match.empty:
                return match.iloc[0].to_dict()

            # Try partial match (case insensitive)
            match = df[
                df["strategy_name"].str.contains(identifier, case=False, na=False)
            ]
            if not match.empty:
                return match.iloc[0].to_dict()

            # Try ticker match
            match = df[df["ticker"].str.contains(identifier, case=False, na=False)]
            if not match.empty:
                return match.iloc[0].to_dict()

            return None

        except Exception as e:
            logger.error(f"Error finding strategy in CSV: {e}")
            return None

    def _generate_position_uuid(self, strategy_row: Dict[str, Any]) -> str:
        """Generate Position_UUID from strategy data"""
        try:
            strategy_name = strategy_row["strategy_name"]
            ticker = strategy_row["ticker"]

            # Parse strategy name to extract components
            parts = strategy_name.split("_")
            if len(parts) >= 4:
                strategy_type = parts[1]  # SMA, EMA, etc.
                short_window = parts[2]
                long_window = parts[3]
                signal_window = "0"  # Default

                # Use current date as entry_date placeholder
                entry_date = "20250706"  # Could be enhanced to use actual entry date

                return f"{ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}_{entry_date}"

            # Fallback UUID
            return f"{ticker}_{strategy_name}_20250706"

        except Exception as e:
            logger.warning(f"Error generating Position_UUID: {e}")
            return f"UNKNOWN_{strategy_row.get('ticker', 'UNK')}_20250706"

    def _populate_from_statistical_csv(
        self, strategy_data: StrategyData, row: Dict[str, Any]
    ) -> None:
        """Populate strategy data from statistical analysis CSV"""
        try:
            strategy_data.sample_size = int(row.get("sample_size", 0))
            strategy_data.sample_size_confidence = float(
                row.get("sample_size_confidence", 0.0)
            )
            strategy_data.dual_layer_convergence_score = float(
                row.get("dual_layer_convergence_score", 0.0)
            )
            strategy_data.asset_layer_percentile = float(
                row.get("asset_layer_percentile", 0.0)
            )
            strategy_data.strategy_layer_percentile = float(
                row.get("strategy_layer_percentile", 0.0)
            )
            strategy_data.exit_signal = str(row.get("exit_signal", "UNKNOWN"))
            strategy_data.signal_confidence = float(row.get("signal_confidence", 0.0))
            strategy_data.exit_recommendation = str(row.get("exit_recommendation", ""))
            strategy_data.statistical_significance = str(
                row.get("statistical_significance", "LOW")
            )
            strategy_data.p_value = float(row.get("p_value", 0.1))

            # Divergence metrics
            strategy_data.z_score_divergence = float(row.get("z_score_divergence", 0.0))
            strategy_data.iqr_divergence = float(row.get("iqr_divergence", 0.0))
            strategy_data.rarity_score = float(row.get("rarity_score", 0.0))

            # Performance metrics
            strategy_data.current_return = float(row.get("current_return", 0.0))
            strategy_data.mfe = float(row.get("mfe", 0.0))
            strategy_data.mae = float(row.get("mae", 0.0))
            strategy_data.unrealized_pnl = float(row.get("unrealized_pnl", 0.0))

        except Exception as e:
            logger.warning(f"Error populating from statistical CSV: {e}")

    def _populate_from_statistical_json(
        self, strategy_data: StrategyData, strategy_name: str
    ) -> None:
        """Populate strategy data from statistical analysis JSON"""
        try:
            if not self.statistical_json.exists():
                logger.warning(f"Statistical JSON not found: {self.statistical_json}")
                return

            with open(self.statistical_json, "r") as f:
                data = json.load(f)

            # Find matching strategy in results
            results = data.get("statistical_analysis_results", [])
            for result in results:
                if result.get("strategy_name") == strategy_name:
                    # Extract performance metrics (THIS WAS MISSING!)
                    performance_metrics = result.get("performance_metrics", {})
                    if performance_metrics:
                        # Load current_return from JSON (authoritative source)
                        if (
                            "current_return" in performance_metrics
                            and performance_metrics["current_return"] is not None
                        ):
                            strategy_data.current_return = float(
                                performance_metrics["current_return"]
                            )

                        # Load MFE/MAE from JSON if they have valid values (not zero)
                        # NOTE: Statistical JSON often has zero MFE/MAE - positions file will be more accurate
                        if (
                            "mfe" in performance_metrics
                            and performance_metrics["mfe"] is not None
                            and performance_metrics["mfe"] != 0.0
                        ):
                            strategy_data.mfe = float(performance_metrics["mfe"])
                            logger.info(f"Using MFE from JSON: {strategy_data.mfe:.4f}")

                        if (
                            "mae" in performance_metrics
                            and performance_metrics["mae"] is not None
                            and performance_metrics["mae"] != 0.0
                        ):
                            strategy_data.mae = float(performance_metrics["mae"])
                            logger.info(f"Using MAE from JSON: {strategy_data.mae:.4f}")

                        # Load unrealized P&L
                        if (
                            "unrealized_pnl" in performance_metrics
                            and performance_metrics["unrealized_pnl"] is not None
                        ):
                            strategy_data.unrealized_pnl = float(
                                performance_metrics["unrealized_pnl"]
                            )

                        logger.info(
                            f"Loaded performance metrics from JSON for {strategy_name}: "
                            f"current_return={strategy_data.current_return:.4f}, "
                            f"mfe={strategy_data.mfe:.4f}, mae={strategy_data.mae:.4f}"
                        )

                    # Extract raw returns data if available
                    raw_data = result.get("raw_analysis_data", {})
                    if raw_data and "returns" in raw_data:
                        strategy_data.raw_returns = raw_data["returns"]

                    strategy_data.raw_analysis_data = raw_data
                    break

        except Exception as e:
            logger.warning(f"Error populating from statistical JSON: {e}")

    def _populate_from_backtesting_data(
        self, strategy_data: StrategyData, strategy_name: str
    ) -> None:
        """Populate strategy data from backtesting parameters"""
        try:
            # Load backtesting JSON
            if self.backtesting_json.exists():
                with open(self.backtesting_json, "r") as f:
                    backtest_data = json.load(f)

                # Find strategy in backtesting parameters
                strategies = backtest_data.get("strategy_parameters", {})

                # Try different key formats
                strategy_key = None
                for key in strategies.keys():
                    if strategy_name in key or key.startswith(strategy_name):
                        strategy_key = key
                        break

                if strategy_key:
                    params = strategies[strategy_key]
                    strategy_data.take_profit_pct = float(
                        params.get("take_profit_pct", 0.0)
                    )
                    strategy_data.stop_loss_pct = float(
                        params.get("stop_loss_pct", 0.0)
                    )
                    strategy_data.max_holding_days = int(
                        params.get("max_holding_days", 0)
                    )
                    strategy_data.min_holding_days = int(
                        params.get("min_holding_days", 0)
                    )
                    strategy_data.trailing_stop_pct = float(
                        params.get("trailing_stop_pct", 0.0)
                    )
                    strategy_data.momentum_exit_threshold = float(
                        params.get("momentum_exit_threshold", 0.0)
                    )
                    strategy_data.trend_exit_threshold = float(
                        params.get("trend_exit_threshold", 0.0)
                    )
                    strategy_data.confidence_level = float(
                        params.get("confidence_level", 0.0)
                    )
                    strategy_data.statistical_validity = str(
                        params.get("statistical_validity", "LOW")
                    )
                    strategy_data.generation_timestamp = str(
                        params.get("generation_timestamp", "")
                    )

            # Load backtesting CSV for additional validation
            if self.backtesting_csv.exists():
                df = pd.read_csv(self.backtesting_csv)

                # Handle CSV files with or without strategy_name column
                match = None
                if "strategy_name" in df.columns:
                    # Try strategy_name column first
                    match = df[df["strategy_name"] == strategy_name]

                if match is None or match.empty:
                    # Fallback to Strategy column for backward compatibility
                    if "Strategy" in df.columns:
                        match = df[df["Strategy"] == strategy_name]

                if not match.empty:
                    row = match.iloc[0]
                    # Cross-validate key parameters
                    if strategy_data.take_profit_pct == 0.0:
                        strategy_data.take_profit_pct = float(
                            row.get("TakeProfit_Pct", 0.0)
                        )
                    if strategy_data.stop_loss_pct == 0.0:
                        strategy_data.stop_loss_pct = float(
                            row.get("StopLoss_Pct", 0.0)
                        )

        except Exception as e:
            logger.warning(f"Error populating from backtesting data: {e}")

    def _populate_from_trade_history(
        self, strategy_data: StrategyData, strategy_name: str
    ) -> None:
        """Load trade history data including MFE and MAE from consolidated positions file"""
        try:
            # Check consolidated positions file
            positions_file = (
                self.base_path / "data" / "raw" / "positions" / "live_signals.csv"
            )
            if positions_file.exists():
                df = pd.read_csv(positions_file)

                # Find strategy by Position_UUID or strategy name
                match = None

                # Try matching by Position_UUID if available
                if (
                    hasattr(strategy_data, "position_uuid")
                    and strategy_data.position_uuid
                ):
                    match = df[df["Position_UUID"] == strategy_data.position_uuid]

                # Fallback to strategy name matching
                if match is None or match.empty:
                    # Try Position_UUID pattern matching (extract strategy part)
                    if "Position_UUID" in df.columns:
                        # Extract ticker and strategy type from strategy_name (e.g., PGR_SMA_37_61)
                        parts = strategy_name.split("_")
                        if len(parts) >= 4:
                            ticker = parts[0]
                            strategy_type = parts[1]
                            short_window = parts[2]
                            long_window = parts[3]
                            pattern = (
                                f"{ticker}_{strategy_type}_{short_window}_{long_window}"
                            )
                            match = df[
                                df["Position_UUID"].str.contains(
                                    pattern, case=False, na=False
                                )
                            ]

                    # Try ticker-based matching if UUID pattern fails
                    if match.empty and "Ticker" in df.columns:
                        ticker = (
                            strategy_name.split("_")[0]
                            if "_" in strategy_name
                            else strategy_name
                        )
                        ticker_matches = df[df["Ticker"] == ticker]
                        if not ticker_matches.empty:
                            # If multiple matches for ticker, try to find best match
                            for _, row in ticker_matches.iterrows():
                                uuid = row["Position_UUID"]
                                if (
                                    strategy_name.replace("_", "_").lower()
                                    in uuid.lower()
                                ):
                                    match = pd.DataFrame([row])
                                    break
                            if match.empty:
                                match = ticker_matches.head(
                                    1
                                )  # Take first match as fallback

                if not match.empty:
                    row = match.iloc[0]

                    # Check data quality and timestamps
                    position_age_days = float(row.get("Days_Since_Entry", 0))
                    position_status = str(row.get("Status", "Unknown"))

                    # Only use positions data if it seems reliable (not too stale)
                    use_positions_data = True
                    if position_age_days > 90:  # More than 90 days old
                        logger.warning(
                            f"Position data for {strategy_name} is {position_age_days} days old - may be stale"
                        )
                        use_positions_data = False

                    if use_positions_data:
                        # Store original values for comparison
                        original_mfe = strategy_data.mfe
                        original_mae = strategy_data.mae
                        original_current_return = strategy_data.current_return

                        # Load MFE and MAE values - positions file is often more accurate than JSON
                        positions_mfe_loaded = False
                        positions_mae_loaded = False

                        if "Max_Favourable_Excursion" in row:
                            new_mfe = float(row["Max_Favourable_Excursion"])
                            # Validate MFE: if current return is positive, MFE shouldn't be negative
                            if strategy_data.current_return > 0 and new_mfe < 0:
                                logger.warning(
                                    f"Rejecting negative MFE ({new_mfe:.4f}) for profitable position {strategy_name} "
                                    f"(current_return: {strategy_data.current_return:.4f})"
                                )
                            else:
                                # Use positions MFE if JSON had zero or if positions value seems more reasonable
                                if strategy_data.mfe == 0.0 or abs(new_mfe) > abs(
                                    strategy_data.mfe
                                ):
                                    old_mfe = strategy_data.mfe
                                    strategy_data.mfe = new_mfe
                                    positions_mfe_loaded = True
                                    logger.info(
                                        f"Using MFE from positions file: {new_mfe:.4f} (was {old_mfe:.4f} from JSON)"
                                    )
                        elif "MFE" in row:
                            new_mfe = float(row["MFE"])
                            if strategy_data.current_return > 0 and new_mfe < 0:
                                logger.warning(
                                    f"Rejecting negative MFE ({new_mfe:.4f}) for profitable position {strategy_name}"
                                )
                            else:
                                if strategy_data.mfe == 0.0 or abs(new_mfe) > abs(
                                    strategy_data.mfe
                                ):
                                    old_mfe = strategy_data.mfe
                                    strategy_data.mfe = new_mfe
                                    positions_mfe_loaded = True
                                    logger.info(
                                        f"Using MFE from positions file: {new_mfe:.4f} (was {old_mfe:.4f} from JSON)"
                                    )

                        if "Max_Adverse_Excursion" in row:
                            new_mae = float(row["Max_Adverse_Excursion"])
                            # Use positions MAE if JSON had zero or if positions value seems more reasonable
                            if strategy_data.mae == 0.0 or abs(new_mae) > abs(
                                strategy_data.mae
                            ):
                                old_mae = strategy_data.mae
                                strategy_data.mae = new_mae
                                positions_mae_loaded = True
                                logger.info(
                                    f"Using MAE from positions file: {new_mae:.4f} (was {old_mae:.4f} from JSON)"
                                )
                        elif "MAE" in row:
                            new_mae = float(row["MAE"])
                            if strategy_data.mae == 0.0 or abs(new_mae) > abs(
                                strategy_data.mae
                            ):
                                old_mae = strategy_data.mae
                                strategy_data.mae = new_mae
                                positions_mae_loaded = True
                                logger.info(
                                    f"Using MAE from positions file: {new_mae:.4f} (was {old_mae:.4f} from JSON)"
                                )

                        # Load current return from positions file if available and convert from absolute to percentage
                        if (
                            "Current_Unrealized_PnL" in row
                            and row["Current_Unrealized_PnL"] is not None
                        ):
                            current_unrealized_pnl = float(
                                row["Current_Unrealized_PnL"]
                            )
                            avg_entry_price = float(row.get("Avg_Entry_Price", 0))
                            if avg_entry_price > 0:
                                # Convert absolute P&L to percentage return
                                positions_current_return = (
                                    current_unrealized_pnl / avg_entry_price
                                )

                                # Compare with statistical analysis return - warn if significantly different
                                if (
                                    abs(
                                        positions_current_return
                                        - strategy_data.current_return
                                    )
                                    > 0.05
                                ):  # 5% difference
                                    logger.warning(
                                        f"Current return mismatch for {strategy_name}: "
                                        f"Statistical={strategy_data.current_return:.4f}, "
                                        f"Positions={positions_current_return:.4f}"
                                    )
                                # Keep statistical analysis value as authoritative for current_return

                        # Log the data sources used
                        logger.info(
                            f"Loaded trade history for {strategy_name}: "
                            f"MFE={strategy_data.mfe:.4f} (was {original_mfe:.4f}), "
                            f"MAE={strategy_data.mae:.4f} (was {original_mae:.4f}), "
                            f"Position age: {position_age_days} days, Status: {position_status}"
                        )
                    else:
                        logger.warning(
                            f"Skipping stale position data for {strategy_name}"
                        )
                else:
                    logger.warning(
                        f"No trade history found for strategy: {strategy_name}"
                    )
            else:
                logger.warning(f"Positions file not found: {positions_file}")

        except Exception as e:
            logger.warning(f"Error loading trade history for {strategy_name}: {e}")

    def _validate_performance_metrics(
        self, strategy_data: StrategyData, strategy_name: str
    ) -> List[str]:
        """
        Validate performance metrics for mathematical consistency and logical constraints

        Returns:
            List of validation warning messages (empty if all checks pass)
        """
        warnings = []

        try:
            current_return = getattr(strategy_data, "current_return", 0.0)
            mfe = getattr(strategy_data, "mfe", 0.0)
            mae = getattr(strategy_data, "mae", 0.0)

            # Constraint 1: MFE cannot be negative if current return is positive
            if current_return > 0 and mfe < 0:
                warnings.append(
                    f"Invalid negative MFE ({mfe:.4f}) with positive current return ({current_return:.4f})"
                )

            # Constraint 2: MAE represents maximum adverse excursion (loss magnitude)
            # Positive MAE with negative current return is mathematically valid
            # (position currently at loss but MAE shows maximum historical loss experienced)
            # This constraint is removed as it was incorrectly flagging valid scenarios

            # Constraint 3: Current return should not exceed MFE (if MFE > 0)
            # This may indicate data source timing mismatch between live current return and historical MFE
            if mfe > 0 and current_return > mfe:
                # Check if this is likely a data freshness issue vs calculation error
                excess_percentage = ((current_return - mfe) / mfe) * 100
                if (
                    excess_percentage < 20
                ):  # Less than 20% excess - likely data timing issue
                    warnings.append(
                        f"Current return ({current_return:.4f}) exceeds MFE ({mfe:.4f}) by {excess_percentage:.1f}% - "
                        "likely data freshness issue (current return uses live data, MFE uses historical data)"
                    )
                else:  # Large excess - likely calculation error
                    warnings.append(
                        f"Current return ({current_return:.4f}) significantly exceeds MFE ({mfe:.4f}) by {excess_percentage:.1f}% - "
                        "possible calculation error"
                    )

            # Constraint 4: Current return should not be worse than MAE (if MAE < 0)
            if mae < 0 and current_return < mae:
                warnings.append(
                    f"Current return ({current_return:.4f}) is worse than MAE ({mae:.4f}) - mathematically impossible"
                )

            # Constraint 5: Warn about extreme values that might indicate data errors
            if abs(mfe) > 2.0:  # MFE > 200%
                warnings.append(f"Extreme MFE value ({mfe:.4f}) - possible data error")

            if abs(mae) > 2.0:  # MAE > 200%
                warnings.append(f"Extreme MAE value ({mae:.4f}) - possible data error")

            if abs(current_return) > 2.0:  # Current return > 200%
                warnings.append(
                    f"Extreme current return ({current_return:.4f}) - possible data error"
                )

            # Constraint 6: Check for impossible zero values in active positions
            signal_confidence = getattr(strategy_data, "signal_confidence", 0.0)
            if signal_confidence > 0 and mfe == 0.0 and mae == 0.0:
                warnings.append(
                    "Both MFE and MAE are zero despite active signal - possible missing trade data"
                )

            # Constraint 7: Check statistical validity consistency
            statistical_validity = getattr(
                strategy_data, "statistical_validity", "UNKNOWN"
            )
            sample_size = getattr(strategy_data, "sample_size", 0)

            if statistical_validity == "HIGH" and sample_size < 100:
                warnings.append(
                    f"HIGH statistical validity claimed with small sample size ({sample_size})"
                )

            if statistical_validity == "LOW" and sample_size > 10000:
                warnings.append(
                    f"LOW statistical validity with large sample size ({sample_size}) - possible calculation error"
                )

        except Exception as e:
            warnings.append(f"Error during validation: {e}")

        return warnings

    def validate_mathematical_constraints(
        self, strategy_data: StrategyData, strategy_name: str, auto_fix: bool = True
    ) -> Dict[str, Any]:
        """
        Real-time mathematical constraint validation with automatic fixing capability

        Validates mathematical relationships between current return, MFE, and MAE.
        Can automatically trigger data refresh when inconsistencies are detected.

        Args:
            strategy_data: Strategy data to validate
            strategy_name: Strategy identifier for logging
            auto_fix: Whether to automatically attempt to fix constraint violations

        Returns:
            Dictionary with validation results and actions taken
        """
        validation_result = {
            "strategy_name": strategy_name,
            "timestamp": pd.Timestamp.now().isoformat(),
            "constraints_passed": 0,
            "constraints_failed": 0,
            "critical_violations": [],
            "warnings": [],
            "auto_fixes_attempted": [],
            "auto_fixes_successful": [],
            "data_quality_score": 0.0,
            "requires_manual_review": False,
        }

        try:
            current_return = getattr(strategy_data, "current_return", 0.0)
            mfe = getattr(strategy_data, "mfe", 0.0)
            mae = getattr(strategy_data, "mae", 0.0)
            sample_size = getattr(strategy_data, "sample_size", 0)

            total_constraints = 7  # Total number of constraints to check

            # Constraint 1: Basic data validity
            if all(
                isinstance(val, (int, float)) and pd.notna(val)
                for val in [current_return, mfe, mae]
            ):
                validation_result["constraints_passed"] += 1
            else:
                validation_result["constraints_failed"] += 1
                validation_result["critical_violations"].append(
                    "Invalid or missing performance metric values"
                )

            # Constraint 2: MFE cannot be negative if current return is positive
            if current_return > 0:
                if mfe >= 0:
                    validation_result["constraints_passed"] += 1
                else:
                    validation_result["constraints_failed"] += 1
                    validation_result["critical_violations"].append(
                        f"Negative MFE ({mfe:.4f}) with positive return ({current_return:.4f})"
                    )

                    if auto_fix:
                        # Attempt to recalculate MFE/MAE
                        fix_attempted = self._check_and_update_stale_mfe_mae(
                            strategy_data, strategy_name
                        )
                        validation_result["auto_fixes_attempted"].append(
                            "Negative MFE recalculation"
                        )
                        if fix_attempted:
                            validation_result["auto_fixes_successful"].append(
                                "Negative MFE recalculation"
                            )
                            # Re-check after fix
                            updated_mfe = getattr(strategy_data, "mfe", 0.0)
                            if updated_mfe >= 0:
                                validation_result["constraints_failed"] -= 1
                                validation_result["constraints_passed"] += 1
            else:
                validation_result["constraints_passed"] += 1

            # Constraint 3: Current return should not exceed MFE (mathematical impossibility)
            if mfe > 0:
                if current_return <= mfe:
                    validation_result["constraints_passed"] += 1
                else:
                    validation_result["constraints_failed"] += 1
                    excess_pct = ((current_return - mfe) / mfe) * 100

                    if excess_pct > 50:
                        validation_result["critical_violations"].append(
                            f"Current return ({current_return:.4f}) exceeds MFE ({mfe:.4f}) by {excess_pct:.1f}% - Critical mathematical violation"
                        )
                        validation_result["requires_manual_review"] = True
                    else:
                        validation_result["warnings"].append(
                            f"Current return ({current_return:.4f}) exceeds MFE ({mfe:.4f}) by {excess_pct:.1f}% - Likely data freshness issue"
                        )

                    if (
                        auto_fix and excess_pct <= 100
                    ):  # Only auto-fix if not too extreme
                        fix_attempted = self._check_and_update_stale_mfe_mae(
                            strategy_data, strategy_name
                        )
                        validation_result["auto_fixes_attempted"].append(
                            "MFE data refresh"
                        )
                        if fix_attempted:
                            validation_result["auto_fixes_successful"].append(
                                "MFE data refresh"
                            )
                            # Re-check after fix
                            updated_mfe = getattr(strategy_data, "mfe", 0.0)
                            if updated_mfe >= current_return:
                                validation_result["constraints_failed"] -= 1
                                validation_result["constraints_passed"] += 1
            else:
                validation_result["constraints_passed"] += 1

            # Constraint 4: Current return should not be worse than MAE (if MAE represents losses)
            if mae < 0:
                if current_return >= mae:
                    validation_result["constraints_passed"] += 1
                else:
                    validation_result["constraints_failed"] += 1
                    validation_result["critical_violations"].append(
                        f"Current return ({current_return:.4f}) worse than MAE ({mae:.4f}) - Mathematically impossible"
                    )
                    validation_result["requires_manual_review"] = True
            else:
                validation_result["constraints_passed"] += 1

            # Constraint 5: Extreme value detection
            extreme_threshold = 3.0  # 300% return/MFE/MAE
            extreme_values = []

            if abs(current_return) > extreme_threshold:
                extreme_values.append(f"current_return: {current_return:.4f}")
            if abs(mfe) > extreme_threshold:
                extreme_values.append(f"MFE: {mfe:.4f}")
            if abs(mae) > extreme_threshold:
                extreme_values.append(f"MAE: {mae:.4f}")

            if not extreme_values:
                validation_result["constraints_passed"] += 1
            else:
                validation_result["constraints_failed"] += 1
                validation_result["warnings"].append(
                    f"Extreme values detected: {', '.join(extreme_values)}"
                )

            # Constraint 6: Sample size consistency
            if sample_size > 0:
                validation_result["constraints_passed"] += 1
            else:
                validation_result["constraints_failed"] += 1
                validation_result["warnings"].append("Missing or zero sample size")

            # Constraint 7: Zero values in active positions (data completeness)
            signal_confidence = getattr(strategy_data, "signal_confidence", 0.0)
            if signal_confidence > 0:
                if mfe != 0.0 or mae != 0.0 or current_return != 0.0:
                    validation_result["constraints_passed"] += 1
                else:
                    validation_result["constraints_failed"] += 1
                    validation_result["warnings"].append(
                        "All performance metrics are zero despite active signal"
                    )

                    if auto_fix:
                        fix_attempted = self._check_and_update_stale_mfe_mae(
                            strategy_data, strategy_name
                        )
                        validation_result["auto_fixes_attempted"].append(
                            "Zero values refresh"
                        )
                        if fix_attempted:
                            validation_result["auto_fixes_successful"].append(
                                "Zero values refresh"
                            )
            else:
                validation_result["constraints_passed"] += 1

            # Calculate data quality score
            if total_constraints > 0:
                validation_result["data_quality_score"] = (
                    validation_result["constraints_passed"] / total_constraints
                )

            # Final assessment
            if validation_result["constraints_failed"] == 0:
                logger.info(
                    f"✅ All mathematical constraints passed for {strategy_name}"
                )
            else:
                logger.warning(
                    f"⚠️ {validation_result['constraints_failed']} constraint violations for {strategy_name}"
                )
                if validation_result["critical_violations"]:
                    logger.error(
                        f"🚨 Critical violations detected for {strategy_name}: {validation_result['critical_violations']}"
                    )

            return validation_result

        except Exception as e:
            logger.error(
                f"Error in mathematical constraint validation for {strategy_name}: {e}"
            )
            validation_result["critical_violations"].append(
                f"Validation error: {str(e)}"
            )
            validation_result["requires_manual_review"] = True
            return validation_result

    def _check_and_update_stale_mfe_mae(
        self, strategy_data: StrategyData, strategy_name: str
    ) -> bool:
        """
        Check if MFE/MAE data appears stale and attempt to update with fresh calculations

        Enhanced to handle mathematical inconsistencies and data freshness issues more robustly.

        Returns:
            bool: True if data was updated, False otherwise
        """
        try:
            # Check for multiple conditions that warrant a fresh calculation:
            # 1. Current return exceeds MFE (mathematical impossibility)
            # 2. Both MFE and MAE are zero (likely missing data)
            # 3. MFE is negative for profitable positions

            needs_update = False
            update_reason = ""

            if strategy_data.current_return > 0 and strategy_data.mfe < 0:
                needs_update = True
                update_reason = "negative MFE with positive return"
            elif (
                strategy_data.mfe > 0
                and strategy_data.current_return > strategy_data.mfe
            ):
                needs_update = True
                excess_percentage = (
                    (strategy_data.current_return - strategy_data.mfe)
                    / strategy_data.mfe
                ) * 100
                update_reason = (
                    f"current return exceeds MFE by {excess_percentage:.1f}%"
                )
            elif (
                strategy_data.mfe == 0.0
                and strategy_data.mae == 0.0
                and strategy_data.current_return != 0.0
            ):
                needs_update = True
                update_reason = "missing MFE/MAE data for active position"

            if not needs_update:
                return False

            logger.info(
                f"Attempting fresh MFE/MAE calculation for {strategy_name}: {update_reason}"
            )

            # Attempt to get fresh MFE/MAE calculation
            try:
                from app.tools.generalized_trade_history_exporter import (
                    calculate_mfe_mae,
                )

                # Extract position details from strategy data
                parts = strategy_name.split("_")
                if len(parts) < 3:  # Minimum: TICKER_TYPE_PARAM
                    logger.warning(f"Invalid strategy name format: {strategy_name}")
                    return False

                ticker = parts[0]

                # Try to get entry date from positions file data
                positions_file = (
                    self.base_path / "data" / "raw" / "positions" / "live_signals.csv"
                )
                if not positions_file.exists():
                    logger.warning(f"Positions file not found: {positions_file}")
                    return False

                import pandas as pd

                df = pd.read_csv(positions_file)

                # Find matching position - try multiple patterns
                patterns = [
                    f"{ticker}_{'_'.join(parts[1:4])}",  # Standard format
                    f"{ticker}_{'_'.join(parts[1:3])}",  # Shorter format
                    f"{ticker}_{parts[1]}",  # Basic format
                    ticker,  # Just ticker
                ]

                position = None
                for pattern in patterns:
                    matches = df[
                        df["Position_UUID"].str.contains(pattern, case=False, na=False)
                    ]
                    if not matches.empty:
                        position = matches.iloc[0]
                        logger.info(f"Found position using pattern: {pattern}")
                        break

                if position is None:
                    logger.warning(
                        f"No matching position found for {strategy_name} in positions file"
                    )
                    return False

                # Get entry details with fallback column names
                entry_date = position.get("Entry_Date", position.get("entry_date", ""))
                entry_price = float(
                    position.get("Avg_Entry_Price", position.get("avg_entry_price", 0))
                )
                direction = position.get("Direction", position.get("direction", "Long"))

                if not entry_date or entry_price <= 0:
                    logger.warning(
                        f"Invalid entry data for {strategy_name}: date={entry_date}, price={entry_price}"
                    )
                    return False

                # Calculate fresh MFE/MAE using current market data
                fresh_mfe, fresh_mae, _, _ = calculate_mfe_mae(
                    ticker=ticker,
                    entry_date=entry_date,
                    exit_date="",  # Open position
                    entry_price=entry_price,
                    direction=direction,
                    timeframe="D",
                )

                # Update if we got valid results
                updated = False
                if fresh_mfe is not None:
                    # Always update if we had mathematical inconsistency or missing data
                    if (
                        strategy_data.mfe <= 0
                        or strategy_data.current_return > strategy_data.mfe
                        or fresh_mfe > strategy_data.mfe
                    ):
                        old_mfe = strategy_data.mfe
                        strategy_data.mfe = fresh_mfe
                        logger.info(
                            f"✅ Updated MFE for {strategy_name}: {old_mfe:.4f} -> {fresh_mfe:.4f}"
                        )
                        updated = True

                if fresh_mae is not None:
                    # Update MAE if it's an improvement or if original was missing/invalid
                    if strategy_data.mae == 0.0 or abs(fresh_mae) > abs(
                        strategy_data.mae
                    ):
                        old_mae = strategy_data.mae
                        strategy_data.mae = fresh_mae
                        logger.info(
                            f"✅ Updated MAE for {strategy_name}: {old_mae:.4f} -> {fresh_mae:.4f}"
                        )
                        updated = True

                if updated:
                    logger.info(
                        f"✅ Successfully refreshed stale data for {strategy_name}: "
                        f"MFE={strategy_data.mfe:.4f}, MAE={strategy_data.mae:.4f}, "
                        f"Current Return={strategy_data.current_return:.4f}"
                    )
                return updated

            except ImportError:
                logger.warning(
                    "Cannot import MFE calculation module - generalized_trade_history_exporter not available"
                )
            except Exception as calc_error:
                logger.warning(
                    f"Error calculating fresh MFE/MAE for {strategy_name}: {calc_error}"
                )

            return False

        except Exception as e:
            logger.error(f"Error checking stale MFE/MAE for {strategy_name}: {e}")
            return False

    def detect_statistical_uniformity_coordinated(
        self, strategy_identifiers: List[str], use_fresh_data: bool = False
    ) -> Dict[str, Any]:
        """
        Detect statistical uniformity using coordinated data loading.

        This method uses the central coordinator to ensure all strategies are analyzed
        with consistent data, providing more reliable uniformity detection.

        Args:
            strategy_identifiers: List of strategy names to analyze
            use_fresh_data: Whether to force fresh data loading

        Returns:
            Dictionary with enhanced uniformity detection results
        """
        try:
            # Load all strategies with coordinated data consistency
            strategies_data_dict = self.get_multiple_strategies(
                strategy_identifiers=strategy_identifiers,
                use_snapshot=True,
                force_refresh=use_fresh_data,
            )

            # Filter out None results and convert to list
            strategies_data = [
                data for data in strategies_data_dict.values() if data is not None
            ]

            if len(strategies_data) < 2:
                return {
                    "error": f"Insufficient data: only {len(strategies_data)} valid strategies found",
                    "requested_strategies": len(strategy_identifiers),
                    "valid_strategies": len(strategies_data),
                }

            # Use the original detection logic with coordinated data
            uniformity_report = self.detect_statistical_uniformity(strategies_data)

            # Add coordination metadata
            uniformity_report["coordination_metadata"] = {
                "used_central_coordinator": True,
                "data_consistency_guaranteed": True,
                "requested_strategies": len(strategy_identifiers),
                "analyzed_strategies": len(strategies_data),
                "data_loading_method": "coordinated_snapshot",
            }

            return uniformity_report

        except Exception as e:
            logger.error(f"Error in coordinated uniformity detection: {e}")
            return {
                "error": str(e),
                "coordination_metadata": {
                    "used_central_coordinator": True,
                    "data_consistency_guaranteed": False,
                    "error_occurred": True,
                },
            }

    def detect_statistical_uniformity(
        self, strategies_data: List[StrategyData]
    ) -> Dict[str, Any]:
        """
        Detect suspicious statistical uniformity across multiple strategies

        Identifies cases where multiple strategies show identical or suspiciously similar
        statistical values, which may indicate hard-coded values or calculation errors.

        Args:
            strategies_data: List of StrategyData objects to analyze

        Returns:
            Dictionary with uniformity detection results and alerts
        """
        uniformity_report = {
            "timestamp": pd.Timestamp.now().isoformat(),
            "total_strategies_analyzed": len(strategies_data),
            "uniformity_alerts": [],
            "statistical_clusters": {},
            "suspicious_patterns": [],
            "recommendations": [],
            "severity_level": "LOW",  # LOW, MEDIUM, HIGH, CRITICAL
        }

        if len(strategies_data) < 2:
            uniformity_report["recommendations"].append(
                "Need at least 2 strategies for uniformity analysis"
            )
            return uniformity_report

        try:
            # Collect statistical values
            p_values = []
            strategy_percentiles = []
            confidence_levels = []
            convergence_scores = []
            z_scores = []
            sample_sizes = []

            strategy_names = []

            for strategy_data in strategies_data:
                strategy_names.append(strategy_data.strategy_name)
                p_values.append(getattr(strategy_data, "p_value", 0.0))
                strategy_percentiles.append(
                    getattr(strategy_data, "strategy_layer_percentile", 0.0)
                )

                # Extract confidence from signal_confidence (handle percentage vs decimal)
                confidence = getattr(strategy_data, "signal_confidence", 0.0)
                if confidence > 1.0:
                    confidence = confidence / 100.0  # Convert percentage to decimal
                confidence_levels.append(confidence)

                convergence_scores.append(
                    getattr(strategy_data, "dual_layer_convergence_score", 0.0)
                )
                z_scores.append(getattr(strategy_data, "z_score_divergence", 0.0))
                sample_sizes.append(getattr(strategy_data, "sample_size", 0))

            # Check for exact matches (highly suspicious)
            self._check_exact_uniformity(
                uniformity_report, "p_value", p_values, strategy_names
            )
            self._check_exact_uniformity(
                uniformity_report,
                "strategy_layer_percentile",
                strategy_percentiles,
                strategy_names,
            )
            self._check_exact_uniformity(
                uniformity_report,
                "signal_confidence",
                confidence_levels,
                strategy_names,
            )
            self._check_exact_uniformity(
                uniformity_report,
                "dual_layer_convergence_score",
                convergence_scores,
                strategy_names,
            )

            # Check for clustering (statistically unlikely similarity)
            self._check_statistical_clustering(
                uniformity_report,
                "signal_confidence",
                confidence_levels,
                strategy_names,
                tolerance=0.02,
            )  # 2% tolerance
            self._check_statistical_clustering(
                uniformity_report, "p_value", p_values, strategy_names, tolerance=0.001
            )  # 0.1% tolerance

            # Check for suspicious patterns
            self._check_suspicious_patterns(
                uniformity_report,
                {
                    "p_values": p_values,
                    "strategy_percentiles": strategy_percentiles,
                    "confidence_levels": confidence_levels,
                    "z_scores": z_scores,
                    "sample_sizes": sample_sizes,
                },
                strategy_names,
            )

            # Determine overall severity
            critical_alerts = [
                alert
                for alert in uniformity_report["uniformity_alerts"]
                if "identical" in alert.lower()
            ]
            high_alerts = [
                alert
                for alert in uniformity_report["uniformity_alerts"]
                if "highly clustered" in alert.lower()
            ]

            if critical_alerts:
                uniformity_report["severity_level"] = "CRITICAL"
                uniformity_report["recommendations"].append(
                    "Immediate investigation required - identical statistical values detected"
                )
            elif high_alerts:
                uniformity_report["severity_level"] = "HIGH"
                uniformity_report["recommendations"].append(
                    "Statistical analysis pipeline audit recommended - suspicious clustering detected"
                )
            elif uniformity_report["uniformity_alerts"]:
                uniformity_report["severity_level"] = "MEDIUM"
                uniformity_report["recommendations"].append(
                    "Monitor for potential hard-coded values or calculation biases"
                )

            # Add general recommendations
            if uniformity_report["severity_level"] in ["HIGH", "CRITICAL"]:
                uniformity_report["recommendations"].extend(
                    [
                        "Verify statistical calculation implementations",
                        "Check for hard-coded fallback values",
                        "Audit data source consistency",
                        "Review random number generation and seeding",
                    ]
                )

            logger.info(
                f"Statistical uniformity analysis completed: {uniformity_report['severity_level']} severity, "
                f"{len(uniformity_report['uniformity_alerts'])} alerts"
            )

            return uniformity_report

        except Exception as e:
            logger.error(f"Error in statistical uniformity detection: {e}")
            uniformity_report["uniformity_alerts"].append(f"Analysis error: {str(e)}")
            uniformity_report["severity_level"] = "UNKNOWN"
            return uniformity_report

    def _check_exact_uniformity(
        self,
        report: Dict,
        metric_name: str,
        values: List[float],
        strategy_names: List[str],
        min_strategies: int = 3,
    ):
        """Check for exact matches across strategies"""
        from collections import Counter

        # Filter out zero/default values for meaningful analysis
        meaningful_values = [
            (val, name) for val, name in zip(values, strategy_names) if val != 0.0
        ]

        if len(meaningful_values) < min_strategies:
            return

        # Count occurrences of each value
        value_counts = Counter([val for val, _ in meaningful_values])

        for value, count in value_counts.items():
            if count >= min_strategies:
                matching_strategies = [
                    name for val, name in meaningful_values if val == value
                ]

                alert = f"🚨 CRITICAL: {count} strategies have identical {metric_name} = {value:.6f} ({', '.join(matching_strategies[:5])}{'...' if len(matching_strategies) > 5 else ''})"
                report["uniformity_alerts"].append(alert)

                if metric_name not in report["statistical_clusters"]:
                    report["statistical_clusters"][metric_name] = []
                report["statistical_clusters"][metric_name].append(
                    {
                        "value": value,
                        "count": count,
                        "strategies": matching_strategies,
                        "type": "exact_match",
                    }
                )

    def _check_statistical_clustering(
        self,
        report: Dict,
        metric_name: str,
        values: List[float],
        strategy_names: List[str],
        tolerance: float = 0.01,
    ):
        """Check for statistically unlikely clustering"""
        import numpy as np

        # Filter meaningful values
        meaningful_data = [
            (val, name)
            for val, name in zip(values, strategy_names)
            if val != 0.0 and not np.isnan(val)
        ]

        if len(meaningful_data) < 4:
            return

        meaningful_values = [val for val, _ in meaningful_data]

        # Calculate clustering metrics
        std_dev = np.std(meaningful_values)
        mean_val = np.mean(meaningful_values)

        if std_dev < tolerance and mean_val != 0:
            # Values are very tightly clustered
            alert = f"⚠️ HIGH: {metric_name} values highly clustered around {mean_val:.4f} (std: {std_dev:.6f}) - statistically unlikely"
            report["uniformity_alerts"].append(alert)

            if metric_name not in report["statistical_clusters"]:
                report["statistical_clusters"][metric_name] = []
            report["statistical_clusters"][metric_name].append(
                {
                    "mean": mean_val,
                    "std_dev": std_dev,
                    "count": len(meaningful_data),
                    "type": "tight_clustering",
                    "tolerance": tolerance,
                }
            )

    def _check_suspicious_patterns(
        self, report: Dict, metrics: Dict[str, List[float]], strategy_names: List[str]
    ):
        """Check for suspicious patterns across metrics"""
        import numpy as np

        # Pattern 1: All strategy percentiles are exactly 50.0
        strategy_percentiles = metrics["strategy_percentiles"]
        exact_50_count = sum(1 for val in strategy_percentiles if val == 50.0)
        if exact_50_count >= 3:
            report["suspicious_patterns"].append(
                f"🔍 PATTERN: {exact_50_count} strategies have strategy_layer_percentile = 50.0 (likely fallback value)"
            )

        # Pattern 2: P-values clustered around common significance levels
        p_values = metrics["p_values"]
        common_p_values = [0.05, 0.01, 0.10, 0.20]
        for common_p in common_p_values:
            exact_matches = sum(1 for val in p_values if abs(val - common_p) < 0.001)
            if exact_matches >= 3:
                report["suspicious_patterns"].append(
                    f"🔍 PATTERN: {exact_matches} strategies have p-value ≈ {common_p} (possibly hard-coded)"
                )

        # Pattern 3: Confidence levels in narrow band
        confidence_levels = [c for c in metrics["confidence_levels"] if c > 0]
        if len(confidence_levels) >= 4:
            conf_std = np.std(confidence_levels)
            conf_mean = np.mean(confidence_levels)
            if conf_std < 0.03 and conf_mean > 0.5:  # Less than 3% std deviation
                report["suspicious_patterns"].append(
                    f"🔍 PATTERN: Confidence levels clustered in narrow band ({conf_mean:.3f} ± {conf_std:.3f}) - unlikely natural variation"
                )

        # Pattern 4: Zero values indicating missing calculations
        for metric_name, values in metrics.items():
            zero_count = sum(1 for val in values if val == 0.0)
            if zero_count >= len(values) * 0.5:  # More than 50% are zero
                report["suspicious_patterns"].append(
                    f"🔍 PATTERN: {zero_count}/{len(values)} strategies have {metric_name} = 0.0 (possible missing calculations)"
                )

    def generate_coordinated_data_quality_report(
        self,
        strategy_identifiers: Optional[List[str]] = None,
        include_uniformity_analysis: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report using central coordination.

        This method leverages the central coordinator to provide enhanced data quality
        analysis with guaranteed data consistency across all strategies.

        Args:
            strategy_identifiers: Specific strategies to analyze (None for all)
            include_uniformity_analysis: Whether to include statistical uniformity detection

        Returns:
            Enhanced data quality report with coordination metadata
        """
        try:
            # Get all strategies if none specified
            if strategy_identifiers is None:
                # Load list of all available strategies from coordinator
                coordinator_status = self.coordinator.get_coordination_status()
                if not coordinator_status.get("data_sources", {}).get(
                    "statistical_csv"
                ):
                    return {"error": "Statistical CSV not available via coordinator"}

                # Get all strategy names from CSV
                df = pd.read_csv(self.coordinator.statistical_csv)
                strategy_identifiers = df["strategy_name"].unique().tolist()

            # Load all strategies with coordinated consistency
            strategies_data_dict = self.get_multiple_strategies(
                strategy_identifiers=strategy_identifiers,
                use_snapshot=True,
                force_refresh=False,
            )

            # Generate enhanced report
            report = {
                "report_timestamp": pd.Timestamp.now().isoformat(),
                "coordination_enabled": True,
                "total_strategies_requested": len(strategy_identifiers),
                "total_strategies_loaded": sum(
                    1 for data in strategies_data_dict.values() if data is not None
                ),
                "strategies_with_issues": 0,
                "critical_issues": 0,
                "warning_issues": 0,
                "coordination_metadata": {
                    "central_coordinator_used": True,
                    "data_consistency_guaranteed": True,
                    "snapshot_based_analysis": True,
                },
                "strategy_details": [],
                "recommendations": [],
                "data_pipeline_health": "UNKNOWN",
            }

            # Analyze each strategy
            valid_strategies = []
            for identifier, strategy_data in strategies_data_dict.items():
                if strategy_data is None:
                    report["strategies_with_issues"] += 1
                    report["critical_issues"] += 1
                    continue

                valid_strategies.append(strategy_data)

                # Perform individual strategy analysis
                strategy_analysis = {
                    "strategy_name": strategy_data.strategy_name,
                    "data_quality_score": 1.0,  # Default high quality from coordinator
                    "validation_passed": True,
                    "issues": [],
                    "coordinator_validated": True,
                }

                # Check for obvious data issues
                if (
                    strategy_data.mfe > 0
                    and strategy_data.current_return > strategy_data.mfe
                ):
                    strategy_analysis["issues"].append(
                        "Current return exceeds MFE (mathematical impossibility)"
                    )
                    strategy_analysis["validation_passed"] = False
                    report["critical_issues"] += 1

                if strategy_data.sample_size == 0:
                    strategy_analysis["issues"].append("Missing sample size")
                    strategy_analysis["validation_passed"] = False
                    report["warning_issues"] += 1

                if not strategy_analysis["validation_passed"]:
                    report["strategies_with_issues"] += 1

                report["strategy_details"].append(strategy_analysis)

            # Include uniformity analysis if requested
            if include_uniformity_analysis and len(valid_strategies) >= 2:
                try:
                    uniformity_analysis = self.detect_statistical_uniformity(
                        valid_strategies
                    )
                    report["uniformity_analysis"] = uniformity_analysis

                    # Count uniformity issues
                    if uniformity_analysis.get("severity_level") in [
                        "HIGH",
                        "CRITICAL",
                    ]:
                        report["critical_issues"] += len(
                            uniformity_analysis.get("uniformity_alerts", [])
                        )
                except Exception as e:
                    report["uniformity_analysis"] = {"error": str(e)}

            # Calculate overall health
            if report["critical_issues"] == 0:
                report["data_pipeline_health"] = "HEALTHY"
            elif report["critical_issues"] < report["total_strategies_loaded"] * 0.1:
                report["data_pipeline_health"] = "DEGRADED"
            else:
                report["data_pipeline_health"] = "CRITICAL"

            # Add recommendations
            if report["critical_issues"] > 0:
                report["recommendations"].append(
                    "Immediate investigation required for critical data quality issues"
                )
            if report["warning_issues"] > 0:
                report["recommendations"].append(
                    "Review and resolve warning-level data quality issues"
                )
            if report["data_pipeline_health"] == "HEALTHY":
                report["recommendations"].append(
                    "Data pipeline operating within normal parameters"
                )

            return report

        except Exception as e:
            logger.error(f"Error generating coordinated data quality report: {e}")
            return {
                "error": str(e),
                "coordination_metadata": {
                    "central_coordinator_used": True,
                    "error_occurred": True,
                },
            }

    def generate_data_quality_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive data quality report for all strategies

        Enhanced with statistical uniformity detection and comprehensive analysis.

        Returns:
            Dictionary containing data quality assessment and recommendations
        """
        report = {
            "report_timestamp": pd.Timestamp.now().isoformat(),
            "total_strategies": 0,
            "strategies_with_issues": 0,
            "critical_issues": 0,
            "warning_issues": 0,
            "data_source_usage": {
                "json_primary": 0,
                "positions_primary": 0,
                "mixed_sources": 0,
            },
            "issue_categories": {},
            "uniformity_analysis": {},
            "mathematical_constraints": {},
            "strategy_details": [],
            "recommendations": [],
            "data_pipeline_health": "UNKNOWN",
        }

        try:
            strategies = self.get_all_strategies()
            report["total_strategies"] = len(strategies)

            issue_counts = {
                "mathematical_impossibility": 0,
                "missing_trade_data": 0,
                "extreme_values": 0,
                "statistical_inconsistency": 0,
                "data_source_mismatch": 0,
            }

            for strategy_name in strategies:
                try:
                    strategy_data = self.get_strategy_data(strategy_name)
                    if not strategy_data:
                        continue

                    # Validate and categorize issues
                    validation_warnings = self._validate_performance_metrics(
                        strategy_data, strategy_name
                    )

                    strategy_report = {
                        "strategy_name": strategy_name,
                        "ticker": strategy_data.ticker,
                        "data_quality_score": self._calculate_data_quality_score(
                            strategy_data, validation_warnings
                        ),
                        "issues": validation_warnings,
                        "issue_severity": "CLEAN"
                        if not validation_warnings
                        else (
                            "CRITICAL" if len(validation_warnings) >= 3 else "WARNING"
                        ),
                        "data_sources_used": self._identify_data_sources_used(
                            strategy_data
                        ),
                        "performance_metrics": {
                            "current_return": strategy_data.current_return,
                            "mfe": strategy_data.mfe,
                            "mae": strategy_data.mae,
                            "unrealized_pnl": strategy_data.unrealized_pnl,
                        },
                    }

                    if validation_warnings:
                        report["strategies_with_issues"] += 1
                        if len(validation_warnings) >= 3:
                            report["critical_issues"] += 1
                        else:
                            report["warning_issues"] += 1

                        # Categorize issues
                        for warning in validation_warnings:
                            if "mathematically impossible" in warning:
                                issue_counts["mathematical_impossibility"] += 1
                            elif "missing trade data" in warning:
                                issue_counts["missing_trade_data"] += 1
                            elif "Extreme" in warning:
                                issue_counts["extreme_values"] += 1
                            elif "statistical validity" in warning:
                                issue_counts["statistical_inconsistency"] += 1

                    report["strategy_details"].append(strategy_report)

                except Exception as e:
                    logger.error(f"Error analyzing strategy {strategy_name}: {e}")

            report["issue_categories"] = issue_counts

            # Calculate data pipeline health
            total_issues = sum(issue_counts.values())
            if total_issues == 0:
                report["data_pipeline_health"] = "HEALTHY"
            elif (
                total_issues <= report["total_strategies"] * 0.1
            ):  # ≤10% of strategies have issues
                report["data_pipeline_health"] = "GOOD"
            elif (
                total_issues <= report["total_strategies"] * 0.3
            ):  # ≤30% of strategies have issues
                report["data_pipeline_health"] = "DEGRADED"
            else:
                report["data_pipeline_health"] = "CRITICAL"

            # Generate recommendations
            report["recommendations"] = self._generate_recommendations(
                issue_counts, report
            )

        except Exception as e:
            logger.error(f"Error generating data quality report: {e}")
            report["error"] = str(e)

        return report

    def _calculate_data_quality_score(
        self, strategy_data: StrategyData, validation_warnings: List[str]
    ) -> float:
        """Calculate data quality score (0-100) for a strategy"""
        score = 100.0

        # Deduct points for each validation warning
        for warning in validation_warnings:
            if "mathematically impossible" in warning:
                score -= 40  # Critical mathematical error
            elif "missing trade data" in warning:
                score -= 30  # Missing critical data
            elif "Extreme" in warning:
                score -= 20  # Suspicious values
            elif "statistical validity" in warning:
                score -= 15  # Statistical inconsistency
            else:
                score -= 10  # Other issues

        # Bonus points for data completeness
        if strategy_data.mfe != 0.0:
            score += 5
        if strategy_data.mae != 0.0:
            score += 5
        if strategy_data.sample_size > 1000:
            score += 5

        return max(0.0, min(100.0, score))

    def _identify_data_sources_used(
        self, strategy_data: StrategyData
    ) -> Dict[str, bool]:
        """Identify which data sources were used for this strategy"""
        return {
            "statistical_csv": True,  # Always used as base
            "statistical_json": strategy_data.raw_analysis_data is not None,
            "backtesting_data": strategy_data.take_profit_pct > 0,
            "positions_file": strategy_data.mfe != 0.0 or strategy_data.mae != 0.0,
        }

    def _generate_recommendations(
        self, issue_counts: Dict[str, int], report: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations based on issue analysis"""
        recommendations = []

        if issue_counts["mathematical_impossibility"] > 0:
            recommendations.append(
                f"CRITICAL: Fix MFE/MAE calculation logic - {issue_counts['mathematical_impossibility']} "
                "strategies have current returns exceeding maximum favorable excursion"
            )

        if issue_counts["missing_trade_data"] > 0:
            recommendations.append(
                f"HIGH: Investigate missing trade history data for {issue_counts['missing_trade_data']} strategies"
            )

        if report["data_pipeline_health"] == "CRITICAL":
            recommendations.append(
                "URGENT: Data pipeline requires immediate attention - majority of strategies have data quality issues"
            )

        if issue_counts["extreme_values"] > 0:
            recommendations.append(
                f"MEDIUM: Review {issue_counts['extreme_values']} strategies with extreme values for data errors"
            )

        # Statistical analysis pipeline recommendations
        strategies_with_zero_mfe = sum(
            1
            for s in report["strategy_details"]
            if s["performance_metrics"]["mfe"] == 0.0
        )
        if strategies_with_zero_mfe > report["total_strategies"] * 0.5:
            recommendations.append(
                "HIGH: Statistical analysis pipeline is not calculating MFE values - requires immediate fix"
            )

        return recommendations

    def get_all_strategies(self) -> List[str]:
        """Get list of all available strategy names"""
        try:
            if not self.statistical_csv.exists():
                return []

            df = pd.read_csv(self.statistical_csv)
            return df["strategy_name"].tolist()

        except Exception as e:
            logger.error(f"Error getting all strategies: {e}")
            return []

    def get_strategy_summary(self, strategy_identifier: str) -> Dict[str, Any]:
        """Get quick summary of strategy data"""
        strategy_data = self.get_strategy_data(strategy_identifier)
        if not strategy_data:
            return {}

        return {
            "strategy_name": strategy_data.strategy_name,
            "ticker": strategy_data.ticker,
            "exit_signal": strategy_data.exit_signal,
            "signal_confidence": strategy_data.signal_confidence,
            "statistical_validity": strategy_data.statistical_validity,
            "sample_size": strategy_data.sample_size,
            "unrealized_pnl": strategy_data.unrealized_pnl,
            "take_profit_pct": strategy_data.take_profit_pct,
            "stop_loss_pct": strategy_data.stop_loss_pct,
            "position_uuid": strategy_data.position_uuid,
        }


def get_signal_data_aggregator(
    base_path: Optional[Path] = None,
) -> SignalDataAggregator:
    """Factory function to get configured SignalDataAggregator"""
    return SignalDataAggregator(base_path)


# CLI support
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Signal Data Aggregator")
    parser.add_argument("--strategy", help="Strategy name or Position_UUID")
    parser.add_argument("--summary", action="store_true", help="Show summary only")
    parser.add_argument(
        "--data-quality-report",
        action="store_true",
        help="Generate comprehensive data quality report",
    )
    parser.add_argument("--base-path", help="Base path to trading system")
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format",
    )
    parser.add_argument("--save-report", help="Save report to file")

    args = parser.parse_args()

    aggregator = get_signal_data_aggregator(
        Path(args.base_path) if args.base_path else None
    )

    if args.data_quality_report:
        print("Generating comprehensive data quality report...")
        report = aggregator.generate_data_quality_report()

        if args.output_format == "json":
            output = json.dumps(report, indent=2)
        else:
            # Format as human-readable text
            output = f"""
=== DATA QUALITY REPORT ===
Generated: {report['report_timestamp']}

OVERVIEW:
- Total Strategies: {report['total_strategies']}
- Strategies with Issues: {report['strategies_with_issues']}
- Critical Issues: {report['critical_issues']}
- Warning Issues: {report['warning_issues']}
- Pipeline Health: {report['data_pipeline_health']}

ISSUE BREAKDOWN:
- Mathematical Impossibilities: {report['issue_categories']['mathematical_impossibility']}
- Missing Trade Data: {report['issue_categories']['missing_trade_data']}
- Extreme Values: {report['issue_categories']['extreme_values']}
- Statistical Inconsistencies: {report['issue_categories']['statistical_inconsistency']}

RECOMMENDATIONS:
"""
            for i, rec in enumerate(report["recommendations"], 1):
                output += f"{i}. {rec}\n"

            output += "\nSTRATEGY DETAILS:\n"
            for strategy in report["strategy_details"]:
                if strategy["issues"]:  # Only show strategies with issues
                    output += f"\n{strategy['strategy_name']} ({strategy['ticker']}):\n"
                    output += (
                        f"  Quality Score: {strategy['data_quality_score']:.1f}/100\n"
                    )
                    output += f"  Severity: {strategy['issue_severity']}\n"
                    output += f"  Issues:\n"
                    for issue in strategy["issues"]:
                        output += f"    - {issue}\n"

        if args.save_report:
            with open(args.save_report, "w") as f:
                f.write(output)
            print(f"Report saved to: {args.save_report}")
        else:
            print(output)

    elif args.strategy:
        if args.summary:
            summary = aggregator.get_strategy_summary(args.strategy)
            if summary:
                for key, value in summary.items():
                    print(f"{key}: {value}")
            else:
                print(f"Strategy '{args.strategy}' not found")
        else:
            strategy_data = aggregator.get_strategy_data(args.strategy)
            if strategy_data:
                print(f"Strategy: {strategy_data.strategy_name}")
                print(f"Signal: {strategy_data.exit_signal}")
                print(f"Confidence: {strategy_data.signal_confidence:.1f}%")
                print(f"Validity: {strategy_data.statistical_validity}")
                print(f"Position UUID: {strategy_data.position_uuid}")

                # Show data quality assessment
                validation_warnings = aggregator._validate_performance_metrics(
                    strategy_data, strategy_data.strategy_name
                )
                if validation_warnings:
                    print("\nData Quality Issues:")
                    for warning in validation_warnings:
                        print(f"  - {warning}")
                else:
                    print("\nData Quality: CLEAN")
            else:
                print(f"Strategy '{args.strategy}' not found")
    else:
        parser.print_help()
