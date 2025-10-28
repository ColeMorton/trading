"""
Data Migration Utilities

This module provides utilities for migrating and cleaning up legacy trading data
to ensure compliance with current data quality standards.

Key Features:
- Legacy UUID format migration
- Schema standardization across portfolio files
- Bulk data quality fixes
- Backup and rollback capabilities
"""

import contextlib
from datetime import datetime
import logging
from pathlib import Path
import shutil
from typing import Any

import pandas as pd

from ..uuid_utils import generate_position_uuid
from ..validators.data_quality_validator import DataQualityValidator


class DataMigrationManager:
    """Manager for data migration and cleanup operations."""

    def __init__(
        self, base_dir: Path | None = None, logger: logging.Logger | None = None,
    ):
        """
        Initialize migration manager.

        Args:
            base_dir: Base directory for the trading system
            logger: Logger instance
        """
        self.base_dir = base_dir or Path.cwd()
        self.logger = logger or logging.getLogger(__name__)
        self.validator = DataQualityValidator(logger)

        # Directories
        self.positions_dir = self.base_dir / "csv" / "positions"
        self.backup_dir = self.base_dir / "backups" / "data_migration"

    def migrate_all_portfolios(self, create_backup: bool = True) -> dict[str, Any]:
        """
        Migrate all portfolio files to current data quality standards.

        Args:
            create_backup: Whether to create backups before migration

        Returns:
            Migration results summary
        """
        results = {
            "migrated_files": [],
            "failed_files": [],
            "total_fixes": 0,
            "backup_location": None,
        }

        if not self.positions_dir.exists():
            self.logger.error(f"Positions directory not found: {self.positions_dir}")
            return results

        # Create backup if requested
        if create_backup:
            backup_path = self._create_backup()
            results["backup_location"] = str(backup_path)
            self.logger.info(f"Created backup at: {backup_path}")

        # Find all portfolio CSV files
        portfolio_files = list(self.positions_dir.glob("*.csv"))

        if not portfolio_files:
            self.logger.warning("No portfolio CSV files found")
            return results

        self.logger.info(f"Found {len(portfolio_files)} portfolio files to migrate")

        # Migrate each file
        for file_path in portfolio_files:
            try:
                file_result = self.migrate_single_portfolio(file_path)

                if file_result["success"]:
                    results["migrated_files"].append(
                        {
                            "file": str(file_path),
                            "fixes_applied": file_result["fixes_applied"],
                            "positions_processed": file_result["positions_processed"],
                        },
                    )
                    results["total_fixes"] += file_result["total_fixes"]
                else:
                    results["failed_files"].append(
                        {"file": str(file_path), "error": file_result["error"]},
                    )

            except Exception as e:
                self.logger.exception(f"Failed to migrate {file_path}: {e}")
                results["failed_files"].append(
                    {"file": str(file_path), "error": str(e)},
                )

        # Summary
        self.logger.info("Migration complete:")
        self.logger.info(
            f"  Successfully migrated: {len(results['migrated_files'])} files",
        )
        self.logger.info(f"  Failed migrations: {len(results['failed_files'])} files")
        self.logger.info(f"  Total fixes applied: {results['total_fixes']}")

        return results

    def migrate_single_portfolio(self, file_path: Path) -> dict[str, Any]:
        """
        Migrate a single portfolio file to current standards.

        Args:
            file_path: Path to the portfolio CSV file

        Returns:
            Migration results for this file
        """
        try:
            self.logger.info(f"Migrating portfolio: {file_path.name}")

            # Read the file
            df = pd.read_csv(file_path)
            original_count = len(df)

            # Validate current state
            validation_results = self.validator.validate_position_data(df)

            self.logger.info(f"  Original positions: {original_count}")
            self.logger.info(
                f"  Issues found: {len(validation_results['critical_issues'])}",
            )

            # Apply fixes
            df_migrated, fixes_applied = self._apply_comprehensive_migration(df)

            # Validate migrated data
            post_validation = self.validator.validate_position_data(df_migrated)

            # Save migrated file
            df_migrated.to_csv(file_path, index=False)

            result = {
                "success": True,
                "positions_processed": original_count,
                "fixes_applied": fixes_applied,
                "total_fixes": len(fixes_applied),
                "issues_before": len(validation_results["critical_issues"]),
                "issues_after": len(post_validation["critical_issues"]),
                "validation_improved": len(validation_results["critical_issues"])
                > len(post_validation["critical_issues"]),
            }

            self.logger.info(
                f"  Migration complete: {len(fixes_applied)} fixes applied",
            )

            return result

        except Exception as e:
            self.logger.exception(f"Failed to migrate {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "positions_processed": 0,
                "fixes_applied": [],
                "total_fixes": 0,
            }

    def _apply_comprehensive_migration(
        self, df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, list[str]]:
        """
        Apply comprehensive migration fixes to a DataFrame.

        Args:
            df: Original DataFrame

        Returns:
            Tuple of (migrated_df, list_of_fixes)
        """
        df_migrated = df.copy()
        fixes_applied = []

        # 1. Fix UUID formats (most critical)
        uuid_fixes = self._fix_uuid_formats(df_migrated)
        if uuid_fixes:
            fixes_applied.extend(uuid_fixes)

        # 2. Populate missing Trade_Type
        trade_type_fixes = self._fix_trade_type(df_migrated)
        if trade_type_fixes:
            fixes_applied.extend(trade_type_fixes)

        # 3. Standardize numerical precision
        precision_fixes = self._standardize_precision(df_migrated)
        if precision_fixes:
            fixes_applied.extend(precision_fixes)

        # 4. Fix scientific notation
        sci_notation_fixes = self._fix_scientific_notation(df_migrated)
        if sci_notation_fixes:
            fixes_applied.extend(sci_notation_fixes)

        # 5. Validate and fix data types
        type_fixes = self._fix_data_types(df_migrated)
        if type_fixes:
            fixes_applied.extend(type_fixes)

        return df_migrated, fixes_applied

    def _fix_uuid_formats(self, df: pd.DataFrame) -> list[str]:
        """Fix UUID formats for SMA/EMA strategies."""
        fixes = []

        if "Strategy_Type" not in df.columns or "Position_UUID" not in df.columns:
            return fixes

        # Fix SMA/EMA UUIDs that incorrectly include signal period
        sma_ema_mask = df["Strategy_Type"].isin(["SMA", "EMA"])
        incorrect_uuid_mask = df["Position_UUID"].str.contains("_0_", na=False)

        positions_to_fix = sma_ema_mask & incorrect_uuid_mask

        if positions_to_fix.any():
            count = positions_to_fix.sum()

            # For each position, reconstruct the UUID using the centralized function
            for idx in df[positions_to_fix].index:
                row = df.loc[idx]

                # Extract entry date from timestamp
                entry_date = None
                if pd.notna(row.get("Entry_Timestamp")):
                    try:
                        entry_date = str(row["Entry_Timestamp"]).split(" ")[0]
                    except:
                        # Try to extract from existing UUID
                        uuid_parts = str(row["Position_UUID"]).split("_")
                        if len(uuid_parts) >= 6:
                            entry_date = uuid_parts[-1]

                if entry_date:
                    # Generate correct UUID
                    new_uuid = generate_position_uuid(
                        ticker=str(row["Ticker"]),
                        strategy_type=str(row["Strategy_Type"]),
                        fast_period=int(row["Fast_Period"]),
                        slow_period=int(row["Slow_Period"]),
                        signal_period=0,  # Will be omitted for SMA/EMA
                        entry_date=entry_date,
                    )
                    df.loc[idx, "Position_UUID"] = new_uuid

            fixes.append(f"Fixed UUID format for {count} SMA/EMA positions")

        return fixes

    def _fix_trade_type(self, df: pd.DataFrame) -> list[str]:
        """Populate missing Trade_Type fields."""
        fixes = []

        if "Trade_Type" not in df.columns:
            return fixes

        # Find positions with missing Trade_Type
        missing_mask = (df["Trade_Type"].isna()) | (df["Trade_Type"] == "")

        if missing_mask.any() and "Direction" in df.columns:
            count = missing_mask.sum()
            df.loc[missing_mask, "Trade_Type"] = df.loc[missing_mask, "Direction"]
            fixes.append(f"Populated Trade_Type for {count} positions")

        return fixes

    def _standardize_precision(self, df: pd.DataFrame) -> list[str]:
        """Standardize numerical precision to 6 decimal places."""
        fixes = []

        financial_columns = [
            "Max_Favourable_Excursion",
            "Max_Adverse_Excursion",
            "MFE_MAE_Ratio",
            "Exit_Efficiency",
            "Exit_Efficiency_Fixed",
            "Return",
            "PnL",
            "Current_Unrealized_PnL",
        ]

        precision_fixes = 0
        for col in financial_columns:
            if col in df.columns:
                # Convert to numeric and round
                numeric_mask = pd.to_numeric(df[col], errors="coerce").notna()
                if numeric_mask.any():
                    df.loc[numeric_mask, col] = pd.to_numeric(
                        df.loc[numeric_mask, col],
                    ).round(6)
                    precision_fixes += numeric_mask.sum()

        if precision_fixes > 0:
            fixes.append(f"Standardized precision for {precision_fixes} numeric values")

        return fixes

    def _fix_scientific_notation(self, df: pd.DataFrame) -> list[str]:
        """Convert scientific notation to decimal format."""
        fixes = []

        numeric_columns = df.select_dtypes(include=["float64", "float32"]).columns
        sci_notation_fixes = 0

        for col in numeric_columns:
            # Find very small values that might display as scientific notation
            small_values = (df[col].abs() < 1e-4) & (df[col] != 0) & df[col].notna()
            if small_values.any():
                count = small_values.sum()
                # Round extremely small values to 0
                df.loc[small_values, col] = 0.0
                sci_notation_fixes += count

        if sci_notation_fixes > 0:
            fixes.append(
                f"Converted {sci_notation_fixes} scientific notation values to decimal",
            )

        return fixes

    def _fix_data_types(self, df: pd.DataFrame) -> list[str]:
        """Ensure proper data types for all columns."""
        fixes = []

        # Integer columns
        int_columns = ["Fast_Period", "Slow_Period", "Signal_Period"]
        for col in int_columns:
            if col in df.columns:
                with contextlib.suppress(Exception):
                    df[col] = (
                        pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
                    )

        # Ensure string columns are strings
        string_columns = [
            "Position_UUID",
            "Ticker",
            "Strategy_Type",
            "Direction",
            "Status",
            "Trade_Type",
        ]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).replace("nan", "")

        fixes.append("Standardized data types for all columns")
        return fixes

    def _create_backup(self) -> Path:
        """Create a backup of all portfolio files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"migration_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        # Copy all CSV files
        for csv_file in self.positions_dir.glob("*.csv"):
            shutil.copy2(csv_file, backup_path / csv_file.name)

        return backup_path

    def rollback_migration(self, backup_path: str) -> bool:
        """
        Rollback to a previous backup.

        Args:
            backup_path: Path to the backup directory

        Returns:
            True if rollback successful, False otherwise
        """
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                self.logger.error(f"Backup directory not found: {backup_path}")
                return False

            # Restore all CSV files
            for backup_file in backup_dir.glob("*.csv"):
                target_file = self.positions_dir / backup_file.name
                shutil.copy2(backup_file, target_file)
                self.logger.info(f"Restored: {backup_file.name}")

            self.logger.info("Rollback completed successfully")
            return True

        except Exception as e:
            self.logger.exception(f"Rollback failed: {e}")
            return False


def migrate_portfolio_data(
    base_dir: str | None = None, create_backup: bool = True,
) -> dict[str, Any]:
    """
    Convenience function to migrate all portfolio data.

    Args:
        base_dir: Base directory of the trading system
        create_backup: Whether to create backups before migration

    Returns:
        Migration results
    """
    manager = DataMigrationManager(Path(base_dir) if base_dir else None)
    return manager.migrate_all_portfolios(create_backup)


def validate_all_portfolios(base_dir: str | None = None) -> dict[str, Any]:
    """
    Convenience function to validate all portfolio files.

    Args:
        base_dir: Base directory of the trading system

    Returns:
        Validation results for all portfolios
    """
    base_path = Path(base_dir) if base_dir else Path.cwd()
    positions_dir = base_path / "csv" / "positions"

    results = {}
    validator = DataQualityValidator()

    for csv_file in positions_dir.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            results[csv_file.name] = validator.validate_position_data(df)
        except Exception as e:
            results[csv_file.name] = {
                "error": str(e),
                "is_valid": False,
                "severity": "critical",
            }

    return results
